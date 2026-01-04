<!-- src/views/dashboard/DashboardView.vue -->
<template>
  <div class="h-full w-full p-6 md:p-8 flex flex-col gap-6 overflow-hidden">

    <!-- 1. Dashboard Header -->
    <header class="flex flex-col md:flex-row md:items-center justify-between gap-4 flex-shrink-0 animate-slide-in-fast">
      <div>
        <h1 class="text-h1 mb-1">Team Pulse</h1>
        <p class="text-muted">实时感知团队心流状态与效能数据</p>
      </div>

      <!-- Period Selector -->
      <div class="bg-card/50 p-1 rounded-xl border border-border/10 flex items-center">
        <button
          v-for="p in periods"
          :key="p.value"
          :class="dashboardStore.period === p.value ? 'bg-primary text-inverted shadow-lg shadow-primary/20' : 'text-muted hover:text-text hover:bg-surface'"
          class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200"
          @click="dashboardStore.setPeriod(p.value)"
        >
          {{ p.label }}
        </button>
      </div>
    </header>

    <!-- 2. Main Grid Layout -->
    <!-- 左侧大图 (60%)，右侧两张小图堆叠 (40%) -->
    <div class="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-6 pb-4">

      <!-- Left Column: Flow Compass -->
      <div class="lg:col-span-7 h-full min-h-[400px] animate-enter" style="animation-delay: 100ms">
        <FlowMoodChart :data="dashboardStore.compassData"/>
      </div>

      <!-- Right Column: Metrics & Insights -->
      <div class="lg:col-span-5 flex flex-col gap-6 h-full animate-enter" style="animation-delay: 200ms">

        <!-- Top Right: Focus Time -->
        <div class="h-[180px] flex-shrink-0">
          <FocusTimeCard :data="dashboardStore.focusTimeData"/>
        </div>

        <!-- Bottom Right: Word Cloud -->
        <div class="flex-1 min-h-[200px]">
          <InsightWordCloud :data="dashboardStore.insightsData"/>
        </div>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div
      v-if="dashboardStore.isLoading"
      class="absolute inset-0 bg-bg-main/50 backdrop-blur-sm z-50 flex-center"
    >
      <div class="col-center gap-4">
        <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
        <span class="text-sm font-medium text-primary animate-pulse">Syncing Data...</span>
      </div>
    </div>

  </div>
</template>

<script lang="ts" setup>
import {onMounted} from 'vue';
import {useDashboardStore} from '@/stores/dashboard';
import FlowMoodChart from '@/components/dashboard/FlowMoodChart.vue';
import FocusTimeCard from '@/components/dashboard/FocusTimeCard.vue';
import InsightWordCloud from '@/components/dashboard/InsightWordCloud.vue';

const dashboardStore = useDashboardStore();

const periods = [
  {label: 'Today', value: 'day'},
  {label: 'This Week', value: 'week'},
  {label: 'This Month', value: 'month'},
] as const;

onMounted(() => {
  dashboardStore.fetchAllDashboardData();
});
</script>
