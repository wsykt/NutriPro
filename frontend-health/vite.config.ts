import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.ts']
  },
  build: {
    rollupOptions: {
      output: {
        // 第三方库按 vendor 拆 chunk，长缓存友好
        manualChunks(id: string) {
          if (id.includes('node_modules/echarts')) return 'echarts-vendor'
          if (id.includes('node_modules/@amap')) return 'amap-vendor'
          if (id.includes('node_modules/vue') || id.includes('node_modules/pinia') || id.includes('node_modules/vue-router')) return 'vue-vendor'
        }
      }
    }
  },
  server: {
    host: '127.0.0.1',
    // 端口由 package.json 的 --port 5173 统一指定，此处不再重复定义
    open: false,
    proxy: {
      '/api': {
        target: 'http://localhost:8082',
        changeOrigin: true
      }
    }
  }
})
