import { getCollection } from "astro:content";
import type { APIRoute } from "astro";

export const GET: APIRoute = async () => {
  const resources = await getCollection("resources");
  const sorted = resources.sort(
    (a, b) => b.data.date.getTime() - a.data.date.getTime()
  );

  const resourceLines = sorted
    .map((r) => `- [${r.data.title}](/resources/${r.slug})`)
    .join("\n");

  const content = `# Protocolized

> Accelerating Order. Protocolized is a research and practice initiative focused on protocols — the rules, standards, and agreements that structure coordination at every scale.

## About

Protocolized is part of Protocol Institute, a parent organization dedicated to advancing the study and practice of protocols across fields.

The site is a public-facing resource hub: a library of papers, frameworks, games, datasets, code, and tools related to protocols and coordination, alongside a community of researchers, practitioners, and academics.

## Resources

${resourceLines}

## Community

- Discord: https://discord.gg/Aj5FbGsNYV
- YouTube: https://www.youtube.com/@protocolized
- Magazine: https://protocolized.summerofprotocols.com

## External Links

- Protocol Institute: https://protocolsociety.org
- Summer of Protocols Archive: https://summerofprotocols.com

## Machine-readable endpoints

- Resource catalog: /api/resources.json
- RSS feed: /rss.xml
- Sitemap: /sitemap-index.xml
`;

  return new Response(content, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
};
