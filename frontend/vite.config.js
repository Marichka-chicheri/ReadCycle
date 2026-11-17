import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // amazon-cognito-identity-js expects a Node-style `global`.
  define: { global: 'globalThis' },
  // When the repo lives on the Windows disk and `npm run dev` runs in WSL (/mnt/c/...),
  // file-change events do not reach Vite, so it keeps serving old files. Polling fixes that.
  server: { watch: { usePolling: true, interval: 300 } },
});
