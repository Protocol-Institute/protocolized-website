"""Single source of truth for the fiction/nonfiction content boundary.

Mirrors worker/src/fiction.ts. Fiction/nonfiction is not a first-class column
anywhere -- it's an emergent property of three independently-set fields
(posts.section, resources.type, books.category). This module centralizes the
definition so the sync scripts (sync-substack.py, sync-substack-resources.py)
check the same thing the Worker does.
"""

FICTION_POST_SECTIONS = {"Fictions"}
FICTION_RESOURCE_TYPE = "fiction"
FICTION_BOOK_CATEGORY = "fiction"

FICTION_SERIES_SLUGS = {
    "trainverse",
    "legends-and-ledgers",
    "zoothesia",
    "stockton-chronicles",
}


def is_fiction_post_section(section):
    return bool(section) and section in FICTION_POST_SECTIONS


def is_fiction_resource_type(resource_type):
    return resource_type == FICTION_RESOURCE_TYPE


def is_fiction_book_category(category):
    return category == FICTION_BOOK_CATEGORY
