<!-- src/components/FlowCharter.vue -->
<template>
  <div class="w-full h-full flex flex-col p-4 sm:p-6 relative overflow-hidden">
    <!-- Header (保持不变) -->
    <header class="flex justify-between items-end mb-6 shrink-0 z-10 animate-slide-in-fast">
      <div>
        <h1 class="text-h1 flex items-center gap-3">
          <div class="relative flex-center">
            <i class="i-carbon-certificate-check text-primary text-3xl z-10"/>
            <div class="absolute inset-0 bg-primary/20 blur-lg rounded-full animate-pulse-slow"></div>
          </div>
          <span class="text-text-main font-bold tracking-tight">
            团队心流协议
          </span>
        </h1>
        <div class="flex items-center gap-3 mt-2 font-mono text-xs text-text-muted select-none">
          <span class="px-2 py-0.5 rounded-md bg-bg-surface border border-border/30 text-primary">
            PROTOCOL v{{ charterStore.charter?.updated_at ? '1.2' : '0.1' }}
          </span>
          <span class="flex items-center gap-1.5">
            <span :class="charterStore.charter?.content ? 'bg-primary shadow-glow-sm' : 'bg-text-muted'"
                  class="w-1.5 h-1.5 rounded-full"></span>
            {{ charterStore.charter?.content ? 'ACTIVE' : 'DRAFT' }}
          </span>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <Menu v-if="!charterStore.isEditing" as="div" class="relative inline-block text-left">
          <MenuButton class="btn-ghost w-9 h-9 p-0 flex-center border border-border/30" title="阅读主题">
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
            <MenuItems
              class="absolute right-0 mt-2 w-40 origin-top-right divide-y divide-border/20 rounded-xl bg-bg-card border border-border/50 shadow-glow-lg ring-1 ring-black/5 focus:outline-none z-50">
              <div class="px-1 py-1">
                <!-- 复用同样的主题列表逻辑 -->
                <MenuItem v-for="theme in MD_THEMES" :key="theme.value" v-slot="{ active }">
                  <button
                    :class="[active ? 'bg-primary/10 text-primary' : 'text-text-main', 'group flex w-full items-center rounded-lg px-2 py-2 text-xs transition-colors']"
                    @click="prefStore.markdownTheme = theme.value"
                  >
                    <span :class="['w-3 h-3 rounded-full mr-2 border border-border/50', theme.colorClass]"></span>
                    {{ theme.label }}
                    <i v-if="prefStore.markdownTheme === theme.value" class="i-carbon-checkmark ml-auto text-primary"/>
                  </button>
                </MenuItem>
              </div>
            </MenuItems>
          </transition>
        </Menu>
        <template v-if="!charterStore.isEditing">
          <div v-if="charterStore.charter" class="text-right hidden sm:block font-mono text-xs mr-2">
            <div class="text-text-muted/60 uppercase tracking-wider">Last Commit</div>
            <div class="text-text-main font-medium flex items-center justify-end gap-1">
              <i class="i-carbon-user-avatar"/>
              {{ charterStore.charter.last_updated_by?.username ?? 'System' }}
            </div>
          </div>
          <button v-if="teamsStore.isCurrentUserOwner" class="btn-primary" @click="handleEnterEdit">
            <i class="i-carbon-edit"/>
            <span>修订协议</span>
          </button>
        </template>
        <template v-else>
          <button class="btn-ghost text-sm" @click="charterStore.cancelEditMode">取消</button>
          <button :disabled="charterStore.isLoading" class="btn-primary text-sm" @click="handleSave">
            <i v-if="charterStore.isLoading" class="i-carbon-circle-dash animate-spin"/>
            <i v-else class="i-carbon-save"/>
            <span>签署生效</span>
          </button>
        </template>
      </div>
    </header>

    <main
      class="flex-1 glass-panel relative overflow-hidden flex flex-col min-h-0 shadow-glow-sm border-t border-white/5 transition-colors duration-500">

      <div v-if="charterStore.isLoading"
           class="absolute inset-0 z-50 bg-bg-main/60 backdrop-blur-md flex-center flex-col gap-4">
        <div class="i-carbon-circle-dash text-4xl text-primary animate-spin-slow"/>
        <span class="text-sm font-mono text-primary tracking-widest animate-pulse">SYNCING DATA...</span>
      </div>

      <Transition mode="out-in" name="fade">

        <!-- 模式 A: 编辑器 (重构后) -->
        <div v-if="charterStore.isEditing" class="h-full animate-enter">
          <MarkdownEditor
            v-model="editableContent"
            placeholder="# 撰写团队协议..."
          >
            <!-- 插槽：注入模板菜单 -->
            <template #toolbar-extra>
              <Menu as="div" class="relative inline-block text-left">
                <MenuButton
                  class="btn-ghost text-xs py-1.5 px-3 h-9 gap-2 border border-border/30 hover:border-primary/50 hover:bg-bg-surface/80">
                  <i class="i-carbon-template"/>
                  <span class="hidden sm:inline font-medium">模板库</span>
                  <i class="i-carbon-chevron-down text-[10px] opacity-70"/>
                </MenuButton>
                <transition
                  enter-active-class="transition duration-100 ease-out"
                  enter-from-class="transform scale-95 opacity-0"
                  enter-to-class="transform scale-100 opacity-100"
                  leave-active-class="transition duration-75 ease-in"
                  leave-from-class="transform scale-100 opacity-100"
                  leave-to-class="transform scale-95 opacity-0"
                >
                  <MenuItems
                    class="absolute right-0 mt-2 w-72 origin-top-right divide-y divide-border/20 rounded-xl bg-bg-card border border-border/50 shadow-glow-lg ring-1 ring-black/5 focus:outline-none z-50 overflow-hidden">
                    <div
                      class="bg-bg-surface/50 px-4 py-2 text-[10px] text-text-muted font-mono uppercase tracking-widest border-b border-border/20">
                      Available Templates
                    </div>
                    <div class="p-1.5">
                      <MenuItem v-for="tpl in TEMPLATES" :key="tpl.name" v-slot="{ active }">
                        <button
                          :class="[active ? 'bg-primary/10' : '', 'group flex w-full items-start rounded-lg p-2.5 transition-all text-left relative overflow-hidden']"
                          @click="applyTemplate(tpl.content)"
                        >
                          <div v-if="active" class="absolute left-0 top-0 bottom-0 w-0.5 bg-primary"></div>
                          <div
                            class="w-8 h-8 rounded-lg bg-bg-surface flex-center mr-3 shrink-0 border border-border/30 group-hover:border-primary/40 group-hover:text-primary transition-colors">
                            <i :class="tpl.icon" class="text-lg opacity-80"/>
                          </div>
                          <div class="flex-1 min-w-0">
                            <div :class="active ? 'text-primary' : 'text-text-main'" class="text-sm font-medium">
                              {{ tpl.name }}
                            </div>
                            <div class="text-[11px] text-text-muted leading-tight mt-0.5 line-clamp-2 opacity-80">
                              {{ tpl.desc }}
                            </div>
                          </div>
                        </button>
                      </MenuItem>
                    </div>
                  </MenuItems>
                </transition>
              </Menu>
            </template>
          </MarkdownEditor>
        </div>

        <!-- 模式 B: 阅读模式 -->
        <div v-else class="h-full relative animate-enter flex flex-col">
          <!--
             ★★★ 关键修改 ★★★
             1. 将 overflow-y-auto 移到这个 wrapper 或者是内部容器
             2. 添加 :data-md-theme 绑定
             3. 添加 markdown-preview-container 类以启用背景色过渡
          -->
          <div
            :data-md-theme="prefStore.markdownTheme"
            class="flex-1 overflow-y-auto custom-scrollbar relative p-8 md:px-16 md:py-12 markdown-preview-container transition-colors duration-300"
          >
            <!-- 背景装饰：只在 Default 主题下显示，或者根据需要调整透明度 -->
            <div v-if="prefStore.markdownTheme === 'default'" class="absolute inset-0 pointer-events-none z-0">
              <div
                class="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 blur-[120px] rounded-full mix-blend-screen"></div>
              <div
                class="absolute bottom-0 left-0 w-[300px] h-[300px] bg-secondary/5 blur-[100px] rounded-full mix-blend-screen"></div>
              <div class="absolute inset-0 bg-grid-pattern opacity-20"></div>
            </div>

            <div class="max-w-4xl mx-auto relative z-10">
              <div v-if="charterStore.charter && charterStore.charter.content">
                <!-- 这里直接使用 .prose-content，因为 CSS 已经是全局的了 -->
                <div class="prose-content" @click="handleLinkClick" v-html="renderedHtml"></div>

                <div class="mt-24 pt-8 border-t border-border/30 flex justify-between items-end opacity-70 select-none">
                  <div class="font-mono text-[10px] leading-relaxed text-text-muted">
                    <p class="flex items-center gap-2"><i class="i-carbon-checkmark-filled text-primary"/> DIGITAL
                      SIGNATURE VERIFIED</p>
                    <p class="text-text-main/50 mt-1">HASH: <span class="text-primary/70">{{ randomHash }}</span></p>
                    <p class="text-text-main/50">TIMESTAMP: {{ new Date().toISOString() }}</p>
                  </div>
                  <div class="i-carbon-ibm-cloud-citrix-daas text-6xl text-text-muted/10"/>
                </div>
              </div>
              <div v-else class="flex flex-col items-center justify-center min-h-[400px] text-center">
                <div
                  class="w-24 h-24 rounded-2xl bg-bg-surface border border-border/50 flex items-center justify-center mb-6 shadow-lg">
                  <i class="i-carbon-document-blank text-5xl text-text-muted"/>
                </div>
                <h3 class="text-2xl font-bold text-text-main mb-2">协议未定义</h3>
                <p class="text-text-muted max-w-md mb-8">团队尚未建立心流公约。</p>
                <button v-if="teamsStore.isCurrentUserOwner" class="btn-primary px-8 py-3" @click="handleEnterEdit">
                  <i class="i-carbon-add"/><span>立即起草</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </main>

    <ConfirmModel
      :is-open="isTemplateModalOpen"
      confirm-text="覆盖并应用"
      description="应用此模板将完全覆盖您当前正在编辑的内容。此操作不可撤销，建议您先备份当前文本。"
      title="覆盖当前内容？"
      @close="isTemplateModalOpen = false"
      @confirm="confirmApplyTemplate"
    />
  </div>
</template>

<script lang="ts" setup>
import {ref, computed} from 'vue';
import {useCharterStore} from '@/stores/charter';
import {useTeamsStore} from '@/stores/teams';
import {usePreferencesStore} from '@/stores/markdown/preferences';
import {Menu, MenuButton, MenuItems, MenuItem} from '@headlessui/vue';
import MarkdownEditor from '@/components/share/MarkdownEditor.vue'; // 引入新组件
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
// noinspection TypeScriptCheckImport
import taskLists from 'markdown-it-task-lists';
import {toast} from 'vue-sonner';
import ConfirmModel from "@/components/share/ConfirmModal.vue";

const charterStore = useCharterStore();
const teamsStore = useTeamsStore();
const editableContent = ref('');
const prefStore = usePreferencesStore();
const randomHash = Math.random().toString(36).substring(2, 15).toUpperCase();

const MD_THEMES = [
  {value: 'default', label: 'Default (Glass)', colorClass: 'bg-gray-500'},
  {value: 'github', label: 'GitHub Style', colorClass: 'bg-white'},
  {value: 'github-dark', label: 'GitHub Dark', colorClass: 'bg-[#0d1117] border border-gray-700'},
  {value: 'dracula', label: 'Dracula', colorClass: 'bg-[#282a36] border border-gray-600'},
  {value: 'notion', label: 'Notion Minimal', colorClass: 'bg-orange-50'},
  {value: 'solarized-light', label: 'Solarized Light', colorClass: 'bg-[#fdf6e3]'},
  {value: 'cobalt', label: 'Cobalt Blue', colorClass: 'bg-blue-900'},
];

// --- 模态框状态管理 ---
const isTemplateModalOpen = ref(false);
const pendingTemplateContent = ref(''); // 暂存用户想选的模板内容

const handleLinkClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  const link = target.closest('a');
  if (link) {
    const href = link.getAttribute('href');
    if (href && !href.startsWith('#')) {
      e.preventDefault();
      window.open(href, '_blank');
    }
  }
};
// --- 阅读模式专用的 Markdown 渲染器 (编辑器自带了它自己的，这里是为了阅读模式) ---
// 实际上，为了极致的复用，你也可以将 md 实例配置抽离成一个 utils/markdown.ts，但这里保留两份实例也无伤大雅
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
}).use(taskLists, {label: true, labelAfter: true});

const renderedHtml = computed(() => charterStore.charter?.content ? md.render(charterStore.charter.content) : '');

// --- 模板数据 (属于 Charter 业务逻辑) ---
const TEMPLATES = [
  {
    name: '标准心流协议',
    desc: '平衡专注与沟通的通用模板',
    icon: 'i-carbon-layers',
    content: `# 🚀 团队心流协议 (Flow Protocol)\n\n## 🎯 核心原则\n1. **单一任务**: 一次只做一件事，拒绝多任务切换。\n2. **深度工作**: 每天保持至少 2 小时不被打扰的深度工作时间。\n3. **异步优先**: 除非紧急，否则优先使用文档和消息留言。\n\n## ⏰ 时间约定\n- **同步时间**: 10:00 - 11:00 (站会、讨论)\n- **心流时段**: 14:00 - 17:00 (全员静默，禁止即时通讯)\n\n## 🤝 协作规范\n- [ ] 提交代码前必须自测\n- [ ] 遇到阻塞超过 30 分钟需立即求助\n- [ ] 会议必须有议程 (Agenda) 和 产出 (Action Items)`
  },
  {
    name: '敏捷冲刺型',
    desc: '适合快速迭代、高频同步的团队',
    icon: 'i-carbon-rocket',
    content: `# ⚡ 敏捷冲刺公约\n\n## 🏁 冲刺目标\n我们致力于快速迭代，拥抱变化，但在冲刺期间保持专注。\n\n## 🔄 仪式\n- **每日站会**: 09:30 (限时 15 分钟)\n- **评审会**: 每周五 16:00\n- **回顾会**: 每周五 17:00\n\n## ✅ 完成的定义 (DoD)\n- [ ] 代码通过 Review\n- [ ] 自动化测试通过\n- [ ] 部署到 Staging 环境`
  },
  {
    name: '开放连接型',
    desc: '鼓励分享、社交和思想碰撞',
    icon: 'i-carbon-network-4',
    content: `# 🌈 开放连接文化\n\n## 💡 愿景\n在保持个人专注的同时，我们珍视每一次思想的碰撞。\n\n## 🗣️ 沟通方式\n- 鼓励 "大声工作" (Work Out Loud)，分享你的进度。\n- 即使是草稿想法，也欢迎在群组讨论。\n- 使用 **Kudos** 卡片感谢队友的帮助。\n\n## 🧘‍♀️ 健康与平衡\n- 每工作 50 分钟，休息 10 分钟。\n- 鼓励线下聚会或虚拟咖啡时间。`
  }
];

const handleEnterEdit = () => {
  editableContent.value = charterStore.charter?.content || TEMPLATES[0].content;
  charterStore.enterEditMode();
};

const handleSave = async () => {
  try {
    await charterStore.saveCharter(editableContent.value);
    toast.success('协议签署成功', {
      description: '所有团队成员现已生效新的心流公约。',
    });
  } catch (e) {
    toast.error('签署失败', {description: '请检查网络连接后重试。'});
  }
};

const applyTemplate = (content: string) => {
  if (!editableContent.value || editableContent.value.trim() === '') {
    editableContent.value = content;
    toast.info('已应用模板');
    return;
  }

  pendingTemplateContent.value = content;
  isTemplateModalOpen.value = true;
};

const confirmApplyTemplate = () => {
  editableContent.value = pendingTemplateContent.value;
  isTemplateModalOpen.value = false;
  toast.success('模板已应用', {
    description: '您可以继续在此基础上进行修改。'
  });
};
</script>

