import apiClient from './request';

/**
 * 为指定团队提交今日签到
 * @param teamId - 团队 ID
 * @param data - 签到数据
 */
export const createCheckin = (teamId: string, data: CheckinCreate): Promise<void> => {
  return apiClient.post(`/teams/${teamId}/checkins/`, data);
};

/**
 * 检查当前用户今天是否已为指定团队签到
 * @param teamId - 团队 ID
 */
export const checkTodayStatus = (teamId: string): Promise<CheckinTodayStatus> => {
  return apiClient.get(`/teams/${teamId}/checkins/today/`);
};
