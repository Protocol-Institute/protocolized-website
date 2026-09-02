#!/usr/bin/env python3
"""
Sync new Substack posts to D1 (posts table) and R2 (body HTML + images).

This script owns the D1 posts table and the R2 body/image mirror — the magazine
layer that serves /p/:slug pages. It does NOT create resource Markdown files;
that is c3po's job via sync-substack-resources.py.

State is tracked in scripts/.substack-sync-state.json (committed to repo) so
GitHub Actions runs are idempotent across days.

Run manually:
    python3 scripts/sync-substack.py

Triggered automatically by .github/workflows/sync-substack.yml (daily cron).
"""

import feedparser
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fiction_classification import is_fiction_post_section, resolve_section

SUBSTACK_FEED_URL = "https://protocolized.summerofprotocols.com/feed"
SUBSTACK_BASE     = "https://protocolized.summerofprotocols.com"
R2_BUCKET         = "protocolized-resources"
R2_BASE_URL       = "https://files.protocolized.io"
DB_NAME           = "protocolized-resources"

REPO_ROOT  = Path(__file__).parent.parent.resolve()
WORKER_DIR = REPO_ROOT / "worker"
WRANGLER   = WORKER_DIR / "node_modules/.bin/wrangler"
STATE_FILE = Path(__file__).parent / ".substack-sync-state.json"


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")[:80]


# ── State ─────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"synced_slugs": []}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── D1 + R2 helpers ───────────────────────────────────────────────────────────

def _wrangler_env():
    return {**os.environ}


def _download(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
            ct = r.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            ext = mimetypes.guess_extension(ct) or ".jpg"
            if ext in (".jpe", ".jfif"):
                ext = ".jpg"
            return data, ct, ext
    except Exception as e:
        print(f"    [warn] download failed {url[:70]}: {e}")
        return None


def _decode_substackcdn(url):
    if "substackcdn.com/image/fetch" in url:
        parts = url.split("/https%3A%2F%2F", 1)
        if len(parts) == 2:
            return "https://" + urllib.parse.unquote(parts[1])
    return url


def _r2_put(content, key, ct):
    suffix = Path(key).suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(content)
        tmp = f.name
    try:
        r = subprocess.run(
            [str(WRANGLER), "r2", "object", "put", f"{R2_BUCKET}/{key}",
             f"--file={tmp}", f"--content-type={ct}", "--remote"],
            capture_output=True, text=True, cwd=WORKER_DIR, env=_wrangler_env(),
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip())
    finally:
        os.unlink(tmp)


def _mirror_image(src_url):
    orig = _decode_substackcdn(src_url)
    result = _download(orig) or (_download(src_url) if orig != src_url else None)
    if not result:
        return None
    data, ct, ext = result
    key = f"images/{hashlib.sha256(data).hexdigest()[:2]}/{hashlib.sha256(data).hexdigest()}{ext}"
    _r2_put(data, key, ct)
    return f"{R2_BASE_URL}/{key}"


_IMG_SRC_RE = re.compile(
    r'(src=")([^"]*(?:substackcdn\.com/image/fetch|substack-post-media\.s3\.amazonaws\.com)[^"]*)"',
    re.IGNORECASE,
)
_SRCSET_RE = re.compile(r'\s+srcset="[^"]*"', re.IGNORECASE)


def _process_body(html_str):
    url_map = {}
    for m in _IMG_SRC_RE.finditer(html_str):
        src = m.group(2)
        if src not in url_map:
            url_map[src] = _mirror_image(src) or src
            time.sleep(0.1)
    rewritten = _IMG_SRC_RE.sub(
        lambda m: f'{m.group(1)}{url_map.get(m.group(2), m.group(2))}"', html_str
    )
    rewritten = _SRCSET_RE.sub("", rewritten)
    image_count = sum(1 for orig, new in url_map.items() if new != orig)
    return rewritten, image_count


def _sq(v):
    if v is None:
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"


def _d1_exec(sql):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
        f.write(sql)
        tmp = f.name
    try:
        r = subprocess.run(
            [str(WRANGLER), "d1", "execute", DB_NAME, "--remote", f"--file={tmp}"],
            capture_output=True, text=True, cwd=WORKER_DIR, env=_wrangler_env(),
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip())
    finally:
        os.unlink(tmp)


def sync_post_to_d1(slug):
    """Fetch post from Substack API, mirror to R2, write metadata to D1."""
    print(f"  [d1] syncing {slug}...")
    try:
        url = f"{SUBSTACK_BASE}/api/v1/posts/{slug}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        time.sleep(0.5)
    except Exception as e:
        print(f"  [d1] API fetch failed: {e}")
        return False

    cover_original = data.get("cover_image")
    cover_r2 = _mirror_image(cover_original) or cover_original if cover_original else None

    body_html = data.get("body_html") or ""
    body_r2_key = None
    image_count = 0
    mirrored_at = None
    if body_html:
        body_html, image_count = _process_body(body_html)
        if image_count > 0:
            mirrored_at = datetime.now(timezone.utc).isoformat()
        body_r2_key = f"posts/{slug}/body.html"
        _r2_put(body_html.encode("utf-8"), body_r2_key, "text/html; charset=utf-8")

    # NB: the per-post endpoint returns section_id but not section_name.
    section_name = resolve_section(
        slug, data.get("section_id"), data.get("section_name")
    )
    if is_fiction_post_section(section_name):
        print(
            f"  [d1] !!! WARNING: '{slug}' is in Substack section '{section_name}' "
            f"(fiction). This site is nonfiction-only post-fork -- new fiction "
            f"content should not be posted to the original Substack. Syncing "
            f"anyway; investigate before merging this run's commit."
        )

    bylines = data.get("publishedBylines") or []
    authors = [b.get("name", "Protocolized") for b in bylines]
    primary = authors[0] if authors else "Protocolized"
    tags = [t.get("slug", "") for t in (data.get("postTags") or [])]
    now = datetime.now(timezone.utc).isoformat()
    prev_slug = data.get("previous_post_slug")
    next_slug = data.get("next_post_slug")

    sql = f"""INSERT INTO posts (
  slug, title, subtitle, date, section, primary_author, authors,
  cover_image, cover_image_original, body_r2_key,
  summary, substack_categories,
  reaction_count, previous_slug, next_slug,
  substack_url, image_count, mirrored_at, synced_at
) VALUES (
  {_sq(slug)}, {_sq(data['title'])}, {_sq(data.get('subtitle'))},
  {_sq((data.get('post_date') or '')[:10])},
  {_sq(section_name)},
  {_sq(primary)}, {_sq(json.dumps(authors))},
  {_sq(cover_r2)}, {_sq(cover_original)}, {_sq(body_r2_key)},
  {_sq(data.get('description'))},
  {_sq(json.dumps(tags))},
  {int(data.get('reactions', {}).get('❤') or 0)},
  {_sq(prev_slug)}, {_sq(next_slug)},
  {_sq(f"{SUBSTACK_BASE}/p/{slug}")},
  {int(image_count)}, {_sq(mirrored_at)}, {_sq(now)}
) ON CONFLICT(slug) DO UPDATE SET
  title = excluded.title, subtitle = excluded.subtitle,
  date = excluded.date, section = excluded.section,
  primary_author = excluded.primary_author, authors = excluded.authors,
  cover_image = excluded.cover_image, cover_image_original = excluded.cover_image_original,
  body_r2_key = excluded.body_r2_key, summary = excluded.summary,
  substack_categories = excluded.substack_categories,
  reaction_count = excluded.reaction_count,
  previous_slug = excluded.previous_slug, next_slug = excluded.next_slug,
  substack_url = excluded.substack_url, image_count = excluded.image_count,
  mirrored_at = excluded.mirrored_at, synced_at = excluded.synced_at,
  is_placeholder = 0;"""

    _d1_exec(sql)

    if prev_slug:
        _d1_exec(f"UPDATE posts SET next_slug = '{slug}' WHERE slug = '{prev_slug}';")

    print(f"  [d1] ok ({image_count} images mirrored)")
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Fetching Substack feed: {SUBSTACK_FEED_URL}")
    feed = feedparser.parse(SUBSTACK_FEED_URL)
    if feed.bozo:
        print(f"Warning: Feed parse issue: {feed.bozo_exception}")

    state = load_state()
    synced_set = set(state.get("synced_slugs", []))
    has_cf_token = bool(os.environ.get("CLOUDFLARE_API_TOKEN"))

    print(f"Found {len(feed.entries)} entries in feed")
    print(f"Already synced: {len(synced_set)} slugs in state")

    synced = skipped = 0
    for entry in feed.entries:
        url = getattr(entry, "link", "")
        m = re.search(r"/p/([^/?#]+)", url)
        if not m:
            continue
        slug = slugify(m.group(1))

        if slug in synced_set:
            skipped += 1
            continue

        title = getattr(entry, "title", "untitled")
        print(f"  New: {slug} ({title[:60]})")

        if has_cf_token:
            ok = sync_post_to_d1(slug)
            if ok:
                synced_set.add(slug)
                synced += 1
        else:
            print(f"  [d1] skipped (CLOUDFLARE_API_TOKEN not set)")

    state["synced_slugs"] = sorted(synced_set)
    save_state(state)
    print(f"\nDone. Synced to D1: {synced}  Already done: {skipped}")


if __name__ == "__main__":
    main()
