// @ts-check
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "astro/config";

// Builds to plain static HTML in dist/ — nginx on the Oracle box serves it
// directly, with no Node process to keep alive in production.
export default defineConfig({
  site: "https://letsmock.com",
  vite: {
    plugins: [tailwindcss()],
  },
});
