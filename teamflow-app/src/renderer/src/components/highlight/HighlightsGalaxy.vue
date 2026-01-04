<!-- src/components/highlights/HighlightsGalaxy.vue -->
<script lang="ts" setup>
import {TresCanvas} from '@tresjs/core'
import GalaxyScene from './GalaxyScene.vue'

const props = defineProps<{
  activeId: string | null
}>()

const emit = defineEmits(['select'])

const handleSelect = (id: string) => {
  emit('select', id)
}
</script>

<template>
  <TresCanvas
    alpha
    clear-color="#0B0E14"
    shadows
    style="width: 100%; height: 100%; pointer-events: auto;"
  >
    <Suspense>
      <GalaxyScene
        :active-id="activeId"
        @select="handleSelect"
      />
    </Suspense>
  </TresCanvas>
</template>
