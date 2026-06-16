import { Base } from "./base";

export function AboutPage({ currentPath }: { currentPath: string }) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "AboutPage",
    name: "About — Protocolized",
    description:
      "Protocolized.io is the media hub for the Protocol Institute, which grew out of the Summer of Protocols program.",
    url: "https://protocolized.io/about",
  };

  return (
    <Base
      title="About"
      description="Protocolized.io is the media hub for the Protocol Institute, which grew out of the Summer of Protocols program."
      jsonLd={jsonLd}
      currentPath={currentPath}
      bodyScript={mobileMenuScript()}
    >
      <div class="py-16 px-6 lg:px-8">
        <div class="max-w-prose mx-auto">
          <h1 class="font-serif text-5xl text-dark mb-8">About</h1>
          <p class="font-body text-lg text-secondary leading-relaxed">
            Protocolized.io is the media hub for the{" "}
            <a
              href="https://protocol-institute.org"
              target="_blank"
              rel="noopener noreferrer"
              class="text-primary hover:text-[#085041] transition-colors"
            >
              Protocol Institute
            </a>
            , which grew out of the Summer of Protocols program (2023–25). For
            more information please see the{" "}
            <a
              href="https://protocol-institute.org/about"
              target="_blank"
              rel="noopener noreferrer"
              class="text-primary hover:text-[#085041] transition-colors"
            >
              Protocol Institute About page
            </a>
            .
          </p>
        </div>
      </div>
    </Base>
  );
}

export function CommunityPage({ currentPath }: { currentPath: string }) {
  const script = mobileMenuScript();
  return (
    <Base
      title="Discord"
      description="Join the Protocol Institute community on Discord."
      currentPath={currentPath}
      bodyScript={script}
    >
      <div class="py-16 px-6 lg:px-8">
        <div class="max-w-prose mx-auto">
          <h1 class="font-serif text-5xl text-dark mb-4">Discord</h1>
          <p class="font-body text-xl text-secondary mb-12 leading-relaxed">
            The work on protocols happens in public, in conversation. Join us.
          </p>

          <section class="card p-8 mb-6" aria-labelledby="discord-heading">
            <div class="flex items-start gap-5">
              <div class="shrink-0 w-12 h-12 bg-[#5865F2]/10 rounded-xl flex items-center justify-center">
                <svg class="w-6 h-6 text-[#5865F2]" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z" />
                </svg>
              </div>
              <div class="flex-1">
                <h2 id="discord-heading" class="font-serif text-2xl text-dark mb-2">Discord</h2>
                <p class="font-body text-secondary leading-relaxed mb-5">
                  The Discord server is where the community happens: discussing resources,
                  sharing new finds, coordinating research, and talking about protocol theory
                  in practice.
                </p>
                <a href="https://discord.gg/Z3fgsW8D4s" target="_blank" rel="noopener noreferrer" class="btn-primary">
                  Join the Discord →
                </a>
              </div>
            </div>
          </section>
        </div>
      </div>
    </Base>
  );
}

export function MagazinePage({
  currentPath,
  posts,
}: {
  currentPath: string;
  posts: import("../db").Post[];
}) {
  const script = mobileMenuScript();
  return (
    <Base
      title="Magazine"
      description="Essays, fiction, and protocol thinking from Protocolized."
      currentPath={currentPath}
      bodyScript={script}
    >
      <div class="py-16 px-6 lg:px-8">
        <div class="max-w-wide mx-auto">
          <div class="max-w-2xl mb-10">
            <h1 class="font-serif text-5xl text-dark mb-4">Magazine</h1>
            <p class="font-body text-xl text-secondary leading-relaxed">
              Essays, fiction, and protocol thinking — published on Substack.
            </p>
          </div>

          {/* Subscribe strip */}
          <div class="mb-12 p-6 rounded-xl bg-primary-light border border-primary/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <p class="font-sans font-medium text-dark mb-1">Subscribe to Protocolized</p>
              <p class="font-sans text-sm text-secondary">New posts to your inbox.</p>
            </div>
            <a
              href="https://protocolized.summerofprotocols.com/#/portal/signup"
              target="_blank"
              rel="noopener noreferrer"
              class="btn-primary shrink-0"
            >
              Subscribe ↗
            </a>
          </div>

          {/* Post list */}
          {posts.length > 0 ? (
            <div class="divide-y divide-gray-100">
              {posts.map((post) => (
                <PostCard post={post} />
              ))}
            </div>
          ) : (
            <div class="text-center py-16">
              <p class="font-sans text-secondary mb-4">
                Posts are being mirrored — check back soon, or read on Substack.
              </p>
              <a
                href="https://protocolized.summerofprotocols.com/archive"
                target="_blank"
                rel="noopener noreferrer"
                class="btn-primary"
              >
                Read on Substack →
              </a>
            </div>
          )}
        </div>
      </div>
    </Base>
  );
}

function PostCard({ post }: { post: import("../db").Post }) {
  return (
    <article class="py-8 flex gap-6 group">
      {post.cover_image && (
        <a href={`/p/${post.slug}`} class="shrink-0 hidden sm:block" tabindex={-1} aria-hidden="true">
          <img
            src={post.cover_image}
            alt=""
            class="w-24 h-24 object-cover rounded-lg"
            loading="lazy"
          />
        </a>
      )}
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-3 mb-2">
          <span class="text-xs font-sans font-medium text-primary bg-primary-light px-2 py-0.5 rounded-full">
            {post.section}
          </span>
          <time datetime={post.date} class="text-xs font-sans text-secondary">
            {fmtDate(post.date, "short")}
          </time>
        </div>
        <h2 class="font-serif text-xl text-dark leading-snug mb-2">
          <a
            href={`/p/${post.slug}`}
            class="hover:text-primary transition-colors"
          >
            {post.title}
          </a>
        </h2>
        {post.subtitle && (
          <p class="font-body text-sm text-secondary leading-relaxed line-clamp-2 mb-3">
            {post.subtitle}
          </p>
        )}
        <span class="text-xs font-sans text-secondary">{post.primary_author}</span>
      </div>
    </article>
  );
}

export function AnthologiesPage({
  currentPath,
  anthologies,
}: {
  currentPath: string;
  anthologies: import("../db").Resource[];
}) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "Anthologies — Protocolized",
    description:
      "Fiction anthologies from the Protocolized universe — speculative stories exploring protocols, coordination, and the systems that shape our world.",
    url: "https://protocolized.io/anthologies",
  };
  const script = mobileMenuScript();

  return (
    <Base
      title="Anthologies"
      description="Fiction anthologies from the Protocolized universe — speculative stories exploring protocols, coordination, and the systems that shape our world."
      jsonLd={jsonLd}
      currentPath={currentPath}
      bodyScript={script}
    >
      <div class="py-16 px-6 lg:px-8">
        <div class="max-w-wide mx-auto">
          <div class="mb-10">
            <h1 class="font-serif text-5xl text-dark mb-4">Anthologies</h1>
            <p class="font-body text-lg text-secondary leading-relaxed max-w-2xl">
              Speculative fiction anthologies exploring protocols, coordination, and the systems
              that shape our world. Each collection imagines futures where the invisible rules
              governing society become visible — and changeable.
            </p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {anthologies.map((a) => (
              <article class="card p-6 flex flex-col gap-4 relative">
                <div class="flex items-start justify-between gap-2">
                  <TypeBadge type={a.type} />
                  <span
                    class="badge font-sans text-xs"
                    style="background-color:#F0E8F5;color:#4A1E5C;"
                  >
                    Anthology
                  </span>
                </div>
                <div>
                  <h2 class="font-serif text-2xl text-dark leading-snug mb-2">
                    <a
                      href={`/resources/${a.slug}`}
                      class="hover:text-primary transition-colors after:absolute after:inset-0"
                    >
                      {a.title}
                    </a>
                  </h2>
                  <p class="text-sm font-body text-secondary leading-relaxed line-clamp-3">
                    {a.description}
                  </p>
                </div>
                <div class="mt-auto flex items-center justify-between gap-2">
                  <p class="text-xs font-sans text-secondary">
                    {a.authors.map((auth) => auth.name).join(", ")}
                  </p>
                  <time
                    datetime={a.date}
                    class="text-xs font-sans text-secondary whitespace-nowrap"
                  >
                    {fmtDate(a.date, "short")}
                  </time>
                </div>
              </article>
            ))}
          </div>

          {anthologies.length === 0 && (
            <p class="font-sans text-secondary py-16 text-center">
              No anthologies found.
            </p>
          )}
        </div>
      </div>
    </Base>
  );
}

export function TypeBadge({ type }: { type: string }) {
  const badges: Record<string, { bg: string; text: string; label: string }> = {
    paper: { bg: "#EEEDFE", text: "#3C3489", label: "Paper" },
    "working-paper": { bg: "#EEEDFE", text: "#3C3489", label: "Working Paper" },
    framework: { bg: "#E1F5EE", text: "#085041", label: "Framework" },
    "workshop-template": { bg: "#FAECE7", text: "#712B13", label: "Workshop Template" },
    game: { bg: "#FBEAF0", text: "#72243E", label: "Game" },
    dataset: { bg: "#E6F1FB", text: "#0C447C", label: "Dataset" },
    interview: { bg: "#FAEEDA", text: "#633806", label: "Interview" },
    presentation: { bg: "#FAEEDA", text: "#633806", label: "Presentation" },
    code: { bg: "#EAF3DE", text: "#27500A", label: "Code" },
    "prompt-template": { bg: "#EAF3DE", text: "#27500A", label: "Prompt Template" },
    image: { bg: "#F1EFE8", text: "#444441", label: "Image" },
    talk: { bg: "#E8F0FB", text: "#1A3A6B", label: "Talk" },
    lecture: { bg: "#E8F0FB", text: "#1A3A6B", label: "Lecture" },
    article: { bg: "#F5F0E8", text: "#5C4A1E", label: "Article" },
    fiction: { bg: "#F0E8F5", text: "#4A1E5C", label: "Fiction" },
    "living-document": { bg: "#E8F5F0", text: "#1A5C42", label: "Living Document" },
  };
  const cfg = badges[type] ?? { bg: "#F1EFE8", text: "#444441", label: type };
  return (
    <span
      class="badge font-sans"
      style={`background-color: ${cfg.bg}; color: ${cfg.text};`}
    >
      {cfg.label}
    </span>
  );
}

const SUBSTACK_POST_RE = /protocolized\.summerofprotocols\.com\/p\/([a-z0-9-]+)/;

export function substackToInternalUrl(url: string | undefined): string | null {
  if (!url) return null;
  const m = url.match(SUBSTACK_POST_RE);
  return m ? `/p/${m[1]}` : null;
}

export function fmtDate(
  dateStr: string,
  style: "short" | "long" | "year" = "short"
): string {
  const d = new Date(dateStr + "T00:00:00Z");
  if (style === "long") {
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      timeZone: "UTC",
    });
  }
  if (style === "year") {
    return d.toLocaleDateString("en-US", { year: "numeric", timeZone: "UTC" });
  }
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    timeZone: "UTC",
  });
}

export function mobileMenuScript(): string {
  return `
    (function() {
      var btn = document.getElementById('mobile-menu-btn');
      var menu = document.getElementById('mobile-menu');
      var menuIcon = document.getElementById('menu-icon');
      var closeIcon = document.getElementById('close-icon');
      if (!btn) return;
      btn.addEventListener('click', function() {
        var isOpen = !menu.classList.contains('hidden');
        menu.classList.toggle('hidden');
        menuIcon.classList.toggle('hidden');
        closeIcon.classList.toggle('hidden');
        btn.setAttribute('aria-expanded', String(!isOpen));
      });
    })();
  `;
}
