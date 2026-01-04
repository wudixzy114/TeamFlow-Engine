<!-- src/components/chat/ChatBubble.vue -->
<script lang="ts" setup>
import {computed} from 'vue';
import {Menu, MenuButton, MenuItems, MenuItem} from '@headlessui/vue';
import {useClipboard} from '@vueuse/core';
import {toast} from 'vue-sonner';
import {getTagConfig, isSpecialTag} from '@/stores/chat/chatTags';

const props = defineProps<{
  message: TeamChat;
  isSelf: boolean;
}>();

const emit = defineEmits<{
  (e: 'delete', id: string): void;
}>();

const {copy} = useClipboard();

// 解析 Tag 配置
const isSpecial = computed(() => isSpecialTag(props.message.tag));
const config = computed(() => getTagConfig(props.message.tag));

// 尝试解析 JSON 内容
const parsedContent = computed(() => {
  if (!isSpecial.value) return null;
  try {
    const data = JSON.parse(props.message.content);
    // 简单的校验，确保是对象
    if (typeof data === 'object' && data !== null) {
      return data;
    }
    return null;
  } catch (e) {
    // 无法解析，回退到普通文本显示
    return null;
  }
});

// 如果解析失败，回退到普通显示模式
const shouldRenderCard = computed(() => isSpecial.value && config.value && parsedContent.value);

const handleCopy = () => {
  // 如果是卡片，复制特定格式的文本，或者只是 Raw JSON
  copy(shouldRenderCard.value ? `[${config.value?.label}] ${parsedContent.value.title || '详情'}` : props.message.content);
  toast.success('已复制');
};

const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
};

// 格式化日期显示 (用于卡片内字段)
const formatFieldTime = (val: string) => {
  const d = new Date(val);
  return isNaN(d.getTime()) ? val : d.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};
</script>

<template>
  <div :class="isSelf ? 'flex-row-reverse' : 'flex-row'" class="flex gap-3 mb-2 group items-end">

    <!-- Avatar -->
    <div
      :class="isSelf ? 'bg-primary text-white' : 'bg-surface border border-white/10 text-text-muted'"
      class="flex-shrink-0 w-8 h-8 rounded-lg flex-center text-xs font-bold select-none shadow-md mb-1 transition-transform hover:scale-105">
      {{ isSelf ? 'Me' : message.sender_id.slice(0, 2).toUpperCase() }}
    </div>

    <!-- Content Container -->
    <div class="flex flex-col max-w-[80%] sm:max-w-[70%]">

      <!-- Sender Name (Group Chat) -->
      <span v-if="!isSelf" class="text-[10px] text-text-muted/60 mb-1 ml-1 truncate max-w-[150px]">
        {{ message.sender_id }}
      </span>

      <div :class="isSelf ? 'flex-row-reverse' : 'flex-row'" class="relative flex items-end gap-2">

        <!-- 1. 社交卡片 (Structured Card) -->
        <div v-if="shouldRenderCard"
             class="overflow-hidden rounded-xl border border-white/10 shadow-xl bg-bg-card min-w-[260px]">

          <!-- Card Header -->
          <div :class="config?.cardTheme"
               class="px-4 py-3 flex items-center gap-2.5 text-white relative overflow-hidden">
            <!-- 背景装饰 -->
            <div class="absolute -right-4 -top-4 text-white/10 text-6xl rotate-12 pointer-events-none">
              <div :class="config?.icon"></div>
            </div>

            <div class="i-carbon-calendar-heat-map text-lg relative z-10"></div>
            <span class="font-bold tracking-wide relative z-10">{{ config?.label }}</span>
          </div>

          <!-- Card Body -->
          <div class="p-4 space-y-3 text-sm">
            <template v-for="field in config?.fields" :key="field.key">
              <div v-if="parsedContent[field.key]" class="flex flex-col gap-0.5">
                <span class="text-[10px] uppercase tracking-wider text-text-muted/70 font-bold">
                  {{ field.label }}
                </span>
                <span class="text-text-main font-medium break-words">
                  <template v-if="field.type === 'datetime'">
                    {{ formatFieldTime(parsedContent[field.key]) }}
                  </template>
                  <template v-else>
                    {{ parsedContent[field.key] }}
                  </template>
                </span>
              </div>
            </template>
          </div>

          <!-- Card Footer (Actions) -->
          <!-- 未来可以在这里加 API 交互，比如 "我要参加" -->
          <div class="px-4 py-2.5 bg-bg-surface/50 border-t border-white/5 flex items-center justify-between">
            <div class="flex -space-x-1.5 overflow-hidden">
              <!-- 模拟参与者头像 -->
              <div class="w-5 h-5 rounded-full ring-2 ring-bg-card bg-gray-600 flex-center text-[8px]">A</div>
              <div class="w-5 h-5 rounded-full ring-2 ring-bg-card bg-gray-500 flex-center text-[8px]">+</div>
            </div>
            <button
              class="text-xs text-primary hover:text-primary-hover font-medium transition-colors flex items-center gap-1">
              加入活动
              <div class="i-carbon-arrow-right"></div>
            </button>
          </div>
        </div>

        <!-- 2. 普通文件 -->
        <div v-else-if="message.tag === 'file'"
             :class="isSelf ? 'bg-primary/10 border-primary/20' : 'bg-surface border-white/5'"
             class="p-3 rounded-xl border flex items-center gap-3 pr-4 cursor-pointer hover:bg-white/5 transition-colors">
          <div class="w-10 h-10 rounded-lg bg-bg-main flex-center shadow-inner">
            <div class="i-carbon-document text-2xl text-primary"></div>
          </div>
          <div class="flex flex-col">
            <span class="text-sm font-medium text-text-main">文件附件</span>
            <a :href="message.content"
               class="text-xs text-text-muted hover:text-primary hover:underline truncate max-w-[150px]"
               target="_blank">
              点击下载
            </a>
          </div>
        </div>

        <!-- 3. 普通图片 -->
        <div v-else-if="message.tag === 'image'" class="rounded-xl overflow-hidden border border-white/10 shadow-lg">
          <img :src="message.content"
               alt=""
               class="max-w-[280px] sm:max-w-xs md:max-w-sm max-h-[300px] object-cover cursor-zoom-in hover:brightness-110 transition" loading="lazy"/>
        </div>

        <!-- 4. 普通文本 (包含 fallback) -->
        <div v-else
             :class="[
               isSelf
                 ? 'bg-gradient-to-br from-primary to-primary-active text-white shadow-lg shadow-primary/20 border-transparent'
                 : 'bg-bg-surface text-text-main border-white/10 shadow-sm'
             ]"
             class="py-2.5 px-4 rounded-2xl border text-sm leading-relaxed break-words whitespace-pre-wrap max-w-full">
          {{ isSelf || !isSpecial ? message.content : '无法解析的卡片消息' }}
        </div>

        <!-- Context Menu Button -->
        <Menu as="div" class="relative opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <MenuButton class="p-1.5 rounded-full hover:bg-white/10 text-text-muted transition">
            <div class="i-carbon-overflow-menu-vertical text-sm"></div>
          </MenuButton>
          <transition
            enter-active-class="transition duration-100 ease-out"
            enter-from-class="transform scale-95 opacity-0"
            enter-to-class="transform scale-100 opacity-100"
            leave-active-class="transition duration-75 ease-in"
            leave-from-class="transform scale-100 opacity-100"
            leave-to-class="transform scale-95 opacity-0"
          >
            <MenuItems :class="isSelf ? 'right-0' : 'left-0'"
                       class="absolute z-10 w-28 mt-1 rounded-xl bg-bg-card border border-white/10 shadow-xl py-1 focus:outline-none origin-top-right">
              <MenuItem v-slot="{ active }">
                <button
                  :class="[active ? 'bg-white/5' : '', 'flex w-full items-center px-3 py-2 text-xs text-text-main']"
                  @click="handleCopy">
                  <div class="i-carbon-copy mr-2"></div>
                  复制
                </button>
              </MenuItem>
              <MenuItem v-if="isSelf" v-slot="{ active }">
                <button
                  :class="[active ? 'bg-red-500/10 text-red-400' : '', 'flex w-full items-center px-3 py-2 text-xs text-text-muted hover:text-red-400']"
                  @click="emit('delete', message.id)">
                  <div class="i-carbon-trash-can mr-2"></div>
                  撤回
                </button>
              </MenuItem>
            </MenuItems>
          </transition>
        </Menu>

      </div>

      <!-- Timestamp -->
      <span :class="isSelf ? 'mr-1 text-right' : 'ml-1 text-left'" class="text-[9px] text-text-muted/40 mt-1 block">
        {{ formatTime(message.created_at) }}
      </span>

    </div>
  </div>
</template>
