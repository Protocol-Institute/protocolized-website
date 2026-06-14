import { Base } from "./base";
import { TypeBadge, fmtDate, mobileMenuScript, substackToInternalUrl } from "./static-pages";
import type { Resource } from "../db";

const SCHEMA_TYPE: Record<string, string> = {
  paper: "ScholarlyArticle",
  "working-paper": "ScholarlyArticle",
  framework: "CreativeWork",
  "workshop-template": "CreativeWork",
  game: "CreativeWork",
  dataset: "Dataset",
  interview: "Interview",
  presentation: "PresentationDigitalDocument",
  code: "SoftwareSourceCode",
  image: "ImageObject",
  "prompt-template": "CreativeWork",
};

export function ResourcePage({
  currentPath,
  resource,
  related,
  bodyHtml,
}: {
  currentPath: string;
  resource: Resource;
  related: Resource[];
  bodyHtml: string;
}) {
  const internalPostUrl = substackToInternalUrl(resource.url);
  const primaryAction = resource.file
    ? { label: "Download", href: resource.file, download: true, external: false }
    : internalPostUrl
    ? { label: "Read article", href: internalPostUrl, external: false, download: false }
    : resource.url
    ? { label: "Open resource", href: resource.url, external: true, download: false }
    : null;

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": SCHEMA_TYPE[resource.type] ?? "CreativeWork",
    name: resource.title,
    description: resource.description,
    datePublished: resource.date,
    author: resource.authors.map((a) => ({
      "@type": "Person",
      name: a.name,
      ...(a.url ? { url: a.url } : {}),
    })),
    keywords: resource.tags,
    url: `https://protocolized.io/resources/${resource.slug}`,
  };

  const script = mobileMenuScript();

  return (
    <Base
      title={resource.title}
      description={resource.description}
      jsonLd={jsonLd}
      currentPath={currentPath}
      bodyScript={script}
    >
      <div class="py-12 px-6 lg:px-8">
        <div class="max-w-prose mx-auto">
          <nav aria-label="Breadcrumb" class="mb-8">
            <ol class="flex items-center gap-2 text-sm font-sans text-secondary" role="list">
              <li>
                <a href="/" class="hover:text-primary transition-colors">
                  Home
                </a>
              </li>
              <li aria-hidden="true" class="text-gray-300">›</li>
              <li>
                <a href="/resources" class="hover:text-primary transition-colors">
                  Resources
                </a>
              </li>
              <li aria-hidden="true" class="text-gray-300">›</li>
              <li class="text-dark truncate max-w-xs" aria-current="page">
                {resource.title}
              </li>
            </ol>
          </nav>

          <h1 class="font-serif text-4xl md:text-5xl text-dark leading-tight mb-6">
            {resource.title}
          </h1>

          <div class="flex flex-wrap items-center gap-3 mb-6 pb-6 border-b border-gray-100">
            <TypeBadge type={resource.type} />
            {resource.authors.length > 0 && (
              <span class="text-sm font-sans text-secondary">
                {resource.authors.map((a, i) => (
                  <>
                    {a.url ? (
                      <a
                        href={a.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        class="hover:text-primary transition-colors"
                      >
                        {a.name}
                      </a>
                    ) : (
                      a.name
                    )}
                    {i < resource.authors.length - 1 ? ", " : ""}
                  </>
                ))}
              </span>
            )}
            <time datetime={resource.date} class="text-sm font-sans text-secondary">
              {fmtDate(resource.date, "long")}
            </time>
            {resource.audience.length > 0 && (
              <div class="flex flex-wrap gap-1.5">
                {resource.audience.map((a) => (
                  <a
                    href={`/resources?audience=${a}`}
                    class="text-xs font-sans bg-gray-100 text-secondary px-2.5 py-1 rounded-full hover:bg-primary-light hover:text-primary transition-colors capitalize"
                  >
                    {a}
                  </a>
                ))}
              </div>
            )}
          </div>

          {resource.thumbnail && (
            <div class="mb-8 rounded-xl overflow-hidden aspect-[2/1] bg-gray-100">
              <img
                src={resource.thumbnail}
                alt={resource.title}
                class="w-full h-full object-cover"
                loading="eager"
              />
            </div>
          )}

          {primaryAction && (
            <div class="mb-8">
              <a
                href={primaryAction.href}
                class="btn-primary text-base px-6 py-3"
                target={primaryAction.external ? "_blank" : undefined}
                rel={primaryAction.external ? "noopener noreferrer" : undefined}
                download={primaryAction.download ? true : undefined}
              >
                {primaryAction.label} →
              </a>
            </div>
          )}

          <div class="prose font-body text-dark max-w-none mb-8">
            <p class="text-lg leading-relaxed text-secondary">{resource.description}</p>
          </div>

          {bodyHtml && (
            <div
              class="prose prose-lg font-body max-w-none mb-12"
              dangerouslySetInnerHTML={{ __html: bodyHtml }}
            />
          )}

          {resource.tags.length > 0 && (
            <div class="mb-12">
              <p class="text-xs font-sans font-medium text-secondary uppercase tracking-wider mb-3">
                Topics
              </p>
              <div class="flex flex-wrap gap-2">
                {resource.tags.map((tag) => (
                  <a
                    href={`/resources?q=${encodeURIComponent(tag)}`}
                    class="text-sm font-sans bg-gray-100 text-secondary px-3 py-1.5 rounded-full hover:bg-primary-light hover:text-primary transition-colors"
                  >
                    {tag}
                  </a>
                ))}
              </div>
            </div>
          )}

          {related.length > 0 && (
            <div class="not-prose mt-16 pt-8 border-t border-gray-100">
              <h2 class="font-serif text-2xl text-dark mb-6">Related resources</h2>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
                {related.map((r) => (
                  <article class="card p-5 flex flex-col gap-3 relative">
                    <TypeBadge type={r.type} />
                    <div>
                      <h3 class="font-serif text-base text-dark leading-snug mb-1">
                        <a
                          href={`/resources/${r.slug}`}
                          class="hover:text-primary transition-colors after:absolute after:inset-0"
                        >
                          {r.title}
                        </a>
                      </h3>
                      <p class="text-xs font-body text-secondary line-clamp-2 leading-relaxed">
                        {r.description}
                      </p>
                    </div>
                    <p class="mt-auto text-xs font-sans text-secondary">
                      {r.authors.map((a) => a.name).join(", ")}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Base>
  );
}
