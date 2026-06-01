# Phase 2 — Substack Mirror: Image R2 Hosting + Post Archive

> **Status:** Planning — ready to build after Phase 1 (D1 create + Worker deploy).
> **Context:** Roadmap Phase 1 (Hono + HTMX) is decided and underway. This plan covers the
> Substack mirroring portion of Phase 2. The live-sync cron portion (CF Cron Trigger →
> D1) is a separate concern documented in the roadmap; this plan focuses on getting the
> full post archive (images + HTML) into R2/D1 so posts are served from our own
> infrastructure instead of Substack's CDN.
>
> **Originally drafted by c3po Claude session; updated in protocolized-website session 2026-06-01.**

---

## What we're building

1. **Image mirror**: all Substack post images rehosted on R2 (`files.protocolized.io`)
2. **Post archive**: full post body HTML stored in D1 `posts` table, with image URLs rewritten to R2
3. **Hono route**: `GET /p/:slug` renders a full post page from D1 (a new `PostPage` JSX component)
4. **Backfill pipeline**: one-time Python script seeded from c3po's existing metadata files + fresh Substack export
5. **Incremental sync**: new sync script that independently polls the Substack API with change detection
6. **"Read on Substack" link**: every post page shows a prominent link back to the canonical Substack URL

---

## Background: image URL structure

Substack serves images through its CDN using a transform-proxy pattern:

```
https://substackcdn.com/image/fetch/{transform_params}/{percent_encoded_original_url}
```

The original image lives on `substack-post-media.s3.amazonaws.com`. To get it:

```python
import urllib.parse
# Full substackcdn URL:
# https://substackcdn.com/image/fetch/$s_!pEoC!,w_1456,.../https%3A%2F%2Fsubstack-post-media.s3...
parts = url.split("/https%3A%2F%2F", 1)
if len(parts) == 2:
    original_url = "https://" + urllib.parse.unquote(parts[1])
# → https://substack-post-media.s3.amazonaws.com/public/images/abc123_1024x1024.png
```

`srcset` attributes contain multiple size variants — only the original S3 URL needs to be
downloaded; all variants can be dropped (`srcset` → omitted, `src` → R2 URL).

Cover images are a separate API field (`cover_image`) and must be handled alongside body images.

---

## Starting point: existing data assets

**Do not re-fetch metadata from scratch.** c3po has already done the API work:

| File | Location | Contents |
|------|----------|----------|
| `api_metadata.json` | `c3po/sources/substack/api_metadata.json` | 117 slugs: title, subtitle, date, section, bylines, tags, wordcount, prev/next slug, reaction count — up to 2026-05-30 |
| `enriched_meta.json` | `c3po/sources/substack/enriched_meta.json` | Per-slug: 2-sentence Haiku-generated summary, enriched categories, primary_author, all_authors |
| Export HTML | `c3po/data/substack/posts/*.html` | 131 HTML files from May 14 export |
| `posts.csv` | `c3po/data/substack/posts.csv` | Export manifest with post_id, slug, date, type, audience |

**Backfill uses these as input, not the Substack API for metadata.**  The API is only
needed for `body_html` (not in the export or api_metadata) and for any posts published
after 2026-05-30 (a handful — ~2 weeks of posts). A fresh export ZIP is preferred for
the initial backfill to get the most complete coverage.

**Export ZIP location:** `c3po/data/substack/8RZgyD3ZTn2rlis5w_1Pqw.zip` (May 14 export,
already extracted). A fresh export should be placed in this same directory before running
the backfill script.

---

## Step 0 — Add `posts` table to schema BEFORE D1 creation

**Critical:** add the `posts` table to `worker/schema.sql` now, before running
`wrangler d1 create`, so it's included in the initial schema apply. No ALTER needed later.

---

## Step 1 — D1 schema: `posts` table

Add to `worker/schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS posts (
  slug                 TEXT PRIMARY KEY,
  title                TEXT NOT NULL,
  subtitle             TEXT,
  date                 TEXT NOT NULL,           -- YYYY-MM-DD
  section              TEXT NOT NULL DEFAULT 'Protocolized',
  primary_author       TEXT NOT NULL DEFAULT 'Protocolized',
  authors              TEXT NOT NULL DEFAULT '[]',  -- JSON: string[]
  cover_image          TEXT,                    -- R2 URL (null until mirrored)
  cover_image_original TEXT,                   -- original substackcdn URL
  body_html            TEXT,                   -- body HTML with R2 image URLs
  body_html_original   TEXT,                   -- body_html from API, untouched
  summary              TEXT,                   -- Haiku-generated 2-sentence summary (from enriched_meta)
  enriched_categories  TEXT NOT NULL DEFAULT '[]',  -- JSON: string[] (from enriched_meta)
  substack_categories  TEXT NOT NULL DEFAULT '[]',  -- JSON: string[] (from postTags)
  section_id           INTEGER,
  reaction_count       INTEGER DEFAULT 0,
  restacks             INTEGER DEFAULT 0,
  previous_slug        TEXT,
  next_slug            TEXT,
  substack_url         TEXT,                   -- canonical Substack URL (kept for "read on substack" link)
  image_count          INTEGER DEFAULT 0,
  mirrored_at          TEXT,                   -- ISO timestamp when images were mirrored to R2
  synced_at            TEXT NOT NULL           -- ISO timestamp of last sync
);

CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(date DESC);
CREATE INDEX IF NOT EXISTS idx_posts_section ON posts(section);
CREATE INDEX IF NOT EXISTS idx_posts_mirrored ON posts(mirrored_at);
```

---

## Step 2 — Backfill script: `scripts/mirror-substack.py`

One-time script. Reads c3po's existing files + fetches body_html from API + mirrors images to R2 + writes to D1.

### Algorithm

```python
# 1. Load c3po metadata (no API call needed for these)
api_meta = json.load(open("../c3po/sources/substack/api_metadata.json"))
enriched  = json.load(open("../c3po/sources/substack/enriched_meta.json"))
# api_meta is a list; build dict by slug
by_slug = {p["slug"]: p for p in api_meta}

for slug in all_slugs:
    # 2. Fetch body_html from Substack API (this IS the required API call)
    post = fetch_post_api(slug)           # GET /api/v1/posts/{slug}

    # 3. Collect all image URLs from body + cover
    images = extract_images(post["body_html"])
    if post.get("cover_image"):
        images.append(("cover", post["cover_image"]))

    # 4. Mirror each image to R2 (skip if already uploaded)
    url_map = {}
    for role, src_url in images:
        original_url = decode_substackcdn(src_url)
        content_hash = sha256(download(original_url))
        ext = guess_extension(original_url)
        r2_key = f"images/{content_hash[:2]}/{content_hash}{ext}"
        if not r2_exists(r2_key):
            r2_upload(r2_key, content)
        url_map[src_url] = f"https://files.protocolized.io/{r2_key}"

    # 5. Rewrite HTML
    rewritten_html = rewrite_image_urls(post["body_html"], url_map)

    # 6. Merge metadata from c3po sources
    meta = by_slug.get(slug, {})
    enrich = enriched.get(slug, {})

    # 7. Write to D1
    insert_post_d1(slug, meta, enrich, post, rewritten_html)

    time.sleep(0.5)
```

### Image deduplication: content-hash approach

R2 key: `images/{hash[:2]}/{hash}.ext` — deduplicates images shared across posts.
Alternative `images/{slug}/{filename}.ext` is easier to audit but uses more storage.
**Use content-hash** (more storage-efficient, idempotent on re-run).

### R2 upload: boto3 via S3-compatible API

Use boto3, not `wrangler r2 object put` (subprocess per image is too slow for bulk).

```python
import boto3
s3 = boto3.client("s3",
    endpoint_url=f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
)
s3.put_object(Bucket="protocolized-resources", Key=r2_key, Body=content,
              ContentType=content_type)
```

Requires an R2 API token (CF dashboard → R2 → Manage R2 API Tokens, write access to
`protocolized-resources`). Check `../../.env.keys` for existing `R2_ACCESS_KEY_ID` —
may already exist from Phase 0 PDF migration.

### D1 write: batch SQL file

Write all inserts to a temp SQL file, execute once per N posts:

```bash
wrangler d1 execute protocolized-resources --remote --file=data/posts_batch.sql
```

### State file: `data/mirror_state.json`

Tracks per-slug status for resumability:

```json
{
  "slug": {
    "api_fetched": true,
    "image_count": 4,
    "images_mirrored": true,
    "d1_written": true,
    "mirrored_at": "2026-06-01T10:00:00Z"
  }
}
```

---

## Step 3 — Incremental sync: `scripts/sync-substack.py` (rewrite)

Replace the current RSS-based stub script entirely. New approach: independent API polling
with `updated_at` change detection (borrowing the proven pattern from c3po's
`ingest/sync_substack.py`, but writing to D1/R2 instead of Pinecone).

**Design principle:** runs independently — no cross-repo dependency on c3po at runtime.
Uses the same API, same change detection logic, separate state file.

```python
# Fetch all posts metadata (paginated)
def fetch_all_posts_api():
    posts, offset = [], 0
    while True:
        url = f"{BASE_URL}/api/v1/posts?limit=50&offset={offset}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        batch = json.loads(urlopen(req).read())
        if not batch: break
        posts.extend(batch)
        if len(batch) < 50: break
        offset += 50
        time.sleep(0.4)
    return posts

# Change detection (mirrors c3po registry pattern)
# State: data/sync_state.json — slug → {updated_at, postTags}
# Detect: new slugs, updated_at changed, tag changes
```

For new/edited posts: fetch body_html → mirror images → rewrite URLs → upsert D1 row.

Note: this script does NOT need to do Haiku enrichment — that stays in c3po.
The enriched summary/categories are written at backfill time; updates to them are a
manual or periodic operation (not needed on every sync).

---

## Step 4 — Hono route: `GET /p/:slug`

Add to `worker/src/index.ts`:

```typescript
app.get("/p/:slug", async (c) => {
  const slug = c.req.param("slug");
  const post = await getPost(c.env.DB, slug);
  if (!post) {
    // Post exists on Substack but not yet mirrored — redirect rather than 404
    return c.redirect(`https://protocolized.summerofprotocols.com/p/${slug}`, 302);
  }
  const { prev, next } = await getAdjacentPosts(c.env.DB, slug);
  return c.html(<PostPage post={post} prev={prev} next={next} />);
});

app.get("/p/:slug/", (c) => c.redirect(`/p/${c.req.param("slug")}`, 301));
```

---

## Step 5 — PostPage component: `worker/src/html/post.tsx`

**Key UX requirement:** every post page shows a prominent "Read on Substack" link back
to the canonical Substack URL. Placement: below the byline / above the body, and again
in the post footer. Style: teal-bordered callout box, not a subtle footnote.

```tsx
export function PostPage({ post, prev, next }: PostPageProps) {
  return (
    <Base title={`${post.title} — Protocolized`} currentPath={`/p/${post.slug}`}>
      <article class="post">
        <header class="post-header">
          <span class="section-badge">{post.section}</span>
          <h1>{post.title}</h1>
          {post.subtitle && <p class="subtitle">{post.subtitle}</p>}
          <div class="byline">
            <span class="author">{post.primary_author}</span>
            <span class="date">{formatDate(post.date)}</span>
          </div>
          {/* Prominent Substack link — above the fold, always visible */}
          <a href={post.substack_url} class="read-on-substack" target="_blank" rel="noopener">
            Read on Substack ↗
          </a>
        </header>
        {post.cover_image && (
          <figure class="cover-image">
            <img src={post.cover_image} alt={post.title} />
          </figure>
        )}
        <div class="post-body" dangerouslySetInnerHTML={{ __html: post.body_html }} />
        {/* Footer Substack link */}
        <div class="post-footer-substack">
          <a href={post.substack_url} target="_blank" rel="noopener">
            Subscribe and comment on Substack ↗
          </a>
        </div>
        <nav class="post-nav">
          {prev && <a href={`/p/${prev.slug}`} class="prev">← {prev.title}</a>}
          {next && <a href={`/p/${next.slug}`} class="next">{next.title} →</a>}
        </nav>
      </article>
    </Base>
  );
}
```

`dangerouslySetInnerHTML` is safe here: body HTML comes from our own D1 (not user input),
all substackcdn URLs have been rewritten to R2 before storage.

---

## Step 6 — DB helpers: `worker/src/db.ts` additions

```typescript
export async function getPost(db: D1Database, slug: string) {
  return db.prepare("SELECT * FROM posts WHERE slug = ?").bind(slug).first();
}

export async function getLatestPosts(db: D1Database, limit = 50) {
  return db.prepare("SELECT slug, title, subtitle, date, section, primary_author, cover_image, summary FROM posts ORDER BY date DESC LIMIT ?").bind(limit).all().then(r => r.results);
}

export async function getAdjacentPosts(db: D1Database, slug: string) {
  const post = await db.prepare("SELECT previous_slug, next_slug FROM posts WHERE slug = ?").bind(slug).first();
  const [prev, next] = await Promise.all([
    post?.previous_slug ? db.prepare("SELECT slug, title FROM posts WHERE slug = ?").bind(post.previous_slug).first() : null,
    post?.next_slug ? db.prepare("SELECT slug, title FROM posts WHERE slug = ?").bind(post.next_slug).first() : null,
  ]);
  return { prev, next };
}
```

---

## Step 7 — R2 bucket binding in `wrangler.toml`

```toml
[[r2_buckets]]
binding = "FILES"
bucket_name = "protocolized-resources"
```

Update `Env` interface in `index.ts`:

```typescript
interface Env {
  DB: D1Database;
  FILES: R2Bucket;
}
```

---

## Step 8 — Magazine page: list posts from D1

The existing `/magazine` route is a static placeholder. Update to pull from D1:

```typescript
app.get("/magazine", async (c) => {
  const posts = await getLatestPosts(c.env.DB, 50);
  return c.html(<MagazinePage currentPath="/magazine" posts={posts} />);
});
```

`MagazinePage` component gets a `PostCard` sub-component wired to D1 data.
Each `PostCard` should also include the "Read on Substack" link.

---

## Execution order

### Today (Phase 1 prerequisite)
1. **Add `posts` table to `worker/schema.sql`** — do this before D1 creation

### Phase 1 (today)
2. Phase 1 steps: create D1 → apply schema (includes `posts` table) → migrate resources → deploy Worker

### Phase 2 (next session, after fresh export arrives)
3. **Get R2 API token** — check `../../.env.keys` for `R2_ACCESS_KEY_ID`; create one if absent (CF dashboard → R2 → Manage API Tokens → write access to `protocolized-resources`)
4. **Run backfill script** — reads `c3po/sources/substack/{api_metadata,enriched_meta}.json` + fetches body_html for each slug + mirrors images to R2 → writes to D1. ~20–30 min for 117 posts + images; resume-safe via `data/mirror_state.json`
5. **Add Hono route + PostPage component** — `worker/src/index.ts` + `worker/src/html/post.tsx`
6. **Add DB helpers** — `worker/src/db.ts`
7. **Test locally** — `wrangler dev` with local D1
8. **Deploy** — `wrangler deploy`
9. **Update magazine page** to pull from D1

### Follow-up (after Phase 2 is stable)
10. **Update c3po Pinecone vector URLs** — one-time: rewrite `url` field in substack namespace vectors from `protocolized.summerofprotocols.com/p/{slug}` → `protocolized.io/p/{slug}`. One-liner update in c3po project.
11. **Replace sync script** — swap RSS-based `scripts/sync-substack.py` with new API+D1 version

---

## Open questions

1. **R2 token**: check `../../.env.keys` for existing `R2_ACCESS_KEY_ID` (may already exist from Phase 0 PDF migration). If not, create one.

2. **Posts published after 2026-05-30**: api_metadata.json covers through May 30. A fresh Substack export ZIP captures everything through export date. The backfill script should use the export manifest for the full slug list, then fetch body_html for each slug via API.

3. **Image deduplication**: content-hash approach (`images/{hash[:2]}/{hash}.ext`) chosen — idempotent, deduplicates across posts, slightly harder to audit.

4. **"Read on Substack" styling**: teal-bordered callout box, above the fold below the byline, and again in the footer. Final CSS to be decided at frontend design time; the structural placement is fixed.

5. **c3po enrichment refresh**: once posts are stable in D1, consider a periodic job to re-run Haiku enrichment on new posts and update `summary` / `enriched_categories` in D1. Not needed at launch.
