<!-- src/components/dashboard/FlowMoodChart.vue -->
<template>
  <div class="glass-panel w-full h-full flex flex-col p-1">
    <!-- Header -->
    <div class="flex items-center justify-between px-5 py-4 border-b border-border/10">
      <div class="flex items-center gap-3">
        <div class="p-2 rounded-lg bg-primary/10 text-primary">
          <span class="i-carbon-chart-radar text-xl"></span>
        </div>
        <div>
          <h3 class="text-sm font-bold text-text">心流罗盘</h3>
          <p class="text-xs text-muted">基于 Csikszentmihalyi 心流模型</p>
        </div>
      </div>

      <!-- Legend -->
      <div class="flex gap-4 text-xs">
        <div class="flex items-center gap-1.5 text-muted">
          <span class="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_rgb(var(--c-primary))]"></span>
          <span>Flow</span>
        </div>
        <div class="flex items-center gap-1.5 text-muted">
          <span class="w-2 h-2 rounded-full bg-accent/80"></span>
          <span>State</span>
        </div>
      </div>
    </div>

    <!-- Chart Container -->
    <div class="flex-1 relative w-full min-h-[350px]">
      <v-chart
        v-if="data"
        :option="chartOption"
        autoresize
        class="w-full h-full"
      />
      <!-- Empty State -->
      <div v-else class="absolute inset-0 flex-center text-muted gap-2">
        <span class="i-carbon-chart-line text-2xl opacity-50"></span>
        <span class="text-sm">暂无轨迹数据</span>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {computed} from 'vue';
import * as echarts from 'echarts/core';
// 确保在 main.ts 中注册了必要的 ECharts 组件，或者在这里 import

const props = defineProps<{
  data: CompassData | null;
}>();

// 颜色常量 (与 style.css 对应)
const COLORS = {
  flow: '#06b6d4',    // Cyan (Primary)
  anxiety: '#8b5cf6', // Violet (Secondary)
  boredom: '#94a3b8', // Slate (Muted)
  apathy: '#ef4444',  // Red (Error)
  text: '#cbd5e1',    // Slate 300
  grid: 'rgba(255,255,255,0.05)'
};

const chartOption = computed(() => {
  if (!props.data) return {};

  const trendData = props.data.trend_data.map((d) => [d.avg_skill, d.avg_challenge, d.date]);

  return {
    backgroundColor: 'transparent',
    grid: {top: 40, right: 40, bottom: 30, left: 40, containLabel: true},
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(20, 20, 25, 0.9)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: {color: '#E2E8F0', fontFamily: 'Inter', fontSize: 12},
      padding: [10, 14],
      backdropFilter: 'blur(4px)',
      formatter: (params: any) => {
        const [skill, challenge, date] = params.value;
        return `
          <div class="font-bold mb-1">${date}</div>
          <div class="text-xs flex items-center justify-between gap-4">
            <span class="text-gray-400">技能 (Skill)</span>
            <span class="font-mono text-cyan-400">${skill.toFixed(2)}</span>
          </div>
          <div class="text-xs flex items-center justify-between gap-4">
            <span class="text-gray-400">挑战 (Challenge)</span>
            <span class="font-mono text-purple-400">${challenge.toFixed(2)}</span>
          </div>
        `;
      }
    },
    xAxis: {
      name: '技能 →',
      nameLocation: 'middle',
      nameGap: 25,
      type: 'value',
      min: -1, max: 1,
      nameTextStyle: {color: COLORS.text, fontSize: 10, opacity: 0.7},
      axisLabel: {color: COLORS.text, fontFamily: 'JetBrains Mono', fontSize: 10},
      splitLine: {show: true, lineStyle: {color: COLORS.grid, type: 'dashed'}},
      axisLine: {lineStyle: {color: 'rgba(255,255,255,0.1)'}}
    },
    yAxis: {
      name: '挑战 ↑',
      nameLocation: 'middle',
      nameGap: 30,
      type: 'value',
      min: -1, max: 1,
      nameTextStyle: {color: COLORS.text, fontSize: 10, opacity: 0.7},
      axisLabel: {color: COLORS.text, fontFamily: 'JetBrains Mono', fontSize: 10},
      splitLine: {show: true, lineStyle: {color: COLORS.grid, type: 'dashed'}},
      axisLine: {lineStyle: {color: 'rgba(255,255,255,0.1)'}}
    },
    series: [
      {
        name: 'Team Trend',
        type: 'line',
        smooth: 0.4,
        symbol: 'circle',
        symbolSize: 8,
        data: trendData,
        lineStyle: {
          width: 3,
          shadowColor: 'rgba(6, 182, 212, 0.5)',
          shadowBlur: 10,
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            {offset: 0, color: COLORS.anxiety},
            {offset: 1, color: COLORS.flow}
          ])
        },
        itemStyle: {
          color: '#0B0E14',
          borderColor: '#fff',
          borderWidth: 2
        },
        // 区域背景划分
        markArea: {
          silent: true,
          itemStyle: {opacity: 0.6}, // 透明度
          data: [
            // Flow: High Skill, High Challenge (右上)
            [{coord: [0.2, 0.2], itemStyle: {color: 'rgba(6, 182, 212, 0.08)'}}, {coord: [1, 1]}],
            // Anxiety: Low Skill, High Challenge (左上)
            [{coord: [-1, 0.2], itemStyle: {color: 'rgba(139, 92, 246, 0.05)'}}, {coord: [-0.2, 1]}],
            // Boredom: Low Skill, Low Challenge (左下)
            [{coord: [-1, -1], itemStyle: {color: 'rgba(148, 163, 184, 0.05)'}}, {coord: [-0.2, -0.2]}],
            // Relaxation: High Skill, Low Challenge (右下)
            [{coord: [0.2, -1], itemStyle: {color: 'rgba(16, 185, 129, 0.05)'}}, {coord: [1, -0.2]}]
          ]
        }
      }
    ],
    // 静态文字标签
    graphic: [
      {
        type: 'text',
        right: '12%',
        top: '15%',
        style: {text: '🌊 FLOW', fill: COLORS.flow, font: '800 14px Inter', opacity: 0.4}
      },
      {
        type: 'text',
        left: '12%',
        top: '15%',
        style: {text: '😰 ANXIETY', fill: COLORS.anxiety, font: '800 14px Inter', opacity: 0.4}
      },
      {
        type: 'text',
        left: '12%',
        bottom: '15%',
        style: {text: '😴 BOREDOM', fill: COLORS.boredom, font: '800 14px Inter', opacity: 0.4}
      },
      {
        type: 'text',
        right: '12%',
        bottom: '15%',
        style: {text: '😌 RELAX', fill: '#34d399', font: '800 14px Inter', opacity: 0.4}
      },
    ]
  };
});
</script>
