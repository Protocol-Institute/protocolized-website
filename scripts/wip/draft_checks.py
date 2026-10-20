"""
draft_checks.py — run a WIP project's checklist against the synced drafts.

The checklist itself (ids, labels, wording) lives in project.json under
"checklist", so the page, the manuscript and this checker share one text. This
module implements the items marked "auto": true. The rest are "manual" (the
editor checks them by reading) and are reported as such.

Statuses: pass · fail · warn (advisory item off target, or a link that couldn't
be verified) · manual · na (doesn't apply, e.g. no AI use mentioned).

Used by scripts/wip/check-drafts.py (standalone) and build-manuscript.py.
"""

from __future__ import annotations

import concurrent.futures as cf
import re
import unicodedata
import subprocess
from pathlib import Path

import fitz  # PyMuPDF

REFS_HEADING = re.compile(r"^(references|bibliography|works cited|sources|notes and (resources|references))\b", re.I)
BIO_HEADING = re.compile(r"^(about the authors?|author bios?|bios?|contributors?)\b", re.I)
AI_HEADING = re.compile(r"^ai assistance\b", re.I)
# A note about how the essay itself was written (not AI as the essay's subject).
AI_PROCESS = re.compile(
    r"(note on process|process note|writing coda|written with an ai|ai collaborator|"
    r"(co-authored|written|edited|drafted|prepared)( \w+)? with (chatgpt|claude|codex|gpt|gemini|copilot|an? (ai|coding agent|model))|"
    r"(chatgpt|claude|codex|gpt-?[\d.]+|gemini|copilot|coding agent)\b.{0,60}\b(drafted|assisted|helped|co-?authored|wrote|prepared|reorganised|reorganized) (this|the) (paper|essay|draft|piece|text))",
    re.I)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PLACEHOLDERS = [
    re.compile(r"(?<!\[)\[\s*(check|scene|cite|citation|ref|reference|source|insert|add|expand|fix|tk|todo|tbd|xx+|note to self)\b[^\]]*\]", re.I),
    re.compile(r"\[\s+[^\]\n]{3,120}?\s+\]"),                      # space-padded [ notes to self ]
    re.compile(r"\b(TODO|TBD|FIXME|XXX)\b"),
    re.compile(r"[(\[]\s*\*?(to verify|to be (completed|added|confirmed|written)|to add|placeholder)\b", re.I),
    re.compile(r"\*(to verify|to be (completed|added|confirmed))\*", re.I),
]
STATUS_LABELS = [
    re.compile(r"\bnot final\b", re.I),
    re.compile(r"\b(rough|initial|first) draft\b", re.I),
    re.compile(r"\bdraft (article|paper|version)\b", re.I),
    re.compile(r"\bdraft[ ,:]+(\d{4}-\d\d-\d\d|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}(, \d{4})?)", re.I),
]
AUTHOR_YEAR = re.compile(r"\(([A-Z][A-Za-z'’\-]+)(?:[^()]{0,60}?)\b((?:1[5-9]|20)\d\d)[a-z]?\b[^()]*\)")
URL = re.compile(r"https?://[^\s)\]>\"'<]+")
HEADING = re.compile(r"^(#{1,6})\s*(.*?)\s*#*\s*$")


# ── Text extraction ────────────────────────────────────────────────────────

def markdown_of(path: Path) -> str:
    if path.suffix == ".pdf":
        with fitz.open(path) as doc:
            return "\n".join(page.get_text() for page in doc)
    md = subprocess.run(["pandoc", str(path), "-t", "gfm", "--wrap=none"],
                        check=True, capture_output=True, text=True).stdout
    return md.replace("\\[", "[").replace("\\]", "]")


def plain(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    return re.sub(r"[*_`#>|]", "", s).strip()


def fold(s: str) -> str:
    """Lowercase and strip accents, so Schrödinger matches Schrodinger."""
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


MONTHS = {"january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december", "jan", "feb", "mar", "apr", "jun",
          "jul", "aug", "sep", "sept", "oct", "nov", "dec", "spring", "summer", "autumn", "fall", "winter"}


def strip_code(md: str) -> str:
    md = re.sub(r"```.*?```", "", md, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", md)


def headings(md: str) -> list[tuple[int, str, int]]:
    """(level, text, line index) for ATX headings; bold-only lines count as level-0 pseudo-headings."""
    out = []
    for i, line in enumerate(md.splitlines()):
        m = HEADING.match(line)
        if m:
            out.append((len(m.group(1)), plain(m.group(2)), i))
    return out


def pseudo_heading(md: str, pattern: re.Pattern) -> bool:
    """A heading-like line (ATX heading, or a short bold/plain line) matching pattern."""
    for line in md.splitlines():
        t = plain(line).rstrip(".:")
        if t and len(t) < 60 and pattern.match(t):
            return True
    return False


# ── Individual checks ──────────────────────────────────────────────────────

def r(status: str, detail: str = "") -> dict:
    return {"status": status, "detail": detail}


def split_refs(md: str) -> tuple[str, str]:
    """(body, references section) split at the first references-type heading line."""
    lines = md.splitlines()
    for i, line in enumerate(lines):
        t = plain(line).rstrip(".:")
        if t and len(t) < 40 and REFS_HEADING.match(t):
            return "\n".join(lines[:i]), "\n".join(lines[i + 1:])
    return md, ""


def check_title(md: str, is_pdf: bool) -> dict:
    if is_pdf:
        return r("manual", "PDF: check in the editable file")
    blocks = [ln for ln in md.splitlines() if ln.strip()][:3]
    for ln in blocks:
        m = HEADING.match(ln)
        if m:
            text = plain(m.group(2))
            if len(m.group(1)) == 1 and not re.match(r"^(abstract|introduction|\d)", text, re.I):
                return r("pass", text)
            return r("fail", f"First heading is “{text}” (level {len(m.group(1))}), not the title as Heading 1")
    return r("fail", "The file doesn't open with the title as Heading 1")


def check_byline(md: str, authors: list[str]) -> dict:
    head = plain(md[:2000]).lower()
    missing = []
    for a in authors:
        toks = [t for t in re.split(r"\s+", a) if len(t) > 1]
        key = (toks[-1] if toks else a).lower()
        if key not in head:
            missing.append(a)
    return r("fail", "Not named near the top: " + ", ".join(missing)) if missing else r("pass")


def check_talk_note(md: str) -> dict:
    return r("pass") if re.search(r"symposium", md[:2500], re.I) else r("fail", "No line naming the symposium talk")


def check_abstract(md: str) -> dict:
    lines = md.splitlines()
    for i, ln in enumerate(lines):
        t = plain(ln)
        if re.match(r"^abstract\b", t, re.I):
            rest = re.sub(r"^abstract[.:]?\s*", "", re.sub(r"\[\^\d+\]", "", t), flags=re.I)
            if len(rest.split()) < 4:
                rest = ""          # heading line, possibly with a footnote marker
            body = [rest] if rest else []
            for nxt in lines[i + 1:]:
                if HEADING.match(nxt) or re.match(r"^\W*keywords\b", plain(nxt), re.I):
                    break
                if not nxt.strip():
                    if body:
                        break          # end of the abstract paragraph
                    continue
                body.append(plain(nxt))
                if len(" ".join(body).split()) > 400:
                    break
            words = len(" ".join(body).split())
            if 100 <= words <= 200:
                return r("pass", f"{words} words")
            return r("warn", f"Abstract is {words} words (aim for 100–200)")
    return r("fail", "No abstract")


def check_bio(md: str) -> dict:
    return r("pass") if pseudo_heading(md, BIO_HEADING) else r("fail", "No “About the author” section")


def check_headings(md: str, is_pdf: bool) -> dict:
    if is_pdf:
        return r("manual", "PDF: check in the editable file")
    hs = headings(md)
    problems = []
    empty = [h for h in hs if not h[1]]
    if empty:
        problems.append(f"{len(empty)} empty heading(s)")
    h1 = [h for h in hs if h[0] == 1 and not REFS_HEADING.match(h[1])]
    if len(h1) > 1:
        problems.append(f"{len(h1)} Heading 1s (only the title should be Heading 1)")
    h2 = [h for h in hs if h[0] == 2 and h[1]]
    if len(h2) < 2:
        problems.append("sections aren't marked with Heading 2")
    return r("fail", "; ".join(problems)) if problems else r("pass", f"{len(h2)} sections")


def check_placeholders(md: str) -> dict:
    text = strip_code(md)
    hits = []
    for pat in PLACEHOLDERS:
        hits += [m.group(0).strip() for m in pat.finditer(text)]
    hits = list(dict.fromkeys(hits))
    if hits:
        shown = "; ".join(h if len(h) <= 60 else h[:59] + "…" for h in hits[:4])
        return r("fail", f"{len(hits)} found, e.g. {shown}")
    return r("pass")


def check_status_labels(md: str) -> dict:
    hits = list(dict.fromkeys(m.group(0) for pat in STATUS_LABELS for m in pat.finditer(md)))
    return r("fail", "Found: " + "; ".join(hits[:4])) if hits else r("pass")


def check_length(md: str) -> dict:
    body, _ = split_refs(md)
    words = len(plain(body).split())
    if 2500 <= words <= 7500:
        return r("pass", f"{words:,} words")
    return r("warn", f"{words:,} words (guideline 2,500–7,500)")


def check_references(md: str) -> dict:
    body, refs = split_refs(md)
    if not refs.strip():
        return r("fail", "No References section")
    refs_plain = fold(plain(refs))
    unmatched = []
    for m in AUTHOR_YEAR.finditer(plain(body)):
        name = m.group(1)
        if name.lower() in MONTHS | {"see", "cf", "e.g", "eg", "i.e", "ie", "in", "the", "and", "as", "since", "from", "c"}:
            continue
        if fold(name) not in refs_plain:
            unmatched.append(f"{name} {m.group(2)}")
    unmatched = list(dict.fromkeys(unmatched))
    if unmatched:   # heuristic (author-date only), so flag rather than fail
        return r("warn", "Possibly cited but not in References (check): " + ", ".join(unmatched[:6])
                 + (f" (+{len(unmatched) - 6} more)" if len(unmatched) > 6 else ""))
    entries = len([ln for ln in refs.splitlines() if plain(ln)])
    return r("pass", f"{entries} entries")


def check_links(md: str, cache: dict) -> dict:
    urls = list(dict.fromkeys(u.rstrip(".,;:*") for u in URL.findall(md)))
    if not urls:
        return r("na", "No links")
    todo = [u for u in urls if u not in cache]
    if todo:
        with cf.ThreadPoolExecutor(max_workers=12) as ex:
            for u, res in zip(todo, ex.map(probe, todo)):
                cache[u] = res
    dead = [u for u in urls if cache[u] == "dead"]
    unsure = [u for u in urls if cache[u] == "unsure"]
    if dead:
        return r("fail", f"{len(dead)} of {len(urls)} broken: " + " · ".join(dead[:3]))
    if unsure:
        return r("warn", f"{len(urls) - len(unsure)} of {len(urls)} verified; {len(unsure)} couldn't be checked automatically (blocked or slow)")
    return r("pass", f"{len(urls)} links")


def probe(url: str) -> str:
    import requests
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"}
    try:
        resp = requests.head(url, headers=headers, timeout=12, allow_redirects=True)
        if resp.status_code in (403, 405, 400, 429) or resp.status_code >= 500:
            resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True, stream=True)
        if resp.status_code < 400:
            return "ok"
        if resp.status_code in (404, 410):
            return "dead"
        return "unsure"
    except requests.exceptions.ConnectionError as e:
        return "dead" if "NameResolution" in str(e) or "Name or service" in str(e) else "unsure"
    except Exception:
        return "unsure"


OPEN_LICENSE = re.compile(r"\b(public domain|cc0|cc[ -]by(?:[ -]sa)?(?:[ -]\d\.\d)?|creative commons attribution(?:[- ]sharealike)?)\b", re.I)
CLOSED_LICENSE = re.compile(r"\b(cc[ -]by(?:[ -]sa)?[ -](nc|nd)|non-?commercial|no-?derivatives|all rights reserved|used with permission|fair use|getty|shutterstock|istock|alamy)\b", re.I)


def count_images(path: Path, md: str) -> int:
    if path.suffix == ".pdf":
        with fitz.open(path) as doc:
            return sum(len(page.get_images()) for page in doc)
    return len(re.findall(r"!\[|<img\b", md))


def check_image_rights(path: Path, md: str) -> dict:
    n = count_images(path, md)
    if n == 0:
        return r("na", "No images")
    closed = list(dict.fromkeys(m.group(0) for m in CLOSED_LICENSE.finditer(md)))
    if closed:
        return r("fail", f"Non-open terms found: {', '.join(closed[:3])}")
    stated = len(OPEN_LICENSE.findall(md))
    if stated < n:
        return r("fail", f"{n} image(s), {stated} open-license statement(s) found in the text")
    return r("pass", f"{n} image(s), each with an open license stated")


def check_editable(path: Path) -> dict:
    return r("fail", "Supplied as PDF only") if path.suffix == ".pdf" else r("pass", path.suffix.lstrip("."))


def check_contact(md: str) -> dict:
    emails = list(dict.fromkeys(EMAIL.findall(md)))
    return r("fail", f"{len(emails)} email address(es) in the text") if emails else r("pass")


def check_ai_note(md: str) -> dict:
    if pseudo_heading(md, AI_HEADING):
        return r("pass")
    m = AI_PROCESS.search(md)
    if m:
        return r("fail", "Has a process note (“" + m.group(0)[:60] + "”) but not in the standard “AI assistance” form")
    return r("na", "No AI assistance noted")


# ── Runner ─────────────────────────────────────────────────────────────────

def run_checks(project: dict, project_dir: Path, chapters: Path, check_links_online: bool = True,
               source_path=None) -> dict:
    """Return {entry id: {"results": {item: {status, detail}}, "summary": {...}}}."""
    items = project.get("checklist", [])
    link_cache: dict[str, str] = {}
    out = {}
    for e in project["contents"]:
        if e.get("checklist") is False:
            continue
        path = source_path(e, project_dir, chapters) if source_path else None
        if path is None:
            continue
        md = markdown_of(path)
        is_pdf = path.suffix == ".pdf"
        auto = {
            "title": lambda: check_title(md, is_pdf),
            "byline": lambda: check_byline(md, e["authors"]),
            "talk-note": lambda: check_talk_note(md),
            "abstract": lambda: check_abstract(md),
            "bio": lambda: check_bio(md),
            "headings": lambda: check_headings(md, is_pdf),
            "no-placeholders": lambda: check_placeholders(md),
            "no-status-labels": lambda: check_status_labels(md),
            "length": lambda: check_length(md),
            "references": lambda: check_references(md),
            "links": lambda: check_links(md, link_cache) if check_links_online else r("manual", "Link check skipped"),
            "image-rights": lambda: check_image_rights(path, md),
            "editable-source": lambda: check_editable(path),
            "no-contact": lambda: check_contact(md),
            "ai-note": lambda: check_ai_note(md),
        }
        results = {}
        for it in items:
            if it.get("auto") and it["id"] in auto:
                res = auto[it["id"]]()
                if it.get("advisory") and res["status"] == "fail":
                    res["status"] = "warn"
            else:
                res = r("manual", "Checked by the editor when reading")
            results[it["id"]] = res
        counts = {s: sum(1 for v in results.values() if v["status"] == s)
                  for s in ("pass", "fail", "warn", "manual", "na")}
        out[e["id"]] = {"results": results, "summary": {**counts, "ready": counts["fail"] == 0}}
    return out
