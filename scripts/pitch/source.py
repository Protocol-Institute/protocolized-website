#!/opt/homebrew/bin/python3
"""Pull/push the pitch document's markdown between pitch/source.md and R2.

The source is not in git (the repo is public). R2 holds the copy the Worker
renders; pitch/source.md is the local (Dropbox-backed) working copy.

  python3 scripts/pitch/source.py pull    # R2 -> pitch/source.md
  python3 scripts/pitch/source.py push    # pitch/source.md -> R2 (live immediately)

Directives the Worker expands (alone on a line): {{team}} {{research-leads}}
{{research-groups}} {{roadmap-projects}}; inline: {{group-count}} {{roadmap-count}}.
Needs CLOUDFLARE_API_TOKEN (see CLAUDE.md, Keys).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "pitch" / "source.md"
OBJECT = "protocolized-resources/pitch/source.md"


def wrangler(*args: str) -> None:
    subprocess.run(["npx", "wrangler", "r2", "object", *args, "--remote"], cwd=ROOT / "worker", check=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pull":
        LOCAL.parent.mkdir(exist_ok=True)
        wrangler("get", OBJECT, f"--file={LOCAL}")
    elif cmd == "push":
        wrangler("put", OBJECT, f"--file={LOCAL}", "--content-type=text/markdown; charset=utf-8")
    else:
        sys.exit(__doc__)
