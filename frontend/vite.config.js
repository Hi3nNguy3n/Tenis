import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    cssCodeSplit: true,
    sourcemap: false,
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('vue') || id.includes('vue-router') || id.includes('pinia') || id.includes('vue-i18n')) {
              return 'vendor-vue'
            }
            if (id.includes('element-plus') || id.includes('@element-plus/icons-vue')) {
              return 'vendor-element'
            }
            if (id.includes('quill') || id.includes('@vueup/vue-quill')) {
              return 'vendor-editor'
            }
          }
        },
      },
    },
  },
})
