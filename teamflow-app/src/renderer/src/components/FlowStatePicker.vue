<template>
  <div class="w-full flex-center py-4">
    <!--
      雷达容器
      relative: 用于定位内部元素
      aspect-square: 保持正方形
      cursor-crosshair: 鼠标样式改为十字准星
    -->
    <div
      ref="planeRef"
      class="relative w-full max-w-[380px] aspect-square rounded-2xl border border-white/10 bg-[#0B0E14] overflow-hidden cursor-crosshair shadow-2xl select-none group"
      @click="handlePlaneClick"
    >
      <!-- ================= 背景层：象限光晕 ================= -->
      <!-- 右上：心流 (Cyan) -->
      <div
        class="absolute top-0 right-0 w-3/4 h-3/4 bg-[radial-gradient(circle_at_top_right,rgba(6,182,212,0.15),transparent_70%)] pointer-events-none"></div>
      <!-- 左上：焦虑 (Purple) -->
      <div
        class="absolute top-0 left-0 w-3/4 h-3/4 bg-[radial-gradient(circle_at_top_left,rgba(139,92,246,0.15),transparent_70%)] pointer-events-none"></div>
      <!-- 右下：无聊 (Slate) -->
      <div
        class="absolute bottom-0 right-0 w-3/4 h-3/4 bg-[radial-gradient(circle_at_bottom_right,rgba(148,163,184,0.1),transparent_70%)] pointer-events-none"></div>
      <!-- 左下：冷漠 (Red) -->
      <div
        class="absolute bottom-0 left-0 w-3/4 h-3/4 bg-[radial-gradient(circle_at_bottom_left,rgba(239,68,68,0.1),transparent_70%)] pointer-events-none"></div>

      <!-- ================= 装饰层：网格系统 ================= -->
      <!-- 细微网格背景 -->
      <div class="absolute inset-0 opacity-20 pointer-events-none"
           style="background-image: linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px); background-size: 40px 40px;">
      </div>

      <!-- 中心轴线 -->
      <div class="absolute top-0 bottom-0 left-1/2 w-px bg-white/20 z-0"></div>
      <div class="absolute left-0 right-0 top-1/2 h-px bg-white/20 z-0"></div>

      <!-- ================= 交互层：光标点 ================= -->
      <div
        v-if="modelValue"
        :style="markerStyle"
        class="absolute z-20 -translate-x-1/2 -translate-y-1/2 pointer-events-none transition-all duration-300 ease-out"
      >
        <!-- 核心点 -->
        <div class="w-4 h-4 bg-white rounded-full shadow-[0_0_10px_#fff] relative flex-center">
          <!-- 扩散波纹动画 -->
          <div class="absolute inset-0 rounded-full bg-primary animate-ping opacity-75"></div>
          <!-- 十字瞄准线 -->
          <div
            class="absolute w-[200vh] h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent opacity-50"></div>
          <div
            class="absolute h-[200vh] w-[1px] bg-gradient-to-b from-transparent via-cyan-500/50 to-transparent opacity-50"></div>
        </div>

        <!-- 当前坐标数值浮窗 (可选，随光标移动) -->
        <div
          class="absolute top-6 left-6 bg-black/80 border border-white/10 px-2 py-1 rounded text-[10px] font-mono text-cyan-400 whitespace-nowrap backdrop-blur-sm">
          x:{{ modelValue.skill_level }} y:{{ modelValue.challenge_level }}
        </div>
      </div>

      <!-- ================= 文本层：标签 ================= -->
      <!-- 象限名称 (大水印风格) -->
      <span class="absolute top-4 left-4 text-xs font-bold tracking-widest text-purple-500/50 uppercase">Anxiety</span>
      <span class="absolute top-4 right-4 text-xs font-bold tracking-widest text-cyan-500/80 uppercase animate-pulse">Flow</span>
      <span class="absolute bottom-4 left-4 text-xs font-bold tracking-widest text-red-500/40 uppercase">Apathy</span>
      <span
        class="absolute bottom-4 right-4 text-xs font-bold tracking-widest text-slate-400/40 uppercase">Boredom</span>

      <!-- 轴线标签 (极简风格) -->
      <div class="absolute top-1 left-1/2 -translate-x-1/2 text-[10px] font-mono text-text-muted bg-[#0B0E14]/50 px-1">
        High Challenge
      </div>
      <div
        class="absolute bottom-1 left-1/2 -translate-x-1/2 text-[10px] font-mono text-text-muted bg-[#0B0E14]/50 px-1">
        Low Challenge
      </div>
      <div
        class="absolute left-1 top-1/2 -translate-y-1/2 text-[10px] font-mono text-text-muted bg-[#0B0E14]/50 px-1 vertical-rl rotate-180">
        Low Skill
      </div>
      <div
        class="absolute right-1 top-1/2 -translate-y-1/2 text-[10px] font-mono text-text-muted bg-[#0B0E14]/50 px-1 vertical-rl rotate-180">
        High Skill
      </div>

    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref, computed} from 'vue';

interface Point {
  skill_level: number;
  challenge_level: number;
}

const props = defineProps<{
  modelValue: Point | null;
}>();

const emit = defineEmits(['update:modelValue']);

const planeRef = ref<HTMLElement | null>(null);

// 计算光标位置
const markerStyle = computed(() => {
  if (!props.modelValue) return {display: 'none'};

  // 数学映射: [-1, 1] -> [0%, 100%]
  const left = (props.modelValue.skill_level + 1) / 2 * 100;
  const top = (1 - props.modelValue.challenge_level) / 2 * 100; // Y轴翻转，因为CSS top是从上到下的

  return {
    left: `${left}%`,
    top: `${top}%`,
  };
});

const handlePlaneClick = (event: MouseEvent) => {
  if (!planeRef.value) return;

  const rect = planeRef.value.getBoundingClientRect();
  // 确保坐标相对于容器
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  // 归一化 [0, 1]
  const normalizedX = Math.max(0, Math.min(1, x / rect.width));
  const normalizedY = Math.max(0, Math.min(1, y / rect.height));

  // 映射回 [-1, 1]
  // Skill (X): 0 -> -1, 1 -> 1
  const skill_level = parseFloat((normalizedX * 2 - 1).toFixed(2));
  // Challenge (Y): 0(top) -> 1, 1(bottom) -> -1
  const challenge_level = parseFloat((1 - normalizedY * 2).toFixed(2));

  emit('update:modelValue', {
    skill_level,
    challenge_level,
  });
};
</script>

<style scoped>
/* 定义竖排文字的辅助类 */
.vertical-rl {
  writing-mode: vertical-rl;
}
</style>
