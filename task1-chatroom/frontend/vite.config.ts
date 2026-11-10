import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const backendUrl = loadEnv(mode, '.', 'RELAY_').RELAY_BACKEND_URL || 'http://127.0.0.1:8000'
  return {
  plugins: [react(), tailwindcss()],
  server: { proxy: {
    '/api': backendUrl,
    '/ws': { target: backendUrl, ws: true },
  } },
  preview: { proxy: {
    '/api': backendUrl,
    '/ws': { target: backendUrl, ws: true },
  } },
  }
})
