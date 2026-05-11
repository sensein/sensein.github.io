import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";

const base = process.env.ASTRO_BASE?.trim() || "/";

export default defineConfig({
  site: "https://sensein.group",
  base,
  trailingSlash: "ignore",
  integrations: [mdx(), sitemap()],
  vite: {
    plugins: [tailwindcss()],
  },
  markdown: {
    shikiConfig: {
      theme: "github-light-default",
      wrap: true,
    },
  },
});
