#!/usr/bin/env python3
"""
Sync YouTube video metadata from c3po enriched_meta.json → resource Markdown files.

Reads c3po's enriched_meta.json (91 videos, all with Claude Haiku summaries,
speakers, categories, key_concepts). Cross-references against existing resource
Markdown files by video ID in their url: field, then:
  - UPDATES the 88 matched files (better description, authors, tags, thumbnail)
  - ADDS 3 new files for videos not yet in the library
  - LEAVES ALONE the 6 library-only resources not in enriched_meta

After running, sync to D1 with:
    python3 scripts/migrate-to-d1.py --remote

Usage:
    python3 scripts/sync-youtube-resources.py
    python3 scripts/sync-youtube-resources.py --dry-run
    python3 scripts/sync-youtube-resources.py --no-thumbnails
    python3 scripts/sync-youtube-resources.py --no-dates     # skip yt-dlp date fetch
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).parent.parent
C3PO_ROOT = Path(os.environ.get("C3PO_ROOT", str(REPO_ROOT.parent / "c3po")))
C3PO_META = C3PO_ROOT / "sources" / "youtube" / "enriched_meta.json"
RESOURCES_DIR = REPO_ROOT / "src" / "content" / "resources"
DATE_CACHE_PATH = Path(__file__).parent / ".yt-date-cache.json"
WRANGLER = REPO_ROOT / "worker" / "node_modules" / ".bin" / "wrangler"
ENV_KEYS = REPO_ROOT.parent / ".env.keys"
R2_BUCKET = "protocolized-resources"
CDN_BASE = "https://files.protocolized.io"

# ── Type mapping by series ────────────────────────────────────────────────────
SERIES_TYPE = {
    "bridge-atlas": "interview",
    "protocol-school-2025": "lecture",
    "popular-lectures": "lecture",
}

# ── Tag mapping from c3po categories ─────────────────────────────────────────
CATEGORY_TAGS = {
    "protocol-theory": "protocols",
    "protocol-watching": "protocol-watching",
    "protocol-fiction": "fiction",
    "governance": "governance",
    "technology-ai": "technology",
    "research-report": "research",
    "memory-archival": "memory",
    "organizations": "organizations",
}
SKIP_CATEGORIES = {"interview", "announcement", "editorial", "guest-talks", "town-hall"}

# ── Audience by series ────────────────────────────────────────────────────────
SERIES_AUDIENCE = {
    "researcher-salon": ["researcher", "academic"],
    "symposium-2024": ["researcher", "academic"],
    "protocol-school-2025": ["researcher", "academic"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_token() -> str:
    if t := os.environ.get("CLOUDFLARE_API_TOKEN"):
        return t
    if ENV_KEYS.exists():
        for line in ENV_KEYS.read_text().splitlines():
            if line.startswith("CLOUDFLARE_API_TOKEN="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("CLOUDFLARE_API_TOKEN not found")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")[:80]


def to_kebab(text: str) -> str:
    """Convert a phrase like 'Nakatomi space' → 'nakatomi-space'."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def yaml_str(s: str) -> str:
    """Wrap a string value for inline YAML, replacing inner double quotes."""
    return '"' + s.replace('"', "'") + '"'


# ── Date fetching ─────────────────────────────────────────────────────────────

def fetch_dates(video_ids: list[str]) -> dict[str, str]:
    """Batch-fetch upload dates via yt-dlp. Returns {video_id: 'YYYY-MM-DD'}."""
    urls = [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]
    result = subprocess.run(
        ["yt-dlp", "--skip-download", "--print", "%(id)s\t%(upload_date)s"] + urls,
        capture_output=True, text=True, timeout=600,
    )
    dates = {}
    for line in result.stdout.splitlines():
        parts = line.strip().split("\t")
        if len(parts) == 2:
            vid_id, raw = parts
            if raw and raw != "NA" and len(raw) == 8:
                dates[vid_id] = f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return dates


# ── Thumbnail handling ────────────────────────────────────────────────────────

def thumbnail_cdn_url(video_id: str) -> str:
    return f"{CDN_BASE}/covers/yt-{video_id}.jpg"


def thumbnail_exists_on_cdn(video_id: str) -> bool:
    try:
        r = requests.head(thumbnail_cdn_url(video_id), timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def upload_thumbnail(video_id: str) -> str | None:
    # Try maxresdefault first, fall back to hqdefault
    for size in ("maxresdefault", "hqdefault"):
        try:
            r = requests.get(f"https://img.youtube.com/vi/{video_id}/{size}.jpg", timeout=15)
            r.raise_for_status()
            if len(r.content) > 5000:  # real image; placeholders are tiny
                break
        except Exception:
            continue
    else:
        return None

    key = f"covers/yt-{video_id}.jpg"
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(r.content)
        tmp = f.name
    try:
        result = subprocess.run(
            [str(WRANGLER), "r2", "object", "put", f"{R2_BUCKET}/{key}",
             "--file", tmp, "--content-type", "image/jpeg", "--remote"],
            capture_output=True, text=True,
            cwd=str(REPO_ROOT / "worker"),
            env={**os.environ, "CLOUDFLARE_API_TOKEN": os.environ["CLOUDFLARE_API_TOKEN"]},
        )
        if result.returncode != 0:
            print(f"    wrangler error: {result.stderr.strip()[:120]}")
            return None
    finally:
        os.unlink(tmp)
    return thumbnail_cdn_url(video_id)


# ── Metadata mapping ──────────────────────────────────────────────────────────

def map_type(series: str) -> str:
    return SERIES_TYPE.get(series, "talk")


def map_tags(series: str, categories: list, key_concepts: list) -> list:
    tags = set()
    tags.add(series)
    for cat in categories:
        if cat in CATEGORY_TAGS:
            tags.add(CATEGORY_TAGS[cat])
    for kc in key_concepts:
        kebab = to_kebab(kc)
        if kebab:
            tags.add(kebab)
    return sorted(tags)


def map_authors(speakers: list) -> list:
    if speakers:
        return [{"name": s} for s in speakers]
    return [{"name": "Protocol Institute"}]


def map_audience(series: str) -> list:
    return SERIES_AUDIENCE.get(series, ["researcher", "practitioner"])


# ── Markdown generation ───────────────────────────────────────────────────────

def make_markdown(video_id: str, data: dict, date: str,
                  thumbnail_url: str | None, featured: bool = False) -> str:
    series = data.get("series", "")
    title = data["title"]
    resource_type = map_type(series)
    authors = map_authors(data.get("speakers", []))
    description = data.get("summary", "")
    tags = map_tags(series, data.get("categories", []), data.get("key_concepts", []))
    audience = map_audience(series)
    url = data.get("url", f"https://www.youtube.com/watch?v={video_id}")

    lines = ["---"]
    lines.append(f"title: {yaml_str(title)}")
    lines.append(f"type: {resource_type}")
    lines.append("authors:")
    for a in authors:
        lines.append(f"  - name: {yaml_str(a['name'])}")
    lines.append(f"date: {date}")
    lines.append(f"description: {yaml_str(description)}")
    lines.append("tags:")
    for tag in tags:
        lines.append(f"  - {tag}")
    lines.append("audience:")
    for aud in audience:
        lines.append(f"  - {aud}")
    lines.append(f"featured: {'true' if featured else 'false'}")
    lines.append(f"url: {yaml_str(url)}")
    if thumbnail_url:
        lines.append(f"thumbnail: {yaml_str(thumbnail_url)}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


# ── Library index ─────────────────────────────────────────────────────────────

def get_library_index() -> dict[str, tuple[str, Path]]:
    """Returns {video_id: (slug, path)} for all YouTube resources in library."""
    yt_re = re.compile(r'url:\s*"https://www\.youtube\.com/watch\?v=([^"]+)"')
    index = {}
    for path in RESOURCES_DIR.glob("*.md"):
        m = yt_re.search(path.read_text())
        if m:
            index[m.group(1)] = (path.stem, path)
    return index


def get_existing_featured(path: Path) -> bool:
    m = re.search(r"featured:\s*(true|false)", path.read_text())
    return bool(m and m.group(1) == "true")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--no-thumbnails", action="store_true", help="Skip thumbnail uploads")
    parser.add_argument("--no-dates", action="store_true", help="Skip yt-dlp date fetch (use cache or fallback)")
    args = parser.parse_args()

    os.environ["CLOUDFLARE_API_TOKEN"] = load_token()

    if not C3PO_META.exists():
        print(f"ERROR: enriched_meta.json not found at {C3PO_META}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {C3PO_META}...")
    meta: dict = json.loads(C3PO_META.read_text())
    print(f"  {len(meta)} videos")

    print("Loading library index...")
    library = get_library_index()
    print(f"  {len(library)} YouTube resources already in library")

    matched = set(meta.keys()) & set(library.keys())
    new_ids = set(meta.keys()) - set(library.keys())
    library_only = set(library.keys()) - set(meta.keys())
    print(f"  matched={len(matched)}  new={len(new_ids)}  library-only (untouched)={len(library_only)}")

    # ── Phase 1: Fetch upload dates ───────────────────────────────────────────
    date_cache: dict[str, str] = {}
    if DATE_CACHE_PATH.exists():
        date_cache = json.loads(DATE_CACHE_PATH.read_text())

    if not args.no_dates:
        missing = [vid for vid in meta if vid not in date_cache]
        if missing:
            print(f"\nFetching upload dates for {len(missing)} videos via yt-dlp...")
            fetched = fetch_dates(missing)
            date_cache.update(fetched)
            print(f"  Got {len(fetched)}/{len(missing)} dates")
            if not args.dry_run:
                DATE_CACHE_PATH.write_text(json.dumps(date_cache, indent=2))
        else:
            print(f"\nAll {len(meta)} dates in cache.")

    # ── Phase 2: Process each video ───────────────────────────────────────────
    existing_slugs = {p.stem for p in RESOURCES_DIR.glob("*.md")}
    thumbnail_cache: dict[str, bool] = {}

    updated = added = thumb_uploaded = thumb_failed = 0

    all_ids = list(matched) + list(new_ids)
    print(f"\nProcessing {len(all_ids)} videos...\n")

    for video_id in all_ids:
        data = meta[video_id]
        date = date_cache.get(video_id, "2024-01-01")

        # ── Thumbnail ──
        thumbnail_url: str | None = None
        if not args.no_thumbnails:
            if video_id in thumbnail_cache:
                thumbnail_url = thumbnail_cdn_url(video_id) if thumbnail_cache[video_id] else None
            elif thumbnail_exists_on_cdn(video_id):
                thumbnail_url = thumbnail_cdn_url(video_id)
                thumbnail_cache[video_id] = True
            elif not args.dry_run:
                result = upload_thumbnail(video_id)
                thumbnail_cache[video_id] = result is not None
                if result:
                    thumbnail_url = result
                    thumb_uploaded += 1
                else:
                    thumb_failed += 1
            else:
                thumbnail_url = thumbnail_cdn_url(video_id)  # assume exists for dry-run

        # ── Write Markdown ──
        if video_id in matched:
            slug, path = library[video_id]
            featured = get_existing_featured(path)
            md = make_markdown(video_id, data, date, thumbnail_url, featured)
            action = "UPDATE"
            if not args.dry_run:
                path.write_text(md, encoding="utf-8")
            updated += 1
        else:
            slug = slugify(data["title"])
            if slug in existing_slugs:
                slug = slug[:76] + "-yt"
            path = RESOURCES_DIR / f"{slug}.md"
            md = make_markdown(video_id, data, date, thumbnail_url, False)
            action = "ADD"
            if not args.dry_run:
                path.write_text(md, encoding="utf-8")
                existing_slugs.add(slug)
            added += 1

        series = data.get("series", "")
        thumb_note = f" 🖼" if thumbnail_url else ""
        print(f"  [{action}] {slug[:55]:<55} [{series}]{thumb_note}")

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}Done.")
    print(f"  Updated: {updated}  Added: {added}")
    if not args.no_thumbnails:
        print(f"  Thumbnails uploaded: {thumb_uploaded}  Failed: {thumb_failed}")
    if not args.dry_run:
        print(f"\nNext step: python3 scripts/migrate-to-d1.py --remote")


if __name__ == "__main__":
    main()
