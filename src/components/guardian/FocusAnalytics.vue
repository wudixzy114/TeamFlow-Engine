<template>
  <el-card shadow="hover">
    <template #header>
      <div class="font-bold">团队专注力分析</div>
    </template>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <v-chart :option="gaugeOption" autoresize class="h-52"/>
        <div class="text-center text-sm text-gray-500 -mt-4">深度工作时间占比</div>
      </div>
      <div>
        <v-chart :option="barOption" autoresize class="h-52"/>
      </div>
    </div>
  </el-card>
</template>

<script lang="ts" setup>
import {computed} from 'vue';
import {useFlowStore} from '@/stores/flow';
import {use} from 'echarts/core';
import {CanvasRenderer} from 'echarts/renderers';
import {GaugeChart, BarChart} from 'echarts/charts';
import {TitleComponent, TooltipComponent, GridComponent, LegendComponent} from 'echarts/components';
import VChart from 'vue-echarts';

use([CanvasRenderer, GaugeChart, BarChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent]);

const flowStore = useFlowStore();

const gaugeOption = computed(() => ({
  series: [
    {
      type: 'gauge',
      progress: {show: true, width: 12},
      axisLine: {lineStyle: {width: 12}},
      axisTick: {show: false},
      splitLine: {show: false},
      axisLabel: {show: false},
      anchor: {show: false},
      pointer: {show: false},
      title: {show: false},
      detail: {
        valueAnimation: true,
        fontSize: 24,
        fontWeight: 'bold',
        offsetCenter: [0, 0],
        formatter: '{value}%'
      },
      data: [{value: flowStore.focusAnalytics.deepWorkPercentage}]
    }
  ]
}));

const barOption = computed(() => ({
  tooltip: {trigger: 'axis'},
  grid: {left: '3%', right: '4%', bottom: '3%', containLabel: true},
  xAxis: {
    type: 'category',
    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  },
  yAxis: {type: 'value', name: '小时'},
  series: [
    {
      name: '专注时长',
      type: 'bar',
      barWidth: '60%',
      data: flowStore.focusAnalytics.weeklyFocusHours,
      itemStyle: {color: '#4f46e5'}
    }
  ]
}));
</script>