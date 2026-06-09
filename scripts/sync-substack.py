#!/usr/bin/env python3
"""
Sync Substack posts from the Protocolized newsletter to the resources library.

Fetches the Substack RSS feed and creates a new markdown file for each post
that doesn't already exist in src/content/resources/.

Run manually:
    python3 scripts/sync-substack.py

Or triggered automatically by the GitHub Action in .github/workflows/sync-substack.yml
"""

import feedparser
import os
import re
import html
import json
import hashlib
import mimetypes
import subprocess
import tempfile
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# Configuration
SUBSTACK_FEED_URL = "https://protocolized.summerofprotocols.com/feed"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "content", "resources")
OUTPUT_DIR = os.path.normpath(OUTPUT_DIR)

SUBSTACK_BASE = "https://protocolized.summerofprotocols.com"
R2_BUCKET     = "protocolized-resources"
R2_BASE_URL   = "https://files.protocolized.io"
DB_NAME       = "protocolized-resources"
REPO_ROOT     = Path(__file__).parent.parent.resolve()
WORKER_DIR    = REPO_ROOT / "worker"
WRANGLER      = WORKER_DIR / "node_modules/.bin/wrangler"


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")[:80]


def escape_yaml_str(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def strip_html(s: str) -> str:
    """Remove HTML tags and decode entities."""
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def truncate(s: str, max_len: int = 280) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def extract_description(entry) -> str:
    """Extract a clean description from a feed entry."""
    # Try summary first, then content
    summary = getattr(entry, "summary", "") or ""
    if summary:
        clean = strip_html(summary)
        if len(clean) > 30:
            return truncate(clean)

    # Try content
    if hasattr(entry, "content") and entry.content:
        content = entry.content[0].get("value", "")
        clean = strip_html(content)
        if len(clean) > 30:
            return truncate(clean)

    return "A post from the Protocolized newsletter."


def get_existing_slugs() -> set:
    """Get all existing resource slugs to avoid duplicates."""
    slugs = set()
    if not os.path.exists(OUTPUT_DIR):
        return slugs
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".md"):
            slugs.add(f[:-3])
    return slugs


def get_existing_urls() -> set:
    """Check existing markdown files for URLs to avoid adding duplicates."""
    urls = set()
    if not os.path.exists(OUTPUT_DIR):
        return urls
    for f in os.listdir(OUTPUT_DIR):
        if not f.endswith(".md"):
            continue
        filepath = os.path.join(OUTPUT_DIR, f)
        try:
            with open(filepath, "r") as fh:
                content = fh.read()
            match = re.search(r'^url:\s*"([^"]+)"', content, re.MULTILINE)
            if match:
                urls.add(match.group(1))
        except Exception:
            pass
    return urls


def infer_tags(title: str, description: str) -> list:
    """Infer relevant tags from title and description text."""
    text = (title + " " + description).lower()
    tag_keywords = {
        "governance": ["governance", "govern", "policy", "regulation"],
        "coordination": ["coordination", "coordinate", "collective"],
        "AI": ["ai", "artificial intelligence", "machine learning", "llm", "gpt"],
        "blockchain": ["blockchain", "crypto", "ethereum", "web3", "defi"],
        "memory": ["memory", "archive", "remembering"],
        "fiction": ["fiction", "story", "narrative", "speculative"],
        "climate": ["climate", "environment", "carbon", "green"],
        "infrastructure": ["infrastructure", "network", "internet", "protocol stack"],
        "community": ["community", "social", "collective", "commons"],
        "theory": ["theory", "theoretical", "framework", "concept"],
        "design": ["design", "designer", "ux", "interface"],
        "standards": ["standard", "specification", "rfc", "ieee"],
        "economics": ["economic", "market", "incentive", "money"],
    }

    found_tags = ["protocols"]
    for tag, keywords in tag_keywords.items():
        if any(kw in text for kw in keywords):
            found_tags.append(tag)
            if len(found_tags) >= 4:
                break

    return found_tags


def create_markdown(entry, slug: str) -> str:
    """Generate a markdown file from a feed entry."""
    title = escape_yaml_str(strip_html(getattr(entry, "title", "Untitled")))
    url = getattr(entry, "link", "")
    description = escape_yaml_str(extract_description(entry))

    # Parse publication date
    try:
        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        date_str = pub_date.strftime("%Y-%m-%d")
    except Exception:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # Infer tags
    tags = infer_tags(title, description)

    lines = [
        "---",
        f'title: "{title}"',
        "type: article",
        "authors:",
        '  - name: "Protocolized"',
        '    url: "https://protocolized.summerofprotocols.com"',
        f"date: {date_str}",
        f'description: "{description}"',
        "tags:",
    ]
    for tag in tags:
        lines.append(f"  - {tag}")
    lines += [
        "audience:",
        "  - researcher",
        "  - practitioner",
        "featured: false",
        f'url: "{escape_yaml_str(url)}"',
        "---",
        "",
    ]

    return "\n".join(lines)


# ── D1 + R2 helpers (only used when CLOUDFLARE_API_TOKEN is set) ───────────

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
    rewritten = _IMG_SRC_RE.sub(lambda m: f'{m.group(1)}{url_map.get(m.group(2), m.group(2))}"', html_str)
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
        return

    # Cover image
    cover_original = data.get("cover_image")
    cover_r2 = None
    if cover_original:
        cover_r2 = _mirror_image(cover_original) or cover_original

    # Body HTML
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

    bylines = data.get("publishedBylines") or []
    authors = [b.get("name", "Protocolized") for b in bylines]
    primary = authors[0] if authors else "Protocolized"
    tags = [t.get("slug", "") for t in (data.get("postTags") or [])]
    now = datetime.now(timezone.utc).isoformat()
    prev_slug = data.get("previous_post_slug")
    next_slug = data.get("next_post_slug")

    sql = f"""INSERT OR REPLACE INTO posts (
  slug, title, subtitle, date, section, primary_author, authors,
  cover_image, cover_image_original, body_r2_key,
  summary, enriched_categories, substack_categories,
  reaction_count, previous_slug, next_slug,
  substack_url, image_count, mirrored_at, synced_at
) VALUES (
  {_sq(slug)}, {_sq(data['title'])}, {_sq(data.get('subtitle'))},
  {_sq((data.get('post_date') or '')[:10])},
  {_sq(data.get('section_name') or 'Protocolized')},
  {_sq(primary)}, {_sq(json.dumps(authors))},
  {_sq(cover_r2)}, {_sq(cover_original)}, {_sq(body_r2_key)},
  {_sq(data.get('description'))},
  {_sq(json.dumps([]))}, {_sq(json.dumps(tags))},
  {int(data.get('reactions', {}).get('❤') or 0)},
  {_sq(prev_slug)}, {_sq(next_slug)},
  {_sq(f"{SUBSTACK_BASE}/p/{slug}")},
  {int(image_count)}, {_sq(mirrored_at)}, {_sq(now)}
);"""

    _d1_exec(sql)

    # Update previous post's next_slug to point here
    if prev_slug:
        _d1_exec(f"UPDATE posts SET next_slug = '{slug}' WHERE slug = '{prev_slug}';")

    print(f"  [d1] ok ({image_count} images mirrored)")


def main():
    print(f"Fetching Substack feed: {SUBSTACK_FEED_URL}")
    feed = feedparser.parse(SUBSTACK_FEED_URL)

    if feed.bozo:
        print(f"Warning: Feed parse issue: {feed.bozo_exception}")

    existing_slugs = get_existing_slugs()
    existing_urls = get_existing_urls()

    print(f"Found {len(feed.entries)} entries in feed")
    print(f"Existing resources: {len(existing_slugs)}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    created = 0
    skipped = 0

    for entry in feed.entries:
        url = getattr(entry, "link", "")

        # Skip if URL already exists
        if url and url in existing_urls:
            skipped += 1
            continue

        # Generate slug from URL or title
        title = strip_html(getattr(entry, "title", "untitled"))
        # Try to extract slug from URL path
        url_match = re.search(r"/p/([^/?#]+)", url)
        if url_match:
            base_slug = slugify(url_match.group(1))
        else:
            base_slug = slugify(title)

        # Ensure unique slug
        slug = base_slug
        counter = 1
        while slug in existing_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1

        existing_slugs.add(slug)
        if url:
            existing_urls.add(url)

        content = create_markdown(entry, slug)
        out_path = os.path.join(OUTPUT_DIR, f"{slug}.md")

        with open(out_path, "w") as f:
            f.write(content)

        print(f"  Created: {slug}.md ({title[:50]})")
        created += 1

        if os.environ.get("CLOUDFLARE_API_TOKEN"):
            sync_post_to_d1(slug)
        else:
            print(f"  [d1] skipped (CLOUDFLARE_API_TOKEN not set)")

    print(f"\nDone. Created: {created}, Skipped (already exists): {skipped}")


if __name__ == "__main__":
    main()
