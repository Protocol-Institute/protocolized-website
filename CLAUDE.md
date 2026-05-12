# Protocolized — CLAUDE.md

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

## Things to watch out for

- Do NOT commit `.env` files or tokens of any kind.
- The `.claude/` directory is gitignored — it contains local Claude Code settings and should not be committed.
- The `raw_resources/` directory is gitignored — it contains source data used during the initial import.
- Resource slugs are derived from filenames. Renaming a resource file changes its URL.
