// src/main/ai/types.ts

// 定义支持的模型配置
export interface AiModelConfig {
  id: string;
  name: string;
  description: string;
  downloadUrl: string;
  mirrorUrl?: string;
  filename: string; // 本地存储的文件名
  sizeBytes: number; // 用于计算进度
  ramRequiredMB: number; // 推荐内存
  category: ModelCategory; // 新增：分类
  tags?: string[];         // 新增：标签，如 ['RAG Core', 'Voice']
  bundleId?: string;
}

export type ModelCategory = 'llm' | 'embedding' | 'asr';

// 下载进度事件接口
export interface DownloadProgress {
  modelId: string;
  receivedBytes: number;
  totalBytes: number;
  speedBytesPerSecond: number;
  progress: number; // 0-100
  status: 'pending' | 'downloading' | 'completed' | 'error';
  errorMessage?: string;
  source?: 'mirror' | 'origin';
}

// 工具定义 (Function Calling)
export interface ToolParameter {
  type: string;
  properties: Record<string, any>;
  required?: string[];
}

export interface AiTool {
  name: string;
  description: string;
  parameters: {
    type: 'object';
    properties: Record<string, any>;
  };
  // scope 决定工具是在主进程直接运行，还是需要发往渲染进程
  scope: 'main' | 'renderer';
  handler: (args: any) => Promise<any>;
}

// AI Service 的状态
export interface AiServiceStatus {
  isModelLoaded: boolean;
  currentModelId?: string;
  isInferencing: boolean;
}

export const AI_IPC_CHANNELS = {
  GET_MODELS: 'ai:get-models',
  DOWNLOAD_MODEL: 'ai:download-model',
  CANCEL_DOWNLOAD: 'ai:cancel-download',
  ON_DOWNLOAD_PROGRESS: 'ai:download-progress',
  CHAT_STREAM: 'ai:chat-stream',
  INIT_SESSION: 'ai:init-session', // 新增
  CHAT_REPLY_CHUNK: 'ai:chat-reply-chunk', // Main -> Renderer
  RESET_SESSION: 'ai:reset-session',
  EXECUTE_RENDERER_ACTION: 'ai:execute-renderer-action',
} as const;

export interface AsrResult {
  text: string;
  duration?: number;
}

