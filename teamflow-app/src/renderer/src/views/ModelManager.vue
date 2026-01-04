<template>
  <div class="h-full flex flex-col p-8 overflow-hidden relative">
    <!-- 1. 动态背景光效 -->
    <div
      class="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] bg-primary/20 blur-[120px] rounded-full pointer-events-none -z-10 mix-blend-screen animate-pulse-slow"></div>
    <div
      class="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] bg-secondary/10 blur-[100px] rounded-full pointer-events-none -z-10 mix-blend-screen"></div>

    <!-- 2. 头部区域 -->
    <div class="flex-between mb-8 shrink-0 animate-fade-in-up">
      <div>
        <h1 class="text-3xl font-bold tracking-tight mb-2 flex items-center gap-3">
          <span class="i-carbon-ibm-watson-discovery text-4xl text-primary"></span>
          <span class="text-gradient">Neural Resource Center</span>
        </h1>
        <p class="text-text-muted text-base">
          Manage local AI models and knowledge bases.
        </p>
      </div>

      <!-- 状态看板 -->
      <div class="flex gap-4">
        <div class="glass-panel px-5 py-3 flex-col-center min-w-[120px]">
          <span class="text-xs text-text-muted uppercase tracking-wider font-bold">Storage</span>
          <span class="text-lg font-mono font-semibold text-text-main">{{ totalStorage }}</span>
        </div>
        <div class="glass-panel px-5 py-3 flex-col-center min-w-[120px]">
          <span class="text-xs text-text-muted uppercase tracking-wider font-bold">Resources</span>
          <span class="text-lg font-mono font-semibold text-primary">{{ installedCount }} / {{
              allResources.length
            }}</span>
        </div>
      </div>
    </div>

    <!-- 3. 资源网格 -->
    <div
      class="flex-1 overflow-y-auto pr-2 pb-8 -mr-2 scrollbar-hide grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-min content-start">

      <div
        v-for="(item, index) in allResources"
        :key="item.id"
        :style="{ animationDelay: `${index * 100}ms` }"
        class="card-interactive flex flex-col h-fit relative group overflow-hidden animate-fade-in-up transition-all duration-500"
      >
        <!-- 顶部装饰条 -->
        <div :class="getCategoryColor(item.category, 'bg')"
             class="absolute top-0 left-0 w-full h-1 transition-all duration-500"></div>

        <div class="p-6 flex flex-col h-full relative z-10">

          <!-- Header -->
          <div class="flex justify-between items-start mb-4">
            <!-- Icon -->
            <div
              :class="[getCategoryColor(item.category, 'bg-soft'), getCategoryColor(item.category, 'border')]"
              class="w-14 h-14 rounded-2xl flex-center border shadow-lg transition-transform group-hover:scale-110 duration-500 relative"
            >
              <!-- Bundle 叠层效果 -->
              <div v-if="item.type === 'bundle'"
                   :class="getCategoryColor(item.category, 'border')"
                   class="absolute -top-1.5 -right-1.5 w-full h-full rounded-2xl border opacity-30 -z-10"></div>
              <div :class="[getCategoryIcon(item.category), 'text-2xl', getCategoryColor(item.category, 'text')]"></div>
            </div>

            <!-- Labels -->
            <div class="flex flex-col items-end gap-1">
               <span
                 :class="[getCategoryColor(item.category, 'border'), getCategoryColor(item.category, 'text')]"
                 class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border backdrop-blur-md"
               >
                 {{ item.category.toUpperCase() }}
               </span>
              <span v-if="item.isDownloaded" class="flex items-center gap-1 text-[10px] text-green-500 font-bold">
                 <div class="i-carbon-checkmark-filled"></div> READY
               </span>
            </div>
          </div>

          <!-- Title & Bundle Tag -->
          <div class="mb-1 flex items-center gap-2">
            <h3 class="text-xl font-bold text-text-main group-hover:text-primary transition-colors">
              {{ item.name }}
            </h3>
            <span v-if="item.type === 'bundle'"
                  class="text-[10px] px-1.5 py-0.5 rounded bg-bg-surface border border-border/50 text-text-muted font-bold tracking-wide">
              BUNDLE
            </span>
          </div>

          <p class="text-sm text-text-muted leading-relaxed line-clamp-2 mb-4">
            {{ item.description }}
          </p>

          <!-- Meta Tags -->
          <div class="flex flex-wrap gap-2 mb-6">
             <span v-for="tag in item.tags" :key="tag"
                   class="text-[10px] px-2 py-1 rounded bg-bg-surface text-text-muted border border-border/50">
               #{{ tag }}
             </span>
            <span class="text-[10px] px-2 py-1 rounded bg-bg-surface text-text-muted border border-border/50 font-mono">
               {{ formatBytes(item.sizeBytes) }}
             </span>
          </div>

          <!-- Footer / Actions -->
          <div class="mt-auto pt-4 border-t border-border/30 flex flex-col gap-3">

            <div class="flex gap-3 items-center">
              <!-- A. Downloading State -->
              <div v-if="item.status === 'downloading'" class="flex-1 flex flex-col justify-center">
                <div class="flex-between text-xs mb-1">
                  <span class="text-text-muted font-mono">{{ item.progress }}%</span>
                  <span class="text-primary">{{ formatSpeed(item.speed) }}</span>
                </div>
                <div class="h-1.5 w-full bg-bg-surface rounded-full overflow-hidden">
                  <div
                    :class="getCategoryColor(item.category, 'bg')"
                    :style="{ width: `${item.progress}%` }"
                    class="h-full rounded-full relative transition-all duration-300"
                  >
                    <div class="absolute inset-0 bg-white/30 animate-pulse"></div>
                  </div>
                </div>
              </div>

              <!-- B. Error State -->
              <div v-else-if="item.status === 'error'" class="flex-1 text-xs text-red-400 flex items-center gap-2">
                <div class="i-carbon-warning-filled"></div>
                <span>Error occurred</span>
                <button class="underline hover:text-red-300 ml-auto" @click.stop="handleAction(item)">Retry</button>
              </div>

              <!-- C. Idle / Completed State -->
              <template v-else>
                <button
                  v-if="!item.isDownloaded"
                  class="btn-primary flex-1 py-2 text-sm shadow-glow-sm"
                  @click.stop="handleAction(item)"
                >
                  <div class="i-carbon-cloud-download text-lg"></div>
                  <span>Get {{ item.type === 'bundle' ? 'All' : 'Model' }}</span>
                </button>

                <button
                  v-else
                  class="btn-outline flex-1 py-2 text-sm border-dashed opacity-80 cursor-default hover:bg-transparent"
                >
                  <div class="i-carbon-checkbox-checked text-lg text-green-500"></div>
                  <span class="text-text-muted">Installed</span>
                </button>
              </template>

              <!-- Expand Button (Bundle Only) -->
              <button
                v-if="item.type === 'bundle'"
                :class="{ 'rotate-180': expandedBundles.has(item.id) }"
                class="btn-ghost w-10 h-10 p-0 text-text-muted hover:text-primary transition-transform duration-300"
                title="View Bundle Contents"
                @click.stop="toggleExpand(item.id)"
              >
                <div class="i-carbon-chevron-down text-lg"></div>
              </button>
            </div>

            <!-- Expandable Content: Bundle Children -->
            <div
              v-if="item.type === 'bundle' && item.children"
              :class="expandedBundles.has(item.id) ? 'grid-rows-[1fr] opacity-100 mt-2' : 'grid-rows-[0fr] opacity-0 mt-0'"
              class="grid transition-[grid-template-rows,opacity,margin] duration-300 ease-out"
            >
              <div class="overflow-hidden">
                <div class="bg-bg-surface/40 rounded-xl p-3 border border-border/20 space-y-3">
                  <div class="text-[10px] text-text-muted uppercase font-bold tracking-wider flex-between">
                    <span>Included Files</span>
                    <span>{{ item.children.length }} items</span>
                  </div>

                  <div v-for="child in item.children" :key="child.id" class="group/child">
                    <div class="flex-between text-xs mb-1">
                      <span class="text-text-main group-hover/child:text-primary transition-colors truncate pr-2">{{
                          child.name
                        }}</span>
                      <span v-if="child.isDownloaded" class="text-green-500 i-carbon-checkmark"></span>
                      <span v-else-if="child.status === 'downloading'" class="text-primary font-mono">{{
                          child.progress
                        }}%</span>
                      <span v-else class="text-text-muted font-mono">{{ formatBytes(child.sizeBytes) }}</span>
                    </div>
                    <!-- Child Progress -->
                    <div class="h-1 w-full bg-bg-main rounded-full overflow-hidden opacity-60">
                      <div
                        :class="child.isDownloaded ? 'bg-green-500' : getCategoryColor(item.category, 'bg')"
                        :style="{ width: `${child.isDownloaded ? 100 : child.progress}%` }"
                        class="h-full rounded-full transition-all duration-300"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {computed, onMounted, ref} from 'vue';
import {useAiStore} from '@/stores/ai';
import {formatBytes, formatSpeed} from '@/utils/format';
import type {ModelCategory} from '../../../types/ai';

// --- Interfaces ---
interface ResourceItem {
  id: string;
  type: 'single' | 'bundle';
  name: string;
  description: string;
  category: ModelCategory;
  tags: string[];
  sizeBytes: number;
  // Status
  isDownloaded: boolean;
  status: string;
  progress: number;
  speed: number;
  // Bundle only
  children?: ResourceItem[];
}

const aiStore = useAiStore();
const expandedBundles = ref(new Set<string>());

onMounted(() => {
  aiStore.initListener();
  aiStore.fetchModels();
  // asrStore listeners removed
});

const toggleExpand = (id: string) => {
  if (expandedBundles.value.has(id)) expandedBundles.value.delete(id);
  else expandedBundles.value.add(id);
};

// === Core Logic: Smart Aggregation ===
const allResources = computed<ResourceItem[]>(() => {
  const standaloneItems: ResourceItem[] = [];
  const bundleMap = new Map<string, ResourceItem>();

  // 1. Traverse all configs
  aiStore.models.forEach((model: any) => {
    // 过滤掉任何可能残留的 ASR 数据
    if (model.category === 'asr') return;

    // 直接从 aiStore 获取状态，不再需要判断 ASR 的特殊状态
    const statusObj = aiStore.downloadState[model.id] || {status: 'idle', progress: 0, speed: 0};

    // 安全获取 tags
    const originalTags = model.tags || [];

    // 构建统一的资源对象
    const resource: ResourceItem = {
      id: model.id,
      type: 'single', // 默认作为单体
      name: model.name,
      description: model.description,
      category: model.category || 'llm',
      tags: originalTags,
      sizeBytes: model.sizeBytes,
      isDownloaded: model.isDownloaded,
      status: statusObj.status,
      progress: statusObj.progress,
      speed: statusObj.speed || 0,
    };

    // 2. 智能归类 (保留 Bundle 逻辑以备未来使用)
    if (model.bundleId) {
      if (!bundleMap.has(model.bundleId)) {
        const bundle: ResourceItem = {
          id: model.bundleId,
          type: 'bundle',
          name: formatBundleName(model.bundleId),
          description: `Includes components required for the ${model.category.toUpperCase()} module.`,
          category: model.category,
          tags: ['Bundle', ...originalTags],
          sizeBytes: 0,
          isDownloaded: false,
          status: 'idle',
          progress: 0,
          speed: 0,
          children: []
        };
        bundleMap.set(model.bundleId, bundle);
      }

      const parent = bundleMap.get(model.bundleId)!;
      parent.children!.push(resource);
      parent.sizeBytes += resource.sizeBytes;

    } else {
      standaloneItems.push(resource);
    }
  });

  // 3. 计算整合包的综合状态
  bundleMap.forEach(bundle => {
    const children = bundle.children || [];
    if (children.length === 0) return;

    const allDownloaded = children.every(c => c.isDownloaded);
    const anyDownloading = children.some(c => c.status === 'downloading');
    const anyError = children.some(c => c.status === 'error');

    bundle.isDownloaded = allDownloaded;

    if (anyDownloading) {
      bundle.status = 'downloading';
      const totalP = children.reduce((sum, c) => sum + c.progress, 0);
      bundle.progress = Math.floor(totalP / children.length);
      bundle.speed = children.reduce((sum, c) => sum + (c.speed || 0), 0);
    } else if (anyError) {
      bundle.status = 'error';
    } else if (allDownloaded) {
      bundle.status = 'completed';
      bundle.progress = 100;
    } else {
      bundle.status = 'idle';
    }
  });

  return [...standaloneItems, ...bundleMap.values()];
});

// 辅助函数
function formatBundleName(id: string) {
  return id
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
    .replace('Bundle', '') + ' Bundle';
}

// === Action Handlers ===
const handleAction = (item: ResourceItem) => {
  if (item.type === 'bundle') {
    // 整合包下载逻辑
    item.children?.forEach(child => {
      if (!child.isDownloaded) aiStore.downloadModel(child.id);
    });
  } else {
    // 独立下载
    aiStore.downloadModel(item.id);
  }
};

// === Statistics ===
const totalStorage = computed(() => {
  const bytes = allResources.value.reduce((acc, item) => {
    if (item.isDownloaded) return acc + item.sizeBytes;
    return acc;
  }, 0);
  return formatBytes(bytes);
});

const installedCount = computed(() => {
  return allResources.value.filter(i => i.isDownloaded).length;
});

// === Style Helpers ===
function getCategoryColor(cat: string, type: 'bg' | 'text' | 'border' | 'bg-soft'): string {
  switch (cat) {
    case 'llm':
      if (type === 'bg') return 'bg-primary';
      if (type === 'bg-soft') return 'bg-primary/10';
      if (type === 'text') return 'text-primary';
      return 'border-primary/30';
    case 'embedding':
      if (type === 'bg') return 'bg-secondary';
      if (type === 'bg-soft') return 'bg-secondary/10';
      if (type === 'text') return 'text-secondary';
      return 'border-secondary/30';
    // Removed ASR case
    default:
      return type === 'text' ? 'text-text-main' : 'bg-gray-500';
  }
}

function getCategoryIcon(cat: string): string {
  switch (cat) {
    case 'llm':
      return 'i-carbon-chat-bot';
    case 'embedding':
      return 'i-carbon-flow-data';
    // Removed ASR case
    default:
      return 'i-carbon-box';
  }
}
</script>

<style scoped>
.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out forwards;
  opacity: 0;
  transform: translateY(20px);
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-pulse-slow {
  animation: pulse 8s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
