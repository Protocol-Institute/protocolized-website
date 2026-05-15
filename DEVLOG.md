# Protocolized Website — Build Log

A build log for protocolized.io — how the magazine and resource library site was built, what infrastructure decisions were made, and where things stand. Written for contributors curious about the process and for future maintainers.

---

## Session 1: Resource Library Foundation

*2026-03-23*

**Tracks:** content-sync, ux

- **Starting point:** The site began as a static Astro 5 site (`output: "static"`, Tailwind CSS) — a magazine and resource library for Protocolized, the Protocol Institute's Substack publication. The goal was a site that mirrored Substack content and served as a permanent home for PDFs and research resources, independent of Substack's platform.

- **Resource library (273 entries):** Initial population from raw source data — 273 resource records written as Astro Content Collections Markdown files in `src/content/resources/`. Each file has frontmatter: title, author, date, tags, type, url/doi, and (for PDFs) a local path in `public/resources/`. The library covers protocol theory, fiction, governance, technology, and organizational studies.

- **Article date fix:** Dates in the Substack CSV export were in a non-standard format that Astro's Content Collections date parser rejected. Fixed by normalizing dates in a preprocessing step before generating Markdown frontmatter. Fiction type added to the type taxonomy (had been omitted from the initial schema).

- **Domain update:** Site description and all internal references updated from `protocollized.substack.com` / Protocol Society to `protocolized.io` / Protocol Institute — the org had recently rebranded. The Substack publication itself remained at `protocolized.substack.com`; the .io domain is the independent site.

---

## Sessions 2–3: Rebrand, Logo Iterations, and GitHub Pages Deploy

*2026-04-03*

**Tracks:** ux, content-sync

- **Protocol Society → Protocol Institute rebrand (2026-04-03):** Full rename across the site — nav, footer, page titles, metadata. Added a media type filter to the resource library (story / article / column / all) keyed off the Substack section the post belongs to: *Fictions* → story, *Articles* → article, *Obliquities* → column. Added a carousel of recent Substack posts with OG images beside the hero — pulled from the existing Substack sync data.

- **Carousel positioning:** Initially the article carousel was below the hero; moved to sit beside it in a two-column layout to make recent issues immediately visible without scrolling. Carousel auto-advances every 5 seconds; timer was rebased in a follow-up to restart on manual navigation.

- **Substack section tags (2026-04-08):** Added `story`, `article`, and `column` tags to post metadata derived from Substack's section_id field (*Fictions*, *Articles*, *Obliquities*). Removed `video` type from the taxonomy — Protocolized has no video posts. The section-derived tags feed the resource library media filter.

- **GitHub Pages deploy (2026-04-08):** Added `.github/workflows/deploy.yml` — builds the Astro site on push to `main` and deploys to GitHub Pages using `actions/deploy-pages@v4`. The deploy triggered a `gh-pages` branch; a follow-up "Trigger GitHub Pages deploy" commit forced an initial build. This was always a stopgap — the site will move to Cloudflare Pages once the migration branch is ready.

- **Logo iteration — animated P mark (2026-04-08):** First animated logo: a simple *P* mark with a CSS draw-on animation (stroke-dashoffset SVG animation, 0.8s ease-out). Favicon updated to match. This replaced a static text wordmark.

- **Logo iteration — protocolized mark (2026-04-21):** Replaced the animated P mark with the new *protocolized mark* — the full branded SVG asset developed separately. Nav logo and favicon both updated. A follow-up commit (2026-04-22) updated the favicon specifically to the new mark after the nav update missed it.

- **Anthologies page:** Added `src/pages/anthologies.astro` — a curated view of the fiction collections (Terminological Twists, Ghosts in Machines, Building and Burning Bridges, The Librarians). This pre-dates the C3PO collection card vectors; the page is hand-authored from known collection membership. It will eventually be driven by C3PO metadata.

- **Summer of Protocols archive link:** Footer updated to link to the SoP archive — the predecessor program (2023–2024) that the Protocol Institute grew out of. The link makes the historical lineage visible to new visitors.

---

## Session 4: Contributor Onboarding, CF Migration Branch, and Framework Decision

*2026-05-12*

**Tracks:** cloudflare-migration, framework, c3po-integration

- **Contributor onboarding docs (2026-05-12):** Added `CLAUDE.md` and `README.md`. `README.md` is public-facing (GitHub visitors). `CLAUDE.md` is LLM-facing — Astro commands, deploy workflow, the sync script, key management policy reference. A separate `claude-vgr.md` tracks VGR-specific context (fork policy, PR workflow, personal account vs. org account distinction) that does not belong in the org-visible CLAUDE.md.

- **Cloudflare Pages migration branch (`feat/cloudflare-migration`, 2026-05-14):** Added `wrangler.toml` (Astro static build config, `pages_build_output_dir = "dist"`), `.github/workflows/deploy.yml` updated to use `cloudflare/pages-action@v1` instead of GitHub Pages, and `MIGRATION.md`. Key blocker: Timber needs to transfer the `protocolized.io` nameservers to Cloudflare DNS before CF Pages can serve the domain. The GitHub Pages deploy remains active until that transfer completes.

- **Personal → PI account migration path:** `MIGRATION.md` documents that the CF Pages project will initially be created under VGR's personal CF account. Once a Protocol Institute org account exists, both the Pages project and the DNS zone transfer to the org account. Same pattern as protocol-institute.org.

- **C3PO service binding stub:** `wrangler.toml` includes a stub service binding for C3PO (`[[services]] binding = "C3PO" service = "c3po"`) and an R2 bucket binding (`[[r2_buckets]] binding = "RESOURCES" bucket_name = "protocolized-resources"`). Neither is active yet — the stubs document the planned integration architecture. The C3PO binding allows the site Worker to call C3PO without cross-origin requests.

- **Feature roadmap (2026-05-14):** `ROADMAP.md` — seven-phase plan: Phase 0 (CF migration), Phase 1 (framework decision gate), Phase 2 (live Substack mirroring via CF Workers Cron Trigger + D1, Events calendar), Phase 3 (IPFS resource migration — Pinata + R2), Phase 4 (C3PO embed + semantic search), Phase 5 (MCP server), Phase 6 (SIWE + content gating — three access tiers: public / member / patron), Phase 7 (Stripe + ETH donations + patron membership).

- **Framework decision gate (2026-05-14):** Phase 1 was designated a *decision gate* rather than a feature sprint — the choice of framework determines how Phases 2–7 are implemented, and committing to the wrong one creates painful mid-build technical debt. Three options analyzed: **Option A** — Astro hybrid mode (`output: "hybrid"` + `@astrojs/cloudflare` adapter): lowest migration cost, preserves 280 Markdown resource files and existing components, but static-first mental model may strain as dynamic features grow. **Option B** — bespoke CF Workers (Hono + HTMX): maximum CF-native control, streaming is first-class, no build step, but requires full content-layer migration to D1 and is a less familiar stack. **Option C** — SvelteKit + CF adapter: best DX for a dynamic-first site, mature CF adapter, but full component rewrite required. Decision is pending; the roadmap recommendation is: *if content continuity is the priority → Option A; if clean architecture for dynamic features is the priority → Option B or C.*

- **Open questions logged in ROADMAP.md:** Framework choice (Option A/B/C) — needed before Phase 2. Whether to migrate existing 280 Markdown resource files to D1 or keep Markdown for historical posts and add D1 only for new content. Pinata vs Filebase for IPFS pinning. Dynamic.xyz vs Privy for SIWE wallet widget (coordinate with .org to use the same provider). Whether PI membership data should live in a unified D1 database shared between .org and .io. Whether to issue a membership NFT or token for Phase 6b token gating.

---

## Session 5: Devlog System, Session Rituals, and Org Admin Infrastructure

*2026-05-14 · 14:30–18:56 PT*

**Tracks:** operations

- **Devlog system:** Added `data/devlog.json` (source of truth), `devlog_session.py` (writes ISO timestamp to `/tmp/protocolized_devlog_session_start.txt`), and `devlog_render.py` (renders `DEVLOG.md` from JSON). Backfilled Sessions 1–4 from git history and status log. Consistent with the C3PO and protocol-institute.org devlog pattern.

- **Session rituals (added to CLAUDE.md):** Startup: timestamp → `track.py status` → read status-vgr.md → check Substack sync activity (git log --grep=sync) → check CF branch divergence → check framework decision state → summarize. Wrap-up: devlog entry + devlog_render.py → status-vgr.md → CLAUDE.md updates → `npm run build` (if code changed) → git commit/push → `track.py end` → fill log-{id}.json → expenses render → Claude memory.

- **PI admin repo reference:** CLAUDE.md updated with a PI key/security policy banner pointing to `../admin/keys.md` and `../admin/security.md`. The `## Keys` section notes that no keys are currently in use; when CF Workers are added, all PI keys go through `../.env.keys` and `../admin/keys.md` — not `Code/.env.keys`. The admin repo (`Protocol-Institute/admin`, private) is the single source of truth for PI contributor expenses, key ownership, and security policy.

---
