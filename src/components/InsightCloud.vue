<template>
  <el-card class="h-full" shadow="hover">
    <template #header>
      <div class="flex justify-between items-center">
        <span class="font-bold">心流助推剂 & 障碍物</span>
        <el-radio-group v-model="activeTab" size="small">
          <el-radio-button label="boosters">助推剂</el-radio-button>
          <el-radio-button label="blockers">障碍物</el-radio-button>
        </el-radio-group>
      </div>
    </template>
    <v-chart :option="chartOption" autoresize class="h-64"/>
  </el-card>
</template>

<script lang="ts" setup>
import {ref, computed} from 'vue';
import {useFlowStore} from '@/stores/flow';
import {use} from 'echarts/core';
import {CanvasRenderer} from 'echarts/renderers';
import {GridComponent} from 'echarts/components';
import VChart from 'vue-echarts';
import 'echarts-wordcloud';

use([CanvasRenderer, GridComponent]);

const flowStore = useFlowStore();
const activeTab = ref<'boosters' | 'blockers'>('boosters');

const chartOption = computed(() => {
  const data = activeTab.value === 'boosters'
      ? flowStore.insights.boosters
      : flowStore.insights.blockers;

  return {
    tooltip: {show: true},
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      left: 'center',
      top: 'center',
      width: '100%',
      height: '100%',
      sizeRange: [12, 40],
      rotationRange: [-45, 45],
      textStyle: {
        fontFamily: 'sans-serif',
        fontWeight: 'bold',
        color: () => {
          // 随机颜色
          return 'rgb(' + [
            Math.round(Math.random() * 160),
            Math.round(Math.random() * 160),
            Math.round(Math.random() * 160)
          ].join(',') + ')';
        }
      },
      data: data.map(item => ({name: item.text, value: item.value}))
    }]
  };
});
</script>