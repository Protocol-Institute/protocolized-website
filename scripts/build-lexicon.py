"""
Build src/data/lexicon.json from two sources:

  1. c3po/sources/lexicon_draft.json  — triage a/b terms extracted from PI corpus
  2. src/content/resources/protocol-lexicon.md — hand-curated existing lexicon page

Merging strategy:
  - All a/b triage terms from the corpus extraction are included.
  - All terms from the existing md page are included.
  - When a term appears in both, both definitions are stored; the hand-curated
    md definition is listed first (it's more polished).
  - Terms from the md page not in the corpus extraction are added with
    triage = "curated" (they were written by hand, not extracted by Haiku).

Usage:
    python3 scripts/build-lexicon.py
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT      = Path(__file__).parent.parent
C3PO_PATH = ROOT.parent / "c3po" / "sources" / "lexicon_draft.json"
MD_PATH   = ROOT / "src" / "content" / "resources" / "protocol-lexicon.md"
OUT_PATH  = ROOT / "src" / "data" / "lexicon.json"


# ── helpers ──────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def first_letter(term: str) -> str:
    ch = term.lstrip("*").strip()[0].upper()
    return ch if ch.isalpha() else "#"


# ── parse the existing protocol-lexicon.md ────────────────────────────────────

def parse_md_lexicon(md_text: str) -> dict[str, dict]:
    """
    Returns {normalized_term: {term, definition, source, source_slug}} for each
    term found in the md file.  Terms are bold (**term**) followed by definition
    then an italic source line (*Source: ...*).
    """
    terms = {}
    # Strip frontmatter
    body = re.sub(r"^---.*?---\s*", "", md_text, flags=re.S).strip()

    # Split on bold term markers — each entry starts with **term**
    # Allow for headers between entries
    blocks = re.split(r"\n(?=\*\*)", body)
    for block in blocks:
        block = block.strip()
        if not block.startswith("**"):
            continue
        # Term: first line, extract from **...**
        lines = block.split("\n")
        term_match = re.match(r"\*\*(.+?)\*\*", lines[0])
        if not term_match:
            continue
        term = term_match.group(1).strip()

        # Definition: lines between term and source, stripped of leading spaces
        defn_lines = []
        source_text = ""
        source_slug = None
        for line in lines[1:]:
            src_match = re.match(r"\*Source:\s*(.+?)\*", line.strip())
            if src_match:
                source_text = src_match.group(1).strip()
                break
            if line.strip():
                defn_lines.append(line.strip())

        definition = " ".join(defn_lines).strip()
        if not definition:
            continue

        # Try to guess source slug from source text
        # e.g. "Introduction to the Protocol Reader" → "introduction-to-the-protocol-reader"
        if source_text:
            source_slug = slugify(source_text)

        key = slugify(term)
        terms[key] = {
            "term": term,
            "definition": definition,
            "source": source_text,
            "source_slug": source_slug,
        }
    return terms


# ── load and filter corpus lexicon ───────────────────────────────────────────

def load_corpus_lexicon(path: Path) -> dict[str, dict]:
    raw = json.loads(path.read_text())
    return {k: v for k, v in raw.items() if v.get("triage") in ("a", "b")}


# ── merge ─────────────────────────────────────────────────────────────────────

def build_merged(corpus: dict, md: dict) -> list[dict]:
    seen_keys = set()
    entries = []

    TRIAGE_LABELS = {
        "a": "PI-coined",
        "b": "PI-specific",
        "curated": "Curated",
    }

    def make_entry(term_str, triage, definitions, context=""):
        key = slugify(term_str)
        return {
            "id":          key,
            "term":        term_str,
            "letter":      first_letter(term_str),
            "triage":      triage,
            "triage_label": TRIAGE_LABELS.get(triage, triage),
            "definitions": definitions,
            "context":     context,
        }

    # First pass: corpus terms (a/b) — they are the primary source
    for corpus_key, corpus_entry in corpus.items():
        term_str    = corpus_entry.get("term", corpus_key)
        slug_key    = slugify(term_str)
        triage      = corpus_entry.get("triage", "b")
        corpus_defn = corpus_entry.get("definition", "").strip()
        context     = corpus_entry.get("context", "").strip()
        corpus_src  = corpus_entry.get("source", "")
        corpus_slug = slugify(corpus_src) if corpus_src else None

        definitions = []

        # If this term is also in the hand-curated md, put md definition first
        if slug_key in md:
            md_entry = md[slug_key]
            definitions.append({
                "text":        md_entry["definition"],
                "source":      md_entry["source"],
                "source_slug": md_entry["source_slug"],
                "type":        "curated",
            })

        # Corpus definition
        if corpus_defn:
            definitions.append({
                "text":        corpus_defn,
                "source":      corpus_src,
                "source_slug": corpus_slug,
                "type":        "corpus",
            })

        seen_keys.add(slug_key)
        entries.append(make_entry(term_str, triage, definitions, context))

    # Second pass: md terms NOT in corpus — add as curated
    for md_key, md_entry in md.items():
        if md_key in seen_keys:
            continue
        term_str = md_entry["term"]
        definitions = [{
            "text":        md_entry["definition"],
            "source":      md_entry["source"],
            "source_slug": md_entry["source_slug"],
            "type":        "curated",
        }]
        seen_keys.add(md_key)
        entries.append(make_entry(term_str, "curated", definitions))

    # Sort alphabetically by term
    entries.sort(key=lambda e: e["term"].lower().lstrip("*").strip())
    return entries


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Loading corpus lexicon from {C3PO_PATH}")
    corpus = load_corpus_lexicon(C3PO_PATH)
    print(f"  {len(corpus)} a/b terms")

    print(f"Parsing existing md lexicon from {MD_PATH}")
    md_text = MD_PATH.read_text()
    md = parse_md_lexicon(md_text)
    print(f"  {len(md)} terms in md")

    entries = build_merged(corpus, md)

    counts = {}
    for e in entries:
        counts[e["triage"]] = counts.get(e["triage"], 0) + 1

    letters = sorted({e["letter"] for e in entries})

    output = {
        "meta": {
            "total":      len(entries),
            "pi_coined":  counts.get("a", 0),
            "pi_specific": counts.get("b", 0),
            "curated":    counts.get("curated", 0),
            "letters":    letters,
            "generated":  "2026-05-20",
        },
        "terms": entries,
    }

    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nWrote {len(entries)} terms to {OUT_PATH}")
    print(f"  PI-coined (a):   {counts.get('a', 0)}")
    print(f"  PI-specific (b): {counts.get('b', 0)}")
    print(f"  Curated (md):    {counts.get('curated', 0)}")
    print(f"  Letters covered: {' '.join(letters)}")


if __name__ == "__main__":
    main()
