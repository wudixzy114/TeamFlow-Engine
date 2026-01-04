<script lang="ts" setup>
import {useLoop} from '@tresjs/core';
import {shallowRef} from 'vue';

const particlesRef = shallowRef();
const gridRef = shallowRef();

// 粒子数量
const count = 1000;
const radius = 80;

// 初始化粒子位置
const positions = new Float32Array(count * 3);
const speeds = new Float32Array(count); // 每个粒子的运动速度

for (let i = 0; i < count; i++) {
  const r = Math.random() * radius;
  const theta = Math.random() * Math.PI * 2;
  const phi = Math.acos(2 * Math.random() - 1);

  positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
  positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
  positions[i * 3 + 2] = r * Math.cos(phi);

  speeds[i] = 0.02 + Math.random() * 0.05;
}

// 动画循环
const {onBeforeRender} = useLoop()

onBeforeRender(({elapsed}) => {
  if (particlesRef.value) {
    // 缓慢旋转整个粒子群
    particlesRef.value.rotation.y = elapsed * 0.05

    // 让粒子产生微微的上下浮动 (呼吸感)
    particlesRef.value.position.y = Math.sin(elapsed * 0.5) * 2
  }

  if (gridRef.value) {
    // 网格像扫描仪一样移动
    const z = (elapsed * 2) % 10
    gridRef.value.position.z = z - 5 // 调整以保持在视口范围内（可选）
    gridRef.value.material.opacity = 0.1 + Math.sin(elapsed * 2) * 0.05 // 更平滑的脉动
  }
})
</script>

<template>
  <TresGroup>
    <!-- 底部网格 (Cyber Grid) -->
    <TresGridHelper
      ref="gridRef"
      :args="[200, 50]"
      :position="[0, -20, 0]"
    >
      <TresLineBasicMaterial :opacity="0.1" :transparent="true" color="#1e293b"/>
    </TresGridHelper>

    <!-- 顶部镜像网格 -->
    <TresGridHelper
      :args="[200, 50]"
      :position="[0, 30, 0]"
      :rotation="[Math.PI, 0, 0]"
    >
      <TresLineBasicMaterial :opacity="0.05" :transparent="true" color="#1e293b"/>
    </TresGridHelper>

    <!-- 浮动粒子 (Data Motes) -->
    <TresPoints ref="particlesRef">
      <TresBufferGeometry :position="[positions, 3]"/>
      <TresPointsMaterial
        :blending="2"
        :opacity="0.4"
        :size="0.4"
        :size-attenuation="true"
        :transparent="true"
        color="#38bdf8"
      />
    </TresPoints>

    <!-- 氛围光 -->
    <TresAmbientLight :intensity="0.2"/>
    <TresDirectionalLight :intensity="1" :position="[10, 20, 10]" color="#a78bfa"/>
    <TresDirectionalLight :intensity="0.5" :position="[-10, -10, -10]" color="#06b6d4"/>
  </TresGroup>
</template>
