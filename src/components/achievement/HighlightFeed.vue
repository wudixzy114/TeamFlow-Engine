<template>
  <el-card shadow="hover">
    <template #header>
      <div class="font-bold">团队高光时刻</div>
    </template>
    <el-scrollbar height="300px">
      <div v-if="flowStore.achievements.highlights.length === 0" class="text-center text-gray-400 py-8">
        暂无高光时刻，期待你的第一次分享！
      </div>
      <div v-else class="space-y-4 pr-4">
        <div v-for="item in flowStore.achievements.highlights" :key="item.id" class="flex space-x-3">
          <el-avatar :src="item.avatar"/>
          <div class="flex-1">
            <div class="flex justify-between items-baseline">
              <span class="font-semibold text-sm">{{ item.author }}</span>
              <span class="text-xs text-gray-400">{{ formatTimeAgo(item.timestamp) }}</span>
            </div>
            <p class="text-sm bg-gray-100 p-2 rounded-lg mt-1">{{ item.content }}</p>
          </div>
        </div>
      </div>
    </el-scrollbar>
  </el-card>
</template>

<script lang="ts" setup>
import {useFlowStore} from '@/stores/flow';

const flowStore = useFlowStore();

// 简单的相对时间格式化函数
const formatTimeAgo = (timestamp: number) => {
  const now = Date.now();
  const seconds = Math.floor((now - timestamp) / 1000);
  let interval = seconds / 31536000;
  if (interval > 1) return Math.floor(interval) + " 年前";
  interval = seconds / 2592000;
  if (interval > 1) return Math.floor(interval) + " 月前";
  interval = seconds / 86400;
  if (interval > 1) return Math.floor(interval) + " 天前";
  interval = seconds / 3600;
  if (interval > 1) return Math.floor(interval) + " 小时前";
  interval = seconds / 60;
  if (interval > 1) return Math.floor(interval) + " 分钟前";
  return "刚刚";
};
</script>