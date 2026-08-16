import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'
import { fileURLToPath } from 'url'
import {
  PWA_PRECACHE_GLOB_IGNORES,
  PWA_PRECACHE_GLOB_PATTERNS,
} from './src/pwa/precacheContract.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const pwaE2eEnabled = mode === 'pwa-e2e'
  const pwaTestVersion = pwaE2eEnabled
    ? process.env.FEEDGO_PWA_TEST_VERSION || 'harness'
    : 'production'

  return {
  define: {
    __FEEDGO_PWA_E2E__: JSON.stringify(pwaE2eEnabled),
    __FEEDGO_PWA_TEST_VERSION__: JSON.stringify(pwaTestVersion),
  },
  plugins: [
    react(),
    VitePWA({
      strategies: 'injectManifest',
      srcDir: 'src/pwa',
      filename: 'service-worker.js',
      injectRegister: false,
      manifest: false,
      injectManifest: {
        globPatterns: [...PWA_PRECACHE_GLOB_PATTERNS],
        globIgnores: [...PWA_PRECACHE_GLOB_IGNORES],
      },
      devOptions: {
        enabled: false,
      },
    }),
  ],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),

      // CORE
      '@core': path.resolve(__dirname, './src/core'),

      // FEATURES
      '@features': path.resolve(__dirname, './src/features'),

      // SHARED
      '@shared': path.resolve(__dirname, './src/shared'),

      // LAYOUTS
      '@layouts': path.resolve(__dirname, './src/layouts'),

      // LEGACY TEMPORAL
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@services': path.resolve(__dirname, './src/services'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@context': path.resolve(__dirname, './src/context'),
      '@router': path.resolve(__dirname, './src/router'),
    },
  },
  }
})
