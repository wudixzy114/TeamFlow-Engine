<!-- src/components/highlights/GalaxyScene.vue -->
<script lang="ts" setup>
import {ref, watch, computed} from 'vue'
import {useLoop} from '@tresjs/core'
import {OrbitControls, Html, Stars, MouseParallax} from '@tresjs/cientos'
import {useHighlightsStore} from '@/stores/highlights'
import {getFibonacciSpherePoints, useThemeColors} from '@/utils/theme'
import HighlightCard3D from './HighlightCard3D.vue'

const props = defineProps<{
  activeId: string | null
}>()

const emit = defineEmits(['select'])

const store = useHighlightsStore()
const themeColors = useThemeColors()
const groupRef = ref()
const points = ref<[number, number, number][]>([])
const highlightsList = computed(() => store.highlights)

// 初始化坐标
watch(() => highlightsList.value.length, (len) => {
  if (len > 0) {
    points.value = getFibonacciSpherePoints(len, 8)
  }
}, {immediate: true})

// 这里的 useLoop 是绝对安全的，因为本组件是在 TresCanvas 内部渲染的
const {onBeforeRender} = useLoop()

onBeforeRender(({elapsed}) => {
  if (groupRef.value && !props.activeId) {
    groupRef.value.rotation.y = elapsed * 0.05
    groupRef.value.rotation.z = Math.sin(elapsed * 0.1) * 0.05
  }
})

function handleSelect(id: string) {
  emit('select', id)
}
</script>

<template>
  <!-- 1. 相机与控制器 (移入内部) -->
  <TresPerspectiveCamera :fov="45" :look-at="[0,0,0]" :position="[0, 0, 18]"/>

  <OrbitControls
    :auto-rotate="!activeId"
    :auto-rotate-speed="0.5"
    :enable-pan="false"
    :enable-rotate="!activeId"
    :enable-zoom="!activeId"
    make-default
  />

  <!-- 2. 灯光系统 (移入内部) -->
  <TresAmbientLight :intensity="2"/>
  <TresDirectionalLight :intensity="1" :position="[10, 10, 10]" color="#ffffff"/>
  <!-- 注意：如果 useThemeColors 返回的是 ref，需要 .value，如果是函数则直接调用 -->
  <TresPointLight :color="themeColors.getPrimary()" :intensity="4" :position="[-10, -5, -10]"/>
  <TresPointLight :color="themeColors.getSecondary()" :intensity="4" :position="[10, 5, -10]"/>

  <!-- 3. 背景 (移入内部) -->
  <Stars :count="5000" :depth="50" :fade="true" :radius="100" :size="0.2"/>

  <!-- 4. 核心高光组 -->
  <TresGroup ref="groupRef">
    <template v-for="(highlight, index) in highlightsList" :key="highlight.id">
      <Html
        v-if="points[index]"
        :distance-factor="12"
        :position="points[index]"
        :sprite="false"
        :z-index-range="[100, 0]"
        transform
      >
      <HighlightCard3D
        :highlight="highlight"
        :is-active="activeId === highlight.id"
        @click="handleSelect(highlight.id)"
      />
      </Html>

      <!-- 装饰球 -->
      <TresMesh v-if="points[index]" :position="points[index]" :scale="0.2">
        <TresSphereGeometry/>
        <TresMeshStandardMaterial
          :emissive="themeColors.getPrimary()"
          :emissive-intensity="2"
          :tone-mapped="false"
          color="#ffffff"
        />
      </TresMesh>
    </template>
  </TresGroup>

  <!-- 5. 特效 (移入内部) -->
  <MouseParallax :ease="3" :factor="1"/>
</template>
