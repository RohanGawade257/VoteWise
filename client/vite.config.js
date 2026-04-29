import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const backendPort = env.VITE_BACKEND_PORT || '8080';

  return {
    plugins: [react()],
    server: {
      proxy: {
        // Proxy all /api requests to the backend in development.
        // Override port via VITE_BACKEND_PORT env var (e.g. in .env.local).
        '/api': {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
        }
      }
    }
  };
});

