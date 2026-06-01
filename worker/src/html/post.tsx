import { Base } from "./base";
import { fmtDate, mobileMenuScript } from "./static-pages";
import type { Post } from "../db";

export function PostPage({
  currentPath,
  post,
  bodyHtml,
  prev,
  next,
}: {
  currentPath: string;
  post: Post;
  bodyHtml: string | null;
  prev: Post | null;
  next: Post | null;
}) {
  const substackUrl =
    post.substack_url ??
    `https://protocolized.summerofprotocols.com/p/${post.slug}`;

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
          <nav aria-label="Breadcrumb" class="mb-8">
            <ol class="flex items-center gap-2 text-sm font-sans text-secondary" role="list">
              <li>
                <a href="/" class="hover:text-primary transition-colors">Home</a>
              </li>
              <li aria-hidden="true" class="text-gray-300">›</li>
              <li>
                <a href="/magazine" class="hover:text-primary transition-colors">Magazine</a>
              </li>
              <li aria-hidden="true" class="text-gray-300">›</li>
              <li class="text-dark truncate max-w-xs" aria-current="page">
                {post.title}
              </li>
            </ol>
          </nav>

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
            <div class="flex items-center gap-4 text-sm font-sans text-secondary mb-6">
              <span class="font-medium text-dark">{post.primary_author}</span>
              <span aria-hidden="true" class="text-gray-300">·</span>
              <time datetime={post.date}>{fmtDate(post.date, "long")}</time>
            </div>

            {/* Prominent "Read on Substack" — above the fold */}
            <a
              href={substackUrl}
              target="_blank"
              rel="noopener noreferrer"
              class="flex items-center gap-3 p-4 rounded-xl border-2 border-primary/30 bg-primary-light hover:border-primary hover:bg-primary/10 transition-colors group"
              aria-label="Read this post on Substack (opens in new tab)"
            >
              <svg
                class="w-5 h-5 text-primary shrink-0"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M22.539 8.242H1.46V5.406h21.08v2.836zM1.46 10.812V24L12 18.11 22.54 24V10.812H1.46zM22.54 0H1.46v2.836h21.08V0z" />
              </svg>
              <span class="font-sans text-sm font-medium text-primary group-hover:text-[#085041] transition-colors">
                Read on Substack — subscribe for new posts
              </span>
              <span class="ml-auto text-primary text-sm" aria-hidden="true">↗</span>
            </a>
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

          {/* Footer Substack CTA */}
          <div class="border-t border-gray-100 pt-8 mb-10">
            <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <p class="font-serif text-lg text-dark mb-1">Protocolized Magazine</p>
                <p class="font-sans text-sm text-secondary">
                  Essays, fiction, and protocol thinking.
                </p>
              </div>
              <a
                href={substackUrl}
                target="_blank"
                rel="noopener noreferrer"
                class="btn-primary shrink-0"
              >
                Subscribe on Substack ↗
              </a>
            </div>
          </div>

          {/* Prev / next navigation */}
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
