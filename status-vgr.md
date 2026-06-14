# Status — vgr (Venkat)

## Active
<!-- current tasks or in-progress work -->

## Upcoming

### Carousel & Resources — next session
- **Books in carousel:** books have no PDF so no banner — need a composite generated from cover_image + title/author (same layout, but source is the book cover JPG from R2 `covers/` rather than a PDF render); update `getRandomBooks` path to use these
- **Magazine articles in carousel:** posts have cover images but no banner composites — generate post banners (title + author + section badge) so they display consistently with resource banners; or special-case them in carousel to use their native cover differently
- **YouTube in resources:** add YouTube videos as first-class resources (type=`talk` or new `video` type); either manual entries or auto-sync from the YouTube RSS feed already wired for the carousel; add to filterable resource library

### Books
- Add content + cover images for Bridges (slug seeded, `published = 0`)
- Add cover images for 4 Jamverse series books (Trainverse, Legends & Ledgers, Zoothesia, Stockton Chronicles)
- Add buy links (`url`) for books when available (Substack URLs removed; only local epubs + real retail links should appear)

### Jamverse / Series
- Jamverse PR #1 (update story links to protocolized.io) awaiting Sachin Benny review/merge
- When Stockton Chronicles ch.2+3 publish on Substack: sync auto-populates, series data already set — no extra steps needed
- After merge, confirm jamverse.protocolized.io story links work end-to-end

### Infrastructure
- Automate `migrate-to-d1.py` on push when `src/content/resources/` changes (GH Actions job)

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
- **2026-06-14** — Session 18. Nav: replaced About with YouTube (external link, new tab). About page rewritten to single compact paragraph with two inline links. Homepage cleanup: removed Featured Resources section, Protocolized Magazine section, and social-links footer section. Renamed "Where do you want to start?" → "Quick Start Pages". Footer replaced with single minimal row: copyright + Protocol Institute | llms.txt | RSS feed (with icon). Resource metadata audit: fixed 22 resources with cover-page boilerplate descriptions, 4 case files with garbled no-space descriptions, Steiert (title → "Protocols in (Emergency) Time", author → Olivia Steiert), Lang (title → "Standards Make the World"), "Unreasonable Sufficiency" (author → Rao/Beiko/Stark/Van Epps/Aue/Ryan). Deleted duplicate steiert-1 resource. All fixes applied to D1. Banner generation: wrote scripts/generate-banners.py; 1200×600 composites (teal cover panel + Georgia title + italic authors, vertically centred); generated 71 banners uploaded to R2 banners/{slug}.jpg, D1 thumbnail updated. Resource detail page now shows banner above Download CTA.
- **2026-06-14** — Session 17. Branding + carousel overhaul. Masthead: added "Protocolized" wordmark + tagline "The Protocol Institute media hub" next to logo in Nav (single-source, base.tsx). Mixed carousel: 4 sources round-robin interleaved — magazine (latest 3), YouTube (latest 2), resource archive (random 2), books (random 1) — each with source badge and caption. YouTube integration via RSS feed from `@protocol-institute` channel with CF edge cache. PDF cover generation: installed PyMuPDF, wrote `scripts/generate-pdf-covers.py`, rendered page 1 of all 72 PDFs → R2 `covers/{slug}.jpg` → D1 `thumbnail` updated (72/72 succeeded). Added `getRandomArchiveResources` + `getRandomBooks` to db.ts. Fixed carousel column overflow (flex-1 min-w-0). Landing page blurb rewritten as inline-linked media hub description; subhead and buttons removed. Community page renamed "Discord" in nav/footer (slug unchanged), stripped to Discord only. Fixed URLs sitewide: Discord invite → `Z3fgsW8D4s`, YouTube → `@protocol-institute`, Protocol Institute → `protocol-institute.org`.
- **2026-06-12** — Session 16. ePub downloads for 4 books: ghosts-in-machines, the-librarians, terminological-twists, the-protocol-reader — all uploaded to R2 (`epubs/*.epub`), D1 `file` field set, Substack placeholder URLs nulled on all books. Protocol Reader cover image uploaded (R2 `covers/the-protocol-reader.jpg`). Books index redesigned: cards now horizontal with small thumbnail (w-20/w-24) instead of tall aspect-[2/3] portrait; grid reduced to 2-col. Book detail CTA split into two buttons: "Download ePub"/"Download PDF" (primary, with `download` attr) and "Get the book →" (secondary, external) shown independently. Inbox processing policy documented in CLAUDE.md: always move to `inbox/.processed/` on completion.
- **2026-06-12** — Session 15. Inbox system: added `inbox/` drop zone (gitignored), CLAUDE.md updated to scan it at session start. Processed 3 book covers from inbox: ghosts-in-machines, the-librarians, terminological-twists uploaded to R2 (`covers/*.jpg`), D1 `cover_image` updated on all 3. Added `category` column to D1 `books` table (ALTER TABLE, default `'fiction'`); `the-protocol-reader` set to `'nonfiction'`. Schema.sql, db.ts (Book interface + BookRow + parseBookRow), and books.tsx (badge on card + detail page) all updated. Worker deployed.
- **2026-06-10** — Session 14. Hono migration audit: restored lexicon page (was 404-looping), fixed sitemap (now includes /books, /p/:slug × 120, /resources/protocol-lexicon), added /api/lexicon.json redirect. Series navigation for 4 Jamverse story cycles: Trainverse, Legends & Ledgers, Zoothesia, Stockton Chronicles — 4 new books in D1, series_slug/series_position on posts, SeriesNav component top+bottom of post pages, breadcrumb updated. Placeholder pages for un-mirrored Stockton ch.2+3 (is_placeholder column, "coming soon" display, sync script fixed to upsert preserving series data). PR #1 submitted to jamverse repo pointing all 14 story links to protocolized.io mirrors; Sachin Benny as reviewer.
- **2026-06-09** — Session 13. Domain cutover complete: protocolized.io now served by Hono Worker (deleted conflicting GitHub Pages A records, added custom domain in CF dashboard). Carousel fixed (was querying resources type=article; now queries posts table). Backfilled 3 missing posts (Jun 1/3/9) to D1+R2 via Substack API. Sync pipeline overhauled: deploy.yml replaced GH Pages workflow with Worker deploy; sync-substack.py now dual-writes Markdown + D1+R2 after each new post; CLOUDFLARE_API_TOKEN added as GH Actions secret. Removed add-new-posts.py (one-time script). Books section launched: /books index + /books/:slug detail pages; D1 books table; 4 books seeded (Protocol Reader + 3 fiction collections with linked ToCs; Bridges stub unpublished). Books added to nav and footer.
- **2026-06-01** — Session 12. Phase 2 complete + UX fixes. 117 posts mirrored to D1 + R2 (body HTML at `posts/{slug}/body.html`). Fixed JSON parse crash on partial D1 SELECTs. Substack clickthroughs eliminated: carousel, resource cards, and resource detail pages all resolve Substack post URLs to internal `/p/:slug`. Article resource cards skip detail page and go directly to post. "View on Substack" demoted to inline byline link. All 117 posts confirmed serving body content (2 newest fetched from Substack API, rest from export files).
- **2026-06-01** — Session 11. Confirmed domain cutover is not a blocker — Phase 2 + full feature parity first, then cut over. GH Pages disabled; PDF/EPUB git history purged (confirmed done last session).
- **2026-06-01** — Session 10 (9:30–10:20am PT). Phase 1 complete: D1 created, 288 resources migrated, Worker deployed to `protocolized-website.team-7e8.workers.dev`. Fixed index.ts→tsx + skipLibCheck. Backfilled 117 Substack cover images into resources.thumbnail. Reviewed Substack API access vs c3po; merged c3po plan into `plans/phase2-substack-mirror.md`. Fresh export unzipped to `data/substack/` (138 posts). Pending: move protocolized.io domain to Worker in CF dashboard; then Phase 2 (Substack post mirror).
- **2026-05-31** — Session 8: C3PO Worker migrated to PI org CF account; c3po.protocolized.io subdomain live; resources page link updated.
- **2026-05-31** — Session 9 (partial). Hono Worker scaffolded: all source files written (`worker/src/index.ts`, `db.ts`, `html/base.tsx`, `home.tsx`, `resources.tsx`, `resource.tsx`, `static-pages.tsx`), plus `schema.sql`, `wrangler.toml`, `package.json`, `tsconfig.json`, `tailwind.config.mjs`. `scripts/migrate-to-d1.py` written. `npm install` done in `worker/`. CSS compiled (`worker/public/style.css`). **Paused before D1 creation and local test.** Resume at: copy static assets → create D1 → apply schema → run migration → `wrangler dev` → deploy.
- **2026-05-30** — Session 7. CF Pages migration complete: protocolized.io live on CF Pages (PI org account). All 82 PDFs + 4 EPUBs migrated to R2 bucket `protocolized-resources`, served at `files.protocolized.io`. 76 resource frontmatter `file:` fields rewritten to R2 URLs. PDFs removed from repo and history purged via git-filter-repo (repo: 353 MB → 1 MB). Framework decision: Hono + HTMX (Option B). SoP content gap analysis: 21 items identified — 4 essays, Bridge Atlas ep 2-5, 17 pills added to Upcoming backlog; 7 items written to `../website/sop-migration.md` for protocol-institute.org. ROADMAP.md updated (Phase 0+1 ✓, Phase 8 added). Hono migration plan written to `worker/PLAN.md`. Next: implement Hono Worker (target: before Monday 8am UTC cron).
- **2026-05-20** — Built Protocol Lexicon page (`/resources/protocol-lexicon/`): 561 terms (233 PI-coined, 320 PI-specific, 8 curated), merged from c3po corpus triage + existing 46-term hand-curated md. Static Astro page with spotlight card (random shuffle), live search, A-Z index bar, 2-col card grid, triage badges, source links. JSON backend at `/api/lexicon.json`. Build script at `scripts/build-lexicon.py`.
- **2026-05-19** — Added C-3PO bot link box to top of resources page sidebar (`src/pages/resources/index.astro`). Beta-labeled, teal/coral styling, links to `https://c3po.vgr-702.workers.dev?ref=protocolized-resources` (new tab). URL tagged for traffic source tracking.
- **2026-05-14** — Added devlog system (data/devlog.json, devlog_session.py, devlog_render.py). Backfilled Sessions 1–4 from git history. Added startup and wrap-up rituals to CLAUDE.md. CLAUDE.md updated with PI admin repo banner (../admin/keys.md, ../admin/security.md).
- **2026-05-14** — Created Cloudflare Pages migration branch (`feat/cloudflare-migration`) with updated `deploy.yml` (cloudflare/pages-action@v1), `wrangler.toml` (with C3PO and R2 service binding stubs), `MIGRATION.md`, and GitHub Issues #1 (migration discussion) and #2 (Timber task for CF account/domain setup). Migration requires Timber to transfer protocolized.io nameservers to Cloudflare.
