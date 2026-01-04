// src/api/auth.ts

import apiClient from './request';
/**
 * 用户注册 (第一步：提交信息，后端会自动发送验证码)
 */
export const register = (data: RegisterRequest): Promise<void> => {
  return apiClient.post('/auth/register/', data);
};

/**
 * 验证注册邮箱 (第二步：提交验证码)
 */
export const verifyEmail = (data: EmailVerificationRequest): Promise<{ message: string }> => {
  return apiClient.post('/auth/verify-email/', data);
};

/**
 * 用户登录
 */
export const login = (data: LoginRequest): Promise<TokenPair> => {
  return apiClient.post('/auth/login/', data);
};

/**
 * 忘记密码 (第一步：请求验证码)
 */
export const forgotPassword = (data: ForgotPasswordRequest): Promise<{ message: string }> => {
  return apiClient.post('/auth/forgot-password/', data);
};

/**
 * 重置密码 (第二步：提交验证码和新密码)
 */
export const resetPassword = (data: ResetPasswordRequest): Promise<{ message: string }> => {
  return apiClient.post('/auth/reset-password/', data );
};

/**
 * 登出
 */
export const logout = (): Promise<{ message: string }> => {
  return apiClient.post('/auth/logout/');
};


/**
 * 获取当前用户信息
 */
export const getMe = (): Promise<User> => {
  return apiClient.get('/auth/me/');
};

/**
 * 刷新 Access Token
 */
export const refreshToken = (data: RefreshTokenRequest): Promise<{ access: string }> => {
  return apiClient.post('/auth/token/refresh/', data);
};
