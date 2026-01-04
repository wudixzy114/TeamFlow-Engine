<template>
  <!-- 容器：使用 glass-panel 预设类，Flex 布局确保头部和内容垂直排列 -->
  <div class="glass-panel flex flex-col relative overflow-hidden transition-all duration-300 hover:border-white/20">

    <!-- Header -->
    <div
      class="flex justify-between items-center px-6 py-4 border-b border-white/5 bg-gradient-to-r from-white/5 to-transparent">
      <h3 class="text-lg font-semibold text-white tracking-wide flex items-center gap-3">
        <!-- 装饰性高亮条，对应 'primary' 主色 -->
        <span class="w-1 h-5 rounded-full bg-primary shadow-[0_0_8px_rgba(6,182,212,0.6)]"></span>
        {{ title }}
      </h3>
      <!-- Extra 操作区 -->
      <div class="flex items-center gap-2 text-sm">
        <slot name="extra"/>
      </div>
    </div>

    <!-- Content -->
    <div class="relative flex-grow p-6 min-h-[300px]">
      <!-- Loading Overlay (替代 v-loading) -->
      <Transition name="fade">
        <div
          v-if="loading"
          class="absolute inset-0 z-20 flex items-center justify-center bg-bg-dark/60 backdrop-blur-sm rounded-b-2xl"
        >
          <div class="flex flex-col items-center gap-3">
            <!-- 使用 UnoCSS 图标作为加载 Spinner -->
            <div class="i-carbon-circle-dash animate-spin text-4xl text-primary shadow-glow-primary"></div>
            <span class="text-xs text-primary/80 font-mono tracking-widest uppercase animate-pulse">Processing</span>
          </div>
        </div>
      </Transition>

      <!-- Slot Content -->
      <!-- 当加载时，内容稍微模糊并降低透明度，制造景深感 -->
      <div :class="{ 'opacity-30 blur-[2px] pointer-events-none': loading }" class="transition-all duration-500 h-full">
        <slot/>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
defineProps<{
  title: string;
  loading?: boolean;
}>();
</script>

<style scoped>
/* 简单的淡入淡出过渡 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
