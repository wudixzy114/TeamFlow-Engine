import apiClient from './request';

/**
 * 获取我的周报数据
 * @param date - 查询周的任意一天, 格式 YYYY-MM-DD
 */
export const getMyWeeklyDigest = (date: string): Promise<WeeklyDigestData> => {
  return apiClient.get('/me/weekly-digest/', {params: {date}});
};

/**
 * 获取我收到的所有 Kudos
 * (与 kudo.ts 重复，保留其一即可，这里保留也没事)
 */
export const listMyReceivedKudos = (): Promise<Kudos[]> => {
  return apiClient.get('/me/kudos/received/');
};

/**
 * 获取个人技能树
 * (之前遗漏)
 */
export const getMySkillTree = (): Promise<SkillTreeData> => {
  return apiClient.get('/me/skill_tree/');
};

/**
 * 修改个人技能树
 * (之前遗漏)
 */
export const updateMySkillTree = (data: object): Promise<SuccessMessage> => {
  // 文档中 RequestBody schema 为空对象 properties:{}，需确认后端实际需求，这里暂用 object
  return apiClient.put('/me/skill_tree/', data);
};
