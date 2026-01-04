import apiClient from './request';

/**
 * 获取当前用户加入的团队列表
 */
export const listMyTeams = (): Promise<Team[]> => {
  return apiClient.get('/teams/');
};

/**
 * 创建一个新团队
 */
export const createTeam = (data: TeamCreate): Promise<SuccessMessage> => {
  return apiClient.post('/teams/', data);
};

/**
 * 解散群组（管理员）
 */
export const deleteTeam = (teamId: string): Promise<SuccessMessage> => {
  return apiClient.delete(`/teams/${teamId}/delete/`);
};

/**
 * 邀请成员加入团队
 */
export const inviteMember = (teamId: string, data: InvitationCreateRequest): Promise<SuccessMessage> => {
  return apiClient.post(`/teams/${teamId}/invitations/`, data);
};

/**
 * 踢出组员（管理员）
 */
export const kickTeamMember = (teamId: string, payload: KickMemberRequest): Promise<SuccessMessage> => {
  return apiClient.delete(`/teams/${teamId}/kick/`, {data: payload});
};

/**
 * 接受团队邀请
 */
export const acceptInvitation = (data: InvitationCode): Promise<SuccessMessage> => {
  return apiClient.post('/teams/invitations/accept/', data);
};

/**
 * 拒绝加入群组
 */
export const declineInvitation = (payload: InvitationCode): Promise<SuccessMessage> => {
  return apiClient.delete('/teams/invitations/decline/', {data: payload});
};

/**
 * 退出群组 (管理员不能使用)
 */
export const leaveTeam = (teamId: string): Promise<SuccessMessage> => {
  return apiClient.delete(`/teams/${teamId}/leave/`);
};

/**
 * 更換群組管理者 (管理者)
 */
export const changeTeamOwner = (teamId: string, data: TeamOwnerUpdateRequest): Promise<SuccessMessage> => {
  return apiClient.put(`/teams/${teamId}/modify_owner/`, data);
};

/**
 * 获取个人所有邀请记录
 */
export const listAllMyInvites = (): Promise<InvitationRecord[]> => {
  return apiClient.get('/me/all_invite/');
};

/**
 * 修改群组信息（管理员）
 */
export const modifyTeam = (teamId: string, data: TeamNameUpdateRequest): Promise<SuccessMessage> => {
  return apiClient.put(`/teams/${teamId}/modify/`, data);
};

/**
 * 获取团队成员
 */
export const listMember = (teamId: string): Promise<TeamMembersResponse> => {
  return apiClient.get(`/teams/${teamId}/members/`);
};

/**
 * 删除团队心流公约（管理员）
 * (之前遗漏)
 */
export const deleteCharter = (teamId: string): Promise<SuccessMessage> => {
  // DELETE body 为空对象
  return apiClient.delete(`/teams/${teamId}/delete-charter/`, {data: {}});
};

/**
 * 获取团队技能树数据
 * (之前遗漏)
 */
export const getTeamSkillTree = (teamId: string): Promise<SkillTreeData> => {
  return apiClient.get(`/teams/${teamId}/skill-tree/`);
};
