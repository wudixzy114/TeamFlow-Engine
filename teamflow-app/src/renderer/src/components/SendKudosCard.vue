<template>
  <div class="flex flex-col gap-6">
    <!-- 接收人选择 -->
    <div class="flex flex-col gap-2">
      <label class="text-sm font-medium text-text-muted ml-1">发送给</label>
      <div class="relative group">
        <select
          v-model="form.receiver_id"
          class="input-base appearance-none cursor-pointer hover:bg-white/5"
        >
          <option disabled selected value="">选择一位团队成员...</option>
          <option v-for="member in availableMembers" :key="member.id" :value="member.id" class="text-black">
            {{ member.username }}
          </option>
        </select>
        <!-- 自定义箭头图标 -->
        <div
          class="i-carbon-chevron-down absolute right-4 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none group-hover:text-primary transition-colors"></div>
      </div>
      <span v-if="errors.receiver_id" class="text-xs text-red-400 ml-1">{{ errors.receiver_id }}</span>
    </div>

    <!-- 卡片类型选择 (自定义 Radio Group) -->
    <div class="flex flex-col gap-2">
      <label class="text-sm font-medium text-text-muted ml-1">能量卡类型</label>
      <div class="grid grid-cols-3 gap-3">
        <button
          v-for="type in cardTypes"
          :key="type.value"
          :class="form.card_type === type.value
            ? 'bg-primary/20 border-primary text-white shadow-glow-primary'
            : 'bg-black/20 border-white/10 text-text-muted hover:bg-white/5 hover:border-white/30'"
          class="relative px-2 py-3 rounded-xl border transition-all duration-300 flex flex-col items-center gap-2 group"
          type="button"
          @click="form.card_type = type.value"
        >
          <i
            :class="[type.icon, 'text-2xl transition-transform duration-300 group-hover:scale-110', form.card_type === type.value ? 'text-cyan-300' : 'opacity-50']"></i>
          <span class="text-xs font-medium">{{ type.label }}</span>
        </button>
      </div>
    </div>

    <!-- 留言输入 -->
    <div class="flex flex-col gap-2">
      <label class="text-sm font-medium text-text-muted ml-1">留言</label>
      <div class="relative">
        <textarea
          v-model="form.message"
          class="input-base resize-none py-3 leading-relaxed"
          maxlength="140"
          placeholder="写下你的赞赏，让 TA 感受到力量..."
          rows="4"
        ></textarea>
        <div class="absolute bottom-2 right-3 text-xs text-text-muted/50">
          {{ form.message.length }}/140
        </div>
      </div>
      <span v-if="errors.message" class="text-xs text-red-400 ml-1">{{ errors.message }}</span>
    </div>

    <!-- 错误提示 (全局) -->
    <div v-if="generalError"
         class="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
      <div class="i-carbon-warning-filled"></div>
      {{ generalError }}
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref, reactive, computed} from 'vue';
import {useKudosStore} from '@/stores/kudos';
import {useTeamsStore} from '@/stores/teams';
import {useAuthStore} from '@/stores/auth';

const emit = defineEmits(['send-success']);
const kudosStore = useKudosStore();
const teamsStore = useTeamsStore();
const authStore = useAuthStore();

const isSending = ref(false);
const generalError = ref('');
const errors = reactive({
  receiver_id: '',
  message: ''
});

const cardTypes = [
  {label: '最佳战友', value: '最佳战友卡', icon: 'i-carbon-partnership'},
  {label: '技术先锋', value: '技术先锋卡', icon: 'i-carbon-code'},
  {label: '创意无限', value: '创意无限卡', icon: 'i-carbon-light'},
];

const form = reactive({
  receiver_id: '',
  card_type: '最佳战友卡',
  message: '',
});

const availableMembers = computed(() => {
  const members = teamsStore.currentTeamDetail?.members || [];
  if (authStore.user && Array.isArray(members)) {
    return members.filter(m => m.id !== authStore.user?.id);
  }
  return [];
});

const validate = () => {
  let isValid = true;
  errors.receiver_id = '';
  errors.message = '';

  if (!form.receiver_id) {
    errors.receiver_id = '请选择一位队友';
    isValid = false;
  }
  if (!form.message.trim()) {
    errors.message = '写点什么吧';
    isValid = false;
  }
  return isValid;
};

const submitForm = async () => {
  if (!validate()) return;

  isSending.value = true;
  generalError.value = '';

  try {
    await kudosStore.sendKudos(form);
    emit('send-success');
    // Reset form
    form.message = '';
    form.receiver_id = '';
    form.card_type = '最佳战友卡';
  } catch (error) {
    generalError.value = '发送失败，请稍后重试';
    console.error(error);
  } finally {
    isSending.value = false;
  }
};

defineExpose({submitForm, isSending}); // 暴露 isSending 供父组件控制按钮状态
</script>
