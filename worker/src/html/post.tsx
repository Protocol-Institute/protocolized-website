import { Base } from "./base";
import { fmtDate, mobileMenuScript } from "./static-pages";
import type { Post, SeriesContext } from "../db";

function SeriesNav({
  ctx,
  position,
}: {
  ctx: SeriesContext;
  position: "top" | "bottom";
}) {
  const { seriesTitle, seriesSlug, prev, next } = ctx;
  const upHref = `/books/${seriesSlug}`;
  const isBottom = position === "bottom";

  return (
    <nav
      aria-label={`${seriesTitle} series navigation`}
      class={
        "series-nav flex items-center gap-2 rounded-lg border border-primary/20 bg-primary-light/20 px-4 py-3 text-sm font-sans" +
        (isBottom ? " mt-2" : " mb-8")
      }
    >
      {/* Prev */}
      <div class="flex-1 min-w-0">
        {prev ? (
          <a
            href={prev.url}
            class="group flex items-center gap-1.5 text-secondary hover:text-primary transition-colors"
            {...(prev.external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
          >
            <span class="flex-shrink-0">←</span>
            <span class="truncate group-hover:text-primary">{prev.title}</span>
            {prev.external && <span class="flex-shrink-0 text-xs opacity-60">↗</span>}
          </a>
        ) : (
          <span class="text-gray-300 select-none">←</span>
        )}
      </div>

      {/* Up — series home */}
      <div class="flex-shrink-0 text-center px-3 border-l border-r border-primary/20">
        <a
          href={upHref}
          class="block font-medium text-primary hover:underline leading-tight"
        >
          ↑ {seriesTitle}
        </a>
        <span class="text-xs text-secondary">
          Part {ctx.position} of {ctx.totalParts}
        </span>
      </div>

      {/* Next */}
      <div class="flex-1 min-w-0 text-right">
        {next ? (
          <a
            href={next.url}
            class="group flex items-center justify-end gap-1.5 text-secondary hover:text-primary transition-colors"
            {...(next.external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
          >
            {next.external && <span class="flex-shrink-0 text-xs opacity-60">↗</span>}
            <span class="truncate group-hover:text-primary">{next.title}</span>
            <span class="flex-shrink-0">→</span>
          </a>
        ) : (
          <span class="text-gray-300 select-none">→</span>
        )}
      </div>
    </nav>
  );
}

export function PostPage({
  currentPath,
  post,
  bodyHtml,
  prev,
  next,
  seriesCtx,
}: {
  currentPath: string;
  post: Post;
  bodyHtml: string | null;
  prev: Post | null;
  next: Post | null;
  seriesCtx: SeriesContext | null;
}) {
  const substackUrl =
    post.substack_url ??
    `https://protocolized.summerofprotocols.com/p/${post.slug}`;
  const isPlaceholder = !!post.is_placeholder;
  const substackSubscribeUrl = "https://protocolized.summerofprotocols.com";

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: post.title,
    ...(post.subtitle ? { description: post.subtitle } : {}),
    datePublished: post.date,
    author: {
      "@type": "Person",
      name: post.primary_author,
    },
    publisher: {
      "@type": "Organization",
      name: "Protocolized",
      url: "https://protocolized.io",
    },
    url: `https://protocolized.io/p/${post.slug}`,
    ...(post.cover_image ? { image: post.cover_image } : {}),
  };

  const script = mobileMenuScript();

  const breadcrumb = seriesCtx ? (
    <ol class="flex items-center gap-2 text-sm font-sans text-secondary" role="list">
      <li><a href="/" class="hover:text-primary transition-colors">Home</a></li>
      <li aria-hidden="true" class="text-gray-300">›</li>
      <li><a href="/books" class="hover:text-primary transition-colors">Books</a></li>
      <li aria-hidden="true" class="text-gray-300">›</li>
      <li>
        <a href={`/books/${seriesCtx.seriesSlug}`} class="hover:text-primary transition-colors">
          {seriesCtx.seriesTitle}
        </a>
      </li>
      <li aria-hidden="true" class="text-gray-300">›</li>
      <li class="text-dark truncate max-w-xs" aria-current="page">{post.title}</li>
    </ol>
  ) : (
    <ol class="flex items-center gap-2 text-sm font-sans text-secondary" role="list">
      <li><a href="/" class="hover:text-primary transition-colors">Home</a></li>
      <li aria-hidden="true" class="text-gray-300">›</li>
      <li><a href="/magazine" class="hover:text-primary transition-colors">Magazine</a></li>
      <li aria-hidden="true" class="text-gray-300">›</li>
      <li class="text-dark truncate max-w-xs" aria-current="page">{post.title}</li>
    </ol>
  );

  return (
    <Base
      title={post.title}
      description={post.subtitle ?? post.summary ?? ""}
      canonicalURL={`https://protocolized.io/p/${post.slug}`}
      jsonLd={jsonLd}
      ogImage={post.cover_image}
      currentPath={currentPath}
      bodyScript={script}
    >
      <div class="py-12 px-6 lg:px-8">
        <div class="max-w-prose mx-auto">

          {/* Breadcrumb */}
          <nav aria-label="Breadcrumb" class="mb-6">
            {breadcrumb}
          </nav>

          {/* Series nav — top */}
          {seriesCtx && <SeriesNav ctx={seriesCtx} position="top" />}

          {/* Header */}
          <header class="mb-8">
            <div class="mb-3">
              <span class="inline-block px-2.5 py-1 rounded-full text-xs font-sans font-medium bg-primary-light text-primary">
                {post.section}
              </span>
            </div>
            <h1 class="font-serif text-4xl lg:text-5xl text-dark leading-tight mb-4">
              {post.title}
            </h1>
            {post.subtitle && (
              <p class="font-body text-xl text-secondary leading-relaxed mb-6">
                {post.subtitle}
              </p>
            )}
            <div class="flex items-center gap-4 text-sm font-sans text-secondary mb-8">
              <span class="font-medium text-dark">{post.primary_author}</span>
              <span aria-hidden="true" class="text-gray-300">·</span>
              <time datetime={post.date}>{fmtDate(post.date, "long")}</time>
              <span aria-hidden="true" class="text-gray-300">·</span>
              {!isPlaceholder && (
                <a
                  href={substackUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="hover:text-primary transition-colors"
                >
                  View on Substack ↗
                </a>
              )}
            </div>
          </header>

          {/* Cover image */}
          {post.cover_image && (
            <figure class="mb-10 -mx-6 lg:-mx-8">
              <img
                src={post.cover_image}
                alt={`Cover image for "${post.title}"`}
                class="w-full object-cover max-h-96"
                loading="eager"
              />
            </figure>
          )}

          {/* Post body */}
          {bodyHtml ? (
            <div
              class="prose max-w-none mb-12"
              dangerouslySetInnerHTML={{ __html: bodyHtml }}
            />
          ) : isPlaceholder ? (
            <div class="mb-12 p-8 rounded-xl border border-primary/20 bg-primary-light/20 text-center">
              <p class="font-serif text-xl text-dark mb-3">Coming soon to Protocolized</p>
              <p class="font-sans text-sm text-secondary mb-6 max-w-sm mx-auto">
                This story will be mirrored here when it's published on Substack.
                In the meantime, you can read it on the author's site.
              </p>
              <a
                href={substackUrl}
                target="_blank"
                rel="noopener noreferrer"
                class="btn-primary"
              >
                Read this story →
              </a>
            </div>
          ) : (
            <div class="mb-12 p-8 rounded-xl border border-gray-200 text-center">
              <p class="font-sans text-secondary mb-4">
                This post hasn't been mirrored yet.
              </p>
              <a
                href={substackUrl}
                target="_blank"
                rel="noopener noreferrer"
                class="btn-primary"
              >
                Read on Substack →
              </a>
            </div>
          )}

          {/* Series nav — bottom */}
          {seriesCtx && <SeriesNav ctx={seriesCtx} position="bottom" />}

          {/* Footer Substack CTA */}
          <div class="border-t border-gray-100 pt-8 mt-10 mb-10">
            <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <p class="font-serif text-lg text-dark mb-1">Protocolized Magazine</p>
                <p class="font-sans text-sm text-secondary">
                  Essays, fiction, and protocol thinking.
                </p>
              </div>
              <a
                href={substackSubscribeUrl}
                target="_blank"
                rel="noopener noreferrer"
                class="btn-primary shrink-0"
              >
                Subscribe on Substack ↗
              </a>
            </div>
          </div>

          {/* Prev / next navigation (chronological) */}
          {(prev || next) && (
            <nav aria-label="Post navigation" class="border-t border-gray-100 pt-8">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {prev ? (
                  <a
                    href={`/p/${prev.slug}`}
                    class="group flex flex-col gap-1 p-4 rounded-xl border border-gray-200 hover:border-primary hover:bg-primary-light transition-colors"
                  >
                    <span class="text-xs font-sans text-secondary">← Previous</span>
                    <span class="font-serif text-dark group-hover:text-primary transition-colors line-clamp-2">
                      {prev.title}
                    </span>
                  </a>
                ) : (
                  <div />
                )}
                {next && (
                  <a
                    href={`/p/${next.slug}`}
                    class="group flex flex-col gap-1 p-4 rounded-xl border border-gray-200 hover:border-primary hover:bg-primary-light transition-colors sm:text-right"
                  >
                    <span class="text-xs font-sans text-secondary">Next →</span>
                    <span class="font-serif text-dark group-hover:text-primary transition-colors line-clamp-2">
                      {next.title}
                    </span>
                  </a>
                )}
              </div>
            </nav>
          )}
        </div>
      </div>
    </Base>
  );
}
