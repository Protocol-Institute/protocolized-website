#!/usr/bin/env python3
"""
scripts/mirror-substack.py

Phase 2 backfill: reads c3po metadata + export HTML → mirrors images to R2 → writes to D1.

  - Body HTML stored in R2 at posts/{slug}/body.html (avoids D1's 100KB statement limit)
  - Images mirrored to R2 at images/{hash[:2]}/{hash}.ext
  - Metadata (no body) written to D1 posts table via wrangler d1 execute --remote
  - All operations use CLOUDFLARE_API_TOKEN via wrangler — no separate R2 API token needed

Run from repo root:
  export CLOUDFLARE_API_TOKEN=$(grep CLOUDFLARE_API_TOKEN /path/to/protocol-institute/.env.keys | cut -d= -f2)
  /opt/homebrew/bin/python3 scripts/mirror-substack.py
"""

import json
import os
import re
import sys
import time
import hashlib
import mimetypes
import urllib.request
import urllib.parse
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent
C3PO_DIR = REPO_ROOT.parent / "c3po"

API_META_FILE = C3PO_DIR / "sources/substack/api_metadata.json"
ENRICHED_META_FILE = C3PO_DIR / "sources/substack/enriched_meta.json"
POSTS_HTML_DIR = C3PO_DIR / "data/substack/posts"
STATE_FILE = REPO_ROOT / "data/mirror_state.json"
ENV_FILE = REPO_ROOT.parent / ".env.keys"  # protocol-institute/.env.keys
WRANGLER = REPO_ROOT / "worker/node_modules/.bin/wrangler"
WORKER_DIR = REPO_ROOT / "worker"

# ── CF / R2 config ─────────────────────────────────────────────────────────

R2_BUCKET = "protocolized-resources"
R2_BASE_URL = "https://files.protocolized.io"
SUBSTACK_BASE = "https://protocolized.summerofprotocols.com"
DB_NAME = "protocolized-resources"

# ── Env loading ────────────────────────────────────────────────────────────

def load_env():
    if not ENV_FILE.exists():
        print(f"[warn] env file not found at {ENV_FILE}", file=sys.stderr)
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            if key.strip() not in os.environ:
                os.environ[key.strip()] = val.strip()

def wrangler_env() -> dict:
    return {**os.environ}

# ── Wrangler R2 helpers ────────────────────────────────────────────────────

def r2_exists(key: str) -> bool:
    result = subprocess.run(
        [str(WRANGLER), "r2", "object", "get", f"{R2_BUCKET}/{key}",
         "--remote", "--pipe"],
        capture_output=True,
        cwd=WORKER_DIR,
        env=wrangler_env(),
    )
    return result.returncode == 0

def r2_put(content: bytes, key: str, content_type: str) -> str:
    """Upload bytes to R2 via wrangler; return R2 URL."""
    suffix = Path(key).suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(content)
        tmp = f.name
    try:
        result = subprocess.run(
            [str(WRANGLER), "r2", "object", "put", f"{R2_BUCKET}/{key}",
             f"--file={tmp}", f"--content-type={content_type}", "--remote"],
            capture_output=True,
            text=True,
            cwd=WORKER_DIR,
            env=wrangler_env(),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
    finally:
        os.unlink(tmp)
    return f"{R2_BASE_URL}/{key}"

# ── Image handling ─────────────────────────────────────────────────────────

def decode_substackcdn(url: str) -> str:
    if "substackcdn.com/image/fetch" in url:
        parts = url.split("/https%3A%2F%2F", 1)
        if len(parts) == 2:
            return "https://" + urllib.parse.unquote(parts[1])
    return url

def download_url(url: str) -> tuple[bytes, str, str] | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read()
            ct = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            ext = mimetypes.guess_extension(ct) or ".jpg"
            if ext in (".jpe", ".jfif"):
                ext = ".jpg"
            return content, ct, ext
    except Exception as e:
        print(f"    [warn] download failed {url[:70]}: {e}", file=sys.stderr)
        return None

def mirror_image(src_url: str, r2_cache: set) -> str | None:
    original_url = decode_substackcdn(src_url)
    result = download_url(original_url)
    if not result and original_url != src_url:
        result = download_url(src_url)
    if not result:
        return None
    content, ct, ext = result
    h = hashlib.sha256(content).hexdigest()
    key = f"images/{h[:2]}/{h}{ext}"
    if key not in r2_cache:
        if not r2_exists(key):
            r2_put(content, key, ct)
        r2_cache.add(key)
    return f"{R2_BASE_URL}/{key}"

IMG_SRC_RE = re.compile(
    r'(src=")([^"]*(?:substackcdn\.com/image/fetch|substack-post-media\.s3\.amazonaws\.com)[^"]*)"',
    re.IGNORECASE,
)
SRCSET_RE = re.compile(r'\s+srcset="[^"]*"', re.IGNORECASE)

def process_body_html(html: str, r2_cache: set) -> tuple[str, int]:
    url_map: dict[str, str] = {}
    count = 0
    for m in IMG_SRC_RE.finditer(html):
        src = m.group(2)
        if src in url_map:
            continue
        print(f"    [img] {src[:72]}...")
        r2_url = mirror_image(src, r2_cache)
        url_map[src] = r2_url or src
        if r2_url:
            count += 1
        time.sleep(0.1)

    def replace_src(m):
        return f'{m.group(1)}{url_map.get(m.group(2), m.group(2))}"'

    rewritten = IMG_SRC_RE.sub(replace_src, html)
    rewritten = SRCSET_RE.sub("", rewritten)
    return rewritten, count

# ── Substack API ───────────────────────────────────────────────────────────

def fetch_post_api(slug: str) -> dict | None:
    url = f"{SUBSTACK_BASE}/api/v1/posts/{slug}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"    [warn] API fetch failed for {slug}: {e}", file=sys.stderr)
        return None

# ── D1 write (metadata only — no body HTML) ────────────────────────────────

def sql_val(v) -> str:
    if v is None:
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"

def write_post_d1(post: dict) -> bool:
    sql = f"""INSERT OR REPLACE INTO posts (
  slug, title, subtitle, date, section, primary_author, authors,
  cover_image, cover_image_original, body_r2_key,
  summary, enriched_categories, substack_categories,
  section_id, reaction_count, restacks, previous_slug, next_slug,
  substack_url, image_count, mirrored_at, synced_at
) VALUES (
  {sql_val(post['slug'])},
  {sql_val(post['title'])},
  {sql_val(post.get('subtitle'))},
  {sql_val(post['date'])},
  {sql_val(post['section'])},
  {sql_val(post['primary_author'])},
  {sql_val(json.dumps(post['authors']))},
  {sql_val(post.get('cover_image'))},
  {sql_val(post.get('cover_image_original'))},
  {sql_val(post.get('body_r2_key'))},
  {sql_val(post.get('summary'))},
  {sql_val(json.dumps(post.get('enriched_categories', [])))},
  {sql_val(json.dumps(post.get('substack_categories', [])))},
  {sql_val(post.get('section_id'))},
  {int(post.get('reaction_count') or 0)},
  {int(post.get('restacks') or 0)},
  {sql_val(post.get('previous_slug'))},
  {sql_val(post.get('next_slug'))},
  {sql_val(post.get('substack_url'))},
  {int(post.get('image_count') or 0)},
  {sql_val(post.get('mirrored_at'))},
  {sql_val(post['synced_at'])}
);"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
        f.write(sql)
        tmp = f.name

    try:
        result = subprocess.run(
            [str(WRANGLER), "d1", "execute", DB_NAME, "--remote", f"--file={tmp}"],
            capture_output=True,
            text=True,
            cwd=WORKER_DIR,
            env=wrangler_env(),
        )
        if result.returncode != 0:
            print(f"    [error] D1 write failed:\n{result.stderr}", file=sys.stderr)
            return False
        return True
    finally:
        os.unlink(tmp)

# ── Main ───────────────────────────────────────────────────────────────────

def main():
    load_env()

    if not os.environ.get("CLOUDFLARE_API_TOKEN"):
        sys.exit(
            f"Error: CLOUDFLARE_API_TOKEN not set.\n"
            f"Run: export CLOUDFLARE_API_TOKEN=$(grep CLOUDFLARE_API_TOKEN {ENV_FILE} | cut -d= -f2)"
        )

    api_meta: list[dict] = json.loads(API_META_FILE.read_text())
    by_slug = {p["slug"]: p for p in api_meta}

    enriched: dict[str, dict] = {}
    if ENRICHED_META_FILE.exists():
        enriched = json.loads(ENRICHED_META_FILE.read_text())

    html_by_id: dict[str, Path] = {}
    for f in POSTS_HTML_DIR.glob("*.html"):
        post_id = f.name.split(".")[0]
        html_by_id[post_id] = f

    state: dict[str, dict] = {}
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())

    r2_cache: set[str] = set()

    slugs = list(by_slug.keys())
    print(f"Processing {len(slugs)} posts (resumable via {STATE_FILE.name})...\n")

    for i, slug in enumerate(slugs, 1):
        print(f"[{i}/{len(slugs)}] {slug}")
        st = state.setdefault(slug, {})

        if st.get("d1_written"):
            print("  skip (already done)")
            continue

        meta = by_slug[slug]
        enrich = enriched.get(slug, {})
        post_id = str(meta["id"])

        # ── Body HTML ──────────────────────────────────────────────────
        body_html_raw: str | None = None
        if post_id in html_by_id:
            body_html_raw = html_by_id[post_id].read_text(encoding="utf-8", errors="replace")
            print(f"  body: export file ({len(body_html_raw):,} chars)")
        else:
            print(f"  body: fetching from API (no export file for id={post_id})...")
            api_data = fetch_post_api(slug)
            if api_data:
                body_html_raw = api_data.get("body_html") or ""
            time.sleep(0.6)

        # ── Cover image ────────────────────────────────────────────────
        cover_image_original: str | None = None
        cover_image: str | None = None

        if not st.get("api_fetched"):
            print(f"  cover: fetching from API...")
            api_data = fetch_post_api(slug)
            if api_data:
                cover_image_original = api_data.get("cover_image")
                st["api_fetched"] = True
            time.sleep(0.5)

        if cover_image_original:
            print(f"  cover: mirroring...")
            cover_image = mirror_image(cover_image_original, r2_cache)
            if not cover_image:
                cover_image = cover_image_original

        # ── Mirror body images + rewrite URLs ─────────────────────────
        mirrored_at: str | None = None
        image_count = 0
        body_html_rewritten = body_html_raw

        if body_html_raw:
            body_html_rewritten, image_count = process_body_html(body_html_raw, r2_cache)
            if image_count > 0:
                mirrored_at = datetime.now(timezone.utc).isoformat()

        print(f"  images: {image_count} mirrored to R2")

        # ── Upload body HTML to R2 ─────────────────────────────────────
        body_r2_key: str | None = None
        if body_html_rewritten:
            body_r2_key = f"posts/{slug}/body.html"
            print(f"  body: uploading to R2...")
            r2_put(body_html_rewritten.encode("utf-8"), body_r2_key, "text/html; charset=utf-8")

        # ── Build D1 record (no body HTML) ────────────────────────────
        bylines = meta.get("publishedBylines") or []
        authors = [b.get("name", "Protocolized") for b in bylines]
        primary_author = (
            enrich.get("primary_author")
            or (authors[0] if authors else "Protocolized")
        )
        substack_tags = [t.get("slug", "") for t in (meta.get("postTags") or [])]

        post_record = {
            "slug": slug,
            "title": meta["title"],
            "subtitle": meta.get("subtitle") or None,
            "date": meta["post_date"][:10],
            "section": meta.get("section_name") or "Protocolized",
            "primary_author": primary_author,
            "authors": authors,
            "cover_image": cover_image,
            "cover_image_original": cover_image_original,
            "body_r2_key": body_r2_key,
            "summary": enrich.get("summary"),
            "enriched_categories": enrich.get("categories") or [],
            "substack_categories": substack_tags,
            "section_id": meta.get("section_id"),
            "reaction_count": meta.get("reaction_count") or 0,
            "restacks": meta.get("restacks") or 0,
            "previous_slug": meta.get("previous_post_slug"),
            "next_slug": meta.get("next_post_slug"),
            "substack_url": f"{SUBSTACK_BASE}/p/{slug}",
            "image_count": image_count,
            "mirrored_at": mirrored_at,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

        # ── Write metadata to D1 ───────────────────────────────────────
        print(f"  d1: writing metadata...")
        ok = write_post_d1(post_record)
        if ok:
            st.update({"d1_written": True, "image_count": image_count, "mirrored_at": mirrored_at})
            print(f"  ok")
        else:
            print(f"  FAILED — will retry on next run")

        state[slug] = st
        STATE_FILE.write_text(json.dumps(state, indent=2))
        time.sleep(0.3)

    done = sum(1 for s in state.values() if s.get("d1_written"))
    print(f"\nDone. {done}/{len(slugs)} posts written to D1.")


if __name__ == "__main__":
    main()
