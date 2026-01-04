import apiClient from './request';

/**
 * 获取团队高光时刻列表
 */
export const listHighlights = (teamId: string): Promise<HighlightSingle[]> => {
  return apiClient.get(`/teams/${teamId}/highlights/`);
};

/**
 * 发布一个新的高光时刻
 */
export const createHighlight = (teamId: string, data: HighlightCreate): Promise<SuccessMessage> => {
  return apiClient.post(`/teams/${teamId}/highlights/`, data);
};

/**
 * 修改一个高光时刻
 */
export const updateHighlight = (teamId: string, data: HighlightUpdate): Promise<void> => {
  return apiClient.put(`/teams/${teamId}/highlights/modify/`, data);
};

/**
 * 删除一个高光时刻
 */
export const deleteHighlight = (teamId: string, data: HighlightDelete): Promise<SuccessMessage> => {
  return apiClient.delete(`/teams/${teamId}/highlights/delete/`, {data});
};

/**
 * 点赞一个高光时刻
 * 修正：文档定义为 PUT
 */
export const likeHighlight = (highlightId: string): Promise<SuccessMessage> => {
  return apiClient.put(`/highlights/${highlightId}/like/`);
};

/**
 * 取消点赞一个高光时刻
 * 修正：文档定义为 DELETE
 */
export const dislikeHighlight = (highlightId: string): Promise<SuccessMessage> => {
  return apiClient.delete(`/highlights/${highlightId}/dislike/`);
};

export const getComments = (highlightId: string): Promise<Comment[]> => {
  return apiClient.get(`/highlights/${highlightId}/all_comments/`);
};

export const createComment = (highlightId: string, data: CommentContentRequest): Promise<SuccessMessage> => {
  return apiClient.post(`/highlight/${highlightId}/comments/`, data);
};

export const updateComment = (highlightId: string, data: CommentModifyRequest): Promise<SuccessMessage> => {
  return apiClient.put(`/highlight/${highlightId}/comments/modify/`, data);
};

export const deleteComment = (highlightId: string, data: CommentDeleteRequest): Promise<SuccessMessage> => {
  return apiClient.delete(`/highlight/${highlightId}/comments/delete/`, {data});
};
