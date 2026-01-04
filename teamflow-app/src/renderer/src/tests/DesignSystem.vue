<!-- src/views/DesignSystem.vue -->
<script lang="ts" setup>
import {ref, onMounted} from 'vue'
import {Switch} from '@headlessui/vue' // 测试 HeadlessUI 集成

// 定义所有可用主题
const themes = [
  {name: 'Focus', value: ''}, // 默认 (空字符串或 root)
  {name: 'Connection', value: 'connection'},
  {name: 'Zen', value: 'zen'},
  {name: 'Clean (Light)', value: 'clean'},
  {name: 'Synthwave', value: 'synthwave'},
  {name: 'Abyss', value: 'abyss'},
]

const currentTheme = ref('')
const isEnabled = ref(false) // 用于测试 Headless UI 组件状态

// 切换主题逻辑
const setTheme = (theme: string) => {
  currentTheme.value = theme
  const html = document.documentElement
  if (theme) {
    html.setAttribute('data-theme', theme)
  } else {
    html.removeAttribute('data-theme')
  }
}

// 初始化
onMounted(() => {
  // 保持当前选中的主题
  const attr = document.documentElement.getAttribute('data-theme')
  if (attr) currentTheme.value = attr
})
</script>

<template>
  <div class="h-full w-full overflow-hidden flex flex-col bg-bg-main text-text-main transition-colors duration-500">
    <!-- 顶部控制栏: 拖拽区 -->
    <header
      class="titlebar-drag-region flex-between px-6 py-4 border-b border-border/10 bg-bg-card/50 backdrop-blur-md z-50">
      <div class="flex items-center gap-3">
        <div class="i-carbon-color-palette text-2xl text-primary animate-spin-slow"/>
        <h1 class="text-h2 font-bold tracking-tight">Design System Lab</h1>
      </div>

      <!-- 主题切换器 (No-Drag) -->
      <div class="no-drag flex gap-2 bg-bg-surface p-1 rounded-xl border border-border/20">
        <button
          v-for="t in themes"
          :key="t.value"
          :class="currentTheme === t.value
            ? 'bg-primary text-text-inverted shadow-glow-sm'
            : 'text-text-muted hover:text-text-main hover:bg-white/5'"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
          @click="setTheme(t.value)"
        >
          {{ t.name }}
        </button>
      </div>
    </header>

    <!-- 主内容滚动区 -->
    <main class="flex-1 overflow-y-auto p-8 relative scrollbar-hide">
      <!-- 背景网格测试 -->
      <div class="absolute inset-0 bg-grid-pattern opacity-50 pointer-events-none z-0"/>

      <div class="relative z-10 max-w-6xl mx-auto space-y-12 pb-20">

        <!-- 1. 色板测试 (Color Palette) -->
        <section class="animate-enter" style="animation-delay: 0ms">
          <h2 class="text-h2 mb-6 flex items-center gap-2">
            <span class="i-carbon-paint-brush text-primary"/> Colors & Variables
          </h2>
          <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            <!-- 封装一个简单的色块组件 -->
            <div class="space-y-2">
              <div class="h-20 w-full rounded-xl bg-bg-main border border-border flex-center shadow-lg">Bg Main</div>
              <p class="text-xs text-text-muted text-center font-mono">--c-bg-main</p>
            </div>
            <div class="space-y-2">
              <div class="h-20 w-full rounded-xl bg-bg-card border border-border flex-center shadow-lg">Bg Card</div>
              <p class="text-xs text-text-muted text-center font-mono">--c-bg-card</p>
            </div>
            <div class="space-y-2">
              <div
                class="h-20 w-full rounded-xl bg-primary border border-border/20 flex-center text-text-inverted font-bold shadow-glow">
                Primary
              </div>
              <p class="text-xs text-text-muted text-center font-mono">--c-primary</p>
            </div>
            <div class="space-y-2">
              <div
                class="h-20 w-full rounded-xl bg-secondary border border-border/20 flex-center text-text-inverted font-bold shadow-glow-secondary">
                Secondary
              </div>
              <p class="text-xs text-text-muted text-center font-mono">--c-secondary</p>
            </div>
            <div class="space-y-2">
              <div class="h-20 w-full rounded-xl bg-accent border border-border/20 flex-center text-black font-bold">
                Accent
              </div>
              <p class="text-xs text-text-muted text-center font-mono">--c-accent</p>
            </div>
          </div>
        </section>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">

          <!-- 2. 排版与文本 (Typography) -->
          <section class="animate-enter space-y-6" style="animation-delay: 100ms">
            <h2 class="text-h2 border-b border-border/20 pb-2">Typography</h2>
            <div class="space-y-4">
              <h1 class="text-h1">Heading 1: Focus & Connection</h1>
              <h2 class="text-h2">Heading 2: The Story of Us</h2>
              <p class="text-text-main leading-relaxed">
                Primary Body Text. 这是主要正文颜色。用于阅读体验。
                <span class="text-primary font-bold">Primary Color Text</span> represents focus.
              </p>
              <p class="text-text-muted text-sm">
                Muted Text. 这是次要文本，用于辅助说明。Should be lower contrast but readable.
              </p>
              <p class="text-gradient text-2xl font-bold">
                Gradient Text: Focus Flow
              </p>
            </div>
          </section>

          <!-- 3. 按钮与交互 (Buttons & Inputs) -->
          <section class="animate-enter space-y-6" style="animation-delay: 200ms">
            <h2 class="text-h2 border-b border-border/20 pb-2">Interaction</h2>

            <div class="flex flex-wrap gap-4 items-center">
              <button class="btn-primary">
                <span class="i-carbon-play-filled"/>
                Primary Action
              </button>
              <button class="btn-outline">
                <span class="i-carbon-settings"/>
                Settings
              </button>
              <button class="btn-ghost">
                <span class="i-carbon-close"/>
                Cancel
              </button>
              <button class="btn-primary opacity-50 cursor-not-allowed">
                Disabled
              </button>
            </div>

            <div class="space-y-3 max-w-md">
              <label class="text-sm font-medium text-text-muted">Input Field</label>
              <div class="relative">
                <span class="i-carbon-search absolute left-3 top-3 text-text-muted text-lg"></span>
                <input class="input-base pl-10" placeholder="Type to search..." type="text"/>
              </div>
            </div>

            <!-- Headless UI Integration Check -->
            <div class="flex items-center gap-4 p-4 rounded-xl bg-bg-surface border border-border/10">
              <span class="text-sm">Headless UI Switch:</span>
              <Switch
                v-model="isEnabled"
                :class="isEnabled ? 'bg-primary shadow-glow-sm' : 'bg-border/20 hover:bg-border/30'"
                class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none"
              >
                <span
                  :class="isEnabled ? 'translate-x-6' : 'translate-x-1'"
                  class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                />
              </Switch>
              <span class="text-xs text-text-muted">{{ isEnabled ? 'Active' : 'Inactive' }}</span>
            </div>
          </section>
        </div>

        <!-- 4. 卡片与特效 (Cards & Glass) -->
        <section class="animate-enter grid grid-cols-1 md:grid-cols-3 gap-6" style="animation-delay: 300ms">
          <!-- 普通磨砂卡片 -->
          <div class="glass-panel p-6 flex flex-col justify-between h-48">
            <div>
              <div class="i-carbon-cube text-3xl text-secondary mb-3"/>
              <h3 class="text-lg font-bold">Glass Panel</h3>
              <p class="text-text-muted text-sm mt-2">Standard backdrop-blur-xl with subtle border.</p>
            </div>
            <div class="text-xs text-border">Class: .glass-panel</div>
          </div>

          <!-- 交互卡片 -->
          <div class="card-interactive p-6 flex flex-col justify-between h-48 cursor-pointer group">
            <div>
              <div class="i-carbon-flash text-3xl text-accent mb-3 group-hover:scale-110 transition-transform"/>
              <h3 class="text-lg font-bold group-hover:text-primary transition-colors">Interactive Card</h3>
              <p class="text-text-muted text-sm mt-2">Hover me! Triggers glow, lift, and border change.</p>
            </div>
            <div class="text-xs text-border">Class: .card-interactive</div>
          </div>

          <!-- 动画演示区 -->
          <div class="glass-panel p-6 flex-center relative overflow-hidden h-48">
            <div class="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent pointer-events-none"/>

            <!-- Flux Core Animation -->
            <div class="flux-core scale-75">
              <div class="flux-ring w-full h-full animate-spin-slow"></div>
              <div class="flux-ring w-2/3 h-2/3 animate-spin-reverse-slow border-secondary/40"></div>
              <div class="absolute text-2xl font-bold tracking-widest text-text-main animate-pulse">
                FOCUS
              </div>
            </div>
          </div>
        </section>

      </div>
    </main>
  </div>
</template>

<style scoped>
/* 局部样式微调，如果需要的话 */
</style>
