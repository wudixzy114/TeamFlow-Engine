<template>
  <!--
    修复点 1: 使用 min-h-0 防止 Flex 子元素溢出
    修复点 2: 颜色替换为语义变量
  -->
  <div class="h-full flex flex-col relative overflow-hidden bg-bg-main text-text-main">

    <!-- 顶部导航栏 -->
    <header class="h-16 flex-between px-6 border-b border-border/40 bg-bg-card/60 backdrop-blur-md z-10 flex-shrink-0">
      <div class="flex items-center gap-3">
        <div :class="aiStore.isSessionReady ? 'bg-green-500 shadow-glow-sm' : 'bg-amber-500 animate-pulse'"
             class="w-2.5 h-2.5 rounded-full transition-colors"></div>
        <div>
          <h2 class="text-text-main font-semibold tracking-wide leading-tight">AI Companion</h2>
          <p class="text-[10px] text-text-muted uppercase tracking-wider">
            {{ aiStore.currentModelName || 'Initializing...' }}</p>
        </div>
      </div>
      <div class="flex gap-2">
        <button class="btn-ghost text-xs py-1.5 px-3 rounded-lg" @click="aiStore.clearSession">
          <div class="i-carbon-trash-can mr-1.5"></div>
          Clear Context
        </button>
      </div>
    </header>

    <!-- 聊天内容区域 -->
    <!--
       修复点 3: 移除 ref="bottomRef" 相关的锚点，改为直接控制容器
       修复点 4: overscroll-contain 防止滚动链传播
    -->
    <div
      ref="chatContainer"
      class="flex-1 min-h-0 overflow-y-auto p-4 md:p-6 space-y-6 scrollbar-hide overscroll-contain"
    >

      <!-- 欢迎/空状态 -->
      <div v-if="aiStore.messages.length === 0" class="h-full col-center text-text-muted opacity-40">
        <div class="p-6 rounded-full bg-bg-surface mb-4">
          <div class="i-carbon-ibm-watson text-6xl text-primary"></div>
        </div>
        <p class="text-sm">Model loaded via node-llama-cpp</p>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="msg in aiStore.messages"
        :key="msg.id"
        :class="msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'"
        class="flex gap-4 max-w-4xl mx-auto w-full group"
      >
        <!-- 头像 -->
        <div
          :class="msg.role === 'user' ? 'bg-primary shadow-glow-sm' : 'bg-bg-surface border border-border/50'"
          class="w-9 h-9 rounded-lg flex-shrink-0 flex-center shadow-md transition-transform hover:scale-105"
        >
          <div
            :class="msg.role === 'user' ? 'i-carbon-user text-text-inverted' : 'i-carbon-machine-learning-model text-secondary'"></div>
        </div>

        <!-- 气泡 -->
        <div
          :class="[
            msg.role === 'user'
              ? 'bg-gradient-to-br from-primary to-primary-active text-text-inverted rounded-tr-none shadow-md'
              : 'glass-panel bg-bg-card/50 border-border/40 text-text-main rounded-tl-none shadow-sm'
          ]"
          class="relative px-5 py-3.5 rounded-2xl max-w-[85%] transition-all duration-200"
        >
          <!-- Markdown 内容渲染 -->
          <div
            v-if="msg.role === 'assistant'"
            class="markdown-body text-sm leading-relaxed"
            v-html="renderMarkdown(msg.content)"
          ></div>

          <!-- 用户消息纯文本 -->
          <div v-else class="text-sm leading-relaxed whitespace-pre-wrap font-medium">{{ msg.content }}</div>

          <!-- 正在输入的游标动画 -->
          <span v-if="msg.isStreaming"
                class="inline-block w-1.5 h-4 ml-1 bg-secondary align-middle animate-pulse rounded-full"></span>

          <!-- 元数据 -->
          <div
            :class="msg.role === 'user' ? 'right-0 text-white/50' : 'left-0 text-text-muted'"
            class="absolute -bottom-5 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2 text-[10px] font-mono px-1">
            <span>{{ new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}) }}</span>
          </div>
        </div>
      </div>

      <!-- 底部留白，方便查看最后一条消息 -->
      <div class="h-4"></div>
    </div>

    <!-- 输入区域 -->
    <div class="p-4 md:p-6 bg-gradient-to-t from-bg-main via-bg-main to-transparent z-10 flex-shrink-0">
      <div
        class="max-w-4xl mx-auto relative glass-panel p-1.5 flex items-end gap-2 transition-all duration-300 focus-within:border-primary/50 focus-within:shadow-glow-sm focus-within:bg-bg-surface/80">

        <!-- 输入框 -->
        <textarea
          v-model="input"
          :disabled="aiStore.isGenerating || !aiStore.isSessionReady"
          class="w-full bg-transparent border-none text-text-main placeholder-text-muted/40 focus:ring-0 resize-none py-3 px-4 max-h-[200px] scrollbar-hide text-sm"
          placeholder="Ask anything... (Enter to send)"
          rows="1"
          @keydown.enter.prevent="handleSend"
        ></textarea>

        <!-- 发送按钮 -->
        <button
          :disabled="!input.trim() || aiStore.isGenerating"
          class="h-9 w-9 rounded-lg bg-primary hover:bg-primary-hover active:bg-primary-active text-white flex-center transition-all disabled:opacity-50 disabled:cursor-not-allowed mb-1 mr-1 shadow-lg hover:shadow-glow"
          @click="handleSend"
        >
          <div v-if="aiStore.isGenerating" class="i-carbon-circle-dash animate-spin text-lg"></div>
          <div v-else class="i-carbon-send-filled text-lg"></div>
        </button>
      </div>

      <div class="text-center mt-2 text-[10px] text-text-muted/40 font-mono">
        Local LLM Execution • Privacy Protected
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref, onMounted, nextTick, watch} from 'vue'
import {useAiStore} from '@/stores/ai'
import MarkdownIt from 'markdown-it'

const aiStore = useAiStore()
const input = ref('')
const chatContainer = ref<HTMLElement | null>(null)
// const bottomRef = ref<HTMLElement | null>(null) // 删除它！

// 初始化 Markdown 解析器
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})

const renderMarkdown = (text: string) => {
  return md.render(text)
}

// 修复后的滚动逻辑：使用 scrollTop 而不是 scrollIntoView
const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
  nextTick(() => {
    if (!chatContainer.value) return

    // 直接设置 scrollTop 到最大高度
    chatContainer.value.scrollTo({
      top: chatContainer.value.scrollHeight,
      behavior: behavior
    })
  })
}

// 监听消息数量变化 (新消息开始) -> 平滑滚动
watch(() => aiStore.messages.length, () => {
  scrollToBottom('smooth')
})

// 监听流式输出变化 -> 即时滚动
watch(() => aiStore.messages[aiStore.messages.length - 1]?.content.length, () => {
  if (chatContainer.value) {
    const {scrollTop, scrollHeight, clientHeight} = chatContainer.value;

    // 只有当用户在底部附近时才自动滚动 (150px 容差)
    // 这样用户向上看历史记录时，AI输出不会强制把用户拉到底部
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 150

    if (isNearBottom) {
      // 流式输出使用 'auto' (瞬间跳转) 避免频繁的动画导致视觉抖动
      chatContainer.value.scrollTop = scrollHeight
    }
  }
})

const handleSend = async () => {
  const text = input.value
  if (!text.trim() || aiStore.isGenerating) return

  input.value = ''

  // 发送时立即滚动到底部
  scrollToBottom('smooth')

  await aiStore.sendMessage(text)
}

onMounted(() => {
  aiStore.initListener()
  if (!aiStore.isSessionReady) {
    aiStore.initSession()
  }
  // 挂载时如果有历史消息，瞬间滚到底部，不要动画
  if (aiStore.messages.length > 0) {
    scrollToBottom('auto')
  }
})
</script>

<style>
/* 确保 Markdown 样式跟随主题 */
.markdown-body {
  color: rgb(var(--c-text-main)); /* 使用 UnoCSS 定义的变量 */
  font-family: inherit;
}

.markdown-body p {
  margin-bottom: 0.75em;
}

.markdown-body p:last-child {
  margin-bottom: 0;
}

.markdown-body pre {
  background-color: rgba(var(--c-bg-card), 0.5) !important; /* 适配主题 */
  border-radius: 12px;
  padding: 16px;
  margin: 12px 0;
  overflow-x: auto;
  border: 1px solid rgba(var(--c-border), 0.3);
}

.markdown-body code {
  font-family: 'JetBrains Mono', monospace;
  background-color: rgba(var(--c-bg-surface), 0.8);
  color: rgb(var(--c-accent)); /* 代码高亮色 */
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 0.85em;
}

.markdown-body pre code {
  background-color: transparent;
  color: rgb(var(--c-text-main));
  padding: 0;
}

.markdown-body ul {
  list-style-type: disc;
  padding-left: 1.5em;
  margin-bottom: 0.5em;
}

.markdown-body strong {
  color: rgb(var(--c-primary)); /* 强调色 */
  font-weight: 600;
}
</style>
