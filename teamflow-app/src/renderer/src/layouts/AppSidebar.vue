<!-- src/components/layout/AppSidebar.vue -->
<script lang="ts" setup>
import {computed, onMounted, onUnmounted} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useLayoutStore} from '@/stores/app/layout'
import {useAuthStore} from '@/stores/auth'
import {useTeamsStore} from "@/stores/teams";

const route = useRoute()
const router = useRouter()
const layoutStore = useLayoutStore()
const authStore = useAuthStore()
const teamsStore = useTeamsStore()

// --- 响应式布局逻辑 ---
let resizeTimeout: NodeJS.Timeout | null = null
const COLLAPSE_RATIO = 0.5

const handleResize = () => {
  if (resizeTimeout) clearTimeout(resizeTimeout)
  resizeTimeout = setTimeout(() => {
    const screenWidth = window.screen.width
    const dynamicThreshold = screenWidth * COLLAPSE_RATIO
    const windowWidth = window.innerWidth
    if (windowWidth < dynamicThreshold && !layoutStore.isSidebarCollapsed) {
      layoutStore.isSidebarCollapsed = true
    }
  }, 100)
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (resizeTimeout) clearTimeout(resizeTimeout)
})

// --- 导航数据定义 ---

interface NavItem {
  title: string
  iconClass: string
  index: string
  requiresAuth?: boolean
}

// 1. Focus Group (本地功能，始终显示)
const focusItems: NavItem[] = [
  {title: '心流仪式', iconClass: 'i-carbon-timer', index: '/flow-ritual'},
  {title: '心流链路', iconClass: 'i-carbon-ibm-cloud-vpc-endpoints', index: '/flow-link'},
  {title: 'AI 管理', iconClass: 'i-carbon-ai', index: '/ai-manager'},
  {title: 'AI 聊天', iconClass: 'i-carbon-chat-bot', index: '/ai-chat'},
]

// 2. Connection Group (完整团队功能)
const connectionItems: NavItem[] = [
  {title: '仪表盘', iconClass: 'i-carbon-dashboard', index: '/dashboard', requiresAuth: true},
  {title: '高光时刻', iconClass: 'i-carbon-star', index: '/highlights', requiresAuth: true},
  {title: '能量墙', iconClass: 'i-carbon-certificate', index: '/kudos-wall', requiresAuth: true},
  {title: '团队聊天', iconClass: 'i-carbon-chat', index: '/team-chat', requiresAuth: true},
  {title: '周报', iconClass: 'i-carbon-calendar', index: '/my-weekly-digest', requiresAuth: true},
  {title: '心流公约', iconClass: 'i-carbon-notebook', index: '/team-charter', requiresAuth: true},
  {title: '技能树', iconClass: 'i-carbon-tree-view-alt', index: '/skill-tree', requiresAuth: true},
  {title: '团队设置', iconClass: 'i-carbon-settings', index: '/team-management', requiresAuth: true},
  {title: '个人信息', iconClass: 'i-carbon-user', index: '/self-info', requiresAuth: true},
  {title: '论坛', iconClass: 'i-carbon-forum', index: '/forum', requiresAuth: true},
]

// 3. No Team Item (无团队时的唯一入口)
const setupTeamItem: NavItem = {
  title: '开启团队之旅',
  iconClass: 'i-carbon-rocket',
  index: '/no-team',
  requiresAuth: true
}

// --- 核心逻辑：计算当前显示的列表 ---
const currentConnectionList = computed(() => {
  // Case 1: 未登录 -> 显示完整列表，利用 isLocked 加上锁图标，诱导用户登录
  if (!authStore.isAuthenticated) {
    return connectionItems
  }

  // Case 2: 已登录但无团队 -> 显示引导入口
  if (!teamsStore.hasTeams) {
    return [setupTeamItem]
  }

  // Case 3: 已登录且有团队 -> 显示完整功能
  return connectionItems
})

// --- 辅助函数 ---

const isActive = (path: string) => route.path.startsWith(path)
const widthClass = computed(() => layoutStore.isSidebarCollapsed ? 'w-[72px]' : 'w-60')

// 判断是否需要显示锁（仅当需要验证且未登录时）
const isLocked = (item: NavItem) => {
  return item.requiresAuth && !authStore.isAuthenticated
}

const handleItemClick = (item: NavItem) => {
  if (isLocked(item)) {
    router.push({
      path: '/login',
      query: {redirect: item.index}
    })
  } else {
    router.push(item.index)
  }
}

// 头像背景色
const userAvatarBg = computed(() => {
  return authStore.isAuthenticated
    ? 'bg-gradient-to-br from-primary to-secondary'
    : 'bg-text-muted/30'
})
</script>

<template>
  <aside
    :class="widthClass"
    class="relative h-full flex flex-col border-r border-border/30 bg-bg-card/50 backdrop-blur-md transition-[width] duration-300 ease-in-out z-20"
  >
    <!-- Logo -->
    <div class="h-14 flex items-center justify-center border-b border-border/20 shrink-0">
      <div
        class="text-xl font-bold text-primary transition-all duration-300 select-none tracking-tight whitespace-nowrap">
        {{ layoutStore.isSidebarCollapsed ? 'T' : 'TeamFlow' }}
      </div>
    </div>

    <!-- Navigation List -->
    <div class="flex-1 overflow-y-auto overflow-x-hidden py-6 flex flex-col gap-6 scrollbar-hide">

      <!-- Group 1: Focus (Always visible) -->
      <nav class="px-3">
        <div
          :class="layoutStore.isSidebarCollapsed ? 'opacity-0' : 'opacity-100'"
          class="mb-2 px-3 text-[10px] font-bold text-text-muted/60 uppercase tracking-wider transition-opacity duration-300 truncate h-5 flex items-center"
        >
          Focus
        </div>
        <ul class="flex flex-col gap-1">
          <li v-for="item in focusItems" :key="item.index">
            <router-link
              :class="[
                isActive(item.index)
                  ? 'bg-primary/10 text-primary shadow-glow-sm'
                  : 'text-text-muted hover:bg-bg-surface hover:text-text-main'
              ]"
              :title="layoutStore.isSidebarCollapsed ? item.title : ''"
              :to="item.index"
              class="relative flex items-center h-10 px-3 rounded-xl transition-all duration-300 group overflow-hidden"
            >
              <!-- Indicator -->
              <div
                :class="isActive(item.index) ? 'opacity-100' : 'opacity-0 -translate-x-full'"
                class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full bg-primary transition-all duration-300"
              ></div>

              <!-- Icon -->
              <div
                :class="[item.iconClass, 'text-xl shrink-0 transition-transform duration-300 group-hover:scale-110']"></div>

              <!-- Title -->
              <span
                :class="layoutStore.isSidebarCollapsed ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'"
                class="ml-3 font-medium whitespace-nowrap transition-all duration-300 origin-left"
              >
                {{ item.title }}
              </span>
            </router-link>
          </li>
        </ul>
      </nav>

      <!-- Group 2: Connection (Dynamic) -->
      <nav class="px-3">
        <div
          :class="layoutStore.isSidebarCollapsed ? 'opacity-0' : 'opacity-100'"
          class="mb-2 px-3 text-[10px] font-bold text-text-muted/60 uppercase tracking-wider transition-opacity duration-300 truncate h-5 flex items-center"
        >
          Connection
        </div>
        <ul class="flex flex-col gap-1">
          <li v-for="item in currentConnectionList" :key="item.index">
            <div
              :class="[
                'cursor-pointer',
                isActive(item.index)
                    ? 'bg-secondary/10 text-secondary shadow-glow-secondary'
                    : 'text-text-muted hover:bg-bg-surface hover:text-text-main',
                isLocked(item) ? 'opacity-70 grayscale-[0.5]' : ''
              ]"
              :title="layoutStore.isSidebarCollapsed ? item.title : ''"
              class="relative flex items-center h-10 px-3 rounded-xl transition-all duration-300 group overflow-hidden"
              @click="handleItemClick(item)"
            >
              <!-- Indicator (Secondary Color) -->
              <div
                :class="isActive(item.index) ? 'opacity-100' : 'opacity-0 -translate-x-full'"
                class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full bg-secondary transition-all duration-300"
              ></div>

              <!-- Icon -->
              <div
                :class="[item.iconClass, 'text-xl shrink-0 transition-transform duration-300 group-hover:scale-110']"></div>

              <!-- Title & Lock -->
              <div
                :class="layoutStore.isSidebarCollapsed ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'"
                class="flex-1 ml-3 flex items-center justify-between min-w-0 transition-all duration-300 origin-left"
              >
                <span class="truncate font-medium">{{ item.title }}</span>
                <div v-if="isLocked(item)" class="i-carbon-locked text-xs ml-2 opacity-60 shrink-0"></div>
              </div>
            </div>
          </li>
        </ul>
      </nav>
    </div>

    <!-- Footer -->
    <div v-if="!layoutStore.isSidebarCollapsed" class="px-4 py-2 mb-2 shrink-0">

      <!-- User Info (Logged In) -->
      <div v-if="authStore.isAuthenticated"
           class="flex items-center gap-3 p-2 rounded-xl bg-bg-surface/50 border border-border/30">
        <div
          :class="userAvatarBg"
          class="w-8 h-8 rounded-full flex-center text-white text-xs font-bold shadow-glow-sm shrink-0"
        >
          {{ authStore.username.charAt(0).toUpperCase() }}
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium truncate text-text-main">{{ authStore.username }}</div>
          <div class="text-[10px] text-text-muted truncate">Online</div>
        </div>
        <button class="p-2 text-text-muted hover:text-red-400 transition-colors" title="Logout"
                @click="authStore.logout()">
          <div class="i-carbon-logout text-lg"></div>
        </button>
      </div>

      <!-- Login Button (Guest) -->
      <router-link v-else
                   class="flex items-center justify-center w-full h-10 rounded-xl bg-primary/10 text-primary border border-primary/20 hover:bg-primary hover:text-white transition-all duration-300 shadow-glow-sm"
                   to="/login">
        <span class="text-sm font-medium">Connect Cloud</span>
        <div class="i-carbon-arrow-right ml-2 text-lg"></div>
      </router-link>
    </div>

    <!-- Toggle Button -->
    <div class="p-3 border-t border-border/20 shrink-0">
      <button
        class="flex items-center justify-center w-full h-10 rounded-xl hover:bg-bg-surface text-text-muted hover:text-text-main transition-colors"
        @click="layoutStore.toggleSidebar"
      >
        <div
          :class="layoutStore.isSidebarCollapsed ? 'rotate-180' : 'rotate-0'"
          class="i-carbon-side-panel-close text-lg transition-transform duration-300"
        ></div>
      </button>
    </div>
  </aside>
</template>
