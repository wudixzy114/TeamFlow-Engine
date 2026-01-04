<script lang="ts" setup>
import {ref} from 'vue'
import {useRouter} from 'vue-router'
import {useTeamsStore} from '@/stores/teams'
import {toast} from 'vue-sonner'

const teamName = ref('')
const isLoading = ref(false)
const router = useRouter()
const teamsStore = useTeamsStore()

const goBack = () => {
  if (teamsStore.hasTeams) {
    router.push({name: 'Dashboard'})
  } else {
    router.push({name: 'NoTeamDefault'})
  }
}

const handleCreate = async () => {
  if (!teamName.value.trim()) {
    toast.warning('请给您的团队起个名字')
    return
  }
  isLoading.value = true
  try {
    const success = await teamsStore.createTeam({name: teamName.value})
    if (success) {
      toast.success('团队创建成功！即将进入...')
      setTimeout(() => {
        router.push({name: 'Dashboard'})
      }, 500)
    }
  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <!--
    FIX: 添加 'flex flex-col'
    防止父级 injected class="flex" 导致内部元素水平并排。
    保留 no-drag 确保交互岛屿特性。
  -->
  <div class="w-full max-w-lg relative no-drag flex flex-col">

    <!-- 装饰背景 -->
    <div
      class="absolute -top-20 -left-20 w-64 h-64 bg-primary/20 blur-[80px] rounded-full pointer-events-none animate-pulse"></div>

    <!-- 顶部导航 -->
    <div class="flex items-center justify-between mb-6 relative z-10 px-1 shrink-0">
      <button class="flex items-center gap-2 text-text-muted hover:text-white transition-colors group" @click="goBack">
        <div
          class="w-8 h-8 rounded-full bg-white/5 flex-center border border-white/5 group-hover:bg-white/10 group-hover:border-white/20 transition-all">
          <div class="i-carbon-arrow-left text-lg group-hover:-translate-x-0.5 transition-transform"></div>
        </div>
        <span class="text-sm font-medium">返回</span>
      </button>
      <span
        class="text-xs font-bold text-primary/80 uppercase tracking-widest bg-primary/10 px-2 py-1 rounded border border-primary/20">Create Mode</span>
    </div>

    <!-- 主卡片 -->
    <div
      class="glass-panel p-10 relative overflow-hidden border-primary/20 shadow-[0_0_30px_rgba(var(--c-primary),0.1)] shrink-0">
      <div class="absolute top-0 right-0 p-8 opacity-5 pointer-events-none">
        <div class="i-carbon-ibm-cloud-pak-mcm text-9xl rotate-12"></div>
      </div>
      <div class="relative z-10">
        <div class="mb-8">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-blue-600 flex-center mb-4 shadow-glow">
            <div class="i-carbon-add-alt text-3xl text-white"></div>
          </div>
          <h2 class="text-3xl font-bold text-white mb-2">命名您的团队</h2>
          <p class="text-text-muted text-sm leading-relaxed">
            这是您团队心流的起点。名称代表着共同的愿景，<br/>不用担心，稍后可以在设置中随时更改。
          </p>
        </div>

        <form class="space-y-8" @submit.prevent="handleCreate">
          <div class="space-y-3">
            <label class="text-xs font-bold text-text-muted uppercase tracking-wider ml-1 flex justify-between">
              <span>Team Name</span>
              <span :class="teamName.length > 15 ? 'text-orange-400' : 'text-text-muted/50'">{{
                  teamName.length
                }}/20</span>
            </label>
            <div class="relative group">
              <input
                v-model="teamName"
                :disabled="isLoading"
                autoFocus
                class="w-full bg-bg-surface/40 border border-white/10 rounded-xl px-5 py-4 text-xl text-white placeholder:text-white/20 outline-none focus:border-primary/50 focus:bg-bg-surface/60 focus:shadow-[0_0_20px_rgba(var(--c-primary),0.15)] transition-all duration-300"
                maxlength="20"
                placeholder="例如：Project Phoenix"
                type="text"
              />
              <div
                class="absolute right-4 top-1/2 -translate-y-1/2 text-primary opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 pointer-events-none">
                <div class="i-carbon-edit text-xl"></div>
              </div>
            </div>
          </div>
          <div class="pt-2">
            <button
              :disabled="isLoading || !teamName.trim()"
              class="w-full h-12 rounded-xl bg-gradient-to-r from-primary to-blue-600 text-white font-bold tracking-wide shadow-glow hover:shadow-[0_0_30px_rgba(var(--c-primary),0.4)] hover:scale-[1.02] active:scale-[0.98] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              type="submit"
            >
              <div v-if="isLoading" class="i-carbon-circle-dash animate-spin text-xl"></div>
              <span v-else>立即创建团队</span>
              <div v-if="!isLoading" class="i-carbon-arrow-right text-lg"></div>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
