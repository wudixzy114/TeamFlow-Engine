<script lang="ts" setup>
import {ref, watch, computed} from 'vue';
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionRoot,
  TransitionChild,
} from '@headlessui/vue';
import {STATUS_OPTIONS, PRESET_TAGS, type SkillMetaData} from '@/constants/skillPresets';

const props = defineProps<{
  isOpen: boolean;
  isEdit: boolean;
  initialData?: { name: string; meta_data?: any };
}>();

const emit = defineEmits(['close', 'confirm']);

const name = ref('');
const proficiency = ref(50);
const status = ref<string>('learning');
const selectedTags = ref<string[]>([]);
const description = ref('');   // 新增

const queryTag = ref('');
const filteredTags = computed(() =>
  queryTag.value === ''
    ? PRESET_TAGS
    : PRESET_TAGS.filter((tag) =>
      tag.toLowerCase().includes(queryTag.value.toLowerCase())
    )
);

watch(() => props.isOpen, (val) => {
  if (val) {
    if (props.isEdit && props.initialData) {
      name.value = props.initialData.name;
      const meta = props.initialData.meta_data || {};
      proficiency.value = meta.proficiency || 50;
      status.value = meta.status || 'learning';
      selectedTags.value = meta.tags || [];
      description.value = meta.description || '';
    } else {
      name.value = '';
      proficiency.value = 50;
      status.value = 'learning';
      selectedTags.value = [];
      description.value = '';
    }
  }
});

function handleConfirm() {
  if (!name.value.trim()) return;

  const meta: SkillMetaData = {
    proficiency: proficiency.value,
    status: status.value as any,
    tags: selectedTags.value,
    description: description.value.trim(),
  };

  emit('confirm', {name: name.value.trim(), meta});
  emit('close');
}

function toggleTag(tag: string) {
  if (selectedTags.value.includes(tag)) {
    selectedTags.value = selectedTags.value.filter(t => t !== tag);
  } else {
    selectedTags.value.push(tag);
  }
}
</script>

<template>
  <TransitionRoot :show="isOpen" appear as="template">
    <Dialog as="div" class="relative z-50" @close="$emit('close')">
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 backdrop-glass"/>
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4 text-center">
          <TransitionChild
            as="template"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel
              class="w-full max-w-lg transform overflow-hidden rounded-2xl glass-panel p-8 text-left align-middle shadow-2xl transition-all">
              <DialogTitle as="h3" class="text-2xl font-bold flex items-center gap-3 mb-8 text-white">
                <div class="i-carbon-tree-view-alt text-primary text-3xl"/>
                {{ isEdit ? '重塑技能节点' : '萌发新技能' }}
              </DialogTitle>

              <div class="space-y-6">
                <!-- 名称 -->
                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">技能名称</label>
                  <input v-model="name" autofocus class="input-base" placeholder="例如：Three.js 光追、系统设计..."
                         type="text"/>
                </div>

                <!-- 状态 -->
                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-3">当前状态</label>
                  <div class="grid grid-cols-3 gap-4">
                    <button
                      v-for="opt in STATUS_OPTIONS"
                      :key="opt.value"
                      :class="[status === opt.value ? 'bg-primary/20 border-primary text-primary shadow-glow' : 'bg-bg-surface/40 border-border/60 text-gray-400 hover:bg-bg-surface/80', 'flex flex-col items-center p-4 rounded-xl border transition-all']"
                      @click="status = opt.value"
                    >
                      <div :class="opt.icon" class="text-2xl mb-2"/>
                      <span class="text-sm">{{ opt.label }}</span>
                    </button>
                  </div>
                </div>

                <!-- 熟练度 -->
                <div>
                  <div class="flex justify-between mb-2">
                    <label class="text-sm font-medium text-gray-300">熟练度 / 信心值</label>
                    <span class="text-lg font-bold text-primary">{{ proficiency }}%</span>
                  </div>
                  <input v-model.number="proficiency"
                         class="w-full h-3 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-primary slider-thumb"
                         max="100" min="0" type="range"/>
                </div>

                <!-- 标签 -->
                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-3">标签</label>
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="tag in PRESET_TAGS"
                      :key="tag"
                      :class="selectedTags.includes(tag) ? 'bg-secondary/30 border-secondary text-secondary' : 'border-gray-600 text-gray-400 hover:border-gray-400'"
                      class="px-3 py-1.5 rounded-lg border text-xs transition-all"
                      @click="toggleTag(tag)"
                    >
                      {{ tag }}
                    </button>
                  </div>
                </div>

                <!-- 描述（新增） -->
                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">描述（可选）</label>
                  <textarea
                    v-model="description"
                    class="input-base resize-none"
                    placeholder="写下你的心得、学习资源、应用场景..."
                    rows="4"
                  />
                </div>
              </div>

              <div class="mt-10 flex justify-end gap-4">
                <button class="btn-ghost" @click="$emit('close')">取消</button>
                <button :disabled="!name.trim()" class="btn-primary flex items-center gap-2" @click="handleConfirm">
                  <div class="i-carbon-save"/>
                  {{ isEdit ? '保存修改' : '创建节点' }}
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<style scoped>
.slider-thumb::-webkit-slider-thumb {
  @apply w-5 h-5 rounded-full shadow-glow bg-primary;
}

.slider-thumb:hover::-webkit-slider-thumb {
  transform: scale(1.3);
}
</style>
