import apiClient from './request';

/**
 * 查看指定团队的 flow session 记录
 * 修正：返回类型应为 FlowSession (含ID), 而不是 Create (不含ID)
 */
export const listFlowSessions = (teamId: string): Promise<FlowSession[]> => {
  return apiClient.get(`/teams/${teamId}/flow-sessions/`);
};

/**
 * 提交一次心流仪式(专注)记录
 */
export const createFlowSession = (teamId: string, data: FlowSessionCreate): Promise<SuccessMessage> => {
  return apiClient.post(`/teams/${teamId}/flow-sessions/`, data);
};

/**
 * 修改 flow 记录
 * (之前遗漏)
 */
export const updateFlowSession = (teamId: string, data: FlowSessionModify): Promise<SuccessMessage> => {
  return apiClient.put(`/teams/${teamId}/flow-sessions/modify/`, data);
};

/**
 * 删除 flow 记录
 * (之前遗漏)
 */
export const deleteFlowSession = (teamId: string, data: FlowSessionDelete): Promise<SuccessMessage> => {
  return apiClient.delete(`/teams/${teamId}/flow-sessions/delete/`, {data});
};
