<template>
  <div
    :class="{ 'bg-bg-surface/30 border-primary/10': isEditing }"
    class="group flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl transition-all duration-300 hover:bg-bg-surface/50 border border-transparent hover:border-white/5"
  >
    <!-- Label 区域 -->
    <div class="flex flex-col mb-2 sm:mb-0">
      <span class="text-text-muted text-sm font-medium">{{ label }}</span>
      <span v-if="!isEditing" class="text-text-main font-medium mt-1 min-h-[1.5rem] flex items-center">
        {{ displayValueText || '未设置' }}
      </span>
    </div>

    <!-- 交互区域 -->
    <div class="flex items-center gap-3 relative z-20">
      <!-- 查看模式：编辑按钮 -->
      <button
        v-if="!isEditing"
        class="btn-ghost p-2 opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100"
        title="编辑"
        @click="startEdit"
      >
        <div class="i-carbon-edit text-lg"></div>
      </button>

      <!-- 编辑模式 -->
      <div v-else class="flex items-center gap-2 animate-slide-in-fast w-full sm:w-auto">

        <div class="relative w-full sm:w-48">

          <!-- Case A: 下拉选择 (使用 Headless UI Listbox) -->
          <Listbox v-if="inputType === 'select'" v-model="internalValue">
            <div class="relative">
              <ListboxButton
                class="relative w-full cursor-pointer rounded-xl bg-bg-surface/80 py-2.5 pl-4 pr-10 text-left text-text-main border border-border focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/50 sm:text-sm transition-all shadow-sm"
              >
                <span class="block truncate">{{ currentOptionLabel }}</span>
                <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                  <div aria-hidden="true" class="i-carbon-chevron-down text-text-muted text-lg"/>
                </span>
              </ListboxButton>

              <transition
                leave-active-class="transition duration-100 ease-in"
                leave-from-class="opacity-100"
                leave-to-class="opacity-0"
              >
                <ListboxOptions
                  class="absolute mt-1 max-h-60 w-full overflow-auto rounded-xl bg-bg-card border border-border/50 py-1 text-base shadow-lg ring-1 ring-black/5 focus:outline-none sm:text-sm z-50 glass-panel"
                >
                  <ListboxOption
                    v-for="opt in options"
                    :key="opt.value"
                    v-slot="{ active, selected }"
                    :value="opt.value"
                    as="template"
                  >
                    <li
                      :class="[
                        active ? 'bg-primary/10 text-primary' : 'text-text-main',
                        'relative cursor-pointer select-none py-2 pl-10 pr-4 transition-colors duration-200'
                      ]"
                    >
                      <span :class="[selected ? 'font-medium' : 'font-normal', 'block truncate']">
                        {{ opt.label }}
                      </span>
                      <span
                        v-if="selected"
                        class="absolute inset-y-0 left-0 flex items-center pl-3 text-primary"
                      >
                        <div aria-hidden="true" class="i-carbon-checkmark text-lg"/>
                      </span>
                    </li>
                  </ListboxOption>
                </ListboxOptions>
              </transition>
            </div>
          </Listbox>

          <!-- Case B: 数字/文本输入 -->
          <input
            v-else
            ref="inputRef"
            v-model="internalValue"
            :type="inputType"
            class="input-base bg-bg-surface/80 hover:bg-bg-surface text-text-main no-spinner"
            @keyup.enter="confirmEdit"
            @keyup.esc="cancelEdit"
          />
        </div>

        <!-- 确认/取消按钮 -->
        <button
          class="p-2 rounded-lg text-primary hover:bg-primary/10 hover:shadow-glow-sm transition-all"
          title="保存"
          @click="confirmEdit"
        >
          <div class="i-carbon-checkmark text-lg"></div>
        </button>
        <button
          class="p-2 rounded-lg text-text-muted hover:text-text-main hover:bg-white/5 transition-colors"
          title="取消"
          @click="cancelEdit"
        >
          <div class="i-carbon-close text-lg"></div>
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref, watch, nextTick, computed} from 'vue';
import {
  Listbox,
  ListboxButton,
  ListboxOptions,
  ListboxOption,
} from '@headlessui/vue'

const props = defineProps<{
  modelValue: string | number | undefined;
  label: string;
  inputType?: 'text' | 'number' | 'select';
  options?: { label: string; value: string }[];
  isEditing?: boolean;
}>();

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel', 'update:isEditing']);

const internalValue = ref(props.modelValue);
const inputRef = ref<HTMLInputElement | null>(null);
const isEditing = ref(props.isEditing || false);

// --- Computed ---
// 用于在 ListboxButton 上显示当前选中的 label
const currentOptionLabel = computed(() => {
  if (props.inputType !== 'select' || !props.options) return internalValue.value;
  const found = props.options.find(o => o.value === internalValue.value);
  return found ? found.label : internalValue.value;
});

// 用于在非编辑状态下显示文本 (Select 需要显示 Label 而不是 Value)
const displayValueText = computed(() => {
  if (props.inputType === 'select' && props.options) {
    const found = props.options.find(o => o.value === props.modelValue);
    return found ? found.label : props.modelValue;
  }
  return props.modelValue;
});

// --- Watchers ---
watch(() => props.modelValue, (val) => {
  internalValue.value = val;
});

watch(() => props.isEditing, (val) => {
  if (val !== undefined) isEditing.value = val;
});

// --- Actions ---
const startEdit = async () => {
  internalValue.value = props.modelValue;
  isEditing.value = true;
  emit('update:isEditing', true);

  await nextTick();
  // 只有 input 才有 focus 方法，Listbox 自动管理
  if (props.inputType !== 'select') {
    inputRef.value?.focus();
  }
};

const cancelEdit = () => {
  internalValue.value = props.modelValue;
  isEditing.value = false;
  emit('update:isEditing', false);
  emit('cancel');
};

const confirmEdit = () => {
  emit('update:modelValue', internalValue.value);
  isEditing.value = false;
  emit('update:isEditing', false);
  emit('confirm', internalValue.value);
};
</script>

<style scoped>
/* 移除数字输入框箭头 */
.no-spinner::-webkit-outer-spin-button,
.no-spinner::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
</style>
