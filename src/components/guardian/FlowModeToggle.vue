<template>
  <div class="flex items-center space-x-2">
    <span :class="userStore.isInFlowMode ? 'text-flow' : 'text-gray-600'" class="text-sm font-medium">
      心流模式
    </span>
    <el-switch
        v-model="userStore.isInFlowMode"
        active-color="var(--el-color-success)"
        active-icon="i-ep-sunrise"
        inactive-icon="i-ep-moon"
        inline-prompt
        @change="userStore.toggleFlowMode"
    />
  </div>
</template>

<script lang="ts" setup>
import {useUserStore} from '@/stores/user'

const userStore = useUserStore()
</script>