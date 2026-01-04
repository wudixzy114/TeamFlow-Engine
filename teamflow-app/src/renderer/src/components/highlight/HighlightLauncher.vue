<!-- src/components/highlights/HighlightLauncher.vue -->
<!--suppress HtmlUnknownTag -->
<script lang="ts" setup>
import {ref, nextTick} from 'vue'
import {useHighlightsStore} from '@/stores/highlights'
import {useAuthStore} from '@/stores/auth' // 用于获取当前用户头像

const store = useHighlightsStore()
const authStore = useAuthStore()

const isOpen = ref(false)
const content = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

// 切换展开/收起
const toggleOpen = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => textareaRef.value?.focus())
  }
}

// 发射高光
const handleLaunch = async () => {
  if (!content.value.trim() || store.isSubmitting) return

  try {
    await store.addHighlight(content.value)
    // 发射成功的动画逻辑：清空 -> 收起
    content.value = ''
    isOpen.value = false
  } catch (e) {
    // 错误处理已在 store/api 层处理，这里可以选择保持打开状态让用户重试
  }
}

// 键盘快捷键
const handleKeydown = (e: KeyboardEvent) => {
  if (e.ctrlKey && e.key === 'Enter') {
    handleLaunch()
  } else if (e.key === 'Escape') {
    isOpen.value = false
  }
}

const userInitial = authStore.user?.nickname?.[0] || authStore.user?.username?.[0] || 'Me'
</script>

<template>
  <div class="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 flex flex-col items-center gap-4 w-full max-w-lg px-4">

    <!-- 发射控制台 (展开状态) -->
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0 translate-y-8 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 translate-y-8 scale-95"
    >
      <div
        v-if="isOpen"
        class="
          w-full glass-panel p-1.5 pl-4
          flex items-start gap-3
          shadow-[0_0_50px_rgba(var(--c-primary),0.2)]
          border border-primary/30
        "
      >
        <!-- 左侧：当前用户头像 (增加临场感) -->
        <div
          class="mt-2 w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex-center text-xs font-bold text-white shadow-inner flex-shrink-0">
          {{ userInitial }}
        </div>

        <!-- 中间：输入区域 -->
        <div class="flex-1 py-2">
          <textarea
            ref="textareaRef"
            v-model="content"
            class="w-full bg-transparent border-none outline-none text-text-main placeholder:text-text-muted/50 resize-none text-sm leading-relaxed scrollbar-hide"
            placeholder="Share a moment of focus or connection..."
            rows="3"
            @keydown="handleKeydown"
          ></textarea>
          <!-- 底部提示 -->
          <div class="flex justify-between items-center mt-1">
            <span class="text-[10px] text-text-muted/60">Markdown supported</span>
            <span class="text-[10px] text-text-muted/60">Ctrl + Enter to launch</span>
          </div>
        </div>

        <!-- 右侧：操作按钮 -->
        <div class="flex flex-col gap-1">
          <!-- 发射按钮 -->
          <button
            :disabled="!content.trim() || store.isSubmitting"
            class="w-10 h-10 rounded-xl bg-primary/20 hover:bg-primary text-primary hover:text-white transition-all duration-300 flex-center group relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
            title="Launch to Galaxy"
            @click="handleLaunch"
          >
            <!-- 正常图标 -->
            <div v-if="!store.isSubmitting" class="i-carbon-rocket text-xl group-hover:animate-bounce"></div>
            <!-- 加载动画 -->
            <div v-else class="i-carbon-circle-dash animate-spin text-xl"></div>

            <!-- 按钮光晕 -->
            <div class="absolute inset-0 bg-white/20 blur-lg opacity-0 group-hover:opacity-50 transition-opacity"></div>
          </button>

          <!-- 关闭按钮 -->
          <button
            class="w-10 h-10 rounded-xl bg-transparent hover:bg-bg-surface text-text-muted hover:text-text-main transition-colors flex-center"
            title="Cancel"
            @click="isOpen = false"
          >
            <div class="i-carbon-close text-lg"></div>
          </button>
        </div>
      </div>
    </Transition>

    <!-- 唤起按钮 (收起状态) -->
    <Transition
      enter-active-class="transition duration-300 delay-100"
      enter-from-class="opacity-0 scale-50"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-100"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-50"
    >
      <button
        v-if="!isOpen"
        class="
          group relative px-6 py-3 rounded-full
          bg-bg-card/80 backdrop-blur-md border border-white/10
          hover:border-primary/50 hover:bg-bg-surface
          shadow-lg hover:shadow-[0_0_20px_rgba(var(--c-primary),0.4)]
          transition-all duration-300
          flex items-center gap-3
        "
        @click="toggleOpen"
      >
        <span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
        <span class="text-sm font-medium text-text-main">Broadcast Signal</span>
        <div class="i-carbon-caret-up text-text-muted group-hover:-translate-y-0.5 transition-transform"></div>
      </button>
    </Transition>

  </div>
</template>
