import { resolve } from 'node:path';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  // Relative paths, so that the site works under any GitHub Pages path.
  base: './',
  plugins: [tailwindcss()],
  build: {
    // MapLibre alone is about 1 MB before compression.
    chunkSizeWarningLimit: 1200,
    rolldownOptions: {
      input: {
        main: resolve(import.meta.dirname, 'index.html'),
      },
    },
  },
});
