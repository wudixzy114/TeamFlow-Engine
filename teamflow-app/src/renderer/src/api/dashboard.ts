import apiClient from './request';

type Period = 'day' | 'week' | 'month';

/**
 * 获取团队情绪罗盘数据
 */
export const getCompassData = (teamId: string, period: Period): Promise<CompassData> => {
  return apiClient.get(`/dashboard/teams/${teamId}/compass/`, { params: { period } });
};

/**
 * 获取团队有效专注时长数据
 */
export const getFocusTimeData = (teamId: string, period: Period): Promise<FocusTimeData> => {
  return apiClient.get(`/dashboard/teams/${teamId}/focus-time/`, { params: { period } });
};

/**
 * 获取 AI 洞察墙数据
 */
export const getInsightsData = (teamId: string, period: Period): Promise<AIInsights> => {
  return apiClient.get(`/dashboard/teams/${teamId}/insights/`, { params: { period } });
};
