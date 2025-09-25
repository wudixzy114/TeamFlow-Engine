<template>
  <el-card shadow="hover">
    <template #header>
      <div class="font-bold">团队技能树</div>
    </template>
    <v-chart :option="chartOption" autoresize class="h-80"/>
  </el-card>
</template>

<script lang="ts" setup>
import {computed} from 'vue';
import {useFlowStore} from '@/stores/flow';
import {use} from 'echarts/core';
import {CanvasRenderer} from 'echarts/renderers';
import {TreeChart} from 'echarts/charts';
import {TooltipComponent} from 'echarts/components';
import VChart from 'vue-echarts';

use([CanvasRenderer, TreeChart, TooltipComponent]);

const flowStore = useFlowStore();

const chartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    triggerOn: 'mousemove',
    formatter: '{b}: 掌握度 {c}'
  },
  series: [
    {
      type: 'tree',
      data: [flowStore.skillTree],
      top: '5%',
      left: '15%',
      bottom: '2%',
      right: '15%',
      symbolSize: 10,
      label: {
        position: 'left',
        verticalAlign: 'middle',
        align: 'right'
      },
      leaves: {
        label: {
          position: 'right',
          verticalAlign: 'middle',
          align: 'left'
        }
      },
      emphasis: {
        focus: 'descendant'
      },
      expandAndCollapse: true,
      animationDuration: 550,
      animationDurationUpdate: 750
    }
  ]
}));
</script>