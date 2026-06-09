#!/usr/bin/env python3
"""
One-shot script: add new Substack posts to D1 + R2.

Fetches each slug from the Substack API, mirrors cover image and body images
to R2, stores body HTML in R2, writes metadata to D1, then stitches the
previous/next slug chain.

Usage:
  export CLOUDFLARE_API_TOKEN=$(grep CLOUDFLARE_API_TOKEN ../../.env.keys | cut -d= -f2)
  /opt/homebrew/bin/python3 scripts/add-new-posts.py
"""

import json, os, re, sys, time, hashlib, mimetypes, tempfile, subprocess, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT     = Path(__file__).parent.parent.resolve()
WORKER_DIR    = REPO_ROOT / "worker"
WRANGLER      = WORKER_DIR / "node_modules/.bin/wrangler"
ENV_FILE      = REPO_ROOT.parent / ".env.keys"

SUBSTACK_BASE = "https://protocolized.summerofprotocols.com"
R2_BUCKET     = "protocolized-resources"
R2_BASE_URL   = "https://files.protocolized.io"
DB_NAME       = "protocolized-resources"

# Ordered oldest → newest so the chain stitches correctly
NEW_SLUGS = [
    "2026-protocol-symposium-new-nature",
    "maintaining-everything-that-matters",
    "challenges-trivial-grand-and-whitehead",
]
PREV_EXISTING_SLUG = "irrigation-by-protocol-when-vineyards"

# ── Env ────────────────────────────────────────────────────────────────────

def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                if k.strip() not in os.environ:
                    os.environ[k.strip()] = v.strip()

# ── Substack API ───────────────────────────────────────────────────────────

def fetch_post_api(slug):
    url = f"{SUBSTACK_BASE}/api/v1/posts/{slug}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

# ── R2 helpers ─────────────────────────────────────────────────────────────

def wrangler_env():
    return {**os.environ}

def r2_put(content: bytes, key: str, ct: str):
    suffix = Path(key).suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(content); tmp = f.name
    try:
        r = subprocess.run(
            [str(WRANGLER), "r2", "object", "put", f"{R2_BUCKET}/{key}",
             f"--file={tmp}", f"--content-type={ct}", "--remote"],
            capture_output=True, text=True, cwd=WORKER_DIR, env=wrangler_env(),
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip())
    finally:
        os.unlink(tmp)

def download(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
            ct = r.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            ext = mimetypes.guess_extension(ct) or ".jpg"
            if ext in (".jpe", ".jfif"): ext = ".jpg"
            return data, ct, ext
    except Exception as e:
        print(f"  [warn] download failed {url[:70]}: {e}")
        return None

def decode_substackcdn(url):
    if "substackcdn.com/image/fetch" in url:
        parts = url.split("/https%3A%2F%2F", 1)
        if len(parts) == 2:
            return "https://" + urllib.parse.unquote(parts[1])
    return url

def mirror_image(src_url):
    orig = decode_substackcdn(src_url)
    result = download(orig) or (download(src_url) if orig != src_url else None)
    if not result:
        return None
    data, ct, ext = result
    h = hashlib.sha256(data).hexdigest()
    key = f"images/{h[:2]}/{h}{ext}"
    r2_put(data, key, ct)
    return f"{R2_BASE_URL}/{key}"

IMG_SRC_RE = re.compile(
    r'(src=")([^"]*(?:substackcdn\.com/image/fetch|substack-post-media\.s3\.amazonaws\.com)[^"]*)"',
    re.IGNORECASE,
)
SRCSET_RE = re.compile(r'\s+srcset="[^"]*"', re.IGNORECASE)

def process_body(html):
    url_map = {}
    for m in IMG_SRC_RE.finditer(html):
        src = m.group(2)
        if src not in url_map:
            print(f"    [img] {src[:70]}...")
            url_map[src] = mirror_image(src) or src
            time.sleep(0.1)
    rewritten = IMG_SRC_RE.sub(lambda m: f'{m.group(1)}{url_map.get(m.group(2), m.group(2))}"', html)
    rewritten = SRCSET_RE.sub("", rewritten)
    return rewritten, sum(1 for v in url_map.values() if v != list(url_map.keys())[list(url_map.values()).index(v)])

# ── D1 helpers ─────────────────────────────────────────────────────────────

def sq(v):
    if v is None: return "NULL"
    return "'" + str(v).replace("'", "''") + "'"

def d1_exec(sql):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
        f.write(sql); tmp = f.name
    try:
        r = subprocess.run(
            [str(WRANGLER), "d1", "execute", DB_NAME, "--remote", f"--file={tmp}"],
            capture_output=True, text=True, cwd=WORKER_DIR, env=wrangler_env(),
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip())
    finally:
        os.unlink(tmp)

def write_post_d1(p):
    sql = f"""INSERT OR REPLACE INTO posts (
  slug, title, subtitle, date, section, primary_author, authors,
  cover_image, cover_image_original, body_r2_key,
  summary, enriched_categories, substack_categories,
  reaction_count, previous_slug, next_slug,
  substack_url, image_count, mirrored_at, synced_at
) VALUES (
  {sq(p['slug'])}, {sq(p['title'])}, {sq(p.get('subtitle'))},
  {sq(p['date'])}, {sq(p['section'])}, {sq(p['primary_author'])},
  {sq(json.dumps(p['authors']))},
  {sq(p.get('cover_image'))}, {sq(p.get('cover_image_original'))},
  {sq(p.get('body_r2_key'))},
  {sq(p.get('summary'))},
  {sq(json.dumps(p.get('enriched_categories', [])))},
  {sq(json.dumps(p.get('substack_categories', [])))},
  {int(p.get('reaction_count') or 0)},
  {sq(p.get('previous_slug'))}, {sq(p.get('next_slug'))},
  {sq(p.get('substack_url'))},
  {int(p.get('image_count') or 0)},
  {sq(p.get('mirrored_at'))},
  {sq(p['synced_at'])}
);"""
    d1_exec(sql)

# ── Main ───────────────────────────────────────────────────────────────────

def main():
    load_env()
    if not os.environ.get("CLOUDFLARE_API_TOKEN"):
        sys.exit("Error: CLOUDFLARE_API_TOKEN not set.")

    slugs = NEW_SLUGS
    records = {}

    for slug in slugs:
        print(f"\n── {slug}")
        print("  fetching API...")
        data = fetch_post_api(slug)
        time.sleep(0.5)

        # Cover image
        cover_original = data.get("cover_image")
        cover_r2 = None
        if cover_original:
            print(f"  mirroring cover image...")
            cover_r2 = mirror_image(cover_original) or cover_original

        # Body HTML
        body_html = data.get("body_html") or ""
        body_r2_key = None
        image_count = 0
        mirrored_at = None
        if body_html:
            print(f"  processing body ({len(body_html):,} chars)...")
            body_html, image_count = process_body(body_html)
            if image_count > 0:
                mirrored_at = datetime.now(timezone.utc).isoformat()
            body_r2_key = f"posts/{slug}/body.html"
            print(f"  uploading body to R2...")
            r2_put(body_html.encode("utf-8"), body_r2_key, "text/html; charset=utf-8")

        bylines = data.get("publishedBylines") or []
        authors = [b.get("name", "Protocolized") for b in bylines]
        primary = authors[0] if authors else "Protocolized"
        tags = [t.get("slug", "") for t in (data.get("postTags") or [])]

        records[slug] = {
            "slug": slug,
            "title": data["title"],
            "subtitle": data.get("subtitle"),
            "date": (data.get("post_date") or data.get("publishedAt") or "")[:10],
            "section": data.get("section_name") or "Protocolized",
            "primary_author": primary,
            "authors": authors,
            "cover_image": cover_r2,
            "cover_image_original": cover_original,
            "body_r2_key": body_r2_key,
            "summary": data.get("description"),
            "enriched_categories": [],
            "substack_categories": tags,
            "reaction_count": data.get("reactions", {}).get("❤") or 0,
            "substack_url": f"{SUBSTACK_BASE}/p/{slug}",
            "image_count": image_count,
            "mirrored_at": mirrored_at,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

    # Stitch prev/next chain
    all_slugs = [PREV_EXISTING_SLUG] + slugs
    for i, slug in enumerate(slugs):
        records[slug]["previous_slug"] = all_slugs[i]        # i+1-1 = i
        records[slug]["next_slug"] = all_slugs[i + 2] if i + 2 < len(all_slugs) else None

    # Write to D1
    for slug in slugs:
        print(f"\n  writing {slug} to D1...")
        write_post_d1(records[slug])
        print(f"  ok")

    # Update existing post's next_slug
    print(f"\n  updating {PREV_EXISTING_SLUG} next_slug → {slugs[0]}...")
    d1_exec(f"UPDATE posts SET next_slug = '{slugs[0]}' WHERE slug = '{PREV_EXISTING_SLUG}';")
    print("  ok")

    print(f"\nDone. Added {len(slugs)} posts.")

if __name__ == "__main__":
    main()
