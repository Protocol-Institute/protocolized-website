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

**In-progress migration (see `worker/PLAN.md`):**
- **Framework**: Hono + HTMX on Cloudflare Workers
- **Content**: D1 database (`protocolized-resources`); 287 Markdown files migrating to D1
- **Deploy**: CF Worker with custom domain `protocolized.io`; Astro CF Pages stays as fallback until Worker is stable

## Commands

```sh
npm install       # install dependencies
npm run dev       # start dev server on http://localhost:4321
npm run build     # production build to dist/
npm run preview   # preview production build locally
```

## Project structure

```
src/
├── components/        # Astro components (Nav, Footer, ResourceCard, BadgeType, etc.)
├── content/
│   ├── config.ts      # Zod schema for the resources collection
│   └── resources/     # ~280 Markdown resource files
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
│   └── sync-substack.py     # Syncs Substack RSS → resource Markdown files
.github/workflows/
│   ├── deploy.yml           # Build & deploy to GitHub Pages on push to main
│   └── sync-substack.yml    # Daily cron to sync new Substack posts
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
| `type`        | enum                | yes      | paper, working-paper, framework, workshop-template, game, dataset, interview, presentation, code, image, prompt-template, talk, lecture, article, fiction |
| `authors`     | array of {name, url?} | yes    |                                                                   |
| `date`        | date                | yes      | YYYY-MM-DD                                                        |
| `description` | string              | yes      |                                                                   |
| `tags`        | string[]            | yes      |                                                                   |
| `audience`    | enum[]              | yes      | researcher, practitioner, academic, corporate                     |
| `featured`    | boolean             | no       | Defaults to false                                                 |
| `file`        | string              | no       | Path to a downloadable file (e.g. PDF)                            |
| `url`         | string              | no       | External link                                                     |
| `thumbnail`   | string              | no       | Image URL                                                         |

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
3. If Hono Worker work is ongoing, check `worker/PLAN.md` for current implementation state.
4. Summarize to Venkat: sync activity, active items from `status-vgr.md`, and Worker migration progress.

---

## After Each Session

**Documentation (always):**
1. `status-vgr.md` — add a dated log entry with PT start–end times and a one-line summary of what changed.
2. `CLAUDE.md` — update stack notes, roadmap status, or schema changes if anything changed.

**Build & verify (if code or content changed):**
3. `npm run build` — verify clean build, zero errors, before committing.

**Repo:**
4. `git add` relevant files (never `.env`); `git commit`; `git push`. Push to `main` — CF Pages auto-deploys Astro fallback. Worker deploys separately via `wrangler deploy` from `worker/`.

**Memory:**
5. Update Claude memory (`/Users/Venkat/.claude/projects/.../memory/`) — save anything non-obvious about the content schema, sync pipeline, framework decision state, or workflow preferences that would help future sessions. Do not duplicate what's in CLAUDE.md or recoverable from code.

## Keys

- `CLOUDFLARE_API_TOKEN` — in `../admin/keys.md`; used by GitHub Actions deploy and wrangler CLI.
- All PI keys go in `../admin/keys.md`, not `Code/.env.keys`.

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
