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

## Session 6: C3PO Link Box and Protocol Lexicon

*2026-05-19*

**Tracks:** c3po-integration, ux

- **C3PO link box (2026-05-19):** Added a beta-labeled link box to the top of the resources page sidebar (`src/pages/resources/index.astro`). Teal/coral styling; links to the deployed C3PO worker with a `?ref=protocolized-resources` query param for traffic-source tracking. Opens in a new tab. This is a surface entry point — the full service binding integration is planned for Phase 4.

- **Protocol Lexicon page (`/resources/protocol-lexicon`, 2026-05-20):** 561 terms compiled from the C3PO corpus triage plus an existing 46-term hand-curated Markdown file. Three tiers: 233 PI-coined terms, 320 PI-specific terms, 8 curated external terms. Static Astro page backed by `public/api/lexicon.json`. Features: spotlight card (random selection with daily shuffle via date seed), live search (debounced input against term + definition), A-Z index bar (jump anchors), two-column card grid, triage badge system, source links. Build script at `scripts/build-lexicon.py`: merges the triage CSV with the hand-curated Markdown and writes JSON. A separate resource entry (`src/content/resources/protocol-lexicon.md`) links the library to the lexicon page.

- **Lexicon triage completion:** 12 remaining terms triaged to close out the lexicon build sprint. Updated `status-vgr.md` with triage status and updated the session ritual in CLAUDE.md to reference the new lexicon infrastructure.

---

## Session 7: Cloudflare Pages Migration, R2 PDF Migration, and Hono Framework Decision

*2026-05-30*

**Tracks:** cloudflare-migration, framework, operations

- **CF Pages migration — Phase 0 complete (2026-05-30):** protocolized.io now serves from Cloudflare Pages under the PI org account (`7e8c7969b2464d23795c555bc6a32af8`). CF Pages project name: `protocolized-website`. Custom domains `protocolized.io` and `www.protocolized.io` active. GitHub Pages remains live as a dead-end fallback until manually disabled in repo settings.

- **R2 PDF migration:** All 82 PDFs and 4 EPUBs (353 MB) migrated from `public/resources/` to the R2 bucket `protocolized-resources`, served at `https://files.protocolized.io` via a custom R2 domain. 76 resource Markdown frontmatter `file:` fields rewritten from `/resources/filename.pdf` to `https://files.protocolized.io/filename.pdf`. Key incident: wrangler 4.x silently routes R2 writes to local miniflare storage when a `wrangler.toml` is present in CWD — all initial uploads went to `.wrangler/state/v3/` instead of CF. Fixed by re-uploading from `/tmp/` with `--remote` flag. Rule added to CLAUDE.md: always use `--remote` for `wrangler r2 object` and `wrangler d1 execute` commands.

- **Git history purge:** PDFs removed from the git tree with `git rm --cached`, then fully expunged from all commit history using `git-filter-repo --path public/resources/ --invert-paths`. Repo size: 353 MB → ~1 MB. Remote re-added after filter-repo removed it (expected behavior); force-pushed clean history.

- **Framework decision — Hono + HTMX (Phase 1 complete):** After reviewing the three options (Astro hybrid, Hono Workers, SvelteKit), chose **Option B: Hono + HTMX on CF Workers**. Rationale: the site's future feature set (streaming C3PO, semantic search, ETH auth, content gating) makes it fundamentally a dynamic web app, not a static magazine. Hono is CF-native, streaming is first-class, and a single coherent architecture avoids accumulating hybrid-mode complexity. ROADMAP.md Phases 0 and 1 marked complete; Phase 8 (Print Ops + ProtocolKit) added as a parallel track.

- **SoP content gap analysis:** Cross-checked 53 SoP research items against 287 protocolized.io resource files. Found 21 items missing from the library: 4 research essays, 5 Bridge Atlas podcast episodes (ep 2–5 + ep 1 already in library), 17 creative "pill" micro-works (fiction, video, game, generative art). Added to the `status-vgr.md` Upcoming backlog. Separately identified 7 items belonging on protocol-institute.org (SoP program history, alumni directory, corporate workshops, CC+ license, Symposium 2025 archive, Teaching Fellows list, Regional Pilots); written to `../website/sop-migration.md`.

- **Hono migration plan (`worker/PLAN.md`):** Full plan for replacing the Astro site with a CF Worker. D1 schema (single `resources` table), Hono JSX routes for all current pages, CSS strategy (copy Astro-compiled Tailwind output), content migration script (287 Markdown → D1), sync script dual-write strategy (Markdown + D1 during transition), and timeline targeting domain cutover before Monday 2026-06-02 8am UTC (next Substack cron run). Fallback: Astro CF Pages stays live; rollback = move custom domain back in CF dashboard.

---

## Session 8: C3PO Migration to PI Org + c3po.protocolized.io

*2026-05-31*

**Tracks:** cloudflare-migration, c3po-integration

- **C3PO migrated to PI org CF account:** The C3PO RAG assistant Worker was moved from the personal Cloudflare account to the Protocol Institute org account (`7e8c7969b2464d23795c555bc6a32af8`). C3PO assets (Pinecone index, model configs) migrated to PI infrastructure. DNS was already on Cloudflare from prior setup; no DNS changes required. This consolidates all PI compute and storage under the org account alongside CF Pages and R2 (already migrated in session 7).

- **c3po.protocolized.io subdomain live:** Custom subdomain `c3po.protocolized.io` configured on the PI org CF account, replacing the personal worker URL `c3po.vgr-702.workers.dev`. The Protocolized resources page sidebar C3PO link updated to the new URL with the `?ref=protocolized-resources` tracking parameter. Bot is now fully embedded as a PI-hosted service.

---

## Session 9: Hono Worker — Full Scaffold

*2026-05-31*

**Tracks:** cloudflare-migration, framework

- **Worker fully scaffolded:** All Hono CF Worker source files written for feature-parity with the Astro site. `worker/src/index.ts` wires 11 routes: `/`, `/about`, `/community`, `/magazine`, `/anthologies`, `/resources`, `/resources/:slug`, `/api/resources.json`, `/llms.txt`, `/rss.xml`, `/sitemap.xml`. Static assets (logo, lexicon HTML/JSON) served from `worker/public/` via the `[assets]` binding.

- **Hono JSX templates:** Five TSX component files implement the full UI in Hono JSX: `base.tsx` (HTML shell with sticky nav + footer, mobile menu), `home.tsx` (article carousel, audience pathway cards, featured resource grid, CTA strip), `resources.tsx` (full filter sidebar — type pills, media toggle, audience checkboxes, sort select — plus vanilla-JS client filter with URL-state sync), `resource.tsx` (detail page with breadcrumb, metadata bar, markdown body via `marked`, related resources), `static-pages.tsx` (about/community/magazine/anthologies). Design parity with Astro site: same Tailwind tokens, badge colors, component classes.

- **Migration script (`scripts/migrate-to-d1.py`):** Reads all 288 resource Markdown files, parses frontmatter with a zero-dependency YAML parser, emits batched SQL INSERT OR REPLACE statements, and runs them via `wrangler d1 execute`. Supports `--remote` flag for production import.

- **Worker infra:** `worker/package.json` (hono, marked, @tailwindcss/typography, wrangler), `worker/tsconfig.json` (jsxImportSource: hono/jsx), `worker/tailwind.config.mjs` (same tokens as Astro site), `worker/schema.sql` (resources table + 3 indexes), `worker/wrangler.toml` (account_id set; database_id = PLACEHOLDER pending D1 create). CSS compiled: `worker/public/style.css`. Key management policy documented in CLAUDE.md: PI org keys live in `../.env.keys` at org root.

- **Remaining before domain cutover:** (1) Copy static assets to `worker/public/` (logo, robots.txt, lexicon HTML/JSON). (2) Create D1 database and fill in `database_id` in wrangler.toml. (3) Run migration. (4) Local test with `wrangler dev`. (5) `wrangler deploy`. (6) Move `protocolized.io` custom domain from CF Pages → Worker in CF dashboard.

---

## Session 10: Phase 1 Complete — Worker Deployed

*2026-06-01 · 9:30–10:20am*

**Tracks:** cloudflare-migration, content-sync

- **D1 database created and populated:** `protocolized-resources` (id: `1b47f2d7-9c84-4078-a27a-2f3eea9f41b7`, WNAM region) created via wrangler. Schema applied with both tables: `resources` (288 rows migrated from Markdown) and `posts` (empty, ready for Phase 2 Substack mirror). Migration script ran in 6 batches, ~10 seconds total.

- **Hono Worker deployed to Cloudflare:** `protocolized-website.team-7e8.workers.dev` — all routes tested (200s across `/`, `/resources`, `/resources/:slug`, `/magazine`, `/about`, `/community`, `/anthologies`, `/rss.xml`, `/llms.txt`, `/api/resources.json`; 404 on unknown slugs). Two pre-deploy fixes: renamed `index.ts` → `index.tsx` (JSX requires .tsx extension for tsc) and added `skipLibCheck: true` (Hono JSX DOM event types conflict with `@cloudflare/workers-types`). Static assets copied to `worker/public/`. Pending manual step: move `protocolized.io` custom domain from CF Pages → Worker in CF dashboard.

- **Substack cover images backfilled into D1:** Discovered the Astro home page fetched OG images from Substack at build time — the Worker had no thumbnails in D1, so the home page showed none. Fix: `scripts/backfill-thumbnails.py` fetches `cover_image` for all 117 Substack posts via the paginated `/api/v1/posts` endpoint and writes to `resources.thumbnail` in D1. Single-batch SQL execution. Images now showing on the Worker home page. These are still substackcdn.com/S3 URLs; Phase 2 will mirror them to R2.

- **Phase 2 plan finalised:** Compared c3po’s Substack API access (paginated list fetch, `updated_at` change detection, Haiku enrichment, Pinecone output) with protocolized-website needs (D1 + R2 output). Decision: independent sync script with borrowed change-detection pattern, no cross-repo coupling. Backfill uses c3po’s existing `api_metadata.json` and `enriched_meta.json` as input (no re-fetching metadata). Fresh Substack export (138 posts, 2026-06-01) unzipped to `data/substack/`. Every post page will show a prominent “Read on Substack” link. Full plan in `plans/phase2-substack-mirror.md`.

---

## Session 11: Status Check — Domain Cutover Deferred

*2026-06-01*

**Tracks:** cloudflare-migration

- **Domain cutover deferred intentionally:** Decision made to keep `protocolized.io` on CF Pages until the Worker has full feature parity. The cutover itself is a 30-second manual step in the CF dashboard and is not a blocker for development. Confirmed GH Pages disabling and git history purge (removing PDFs from repo) were both completed in earlier sessions.

---

## Session 12: Phase 2 Complete — Posts Mirrored, Substack Links Internalized

*2026-06-01*

**Tracks:** cloudflare-migration, content-sync

- **117 Substack posts fully mirrored to D1 + R2:** `scripts/mirror-substack.py` reads c3po's `api_metadata.json` and export HTML files, mirrors images to R2, uploads body HTML to `posts/{slug}/body.html` in R2, and writes metadata to D1. Body HTML stored in R2 rather than D1 due to D1's 100KB SQL statement limit — D1 stores a `body_r2_key` pointer instead. State tracked in `data/mirror_state.json` for resumable runs. Two posts without export files (`irrigation-by-protocol-when-vineyards`, `the-overloaded-train`) fetched from the Substack API. Fix script (`fix-missing-body-r2.py`) patched 115 posts that had D1 rows without `body_r2_key` from earlier failed runs.

- **New Worker routes for magazine content:** `/magazine` queries D1 for all posts (ordered by date) and renders a card list with cover image, section badge, byline, and subtitle. `/p/:slug` fetches body HTML from R2 via the `FILES` R2 binding and renders it with Tailwind Typography prose styles. Falls back gracefully if body is missing. Prev/next navigation uses `previous_slug`/`next_slug` from D1. R2 bucket binding added to `wrangler.toml`.

- **All Substack clickthroughs eliminated:** Added `substackToInternalUrl()` helper in `static-pages.tsx` that detects `protocolized.summerofprotocols.com/p/{slug}` URLs and rewrites them to internal `/p/{slug}` routes. Applied throughout: homepage carousel cards, resource index cards, and resource detail page primary action all resolve to `/p/:slug` instead of opening Substack. Article resource cards now link directly to the post page, bypassing the resource detail page. &ldquo;View on Substack&rdquo; demoted to a small inline link in the post byline (author &middot; date &middot; View on Substack &uarr;).

- **Fixed Worker crash on `/magazine` and `/p/:slug`:** `getLatestPosts()` and `getAdjacentPosts()` use partial column SELECTs (no `enriched_categories`, `substack_categories`, or `authors`), but `parsePostRow()` called `JSON.parse()` on those columns unconditionally — causing `SyntaxError: &quot;undefined&quot; is not valid JSON`. Fixed by guarding all JSON parses with null checks and fallback empty arrays.

---

## Session 13: Domain Cutover, Sync Overhaul, Books Section

*2026-06-09*

**Tracks:** cloudflare-migration, content-sync, ux

- **`protocolized.io` now served by the Hono Worker.** The site had been on GitHub Pages (4 A records at 185.199.x.x) with Cloudflare proxying in front — the CF Pages project existed but was not receiving traffic. To cut over: deleted the 4 GitHub Pages A records in the CF DNS tab, then added `protocolized.io` and `www.protocolized.io` as custom domains on the Worker in the CF dashboard. CF Pages project remains as an instant rollback (30-second domain flip), but the Astro static build no longer serves live traffic.

- **Homepage carousel was querying the wrong table.** `getLatestArticles()` queried `resources WHERE type = 'article'` — those are research library entries, not magazine posts. The carousel was either empty or showing stale library articles. Fix: home route now calls `getLatestPosts()` against the `posts` table; `home.tsx` updated to accept `Post[]` instead of `Resource[]` and render `cover_image`/`subtitle` fields.

- **Three changes make the sync pipeline end-to-end:** (1) `deploy.yml` replaced the old GitHub Pages workflow with a Worker deploy (`npm run deploy` from `worker/`). (2) `sync-substack.py` now dual-writes: after creating a Markdown file for each new post, it calls the Substack API to fetch body HTML and cover image, mirrors both to R2, and writes metadata to D1 — gated on `CLOUDFLARE_API_TOKEN` being present so local runs still work. (3) `CLOUDFLARE_API_TOKEN` added as a GitHub Actions secret via `gh secret set`. Three posts that had accumulated since the last D1 write (Jun 1, 3, 9) were backfilled manually via a one-time `add-new-posts.py` script (since deleted).

- **New `/books` section with index and detail pages.** D1 `books` table: `slug`, `title`, `subtitle`, `editor`, `date`, `description`, `body` (markdown), `cover_image`, `url`, `file` (R2 PDF), `toc` (JSON array of `{title, author?, url?}`), `contributors` (JSON), `tags` (for related-resources query), `sort_order`, `published`. Index page: 2–3 col grid with 2:3 cover placeholder, clipped description. Detail page: cover + meta left, body/ToC/contributors/related resources right; download button when `file` or `url` present. ToC entries link to internal `/p/:slug` routes where stories are already mirrored. Four books seeded: *The Protocol Reader* (published), *Terminological Twists*, *The Librarians*, *Ghosts in Machines* (all published with full ToC and contributors); *Bridges* stub unpublished. Books added to nav and footer.

---

## Session 14: Hono Migration Audit, Series Navigation, Jamverse Integration

*2026-06-10*

**Tracks:** cloudflare-migration, ux, framework

- **Three features missing from the Hono Worker were identified and restored:** (1) **Protocol Lexicon page** (`/resources/protocol-lexicon`) was 404-looping — the Worker scaffold had a comment saying it would be served as a static asset, but no static HTML was ever created and the route redirected to itself. Fixed by creating `worker/src/html/lexicon.tsx`: Hono JSX component that server-renders all 566 term cards from `worker/public/lexicon.json` (imported at build time via `resolveJsonModule: true`), with a spotlight card that fetches `/lexicon.json` client-side and DOM-based search. A trailing-slash redirect was also needed (`/resources/protocol-lexicon/` → canonical). (2) **Sitemap** was frozen at scaffold time and missing 120+ URLs: all `/p/:slug` posts, `/books` and `/books/:slug`, and `/resources/protocol-lexicon`. Sitemap route now queries D1 for all three tables in parallel and emits 421 URLs. (3) **`/api/lexicon.json`** path had moved to `/lexicon.json` during migration — added a 301 redirect for backward compatibility.

- **Series reading navigation scaffolded for four story cycles that form the Jamverse extended universe at jamverse.protocolized.io.** Architecture: two new columns on the `posts` D1 table (`series_slug TEXT`, `series_position INTEGER`) with a covering index. Each story cycle is registered as a book in the `books` table (4 new entries: Trainverse / Sachin Benny, Legends &amp; Ledgers / Elizabeth Maher, Zoothesia / Spencer Nitkey, Stockton Chronicles / Randy Lubin). A new `getSeriesContext()` DB helper runs 3 parallel D1 queries — book title+TOC, prev post, next post by position — and falls back to the book TOC for stories not in D1 (e.g. external Randy Lubin stories). Post pages with `series_slug` set receive a compact `SeriesNav` component rendered at both top and bottom: `&lt;&lt; prev | ↑ Series Title (Part N of M) | next &gt;&gt;`. Breadcrumb updates to `Home › Books › {Series} › {Title}` for series posts. 12 posts tagged with series data via D1 UPDATE.

- **The Caucus and Joan Henry vs the Algorithm are published on Randy Lubin's site, not yet on the Protocolized Substack.** Rather than breaking the series reading experience with external redirects, two internal placeholder pages were created (`/p/the-caucus`, `/p/joan-henry-vs-the-algorithm`) with full series navigation and a styled &ldquo;Coming soon to Protocolized&rdquo; card linking out to randylubin.com. A new `is_placeholder INTEGER DEFAULT 0` column on posts controls three behaviors: (1) placeholder posts are excluded from the magazine feed and sitemap; (2) `post.tsx` shows the coming-soon card instead of body content; (3) `sync-substack.py` changed from `INSERT OR REPLACE` (delete+insert, wiped all columns) to `INSERT ... ON CONFLICT(slug) DO UPDATE SET` listing only content fields — this preserves `series_slug`, `series_position`, and resets `is_placeholder = 0` when the real Substack post arrives. No manual steps needed when those stories eventually publish.

- **PR #1 submitted to Protocol-Institute/jamverse** replacing all 14 story URLs across 7 HTML files. 12 Substack URLs (`protocolized.summerofprotocols.com/p/*`) replaced with `protocolized.io/p/*`; 2 Randy Lubin URLs (`randylubin.com/fiction/...`) replaced with the new internal placeholder pages. The `devlog.html` in jamverse was left unchanged — it contains a text-only historical reference to randylubin.com, not a navigation link. Sachin Benny (lead dev on jamverse) set as PR reviewer.

---

## Session 15: Inbox System, Book Covers, Books Category Tag

*2026-06-12*

**Tracks:** operations, ux

- **Added `inbox/` as a gitignored drop zone for files Venkat wants processed between sessions** (covers, PDFs, content, etc.). CLAUDE.md session-start checklist updated: step 3 is now &ldquo;scan `inbox/` and handle anything present.&rdquo; The inbox is not committed — files are processed (uploaded to R2, etc.) and recorded in the session wrap-up, then left for manual cleanup.

- **Three cover images were processed from inbox and uploaded to R2** at `covers/{slug}.jpg` (served at `files.protocolized.io/covers/`): `ghosts-in-machines.jpg`, `the-librarians.jpg`, `terminological-twists.jpg`. D1 `books` table updated with `cover_image` URLs for all three. The-protocol-reader and the 4 Jamverse series books still have no cover.

- **Added a `category` column to the D1 `books` table** (`TEXT NOT NULL DEFAULT 'fiction'`) via `ALTER TABLE`. `the-protocol-reader` set to `'nonfiction'`; all others default to `'fiction'`. Schema updated in `schema.sql`; TypeScript updated in `db.ts` (`Book` interface, `BookRow`, `parseBookRow`). UI: a small pill badge appears next to the title on the books index card and in the metadata row on the book detail page. The field is open-ended — future nonfiction books just need `category = 'nonfiction'` set on insert.

---

## Session 16: ePub Downloads, Book Thumbnails, Inbox Policy

*2026-06-12*

**Tracks:** operations, ux

- **Four books now have downloadable ePubs served from R2 at `files.protocolized.io/epubs/{slug}.epub`:** *Ghosts in Machines*, *The Librarians*, *Terminological Twists*, and *The Protocol Reader*. Files uploaded via `wrangler r2 object put --remote` with `content-type: application/epub+zip`. D1 `books.file` field set for all four. The Substack collections placeholder URL (`protocolized.summerofprotocols.com/p/collections`) and the SoP URL on Protocol Reader were nulled out — book pages will only link to locally served files or real retail buy links, never to Substack. The `url` field is reserved for future retail links (e.g. Amazon, Bookshop.org).

- **The single CTA on book detail pages was replaced with two independent buttons.** Previously the logic collapsed `file` and `url` into a single link (file took priority). Now: if `book.file` is set, a primary &ldquo;Download ePub&rdquo; / &ldquo;Download PDF&rdquo; button is shown (label auto-detected from extension; `download` attribute forces browser download rather than inline open). If `book.url` is set, a secondary &ldquo;Get the book &rarr;&rdquo; button is shown as an external link. Each appears independently, so books with only a file, only a URL, or both are all handled correctly without extra logic.

- **The /books index cards were redesigned from tall portrait cards to compact horizontal thumbnail cards.** Previously each card was `flex flex-col` with an `aspect-[2/3]` image container — on a 3-column grid, the cover dominated the card at ~450px tall. Now each card is a horizontal row: a small `w-20 h-28` (sm: `w-24 h-36`) cover thumbnail on the left, title/subtitle/blurb text on the right. Grid reduced from `lg:grid-cols-3` to max `sm:grid-cols-2`. Detail pages retain the original `lg:w-64` large cover.

- **Established and documented a formal inbox processing policy in CLAUDE.md.** Rule: after handling any file from `inbox/`, move it to `inbox/.processed/` immediately — never leave processed files in the inbox root, never delete from `.processed/` (it is a local-only record; the directory is gitignored). Files with no clear action are left in inbox and flagged in the session summary. The policy was triggered by processed cover images from Session 15 being left in the inbox root.

---

## Session 17: Masthead, mixed carousel, PDF covers, branding cleanup

*2026-06-14*

**Tracks:** ux, framework, operations

- **Added the site name and tagline to the nav bar in `base.tsx`**, making it appear on every page. The logo link now shows the Protocolized mark image + &ldquo;Protocolized&rdquo; in Instrument Serif (`text-xl`) + &ldquo;The Protocol Institute media hub&rdquo; in a smaller italic serif below. This is the single canonical masthead — no per-page duplication.

- **Replaced the magazine-only carousel with a 4-source round-robin**: latest 3 magazine posts, latest 2 YouTube videos, 2 random archive PDFs, 1 random book. Sources are interleaved (M→Y→A→B→M→Y→A→M) so all types always appear. Each slide has a source badge overlaid on the image: teal for magazine, red for YouTube, coral for archive, grey for book. Captions: &ldquo;Latest from magazine&rdquo;, &ldquo;Latest from YouTube channel&rdquo;, &ldquo;Resource Archive spotlight&rdquo;, &ldquo;Book spotlight&rdquo;. Archive and book slides are randomly sampled on each page load. Unified `CarouselItem` type in `home.tsx`; `buildCarouselItems()` handles interleaving.

- **New `worker/src/youtube.ts` fetches the Protocol Institute YouTube channel RSS feed** (`channel_id=UCcNZ6wTbeeAJ-O_OIhs2j3A`, i.e. `@protocol-institute`) at Worker request time. Uses `cf: { cacheTtl: 3600, cacheEverything: true }` to edge-cache the RSS for 1 hour — no API key required, no D1 writes. Video thumbnails come from `i.ytimg.com/vi/{id}/hqdefault.jpg` (free, no auth). The parser uses regex splits on `&lt;entry&gt;` tags; no DOM parser needed in Workers.

- **New script `scripts/generate-pdf-covers.py` renders page 1 of each PDF resource as a JPEG** using PyMuPDF (fitz). For each resource with `file LIKE '%.pdf'`: downloads from `files.protocolized.io`, renders at 900px wide, uploads to R2 at `covers/{slug}.jpg`, updates D1 `thumbnail` field. All 72 PDFs processed in one run (0 failures). Thumbnails now live at `files.protocolized.io/covers/{slug}.jpg`. The script auto-loads `CLOUDFLARE_API_TOKEN` from `../admin/.env.keys` if not in env; skips already-thumbnailed resources by default; supports `--all` and `--slug` flags.

- **Added `getRandomArchiveResources(db, limit)` and `getRandomBooks(db, limit)` to `db.ts`**. Archive query: `WHERE file LIKE '%.pdf' AND thumbnail IS NOT NULL ORDER BY RANDOM()`. Books query: `WHERE published = 1 AND cover_image IS NOT NULL ORDER BY RANDOM()`. D1 supports `RANDOM()` natively; no application-side shuffle needed.

- **Fixed carousel column clipping at intermediate viewport widths.** Root cause: `lg:w-5/12 + lg:w-7/12 = 100%` but the `gap-16` (64px) between columns was additive, pushing the carousel past the container edge. Fix: carousel column changed from `lg:w-7/12` to `flex-1 min-w-0`; `min-w-0` added to both the flex container and the left column. The carousel now correctly takes the remaining space after the left column and gap.

- **Simplified the hero left column**: removed &ldquo;Accelerating Order.&rdquo; subheadline, replaced body copy with inline-linked media hub description (&ldquo;Protocolized is the media hub for the Protocol Institute. Explore our research archive, our magazine (also available on Substack), YouTube channel and book collection.&rdquo;), removed both CTA buttons. All five link targets wired: Protocol Institute (external), /resources, /magazine, Substack (external), /books.

- **Community page stripped down to Discord only.** Nav and footer label changed from &ldquo;Community&rdquo; to &ldquo;Discord&rdquo; (slug `/community` unchanged). YouTube section, Events section, and footer note removed. Page title/h1 updated to &ldquo;Discord&rdquo;. Discord invite URL updated sitewide to `discord.gg/Z3fgsW8D4s` (was `Aj5FbGsNYV`).

- **Fixed three wrong URLs that were consistent across the codebase:** (1) Protocol Institute link was `protocolsociety.org` in About page and footer — corrected to `protocol-institute.org` everywhere. (2) YouTube handle was `@protocolized` throughout — corrected to `@protocol-institute`. (3) Discord invite was stale — updated to `Z3fgsW8D4s` in all files (base.tsx, home.tsx, static-pages.tsx, index.tsx).

---
