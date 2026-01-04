import axios, {type AxiosInstance, type InternalAxiosRequestConfig, type AxiosError} from 'axios';
import {useAuthStore} from '@/stores/auth';
import {toast} from 'vue-sonner';

// 环境变量获取
const baseURL = import.meta.env.VITE_API_BASE_URL;

const apiClient: AxiosInstance = axios.create({
  baseURL: baseURL,
  timeout: 15000, //稍微增加超时时间以适应慢网
});

// --- 请求拦截器 ---
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const authStore = useAuthStore();
    const accessToken = authStore.accessToken;

    if (accessToken && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error: AxiosError) => {
    console.error('Request setup error:', error);
    return Promise.reject(error);
  }
);

// --- 响应拦截器 ---
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  async (error: AxiosError<{ detail?: string | any }>) => {
    const {response, config} = error;
    const authStore = useAuthStore();

    // 处理没有响应的情况 (网络错误/服务器宕机)
    if (!response) {
      toast.error('网络连接异常，请检查您的网络设置');
      return Promise.reject(error);
    }

    const status = response.status;
    const data = response.data;

    // 获取后端返回的错误信息
    let errorMessage = '请求发生错误，请稍后再试';

    if (data?.detail) {
      if (typeof data.detail === 'string') {
        errorMessage = data.detail;
      } else if (Array.isArray(data.detail) && data.detail.length > 0) {
        // 处理 FastAPI/Pydantic 的验证错误数组
        errorMessage = data.detail.map((e: any) => e.msg).join(', ');
      }
    }

    switch (status) {
      case 400:
        toast.error(errorMessage);
        break;

      case 401:
        // 区分是 "登录接口本身失败" 还是 "Token 过期"
        const isLoginAttempt = config?.url?.endsWith('/auth/login/');
        const isLogoutAttempt = config?.url?.endsWith('/auth/logout/');

        if (isLoginAttempt) {
          toast.error('邮箱或密码错误，请重试');
        } else if (isLogoutAttempt) {
          // 登出失败直接忽略，前端清理即可
          console.warn('Logout API returned 401');
        } else {
          // Token 过期
          if (authStore.accessToken && !authStore.isLoggingOut) { // 防止重复弹窗
            toast.error('登录已过期，请重新登录');
            authStore.logout(true); // true 表示因过期而被动登出
          }
        }
        break;

      case 403:
        toast.error('您没有权限执行此操作');
        break;

      case 404:
        // 某些业务逻辑（如检查签到状态、获取公约）可能依赖 404 状态码做逻辑判断
        // 这里可以做一个简单的过滤，如果不是 GET 请求或者是特定的静默检查，可以不弹窗
        // 为了通用性，暂时只对明确的资源缺失报错
        if (config?.method !== 'get') {
          toast.error('请求的资源不存在');
        }
        break;

      case 422:
        toast.error(`数据校验失败: ${errorMessage}`);
        break;

      case 500:
        toast.error('服务器内部错误，请联系管理员');
        break;

      default:
        toast.error(errorMessage);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
