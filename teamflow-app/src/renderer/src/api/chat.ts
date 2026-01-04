import apiClient from './request';

export interface GetChatParams {
  before_msg_id?: string;
  after_msg_id?: string;
}

/**
 * 获取群组聊天信息
 * @param teamId 团队ID
 * @param params 查询参数 (before_msg_id, after_msg_id)
 */
export const getChatMessages = (teamId: string, params?: GetChatParams) => {
  return apiClient.get<any, TeamChat[]>(`/teams/${teamId}/chat/messages/`, {
    params: {
      before_msg_id: params?.before_msg_id,
      after_msg_id: params?.after_msg_id
    }
  });
};

/**
 * 发送消息
 */
export const sendChatMessage = (teamId: string, data: NewTeamChatRequest) => {
  return apiClient.post<any, SendMessageResponse>(`/teams/${teamId}/chat/post_messages/`, data);
};

/**
 * 删除消息
 * 注意：根据 OpenAPI，这是一个 DELETE 请求，但参数是在 Body 中传递的
 */
export const deleteChatMessage = (teamId: string, data: DeleteTeamChatRequest) => {
  // Axios 的 delete 第二个参数是 config，body 需要放在 config.data 中
  return apiClient.delete<any, SendMessageResponse>(`/teams/${teamId}/chat/delete_messages/`, {
    data: {id: data.id} // 对应后端 schema NewTeamChatID
  });
};

/**
 * 上传文件
 */
export const uploadChatFile = (teamId: string, data: FileUploadRequest) => {
  const formData = new FormData();
  formData.append('tag', data.tag);
  formData.append('file', data.file);

  return apiClient.post<any, any>(`/teams/${teamId}/chat/post_file/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

