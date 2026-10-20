#!/usr/bin/env python3
"""
Sync the Protocol Symposium 2026 archive from c3po → resource pages.

The resource page is the canonical home of each symposium talk: the recording
link, the slides and papers, and the transcript. protocol-institute.org embeds the
video on its programme page and links here for the rest.

c3po builds the archive (ingest/archive_symposium.py): a manifest, one transcript
per recording, and the slide PDFs with email addresses already redacted. This
script owns the presentation of that data on protocolized.io:

  - uploads each slide file to R2 at symposium-2026/<file>, skipped when the CDN
    already serves identical bytes (so a revised deck is re-uploaded)
  - writes the body of each resource file: recording link, slides list, transcript
  - creates resource files for talks that have none yet (two late recordings, and
    talks with slides but no recording); existing frontmatter is left alone,
    except that a slides-only page whose recording arrived later gains `type: talk`,
    `url` and `thumbnail`

The body is regenerated on every run; edit c3po's data or this renderer, not the
Markdown. sync-youtube-resources.py preserves the body when it rewrites
frontmatter, so the two scripts do not undo each other.

After running, D1 is updated by the Sync Resources to D1 workflow on merge
(or manually: python3 scripts/migrate-to-d1.py --remote).

Usage:
    python3 scripts/sync-symposium-archive.py --dry-run
    python3 scripts/sync-symposium-archive.py
    python3 scripts/sync-symposium-archive.py --no-upload    # write Markdown only
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import date as Date
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).parent.parent
C3PO_ROOT = Path(os.environ.get("C3PO_ROOT", str(REPO_ROOT.parent / "c3po")))
ARCHIVE = C3PO_ROOT / "sources" / "symposium"
RESOURCES_DIR = REPO_ROOT / "src" / "content" / "resources"
WRANGLER = REPO_ROOT / "worker" / "node_modules" / ".bin" / "wrangler"
ENV_KEYS = REPO_ROOT.parent / ".env.keys"
R2_BUCKET = "protocolized-resources"
CDN_BASE = "https://files.protocolized.io"
R2_PREFIX = "symposium-2026"

CONTENT_TYPES = {"pdf": "application/pdf", "zip": "application/zip"}
DESCRIPTION_MAX = 600


def load_token() -> str:
    if os.environ.get("CLOUDFLARE_API_TOKEN"):
        return os.environ["CLOUDFLARE_API_TOKEN"]
    for line in ENV_KEYS.read_text().splitlines():
        if line.startswith("CLOUDFLARE_API_TOKEN="):
            return line.split("=", 1)[1].strip()
    sys.exit("CLOUDFLARE_API_TOKEN not set and not in ../.env.keys")


def yaml_str(s: str) -> str:
    return '"' + s.replace('"', "'").replace("\n", " ") + '"'


def split_frontmatter(text: str) -> tuple[str, str]:
    """(frontmatter block including both --- fences, body)."""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    return text[: end + 4], text[end + 4:]


# ── R2 ────────────────────────────────────────────────────────────────────────

def cdn_url(name: str) -> str:
    return f"{CDN_BASE}/{R2_PREFIX}/{name}"


def on_cdn(name: str, path: Path) -> bool:
    """True when the CDN already serves exactly this file.

    Speakers revise their decks; c3po rebuilds the PDF under the same name when
    the Drive file changes, and this re-uploads it. R2's ETag is the MD5 of a
    single-part upload, so it is compared directly — a revision that happens to
    keep the byte count is still caught. (files.protocolized.io does not cache
    at the edge, so an overwritten object is served new immediately.)"""
    if not path.exists():
        return False
    try:
        r = requests.head(cdn_url(name), timeout=10)
    except Exception:
        return False
    if r.status_code != 200:
        return False
    etag = r.headers.get("etag", "").strip('"')
    if etag and "-" not in etag:
        return etag == hashlib.md5(path.read_bytes()).hexdigest()
    return int(r.headers.get("content-length", -1)) == path.stat().st_size


def upload(path: Path, fmt: str, token: str, attempts: int = 3) -> bool:
    """wrangler r2 object put, retried: large PDFs hit transient fetch failures."""
    for attempt in range(1, attempts + 1):
        if _put(path, fmt, token, quiet=attempt < attempts):
            return True
        time.sleep(5 * attempt)
    return False


def _put(path: Path, fmt: str, token: str, quiet: bool) -> bool:
    result = subprocess.run(
        [str(WRANGLER), "r2", "object", "put", f"{R2_BUCKET}/{R2_PREFIX}/{path.name}",
         "--file", str(path), "--content-type", CONTENT_TYPES[fmt], "--remote"],
        capture_output=True, text=True, cwd=str(REPO_ROOT / "worker"),
        env={**os.environ, "CLOUDFLARE_API_TOKEN": token},
    )
    if result.returncode != 0 and not quiet:
        print(f"    wrangler error: {result.stderr.strip()[:160]}")
    return result.returncode == 0


def upload_thumbnail(video_id: str, token: str) -> str | None:
    """YouTube's own thumbnail, mirrored like sync-youtube-resources.py does."""
    import tempfile
    for size in ("maxresdefault", "hqdefault"):
        r = requests.get(f"https://img.youtube.com/vi/{video_id}/{size}.jpg", timeout=15)
        if r.ok and len(r.content) > 5000:      # placeholders are tiny
            break
    else:
        return None
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(r.content)
    try:
        result = subprocess.run(
            [str(WRANGLER), "r2", "object", "put", f"{R2_BUCKET}/covers/yt-{video_id}.jpg",
             "--file", f.name, "--content-type", "image/jpeg", "--remote"],
            capture_output=True, text=True, cwd=str(REPO_ROOT / "worker"),
            env={**os.environ, "CLOUDFLARE_API_TOKEN": token},
        )
    finally:
        os.unlink(f.name)
    return f"{CDN_BASE}/covers/yt-{video_id}.jpg" if result.returncode == 0 else None


# ── Rendering ─────────────────────────────────────────────────────────────────

def clock(sec: int) -> str:
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def long_date(iso: str | None) -> str:
    if not iso:
        return ""
    d = Date.fromisoformat(iso)
    return f"{d.strftime('%A, %B')} {d.day}, {d.year}"


def md_escape(text: str) -> str:
    """Caption text is plain speech; keep Markdown from reading it as markup."""
    return re.sub(r"([\\`*_\[\]<>#|])", r"\\\1", text)


def slide_line(s: dict, talk_titles: dict, multi: bool) -> str:
    label = s["title"]
    talk = talk_titles.get(s["talk"], "")
    if multi and talk and not talk.lower().startswith(" ".join(label.lower().split()[:2])):
        label = f"{talk}: {label}"
    if s.get("external_url"):
        return f"- [{label}]({s['external_url']}) (web page, hosted by the speaker)"
    if s["format"] == "zip":
        return f"- [{label}]({cdn_url(s['file'])}) (zip, supporting materials)"
    pages = f", {s['pages']} pages" if s.get("pages") else ""
    web = ""
    if s.get("how") == "web deck export":     # published by the speaker as a web deck
        web = f" · [web version]({s['source_url']})"
    return f"- [{label}]({cdn_url(s['file'])}) (PDF{pages}){web}"


def render_body(r: dict, transcript: dict | None, manifest: dict) -> str:
    out = []
    talk_titles = {}
    if transcript:
        talk_titles = {s["talk"]: s["title"] for s in transcript["sections"] if s.get("talk")}
    when = long_date(r.get("date"))
    programme = f"[{manifest['event']}]({manifest['programme_url']})"

    if r.get("video_url"):
        length = f" ({clock(r['duration_sec'])})" if r.get("duration_sec") else ""
        out.append(f"**Recording:** [Watch on YouTube]({r['video_url']}){length}  ")
    out.append(f"**Event:** {programme}" + (f", {when}" if when else ""))

    if len(talk_titles) > 1:
        out += ["", "This recording covers several items from the programme:", ""]
        for sec in transcript["sections"]:
            at = f"{r['video_url']}&t={sec['start']}s"
            out.append(f"- [{clock(sec['start'])}]({at}) {sec['title']}")

    if r["slides"]:
        out += ["", "## Slides and papers", ""]
        out += [slide_line(s, talk_titles, len(talk_titles) > 1) for s in r["slides"]]
        out += ["", "*Shared by the speakers for the symposium. Email addresses have been removed.*"]

    if transcript:
        out += ["", "## Transcript", "",
                "*YouTube's automatic captions, unedited, so names and technical terms are "
                "often misheard. Each timestamp opens the video at that moment.*"]
        sections = transcript["sections"]
        for sec in sections:
            if len(sections) > 1 and sec.get("title"):
                out += ["", f"### {sec['title']}"]
            for t, text in sec["paragraphs"]:
                out += ["", f"[{clock(t)}]({r['video_url']}&t={t}s) {md_escape(text)}"]
    return "\n".join(out) + "\n"


def new_frontmatter(r: dict, thumbnail: str | None) -> str:
    desc = re.sub(r"\s+", " ", r.get("description") or "").strip()
    if len(desc) > DESCRIPTION_MAX:
        desc = desc[: DESCRIPTION_MAX - 1].rsplit(" ", 1)[0] + "…"
    lines = ["---", f"title: {yaml_str(r['title'])}",
             f"type: {'talk' if r['kind'] == 'recording' else 'presentation'}", "authors:"]
    for name in r.get("speakers") or []:
        lines.append(f"  - name: {yaml_str(name)}")
    lines += [f"date: {r.get('date') or '2026-09-21'}", f"description: {yaml_str(desc)}",
              "tags:", "  - symposium-2026", "  - protocols",
              "audience:", "  - researcher", "featured: false"]
    if r.get("video_url"):
        lines.append(f"url: {yaml_str(r['video_url'])}")
        if thumbnail:
            lines.append(f"thumbnail: {yaml_str(thumbnail)}")
    else:
        first = next((s for s in r["slides"] if s.get("file")), None)
        if first:
            lines.append(f"file: {yaml_str(cdn_url(first['file']))}")
    lines.append("---")
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-upload", action="store_true", help="skip R2 uploads")
    args = ap.parse_args()

    manifest = json.loads((ARCHIVE / "archive.json").read_text())
    token = None if (args.dry_run or args.no_upload) else load_token()
    uploaded = present = created = updated = 0

    for slug, r in manifest["resources"].items():
        for s in r["slides"]:
            if not s.get("file"):
                continue
            path = ARCHIVE / "slides" / s["file"]
            if on_cdn(s["file"], path):
                present += 1
            elif args.dry_run or args.no_upload:
                print(f"  [UPLOAD?] {s['file']}")
            elif not path.exists():
                sys.exit(f"missing {path} — run c3po's ingest/archive_symposium.py on this machine")
            elif upload(path, s["format"], token):
                uploaded += 1
                print(f"  [UPLOAD] {s['file']}")
            else:
                sys.exit(f"upload failed: {s['file']}")

        transcript = None
        if r.get("transcript"):
            transcript = json.loads((ARCHIVE / r["transcript"]).read_text())
        body = render_body(r, transcript, manifest)

        def thumbnail_for(video_id: str) -> str | None:
            thumb = f"{CDN_BASE}/covers/yt-{video_id}.jpg"
            if requests.head(thumb, timeout=10).ok:
                return thumb
            return None if args.dry_run or args.no_upload else upload_thumbnail(video_id, token)

        md_path = RESOURCES_DIR / f"{slug}.md"
        if md_path.exists():
            fm, _ = split_frontmatter(md_path.read_text(encoding="utf-8"))
            action = "UPDATE"
            updated += 1
            if r.get("video_url") and not re.search(r"^url:", fm, re.M):
                # A slides-only page whose recording arrived later: c3po keeps the
                # page (same URL) and makes it the recording's page. Upgrade the
                # frontmatter in place; title, authors, description and the slides
                # file stay as they were.
                fm = re.sub(r"^type: presentation$", "type: talk", fm, count=1, flags=re.M)
                add = [f"url: {yaml_str(r['video_url'])}"]
                thumb = thumbnail_for(r["video_id"])
                if thumb and not re.search(r"^thumbnail:", fm, re.M):
                    add.append(f"thumbnail: {yaml_str(thumb)}")
                fm = fm.rstrip()
                assert fm.endswith("---")
                fm = fm[:-3].rstrip("\n") + "\n" + "\n".join(add) + "\n---"
                action = "UPGRADE"
        else:
            thumb = thumbnail_for(r["video_id"]) if r.get("video_id") else None
            fm = new_frontmatter(r, thumb)
            action = "ADD"
            created += 1
        text = f"{fm}\n\n{body}"
        if not args.dry_run:
            md_path.write_text(text, encoding="utf-8")
        size = len(text.encode())
        warn = "  ⚠ near D1's 100KB statement limit" if size > 90_000 else ""
        print(f"  [{action}] {slug[:60]:<60} {len(r['slides'])} file(s)  {size // 1024}KB{warn}")

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}Done. Updated {updated}  Added {created}"
          f"  Uploaded {uploaded}  Already on CDN {present}")
    if not args.dry_run:
        print("Next: commit; the Sync Resources to D1 workflow pushes to D1 on merge.")


if __name__ == "__main__":
    main()
