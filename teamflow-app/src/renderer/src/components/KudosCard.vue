<template>
  <div
    :class="[
      isLargeView ? 'min-h-[400px] rounded-3xl' : 'min-h-[220px] card-interactive',
      themeGradient
    ]"
    class="relative flex flex-col justify-between p-6 overflow-hidden transition-all duration-500 group"
  >
    <!-- 背景装饰光斑 -->
    <div
      class="absolute top-0 right-0 -mt-10 -mr-10 w-32 h-32 bg-white/10 blur-3xl rounded-full pointer-events-none"></div>
    <div
      class="absolute bottom-0 left-0 -mb-10 -ml-10 w-32 h-32 bg-black/20 blur-3xl rounded-full pointer-events-none"></div>

    <!-- 头部 -->
    <div class="relative z-10 flex justify-between items-start">
      <div class="flex flex-col">
        <span class="text-xs font-bold tracking-widest uppercase opacity-70 mb-1">Kudos Card</span>
        <h3 class="text-xl font-bold text-white font-display shadow-black/10 drop-shadow-md">
          {{ kudo.card_type }}
        </h3>
      </div>

      <div
        class="flex items-center gap-2 px-3 py-1 rounded-full bg-black/20 backdrop-blur-md border border-white/10 shadow-sm">
        <div class="i-carbon-user-avatar text-white/80 text-sm"></div>
        <span class="text-xs font-medium text-white">
          {{ kudo.sender?.username || '匿名' }}
        </span>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="relative z-10 flex-grow flex items-center py-4">
      <div class="relative">
        <div class="i-carbon-quotes text-4xl absolute -top-4 -left-2 opacity-20 text-white"></div>
        <p
          :class="isLargeView ? 'text-lg whitespace-pre-wrap' : 'text-base line-clamp-4'"
          class="text-white/95 font-medium leading-relaxed text-shadow-sm"
        >
          {{ kudo.message }}
        </p>
      </div>
    </div>

    <!-- 底部 -->
    <div class="relative z-10 flex justify-between items-end pt-4 border-t border-white/10">
      <div class="flex flex-col">
        <span class="text-[10px] uppercase tracking-wider opacity-60">Received on</span>
        <span class="text-xs font-mono font-semibold opacity-90">{{ formattedDate }}</span>
      </div>

      <!-- 装饰性 Logo 或 图标 -->
      <div
        class="i-carbon-certificate text-2xl opacity-40 group-hover:opacity-100 transition-opacity duration-300"></div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {computed} from 'vue';

const props = defineProps<{
  kudo: Kudos;
  isLargeView?: boolean;
}>();

const formattedDate = computed(() => {
  if (!props.kudo?.created_at) return '';
  return new Date(props.kudo.created_at).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '.');
});

// 基于卡片类型的渐变色映射
const themeGradient = computed(() => {
  const map: Record<string, string> = {
    // 最佳战友：深青色 -> 蓝色
    '最佳战友卡': 'bg-gradient-to-br from-cyan-600 to-blue-700 border border-cyan-400/30 shadow-glow-primary',
    // 技术先锋：紫色 -> 靛蓝
    '技术先锋卡': 'bg-gradient-to-br from-violet-600 to-indigo-700 border border-violet-400/30 shadow-glow-secondary',
    // 创意无限：琥珀色 -> 橙色
    '创意无限卡': 'bg-gradient-to-br from-amber-500 to-orange-600 border border-amber-400/30 shadow-[0_0_20px_rgba(245,158,11,0.3)]',
  };
  return map[props.kudo.card_type] || 'bg-gradient-to-br from-slate-600 to-slate-700 border border-white/10';
});
</script>
