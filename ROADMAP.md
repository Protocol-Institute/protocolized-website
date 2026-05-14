# Roadmap — protocolized.io

Features planned for the CF-powered version of the site. Most require a foundational architecture upgrade (Phase 1) before they can be built.

CF resources needed across all phases:
- **D1** — magazine posts cache, events, member/patron data
- **KV** — sessions, SIWE nonces, rate limiting
- **R2** — PDF mirror/cache (alongside IPFS), gated resource serving
- **Workers Cron Triggers** — live Substack sync (replaces GitHub Actions cron)
- **Service binding** — C3PO Worker ↔ Pages (already stubbed in `wrangler.toml`)
- **Pinecone** — already in use by C3PO; reused for semantic search
- **Pinata** — IPFS pinning service for PDF resources
- **Resend** — email for auth (if email PIN auth added, per .org Phase 2 pattern)
- **Stripe** — patron subscriptions and donations

---

## Phase 0 — CF Pages Migration *(in progress)*

See `MIGRATION.md`. Prerequisite for all phases below. Completes the move from GitHub Pages to Cloudflare Pages and installs the GitHub Actions `deploy.yml` using `cloudflare/pages-action`.

---

## Phase 1 — Architecture Upgrade: Astro Hybrid Mode *(first CF work session)*

**This is a prerequisite for Phases 2–7.** Currently `astro.config.mjs` sets `output: "static"` — the entire site pre-renders at build time. Dynamic features (live magazine, C3PO chat, semantic search, auth) require server-rendered routes.

Switch to Astro **hybrid** output mode with `@astrojs/cloudflare` adapter:

```js
// astro.config.mjs
import cloudflare from "@astrojs/cloudflare";
export default defineConfig({
  output: "hybrid",   // static by default; pages opt into SSR individually
  adapter: cloudflare(),
  ...
});
```

With hybrid mode:
- All existing pages stay static (`export const prerender = true` is the default)
- New dynamic routes (magazine feed, search, C3PO, auth) opt into SSR per-page
- D1, KV, R2 bindings become available in server routes via `Astro.locals.runtime.env`
- Build output is still deployed to CF Pages; dynamic routes become Workers automatically

Add `@astrojs/cloudflare` as a dev dependency. Add D1 and KV bindings to `wrangler.toml` now (even before the databases are created) so they're ready.

---

## Phase 2 — Live Substack Mirroring + Events *(quick wins after Phase 1)*

### Live Substack mirroring

Replace the GitHub Actions daily cron with a **CF Workers Cron Trigger** running every 15–30 minutes.

Current flow: `sync-substack.yml` → `scripts/sync-substack.py` → commits Markdown to repo → triggers Pages rebuild.

New flow:
1. CF Worker cron trigger polls the Protocolized RSS feed
2. Compares against D1 (`posts` table) — inserts new posts, skips existing
3. No repo commit, no rebuild; the `magazine.astro` page switches from static to SSR and reads from D1 directly

D1 schema:
```sql
posts (slug, title, description, date, url, content_html, tags, created_at)
```

The existing Markdown files in `src/content/` can be migrated to D1 in bulk (one-time import). Or kept as the historical record and D1 used only for new posts — hybrid content sources work fine in Astro.

Benefit: new Protocolized issues appear on the site within 30 minutes of publication, with no CI job or commit required.

### Events calendar

New `/events` page (SSR route).

- Worker fetches the Protocol Institute Google Calendar API on request (or on a CF cron, cached in D1)
- Same GCal API key as protocol-institute.org; store as CF Pages secret `GCAL_API_KEY`
- Page renders upcoming events with title, date, description, registration link
- If a PI org-wide calendar exists, both sites can read from the same GCal source

---

## Phase 3 — IPFS Resource Migration *(can run parallel to Phase 2)*

Move ~353 MB of PDFs out of the git repository. Keeps resource URLs stable and permanent regardless of hosting changes.

### Why IPFS (not just R2)

R2 is controlled infrastructure — URLs break if PI changes hosting. IPFS CIDs are content-addressed and permanent: the same file always has the same CID, any gateway can serve it, and the content can be independently verified.

R2 is still used as a **performance mirror** — CF Workers serve from R2 (fast, cheap) and fall back to an IPFS gateway only if needed.

### Migration steps

1. **Upload PDFs to IPFS** via Pinata API (script: `scripts/ipfs-upload.py`):
   - For each PDF in `public/resources/`, upload to Pinata, receive CID
   - Store `{filename → CID}` mapping in a local JSON for the next step

2. **Update resource Markdown frontmatter**: add `ipfs_cid` field to each resource file
   - Update `src/content/config.ts` to include `ipfs_cid: z.string().optional()`
   - Script updates all ~82 PDF resources with their CID

3. **Upload PDFs to R2** (`protocolized-resources` bucket) as the performance mirror

4. **Remove PDFs from repo**: `git rm public/resources/*.pdf`
   - Note: large files in git history require `git-filter-repo` to fully purge; do this as a separate step to avoid disrupting branch history during active development

5. **Serve via Worker**: a route at `/resources/files/[cid]` proxies from R2 (or IPFS gateway as fallback). Gated resources (Phase 6) use R2 signed URLs instead of public access.

### Access model

| Resource type | Storage | Served via |
|---|---|---|
| Public PDFs | IPFS (pinned) + R2 mirror | R2 public URL or CF Worker proxy |
| Gated PDFs | R2 only (private) | CF Worker signed URL (after auth) |

---

## Phase 4 — C3PO Public Embed + Semantic Search *(after CF migration)*

### C3PO chat widget

C3PO (CF Worker — `vgururao/c3po`, migrating to `Protocol-Institute/c3po`) is integrated into the Resources page via the service binding already stubbed in `wrangler.toml`:

```toml
[[services]]
binding = "C3PO"
service = "c3po-worker"
```

The Resources page gains a chat panel. User queries go from the page → Pages Function (SSR route) → C3PO via service binding (no cross-origin, no CORS). C3PO queries Pinecone, calls Claude, returns cited sources.

Rate limiting: KV-backed, by IP or session. Unauthenticated users get N queries/day; authenticated members get more.

### Semantic search

C3PO already has the full corpus indexed in Pinecone. Replacing or augmenting Fuse.js with semantic search:

- Resources page gets a search mode toggle: **Keyword** (Fuse.js, client-side) | **Semantic** (Pinecone, via C3PO binding)
- Semantic mode: query → C3PO `/search` endpoint → Pinecone top-K → return matching resource slugs → display resource cards
- Resource detail pages: "Related resources" section using Pinecone similarity (fetch once at SSR render time, cache in KV)

This reuses C3PO's existing infrastructure with no new vector DB setup.

---

## Phase 5 — MCP Server *(extends Phase 4)*

Expose C3PO as a **Model Context Protocol** server so AI assistants (Claude, Cursor, etc.) can query the Protocol Institute corpus as a tool.

### Endpoint

A new route on the C3PO Worker: `GET /mcp` (SSE) and `POST /mcp` (JSON-RPC 2.0).

CF Workers support streaming responses natively, which MCP's SSE transport requires.

### Tools exposed

| Tool | Description |
|---|---|
| `search_protocols(query, n?)` | Semantic search over corpus, returns top-N results with metadata |
| `get_resource(slug)` | Returns full metadata + abstract for a specific resource |
| `ask_corpus(question)` | Full RAG query: retrieves + synthesizes, returns answer with citations |
| `list_resources(type?, tag?)` | Filtered listing of corpus resources |

### Auth

MCP connections authenticated via API key (`Authorization: Bearer <key>`). Keys issued per-client, stored as CF secrets, rate-limited via KV.

### Discovery

- `/.well-known/mcp.json` on `protocolized.io` advertises the MCP server URL
- `llms.txt` (already exists) updated with MCP connection instructions
- Documentation page: `src/pages/api-access.astro`

---

## Phase 6 — Ethereum Authentication + Content Gating *(after Phase 3 IPFS migration)*

### SIWE implementation

Sign-In with Ethereum (EIP-4361) — same stack as protocol-institute.org Phase 4:
- Use Dynamic.xyz or Privy for wallet connection widget (CDN-loaded, works in Astro)
- CF Worker routes: `/api/auth/nonce` (generates nonce, stores in KV) and `/api/auth/verify` (validates SIWE message, sets session cookie)
- Session backed by KV (24h TTL)

### Content gating model

Three access tiers, defined in resource frontmatter:

```yaml
access: public | member | patron   # default: public
```

- **public** — served to anyone; public IPFS CID + R2 mirror
- **member** — requires verified ETH address (any wallet); served via R2 signed URL
- **patron** — requires active Stripe subscription or token holding; served via R2 signed URL

Add `access` field to `src/content/config.ts` (optional, defaults to `"public"`).

### Token gating (Phase 6b)

If PI issues a membership token or NFT: Worker checks on-chain balance via an Ethereum RPC call (Alchemy or Infura, or CF's own blockchain RPC if available). Token holders get `patron` access automatically without a Stripe subscription.

---

## Phase 7 — Donations + Patron Membership *(can overlap Phase 6)*

### Fiat — Stripe

- Stripe Checkout for one-time donations and recurring patron subscriptions
- Worker at `/api/subscribe` creates a Checkout session; `/api/webhook` handles fulfillment
- On successful subscription: write `{eth_address → patron}` to D1 (if ETH address is linked), or `{email → patron}` for non-ETH users
- `support.astro` page replaces placeholder content with Stripe widget

### Crypto — Ethereum

- ETH/USDC donation to PI treasury address
- EIP-681 payment request URI + QR code (no server-side logic needed)
- For USDC: standard ERC-20 transfer
- After SIWE is live (Phase 6): one-click donation from connected wallet

### Patron benefits

- Access to `member` and `patron` resources (Phase 6 gating)
- Increased C3PO query quota
- Future: early access to Protocolized issues, Discord role sync

---

## Shared Infrastructure with protocol-institute.org

Some CF resources can be shared between the two sites if they're in the same CF account:

| Resource | Shareable? | Notes |
|---|---|---|
| GCal API key | Yes | Same calendar source for both sites |
| Stripe account | Yes | Single Stripe account for PI, different products |
| C3PO Worker | Yes | Service binding from both Pages projects |
| D1 member/patron data | Maybe | Depends on whether membership is unified across both sites |
| SIWE/session logic | Via shared Worker | Auth Worker could be a standalone service both sites bind to |

---

## Dependency Graph

```
Phase 0 (CF migration)
  └── Phase 1 (Astro hybrid mode) ← prerequisite for all below
        ├── Phase 2 (live Substack + events)
        ├── Phase 3 (IPFS migration) ← prerequisite for Phase 6 gating
        │     └── Phase 6 (ETH auth + content gating)
        │           └── Phase 7 (donations + patron membership)
        ├── Phase 4 (C3PO embed + semantic search)
        │     └── Phase 5 (MCP server)
        └── Phase 7 (donations — can start Stripe independently of Phase 6)
```

## Open Questions

- Pinata vs Filebase vs web3.storage successor for IPFS pinning? (Pinata recommended — active, good API, generous free tier.)
- Dynamic.xyz vs Privy for SIWE wallet widget? (Same question as .org — evaluate once member count is known; coordinate with .org to use the same provider.)
- Unified PI membership across .org and .io, or separate? (Shared D1 in same CF account is simplest if unified.)
- Token-gating (Phase 6b): will PI issue a membership NFT or ERC-20 token? (Determines whether on-chain gating is needed or Stripe subscription alone suffices.)
- MCP auth model: public (API key per client) or gated behind ETH auth? (API key recommended initially — simpler to instrument and rate-limit.)
- For the Substack migration to D1: keep existing Markdown files as historical record, or full migration to D1? (Hybrid approach — keep Markdown for pre-D1 content, D1 for new posts — is lowest risk.)
