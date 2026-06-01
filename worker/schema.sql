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
  body_html            TEXT,
  body_html_original   TEXT,
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
  synced_at            TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(date DESC);
CREATE INDEX IF NOT EXISTS idx_posts_section ON posts(section);
CREATE INDEX IF NOT EXISTS idx_posts_mirrored ON posts(mirrored_at);
