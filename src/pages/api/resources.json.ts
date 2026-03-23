import { getCollection } from "astro:content";
import type { APIRoute } from "astro";

export const GET: APIRoute = async () => {
  const resources = await getCollection("resources");
  const data = resources
    .sort((a, b) => b.data.date.getTime() - a.data.date.getTime())
    .map((r) => ({
      slug: r.slug,
      title: r.data.title,
      type: r.data.type,
      authors: r.data.authors,
      date: r.data.date.toISOString(),
      description: r.data.description,
      tags: r.data.tags,
      audience: r.data.audience,
      featured: r.data.featured,
      file: r.data.file ?? null,
      url: r.data.url ?? null,
      thumbnail: r.data.thumbnail ?? null,
      href: `/resources/${r.slug}`,
    }));

  return new Response(JSON.stringify({ resources: data, count: data.length }, null, 2), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
    },
  });
};
