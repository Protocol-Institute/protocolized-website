#!/usr/bin/env python3
"""
One-time migration: read all 288 Markdown resource files and import to D1.

Usage:
    # local (for dev/test):
    python3 scripts/migrate-to-d1.py

    # remote (production):
    python3 scripts/migrate-to-d1.py --remote
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RESOURCES_DIR = Path(__file__).parent.parent / "src" / "content" / "resources"
WRANGLER_TOML = Path(__file__).parent.parent / "worker" / "wrangler.toml"
DB_NAME = "protocolized-resources"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text)."""
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    fm_raw = text[3:end].strip()
    body = text[end + 3:].strip()
    fm = {}
    _parse_yaml_block(fm_raw, fm)
    return fm, body


def _parse_yaml_block(text: str, out: dict):
    """Minimal YAML parser for the resource frontmatter (no external deps)."""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.startswith("#"):
            i += 1
            continue
        indent = len(line) - len(line.lstrip())
        if indent > 0:
            i += 1
            continue  # nested handled below

        if ":" not in line:
            i += 1
            continue

        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()

        if rest == "" or rest == "|" or rest == ">":
            # block scalar or list — collect until next non-indented key
            items = []
            i += 1
            while i < len(lines):
                sub = lines[i]
                if not sub.strip():
                    i += 1
                    continue
                sub_indent = len(sub) - len(sub.lstrip())
                if sub_indent == 0 and ":" in sub:
                    break
                stripped = sub.strip().lstrip("- ").strip()
                if stripped:
                    # might be "- name: Foo" sub-dict
                    if ":" in stripped and not stripped.startswith('"') and not stripped.startswith("'"):
                        # sub-dict entry — for now just skip
                        pass
                    items.append(stripped)
                i += 1
            out[key] = items if items else ""
        elif rest.startswith("["):
            # inline list
            inner = rest.strip("[]")
            items = [v.strip().strip('"').strip("'") for v in inner.split(",") if v.strip()]
            out[key] = items
            i += 1
        elif rest.startswith("-"):
            # block list starting on same line (unusual but handle)
            out[key] = [rest.lstrip("- ").strip()]
            i += 1
        else:
            out[key] = rest.strip('"').strip("'")
            i += 1


def parse_resource_file(path: Path) -> dict | None:
    """Parse a .md resource file into a dict matching D1 schema."""
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    if not fm.get("title") or not fm.get("type"):
        print(f"  SKIP (missing title/type): {path.name}", file=sys.stderr)
        return None

    slug = path.stem

    # authors — handle list of dicts or list of strings
    raw_authors = fm.get("authors", [])
    authors = []
    if isinstance(raw_authors, list):
        for a in raw_authors:
            if isinstance(a, dict):
                authors.append(a)
            elif isinstance(a, str) and a:
                # Try to parse "name: Foo" / "url: bar" lines embedded as strings
                if a.startswith("name:"):
                    authors.append({"name": a[5:].strip().strip('"')})
                else:
                    authors.append({"name": a})
    elif isinstance(raw_authors, str) and raw_authors:
        authors.append({"name": raw_authors})

    # date
    date_val = str(fm.get("date", "2023-01-01")).strip()
    # normalize dates like "2023-12-13 00:00:00" → "2023-12-13"
    date_val = date_val.split()[0] if " " in date_val else date_val

    # tags / audience — ensure lists
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags] if tags else []
    audience = fm.get("audience", [])
    if isinstance(audience, str):
        audience = [audience] if audience else []

    featured = fm.get("featured", False)
    if isinstance(featured, str):
        featured = featured.lower() in ("true", "yes", "1")

    return {
        "slug": slug,
        "title": str(fm.get("title", "")).strip('"').strip("'"),
        "type": str(fm.get("type", "")).strip(),
        "authors": json.dumps(authors),
        "date": date_val,
        "description": str(fm.get("description", "")).strip('"').strip("'"),
        "tags": json.dumps(tags),
        "audience": json.dumps(audience),
        "featured": 1 if featured else 0,
        "file": fm.get("file") or None,
        "url": fm.get("url") or None,
        "thumbnail": fm.get("thumbnail") or None,
        "body": body if body else None,
    }


def sql_escape(v) -> str:
    if v is None:
        return "NULL"
    s = str(v)
    s = s.replace("'", "''")
    return f"'{s}'"


def build_sql(resources: list[dict]) -> str:
    lines = []
    for r in resources:
        cols = "slug, title, type, authors, date, description, tags, audience, featured, file, url, thumbnail, body"
        vals = ", ".join([
            sql_escape(r["slug"]),
            sql_escape(r["title"]),
            sql_escape(r["type"]),
            sql_escape(r["authors"]),
            sql_escape(r["date"]),
            sql_escape(r["description"]),
            sql_escape(r["tags"]),
            sql_escape(r["audience"]),
            str(r["featured"]),
            sql_escape(r["file"]),
            sql_escape(r["url"]),
            sql_escape(r["thumbnail"]),
            sql_escape(r["body"]),
        ])
        lines.append(
            f"INSERT OR REPLACE INTO resources ({cols}) VALUES ({vals});"
        )
    return "\n".join(lines)


def run_wrangler(sql_path: str, remote: bool):
    cmd = [
        "npx", "wrangler", "d1", "execute", DB_NAME,
        "--file", sql_path,
        "--config", str(WRANGLER_TOML),
    ]
    if remote:
        cmd.append("--remote")
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(WRANGLER_TOML.parent.parent))
    if result.returncode != 0:
        print("ERROR: wrangler command failed", file=sys.stderr)
        sys.exit(1)


def main():
    remote = "--remote" in sys.argv

    md_files = sorted(RESOURCES_DIR.glob("*.md"))
    print(f"Found {len(md_files)} resource files in {RESOURCES_DIR}")

    resources = []
    for f in md_files:
        r = parse_resource_file(f)
        if r:
            resources.append(r)

    print(f"Parsed {len(resources)} valid resources")

    # Write SQL in batches (D1 has limits per execute call)
    BATCH = 50
    batches = [resources[i : i + BATCH] for i in range(0, len(resources), BATCH)]

    for idx, batch in enumerate(batches):
        sql = build_sql(batch)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sql", delete=False, encoding="utf-8"
        ) as f:
            f.write(sql)
            tmp = f.name

        print(f"Batch {idx + 1}/{len(batches)}: {len(batch)} resources → {tmp}")
        run_wrangler(tmp, remote)
        os.unlink(tmp)

    print(f"Done. {len(resources)} resources imported to D1 ({'remote' if remote else 'local'}).")


if __name__ == "__main__":
    main()
