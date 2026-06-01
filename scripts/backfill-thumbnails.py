#!/usr/bin/env python3
"""
One-time: fetch cover_image for every Substack post from the API and
write it into the resources.thumbnail column in D1.

Usage:
    python3 scripts/backfill-thumbnails.py [--dry-run]
"""

import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

BASE_URL = "https://protocolized.summerofprotocols.com"
WRANGLER_TOML = Path(__file__).parent.parent / "worker" / "wrangler.toml"
DB_NAME = "protocolized-resources"
DRY_RUN = "--dry-run" in sys.argv


def fetch_all_posts():
    posts, offset = [], 0
    while True:
        url = f"{BASE_URL}/api/v1/posts?limit=50&offset={offset}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            batch = json.loads(r.read())
        if not batch:
            break
        posts.extend(batch)
        print(f"  fetched {len(posts)} posts...")
        if len(batch) < 50:
            break
        offset += 50
        time.sleep(0.4)
    return posts


def run_sql(sql: str):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write(sql)
        f.flush()
        cmd = [
            "npx", "wrangler", "d1", "execute", DB_NAME,
            "--file", f.name,
            "--config", str(WRANGLER_TOML),
            "--remote",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr[-500:]}")
            sys.exit(1)


def main():
    print("Fetching all Substack posts from API...")
    posts = fetch_all_posts()
    print(f"Total posts: {len(posts)}")

    # Build slug → cover_image map (only posts that have a cover image)
    slug_to_cover = {}
    for p in posts:
        slug = p.get("slug", "")
        cover = p.get("cover_image", "")
        if slug and cover:
            slug_to_cover[slug] = cover

    print(f"Posts with cover_image: {len(slug_to_cover)}")

    if DRY_RUN:
        for slug, url in list(slug_to_cover.items())[:5]:
            print(f"  {slug} → {url[:80]}...")
        print("Dry run — no writes.")
        return

    # Build UPDATE statements
    updates = []
    for slug, cover_url in slug_to_cover.items():
        escaped = cover_url.replace("'", "''")
        updates.append(
            f"UPDATE resources SET thumbnail = '{escaped}' WHERE slug = '{slug}' AND type = 'article';"
        )

    if not updates:
        print("Nothing to update.")
        return

    # Execute in one batch
    sql = "\n".join(updates)
    print(f"Writing {len(updates)} thumbnail URLs to D1...")
    run_sql(sql)
    print(f"Done. {len(updates)} resources updated.")


if __name__ == "__main__":
    main()
