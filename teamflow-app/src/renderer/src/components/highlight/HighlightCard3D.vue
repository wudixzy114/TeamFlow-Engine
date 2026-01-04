<!-- src/components/highlights/HighlightCard3D.vue -->
<script lang="ts" setup>
import {computed} from 'vue'
import {useHighlightsStore} from "@/stores/highlights";

const props = defineProps<{
  highlight: HighlightSingle
  isActive: boolean
}>()

const store = useHighlightsStore()
const userName = computed(() => props.highlight.user?.username || props.highlight.user?.nickname || 'Anonymous')
const userInitial = computed(() => userName.value[0]?.toUpperCase() || 'U')
const commentsCount = computed(() => {
  const comments = store.commentsMap[props.highlight.id]
  return comments ? comments.length : 0
})

const truncatedContent = (text: string) => {
  if (!text) return ''
  return text.length > 50 ? text.substring(0, 50) + '...' : text
}
</script>

<template>
  <div
    :class="[
      isActive
        ? 'bg-primary/20 border-primary shadow-[0_0_30px_rgba(var(--c-primary),0.6)] scale-110 z-50'
        : 'bg-bg-card/40 border-white/10 hover:bg-bg-card/70 hover:border-white/30 hover:scale-105'
    ]"
    class="
      group relative w-[280px] p-5 cursor-pointer select-none
      rounded-2xl border transition-all duration-500
      flex flex-col gap-3
    "
    style="backdrop-filter: blur(8px);"
  >
    <!-- 发光边缘 -->
    <div
      class="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>

    <!-- 用户头像与信息 -->
    <div class="flex items-center gap-3">
      <div
        class="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-secondary flex-center text-xs font-bold text-white shadow-inner">
        {{ userInitial }}
      </div>
      <div class="flex flex-col">
        <span class="text-xs font-medium text-text-main">{{ userName }}</span>
        <span class="text-[10px] text-text-muted">{{ new Date(highlight.created_at).toLocaleDateString() }}</span>
      </div>
    </div>

    <!-- 内容预览 -->
    <div class="text-sm text-text-main leading-relaxed font-light break-words">
      {{ truncatedContent(highlight.content) }}
    </div>

    <!-- 底部数据栏 -->
    <div class="flex items-center gap-4 text-xs text-text-muted mt-1">
      <div class="flex items-center gap-1">
        <div :class="highlight.liked_by_current_user ? 'text-rose-500' : ''">
          <div v-if="highlight.liked_by_current_user" class="i-carbon-favorite-filled"></div>
          <div v-else class="i-carbon-favorite"></div>
        </div>
        <span>{{ highlight.likes_count }}</span>
      </div>
      <div class="flex items-center gap-1 hover:text-primary transition-colors">
        <div class="i-carbon-chat"></div>
        <span>{{ commentsCount }}</span>
      </div>
    </div>
  </div>
</template>
