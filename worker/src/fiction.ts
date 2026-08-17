// Single source of truth for the fiction/nonfiction content boundary.
//
// Fiction/nonfiction is not a first-class column anywhere — it's an emergent
// property of three independently-set fields (posts.section, resources.type,
// books.category). This module centralizes the definition so every route and
// query checks the same thing. See ../../../.claude/plans (fiction split plan)
// for the full rationale.

export const FICTION_POST_SECTIONS = new Set(["Fictions"]);
export const FICTION_RESOURCE_TYPE = "fiction";
export const FICTION_BOOK_CATEGORY = "fiction";

// Fiction series (posts.series_slug values whose home book is fiction).
// getSeriesContext() needs to know this without an extra join.
export const FICTION_SERIES_SLUGS = new Set([
  "trainverse",
  "legends-and-ledgers",
  "zoothesia",
  "stockton-chronicles",
]);

export function isFictionPostSection(section: string | null | undefined): boolean {
  return !!section && FICTION_POST_SECTIONS.has(section);
}

export function isFictionResourceType(type: string | null | undefined): boolean {
  return type === FICTION_RESOURCE_TYPE;
}

export function isFictionBookCategory(category: string | null | undefined): boolean {
  return category === FICTION_BOOK_CATEGORY;
}
