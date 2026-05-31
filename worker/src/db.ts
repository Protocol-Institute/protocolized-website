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
