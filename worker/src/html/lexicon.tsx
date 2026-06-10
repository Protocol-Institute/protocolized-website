import { Base } from "./base";
import lexiconData from "../../public/lexicon.json";

type LexiconMeta = {
  total: number;
  pi_coined: number;
  pi_specific: number;
  curated: number;
  letters: string[];
};

type Definition = {
  text: string;
  source?: string;
  source_slug?: string;
  type?: string;
};

type LexiconTerm = {
  id: string;
  term: string;
  letter: string;
  triage: string;
  triage_label: string;
  definitions: Definition[];
};

function badgeClass(triage: string): string {
  if (triage === "a") return "lex-badge lex-badge-a";
  if (triage === "b") return "lex-badge lex-badge-b";
  return "lex-badge lex-badge-cur";
}

const LEXICON_STYLES = `
  .lex-az-bar{display:flex;flex-wrap:wrap;gap:.15rem}
  .lex-az-link{display:inline-block;width:2rem;height:2rem;line-height:2rem;text-align:center;font-family:"Outfit",system-ui,sans-serif;font-size:.8rem;font-weight:600;border-radius:3px;color:#555;text-decoration:none;background:#f3f0ea;transition:background .12s,color .12s}
  .lex-az-link:hover{background:#0F6E56;color:#fff}
  .lex-az-link.inactive{color:#ccc;background:transparent;pointer-events:none}
  .lex-badge{display:inline-block;font-family:"Outfit",system-ui,sans-serif;font-size:.68rem;font-weight:600;letter-spacing:.04em;text-transform:uppercase;padding:.15em .55em;border-radius:3px;vertical-align:middle}
  .lex-badge-a{background:#e1f5ee;color:#0a5540}
  .lex-badge-b{background:#e8f0fb;color:#2a4d8a}
  .lex-badge-cur{background:#f3f0ea;color:#666}
  .lex-source-link{font-family:"Outfit",system-ui,sans-serif;font-size:.78rem;color:#0F6E56;text-decoration:none}
  .lex-source-link:hover{text-decoration:underline}
  .lex-source-plain{font-family:"Outfit",system-ui,sans-serif;font-size:.78rem;color:#888}
  .lex-def+.lex-def{margin-top:.75rem;padding-top:.75rem;border-top:1px solid #f0ece4}
  .lex-def-label{font-family:"Outfit",system-ui,sans-serif;font-size:.7rem;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:#bbb;margin-bottom:.2rem}
  @keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
  #spotlight-card{animation:fadein .35s ease}
  .lex-letter-section{scroll-margin-top:5rem}
`;

const LEXICON_SCRIPT = `
(function() {
  var terms = null;
  var BADGE = { a: 'lex-badge-a', b: 'lex-badge-b', curated: 'lex-badge-cur' };

  function pickSpotlight() {
    if (!terms) return;
    var t = terms[Math.floor(Math.random() * terms.length)];
    document.getElementById('spotlight-term').textContent = t.term;
    var badge = document.getElementById('spotlight-badge');
    badge.textContent = t.triage_label;
    badge.className = 'lex-badge ' + (BADGE[t.triage] || 'lex-badge-cur') + ' mb-3 inline-block';
    var def = t.definitions[0] || {};
    document.getElementById('spotlight-def').textContent = def.text || '';
    document.getElementById('spotlight-src').textContent = def.source || '';
    var card = document.getElementById('spotlight-card');
    card.style.animation = 'none';
    void card.offsetWidth;
    card.style.animation = 'fadein 0.25s ease';
  }

  fetch('/lexicon.json').then(function(r){return r.json();}).then(function(d){
    terms = d.terms;
    pickSpotlight();
  });

  document.getElementById('spotlight-refresh').addEventListener('click', pickSpotlight);

  function filterLexicon(q) {
    q = q.trim().toLowerCase();
    var cards = document.querySelectorAll('.lex-card');
    var sections = document.querySelectorAll('.lex-letter-section');
    var any = false;
    cards.forEach(function(card) {
      var termText = card.dataset.term || '';
      var defText = (card.querySelector('.lex-body-text') || {textContent:''}).textContent.toLowerCase();
      var match = !q || termText.includes(q) || defText.includes(q);
      card.style.display = match ? '' : 'none';
      if (match) any = true;
    });
    sections.forEach(function(s) {
      s.style.display = s.querySelectorAll('.lex-card:not([style*="display: none"])').length > 0 ? '' : 'none';
    });
    document.getElementById('lex-no-results').classList.toggle('hidden', any || !q);
  }

  var el = document.getElementById('lex-search');
  if (el) el.addEventListener('input', function(){ filterLexicon(this.value); });
})();
`;

export function LexiconPage({ currentPath }: { currentPath: string }) {
  const { meta, terms } = lexiconData as { meta: LexiconMeta; terms: LexiconTerm[] };
  const { letters } = meta;

  const byLetter: Record<string, LexiconTerm[]> = {};
  for (const t of terms) {
    if (!byLetter[t.letter]) byLetter[t.letter] = [];
    byLetter[t.letter].push(t);
  }

  const allLetters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
  const first = terms[0];

  const description =
    `${meta.total} terms coined or specifically used by the Protocol Institute — from protocolization and hardness to Kafka protocols, dynamic non-events, and protocol dysphoria. PI-coined vocabulary, PI-specific usages, and hand-curated definitions from across the corpus.`;

  return (
    <Base
      title="Protocol Lexicon"
      description={description}
      currentPath={currentPath}
      bodyScript={LEXICON_SCRIPT}
    >
      <style dangerouslySetInnerHTML={{ __html: LEXICON_STYLES }} />

      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-10 pb-20">

        {/* Header */}
        <div class="mb-8">
          <div class="flex flex-wrap items-baseline gap-3 mb-2">
            <h1 class="font-serif text-3xl text-dark">Protocol Lexicon</h1>
            <span class="font-sans text-sm text-secondary bg-surface px-2 py-0.5 rounded">{meta.total} terms</span>
          </div>
          <p class="font-body text-secondary text-base leading-relaxed max-w-2xl mb-3">
            Terms coined, adapted, or specifically defined within the Protocol Institute corpus.
            Sourced from across the PI research library; definitions reflect how they are used in that body of work.
            This is a living document — updated as the corpus grows.
          </p>
          <div class="flex flex-wrap gap-3 font-sans text-sm">
            <span class="lex-badge lex-badge-a">{meta.pi_coined} PI-coined</span>
            <span class="lex-badge lex-badge-b">{meta.pi_specific} PI-specific usage</span>
            {meta.curated > 0 && <span class="lex-badge lex-badge-cur">{meta.curated} curated</span>}
          </div>
        </div>

        {/* Spotlight */}
        <div id="spotlight-card" class="mb-10 p-5 rounded-lg border border-primary/20 bg-primary-light/30 relative overflow-hidden">
          <div class="flex items-center justify-between mb-3">
            <span class="font-sans text-xs font-semibold tracking-widest uppercase text-primary/70">Spotlight term</span>
            <button
              id="spotlight-refresh"
              class="font-sans text-xs text-primary/60 hover:text-primary transition-colors cursor-pointer bg-transparent border-none p-0"
              title="Another term"
            >↺ shuffle</button>
          </div>
          <div id="spotlight-content">
            <h2 id="spotlight-term" class="font-serif text-2xl text-dark mb-1">{first.term}</h2>
            <span id="spotlight-badge" class={badgeClass(first.triage) + " mb-3 inline-block"}>{first.triage_label}</span>
            <p id="spotlight-def" class="font-body text-dark text-base leading-relaxed mt-2">{first.definitions[0]?.text ?? ""}</p>
            <p id="spotlight-src" class="mt-2 font-sans text-xs text-secondary">{first.definitions[0]?.source ?? ""}</p>
          </div>
        </div>

        {/* Search + A–Z bar */}
        <div class="mb-6 flex flex-col sm:flex-row gap-3 items-start sm:items-center">
          <input
            id="lex-search"
            type="search"
            placeholder="Search terms…"
            class="font-sans text-sm border border-gray-200 rounded px-3 py-2 w-full sm:w-64 bg-white focus:outline-none focus:border-primary"
          />
          <div class="lex-az-bar">
            {allLetters.map((l) => (
              <a
                href={"#letter-" + l}
                class={"lex-az-link" + (letters.includes(l) ? "" : " inactive")}
              >{l}</a>
            ))}
          </div>
        </div>

        {/* Term grid by letter */}
        <div id="lex-grid">
          {letters.map((letter) => (
            <section id={"letter-" + letter} class="lex-letter-section mb-10">
              <h2 class="font-serif text-2xl text-dark border-b border-gray-200 pb-1 mb-4">{letter}</h2>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(byLetter[letter] ?? []).map((entry) => (
                  <div
                    class="lex-card bg-white border border-gray-100 rounded-lg p-4 shadow-sm hover:shadow-md hover:border-primary/20 transition-all"
                    data-term={entry.term.toLowerCase()}
                    data-id={entry.id}
                  >
                    <div class="flex items-start justify-between gap-2 mb-2">
                      <h3 class="font-serif text-lg text-dark leading-snug">{entry.term}</h3>
                      <span class={badgeClass(entry.triage) + " flex-shrink-0"}>{entry.triage_label}</span>
                    </div>
                    {entry.definitions.map((def) => (
                      <div class="lex-def">
                        {entry.definitions.length > 1 && (
                          <div class="lex-def-label">{def.type === "curated" ? "Definition" : "From corpus"}</div>
                        )}
                        <p class="font-body lex-body-text text-sm text-dark/80 leading-relaxed">{def.text}</p>
                        {def.source && (
                          <p class="mt-1.5">
                            {def.source_slug ? (
                              <a href={"/resources/" + def.source_slug} class="lex-source-link">↗ {def.source}</a>
                            ) : (
                              <span class="lex-source-plain">{def.source}</span>
                            )}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </section>
          ))}
          <p id="lex-no-results" class="hidden font-sans text-secondary text-sm py-8 text-center">No terms match your search.</p>
        </div>

      </div>
    </Base>
  );
}
