<template>
  <div>
    <h1 class="text-3xl font-bold mb-6">团队心流仪表盘</h1>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left Column (Perception) -->
      <div class="lg:col-span-2 space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <CheckInMatrix/>
          <EnergyFeed/>
        </div>
        <InsightCloud/>
      </div>

      <!-- Right Column (Guardian & Interaction) -->
      <div class="space-y-6">
        <FocusAnalytics/>
        <TeamStatusList/>
        <InsightCollector @submit="handleInsightSubmit"/>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ElMessage} from 'element-plus';
import CheckInMatrix from '@/components/CheckInMatrix.vue';
import EnergyFeed from '@/components/EnergyFeed.vue';
import InsightCloud from '@/components/InsightCloud.vue';
import InsightCollector from '@/components/InsightCollector.vue'; // 我们需要创建这个组件
import {useFlowStore} from '@/stores/flow';
import FocusAnalytics from '@/components/guardian/FocusAnalytics.vue';
import TeamStatusList from '@/components/guardian/TeamStatusList.vue';

const flowStore = useFlowStore();

const handleInsightSubmit = ({type, text}: { type: 'booster' | 'blocker', text: string }) => {
  if (!text.trim()) {
    ElMessage.warning('内容不能为空');
    return;
  }
  flowStore.addInsight(type, text.trim());
  ElMessage.success('感谢你的分享！');
};
</script>