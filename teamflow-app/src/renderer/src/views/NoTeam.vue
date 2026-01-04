<script lang="ts" setup>
import {computed} from 'vue'
import {useAuthStore} from '@/stores/auth'
import {useTeamsStore} from '@/stores/teams'
import {useRouter, useRoute} from 'vue-router'
import WindowControls from '@/layouts/WindowControls.vue'

const authStore = useAuthStore()
const teamsStore = useTeamsStore()
const router = useRouter()
const route = useRoute()

const handleLogout = async () => {
  await authStore.logout()
  await router.replace('/login')
}

const goHome = () => {
  router.push('/')
}

const userStatusLabel = computed(() => {
  if (teamsStore.hasTeams) {
    return `已加入 ${teamsStore.myTeams.length} 个团队`
  }
  return '未加入团队'
})
</script>

<template>
  <!-- 根节点：开启全局拖拽 -->
  <div
    class="relative min-h-screen w-full flex flex-col overflow-hidden bg-bg-main font-sans text-text-main transition-colors duration-500 titlebar-drag-region">

    <!-- 窗口控制 -->
    <WindowControls class="no-drag"/>

    <!-- 用户信息 -->
    <div class="fixed top-6 left-6 z-50 flex items-center gap-3 no-drag">
      <button
        class="flex items-center gap-2 text-text-muted hover:text-white transition-colors group bg-bg-card/30 px-4 py-2 rounded-full backdrop-blur-md border border-white/5 hover:border-white/20 h-[42px]"
        @click="goHome"
      >
        <div class="i-carbon-arrow-left text-lg group-hover:-translate-x-1 transition-transform"></div>
        <span class="text-xs font-medium">首页</span>
      </button>

      <div
        class="glass-panel px-4 py-1.5 rounded-full flex items-center gap-3 border-white/10 hover:border-white/20 transition-all duration-300 h-[42px]">
        <div
          class="w-7 h-7 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-[10px] font-bold text-white shadow-glow-sm">
          {{ authStore.username.charAt(0).toUpperCase() }}
        </div>
        <div class="flex flex-col justify-center">
          <span class="text-[11px] font-bold text-text-main leading-tight">{{ authStore.username }}</span>
          <span class="text-[9px] text-text-muted leading-tight">{{ userStatusLabel }}</span>
        </div>
        <div class="w-[1px] h-3 bg-white/10 mx-1"></div>
        <button class="text-text-muted hover:text-red-400 transition-colors flex items-center justify-center p-1"
                @click="handleLogout">
          <div class="i-carbon-logout text-base"></div>
        </button>
      </div>
    </div>

    <!-- 背景层 -->
    <div class="absolute inset-0 z-0 select-none pointer-events-none">
      <div class="absolute inset-0 bg-gradient-to-br from-bg-main via-bg-card to-bg-main"></div>
      <div
        class="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-primary/10 blur-[120px] rounded-full mix-blend-screen animate-pulse"
        style="animation-duration: 8s"></div>
      <div
        class="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-secondary/10 blur-[120px] rounded-full mix-blend-screen animate-pulse"
        style="animation-duration: 10s"></div>
      <div class="absolute inset-0 bg-grid-pattern opacity-[0.03]"></div>
    </div>

    <!--
      主内容区域：Grid 布局
      1. 使用 grid 和 place-items-center 居中
      2. p-8 留出拖拽边缘
    -->
    <main class="flex-1 relative z-10 grid place-items-center p-8 overflow-hidden">
      <router-view v-slot="{ Component }">
        <transition
          enter-active-class="transition-all duration-500 ease-out transform-gpu"
          enter-from-class="opacity-0 translate-y-4 scale-95"
          enter-to-class="opacity-100 translate-y-0 scale-100"
          leave-active-class="transition-all duration-300 ease-in transform-gpu"
          leave-from-class="opacity-100 translate-y-0 scale-100"
          leave-to-class="opacity-0 -translate-y-4 scale-95"
        >
          <!--
             FIX:
             1. 移除 mode="out-in"，允许同时存在
             2. 强制 w-full 确保宽度正常
             3. class="col-start-1 row-start-1" 让新旧页面重叠在同一个格子里，实现完美的交叉淡入淡出
          -->
          <component
            :is="Component"
            :key="route.fullPath"
            class="col-start-1 row-start-1 w-full flex justify-center"
          />
        </transition>
      </router-view>
    </main>

    <!-- 底部 Slogan -->
    <footer class="relative z-10 pb-6 text-center pointer-events-none">
      <p class="text-[10px] text-text-muted/40 font-mono tracking-[0.3em] uppercase select-none">
        Focus Individually · Connect Globally
      </p>
    </footer>
  </div>
</template>
