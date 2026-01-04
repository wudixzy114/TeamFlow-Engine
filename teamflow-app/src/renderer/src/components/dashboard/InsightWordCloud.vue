<!-- src/components/dashboard/InsightWordCloud.vue -->
<template>
  <div class="glass-panel w-full h-full flex flex-col">
    <!-- Header with Tabs -->
    <div class="px-5 py-4 border-b border-border/10 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="i-carbon-ibm-watson-discovery text-accent text-lg"></span>
        <h3 class="text-sm font-bold text-text">AI 团队洞察</h3>
      </div>

      <!-- Pill Tabs -->
      <div class="flex bg-surface/50 rounded-lg p-1 border border-border/10">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="currentTab === tab.id ? 'text-white' : 'text-muted hover:text-text'"
          class="relative px-3 py-1 text-xs font-medium rounded transition-all duration-200 z-10 flex items-center gap-1.5"
          @click="currentTab = tab.id"
        >
          <!-- Active Background -->
          <div
            v-if="currentTab === tab.id"
            class="absolute inset-0 bg-border/20 rounded shadow-sm -z-10"
          ></div>

          <span :class="tab.icon"></span>
          {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 relative w-full min-h-[200px]">
      <transition mode="out-in" name="fade">
        <v-chart
          v-if="hasData"
          :key="currentTab"
          :option="chartOption"
          autoresize
          class="w-full h-full"
        />

        <!-- Empty State -->
        <div v-else class="absolute inset-0 flex-center flex-col gap-3 text-muted">
          <div class="i-carbon-phrase-sentiment text-4xl opacity-20"></div>
          <p class="text-xs">暂无{{ currentTab === 'boosters' ? '助推' : '障碍' }}分析</p>
        </div>
      </transition>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref, computed} from 'vue';
import 'echarts-wordcloud'; // 必须引入

const props = defineProps<{
  data: AIInsights | null;
}>();

type TabType = 'boosters' | 'blockers';
const currentTab = ref<TabType>('boosters');

const tabs = [
  {id: 'boosters', label: '助推剂', icon: 'i-carbon-rocket'},
  {id: 'blockers', label: '障碍点', icon: 'i-carbon-road-barrier'}
] as const;

const currentData = computed(() => {
  if (!props.data) return [];
  return currentTab.value === 'boosters'
    ? props.data.boosters_wordcloud
    : props.data.blockers_wordcloud;
});

const hasData = computed(() => currentData.value && currentData.value.length > 0);

const chartOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    show: true,
    backgroundColor: 'rgba(20,20,25,0.9)',
    borderColor: 'rgba(255,255,255,0.1)',
    textStyle: {color: '#fff'}
  },
  series: [{
    type: 'wordCloud',
    shape: 'circle',
    left: 'center', top: 'center',
    width: '95%', height: '95%',
    sizeRange: [12, 40],
    rotationRange: [-45, 90],
    gridSize: 10,
    drawOutOfBound: false,
    textStyle: {
      fontFamily: 'Inter',
      fontWeight: 'bold',
      color: () => {
        // Boosters: Cool/Vibrant colors; Blockers: Warm/Warning colors
        const boostersColors = ['#22d3ee', '#3b82f6', '#818cf8', '#34d399', '#f472b6'];
        const blockersColors = ['#ef4444', '#f97316', '#fbbf24', '#f87171', '#fb923c'];

        const palette = currentTab.value === 'boosters' ? boostersColors : blockersColors;
        return palette[Math.floor(Math.random() * palette.length)];
      }
    },
    emphasis: {
      textStyle: {
        shadowBlur: 10,
        shadowColor: '#333'
      }
    },
    data: currentData.value
  }]
}));
</script>
