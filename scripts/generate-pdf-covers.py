#!/usr/bin/env python3
"""
Render page 1 of each PDF resource as a JPEG cover image.
Uploads to R2 at covers/{slug}.jpg and updates D1 thumbnail field.

Usage:
    python3 scripts/generate-pdf-covers.py            # all PDFs missing thumbnails
    python3 scripts/generate-pdf-covers.py --all      # re-generate all, overwriting existing
    python3 scripts/generate-pdf-covers.py --slug foo # single resource
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import fitz  # PyMuPDF

REPO_ROOT = Path(__file__).parent.parent
WRANGLER = REPO_ROOT / "worker" / "node_modules" / ".bin" / "wrangler"
ENV_KEYS = REPO_ROOT.parent / ".env.keys"
R2_BUCKET = "protocolized-resources"
CDN_BASE = "https://files.protocolized.io"
COVER_PREFIX = "covers"
# Width in pixels for the generated JPEG (height is proportional to the page)
RENDER_WIDTH = 900
JPEG_QUALITY = 88


def load_token() -> str:
    """Return CLOUDFLARE_API_TOKEN from env or the PI .env.keys file."""
    if t := os.environ.get("CLOUDFLARE_API_TOKEN"):
        return t
    if ENV_KEYS.exists():
        for line in ENV_KEYS.read_text().splitlines():
            if line.startswith("CLOUDFLARE_API_TOKEN="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError(f"CLOUDFLARE_API_TOKEN not found in env or {ENV_KEYS}")


def run_wrangler(*args: str) -> str:
    env = {**os.environ, "CLOUDFLARE_API_TOKEN": os.environ["CLOUDFLARE_API_TOKEN"]}
    result = subprocess.run(
        [str(WRANGLER), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(Path(__file__).parent.parent / "worker"),
    )
    if result.returncode != 0:
        raise RuntimeError(f"wrangler error: {result.stderr.strip()}")
    return result.stdout


def d1(command: str) -> list[dict]:
    out = run_wrangler("d1", "execute", "protocolized-resources", "--remote",
                       "--json", f"--command={command}")
    # Wrangler may print banner lines before the JSON — find the first '[' or '{'
    start = min(
        (i for i in (out.find("["), out.find("{")) if i >= 0),
        default=-1,
    )
    if start < 0:
        return []
    data = json.loads(out[start:])
    if isinstance(data, dict):
        data = [data]
    return data[0]["results"] if data and data[0].get("results") else []


def get_pdf_resources(slug_filter: str | None = None, only_missing: bool = True) -> list[dict]:
    if slug_filter:
        return d1(f"SELECT slug, file FROM resources WHERE slug = '{slug_filter}' AND file LIKE '%.pdf'")
    if only_missing:
        return d1("SELECT slug, file FROM resources WHERE file LIKE '%.pdf' AND thumbnail IS NULL ORDER BY slug")
    return d1("SELECT slug, file FROM resources WHERE file LIKE '%.pdf' ORDER BY slug")


def download_pdf(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "protocolized-cover-gen/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
        f.write(resp.read())


def render_cover(pdf_path: Path, out_path: Path) -> tuple[int, int]:
    """Render page 1 to JPEG; return (width_px, height_px)."""
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    scale = RENDER_WIDTH / page.rect.width
    h_px = int(page.rect.height * scale)
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(str(out_path), output="jpg", jpg_quality=JPEG_QUALITY)
    doc.close()
    return RENDER_WIDTH, h_px


def upload_to_r2(local_path: Path, r2_key: str) -> None:
    run_wrangler(
        "r2", "object", "put",
        f"{R2_BUCKET}/{r2_key}",
        "--file", str(local_path),
        "--content-type", "image/jpeg",
        "--remote",
    )


def update_thumbnail(slug: str, url: str) -> None:
    run_wrangler(
        "d1", "execute", "protocolized-resources", "--remote",
        f"--command=UPDATE resources SET thumbnail = '{url}' WHERE slug = '{slug}'",
    )


def process(slug: str, file_url: str, tmpdir: Path) -> bool:
    r2_key = f"{COVER_PREFIX}/{slug}.jpg"
    cdn_url = f"{CDN_BASE}/{r2_key}"
    pdf_path = tmpdir / f"{slug}.pdf"
    jpg_path = tmpdir / f"{slug}.jpg"

    print(f"  downloading {file_url} ...", end=" ", flush=True)
    download_pdf(file_url, pdf_path)
    print(f"{pdf_path.stat().st_size // 1024} KB", flush=True)

    print(f"  rendering page 1 ...", end=" ", flush=True)
    w_px, h_px = render_cover(pdf_path, jpg_path)
    print(f"{jpg_path.stat().st_size // 1024} KB ({w_px}×{h_px}px)", flush=True)

    print(f"  uploading to R2 at {r2_key} ...", end=" ", flush=True)
    upload_to_r2(jpg_path, r2_key)
    print("ok", flush=True)

    print(f"  updating D1 thumbnail → {cdn_url} ...", end=" ", flush=True)
    update_thumbnail(slug, cdn_url)
    print("ok", flush=True)

    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Re-generate even if thumbnail exists")
    parser.add_argument("--slug", help="Process a single resource by slug")
    args = parser.parse_args()

    token = load_token()
    os.environ["CLOUDFLARE_API_TOKEN"] = token

    rows = get_pdf_resources(slug_filter=args.slug, only_missing=not args.all)
    if not rows:
        print("Nothing to process.")
        return

    print(f"Processing {len(rows)} resource(s)...\n")
    ok = err = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        for row in rows:
            slug, file_url = row["slug"], row["file"]
            print(f"[{slug}]")
            try:
                process(slug, file_url, Path(tmpdir))
                ok += 1
            except Exception as e:
                print(f"  ERROR: {e}", file=sys.stderr)
                err += 1
            print()

    print(f"Done. {ok} succeeded, {err} failed.")


if __name__ == "__main__":
    main()
