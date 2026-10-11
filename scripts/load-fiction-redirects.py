#!/usr/bin/env python3
"""
Load data/monstroustimes-map.json into the D1 fiction_redirects table.

The map is the source of truth for where fiction moved at the fiction split
cutover (Session 24): /p/:slug -> MT article, /books/:slug -> MT series page,
/anthologies -> MT series index. The Worker only consults fiction_redirects
when FICTION_SEGREGATION_ACTIVE = "true".

Idempotent: replaces the whole table with the map's contents, so editing the
JSON and re-running is the way to add or change a redirect (e.g. once a new
fiction piece that went out on the old Substack appears on MT).

Usage:
    python3 scripts/load-fiction-redirects.py --dry-run   # print SQL only
    python3 scripts/load-fiction-redirects.py --remote

Without --remote, targets the local miniflare D1 (dev/test only).
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

WRANGLER_TOML = Path(__file__).parent.parent / "worker" / "wrangler.toml"
REPO_ROOT = WRANGLER_TOML.parent.parent
MAP_FILE = REPO_ROOT / "data" / "monstroustimes-map.json"
DB_NAME = "protocolized-resources"

# JSON section -> fiction_redirects.kind (matched by the Worker per route)
KINDS = {"posts": "post", "books": "book", "pages": "page"}


def sql_escape(s: str) -> str:
    return s.replace("'", "''")


def build_sql(mapping: dict) -> str:
    rows = []
    seen = {}
    for section, kind in KINDS.items():
        for slug, url in mapping.get(section, {}).items():
            # slug is the table's primary key, so a post and a book can't
            # share one -- fail loudly rather than let one silently win.
            if slug in seen:
                sys.exit(f"ERROR: slug '{slug}' appears in both {seen[slug]} and {section}")
            seen[slug] = section
            rows.append(f"('{sql_escape(slug)}', '{kind}', '{sql_escape(url)}')")
    return (
        "DELETE FROM fiction_redirects;\n"
        "INSERT INTO fiction_redirects (slug, kind, redirect_url) VALUES\n  "
        + ",\n  ".join(rows)
        + ";\n"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remote", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    mapping = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    sql = build_sql(mapping)
    counts = {k: len(mapping.get(k, {})) for k in KINDS}
    print(f"fiction_redirects: {counts}")

    if args.dry_run:
        print(sql)
        return

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".sql", delete=False, encoding="utf-8"
    ) as f:
        f.write(sql)
        tmp = f.name
    cmd = [
        "npx", "wrangler", "d1", "execute", DB_NAME,
        "--file", tmp,
        "--config", str(WRANGLER_TOML),
    ]
    if args.remote:
        cmd.append("--remote")
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    Path(tmp).unlink()
    if result.returncode != 0:
        print("ERROR: wrangler execute failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
