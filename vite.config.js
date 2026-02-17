import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: {http: "https://smee.io/QXLOiYoGt4PsGcW", https: "https://smee.io/QXLOiYoGt4PsGcW"},
    allowedHosts: ["webhook.site/7177ff7c-484e-498c-abe9-1320a1219ffa"]
  }
})
