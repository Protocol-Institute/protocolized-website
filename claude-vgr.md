# Claude Notes — vgr (Venkat)
> **Environment rules, keys & safety policies:** see [Code/CLAUDE.md](../CLAUDE.md) — read before starting work.


Venkat is a contributing member of Protocol-Institute, not the primary maintainer.

## Repo: protocolized-website
Astro + Tailwind site. Requires build step.

```bash
cd protocolized-website
npm install          # first time
npm run dev          # dev server
npm run build        # production build (outputs to dist/)
```

Key dirs: `src/` (Astro components/pages), `public/` (static assets), `scripts/`.

## Workflow Notes
- `.claude/` is gitignored — primary maintainer's CLAUDE.md cannot live there; flag this to them.
- Primary maintainer's CLAUDE.md not yet present; expected to be added at repo root.
- **Default: commit directly to `main` on the upstream repo** (Protocol-Institute/protocolized-website).
- **Fork (vgururao/protocolized-website) is only for changes that require review** — push a branch there and open a PR to upstream. Delete the branch after merge.
- Do not use the fork as a general working copy; keep it in sync with upstream when it's needed.

## Deploy

Push to `main` — GitHub Actions runs `deploy.yml` which deploys the Hono Worker to Cloudflare (`npm run deploy` from `worker/`). Domain `protocolized.io` is on Cloudflare Workers (cutover 2026-06-09). Astro CF Pages project still exists as a fallback but receives no traffic.
