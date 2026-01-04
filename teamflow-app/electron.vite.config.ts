/// <reference types="vitest" />

import {resolve} from 'path'
import {defineConfig, externalizeDepsPlugin} from 'electron-vite'
import vue from '@vitejs/plugin-vue'
import Unocss from 'unocss/vite'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import Icons from 'unplugin-icons/vite';
import IconsResolver from 'unplugin-icons/resolver';
import {templateCompilerOptions} from "@tresjs/core";

// noinspection JSUnusedGlobalSymbols
export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()]
  },
  preload: {
    plugins: [externalizeDepsPlugin()]
  },
  renderer: {
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src/renderer/src'),
      }
    },
    plugins: [
      vue({
        ...templateCompilerOptions
      }),
      Unocss(),
      AutoImport({
        imports: [
          'vue',
          'vue-router',
          'pinia',
          '@vueuse/core', // 如果你使用了 VueUse，建议加上，没有可去掉
        ],
        dts: 'src/renderer/auto-imports.d.ts', // 生成类型声明文件，优化 TS 体验
        dirs: ['src/renderer/src/composables', 'src/renderer/src/stores'], // 自动导入这些目录下的导出
      }),
      Components({
        dirs: ['src/renderer/src/components'], // 自动导入该目录下的组件
        extensions: ['vue'],
        deep: true,
        dts: 'src/renderer/components.d.ts', // 生成组件类型声明
        resolvers: [
          // 仅保留图标解析器
          IconsResolver({
            prefix: 'i', // 使用方式: <i-mdi-home />
            enabledCollections: ['mdi', 'carbon', 'ph'], // 建议显式指定常用图标集，避免解析过多
          }),
        ]
      }),
      Icons({
        autoInstall: true,
        compiler: 'vue3',
        scale: 1.2,
      }),
    ],
    optimizeDeps: {
      include: ['echarts', 'gsap', 'axios']
    },
    build: {
      rollupOptions: {
        external: ['node-llama-cpp'],
        output: {
          manualChunks: {
            vendor: ['vue', 'vue-router', 'pinia', 'axios'],
            viz: ['echarts', 'gsap']
          }
        }
      }
    },
  },
})
