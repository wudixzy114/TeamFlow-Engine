import apiClient from './request';

/**
 * 发送一张 Kudos 能量卡
 * @param teamId - 团队 ID
 * @param data - Kudos 创建数据
 */
export const sendKudos = (teamId: string, data: KudosCreate): Promise<SuccessMessage> => {
  return apiClient.post(`/teams/${teamId}/kudos/`, data);
};

/**
 * 获取当前用户收到的所有 Kudos
 */
export const listMyReceivedKudos = (): Promise<Kudos[]> => {
  return apiClient.get('/me/kudos/received/');
};

