<!--suppress HtmlUnknownTag -->
<script lang="ts" setup>
import {useP2PStore} from '@/stores/p2p'
import {storeToRefs} from 'pinia'

const p2pStore = useP2PStore()
const {searchQuery, isSearching, searchResults, sharedDir, sharedFileCount} = storeToRefs(p2pStore)

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}
</script>

<template>
  <div class="h-full flex flex-col bg-bg-card/30 backdrop-blur-md border-l border-border/40 w-96 relative">

    <!-- Header: Share Settings -->
    <div class="p-5 border-b border-border/40 bg-bg-card/50">
      <h3 class="text-xs font-bold text-text-muted uppercase tracking-wider mb-4 flex items-center gap-2">
        <div class="i-carbon-share-knowledge text-lg text-primary"></div>
        本地共享资源
      </h3>

      <div v-if="sharedDir" class="bg-bg-surface/50 border border-border/30 rounded-xl p-3">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2 overflow-hidden">
            <div class="i-carbon-folder text-secondary flex-shrink-0"></div>
            <span :title="sharedDir" class="text-xs text-text-main font-mono truncate">{{ sharedDir }}</span>
          </div>
        </div>
        <div class="flex items-center justify-between">
           <span class="text-[10px] text-text-muted bg-bg-card px-2 py-0.5 rounded-md border border-border/20">
             {{ sharedFileCount }} 个文件已索引
           </span>
          <button class="text-[10px] text-primary hover:underline hover:text-primary-hover"
                  @click="p2pStore.setSharedDirectory()">
            更改路径
          </button>
        </div>
      </div>

      <button
        v-else
        class="w-full py-3 rounded-xl border border-dashed border-border/50 text-text-muted text-xs hover:bg-bg-surface hover:border-primary/50 hover:text-text-main transition flex-center gap-2 group"
        @click="p2pStore.setSharedDirectory()"
      >
        <div class="i-carbon-add-alt group-hover:scale-110 transition-transform"></div>
        设置共享文件夹以开始
      </button>
    </div>

    <!-- Search Input -->
    <div class="p-5 pb-2">
      <div class="relative group">
        <input
          v-model="searchQuery"
          class="input-base pl-10 h-11 rounded-xl bg-bg-surface/50 focus:bg-bg-surface transition-all shadow-sm"
          placeholder="搜索全网资源..."
          type="text"
          @keyup.enter="p2pStore.performSearch()"
        />
        <div class="absolute left-3.5 top-3 text-text-muted group-focus-within:text-primary transition-colors">
          <div class="i-carbon-search text-lg"></div>
        </div>
        <div v-if="isSearching" class="absolute right-3.5 top-3 text-primary animate-spin">
          <div class="i-carbon-circle-dash text-lg"></div>
        </div>
      </div>
    </div>

    <!-- Results List -->
    <div class="flex-1 overflow-y-auto px-5 pb-5 space-y-3 scrollbar-hide">
      <div v-if="searchResults.length === 0 && !isSearching"
           class="flex flex-col items-center justify-center py-10 opacity-40 gap-3">
        <div class="i-carbon-search-locate text-4xl text-text-muted"></div>
        <span class="text-xs text-text-muted">输入关键词搜索局域网</span>
      </div>

      <div
        v-for="file in searchResults"
        :key="file.id"
        class="card-interactive p-3 rounded-xl border border-border/30 bg-bg-card/40 group flex items-center justify-between gap-3"
      >
        <div class="flex items-center gap-3 overflow-hidden">
          <!-- Icon -->
          <div
            class="w-10 h-10 rounded-lg bg-bg-surface border border-border/30 flex-center text-secondary shrink-0 group-hover:scale-105 transition-transform">
            <div class="i-carbon-document text-xl"></div>
          </div>

          <div class="min-w-0 flex flex-col gap-0.5">
            <div :title="file.name" class="text-sm text-text-main font-medium truncate">{{ file.name }}</div>
            <div class="text-[10px] text-text-muted flex items-center gap-2 font-mono">
              <span>{{ formatSize(file.size) }}</span>
              <span class="text-border">|</span>
              <span class="truncate max-w-[80px]">User: {{ file.ownerId?.substring(0, 4) }}</span>
            </div>
          </div>
        </div>

        <button
          class="btn-ghost p-0 w-8 h-8 rounded-full hover:bg-primary hover:text-text-inverted transition-all shrink-0"
          title="下载文件"
          @click="p2pStore.downloadFile(file)"
        >
          <div class="i-carbon-download"></div>
        </button>
      </div>
    </div>
  </div>
</template>
