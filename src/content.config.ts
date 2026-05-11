import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const posts = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/posts" }),
  schema: z.object({
    title: z.string(),
    author: z.string().optional(),
    layout: z.string().optional(),
    excerpt: z.string().optional(),
    date: z.coerce.date().optional(),
  }),
});

export const collections = { posts };
