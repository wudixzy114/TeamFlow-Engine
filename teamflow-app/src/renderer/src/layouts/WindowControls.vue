<!-- src/components/layout/WindowControls.vue -->
<script lang="ts" setup>
import ThemeSwitcher from '@/components/theme/ThemeSwitcher.vue'
import {ref, onMounted, onUnmounted} from 'vue'

const isMaximized = ref(false)

const checkInitialState = async () => {
  if (window.layout?.isMaximized) {
    isMaximized.value = await window.layout.isMaximized()
  }
}
const minimizeWindow = () => window.layout?.minimize()
const closeWindow = () => window.layout?.close()
const toggleMaximize = () => {
  window.layout?.maximize()
  isMaximized.value = !isMaximized.value
}

let cleanupListener: (() => void) | undefined
onMounted(() => {
  checkInitialState()
  if (window.layout?.onWindowStateChange) {
    cleanupListener = window.layout.onWindowStateChange((state) => {
      isMaximized.value = state === 'maximized'
    })
  }
})
onUnmounted(() => {
  if (cleanupListener) cleanupListener()
})
</script>

<template>
  <div class="fixed top-0 right-0 p-4 z-50 flex items-center gap-2 no-drag">
    <!-- 主题切换 (可选，登录页可能也想换肤) -->
    <ThemeSwitcher/>

    <!-- 分隔线 -->
    <div class="h-4 w-[1px] bg-white/20 mx-1"></div>

    <!-- 最小化 -->
    <button
      class="w-8 h-8 flex-center rounded-lg hover:bg-white/10 text-white/70 hover:text-white transition-colors"
      title="Minimize"
      @click="minimizeWindow"
    >
      <div class="i-carbon-subtract text-lg"></div>
    </button>

    <!-- 最大化 -->
    <button
      :title="isMaximized ? 'Restore' : 'Maximize'"
      class="w-8 h-8 flex-center rounded-lg hover:bg-white/10 text-white/70 hover:text-white transition-colors overflow-hidden relative"
      @click="toggleMaximize"
    >
      <div v-if="!isMaximized" class="i-carbon-maximize text-lg"></div>
      <div v-else class="i-carbon-shrink-screen text-lg"></div>
    </button>

    <!-- 关闭 -->
    <button
      class="w-8 h-8 flex-center rounded-lg hover:bg-red-500/80 text-white/70 hover:text-white transition-colors"
      title="Close"
      @click="closeWindow"
    >
      <div class="i-carbon-close text-lg"></div>
    </button>
  </div>
</template>
