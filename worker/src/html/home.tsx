import { Base } from "./base";
import { fmtDate, mobileMenuScript } from "./static-pages";
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
  author?: string;
  section?: string;
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
    author: p.primary_author,
    section: p.section,
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
    image: b.banner ?? b.cover_image,
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
  latestPosts,
  archiveResources,
  carouselBooks,
  ytVideos,
}: {
  currentPath: string;
  latestPosts: Post[];
  archiveResources: Resource[];
  carouselBooks: Book[];
  ytVideos: YouTubeVideo[];
}) {
  const carouselItems = buildCarouselItems(latestPosts, ytVideos, archiveResources, carouselBooks);

  const jsonLd = [
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      name: "Protocolized",
      url: "https://protocolized.io",
      description:
        "A sci-fi and thinkpiece magazine and research library on protocols, published by the Protocol Institute.",
      potentialAction: {
        "@type": "SearchAction",
        target: {
          "@type": "EntryPoint",
          urlTemplate: "https://protocolized.io/resources?q={search_term_string}",
        },
        "query-input": "required name=search_term_string",
      },
    },
    {
      "@context": "https://schema.org",
      "@type": "Organization",
      name: "Protocol Institute",
      url: "https://protocol-institute.org",
      sameAs: [
        "https://discord.gg/Z3fgsW8D4s",
        "https://www.youtube.com/@protocol-institute",
        "https://protocolized.summerofprotocols.com",
      ],
    },
  ];

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
                            {item.source === "magazine" && item.image && (item.author || item.section) && (
                              <>
                                <div class="absolute inset-x-0 bottom-0 h-2/5 bg-gradient-to-t from-black/65 to-transparent pointer-events-none" />
                                <div class="absolute bottom-3 left-3 right-3 flex items-end justify-between pointer-events-none">
                                  {item.author && (
                                    <span class="text-white/90 text-xs font-sans truncate">{item.author}</span>
                                  )}
                                  {item.section && item.section !== "Protocolized" && (
                                    <span class="text-white/70 text-xs font-sans shrink-0 ml-2">{item.section}</span>
                                  )}
                                </div>
                              </>
                            )}
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
          <h2 class="font-serif text-2xl text-dark mb-8">Quick Start Pages</h2>
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

    </Base>
  );
}
