<template>
  <div>
    <h1 class="text-3xl font-bold mb-6">成就与成长</h1>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Left Column -->
      <div class="space-y-6">
        <HighlightComposer/>
        <HighlightFeed/>
        <TaskCompleter/>
      </div>

      <!-- Right Column -->
      <div class="space-y-6">
        <SkillTree/>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import HighlightComposer from '@/components/achievement/HighlightComposer.vue';
import HighlightFeed from '@/components/achievement/HighlightFeed.vue';
import TaskCompleter from '@/components/achievement/TaskCompleter.vue';
import SkillTree from '@/components/achievement/SkillTree.vue';
</script>