import 'dotenv/config'
import {app} from 'electron';
import path from 'path';
import {AiModelConfig} from '../../types/ai'

const getMirrorUrl = (originalUrl: string) => {
  return originalUrl.replace('huggingface.co', 'hf-mirror.com');
};
export const MODELS_DIR = path.join(app.getPath('userData'), 'models');
const BASE_URL = process.env.VITE_API_BASE_URL
const API_BASE_URL = `${BASE_URL}/download`;
const Qwen4B = 'https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q4_K_M.gguf?download=true'
const Qwen06B = 'https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF/resolve/main/Qwen3-Embedding-0.6B-Q8_0.gguf?download=true'
export const AVAILABLE_MODELS: AiModelConfig[] = [
  {
    id: 'unsloth/Qwen3-4B-Instruct-2507-GGUF',
    name: 'unsloth/Qwen3-4B-Instruct-2507-GGUF',
    description: '阿里巴巴 Qwen3 系列的 4B 指令微调模型，由 Unsloth 优化并量化，适合高效本地推理。',
    // 使用 HuggingFace 的 GGUF 下载链接 (Q4_K_M 量化版本平衡了速度和质量)
    downloadUrl: Qwen4B,
    mirrorUrl: getMirrorUrl(Qwen4B),
    filename: 'Qwen3-4B-Instruct-2507-GGUF-Q4_K_M.gguf',
    sizeBytes: 2590000000, // 约 2.6GB
    ramRequiredMB: 6144,
    category: 'llm', // 标记为 LLM
    tags: ['Chat Core'],
  },
  {
    id: 'Qwen/Qwen3-Embedding-0.6B-GGUF',
    name: 'Qwen/Qwen3-Embedding-0.6B-GGUF',
    description: '阿里巴巴 Qwen3 系列的 0.6B 嵌入模型，用于生成文本嵌入向量。',
    downloadUrl: Qwen06B,
    mirrorUrl: getMirrorUrl(Qwen06B),
    filename: 'Qwen3-Embedding-0.6B-GGUF',
    sizeBytes: 640000000, // 约 640MB
    ramRequiredMB: 512,
    category: 'embedding', // 标记为 Embedding
    tags: ['RAG', 'Memory'],
  },
  {
    id: 'sherpa-onnx/SenseVoiceSmall-Model',
    name: 'SenseVoice (Model)',
    description: '阿里 SenseVoice 语音识别模型主体',
    // 指向你的后端 API
    downloadUrl: `${API_BASE_URL}/sense-voice-model.int8.onnx`,
    // 后端直链通常不需要镜像，如果你的服务器在海外，这里可以填 CDN 地址
    mirrorUrl: `${API_BASE_URL}/sense-voice-model.int8.onnx`,
    filename: 'sense-voice-model.int8.onnx',
    sizeBytes: 204000000, // 约 204MB
    ramRequiredMB: 500,
    category: 'asr',
    bundleId: 'sensevoice-bundle'
  },
];

export const getModelPath = (filename: string) => path.join(MODELS_DIR, filename);
export const CHAT_MODEL_FILENAME: string = 'Qwen3-4B-Instruct-2507-GGUF-Q4_K_M.gguf';
export const EMBED_MODEL_FILENAME: string = 'Qwen3-Embedding-0.6B-GGUF';
