import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import Unocss from 'unocss/vite'
import * as path from "node:path";

// https://vite.dev/config/
export default defineConfig({
    plugins: [vue(), Unocss()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, 'src')
        }
    }
})
