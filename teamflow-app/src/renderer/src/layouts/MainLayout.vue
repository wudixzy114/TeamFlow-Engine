<!-- src/layouts/MainLayout.vue -->
<script lang="ts" setup xmlns:CheckinModal="http://www.w3.org/1999/html">
import AppSidebar from '@/layouts/AppSidebar.vue'
import AppHeader from '@/layouts/AppHeader.vue'
import CheckinModal from "@/components/checkin/CheckinModal.vue";
import {useTeamsStore} from "@/stores/teams";
import {useCheckinStore} from "@/stores/checkin";

const route = useRoute()
const isImmersive = computed(() => !!route.meta.immersive)
const checkinStore = useCheckinStore()
const teamsStore = useTeamsStore()

const showCheckinModal = ref(false)
const showCheckinTrigger = computed(() => {
  if (isImmersive.value) return false
  if (checkinStore.isLoading) return false
  if (!teamsStore.currentTeamId) return false
  return !checkinStore.hasCurrentTeamCheckedIn()
})
</script>

<template>
  <div class="flex h-screen w-screen overflow-hidden bg-bg-main text-text-main transition-colors duration-300">
    <!-- 1. Sidebar (Left Rail) -->
    <AppSidebar/>

    <!-- 2. Main Content Area (Right) -->
    <div class="flex-1 flex flex-col relative min-w-0">

      <!-- Ambient Background Effects (Global) -->
      <!-- 动态网格背景，带遮罩 -->
      <div class="absolute inset-0 bg-grid-pattern opacity-30 pointer-events-none z-0"></div>

      <!-- 动态光晕效果：右上角主色，左下角次色 -->
      <div
        class="absolute -top-[20%] -right-[10%] w-[500px] h-[500px] bg-primary/10 blur-[100px] rounded-full pointer-events-none z-0 transition-colors duration-500"></div>
      <div
        class="absolute -bottom-[20%] -left-[10%] w-[400px] h-[400px] bg-secondary/5 blur-[80px] rounded-full pointer-events-none z-0 transition-colors duration-500"></div>

      <!-- 3. Header (Top) -->
      <div
        :class="[ isImmersive ? 'absolute top-0 left-0 z-50' : 'relative z-20' ]"
        class="w-full transition-all duration-300"
      >
        <!-- 将沉浸状态传给 Header 组件，让它自己决定是否透明 -->
        <AppHeader :transparent="isImmersive"/>
      </div>

      <!-- 4. Router View (Content) -->
      <main class="flex-1 relative z-10 overflow-hidden">
        <router-view v-slot="{ Component, route }">
          <transition name="fade">
            <component
              :is="Component"
              :key="route.path"
              class="w-full h-full absolute inset-0 overflow-y-auto scrollbar-hide"
            />
          </transition>
        </router-view>
      </main>

      <transition name="scale-fade">
        <button
          v-if="showCheckinTrigger"
          class="absolute bottom-8 right-8 z-40 w-14 h-14 rounded-full flex items-center justify-center
                 bg-gradient-to-br from-primary to-primary-active text-white shadow-lg shadow-primary/30
                 hover:shadow-primary/50 hover:scale-105 active:scale-95 transition-all duration-300 group"
          title="Daily Check-in"
          @click="showCheckinModal = true"
        >
          <!-- 静态图标 -->
          <span class="i-carbon-radar text-2xl group-hover:animate-ping absolute opacity-30"></span>
          <span class="i-carbon-radar text-2xl relative"></span>

          <!-- 提示红点 -->
          <span class="absolute top-3 right-3 w-2.5 h-2.5 bg-red-400 rounded-full border border-bg-card"></span>
        </button>
      </transition>

      <!-- 签到模态框 -->
      <CheckinModal
        :is-open="showCheckinModal"
        @close="showCheckinModal = false"
      />
    </div>
  </div>
</template>

<!--suppress CssUnusedSymbol -->
<style scoped>
/* 针对路由切换的微调 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px); /* 轻微的上浮进场效果 */
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.scale-fade-enter-active,
.scale-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); /* 弹性效果 */
}

.scale-fade-enter-from,
.scale-fade-leave-to {
  opacity: 0;
  transform: scale(0) rotate(-45deg);
}
</style>
