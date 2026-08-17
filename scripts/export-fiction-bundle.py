#!/usr/bin/env python3
"""
Export all fiction content (posts, resources, books + R2 assets) into a
portable bundle for the new fiction publication (working name "Monstrous
Times") to bootstrap from.

Fiction/nonfiction boundary: see fiction_classification.py (single source of
truth, mirrors worker/src/fiction.ts).

Usage:
    python3 scripts/export-fiction-bundle.py            # queries remote D1
    python3 scripts/export-fiction-bundle.py --local     # local miniflare D1 (dev/test only)

Output: exports/fiction-bundle-YYYYMMDD/ (manifest.json + assets/) plus a
zipped copy at exports/fiction-bundle-YYYYMMDD.zip. Not committed to git
(see .gitignore) -- this is a handoff artifact, not a repo asset.

Run once now as a baseline. Re-run immediately before the actual Monstrous
Times cutover so the handoff bundle is fresh, not stale.
"""

import argparse
import json
import subprocess
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fiction_classification import (
    FICTION_BOOK_CATEGORY,
    FICTION_POST_SECTIONS,
    FICTION_RESOURCE_TYPE,
)

WRANGLER_TOML = Path(__file__).parent.parent / "worker" / "wrangler.toml"
REPO_ROOT = WRANGLER_TOML.parent.parent
DB_NAME = "protocolized-resources"
R2_BASE_URL = "https://files.protocolized.io"
EXPORT_ROOT = REPO_ROOT / "exports"


def query(sql: str, remote: bool) -> list[dict]:
    cmd = [
        "npx", "wrangler", "d1", "execute", DB_NAME,
        "--command", sql,
        "--config", str(WRANGLER_TOML),
        "--json",
    ]
    if remote:
        cmd.append("--remote")
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR: wrangler query failed", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    data = json.loads(result.stdout)
    return data[0]["results"]


def download(url: str, dest: Path) -> bool:
    if not url:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            dest.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"  [warn] download failed {url[:80]}: {e}")
        return False


def r2_key_from_url(url: str | None) -> str | None:
    """Extract the R2 object key from a files.protocolized.io URL, if it is one."""
    if not url or R2_BASE_URL not in url:
        return None
    return url.split(R2_BASE_URL + "/", 1)[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true", help="Query local miniflare D1 instead of remote")
    args = parser.parse_args()
    remote = not args.local

    today = date.today().isoformat()
    out_dir = EXPORT_ROOT / f"fiction-bundle-{today}"
    assets_dir = out_dir / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)

    fiction_sections_sql = ",".join(f"'{s}'" for s in sorted(FICTION_POST_SECTIONS))

    print("Querying fiction posts...")
    posts = query(f"SELECT * FROM posts WHERE section IN ({fiction_sections_sql})", remote)
    print(f"  {len(posts)} posts")

    print("Querying fiction resources...")
    resources = query(f"SELECT * FROM resources WHERE type = '{FICTION_RESOURCE_TYPE}'", remote)
    print(f"  {len(resources)} resources")

    print("Querying fiction books...")
    books = query(f"SELECT * FROM books WHERE category = '{FICTION_BOOK_CATEGORY}'", remote)
    print(f"  {len(books)} books")

    print("Downloading R2 assets...")
    asset_count = 0

    for p in posts:
        if p.get("body_r2_key"):
            url = f"{R2_BASE_URL}/{p['body_r2_key']}"
            if download(url, assets_dir / p["body_r2_key"]):
                asset_count += 1
        key = r2_key_from_url(p.get("cover_image"))
        if key and download(p["cover_image"], assets_dir / key):
            asset_count += 1

    for r in resources:
        for field in ("file", "thumbnail"):
            url = r.get(field)
            key = r2_key_from_url(url)
            if key and download(url, assets_dir / key):
                asset_count += 1

    for b in books:
        for field in ("cover_image", "banner", "file"):
            url = b.get(field)
            key = r2_key_from_url(url)
            if key and download(url, assets_dir / key):
                asset_count += 1

    print(f"  {asset_count} assets downloaded")

    manifest = {
        "generated_at": today,
        "source": f"protocolized-website D1 ({DB_NAME}), {'remote' if remote else 'local'}",
        "counts": {"posts": len(posts), "resources": len(resources), "books": len(books)},
        "posts": posts,
        "resources": resources,
        "books": books,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {manifest_path}")

    zip_path = EXPORT_ROOT / f"fiction-bundle-{today}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in out_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(out_dir.parent))
    print(f"Zipped to {zip_path}")


if __name__ == "__main__":
    main()
