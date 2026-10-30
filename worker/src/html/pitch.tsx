import { Base } from "./base";
import { fmtDate, mobileMenuScript } from "./static-pages";
import { PI_SITE, type PdfMeta } from "../pitch";

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
@page{size:Letter;margin:24mm 24mm 26mm;
  @bottom-left{content:"Protocol Institute";font:7.5pt Outfit,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#9a9a94}
  @bottom-right{content:counter(page);font:8pt Outfit,sans-serif;color:#9a9a94}}
body{background:#fff;margin:0}
.pitch-doc{font-size:10.3pt;line-height:1.62;color:#222}
.masthead{display:flex;align-items:center;justify-content:space-between;padding-bottom:9mm;margin-bottom:11mm;border-bottom:.5pt solid #cfcfc8}
.masthead .brand{display:flex;align-items:center;gap:4mm}
.masthead img{height:13mm;width:auto}
.masthead .org{font:500 8.5pt Outfit,sans-serif;letter-spacing:.2em;text-transform:uppercase;color:#222}
.masthead .stamp{font:7.5pt Outfit,sans-serif;letter-spacing:.06em;color:#9a9a94}
.pitch-doc h1{font-size:34pt;line-height:1.05;letter-spacing:-.01em;margin:0 0 3mm}
.pitch-doc h1 + p{font-size:9.5pt;color:#77776f;margin:0 0 9mm}
.pitch-doc h2{font-size:18pt;color:#222;margin:11mm 0 3mm;padding-top:5mm;border-top:.5pt solid #cfcfc8;break-after:avoid}
.pitch-doc h3{font:600 8.5pt Outfit,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#0F6E56;margin:7mm 0 2mm;break-after:avoid}
.pitch-doc p{margin:0 0 3.2mm;orphans:3;widows:3}
.pitch-doc a{color:inherit;text-decoration:none;border-bottom:.4pt solid #0F6E56}
.pitch-doc ul.people,.pitch-doc ul.roadmap{margin:2mm 0 4mm}
.pitch-doc ul.people li,.pitch-doc ul.roadmap li{border-left:0;padding:2.4mm 0;margin:0;border-bottom:.4pt solid #e4e4de;break-inside:avoid}
.pitch-doc ul.people li:last-child,.pitch-doc ul.roadmap li:last-child{border-bottom:0}
.pitch-doc li{break-inside:avoid}
.pitch-doc .notes{margin-top:12mm;font-size:8.6pt;color:#555}
.pitch-doc .notes h2{font-size:12pt;border-top:.5pt solid #cfcfc8}
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
<body><article class="pitch-doc">
<header class="masthead"><div class="brand"><img src="${PI_SITE}/assets/logo-static.png" alt=""><span class="org">Protocol Institute</span></div><span class="stamp">${stamp}</span></header>
${html}</article></body></html>`;
}
