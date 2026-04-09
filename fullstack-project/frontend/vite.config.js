import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const backendHost = process.env.BACKEND_HOST || 'localhost'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/user': `http://${backendHost}:8000`,
      '/restaurant': `http://${backendHost}:8000`,
      '/cart': `http://${backendHost}:8000`,
      '/order': `http://${backendHost}:8000`,
      '/payment': `http://${backendHost}:8000`,
      '/receipt': `http://${backendHost}:8000`,
      '/delivery': `http://${backendHost}:8000`,
      '/promo': `http://${backendHost}:8000`,
      '/admin': `http://${backendHost}:8000`,
      '/config': `http://${backendHost}:8000`,
      '/ws': { target: `ws://${backendHost}:8000`, ws: true },
    },
  },
})
