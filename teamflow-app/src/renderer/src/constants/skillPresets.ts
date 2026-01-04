export interface SkillMetaData {
  proficiency: number; // 0 - 100
  status: 'learning' | 'mastered' | 'backlog';
  tags: string[];
  description?: string;
}

export const PRESET_TAGS = [
  'Deep Work', 'Leadership', 'Creativity', 'Frontend', 'Backend',
  'DevOps', 'Design', 'Communication', 'Strategy', 'Wellness'
];

export const STATUS_OPTIONS = [
  {value: 'learning', label: '正在攻克', icon: 'i-carbon-hourglass'},
  {value: 'mastered', label: '已掌握', icon: 'i-carbon-checkmark-filled'},
  {value: 'backlog', label: '计划中', icon: 'i-carbon-idea'},
];

// 根据主题获取颜色变量的辅助函数
export function getThemeColor(variable: string, alpha = 1) {
  const el = document.documentElement;
  const rgb = getComputedStyle(el).getPropertyValue(`--c-${variable}`).trim();
  return `rgba(${rgb}, ${alpha})`;
}
