import apiClient from './request';

/**
 * 获取信息通知
 */
export const getMessages = (): Promise<Message[]> => {
  return apiClient.get('/me/message/');
};

/**
 * 删除信息通知
 */
export const deleteMessage = (data: MessageDelete): Promise<SuccessMessage> => {
  return apiClient.delete('/me/message/delete/', {data: data});
};

