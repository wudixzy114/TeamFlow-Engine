<!-- src/components/checkin/FlowCompass.vue -->
<template>
  <div class="flex flex-col items-center gap-4">
    <!-- 状态反馈头 -->
    <div class="h-8 flex items-center justify-center transition-all duration-300">
      <div v-if="currentState" class="flex items-center gap-2 animate-slide-in-fast">
        <span :class="[currentState.color, 'font-bold text-lg']">{{ currentState.label }}</span>
        <span class="text-muted text-xs border-l border-border/30 pl-2">{{ currentState.description }}</span>
      </div>
      <div v-else class="text-muted text-sm">点击或拖拽选择当前状态</div>
    </div>

    <!-- 罗盘主体 -->
    <div
      ref="compassRef"
      class="relative w-64 h-64 bg-surface/30 rounded-2xl border border-border/20 shadow-inner cursor-crosshair touch-none select-none overflow-hidden group"
      @pointerdown="handlePointerDown"
      @pointerleave="handlePointerUp"
      @pointermove="handlePointerMove"
      @pointerup="handlePointerUp"
    >
      <!-- 背景网格与轴线 -->
      <div class="absolute inset-0 opacity-20 bg-grid-pattern"></div>

      <!-- X轴 (Skill) -->
      <div
        class="absolute top-1/2 left-0 w-full h-px bg-border/40 flex justify-between items-center px-2 text-[10px] text-muted font-mono">
        <span>Low Skill</span>
        <span>High Skill</span>
      </div>

      <!-- Y轴 (Challenge) -->
      <div
        class="absolute left-1/2 top-0 h-full w-px bg-border/40 flex flex-col justify-between items-center py-2 text-[10px] text-muted font-mono">
        <span class="bg-surface/80 px-1 rounded">High Challenge</span>
        <span class="bg-surface/80 px-1 rounded">Low Challenge</span>
      </div>

      <!-- Flow 通道 (对角线提示) -->
      <div
        class="absolute inset-0 bg-gradient-to-tr from-transparent via-primary/5 to-primary/10 pointer-events-none"></div>

      <!-- 交互点 -->
      <div
        :style="{
          left: `${pointerPosition.x}%`,
          top: `${pointerPosition.y}%`,
          transform: isDragging ? 'scale(1.2)' : 'scale(1)'
        }"
        class="absolute w-5 h-5 -ml-2.5 -mt-2.5 rounded-full bg-primary shadow-[0_0_15px_rgb(var(--c-primary))] border-2 border-white transition-transform duration-75 ease-out will-change-transform z-10"
      >
        <!-- 波动光环动画 -->
        <div class="absolute inset-0 rounded-full animate-ping bg-primary/50"></div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref, computed, onMounted, watch} from 'vue';
import {getFlowState} from '@/utils/flow-state'; // 假设放在这里

// Props: 接收双向绑定的值 (-1 到 1)
const props = defineProps<{
  challenge: number;
  skill: number;
}>();

const emit = defineEmits<{
  (e: 'update:challenge', val: number): void;
  (e: 'update:skill', val: number): void;
}>();

const compassRef = ref<HTMLDivElement | null>(null);
const isDragging = ref(false);

// 内部 UI 坐标 (0-100%)
const pointerPosition = computed(() => ({
  x: (props.skill + 1) / 2 * 100,
  y: (1 - props.challenge) / 2 * 100 // Y轴反转，上面是1
}));

// 计算当前状态文本
const currentState = computed(() => getFlowState(props.skill, props.challenge));

// 坐标转换逻辑
const updateValueFromEvent = (e: PointerEvent) => {
  if (!compassRef.value) return;

  const rect = compassRef.value.getBoundingClientRect();

  // 计算 0-1 的相对位置
  let x = (e.clientX - rect.left) / rect.width;
  let y = (e.clientY - rect.top) / rect.height;

  // 限制边界
  x = Math.max(0, Math.min(1, x));
  y = Math.max(0, Math.min(1, y));

  // 转换为 -1 到 1
  // Skill: Left(-1) -> Right(1)
  const skillVal = Number((x * 2 - 1).toFixed(2));
  // Challenge: Top(1) -> Bottom(-1) -> UI y is 0 at top
  const challengeVal = Number(((1 - y) * 2 - 1).toFixed(2));

  emit('update:skill', skillVal);
  emit('update:challenge', challengeVal);
};

const handlePointerDown = (e: PointerEvent) => {
  isDragging.value = true;
  compassRef.value?.setPointerCapture(e.pointerId);
  updateValueFromEvent(e);
};

const handlePointerMove = (e: PointerEvent) => {
  if (!isDragging.value) return;
  updateValueFromEvent(e);
};

const handlePointerUp = (e: PointerEvent) => {
  isDragging.value = false;
  compassRef.value?.releasePointerCapture(e.pointerId);
};
</script>
