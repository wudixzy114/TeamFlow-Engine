<script lang="ts" setup>
import {computed, onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {useTeamsStore} from '@/stores/teams'
import {toast} from 'vue-sonner'

const router = useRouter()
const teamsStore = useTeamsStore()
const isLoading = ref(true)

const invitations = computed(() => teamsStore.myInvitations)

const goBack = () => {
  if (teamsStore.hasTeams) {
    router.push({name: 'Dashboard'})
  } else {
    router.push({name: 'NoTeamDefault'})
  }
}

const handleRefresh = async () => {
  if (isLoading.value) return
  isLoading.value = true
  try {
    await Promise.all([
      teamsStore.fetchAllMyInvites(),
      new Promise(resolve => setTimeout(resolve, 500))
    ])
    toast.success('邀请列表已更新')
  } catch (error) {
    console.error(error)
    toast.error('刷新失败')
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  try {
    await teamsStore.fetchAllMyInvites()
  } finally {
    isLoading.value = false
  }
})

const handleAccept = async (code: string) => {
  const success = await teamsStore.acceptInvite(code)
  if (success) {
    setTimeout(() => {
      router.push({name: 'Dashboard'})
    }, 300)
  }
}

const handleDecline = async (code: string) => {
  await teamsStore.declineInvite(code)
}
</script>

<template>
  <!-- 添加 no-drag -->
  <div class="w-full max-w-3xl h-[600px] flex flex-col relative no-drag">
    <!-- 装饰背景 -->
    <div
      class="absolute -bottom-20 -right-20 w-64 h-64 bg-secondary/10 blur-[80px] rounded-full pointer-events-none animate-pulse"></div>

    <!-- Header Section -->
    <div class="flex items-center justify-between mb-8 shrink-0 relative z-10 px-2">
      <div class="flex items-center gap-4">
        <button
          class="w-10 h-10 rounded-full bg-white/5 border border-white/5 flex-center hover:bg-white/10 hover:border-white/20 text-text-muted hover:text-white transition-all group"
          @click="goBack"
        >
          <div class="i-carbon-arrow-left text-lg group-hover:-translate-x-0.5 transition-transform"></div>
        </button>
        <div>
          <h2 class="text-2xl font-bold text-white flex items-center gap-2">
            收到的邀请
            <span v-if="invitations.length > 0"
                  class="px-2 py-0.5 rounded-full bg-secondary text-white text-xs align-middle shadow-glow-secondary">
              {{ invitations.length }}
            </span>
          </h2>
          <p class="text-sm text-text-muted">查看并管理您的团队加入请求</p>
        </div>
      </div>
      <button
        :class="{'opacity-70 cursor-wait': isLoading}"
        :disabled="isLoading"
        class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-surface/50 border border-white/5 text-xs text-text-muted hover:text-white hover:bg-bg-surface transition-all active:scale-95"
        @click="handleRefresh"
      >
        <div :class="{'animate-spin': isLoading}" class="i-carbon-renew transition-transform duration-700"></div>
        <span>刷新列表</span>
      </button>
    </div>

    <!-- Main Content Area -->
    <div
      class="flex-1 glass-panel border-secondary/20 relative overflow-hidden flex flex-col shadow-[0_0_30px_rgba(var(--c-secondary),0.05)]">
      <div v-if="isLoading && invitations.length === 0" class="flex-1 flex flex-col items-center justify-center gap-4">
        <div class="w-12 h-12 border-2 border-secondary/30 border-t-secondary rounded-full animate-spin"></div>
        <p class="text-sm text-text-muted animate-pulse">正在同步数据...</p>
      </div>

      <div v-else-if="invitations.length === 0" class="flex-1 flex flex-col items-center justify-center relative">
        <div class="absolute inset-0 bg-grid-pattern opacity-[0.05]"></div>
        <div
          class="w-24 h-24 rounded-3xl bg-bg-surface/50 flex-center mb-6 border border-white/5 rotate-3 hover:rotate-6 transition-transform duration-500">
          <div class="i-carbon-mail-all text-5xl text-text-muted/30"></div>
        </div>
        <h3 class="text-lg font-bold text-text-main mb-1">暂无新的邀请</h3>
        <p class="text-text-muted text-sm max-w-xs text-center leading-relaxed">
          当团队管理员向您发送邀请时，<br/>它们会出现在这里。
        </p>
        <div class="mt-8 flex gap-4">
          <button class="text-xs text-secondary hover:underline decoration-dashed"
                  @click="router.push('/no-team/create')">
            或者，创建一个新团队？
          </button>
        </div>
      </div>

      <div v-else class="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-hide z-10">
        <div
          v-for="(invite, index) in invitations"
          :key="invite.invite_code"
          :style="{ animationDelay: `${index * 50}ms` }"
          class="group relative bg-bg-surface/30 border border-white/5 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all duration-300 hover:bg-bg-surface/60 hover:border-secondary/30 hover:-translate-y-1 hover:shadow-lg"
        >
          <div
            class="absolute left-0 top-0 bottom-0 w-1 bg-secondary rounded-l-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div class="flex items-center gap-4 flex-1 min-w-0">
            <div
              class="w-12 h-12 rounded-xl bg-gradient-to-br from-secondary/20 to-orange-500/10 flex-center border border-secondary/20 shrink-0 group-hover:scale-105 transition-transform duration-300">
              <div class="i-carbon-email text-2xl text-secondary"></div>
            </div>
            <div class="min-w-0 flex-1">
              <h3 :title="invite.team_name"
                  class="text-base font-bold text-white truncate group-hover:text-secondary transition-colors duration-300">
                {{ invite.team_name }}
              </h3>
              <div class="flex items-center gap-2 mt-1">
                <span class="text-xs text-text-muted shrink-0">Code:</span>
                <code :title="invite.invite_code"
                      class="px-1.5 py-0.5 rounded bg-black/20 text-xs font-mono text-secondary/80 border border-secondary/10 truncate max-w-[150px] sm:max-w-[200px]">
                  {{ invite.invite_code }}
                </code>
              </div>
            </div>
          </div>
          <div
            class="flex items-center gap-3 w-full sm:w-auto mt-2 sm:mt-0 opacity-80 group-hover:opacity-100 transition-opacity shrink-0">
            <button
              class="flex-1 sm:flex-none px-4 py-2 rounded-lg text-xs font-medium text-text-muted hover:text-red-400 hover:bg-red-500/10 transition-colors"
              @click="handleDecline(invite.invite_code)">
              忽略
            </button>
            <button
              class="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2 rounded-lg bg-secondary text-white text-xs font-bold shadow-glow-secondary hover:bg-secondary/90 hover:scale-105 active:scale-95 transition-all duration-300"
              @click="handleAccept(invite.invite_code)">
              <div class="i-carbon-checkmark text-sm"></div>
              <span>接受</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
