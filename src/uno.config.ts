import {defineConfig, presetAttributify, presetIcons} from 'unocss'
import presetWind3 from '@unocss/preset-wind3'  // 新增导入

export default defineConfig({
    presets: [
        presetWind3(),
        presetAttributify(),
        presetIcons({
            scale: 1.2,
            warn: true,
        }),
    ],
    // 自定义规则或主题
    theme: {
        colors: {
            primary: '#4f46e5', // a nice indigo
            flow: '#2dd4bf', // teal for flow state
            anxiety: '#f97316', // orange for anxiety
            boredom: '#64748b', // slate for boredom
        }
    }
})