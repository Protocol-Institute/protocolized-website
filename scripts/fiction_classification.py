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


# ---------------------------------------------------------------------------
# Substack section resolution
# ---------------------------------------------------------------------------
# The per-post Substack endpoint (/api/v1/posts/{slug}) returns section_id but
# NOT section_name -- section_name is only present in the bulk archive listing
# (which is what c3po caches in sources/substack/api_metadata.json, and what the
# original 2026-06 export was built from).
#
# sync-substack.py reads the per-post endpoint, so it never saw a section_name
# and silently fell back to the literal default "Protocolized". Because
# "Protocolized" is itself a real section, the misfiling was invisible: every
# post mirrored after the Worker-era sync began landed in the wrong section,
# including 6 fiction posts that the FICTION_POST_SECTIONS check then failed to
# recognize. Resolve from section_id instead; it is always present.
#
# Map verified 2026-09-02 against both the live per-post API and c3po's cached
# archive metadata (134 posts, zero disagreements).
SUBSTACK_SECTION_BY_ID = {
    333103: "Obliquities",
    333105: "Fictions",
    333110: "Articles",
    None: "Protocolized",  # genuinely sectionless posts show as "Protocolized"
}

# Editorial overrides: slugs whose section on this site deliberately differs
# from what Substack reports. Applied last, so a re-sync cannot revert them.
#
# The three Jamverse meta/announcement posts were reclassified to "Fictions" in
# the Phase 0 fiction split (2026-08-17): they are house-keeping posts about the
# fiction programme and belong with the fiction publication at cutover, even
# though Substack files them under Protocolized/Obliquities.
SECTION_OVERRIDES = {
    "jamverse-jam": "Fictions",
    "jamverse-live": "Fictions",
    "jamverse-jam-contest-closes-today": "Fictions",
}


def resolve_section(slug, section_id, section_name=None, apply_overrides=True):
    """Return the section a post belongs to on this site.

    Precedence: editorial override > section_name (when the source supplies it)
    > section_id lookup > "Protocolized". Never guesses from a missing field.

    Pass apply_overrides=False for callers that need the section as a *format*
    signal rather than a routing one. SECTION_OVERRIDES expresses which
    publication a post travels with, not what kind of thing it is: the Jamverse
    announcement posts route with the fiction pub but are still articles, and
    mapping their override through to resources.type would mistype them as
    `fiction` in the library. sync-substack-resources.py therefore opts out.
    """
    if apply_overrides and slug in SECTION_OVERRIDES:
        return SECTION_OVERRIDES[slug]
    if section_name:
        return section_name
    if section_id in SUBSTACK_SECTION_BY_ID:
        return SUBSTACK_SECTION_BY_ID[section_id]
    # Unknown section_id -- a new section was added on Substack. Surface it
    # rather than silently filing the post under the wrong name.
    print(
        f"  !!! WARNING: post '{slug}' has unrecognized Substack section_id "
        f"{section_id!r}. Add it to SUBSTACK_SECTION_BY_ID in "
        f"scripts/fiction_classification.py. Filing as 'Protocolized' for now."
    )
    return "Protocolized"
