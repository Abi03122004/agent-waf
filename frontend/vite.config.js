import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const backendTarget = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';
const wsTarget = backendTarget.replace(/^http/, 'ws');

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/agent': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/metrics': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/audit': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/rules': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/dashboard/ws': {
        target: wsTarget,
        ws: true,
        changeOrigin: true,
      },
    },
  },
});
