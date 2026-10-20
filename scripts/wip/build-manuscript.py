#!/opt/homebrew/bin/python3
"""
build-manuscript.py — fold updated drafts into a new versioned working manuscript.

A work-in-progress project lives in wip/<slug>/:

  project.json        Source of truth: metadata, contents (in TOC order), readiness
                      assessments, and the changelog. Edit the order of "contents" to
                      reorder the volume.
  sources.lock.json   Content hash of each draft as of the last published version.
                      Written by this script; how it knows what changed.
  <slug>.pdf          The latest compiled manuscript. The only manuscript in git, at a
                      stable path, so git history is how you rewind.
  intro.md etc.       Local chapters ("source": {"kind": "local"}).
  archive/versions/   Every published manuscript, <slug>-vX.Y.pdf (local only).
  archive/chapters/   Latest copy of each draft, synced from the Drive intake folder
                      (local only: the repo is public, contributors' drafts are not).
  build/              Previews and the cover (gitignored).

The Drive folder stays the intake: authors add and update drafts there.

What a run does:
  1. Syncs every draft from the Drive folder into archive/chapters/, and reports Drive
     files that no contents entry claims yet (new drafts are never pulled in on their
     own: add an entry to project.json).
  2. Hashes each draft's *text* (docx → pandoc text, pdf → extracted text). Google Docs
     exports are not byte-stable, so hashing the file itself would flag false changes.
  3. Compares against sources.lock.json. Nothing changed → stops, unless --force.
  4. Renders each chapter (docx/md via pandoc → HTML → WeasyPrint; PDFs inserted as-is,
     each behind an opener page), then front matter (cover, title page with the
     changelog note, contents with page numbers and readiness, added/updated lists),
     merges, stamps a running footer and page numbers, adds bookmarks, and redacts
     email addresses.
  5. With --publish --message "…":
       - saves archive/versions/<slug>-vX.Y.pdf and replaces <slug>.pdf,
       - uploads to R2 at wip/<slug>/<slug>-vX.Y.pdf,
       - records the version in project.json, with the message as its changelog entry,
         and rewrites the lock (readiness scores assessed against older text go stale),
       - commits exactly those files with the same message and pushes, which deploys
         the page, then deletes the previous version from R2. Only the latest is served.
     The commit message and the site changelog are the same text by construction.

Without --publish it writes build/<slug>-preview.pdf and changes nothing else.

Versions are 0.N while gathering drafts. 1.0 is reserved for the version judged
ready to move to editing; that call is a human one (set "stage" in project.json).

Usage:
  python3 scripts/wip/build-manuscript.py protocol-reader-vol-2              # preview
  python3 scripts/wip/build-manuscript.py protocol-reader-vol-2 --publish \
      --message "Added Humboldt's laws essay; Kronovet revision folded in"
  python3 scripts/wip/build-manuscript.py protocol-reader-vol-2 --no-fetch   # use synced copies
  python3 scripts/wip/build-manuscript.py protocol-reader-vol-2 --force      # rebuild with no changes

Requires: pandoc, weasyprint (CLI), PyMuPDF (fitz), Pillow, gdown.
"""

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
WIP_ROOT = REPO_ROOT / "wip"
FONT_CACHE = REPO_ROOT / "scripts" / "wip" / ".fonts"
WRANGLER = REPO_ROOT / "worker" / "node_modules" / ".bin" / "wrangler"
R2_BUCKET = "protocolized-resources"
FILES_BASE = "https://files.protocolized.io"
SITE = "https://protocolized.io"

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
MAX_IMAGE_PX = 1600  # figures are downscaled and heavy rasters re-encoded as JPEG


# ── Fetching ───────────────────────────────────────────────────────────────

def ext_of(name: str) -> str:
    return Path(name).suffix.lower() or ".docx"


def fetch_sources(project: dict, chapters: Path) -> None:
    import gdown

    src = project.get("source", {})
    if src.get("kind") != "gdrive-folder":
        return
    print("Listing Drive folder…")
    listing = gdown.download_folder(id=src["id"], skip_download=True, quiet=True) or []
    on_drive = {f.id: Path(f.path).name for f in listing}
    claimed = {e["source"]["id"] for e in project["contents"] if e["source"]["kind"] == "gdrive"}

    for fid, name in on_drive.items():
        if fid not in claimed:
            print(f"  NEW FILE not in contents (add an entry to include it): {name}  [{fid}]")
    for e in project["contents"]:
        s = e["source"]
        if s["kind"] != "gdrive":
            continue
        if s["id"] not in on_drive:
            print(f"  MISSING from folder (using last synced copy if present): {e['id']}")
            continue
        if on_drive[s["id"]] != s.get("name"):
            print(f"  renamed on Drive: {s.get('name')} → {on_drive[s['id']]}")
        out = chapters / f"{e['id']}{ext_of(on_drive[s['id']])}"
        for old in chapters.glob(f"{e['id']}.*"):
            if old != out:
                old.unlink()  # draft changed format (e.g. docx → pdf): keep only the latest
        gdown.download(id=s["id"], output=str(out), quiet=True)
        print(f"  synced {e['id']}")


def source_path(entry: dict, project_dir: Path, chapters: Path) -> Path | None:
    s = entry["source"]
    if s["kind"] == "local":
        return project_dir / s["path"]
    for ext in (ext_of(s.get("name", "")), ".docx", ".pdf"):
        p = chapters / f"{entry['id']}{ext}"
        if p.exists():
            return p
    return None


# ── Hashing ────────────────────────────────────────────────────────────────

def text_of(path: Path) -> str:
    if path.suffix == ".pdf":
        with fitz.open(path) as doc:
            return "\n".join(page.get_text() for page in doc)
    return subprocess.run(
        ["pandoc", str(path), "-t", "plain", "--wrap=none"],
        check=True, capture_output=True, text=True,
    ).stdout


def content_hash(path: Path) -> str:
    norm = re.sub(r"\s+", " ", text_of(path)).strip()
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


# ── Rendering ──────────────────────────────────────────────────────────────

def font_face_css() -> str:
    faces = []
    for fam, file, style in [
        ("Instrument Serif", "InstrumentSerif-Regular.ttf", "normal"),
        ("Instrument Serif", "InstrumentSerif-Italic.ttf", "italic"),
    ]:
        p = FONT_CACHE / file
        if p.exists():
            faces.append(f"@font-face {{ font-family: '{fam}'; font-style: {style}; src: url('file://{p}'); }}")
    return "\n".join(faces)


CSS = """
@page { size: Letter; margin: 0.9in 1in 1in 1in; }
html { font-family: Georgia, 'Times New Roman', serif; font-size: 10.5pt; line-height: 1.5; color: #2C2C2A; }
h1, h2, h3, h4 { font-family: 'Instrument Serif', Georgia, serif; font-weight: normal; line-height: 1.2; color: #2C2C2A; break-after: avoid; }
h1 { font-size: 24pt; margin: 0 0 0.4em; }
h2 { font-size: 16pt; margin: 1.4em 0 0.4em; }
h3 { font-size: 13pt; margin: 1.2em 0 0.3em; }
h4 { font-size: 11pt; margin: 1em 0 0.3em; }
p { margin: 0 0 0.7em; orphans: 2; widows: 2; }
a { color: #0F6E56; text-decoration: none; }
img { max-width: 100%; height: auto; }
figure { margin: 1em 0; break-inside: avoid; }
blockquote { margin: 1em 1.5em; color: #555; font-style: italic; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 1em 0; }
th, td { border: 0.5pt solid #ccc; padding: 4pt 6pt; vertical-align: top; text-align: left; }
th { background: #E1F5EE; }
code, pre { font-family: Menlo, monospace; font-size: 8.5pt; }
pre { white-space: pre-wrap; background: #F9F8F5; padding: 6pt; }
section.footnotes, aside.footnotes { font-size: 9pt; border-top: 0.5pt solid #ccc; margin-top: 2em; }

.opener { page: opener; height: 8.6in; display: flex; flex-direction: column; justify-content: center; }
.opener .num { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; letter-spacing: 0.15em; color: #D85A30; text-transform: uppercase; }
.opener .title { font-family: 'Instrument Serif', Georgia, serif; font-size: 32pt; line-height: 1.1; margin: 0.25em 0 0.3em; }
.opener .authors { font-size: 14pt; font-style: italic; margin-bottom: 2em; }
.meta { font-family: Helvetica, Arial, sans-serif; font-size: 9pt; color: #555; border-top: 0.75pt solid #0F6E56; padding-top: 0.8em; }
.meta div { margin: 0.25em 0; }
.score { display: inline-block; background: #0F6E56; color: white; border-radius: 3pt; padding: 0 5pt; font-weight: bold; }
.score.low { background: #D85A30; }
.after-opener { break-before: page; }

.titlepage { height: 8.6in; display: flex; flex-direction: column; justify-content: center; }
.titlepage h1 { font-size: 40pt; margin: 0; }
.titlepage .sub { font-family: 'Instrument Serif', Georgia, serif; font-style: italic; font-size: 18pt; color: #555; margin: 0.3em 0 1.5em; }
.titlepage .ed { font-size: 13pt; margin-bottom: 3em; }
.draftbox.changelog { border-color: #0F6E56; background: #E1F5EE; margin-bottom: 10pt; }
.draftbox { font-family: Helvetica, Arial, sans-serif; font-size: 9pt; border: 1pt solid #D85A30; padding: 8pt 10pt; color: #2C2C2A; }
.toc { width: 100%; border: none; font-size: 10pt; }
.toc td { border: none; border-bottom: 0.4pt dotted #bbb; padding: 4pt 2pt; }
.toc .part td { border: none; font-family: Helvetica, Arial, sans-serif; font-size: 8pt; letter-spacing: 0.12em; text-transform: uppercase; color: #0F6E56; padding-top: 12pt; }
.toc .pg, .toc .rd { text-align: right; white-space: nowrap; width: 3em; }
.toc .au { color: #555; font-style: italic; }
.changes { font-family: Helvetica, Arial, sans-serif; font-size: 9pt; }
.changes li { margin: 0.2em 0; }
.front { break-before: page; }
"""


def shrink_media(media_dir: Path) -> dict[str, str]:
    """Downscale figures and re-encode heavy rasters as JPEG. Returns {old path: new path}
    for files whose name changed, so the HTML can be rewritten to match."""
    renamed = {}
    for p in list(media_dir.rglob("*")):
        if p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}:
            continue
        try:
            with Image.open(p) as im:
                big = p.stat().st_size > 400_000
                if max(im.size) <= MAX_IMAGE_PX and not big:
                    continue
                im.thumbnail((MAX_IMAGE_PX, MAX_IMAGE_PX))
                if big:
                    rgb = Image.new("RGB", im.size, "white")
                    rgb.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[3])
                    new = p.with_suffix(".jpg") if p.suffix.lower() != ".jpg" else p
                    rgb.save(new, "JPEG", quality=82, optimize=True)
                    if new != p:
                        p.unlink()
                        renamed[str(p)] = str(new)
                else:
                    im.save(p)
        except Exception as e:
            print(f"    (could not shrink {p.name}: {e})")
    return renamed


def to_html_body(path: Path, workdir: Path) -> str:
    media = workdir / "media"
    out = subprocess.run(
        ["pandoc", str(path), "-t", "html5", "--wrap=none", f"--extract-media={media}"],
        check=True, capture_output=True, text=True, cwd=path.parent,
    ).stdout
    if media.exists():
        for old, new in shrink_media(media).items():
            out = out.replace(old, new)
    return EMAIL_RE.sub("[email removed]", out)


def render_pdf(html_doc: str, out: Path, workdir: Path) -> None:
    src = workdir / (out.stem + ".html")
    src.write_text(html_doc)
    subprocess.run(["weasyprint", "-q", "-u", str(workdir) + "/", str(src), str(out)], check=True)


def page_doc(body: str) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{font_face_css()}{CSS}</style></head><body>{body}</body></html>"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def authors_str(authors: list[str]) -> str:
    if len(authors) <= 2:
        return " and ".join(authors)
    return ", ".join(authors[:-1]) + ", and " + authors[-1]


def opener_html(n: int, e: dict, path: Path | None, stale: bool, changed: bool) -> str:
    r = e["readiness"]
    low = " low" if r["score"] <= 4 else ""
    rows = [f"<div><span class='score{low}'>{r['score']}/10</span>&nbsp; Readiness, assessed {esc(r['assessed'])}{' (draft has changed since)' if stale else ''}: {esc(r['note'])}</div>"]
    if e.get("talk"):
        rows.append(f"<div>Talk: <a href='{SITE}/resources/{e['talk']}'>{SITE.replace('https://', '')}/resources/{esc(e['talk'])}</a></div>")
    if e["source"]["kind"] == "gdrive":
        rows.append(f"<div>Source: {esc(e['source'].get('name', ''))}{' · updated in this version' if changed else ''}</div>")
    if path is None:
        rows.append("<div><b>Draft not available.</b></div>")
    label = "Introduction" if e["part"] == "front" else f"Chapter {n}"
    return (
        f"<div class='opener'><div class='num'>{label}</div>"
        f"<div class='title'>{esc(e['title'])}</div>"
        f"<div class='authors'>{esc(authors_str(e['authors']))}</div>"
        f"<div class='meta'>{''.join(rows)}</div></div>"
    )


def redact_emails(doc: fitz.Document) -> int:
    n = 0
    for page in doc:
        hits = [w for w in page.get_text("words") if EMAIL_RE.search(w[4])]
        for w in hits:
            page.add_redact_annot(fitz.Rect(w[:4]), text="[email removed]", fontsize=6)
            n += 1
        if hits:
            page.apply_redactions()
    return n


def stamp(doc: fitz.Document, front_count: int, label: str) -> None:
    """Running footer on every page but the cover; page numbers on body pages only."""
    for i in range(1, doc.page_count):
        page = doc[i]
        y = page.rect.height - 22
        page.insert_text((36, y), label, fontsize=7, fontname="helv", color=(0.45, 0.45, 0.45))
        if i >= front_count:
            num = str(i - front_count + 1)
            page.insert_text((page.rect.width - 36 - fitz.get_text_length(num, "helv", 8), y), num,
                             fontsize=8, fontname="helv", color=(0.25, 0.25, 0.25))


# ── Main ───────────────────────────────────────────────────────────────────

def next_version(project: dict) -> str:
    if not project["versions"]:
        return "0.1"
    major, minor = project["versions"][0]["version"].split(".")
    return f"{major}.{int(minor) + 1}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--no-fetch", action="store_true", help="use cached drafts, skip Drive")
    ap.add_argument("--force", action="store_true", help="build even if no draft changed")
    ap.add_argument("--publish", action="store_true",
                    help="archive, upload, record, commit and push this version")
    ap.add_argument("--message", default="",
                    help="changelog entry; also the git commit message (required with --publish)")
    ap.add_argument("--trailer", action="append", default=[],
                    help="git trailer for the commit only, e.g. 'Co-Authored-By: …' (repeatable)")
    ap.add_argument("--no-push", action="store_true", help="commit but don't push")
    args = ap.parse_args()
    if args.publish and not args.message.strip():
        ap.error("--publish needs --message: it is both the changelog entry and the commit message")

    project_dir = WIP_ROOT / args.slug
    pj_path = project_dir / "project.json"
    lock_path = project_dir / "sources.lock.json"
    project = json.loads(pj_path.read_text())
    lock = json.loads(lock_path.read_text()) if lock_path.exists() else {}
    chapters = project_dir / "archive" / "chapters"
    versions_dir = project_dir / "archive" / "versions"
    build = project_dir / "build"
    for d in (chapters, versions_dir, build):
        d.mkdir(parents=True, exist_ok=True)

    if not args.no_fetch:
        fetch_sources(project, chapters)

    # What changed since the last published version?
    paths, hashes, changed = {}, {}, []
    for e in project["contents"]:
        p = source_path(e, project_dir, chapters)
        paths[e["id"]] = p
        if p is None:
            print(f"  no draft for {e['id']}")
            continue
        hashes[e["id"]] = content_hash(p)
        if lock.get(e["id"], {}).get("hash") != hashes[e["id"]]:
            changed.append(e["id"])
    added = [i for i in changed if i not in lock]
    updated = [i for i in changed if i in lock]

    version = next_version(project)
    print(f"\n{len(changed)} of {len(project['contents'])} drafts new or changed since "
          f"{'v' + project['versions'][0]['version'] if project['versions'] else 'the start'}: "
          f"{', '.join(changed) or '—'}")
    if not changed and not args.force:
        print("Nothing to fold in. (Use --force to rebuild anyway.)")
        return

    today = dt.date.today().isoformat()
    vlabel = f"v{version}" if args.publish else f"preview of v{version}"
    footer = f"{project['title']} · working draft {vlabel} · {today} · not for citation or circulation"

    # 1. Chapters, each rendered to its own PDF.
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        chapter_pdfs = []
        n = 0
        for e in project["contents"]:
            if e["part"] != "front":
                n += 1
            p = paths[e["id"]]
            r = e["readiness"]
            stale = bool(r.get("assessed_hash")) and r["assessed_hash"] != hashes.get(e["id"])
            opener = opener_html(n, e, p, stale, e["id"] in changed)
            wd = tmp / e["id"]
            wd.mkdir()
            out = wd / "chapter.pdf"
            print(f"  rendering {e['id']}")
            if p is not None and p.suffix != ".pdf":
                body = to_html_body(p, wd)
                render_pdf(page_doc(opener + f"<div class='after-opener'>{body}</div>"), out, wd)
            else:
                render_pdf(page_doc(opener), out, wd)
                if p is not None:
                    with fitz.open(out) as doc, fitz.open(p) as src:
                        doc.insert_pdf(src)
                        doc.save(out.with_name("merged.pdf"))
                    out = out.with_name("merged.pdf")
            chapter_pdfs.append((e, out))

        # 2. Body = all chapters; record start pages (body pages are numbered from 1).
        body = fitz.open()
        starts = {}
        for e, pdf in chapter_pdfs:
            starts[e["id"]] = body.page_count + 1
            with fitz.open(pdf) as d:
                body.insert_pdf(d)

        # 3. Front matter, now that page numbers are known.
        parts = {p["id"]: p["title"] for p in project.get("parts", [])}
        toc_rows, cur_part, n = [], None, 0
        for e in project["contents"]:
            if e["part"] != cur_part:
                cur_part = e["part"]
                if parts.get(cur_part):
                    toc_rows.append(f"<tr class='part'><td colspan='4'>{esc(parts[cur_part])}</td></tr>")
            if e["part"] != "front":
                n += 1
            num = "" if e["part"] == "front" else f"{n}."
            mark = " •" if e["id"] in changed else ""
            toc_rows.append(
                f"<tr><td style='width:1.6em'>{num}</td><td>{esc(e['title'])}{mark}<br><span class='au'>{esc(authors_str(e['authors']))}</span></td>"
                f"<td class='rd'>{e['readiness']['score']}/10</td><td class='pg'>{starts[e['id']]}</td></tr>"
            )
        scores = [e["readiness"]["score"] for e in project["contents"]]
        names = {e["id"]: e["title"] for e in project["contents"]}
        history = "".join(
            f"<li><b>v{esc(v['version'])}</b> · {esc(v['date'])} · {esc(v.get('message', ''))}</li>"
            for v in project["versions"][:12]
        )
        def name_list(ids):
            return "".join(f"<li>{esc(names[i])} <span class='au'>({esc(authors_str(next(e['authors'] for e in project['contents'] if e['id'] == i)))})</span></li>" for i in ids)
        changelog_note = esc(args.message) if args.message else "Preview build: no changelog entry yet."
        front_html = f"""
<div class='titlepage'>
  <h1>{esc(project['title'])}</h1>
  <div class='sub'>{esc(project.get('subtitle', ''))}</div>
  <div class='ed'>Edited by {esc(project.get('editor', ''))}</div>
  <div class='draftbox changelog'><b>What changed in {esc(vlabel)}</b> · {today}<br>{changelog_note}</div>
  <div class='draftbox'><b>Working draft {esc(vlabel)}</b> · compiled {today}<br>
  A front-end working manuscript assembled from authors' drafts as they stand. Not edited,
  not for citation or circulation. Readiness scores (1 = placeholder stub, 10 = finished)
  are the compiler's rough assessment of each draft.<br>
  Project page: {SITE.replace('https://', '')}/wip/{esc(project['slug'])}</div>
</div>
<div class='front'>
  <h2>Contents</h2>
  <table class='toc'>{''.join(toc_rows)}</table>
  <p class='changes'>• new or updated in this version. Mean readiness {sum(scores) / len(scores):.1f}/10 across {len(scores)} pieces.</p>
</div>
<div class='front changes'>
  <h2>In this version</h2>
  <p>{changelog_note}</p>
  {f'<h3>Added</h3><ul>{name_list(added)}</ul>' if added else ''}
  {f'<h3>Updated</h3><ul>{name_list(updated)}</ul>' if updated else ''}
  {'' if changed else '<p>No draft changes (rebuild).</p>'}
  {f'<h3>Changelog</h3><ul>{history}</ul>' if history else ''}
</div>"""
        front_pdf = tmp / "front.pdf"
        render_pdf(page_doc(front_html), front_pdf, tmp)

        # 4. Assemble: cover image page + front matter + body.
        final = fitz.open()
        cover = build / "cover.jpg"
        if cover.exists():
            pg = final.new_page(width=612, height=792)
            pg.insert_image(pg.rect, filename=str(cover), keep_proportion=True)
        with fitz.open(front_pdf) as d:
            final.insert_pdf(d)
        front_count = final.page_count
        final.insert_pdf(body)

        stamp(final, front_count, footer)
        redacted = redact_emails(final)

        outline = [[1, "Contents", 2]]
        cur_part = None
        for e in project["contents"]:
            level = 1
            if parts.get(e["part"]):
                if e["part"] != cur_part:
                    outline.append([1, parts[e["part"]], front_count + starts[e["id"]]])
                level = 2
            cur_part = e["part"]
            outline.append([level, e["title"], front_count + starts[e["id"]]])
        final.set_toc(outline)
        final.set_metadata({"title": f"{project['title']} — working draft {vlabel}",
                            "author": project.get("editor", ""), "subject": project.get("subtitle", "")})

        fname = f"{args.slug}-v{version}.pdf" if args.publish else f"{args.slug}-preview.pdf"
        out_pdf = build / fname
        final.save(out_pdf, garbage=4, deflate=True)
        pages = final.page_count
        final.close()

    size_mb = out_pdf.stat().st_size / 1e6
    print(f"\nWrote {out_pdf.relative_to(REPO_ROOT)} · {pages} pages · {size_mb:.1f} MB"
          f"{f' · {redacted} email address(es) redacted' if redacted else ''}")

    if not args.publish:
        print("Preview only. Re-run with --publish to upload and record it as a version.")
        return

    # Archive every version locally; the stable-path copy is the one git tracks.
    shutil.copy2(out_pdf, versions_dir / fname)
    latest_pdf = project_dir / f"{args.slug}.pdf"
    shutil.copy2(out_pdf, latest_pdf)

    key = f"wip/{args.slug}/{fname}"
    wrangler(["r2", "object", "put", f"{R2_BUCKET}/{key}", f"--file={out_pdf}",
              "--content-type=application/pdf"])
    print(f"Uploaded → {FILES_BASE}/{key}")

    for e in project["contents"]:
        h = hashes.get(e["id"])
        r = e["readiness"]
        if h and not r.get("assessed_hash"):
            r["assessed_hash"] = h      # first sighting: the assessment was made against this text
        r["stale"] = bool(h and r.get("assessed_hash") and r["assessed_hash"] != h)
    superseded = [v["file"] for v in project["versions"] if v.get("file")]
    for v in project["versions"]:
        v["file"] = None                # only the latest version is served
    project["versions"].insert(0, {
        "version": version, "date": today, "file": f"{FILES_BASE}/{key}",
        "pages": pages, "added": added, "updated": updated, "message": args.message.strip(),
    })
    pj_path.write_text(json.dumps(project, indent=2, ensure_ascii=False) + "\n")
    lock_path.write_text(json.dumps(
        {i: {"hash": h, "version": version if i in changed else lock.get(i, {}).get("version", version)}
         for i, h in hashes.items()}, indent=2) + "\n")
    print(f"Recorded v{version} in project.json and sources.lock.json.")

    # Commit exactly these files, with the changelog entry as the message.
    tracked = [pj_path, lock_path, latest_pdf]
    msg = args.message.strip()
    if args.trailer:
        msg += "\n\n" + "\n".join(args.trailer)
    git(["add", "--", *map(str, tracked)])
    git(["commit", "-q", "-m", msg, "--", *map(str, tracked)])
    print("Committed: " + args.message.strip().splitlines()[0])
    if args.no_push:
        print("Not pushed (--no-push). Push to deploy, then delete the superseded R2 files by hand.")
        return
    git(["push", "-q", "origin", "HEAD"])
    print("Pushed; the Worker deploy updates the page.")

    for url in superseded:
        old_key = url.removeprefix(FILES_BASE + "/")
        if old_key != key:
            wrangler(["r2", "object", "delete", f"{R2_BUCKET}/{old_key}"])
            print(f"Removed superseded {url} (kept in archive/versions/)")


def wrangler(argv: list[str]) -> None:
    subprocess.run([str(WRANGLER), *argv, "--remote"], check=True, cwd=REPO_ROOT / "worker")


def git(argv: list[str]) -> None:
    subprocess.run(["git", *argv], check=True, cwd=REPO_ROOT)


if __name__ == "__main__":
    main()
