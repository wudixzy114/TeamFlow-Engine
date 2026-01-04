import {ipcMain, BrowserWindow, IpcMainInvokeEvent} from 'electron';
import {modelManager} from './manager';
import {AI_IPC_CHANNELS} from '../../types/ai';
import {AVAILABLE_MODELS, EMBED_MODEL_FILENAME} from "./config";
import {aiEngine} from "./engine";

/**
 * 注册 AI 模块的所有 IPC 监听器
 */
export function setupAiIPC() {
  console.log('[AI Service] Initializing IPC handlers...');
  ipcMain.handle(AI_IPC_CHANNELS.GET_MODELS, () => {
    return modelManager.getModelsList();
  });
  ipcMain.handle(AI_IPC_CHANNELS.DOWNLOAD_MODEL, async (event: IpcMainInvokeEvent, modelId: string) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (!win) {
      console.error('[AI Service] Received download request but cannot find sender window.');
      throw new Error('Window not found');
    }
    console.log(`[AI Service] Starting download for model: ${modelId}`);

    // 注意：这里不使用 await 阻塞，而是触发异步下载，
    // 因为下载过程是通过 'ai:download-progress' 事件通知前端的。
    // 我们只捕获启动时的致命错误。
    modelManager.downloadModel(modelId, win).catch((err) => {
      console.error(`[AI Service] Fatal error starting download for ${modelId}:`, err);
    });

    return {status: 'started', modelId};
  });
  ipcMain.handle(AI_IPC_CHANNELS.CANCEL_DOWNLOAD, () => {
    console.log('[AI Service] Canceling current download...');
    modelManager.cancelDownload();
    return {status: 'canceled'};
  });
  ipcMain.handle(AI_IPC_CHANNELS.INIT_SESSION, async (_event, modelId?: string) => {
    try {
      let targetModelId = modelId;
      if (!targetModelId) {
        const allModels = modelManager.getModelsList();
        const chatModel = allModels.find(m =>
          m.isDownloaded && m.filename !== EMBED_MODEL_FILENAME
        );
        if (chatModel) targetModelId = chatModel.id;
      }

      const embedModel = AVAILABLE_MODELS.find(m => m.filename === EMBED_MODEL_FILENAME)
      if (!embedModel || !modelManager.isModelDownloaded(embedModel.id)) {
        console.warn("Embedding model missing. Tool retrieval will be disabled.");
      }

      if (!targetModelId) return {status: 'error', error: "No model downloaded"};

      const modelConfig = AVAILABLE_MODELS.find(m => m.id === targetModelId);
      if (!modelConfig || modelConfig.filename === EMBED_MODEL_FILENAME) return {
        status: 'error',
        error: "Model config invalid"
      };

      // 调用 Engine 加载
      await aiEngine.loadModel(modelConfig.filename);

      return {status: 'ready', modelName: modelConfig.name};
    } catch (error: any) {
      console.error("IPC Init Session Error:", error);
      return {status: 'error', error: error.message};
    }
  });
  ipcMain.handle(AI_IPC_CHANNELS.CHAT_STREAM, async (event, message: string) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (!win) return {status: 'error', error: 'No window found'};

    try {
      const response = await aiEngine.chat(message, (chunk) => {
        if (!win.isDestroyed()) {
          win.webContents.send(AI_IPC_CHANNELS.CHAT_REPLY_CHUNK, chunk);
        }
      });
      return {status: 'completed', fullResponse: response};
    } catch (error: any) {
      console.error("IPC Chat Error:", error);
      return {status: 'error', error: error.message};
    }
  });
  ipcMain.handle(AI_IPC_CHANNELS.RESET_SESSION, async () => {
    await aiEngine.resetSession();
    return {status: 'ok'};
  });
}

