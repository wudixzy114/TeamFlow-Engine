<!-- src/components/layout/AppHeader.vue -->
<!--suppress HtmlUnknownTag, CssUnusedSymbol -->
<script lang="ts" setup>
import ThemeSwitcher from '@/components/theme/ThemeSwitcher.vue'
import HeaderTeamSwitcher from '@/layouts/HeaderTeamSwitcher.vue'

defineProps<{
  transparent?: boolean
}>()
const checkInitialState = async () => {
  if (window.layout?.isMaximized) {
    isMaximized.value = await window.layout.isMaximized()
  }
}
const isMaximized = ref(false)
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
  <header
    :class="[
      transparent
        ? 'bg-transparent'  /* 沉浸模式：全透明 + 轻微模糊增强文字可读性 */
        : 'bg-bg-main/50 backdrop-blur-md border-b border-border/40' /* 标准模式：半透明背景 + 边框 */
    ]"
    class="
      h-14 flex items-center justify-between px-4 shrink-0
      titlebar-drag-region select-none
      transition-all duration-300
    "
  >
    <!-- Left: Breadcrumbs or Page Title (Optional) -->
    <div class="flex items-center gap-4 no-drag">
      <!-- 团队切换器 (核心修改点) -->
      <HeaderTeamSwitcher/>

      <!-- 预留插槽 (例如面包屑) -->
      <slot name="prefix"></slot>
    </div>

    <!-- Right: Actions & Window Controls -->
    <div class="flex items-center gap-2 no-drag">
      <!-- Theme Switcher -->
      <div class="mr-2">
        <ThemeSwitcher/>
      </div>

      <!-- Divider -->
      <div class="h-4 w-[1px] bg-border/40 mx-1"></div>

      <!-- Window Controls -->
      <button
        class="w-8 h-8 flex-center rounded-lg hover:bg-bg-surface text-text-muted hover:text-text-main transition-colors"
        @click="minimizeWindow">
        <div class="i-carbon-subtract text-lg"></div>
      </button>
      <button
        :title="isMaximized ? 'Restore' : 'Maximize'"
        class="w-8 h-8 flex-center rounded-lg hover:bg-bg-surface text-text-muted hover:text-text-main transition-colors overflow-hidden relative"
        @click="toggleMaximize"
      >
        <Transition mode="out-in" name="icon-fade">
          <div
            v-if="!isMaximized"
            key="maximize"
            class="i-carbon-maximize text-lg absolute"
          ></div>
          <div
            v-else
            key="restore"
            class="i-carbon-shrink-screen text-lg absolute"
          ></div>
        </Transition>
      </button>
      <button
        class="w-8 h-8 flex-center rounded-lg hover:bg-red-500/10 text-text-muted hover:text-red-500 transition-colors"
        @click="closeWindow">
        <div class="i-carbon-close text-lg"></div>
      </button>
    </div>
  </header>
</template>

<style scoped>
.icon-fade-enter-active,
.icon-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.icon-fade-enter-from {
  opacity: 0;
  transform: scale(0.8) rotate(-45deg);
}

.icon-fade-leave-to {
  opacity: 0;
  transform: scale(0.8) rotate(45deg);
}

/* 确保图标绝对定位居中，防止切换时布局跳动 */
.i-carbon-maximize,
.i-carbon-shrink-screen {
  /* Carbon 图标本质是 mask 或者 svg，block 布局更稳定 */
  display: block;
}
</style>
