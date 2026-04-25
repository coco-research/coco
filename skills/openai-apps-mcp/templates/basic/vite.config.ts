import { defineConfig } from 'vite';
import { cloudflareDevProxyVitePlugin as cloudflare } from '@cloudflare/vite-plugin';

export default defineConfig({
  plugins: [
    cloudflare({
      configPath: 'wrangler.jsonc',
      persist: { path: '.wrangler/state' }
    })
  ],
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        worker: './src/index.ts'
      },
      output: {
        entryFileNames: (chunkInfo) => {
          if (chunkInfo.name === 'worker') return 'index.js';
          return 'client/[name]-[hash].js';
        },
        assetFileNames: 'client/[name]-[hash][extname]'
      }
    }
  }
});
