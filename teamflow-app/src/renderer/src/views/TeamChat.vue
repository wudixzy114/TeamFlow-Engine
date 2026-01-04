<!-- src/views/TeamChat.vue -->
<script lang="ts" setup>
import {ref, onUnmounted, nextTick, watch, computed} from 'vue';
import {Menu, MenuButton, MenuItems, MenuItem} from '@headlessui/vue';
import {useTeamsStore} from '@/stores/teams';
import {useChatStore} from '@/stores/chat';
import {useAuthStore} from '@/stores/auth';
import ChatBubble from '@/components/chat/ChatBubble.vue';
import ChatActionModal from '@/components/chat/ChatActionModal.vue';
import {SOCIAL_TAGS, type TagConfig} from '@/stores/chat/chatTags';
import {aiAgent} from '@/stores/chat/aiAgent';
import {useIntersectionObserver} from '@vueuse/core';

const teamsStore = useTeamsStore();
const chatStore = useChatStore();
const authStore = useAuthStore();

const messagesContainer = ref<HTMLElement | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const inputValue = ref('');
const sentinelRef = ref<HTMLElement | null>(null);

// Modal Control
const isModalOpen = ref(false);
const selectedActionConfig = ref<TagConfig | null>(null);

// --- Initialization & Hooks ---

const {stop} = useIntersectionObserver(
  sentinelRef,
  async ([{isIntersecting}]) => {
    if (
      isIntersecting &&
      !chatStore.isLoadingHistory &&
      !chatStore.isLoading &&
      chatStore.hasMoreHistory
    ) {
      // 1. 记录当前容器高度
      const container = messagesContainer.value;
      if (!container) return;

      const previousScrollHeight = container.scrollHeight;
      const previousScrollTop = container.scrollTop;

      // 2. 加载历史
      const addedCount = await chatStore.loadHistoryMessages();

      // 3. 恢复位置
      if (addedCount > 0) {
        await nextTick();

        const newScrollHeight = container.scrollHeight;
        const diff = newScrollHeight - previousScrollHeight;

        // 如果 diff 很小，说明没怎么变，强制给一点偏移量防止吸顶
        if (diff > 0) {
          container.scrollTop = diff + (previousScrollTop > 0 ? previousScrollTop : 0);
        } else {
          // 极端情况：加载了数据但没产生高度变化？(不太可能)
        }
      }
    }
  },
  {
    root: messagesContainer.value, // 监听容器
    rootMargin: '100px 0px 0px 0px', // 提前 100px 触发，体验更丝滑
    threshold: 0, // 只要露头一点点就触发
  }
);

watch(() => teamsStore.currentTeamId, async (newTeamId) => {
  aiAgent.clearCache();
  if (newTeamId) {
    await chatStore.switchChatRoom(newTeamId);
    if (!chatStore.isLoadingHistory) {
      scrollToBottom(false);
    }
  } else {
    chatStore.clearChat();
  }
}, {immediate: true});

onUnmounted(() => chatStore.clearChat());

watch(() => chatStore.sortedMessages, (newVal, oldVal) => {
  const isNewMessageArrived =
    oldVal.length > 0 &&
    newVal.length > 0 &&
    new Date(newVal[newVal.length - 1].created_at).getTime() > new Date(oldVal[oldVal.length - 1].created_at).getTime();

  // 或者是刚初始化完成 (oldVal 为空)
  const isInitialLoad = oldVal.length === 0 && newVal.length > 0;

  if ((isNewMessageArrived || isInitialLoad) && !chatStore.isLoadingHistory) {
    scrollToBottom();
  }

  if (newVal.length > 0) aiAgent.inspect(newVal);
}, {deep: true});

// --- Actions ---

const scrollToBottom = async (smooth = true) => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTo({
      top: messagesContainer.value.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto',
    });
  }
};

const handleSendText = async () => {
  if (!inputValue.value.trim() || chatStore.isSending) return;
  const content = inputValue.value;
  inputValue.value = '';
  if (textareaRef.value) textareaRef.value.style.height = '42px';
  await chatStore.sendMessage(content, 'text');
};

const openActionModal = (config: TagConfig) => {
  selectedActionConfig.value = config;
  isModalOpen.value = true;
};

const handleActionSubmit = async (content: string) => {
  if (selectedActionConfig.value) {
    await chatStore.sendMessage(content, selectedActionConfig.value.key);
  }
};

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    const file = target.files[0];
    const tag = file.type.startsWith('image/') ? 'image' : 'file';
    await chatStore.sendFile(file, tag);
    target.value = '';
  }
};

const autoResize = () => {
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = '42px';
  el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
};

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSendText();
  }
};

const currentUserId = computed(() => authStore.user?.id || '');
</script>

<template>
  <div class="h-full w-full flex flex-col relative bg-bg-main overflow-hidden">

    <!-- Action Modal -->
    <ChatActionModal
      :config="selectedActionConfig"
      :is-open="isModalOpen"
      @close="isModalOpen = false"
      @submit="handleActionSubmit"
    />

    <!-- Header -->
    <header class="h-16 flex-none border-b border-white/5 flex-between px-6 bg-bg-card/30 backdrop-blur-md z-10">
      <div class="flex items-center gap-4">
        <template v-if="teamsStore.currentTeamDetail">
          <div
            class="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary/20 to-secondary/20 border border-white/5 flex-center text-primary font-bold shadow-[0_0_15px_rgba(var(--c-primary),0.1)]">
            {{ teamsStore.currentTeamDetail.name.slice(0, 1).toUpperCase() }}
          </div>
          <div>
            <h2 class="font-bold text-lg text-text-main tracking-tight flex items-center gap-2">
              {{ teamsStore.currentTeamDetail.name }}
              <div class="text-[10px] px-1.5 py-0.5 rounded bg-primary/10 text-primary font-medium">TEAM</div>
            </h2>
            <div class="text-xs text-text-muted flex items-center gap-1.5 opacity-80">
              <span class="w-1.5 h-1.5 rounded-full bg-success shadow-[0_0_5px_rgb(var(--c-success))]"></span>
              {{ teamsStore.currentTeamDetail.members.length }} online
            </div>
          </div>
        </template>
        <template v-else>
          <div class="w-24 h-6 bg-white/5 animate-pulse rounded"></div>
        </template>
      </div>

      <div class="flex items-center gap-2">
        <button class="btn-ghost p-2 rounded-lg" title="AI 分析">
          <div class="i-carbon-machine-learning-model text-lg"></div>
        </button>
        <button class="btn-ghost p-2 rounded-lg" title="设置">
          <div class="i-carbon-settings text-lg"></div>
        </button>
      </div>
    </header>

    <!-- Main Chat Area -->
    <main ref="messagesContainer" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 scrollbar-hide">

      <!-- Loading (Overlay) -->
      <div v-if="chatStore.isLoading" class="absolute inset-0 z-20 bg-bg-main flex-center flex-col gap-4">
        <div class="i-svg-spinners-blocks-scale text-4xl text-primary opacity-50"></div>
        <span class="text-text-muted text-sm animate-pulse">正在同步消息记录...</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="chatStore.sortedMessages.length === 0"
           class="flex-center h-full flex-col gap-6 text-text-muted/30">
        <div class="relative">
          <div class="i-carbon-chat text-8xl opacity-50"></div>
          <div class="i-carbon-idea text-4xl absolute -top-2 -right-2 text-primary animate-bounce"></div>
        </div>
        <div class="text-center">
          <p class="text-lg font-medium text-text-muted">Start the conversation</p>
          <p class="text-xs mt-1">Share ideas, files, or plan an activity.</p>
        </div>
      </div>

      <!-- Messages List -->
      <template v-else>
        <div ref="sentinelRef" class="w-full h-4 flex-center flex-shrink-0">
          <!-- 仅在真正加载时显示 loading 图标 -->
          <div v-if="chatStore.isLoadingHistory"
               class="flex items-center gap-2 text-[10px] text-primary/80 bg-primary/5 px-3 py-0.5 rounded-full">
            <div class="i-svg-spinners-90-ring-with-bg"></div>
            <span>Syncing history...</span>
          </div>
          <!-- 如果没有更多了，显示提示 -->
          <div v-else-if="!chatStore.hasMoreHistory" class="text-[10px] text-text-muted/20 select-none">
            Top of history
          </div>
        </div>

        <div v-for="(msg, index) in chatStore.sortedMessages" :key="msg.id">
          <!-- Date Divider -->
          <div
            v-if="index === 0 || new Date(msg.created_at).getDate() !== new Date(chatStore.sortedMessages[index - 1].created_at).getDate()"
            class="flex-center py-6">
            <div
              class="px-4 py-1 rounded-full bg-bg-card/50 border border-white/5 text-[10px] font-bold text-text-muted/60 backdrop-blur-sm">
              {{
                new Date(msg.created_at).toLocaleDateString(undefined, {
                  weekday: 'long',
                  month: 'short',
                  day: 'numeric'
                })
              }}
            </div>
          </div>

          <ChatBubble
            :is-self="msg.sender_id === currentUserId"
            :message="msg"
            @delete="chatStore.deleteMessage"
          />
        </div>
        <div class="h-2"></div> <!-- Spacer -->
      </template>

    </main>

    <!-- Input Footer -->
    <footer class="flex-none p-4 sm:p-6 pt-2 z-20">
      <div class="glass-panel p-2 flex items-end gap-2 transition-all shadow-2xl relative">

        <!-- Feature Menu -->
        <Menu as="div" class="relative flex-shrink-0">
          <MenuButton
            class="btn-ghost w-[42px] h-[42px] p-0 rounded-xl hover:bg-primary/10 hover:text-primary transition-all group">
            <div class="i-carbon-add-filled text-xl transition-transform group-hover:rotate-90"></div>
          </MenuButton>

          <transition
            enter-active-class="transition duration-200 ease-out"
            enter-from-class="translate-y-2 opacity-0 scale-95"
            enter-to-class="translate-y-0 opacity-100 scale-100"
            leave-active-class="transition duration-150 ease-in"
            leave-from-class="translate-y-0 opacity-100 scale-100"
            leave-to-class="translate-y-2 opacity-0 scale-95"
          >
            <MenuItems
              class="absolute bottom-14 left-0 w-64 p-2 rounded-2xl bg-[#1a1f2e] border border-white/10 shadow-[0_10px_40px_-10px_rgba(0,0,0,0.5)] focus:outline-none origin-bottom-left backdrop-blur-xl">
              <div class="px-3 py-2 text-[10px] font-bold text-text-muted/50 uppercase tracking-widest">Connection
                Actions
              </div>

              <div class="grid grid-cols-1 gap-1">
                <MenuItem v-for="tag in SOCIAL_TAGS" :key="tag.key" v-slot="{ active }">
                  <button
                    :class="[active ? 'bg-white/5' : '', 'flex items-center gap-3 w-full px-3 py-2.5 rounded-xl transition-all group/item']"
                    @click="openActionModal(tag)">
                    <div :class="[tag.icon, tag.color]"
                         class="text-lg bg-white/5 p-1.5 rounded-lg group-hover/item:bg-white/10 transition"></div>
                    <div class="flex flex-col items-start">
                      <span class="text-sm font-medium text-text-main">{{ tag.label }}</span>
                      <span class="text-[10px] text-text-muted/60">发起{{ tag.label }}邀约</span>
                    </div>
                  </button>
                </MenuItem>
              </div>
            </MenuItems>
          </transition>
        </Menu>

        <!-- File Upload -->
        <button
          class="btn-ghost w-[42px] h-[42px] p-0 rounded-xl hover:bg-white/5 text-text-muted hover:text-text-main transition-colors"
          @click="fileInput?.click()">
          <div class="i-carbon-image text-xl"></div>
        </button>
        <input ref="fileInput" accept="image/*,.pdf,.doc,.docx" class="hidden" type="file" @change="handleFileChange"/>

        <!-- Text Input -->
        <div
          class="flex-1 bg-bg-surface/50 rounded-xl border border-white/5 focus-within:border-primary/50 focus-within:bg-bg-surface focus-within:shadow-[0_0_15px_rgba(var(--c-primary),0.1)] transition-all flex items-center px-3">
           <textarea
             ref="textareaRef"
             v-model="inputValue"
             class="w-full bg-transparent border-none outline-none text-text-main placeholder:text-text-muted/40 py-3 resize-none h-[42px] leading-relaxed scrollbar-hide text-sm"
             placeholder="Type a message..."
             rows="1"
             @input="autoResize"
             @keydown="handleKeydown"
           ></textarea>
        </div>

        <!-- Send Button -->
        <button
          :class="inputValue.trim() ? 'bg-primary text-white shadow-lg shadow-primary/30 hover:scale-105 active:scale-95' : 'bg-white/5 text-text-muted cursor-not-allowed'"
          :disabled="!inputValue.trim() || chatStore.isSending"
          class="w-[42px] h-[42px] rounded-xl flex-center transition-all duration-300 flex-shrink-0"
          @click="handleSendText"
        >
          <div v-if="chatStore.isSending" class="i-svg-spinners-ring-resize"></div>
          <div v-else class="i-carbon-send-filled text-lg"></div>
        </button>

      </div>
      <div class="text-[10px] text-center mt-2 text-text-muted/20 select-none">Enter to send, Shift + Enter for new
        line
      </div>
    </footer>

  </div>
</template>

<style scoped>
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
