<template>
  <el-card shadow="hover">
    <template #header>
      <div class="font-bold">分享你的洞察</div>
    </template>
    <div class="space-y-4">
      <div>
        <label class="text-sm font-medium text-gray-700">今天成就我的是什么？ (心流助推剂)</label>
        <el-input v-model="boosterText" placeholder="例如：一个清晰的需求文档" type="textarea"/>
      </div>
      <div>
        <label class="text-sm font-medium text-gray-700">今天阻碍我的是什么？ (心流障碍物)</label>
        <el-input v-model="blockerText" placeholder="例如：频繁的会议打扰" type="textarea"/>
      </div>
      <el-button class="w-full" type="primary" @click="submitInsights">匿名分享</el-button>
    </div>
  </el-card>
</template>

<script lang="ts" setup>
import {ref} from 'vue';

const boosterText = ref('');
const blockerText = ref('');
const emit = defineEmits(['submit']);

const submitInsights = () => {
  if (boosterText.value) {
    emit('submit', {type: 'booster', text: boosterText.value});
    boosterText.value = '';
  }
  if (blockerText.value) {
    emit('submit', {type: 'blocker', text: blockerText.value});
    blockerText.value = '';
  }
};
</script>