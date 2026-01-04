<script lang="ts" setup>
import {ref, computed} from 'vue';
import {useLoop} from '@tresjs/core';
import {Html} from '@tresjs/cientos';

const props = defineProps<{
  node: any;
  isSelected: boolean;
  isHighlighted: boolean;
}>();

const emit = defineEmits(['click', 'right-click']);

const meshRef = ref();
const ringRef = ref();
const hover = ref(false);

// 鲜艳色彩配置 (Vibrant Colors)
const nodeStyle = computed(() => {
  const type = props.node.type;
  const status = props.node.meta_data?.status;
  const prof = props.node.meta_data?.proficiency || 0;

  // 1. ROOT: 金色核心
  if (type === 'ROOT') {
    return {color: '#FFD700', emissive: '#FFA500', intensity: 3, scale: 1.0};
  }

  // 2. USER: 赛博青色
  if (type === 'USER') {
    return {color: '#00F0FF', emissive: '#00A3FF', intensity: 2, scale: 0.9};
  }

  const baseColor = getDynamicColor(props.node.id || props.node.name);
  const isMastered = props.node.meta_data?.proficiency >= 90;

  // Default Skill (Blue/Green mix)
  return {color: baseColor, emissive: baseColor, intensity: 1.2, scale: isMastered ? 0.8 : 0.7}; // Emerald
});

const {onBeforeRender} = useLoop();

// 随机相位，避免所有节点动作整齐划一
const randomPhase = Math.random() * 100;

onBeforeRender(({elapsed}) => {
  if (!meshRef.value) return;

  const t = elapsed + randomPhase;

  // 旋转逻辑：ROOT 慢速威严，USER 中速，SKILL 快速灵动
  const rotSpeed = props.node.type === 'ROOT' ? 0.2 : (props.node.type === 'USER' ? 0.5 : 0.8);
  meshRef.value.rotation.y = t * rotSpeed * 0.5;
  meshRef.value.rotation.z = t * rotSpeed * 0.2;

  // 悬浮呼吸效果
  const floatRange = props.isSelected ? 0.2 : 0.05;
  meshRef.value.position.y = Math.sin(t * 2) * floatRange;

  // 选中时的光环动画
  if (props.isSelected && ringRef.value) {
    ringRef.value.rotation.z = -t;
    ringRef.value.scale.setScalar(1.2 + Math.sin(t * 3) * 0.15);
  }
});

function handleClick(ev: any) {
  ev.stopPropagation();
  emit('click', props.node);
}

function handleRightClick(ev: any) {
  if (ev.nativeEvent) {
    ev.nativeEvent.preventDefault();
  }
  ev.stopPropagation();
  emit('right-click', {node: props.node, event: ev});
}

const NEON_PALETTE = [
  '#FF0055', '#00FF9F', '#00F3FF', '#FFD700',
  '#BC13FE', '#FF7700', '#F0F', '#4D4DFF'
];

function getDynamicColor(str: string) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return NEON_PALETTE[Math.abs(hash) % NEON_PALETTE.length];
}
</script>

<template>
  <TresGroup :position="[node.x, node.y, node.z]">

    <!-- 1. ROOT Node: Octahedron (Diamond shape) -->
    <TresMesh
      v-if="node.type === 'ROOT'"
      ref="meshRef"
      @click="handleClick"
      @context-menu="handleRightClick"
      @pointer-enter="hover = true"
      @pointer-leave="hover = false"
    >
      <TresOctahedronGeometry :args="[nodeStyle.scale * 2.5, 0]"/> <!-- 大而锋利 -->
      <TresMeshStandardMaterial
        :color="nodeStyle.color"
        :emissive="nodeStyle.emissive"
        :emissive-intensity="isHighlighted ? nodeStyle.intensity : 0.2"
        :metalness="0.9"
        :opacity="isHighlighted ? 1 : 0.1"
        :roughness="0.1"
        :transparent="true"
      />
    </TresMesh>

    <!-- 2. USER Node: Icosahedron (Complex sphere) -->
    <TresMesh
      v-else-if="node.type === 'USER'"
      ref="meshRef"
      @click="handleClick"
      @context-menu="handleRightClick"
      @pointer-enter="hover = true"
      @pointer-leave="hover = false"
    >
      <TresIcosahedronGeometry :args="[nodeStyle.scale * 1.8, 1]"/>
      <TresMeshStandardMaterial
        :color="nodeStyle.color"
        :emissive="nodeStyle.emissive"
        :emissive-intensity="isHighlighted ? nodeStyle.intensity : 0.2"
        :metalness="0.8"
        :opacity="isHighlighted ? 1 : 0.1"
        :roughness="0.2"
        :transparent="true"
        wireframe
      />
      <!-- 内部实心球 -->
      <TresMesh>
        <TresIcosahedronGeometry :args="[nodeStyle.scale * 1.4, 0]"/>
        <TresMeshBasicMaterial :color="nodeStyle.color" :opacity="isHighlighted ? 0.8 : 0.1" transparent/>
      </TresMesh>
    </TresMesh>

    <!-- 3. SKILL Node: Sphere (Smooth) -->
    <TresMesh
      v-else
      ref="meshRef"
      @click="handleClick"
      @context-menu="handleRightClick"
      @pointer-enter="hover = true"
      @pointer-leave="hover = false"
    >
      <TresSphereGeometry :args="[nodeStyle.scale * 1.5, 32, 32]"/>
      <TresMeshStandardMaterial
        :color="nodeStyle.color"
        :emissive="nodeStyle.emissive"
        :emissive-intensity="isHighlighted ? nodeStyle.intensity : 0.1"
        :metalness="0.6"
        :opacity="isHighlighted ? 1 : 0.1"
        :roughness="0.3"
        :transparent="true"
      />
    </TresMesh>

    <!-- Selection Ring (Shared) -->
    <TresMesh v-if="isSelected" ref="ringRef">
      <TresTorusGeometry :args="[node.val * 0.2 + 1.2, 0.08, 16, 100]"/>
      <TresMeshBasicMaterial :opacity="0.8" :transparent="true" color="#ffffff"/>
    </TresMesh>

    <!-- Labels -->
    <Html
      v-if="isHighlighted && (isSelected || hover || node.type !== 'SKILL')"
      :distance-factor="15"
      :position="[0, node.val * 0.2 + 2, 0]"
      center
      pointer-events="none"
      transform
    >
    <div
      :class="[
          isSelected
            ? 'bg-primary/20 border-primary text-white shadow-[0_0_20px_rgba(var(--c-primary),0.4)] scale-110'
            : 'bg-black/40 border-white/10 text-gray-300'
        ]"
      class="px-3 py-1.5 rounded-md backdrop-blur-md border transition-all duration-300 flex flex-col items-center gap-1"
    >
      <span class="text-xs font-bold tracking-wider whitespace-nowrap">{{ node.name }}</span>
      <!-- 仅 User 和 Skill 显示熟练度/职位信息 -->
      <span v-if="node.type !== 'ROOT' && node.meta_data?.proficiency" class="text-[10px] opacity-80 font-mono">
           {{ node.meta_data.proficiency }}%
        </span>
    </div>
    </Html>
  </TresGroup>
</template>
