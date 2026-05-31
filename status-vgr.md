# Status — vgr (Venkat)

## Active
<!-- current tasks or in-progress work -->

## Upcoming
<!-- planned changes or features -->

### Infrastructure
- Disable GitHub Pages in repo settings (source → None) — protocolized.io now serves from CF Pages
- Add `--remote` note to CLAUDE.md for all future `wrangler r2 object` commands (local miniflare trap)
- Purge PDF/EPUB git history with `git-filter-repo` to reclaim repo size (353 MB removed from HEAD but still in history)

### SoP Resource Migration (from summerofprotocols.com)
Add resource entries for the following SoP content not yet in the library.

**Missing research essays:**
- Protocols Don't Build Pyramids — Drew Austin (essay, summerofprotocols.com/research/protocols-dont-build-pyramids)
- Protocols in (Emergency) Time — Olivia Steiert (essay, summerofprotocols.com/research/protocols-in-emergency-time)
- The Swarm and the Formation — Rafael Fernández (essay, summerofprotocols.com/research/the-swarm-and-the-formation)
- New Time Machines — Aaron Lewis, Kei Kreutler, Alice Noujaim, Nahee Kim, Spencer Chang (serialized fiction, summerofprotocols.com/research/new-time-machines)

**Bridge Atlas episodes 2–5** (Christine Kim, podcast series on Ethereum stewardship — ep.1 already in library):
- Ep. 2: Commons and Crises
- Ep. 3: Computing and Society
- Ep. 4: Protocol Design Considerations
- Ep. 5: Future Trust and Institutions

**Missing "pill" creative micro-works** (all from SoP, type=fiction/image/game as appropriate):
- A Pattern Language for Digital Spaces — Guo Liu (comic/graphic)
- all just fresh-off-the-boat or floating — hua xi zi (video)
- Below the API — Stephen Bailey (fiction)
- Farflora — Sevenfloor / Xiaoting Tan (generative art / NFT)
- FutureRack — Chenoe Hart (comic, 19" equipment rack as flexible standard)
- Meet me on the deep net — Lizz Thabet (browser game)
- Memories of Us — Will Abramson (fiction)
- Micronaut Odyssey — Wendi Yan (video)
- On-chain Data Sculpture Exhibition — Haotian Fang (video)
- protocol.guide — Willie Shaw Fineberg (external mini-site / tool)
- Protocol Party — Mashal Waqar (game — distinct from the card sets already in library)
- Protocol with uncommunicables — Yuemin Huang (video)
- Re-Move — Nahee Kim (visual narrative)
- Renotations — Ben Zucker (musical protocol kit)
- Technium Underground: The Eternal Return of Hara — Kay Yu (fiction)
- Terminal Highway — Sachin Benny (fiction)
- The Caucus — Randy Lubin (fiction/game)

**ProtocolKit** — Physical research kit from SoP23. Add a resource entry now (type=`framework`, link to SoP page); a full product page is tracked in ROADMAP Phase 8.

## Done
<!-- completed items, reverse chronological -->
- **2026-05-31** — Session 8 (partial). Hono Worker scaffolded: all source files written (`worker/src/index.ts`, `db.ts`, `html/base.tsx`, `home.tsx`, `resources.tsx`, `resource.tsx`, `static-pages.tsx`), plus `schema.sql`, `wrangler.toml`, `package.json`, `tsconfig.json`, `tailwind.config.mjs`. `scripts/migrate-to-d1.py` written. `npm install` done in `worker/`. CSS compiled (`worker/public/style.css`). **Paused before D1 creation and local test.** Resume at: copy static assets → create D1 → apply schema → run migration → `wrangler dev` → deploy.
- **2026-05-30** — Session 7. CF Pages migration complete: protocolized.io live on CF Pages (PI org account). All 82 PDFs + 4 EPUBs migrated to R2 bucket `protocolized-resources`, served at `files.protocolized.io`. 76 resource frontmatter `file:` fields rewritten to R2 URLs. PDFs removed from repo and history purged via git-filter-repo (repo: 353 MB → 1 MB). Framework decision: Hono + HTMX (Option B). SoP content gap analysis: 21 items identified — 4 essays, Bridge Atlas ep 2-5, 17 pills added to Upcoming backlog; 7 items written to `../website/sop-migration.md` for protocol-institute.org. ROADMAP.md updated (Phase 0+1 ✓, Phase 8 added). Hono migration plan written to `worker/PLAN.md`. Next: implement Hono Worker (target: before Monday 8am UTC cron).
- **2026-05-20** — Built Protocol Lexicon page (`/resources/protocol-lexicon/`): 561 terms (233 PI-coined, 320 PI-specific, 8 curated), merged from c3po corpus triage + existing 46-term hand-curated md. Static Astro page with spotlight card (random shuffle), live search, A-Z index bar, 2-col card grid, triage badges, source links. JSON backend at `/api/lexicon.json`. Build script at `scripts/build-lexicon.py`.
- **2026-05-19** — Added C-3PO bot link box to top of resources page sidebar (`src/pages/resources/index.astro`). Beta-labeled, teal/coral styling, links to `https://c3po.vgr-702.workers.dev?ref=protocolized-resources` (new tab). URL tagged for traffic source tracking.
- **2026-05-14** — Added devlog system (data/devlog.json, devlog_session.py, devlog_render.py). Backfilled Sessions 1–4 from git history. Added startup and wrap-up rituals to CLAUDE.md. CLAUDE.md updated with PI admin repo banner (../admin/keys.md, ../admin/security.md).
- **2026-05-14** — Created Cloudflare Pages migration branch (`feat/cloudflare-migration`) with updated `deploy.yml` (cloudflare/pages-action@v1), `wrangler.toml` (with C3PO and R2 service binding stubs), `MIGRATION.md`, and GitHub Issues #1 (migration discussion) and #2 (Timber task for CF account/domain setup). Migration requires Timber to transfer protocolized.io nameservers to Cloudflare.
