#!/opt/homebrew/bin/python3
"""Build the pitch PDF from the live /pitch/print page and upload it to R2.

The page expands the live lists (team, research groups, roadmap) on every
request, so the PDF is always built from current data. A content hash is
compared with the one stored beside the last PDF; if nothing changed the run
exits without building. Run every 15 minutes by .github/workflows/pitch-pdf.yml.

  PITCH_PASSWORD=... python3 scripts/pitch/build-pitch-pdf.py [--force] [--no-upload]

--no-upload writes pitch/build/protocol-institute-overview.pdf and changes nothing remote.
Requires: weasyprint; wrangler (worker/node_modules) + CLOUDFLARE_API_TOKEN for the upload.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = os.environ.get("PITCH_SITE", "https://protocolized.io")
BUCKET = "protocolized-resources"
PDF_KEY = "pitch/protocol-institute-overview.pdf"
META_KEY = "pitch/pdf-meta.json"


def get(path: str, password: str):
    req = urllib.request.Request(SITE + path, headers={"Authorization": f"Bearer {password}", "User-Agent": "pitch-pdf-build"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(), r.headers


def r2_put(key: str, path: Path, content_type: str) -> None:
    subprocess.run(
        ["npx", "wrangler", "r2", "object", "put", f"{BUCKET}/{key}", f"--file={path}", f"--content-type={content_type}", "--remote"],
        cwd=ROOT / "worker", check=True,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-upload", action="store_true")
    args = ap.parse_args()
    password = os.environ.get("PITCH_PASSWORD")
    if not password:
        sys.exit("PITCH_PASSWORD is not set")

    status = json.loads(get("/pitch/status.json", password)[0])
    if not args.force and status["hash"] and (status.get("pdf") or {}).get("hash") == status["hash"]:
        print(f"PDF is current ({status['hash']}); nothing to do")
        return 0

    html, headers = get("/pitch/print", password)
    page_hash = headers["X-Pitch-Hash"]

    from weasyprint import HTML
    out = ROOT / "pitch" / "build" / "protocol-institute-overview.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html.decode("utf-8"), base_url=SITE + "/").write_pdf(out)
    print(f"built {out} ({out.stat().st_size // 1024} KB, hash {page_hash})")
    if args.no_upload:
        return 0

    meta = out.with_name("pdf-meta.json")
    meta.write_text(json.dumps({"hash": page_hash, "built_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}))
    r2_put(PDF_KEY, out, "application/pdf")
    r2_put(META_KEY, meta, "application/json")  # last: the page treats the PDF as current once this lands
    print("uploaded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
