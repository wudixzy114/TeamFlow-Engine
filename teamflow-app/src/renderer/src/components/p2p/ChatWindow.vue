<!--suppress HtmlUnknownTag -->
<script lang="ts" setup>
import {ref, nextTick, watch} from 'vue'
import {useP2PStore} from '@/stores/p2p'
import {useAuthStore} from '@/stores/auth'
import {storeToRefs} from 'pinia'

const p2pStore = useP2PStore()
const authStore = useAuthStore()
const {activePeer, currentChatMessages} = storeToRefs(p2pStore)

const inputMessage = ref('')
const chatContainerRef = ref<HTMLElement | null>(null)

// 自动滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
    }
  })
}

watch(currentChatMessages, scrollToBottom, {deep: true})
watch(activePeer, scrollToBottom)

const handleSend = () => {
  if (!inputMessage.value.trim()) return
  p2pStore.sendMessage(inputMessage.value)
  inputMessage.value = ''
}

const formatTime = (ts: number) => {
  return new Date(ts).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})
}
</script>

<template>
  <div class="h-full flex flex-col bg-bg-card/40 relative overflow-hidden">
    <!-- 背景纹理 -->
    <div class="absolute inset-0 bg-grid-pattern opacity-30 pointer-events-none"></div>

    <!-- Empty State -->
    <div v-if="!activePeer" class="flex-1 col-center text-text-muted z-10">
      <div class="w-24 h-24 rounded-full bg-bg-surface flex-center mb-6 shadow-glow-sm">
        <div class="i-carbon-connect text-6xl opacity-50 text-primary"></div>
      </div>
      <h3 class="text-h2 mb-2">建立连接</h3>
      <p class="opacity-60 text-sm">选择左侧伙伴开始心流协作</p>
    </div>

    <template v-else>
      <!-- Chat Header -->
      <header class="h-16 border-b border-border/40 flex-between px-6 bg-bg-card/60 backdrop-blur-md z-20">
        <div class="flex items-center gap-3">
          <div class="relative">
            <div class="w-2.5 h-2.5 rounded-full bg-primary shadow-glow animate-pulse"></div>
          </div>
          <div class="flex flex-col">
            <span class="font-semibold text-text-main tracking-wide leading-none">{{ activePeer.username }}</span>
            <span class="text-[10px] text-text-muted uppercase tracking-wider mt-1 opacity-70">P2P Direct Link</span>
          </div>
        </div>

        <div class="flex gap-2">
          <button class="btn-ghost p-2 rounded-full w-10 h-10" title="发送文件">
            <div class="i-carbon-document-add text-lg"></div>
          </button>
        </div>
      </header>

      <!-- Chat Messages Area -->
      <div
        ref="chatContainerRef"
        class="flex-1 min-h-0 overflow-y-auto p-6 space-y-6 scrollbar-hide z-10 overscroll-contain"
      >
        <div
          v-for="msg in currentChatMessages"
          :key="msg.id"
          :class="msg.senderId === authStore.user?.id ? 'justify-end' : 'justify-start'"
          class="flex w-full group"
        >
          <!-- Message Bubble -->
          <div class="flex flex-col max-w-[70%]">
            <div
              :class="[
                msg.senderId === authStore.user?.id
                  ? 'bg-gradient-to-br from-primary to-primary-active text-text-inverted rounded-2xl rounded-tr-sm shadow-md'
                  : 'bg-bg-surface border border-border/50 text-text-main rounded-2xl rounded-tl-sm shadow-sm'
              ]"
              class="p-4 relative transition-transform hover:scale-[1.01]"
            >
              <div class="text-sm leading-relaxed whitespace-pre-wrap font-sans">{{ msg.payload }}</div>
            </div>

            <!-- Metadata -->
            <div
              :class="msg.senderId === authStore.user?.id ? 'self-end' : 'self-start'"
              class="text-[10px] text-text-muted mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 px-1"
            >
              {{ formatTime(msg.timestamp) }}
              <span v-if="msg.senderId === authStore.user?.id" class="i-carbon-checkmark text-primary"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="flex-shrink-0 p-5 bg-bg-card/80 border-t border-border/40 backdrop-blur-md z-20">
        <div class="relative flex items-center gap-3">
          <div class="relative flex-1">
            <input
              v-model="inputMessage"
              class="input-base pr-12 h-12 rounded-2xl bg-bg-surface/50 hover:bg-bg-surface focus:bg-bg-surface transition-colors shadow-inner"
              placeholder="输入消息..."
              type="text"
              @keyup.enter="handleSend"
            />
            <div class="absolute right-3 top-3 text-text-muted/50 text-xs flex items-center gap-1 pointer-events-none">
              <span class="border border-border/50 rounded px-1">↵</span>
            </div>
          </div>

          <button
            :disabled="!inputMessage.trim()"
            class="w-12 h-12 rounded-2xl bg-primary text-text-inverted flex-center hover:shadow-glow hover:brightness-110 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            @click="handleSend"
          >
            <div class="i-carbon-send-alt text-xl"></div>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
