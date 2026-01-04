import apiClient from './request';

/**
 * 获得用户信息
 */
export const getSelfInfo = (): Promise<User> => {
  return apiClient.get('/auth/me/');
};

/**
 * 修改个人信息 (除邮箱密码外)
 * 使用 UserInfoUpdate 类型 (支持部分更新)
 */
export const updateSelfInfo = (data: ModifyUserInfoRequest): Promise<SuccessMessage> => {
  return apiClient.put('/auth/modify_selfinfo/', data);
};

/**
 * 修改邮箱（发送验证码）
 */
export const updateEmail = (data: ResetEmailRequest): Promise<void> => {
  return apiClient.put('/auth/reset-email/', data);
};

/**
 * 修改邮箱验证
 */
export const emailVerify = (data: { code: string }): Promise<void> => {
  return apiClient.put('/auth/verify-email-reset/', data);
};
