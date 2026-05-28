import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { boneyardPlugin } from 'boneyard-js/vite'

export default defineConfig({
  plugins: [react(), tailwindcss(), boneyardPlugin()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
