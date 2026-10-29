import { Base } from "./base";
import { fmtDate, mobileMenuScript } from "./static-pages";
import { WIP_STAGES, type WipChecklistItem, type WipEntry, type WipProject } from "../wip";

// Work-in-progress pages are unlisted: noindex, absent from nav, sitemap,
// RSS and llms.txt. They are shareable by link while drafts are gathered.

function authorList(authors: string[]): string {
  if (authors.length <= 2) return authors.join(" and ");
  return `${authors.slice(0, -1).join(", ")}, and ${authors[authors.length - 1]}`;
}

function meanReadiness(p: WipProject): number {
  const s = p.contents.map((e) => e.readiness.score);
  return s.reduce((a, b) => a + b, 0) / s.length;
}

function titleOf(p: WipProject, id: string): string {
  return p.contents.find((e) => e.id === id)?.title ?? id;
}

function StagePill({ stage }: { stage: string }) {
  return (
    <span class="text-xs font-sans px-2.5 py-0.5 rounded-full bg-accent/10 text-accent font-medium">
      Work in progress · {WIP_STAGES[stage] ?? stage}
    </span>
  );
}

// ── Index ──────────────────────────────────────────────────────────────────

export function WipIndexPage({ currentPath, projects }: { currentPath: string; projects: WipProject[] }) {
  return (
    <Base
      title="Works in progress"
      description="Working documents from the Protocol Institute: volumes and resources being assembled before editing."
      currentPath={currentPath}
      bodyScript={mobileMenuScript()}
      noindex
    >
      <section class="py-16 md:py-20 px-6 lg:px-8">
        <div class="max-w-wide mx-auto">
          <h1 class="font-serif text-4xl md:text-5xl text-dark mb-3">Works in progress</h1>
          <p class="font-sans text-secondary text-lg max-w-2xl mb-10">
            Volumes and resources being assembled from drafts. Each one ends up in the resource library once it is edited and published.
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {projects.map((p) => (
              <a href={`/wip/${p.slug}`} class="group flex gap-5 items-start">
                <div class="w-24 h-36 shrink-0 bg-primary-light rounded overflow-hidden">
                  {p.cover && <img src={p.cover} alt="" class="w-full h-full object-cover" loading="lazy" />}
                </div>
                <div class="flex-1 min-w-0">
                  <h2 class="font-serif text-xl text-dark leading-snug group-hover:text-primary transition-colors mb-1">{p.title}</h2>
                  {p.subtitle && <p class="font-sans text-sm text-secondary italic mb-2">{p.subtitle}</p>}
                  <StagePill stage={p.stage} />
                  <p class="font-sans text-sm text-secondary mt-2">
                    {p.contents.length} pieces · mean readiness {meanReadiness(p).toFixed(1)}/10
                    {p.versions[0] && ` · draft v${p.versions[0].version}`}
                  </p>
                  {p.deadline && (
                    <p class="font-sans text-sm text-accent font-medium mt-1">
                      {p.deadline.label}: {longDate(p.deadline.date)}
                    </p>
                  )}
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>
    </Base>
  );
}

// ── Deadline and checklist ─────────────────────────────────────────────────

function daysUntil(date: string): number {
  const today = new Date(new Date().toISOString().slice(0, 10) + "T00:00:00Z");
  return Math.round((new Date(date + "T00:00:00Z").getTime() - today.getTime()) / 86_400_000);
}

function longDate(date: string): string {
  return new Date(date + "T00:00:00Z").toLocaleDateString("en-US", {
    weekday: "long", year: "numeric", month: "long", day: "numeric", timeZone: "UTC",
  });
}

function DeadlineBanner({ project }: { project: WipProject }) {
  const d = project.deadline;
  if (!d) return null;
  const left = daysUntil(d.date);
  const when = left > 1 ? `${left} days left` : left === 1 ? "Due tomorrow" : left === 0 ? "Due today" : "Deadline passed";
  return (
    <section class="px-6 lg:px-8 pt-6" aria-label="Deadline">
      <div class="max-w-wide mx-auto rounded-lg bg-accent text-white px-6 py-5 flex flex-col md:flex-row md:items-center gap-3 md:gap-8">
        <div class="shrink-0">
          <p class="font-sans text-xs uppercase tracking-wider text-white/80">{d.label}</p>
          <p class="font-serif text-3xl md:text-4xl leading-tight">{longDate(d.date)}</p>
          <p class="font-sans text-sm font-medium text-white/90">{when}</p>
        </div>
        <div class="flex-1">
          <p class="font-sans text-sm leading-relaxed text-white/95">{d.detail}</p>
          <p class="mt-2 font-sans text-sm font-medium">
            <a href={`/wip/${project.slug}/checklist`} class="underline underline-offset-2">Read the checklist →</a>
            <span class="mx-2 text-white/60" aria-hidden="true">·</span>
            <a href={`/wip/${project.slug}/checklist.md`} download class="underline underline-offset-2">Download (.md)</a>
          </p>
        </div>
      </div>
    </section>
  );
}

const STATUS_STYLE: Record<string, string> = {
  pass: "text-primary",
  fail: "text-accent",
  warn: "text-amber-700",
  manual: "text-secondary",
  na: "text-secondary",
};
const STATUS_MARK: Record<string, string> = { pass: "✓", fail: "✗", warn: "!", manual: "·", na: "–" };

function Checklist({ items }: { items: WipChecklistItem[] }) {
  const sections = [...new Set(items.map((i) => i.section))];
  return (
    <section id="checklist" class="mb-12 scroll-mt-24">
      <h2 class="font-serif text-2xl text-dark mb-1">Checklist for the next draft</h2>
      <p class="font-sans text-sm text-secondary mb-5 max-w-prose">
        Every essay's next draft should meet all of these. Items marked <span class="font-medium">auto</span> are checked by script against the draft in the shared folder; the editor checks the rest by reading.
      </p>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-6">
        {sections.map((sec) => (
          <div>
            <h3 class="font-sans text-xs uppercase tracking-wider text-primary mb-2">{sec}</h3>
            <ol class="space-y-3">
              {items.filter((i) => i.section === sec).map((i) => (
                <li class="font-sans text-sm">
                  <p class="text-dark font-medium">
                    {i.label}
                    {i.auto && <span class="ml-2 text-[10px] uppercase tracking-wider text-secondary border border-gray-300 rounded px-1 py-px align-middle">auto</span>}
                    {i.advisory && <span class="ml-1 text-[10px] uppercase tracking-wider text-secondary border border-gray-300 rounded px-1 py-px align-middle">guideline</span>}
                  </p>
                  <p class="text-secondary text-xs leading-relaxed mt-0.5">{i.detail}</p>
                  {i.licenses && (
                    <p class="text-xs mt-1">
                      <span class="text-dark">Accepted licenses:</span>{" "}
                      {i.licenses.map((l) => (
                        <span class="inline-block mr-1 mb-1 px-1.5 py-px rounded bg-primary-light text-primary">{l}</span>
                      ))}
                    </p>
                  )}
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>
    </section>
  );
}

function EntryChecks({ project, entry }: { project: WipProject; entry: WipEntry }) {
  const c = project.checks?.entries[entry.id];
  if (!c || !project.checklist) return null;
  const items = project.checklist;
  const auto = items.filter((i) => i.auto);
  const passing = auto.filter((i) => ["pass", "na"].includes(c.results[i.id]?.status)).length;
  const open = items.filter((i) => ["fail", "warn"].includes(c.results[i.id]?.status));
  return (
    <details class="mt-3 group">
      <summary class="cursor-pointer font-sans text-xs text-secondary list-none">
        <span class={c.summary.ready ? "text-primary font-medium" : "text-dark font-medium"}>
          Checklist: {passing} of {auto.length} automated checks pass
        </span>
        {open.length > 0 && (
          <span>
            {" · "}to fix:{" "}
            {open.map((i, k) => (
              <span class={STATUS_STYLE[c.results[i.id].status]}>{i.label}{k < open.length - 1 ? ", " : ""}</span>
            ))}
          </span>
        )}
        <span class="ml-1 text-primary group-open:hidden">show details</span>
      </summary>
      <ul class="mt-2 pl-3 border-l-2 border-gray-200 space-y-1">
        {items.map((i) => {
          const res = c.results[i.id];
          if (!res) return null;
          return (
            <li class="font-sans text-xs leading-relaxed">
              <span class={`inline-block w-4 ${STATUS_STYLE[res.status]}`}>{STATUS_MARK[res.status]}</span>
              <span class="text-dark">{i.label}</span>
              {res.detail && <span class="text-secondary">: {res.detail}</span>}
            </li>
          );
        })}
      </ul>
    </details>
  );
}

// ── Project ────────────────────────────────────────────────────────────────

function ReadinessMeter({ score }: { score: number }) {
  const tone = score <= 3 ? "bg-accent" : score <= 5 ? "bg-accent/60" : "bg-primary";
  return (
    <div class="flex items-center gap-2" aria-label={`Readiness ${score} out of 10`}>
      <div class="flex gap-0.5" aria-hidden="true">
        {Array.from({ length: 10 }, (_, i) => (
          <span class={`block w-2.5 h-2.5 rounded-sm ${i < score ? tone : "bg-gray-200"}`} />
        ))}
      </div>
      <span class="font-sans text-xs font-medium text-dark tabular-nums">{score}/10</span>
    </div>
  );
}

function EntryRow({ project, entry, num }: { project: WipProject; entry: WipEntry; num: number | null }) {
  const r = entry.readiness;
  return (
    <li class="py-5 border-b border-gray-200 last:border-b-0">
      <div class="flex gap-4">
        <span class="font-sans text-sm text-secondary w-6 shrink-0 text-right pt-0.5 tabular-nums">
          {num !== null ? `${num}.` : ""}
        </span>
        <div class="flex-1 min-w-0">
          <h3 class="font-serif text-xl text-dark leading-snug">{entry.title}</h3>
          <p class="font-sans text-sm text-secondary italic mb-1.5">{authorList(entry.authors)}</p>
          <p class="font-body text-sm text-dark leading-relaxed mb-3">{entry.summary}</p>
          <div class="flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-4">
            <ReadinessMeter score={r.score} />
            <p class="font-sans text-xs text-secondary leading-relaxed flex-1">
              {r.note}
              {r.stale && <span class="text-accent"> Draft updated since this assessment.</span>}
            </p>
          </div>
          <EntryChecks project={project} entry={entry} />
          {entry.talk && (
            <a href={`/resources/${entry.talk}`} class="inline-block mt-2 font-sans text-xs text-primary hover:underline">
              The talk →
            </a>
          )}
        </div>
      </div>
    </li>
  );
}

export function WipProjectPage({ currentPath, project }: { currentPath: string; project: WipProject }) {
  const latest = project.versions[0];
  const mean = meanReadiness(project);
  const ready = project.contents.filter((e) => e.readiness.score >= 8).length;
  const parts = project.parts.length ? project.parts : [{ id: "", title: "" }];
  let n = 0;

  return (
    <Base
      title={project.title}
      description={project.description}
      ogImage={project.cover}
      currentPath={currentPath}
      bodyScript={mobileMenuScript()}
      noindex
    >
      <div class="px-6 lg:px-8 pt-6">
        <div class="max-w-wide mx-auto">
          <nav class="text-sm font-sans text-secondary" aria-label="Breadcrumb">
            <a href="/wip" class="hover:text-primary transition-colors">Works in progress</a>
            <span class="mx-2 text-gray-300" aria-hidden="true">›</span>
            <span class="text-dark">{project.title}</span>
          </nav>
        </div>
      </div>

      <DeadlineBanner project={project} />

      <article class="px-6 lg:px-8 py-10">
        <div class="max-w-wide mx-auto flex flex-col lg:flex-row gap-10 lg:gap-16">
          {/* Left: cover, manuscript, versions */}
          <aside class="lg:w-64 shrink-0">
            <div class="aspect-[2/3] bg-primary-light rounded-lg overflow-hidden mb-4 max-w-[16rem]">
              {project.cover && (
                <img src={project.cover} alt={`Placeholder cover for ${project.title}`} class="w-full h-full object-cover" loading="eager" />
              )}
            </div>

            {latest?.file ? (
              <a href={latest.file} class="btn-primary w-full text-center block mb-2">
                Working draft v{latest.version} (PDF)
              </a>
            ) : (
              <p class="font-sans text-sm text-secondary mb-2">No manuscript compiled yet.</p>
            )}
            {latest && (
              <p class="font-sans text-xs text-secondary mb-6">
                Compiled {fmtDate(latest.date, "long")} · {latest.pages} pages. Unedited; not for citation or circulation.
              </p>
            )}

            {project.versions.length > 0 && (
              <section>
                <h2 class="font-sans text-xs uppercase tracking-wider text-secondary mb-2">Changelog</h2>
                <ol class="space-y-3">
                  {project.versions.map((v) => (
                    <li class="font-sans text-xs text-secondary leading-relaxed">
                      <span class="font-medium text-dark">v{v.version}</span> · {fmtDate(v.date)}
                      <span class="block">{v.message}</span>
                    </li>
                  ))}
                </ol>
              </section>
            )}
          </aside>

          {/* Right: header, status, contents */}
          <div class="flex-1 min-w-0">
            <div class="mb-3"><StagePill stage={project.stage} /></div>
            <h1 class="font-serif text-4xl md:text-5xl text-dark leading-tight mb-2">{project.title}</h1>
            {project.subtitle && <p class="font-serif text-xl md:text-2xl text-secondary italic mb-4">{project.subtitle}</p>}
            {project.editor && <p class="font-sans text-sm text-secondary mb-6">Edited by {project.editor}</p>}
            <p class="font-body text-base text-dark leading-relaxed mb-8 max-w-prose">{project.description}</p>

            {latest && (
              <section class="mb-8 p-4 border-l-4 border-primary bg-primary-light/50 rounded-r max-w-prose">
                <h2 class="font-sans text-xs uppercase tracking-wider text-primary mb-1">
                  What's new in v{latest.version} · {fmtDate(latest.date, "long")}
                </h2>
                <p class="font-body text-sm text-dark leading-relaxed">{latest.message}</p>
                {(latest.added.length > 0 || latest.updated.length > 0) && (
                  <p class="font-sans text-xs text-secondary mt-2">
                    {latest.added.length > 0 && `Added: ${latest.added.map((id) => titleOf(project, id)).join("; ")}. `}
                    {latest.updated.length > 0 && `Updated: ${latest.updated.map((id) => titleOf(project, id)).join("; ")}.`}
                  </p>
                )}
              </section>
            )}

            <dl class="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-2xl mb-10">
              <div>
                <dt class="font-sans text-xs text-secondary">Pieces</dt>
                <dd class="font-serif text-3xl text-dark">{project.contents.length}</dd>
              </div>
              <div>
                <dt class="font-sans text-xs text-secondary">Mean readiness</dt>
                <dd class="font-serif text-3xl text-dark">{mean.toFixed(1)}<span class="text-lg text-secondary">/10</span></dd>
              </div>
              <div>
                <dt class="font-sans text-xs text-secondary">Copy-edit ready (8+)</dt>
                <dd class="font-serif text-3xl text-dark">{ready}</dd>
              </div>
              {project.checks && (
                <div>
                  <dt class="font-sans text-xs text-secondary">Pass the checklist</dt>
                  <dd class="font-serif text-3xl text-dark">
                    {Object.values(project.checks.entries).filter((c) => c.summary.ready).length}
                    <span class="text-lg text-secondary">/{Object.keys(project.checks.entries).length}</span>
                  </dd>
                </div>
              )}
            </dl>

            <h2 class="font-serif text-2xl text-dark mb-1">Contents</h2>
            <p class="font-sans text-xs text-secondary mb-4">Provisional order.</p>
            {parts.map((part) => {
              const entries = project.contents.filter((e) => !part.id || e.part === part.id);
              if (!entries.length) return null;
              return (
                <section class="mb-4">
                  {part.title && (
                    <h3 class="font-sans text-xs uppercase tracking-wider text-primary mt-6 mb-1">{part.title}</h3>
                  )}
                  <ol>
                    {entries.map((e) => {
                      const num = e.part === "front" ? null : ++n;
                      return <EntryRow project={project} entry={e} num={num} />;
                    })}
                  </ol>
                </section>
              );
            })}

            <section class="mt-10 p-5 bg-primary-light/60 rounded-lg max-w-prose">
              <h2 class="font-sans text-sm font-medium text-dark mb-2">About the readiness scores</h2>
              <p class="font-sans text-xs text-secondary leading-relaxed mb-3">
                A rough, editor-side read of how far each draft is from finished, so the volume's progress is visible at a glance. It is not a judgment of the ideas.
              </p>
              <ul class="font-sans text-xs text-secondary space-y-1">
                {Object.entries(project.readiness_scale).map(([k, v]) => (
                  <li><span class="inline-block w-6 font-medium text-dark tabular-nums">{k}</span>{v}</li>
                ))}
              </ul>
            </section>
          </div>
        </div>
      </article>
    </Base>
  );
}

/** The checklist as a Markdown document, for the download and for pasting to authors. */
export function checklistMarkdown(project: WipProject): string {
  const items = project.checklist ?? [];
  const out: string[] = [`# Checklist for the next draft: ${project.title}`, ""];
  if (project.deadline) {
    out.push(`**${project.deadline.label}:** ${longDate(project.deadline.date)}`, "", project.deadline.detail, "");
  }
  out.push(
    "Every essay's next draft should meet all of these. Items marked *auto* are checked by script against the draft in the shared folder; the editor checks the rest by reading.",
    ""
  );
  for (const sec of [...new Set(items.map((i) => i.section))]) {
    out.push(`## ${sec}`, "");
    for (const i of items.filter((x) => x.section === sec)) {
      const tags = [i.auto ? "auto" : "", i.advisory ? "guideline" : ""].filter(Boolean);
      out.push(`- [ ] **${i.label}**${tags.length ? ` *(${tags.join(", ")})*` : ""}  `, `  ${i.detail}`);
      if (i.licenses) out.push(`  Accepted licenses: ${i.licenses.join(", ")}.`);
    }
    out.push("");
  }
  return out.join("\n");
}

export function WipChecklistPage({ project, currentPath }: { project: WipProject; currentPath: string }) {
  return (
    <Base
      title={`Checklist: ${project.title}`}
      description={`Checklist every essay's next draft must pass for ${project.title}.`}
      currentPath={currentPath}
      bodyScript={mobileMenuScript()}
      noindex
    >
      <div class="px-6 lg:px-8 pt-6">
        <div class="max-w-wide mx-auto">
          <nav class="text-sm font-sans text-secondary" aria-label="Breadcrumb">
            <a href="/wip" class="hover:text-primary transition-colors">Works in progress</a>
            <span class="mx-2 text-gray-300" aria-hidden="true">›</span>
            <a href={`/wip/${project.slug}`} class="hover:text-primary transition-colors">{project.title}</a>
            <span class="mx-2 text-gray-300" aria-hidden="true">›</span>
            <span class="text-dark">Checklist</span>
          </nav>
        </div>
      </div>
      <DeadlineBanner project={project} />
      <div class="px-6 lg:px-8 py-10">
        <div class="max-w-wide mx-auto">
          <p class="font-sans text-sm mb-6">
            <a href={`/wip/${project.slug}`} class="text-primary hover:underline">← Back to the project</a>
            <span class="mx-2 text-gray-300" aria-hidden="true">·</span>
            <a href={`/wip/${project.slug}/checklist.md`} download class="text-primary hover:underline">Download (.md)</a>
          </p>
          {project.checklist && <Checklist items={project.checklist} />}
        </div>
      </div>
    </Base>
  );
}
