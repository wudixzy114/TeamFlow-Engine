import {defineConfig, presetAttributify, presetIcons, presetWebFonts} from 'unocss'
import presetWind4 from '@unocss/preset-wind4'

// ⚡️ 核心工具：自动生成透明度阶梯
const createColor = (name: string) => {
  const varName = `--c-${name}`
  const colors: Record<string, string> = {
    DEFAULT: `rgb(var(${varName}))`,
  }
  // 0-100 透明度
  for (let i = 0; i <= 100; i += 5) {
    colors[i] = `rgb(var(${varName}) / ${i / 100})`
  }
  // 常用断点
  colors['33'] = `rgb(var(${varName}) / 0.33)`
  colors['66'] = `rgb(var(${varName}) / 0.66)`
  return colors
}

export default defineConfig({
  presets: [
    presetWind4(),
    presetAttributify(),
    presetIcons({scale: 1.2, cdn: 'https://esm.sh/'}),
    presetWebFonts({
      // ✅ 修复：移除了非法 URL 参数。
      // OpenType 特性 (cv11, cv05) 已在 style.css 的 body 中通过 font-feature-settings 开启
      fonts: {
        sans: 'Inter:400,500,600,700',
        mono: 'JetBrains Mono:400,600',
      },
    }),
  ],
  content: {
    pipeline: {
      include: ['./src/**/*.{vue,js,ts,jsx,tsx}'],
    }
  },
  theme: {
    colors: {
      // 背景
      bg: createColor('bg-main'),       // class="bg-bg"
      card: createColor('bg-card'),     // class="bg-card"
      surface: createColor('bg-surface'),// class="bg-surface"

      // 品牌
      primary: createColor('primary'),
      'primary-hover': createColor('primary-hover'),
      'primary-active': createColor('primary-active'),

      secondary: createColor('secondary'),
      accent: createColor('accent'),

      // 状态
      success: createColor('success'),
      warning: createColor('warning'),
      error: createColor('error'),

      // 文本
      // ✅ 优化命名，防止出现 text-text-muted 这种冗余
      text: createColor('text-main'),         // class="text-text" (主要文本)
      muted: createColor('text-muted'),       // class="text-muted" (次要文本)
      inverted: createColor('text-inverted'), // class="text-inverted" (反色文本)

      border: createColor('border'),
    },
    animation: {
      keyframes: {
        'slide-in-fast': '{ 0% { opacity: 0; transform: translateY(10px) scale(0.98); } 100% { opacity: 1; transform: translateY(0) scale(1); } }',
        'spin-slow': '{ from { transform: rotate(0deg); } to { transform: rotate(360deg); } }',
        'spin-reverse-slow': '{ from { transform: rotate(360deg); } to { transform: rotate(0deg); } }',
      },
      durations: {
        'slide-in-fast': '0.35s',
        'spin-slow': '12s',
        'spin-reverse-slow': '15s',
      },
      timingFns: {
        'slide-in-fast': 'cubic-bezier(0.2, 0.8, 0.2, 1)',
      },
    },
  },
  shortcuts: [
    ['glass-panel', 'bg-card/70 backdrop-blur-xl border border-border/10 rounded-2xl shadow-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] backdrop-blur-xl transform-gpu'],
    ['card-interactive', 'glass-panel transition-all duration-200 hover:-translate-y-1 hover:bg-surface/80 hover:border-primary/50 hover:shadow-[0_0_20px_rgb(var(--c-primary)/0.3)] cursor-pointer'],
    ['btn-primary', 'btn-base bg-gradient-to-br from-primary to-primary-active text-inverted shadow-lg hover:shadow-[0_0_20px_rgb(var(--c-primary)/0.3)] hover:brightness-110 border border-white/10'],
    ['input-base', 'w-full bg-surface/50 border border-border/20 rounded-lg px-4 py-2.5 text-text outline-none focus:border-primary/80 focus:shadow-[0_0_10px_rgb(var(--c-primary)/0.2)] transition-all placeholder:text-muted/40 tabular-nums'],
    ['animate-enter', 'animate-slide-in-fast animate-fill-both'],
    ['flex-center', 'flex items-center justify-center'],
    ['flex-between', 'flex items-center justify-between'],
    ['col-center', 'flex flex-col items-center justify-center'],
    ['btn-base', 'px-5 py-2 rounded-lg font-medium transition-all duration-200 active:scale-95 flex-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none text-sm tracking-wide'],
    ['btn-outline', 'btn-base bg-transparent border border-border/30 text-text hover:bg-surface hover:border-primary/50 hover:text-primary'],
    ['btn-ghost', 'btn-base bg-transparent text-muted hover:text-text hover:bg-surface/50'],
    // Typography
    ['text-gradient', 'bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary font-bold'],
    ['text-h1', 'text-3xl md:text-4xl font-bold text-text tracking-tight leading-tight'],
    ['text-h2', 'text-xl font-semibold text-text tracking-tight'],

    ['flux-core', 'relative flex-center w-64 h-64'],
    ['flux-ring', 'absolute rounded-full border border-primary/30 shadow-[0_0_15px_rgb(var(--c-primary)/0.2)] backdrop-blur-sm'],
  ],
  rules: [
    ['bg-grid-pattern', {
      'background-image': 'linear-gradient(to right, rgb(var(--c-border) / 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgb(var(--c-border) / 0.05) 1px, transparent 1px)',
      'background-size': '40px 40px',
      'mask-image': 'linear-gradient(to bottom, black 40%, transparent 100%)'
    }],
    ['scrollbar-hide', {
      'scrollbar-width': 'none',
      '-ms-overflow-style': 'none',
    }],
  ],
})
