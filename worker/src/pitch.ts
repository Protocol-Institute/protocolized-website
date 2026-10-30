import { marked } from "marked";

// Password-protected living pitch document (/pitch).
//
// The prose lives in R2 (pitch/source.md): the repo is public and the pitch
// carries fundraising figures, so the text never enters git. Lists that go
// stale ({{team}}, {{research-groups}}, {{roadmap-projects}}, the counts) are
// directives in that markdown, expanded on every request from the Institute
// site's public APIs. The PDF is built from /pitch/print by a GitHub Action.

export const PI_SITE = "https://protocol-institute.org";
const ROADMAP_PROGRAM = "research-roadmap";
const ROADMAP_YEAR = "2027";

export interface PitchEnv {
  FILES: R2Bucket;
  PITCH_PASSWORD?: string;
  /** Second password: grants the read-only view plus the markdown editor. */
  PITCH_EDIT_PASSWORD?: string;
}

// ── Auth ───────────────────────────────────────────────────────────────────

const VIEW_COOKIE = "pitch_session";
const EDIT_COOKIE = "pitch_edit";

async function hmacHex(key: string, msg: string): Promise<string> {
  const k = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(key),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(msg));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

// The cookie is derived from the password, so rotating the password signs
// everyone out and no separate session secret is needed.
export const sessionToken = (password: string) => hmacHex(password, "pitch-session-v1");

async function matches(secret: string | undefined, attempt: string): Promise<boolean> {
  if (!secret) return false;
  const [x, y] = await Promise.all([hmacHex("cmp", attempt), hmacHex("cmp", secret)]);
  return safeEqual(x, y);
}

export type Role = "viewer" | "editor";

/** Which password (if either) this attempt is. The edit password also grants viewing. */
export async function roleFor(env: PitchEnv, attempt: string): Promise<Role | null> {
  if (await matches(env.PITCH_EDIT_PASSWORD, attempt)) return "editor";
  if (await matches(env.PITCH_PASSWORD, attempt)) return "viewer";
  return null;
}

/** Cookies set on login; each is an HMAC keyed by its own password. */
export async function sessionCookies(env: PitchEnv, role: Role): Promise<string[]> {
  const out = [`${VIEW_COOKIE}=${await hmacHex(env.PITCH_PASSWORD!, "pitch-session-v1")}`];
  if (role === "editor") out.push(`${EDIT_COOKIE}=${await hmacHex(env.PITCH_EDIT_PASSWORD!, "pitch-edit-v1")}`);
  return out.map((c) => `${c}; Path=/pitch; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000`);
}

function cookieOf(req: Request, name: string): string | undefined {
  return req.headers.get("Cookie")?.match(new RegExp(`(?:^|;\\s*)${name}=([0-9a-f]+)`))?.[1];
}

/** Editors only: the edit-password cookie, or Bearer edit password. */
export async function isEditor(env: PitchEnv, req: Request): Promise<boolean> {
  const pw = env.PITCH_EDIT_PASSWORD;
  if (!pw) return false;
  const bearer = req.headers.get("Authorization")?.match(/^Bearer (.+)$/)?.[1];
  if (bearer && (await matches(pw, bearer))) return true;
  const c = cookieOf(req, EDIT_COOKIE);
  return !!c && safeEqual(c, await hmacHex(pw, "pitch-edit-v1"));
}

/** Viewing: the view cookie (or Bearer password, used by the PDF build), or any editor. */
export async function isAuthed(env: PitchEnv, req: Request): Promise<boolean> {
  if (await isEditor(env, req)) return true;
  const pw = env.PITCH_PASSWORD;
  if (!pw) return false;
  const bearer = req.headers.get("Authorization")?.match(/^Bearer (.+)$/)?.[1];
  if (bearer && (await matches(pw, bearer))) return true;
  const c = cookieOf(req, VIEW_COOKIE);
  return !!c && safeEqual(c, await hmacHex(pw, "pitch-session-v1"));
}

/** Save a new source, keeping the previous one under pitch/history/ so any edit can be rewound. */
export async function saveSource(env: PitchEnv, md: string): Promise<void> {
  const prev = await env.FILES.get("pitch/source.md");
  if (prev) await env.FILES.put(`pitch/history/${new Date().toISOString().replace(/[:.]/g, "-")}.md`, await prev.text());
  await env.FILES.put("pitch/source.md", md, { httpMetadata: { contentType: "text/markdown; charset=utf-8" } });
}

export const getSource = async (env: PitchEnv) => (await env.FILES.get("pitch/source.md"))?.text() ?? null;

// ── Live data ──────────────────────────────────────────────────────────────

interface Host { slug: string; name: string }
interface Program { slug: string; kind: string; status: string; title: string; description: string; href: string; hosts: Host[] }
interface Member {
  slug: string; name: string; bio: string | null; tier: string;
  team_title: string | null; team_core: number; team_sort: number | null;
}
interface ProjectProgram { slug: string; kind: string; title: string; status: string; edition: { slug: string } | null }
interface Project { slug: string; title: string; description: string; lead_name: string | null; programs: ProjectProgram[] }

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(PI_SITE + path, { cf: { cacheTtl: 300, cacheEverything: true } } as RequestInit);
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export interface LiveData {
  groups: Program[];
  members: Member[];
  roadmap: Project[];
}

export async function fetchLive(): Promise<LiveData> {
  const [programs, members, projects] = await Promise.all([
    getJson<{ programs: Program[] }>("/api/programs?detail=1"),
    getJson<{ members: Member[] }>("/api/members"),
    getJson<{ projects: Project[] }>("/api/projects"),
  ]);
  return {
    groups: programs.programs.filter((p) => p.kind === "sig" && p.status === "active"),
    members: members.members,
    roadmap: projects.projects.filter((p) =>
      p.programs.some((a) => a.slug === ROADMAP_PROGRAM && a.status === "approved" && a.edition?.slug === ROADMAP_YEAR)
    ),
  };
}

// ── Rendering ──────────────────────────────────────────────────────────────

const esc = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/** First paragraph, markdown links/emphasis flattened: user-written text is shown as plain text. */
function abstract(md: string | null, max = 420): string {
  const first = (md ?? "").trim().split(/\n\s*\n/)[0] ?? "";
  const plain = first.replace(/\[([^\]]+)\]\([^)]*\)/g, "$1").replace(/[*_`#>]/g, "").replace(/\s+/g, " ").trim();
  if (plain.length <= max) return plain;
  const cut = plain.slice(0, max);
  return cut.slice(0, Math.max(cut.lastIndexOf(" "), 0)) + "…";
}

const listOf = (names: string[]) =>
  names.length <= 2 ? names.join(" and ") : `${names.slice(0, -1).join(", ")}, and ${names[names.length - 1]}`;

const profile = (m: Member) =>
  `<strong><a href="${PI_SITE}/members/profile?slug=${encodeURIComponent(m.slug)}">${esc(m.name)}</a></strong>`;

function teamHtml(d: LiveData): string {
  const core = d.members
    .filter((m) => m.team_core)
    .sort((a, b) => (a.team_sort ?? 99) - (b.team_sort ?? 99));
  return `<ul class="people">${core
    .map((m) => {
      const bio = abstract(m.bio, 320);
      return `<li>${profile(m)}${m.team_title ? ` — ${esc(m.team_title)}` : ""}${bio ? `<br>${esc(bio)}` : ""}</li>`;
    })
    .join("")}</ul>`;
}

function leadsHtml(d: LiveData): string {
  const leads = d.members.filter((m) => m.tier === "community_lead");
  return `<ul class="people">${leads
    .map((m) => {
      const gs = d.groups.filter((g) => g.hosts.some((h) => h.slug === m.slug)).map((g) => g.title);
      return `<li>${profile(m)}${gs.length ? ` — ${esc(listOf(gs))}` : ""}</li>`;
    })
    .join("")}</ul>`;
}

function groupsHtml(d: LiveData): string {
  return `<ol class="groups">${d.groups
    .map((g) => {
      const leads = g.hosts.map((h) => h.name);
      return (
        `<li><strong><a href="${PI_SITE}${g.href}">${esc(g.title)}</a>:</strong> ${esc(abstract(g.description, 600))}` +
        `${leads.length ? ` <em>(lead${leads.length > 1 ? "s" : ""}: ${esc(listOf(leads))})</em>` : ""}</li>`
      );
    })
    .join("")}</ol>`;
}

function roadmapHtml(d: LiveData): string {
  return `<ul class="roadmap">${d.roadmap
    .map((p) => {
      const gs = p.programs.filter((a) => a.kind === "sig" && a.status === "approved").map((a) => a.title);
      const meta = [gs.length ? esc(listOf(gs)) : "", p.lead_name ? `lead: ${esc(p.lead_name)}` : ""].filter(Boolean);
      return (
        `<li><strong><a href="${PI_SITE}/projects/project/?slug=${encodeURIComponent(p.slug)}">${esc(p.title)}</a></strong>` +
        `${meta.length ? ` <span class="meta">(${meta.join("; ")})</span>` : ""}` +
        `<br>${esc(abstract(p.description, 300))}</li>`
      );
    })
    .join("")}</ul>`;
}

/** Footnotes: `[^1]` references and `[^1]: text` definitions, collected into a Notes list. */
function footnotes(md: string): { body: string; notes: string } {
  const defs = new Map<string, string>();
  const body = md.replace(/^\[\^(\w+)\]:\s*(.*)$/gm, (_, id: string, text: string) => {
    defs.set(id, text.trim());
    return "";
  });
  const order: string[] = [];
  const withRefs = body.replace(/\[\^(\w+)\]/g, (m, id: string) => {
    if (!defs.has(id)) return m;
    if (!order.includes(id)) order.push(id);
    return `<sup id="ref-${id}"><a href="#fn-${id}">${order.indexOf(id) + 1}</a></sup>`;
  });
  const notes = order.length
    ? `<section class="notes"><h2>Notes</h2><ol>${order
        .map((id) => `<li id="fn-${id}">${marked.parseInline(defs.get(id)!)} <a href="#ref-${id}">↩</a></li>`)
        .join("")}</ol></section>`
    : "";
  return { body: withRefs, notes };
}

export interface RenderedPitch {
  html: string;
  /** Content hash: changes when the text or any live list changes. */
  hash: string;
  /** True when the Institute APIs could not be reached, so live lists are placeholders. */
  degraded: boolean;
}

export async function renderPitch(env: PitchEnv): Promise<RenderedPitch | null> {
  const obj = await env.FILES.get("pitch/source.md");
  if (!obj) return null;
  let md = await obj.text();

  let live: LiveData | null = null;
  try {
    live = await fetchLive();
  } catch {
    live = null;
  }
  const unavailable = `<p class="note">Live list unavailable right now; reload shortly.</p>`;

  const counts: Record<string, string> = {
    "group-count": live ? String(live.groups.length) : "—",
    "roadmap-count": live ? String(live.roadmap.length) : "—",
  };
  md = md.replace(/\{\{([\w-]+-count)\}\}/g, (m, k: string) => counts[k] ?? m);

  // {{page:KEY}}: a public managed page on the Institute site (canonical copy of
  // that text, e.g. static/values), inlined so the PDF stands alone.
  const pageKeys = [...new Set([...md.matchAll(/^\{\{page:([\w/.-]+)\}\}[ \t]*$/gm)].map((m) => m[1]))];
  const pages = new Map<string, string>();
  let pagesOk = true;
  await Promise.all(
    pageKeys.map(async (k) => {
      try {
        pages.set(k, (await getJson<{ content_md: string }>(`/api/pages/${k}`)).content_md);
      } catch {
        pagesOk = false;
      }
    })
  );

  const blocks: Record<string, (d: LiveData) => string> = {
    team: teamHtml,
    "research-leads": leadsHtml,
    "research-groups": groupsHtml,
    "roadmap-projects": roadmapHtml,
  };

  const { body, notes } = footnotes(md);
  const parts = body.split(/^\{\{([\w:/.-]+)\}\}[ \t]*$/m); // text, name, text, name, …
  const html =
    parts
      .map((seg, i) => {
        if (i % 2 === 0) return marked.parse(seg, { async: false }) as string;
        if (seg.startsWith("page:")) {
          const pmd = pages.get(seg.slice(5));
          return pmd === undefined ? unavailable : (marked.parse(pmd, { async: false }) as string);
        }
        const build = blocks[seg];
        if (!build) return `<p class="note">Unknown directive: ${esc(seg)}</p>`;
        return live ? build(live) : unavailable;
      })
      .join("\n") + notes;

  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(html));
  const hash = [...new Uint8Array(digest)].slice(0, 12).map((b) => b.toString(16).padStart(2, "0")).join("");
  return { html, hash, degraded: !live || !pagesOk };
}

export interface PdfMeta { hash: string; built_at: string }

export async function getPdfMeta(env: PitchEnv): Promise<PdfMeta | null> {
  const obj = await env.FILES.get("pitch/pdf-meta.json");
  return obj ? ((await obj.json()) as PdfMeta) : null;
}
