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

## Branch Sync Strategy: `main` ↔ `feat/cloudflare-migration`

Two parallel tracks:
- **`main`** — all content and page work: Substack syncs, Astro page/component edits, resource files, status/admin files. Deploy target: GitHub Pages.
- **`feat/cloudflare-migration`** — infra only: `wrangler.toml`, `.github/workflows/deploy.yml` (CF version), `MIGRATION.md`. No content changes here.

Because the file sets don't overlap, merge-downs are conflict-free.

**Periodic sync (merge `main` → CF branch):** do this at the start of each CF work session, or after a batch of main commits lands.
```bash
git checkout feat/cloudflare-migration
git merge main --no-edit
git push
git checkout main
```

**Landing the migration:** when CF infra is ready to ship, merge `feat/cloudflare-migration` → `main` (regular merge or squash). The CF `deploy.yml` will replace the GitHub Pages one; delete the old workflow file as part of that merge. Delete the CF branch after.

**Watch for conflicts:** if CF work ever needs to touch `src/` or `public/` (e.g., adding Cloudflare-specific redirects or headers), note it in the commit message so the next merge-down is easy to inspect.
