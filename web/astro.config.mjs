// @ts-check
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "astro/config";

// Builds to plain static HTML in dist/ — nginx on the Oracle box serves it
// directly, with no Node process to keep alive in production.
export default defineConfig({
  site: "https://letsmock.com",
  // Emit privacy.html rather than privacy/index.html, so /privacy answers 200
  // instead of redirecting. The privacy URL is submitted to Google Play, and a
  // redirect there is one more thing for a reviewer to trip over.
  build: { format: "file" },
  trailingSlash: "never",
  vite: {
    plugins: [tailwindcss()],
  },
});
