import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

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
})