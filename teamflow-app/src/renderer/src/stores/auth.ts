import {defineStore} from 'pinia';
import {computed, ref} from 'vue';
import {api} from '@/api';
import router from '@/router';
import {useTeamsStore} from "@/stores/teams";

export const useAuthStore = defineStore('auth', () => {
  // --- State ---
  const accessToken = ref<string | null>(null);
  const refreshToken = ref<string | null>(null);
  const user = ref<User | null>(null);
  const isLoggingOut = ref(false);

  // --- Getters ---
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value);
  const username = computed(() => user.value?.username || '未知用户');

  // --- Actions ---
  function setAuth(tokens: TokenPair) {
    accessToken.value = tokens.access;
    refreshToken.value = tokens.refresh;
  }

  function clearAuth() {
    accessToken.value = null;
    refreshToken.value = null;
    user.value = null;
  }

  /**
   * 用户登录
   */
  async function login(credentials: LoginRequest) {
    try {
      isLoggingOut.value = false;
      const tokens = await api.auth.login(credentials);
      setAuth(tokens);
      await fetchUser();
      await router.push('/');
    } catch (error) {
      console.error('Login process failed:', error);
      throw error;
    }
  }

  /**
   * 获取当前用户信息
   */
  async function fetchUser() {
    if (!accessToken.value) return;
    try {
      user.value = await api.auth.getMe();
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      logout(true);
    }
  }

  /**
   * 登出
   * @param forceExpired - 是否是因为 Token 过期导致的强制登出
   */
  async function logout(forceExpired = false) {
    if (isLoggingOut.value) return; // 防止重复调用
    isLoggingOut.value = true;
    const teamsStore = useTeamsStore();
    const wasAuth = !!accessToken.value;
    clearAuth();
    teamsStore.resetState();
    if (wasAuth && !forceExpired) {
      try {
        await api.auth.logout();
      } catch (error) {
        console.warn("Logout API call failed:", error);
      }
    }

    if (router.currentRoute.value.path !== '/login') {
      await router.replace('/login');
    }

    isLoggingOut.value = false;
  }

  /**
   * 注册 (第一步)
   */
  async function register(credentials: RegisterRequest) {
    await api.auth.register(credentials);
  }

  /**
   * 验证邮箱 (注册第二步)
   */
  async function verifyEmail(payload: EmailVerificationRequest) {
    await api.auth.verifyEmail(payload);
    await router.push('/login');
  }

  /**
   * 忘记密码 (第一步)
   */
  async function forgotPassword(payload: ForgotPasswordRequest) {
    await api.auth.forgotPassword(payload);
  }

  /**
   * 重置密码 (第二步)
   */
  async function resetPassword(payload: ResetPasswordRequest) {
    await api.auth.resetPassword(payload);
    await router.push('/login');
  }

  function setUserInfo(newUserInfo: User) {
    user.value = newUserInfo;
  }

  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    username,
    isLoggingOut,
    login,
    logout,
    fetchUser,
    register,
    verifyEmail,
    forgotPassword,
    resetPassword,
    setUserInfo,
  };
}, {
  persist: {
    pick: ['accessToken', 'refreshToken', 'user'],
  },
});
