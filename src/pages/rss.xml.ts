import rss from "@astrojs/rss";
import { getCollection } from "astro:content";
import type { APIContext } from "astro";

export async function GET(context: APIContext) {
  const resources = await getCollection("resources");
  const sorted = resources.sort(
    (a, b) => b.data.date.getTime() - a.data.date.getTime()
  );

  return rss({
    title: "Protocolized Resources",
    description:
      "New resources on protocols — papers, frameworks, games, datasets, code, and more.",
    site: context.site!.toString(),
    items: sorted.map((r) => ({
      title: r.data.title,
      link: `/resources/${r.slug}`,
      description: r.data.description,
      pubDate: r.data.date,
      categories: [...r.data.tags, r.data.type],
      author: r.data.authors.map((a) => a.name).join(", "),
    })),
    customData: `<language>en-us</language>`,
  });
}
