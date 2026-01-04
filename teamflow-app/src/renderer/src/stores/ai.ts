import {defineStore} from 'pinia'
import {ref} from 'vue'

// 对应后端的类型定义
export interface AiModel {
  id: string
  name: string
  description: string
  sizeBytes: number
  ramRequiredMB: number
  isDownloaded: boolean
}

export interface DownloadStatus {
  modelId: string
  receivedBytes: number
  totalBytes: number
  speed: number
  progress: number
  status: 'pending' | 'downloading' | 'completed' | 'error'
  source?: 'mirror' | 'origin' // 显示当前下载源
  errorMessage?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  isStreaming?: boolean // 是否正在生成中
}

export const useAiStore = defineStore('ai', () => {
  const models = ref<AiModel[]>([])
  const downloadState = ref<Record<string, DownloadStatus>>({})

  const messages = ref<ChatMessage[]>([])
  const isSessionReady = ref(false)
  const isGenerating = ref(false)
  const currentModelName = ref('')

  let stopDownloadListener: (() => void) | undefined
  let stopChatListener: (() => void) | undefined

  // 初始化监听器
  const initListener = () => {
    if (stopDownloadListener) stopDownloadListener()
    if (stopChatListener) stopChatListener()
    // 监听后端发来的进度事件
    stopDownloadListener = window.ai.onDownloadProgress((data: DownloadStatus) => {
      downloadState.value[data.modelId] = data
      // 如果下载完成，自动刷新列表以更新 isDownloaded 状态
      if (data.status === 'completed') {
        fetchModels()
      }
    })

    stopChatListener = window.ai.onChatReply((chunk: string) => {
      // 找到最后一条消息（如果是 AI 的正在流式传输的消息）
      const lastMsg = messages.value[messages.value.length - 1]

      if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
        lastMsg.content += chunk
      } else if (!lastMsg || lastMsg.role !== 'assistant' || !lastMsg.isStreaming) {
        messages.value.push({
          id: Date.now().toString(),
          role: 'assistant',
          content: chunk,
          timestamp: Date.now(),
          isStreaming: true
        })
      }
    })
  }

  const initSession = async (modelId?: string) => {
    isSessionReady.value = false
    try {
      const res = await window.ai.initSession(modelId)
      if (res.status === 'ready' && res.modelName) {
        isSessionReady.value = true
        currentModelName.value = res.modelName
        // 添加一条系统欢迎语
        messages.value = [{
          id: 'system-init',
          role: 'assistant',
          content: `AI Engine Ready. Loaded model: **${res.modelName}**. How can I help you today?`,
          timestamp: Date.now()
        }]
      } else {
        console.error("Session init failed:", res.error)
        messages.value = [{
          id: 'system-error',
          role: 'system',
          content: `Failed to initialize AI session. Error: ${res.error || 'Unknown error'}`,
          timestamp: Date.now()
        }]
      }
    } catch (e) {
      console.error(e)
      messages.value = [{
        id: 'system-error',
        role: 'system',
        content: `A critical error occurred while initializing the session: ${e}`,
        timestamp: Date.now()
      }]
    }
  }

  const sendMessage = async (text: string) => {
    if (!text.trim() || isGenerating.value) return

    // 1. 添加用户消息
    messages.value.push({
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: Date.now()
    })

    isGenerating.value = true

    try {
      // 2. 预先添加一个空的 AI 消息占位 (可选，或者让监听器自动创建)
      // 这里我们让监听器自动创建，但我们可以设一个 flag

      // 3. 调用后端
      const res = await window.ai.chat(text)

      // 4. 完成
      if (res.status === 'completed') {
        // 标记最后一条消息结束流式传输
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg && lastMsg.role === 'assistant') {
          lastMsg.isStreaming = false
        }
      }
    } catch (e) {
      messages.value.push({
        id: Date.now().toString(),
        role: 'system',
        content: `Error: ${e}`,
        timestamp: Date.now()
      })
    } finally {
      isGenerating.value = false
    }
  }

  const clearSession = async () => {
    await window.ai.resetSession()
    messages.value = []
  }

  // 获取模型列表
  const fetchModels = async () => {
    try {
      models.value = await window.ai.getModels()
    } catch (error) {
      console.error('Failed to fetch models:', error)
    }
  }

  // 开始下载
  const downloadModel = async (modelId: string) => {
    // 设置初始状态
    downloadState.value[modelId] = {
      modelId,
      receivedBytes: 0,
      totalBytes: 0,
      speed: 0,
      progress: 0,
      status: 'pending'
    }
    await window.ai.downloadModel(modelId)
  }

  // 取消下载
  const cancelDownload = async () => {
    await window.ai.cancelDownload()
    // 状态会被后端的 error 事件更新，或者我们可以手动重置
  }

  return {
    models,
    downloadState,
    initListener,
    fetchModels,
    downloadModel,
    cancelDownload,

    messages,
    isSessionReady,
    isGenerating,
    currentModelName,
    initSession,
    sendMessage,
    clearSession
  }
})
