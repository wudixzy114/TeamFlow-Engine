<template>
  <el-card shadow="hover">
    <template #header>
      <div class="font-bold">发布高光时刻</div>
    </template>
    <div class="flex space-x-3">
      <el-input
          v-model="content"
          :rows="2"
          placeholder="分享一个胜利、一次突破，或一句感谢..."
          resize="none"
          type="textarea"
      />
      <el-button :disabled="!content.trim()" type="primary" @click="publish">发布</el-button>
    </div>
  </el-card>
</template>

<script lang="ts" setup>
import {ref} from 'vue';
import {useFlowStore} from '@/stores/flow';

const content = ref('');
const flowStore = useFlowStore();

const publish = () => {
  flowStore.addHighlight(content.value);
  content.value = '';
};
</script>