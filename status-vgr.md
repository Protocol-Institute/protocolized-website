# Status — vgr (Venkat)

## Active
<!-- current tasks or in-progress work -->

## Upcoming
<!-- planned changes or features -->
- Migrate hosting from GitHub Pages to Cloudflare Pages (required for C3PO integration)
- Timber needs to: set up CF account + CF-managed domain for protocolized.io (nameserver transfer at Google Domains), create Pages project, set API token + GitHub secrets (see GitHub Issue #2)

## Done
<!-- completed items, reverse chronological -->
- **2026-05-14** — Created Cloudflare Pages migration branch (`feat/cloudflare-migration`) with updated `deploy.yml` (cloudflare/pages-action@v1), `wrangler.toml` (with C3PO and R2 service binding stubs), `MIGRATION.md`, and GitHub Issues #1 (migration discussion) and #2 (Timber task for CF account/domain setup). Migration requires Timber to transfer protocolized.io nameservers to Cloudflare.
