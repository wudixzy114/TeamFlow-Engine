<!--suppress HtmlUnknownTag -->
<script lang="ts" setup>
import {useP2PStore} from '@/stores/p2p'
import {storeToRefs} from 'pinia'
import {ref, computed} from 'vue'

const p2pStore = useP2PStore()
const {downloadList} = storeToRefs(p2pStore)
const isExpanded = ref(false)

const activeDownloads = computed(() => downloadList.value.filter(d => d.status === 'downloading').length)
</script>

<template>
  <div class="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3 font-sans">
    <!-- Panel -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="translate-y-4 opacity-0 scale-95"
      enter-to-class="translate-y-0 opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="translate-y-0 opacity-100 scale-100"
      leave-to-class="translate-y-4 opacity-0 scale-95"
    >
      <div
        v-if="isExpanded && downloadList.length > 0"
        class="w-80 glass-panel shadow-2xl p-0 overflow-hidden flex flex-col"
      >
        <div class="px-4 py-3 border-b border-border/40 flex-between bg-bg-surface/30">
          <span class="text-xs font-bold text-text-main flex items-center gap-2">
            <div class="i-carbon-data-transfer-down"></div>
            传输任务
          </span>
          <button class="text-text-muted hover:text-text-main transition" @click="isExpanded = false">
            <div class="i-carbon-close"></div>
          </button>
        </div>

        <div class="max-h-64 overflow-y-auto p-2 space-y-1 scrollbar-hide bg-bg-card/50">
          <div v-for="task in downloadList" :key="task.fileId"
               class="hover:bg-bg-surface/50 rounded-lg p-2 transition-colors group">
            <div class="flex justify-between mb-1.5 items-center">
              <span :title="task.fileName" class="truncate text-xs text-text-main font-medium max-w-[180px]">
                {{ task.fileName }}
              </span>
              <span
                :class="task.status === 'completed' ? 'text-green-500 bg-green-500/10' : 'text-primary bg-primary/10'"
                class="text-[10px] font-mono px-1.5 py-0.5 rounded"
              >
                {{ task.status === 'completed' ? 'DONE' : `${task.progress}%` }}
              </span>
            </div>

            <!-- Progress Bar -->
            <div class="w-full h-1 bg-bg-surface rounded-full overflow-hidden">
              <div
                :class="task.status === 'completed' ? 'bg-green-500' : 'bg-primary shadow-glow-sm'"
                :style="{ width: `${task.progress}%` }"
                class="h-full transition-all duration-300 rounded-full"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Toggle Button -->
    <Transition name="fade">
      <button
        v-if="downloadList.length > 0"
        class="h-12 pl-4 pr-5 rounded-full bg-bg-card border border-border/50 text-text-main shadow-lg hover:shadow-glow-secondary flex-center gap-3 transition-all active:scale-95 group backdrop-blur-xl"
        @click="isExpanded = !isExpanded"
      >
        <div class="relative">
          <div class="i-carbon-cloud-download text-xl group-hover:text-primary transition-colors"></div>
          <span v-if="activeDownloads > 0"
                class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-primary rounded-full animate-ping"></span>
          <span v-if="activeDownloads > 0" class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-primary rounded-full"></span>
        </div>
        <div class="flex flex-col items-start leading-none">
          <span class="text-xs font-bold">{{ activeDownloads }} 进行中</span>
          <span class="text-[10px] text-text-muted">点击查看详情</span>
        </div>
      </button>
    </Transition>
  </div>
</template>
