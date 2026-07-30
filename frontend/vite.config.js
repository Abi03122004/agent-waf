import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/agent': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/metrics': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/audit': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/rules': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/dashboard/ws': {
        target: 'ws://127.0.0.1:8001',
        ws: true,
        changeOrigin: true,
      },
    },
  },
});
