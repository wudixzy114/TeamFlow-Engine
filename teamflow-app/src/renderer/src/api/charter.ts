import apiClient from './request';

/**
 * 获取团队心流公约
 * @param teamId - 团队 ID
 */
export const getCharter = (teamId: string): Promise<Charter> => {
  return apiClient.get(`/teams/${teamId}/charter/`);
};

/**
 * 更新团队心流公约 (管理员)
 * @param teamId - 团队 ID
 * @param data - 公约内容
 */
export const updateCharter = (teamId: string, data: { content: string }): Promise<void> => {
  return apiClient.put(`/teams/${teamId}/charter/`, data);
};
