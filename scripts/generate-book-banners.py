#!/usr/bin/env python3
"""
Generate 1200×600 banner composites for books.

Layout: teal left panel with book cover | surface right panel with title + editor.
Uploads to R2 at banners/books/{slug}.jpg and updates D1 books.banner.

Usage:
    python3 scripts/generate-book-banners.py            # all books with covers, missing banners
    python3 scripts/generate-book-banners.py --all      # regenerate all
    python3 scripts/generate-book-banners.py --slug foo # single book
"""

import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO_ROOT = Path(__file__).parent.parent
WRANGLER = REPO_ROOT / "worker" / "node_modules" / ".bin" / "wrangler"
ENV_KEYS = REPO_ROOT.parent / ".env.keys"
R2_BUCKET = "protocolized-resources"
CDN_BASE = "https://files.protocolized.io"
BANNER_PREFIX = "banners/books"

W, H = 1200, 600
COVER_PANEL_W = 390
TEXT_X = COVER_PANEL_W + 56
TEXT_MAX_W = W - TEXT_X - 56
MAX_TITLE_LINES = 4

TEAL       = (15, 110, 86)
SURFACE    = (249, 248, 245)
DARK       = (44, 44, 42)
SECONDARY  = (110, 110, 108)

FONT_GEORGIA_REG  = "/System/Library/Fonts/Supplemental/Georgia.ttf"
FONT_GEORGIA_ITAL = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"
FONT_SANS         = "/Library/Fonts/Calibri.ttf"


def load_fonts():
    return {
        "badge":    ImageFont.truetype(FONT_SANS,         13),
        "title":    ImageFont.truetype(FONT_GEORGIA_REG,  40),
        "subtitle": ImageFont.truetype(FONT_GEORGIA_ITAL, 22),
        "editor":   ImageFont.truetype(FONT_GEORGIA_ITAL, 18),
        "meta":     ImageFont.truetype(FONT_SANS,         13),
        "mark":     ImageFont.truetype(FONT_SANS,         12),
    }


def wrap_text(text: str, draw, font, max_width: int, max_lines: int, shrink_sizes=(40, 34, 28)):
    for size in shrink_sizes:
        fnt = ImageFont.truetype(FONT_GEORGIA_REG, size)
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
    return lines[:max_lines], ImageFont.truetype(FONT_GEORGIA_REG, 28)


def make_banner(cover_bytes: bytes, title: str, subtitle: str | None,
                editor: str | None, category: str, year: str) -> bytes:
    fonts = load_fonts()
    canvas = Image.new("RGB", (W, H), SURFACE)
    draw = ImageDraw.Draw(canvas)

    # Left teal panel
    canvas.paste(Image.new("RGB", (COVER_PANEL_W, H), TEAL), (0, 0))

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

    shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.rectangle([cx + 6, cy + 6, cx + cw + 6, cy + ch + 6], fill=(0, 30, 20, 160))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=8))
    canvas = canvas.convert("RGBA")
    canvas.alpha_composite(shadow_layer)
    canvas = canvas.convert("RGB")

    canvas.paste(cover, (cx, cy))
    draw = ImageDraw.Draw(canvas)

    # Right panel accent line
    draw.rectangle([COVER_PANEL_W, 0, W - 1, 5], fill=TEAL)

    # Calculate text block height for vertical centering
    title_lines, title_font = wrap_text(title, draw, fonts["title"], TEXT_MAX_W, MAX_TITLE_LINES)
    line_h = int(title_font.size * 1.25)

    badge_h   = fonts["badge"].size
    badge_gap = 16
    title_h   = len(title_lines) * line_h

    sub_gap = 12
    sub_h   = int(fonts["subtitle"].size * 1.3) if subtitle else 0

    editor_gap = 20
    editor_h   = int(fonts["editor"].size * 1.4) if editor else 0

    total_h = badge_h + badge_gap + title_h
    if subtitle:
        total_h += sub_gap + sub_h
    if editor:
        total_h += editor_gap + editor_h

    start_y = (H - total_h) // 2

    # Badge
    badge = ("Nonfiction" if category == "nonfiction" else "Book").upper()
    draw.text((TEXT_X, start_y), badge, font=fonts["badge"], fill=TEAL)

    # Title
    ty = start_y + badge_h + badge_gap
    for line in title_lines:
        draw.text((TEXT_X, ty), line, font=title_font, fill=DARK)
        ty += line_h

    # Subtitle
    if subtitle:
        ty += sub_gap
        # wrap subtitle if needed
        sub_lines, sub_font = wrap_text(subtitle, draw, fonts["subtitle"], TEXT_MAX_W, 2,
                                        shrink_sizes=(22, 18, 16))
        sub_line_h = int(sub_font.size * 1.3)
        for line in sub_lines:
            draw.text((TEXT_X, ty), line, font=sub_font, fill=SECONDARY)
            ty += sub_line_h

    # Editor
    if editor:
        editor_text = f"Edited by {editor}" if category == "nonfiction" else editor
        draw.text((TEXT_X, ty + editor_gap), editor_text, font=fonts["editor"], fill=SECONDARY)

    draw.text((TEXT_X, H - 48), year, font=fonts["meta"], fill=SECONDARY)

    mark = "Protocolized"
    bb = draw.textbbox((0, 0), mark, font=fonts["mark"])
    mark_w = bb[2] - bb[0]
    draw.text((W - 48 - mark_w, H - 48), mark, font=fonts["mark"], fill=TEAL)

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=90, optimize=True)
    return buf.getvalue()


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


def get_books(slug_filter=None, only_missing=True) -> list[dict]:
    base = "SELECT slug, title, subtitle, editor, category, cover_image, date FROM books WHERE published = 1 AND cover_image IS NOT NULL"
    if slug_filter:
        return d1(f"{base} AND slug = '{slug_filter}'")
    if only_missing:
        return d1(f"{base} AND (banner IS NULL) ORDER BY sort_order")
    return d1(f"{base} ORDER BY sort_order")


def upload_banner(local_bytes: bytes, slug: str) -> str:
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


def update_banner(slug: str, url: str) -> None:
    run_wrangler("d1", "execute", "protocolized-resources", "--remote",
                 f"--command=UPDATE books SET banner = '{url}' WHERE slug = '{slug}'")


def process(row: dict) -> bool:
    slug     = row["slug"]
    title    = row["title"]
    subtitle = row.get("subtitle")
    editor   = row.get("editor")
    category = row.get("category", "fiction")
    year     = row["date"][:4]
    cover_url = row["cover_image"]

    print(f"  fetching cover ...", end=" ", flush=True)
    r = requests.get(cover_url, timeout=20)
    r.raise_for_status()
    cover_bytes = r.content
    print(f"{len(cover_bytes)//1024} KB", flush=True)

    print(f"  compositing ...", end=" ", flush=True)
    banner_bytes = make_banner(cover_bytes, title, subtitle, editor, category, year)
    print(f"{len(banner_bytes)//1024} KB", flush=True)

    print(f"  uploading to R2 ...", end=" ", flush=True)
    cdn_url = upload_banner(banner_bytes, slug)
    print(f"ok → {cdn_url}", flush=True)

    print(f"  updating D1 banner ...", end=" ", flush=True)
    update_banner(slug, cdn_url)
    print("ok", flush=True)

    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Regenerate even if banner exists")
    parser.add_argument("--slug", help="Process a single book by slug")
    args = parser.parse_args()

    os.environ["CLOUDFLARE_API_TOKEN"] = load_token()

    rows = get_books(slug_filter=args.slug, only_missing=not args.all)
    if not rows:
        print("Nothing to process.")
        return

    print(f"Processing {len(rows)} book(s)...\n")
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
