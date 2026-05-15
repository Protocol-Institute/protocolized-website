# Protocolized — CLAUDE.md

> **PI key registry & security policy:** see [`../admin/keys.md`](../admin/keys.md) and [`../admin/security.md`](../admin/security.md) . Do not register PI keys in `Code/.env.keys`.

## What is this project?

Protocolized is the website for a sci-fi and thinkpiece magazine and research library on protocols, published by the Protocol Institute. It lives at [protocolized.io](https://protocolized.io).

The site has two main sections:
1. **Magazine** — stories, articles, and columns synced daily from the Protocolized Substack
2. **Research library** — 280 resources (papers, talks, frameworks, datasets, etc.) from the Summer of Protocols program

## Stack

- **Framework**: Astro 5.x (static output)
- **Styling**: Tailwind CSS 3.x with custom design tokens
- **Content**: Astro Content Collections (Markdown files with YAML frontmatter)
- **Search**: Fuse.js for client-side fuzzy search
- **Deploy**: GitHub Pages via GitHub Actions (push to `main` triggers deploy)
- **Node**: v22 (CI uses `node-version: 22`; locally via nvm)

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

**Always do this first before any other work:**

1. Run `python3 devlog_session.py start` — records session start time to `/tmp/protocolized_devlog_session_start.txt`.
2. Run `python3 ../admin/expenses/track.py status` — shows all active PI project sessions and flags any overlap. If another project session is already running, no action needed; overlap is tracked automatically.
3. Read `status-vgr.md` — review active and upcoming items from the last session.
4. Check Substack sync activity since last session — how many posts have been synced, and are there any pending?
   ```bash
   git log --oneline --grep="sync" -10   # recent sync commits
   ```
   Then check the live feed against the most recent synced post date in `src/content/` to see if any unsynced posts exist.
5. Check branch state — how far has `feat/cloudflare-migration` drifted from `main`?
   ```bash
   git log main..feat/cloudflare-migration --oneline   # on CF branch, not yet on main
   git log feat/cloudflare-migration..main --oneline   # on main, not yet merged into CF branch
   ```
6. Check framework decision status — has the Phase 1 framework choice (Option A/B/C from `ROADMAP.md`) been made? If yes, update the roadmap and proceed to Phase 2 planning.
7. Briefly summarize to Venkat: sync activity since last session, CF migration status (is Timber's nameserver transfer done?), framework decision state, and active items from `status-vgr.md`.

---

## After Each Session

**Documentation (always):**
1. `data/devlog.json` — add session entry with items in HTML. Run `python3 devlog_session.py end` for the timestamp. Run `python3 devlog_render.py` to regenerate `DEVLOG.md`. The devlog is the primary record of architectural decisions, framework choices, and infrastructure work — write for a public technical audience.
2. `status-vgr.md` — add a dated log entry with PT start–end times and a one-line summary of what changed.
3. `CLAUDE.md` — update stack notes, roadmap status, or schema changes if anything changed.

**Build & verify (if code or content changed):**
4. `npm run build` — verify clean build, zero errors, before committing.

**Repo:**
5. `git add` relevant files (never `.env`); `git commit`; `git push`. Push to `main` for GitHub Pages deploy; push to `feat/cloudflare-migration` for CF Pages preview once migration is live.

**Expenses (always):**
6. `python3 ../admin/expenses/track.py end` — computes billable hours from all active session start files; detects overlap; prints a pre-filled log entry.
7. Paste the entry into `../admin/expenses/log-{your-id}.json` sessions array; fill in `api_costs` (any API charges incurred this session) and `notes`.
8. `python3 ../admin/expenses/render.py` — regenerates `EXPENSES.md` and `expenses.csv`.

**Memory:**
9. Update Claude memory (`/Users/Venkat/.claude/projects/.../memory/`) — save anything non-obvious about the content schema, sync pipeline, framework decision state, or workflow preferences that would help future sessions. Do not duplicate what's in CLAUDE.md or recoverable from code.

## Keys

No keys are currently in use for this repo. When CF Workers are added (post Phase 0 migration), keys (Cloudflare API token, future service keys) will be provisioned via `../.env.keys` and inventoried in `../admin/keys.md`. Do not use `Code/.env.keys` for PI keys.

## Things to watch out for

- Do NOT commit `.env` files or tokens of any kind.
- The `.claude/` directory is gitignored — it contains local Claude Code settings and should not be committed.
- The `raw_resources/` directory is gitignored — it contains source data used during the initial import.
- Resource slugs are derived from filenames. Renaming a resource file changes its URL.
