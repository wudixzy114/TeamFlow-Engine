<!-- src/components/dashboard/FocusTimeCard.vue -->
<template>
  <div class="glass-panel w-full h-full flex flex-col p-5 relative overflow-hidden group">
    <!-- Decorator -->
    <div
      class="absolute -right-4 -top-4 w-24 h-24 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-colors duration-500"></div>

    <div class="flex items-start justify-between relative z-10">
      <div>
        <h3 class="text-sm font-medium text-muted mb-1">深度专注时长</h3>
        <div class="flex items-baseline gap-2">
          <span class="text-3xl font-bold text-text tabular-nums tracking-tight">
            {{ totalHours }}
          </span>
          <span class="text-sm font-medium text-muted">hrs</span>
        </div>
      </div>
      <div class="p-2 bg-surface rounded-lg border border-border/10">
        <span class="i-carbon-hourglass text-primary text-lg"></span>
      </div>
    </div>

    <!-- Chart -->
    <div class="flex-1 mt-4 min-h-[100px] w-full">
      <v-chart
        v-if="data && data.daily_trend.length > 0"
        :option="chartOption"
        autoresize
        class="w-full h-full"
      />
      <div v-else class="h-full flex-center text-xs text-muted">
        暂无数据
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {computed} from 'vue';
import * as echarts from 'echarts/core';

const props = defineProps<{
  data: FocusTimeData | null;
}>();

const totalHours = computed(() => {
  return props.data?.total_hours.toFixed(1) || '0.0';
});

const chartOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(20,20,25,0.9)',
    borderColor: 'rgba(255,255,255,0.1)',
    textStyle: {color: '#fff', fontSize: 12},
    padding: [8, 12],
    formatter: '{b}: {c} hrs',
    axisPointer: {type: 'none'} // 隐藏指针线，更简洁
  },
  grid: {top: 5, right: 0, bottom: 0, left: 0},
  xAxis: {
    type: 'category',
    data: props.data?.daily_trend.map(d => d.date) || [],
    show: false
  },
  yAxis: {
    type: 'value',
    show: false
  },
  series: [{
    type: 'bar',
    barWidth: '60%',
    data: props.data?.daily_trend.map(d => d.hours) || [],
    itemStyle: {
      borderRadius: 4,
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        {offset: 0, color: '#22d3ee'}, // primary-hover (Cyan 400)
        {offset: 1, color: 'rgba(34, 211, 238, 0.2)'}
      ])
    },
    emphasis: {
      itemStyle: {
        color: '#67e8f9' // Cyan 300
      }
    }
  }]
}));
</script>
