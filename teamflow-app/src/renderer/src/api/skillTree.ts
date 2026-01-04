// --- skillTree.ts ---

import apiClient from './request';

/**
 * 获取个人技能树
 * GET /me/skill_tree/
 */
export const getSkillTree = (): Promise<SkillTreeData> => {
  return apiClient.get('/me/skill_tree/');
};

/**
 * 获取团队技能树数据
 * GET /teams/{team_id}/skill-tree/
 */
export const getTeamSkillTree = (teamId: string): Promise<SkillTreeData> => {
  return apiClient.get(`/teams/${teamId}/skill-tree/`);
};

/**
 * 添加个人技能节点（根节点）
 * POST /me/skill_tree/node
 */
export const addRootSkillNode = (data: UserSkillItemRequest): Promise<AddSkillNodeResponse> => {
  return apiClient.post('/me/skill_tree/node/', data);
};

/**
 * 添加个人技能节点（子节点）
 * POST /me/skill_tree/node/{parent_id}
 */
export const addChildSkillNode = (parentId: string, data: UserSkillItemRequest): Promise<AddSkillNodeResponse> => {
  return apiClient.post(`/me/skill_tree/node/${parentId}/`, data);
};

/**
 * 修改个人技能节点
 * PUT /me/skill_tree/node/{node_id}
 */
export const updateSkillNode = (nodeId: string, data: ModifyNodeRequest): Promise<SuccessMessage> => {
  return apiClient.put(`/me/skill_tree/node/${nodeId}/`, data);
};

/**
 * 删除个人技能节点
 * DELETE /me/skill_tree/node/{node_id}
 */
export const deleteSkillNode = (nodeId: string): Promise<SuccessMessage> => {
  return apiClient.delete(`/me/skill_tree/node/${nodeId}/`);
};
