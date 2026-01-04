<!--suppress HtmlUnknownTag -->
<script lang="ts" setup>
import {useP2PStore, type ExtendedPeer} from '@/stores/p2p'
import {storeToRefs} from 'pinia'

const p2pStore = useP2PStore()
const {sortedPeerList, activePeerId} = storeToRefs(p2pStore)

// --- 状态配置 ---
// 定义每种状态的视觉样式和文案
const statusConfig = {
  connected: {
    text: '已连接',
    class: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/20',
    dot: 'bg-emerald-500'
  },
  connecting: {
    text: '连接中',
    class: 'bg-amber-500/15 text-amber-500 border-amber-500/20',
    dot: 'bg-amber-500 animate-pulse'
  },
  online: {
    text: '在线',
    class: 'bg-primary/15 text-primary border-primary/20', // 使用主题色
    dot: 'bg-primary'
  },
  offline: {
    text: '离线',
    class: 'bg-text-muted/10 text-text-muted border-border/20',
    dot: 'bg-text-muted'
  }
}

// 获取 Peer 的当前状态配置
function getStatus(peer: ExtendedPeer) {
  return statusConfig[peer.status] || statusConfig.offline
}

// 处理删除确认
function handleDelete(e: Event, id: string) {
  e.stopPropagation() // 防止触发 selectPeer
  if (confirm('确定要移除该用户记录吗？这将同时删除聊天记录。')) {
    p2pStore.removePeer(id)
  }
}
</script>

<template>
  <div class="h-full flex flex-col bg-bg-card/30 border-r border-border/40 relative backdrop-blur-sm">

    <!-- 1. Header Area -->
    <div class="p-4 border-b border-border/40 flex-none bg-bg-main/50">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-lg font-bold tracking-tight text-text-main flex items-center gap-2">
          <div class="i-carbon-network-4 text-primary"></div>
          Connections
        </h2>
        <!-- 简单的计数器 Badge -->
        <span class="text-[10px] font-mono bg-bg-surface px-1.5 py-0.5 rounded border border-border/50 text-text-muted">
          {{ sortedPeerList.length }}
        </span>
      </div>

      <!-- 搜索或状态栏 (这里可以放一个小的搜索框，暂用状态描述代替) -->
      <div class="text-xs text-text-muted/80 truncate">
        发现局域网内的队友与设备
      </div>
    </div>

    <!-- 2. Peer List -->
    <div class="flex-1 overflow-y-auto p-2 space-y-2 scrollbar-hide">

      <!-- Empty State -->
      <div v-if="sortedPeerList.length === 0"
           class="flex flex-col items-center justify-center py-10 opacity-60 text-center">
        <div class="w-12 h-12 rounded-full bg-bg-surface flex-center mb-3 shadow-inner">
          <div class="i-carbon-radar text-2xl text-text-muted animate-pulse"></div>
        </div>
        <p class="text-sm font-medium text-text-main">雷达扫描中...</p>
        <p class="text-xs text-text-muted mt-1 px-4">
          等待其他设备加入同一局域网
        </p>
      </div>

      <!-- Peer Item -->
      <div
        v-for="peer in sortedPeerList"
        :key="peer.id"
        :class="[
          activePeerId === peer.id
            ? 'bg-bg-surface border-primary/40 shadow-glow-sm'
            : 'bg-transparent border-transparent hover:bg-bg-surface/60 hover:border-border/20'
        ]"
        class="group relative flex items-center gap-3 p-3 rounded-xl border transition-all duration-300 cursor-pointer select-none overflow-hidden"
        @click="p2pStore.selectPeer(peer.id)"
      >
        <!-- A. Avatar & Online Dot -->
        <div class="relative flex-none">
          <div
            :class="peer.status === 'offline' ? 'bg-text-muted grayscale' : 'bg-gradient-to-br from-primary to-secondary'"
            class="w-10 h-10 rounded-full flex-center text-sm font-bold text-text-inverted shadow-lg transition-transform duration-300 group-hover:scale-105"
          >
            {{ peer.username.slice(0, 2).toUpperCase() }}
          </div>

          <!-- 状态小圆点 (仅头像旁) -->
          <div
            :class="getStatus(peer).dot"
            class="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-bg-card transition-colors duration-300"
          ></div>
        </div>

        <!-- B. Info Section -->
        <div class="flex-1 min-w-0 flex flex-col gap-1">
          <!-- Top Row: Name & Icons -->
          <div class="flex items-center justify-between">
             <span
               :class="[
                 peer.status === 'offline' ? 'text-text-muted' : 'text-text-main',
                 activePeerId === peer.id ? 'font-bold' : 'font-medium'
               ]"
               class="text-sm truncate transition-colors"
             >
               {{ peer.username }}
             </span>

            <!-- Favorite Icon (Always visible if favorite, or on hover) -->
            <div
              v-if="peer.isFavorite"
              class="i-carbon-star-filled text-xs text-accent mr-1"
            ></div>
          </div>

          <!-- Bottom Row: Explicit Status Badge & IP -->
          <div class="flex items-center gap-2">
            <!-- 明确的状态文字 Pill -->
            <div
              :class="getStatus(peer).class"
              class="text-[9px] px-1.5 py-0.5 rounded-[4px] border uppercase font-bold tracking-wider"
            >
              {{ getStatus(peer).text }}
            </div>

            <span class="text-[10px] text-text-muted font-mono truncate opacity-60">
              {{ peer.ip }}
            </span>
          </div>
        </div>

        <!-- C. Action Menu (Hover Only) -->
        <!-- 使用 absolute positioning 覆盖在右侧，悬浮时显示 -->
        <div
          class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-bg-surface/90 backdrop-blur px-1 py-1 rounded-lg border border-border/30 shadow-lg">

          <!-- Star Btn -->
          <button
            :title="peer.isFavorite ? '取消收藏' : '收藏用户'"
            class="p-1.5 rounded-md hover:bg-bg-card text-text-muted hover:text-accent transition-colors"
            @click.stop="p2pStore.toggleFavorite(peer.id)"
          >
            <div :class="peer.isFavorite ? 'i-carbon-star-filled' : 'i-carbon-star'"></div>
          </button>

          <!-- Delete Btn -->
          <button
            class="p-1.5 rounded-md hover:bg-bg-card text-text-muted hover:text-red-500 transition-colors"
            title="移除记录"
            @click="handleDelete($event, peer.id)"
          >
            <div class="i-carbon-trash-can"></div>
          </button>
        </div>
      </div>
    </div>

    <!-- 3. Bottom Status Bar / My Info -->
    <div class="flex-none p-3 border-t border-border/40 bg-bg-surface/30">
      <div class="flex items-center gap-2 text-xs text-text-muted">
        <div class="i-carbon-circle-filled text-primary animate-pulse text-[8px]"></div>
        <span class="font-mono opacity-80">Discovery Service Running</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 针对不同主题的微调 */
</style>
