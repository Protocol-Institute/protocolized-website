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
