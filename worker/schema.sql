CREATE TABLE IF NOT EXISTS resources (
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

CREATE INDEX IF NOT EXISTS idx_date ON resources(date DESC);
CREATE INDEX IF NOT EXISTS idx_type ON resources(type);
CREATE INDEX IF NOT EXISTS idx_featured ON resources(featured);

CREATE TABLE IF NOT EXISTS posts (
  slug                 TEXT PRIMARY KEY,
  title                TEXT NOT NULL,
  subtitle             TEXT,
  date                 TEXT NOT NULL,
  section              TEXT NOT NULL DEFAULT 'Protocolized',
  primary_author       TEXT NOT NULL DEFAULT 'Protocolized',
  authors              TEXT NOT NULL DEFAULT '[]',
  cover_image          TEXT,
  cover_image_original TEXT,
  body_r2_key          TEXT,
  summary              TEXT,
  enriched_categories  TEXT NOT NULL DEFAULT '[]',
  substack_categories  TEXT NOT NULL DEFAULT '[]',
  section_id           INTEGER,
  reaction_count       INTEGER DEFAULT 0,
  restacks             INTEGER DEFAULT 0,
  previous_slug        TEXT,
  next_slug            TEXT,
  substack_url         TEXT,
  image_count          INTEGER DEFAULT 0,
  mirrored_at          TEXT,
  synced_at            TEXT NOT NULL,
  series_slug          TEXT,           -- FK → books.slug for series posts
  series_position      INTEGER         -- 1-based position within the series
);

CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(date DESC);
CREATE INDEX IF NOT EXISTS idx_posts_section ON posts(section);
CREATE INDEX IF NOT EXISTS idx_posts_mirrored ON posts(mirrored_at);
CREATE INDEX IF NOT EXISTS idx_posts_series ON posts(series_slug, series_position);

CREATE TABLE IF NOT EXISTS books (
  slug         TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  subtitle     TEXT,
  editor       TEXT,
  date         TEXT NOT NULL,
  description  TEXT NOT NULL,
  body         TEXT,
  cover_image  TEXT,
  url          TEXT,
  file         TEXT,
  toc          TEXT NOT NULL DEFAULT '[]',
  contributors TEXT NOT NULL DEFAULT '[]',
  tags         TEXT NOT NULL DEFAULT '[]',
  sort_order   INTEGER NOT NULL DEFAULT 0,
  published    INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_books_sort ON books(sort_order ASC, date DESC);
