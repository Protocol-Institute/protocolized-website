#!/opt/homebrew/bin/python3
"""
check-drafts.py — run a WIP project's checklist against its synced drafts.

Writes wip/<slug>/checks.json (shown on the project page and in the manuscript's
chapter openers) and prints a per-draft summary. The checklist is defined in
project.json; the automated checks are in draft_checks.py.

Run it after build-manuscript.py has synced the drafts (or use --fetch here).
build-manuscript.py --publish runs the same checks and commits checks.json with
the release, so a standalone run is for authors' and the editor's spot checks.

Usage:
  python3 scripts/wip/check-drafts.py protocol-reader-vol-2
  python3 scripts/wip/check-drafts.py protocol-reader-vol-2 --entry blygger -v
  python3 scripts/wip/check-drafts.py protocol-reader-vol-2 --no-links
"""

import argparse
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import draft_checks  # noqa: E402

spec = importlib.util.spec_from_file_location("build_manuscript", HERE / "build-manuscript.py")
bm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bm)

MARK = {"pass": "✓", "fail": "✗", "warn": "!", "manual": "·", "na": "–"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--fetch", action="store_true", help="sync drafts from Drive first")
    ap.add_argument("--no-links", action="store_true", help="skip the online link check")
    ap.add_argument("--entry", help="only print this entry (checks.json is still written in full)")
    ap.add_argument("-v", "--verbose", action="store_true", help="print every item with its detail")
    args = ap.parse_args()

    project_dir = bm.WIP_ROOT / args.slug
    project = json.loads((project_dir / "project.json").read_text())
    chapters = project_dir / "archive" / "chapters"
    if args.fetch:
        bm.fetch_sources(project, chapters)

    checks = draft_checks.run_checks(project, project_dir, chapters, not args.no_links, bm.source_path)
    out = project_dir / "checks.json"
    out.write_text(json.dumps({"generated": dt.date.today().isoformat(), "entries": checks},
                              indent=2, ensure_ascii=False) + "\n")

    labels = {it["id"]: it["label"] for it in project["checklist"]}
    titles = {e["id"]: e["title"] for e in project["contents"]}
    for eid, c in checks.items():
        if args.entry and eid != args.entry:
            continue
        s = c["summary"]
        print(f"\n{'READY ' if s['ready'] else ''}{titles[eid][:70]}  "
              f"[{s['pass']} pass · {s['fail']} fail · {s['warn']} warn · {s['manual']} manual]")
        for item, res in c["results"].items():
            if args.verbose or res["status"] in ("fail", "warn"):
                print(f"   {MARK[res['status']]} {labels[item]}{': ' + res['detail'] if res['detail'] else ''}")
    ready = sum(1 for c in checks.values() if c["summary"]["ready"])
    print(f"\n{ready} of {len(checks)} drafts pass every automated check. Wrote {out.relative_to(bm.REPO_ROOT)}")


if __name__ == "__main__":
    main()
