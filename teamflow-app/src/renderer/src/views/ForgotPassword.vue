<template>
  <div class="min-h-screen w-full flex overflow-hidden bg-bg relative font-sans text-text-main titlebar-drag-region">
    <WindowControls/>
    <button
      class="fixed top-6 left-6 z-50 flex items-center gap-2 text-text-muted hover:text-white transition-colors no-drag group bg-bg-card/30 px-4 py-2 rounded-full backdrop-blur-md border border-white/5 hover:border-white/20"
      @click="$router.push('/')"
    >
      <div class="i-carbon-arrow-left text-lg group-hover:-translate-x-1 transition-transform"></div>
      <span class="text-sm font-medium">返回首页</span>
    </button>

    <!-- 背景 -->
    <div class="absolute inset-0 z-0 select-none pointer-events-none">
      <div class="absolute inset-0 bg-gradient-to-br from-bg-main via-bg-card to-bg-main"></div>
      <div
        class="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] bg-accent/10 blur-[120px] rounded-full mix-blend-screen animate-pulse-slow"></div>
      <div class="absolute inset-0 bg-grid-pattern opacity-[0.03]"></div>
    </div>

    <!-- 左侧：Flux Engine (Accent Mode) -->
    <div class="hidden lg:flex w-5/12 relative z-10 flex-col justify-center items-center p-12">
      <div class="flux-core mb-12">
        <!-- 金色核心 -->
        <div
          class="absolute w-24 h-24 rounded-full bg-gradient-to-br from-accent via-accent to-yellow-200 shadow-[0_0_50px_rgba(var(--c-accent),0.6)] z-10 animate-pulse"></div>
        <div
          class="flux-ring w-40 h-40 border-t-transparent border-l-transparent animate-spin-slow opacity-80 border-accent/40"></div>
        <div
          class="flux-ring w-56 h-56 border-b-transparent border-r-transparent animate-spin-reverse-slow border-white/20 opacity-60"></div>
      </div>
      <div class="text-center relative z-20">
        <h1 class="text-5xl font-bold text-white tracking-tight mb-4">Recovery</h1>
        <p class="text-lg text-text-muted font-light">Restore your access to the flow.</p>
      </div>
    </div>

    <div class="w-full lg:w-7/12 flex justify-center items-center relative z-10 p-6">
      <div
        class="glass-panel w-full max-w-[400px] p-10 animate-enter shadow-2xl border-white/10 min-h-[480px] flex flex-col justify-center no-drag">

        <Transition mode="out-in" name="fade">
          <!-- Step 1: 发送验证码 -->
          <div v-if="currentStep === 1" key="step1" class="w-full">
            <button
              class="mb-6 flex items-center text-text-muted hover:text-white transition-colors text-xs uppercase tracking-widest group"
              @click="$router.push('/login')">
              <div class="i-carbon-arrow-left mr-2 group-hover:-translate-x-1 transition-transform"></div>
              返回登录
            </button>
            <div class="mb-8">
              <h2 class="text-2xl font-bold text-white mb-2">找回密码</h2>
              <p class="text-sm text-text-muted">输入注册邮箱以获取验证码</p>
            </div>

            <form class="space-y-6" @submit.prevent="handleSendCode">
              <input v-model="sendCodeForm.email"
                     class="input-base bg-bg-surface/50 border-white/5 focus:border-accent/50"
                     placeholder="请输入邮箱地址" required type="email"/>
              <button :disabled="loading || countdown > 0"
                      class="btn-primary w-full justify-center h-11 bg-gradient-to-r from-accent to-yellow-600 border-accent/20"
                      type="submit">
                <span v-if="!loading">{{ countdown > 0 ? `${countdown}秒后可重发` : '发送验证码' }}</span>
                <div v-else class="i-carbon-circle-dash animate-spin text-xl"></div>
              </button>
            </form>
          </div>

          <!-- Step 2: 重置密码 -->
          <div v-else-if="currentStep === 2" key="step2" class="w-full">
            <div class="mb-6">
              <h2 class="text-2xl font-bold text-white mb-2">设置新密码</h2>
              <p class="text-sm text-text-muted">请保护好您的新安全凭证</p>
            </div>

            <form class="space-y-4" @submit.prevent="handleResetPassword">
              <input v-model="resetForm.code"
                     class="input-base text-center font-mono tracking-widest focus:border-accent/50"
                     placeholder="输入验证码" required type="text"/>

              <div class="space-y-1">
                <input v-model="resetForm.new_password"
                       class="input-base bg-bg-surface/50 border-white/5 focus:border-accent/50" placeholder="新密码"
                       required type="password"/>
                <div class="text-[10px] text-text-muted/60 mt-1 pl-1">规则：至少8位，包含大小写字母和数字，无特殊符号</div>
              </div>

              <input v-model="resetForm.confirmPassword"
                     class="input-base bg-bg-surface/50 border-white/5 focus:border-accent/50" placeholder="确认新密码"
                     required type="password"/>

              <button :disabled="loading"
                      class="btn-primary w-full justify-center h-11 bg-gradient-to-r from-accent to-yellow-600 border-accent/20 mt-2"
                      type="submit">
                <span v-if="!loading">确认重置</span>
                <div v-else class="i-carbon-circle-dash animate-spin text-xl"></div>
              </button>

              <div class="flex justify-between items-center px-1 mt-4">
                <button class="text-xs text-text-muted hover:text-white underline" type="button" @click="currentStep=1">
                  更换邮箱
                </button>
                <button
                  :disabled="countdown > 0 || loading"
                  class="text-xs text-accent hover:text-yellow-400 disabled:text-text-muted disabled:cursor-not-allowed transition-colors"
                  type="button"
                  @click="handleSendCode"
                >
                  {{ countdown > 0 ? `${countdown}秒后重发` : '重新发送验证码' }}
                </button>
              </div>
            </form>
          </div>
        </Transition>

      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref, reactive} from 'vue';
import {useAuthStore} from '@/stores/auth';
import {toast} from 'vue-sonner';
import {useRouter} from 'vue-router';
import WindowControls from "@/layouts/WindowControls.vue";

const authStore = useAuthStore();
const router = useRouter();
const currentStep = ref(1);
const countdown = ref(0);
const loading = ref(false);

const sendCodeForm = reactive({email: ''});
const resetForm = reactive({code: '', new_password: '', confirmPassword: ''});

// 正则校验
const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$/;

const handleSendCode = async () => {
  loading.value = true;
  try {
    // ForgotPasswordRequest ({email})
    await authStore.forgotPassword({email: sendCodeForm.email});
    toast.success(`验证码已发送至 ${sendCodeForm.email}`);
    currentStep.value = 2;
    startCountdown();
  } catch (error: any) {
    const detail = error.response?.data?.detail;
    toast.error(typeof detail === 'string' ? detail : '发送失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

const startCountdown = () => {
  countdown.value = 60;
  const timer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) clearInterval(timer);
  }, 1000);
};

const handleResetPassword = async () => {
  if (!PASSWORD_REGEX.test(resetForm.new_password)) {
    toast.error('密码不符合规则', {description: '需8位以上，包含大小写字母和数字，不可包含符号'});
    return;
  }
  if (resetForm.new_password !== resetForm.confirmPassword) {
    toast.error('两次密码不一致');
    return;
  }

  loading.value = true;
  try {
    await authStore.resetPassword({
      email: sendCodeForm.email,
      code: resetForm.code,
      new_password: resetForm.new_password,
    });
    toast.success('密码重置成功！请使用新密码登录');
    await router.push('/login');
  } catch (error: any) {
    const detail = error.response?.data?.detail;
    toast.error(typeof detail === 'string' ? detail : '重置失败，请检查验证码');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: scale(0.98);
}

.fade-leave-to {
  opacity: 0;
  transform: scale(1.02);
}
</style>
