<template>
  <div class="min-h-screen w-full flex overflow-hidden bg-bg relative font-sans text-text-main titlebar-drag-region">
    <WindowControls/>

    <!-- 返回首页 -->
    <button
      class="fixed top-6 left-6 z-50 flex items-center gap-2 text-text-muted hover:text-white transition-colors no-drag group bg-bg-card/30 px-4 py-2 rounded-full backdrop-blur-md border border-white/5 hover:border-white/20"
      @click="$router.push('/')"
    >
      <div class="i-carbon-arrow-left text-lg group-hover:-translate-x-1 transition-transform"></div>
      <span class="text-sm font-medium">返回首页</span>
    </button>

    <!-- 背景 -->
    <div class="absolute inset-0 z-0 select-none pointer-events-none">
      <div class="absolute inset-0 bg-gradient-to-bl from-bg-main via-bg-card to-bg-main"></div>
      <div
        class="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] bg-secondary/20 blur-[120px] rounded-full mix-blend-screen animate-pulse-slow"></div>
      <div class="absolute inset-0 bg-grid-pattern opacity-[0.03]"></div>
    </div>

    <!-- 左侧：Flux Engine -->
    <div class="hidden lg:flex w-5/12 relative z-10 flex-col justify-center items-center p-12">
      <div class="flux-core mb-12">
        <div
          class="absolute w-24 h-24 rounded-full bg-gradient-to-br from-secondary via-secondary to-primary shadow-[0_0_50px_rgba(var(--c-secondary),0.6)] z-10 animate-pulse"></div>
        <div
          class="flux-ring w-40 h-40 border-t-transparent border-l-transparent animate-spin-slow opacity-80 border-primary/40"></div>
        <div
          class="flux-ring w-56 h-56 border-b-transparent border-r-transparent animate-spin-reverse-slow border-white/20 opacity-60"></div>
        <div class="absolute w-64 h-64 animate-spin-slow">
          <div
            class="absolute bottom-0 right-1/2 translate-x-1/2 w-3 h-3 bg-white rounded-full shadow-[0_0_10px_white]"></div>
        </div>
      </div>
      <div class="text-center relative z-20">
        <h1 class="text-5xl font-bold text-white tracking-tight mb-4 drop-shadow-lg">Join the Grid</h1>
        <p class="text-lg text-text-muted font-light">Connect your mind to the collective.</p>
      </div>
    </div>

    <div class="w-full lg:w-7/12 flex justify-center items-center relative z-10 p-6">
      <!-- 【修正】no-drag -->
      <div
        class="glass-panel w-full max-w-[400px] p-10 animate-enter shadow-2xl border-white/10 min-h-[520px] flex flex-col justify-center no-drag">

        <div class="absolute top-0 left-0 w-full h-1 bg-white/5">
          <div :style="{ width: currentStep === 1 ? '50%' : '100%' }"
               class="h-full bg-gradient-to-r from-primary to-secondary transition-all duration-500 ease-out"></div>
        </div>

        <Transition mode="out-in" name="fade">
          <!-- Step 1 -->
          <div v-if="currentStep === 1" key="step1" class="w-full">
            <div class="mb-6">
              <h2 class="text-2xl font-bold text-white mb-1">创建账户</h2>
              <p class="text-sm text-text-muted">开启您的心流之旅</p>
            </div>
            <!-- 表单内容保持不变 -->
            <form class="space-y-4" @submit.prevent="handleRegisterStep1">
              <div class="space-y-1"><input v-model="registerForm.username"
                                            class="input-base bg-bg-surface/50 border-white/5"
                                            placeholder="用户名 (至少5位)" required type="text"/></div>
              <div class="space-y-1"><input v-model="registerForm.email"
                                            class="input-base bg-bg-surface/50 border-white/5" placeholder="邮箱地址"
                                            required type="email"/></div>
              <div class="space-y-1"><input v-model="registerForm.password"
                                            class="input-base bg-bg-surface/50 border-white/5" placeholder="密码"
                                            required type="password"/>
                <div class="text-[10px] text-text-muted/60 mt-1 pl-1 leading-tight space-y-0.5">
                  <p :class="{'text-primary': hasLength, 'text-red-400': isDirty && !hasLength}">• 至少8位</p>
                  <p :class="{'text-primary': hasCaseAndDigit, 'text-red-400': isDirty && !hasCaseAndDigit}">•
                    包含大写字母、小写字母和数字</p>
                  <p :class="{'text-primary': hasNoSymbol, 'text-red-400': isDirty && !hasNoSymbol}">• 仅限字母和数字
                    (不可包含特殊符号)</p>
                </div>
              </div>
              <div class="space-y-1"><input v-model="registerForm.confirmPassword"
                                            class="input-base bg-bg-surface/50 border-white/5" placeholder="确认密码"
                                            required type="password"/></div>
              <button :disabled="loading" class="btn-primary w-full justify-center mt-4 h-11 shadow-glow-sm"
                      type="submit">
                <span v-if="!loading">下一步</span>
                <div v-else class="i-carbon-circle-dash animate-spin text-xl"></div>
              </button>
            </form>
          </div>

          <!-- Step 2 -->
          <div v-else-if="currentStep === 2" key="step2" class="w-full text-center">
            <div class="w-16 h-16 bg-primary/20 rounded-full flex-center mx-auto mb-6 text-primary animate-pulse">
              <i class="i-carbon-email text-3xl"></i>
            </div>
            <h2 class="text-2xl font-bold text-white mb-2">验证您的邮箱</h2>
            <p class="text-sm text-text-muted mb-6">
              验证码已发送至 <span class="text-white font-mono block mt-1">{{ registerForm.email }}</span>
            </p>

            <form class="space-y-6" @submit.prevent="handleVerify">
              <input v-model="verifyForm.code"
                     class="input-base text-center text-2xl tracking-[0.5em] font-mono h-14 border-primary/30 focus:border-primary focus:shadow-glow-sm"
                     placeholder="XXXXXX" required type="text"/>

              <button :disabled="loading" class="btn-primary w-full justify-center h-11" type="submit">
                <span v-if="!loading">完成注册</span>
                <div v-else class="i-carbon-circle-dash animate-spin text-xl"></div>
              </button>

              <!-- 【新增】重发验证码按钮 -->
              <div class="flex justify-between items-center px-1">
                <button
                  class="text-xs text-text-muted hover:text-white underline transition-colors"
                  type="button"
                  @click="currentStep = 1"
                >
                  更换邮箱
                </button>
                <button
                  :disabled="resendCountdown > 0 || loading"
                  class="text-xs text-primary hover:text-primary-hover disabled:text-text-muted disabled:cursor-not-allowed transition-colors"
                  type="button"
                  @click="handleResendCode"
                >
                  {{ resendCountdown > 0 ? `${resendCountdown}秒后重发` : '重新发送验证码' }}
                </button>
              </div>
            </form>
          </div>
        </Transition>

        <div v-if="currentStep === 1" class="mt-6 text-center text-sm text-text-muted">
          已有账户？<a class="text-white font-medium hover:text-primary cursor-pointer transition-colors"
                      @click="$router.push('/login')">立即登录</a>
        </div>
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

const resendCountdown = ref(0);
let timer: ReturnType<typeof setInterval> | null = null;

const authStore = useAuthStore();
const router = useRouter();
const currentStep = ref(1);
const loading = ref(false);
const isDirty = ref(false);

const registerForm = reactive({username: '', email: '', password: '', confirmPassword: ''});
const verifyForm = reactive({code: ''});

const USERNAME_REGEX = /^[A-Za-z0-9]{5,}$/;
// 密码：8位以上，包含大小写和数字，且只能是字母和数字
const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$/;


const startCountdown = () => {
  resendCountdown.value = 60;
  if (timer) clearInterval(timer);
  timer = setInterval(() => {
    resendCountdown.value--;
    if (resendCountdown.value <= 0) {
      if (timer) clearInterval(timer);
    }
  }, 1000);
};


const hasLength = computed(() => registerForm.password.length >= 8);
const hasCaseAndDigit = computed(() => /(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(registerForm.password));
const hasNoSymbol = computed(() => /^[A-Za-z\d]*$/.test(registerForm.password));

watch(() => registerForm.password, () => {
  if (registerForm.password) isDirty.value = true;
});

const handleRegisterStep1 = async () => {
  if (!USERNAME_REGEX.test(registerForm.username)) {
    toast.error('用户名格式错误', {description: '用户名需至少5位，且仅包含字母或数字'});
    return;
  }

  if (!PASSWORD_REGEX.test(registerForm.password)) {
    toast.error('密码不符合要求', {
      description: '密码需至少8位，包含大小写字母和数字，且不包含特殊符号。'
    });
    return;
  }

  if (registerForm.password !== registerForm.confirmPassword) {
    toast.error('两次密码输入不一致');
    return;
  }

  loading.value = true;
  try {
    await authStore.register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password
    });
    toast.success('注册申请已提交，请查收邮件验证码');
    currentStep.value = 2;
    startCountdown();
  } catch (error: any) {
    const detail = error.response?.data?.detail;
    const msg = Array.isArray(detail) ? detail[0]?.msg : (detail || '注册请求失败');
    toast.error(msg);
  } finally {
    loading.value = false;
  }
};

const handleResendCode = async () => {
  if (resendCountdown.value > 0) return;
  loading.value = true;
  try {
    await authStore.register(registerForm);
    toast.success('验证码已重新发送');
    startCountdown();
  } catch (error: any) {
    toast.error(error.response?.data?.detail || '发送失败');
  } finally {
    loading.value = false;
  }
}

const handleVerify = async () => {
  if (!verifyForm.code) return;
  loading.value = true;
  try {
    await authStore.verifyEmail({
      email: registerForm.email,
      code: verifyForm.code
    });
    toast.success('注册成功！正在跳转登录页...');
    await router.push('/login');
  } catch (error: any) {
    const detail = error.response?.data?.detail;
    const msg = Array.isArray(detail) ? detail[0]?.msg : (detail || '验证失败，请检查验证码');
    toast.error(msg);
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
