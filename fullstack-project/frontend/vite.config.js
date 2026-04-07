import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/user': 'http://localhost:8000',
      '/restaurant': 'http://localhost:8000',
      '/cart': 'http://localhost:8000',
      '/order': 'http://localhost:8000',
      '/payment': 'http://localhost:8000',
      '/receipt': 'http://localhost:8000',
      '/delivery': 'http://localhost:8000',
      '/promo': 'http://localhost:8000',
      '/admin': 'http://localhost:8000',
      '/config': 'http://localhost:8000',
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
})
