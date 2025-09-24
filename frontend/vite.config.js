import { defineConfig } from 'vite'

export default defineConfig({
  root: 'src',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
  },
  define: {
    // Make API URL available to the frontend
    __API_URL__: JSON.stringify(process.env.VITE_API_URL || ''),
  }
})