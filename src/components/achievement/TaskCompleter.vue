<template>
  <el-card shadow="hover">
    <template #header>
      <div class="font-bold">完成任务，链接意义</div>
    </template>
    <div class="flex space-x-3">
      <el-input v-model="taskName" placeholder="输入你刚完成的任务名"/>
      <el-button :disabled="!taskName.trim()" type="success" @click="completeTask">我完成了！</el-button>
    </div>
  </el-card>
</template>

<script lang="ts" setup>
import {ref} from 'vue';
import {useFlowStore} from '@/stores/flow';
import {ElNotification} from 'element-plus';

const taskName = ref('用户登录模块重构');
const flowStore = useFlowStore();

const completeTask = () => {
  const meaning = flowStore.getMeaningLink(taskName.value);
  ElNotification({
    title: '🎉 任务完成！意义非凡！',
    message: meaning,
    type: 'success',
    duration: 6000,
  });
  taskName.value = '';
};
</script>