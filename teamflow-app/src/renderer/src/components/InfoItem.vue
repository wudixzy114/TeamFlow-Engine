<template>
  <div class="flex items-center py-3 border-b border-white/5 hover:bg-white/5 transition-colors px-2 rounded-lg group">
    <!-- Label -->
    <span class="w-24 text-sm font-medium text-text-muted flex-shrink-0">{{ label }}</span>

    <div class="flex-grow flex items-center justify-between gap-4 min-h-[32px]">
      <!-- Display Mode -->
      <template v-if="!editing">
        <span class="text-text-main font-medium truncate">{{ modelValue || '-' }}</span>
        <button
          class="text-primary text-xs opacity-0 group-hover:opacity-100 transition-opacity hover:underline cursor-pointer"
          @click="$emit('edit')"
        >
          修改
        </button>
      </template>

      <!-- Edit Mode -->
      <template v-else>
        <div class="flex-grow max-w-[240px]">
          <!-- Text Input -->
          <input
            v-if="!inputType || inputType === 'text'"
            :value="modelValue"
            autoFocus
            class="input-base py-1 text-sm"
            type="text"
            @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
            @keyup.enter="$emit('confirm')"
          />

          <!-- Number Input -->
          <input
            v-else-if="inputType === 'number'"
            :value="modelValue"
            class="input-base py-1 text-sm"
            max="150"
            min="0"
            type="number"
            @input="$emit('update:modelValue', Number(($event.target as HTMLInputElement).value))"
            @keyup.enter="$emit('confirm')"
          />

          <!-- Select Input -->
          <div v-else-if="inputType === 'select'" class="relative">
            <select
              :value="modelValue"
              class="input-base py-1 text-sm appearance-none cursor-pointer"
              @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
            >
              <option disabled selected value="">请选择</option>
              <option
                v-for="option in options"
                :key="option.value"
                :value="option.value"
                class="text-black bg-white"
              >
                <!-- 注意：option 在深色模式下的背景通常需要强制为浅色或特定深色，
                     由于原生 select 样式限制，这里简单设为黑字白底以确保可读性，
                     或者你可以自定义下拉菜单组件 -->
                {{ option.label }}
              </option>
            </select>
            <!-- 自定义下拉箭头图标 -->
            <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-text-muted">
              <div class="i-carbon-chevron-down"></div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <button
          class="text-primary text-xs hover:text-primary/80 font-medium px-2 py-1 bg-primary/10 rounded ml-2 transition-colors"
          @click="$emit('confirm')"
        >
          确定
        </button>
      </template>
    </div>
  </div>
</template>

<script lang="ts" setup>
interface SelectOption {
  label: string;
  value: string | number;
}

withDefaults(defineProps<{
  label: string;
  modelValue: any;
  editing: boolean;
  inputType?: 'text' | 'number' | 'select';
  options?: SelectOption[];
}>(), {
  inputType: 'text',
  options: () => []
});

defineEmits(['update:modelValue', 'edit', 'confirm']);
</script>

<style scoped>
/* 隐藏 Number Input 的默认箭头 */
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
</style>
