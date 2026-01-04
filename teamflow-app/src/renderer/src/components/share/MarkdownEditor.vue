<!-- src/components/common/MarkdownEditor.vue -->
<template>
  <div class="flex flex-col h-full w-full relative min-h-0">

    <!-- 1. 工具栏 -->
    <div
      class="h-14 border-b border-border/40 bg-bg-surface/30 flex items-center px-4 justify-between shrink-0 gap-4 backdrop-blur-sm z-20">

      <!-- 左侧：基础工具 -->
      <div class="flex items-center gap-1.5 overflow-x-auto scrollbar-hide h-full py-2 flex-1">
        <template v-for="(tool, index) in editorTools" :key="index">
          <div v-if="tool.type === 'divider'" class="w-px h-5 bg-border/20 mx-1 shrink-0 self-center"></div>
          <button
            v-else
            class="group w-9 h-9 flex-center rounded-lg text-text-muted transition-all duration-200 outline-none
                   hover:bg-bg-surface hover:text-primary active:scale-95 active:bg-primary/10
                   focus-visible:ring-2 focus-visible:ring-primary/50 shrink-0"
            @blur="hideTooltip"
            @click="handleToolAction(tool)"
            @focus="showTooltip($event, tool)"
            @mouseenter="showTooltip($event, tool)"
            @mouseleave="hideTooltip"
          >
            <i :class="[tool.icon, 'text-lg transition-transform duration-300 group-hover:scale-110']"></i>
          </button>
        </template>
      </div>

      <!-- 右侧插槽：允许父组件注入额外按钮（如模板、保存等） -->
      <div class="flex items-center gap-3 shrink-0">
        <Menu as="div" class="relative inline-block text-left">
          <MenuButton
            class="w-9 h-9 flex-center rounded-lg text-text-muted hover:bg-bg-surface hover:text-primary transition-all active:scale-95 outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            title="切换阅读主题">
            <i class="i-carbon-color-palette text-lg"/>
          </MenuButton>

          <transition
            enter-active-class="transition duration-100 ease-out"
            enter-from-class="transform scale-95 opacity-0"
            enter-to-class="transform scale-100 opacity-100"
            leave-active-class="transition duration-75 ease-in"
            leave-from-class="transform scale-100 opacity-100"
            leave-to-class="transform scale-95 opacity-0"
          >
            <!-- 注意：origin-top-right 和 right-0，确保向左展开防止溢出屏幕 -->
            <MenuItems
              class="absolute right-0 mt-2 w-48 origin-top-right divide-y divide-border/20 rounded-xl bg-bg-card border border-border/50 shadow-glow-lg ring-1 ring-black/5 focus:outline-none z-50 overflow-hidden">
              <div class="px-1 py-1">
                <div class="px-2 py-1.5 text-[10px] text-text-muted uppercase tracking-wider font-mono opacity-80">
                  Preview Theme
                </div>
                <MenuItem v-for="theme in MD_THEMES" :key="theme.value" v-slot="{ active }">
                  <button
                    :class="[
                      active ? 'bg-primary/10 text-primary' : 'text-text-main',
                      'group flex w-full items-center rounded-lg px-2 py-2 text-xs transition-colors'
                    ]"
                    @click="prefStore.markdownTheme = theme.value"
                  >
                    <!-- 颜色预览圆点 -->
                    <span
                      :class="['w-3 h-3 rounded-full mr-2 border border-border/50 shadow-sm', theme.colorClass]"></span>
                    {{ theme.label }}
                    <!-- 选中状态勾选 -->
                    <i v-if="prefStore.markdownTheme === theme.value" class="i-carbon-checkmark ml-auto text-primary"/>
                  </button>
                </MenuItem>
              </div>
            </MenuItems>
          </transition>
        </Menu>
        <div class="w-px h-5 bg-border/20 mx-1"></div>
        <slot name="toolbar-extra"></slot>
      </div>
    </div>

    <!-- 2. 编辑区与预览区 -->
    <div class="flex-1 grid grid-cols-1 md:grid-cols-2 min-h-0 divide-x divide-border/40">

      <!-- 编辑输入框 (左) -->
      <div class="relative h-full bg-bg-main/30 group min-h-0 flex flex-col">
        <textarea
          ref="editorRef"
          :placeholder="placeholder"
          :value="modelValue"
          class="flex-1 w-full bg-transparent border-none p-6 text-sm font-mono text-text-main outline-none resize-none custom-scrollbar leading-relaxed selection:bg-primary/30 placeholder:text-text-muted/30 focus:bg-bg-surface/10 transition-colors duration-300"
          spellcheck="false"
          @input="onInput"
          @keydown.tab.prevent="insertTab"
        ></textarea>
        <!-- 聚焦光晕 -->
        <div
          class="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-0 transition-opacity peer-focus:opacity-100 pointer-events-none"></div>
      </div>

      <!-- 实时预览 (右) -->
      <!-- fix: 添加 min-h-0 确保 flex 子项能正确滚动 -->
      <div class="hidden md:flex flex-col h-full bg-bg-card/30 min-h-0">
        <!--
           theme container:
           1. data-md-theme 用于 CSS 样式隔离
           2. markdown-preview-container 用于过渡动画
           3. flex-1 overflow-y-auto 用于独立滚动
        -->
        <div
          :data-md-theme="prefStore.markdownTheme"
          class="flex-1 p-6 overflow-y-auto custom-scrollbar markdown-preview-container"
          @click="handlePreviewClick"
        >
          <div class="prose-content" v-html="renderedPreviewHtml"></div>
        </div>
      </div>
    </div>

    <!-- 3. 全局 Tooltip (Teleport) -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 translate-y-1 scale-95"
        enter-to-class="opacity-100 translate-y-0 scale-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100 translate-y-0 scale-100"
        leave-to-class="opacity-0 translate-y-1 scale-95"
      >
        <div
          v-if="tooltipState.visible"
          :style="{
            left: `${tooltipState.x}px`,
            top: `${tooltipState.y}px`,
            transform: 'translateX(-50%)'
          }"
          class="fixed z-[9999] px-3 py-1.5 bg-bg-card border border-border/50 text-text-main text-[11px] font-medium rounded-lg shadow-glow-lg flex items-center gap-2 pointer-events-none"
        >
          <span>{{ tooltipState.title }}</span>
          <span v-if="tooltipState.shortcut"
                class="text-[9px] text-text-muted bg-bg-surface px-1 rounded border border-border/30 font-mono">
            {{ tooltipState.shortcut }}
          </span>
          <div
            class="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-bg-card border-t border-l border-border/50 rotate-45"></div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<script lang="ts" setup>
import {ref, computed, nextTick, onBeforeUnmount} from 'vue';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
// noinspection TypeScriptCheckImport
import taskLists from 'markdown-it-task-lists';
// noinspection TypeScriptCheckImport
import linkAttributes from 'markdown-it-link-attributes';
import {Menu, MenuButton, MenuItems, MenuItem} from '@headlessui/vue';
import {usePreferencesStore} from '@/stores/markdown/preferences';

// --- Props & Emits ---
const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '# 开始编写...'
  }
});

const emit = defineEmits(['update:modelValue']);

// --- Theme Logic ---
const prefStore = usePreferencesStore();

const MD_THEMES = [
  {value: 'default', label: 'Default (Glass)', colorClass: 'bg-gray-500'},
  {value: 'github', label: 'GitHub Style', colorClass: 'bg-white'},
  {value: 'github-dark', label: 'GitHub Dark', colorClass: 'bg-[#0d1117] border border-gray-700'},
  {value: 'dracula', label: 'Dracula', colorClass: 'bg-[#282a36] border border-gray-600'},
  {value: 'notion', label: 'Notion Minimal', colorClass: 'bg-orange-50'},
  {value: 'solarized-light', label: 'Solarized Light', colorClass: 'bg-[#fdf6e3]'},
  {value: 'cobalt', label: 'Cobalt Blue', colorClass: 'bg-blue-900'},
];

// --- Setup Markdown ---
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
        }).value}</code></pre>`;
      } catch (__) {
      }
    }
    return `<pre class="hljs-container"><code>${md.utils.escapeHtml(str)}</code></pre>`;
  }
})
  .use(taskLists, {label: true, labelAfter: true})
  .use(linkAttributes, {
    // 核心：强制所有链接在新窗口打开，且添加安全属性
    attrs: {
      target: '_blank',
      rel: 'noopener noreferrer'
    }
  });

// --- State ---
const editorRef = ref<HTMLTextAreaElement | null>(null);
const renderedPreviewHtml = computed(() => md.render(props.modelValue || ''));

// --- Link Safety Interceptor ---
// 这是 Electron 中防止路由被劫持的关键
const handlePreviewClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  // 向上查找最近的 A 标签（防止点到 A 标签内的 i 或 span 没反应）
  const link = target.closest('a');

  if (link) {
    const href = link.getAttribute('href');
    // 如果是锚点链接 (#section)，允许默认行为（页面滚动）
    if (href && href.startsWith('#')) return;

    // 阻止默认行为（防止 Vue Router 接管或 Electron 内部跳转）
    e.preventDefault();

    if (href) {
      // 调用 window.open，这通常会被 Electron 的 setWindowOpenHandler 捕获
      // 从而在系统默认浏览器中打开
      window.open(href, '_blank');
    }
  }
};


// --- Tooltip Logic (Unchanged) ---
const tooltipState = ref({visible: false, x: 0, y: 0, title: '', shortcut: ''});
let tooltipTimer: ReturnType<typeof setTimeout> | null = null;

const showTooltip = (e: Event, tool: EditorTool) => {
  const target = e.currentTarget as HTMLElement;
  if (!target) return;
  const rect = target.getBoundingClientRect();
  if (tooltipTimer) clearTimeout(tooltipTimer);
  tooltipTimer = setTimeout(() => {
    tooltipState.value = {
      visible: true,
      x: rect.left + rect.width / 2,
      y: rect.bottom + 8,
      title: tool.title || '',
      shortcut: tool.shortcut || ''
    };
  }, 400);
};

const hideTooltip = () => {
  if (tooltipTimer) clearTimeout(tooltipTimer);
  tooltipState.value.visible = false;
};

onBeforeUnmount(() => {
  if (tooltipTimer) clearTimeout(tooltipTimer);
});

// --- Editor Tools Logic (Unchanged) ---
type ToolType = 'bold' | 'italic' | 'strike' | 'h2' | 'ul' | 'ol' | 'task' | 'quote' | 'code' | 'link' | 'hr';

interface EditorTool {
  type: 'action' | 'divider';
  toolType?: ToolType;
  title?: string;
  icon?: string;
  shortcut?: string;
}

const editorTools: EditorTool[] = [
  {type: 'action', toolType: 'bold', title: '加粗', icon: 'i-carbon-text-bold', shortcut: 'Cmd+B'},
  {type: 'action', toolType: 'italic', title: '斜体', icon: 'i-carbon-text-italic', shortcut: 'Cmd+I'},
  {type: 'action', toolType: 'strike', title: '删除线', icon: 'i-carbon-text-strikethrough'},
  {type: 'divider'},
  {type: 'action', toolType: 'h2', title: '二级标题', icon: 'i-carbon-heading'},
  {type: 'action', toolType: 'ul', title: '无序列表', icon: 'i-carbon-list-bulleted'},
  {type: 'action', toolType: 'task', title: '任务清单', icon: 'i-carbon-checkbox-checked'},
  {type: 'divider'},
  {type: 'action', toolType: 'quote', title: '引用', icon: 'i-carbon-quotes'},
  {type: 'action', toolType: 'code', title: '代码块', icon: 'i-carbon-code'},
  {type: 'action', toolType: 'link', title: '插入链接', icon: 'i-carbon-link'},
  {type: 'divider'},
  {type: 'action', toolType: 'hr', title: '分割线', icon: 'i-carbon-row-expand'},
];

const onInput = (e: Event) => {
  const target = e.target as HTMLTextAreaElement;
  emit('update:modelValue', target.value);
};

const insertTab = () => {
  const textarea = editorRef.value;
  if (!textarea) return;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = props.modelValue;
  const newVal = text.substring(0, start) + '  ' + text.substring(end);
  emit('update:modelValue', newVal);
  nextTick(() => {
    textarea.selectionStart = textarea.selectionEnd = start + 2;
  });
};

const handleToolAction = (tool: EditorTool) => {
  if (!tool.toolType) return;
  const textarea = editorRef.value;
  if (!textarea) return;
  switch (tool.toolType) {
    case 'bold':
      toggleWrapper('**');
      break;
    case 'italic':
      toggleWrapper('*');
      break;
    case 'strike':
      toggleWrapper('~~');
      break;
    case 'code':
      toggleBlock('```');
      break;
    case 'h2':
      toggleLinePrefix('## ');
      break;
    case 'ul':
      toggleLinePrefix('- ');
      break;
    case 'task':
      toggleLinePrefix('- [ ] ');
      break;
    case 'quote':
      toggleLinePrefix('> ');
      break;
    case 'link':
      insertLink();
      break;
    case 'hr':
      insertLine('\n---\n');
      break;
  }
  textarea.focus();
};

const toggleWrapper = (token: string) => {
  const textarea = editorRef.value!;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = props.modelValue;
  const len = token.length;
  const selectedText = text.substring(start, end);
  const before = text.substring(start - len, start);
  const after = text.substring(end, end + len);
  const isWrappedOutside = before === token && after === token;
  const isWrappedInside = selectedText.startsWith(token) && selectedText.endsWith(token);
  let newVal: string;
  let newStart = start;
  let newEnd = end;
  if (isWrappedOutside) {
    newVal = text.substring(0, start - len) + selectedText + text.substring(end + len);
    newStart = start - len;
    newEnd = end - len;
  } else if (isWrappedInside) {
    const content = selectedText.substring(len, selectedText.length - len);
    newVal = text.substring(0, start) + content + text.substring(end);
    newEnd = end - (len * 2);
  } else {
    newVal = text.substring(0, start) + token + selectedText + token + text.substring(end);
    if (selectedText.length === 0) newStart = start + len;
    newEnd = (selectedText.length === 0) ? newStart : end + (len * 2);
  }
  emit('update:modelValue', newVal);
  nextTick(() => textarea.setSelectionRange(newStart, newEnd));
};

const toggleLinePrefix = (prefix: string) => {
  const textarea = editorRef.value!;
  const start = textarea.selectionStart;
  const text = props.modelValue;
  const lineStart = text.lastIndexOf('\n', start - 1) + 1;
  let lineEnd = text.indexOf('\n', start);
  if (lineEnd === -1) lineEnd = text.length;
  const currentLine = text.substring(lineStart, lineEnd);
  let newVal: string;
  let cursorOffset = 0;
  if (currentLine.startsWith(prefix)) {
    newVal = text.substring(0, lineStart) + currentLine.substring(prefix.length) + text.substring(lineEnd);
    cursorOffset = -prefix.length;
  } else {
    const regex = /^(#+\s|-\s|-\s\[\s]\s|>\s)/;
    const match = currentLine.match(regex);
    if (match) {
      newVal = text.substring(0, lineStart) + prefix + currentLine.substring(match[0].length) + text.substring(lineEnd);
      cursorOffset = prefix.length - match[0].length;
    } else {
      newVal = text.substring(0, lineStart) + prefix + currentLine + text.substring(lineEnd);
      cursorOffset = prefix.length;
    }
  }
  emit('update:modelValue', newVal);
  nextTick(() => textarea.setSelectionRange(start + cursorOffset, start + cursorOffset));
};

const toggleBlock = (token: string) => {
  const textarea = editorRef.value!;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = props.modelValue;
  const selection = text.substring(start, end);
  const newText = `\n${token}\n${selection}\n${token}\n`;
  emit('update:modelValue', text.substring(0, start) + newText + text.substring(end));
  nextTick(() => {
    if (selection.length === 0) {
      const pos = start + token.length + 2;
      textarea.setSelectionRange(pos, pos);
    } else {
      textarea.setSelectionRange(start + newText.length, start + newText.length);
    }
  });
};

const insertLink = () => {
  const textarea = editorRef.value!;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = props.modelValue;
  const selection = text.substring(start, end);
  if (selection.length > 0) {
    emit('update:modelValue', text.substring(0, start) + `[${selection}](url)` + text.substring(end));
    nextTick(() => textarea.setSelectionRange(start + selection.length + 3, start + selection.length + 6));
  } else {
    emit('update:modelValue', text.substring(0, start) + `[](url)` + text.substring(end));
    nextTick(() => textarea.setSelectionRange(start + 1, start + 1));
  }
};

const insertLine = (str: string) => {
  const textarea = editorRef.value!;
  const start = textarea.selectionStart;
  const text = props.modelValue;
  emit('update:modelValue', text.substring(0, start) + str + text.substring(start));
  nextTick(() => textarea.setSelectionRange(start + str.length, start + str.length));
}
</script>
