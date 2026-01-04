<!-- src/components/layout/HeaderTeamSwitcher.vue -->
<script lang="ts" setup>
import {computed} from 'vue'
import {useRouter} from 'vue-router'
import {Menu, MenuButton, MenuItems, MenuItem} from '@headlessui/vue'
import {useTeamsStore} from '@/stores/teams'
import {useAuthStore} from '@/stores/auth'

const router = useRouter()
const teamsStore = useTeamsStore()
const authStore = useAuthStore()

// 获取当前团队
const currentTeam = computed(() =>
  teamsStore.myTeams.find(t => t.id === teamsStore.currentTeamId)
)

// 团队首字母
const getInitial = (name: string) => name ? name.charAt(0).toUpperCase() : 'T'

const handleSwitch = (teamId: string) => {
  teamsStore.setCurrentTeam(teamId)
}

const navigateTo = (path: string) => {
  router.push(path)
}
</script>

<template>
  <div v-if="authStore.isAuthenticated" class="relative z-50">
    <Menu as="div" class="relative inline-block text-left">
      <div>
        <MenuButton
          class="group inline-flex items-center gap-2 rounded-lg bg-bg-surface/50 border border-border/30 py-1.5 pl-2 pr-3 hover:bg-bg-surface hover:border-border/60 transition-all duration-200 outline-none focus:ring-2 focus:ring-primary/20"
        >
          <!-- Avatar / Icon -->
          <div
            class="w-6 h-6 rounded bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-[10px] font-bold text-white shadow-sm"
          >
            {{ currentTeam ? getInitial(currentTeam.name) : '+' }}
          </div>

          <!-- Team Name -->
          <span class="text-sm font-medium text-text-main max-w-[120px] truncate">
            {{ currentTeam?.name || '选择团队' }}
          </span>

          <!-- Chevron -->
          <div class="i-carbon-chevron-sort text-text-muted group-hover:text-text-main transition-colors text-xs"></div>
        </MenuButton>
      </div>

      <transition
        enter-active-class="transition duration-100 ease-out"
        enter-from-class="transform scale-95 opacity-0"
        enter-to-class="transform scale-100 opacity-100"
        leave-active-class="transition duration-75 ease-in"
        leave-from-class="transform scale-100 opacity-100"
        leave-to-class="transform scale-95 opacity-0"
      >
        <!-- 关键修改：添加 'no-drag' 类，防止 Electron 窗口拖拽拦截点击事件 -->
        <MenuItems
          class="absolute left-0 mt-2 w-56 origin-top-left divide-y divide-border/20 rounded-xl bg-bg-card border border-border/40 shadow-glow-sm ring-1 ring-black/5 focus:outline-none backdrop-blur-xl no-drag"
        >

          <!-- Section 1: Team List -->
          <div class="px-1 py-1 max-h-64 overflow-y-auto scrollbar-hide">
            <div class="px-2 py-1.5 text-[10px] font-bold text-text-muted/60 uppercase tracking-wider">
              切换团队
            </div>

            <MenuItem
              v-for="team in teamsStore.myTeams"
              :key="team.id"
              v-slot="{ active }"
            >
              <button
                :class="[
                    active ? 'bg-primary/10 text-primary' : 'text-text-main',
                    'group flex w-full items-center justify-between rounded-lg px-2 py-2 text-sm transition-colors'
                  ]"
                @click="handleSwitch(team.id)"
              >
                <div class="flex items-center gap-2 truncate">
                  <span
                    :class="team.id === teamsStore.currentTeamId ? 'bg-primary' : 'bg-transparent border border-text-muted/50'"
                    class="w-2 h-2 rounded-full shrink-0"></span>
                  <span class="truncate">{{ team.name }}</span>
                </div>

                <div v-if="team.id === teamsStore.currentTeamId" class="i-carbon-checkmark text-primary shrink-0"></div>
              </button>
            </MenuItem>
          </div>

          <!-- Section 2: Actions -->
          <div class="px-1 py-1">
            <MenuItem v-slot="{ active }">
              <button
                :class="[
                  active ? 'bg-bg-surface text-text-main' : 'text-text-muted',
                  'group flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm transition-colors'
                ]"
                @click="navigateTo('/no-team/create')"
              >
                <div class="i-carbon-add-alt text-lg"></div>
                创建新团队
              </button>
            </MenuItem>
            <MenuItem v-slot="{ active }">
              <button
                :class="[
                  active ? 'bg-bg-surface text-text-main' : 'text-text-muted',
                  'group flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm transition-colors'
                ]"
                @click="navigateTo('/no-team/join')"
              >
                <div class="i-carbon-login text-lg"></div>
                加入团队
              </button>
            </MenuItem>
          </div>
        </MenuItems>
      </transition>
    </Menu>
  </div>
</template>
