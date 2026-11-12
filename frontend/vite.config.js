import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  base: '/static/', // Indispensable pour que Django trouve les fichiers
  build: {
    manifest: 'manifest.json',
    outDir: resolve('./dist'), // Les fichiers compilés iront dans frontend/dist
    rollupOptions: {
      input: {
        main: resolve('./src/main.jsx'),
      },
    },
    emptyOutDir: true,
  },
})