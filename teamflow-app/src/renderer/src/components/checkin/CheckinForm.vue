<!-- src/components/checkin/CheckinForm.vue -->
<template>
  <div class="flex flex-col md:flex-row gap-8">

    <!-- 左侧：罗盘区域 -->
    <div
      class="flex-shrink-0 flex flex-col items-center justify-center bg-bg/50 rounded-2xl p-4 border border-border/10">
      <div class="text-sm font-semibold text-muted mb-4 uppercase tracking-wider">Mood Compass</div>
      <FlowCompass
        v-model:challenge="formData.challenge_level"
        v-model:skill="formData.skill_level"
      />
    </div>

    <!-- 右侧：文本输入区域 -->
    <div class="flex-1 flex flex-col justify-between py-2">
      <div class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-text mb-2 flex items-center gap-2">
            <span class="i-carbon-trophy text-accent text-lg"></span>
            今天的成就 (Achievement)
          </label>
          <textarea
            v-model="formData.achievement_text"
            class="input-base resize-none"
            placeholder="完成了什么关键任务？感觉如何？"
            rows="3"
          ></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-text mb-2 flex items-center gap-2">
            <span class="i-carbon-road-barrier text-error text-lg"></span>
            遇到的阻碍 (Blocker)
          </label>
          <textarea
            v-model="formData.obstacle_text"
            class="input-base resize-none border-error/20 focus:border-error/50 focus:shadow-[0_0_10px_rgb(var(--c-error)/0.1)]"
            placeholder="有什么阻碍了你的进度？"
            rows="3"
          ></textarea>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div class="mt-8 flex items-center justify-end gap-3">
        <button
          v-if="allowCancel"
          class="btn-ghost"
          @click="$emit('cancel')"
        >
          暂不签到
        </button>

        <button
          :disabled="checkinStore.isLoading"
          class="btn-primary min-w-[120px]"
          @click="handleSubmit"
        >
          <span v-if="checkinStore.isLoading" class="i-carbon-circle-dash animate-spin text-xl"></span>
          <span v-else class="flex items-center gap-2">
            <span class="i-carbon-send-alt-filled"></span>
            Check-in
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {reactive} from 'vue';
import {useCheckinStore} from '@/stores/checkin';
import FlowCompass from './FlowCompass.vue';
import type {CheckinCreate} from '@/api';

const props = defineProps<{
  allowCancel?: boolean;
}>();

const emit = defineEmits(['success', 'cancel']);

const checkinStore = useCheckinStore();

// 初始化数据：默认为 0.5, 0.5 (进入 Flow 区域，给予积极暗示)
const formData = reactive<CheckinCreate>({
  challenge_level: 0.5,
  skill_level: 0.5,
  achievement_text: '',
  obstacle_text: ''
});

const handleSubmit = async () => {
  try {
    // 清理空字符串为 undefined/null
    const payload: CheckinCreate = {
      ...formData,
      achievement_text: formData.achievement_text?.trim() || null,
      obstacle_text: formData.obstacle_text?.trim() || null,
    };

    await checkinStore.submitCheckin(payload);
    emit('success');
  } catch (e) {
    // 错误已在 store 中由 toast 处理
  }
};
</script>
