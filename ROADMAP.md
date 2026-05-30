# Roadmap — protocolized.io

Features planned for the CF-powered version of the site. **Phase 1 is a framework decision gate** — the choice made there determines how Phases 2–7 are implemented. The CF resources, feature set, and dependencies are the same regardless of framework.

CF resources needed across all phases:
- **D1** — magazine posts, events, member/patron data
- **KV** — sessions, SIWE nonces, rate limiting
- **R2** — PDF mirror/cache (alongside IPFS), gated resource serving
- **Workers Cron Triggers** — live Substack sync
- **Service binding** — C3PO Worker ↔ site (already stubbed in `wrangler.toml`)
- **Pinecone** — already in use by C3PO; reused for semantic search
- **Pinata** — IPFS pinning for PDF resources
- **Stripe** — patron subscriptions and donations
- **Resend** — transactional email (auth, notifications)

---

## Phase 0 — CF Pages Migration *(in progress)*

See `MIGRATION.md`. Prerequisite for all phases below.

---

## Phase 1 — Framework Evaluation and Decision *(before any dynamic work begins)*

The current stack (Astro 5, `output: "static"`) was chosen for a static magazine/library site. The planned features — live Substack, C3PO chat, streaming MCP, semantic search, ETH auth, content gating — make this a dynamic web application. **Committing to the framework now prevents a painful mid-build switch later.**

### What matters for this decision

| Criterion | Weight | Notes |
|---|---|---|
| Content layer migration cost | High | 280 resource Markdown files + Substack history must go somewhere |
| Streaming support | High | MCP server and C3PO chat require streaming responses |
| CF bindings (D1, KV, R2) | Medium | All serious contenders support these; not a differentiator |
| Build complexity | Medium | A build step is fine; a complex one creates CI friction |
| Team maintainability | High | Small team, occasional contributors |

### Options

#### Option A — Astro hybrid mode (keep current framework)

Switch `output: "static"` → `output: "hybrid"` and add `@astrojs/cloudflare` adapter. Static pages stay static; new dynamic routes (magazine, search, auth) opt into SSR per-page via `export const prerender = false`.

**Keep:** all 280 resource Markdown files, existing components (ResourceCard, Nav, Footer), Fuse.js search, RSS feed, Substack sync infrastructure.
**Add:** D1 for live magazine posts, KV for sessions, Worker routes for C3PO and auth.

Pros:
- Lowest migration cost — existing content layer is preserved intact
- `@astrojs/cloudflare` adapter is mature and first-class
- Hybrid mode is well-suited to a mostly-static site with some dynamic endpoints
- Familiar to anyone who has worked on the current codebase

Cons:
- Astro's mental model is static-first; SSR feels like a workaround as dynamic features grow
- Streaming responses (MCP, C3PO chat) are possible but require care with Astro's response handling
- Content Collections (Markdown) and D1 become two separate content systems to maintain

#### Option B — Bespoke CF Workers (Hono + HTMX)

Abandon the framework entirely. The site becomes a CF Worker that renders HTML server-side using [Hono](https://hono.dev) (a lightweight CF-native web framework) + HTMX for interactive fragments. No build step.

**Rebuild:** content rendering, resource library, magazine feed — but all content moves to D1 (one-time migration from Markdown), which is cleaner long-term.
**Keep:** all CSS, assets, and site design.

Pros:
- Maximum CF-native control — D1, KV, R2, streaming, cron triggers all feel natural
- Streaming is first-class: MCP and C3PO chat are trivial to implement
- No build step; the Worker IS the site
- A single coherent architecture (no static/dynamic split)

Cons:
- Full rebuild of content rendering and resource library (~280 files → D1 migration)
- Hono + HTMX is a less common stack; fewer contributors will be familiar with it
- Loss of Astro's type-safe Content Collections (but Zod schema can be replicated on D1)

#### Option C — SvelteKit + CF adapter

Full rewrite using SvelteKit with `@sveltejs/adapter-cloudflare`. SvelteKit is designed for full-stack dynamic apps; the CF adapter is mature and widely used.

**Rebuild:** all pages and components in Svelte syntax; content moves to D1.
**Keep:** all CSS, assets, design.

Pros:
- Best DX for a dynamic-first site — data loading, form actions, and streaming all feel natural
- CF adapter has full D1/KV/R2 support via platform.env
- Svelte components are readable for contributors without deep framework knowledge
- Streaming (for MCP, C3PO) is well-supported

Cons:
- Full component rewrite
- Content layer migration: Markdown → D1 (same as Option B)
- Adds a new framework to the PI stack (currently: plain HTML on .org, Astro on .io)

### Recommendation

**If content layer continuity is the priority → Option A.** The Markdown resource files and Astro Content Collections represent significant curation work. Hybrid mode preserves them while adding dynamic capabilities incrementally.

**If clean architecture for dynamic features is the priority → Option B or C.** The site's future is more dynamic app than static magazine. A clean break now avoids accumulating hybrid-mode complexity. Option B (bespoke Workers + Hono) is the most CF-native and keeps the stack minimal. Option C (SvelteKit) is better if the site will have regular contributors who need an approachable framework.

**Decision should be made before Phase 2 begins.** The rest of this roadmap describes features in framework-agnostic terms; implementation notes call out where the choice matters.

---

## Phase 2 — Live Substack Mirroring + Events *(after Phase 1 decision)*

### Live Substack mirroring

Replace the GitHub Actions daily cron with a **CF Workers Cron Trigger** (every 15–30 minutes).

Current flow: `sync-substack.yml` → `scripts/sync-substack.py` → commits Markdown to repo → triggers rebuild.

New flow:
1. CF Worker cron polls Protocolized RSS feed
2. Compares against D1 `posts` table; inserts new posts, skips existing
3. Magazine page reads from D1 on request — no rebuild, no commit

D1 schema:
```sql
posts (slug, title, description, date, url, content_html, tags, created_at)
```

**Framework impact:** in Option A, the magazine page switches from static (Astro Content Collections) to SSR (reads D1). In Options B/C, the magazine page is already server-rendered — only the cron Worker changes.

Existing Markdown post files can be migrated to D1 in bulk (one-time import script) or kept as historical record with D1 used only for new posts.

### Events calendar

New `/events` route (server-rendered regardless of framework).

- Worker fetches Protocol Institute Google Calendar API; results cached in KV (TTL: 1h)
- Page renders upcoming events: title, date, description, registration link
- Same `GCAL_API_KEY` secret as protocol-institute.org; both sites can read from the same calendar

---

## Phase 3 — IPFS Resource Migration *(can run parallel to Phase 2)*

Move ~353 MB of PDFs out of the git repository. Framework-independent — this is a data migration and a Worker route, not a site-framework concern.

### Why IPFS + R2 (not just R2)

R2 URLs are tied to PI's CF account. IPFS CIDs are content-addressed and permanent — the same file always has the same CID, verifiable by anyone, accessible via any gateway. R2 serves as the **performance mirror**: fast and cheap for the 99% case, IPFS gateway as fallback.

### Steps

1. **Upload PDFs to IPFS** via Pinata API (`scripts/ipfs-upload.py`): for each PDF, upload → receive CID → store `{filename → CID}` in a local JSON.

2. **Update resource records** with `ipfs_cid` field:
   - Option A: add `ipfs_cid: z.string().optional()` to Astro Content Collections config; script patches each Markdown file's frontmatter
   - Options B/C: add `ipfs_cid` column to D1 `resources` table; script runs SQL updates

3. **Upload to R2** (`protocolized-resources` bucket) as performance mirror.

4. **Worker route** at `/resources/files/[slug]`: serves from R2 (fast); falls back to IPFS gateway. Gated resources (Phase 6) get R2 signed URLs instead of public access.

5. **Remove PDFs from repo**: `git rm public/resources/*.pdf`. Full history purge requires `git-filter-repo` — do this as a separate cleanup step after the migration is verified.

### Access model

| Resource type | Storage | Served via |
|---|---|---|
| Public PDFs | IPFS (pinned) + R2 mirror | R2 public URL or Worker proxy |
| Gated PDFs | R2 private only | Worker-generated signed URL (after auth check) |

---

## Phase 4 — C3PO Embed + Semantic Search *(after CF migration)*

### C3PO chat widget

C3PO (CF Worker — `vgururao/c3po`, migrating to `Protocol-Institute/c3po`) integrates via the service binding already stubbed in `wrangler.toml`. No cross-origin requests; queries go page → site Worker → C3PO via binding.

The Resources page gains a chat panel. Rate limiting: KV-backed by IP or session. Unauthenticated users get a daily query budget; authenticated members (Phase 6) get more.

**Framework impact:** in all options the actual C3PO call is identical (service binding). The chat UI is an HTMX fragment (Options B/C) or an Astro island (Option A).

### Semantic search

C3PO's Pinecone index already covers the full corpus. Add a semantic search mode alongside Fuse.js:

- Resources page: toggle **Keyword** (Fuse.js, client-side) | **Semantic** (Pinecone, via C3PO binding)
- Semantic: query → site Worker → C3PO `/search` → Pinecone top-K → matching resource slugs → rendered cards
- Resource detail pages: "Related resources" section via Pinecone similarity, cached in KV at render time

No new vector infrastructure needed — this reuses C3PO's existing index.

---

## Phase 5 — MCP Server *(extends Phase 4)*

Expose C3PO as a **Model Context Protocol** server so AI assistants (Claude, Cursor, etc.) can query the PI corpus as a tool.

### Transport

New route on the C3PO Worker: `GET /mcp` (SSE) + `POST /mcp` (JSON-RPC 2.0). CF Workers support streaming natively; this is the right runtime for MCP regardless of site framework.

### Tools

| Tool | Description |
|---|---|
| `search_protocols(query, n?)` | Semantic search, returns top-N results with metadata |
| `get_resource(slug)` | Full metadata + abstract for a specific resource |
| `ask_corpus(question)` | RAG query: retrieve + synthesize, return answer with citations |
| `list_resources(type?, tag?)` | Filtered resource listing |

### Auth and discovery

- API key per client (`Authorization: Bearer <key>`), rate-limited via KV
- `/.well-known/mcp.json` on `protocolized.io` advertises the server URL
- `llms.txt` (already exists) updated with MCP connection instructions

---

## Phase 6 — Ethereum Authentication + Content Gating *(after Phase 3)*

### SIWE

Sign-In with Ethereum (EIP-4361). Same approach as protocol-institute.org Phase 4; coordinate to use the same wallet widget provider (Dynamic.xyz or Privy) across both sites.

Worker routes (framework-independent):
- `/api/auth/nonce` — generate nonce, store in KV with short TTL
- `/api/auth/verify` — validate SIWE message, set signed session cookie (KV-backed, 24h TTL)

### Content gating

Three access tiers on resource records:

```
public   — any visitor; IPFS + R2 public access
member   — verified ETH address (any wallet); R2 signed URL
patron   — active Stripe subscription or token holder; R2 signed URL
```

**Framework impact:** the `access` field lives in Markdown frontmatter (Option A) or a D1 column (Options B/C). The Worker auth logic and R2 signed URL generation are identical across all options.

### Token gating (Phase 6b)

If PI issues a membership NFT or ERC-20: Worker checks on-chain balance via Alchemy/Infura RPC. Token holders get `patron` access without a Stripe subscription.

---

## Phase 7 — Donations + Patron Membership *(can overlap Phase 6)*

### Fiat — Stripe

- Worker at `/api/subscribe` creates a Stripe Checkout Session (subscription or one-time)
- Webhook at `/api/stripe/webhook` handles fulfillment: write patron status to D1
- If ETH address is linked (Phase 6), associate subscription with address; otherwise store by email

### Crypto — Ethereum

- ETH/USDC to PI treasury address — EIP-681 URI + QR code (no server-side logic)
- After SIWE is live: one-click donation from connected wallet

### Patron benefits

- Access to `member` and `patron` gated resources
- Higher C3PO query quota
- Future: Discord role sync, early access to Protocolized issues

---

## Shared Infrastructure with protocol-institute.org

| Resource | Shareable? | Notes |
|---|---|---|
| GCal API key | Yes | Same calendar source for both sites |
| Stripe account | Yes | Single PI Stripe account, different products |
| C3PO Worker | Yes | Service binding works from both CF Pages projects |
| D1 member/patron data | Maybe | Simplest if PI membership is unified across both sites |
| SIWE/auth Worker | Via shared Worker | A standalone PI auth Worker both sites bind to avoids duplicating the session logic |

---

## Dependency Graph

```
Phase 0 (CF migration)
  └── Phase 1 (framework decision) ← gate for all dynamic work
        ├── Phase 2 (live Substack + events)
        ├── Phase 3 (IPFS migration) ← prerequisite for Phase 6 gating
        │     └── Phase 6 (ETH auth + content gating)
        │           └── Phase 7 (donations + patron membership)
        ├── Phase 4 (C3PO + semantic search)
        │     └── Phase 5 (MCP server)
        └── Phase 7 (Stripe — can start independently of Phase 6)
```

---

## Open Questions

- **Framework** (Phase 1): Option A (Astro hybrid), B (bespoke Workers + Hono), or C (SvelteKit)? Decision needed before Phase 2.
- **Content layer**: migrate existing 280 Markdown resource files to D1, or keep Markdown + add D1 for new content? Affects all options.
- **IPFS pinning**: Pinata vs Filebase? (Pinata recommended — active, good API, generous free tier.)
- **SIWE wallet widget**: Dynamic.xyz vs Privy? Coordinate with .org to use the same provider across both sites.
- **Unified PI membership**: shared D1 across .org and .io, or separate? Shared is simpler if membership is a single PI concept.
- **Token gating** (Phase 6b): will PI issue a membership NFT or token? Determines whether on-chain balance checks are needed.
- **MCP auth**: public API key or gated behind ETH auth? (API key recommended initially.)
- **Substack history**: full D1 migration, or hybrid (Markdown for past, D1 for new posts)?
