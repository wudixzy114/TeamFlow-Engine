<!-- src/components/common/ConfirmModal.vue -->
<template>
  <TransitionRoot :show="isOpen" appear as="template">
    <Dialog as="div" class="relative z-50" @close="closeModal">

      <!-- 背景遮罩 (Backdrop) -->
      <TransitionChild
        as="template"
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
              class="w-full max-w-md transform overflow-hidden rounded-2xl bg-bg-card border border-border/50 p-6 text-left align-middle shadow-glow-lg transition-all relative">
              <div
                class="absolute top-0 right-0 -mr-16 -mt-16 w-32 h-32 rounded-full bg-primary/20 blur-2xl pointer-events-none"></div>

              <DialogTitle as="h3" class="text-lg font-medium leading-6 text-text-main flex items-center gap-2">
                <i class="i-carbon-warning-filled text-accent text-xl"/>
                {{ title }}
              </DialogTitle>

              <div class="mt-3">
                <p class="text-sm text-text-muted">
                  {{ description }}
                </p>
              </div>

              <div class="mt-6 flex justify-end gap-3">
                <button
                  class="btn-ghost text-sm px-4 py-2"
                  type="button"
                  @click="closeModal"
                >
                  {{ cancelText }}
                </button>
                <button
                  class="btn-primary bg-gradient-to-r from-accent to-orange-600 text-white text-sm px-4 py-2 border-none shadow-glow-sm"
                  type="button"
                  @click="confirmAction"
                >
                  {{ confirmText }}
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
import {TransitionRoot, TransitionChild, Dialog, DialogPanel, DialogTitle} from '@headlessui/vue';

const props = defineProps({
  isOpen: Boolean,
  title: {type: String, default: '确认操作'},
  description: {type: String, default: '此操作无法撤销，确定要继续吗？'},
  confirmText: {type: String, default: '确定'},
  cancelText: {type: String, default: '取消'},
});

const emit = defineEmits(['close', 'confirm']);

const closeModal = () => {
  emit('close');
};

const confirmAction = () => {
  emit('confirm');
};
</script>
