<script lang="ts" setup>
import {computed} from 'vue'
import {Menu, MenuButton, MenuItems, MenuItem} from '@headlessui/vue'
import {useThemeStore, type ThemeType} from '@/stores/theme'

const themeStore = useThemeStore()

// 定义主题元数据：名称、图标、预览色（用于UI展示）
const themeOptions: { id: ThemeType; name: string; icon: string; color: string; desc: string }[] = [
  {id: 'focus', name: 'Focus', icon: 'i-carbon-center-circle', color: '#06b6d4', desc: 'Deep Blue Flow'},
  {
    id: 'connection',
    name: 'Connection',
    icon: 'i-carbon-connection-two-way',
    color: '#f43f5e',
    desc: 'Warm Rose Vibes'
  },
  {id: 'zen', name: 'Zen', icon: 'i-carbon-sprout', color: '#10b981', desc: 'Nature Balance'},
  {id: 'clean', name: 'Clean', icon: 'i-carbon-sun', color: '#f8fafc', desc: 'Bright Professional'},
  {id: 'synthwave', name: 'Synth', icon: 'i-carbon-flash', color: '#ec4899', desc: 'Neon Energy'},
  {id: 'abyss', name: 'Abyss', icon: 'i-carbon-moon', color: '#000000', desc: 'Pure Darkness'},
]

// 获取当前主题的详细信息
const currentThemeInfo = computed(() =>
  themeOptions.find(t => t.id === themeStore.mode) || themeOptions[0]
)
</script>

<template>
  <Menu as="div" class="relative inline-block text-left z-50">
    <!-- 1. 触发按钮 -->
    <div>
      <MenuButton
        class="group btn-ghost h-10 px-3 gap-3 border border-transparent hover:border-white/10 hover:bg-white/5 transition-all">
        <!-- 色彩指示器 (动态光晕) -->
        <span class="relative flex h-3 w-3">
          <span
            :style="{ backgroundColor: currentThemeInfo.color }"
            class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 duration-1000"
          ></span>
          <span
            :style="{ backgroundColor: currentThemeInfo.color }"
            class="relative inline-flex rounded-full h-3 w-3 transition-colors duration-300"
          ></span>
        </span>

        <span class="text-sm font-medium hidden sm:block">{{ currentThemeInfo.name }}</span>
        <div class="i-carbon-chevron-down text-xs opacity-50 group-hover:opacity-100 transition-opacity"></div>
      </MenuButton>
    </div>

    <!-- 2. 动画过渡 -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-75 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <!-- 3. 下拉面板 (Glass Panel) -->
      <MenuItems
        class="absolute right-0 mt-2 w-64 origin-top-right divide-y divide-white/5 rounded-xl bg-bg-card/80 backdrop-blur-2xl border border-white/10 shadow-glow-lg focus:outline-none overflow-hidden"
      >
        <div class="px-1 py-1">
          <div class="px-3 py-2 text-xs font-semibold text-text-muted uppercase tracking-wider">
            Select Theme
          </div>

          <MenuItem v-for="theme in themeOptions" :key="theme.id" v-slot="{ active }">
            <button
              :class="[
                active ? 'bg-primary/10 text-primary' : 'text-text-main',
                themeStore.mode === theme.id ? 'bg-white/5' : ''
              ]"
              class="group flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm transition-all duration-200"
              @click="themeStore.mode = theme.id"
            >
              <!--suppress HtmlUnknownTag -->
              <div class="flex items-center gap-3">
                <!-- 图标容器 -->
                <div
                  :class="active || themeStore.mode === theme.id ? 'bg-white/10 text-primary' : 'bg-black/20 text-text-muted'"
                  class="flex-center w-8 h-8 rounded-md transition-colors"
                >
                  <div :class="theme.icon" class="text-lg"></div>
                </div>

                <!-- 文字信息 -->
                <div class="flex flex-col items-start">
                  <span :class="themeStore.mode === theme.id ? 'text-primary' : ''" class="font-medium">
                    {{ theme.name }}
                  </span>
                  <span :class="themeStore.mode === theme.id ? 'text-primary' : 'text-text-muted'"
                        class="text-[10px] opacity-60">
                    {{ theme.desc }}
                  </span>
                </div>
              </div>

              <!-- 选中对勾 (只在选中时显示) -->
              <div v-if="themeStore.mode === theme.id"
                   class="i-carbon-checkmark text-primary text-lg"
              ></div>

              <!-- 悬停时的色彩预览点 (未选中时显示) -->
              <i
                v-else
                :style="{ backgroundColor: theme.color }"
                class="w-2 h-2 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              ></i>
            </button>
          </MenuItem>
        </div>
      </MenuItems>
    </transition>
  </Menu>
</template>

<style scoped>
/* 针对下拉阴影的微调，利用 UnoCSS 已经定义的 shadow-glow */
.shadow-glow-lg {
  box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.5),
  0 0 0 1px rgba(255, 255, 255, 0.05); /* 极细的内发光边框 */
}
</style>
