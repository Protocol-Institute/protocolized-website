import { Hono } from "hono";
import { marked } from "marked";
import {
  getAllResources,
  getResource,
  getLatestArticles,
  getRelatedResources,
  getAnthologies,
  getPost,
  getLatestPosts,
  getAdjacentPosts,
  getAllBooks,
  getBook,
  getSeriesContext,
  getRandomArchiveResources,
  getRandomBooks,
} from "./db";
import { getLatestYouTubeVideos } from "./youtube";
import { HomePage } from "./html/home";
import { ResourcesPage } from "./html/resources";
import { ResourcePage } from "./html/resource";
import { PostPage } from "./html/post";
import { BooksPage, BookPage } from "./html/books";
import { LexiconPage } from "./html/lexicon";
import { AboutPage, CommunityPage, MagazinePage, AnthologiesPage } from "./html/static-pages";
import { NewNatureFeaturePage } from "./html/feature-new-nature";

interface Env {
  DB: D1Database;
  FILES: R2Bucket;
}

const app = new Hono<{ Bindings: Env }>();

app.get("/", async (c) => {
  const [posts, archiveResources, books, ytVideos] = await Promise.all([
    getLatestPosts(c.env.DB, 3),
    getRandomArchiveResources(c.env.DB, 2),
    getRandomBooks(c.env.DB, 1),
    getLatestYouTubeVideos(2),
  ]);
  return c.html(
    <HomePage
      currentPath="/"
      latestPosts={posts}
      archiveResources={archiveResources}
      carouselBooks={books}
      ytVideos={ytVideos}
    />
  );
});

app.get("/about", (c) =>
  c.html(<AboutPage currentPath="/about" />)
);

app.get("/community", (c) =>
  c.html(<CommunityPage currentPath="/community" />)
);

app.get("/magazine", async (c) => {
  const posts = await getLatestPosts(c.env.DB, 100);
  return c.html(<MagazinePage currentPath="/magazine" posts={posts} />);
});

app.get("/p/:slug", async (c) => {
  const slug = c.req.param("slug");
  const post = await getPost(c.env.DB, slug);
  if (!post) {
    return c.redirect(
      `https://protocolized.summerofprotocols.com/p/${slug}`,
      302
    );
  }
  const [{ prev, next }, bodyObj, seriesCtx] = await Promise.all([
    getAdjacentPosts(c.env.DB, post),
    post.body_r2_key ? c.env.FILES.get(post.body_r2_key) : Promise.resolve(null),
    post.series_slug && post.series_position != null
      ? getSeriesContext(c.env.DB, post.series_slug, post.series_position)
      : Promise.resolve(null),
  ]);
  const bodyHtml = bodyObj ? await bodyObj.text() : null;
  return c.html(
    <PostPage
      currentPath={`/p/${slug}`}
      post={post}
      bodyHtml={bodyHtml}
      prev={prev}
      next={next}
      seriesCtx={seriesCtx}
    />
  );
});

app.get("/p/:slug/", (c) =>
  c.redirect(`/p/${c.req.param("slug")}`, 301)
);

app.get("/books", async (c) => {
  const books = await getAllBooks(c.env.DB);
  return c.html(<BooksPage currentPath="/books" books={books} />);
});

app.get("/books/:slug", async (c) => {
  const slug = c.req.param("slug");
  const book = await getBook(c.env.DB, slug);
  if (!book) return c.html(notFound(), 404);

  const [related, bodyHtml] = await Promise.all([
    book.tags.length > 0
      ? getRelatedResources(c.env.DB, slug, book.tags)
      : Promise.resolve([]),
    book.body
      ? Promise.resolve(marked.parse(book.body) as string)
      : Promise.resolve(""),
  ]);

  return c.html(
    <BookPage
      currentPath={`/books/${slug}`}
      book={book}
      related={related}
      bodyHtml={bodyHtml}
    />
  );
});

app.get("/features/new-nature", (c) =>
  c.html(<NewNatureFeaturePage currentPath="/features/new-nature" />)
);
app.get("/features/new-nature/", (c) =>
  c.redirect("/features/new-nature", 301)
);

app.get("/anthologies", async (c) => {
  const anthologies = await getAnthologies(c.env.DB);
  return c.html(
    <AnthologiesPage currentPath="/anthologies" anthologies={anthologies} />
  );
});

app.get("/resources", async (c) => {
  const resources = await getAllResources(c.env.DB);
  return c.html(
    <ResourcesPage currentPath="/resources" resources={resources} />
  );
});

app.get("/resources/protocol-lexicon", (c) =>
  c.html(<LexiconPage currentPath="/resources/protocol-lexicon" />)
);
app.get("/resources/protocol-lexicon/", (c) =>
  c.redirect("/resources/protocol-lexicon", 301)
);

app.get("/resources/:slug", async (c) => {
  const slug = c.req.param("slug");

  const resource = await getResource(c.env.DB, slug);
  if (!resource) {
    return c.html(notFound(), 404);
  }

  const [related, bodyHtml] = await Promise.all([
    getRelatedResources(c.env.DB, slug, resource.tags),
    resource.body
      ? Promise.resolve(marked.parse(resource.body) as string)
      : Promise.resolve(""),
  ]);

  return c.html(
    <ResourcePage
      currentPath={`/resources/${slug}`}
      resource={resource}
      related={related}
      bodyHtml={bodyHtml}
    />
  );
});

app.get("/api/lexicon.json", (c) => c.redirect("/lexicon.json", 301));

app.get("/api/resources.json", async (c) => {
  const resources = await getAllResources(c.env.DB);
  const data = resources.map((r) => ({
    slug: r.slug,
    title: r.title,
    type: r.type,
    mediaType: ["talk", "lecture", "presentation"].includes(r.type)
      ? "video"
      : "text",
    description: r.description,
    authors: r.authors,
    date: r.date,
    tags: r.tags,
    audience: r.audience,
    featured: r.featured,
  }));
  return c.json(data);
});

app.get("/llms.txt", async (c) => {
  const resources = await getAllResources(c.env.DB);
  const lines = resources
    .map((r) => `- [${r.title}](/resources/${r.slug})`)
    .join("\n");

  const content = `# Protocolized

> Accelerating Order. Protocolized is a sci-fi and thinkpiece magazine and research library on protocols, published by the Protocol Institute.

## About

Protocolized is part of Protocol Institute, a parent organization dedicated to advancing the study and practice of protocols across fields.

The magazine publishes stories, articles, and columns exploring protocols through fiction and critical thinking. The research library hosts papers, talks, templates, and more from the Summer of Protocols program.

## Resources

${lines}

## Community

- Discord: https://discord.gg/Z3fgsW8D4s
- YouTube: https://www.youtube.com/@protocolized
- Magazine: https://protocolized.summerofprotocols.com

## External Links

- Protocol Institute: https://protocolsociety.org
- Summer of Protocols Archive: https://summerofprotocols.com

## Machine-readable endpoints

- Resource catalog: /api/resources.json
- RSS feed: /rss.xml
- Sitemap: /sitemap.xml
`;

  return new Response(content, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
});

app.get("/rss.xml", async (c) => {
  const resources = await getAllResources(c.env.DB);
  const items = resources
    .map((r) => {
      const pubDate = new Date(r.date + "T00:00:00Z").toUTCString();
      const cats = [...r.tags, r.type]
        .map((t) => `<category>${t}</category>`)
        .join("");
      const authors = r.authors.map((a) => a.name).join(", ");
      return `
    <item>
      <title><![CDATA[${r.title}]]></title>
      <link>https://protocolized.io/resources/${r.slug}</link>
      <guid>https://protocolized.io/resources/${r.slug}</guid>
      <description><![CDATA[${r.description}]]></description>
      <pubDate>${pubDate}</pubDate>
      ${cats}
      <author>${authors}</author>
    </item>`;
    })
    .join("");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Protocolized Resources</title>
    <link>https://protocolized.io</link>
    <description>New resources on protocols — papers, frameworks, games, datasets, code, and more.</description>
    <language>en-us</language>
    <atom:link href="https://protocolized.io/rss.xml" rel="self" type="application/rss+xml" />
    ${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
  });
});

app.get("/sitemap.xml", async (c) => {
  const [resources, books, posts] = await Promise.all([
    getAllResources(c.env.DB),
    getAllBooks(c.env.DB),
    getLatestPosts(c.env.DB, 10000),
  ]);

  const today = new Date().toISOString().slice(0, 10);

  function url(loc: string, opts: { lastmod?: string; changefreq?: string; priority?: string } = {}) {
    return [
      `  <url>`,
      `    <loc>https://protocolized.io${loc}</loc>`,
      opts.lastmod   ? `    <lastmod>${opts.lastmod}</lastmod>` : null,
      opts.changefreq ? `    <changefreq>${opts.changefreq}</changefreq>` : null,
      opts.priority  ? `    <priority>${opts.priority}</priority>` : null,
      `  </url>`,
    ].filter(Boolean).join("\n");
  }

  const staticUrls = [
    url("/",                        { lastmod: today, changefreq: "daily",   priority: "1.0" }),
    url("/resources",               { lastmod: today, changefreq: "daily",   priority: "0.9" }),
    url("/magazine",                { lastmod: today, changefreq: "daily",   priority: "0.8" }),
    url("/books",                   { lastmod: today, changefreq: "weekly",  priority: "0.7" }),
    url("/resources/protocol-lexicon", { lastmod: today, changefreq: "weekly", priority: "0.7" }),
    url("/features/new-nature",     { lastmod: "2026-06-17", changefreq: "monthly", priority: "0.8" }),
    url("/about",                   { changefreq: "monthly", priority: "0.5" }),
    url("/community",               { changefreq: "monthly", priority: "0.5" }),
    url("/anthologies",             { changefreq: "monthly", priority: "0.6" }),
  ];

  const postUrls = posts.map((p) =>
    url(`/p/${p.slug}`, {
      lastmod: p.date,
      changefreq: "monthly",
      priority: "0.8",
    })
  );

  const resourceUrls = resources.map((r) =>
    url(`/resources/${r.slug}`, {
      lastmod: r.date,
      changefreq: "monthly",
      priority: "0.6",
    })
  );

  const bookUrls = books.map((b) =>
    url(`/books/${b.slug}`, {
      lastmod: b.date,
      changefreq: "monthly",
      priority: "0.7",
    })
  );

  const allUrls = [...staticUrls, ...postUrls, ...resourceUrls, ...bookUrls].join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${allUrls}
</urlset>`;

  return new Response(xml, {
    headers: { "Content-Type": "application/xml; charset=utf-8" },
  });
});

function notFound() {
  return (
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <title>Not found — Protocolized</title>
        <link rel="stylesheet" href="/style.css" />
      </head>
      <body class="min-h-screen flex items-center justify-center bg-surface">
        <div class="text-center">
          <p class="font-sans text-secondary text-sm mb-4">404</p>
          <h1 class="font-serif text-4xl text-dark mb-4">Resource not found</h1>
          <p class="font-sans text-secondary mb-8">
            This resource doesn't exist or may have been moved.
          </p>
          <a href="/resources" class="btn-primary">
            Browse all resources →
          </a>
        </div>
      </body>
    </html>
  );
}

export default app;
