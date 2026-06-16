# Protocolized — CLAUDE.md

> **PI key registry & security policy:** see [`../admin/keys.md`](../admin/keys.md) and [`../admin/security.md`](../admin/security.md) . Do not register PI keys in `Code/.env.keys`.

## What is this project?

Protocolized is the website for a sci-fi and thinkpiece magazine and research library on protocols, published by the Protocol Institute. It lives at [protocolized.io](https://protocolized.io).

The site has two main sections:
1. **Magazine** — stories, articles, and columns synced daily from the Protocolized Substack
2. **Research library** — 280 resources (papers, talks, frameworks, datasets, etc.) from the Summer of Protocols program

## Incoming Redirects — summerofprotocols.com

`summerofprotocols.com` is being migrated to Cloudflare and will then redirect to
`protocolized.io` (catch-all) and `protocol-institute.org` (specific institutional
paths). This site receives the **catch-all** — most unmapped SoP URLs will land here.

Paths explicitly redirected here:
- `/research/*` and `/essays/*` → `/resources`
- All other unmapped SoP paths → `/` (homepage)

**Implication for this project:** the `/resources` page and homepage will receive
inbound traffic from old summerofprotocols.com links. Keep those pages functional
and well-described. If a resource that lived on SoP is missing from the library,
it should be added before the redirect goes live.

Full redirect mapping and implementation plan: `../admin/sop-domain-migration.md`.

---

## Stack

**Current (live fallback):**
- **Framework**: Astro 5.x (static output)
- **Styling**: Tailwind CSS 3.x with custom design tokens
- **Content**: Astro Content Collections (Markdown files in `src/content/resources/`)
- **Search**: Fuse.js for client-side fuzzy search
- **Deploy**: Cloudflare Pages (CF Pages project `protocolized-website`, PI org account)
- **Node**: v22 (CI uses `node-version: 22`; locally via nvm)

**Worker (deployed, pending domain cutover):**
- **Framework**: Hono + JSX on Cloudflare Workers (`worker/src/index.tsx`)
- **Content**: D1 database `protocolized-resources` (id: `1b47f2d7-9c84-4078-a27a-2f3eea9f41b7`); 288 resources + 117 posts migrated. Post body HTML in R2 at `posts/{slug}/body.html`; D1 stores `body_r2_key` pointer (avoids 100KB statement limit).
- **Deploy**: Live at `https://protocolized-website.team-7e8.workers.dev`; Astro CF Pages stays as fallback until `protocolized.io` custom domain is moved to Worker in CF dashboard
- **Status (2026-06-10):** Domain cutover complete — `protocolized.io` now served by Worker. Phase 2 complete. All 117 posts + 3 backfilled (Jun 1/3/9) in D1+R2. `sync-substack.py` dual-writes Markdown + D1+R2 on each new post (uses ON CONFLICT upsert to preserve `series_slug`/`series_position`/`is_placeholder`). `deploy.yml` deploys Worker on push to main. `CLOUDFLARE_API_TOKEN` set as GH Actions secret. Books section live at `/books` with D1 `books` table. 4 series books added (Trainverse, Legends & Ledgers, Zoothesia, Stockton Chronicles) for Jamverse extended universe. Posts table has `series_slug`, `series_position`, `is_placeholder` columns for series navigation. Protocol Lexicon live at `/resources/protocol-lexicon`.

## Commands

**Astro (root):**
```sh
npm install       # install dependencies
npm run dev       # start dev server on http://localhost:4321
npm run build     # production build to dist/
npm run preview   # preview production build locally
```

**Worker (from `worker/`):**
```sh
npm install           # install worker dependencies
npm run build:css     # compile Tailwind → public/style.css
npm run dev           # wrangler dev (local miniflare D1)
npm run deploy        # build CSS + wrangler deploy (requires CLOUDFLARE_API_TOKEN)
```

**D1 (from `worker/`, requires CLOUDFLARE_API_TOKEN):**
```sh
wrangler d1 create protocolized-resources          # one-time: create DB, capture ID
wrangler d1 execute protocolized-resources --file=schema.sql --remote
# then from repo root:
python3 scripts/migrate-to-d1.py --remote          # import all resources (310 as of Session 19)
```

## Project structure

```
src/
├── components/        # Astro components (Nav, Footer, ResourceCard, BadgeType, etc.)
├── content/
│   ├── config.ts      # Zod schema for the resources collection
│   └── resources/     # 310 Markdown resource files (Session 19)
├── layouts/
│   ├── Base.astro     # HTML shell (fonts, JSON-LD, nav/footer)
│   └── Resource.astro # Resource detail page layout
├── pages/
│   ├── index.astro          # Home page
│   ├── about.astro          # About page
│   ├── community.astro      # Community page
│   ├── magazine.astro       # Magazine page
│   ├── anthologies.astro    # Anthologies page
│   ├── resources/
│   │   ├── index.astro      # Filterable resource library (vanilla JS)
│   │   └── [slug].astro     # Resource detail pages
│   ├── api/resources.json.ts # JSON API endpoint
│   ├── llms.txt.ts          # LLM-readable site summary
│   └── rss.xml.ts           # RSS feed
scripts/
├── sync-substack.py    # Syncs Substack RSS → resource Markdown files
├── build-lexicon.py    # Builds /api/lexicon.json from corpus triage data
└── migrate-to-d1.py   # One-time: imports all 288 resources to D1
worker/                # Hono CF Worker (in-progress replacement for Astro)
├── src/
│   ├── index.ts        # All routes
│   ├── db.ts           # D1 query helpers
│   └── html/           # Hono JSX page components
├── public/             # Static assets (style.css, logo, robots.txt, lexicon)
├── schema.sql          # D1 DDL
├── wrangler.toml       # Worker config (update database_id after D1 create)
└── package.json
data/
└── devlog.json         # Session devlog (rendered at /devlog by scripts/devlog_render.py)
scripts/
├── generate-banners.py          # 1200×600 banner composites for PDF resources → R2 banners/{slug}.jpg
├── generate-book-banners.py     # Same layout for books → R2 banners/books/{slug}.jpg
├── generate-pdf-covers.py       # PDF page-1 renders → R2 covers/{slug}.jpg
├── sync-youtube-resources.py    # Pull c3po YouTube enriched_meta → resource Markdown + R2 thumbnails
├── sync-pdf-resources.py        # Pull c3po PDF enriched_meta → update resource descriptions + tags
├── sync-substack-resources.py   # Pull c3po Substack enriched_meta → resource Markdown (all post types)
└── migrate-to-d1.py             # Sync all resource Markdown → D1 resources table
.github/workflows/
├── deploy.yml          # Build & deploy Worker on push to main
└── sync-substack.yml   # Daily cron to sync new Substack posts (posts table + Markdown)
```

## Design tokens

| Token         | Value                                          |
|---------------|------------------------------------------------|
| Primary       | `#0F6E56` (teal)                               |
| Primary light | `#E1F5EE`                                      |
| Accent        | `#D85A30` (coral)                              |
| Surface       | `#F9F8F5`                                      |
| Dark          | `#2C2C2A`                                      |
| Display font  | Instrument Serif                               |
| Body font     | Lora                                           |
| UI font       | Outfit                                         |
| Mono font     | JetBrains Mono                                 |

All tokens are defined in `tailwind.config.mjs`.

## Resource content schema

Each resource is a Markdown file in `src/content/resources/`. Frontmatter fields (defined in `src/content/config.ts`):

| Field         | Type                | Required | Notes                                                             |
|---------------|---------------------|----------|-------------------------------------------------------------------|
| `title`       | string              | yes      |                                                                   |
| `type`        | enum                | yes      | paper, working-paper, framework, workshop-template, game, dataset, interview, presentation, code, image, prompt-template, talk, lecture, article, fiction, living-document |
| `authors`     | array of {name, url?} | yes    |                                                                   |
| `date`        | date                | yes      | YYYY-MM-DD                                                        |
| `description` | string              | yes      |                                                                   |
| `tags`        | string[]            | yes      |                                                                   |
| `audience`    | enum[]              | yes      | researcher, practitioner, academic, corporate                     |
| `featured`    | boolean             | no       | Defaults to false                                                 |
| `file`        | string              | no       | Path to a downloadable file (e.g. PDF)                            |
| `url`         | string              | no       | External link                                                     |
| `thumbnail`   | string              | no       | Image URL                                                         |

## Resource enrichment pipeline (c3po → protocolized-website)

**c3po is the canonical enrichment source.** New content should be ingested through c3po first. Three sync scripts pull enriched metadata back into the resource library:

| Content type | c3po source | sync script |
|---|---|---|
| YouTube videos | `c3po/sources/youtube/enriched_meta.json` | `scripts/sync-youtube-resources.py` |
| PDFs | `c3po/sources/pdfs/enriched_meta.json` | `scripts/sync-pdf-resources.py` |
| Substack posts | `c3po/sources/substack/enriched_meta.json` | `scripts/sync-substack-resources.py` |

After any sync script: run `python3 scripts/migrate-to-d1.py --remote`. See `c3po/plans/resource-pipeline.md` for the full architecture.

**D1 books table columns** (as of Session 19): slug, title, subtitle, editor, date, description, body, cover_image, url, file, toc, contributors, tags, sort_order, published, category, banner, cta_label.

## Conventions

- Pages use Astro's file-based routing. No client-side framework — interactivity is vanilla JS.
- Filtering on the resource library page is done with vanilla JS and Fuse.js, not a framework.
- The Substack sync script (`scripts/sync-substack.py`) runs via GitHub Actions on a daily cron. It can also be run manually with `python3 scripts/sync-substack.py`.
- Commits from the sync bot use the message format: `chore: sync N new Substack post(s) from Protocolized`.
- The build must produce zero errors. Run `npm run build` before pushing.

## At Session Start

1. Read `status-vgr.md` — review active and upcoming items.
2. Check Substack sync activity since last session:
   ```bash
   git log --oneline --grep="sync" -10
   ```
3. **Scan `inbox/`** — Venkat drops files here between sessions (covers, assets, content). List contents and handle anything present before starting other work. The inbox is gitignored; files should be processed (uploaded to R2, etc.) and noted in the session wrap-up.
   - **Processing policy:** after handling any file, move it to `inbox/.processed/` immediately — do not leave processed files in the root of `inbox/`. Never delete from `.processed/` (it's a local record; gitignored). If a file in `inbox/` has no clear action yet, leave it and flag it in the session summary.
4. If Hono Worker work is ongoing, check `worker/PLAN.md` and `worker/wrangler.toml` for current implementation state (esp. whether `database_id` has been filled in yet).
5. For any wrangler/CF ops, export the API token from the org key store:
   ```sh
   export CLOUDFLARE_API_TOKEN=$(grep CLOUDFLARE_API_TOKEN ../../.env.keys | cut -d= -f2)
   ```
6. Summarize to Venkat: inbox contents + action taken, sync activity, active items from `status-vgr.md`, and Worker migration progress.

---

## After Each Session

**Before starting wrap-up:** Do not initiate wrap-up unilaterally. Wait until Venkat says to wrap up or asks "what did we do."

**Checklist — complete in order:**

1. **`status-vgr.md`** — add a dated entry to the Done section. Move any completed Upcoming items to Done.
2. **`CLAUDE.md`** — update stack notes, Worker status, schema changes, or deployment info if anything changed.
3. **`data/devlog.json`** — append a new session record (see schema below). **Never skip.** This is the load-bearing architectural record.
4. **Regenerate devlog:** `python3 devlog_render.py` from repo root (updates the rendered devlog page).
5. **Repo** — `git add` relevant files (never `.env`); `git commit`; `git push origin main`.
6. **Memory** — save anything non-obvious about the Worker architecture, sync pipeline, schema decisions, or workflow preferences. Do not duplicate what's in CLAUDE.md or recoverable from code.

**Devlog JSON schema** (append to `data/devlog.json` → `sessions` array):

```json
{
  "id": <next integer>,
  "sort_key": <session_number as float>,
  "label": "Session N",
  "title": "Short descriptive title",
  "date": "YYYY-MM-DD",
  "time_pt": "",
  "tracks": ["cloudflare-migration" | "content-sync" | "c3po-integration" | "framework" | "operations" | "ux"],
  "costs_usd": {},
  "vector_counts": {},
  "deployed": true | false,
  "items": [
    { "title": "Component or decision name:", "html": "Explanation in HTML." }
  ]
}
```

**Devlog writing standard** — write `items` as if briefing a future engineer on architectural decisions, not just changes. Explain *why*, name the current state of the affected subsystem, and note anything that closes off alternatives or locks in a direction.

**Wrap-up report (never skip):**

After completing the checklist, report to Venkat with a table:

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | status-vgr.md | ✅ / ❌ | |
| 2 | CLAUDE.md | ✅ / ❌ / n/a | |
| 3 | devlog.json | ✅ / ❌ | |
| 4 | devlog_render.py | ✅ / ❌ | |
| 5 | git commit + push | ✅ / ❌ | |
| 6 | Memory updated | ✅ / ❌ / n/a | |

## Keys

**Policy:** All PI org keys are managed via the `/admin` project:
- **Registry** (names, owners, no values): `../admin/keys.md`
- **Values**: `../.env.keys` at the org root (`protocol-institute/.env.keys`). Dropbox-ignored, never committed.

To use keys locally, source the org-level file or copy needed keys into a local `.env` in this project root (gitignored):
```sh
export $(grep -v '^#' ../../.env.keys | xargs)   # source all org keys
# or just: export CLOUDFLARE_API_TOKEN=<value from ../.env.keys>
```

Current keys used by this project (values in `../.env.keys`):
- `CLOUDFLARE_API_TOKEN` — PI org CF token. Used by wrangler CLI and GitHub Actions deploy.
  - This token works for **wrangler** R2/D1 operations (`wrangler r2 object put`, `wrangler d1 execute`).
  - It does **not** work as boto3/S3-compatible API credentials. boto3 requires a separate R2 API token (`R2_ACCESS_KEY_ID` + `R2_SECRET_ACCESS_KEY`) created in CF dashboard → R2 → Manage API Tokens. As of 2026-06-01, no such token exists — R2 uploads use wrangler subprocess instead.

The PI org Cloudflare account ID (`7e8c7969b2464d23795c555bc6a32af8`) is set in `worker/wrangler.toml`.

## R2 Bucket

R2 bucket `protocolized-resources` is live and serving `files.protocolized.io`.
- PDFs and EPUBs: `files.protocolized.io/*.pdf` etc (migrated Session 7)
- Post images (Phase 2): will be at `files.protocolized.io/images/{hash[:2]}/{hash}.ext`
- Bucket is writable via `wrangler r2 object put protocolized-resources/key --file=... --remote`
- No separate R2 API token exists yet; if boto3 is needed for bulk uploads, create one in CF dashboard.

## Wrangler CLI

**Critical:** When a `wrangler.toml` is present in the CWD, wrangler 4.x defaults to
**local miniflare storage** for R2/D1 commands. Always use `--remote` for any operation
against live CF resources:

```bash
wrangler r2 object put bucket/key --file=... --remote
wrangler d1 execute DB_NAME --remote --file=schema.sql
wrangler d1 execute DB_NAME --remote --command="INSERT ..."
```

Omitting `--remote` silently succeeds but writes to `.wrangler/state/v3/` instead of CF.

## Things to watch out for

- Do NOT commit `.env` files or tokens of any kind.
- The `.claude/` directory is gitignored — it contains local Claude Code settings and should not be committed.
- The `raw_resources/` directory is gitignored — it contains source data used during the initial import.
- Resource slugs are derived from filenames. Renaming a resource file changes its URL.
