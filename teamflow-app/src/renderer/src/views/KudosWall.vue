<!--suppress CssUnusedSymbol -->
<template>
  <div class="min-h-screen bg-bg-dark p-6 md:p-10 text-text-main relative overflow-y-auto">
    <!-- 顶部背景光效 -->
    <div
      class="fixed top-0 left-0 w-full h-[500px] bg-gradient-to-b from-primary/5 to-transparent pointer-events-none -z-0"></div>

    <div class="relative z-10 max-w-7xl mx-auto">
      <!-- 1. 顶部 Header -->
      <header class="flex flex-col md:flex-row justify-between items-end mb-10 gap-6 border-b border-white/5 pb-6">
        <div>
          <h1 class="text-4xl font-bold text-white tracking-tight flex items-center gap-3">
            <span class="i-carbon-trophy-filled text-accent"></span>
            Kudos Wall
          </h1>
          <p class="text-text-muted mt-2">认可与被认可，汇聚团队正能量。</p>
        </div>

        <div class="flex items-center gap-4">
          <!-- 筛选/选择器 Toggle -->
          <div ref="selectorRef" class="relative">
            <button
              :class="{'bg-white/10 border-primary/50': isSelectorOpen}"
              class="btn-outline gap-2 text-sm"
              @click="isSelectorOpen = !isSelectorOpen"
            >
              <div class="i-carbon-filter"></div>
              <span>筛选展示</span>
              <div :class="{'rotate-180': isSelectorOpen}"
                   class="i-carbon-chevron-down text-xs transition-transform duration-300"></div>
            </button>

            <!-- 自定义 Dropdown Panel -->
            <Transition name="fade-scale">
              <div v-if="isSelectorOpen"
                   class="absolute right-0 top-full mt-2 w-96 glass-panel z-50 overflow-hidden flex flex-col max-h-[500px]">
                <div class="p-3 bg-black/20 border-b border-white/10 flex justify-between items-center">
                  <span class="text-xs font-bold text-text-muted uppercase tracking-wider">Received Kudos</span>
                  <button class="text-xs text-primary hover:text-primary-hover" @click="toggleAllSelection">
                    {{ selectedKudoIds.size === kudosStore.receivedKudos?.length ? '全不选' : '全选' }}
                  </button>
                </div>

                <div v-if="kudosStore.receivedKudos?.length" class="overflow-y-auto p-2 space-y-1 scrollbar-hide">
                  <div
                    v-for="kudo in kudosStore.receivedKudos"
                    :key="kudo.id"
                    :class="selectedKudoIds.has(kudo.id) ? 'bg-primary/10 border-primary/20' : 'hover:bg-white/5'"
                    class="p-3 rounded-lg cursor-pointer transition-colors flex items-start gap-3 group border border-transparent"
                    @click="toggleKudoSelection(kudo.id)"
                  >
                    <div class="mt-1">
                      <div
                        :class="selectedKudoIds.has(kudo.id) ? 'bg-primary border-primary' : 'border-text-muted/50 group-hover:border-primary/50'"
                        class="w-4 h-4 rounded border flex items-center justify-center transition-colors"
                      >
                        <div v-if="selectedKudoIds.has(kudo.id)"
                             class="i-carbon-checkmark text-white text-[10px]"></div>
                      </div>
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="flex justify-between items-center mb-1">
                        <span class="font-medium text-sm text-white truncate">{{
                            kudo.sender?.username || 'Ghost'
                          }}</span>
                        <span class="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-text-muted">{{
                            kudo.card_type
                          }}</span>
                      </div>
                      <p class="text-xs text-text-muted line-clamp-2">{{ kudo.message }}</p>
                    </div>
                  </div>
                </div>
                <div v-else class="p-8 text-center text-text-muted text-sm">
                  暂无数据
                </div>
              </div>
            </Transition>
          </div>

          <!-- 发送按钮 -->
          <button class="btn-primary shadow-lg shadow-cyan-500/20" @click="openSendDialog">
            <div class="i-carbon-paper-plane"></div>
            <span>发送 Kudos</span>
          </button>
        </div>
      </header>

      <!-- 2. Grid 展示区 -->
      <main class="min-h-[60vh]">
        <div v-if="kudosStore.isLoading" class="flex-center h-64">
          <div class="i-carbon-circle-dash animate-spin text-4xl text-primary"></div>
        </div>

        <div v-else-if="displayedKudos.length > 0"
             class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <TransitionGroup name="list">
            <div
              v-for="(kudo, index) in displayedKudos"
              :key="kudo.id"
              :class="{ 'opacity-50 scale-95 grayscale': draggingKudoId === kudo.id }"
              class="cursor-move"
              draggable="true"
              @click="viewKudo(kudo)"
              @dragend="handleDragEnd"
              @dragenter="handleDragEnter(index)"
              @dragstart="handleDragStart(kudo, index)"
              @dragover.prevent
            >
              <KudosCard :kudo="kudo"/>
            </div>
          </TransitionGroup>
        </div>

        <div v-else
             class="flex flex-col items-center justify-center h-96 text-text-muted border-2 border-dashed border-white/10 rounded-3xl bg-white/5">
          <div class="i-carbon-idea text-6xl mb-4 opacity-20"></div>
          <p class="text-lg font-medium">还没有收到 Kudos，或者未选中任何卡片。</p>
          <p class="text-sm opacity-60 mt-2">快去给队友发送第一张吧！</p>
        </div>
      </main>
    </div>

    <!-- 3. 发送 Kudos 模态框 (Custom Modal) -->
    <Transition name="fade">
      <div v-if="isDialogVisible" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="isDialogVisible = false"></div>

        <!-- Modal Content -->
        <div
          class="relative glass-panel w-full max-w-lg p-8 border-white/20 shadow-2xl transform transition-all animate-in zoom-in-95 duration-200">
          <div class="flex justify-between items-center mb-8">
            <h2 class="text-2xl font-bold text-white flex items-center gap-2">
              <div class="i-carbon-send-alt text-primary"></div>
              发送能量卡
            </h2>
            <button class="text-text-muted hover:text-white transition-colors" @click="isDialogVisible = false">
              <div class="i-carbon-close text-xl"></div>
            </button>
          </div>

          <SendKudosCard ref="sendKudosFormRef" @send-success="handleSendSuccess"/>

          <div class="mt-8 flex justify-end gap-3">
            <button class="btn-ghost" @click="isDialogVisible = false">取消</button>
            <button :disabled="sendKudosFormRef?.isSending" class="btn-primary w-32" @click="handleConfirmSend">
              <div v-if="sendKudosFormRef?.isSending" class="i-carbon-circle-dash animate-spin"></div>
              <span v-else>确认发送</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 4. 查看详情 模态框 -->
    <Transition name="fade">
      <div v-if="viewingKudo" class="fixed inset-0 z-[100] flex items-center justify-center p-4"
           @click.self="closeKudoView">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-md" @click="closeKudoView"></div>

        <div class="relative w-full max-w-2xl transform transition-all animate-in zoom-in-95 duration-300">
          <button
            class="absolute -top-12 right-0 text-white/50 hover:text-white transition-colors flex items-center gap-2"
            @click="closeKudoView"
          >
            <span class="text-sm">Close</span>
            <div class="i-carbon-close-outline text-2xl"></div>
          </button>
          <KudosCard :is-large-view="true" :kudo="viewingKudo" class="shadow-2xl shadow-black/50"/>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script lang="ts" setup>
import {ref, onMounted, computed, onUnmounted} from 'vue';
import {useKudosStore} from '@/stores/kudos';
import KudosCard from '@/components/KudosCard.vue';
import SendKudosCard from '@/components/SendKudosCard.vue';

const kudosStore = useKudosStore();

// --- 状态管理 ---
const isDialogVisible = ref(false);
const isSelectorOpen = ref(false);
const selectorRef = ref<HTMLElement | null>(null);
const sendKudosFormRef = ref<any>(null); // Using any to access exposed props easily in template

// --- 逻辑 ---
const openSendDialog = () => {
  isDialogVisible.value = true;
};

const handleConfirmSend = async () => {
  await sendKudosFormRef.value?.submitForm();
};

const handleSendSuccess = async () => {
  isDialogVisible.value = false;
  await kudosStore.fetchMyReceivedKudos();
  resetKudoSelection();
};

// --- 选择器逻辑 ---
const selectedKudoIds = ref(new Set<string>());

// 点击外部关闭 Selector
const handleClickOutside = (event: MouseEvent) => {
  if (selectorRef.value && !selectorRef.value.contains(event.target as Node)) {
    isSelectorOpen.value = false;
  }
};
onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});

const toggleAllSelection = () => {
  if (!kudosStore.receivedKudos) return;
  if (selectedKudoIds.value.size === kudosStore.receivedKudos.length) {
    selectedKudoIds.value.clear();
  } else {
    selectedKudoIds.value = new Set(kudosStore.receivedKudos.map(k => k.id));
  }
};

const displayedKudos = computed({
  get() {
    if (!kudosStore.receivedKudos || !Array.isArray(kudosStore.receivedKudos)) return [];
    return kudosStore.receivedKudos.filter(kudo => selectedKudoIds.value.has(kudo.id));
  },
  set(newValue) {
    kudosStore.updateKudosOrder(newValue);
  }
});

const toggleKudoSelection = (kudoId: string) => {
  const newSet = new Set(selectedKudoIds.value);
  if (newSet.has(kudoId)) newSet.delete(kudoId);
  else newSet.add(kudoId);
  selectedKudoIds.value = newSet; // Trigger reactivity
};

const resetKudoSelection = () => {
  if (kudosStore.receivedKudos?.length) {
    selectedKudoIds.value = new Set(kudosStore.receivedKudos.map(k => k.id));
  }
};

// --- 拖拽逻辑 (保持不变，只是适配样式) ---
const draggingKudoId = ref<string | null>(null);
const dragStartIndex = ref<number | null>(null);

const handleDragStart = (kudo: any, index: number) => {
  draggingKudoId.value = kudo.id;
  dragStartIndex.value = index;
};
const handleDragEnter = (targetIndex: number) => {
  if (dragStartIndex.value === null || dragStartIndex.value === targetIndex) return;
  const list = [...displayedKudos.value];
  const draggedItem = list.splice(dragStartIndex.value, 1)[0];
  list.splice(targetIndex, 0, draggedItem);
  dragStartIndex.value = targetIndex;
  displayedKudos.value = list;
};
const handleDragEnd = () => {
  draggingKudoId.value = null;
  dragStartIndex.value = null;
};

// --- 查看详情 ---
const viewingKudo = ref<any | null>(null);
const viewKudo = (kudo: any) => {
  viewingKudo.value = kudo;
};
const closeKudoView = () => {
  viewingKudo.value = null;
};

onMounted(async () => {
  await kudosStore.fetchMyReceivedKudos();
  resetKudoSelection();
});
</script>

<style scoped>
/* 过渡动画定义 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* 下拉菜单动画 */
.fade-scale-enter-active, .fade-scale-leave-active {
  transition: all 0.2s ease-out;
}

.fade-scale-enter-from, .fade-scale-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

/* 列表移动动画 */
.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.5s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}

.list-leave-active {
  position: absolute; /* 确保移除时布局平滑 */
}
</style>
