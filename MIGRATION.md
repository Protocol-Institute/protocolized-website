# Migration: GitHub Pages → Cloudflare Pages

This document tracks the planned migration of protocolized.io from GitHub Pages to Cloudflare Pages. The discussion issue for this migration is at Protocol-Institute/protocolized-website#[issue number].

## Why Migrate

1. **C3PO integration.** The Protocol Institute is building a RAG research assistant (C3PO — github.com/vgururao/c3po, to be transferred to this org) that will live in the Resources page. C3PO will be deployed as a Cloudflare Worker. Workers integrate with Cloudflare Pages via service bindings — no cross-origin request overhead, no CORS configuration. This is not possible with GitHub Pages hosting.

2. **PDF storage.** The repo currently contains ~353 MB of PDFs in `public/resources/`. That's a git anti-pattern and will hit GitHub limits as the library grows. Cloudflare R2 (object storage) can host these files, reducing repo size and enabling proper CDN delivery. A service binding in `wrangler.toml` would expose R2 to the site.

3. **Edge performance and analytics.** Cloudflare Pages serves from ~300 edge locations globally. protocol-institute.org is already on Cloudflare; migrating protocolized.io makes the entire PI stack consistent. Cloudflare Web Analytics provides privacy-respecting traffic data without a third-party script.

4. **Preview deployments.** Cloudflare Pages generates a preview URL for every branch push, making it easy to review changes before merging to main.

## What Changes

| | Before | After |
|---|---|---|
| Hosting | GitHub Pages | Cloudflare Pages |
| Deploy trigger | GitHub Actions → GH Pages API | GitHub Actions → `cloudflare/pages-action` |
| DNS | Google Domains → GitHub Pages IPs | Google Domains → Cloudflare Pages |
| Build | GH Actions runner | GH Actions runner (unchanged) |
| Substack sync | GH Actions cron (unchanged) | GH Actions cron (unchanged) |
| Astro config | `output: "static"` (unchanged) | `output: "static"` (unchanged) |
| Node version | 22 (unchanged) | 22 (unchanged) |

The daily Substack sync workflow (`sync-substack.yml`) is **not affected** — it commits to the repo, which triggers the deploy workflow as usual.

## What Stays the Same

- All Astro pages, components, and content
- Resource library and filterable grid
- Magazine sync from Substack
- `npm run build` / `npm run dev` locally
- Site URL: protocolized.io

## Migration Steps

### Step 1 — Create Cloudflare Pages project (manual, one-time)

In the Cloudflare dashboard (personal account initially, to be transferred to PI account):
- Pages → Create a project → Connect to Git → Protocol-Institute/protocolized-website
- Framework preset: Astro
- Build command: `npm run build`
- Build output directory: `dist`
- Node version environment variable: `NODE_VERSION = 22`

### Step 2 — Add GitHub Actions secrets

In the Protocol-Institute/protocolized-website repo settings → Secrets:
- `CLOUDFLARE_API_TOKEN` — CF API token with Cloudflare Pages: Edit permission
- `CLOUDFLARE_ACCOUNT_ID` — CF account ID

### Step 3 — Merge this branch

This branch (`feat/cloudflare-migration`) contains:
- Updated `deploy.yml` using `cloudflare/pages-action` instead of GitHub Pages actions
- `wrangler.toml` with Pages config and commented future bindings

Merging to main triggers the first CF Pages deploy. Verify at the `*.pages.dev` preview URL before touching DNS.

### Step 4 — Update DNS

Current `protocolized.io` DNS (in Google Domains):
- A records → GitHub Pages IPs (185.199.108-111.153)
- `www` CNAME → ext-sq.squarespace.com (leftover, should be cleaned up)

After Cloudflare Pages project is live:
- Remove the four A records pointing to GitHub Pages
- Add CNAME: `protocolized.io` → `<project>.pages.dev`
- Remove the stale `www` CNAME (or point it to the same CF Pages project)

DNS TTL is typically 3600s — plan for up to 1h propagation.

### Step 5 — Disable GitHub Pages

In repo settings → Pages → set source to "None" after DNS is confirmed working.

### Step 6 — Transfer Cloudflare project to PI account (when ready)

Once the PI organization has its own Cloudflare account, transfer the Pages project from the personal account.

## Future: C3PO Integration

Once C3PO is deployed as a Cloudflare Worker (Phase 2 of github.com/vgururao/c3po), the Resources page will be redesigned to include it. The integration will work as follows:

1. Add service binding in `wrangler.toml` (already stubbed):
   ```toml
   [[services]]
   binding = "C3PO"
   service = "c3po-worker"
   ```
2. Resources page gets a chat interface for querying the Protocol Institute research corpus
3. PDF files currently in `public/resources/` move to Cloudflare R2, served via R2 binding

This integration is only possible on Cloudflare Pages. It is the primary technical driver for this migration.

## Future: PDF Migration to R2

The `public/resources/` directory contains ~353 MB of PDFs committed to git. This should eventually be moved to Cloudflare R2:
1. Create R2 bucket `protocolized-resources`
2. Upload existing PDFs via `rclone` or `wrangler r2 object put`
3. Update resource markdown `file:` fields to point to R2 URLs
4. Remove PDFs from the repo (large file history requires `git-filter-repo`)

This is a separate migration from the Pages switch and can happen after C3PO is live.

## Rollback Plan

If CF Pages deploy fails or the site breaks after DNS switch:
- Point the A records back to GitHub Pages IPs
- Re-enable GitHub Pages in repo settings
- Revert `deploy.yml` to the original GitHub Pages workflow

The original `deploy.yml` is preserved in git history on `main` before the merge.
