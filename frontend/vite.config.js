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
    allowedHosts: [
      // Default minimal hosts
      'localhost',
      '127.0.0.1',
      // Additional hosts from environment variable
      ...(process.env.VITE_ALLOWED_HOSTS 
        ? process.env.VITE_ALLOWED_HOSTS.split(',').map(host => host.trim())
        : [])
    ]
  },
  define: {
    // Make API URL available to the frontend
    __API_URL__: JSON.stringify(process.env.VITE_API_URL || ''),
  }
})