<!-- src/components/common/InputModal.vue -->
<template>
  <TransitionRoot :show="isOpen" appear as="template">
    <Dialog as="div" class="relative z-50" @close="closeModal">
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-bg-main/80 backdrop-blur-sm"/>
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4 text-center">
          <TransitionChild
            as="template"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95 translate-y-4"
            enter-to="opacity-100 scale-100 translate-y-0"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100 translate-y-0"
            leave-to="opacity-0 scale-95 translate-y-4"
          >
            <DialogPanel
              class="w-full max-w-md transform overflow-hidden rounded-2xl glass-panel p-6 text-left align-middle shadow-xl transition-all border border-border/20">
              <DialogTitle as="h3" class="text-h2 mb-2">
                {{ title }}
              </DialogTitle>
              <div class="mt-2 text-sm text-muted mb-6">
                {{ description }}
              </div>

              <div class="space-y-4">
                <input
                  ref="inputRef"
                  v-model="inputValue"
                  :placeholder="placeholder"
                  class="input-base w-full"
                  type="text"
                  @keyup.enter="handleConfirm"
                />
              </div>

              <div class="mt-8 flex justify-end gap-3">
                <button
                  class="btn-ghost"
                  type="button"
                  @click="closeModal"
                >
                  取消
                </button>
                <button
                  :disabled="!inputValue.trim()"
                  class="btn-primary"
                  type="button"
                  @click="handleConfirm"
                >
                  保存
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script lang="ts" setup>
import {ref, watch, nextTick} from 'vue';
import {TransitionRoot, TransitionChild, Dialog, DialogPanel, DialogTitle} from '@headlessui/vue';

const props = defineProps<{
  isOpen: boolean;
  title: string;
  description?: string;
  placeholder?: string;
  defaultValue?: string;
}>();

const emit = defineEmits(['close', 'confirm']);

const inputValue = ref('');
const inputRef = ref<HTMLInputElement | null>(null);

// 当打开时，重置值并聚焦
watch(() => props.isOpen, async (newVal) => {
  if (newVal) {
    inputValue.value = props.defaultValue || '';
    await nextTick();
    inputRef.value?.focus();
  }
});

const closeModal = () => {
  emit('close');
};

const handleConfirm = () => {
  if (inputValue.value.trim()) {
    emit('confirm', inputValue.value.trim());
  }
};
</script>
