// src/stores/chat/chatTags.ts

export type FieldType = 'text' | 'datetime' | 'select' | 'textarea';

export interface FormField {
  key: string;
  label: string;
  type: FieldType;
  placeholder?: string;
  options?: string[]; // 用于 select
  required?: boolean;
}

export interface TagConfig {
  key: string;
  label: string;
  icon: string;
  color: string;     //用于图标颜色
  cardTheme: string; // 用于卡片渐变背景
  fields?: FormField[]; // 如果没有字段，则是普通文本消息
}

// 基础类型
export const BASIC_TAGS = ['text', 'file', 'image'];

// 社交连接类型 (Connection)
export const SOCIAL_TAGS: Record<string, TagConfig> = {
  meal: {
    key: 'meal',
    label: '约饭搭子',
    icon: 'i-carbon-restaurant',
    color: 'text-orange-400',
    cardTheme: 'bg-gradient-to-br from-orange-500/90 to-red-500/90',
    fields: [
      {key: 'title', label: '吃什么', type: 'text', placeholder: '例如：楼下轻食', required: true},
      {key: 'location', label: '地点', type: 'text', placeholder: '餐厅名称或集合点', required: true},
      {key: 'time', label: '出发时间', type: 'datetime', required: true},
      {key: 'note', label: '备注', type: 'textarea', placeholder: '辣度、忌口等...'}
    ]
  },
  activity: {
    key: 'activity',
    label: '集体活动',
    icon: 'i-carbon-activity',
    color: 'text-emerald-400',
    cardTheme: 'bg-gradient-to-br from-emerald-500/90 to-teal-600/90',
    fields: [
      {key: 'title', label: '活动主题', type: 'text', placeholder: '例如：羽毛球局', required: true},
      {key: 'time', label: '活动时间', type: 'datetime', required: true},
      {key: 'location', label: '地点', type: 'text', required: true},
      {key: 'max_people', label: '人数限制', type: 'text', placeholder: '例如：4人'}
    ]
  },
  teambuilding: {
    key: 'teambuilding',
    label: '正式团建',
    icon: 'i-carbon-events',
    color: 'text-violet-400',
    cardTheme: 'bg-gradient-to-br from-violet-600/90 to-purple-600/90',
    fields: [
      {key: 'title', label: '团建名称', type: 'text', required: true},
      {key: 'description', label: '详细安排', type: 'textarea', required: true},
      {key: 'link', label: '相关链接', type: 'text', placeholder: '文档或投票链接'}
    ]
  },
  entertainment: {
    key: 'entertainment',
    label: '摸鱼/娱乐',
    icon: 'i-carbon-game-console',
    color: 'text-pink-400',
    cardTheme: 'bg-gradient-to-br from-pink-500/90 to-rose-500/90',
    fields: [
      {key: 'game', label: '游戏/项目', type: 'text', required: true},
      {
        key: 'platform',
        label: '平台',
        type: 'select',
        options: ['PC', 'Mobile', 'Switch', 'PS5', 'Board Game'],
        required: true
      },
      {key: 'time', label: '开始时间', type: 'text', placeholder: '现在 / 下班后'}
    ]
  }
};

export const isSpecialTag = (tag: string): boolean => {
  return !BASIC_TAGS.includes(tag) && !!SOCIAL_TAGS[tag];
};

export const getTagConfig = (tag: string): TagConfig | null => {
  return SOCIAL_TAGS[tag] || null;
};
