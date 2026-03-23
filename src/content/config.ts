import { defineCollection, z } from "astro:content";

const resources = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    type: z.enum([
      "paper",
      "working-paper",
      "framework",
      "workshop-template",
      "game",
      "dataset",
      "interview",
      "presentation",
      "code",
      "image",
      "prompt-template",
      "talk",
      "lecture",
      "article",
      "video",
    ]),
    authors: z.array(
      z.object({
        name: z.string(),
        url: z.string().optional(),
      })
    ),
    date: z.date(),
    description: z.string(),
    tags: z.array(z.string()),
    audience: z.array(
      z.enum(["researcher", "practitioner", "academic", "corporate"])
    ),
    featured: z.boolean().default(false),
    file: z.string().optional(),
    url: z.string().optional(),
    thumbnail: z.string().optional(),
  }),
});

export const collections = { resources };
