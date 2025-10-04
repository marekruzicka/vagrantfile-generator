import { defineConfig } from 'vite'

const internalApiTarget = process.env.VITE_API_URL || 'http://localhost:8000'
const browserApiUrl = process.env.VITE_BROWSER_API_URL || ''

export default defineConfig({
  root: 'src',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    allowedHosts: [
      // Default minimal hosts
      'localhost',
      '127.0.0.1',
      // Additional hosts from environment variable
      ...(process.env.VITE_ALLOWED_HOSTS 
        ? process.env.VITE_ALLOWED_HOSTS.split(',').map(host => host.trim())
        : [])
      ,
      // Allow-all fallback for preview/dev where explicit host mapping is used
      '*'
    ],
    // Proxy API requests to backend (reuse VITE_API_URL)
    proxy: {
      '/api': {
        target: internalApiTarget,
        changeOrigin: true,
        secure: false
      }
    }
  },
  preview: {
    port: 5173,
    host: '0.0.0.0',
    // preview has its own allowedHosts setting
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      ...(process.env.VITE_ALLOWED_HOSTS
        ? process.env.VITE_ALLOWED_HOSTS.split(',').map(h => h.trim())
        : [])
      ,
      'k8plus',
      'k8plus:8080',
      '*'
    ],
    // Proxy API calls in preview as well
    proxy: {
      '/api': {
        target: internalApiTarget,
        changeOrigin: true,
        secure: false
      }
    }
  },
  define: {
    // Make browser-visible API URL available to the frontend
    __API_URL__: JSON.stringify(browserApiUrl),
  }
})