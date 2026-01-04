<!-- src/components/share/MarkdownReader.vue -->
<script lang="ts" setup>
import {computed} from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
// noinspection TypeScriptCheckImport
import taskLists from 'markdown-it-task-lists'
import {usePreferencesStore} from '@/stores/markdown/preferences'

const props = defineProps<{
  content: string
}>()

const prefStore = usePreferencesStore()

// 配置 Markdown 解析器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: (str, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs-container"><code>${hljs.highlight(str, {
          language: lang,
          ignoreIllegals: true
        }).value}</code></pre>`
      } catch (__) {
      }
    }
    return `<pre class="hljs-container"><code>${md.utils.escapeHtml(str)}</code></pre>`
  }
}).use(taskLists, {label: true, labelAfter: true})

// 渲染 HTML
const renderedHtml = computed(() => md.render(props.content || ''))

// 处理链接点击（防止 Electron 内部跳转）
const handleLinkClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  const link = target.closest('a')
  if (link) {
    const href = link.getAttribute('href')
    if (href && !href.startsWith('#')) {
      e.preventDefault()
      window.open(href, '_blank')
    }
  }
}
</script>

<template>
  <div
    :data-md-theme="prefStore.markdownTheme"
    class="markdown-preview-container transition-colors duration-300 relative"
  >
    <!-- 背景装饰 (仅在 Default 主题显示) -->
    <div v-if="prefStore.markdownTheme === 'default'" class="absolute inset-0 pointer-events-none z-0 overflow-hidden">
      <div
        class="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 blur-[120px] rounded-full mix-blend-screen opacity-50"></div>
      <div
        class="absolute bottom-0 left-0 w-[300px] h-[300px] bg-secondary/5 blur-[100px] rounded-full mix-blend-screen opacity-30"></div>
      <div class="absolute inset-0 bg-grid-pattern opacity-10"></div>
    </div>

    <!-- 内容区域 -->
    <div class="relative z-10">
      <div
        class="prose-content"
        @click="handleLinkClick"
        v-html="renderedHtml"
      ></div>
    </div>
  </div>
</template>
