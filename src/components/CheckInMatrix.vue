<template>
  <el-card shadow="hover">
    <template #header>
      <div class="font-bold">每日心智签到</div>
    </template>
    <div class="relative aspect-square w-full max-w-sm mx-auto">
      <!-- Y 轴标签 -->
      <div class="absolute -left-12 top-0 h-full flex flex-col justify-between text-xs text-gray-500 py-1">
        <span>高挑战</span><span>低挑战</span>
      </div>
      <!-- X 轴标签 -->
      <div class="absolute -bottom-8 left-0 w-full flex justify-between text-xs text-gray-500 px-1">
        <span>低能力</span><span>高能力</span>
      </div>
      <!-- 矩阵网格 -->
      <div class="grid grid-cols-8 grid-rows-8 h-full w-full border-2 rounded-lg overflow-hidden">
        <div
            v-for="i in 64"
            :key="i"
            :class="getCellClass(i)"
            class="cell border-gray-200 border-b border-r cursor-pointer transition-all duration-200"
            @click="handleCheckIn(i)"
            @mouseleave="hoveredIndex = null"
            @mouseover="hoveredIndex = i"
        ></div>
      </div>
      <!-- 状态提示 -->
      <div v-if="hoveredState"
           class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white/80 backdrop-blur-sm px-4 py-2 rounded-full shadow-lg pointer-events-none">
        状态: <span :class="`text-${getStateColor(hoveredState)}`" class="font-bold">{{ hoveredState }}</span>
      </div>
    </div>
  </el-card>
</template>

<script lang="ts" setup>
import {ref, computed} from 'vue'
import {useFlowStore, type MentalState} from '@/stores/flow'
import {ElMessage} from "element-plus";

const flowStore = useFlowStore()
const hoveredIndex = ref<number | null>(null)

// 坐标到状态的映射
const getState = (x: number, y: number): MentalState => {
  if (x > 4 && y > 4) return 'Flow'
  if (x <= 4 && y > 4) return 'Anxiety'
  if (x > 4 && y <= 4) return 'Boredom'
  // ... 其他7个状态的精确定义
  if (x > 4 && y > 4) return 'Flow';
  if (x <= 4 && y > 4) return 'Anxiety';
  if (x > 4 && y <= 4) return 'Boredom';
  if (x <= 4 && y <= 4) return 'Apathy';
  // 简化其他状态
  if (x > 6 && y > 6) return 'Arousal';
  if (x < 3 && y > 6) return 'Worry';
  if (x > 6 && y < 3) return 'Relaxation';
  if (x > 4 && x < 7 && y > 4 && y < 7) return 'Control';
  return 'Apathy';
}

const getStateColor = (state: MentalState) => {
  const colorMap = {
    Flow: 'flow',
    Anxiety: 'anxiety',
    Boredom: 'boredom',
    Apathy: 'gray-400',
    Arousal: 'yellow-500',
    Worry: 'red-500',
    Relaxation: 'blue-400',
    Control: 'green-500'
  };
  return colorMap[state] || 'gray-400';
}


const hoveredState = computed(() => {
  if (hoveredIndex.value === null) return null
  const x = (hoveredIndex.value - 1) % 8 + 1
  const y = 8 - Math.floor((hoveredIndex.value - 1) / 8)
  return getState(x, y)
})

const getCellClass = (index: number) => {
  if (hoveredIndex.value === null) return 'bg-gray-50'

  const x = (index - 1) % 8 + 1
  const y = 8 - Math.floor((index - 1) / 8)
  const state = getState(x, y)
  const color = getStateColor(state)

  const hx = (hoveredIndex.value - 1) % 8 + 1
  const hy = 8 - Math.floor((hoveredIndex.value - 1) / 8)
  const hState = getState(hx, hy)

  if (state === hState) {
    return `bg-${color}/60`
  }
  return `bg-${color}/10 opacity-50`
}

const handleCheckIn = (index: number) => {
  const x = (index - 1) % 8 + 1
  const y = 8 - Math.floor((index - 1) / 8)
  const state = getState(x, y)

  ElMessage.success(`签到成功！当前状态: ${state}`)
  flowStore.addEnergyPoint(state)
  // 可以在这里加一个API调用
}
</script>

<style scoped>
.cell:nth-child(8n) {
  border-right: none;
}

.cell:nth-child(n+57) {
  border-bottom: none;
}
</style>