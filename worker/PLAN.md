# Hono + HTMX Migration Plan

Replaces the Astro 5 static site with a Cloudflare Worker using Hono (server-side
rendering) + HTMX (interactive fragments). Phase 1 decision: 2026-05-30.

**Fallback:** Astro CF Pages deployment stays intact. Rollback = move `protocolized.io`
custom domain from Worker back to CF Pages project in CF dashboard (~30 sec).

---

## Project layout (this directory)

```
worker/
  src/
    index.ts           # Hono app — all routes wired
    db.ts              # D1 query helpers
    html/
      base.tsx         # <html> shell, nav, footer
      home.tsx         # Home page
      resources.tsx    # Resource library (list)
      resource.tsx     # Resource detail page
      static-pages.tsx # about / community / magazine / anthologies
      rss.ts           # RSS feed generator
  public/
    style.css          # Tailwind compiled output (copied from Astro dist)
    (fonts, favicon, images — copied from current public/)
  schema.sql           # D1 DDL
  wrangler.toml
  package.json
  tsconfig.json
scripts/
  migrate-to-d1.py    # one-time: 287 Markdown files → D1
  sync-substack.py    # update to dual-write: Markdown + D1
```

---

## D1 schema

```sql
CREATE TABLE resources (
  slug        TEXT PRIMARY KEY,
  title       TEXT NOT NULL,
  type        TEXT NOT NULL,
  authors     TEXT NOT NULL,   -- JSON: [{name, url?}]
  date        TEXT NOT NULL,   -- YYYY-MM-DD
  description TEXT NOT NULL,
  tags        TEXT NOT NULL,   -- JSON: string[]
  audience    TEXT NOT NULL,   -- JSON: string[]
  featured    INTEGER NOT NULL DEFAULT 0,
  file        TEXT,
  url         TEXT,
  thumbnail   TEXT,
  body        TEXT             -- markdown body (for detail pages)
);
CREATE INDEX idx_date ON resources(date DESC);
CREATE INDEX idx_type ON resources(type);
```

---

## Routes

| Route | Rendering | Notes |
|-------|-----------|-------|
| `GET /` | Hono JSX | Featured resources + latest 5 articles |
| `GET /about` | Hono JSX | Static content |
| `GET /community` | Hono JSX | Static content |
| `GET /magazine` | Hono JSX | Static content (Substack embed) |
| `GET /anthologies` | Hono JSX | Static content |
| `GET /resources` | Hono JSX | Full library; client-side Fuse.js filtering (Phase 1 parity) |
| `GET /resources/protocol-lexicon` | Static HTML | Served from `public/lexicon.html`; individual term URLs in Phase 2 |
| `GET /resources/:slug` | Hono JSX | Detail page; markdown rendered via `marked` |
| `GET /api/resources.json` | JSON | D1 query, same schema as current |
| `GET /api/lexicon.json` | Static JSON | Served from `public/lexicon.json` |
| `GET /rss.xml` | Text | Generated from D1 |
| `GET /llms.txt` | Static | Served from `public/llms.txt` |
| `GET /sitemap.xml` | XML | Generated from D1 |

---

## CSS strategy

For the initial migration: copy the Astro-compiled Tailwind CSS from `dist/_astro/*.css`
into `worker/public/style.css`. Serve as static asset via `[assets]` binding.

When the Worker CSS needs independent changes (post-migration): set up standalone
`tailwindcss` CLI inside `worker/` with its own `tailwind.config.mjs`.

---

## Content migration

### One-time import

```bash
# 1. Create D1 database
wrangler d1 create protocolized-resources --remote

# 2. Apply schema
wrangler d1 execute protocolized-resources --remote --file=worker/schema.sql

# 3. Import 287 Markdown files
/opt/homebrew/bin/python3 scripts/migrate-to-d1.py
```

The migration script (`scripts/migrate-to-d1.py`):
- Reads each `.md` file in `src/content/resources/`
- Parses frontmatter (title, type, authors, date, tags, audience, featured, file, url, thumbnail)
- Captures markdown body
- Outputs a SQL file then runs `wrangler d1 execute --remote`

### Ongoing sync (Substack → D1)

Update `scripts/sync-substack.py` to dual-write:
1. Still creates Markdown file (keeps Astro fallback synced)
2. Also runs `wrangler d1 execute --remote` to insert the new post

Drop the Markdown write once Hono is confirmed stable.

---

## Wrangler config (`worker/wrangler.toml`)

```toml
name = "protocolized-website"
main = "src/index.ts"
compatibility_date = "2025-01-01"
compatibility_flags = ["nodejs_compat"]

[[d1_databases]]
binding = "DB"
database_name = "protocolized-resources"
database_id = "<id from wrangler d1 create>"

[assets]
directory = "./public"
```

---

## Timeline

| When | What |
|------|------|
| Next session (start) | Scaffold `worker/` project, `npm init`, install Hono, create D1 |
| Next session (mid) | Write migration script, import all 287 resources, build all routes |
| Day before cutover | Test on `protocolized-worker.workers.dev`, update sync script |
| Monday 2026-06-02 (before 8am UTC) | Switch `protocolized.io` custom domain to Worker; verify first Substack post goes to D1 |

---

## Decisions made

- **Filtering:** keep client-side Fuse.js (Phase 1 parity); HTMX server-side fragments deferred
- **Lexicon:** static HTML from `public/lexicon.html` for now; individual term URLs planned for Phase 2
- **Astro source:** kept in `src/` as fallback — do not delete until Worker is confirmed stable for 1+ week
