# Works in progress: hosting working documents on protocolized.io

*Draft plan, 2026-10-19. First instance: Protocol Reader: Volume 2.*

## What this category is

A **work in progress (WIP)** is a front-end working document: something being assembled from
contributors' drafts that will eventually become one or more items in the resource library.
The first is a proceedings volume. Likely others: a second-season anthology, a report built
from a workshop, a lexicon revision, a symposium archive volume.

A WIP has a beginning (drafts start arriving), a middle (repeated fold-ins, each producing a
versioned manuscript), and an end (a version is judged ready to move to editing and
publishing). This site handles only the front end. Editing and production happen elsewhere,
and the result arrives back here as a book and/or resources.

## What exists now (v1, built 2026-10-19)

| Piece | Where | Notes |
|---|---|---|
| Manifest | `wip/<slug>/project.json` | Source of truth: metadata, stage, parts, contents in TOC order, readiness assessments, version history. Reordering the volume means reordering `contents`. |
| Local chapters | `wip/<slug>/*.md` | E.g. the editor's introduction stub. |
| Change lock | `wip/<slug>/sources.lock.json` | Text hash of each draft at the last published version. |
| Latest manuscript | `wip/<slug>/<slug>.pdf` | The only manuscript in git, at a stable path. Each release replaces it, so git history is the rewind mechanism. |
| Archive (local) | `wip/<slug>/archive/versions/`, `archive/chapters/` | Every published version, and the latest synced copy of each draft. Gitignored (**the repo is public; contributors' drafts never enter it**); backed up by Dropbox. The Drive folder stays the intake. |
| Build script | `scripts/wip/build-manuscript.py` | Fetch from Drive → detect changes → render → merge → publish to R2 → record version. |
| Cover | `scripts/wip/make-placeholder-cover.py` | Seeded placeholder in the site palette, R2 `wip/<slug>/cover.jpg`. |
| Pages | `/wip`, `/wip/<slug>` (`worker/src/html/wip.tsx`) | Bundled from the manifest at deploy time. Unlisted: `noindex`, not in nav, sitemap, RSS or llms.txt. |
| Files | `files.protocolized.io/wip/<slug>/` | The latest manuscript only (`<slug>-vX.Y.pdf`; the previous one is deleted on release) and the cover. |

**The fold-in loop:** an author updates their doc in the shared Drive folder → run
`build-manuscript.py <slug>` (preview) → `--publish --message "…"`. Publishing archives the
version, uploads it, and commits and pushes with that message. The same message is the
changelog entry on the page and at the top of the manuscript, so the git log and the site
changelog are the same text. The page shows only the latest version and flags any readiness
score assessed against an older text.

**Adding a new draft:** the script reports any Drive file that no contents entry claims
(`NEW FILE not in contents`). Add an entry to `contents` (id, part, title, authors,
summary, talk slug, source id, readiness), then publish. New drafts are never pulled in
automatically, so a stray upload can't end up in the manuscript.

## Decisions taken in v1, and why

- **Manifest in git, not D1.** A WIP changes a few times a week, edited by one person, and its
  history (scores, ordering, notes) is worth having in git. Bundling the JSON means no schema,
  no migration, and a reviewable diff for every change. The cost is that a page update needs a
  push (and therefore a deploy). Fine at this scale.
- **Hash the text, not the file.** Google Docs exports aren't byte-stable, so file hashes
  would flag every draft as changed on every run.
- **PDF as the manuscript format.** Readers can open it anywhere, with stable page numbers to
  cite in feedback. Drafts supplied as PDF (two in Vol. 2) go in as-is behind an opener page.
  Email addresses are redacted, matching the symposium archive practice.
- **Readiness is a human/Claude assessment, not computed.** The script only tracks whether the
  text has changed since the score was given (`assessed_hash` → `stale`). Scores stay coarse:
  1 placeholder stub, 4 partial, 6 complete but needs substantial editing, 8 ready for copy
  edit, 10 finished.
- **Unlisted, not private.** Shareable by link with contributors, kept out of search and site
  listings. Anything stronger needs auth (see below).

## Plan for the recurring case

### Phase 1: make the second project cheap (next time one starts)

1. `scripts/wip/new-project.py <slug> --drive-folder <id>`: scaffolds `project.json` from the
   folder listing (one entry per file, titles from the filenames, readiness unset), writes
   the intro stub, and generates the cover. Registers the import in `worker/src/wip.ts`.
   (The registry should become a glob import of `wip/*/project.json`, so there's no
   hand registration.)
2. A `--reassess` mode that writes a per-draft brief (word count, headings, bracketed
   notes-to-self, `[check]` markers, references present, title/byline present) to help
   whoever re-scores. The score itself stays a judgment call.
3. Also emit an EPUB or DOCX of the manuscript (pandoc) for reviewers who want to annotate.

### Phase 2: richer page, still static

- Per-entry history: when each draft last changed, the score history (from git), and
  "changed since vX".
- A per-chapter HTML reading view at `/wip/<slug>/<entry>`, for drafts not supplied as PDF.
  Useful for contributors' quick reads on a phone.
- A readiness overview chart (distribution of scores across versions) once there are
  several versions to plot.

### Phase 3: if the cadence or audience grows

Move to D1 when any of these become true: more than one editor, more than ~3 concurrent
WIPs, or updates that shouldn't wait for a deploy.

- Tables: `wip_projects`, `wip_entries` (order column for the TOC), `wip_versions`.
  The manifest becomes an import/export format.
- Access control. Two options: per-project secret links (simple: a token in the URL, checked
  by the Worker, with R2 objects served through the Worker rather than from the public bucket
  domain), or reuse the Protocol Institute members login cookie that `cogergo` already
  shares. Needed before any WIP holds material contributors haven't agreed to show by link.
- Run the fold-in as a scheduled GitHub Action (daily, like the Substack sync), opening a PR
  whenever drafts change.

### Graduation: from WIP to library

When a version is judged ready for editing, set `stage: "editing"`, and later
`"production"` and `"published"`. On publication:

1. The volume becomes a `books` row (cover, TOC, file, buy link). Each essay becomes a
   resource (`type: article` or `paper`), linked to its talk resource, which is already in
   the library for every Vol. 2 entry.
2. `/wip/<slug>` stays up as the volume's making-of record, or 301s to `/books/<slug>`.
   This is an open choice. Keeping it preserves the version history; redirecting keeps the
   site tidy.
3. Delete the R2 manuscript drafts, or keep them private, once the book is out. Old working
   drafts shouldn't stay in circulation once the edited text exists.

## Open questions for Venkat

- **Visibility.** The v1 page is public-but-unlisted, and the readiness notes about named
  contributors are visible to anyone with the link. Is that the right posture for
  contributors, or should the readiness notes be editor-only (e.g. in the PDF only, behind
  a secret link)?
- **Do contributors see the page?** If so, a short note to them about what the scores mean,
  and how to update their draft, would help.
- **Volume length.** v0.1 is 216 pages. The Atwater appendices and the Katz/Alston piece
  account for about 50 of them.
