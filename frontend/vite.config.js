import { defineConfig } from 'vite'
import { resolve } from 'path'
import { readFileSync } from 'fs'
import { dirname, resolve as pathResolve } from 'path'

const internalApiTarget = process.env.VITE_API_URL || 'http://localhost:8000'
const browserApiUrl = process.env.VITE_BROWSER_API_URL || ''

function vitePluginHtmlInclude() {
  const INCLUDE_RE = /<!--\s*@vite-include\s+(.+?)\s*-->/g

  return {
    name: 'vite-plugin-html-include',
    transformIndexHtml: {
      order: 'pre',
      handler(html, ctx) {
        return html.replace(INCLUDE_RE, (match, includePath) => {
          const absPath = pathResolve(dirname(ctx.filename), includePath.trim())
          try {
            return readFileSync(absPath, 'utf-8')
          } catch (err) {
            console.warn(
              `[vite-plugin-html-include] Could not include "${includePath}" ` +
              `from "${ctx.filename}": ${err.message}`
            )
            return match
          }
        })
      }
    }
  }
}

export default defineConfig({
  plugins: [vitePluginHtmlInclude()],
  root: 'src',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'src/index.html'),
        landing: resolve(__dirname, 'src/landing.html'),
      },
    },
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