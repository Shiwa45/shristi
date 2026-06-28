import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/design-studio/',
  plugins: [react()],
  server: {
    allowedHosts: ['rentable-antitrust-lining.ngrok-free.dev'],
    proxy: {
      // Forward Django API calls and media files to the Django dev server
      '/design-tool/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/orders': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
