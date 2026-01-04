import apiClient from './request';

// ======================
// 版块 (Sections)
// ======================

/**
 * 获取版块列表
 */
export const getForumSections = (teamId: string): Promise<ForumSection[]> => {
  return apiClient.get(`/teams/${teamId}/forum/sections/`);
};

/**
 * 创建新版块 (管理员)
 */
export const createForumSection = (teamId: string, data: ForumSectionCreateRequest): Promise<ForumSection> => {
  return apiClient.post(`/teams/${teamId}/forum/sections/`, data);
};

/**
 * 修改版块信息 (管理员)
 */
export const updateForumSection = (teamId: string, sectionId: string, data: ForumSectionModifyRequest): Promise<ForumSection> => {
  return apiClient.put(`/teams/${teamId}/forum/sections/${sectionId}/`, data);
};

/**
 * 删除版块 (管理员)
 */
export const deleteForumSection = (teamId: string, sectionId: string): Promise<SuccessMessage> => {
  return apiClient.delete(`/teams/${teamId}/forum/sections/${sectionId}/`);
};

// ======================
// 帖子 (Posts)
// ======================

/**
 * 获取帖子列表
 * @param page 默认 1
 * @param size 默认 20
 */
export const getForumPosts = (
  teamId: string,
  sectionId: string,
  page: number = 1,
  size: number = 20
): Promise<ForumPost[]> => {
  return apiClient.get(`/teams/${teamId}/forum/sections/${sectionId}/posts/`, {
    params: {page, size}
  });
};

/**
 * 发布新帖子
 */
export const createForumPost = (teamId: string, sectionId: string, data: ForumPostCreateRequest): Promise<ForumPost> => {
  return apiClient.post(`/teams/${teamId}/forum/sections/${sectionId}/posts/`, data);
};

/**
 * 获取帖子详情
 */
export const getForumPostDetail = (teamId: string, postId: string): Promise<ForumPost> => {
  return apiClient.get(`/teams/${teamId}/forum/posts/${postId}/`);
};

/**
 * 修改帖子
 */
export const updateForumPost = (teamId: string, postId: string, data: ForumPostModifyRequest): Promise<ForumPost> => {
  return apiClient.put(`/teams/${teamId}/forum/posts/${postId}/`, data);
};

/**
 * 删除帖子
 */
export const deleteForumPost = (teamId: string, postId: string): Promise<SuccessMessage> => {
  return apiClient.delete(`/teams/${teamId}/forum/posts/${postId}/`);
};

/**
 * 点赞帖子
 */
export const likeForumPost = (teamId: string, postId: string): Promise<SuccessMessage> => {
  return apiClient.put(`/teams/${teamId}/forum/posts/${postId}/like/`);
};

/**
 * 取消点赞帖子
 */
export const unlikeForumPost = (teamId: string, postId: string): Promise<SuccessMessage> => {
  return apiClient.delete(`/teams/${teamId}/forum/posts/${postId}/dislike/`);
};

// ======================
// 评论 (Comments)
// ======================

/**
 * 获取帖子评论列表
 */
export const getForumComments = (teamId: string, postId: string): Promise<ForumComment[]> => {
  return apiClient.get(`/teams/${teamId}/forum/posts/${postId}/comments/`);
};

/**
 * 发表评论
 */
export const createForumComment = (teamId: string, postId: string, data: ForumCommentCreateRequest): Promise<ForumComment> => {
  return apiClient.post(`/teams/${teamId}/forum/posts/${postId}/comments/`, data);
};

/**
 * 删除评论
 */
export const deleteForumComment = (teamId: string, commentId: string): Promise<SuccessMessage> => {
  return apiClient.delete(`/teams/${teamId}/forum/comments/${commentId}/`);
};
