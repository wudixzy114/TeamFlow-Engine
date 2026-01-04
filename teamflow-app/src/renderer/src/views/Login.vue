<template>
  <div class="min-h-screen w-full flex overflow-hidden bg-bg relative font-sans text-text-main titlebar-drag-region">

    <!-- 窗口控制 (右上角) -->
    <WindowControls/>

    <!-- 【新增】返回首页/取消登录 (左上角) -->
    <button
      class="fixed top-6 left-6 z-50 flex items-center gap-2 text-text-muted hover:text-white transition-colors no-drag group bg-bg-card/30 px-4 py-2 rounded-full backdrop-blur-md border border-white/5 hover:border-white/20"
      @click="$router.push('/')"
    >
      <div class="i-carbon-arrow-left text-lg group-hover:-translate-x-1 transition-transform"></div>
      <span class="text-sm font-medium">返回首页</span>
    </button>

    <!-- 背景与 Flux Engine (保持不变) -->
    <div class="absolute inset-0 z-0 select-none pointer-events-none">
      <div class="absolute inset-0 bg-gradient-to-br from-bg-main via-bg-card to-bg-main"></div>
      <div
        class="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/20 blur-[120px] rounded-full mix-blend-screen animate-pulse-slow"></div>
      <div
        class="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-secondary/10 blur-[120px] rounded-full mix-blend-screen"></div>
      <div class="absolute inset-0 bg-grid-pattern opacity-[0.03]"></div>
    </div>

    <!-- 左侧 Flux Engine -->
    <div class="hidden lg:flex w-5/12 relative z-10 flex-col justify-center items-center p-12 overflow-hidden">
      <div class="absolute inset-0 flex items-center justify-center opacity-[0.02] pointer-events-none">
        <span class="text-[20rem] font-bold tracking-tighter">FLOW</span>
      </div>
      <div class="flux-core mb-12">
        <div
          class="absolute w-24 h-24 rounded-full bg-gradient-to-br from-primary via-primary-hover to-secondary shadow-[0_0_50px_rgba(var(--c-primary),0.6)] z-10 animate-pulse"></div>
        <div class="flux-ring w-40 h-40 border-t-transparent border-l-transparent animate-spin-slow opacity-80"></div>
        <div
          class="flux-ring w-56 h-56 border-b-transparent border-r-transparent animate-spin-reverse-slow border-secondary/30 opacity-60"></div>
        <div class="absolute w-64 h-64 animate-spin-slow">
          <div
            class="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-3 bg-white rounded-full shadow-[0_0_10px_white]"></div>
        </div>
      </div>
      <div class="text-center relative z-20">
        <h1
          class="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white via-white to-white/70 tracking-tight mb-4 drop-shadow-lg">
          Team Flow</h1>
        <p class="text-lg text-text-muted font-light tracking-wide"><span class="text-primary font-medium">Focus</span>
          for depth. <span class="text-secondary font-medium">Connection</span> for scale.</p>
      </div>
    </div>

    <!-- 右侧：登录表单 -->
    <div class="w-full lg:w-7/12 flex justify-center items-center relative z-10 p-6">
      <!-- 【修正】no-drag 加在这里，而不是外层容器 -->
      <div class="glass-panel w-full max-w-[400px] p-10 animate-enter shadow-2xl border-white/10 no-drag">

        <div class="mb-8">
          <h2 class="text-2xl font-bold text-text-main mb-1">欢迎回来</h2>
          <p class="text-sm text-text-muted">进入您的心流工作台</p>
        </div>

        <form class="space-y-5" @submit.prevent="handleLogin">
          <div class="space-y-1.5">
            <label class="text-xs font-semibold text-text-muted uppercase tracking-wider ml-1">账号</label>
            <div class="relative group">
              <input v-model="loginForm.identifier"
                     :disabled="loading"
                     class="input-base bg-bg-surface/50 border-white/5 focus:border-primary/50 focus:bg-bg-surface transition-all duration-200"
                     placeholder="邮箱 或 用户名" required type="text"/>
            </div>
          </div>

          <div class="space-y-1.5">
            <div class="flex-between ml-1">
              <label class="text-xs font-semibold text-text-muted uppercase tracking-wider">密码</label>
              <a class="text-xs text-primary hover:text-white cursor-pointer transition-colors"
                 @click="$router.push('/forgot-password')">忘记密码？</a>
            </div>
            <div class="relative group">
              <input v-model="loginForm.password"
                     :disabled="loading"
                     class="input-base bg-bg-surface/50 border-white/5 focus:border-primary/50 focus:bg-bg-surface transition-all duration-200"
                     placeholder="" required type="password"/>
            </div>
          </div>

          <button :disabled="loading"
                  class="btn-primary w-full justify-center mt-6 h-11 text-base font-semibold tracking-wide shadow-glow-sm hover:shadow-glow transition-all duration-200 active:scale-[0.98]"
                  type="submit">
            <div v-if="loading" class="i-carbon-circle-dash animate-spin text-xl"></div>
            <span v-else>立即登录</span>
          </button>
        </form>

        <div class="mt-8 pt-6 border-t border-white/5 text-center text-sm text-text-muted">
          <span class="opacity-70">还没有账户？</span>
          <a class="text-text-main font-medium hover:text-primary cursor-pointer ml-2 transition-colors"
             @click="$router.push('/register')">创建新账户</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {reactive, ref} from 'vue';
import {useAuthStore} from '@/stores/auth';
import {toast} from 'vue-sonner';
import {useRouter} from 'vue-router';
import WindowControls from '@/layouts/WindowControls.vue';

const authStore = useAuthStore();
const router = useRouter();
const loading = ref(false);

const loginForm = reactive({identifier: '', password: ''});

const handleLogin = async () => {
  if (!loginForm.identifier || !loginForm.password) return;
  loading.value = true;
  try {
    await authStore.login({email: loginForm.identifier, password: loginForm.password});
    toast.success('欢迎回来！');
    await router.push('/');
  } catch (error: any) {
    const detail = error.response?.data?.detail;
    toast.error(typeof detail === 'string' ? detail : '登录失败');
  } finally {
    loading.value = false;
  }
};
</script>
