import type { Child } from "hono/jsx";

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/resources", label: "Resources" },
  { href: "/about", label: "About" },
  { href: "/community", label: "Community" },
  { href: "/magazine", label: "Magazine" },
];

function isActive(href: string, currentPath: string): boolean {
  if (href === "/") return currentPath === "/";
  return currentPath.startsWith(href);
}

interface BaseProps {
  title: string;
  description?: string;
  canonicalURL?: string;
  jsonLd?: object;
  ogImage?: string;
  currentPath: string;
  children?: Child;
  headScript?: string;
  bodyScript?: string;
}

export function Base({
  title,
  description = "Protocolized is a sci-fi and thinkpiece magazine and research library on protocols, published by the Protocol Institute.",
  canonicalURL,
  jsonLd,
  ogImage,
  currentPath,
  children,
  bodyScript,
}: BaseProps) {
  const siteTitle =
    title === "Protocolized" ? title : `${title} — Protocolized`;
  const canonical = canonicalURL ?? `https://protocolized.io${currentPath}`;

  return (
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content={description} />
        <link rel="canonical" href={canonical} />

        <meta property="og:type" content="website" />
        <meta property="og:title" content={siteTitle} />
        <meta property="og:description" content={description} />
        <meta property="og:url" content={canonical} />
        {ogImage && <meta property="og:image" content={ogImage} />}

        <meta name="twitter:card" content="summary" />
        <meta name="twitter:title" content={siteTitle} />
        <meta name="twitter:description" content={description} />

        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossorigin=""
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Instrument+Serif&family=Lora:ital,wght@0,400;0,500;1,400&family=Outfit:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap"
          rel="stylesheet"
        />

        <link rel="icon" type="image/png" href="/protocolized_mark.png" />
        <link rel="alternate" type="application/rss+xml" title="Protocolized Resources" href="/rss.xml" />

        {jsonLd && (
          <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
          />
        )}

        <link rel="stylesheet" href="/style.css" />
        <title>{siteTitle}</title>
      </head>
      <body>
        <a
          href="#main-content"
          class="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 btn-primary"
        >
          Skip to content
        </a>

        <Nav currentPath={currentPath} />

        <main id="main-content" class="flex-1">
          {children}
        </main>

        <Footer />

        {bodyScript && (
          <script dangerouslySetInnerHTML={{ __html: bodyScript }} />
        )}
      </body>
    </html>
  );
}

function Nav({ currentPath }: { currentPath: string }) {
  return (
    <header class="sticky top-0 z-40 bg-surface/95 backdrop-blur-sm border-b border-gray-200">
      <div class="max-w-wide mx-auto px-6 lg:px-8">
        <nav
          class="flex items-center justify-between h-16"
          aria-label="Main navigation"
        >
          <a href="/" class="flex items-center" aria-label="Protocolized — Home">
            <img
              src="/protocolized_mark.png"
              class="h-10 w-auto"
              alt="Protocolized logo"
            />
          </a>

          <ul class="hidden md:flex items-center gap-1" role="list">
            {NAV_LINKS.map(({ href, label }) => (
              <li>
                <a
                  href={href}
                  class={
                    isActive(href, currentPath)
                      ? "px-3 py-2 rounded-md text-sm font-sans font-medium transition-colors text-primary bg-primary-light"
                      : "px-3 py-2 rounded-md text-sm font-sans font-medium transition-colors text-secondary hover:text-dark hover:bg-gray-100"
                  }
                  aria-current={isActive(href, currentPath) ? "page" : undefined}
                >
                  {label}
                </a>
              </li>
            ))}
          </ul>

          <button
            id="mobile-menu-btn"
            class="md:hidden p-2 rounded-md text-secondary hover:text-dark hover:bg-gray-100 transition-colors"
            aria-expanded="false"
            aria-controls="mobile-menu"
            aria-label="Toggle navigation menu"
          >
            <svg
              id="menu-icon"
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
            <svg
              id="close-icon"
              class="w-5 h-5 hidden"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </nav>

        <div id="mobile-menu" class="hidden md:hidden pb-4">
          <ul class="flex flex-col gap-1" role="list">
            {NAV_LINKS.map(({ href, label }) => (
              <li>
                <a
                  href={href}
                  class={
                    isActive(href, currentPath)
                      ? "block px-3 py-2 rounded-md text-sm font-sans font-medium transition-colors text-primary bg-primary-light"
                      : "block px-3 py-2 rounded-md text-sm font-sans font-medium transition-colors text-secondary hover:text-dark hover:bg-gray-100"
                  }
                  aria-current={isActive(href, currentPath) ? "page" : undefined}
                >
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </header>
  );
}

function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer class="bg-white border-t border-gray-200 mt-auto">
      <div class="max-w-wide mx-auto px-6 lg:px-8 py-12">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <p class="font-serif text-lg text-dark mb-2">Protocolized</p>
            <p class="text-sm text-secondary font-sans leading-relaxed">
              Accelerating Order. A sci-fi and thinkpiece magazine and research
              library on protocols.
            </p>
          </div>

          <div>
            <p class="text-xs font-sans font-medium text-secondary uppercase tracking-wider mb-3">
              Pages
            </p>
            <ul class="space-y-2" role="list">
              {[
                { href: "/resources", label: "Resources" },
                { href: "/about", label: "About" },
                { href: "/community", label: "Community" },
                { href: "/magazine", label: "Magazine" },
              ].map(({ href, label }) => (
                <li>
                  <a
                    href={href}
                    class="text-sm font-sans text-secondary hover:text-primary transition-colors"
                  >
                    {label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p class="text-xs font-sans font-medium text-secondary uppercase tracking-wider mb-3">
              Links
            </p>
            <ul class="space-y-2" role="list">
              <li>
                <a
                  href="https://protocolsociety.org"
                  class="text-sm font-sans text-secondary hover:text-primary transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Protocol Institute ↗
                </a>
              </li>
              <li>
                <a
                  href="https://summerofprotocols.com"
                  class="text-sm font-sans text-secondary hover:text-primary transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Archive (SoP) ↗
                </a>
              </li>
              <li>
                <a
                  href="/llms.txt"
                  class="text-sm font-sans text-secondary hover:text-primary transition-colors"
                >
                  llms.txt
                </a>
              </li>
              <li>
                <a
                  href="/rss.xml"
                  class="text-sm font-sans text-secondary hover:text-primary transition-colors"
                >
                  RSS feed
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div class="pt-8 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p class="text-xs font-sans text-secondary">
            © {year} Protocolized / Protocol Institute
          </p>
          <div class="flex items-center gap-4">
            <a
              href="https://discord.gg/Aj5FbGsNYV"
              class="text-xs font-sans text-secondary hover:text-primary transition-colors"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Join Discord"
            >
              Discord
            </a>
            <a
              href="https://www.youtube.com/@protocolized"
              class="text-xs font-sans text-secondary hover:text-primary transition-colors"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="YouTube channel"
            >
              YouTube
            </a>
            <a
              href="https://protocolized.summerofprotocols.com"
              class="text-xs font-sans text-secondary hover:text-primary transition-colors"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Magazine on Substack"
            >
              Magazine
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
