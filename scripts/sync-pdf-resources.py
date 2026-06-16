#!/usr/bin/env python3
"""
Sync PDF enrichment from c3po enriched_meta.json → resource Markdown files.

Reads c3po/sources/pdfs/enriched_meta.json (72 non-deprecated entries, each with
a Haiku-generated 2-sentence summary + categories). Cross-references against
existing resource Markdown files by the PDF basename in their file: URL field, then:
  - Updates description with c3po summary (replaces boilerplate)
  - Merges c3po categories (mapped to tag vocabulary) into existing tags
  - Leaves all other fields (authors, date, type, audience, file, url) untouched
  - Flags the 2 PDFs in enriched_meta with no matching resource file

Does NOT upload thumbnails (PDFs already have covers from generate-pdf-covers.py).
Does NOT touch dates or authors (those are already correct in the Markdown files).

After running, sync to D1 with:
    python3 scripts/migrate-to-d1.py --remote

Usage:
    python3 scripts/sync-pdf-resources.py
    python3 scripts/sync-pdf-resources.py --dry-run
    python3 scripts/sync-pdf-resources.py --slug some-slug   # single resource
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
C3PO_META = REPO_ROOT.parent / "c3po" / "sources" / "pdfs" / "enriched_meta.json"
RESOURCES_DIR = REPO_ROOT / "src" / "content" / "resources"

# Map c3po category vocab → resource tag vocab (same as YouTube sync)
CATEGORY_TAGS = {
    "protocol-theory":   "protocols",
    "protocol-watching": "protocol-watching",
    "protocol-fiction":  "fiction",
    "governance":        "governance",
    "technology-ai":     "technology",
    "research-report":   "research",
    "memory-archival":   "memory",
    "organizations":     "organizations",
    # pass-through tags (not in default vocab but valid to add)
    "interview":         "interview",
}
# categories we don't translate to tags
SKIP_CATEGORIES = {"announcement", "editorial"}


def map_categories(categories: list[str]) -> list[str]:
    tags = []
    for cat in categories:
        if cat in CATEGORY_TAGS:
            tags.append(CATEGORY_TAGS[cat])
        elif cat not in SKIP_CATEGORIES:
            # pass through unknown categories as-is (e.g. 'ai-adoption')
            tags.append(cat)
    return tags


def yaml_str(s: str) -> str:
    return '"' + s.replace('"', "'") + '"'


def update_description(text: str, new_desc: str) -> str:
    """Replace the description: field value in frontmatter."""
    new_line = f"description: {yaml_str(new_desc)}"
    updated = re.sub(
        r'^description:\s*".*?"',
        new_line,
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    if updated == text:
        # Unquoted or single-quoted — broader match
        updated = re.sub(
            r"^description:\s*.+$",
            new_line,
            text,
            count=1,
            flags=re.MULTILINE,
        )
    return updated


def update_tags(text: str, extra_tags: list[str]) -> str:
    """Merge extra_tags into the existing tags: block, preserving existing tags."""
    m = re.search(r"^(tags:\s*\n)((?:[ \t]*-[ \t]*.+\n)+)", text, re.MULTILINE)
    if not m:
        return text
    existing = set(
        t.strip() for t in re.findall(r"^[ \t]*-[ \t]*(.+)", m.group(2), re.MULTILINE)
    )
    merged = sorted(existing | set(extra_tags))
    new_block = "tags:\n" + "".join(f"  - {t}\n" for t in merged)
    return text[: m.start()] + new_block + text[m.end() :]


def build_library_index() -> dict[str, tuple[str, Path]]:
    """Returns {pdf_basename: (slug, path)} for all resources with a PDF file: field."""
    index = {}
    for f in RESOURCES_DIR.glob("*.md"):
        text = f.read_text(encoding="utf-8")
        m = re.search(r'^file:\s*"?(.+?\.pdf)"?\s*$', text, re.MULTILINE)
        if m:
            url = m.group(1).strip().strip('"')
            basename = url.split("/")[-1]
            index[basename] = (f.stem, f)
    return index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--slug", help="Process a single resource by slug")
    args = parser.parse_args()

    if not C3PO_META.exists():
        print(f"ERROR: enriched_meta.json not found at {C3PO_META}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {C3PO_META}...")
    raw = json.loads(C3PO_META.read_text())
    enrich_map = {k: v for k, v in raw.items() if not v.get("deprecated")}
    print(f"  {len(enrich_map)} non-deprecated PDF enrichments")

    print("Building library index...")
    library = build_library_index()
    print(f"  {len(library)} resources with PDF file fields")

    matched = set(enrich_map.keys()) & set(library.keys())
    unmatched = set(enrich_map.keys()) - set(library.keys())
    print(f"  Matched: {len(matched)}  Unmatched (no resource file): {len(unmatched)}")

    if unmatched:
        print("\nUnmatched PDFs (in c3po but not in resource library — needs manual entry):")
        for k in sorted(unmatched):
            v = enrich_map[k]
            print(f"  {k}")
            print(f"    summary: {v.get('summary', '')[:100]}...")
            print(f"    categories: {v.get('categories', [])}")

    updated = skipped = 0
    print()

    for basename in sorted(matched):
        slug, path = library[basename]
        if args.slug and slug != args.slug:
            continue

        enrich = enrich_map[basename]
        summary = enrich.get("summary", "").strip()
        new_tags = map_categories(enrich.get("categories", []))

        if not summary:
            print(f"  [SKIP] {slug} — no summary in enriched_meta")
            skipped += 1
            continue

        original = path.read_text(encoding="utf-8")
        updated_text = update_description(original, summary)
        updated_text = update_tags(updated_text, new_tags)

        if updated_text == original:
            print(f"  [SAME] {slug}")
            skipped += 1
            continue

        # Show what changed
        old_desc_m = re.search(r'^description:\s*"?(.+?)"?\s*$', original, re.MULTILINE)
        old_desc = old_desc_m.group(1).strip('"') if old_desc_m else ""
        print(f"  [UPDATE] {slug}")
        if old_desc != summary:
            print(f"    desc: {old_desc[:80]!r}")
            print(f"       → {summary[:80]!r}")
        if new_tags:
            print(f"    tags +: {new_tags}")

        if not args.dry_run:
            path.write_text(updated_text, encoding="utf-8")
        updated += 1

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}Done.")
    print(f"  Updated: {updated}  Unchanged: {skipped}")
    if not args.dry_run and updated:
        print(f"\nNext: python3 scripts/migrate-to-d1.py --remote")


if __name__ == "__main__":
    main()
