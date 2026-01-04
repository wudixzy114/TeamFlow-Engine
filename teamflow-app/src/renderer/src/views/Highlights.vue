<!-- src/views/HighlightsView.vue -->
<script lang="ts" setup>
import {ref, onMounted} from 'vue'
import {useHighlightsStore} from '@/stores/highlights'
import HighlightsGalaxy from '@/components/highlight/HighlightsGalaxy.vue'
import HighlightDetail from '@/components/highlight/HighlightDetail.vue'
import HighlightLauncher from '@/components/highlight/HighlightLauncher.vue'

const store = useHighlightsStore()
const activeHighlightId = ref<string | null>(null)

onMounted(() => {
  store.fetchHighlights()
})

const handleSelect = (id: string) => {
  activeHighlightId.value = id
}

const handleCloseDetail = () => {
  activeHighlightId.value = null
}
</script>

<template>
  <div class="relative w-full h-full bg-bg-main overflow-hidden">

    <!-- 1. 顶层 UI (Overlay) -->
    <div class="absolute top-0 left-0 w-full z-10 pointer-events-none p-8 pt-20 flex justify-between items-start">
      <div class="flex flex-col gap-2 pointer-events-auto">
        <h1 class="text-4xl font-bold tracking-tight text-white drop-shadow-lg">
          Galaxy <span class="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">Moments</span>
        </h1>
        <p class="text-text-muted/80 max-w-md text-sm glass-panel px-4 py-2 mt-2 border-l-4 border-l-primary">
          Explore the collective memories of the team. Each star is a thought, connected in the void.
        </p>
      </div>

      <!-- 右上角工具栏：只保留刷新，新建功能移到底部 -->
      <div class="pointer-events-auto flex gap-3">
        <button
          class="btn-ghost border border-white/10 bg-bg-card/50 backdrop-blur text-white hover:rotate-180 transition-transform duration-700"
          title="Refresh Galaxy"
          @click="store.fetchHighlights()"
        >
          <div :class="store.isLoading ? 'animate-spin' : ''" class="i-carbon-renew text-xl"></div>
        </button>
      </div>
    </div>

    <!-- 2. 3D 场景层 -->
    <div class="absolute inset-0 z-0">
      <HighlightsGalaxy
        :active-id="activeHighlightId"
        @select="handleSelect"
      />
    </div>

    <!-- 3. 详情侧边栏 -->
    <HighlightDetail
      :highlight-id="activeHighlightId"
      @close="handleCloseDetail"
    />

    <!-- 4. 底部发射框 (替代原有的弹窗) -->
    <HighlightLauncher/>

    <!-- 加载状态 -->
    <div v-if="store.isLoading && store.highlights.length === 0" class="absolute inset-0 flex-center z-50 bg-bg-main">
      <div class="col-center gap-4">
        <!-- 简单的呼吸灯效果 -->
        <div class="relative flex-center">
          <div class="absolute w-16 h-16 bg-primary/20 rounded-full animate-ping"></div>
          <div class="relative w-8 h-8 bg-primary rounded-full shadow-[0_0_20px_rgba(var(--c-primary),0.8)]"></div>
        </div>
        <span
          class="text-text-muted animate-pulse font-mono tracking-widest text-xs uppercase">Initializing System...</span>
      </div>
    </div>
  </div>
</template>
