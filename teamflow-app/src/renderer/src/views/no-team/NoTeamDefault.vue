<script lang="ts" setup>
import {useRouter} from 'vue-router'

const router = useRouter()
</script>

<template>
  <!-- 添加 no-drag：形成一个“交互岛屿”，岛屿内可点击，岛屿外(padding)可拖拽 -->
  <div class="w-full max-w-5xl flex flex-col items-center text-center no-drag">

    <div class="mb-12 space-y-4">
      <div
        class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-text-muted mb-4 backdrop-blur-md">
        <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
        <span>系统已就绪</span>
      </div>

      <h1 class="text-5xl md:text-6xl font-bold tracking-tight text-white drop-shadow-2xl">
        开启您的 <span class="text-transparent bg-clip-text bg-gradient-to-r from-primary via-white to-secondary">Team Flow</span>
      </h1>

      <p class="text-lg text-text-muted max-w-2xl mx-auto font-light leading-relaxed">
        您已进入个人心流空间。现在，请选择连接方式以解锁完整的协作能力。
        <br class="hidden md:block"/>无论是创建新规则，还是融入现有集体，都从这里开始。
      </p>
    </div>

    <!-- Action Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 w-full px-4 md:px-12">
      <!-- Create Team -->
      <div
        class="group relative h-64 glass-panel p-1 rounded-3xl cursor-pointer hover:-translate-y-2 transition-all duration-500 hover:shadow-[0_0_40px_rgba(var(--c-primary),0.3)]"
        @click="router.push('/no-team/create')"
      >
        <div
          class="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-3xl"></div>
        <div
          class="relative h-full bg-bg-card/40 rounded-[20px] p-8 flex flex-col items-center justify-center border border-white/5 overflow-hidden">
          <div
            class="i-carbon-add-alt text-[10rem] absolute -right-10 -bottom-10 text-white/5 group-hover:text-primary/10 group-hover:scale-110 group-hover:-rotate-12 transition-all duration-700"></div>
          <div
            class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center mb-6 shadow-glow group-hover:scale-110 transition-transform duration-500">
            <div class="i-carbon-add-alt text-3xl text-white"></div>
          </div>
          <h2 class="text-2xl font-bold text-white mb-2 relative z-10">创建新团队</h2>
          <p class="text-text-muted text-sm mb-6 relative z-10 opacity-80">我是管理者，我要定义规则</p>
          <span
            class="flex items-center text-primary font-bold text-sm bg-primary/10 px-4 py-2 rounded-full border border-primary/20 group-hover:bg-primary group-hover:text-white transition-all duration-300">
            立即创建 <div class="i-carbon-arrow-right ml-2 group-hover:translate-x-1 transition-transform"></div>
          </span>
        </div>
      </div>

      <!-- Join Team -->
      <div
        class="group relative h-64 glass-panel p-1 rounded-3xl cursor-pointer hover:-translate-y-2 transition-all duration-500 hover:shadow-[0_0_40px_rgba(var(--c-secondary),0.3)]"
        @click="router.push('/no-team/join')"
      >
        <div
          class="absolute inset-0 bg-gradient-to-br from-secondary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-3xl"></div>
        <div
          class="relative h-full bg-bg-card/40 rounded-[20px] p-8 flex flex-col items-center justify-center border border-white/5 overflow-hidden">
          <div
            class="i-carbon-collaborate text-[10rem] absolute -left-10 -bottom-10 text-white/5 group-hover:text-secondary/10 group-hover:scale-110 group-hover:rotate-12 transition-all duration-700"></div>
          <div
            class="w-16 h-16 rounded-2xl bg-gradient-to-br from-secondary to-orange-600 flex items-center justify-center mb-6 shadow-glow-secondary group-hover:scale-110 transition-transform duration-500">
            <div class="i-carbon-collaborate text-3xl text-white"></div>
          </div>
          <h2 class="text-2xl font-bold text-white mb-2 relative z-10">加入团队</h2>
          <p class="text-text-muted text-sm mb-6 relative z-10 opacity-80">我是成员，我有邀请码</p>
          <span
            class="flex items-center text-secondary font-bold text-sm bg-secondary/10 px-4 py-2 rounded-full border border-secondary/20 group-hover:bg-secondary group-hover:text-white transition-all duration-300">
            输入邀请码 <div class="i-carbon-login ml-2 group-hover:translate-x-1 transition-transform"></div>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
