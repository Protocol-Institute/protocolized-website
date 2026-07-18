#!/usr/bin/env python3
"""
Add a post as the next chapter in a series book: appends a TOC entry to
books.toc and sets series_slug/series_position on the posts row.

Replaces the ad-hoc `wrangler d1 execute` commands used to wire up the
original 4 Jamverse series (Trainverse, Legends & Ledgers, Zoothesia,
Stockton Chronicles) in Session 14 -- those were never scripted, so this
exists to make future additions repeatable and reviewable.

Usage:
    python3 scripts/update-series-toc.py --book legends-and-ledgers --post the-big-man --remote
    python3 scripts/update-series-toc.py --book legends-and-ledgers --post the-big-man \
        --title "The Big Man" --author "Elizabeth Maher" --position 3 --remote

If --title/--author are omitted, they're pulled from the posts row (title)
and the most recent existing TOC entry's author (assumed same author for
the series). If --position is omitted, it's set to len(toc) + 1.

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
DB_NAME = "protocolized-resources"


def sql_escape(s: str) -> str:
    return s.replace("'", "''")


def query(sql: str, remote: bool) -> list[dict]:
    cmd = [
        "npx", "wrangler", "d1", "execute", DB_NAME,
        "--command", sql,
        "--config", str(WRANGLER_TOML),
        "--json",
    ]
    if remote:
        cmd.append("--remote")
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR: wrangler query failed", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    data = json.loads(result.stdout)
    return data[0]["results"]


def run_sql_file(sql: str, remote: bool):
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
    if remote:
        cmd.append("--remote")
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    Path(tmp).unlink()
    if result.returncode != 0:
        print("ERROR: wrangler update failed", file=sys.stderr)
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True, help="books.slug for the series")
    ap.add_argument("--post", required=True, help="posts.slug for the new chapter")
    ap.add_argument("--title", help="Chapter title (default: pulled from posts.title)")
    ap.add_argument("--author", help="Author name (default: same as last TOC entry)")
    ap.add_argument("--position", type=int, help="series_position (default: len(toc) + 1)")
    ap.add_argument("--remote", action="store_true", help="Target live D1 (default: local)")
    args = ap.parse_args()

    book_rows = query(f"SELECT toc FROM books WHERE slug = '{sql_escape(args.book)}'", args.remote)
    if not book_rows:
        print(f"ERROR: no book found with slug '{args.book}'", file=sys.stderr)
        sys.exit(1)
    toc = json.loads(book_rows[0]["toc"])

    post_rows = query(
        f"SELECT slug, title, series_slug, series_position FROM posts WHERE slug = '{sql_escape(args.post)}'",
        args.remote,
    )
    if not post_rows:
        print(f"ERROR: no post found with slug '{args.post}'", file=sys.stderr)
        sys.exit(1)
    post = post_rows[0]

    if post["series_slug"] is not None:
        print(
            f"ERROR: post '{args.post}' is already in series "
            f"'{post['series_slug']}' at position {post['series_position']}",
            file=sys.stderr,
        )
        sys.exit(1)

    title = args.title or post["title"]
    author = args.author or (toc[-1].get("author") if toc else None)
    if not author:
        print("ERROR: --author required (no existing TOC entry to infer from)", file=sys.stderr)
        sys.exit(1)
    position = args.position or (len(toc) + 1)

    toc.append({"title": title, "author": author, "url": f"/p/{args.post}"})

    print(f"Adding to '{args.book}': \"{title}\" by {author}, position {position}")
    print(f"New TOC length: {len(toc)}")

    toc_json = json.dumps(toc)
    sql = "\n".join([
        f"UPDATE books SET toc = '{sql_escape(toc_json)}' WHERE slug = '{sql_escape(args.book)}';",
        f"UPDATE posts SET series_slug = '{sql_escape(args.book)}', series_position = {position} "
        f"WHERE slug = '{sql_escape(args.post)}';",
    ])
    run_sql_file(sql, args.remote)
    print("Done.")


if __name__ == "__main__":
    main()
