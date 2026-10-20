#!/opt/homebrew/bin/python3
"""
make-placeholder-cover.py — generate a placeholder cover for a work-in-progress project.

Reads wip/<slug>/project.json for title, subtitle and editor, draws a 1600×2400
cover in the site palette (teal field, a seeded node-and-edge mesh, a coral
"working draft" band) and writes wip/<slug>/build/cover.jpg. The mesh is seeded
by the slug, so each project gets its own pattern and reruns are stable.

With --upload, puts it on R2 at wip/<slug>/cover.jpg (served from
files.protocolized.io), the URL project.json's "cover" field points at.

Usage:
  python3 scripts/wip/make-placeholder-cover.py protocol-reader-vol-2
  python3 scripts/wip/make-placeholder-cover.py protocol-reader-vol-2 --upload
"""

import argparse
import hashlib
import json
import random
import subprocess
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
WIP_ROOT = REPO_ROOT / "wip"
FONT_CACHE = REPO_ROOT / "scripts" / "wip" / ".fonts"
WRANGLER = REPO_ROOT / "worker" / "node_modules" / ".bin" / "wrangler"
R2_BUCKET = "protocolized-resources"

W, H = 1600, 2400
TEAL = (15, 110, 86)
TEAL_DEEP = (10, 78, 61)
TEAL_LIGHT = (225, 245, 238)
CORAL = (216, 90, 48)
SURFACE = (249, 248, 245)

# Site display fonts (OFL), fetched once into a gitignored cache.
FONT_URLS = {
    "InstrumentSerif-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/instrumentserif/InstrumentSerif-Regular.ttf",
    "InstrumentSerif-Italic.ttf": "https://github.com/google/fonts/raw/main/ofl/instrumentserif/InstrumentSerif-Italic.ttf",
}
FALLBACKS = {
    "InstrumentSerif-Regular.ttf": "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "InstrumentSerif-Italic.ttf": "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
}
SANS = "/System/Library/Fonts/Supplemental/Arial.ttf"
SANS_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def font_path(name: str) -> str:
    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    p = FONT_CACHE / name
    if not p.exists():
        try:
            urllib.request.urlretrieve(FONT_URLS[name], p)
        except Exception as e:  # offline: fall back to a system serif
            print(f"  font download failed ({e}); using {FALLBACKS[name]}", file=sys.stderr)
            return FALLBACKS[name]
    return str(p)


def draw_mesh(img: Image.Image, seed: str) -> None:
    """A loose protocol mesh: jittered grid nodes, short edges, a few hubs."""
    rng = random.Random(int(hashlib.sha256(seed.encode()).hexdigest(), 16))
    d = ImageDraw.Draw(img, "RGBA")
    step = 120
    nodes = []
    for gx in range(-1, W // step + 2):
        for gy in range(-1, H // step + 2):
            if rng.random() < 0.55:
                nodes.append((gx * step + rng.randint(-40, 40), gy * step + rng.randint(-40, 40)))
    for i, (x, y) in enumerate(nodes):
        near = sorted(nodes, key=lambda n: (n[0] - x) ** 2 + (n[1] - y) ** 2)[1:4]
        for nx, ny in near[: rng.randint(1, 3)]:
            d.line([(x, y), (nx, ny)], fill=(225, 245, 238, 38), width=2)
    for x, y in nodes:
        r = 9 if rng.random() < 0.08 else 4
        d.ellipse([x - r, y - r, x + r, y + r], fill=(225, 245, 238, 90 if r > 4 else 60))


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_cover(project: dict) -> Image.Image:
    img = Image.new("RGB", (W, H), TEAL)
    # Darker lower band behind the type block.
    ImageDraw.Draw(img).rectangle([0, int(H * 0.52), W, H], fill=TEAL_DEEP)
    draw_mesh(img, project["slug"])
    d = ImageDraw.Draw(img)

    serif = font_path("InstrumentSerif-Regular.ttf")
    serif_it = font_path("InstrumentSerif-Italic.ttf")
    f_kicker = ImageFont.truetype(SANS_BOLD, 34)
    f_title = ImageFont.truetype(serif, 190)
    f_vol = ImageFont.truetype(serif_it, 120)
    f_sub = ImageFont.truetype(serif_it, 56)
    f_editor = ImageFont.truetype(SANS, 40)
    f_band = ImageFont.truetype(SANS_BOLD, 28)

    x = 130
    max_w = W - 2 * x

    # Kicker
    d.text((x, 170), "PROTOCOL INSTITUTE", font=f_kicker, fill=TEAL_LIGHT)
    d.line([(x, 230), (x + 120, 230)], fill=CORAL, width=6)

    # Title: split "Protocol Reader: Volume 2" into title + volume line.
    title = project["title"]
    main, _, vol = title.partition(":")
    y = int(H * 0.56)
    for line in wrap(d, main.strip(), f_title, max_w):
        d.text((x, y), line, font=f_title, fill=SURFACE)
        y += 200
    if vol.strip():
        d.text((x, y), vol.strip(), font=f_vol, fill=TEAL_LIGHT)
        y += 160
    y += 30
    for line in wrap(d, project.get("subtitle", ""), f_sub, max_w):
        d.text((x, y), line, font=f_sub, fill=TEAL_LIGHT)
        y += 70

    if project.get("editor"):
        d.text((x, H - 230), f"Edited by {project['editor']}", font=f_editor, fill=SURFACE)

    # Working-draft pill, top right, level with the kicker.
    label = "WORKING DRAFT  ·  PLACEHOLDER COVER"
    lw = d.textlength(label, font=f_band)
    px, py = W - x - lw - 64, 150
    d.rounded_rectangle([px, py, px + lw + 64, py + 72], radius=36, fill=CORAL)
    d.text((px + 32, py + 16), label, font=f_band, fill=SURFACE)
    return img


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--upload", action="store_true", help="upload to R2 at wip/<slug>/cover.jpg")
    args = ap.parse_args()

    project_dir = WIP_ROOT / args.slug
    project = json.loads((project_dir / "project.json").read_text())
    out = project_dir / "build" / "cover.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    make_cover(project).save(out, "JPEG", quality=88, optimize=True)
    print(f"Wrote {out.relative_to(REPO_ROOT)}")

    if args.upload:
        key = f"{R2_BUCKET}/wip/{args.slug}/cover.jpg"
        subprocess.run(
            [str(WRANGLER), "r2", "object", "put", key, f"--file={out}",
             "--content-type=image/jpeg", "--remote"],
            check=True, cwd=REPO_ROOT / "worker",
        )
        print(f"Uploaded → https://files.protocolized.io/wip/{args.slug}/cover.jpg")


if __name__ == "__main__":
    main()
