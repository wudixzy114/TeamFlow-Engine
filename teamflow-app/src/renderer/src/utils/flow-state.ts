// src/utils/flow-state.ts

export const getFlowState = (x: number, y: number): { label: string; color: string; description: string } => {
  // x: Skill (-1 to 1), y: Challenge (-1 to 1)

  // 简单的区域判断，可根据实际需求微调阈值
  if (x > 0.3 && y > 0.3) return {label: 'Flow', color: 'text-primary', description: '全神贯注，巅峰状态'};
  if (x < -0.3 && y > 0.3) return {label: 'Anxiety', color: 'text-error', description: '挑战过高，感到焦虑'};
  if (x > 0.3 && y < -0.3) return {label: 'Relaxation', color: 'text-success', description: '游刃有余，轻松惬意'};
  if (x < -0.3 && y < -0.3) return {label: 'Apathy', color: 'text-muted', description: '缺乏动力，无感状态'};

  if (y > 0.3) return {label: 'Arousal', color: 'text-warning', description: '激发兴趣，稍显吃力'};
  if (y < -0.3) return {label: 'Boredom', color: 'text-secondary', description: '挑战不足，感到无聊'};
  if (x > 0.3) return {label: 'Control', color: 'text-accent', description: '掌控自如，信心十足'};
  if (x < -0.3) return {label: 'Worry', color: 'text-error', description: '能力不足，有些担忧'};

  return {label: 'Balance', color: 'text-text', description: '平衡状态'};
};
