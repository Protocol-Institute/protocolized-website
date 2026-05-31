import { Base } from "./base";
import { TypeBadge, fmtDate, mobileMenuScript } from "./static-pages";
import type { Resource } from "../db";

const TYPE_LABELS: Record<string, string> = {
  paper: "Paper",
  "working-paper": "Working Paper",
  framework: "Framework",
  "workshop-template": "Workshop Template",
  game: "Game",
  dataset: "Dataset",
  interview: "Interview",
  presentation: "Presentation",
  code: "Code",
  image: "Image",
  "prompt-template": "Prompt Template",
  talk: "Talk",
  lecture: "Lecture",
  article: "Article",
  fiction: "Fiction",
};

const VIDEO_TYPES = new Set(["talk", "lecture", "presentation"]);

export function ResourcesPage({
  currentPath,
  resources,
}: {
  currentPath: string;
  resources: Resource[];
}) {
  const allTypes = [...new Set(resources.map((r) => r.type))].sort();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "Resources — Protocolized",
    description:
      "Browse the full library of protocol-related resources: papers, frameworks, games, datasets, code, and more.",
    url: "https://protocolized.io/resources",
    itemListElement: resources.map((r, i) => ({
      "@type": "ListItem",
      position: i + 1,
      url: `https://protocolized.io/resources/${r.slug}`,
      name: r.title,
    })),
  };

  const script = `
    ${mobileMenuScript()}

    (function() {
      var state = { query: '', types: new Set(), mediaTypes: new Set(), audiences: new Set(), sort: 'newest' };

      var params = new URLSearchParams(window.location.search);
      if (params.get('q')) state.query = params.get('q');
      if (params.get('type')) state.types.add(params.get('type'));
      if (params.get('audience')) state.audiences.add(params.get('audience'));

      var searchInput = document.getElementById('search-input');
      var sortSelect = document.getElementById('sort-select');
      var clearBtn = document.getElementById('clear-filters');
      var resourceCount = document.getElementById('resource-count');
      var grid = document.getElementById('resource-grid');
      var emptyState = document.getElementById('empty-state');
      var typePills = document.querySelectorAll('[data-filter="type"]');
      var mediaPills = document.querySelectorAll('[data-filter="media"]');
      var audienceCheckboxes = document.querySelectorAll('.audience-checkbox');

      if (searchInput && state.query) searchInput.value = state.query;
      typePills.forEach(function(pill) {
        if (state.types.has(pill.dataset.value)) {
          pill.classList.add('bg-primary', 'text-white', 'border-primary');
          pill.classList.remove('text-secondary', 'border-gray-200');
        }
      });
      audienceCheckboxes.forEach(function(cb) {
        if (state.audiences.has(cb.dataset.value)) cb.checked = true;
      });

      function updateURL() {
        var p = new URLSearchParams();
        if (state.query) p.set('q', state.query);
        if (state.types.size === 1) p.set('type', [...state.types][0]);
        if (state.audiences.size === 1) p.set('audience', [...state.audiences][0]);
        var newURL = window.location.pathname + (p.toString() ? '?' + p.toString() : '');
        window.history.replaceState({}, '', newURL);
      }

      function applyFilters() {
        var items = document.querySelectorAll('.resource-item');
        var visible = 0;

        var sortedItems = [...items].sort(function(a, b) {
          if (state.sort === 'newest') return new Date(b.dataset.date).getTime() - new Date(a.dataset.date).getTime();
          if (state.sort === 'alphabetical') return (a.dataset.title || '').localeCompare(b.dataset.title || '');
          if (state.sort === 'featured') return (a.dataset.featured === 'true' ? 0 : 1) - (b.dataset.featured === 'true' ? 0 : 1);
          return 0;
        });
        sortedItems.forEach(function(item) { grid.appendChild(item); });

        items.forEach(function(item) {
          var q = state.query.toLowerCase();
          var matchesQuery = !q
            || (item.dataset.title || '').includes(q)
            || (item.dataset.description || '').includes(q)
            || JSON.parse(item.dataset.tags || '[]').some(function(t) { return t.toLowerCase().includes(q); })
            || JSON.parse(item.dataset.authors || '[]').some(function(a) { return a.includes(q); });
          var matchesType = state.types.size === 0 || state.types.has(item.dataset.type);
          var matchesMedia = state.mediaTypes.size === 0 || state.mediaTypes.has(item.dataset.mediaType);
          var matchesAudience = state.audiences.size === 0
            || JSON.parse(item.dataset.audience || '[]').some(function(a) { return state.audiences.has(a); });
          var show = matchesQuery && matchesType && matchesMedia && matchesAudience;
          item.style.display = show ? '' : 'none';
          if (show) visible++;
        });

        if (resourceCount) resourceCount.textContent = String(visible);
        if (emptyState) emptyState.classList.toggle('hidden', visible > 0);
        if (grid) grid.classList.toggle('hidden', visible === 0);
        var hasFilters = state.query || state.types.size > 0 || state.mediaTypes.size > 0 || state.audiences.size > 0;
        if (clearBtn) clearBtn.classList.toggle('hidden', !hasFilters);
        updateURL();
      }

      if (searchInput) searchInput.addEventListener('input', function(e) {
        state.query = e.target.value;
        applyFilters();
      });

      typePills.forEach(function(pill) {
        pill.addEventListener('click', function() {
          var v = pill.dataset.value;
          if (state.types.has(v)) {
            state.types.delete(v);
            pill.classList.remove('bg-primary', 'text-white', 'border-primary');
            pill.classList.add('text-secondary', 'border-gray-200');
          } else {
            state.types.add(v);
            pill.classList.add('bg-primary', 'text-white', 'border-primary');
            pill.classList.remove('text-secondary', 'border-gray-200');
          }
          applyFilters();
        });
      });

      mediaPills.forEach(function(pill) {
        pill.addEventListener('click', function() {
          var v = pill.dataset.value;
          if (state.mediaTypes.has(v)) {
            state.mediaTypes.delete(v);
            pill.classList.remove('bg-primary', 'text-white', 'border-primary');
            pill.classList.add('text-secondary', 'border-gray-200');
          } else {
            state.mediaTypes.add(v);
            pill.classList.add('bg-primary', 'text-white', 'border-primary');
            pill.classList.remove('text-secondary', 'border-gray-200');
          }
          applyFilters();
        });
      });

      audienceCheckboxes.forEach(function(cb) {
        cb.addEventListener('change', function() {
          var v = cb.dataset.value;
          if (cb.checked) state.audiences.add(v); else state.audiences.delete(v);
          applyFilters();
        });
      });

      if (sortSelect) sortSelect.addEventListener('change', function() {
        state.sort = sortSelect.value;
        applyFilters();
      });

      if (clearBtn) clearBtn.addEventListener('click', function() {
        state.query = '';
        state.types.clear();
        state.mediaTypes.clear();
        state.audiences.clear();
        if (searchInput) searchInput.value = '';
        typePills.forEach(function(p) {
          p.classList.remove('bg-primary', 'text-white', 'border-primary');
          p.classList.add('text-secondary', 'border-gray-200');
        });
        mediaPills.forEach(function(p) {
          p.classList.remove('bg-primary', 'text-white', 'border-primary');
          p.classList.add('text-secondary', 'border-gray-200');
        });
        audienceCheckboxes.forEach(function(cb) { cb.checked = false; });
        applyFilters();
      });

      if (state.query || state.types.size > 0 || state.audiences.size > 0) applyFilters();
    })();
  `;

  return (
    <Base
      title="Resources"
      description="Browse the full library of protocol-related resources: papers, frameworks, games, datasets, code, and more."
      jsonLd={jsonLd}
      currentPath={currentPath}
      bodyScript={script}
    >
      <div class="py-12 px-6 lg:px-8">
        <div class="max-w-wide mx-auto">
          <div class="mb-8">
            <h1 class="font-serif text-4xl text-dark mb-2">Resources</h1>
            <p class="font-sans text-secondary">
              <span id="resource-count">{resources.length}</span> resources on
              protocols — papers, frameworks, games, datasets, and more.
            </p>
          </div>

          <div class="flex flex-col lg:flex-row gap-8">
            <aside class="lg:w-64 shrink-0" aria-label="Filter resources">
              <div class="mb-6 p-4 rounded-lg border border-primary/30 bg-[#E1F5EE]">
                <span class="inline-block text-[0.65rem] font-sans font-semibold uppercase tracking-wider bg-[#D85A30] text-white px-1.5 py-0.5 rounded">
                  Beta
                </span>
                <p class="mt-2 mb-3 text-sm font-sans text-dark leading-snug">
                  Chat with C-3PO, our archive expert bot.
                </p>
                <a
                  href="https://c3po.protocolized.io?ref=protocolized-resources"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="block w-full text-center text-sm font-sans font-medium bg-primary text-white py-2 rounded-lg hover:bg-primary/90 transition-colors"
                >
                  Open C-3PO ↗
                </a>
              </div>

              <div class="mb-6">
                <label
                  for="search-input"
                  class="block text-xs font-sans font-medium text-secondary uppercase tracking-wider mb-2"
                >
                  Search
                </label>
                <div class="relative">
                  <input
                    id="search-input"
                    type="search"
                    placeholder="Title, author, tag..."
                    class="w-full pl-9 pr-4 py-2.5 text-sm font-sans border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                    aria-label="Search resources"
                  />
                  <svg
                    class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>
              </div>

              <div class="mb-6">
                <p class="text-xs font-sans font-medium text-secondary uppercase tracking-wider mb-2">
                  Type
                </p>
                <div class="flex flex-wrap gap-2">
                  {allTypes.map((type) => (
                    <button
                      class="filter-pill font-sans text-xs px-3 py-1.5 rounded-full border border-gray-200 text-secondary hover:border-primary hover:text-primary transition-colors"
                      data-filter="type"
                      data-value={type}
                    >
                      {TYPE_LABELS[type] ?? type}
                    </button>
                  ))}
                </div>
              </div>

              <div class="mb-6">
                <p class="text-xs font-sans font-medium text-secondary uppercase tracking-wider mb-2">
                  Media
                </p>
                <div class="flex flex-wrap gap-2">
                  {(["video", "text"] as const).map((mt) => (
                    <button
                      class="filter-pill font-sans text-xs px-3 py-1.5 rounded-full border border-gray-200 text-secondary hover:border-primary hover:text-primary transition-colors"
                      data-filter="media"
                      data-value={mt}
                    >
                      {mt === "video" ? "Video" : "Text"}
                    </button>
                  ))}
                </div>
              </div>

              <div class="mb-6">
                <p class="text-xs font-sans font-medium text-secondary uppercase tracking-wider mb-2">
                  Audience
                </p>
                <div class="flex flex-col gap-2">
                  {(["researcher", "practitioner", "academic", "corporate"] as const).map((aud) => (
                    <label class="flex items-center gap-2 cursor-pointer group">
                      <input
                        type="checkbox"
                        class="audience-checkbox sr-only"
                        data-value={aud}
                      />
                      <span class="w-4 h-4 rounded border-2 border-gray-300 group-has-[:checked]:border-primary group-has-[:checked]:bg-primary flex items-center justify-center shrink-0 transition-colors">
                        <svg
                          class="w-2.5 h-2.5 text-white hidden group-has-[:checked]:block"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fill-rule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clip-rule="evenodd"
                          />
                        </svg>
                      </span>
                      <span class="text-sm font-sans text-secondary capitalize group-has-[:checked]:text-dark transition-colors">
                        {aud}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div class="mb-6">
                <label
                  for="sort-select"
                  class="block text-xs font-sans font-medium text-secondary uppercase tracking-wider mb-2"
                >
                  Sort
                </label>
                <select
                  id="sort-select"
                  class="w-full text-sm font-sans border border-gray-200 rounded-lg bg-white px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary text-dark"
                >
                  <option value="newest">Newest first</option>
                  <option value="alphabetical">Alphabetical</option>
                  <option value="featured">Featured first</option>
                </select>
              </div>

              <button
                id="clear-filters"
                class="text-sm font-sans text-secondary hover:text-dark transition-colors hidden"
              >
                Clear all filters
              </button>
            </aside>

            <div class="flex-1">
              <div
                id="resource-grid"
                class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5"
                role="region"
                aria-label="Resource results"
                aria-live="polite"
              >
                {resources.map((r) => (
                  <article
                    class="card p-5 flex flex-col gap-3 resource-item relative"
                    data-slug={r.slug}
                    data-type={r.type}
                    data-media-type={VIDEO_TYPES.has(r.type) ? "video" : "text"}
                    data-tags={JSON.stringify(r.tags)}
                    data-audience={JSON.stringify(r.audience)}
                    data-title={r.title.toLowerCase()}
                    data-description={r.description.toLowerCase()}
                    data-authors={JSON.stringify(r.authors.map((a) => a.name.toLowerCase()))}
                    data-date={r.date}
                    data-featured={String(r.featured)}
                  >
                    <div class="flex items-start justify-between gap-2">
                      <TypeBadge type={r.type} />
                      {r.featured && (
                        <span
                          class="badge font-sans text-[#D85A30]"
                          style="background-color:#FAECE7;"
                        >
                          Featured
                        </span>
                      )}
                    </div>
                    <div>
                      <h3 class="font-serif text-lg text-dark leading-snug mb-1">
                        <a
                          href={`/resources/${r.slug}`}
                          class="hover:text-primary transition-colors after:absolute after:inset-0"
                        >
                          {r.title}
                        </a>
                      </h3>
                      <p class="text-sm font-body text-secondary line-clamp-2 leading-relaxed">
                        {r.description}
                      </p>
                    </div>
                    <div class="mt-auto flex items-center justify-between gap-2">
                      <div class="flex flex-wrap gap-1">
                        {r.tags.slice(0, 3).map((tag) => (
                          <span class="text-xs font-sans text-secondary bg-gray-100 px-2 py-0.5 rounded-full">
                            {tag}
                          </span>
                        ))}
                      </div>
                      <time
                        datetime={r.date}
                        class="text-xs font-sans text-secondary whitespace-nowrap shrink-0"
                      >
                        {fmtDate(r.date, "short")}
                      </time>
                    </div>
                    {r.authors.length > 0 && (
                      <p class="text-xs font-sans text-secondary">
                        {r.authors.map((a) => a.name).join(", ")}
                      </p>
                    )}
                  </article>
                ))}
              </div>

              <div
                id="empty-state"
                class="hidden text-center py-16 text-secondary font-sans"
                role="status"
              >
                <p class="text-lg mb-2">No resources match your filters.</p>
                <p class="text-sm">Try adjusting your search or filter criteria.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Base>
  );
}
