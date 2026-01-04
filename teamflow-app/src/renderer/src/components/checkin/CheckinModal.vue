<!-- src/components/checkin/CheckinModal.vue -->
<template>
  <TransitionRoot :show="isOpen" appear as="template">
    <Dialog as="div" class="relative z-50" @close="closeModal">

      <!-- 遮罩层 -->
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

          <!-- 内容卡片 -->
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
              class="w-full max-w-3xl transform overflow-hidden rounded-2xl glass-panel p-6 md:p-10 text-left align-middle shadow-2xl transition-all border border-border/20">

              <DialogTitle as="h3" class="text-h2 flex items-center gap-3 mb-2">
                <span class="i-carbon-radar text-primary text-2xl"></span>
                Daily Check-in
              </DialogTitle>

              <div class="mt-1 text-muted text-sm mb-8">
                记录当下的心流状态，连接团队脉搏。
              </div>

              <CheckinForm
                :allow-cancel="true"
                @cancel="closeModal"
                @success="handleSuccess"
              />

            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script lang="ts" setup>
import {TransitionRoot, TransitionChild, Dialog, DialogPanel, DialogTitle} from '@headlessui/vue';
import CheckinForm from './CheckinForm.vue';

const props = defineProps<{
  isOpen: boolean;
}>();

const emit = defineEmits(['close']);

const closeModal = () => {
  emit('close');
};

const handleSuccess = () => {
  // 可以在这里添加撒花特效等
  closeModal();
};
</script>
