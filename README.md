# Protocolized

The website for [Protocolized](https://protocolized.io) — a sci-fi and thinkpiece magazine and research library on protocols, published by the Protocol Institute.

## What's here

- **Magazine** — stories, articles, and columns from the [Protocolized Substack](https://protocolized.summerofprotocols.com), synced automatically
- **Research library** — 280+ resources (papers, talks, frameworks, datasets, games, and more) from the [Summer of Protocols](https://summerofprotocols.com) program

## Getting started

```sh
# Clone the repo
git clone https://github.com/Protocolized/protocolized-website.git
cd protocolized-website

# Install dependencies (requires Node 22+)
npm install

# Start the dev server
npm run dev
```

The site will be available at `http://localhost:4321`.

## Commands

| Command           | Description                              |
|-------------------|------------------------------------------|
| `npm run dev`     | Start dev server at `localhost:4321`     |
| `npm run build`   | Build the production site to `dist/`     |
| `npm run preview` | Preview the production build locally     |

## Stack

- [Astro](https://astro.build) 5.x — static site generator
- [Tailwind CSS](https://tailwindcss.com) 3.x — utility-first styling
- [Fuse.js](https://www.fusejs.io) — client-side fuzzy search
- GitHub Actions — CI/CD (deploy on push) and daily Substack sync

## Project structure

```
src/
├── components/     Reusable Astro components
├── content/
│   ├── config.ts   Content collection schema (Zod)
│   └── resources/  ~280 Markdown resource files
├── layouts/        Base and Resource page layouts
├── pages/          File-based routing (home, about, resources, etc.)
scripts/            Automation (Substack RSS sync)
.github/workflows/  CI/CD and scheduled sync
```

## Adding a resource

Create a new `.md` file in `src/content/resources/`. Use kebab-case for the filename — it becomes the URL slug.

```yaml
---
title: "Your Resource Title"
type: paper           # paper | working-paper | framework | workshop-template | game | dataset | interview | presentation | code | image | prompt-template | talk | lecture | article | fiction
authors:
  - name: "Author Name"
    url: "https://example.com"   # optional
date: 2024-06-15
description: "A short description of the resource."
tags:
  - protocols
  - governance
audience:
  - researcher        # researcher | practitioner | academic | corporate
featured: false
url: "https://example.com/resource"   # optional external link
file: "/resources/filename.pdf"       # optional downloadable file
---

Optional body content in Markdown.
```

Run `npm run build` to verify the new resource compiles without errors.

## Machine-readable endpoints

| Endpoint               | Description                     |
|------------------------|---------------------------------|
| `/llms.txt`            | LLM-readable site summary       |
| `/api/resources.json`  | Full resource catalog as JSON    |
| `/rss.xml`             | RSS feed                        |
| `/sitemap-index.xml`   | Sitemap                         |

## Contributing

1. Fork the repo and create a feature branch
2. Make your changes
3. Run `npm run build` to confirm zero build errors
4. Open a pull request against `main`

For AI-assisted development, see [`CLAUDE.md`](CLAUDE.md) for project conventions and structure details.

## Community

- [Discord](https://discord.gg/Aj5FbGsNYV)
- [YouTube](https://www.youtube.com/@protocolized)
- [Magazine (Substack)](https://protocolized.summerofprotocols.com)

## Links

- [Protocol Institute](https://protocolsociety.org)
- [Summer of Protocols Archive](https://summerofprotocols.com)
