<!--suppress CssUnusedSymbol -->
<template>
  <el-card class="h-full" shadow="hover">
    <template #header>
      <div class="font-bold">实时团队能量场</div>
    </template>
    <div class="relative h-64 w-full bg-gray-800 rounded-lg overflow-hidden">
      <transition-group name="fade">
        <div
            v-for="point in flowStore.energyFeed"
            :key="point.id"
            :style="getPointStyle(point)"
            class="energy-point"
        ></div>
      </transition-group>
    </div>
  </el-card>
</template>

<script lang="ts" setup>
import {useFlowStore, type EnergyPoint} from '@/stores/flow'

const flowStore = useFlowStore()

const colorMap: Record<string, string> = {
  Flow: '#2dd4bf',
  Anxiety: '#f97316',
  Boredom: '#64748b',
  Apathy: '#9ca3af',
  Arousal: '#eab308',
  Worry: '#ef4444',
  Relaxation: '#3b82f6',
  Control: '#22c55e'
};

// 为每个点生成随机位置、颜色，以及动画随机偏移变量
const getPointStyle = (point: EnergyPoint) => {
  const randomTop = Math.random() * 85 + 5; // 5% to 90%
  const randomLeft = Math.random() * 85 + 5; // 5% to 90%
  const i = Math.floor(Math.random() * 6); // 0 to 5
  const j = Math.floor(Math.random() * 6); // 0 to 5
  const randomX = i * 20 - 50; // -50 to 50
  const randomY = j * 20 - 50; // -50 to 50
  return {
    top: `${randomTop}%`,
    left: `${randomLeft}%`,
    backgroundColor: colorMap[point.state] || '#ffffff',
    boxShadow: `0 0 15px 5px ${colorMap[point.state] || '#ffffff'}60`,
    '--random-x': `${randomX}px`,
    '--random-y': `${randomY}px`
  }
}
</script>

<style scoped>
.energy-point {
  position: absolute;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  transition: all 10s cubic-bezier(0.25, 1, 0.5, 1); /* Long transition for smooth movement */
  animation: float 10s ease-in-out infinite alternate;
}

@keyframes float {
  0% {
    transform: translate(0, 0) scale(1);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    /*noinspection CssUnresolvedCustomProperty*/
    transform: translate(calc(var(--random-x, 20px)), calc(var(--random-y, 20px))) scale(1.2);
    opacity: 0;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>