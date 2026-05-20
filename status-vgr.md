# Status — vgr (Venkat)

## Active
<!-- current tasks or in-progress work -->

## Upcoming
<!-- planned changes or features -->
- Migrate hosting from GitHub Pages to Cloudflare Pages (required for C3PO integration)
- Timber needs to: set up CF account + CF-managed domain for protocolized.io (nameserver transfer at Google Domains), create Pages project, set API token + GitHub secrets (see GitHub Issue #2)

## Done
<!-- completed items, reverse chronological -->
- **2026-05-20** — Built Protocol Lexicon page (`/resources/protocol-lexicon/`): 561 terms (233 PI-coined, 320 PI-specific, 8 curated), merged from c3po corpus triage + existing 46-term hand-curated md. Static Astro page with spotlight card (random shuffle), live search, A-Z index bar, 2-col card grid, triage badges, source links. JSON backend at `/api/lexicon.json`. Build script at `scripts/build-lexicon.py`.
- **2026-05-19** — Added C-3PO bot link box to top of resources page sidebar (`src/pages/resources/index.astro`). Beta-labeled, teal/coral styling, links to `https://c3po.vgr-702.workers.dev?ref=protocolized-resources` (new tab). URL tagged for traffic source tracking.
- **2026-05-14** — Added devlog system (data/devlog.json, devlog_session.py, devlog_render.py). Backfilled Sessions 1–4 from git history. Added startup and wrap-up rituals to CLAUDE.md. CLAUDE.md updated with PI admin repo banner (../admin/keys.md, ../admin/security.md).
- **2026-05-14** — Created Cloudflare Pages migration branch (`feat/cloudflare-migration`) with updated `deploy.yml` (cloudflare/pages-action@v1), `wrangler.toml` (with C3PO and R2 service binding stubs), `MIGRATION.md`, and GitHub Issues #1 (migration discussion) and #2 (Timber task for CF account/domain setup). Migration requires Timber to transfer protocolized.io nameservers to Cloudflare.
