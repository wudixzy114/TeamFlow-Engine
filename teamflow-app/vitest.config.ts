import {defineConfig} from 'vitest/config';
import path from 'path';
import vue from '@vitejs/plugin-vue';
import AutoImport from 'unplugin-auto-import/vite';

export default defineConfig({
  plugins: [
    vue(),
    // AutoImport 最好加上，因为你的业务代码（Store 等）可能依赖它的自动导入
    AutoImport({
      imports: ['vue', 'vue-router', 'pinia', '@vueuse/core'],
      dts: false, // 测试时不生成 d.ts
      // 确保这里的 dirs 路径与你项目实际路径匹配
      dirs: [
        path.resolve(__dirname, 'src/renderer/src/composables'),
        path.resolve(__dirname, 'src/renderer/src/stores')
      ],
    }),
  ],
  test: {
    environment: 'happy-dom', // 模拟浏览器环境
    globals: true, // 允许直接使用 describe, it, expect 而不需要 import
    include: ['src/renderer/src/tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'], // 指定测试文件位置
  },
  resolve: {
    alias: {
      // 关键：手动复刻 electron-vite.config.ts renderer 部分的 alias
      '@': path.resolve(__dirname, 'src/renderer/src'),
      '#': path.resolve(__dirname, 'src')
    }
  }
});
