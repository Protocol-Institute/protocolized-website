#!/usr/bin/env python3
"""
Sync Substack post enrichments from c3po → resource Markdown files.

Joins two c3po sources:
  sources/substack/enriched_meta.json  — summary, categories, primary_author
  sources/substack/api_metadata.json   — title, date, section, bylines

For each post in enriched_meta:
  - Resource Markdown exists → UPDATE description, type, authors, tags
  - No Markdown yet         → CREATE new stub

Posts with no api_metadata entry (16 older export posts) get date: 1970-01-01
as a sentinel for later cleanup (run fetch_api_metadata.py in c3po first).

After running:
    python3 scripts/migrate-to-d1.py --remote

Usage:
    python3 scripts/sync-substack-resources.py
    python3 scripts/sync-substack-resources.py --dry-run
    python3 scripts/sync-substack-resources.py --slug some-slug
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
C3PO_ROOT = REPO_ROOT.parent / "c3po"
ENRICHED_META  = C3PO_ROOT / "sources" / "substack" / "enriched_meta.json"
API_META       = C3PO_ROOT / "sources" / "substack" / "api_metadata.json"
RESOURCES_DIR  = REPO_ROOT / "src" / "content" / "resources"

SUBSTACK_BASE = "https://protocolized.summerofprotocols.com"

SECTION_TYPE = {
    "Articles":     "article",
    "Fictions":     "fiction",
    "Obliquities":  "article",
    "Protocolized": "article",
}

CATEGORY_TAGS = {
    "protocol-theory":   "protocols",
    "protocol-watching": "protocol-watching",
    "protocol-fiction":  "fiction",
    "governance":        "governance",
    "technology-ai":     "technology",
    "research-report":   "research",
    "memory-archival":   "memory",
    "organizations":     "organizations",
    "interview":         "interview",
    "editorial":         "editorial",
}
SKIP_CATEGORIES = {"announcement"}

SENTINEL_DATE = "1970-01-01"

WRANGLER  = REPO_ROOT / "worker" / "node_modules" / ".bin" / "wrangler"
ENV_KEYS  = REPO_ROOT.parent / ".env.keys"
R2_BUCKET = "protocolized-resources"


def yaml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")[:80]


def map_type(section: str) -> str:
    return SECTION_TYPE.get(section, "article")


def map_tags(categories: list[str], section: str) -> list[str]:
    tags = set()
    for cat in categories:
        if cat in CATEGORY_TAGS:
            tags.add(CATEGORY_TAGS[cat])
        elif cat not in SKIP_CATEGORIES:
            tags.add(cat)
    # section-derived tags
    if section == "Fictions":
        tags.add("fiction")
    elif section == "Obliquities":
        tags.add("obliquities")
    tags.add("protocols")
    return sorted(tags)


def resolve_authors(enriched: dict, api: dict) -> list[str]:
    """Return resolved author name(s), preferring enriched_meta's alias-resolved names."""
    all_authors = enriched.get("all_authors") or []
    if all_authors and all_authors != ["Protocolized"]:
        return all_authors
    # Fall back to api bylines
    bylines = api.get("publishedBylines") or []
    names = [b.get("name", "") for b in bylines if b.get("name")]
    return names if names else ["Protocolized"]


# ── Targeted YAML field updates ───────────────────────────────────────────────

def update_field(text: str, key: str, new_value: str) -> str:
    """Replace a simple scalar field value."""
    return re.sub(
        rf'^({re.escape(key)}:\s*).*$',
        rf'\g<1>{new_value}',
        text, count=1, flags=re.MULTILINE,
    )


def update_authors_block(text: str, authors: list[str]) -> str:
    """Replace the authors: block."""
    new_block = "authors:\n" + "".join(f"  - name: {yaml_str(a)}\n" for a in authors)
    # Match existing authors block (key + indented lines)
    return re.sub(
        r"^authors:\s*\n(?:[ \t]+-[ \t]*.+\n(?:[ \t]+\w.+\n)*)+",
        new_block,
        text, count=1, flags=re.MULTILINE,
    )


def update_tags_block(text: str, extra_tags: list[str]) -> str:
    """Merge extra_tags into existing tags block."""
    m = re.search(r"^(tags:\s*\n)((?:[ \t]*-[ \t]*.+\n)+)", text, re.MULTILINE)
    if not m:
        return text
    existing = set(t.strip() for t in re.findall(r"^[ \t]*-[ \t]*(.+)", m.group(2), re.MULTILINE))
    merged = sorted(existing | set(extra_tags))
    new_block = "tags:\n" + "".join(f"  - {t}\n" for t in merged)
    return text[:m.start()] + new_block + text[m.end():]


# ── Full Markdown generation (new files) ──────────────────────────────────────

def make_markdown(slug: str, enriched: dict, api: dict) -> str:
    section = api.get("section_name", "")
    title   = api.get("title") or slug
    date    = (api.get("post_date") or "")[:10] or SENTINEL_DATE
    subtitle = api.get("subtitle") or ""
    authors = resolve_authors(enriched, api)
    resource_type = map_type(section)
    description   = enriched.get("summary", "")
    tags  = map_tags(enriched.get("categories", []), section)
    url   = f"{SUBSTACK_BASE}/p/{slug}"

    lines = [
        "---",
        f"title: {yaml_str(title)}",
        f"type: {resource_type}",
        "authors:",
    ]
    for a in authors:
        lines.append(f"  - name: {yaml_str(a)}")
    lines.append(f"date: {date}")
    if description:
        lines.append(f"description: {yaml_str(description)}")
    else:
        lines.append(f'description: "A post from the Protocolized magazine."')
    lines += ["tags:"] + [f"  - {t}" for t in tags]
    lines += [
        "audience:",
        "  - researcher",
        "  - practitioner",
        "featured: false",
        f"url: {yaml_str(url)}",
        "---",
        "",
    ]
    return "\n".join(lines)


# ── Existing file update ──────────────────────────────────────────────────────

def update_existing(path: Path, slug: str, enriched: dict, api: dict) -> tuple[str, str]:
    """
    Update description, type, authors, tags in an existing resource file.
    Returns (original_text, updated_text).
    """
    original = path.read_text(encoding="utf-8")
    text = original

    summary = enriched.get("summary", "").strip()
    if summary:
        text = update_field(text, "description", yaml_str(summary))

    section = api.get("section_name", "")
    new_type = map_type(section)
    text = update_field(text, "type", new_type)

    authors = resolve_authors(enriched, api)
    text = update_authors_block(text, authors)

    extra_tags = map_tags(enriched.get("categories", []), section)
    text = update_tags_block(text, extra_tags)

    return original, text


# ── Main ──────────────────────────────────────────────────────────────────────

def load_token() -> str:
    if t := os.environ.get("CLOUDFLARE_API_TOKEN"):
        return t
    if ENV_KEYS.exists():
        for line in ENV_KEYS.read_text().splitlines():
            if line.startswith("CLOUDFLARE_API_TOKEN="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("CLOUDFLARE_API_TOKEN not found")


def query_d1(command: str) -> list[dict]:
    env = {**os.environ, "CLOUDFLARE_API_TOKEN": os.environ["CLOUDFLARE_API_TOKEN"]}
    result = subprocess.run(
        [str(WRANGLER), "d1", "execute", "protocolized-resources",
         "--remote", "--json", f"--command={command}"],
        capture_output=True, text=True, env=env,
        cwd=str(REPO_ROOT / "worker"),
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip()[:200])
    out = result.stdout
    start = min((i for i in (out.find("["), out.find("{")) if i >= 0), default=-1)
    if start < 0:
        return []
    data = json.loads(out[start:])
    if isinstance(data, dict):
        data = [data]
    return data[0].get("results", []) if data else []


def make_markdown_from_d1(row: dict) -> str:
    """Create a resource stub from a D1 posts row (no enrichment available)."""
    slug    = row["slug"]
    title   = row.get("title", slug)
    date    = row.get("date", SENTINEL_DATE) or SENTINEL_DATE
    section = row.get("section", "Protocolized")
    author  = row.get("primary_author", "Protocolized")
    summary = row.get("summary") or ""
    resource_type = map_type(section)
    tags = map_tags([], section)
    url  = f"{SUBSTACK_BASE}/p/{slug}"

    lines = [
        "---",
        f"title: {yaml_str(title)}",
        f"type: {resource_type}",
        "authors:",
        f"  - name: {yaml_str(author)}",
        f"date: {date}",
        f"description: {yaml_str(summary) if summary else '\"A post from the Protocolized magazine.\"'}",
        "tags:",
    ] + [f"  - {t}" for t in tags] + [
        "audience:",
        "  - researcher",
        "  - practitioner",
        "featured: false",
        f"url: {yaml_str(url)}",
        "---",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--slug", help="Process a single slug only")
    args = parser.parse_args()

    for p in (ENRICHED_META, API_META):
        if not p.exists():
            print(f"ERROR: {p} not found", file=sys.stderr)
            sys.exit(1)

    enriched_all: dict = json.loads(ENRICHED_META.read_text())
    api_raw = json.loads(API_META.read_text())
    api_all: dict = (
        {p["slug"]: p for p in api_raw} if isinstance(api_raw, list) else api_raw
    )

    print(f"enriched_meta: {len(enriched_all)} posts")
    print(f"api_metadata:  {len(api_all)} posts")

    # Build library index: slug → path (for all existing resources)
    library: dict[str, Path] = {f.stem: f for f in RESOURCES_DIR.glob("*.md")}
    # Subset that are Substack articles/fiction (have a Substack url)
    substack_re = re.compile(r'url:\s*"https://protocolized\.summerofprotocols\.com/p/')
    substack_slugs = {
        slug for slug, path in library.items()
        if substack_re.search(path.read_text(encoding="utf-8"))
    }
    print(f"Existing Substack resource files: {len(substack_slugs)}")

    target_slugs = (
        [args.slug] if args.slug
        else sorted(enriched_all.keys())
    )

    existing_slugs_all = {f.stem for f in RESOURCES_DIR.glob("*.md")}
    created = updated = unchanged = 0

    for slug in target_slugs:
        enriched = enriched_all.get(slug, {})
        api      = api_all.get(slug, {})

        if slug in substack_slugs:
            # UPDATE existing file
            path = library[slug]
            original, updated_text = update_existing(path, slug, enriched, api)
            if updated_text == original:
                unchanged += 1
                continue
            section = api.get("section_name", "?")
            print(f"  [UPDATE] {slug[:60]:<60} [{section}]")
            if not args.dry_run:
                path.write_text(updated_text, encoding="utf-8")
            updated += 1

        elif slug not in existing_slugs_all:
            # CREATE new file
            md = make_markdown(slug, enriched, api)
            path = RESOURCES_DIR / f"{slug}.md"
            section = api.get("section_name", "unknown")
            date = (api.get("post_date") or "")[:10] or SENTINEL_DATE
            print(f"  [CREATE] {slug[:60]:<60} [{section}] {date}")
            if not args.dry_run:
                path.write_text(md, encoding="utf-8")
                existing_slugs_all.add(slug)
            created += 1

        else:
            # Slug exists as a non-Substack resource (e.g. a PDF resource with same name) — skip
            print(f"  [SKIP]   {slug} — exists as non-Substack resource")

    # ── D1 fallback: posts in D1 not in enriched_meta ────────────────────────
    if not args.slug:
        print("\nChecking D1 posts table for any not in enriched_meta...")
        try:
            os.environ["CLOUDFLARE_API_TOKEN"] = load_token()
            d1_posts = query_d1(
                "SELECT slug, title, date, section, primary_author, summary "
                "FROM posts WHERE is_placeholder IS NULL OR is_placeholder=0 "
                "ORDER BY date DESC"
            )
            enriched_slugs = set(enriched_all.keys())
            for row in d1_posts:
                slug = row["slug"]
                if slug in enriched_slugs:
                    continue  # already handled above
                if slug in substack_slugs or slug in existing_slugs_all:
                    continue  # already in library
                section = row.get("section", "")
                date = row.get("date", SENTINEL_DATE) or SENTINEL_DATE
                print(f"  [CREATE] {slug[:60]:<60} [D1-only/{section}] {date}")
                if not args.dry_run:
                    md = make_markdown_from_d1(row)
                    path = RESOURCES_DIR / f"{slug}.md"
                    path.write_text(md, encoding="utf-8")
                    existing_slugs_all.add(slug)
                created += 1
        except Exception as e:
            print(f"  D1 query failed (skipping fallback): {e}")

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}Done.")
    print(f"  Created: {created}  Updated: {updated}  Unchanged: {unchanged}")
    if not args.dry_run and (created or updated):
        print(f"\nNext: python3 scripts/migrate-to-d1.py --remote")


if __name__ == "__main__":
    main()
