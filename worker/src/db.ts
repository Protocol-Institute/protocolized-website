export interface Author {
  name: string;
  url?: string;
}

export interface Resource {
  slug: string;
  title: string;
  type: string;
  authors: Author[];
  date: string;
  description: string;
  tags: string[];
  audience: string[];
  featured: boolean;
  file?: string;
  url?: string;
  thumbnail?: string;
  body?: string;
}

interface ResourceRow {
  slug: string;
  title: string;
  type: string;
  authors: string;
  date: string;
  description: string;
  tags: string;
  audience: string;
  featured: number;
  file: string | null;
  url: string | null;
  thumbnail: string | null;
  body: string | null;
}

function parseRow(row: ResourceRow): Resource {
  return {
    slug: row.slug,
    title: row.title,
    type: row.type,
    authors: JSON.parse(row.authors),
    date: row.date,
    description: row.description,
    tags: JSON.parse(row.tags),
    audience: JSON.parse(row.audience),
    featured: row.featured === 1,
    file: row.file ?? undefined,
    url: row.url ?? undefined,
    thumbnail: row.thumbnail ?? undefined,
    body: row.body ?? undefined,
  };
}

export async function getAllResources(db: D1Database): Promise<Resource[]> {
  const result = await db
    .prepare("SELECT * FROM resources ORDER BY date DESC")
    .all<ResourceRow>();
  return result.results.map(parseRow);
}

export async function getResource(
  db: D1Database,
  slug: string
): Promise<Resource | null> {
  const row = await db
    .prepare("SELECT * FROM resources WHERE slug = ?")
    .bind(slug)
    .first<ResourceRow>();
  return row ? parseRow(row) : null;
}

export async function getFeaturedResources(
  db: D1Database
): Promise<Resource[]> {
  const result = await db
    .prepare(
      "SELECT * FROM resources WHERE featured = 1 ORDER BY date DESC LIMIT 6"
    )
    .all<ResourceRow>();
  return result.results.map(parseRow);
}

export async function getRandomArchiveResources(
  db: D1Database,
  limit = 2
): Promise<Resource[]> {
  const result = await db
    .prepare(
      "SELECT * FROM resources WHERE file LIKE '%.pdf' AND thumbnail IS NOT NULL ORDER BY RANDOM() LIMIT ?"
    )
    .bind(limit)
    .all<ResourceRow>();
  return result.results.map(parseRow);
}

export async function getLatestArticles(
  db: D1Database,
  limit = 5
): Promise<Resource[]> {
  const result = await db
    .prepare(
      "SELECT * FROM resources WHERE type = 'article' ORDER BY date DESC LIMIT ?"
    )
    .bind(limit)
    .all<ResourceRow>();
  return result.results.map(parseRow);
}

export async function getRelatedResources(
  db: D1Database,
  slug: string,
  tags: string[]
): Promise<Resource[]> {
  if (tags.length === 0) return [];
  const result = await db
    .prepare("SELECT * FROM resources WHERE slug != ? ORDER BY date DESC")
    .bind(slug)
    .all<ResourceRow>();
  const parsed = result.results.map(parseRow);
  return parsed
    .filter((r) => r.tags.some((t) => tags.includes(t)))
    .sort((a, b) => {
      const aM = a.tags.filter((t) => tags.includes(t)).length;
      const bM = b.tags.filter((t) => tags.includes(t)).length;
      return bM - aM;
    })
    .slice(0, 3);
}

export async function getAnthologies(db: D1Database): Promise<Resource[]> {
  const result = await db
    .prepare("SELECT * FROM resources WHERE tags LIKE '%anthology%' ORDER BY date DESC")
    .all<ResourceRow>();
  return result.results.map(parseRow).filter((r) => r.tags.includes("anthology"));
}

// ── Books ─────────────────────────────────────────────────────────────────

export interface TocEntry {
  title: string;
  author?: string;
  url?: string;
}

export interface Contributor {
  name: string;
  role?: string;
}

export interface Book {
  slug: string;
  title: string;
  subtitle?: string;
  editor?: string;
  date: string;
  description: string;
  body?: string;
  cover_image?: string;
  url?: string;
  file?: string;
  toc: TocEntry[];
  contributors: Contributor[];
  tags: string[];
  sort_order: number;
  published: boolean;
  category: string;
}

interface BookRow {
  slug: string;
  title: string;
  subtitle: string | null;
  editor: string | null;
  date: string;
  description: string;
  body: string | null;
  cover_image: string | null;
  url: string | null;
  file: string | null;
  toc: string;
  contributors: string;
  tags: string;
  sort_order: number;
  published: number;
  category: string;
}

function parseBookRow(row: BookRow): Book {
  return {
    slug: row.slug,
    title: row.title,
    subtitle: row.subtitle ?? undefined,
    editor: row.editor ?? undefined,
    date: row.date,
    description: row.description,
    body: row.body ?? undefined,
    cover_image: row.cover_image ?? undefined,
    url: row.url ?? undefined,
    file: row.file ?? undefined,
    toc: JSON.parse(row.toc),
    contributors: JSON.parse(row.contributors),
    tags: JSON.parse(row.tags),
    sort_order: row.sort_order,
    published: row.published === 1,
    category: row.category ?? "fiction",
  };
}

export async function getRandomBooks(db: D1Database, limit = 1): Promise<Book[]> {
  const result = await db
    .prepare(
      "SELECT * FROM books WHERE published = 1 AND cover_image IS NOT NULL ORDER BY RANDOM() LIMIT ?"
    )
    .bind(limit)
    .all<BookRow>();
  return result.results.map(parseBookRow);
}

export async function getAllBooks(db: D1Database): Promise<Book[]> {
  const result = await db
    .prepare("SELECT * FROM books WHERE published = 1 ORDER BY sort_order ASC, date DESC")
    .all<BookRow>();
  return result.results.map(parseBookRow);
}

export async function getBook(db: D1Database, slug: string): Promise<Book | null> {
  const row = await db
    .prepare("SELECT * FROM books WHERE slug = ? AND published = 1")
    .bind(slug)
    .first<BookRow>();
  return row ? parseBookRow(row) : null;
}

// ── Posts ──────────────────────────────────────────────────────────────────

export interface Post {
  slug: string;
  title: string;
  subtitle?: string;
  date: string;
  section: string;
  primary_author: string;
  authors: string[];
  cover_image?: string;
  body_r2_key?: string;
  summary?: string;
  enriched_categories: string[];
  substack_categories: string[];
  reaction_count: number;
  previous_slug?: string;
  next_slug?: string;
  substack_url?: string;
  image_count: number;
  mirrored_at?: string;
  series_slug?: string;
  series_position?: number;
  is_placeholder?: boolean;
}

interface PostRow {
  slug: string;
  title: string;
  subtitle: string | null;
  date: string;
  section: string;
  primary_author: string;
  authors: string;
  cover_image: string | null;
  body_r2_key: string | null;
  summary: string | null;
  enriched_categories: string;
  substack_categories: string;
  reaction_count: number;
  previous_slug: string | null;
  next_slug: string | null;
  substack_url: string | null;
  image_count: number;
  mirrored_at: string | null;
  series_slug: string | null;
  series_position: number | null;
  is_placeholder: number | null;
}

function parsePostRow(row: PostRow): Post {
  return {
    slug: row.slug,
    title: row.title,
    subtitle: row.subtitle ?? undefined,
    date: row.date,
    section: row.section ?? "Protocolized",
    primary_author: row.primary_author ?? "Protocolized",
    authors: row.authors ? JSON.parse(row.authors) : [],
    cover_image: row.cover_image ?? undefined,
    body_r2_key: row.body_r2_key ?? undefined,
    summary: row.summary ?? undefined,
    enriched_categories: row.enriched_categories ? JSON.parse(row.enriched_categories) : [],
    substack_categories: row.substack_categories ? JSON.parse(row.substack_categories) : [],
    reaction_count: row.reaction_count ?? 0,
    previous_slug: row.previous_slug ?? undefined,
    next_slug: row.next_slug ?? undefined,
    substack_url: row.substack_url ?? undefined,
    image_count: row.image_count ?? 0,
    mirrored_at: row.mirrored_at ?? undefined,
    series_slug: row.series_slug ?? undefined,
    series_position: row.series_position ?? undefined,
    is_placeholder: row.is_placeholder === 1 ? true : undefined,
  };
}

export async function getPost(db: D1Database, slug: string): Promise<Post | null> {
  const row = await db
    .prepare("SELECT * FROM posts WHERE slug = ?")
    .bind(slug)
    .first<PostRow>();
  return row ? parsePostRow(row) : null;
}

export async function getLatestPosts(db: D1Database, limit = 50): Promise<Post[]> {
  const result = await db
    .prepare(
      "SELECT slug, title, subtitle, date, section, primary_author, authors, cover_image, summary, substack_url, reaction_count, image_count, mirrored_at FROM posts WHERE is_placeholder IS NULL OR is_placeholder = 0 ORDER BY date DESC LIMIT ?"
    )
    .bind(limit)
    .all<PostRow>();
  return result.results.map(parsePostRow);
}

export async function getAdjacentPosts(
  db: D1Database,
  post: Post
): Promise<{ prev: Post | null; next: Post | null }> {
  const [prevRow, nextRow] = await Promise.all([
    post.previous_slug
      ? db
          .prepare("SELECT slug, title, date FROM posts WHERE slug = ?")
          .bind(post.previous_slug)
          .first<PostRow>()
      : null,
    post.next_slug
      ? db
          .prepare("SELECT slug, title, date FROM posts WHERE slug = ?")
          .bind(post.next_slug)
          .first<PostRow>()
      : null,
  ]);
  return {
    prev: prevRow ? parsePostRow(prevRow) : null,
    next: nextRow ? parsePostRow(nextRow) : null,
  };
}

// ── Series context ─────────────────────────────────────────────────────────

export interface SeriesEntry {
  slug?: string;
  title: string;
  url: string;
  external?: boolean;
}

export interface SeriesContext {
  seriesTitle: string;
  seriesSlug: string;
  position: number;
  totalParts: number;
  prev: SeriesEntry | null;
  next: SeriesEntry | null;
}

export async function getSeriesContext(
  db: D1Database,
  seriesSlug: string,
  position: number
): Promise<SeriesContext | null> {
  const [bookRow, prevPost, nextPost] = await Promise.all([
    db
      .prepare("SELECT title, toc FROM books WHERE slug = ?")
      .bind(seriesSlug)
      .first<{ title: string; toc: string }>(),
    db
      .prepare("SELECT slug, title FROM posts WHERE series_slug = ? AND series_position = ?")
      .bind(seriesSlug, position - 1)
      .first<{ slug: string; title: string }>(),
    db
      .prepare("SELECT slug, title FROM posts WHERE series_slug = ? AND series_position = ?")
      .bind(seriesSlug, position + 1)
      .first<{ slug: string; title: string }>(),
  ]);

  if (!bookRow) return null;

  const toc: TocEntry[] = JSON.parse(bookRow.toc);
  const totalParts = toc.length;

  // Prefer D1 post; fall back to TOC entry for external/un-mirrored stories
  let prev: SeriesEntry | null = null;
  if (prevPost) {
    prev = { slug: prevPost.slug, title: prevPost.title, url: `/p/${prevPost.slug}` };
  } else if (position > 1) {
    const tocEntry = toc[position - 2];
    if (tocEntry?.url) prev = { title: tocEntry.title, url: tocEntry.url, external: true };
  }

  let next: SeriesEntry | null = null;
  if (nextPost) {
    next = { slug: nextPost.slug, title: nextPost.title, url: `/p/${nextPost.slug}` };
  } else if (position < totalParts) {
    const tocEntry = toc[position];
    if (tocEntry?.url) next = { title: tocEntry.title, url: tocEntry.url, external: true };
  }

  return { seriesTitle: bookRow.title, seriesSlug, position, totalParts, prev, next };
}
