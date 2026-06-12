import { Base } from "./base";
import { fmtDate, mobileMenuScript } from "./static-pages";
import type { Book, Resource } from "../db";

// ── Index ──────────────────────────────────────────────────────────────────

export function BooksPage({
  currentPath,
  books,
}: {
  currentPath: string;
  books: Book[];
}) {
  return (
    <Base
      title="Books"
      description="Books published by the Protocol Institute and the Summer of Protocols program."
      currentPath={currentPath}
      bodyScript={mobileMenuScript()}
    >
      <section class="py-16 md:py-20 px-6 lg:px-8">
        <div class="max-w-wide mx-auto">
          <div class="mb-10">
            <h1 class="font-serif text-4xl md:text-5xl text-dark mb-3">Books</h1>
            <p class="font-sans text-secondary text-lg max-w-2xl">
              Publications from the Protocol Institute and the Summer of Protocols program.
            </p>
          </div>

          {books.length === 0 ? (
            <p class="font-sans text-secondary">No books yet.</p>
          ) : (
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {books.map((book) => (
                <BookCard book={book} />
              ))}
            </div>
          )}
        </div>
      </section>
    </Base>
  );
}

function BookCard({ book }: { book: Book }) {
  const blurb = book.description.length > 160
    ? book.description.slice(0, 157) + "…"
    : book.description;

  return (
    <a href={`/books/${book.slug}`} class="group flex gap-5 items-start">
      <div class="w-20 h-28 sm:w-24 sm:h-36 shrink-0 bg-primary-light rounded overflow-hidden">
        {book.cover_image ? (
          <img
            src={book.cover_image}
            alt={`Cover of ${book.title}`}
            class="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div class="w-full h-full flex flex-col items-center justify-center p-2 text-center">
            <span class="font-serif text-xs text-primary leading-tight">{book.title}</span>
          </div>
        )}
      </div>

      <div class="flex-1 min-w-0">
        <div class="flex items-start gap-2 mb-1 flex-wrap">
          <h2 class="font-serif text-xl text-dark leading-snug group-hover:text-primary transition-colors">
            {book.title}
          </h2>
          <span class="shrink-0 text-xs font-sans px-2 py-0.5 rounded-full bg-gray-100 text-secondary capitalize mt-1">
            {book.category}
          </span>
        </div>
        {book.subtitle && (
          <p class="font-sans text-sm text-secondary mb-1 italic">{book.subtitle}</p>
        )}
        {book.editor && (
          <p class="font-sans text-sm text-secondary mb-2">Ed. {book.editor}</p>
        )}
        <p class="font-body text-sm text-secondary leading-relaxed">{blurb}</p>
      </div>
    </a>
  );
}

// ── Detail ─────────────────────────────────────────────────────────────────

export function BookPage({
  currentPath,
  book,
  related,
  bodyHtml,
}: {
  currentPath: string;
  book: Book;
  related: Resource[];
  bodyHtml: string;
}) {
  const fullTitle = book.subtitle ? `${book.title}: ${book.subtitle}` : book.title;

  return (
    <Base
      title={fullTitle}
      description={book.description}
      ogImage={book.cover_image}
      currentPath={currentPath}
      bodyScript={mobileMenuScript()}
    >
      {/* Breadcrumb */}
      <div class="px-6 lg:px-8 pt-6">
        <div class="max-w-wide mx-auto">
          <nav class="text-sm font-sans text-secondary" aria-label="Breadcrumb">
            <a href="/books" class="hover:text-primary transition-colors">Books</a>
            <span class="mx-2 text-gray-300" aria-hidden="true">›</span>
            <span class="text-dark">{book.title}</span>
          </nav>
        </div>
      </div>

      <article class="px-6 lg:px-8 py-10">
        <div class="max-w-wide mx-auto">
          <div class="flex flex-col lg:flex-row gap-10 lg:gap-16">

            {/* Left: cover + action */}
            <div class="lg:w-64 shrink-0">
              <div class="aspect-[2/3] bg-primary-light rounded-lg overflow-hidden mb-4">
                {book.cover_image ? (
                  <img
                    src={book.cover_image}
                    alt={`Cover of ${book.title}`}
                    class="w-full h-full object-cover"
                    loading="eager"
                  />
                ) : (
                  <div class="w-full h-full flex flex-col items-center justify-center p-6 text-center">
                    <span class="font-serif text-xl text-primary leading-snug">{book.title}</span>
                  </div>
                )}
              </div>

              {(book.url || book.file) && (
                <div class="flex flex-col gap-2">
                  {book.file && (
                    <a href={book.file} download class="btn-primary w-full text-center block">
                      {book.file.endsWith(".epub") ? "Download ePub" : "Download PDF"}
                    </a>
                  )}
                  {book.url && (
                    <a
                      href={book.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      class="btn-secondary w-full text-center block"
                    >
                      Get the book →
                    </a>
                  )}
                </div>
              )}
            </div>

            {/* Right: metadata + body */}
            <div class="flex-1 min-w-0">
              <h1 class="font-serif text-3xl md:text-4xl text-dark leading-snug mb-2">
                {book.title}
              </h1>
              {book.subtitle && (
                <p class="font-serif text-xl text-secondary italic mb-4">{book.subtitle}</p>
              )}

              <div class="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm font-sans text-secondary mb-6">
                {book.editor && <span>Edited by {book.editor}</span>}
                {book.date && <span>{fmtDate(book.date, "year")}</span>}
                <span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-secondary capitalize">
                  {book.category}
                </span>
              </div>

              {/* Description / body */}
              {bodyHtml ? (
                <div
                  class="prose prose-protocolized mb-10"
                  dangerouslySetInnerHTML={{ __html: bodyHtml }}
                />
              ) : (
                <p class="font-body text-base text-secondary leading-relaxed mb-10">
                  {book.description}
                </p>
              )}

              {/* Table of contents */}
              {book.toc.length > 0 && (
                <section class="mb-10">
                  <h2 class="font-serif text-xl text-dark mb-4">Contents</h2>
                  <ol class="space-y-2">
                    {book.toc.map((entry, i) => (
                      <li class="flex gap-3 text-sm font-sans">
                        <span class="text-secondary shrink-0 w-5 text-right">{i + 1}.</span>
                        <span>
                          {entry.url ? (
                            <a href={entry.url} class="text-dark hover:text-primary transition-colors">
                              {entry.title}
                            </a>
                          ) : (
                            <span class="text-dark">{entry.title}</span>
                          )}
                          {entry.author && (
                            <span class="text-secondary"> — {entry.author}</span>
                          )}
                        </span>
                      </li>
                    ))}
                  </ol>
                </section>
              )}

              {/* Contributors */}
              {book.contributors.length > 0 && (
                <section class="mb-10">
                  <h2 class="font-serif text-xl text-dark mb-4">Contributors</h2>
                  <div class="flex flex-wrap gap-2">
                    {book.contributors.map((c) => (
                      <span class="text-xs font-sans bg-gray-100 text-secondary px-3 py-1 rounded-full">
                        {c.name}{c.role ? ` · ${c.role}` : ""}
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {/* Related resources */}
              {related.length > 0 && (
                <section>
                  <h2 class="font-serif text-xl text-dark mb-4">Related resources</h2>
                  <div class="space-y-3">
                    {related.map((r) => (
                      <a
                        href={`/resources/${r.slug}`}
                        class="flex items-start gap-3 group p-3 rounded-lg hover:bg-gray-50 transition-colors -mx-3"
                      >
                        <span class="text-xs font-sans bg-gray-100 text-secondary px-2 py-0.5 rounded-full shrink-0 mt-0.5">
                          {r.type}
                        </span>
                        <div class="min-w-0">
                          <p class="font-sans text-sm text-dark group-hover:text-primary transition-colors leading-snug">
                            {r.title}
                          </p>
                          <p class="text-xs font-sans text-secondary mt-0.5 line-clamp-1">
                            {r.description}
                          </p>
                        </div>
                      </a>
                    ))}
                  </div>
                </section>
              )}
            </div>
          </div>
        </div>
      </article>
    </Base>
  );
}
