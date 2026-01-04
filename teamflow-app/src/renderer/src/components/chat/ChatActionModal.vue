<!-- src/components/chat/ChatActionModal.vue -->
<script lang="ts" setup>
import {ref, watch} from 'vue';
import {Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild} from '@headlessui/vue';
import {type TagConfig} from '@/stores/chat/chatTags';

const props = defineProps<{
  isOpen: boolean;
  config: TagConfig | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'submit', content: string): void;
}>();

// 存储表单数据
const formData = ref<Record<string, string>>({});

// 当配置变化或打开时，重置/初始化表单
watch(() => props.config, (newConfig) => {
  if (newConfig && newConfig.fields) {
    formData.value = {};
    newConfig.fields.forEach(field => {
      formData.value[field.key] = '';
    });
  }
}, {immediate: true});

const handleSubmit = () => {
  // 简单校验
  if (props.config?.fields) {
    for (const field of props.config.fields) {
      if (field.required && !formData.value[field.key]) {
        // 这里可以使用 toast 提示
        return;
      }
    }
  }
  // 将对象序列化为 JSON 字符串发送
  emit('submit', JSON.stringify(formData.value));
  emit('close');
};
</script>

<template>
  <TransitionRoot :show="isOpen" appear as="template">
    <Dialog as="div" class="relative z-50" @close="emit('close')">
      <TransitionChild
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm"/>
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
          <TransitionChild
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95 translate-y-4"
            enter-to="opacity-100 scale-100 translate-y-0"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100 translate-y-0"
            leave-to="opacity-0 scale-95 translate-y-4"
          >
            <DialogPanel
              v-if="config"
              class="w-full max-w-md transform overflow-hidden rounded-2xl bg-bg-card border border-white/10 p-6 shadow-2xl transition-all"
            >
              <!-- Header -->
              <div class="flex items-center gap-4 mb-6">
                <div :class="config.cardTheme" class="w-12 h-12 rounded-xl flex-center shadow-lg text-white">
                  <div :class="config.icon" class="text-2xl"></div>
                </div>
                <div>
                  <DialogTitle as="h3" class="text-lg font-bold text-text-main">
                    发起{{ config.label }}
                  </DialogTitle>
                  <p class="text-xs text-text-muted">填写详情，邀请团队成员加入</p>
                </div>
              </div>

              <!-- Form -->
              <div class="space-y-4">
                <div v-for="field in config.fields" :key="field.key" class="space-y-1">
                  <label class="text-xs font-medium text-text-muted ml-1">
                    {{ field.label }} <span v-if="field.required" class="text-primary">*</span>
                  </label>

                  <!-- Select -->
                  <div v-if="field.type === 'select'" class="relative">
                    <select
                      v-model="formData[field.key]"
                      class="input-base appearance-none bg-bg-surface text-text-main"
                    >
                      <option disabled selected value="">请选择</option>
                      <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
                    </select>
                    <div class="absolute right-3 top-3 pointer-events-none text-text-muted">
                      <div class="i-carbon-chevron-down"></div>
                    </div>
                  </div>

                  <!-- Textarea -->
                  <textarea
                    v-else-if="field.type === 'textarea'"
                    v-model="formData[field.key]"
                    :placeholder="field.placeholder"
                    class="input-base bg-bg-surface resize-none"
                    rows="3"
                  ></textarea>

                  <!-- Date/Time (Html native for now, can be replaced by specialized picker) -->
                  <input
                    v-else-if="field.type === 'datetime'"
                    v-model="formData[field.key]"
                    class="input-base bg-bg-surface"
                    type="datetime-local"
                  />

                  <!-- Text Input -->
                  <input
                    v-else
                    v-model="formData[field.key]"
                    :placeholder="field.placeholder"
                    class="input-base bg-bg-surface"
                    type="text"
                    @keyup.enter="handleSubmit"
                  />
                </div>
              </div>

              <!-- Footer -->
              <div class="mt-8 flex justify-end gap-3">
                <button
                  class="btn-ghost text-sm"
                  type="button"
                  @click="emit('close')"
                >
                  取消
                </button>
                <button
                  class="btn-primary text-sm shadow-lg shadow-primary/20"
                  type="button"
                  @click="handleSubmit"
                >
                  <div class="i-carbon-send-filled"></div>
                  发布通知
                </button>
              </div>

            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
