#!/usr/bin/env python3
"""
Generate 1200×600 banner composites for PDF resources.

Layout: teal left panel with book cover | surface right panel with title + authors.
Uploads to R2 at banners/{slug}.jpg and updates D1 thumbnail.

Usage:
    python3 scripts/generate-banners.py            # all PDFs with covers, missing banners
    python3 scripts/generate-banners.py --all      # regenerate all
    python3 scripts/generate-banners.py --slug foo # single resource
"""

import argparse
import io
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO_ROOT = Path(__file__).parent.parent
WRANGLER = REPO_ROOT / "worker" / "node_modules" / ".bin" / "wrangler"
ENV_KEYS = REPO_ROOT.parent / ".env.keys"
R2_BUCKET = "protocolized-resources"
CDN_BASE = "https://files.protocolized.io"
BANNER_PREFIX = "banners"

# Canvas dimensions (2:1 matches carousel aspect-[2/1])
W, H = 1200, 600
COVER_PANEL_W = 390      # left teal panel width
TEXT_X = COVER_PANEL_W + 56
TEXT_MAX_W = W - TEXT_X - 56
MAX_TITLE_LINES = 4

# Brand colours
TEAL        = (15, 110, 86)
TEAL_LIGHT  = (18, 130, 100)
SURFACE     = (249, 248, 245)
DARK        = (44, 44, 42)
SECONDARY   = (110, 110, 108)
WHITE       = (255, 255, 255)

# Fonts
FONT_GEORGIA_REG  = "/System/Library/Fonts/Supplemental/Georgia.ttf"
FONT_GEORGIA_ITAL = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"
FONT_SANS         = "/Library/Fonts/Calibri.ttf"


def load_fonts():
    return {
        "badge":   ImageFont.truetype(FONT_SANS,         13),
        "title":   ImageFont.truetype(FONT_GEORGIA_REG,  40),
        "title_sm":ImageFont.truetype(FONT_GEORGIA_REG,  34),
        "authors": ImageFont.truetype(FONT_GEORGIA_ITAL, 18),
        "meta":    ImageFont.truetype(FONT_SANS,         13),
        "mark":    ImageFont.truetype(FONT_SANS,         12),
    }


def wrap_title(text: str, draw: ImageDraw.ImageDraw, font, max_width: int, max_lines: int) -> tuple[list[str], ImageFont.FreeTypeFont]:
    """Word-wrap title; shrink font if too many lines."""
    for fnt in (font, ImageFont.truetype(FONT_GEORGIA_REG, 34), ImageFont.truetype(FONT_GEORGIA_REG, 28)):
        words = text.split()
        lines, current = [], []
        for word in words:
            probe = " ".join(current + [word])
            bb = draw.textbbox((0, 0), probe, font=fnt)
            if bb[2] - bb[0] <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        if len(lines) <= max_lines:
            return lines, fnt
    # Last resort: truncate
    return lines[:max_lines], ImageFont.truetype(FONT_GEORGIA_REG, 28)


def format_authors(authors: list[dict]) -> str:
    names = [a["name"] for a in authors]
    if len(names) <= 3:
        return ", ".join(names)
    return ", ".join(names[:3]) + f" + {len(names) - 3} more"


def badge_label(resource_type: str) -> str:
    labels = {
        "paper": "Paper", "working-paper": "Working Paper",
        "framework": "Framework", "workshop-template": "Workshop Template",
        "game": "Game", "dataset": "Dataset", "interview": "Interview",
        "presentation": "Presentation", "code": "Code",
        "prompt-template": "Prompt Template", "image": "Image",
        "talk": "Talk", "lecture": "Lecture",
        "article": "Article", "fiction": "Fiction",
        "living-document": "Living Document",
    }
    return labels.get(resource_type, resource_type.replace("-", " ").title())


def make_banner(cover_bytes: bytes, title: str, authors: list[dict],
                resource_type: str, year: str) -> bytes:
    fonts = load_fonts()
    canvas = Image.new("RGB", (W, H), SURFACE)
    draw = ImageDraw.Draw(canvas)

    # ── Left panel: teal background ──────────────────────────────────────────
    canvas.paste(Image.new("RGB", (COVER_PANEL_W, H), TEAL), (0, 0))

    # Cover image: fit inside left panel with padding
    PAD = 28
    max_cw = COVER_PANEL_W - 2 * PAD
    max_ch = H - 2 * PAD

    cover_raw = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    r = cover_raw.width / cover_raw.height
    if r > max_cw / max_ch:
        cw, ch = max_cw, int(max_cw / r)
    else:
        ch, cw = max_ch, int(max_ch * r)
    cover = cover_raw.resize((cw, ch), Image.LANCZOS)

    cx = (COVER_PANEL_W - cw) // 2
    cy = (H - ch) // 2

    # Drop shadow (blurred dark rectangle offset by 6px)
    shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.rectangle([cx + 6, cy + 6, cx + cw + 6, cy + ch + 6], fill=(0, 30, 20, 160))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=8))
    canvas = canvas.convert("RGBA")
    canvas.alpha_composite(shadow_layer)
    canvas = canvas.convert("RGB")

    canvas.paste(cover, (cx, cy))
    draw = ImageDraw.Draw(canvas)

    # ── Right panel: text ─────────────────────────────────────────────────────
    # Thin teal accent line at the top of the text panel
    draw.rectangle([COVER_PANEL_W, 0, W - 1, 5], fill=TEAL)

    # Pre-calculate text block height so we can vertically centre it
    title_lines, title_font = wrap_title(title, draw, fonts["title"], TEXT_MAX_W, MAX_TITLE_LINES)
    line_h = int(title_font.size * 1.25)

    badge_h    = fonts["badge"].size
    badge_gap  = 16
    title_h    = len(title_lines) * line_h
    author_gap = 20
    author_h   = int(fonts["authors"].size * 1.4) if authors else 0
    total_h    = badge_h + badge_gap + title_h + (author_gap + author_h if authors else 0)

    start_y = (H - total_h) // 2

    # Resource type badge
    badge = badge_label(resource_type).upper()
    draw.text((TEXT_X, start_y), badge, font=fonts["badge"], fill=TEAL)

    # Title
    ty = start_y + badge_h + badge_gap
    for line in title_lines:
        draw.text((TEXT_X, ty), line, font=title_font, fill=DARK)
        ty += line_h

    # Authors
    if authors:
        author_text = format_authors(authors)
        draw.text((TEXT_X, ty + author_gap), author_text, font=fonts["authors"], fill=SECONDARY)

    # Year (bottom-left of text panel)
    draw.text((TEXT_X, H - 48), year, font=fonts["meta"], fill=SECONDARY)

    # "Protocolized" mark (bottom-right)
    mark = "Protocolized"
    bb = draw.textbbox((0, 0), mark, font=fonts["mark"])
    mark_w = bb[2] - bb[0]
    draw.text((W - 48 - mark_w, H - 48), mark, font=fonts["mark"], fill=TEAL)

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=90, optimize=True)
    return buf.getvalue()


# ── D1 / Wrangler helpers (same pattern as generate-pdf-covers.py) ────────────

def load_token() -> str:
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
        capture_output=True, text=True, env=env,
        cwd=str(REPO_ROOT / "worker"),
    )
    if result.returncode != 0:
        raise RuntimeError(f"wrangler error: {result.stderr.strip()}")
    return result.stdout


def d1(command: str) -> list[dict]:
    out = run_wrangler("d1", "execute", "protocolized-resources", "--remote",
                       "--json", f"--command={command}")
    start = min((i for i in (out.find("["), out.find("{")) if i >= 0), default=-1)
    if start < 0:
        return []
    data = json.loads(out[start:])
    if isinstance(data, dict):
        data = [data]
    return data[0]["results"] if data and data[0].get("results") else []


def get_resources(slug_filter=None, only_missing=True) -> list[dict]:
    base = "SELECT slug, title, authors, type, date FROM resources WHERE file LIKE '%.pdf'"
    if slug_filter:
        return d1(f"{base} AND slug = '{slug_filter}'")
    if only_missing:
        # banners not yet generated: thumbnail is null or still points to covers/
        return d1(f"{base} AND (thumbnail IS NULL OR thumbnail NOT LIKE '%/banners/%') ORDER BY slug")
    return d1(f"{base} ORDER BY slug")


def download_cover(slug: str) -> bytes:
    url = f"{CDN_BASE}/covers/{slug}.jpg"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.content


def upload_banner(local_bytes: bytes, slug: str) -> str:
    import tempfile
    key = f"{BANNER_PREFIX}/{slug}.jpg"
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(local_bytes)
        tmp_path = f.name
    try:
        run_wrangler("r2", "object", "put", f"{R2_BUCKET}/{key}",
                     "--file", tmp_path, "--content-type", "image/jpeg", "--remote")
    finally:
        os.unlink(tmp_path)
    return f"{CDN_BASE}/{key}"


def update_thumbnail(slug: str, url: str) -> None:
    run_wrangler("d1", "execute", "protocolized-resources", "--remote",
                 f"--command=UPDATE resources SET thumbnail = '{url}' WHERE slug = '{slug}'")


def process(row: dict) -> bool:
    slug = row["slug"]
    title = row["title"]
    authors = json.loads(row["authors"]) if isinstance(row["authors"], str) else row["authors"]
    resource_type = row["type"]
    year = row["date"][:4]

    print(f"  fetching cover ...", end=" ", flush=True)
    cover_bytes = download_cover(slug)
    print(f"{len(cover_bytes)//1024} KB", flush=True)

    print(f"  compositing ...", end=" ", flush=True)
    banner_bytes = make_banner(cover_bytes, title, authors, resource_type, year)
    print(f"{len(banner_bytes)//1024} KB", flush=True)

    print(f"  uploading to R2 ...", end=" ", flush=True)
    cdn_url = upload_banner(banner_bytes, slug)
    print(f"ok → {cdn_url}", flush=True)

    print(f"  updating D1 thumbnail ...", end=" ", flush=True)
    update_thumbnail(slug, cdn_url)
    print("ok", flush=True)

    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Regenerate even if banner exists")
    parser.add_argument("--slug", help="Process a single resource by slug")
    args = parser.parse_args()

    os.environ["CLOUDFLARE_API_TOKEN"] = load_token()

    rows = get_resources(slug_filter=args.slug, only_missing=not args.all)
    if not rows:
        print("Nothing to process.")
        return

    print(f"Processing {len(rows)} resource(s)...\n")
    ok = err = 0

    for row in rows:
        print(f"[{row['slug']}]")
        try:
            process(row)
            ok += 1
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            err += 1
        print()

    print(f"Done. {ok} succeeded, {err} failed.")


if __name__ == "__main__":
    main()
