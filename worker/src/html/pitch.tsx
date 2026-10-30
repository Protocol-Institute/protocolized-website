import { Base } from "./base";
import { fmtDate, mobileMenuScript } from "./static-pages";
import type { PdfMeta } from "../pitch";

// Typography for the pitch document, shared by the web page (scoped under
// .pitch-doc) and the standalone print template WeasyPrint renders.
const DOC_CSS = `
.pitch-doc{font-family:Lora,Georgia,serif;font-size:1.05rem;line-height:1.65;color:#2C2C2A}
.pitch-doc h1{font-family:'Instrument Serif',Georgia,serif;font-weight:400;font-size:2.6rem;line-height:1.1;margin:0 0 .3rem}
.pitch-doc h2{font-family:'Instrument Serif',Georgia,serif;font-weight:400;font-size:1.9rem;line-height:1.2;margin:2.4rem 0 .6rem;color:#0F6E56}
.pitch-doc h3{font-family:Outfit,sans-serif;font-weight:600;font-size:1.05rem;margin:1.6rem 0 .4rem}
.pitch-doc p{margin:.8rem 0}
.pitch-doc a{color:#0F6E56;text-decoration:underline;text-underline-offset:2px}
.pitch-doc ul,.pitch-doc ol{margin:.8rem 0;padding-left:1.5rem}
.pitch-doc li{margin:.5rem 0}
.pitch-doc ul.people,.pitch-doc ul.roadmap{list-style:none;padding-left:0}
.pitch-doc ul.people li,.pitch-doc ul.roadmap li{border-left:3px solid #E1F5EE;padding-left:.8rem}
.pitch-doc .meta{color:#6b6b66;font-size:.92em}
.pitch-doc .note{color:#D85A30;font-family:Outfit,sans-serif;font-size:.9rem}
.pitch-doc sup a{text-decoration:none}
.pitch-doc .notes{font-size:.9rem;margin-top:2.4rem;border-top:1px solid #ddd}
.pitch-doc .notes h2{font-size:1.3rem;color:#2C2C2A}
.pitch-doc em em,.pitch-doc strong em{font-style:italic}
`;

const PRINT_CSS = `
@page{size:Letter;margin:22mm 20mm 24mm;@bottom-center{content:"Protocol Institute Overview · " counter(page) " / " counter(pages);font:8pt Outfit,sans-serif;color:#888}}
body{background:#fff;margin:0}
.pitch-doc{font-size:10.5pt;line-height:1.5}
.pitch-doc h1{font-size:28pt}
.pitch-doc h2{font-size:17pt;margin-top:1.6rem;break-after:avoid}
.pitch-doc h3{break-after:avoid}
.pitch-doc li,.pitch-doc ul.people li{break-inside:avoid}
.pitch-doc a{text-decoration:none}
.stamp{font:8pt Outfit,sans-serif;color:#888;margin:0 0 1.2rem}
`;

// ── Login ──────────────────────────────────────────────────────────────────

export function PitchLoginPage({ error }: { error?: boolean }) {
  return (
    <Base
      title="Sign in"
      description="Protocol Institute overview. Password required."
      currentPath="/pitch"
      bodyScript={mobileMenuScript()}
      noindex
    >
      <section class="max-w-md mx-auto px-6 py-24">
        <h1 class="font-serif text-4xl text-dark mb-2">Protocol Institute overview</h1>
        <p class="font-sans text-secondary mb-8">This document is shared by invitation. Enter the password you were given.</p>
        <form method="post" action="/pitch/login" class="flex flex-col gap-3">
          <label class="font-sans text-sm text-secondary" for="pw">Password</label>
          <input id="pw" name="password" type="password" required autofocus autocomplete="current-password"
            class="border border-gray-300 rounded px-3 py-2 font-sans bg-white" />
          {error && <p class="font-sans text-sm text-accent">That password didn't match.</p>}
          <button type="submit" class="btn-primary self-start">Continue →</button>
        </form>
      </section>
    </Base>
  );
}

// ── Document page ──────────────────────────────────────────────────────────

export function PitchPage({ html, hash, pdf, degraded, canEdit }: {
  html: string; hash: string; pdf: PdfMeta | null; degraded: boolean; canEdit: boolean;
}) {
  const current = pdf?.hash === hash;
  return (
    <Base
      title="Protocol Institute overview"
      description="Protocol Institute overview. Password required."
      currentPath="/pitch"
      bodyScript={mobileMenuScript()}
      noindex
    >
      <style dangerouslySetInnerHTML={{ __html: DOC_CSS }} />
      <div class="max-w-3xl mx-auto px-6 py-10">
        <div class="flex flex-wrap items-center justify-between gap-3 mb-8 pb-4 border-b border-gray-200 font-sans text-sm">
          <div class="text-secondary">
            Living document · the team, research-group and roadmap lists update from the Institute site.
            {degraded && <span class="text-accent"> Live data is unreachable right now.</span>}
            {canEdit && <> <a href="/pitch/edit" class="underline">Edit text</a></>}
          </div>
          {pdf ? (
            <div class="flex items-center gap-3">
              <span class="text-secondary">
                PDF built {fmtDate(pdf.built_at.slice(0, 10))}{current ? "" : " · a newer version is being built"}
              </span>
              <a href="/pitch/protocol-institute-overview.pdf" class="btn-primary">Download PDF</a>
            </div>
          ) : (
            <span class="text-secondary">PDF not built yet</span>
          )}
        </div>
        <article class="pitch-doc" dangerouslySetInnerHTML={{ __html: html }} />
      </div>
    </Base>
  );
}

// ── Editor ─────────────────────────────────────────────────────────────────

export function PitchEditPage({ source }: { source: string }) {
  return (
    <Base title="Edit overview" currentPath="/pitch/edit" bodyScript={mobileMenuScript()} noindex>
      <div class="max-w-4xl mx-auto px-6 py-10 font-sans">
        <h1 class="font-serif text-3xl text-dark mb-2">Edit the overview</h1>
        <p class="text-sm text-secondary mb-4">
          Markdown. This is the private text of the pitch; saving keeps the previous version and the PDF rebuilds within
          about 15 minutes. Live blocks, each alone on its own line: <code>{"{{team}}"}</code>{" "}
          <code>{"{{research-leads}}"}</code> <code>{"{{research-groups}}"}</code> <code>{"{{roadmap-projects}}"}</code>{" "}
          <code>{"{{page:static/values}}"}</code> (any public managed page, inlined). Inline: <code>{"{{group-count}}"}</code>{" "}
          <code>{"{{roadmap-count}}"}</code>. Footnotes: <code>[^1]</code> and <code>[^1]: text</code>.
        </p>
        <form method="post" action="/pitch/edit">
          <textarea name="source" rows={36} spellcheck={true}
            class="w-full border border-gray-300 rounded p-3 font-mono text-sm bg-white">{source}</textarea>
          <div class="flex gap-4 items-center mt-3">
            <button type="submit" class="btn-primary">Save</button>
            <a href="/pitch" class="text-sm text-secondary underline">Cancel</a>
          </div>
        </form>
      </div>
    </Base>
  );
}

// ── Print template (what WeasyPrint renders) ───────────────────────────────

export function pitchPrintDocument(html: string, stamp: string): string {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Protocol Institute Overview</title>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif&family=Lora:ital,wght@0,400;0,500;1,400&family=Outfit:wght@400;500;600&display=swap" rel="stylesheet">
<style>${DOC_CSS}${PRINT_CSS}</style></head>
<body><article class="pitch-doc"><p class="stamp">${stamp}</p>${html}</article></body></html>`;
}
