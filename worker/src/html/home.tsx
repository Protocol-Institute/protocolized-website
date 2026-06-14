import { Base } from "./base";
import { TypeBadge, fmtDate, mobileMenuScript } from "./static-pages";
import type { Resource, Post, Book } from "../db";
import type { YouTubeVideo } from "../youtube";

type CarouselSource = "magazine" | "youtube" | "archive" | "book";

interface CarouselItem {
  title: string;
  url: string;
  image?: string;
  caption: string;
  description?: string;
  date?: string;
  external?: boolean;
  source: CarouselSource;
}

const SOURCE_BADGE: Record<CarouselSource, string> = {
  magazine: "bg-primary-light text-primary",
  youtube:  "bg-red-50 text-red-600",
  archive:  "bg-[#FAECE7] text-[#D85A30]",
  book:     "bg-gray-100 text-dark",
};

function buildCarouselItems(
  posts: Post[],
  ytVideos: YouTubeVideo[],
  archiveResources: Resource[],
  books: Book[],
): CarouselItem[] {
  const magazine: CarouselItem[] = posts.map((p) => ({
    title: p.title,
    url: `/p/${p.slug}`,
    image: p.cover_image,
    caption: "Latest from magazine",
    description: p.subtitle ?? p.summary,
    date: p.date,
    source: "magazine" as const,
  }));

  const youtube: CarouselItem[] = ytVideos.map((v) => ({
    title: v.title,
    url: v.url,
    image: v.thumbnail,
    caption: "Latest from YouTube channel",
    description: v.description,
    date: v.published,
    external: true,
    source: "youtube" as const,
  }));

  const archive: CarouselItem[] = archiveResources.map((r) => ({
    title: r.title,
    url: `/resources/${r.slug}`,
    image: r.thumbnail,
    caption: "Resource Archive spotlight",
    description: r.description,
    date: r.date,
    source: "archive" as const,
  }));

  const bookItems: CarouselItem[] = books.map((b) => ({
    title: b.title,
    url: `/books/${b.slug}`,
    image: b.cover_image,
    caption: "Book spotlight",
    description: b.description,
    date: b.date,
    source: "book" as const,
  }));

  // Round-robin interleave: M, Y, A, B, M, Y, A, ...
  const sources = [magazine, youtube, archive, bookItems];
  const items: CarouselItem[] = [];
  const maxLen = Math.max(...sources.map((s) => s.length));
  for (let i = 0; i < maxLen; i++) {
    for (const src of sources) {
      if (i < src.length) items.push(src[i]);
    }
  }
  return items;
}

const AUDIENCE_CARDS = [
  {
    audience: "Researchers",
    description: "Papers, datasets, frameworks, and citations for academic inquiry.",
    filter: "researcher",
    icon: "🔬",
  },
  {
    audience: "Practitioners",
    description: "Templates, games, workshop tools, and how-to guides.",
    filter: "practitioner",
    icon: "⚙️",
  },
  {
    audience: "Academics",
    description: "Publications, working papers, and collaborator resources.",
    filter: "academic",
    icon: "📚",
  },
  {
    audience: "Corporate Partners",
    description: "Frameworks, case studies, and strategic coordination tools.",
    filter: "corporate",
    icon: "🏢",
  },
];

export function HomePage({
  currentPath,
  featuredResources,
  latestPosts,
  archiveResources,
  carouselBooks,
  ytVideos,
}: {
  currentPath: string;
  featuredResources: Resource[];
  latestPosts: Post[];
  archiveResources: Resource[];
  carouselBooks: Book[];
  ytVideos: YouTubeVideo[];
}) {
  const carouselItems = buildCarouselItems(latestPosts, ytVideos, archiveResources, carouselBooks);
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "Protocolized",
    description:
      "A sci-fi and thinkpiece magazine and research library on protocols, published by the Protocol Institute.",
    url: "https://protocolized.io",
    sameAs: [
      "https://discord.gg/Z3fgsW8D4s",
      "https://www.youtube.com/@protocol-institute",
      "https://protocolized.summerofprotocols.com",
    ],
  };

  const carouselScript = carouselItems.length > 0 ? `
    (function() {
      var track = document.getElementById('carousel-track');
      var dots = document.querySelectorAll('.carousel-dot');
      var prevBtn = document.getElementById('carousel-prev');
      var nextBtn = document.getElementById('carousel-next');
      var carousel = document.getElementById('article-carousel');
      if (!track || dots.length === 0) return;
      var current = 0;
      var total = dots.length;
      var INTERVAL = 5000;
      var timer = null;
      var paused = false;

      function goTo(index) {
        current = ((index % total) + total) % total;
        track.style.transform = 'translateX(-' + (current * 100) + '%)';
        dots.forEach(function(dot, i) {
          dot.classList.toggle('bg-primary', i === current);
          dot.classList.toggle('bg-gray-300', i !== current);
        });
      }

      function startTimer() {
        if (timer) clearInterval(timer);
        timer = setInterval(function() { goTo(current + 1); }, INTERVAL);
      }

      function stopTimer() {
        if (timer) { clearInterval(timer); timer = null; }
      }

      if (prevBtn) prevBtn.addEventListener('click', function() { goTo(current - 1); if (!paused) startTimer(); });
      if (nextBtn) nextBtn.addEventListener('click', function() { goTo(current + 1); if (!paused) startTimer(); });
      dots.forEach(function(dot) {
        dot.addEventListener('click', function() {
          goTo(Number(dot.dataset.index));
          if (!paused) startTimer();
        });
      });
      if (carousel) {
        carousel.addEventListener('mouseenter', function() { paused = true; stopTimer(); });
        carousel.addEventListener('mouseleave', function() { paused = false; startTimer(); });
      }
      startTimer();
    })();
  ` : "";

  const script = mobileMenuScript() + carouselScript;

  return (
    <Base
      title="Protocolized"
      description="Accelerating Order. A sci-fi and thinkpiece magazine and research library on protocols, published by the Protocol Institute."
      jsonLd={jsonLd}
      currentPath={currentPath}
      bodyScript={script}
    >
      <section class="py-20 md:py-28 px-6 lg:px-8">
        <div class="max-w-wide mx-auto">
          <div class="flex flex-col lg:flex-row lg:items-center gap-12 lg:gap-16 min-w-0">
            <div class="lg:w-5/12 shrink-0 min-w-0">
              <h1 class="font-serif text-5xl md:text-6xl lg:text-7xl text-dark mb-6 leading-none tracking-tight">
                Protocolized
              </h1>
              <p class="font-body text-lg text-secondary leading-relaxed max-w-lg">
                Protocolized is the media hub for the{" "}
                <a href="https://protocol-institute.org" target="_blank" rel="noopener noreferrer" class="text-primary hover:text-[#085041] transition-colors">Protocol Institute</a>.
                {" "}Explore our{" "}
                <a href="/resources" class="text-primary hover:text-[#085041] transition-colors">research archive</a>,
                {" "}our{" "}
                <a href="/magazine" class="text-primary hover:text-[#085041] transition-colors">magazine</a>
                {" "}(also available on{" "}
                <a href="https://protocolized.summerofprotocols.com" target="_blank" rel="noopener noreferrer" class="text-primary hover:text-[#085041] transition-colors">Substack</a>),{" "}
                <a href="https://www.youtube.com/@protocol-institute" target="_blank" rel="noopener noreferrer" class="text-primary hover:text-[#085041] transition-colors">YouTube channel</a>
                {" "}and{" "}
                <a href="/books" class="text-primary hover:text-[#085041] transition-colors">book collection</a>.
              </p>
            </div>

            {carouselItems.length > 0 && (
              <div class="flex-1 min-w-0">
                <div class="relative overflow-hidden rounded-xl" id="article-carousel">
                  <div
                    class="flex transition-transform duration-500 ease-in-out"
                    id="carousel-track"
                  >
                    {carouselItems.map((item, i) => (
                      <article class="w-full shrink-0" data-slide={i}>
                        <a
                          href={item.url}
                          class="block group"
                          {...(item.external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
                        >
                          <div class="aspect-[2/1] bg-gray-100 rounded-xl overflow-hidden mb-4 relative">
                            {item.image ? (
                              <img
                                src={item.image}
                                alt={item.title}
                                class="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-300"
                                loading={i === 0 ? "eager" : "lazy"}
                              />
                            ) : (
                              <div class="w-full h-full flex items-center justify-center bg-primary-light">
                                <span class="font-serif text-2xl text-primary/40">Protocolized</span>
                              </div>
                            )}
                            <span class={`absolute top-3 left-3 text-xs font-sans font-medium px-2 py-1 rounded-full ${SOURCE_BADGE[item.source]}`}>
                              {item.caption}
                            </span>
                          </div>
                          <div class="flex items-start gap-3">
                            <div class="flex-1 min-w-0">
                              <h3 class="font-serif text-lg md:text-xl text-dark leading-snug mb-1 group-hover:text-primary transition-colors">
                                {item.title}
                              </h3>
                              {item.description && (
                                <p class="text-sm font-body text-secondary leading-relaxed line-clamp-2">
                                  {item.description}
                                </p>
                              )}
                            </div>
                            {item.date && (
                              <time
                                datetime={item.date}
                                class="text-xs font-sans text-secondary whitespace-nowrap shrink-0 pt-1"
                              >
                                {fmtDate(item.date, "short")}
                              </time>
                            )}
                          </div>
                        </a>
                      </article>
                    ))}
                  </div>

                  <button
                    id="carousel-prev"
                    class="absolute left-2 top-[25%] -translate-y-1/2 w-8 h-8 rounded-full bg-white/90 border border-gray-200 flex items-center justify-center text-secondary hover:text-primary hover:border-primary transition-colors shadow-sm"
                    aria-label="Previous slide"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  <button
                    id="carousel-next"
                    class="absolute right-2 top-[25%] -translate-y-1/2 w-8 h-8 rounded-full bg-white/90 border border-gray-200 flex items-center justify-center text-secondary hover:text-primary hover:border-primary transition-colors shadow-sm"
                    aria-label="Next slide"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
                <div class="flex justify-center gap-2 mt-4">
                  {carouselItems.map((_, i) => (
                    <button
                      class={`carousel-dot w-2 h-2 rounded-full transition-colors ${i === 0 ? "bg-primary" : "bg-gray-300"}`}
                      data-index={i}
                      aria-label={`Go to slide ${i + 1}`}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      <section class="py-16 px-6 lg:px-8 bg-white border-y border-gray-100">
        <div class="max-w-wide mx-auto">
          <h2 class="font-serif text-2xl text-dark mb-2">Where do you want to start?</h2>
          <p class="font-sans text-secondary mb-8">Find resources matched to your work.</p>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {AUDIENCE_CARDS.map((card) => (
              <a
                href={`/resources?audience=${card.filter}`}
                class="card p-6 flex flex-col gap-3 hover:border-primary transition-colors group"
              >
                <span class="text-2xl" aria-hidden="true">{card.icon}</span>
                <div>
                  <p class="font-serif text-lg text-dark mb-1 group-hover:text-primary transition-colors">
                    {card.audience}
                  </p>
                  <p class="text-sm font-sans text-secondary leading-relaxed">
                    {card.description}
                  </p>
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>

      {featuredResources.length > 0 && (
        <section class="py-16 px-6 lg:px-8">
          <div class="max-w-wide mx-auto">
            <div class="flex items-center justify-between mb-8">
              <div>
                <h2 class="font-serif text-2xl text-dark mb-1">Featured resources</h2>
                <p class="font-sans text-secondary text-sm">Curated highlights from the library.</p>
              </div>
              <a
                href="/resources"
                class="text-sm font-sans text-primary hover:text-[#085041] transition-colors shrink-0"
              >
                View all →
              </a>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {featuredResources.map((r) => (
                <article class="card p-5 flex flex-col gap-3 relative">
                  <div class="flex items-start justify-between gap-2">
                    <TypeBadge type={r.type} />
                    <span class="badge font-sans text-[#D85A30]" style="background-color:#FAECE7;">
                      Featured
                    </span>
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
                    <time datetime={r.date} class="text-xs font-sans text-secondary whitespace-nowrap shrink-0">
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
          </div>
        </section>
      )}

      <section class="py-16 px-6 lg:px-8 bg-white border-t border-gray-100">
        <div class="max-w-wide mx-auto">
          <div class="bg-primary-light rounded-xl p-8 md:p-12 flex flex-col md:flex-row items-center justify-between gap-8">
            <div>
              <h2 class="font-serif text-2xl text-dark mb-2">Protocolized Magazine</h2>
              <p class="font-sans text-secondary leading-relaxed max-w-md">
                Subscribe for new resources, essays on protocol theory, and updates from the community.
              </p>
            </div>
            <div class="flex flex-wrap gap-4 shrink-0">
              <a
                href="https://protocolized.summerofprotocols.com"
                target="_blank"
                rel="noopener noreferrer"
                class="btn-primary"
              >
                Read on Substack →
              </a>
              <a href="/magazine" class="btn-secondary">
                Learn more
              </a>
            </div>
          </div>
        </div>
      </section>

      <section class="py-10 px-6 lg:px-8">
        <div class="max-w-wide mx-auto">
          <div class="flex flex-wrap items-center justify-center gap-8 text-sm font-sans text-secondary">
            <a
              href="https://discord.gg/Z3fgsW8D4s"
              target="_blank"
              rel="noopener noreferrer"
              class="flex items-center gap-2 hover:text-primary transition-colors"
              aria-label="Join our Discord"
            >
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z" />
              </svg>
              Discord
            </a>
            <a
              href="https://www.youtube.com/@protocol-institute"
              target="_blank"
              rel="noopener noreferrer"
              class="flex items-center gap-2 hover:text-primary transition-colors"
              aria-label="Watch on YouTube"
            >
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
              </svg>
              YouTube
            </a>
            <a
              href="https://protocolized.summerofprotocols.com"
              target="_blank"
              rel="noopener noreferrer"
              class="flex items-center gap-2 hover:text-primary transition-colors"
              aria-label="Read on Substack"
            >
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M22.539 8.242H1.46V5.406h21.08v2.836zM1.46 10.812V24L12 18.11 22.54 24V10.812H1.46zM22.54 0H1.46v2.836h21.08V0z" />
              </svg>
              Substack
            </a>
          </div>
        </div>
      </section>
    </Base>
  );
}
