#!/usr/bin/env python3
"""
scripts/fix-missing-body-r2.py

Upload body HTML to R2 and set body_r2_key in D1 for all posts.
Idempotent: R2 put overwrites existing objects; D1 UPDATE sets same value if already correct.

Run from repo root:
  export CLOUDFLARE_API_TOKEN=$(grep CLOUDFLARE_API_TOKEN /path/to/protocol-institute/.env.keys | cut -d= -f2)
  /opt/homebrew/bin/python3 scripts/fix-missing-body-r2.py
"""

import json
import os
import re
import sys
import time
import subprocess
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent
C3PO_DIR = REPO_ROOT.parent / "c3po"

API_META_FILE = C3PO_DIR / "sources/substack/api_metadata.json"
POSTS_HTML_DIR = C3PO_DIR / "data/substack/posts"
STATE_FILE = REPO_ROOT / "data/mirror_state.json"
ENV_FILE = REPO_ROOT.parent / ".env.keys"
WRANGLER = REPO_ROOT / "worker/node_modules/.bin/wrangler"
WORKER_DIR = REPO_ROOT / "worker"

R2_BUCKET = "protocolized-resources"
DB_NAME = "protocolized-resources"

SRCSET_RE = re.compile(r'\s+srcset="[^"]*"', re.IGNORECASE)


def load_env():
    if not ENV_FILE.exists():
        print(f"[warn] env file not found at {ENV_FILE}", file=sys.stderr)
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            if key.strip() not in os.environ:
                os.environ[key.strip()] = val.strip()


def wrangler_env():
    return {**os.environ}


def r2_put(content: bytes, key: str, content_type: str):
    suffix = Path(key).suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(content)
        tmp = f.name
    try:
        result = subprocess.run(
            [str(WRANGLER), "r2", "object", "put", f"{R2_BUCKET}/{key}",
             f"--file={tmp}", f"--content-type={content_type}", "--remote"],
            capture_output=True, text=True, cwd=WORKER_DIR, env=wrangler_env(),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
    finally:
        os.unlink(tmp)


def sql_val(v) -> str:
    if v is None:
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"


def d1_execute(sql: str) -> bool:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
        f.write(sql)
        tmp = f.name
    try:
        result = subprocess.run(
            [str(WRANGLER), "d1", "execute", DB_NAME, "--remote", f"--file={tmp}"],
            capture_output=True, text=True, cwd=WORKER_DIR, env=wrangler_env(),
        )
        if result.returncode != 0:
            print(f"  [error] D1 execute failed:\n{result.stderr}", file=sys.stderr)
            return False
        return True
    finally:
        os.unlink(tmp)


def main():
    load_env()

    if not os.environ.get("CLOUDFLARE_API_TOKEN"):
        sys.exit(
            f"Error: CLOUDFLARE_API_TOKEN not set.\n"
            f"Run: export CLOUDFLARE_API_TOKEN=$(grep CLOUDFLARE_API_TOKEN {ENV_FILE} | cut -d= -f2)"
        )

    api_meta: list[dict] = json.loads(API_META_FILE.read_text())
    slug_to_id = {p["slug"]: str(p["id"]) for p in api_meta}

    html_by_id: dict[str, Path] = {}
    for f in POSTS_HTML_DIR.glob("*.html"):
        post_id = f.name.split(".")[0]
        html_by_id[post_id] = f

    state: dict = {}
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())

    slugs = [p["slug"] for p in api_meta]
    print(f"Processing {len(slugs)} posts (upload body to R2 + UPDATE D1)...\n")

    ok_count = 0
    skip_count = 0
    fail_count = 0

    for i, slug in enumerate(slugs, 1):
        print(f"[{i}/{len(slugs)}] {slug}")

        # Check state file — only skip if body_r2_uploaded is already recorded
        st = state.get(slug, {})
        if st.get("body_r2_uploaded"):
            print("  skip (already fixed)")
            skip_count += 1
            continue

        post_id = slug_to_id.get(slug)
        if not post_id:
            print(f"  skip: no post_id in api_metadata")
            skip_count += 1
            continue

        html_path = html_by_id.get(post_id)
        if not html_path:
            print(f"  skip: no export HTML for id={post_id}")
            skip_count += 1
            continue

        body_html = html_path.read_text(encoding="utf-8", errors="replace")
        body_html = SRCSET_RE.sub("", body_html)
        print(f"  body: {len(body_html):,} chars")

        body_r2_key = f"posts/{slug}/body.html"

        try:
            r2_put(body_html.encode("utf-8"), body_r2_key, "text/html; charset=utf-8")
            print(f"  R2: uploaded")
        except Exception as e:
            print(f"  FAILED R2: {e}")
            fail_count += 1
            continue

        sql = f"UPDATE posts SET body_r2_key={sql_val(body_r2_key)} WHERE slug={sql_val(slug)};"
        if d1_execute(sql):
            print(f"  D1: updated")
            st["body_r2_uploaded"] = True
            state[slug] = st
            STATE_FILE.write_text(json.dumps(state, indent=2))
            ok_count += 1
        else:
            print(f"  FAILED D1 update")
            fail_count += 1

        time.sleep(0.2)

    print(f"\nDone. {ok_count} fixed, {skip_count} skipped, {fail_count} failed.")


if __name__ == "__main__":
    main()
