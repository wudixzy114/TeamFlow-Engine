<script lang="ts" setup>
import {onMounted} from 'vue'
import {useP2PStore} from '@/stores/p2p'
import PeerList from '@/components/p2p/PeerList.vue'
import ChatWindow from '@/components/p2p/ChatWindow.vue'
import FileSearch from '@/components/p2p/FileSearch.vue'
import DownloadManager from '@/components/p2p/DownloadManager.vue'

const p2pStore = useP2PStore()

onMounted(() => {
  p2pStore.startP2PService()
})
</script>

<template>
  <div class="h-full w-full bg-bg-main text-text-main flex flex-col overflow-hidden transition-colors duration-500">
    <!-- Main Content Area -->
    <div class="flex-1 flex overflow-hidden relative">

      <!-- Ambient Background Glow (Optional, nice for "Focus") -->
      <div
        class="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/5 blur-[120px] rounded-full pointer-events-none z-0"></div>
      <div
        class="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-secondary/5 blur-[120px] rounded-full pointer-events-none z-0"></div>

      <!-- Left Sidebar: Peers -->
      <!-- Added responsive classes: hidden on small screens unless toggled (logic omitted for brevity, keeping simple responsive) -->
      <aside
        class="w-80 flex-shrink-0 z-10 border-r border-border/40 backdrop-blur-xl bg-bg-card/30 hidden md:block transition-all duration-300">
        <PeerList/>
      </aside>

      <!-- Middle: Chat (Focus Area) -->
      <main class="flex-1 min-w-0 min-h-0 z-10 flex flex-col relative bg-bg-main/50 shadow-2xl">
        <ChatWindow/>
      </main>

      <!-- Right Sidebar: Search -->
      <aside class="w-96 flex-shrink-0 z-10 hidden xl:block transition-all duration-300">
        <FileSearch/>
      </aside>

      <!-- Overlays -->
      <DownloadManager/>

    </div>
  </div>
</template>
