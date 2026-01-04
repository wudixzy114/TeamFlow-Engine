import fs from 'fs-extra';
import axios from 'axios';
import {BrowserWindow} from 'electron';
import {AVAILABLE_MODELS, MODELS_DIR, getModelPath} from './config';
import {DownloadProgress} from '../../types/ai';

class ModelManager {
  private downloadController: AbortController | null = null

  constructor() {
    this.initStorage()
  }

  isModelDownloaded(modelId: string): boolean {
    const model = AVAILABLE_MODELS.find((m) => m.id === modelId);
    if (!model) return false
    const filePath = getModelPath(model.filename);
    return fs.existsSync(filePath) && fs.statSync(filePath).size > 0;
  }

  getModelsList() {
    return AVAILABLE_MODELS.map((m) => ({
      ...m,
      isDownloaded: this.isModelDownloaded(m.id)
    }))
  }

  cancelDownload() {
    if (this.downloadController) {
      this.downloadController.abort();
      this.downloadController = null;
    }
  }

  async downloadModel(modelId: string, win: BrowserWindow) {
    const model = AVAILABLE_MODELS.find((m) => m.id === modelId);
    if (!model) throw new Error(`Model ${modelId} not found`);

    const filePath = getModelPath(model.filename);

    if (await fs.pathExists(filePath)) {
      this.broadcastProgress(win, {
        modelId,
        receivedBytes: model.sizeBytes,
        totalBytes: model.sizeBytes,
        speedBytesPerSecond: 0,
        progress: 100,
        status: 'completed',
      });
      return;
    }

    this.downloadController = new AbortController();

    // 尝试顺序：镜像 -> 源站
    const sources: { url: string, type: string }[] = [];
    if (model.mirrorUrl) sources.push({url: model.mirrorUrl, type: 'mirror'});
    sources.push({url: model.downloadUrl, type: 'origin'});

    for (const source of sources) {
      try {
        console.log(`[AI Model] Trying download from ${source.type}: ${source.url}`);
        await this.performDownload(source.url, filePath, model.sizeBytes, modelId, win, source.type as 'mirror' | 'origin');

        // 如果代码执行到这里，说明下载成功，跳出循环
        return;
      } catch (error) {
        if (axios.isCancel(error)) {
          console.log('[AI Model] Download canceled by user.');
          await fs.remove(filePath); // 删除未完成的文件
          return;
        }

        console.warn(`[AI Model] Failed to download from ${source.type}. Error: ${error}`);

        // 如果这是最后一个源，且依然失败，抛出错误
        if (source === sources[sources.length - 1]) {
          this.broadcastProgress(win, {
            modelId,
            receivedBytes: 0,
            totalBytes: model.sizeBytes,
            speedBytesPerSecond: 0,
            progress: 0,
            status: 'error',
            errorMessage: `All sources failed. Last error: ${error}`
          });
          await fs.remove(filePath);
        }
        // 否则继续尝试下一个源
      }
    }
  }

  async downloadPrivateFile(
    filename: string,
    downloadUrl: string,
    authToken: string,
    win: BrowserWindow
  ) {
    const filePath = getModelPath(filename);

    // 1. 检查文件是否存在
    if (await fs.pathExists(filePath)) {
      const stats = await fs.stat(filePath);
      // 如果文件已存在，直接广播 100% 进度
      this.broadcastPrivateProgress(win, {
        filename,
        receivedBytes: stats.size,
        totalBytes: stats.size,
        progress: 100,
        status: 'completed',
      });
      return;
    }

    this.downloadController = new AbortController();

    try {
      console.log(`[AI Private Download] Starting: ${filename}`);

      const writer = fs.createWriteStream(filePath);

      const response = await axios({
        method: 'get',
        url: downloadUrl,
        responseType: 'stream',
        headers: {
          'Authorization': authToken, // 直接注入前端传来的 Bearer Token
        },
        signal: this.downloadController.signal,
        timeout: 15000,
      });

      const totalBytes = parseInt(response.headers['content-length'] || '0', 10);
      let downloadedLength = 0;
      let startTime = Date.now();
      let lastUpdate = 0;

      response.data.on('data', (chunk: Buffer) => {
        downloadedLength += chunk.length;
        const now = Date.now();

        // 500ms 节流发送进度，避免阻塞 IPC
        if (now - lastUpdate > 500) {
          const duration = (now - startTime) / 1000;
          const speed = duration > 0 ? downloadedLength / duration : 0;

          this.broadcastPrivateProgress(win, {
            filename,
            receivedBytes: downloadedLength,
            totalBytes,
            speedBytesPerSecond: speed,
            progress: totalBytes > 0 ? Math.min(Math.round((downloadedLength / totalBytes) * 100), 99) : 0,
            status: 'downloading',
          });
          lastUpdate = now;
        }
      });

      response.data.pipe(writer);

      await new Promise<void>((resolve, reject) => {
        writer.on('finish', () => {
          this.broadcastPrivateProgress(win, {
            filename,
            receivedBytes: totalBytes,
            totalBytes,
            progress: 100,
            status: 'completed',
          });
          resolve();
        });
        writer.on('error', reject);
        response.data.on('error', reject);
      });

    } catch (error) {
      if (axios.isCancel(error)) {
        console.log('[AI Private Download] Canceled.');
        await fs.remove(filePath);
      } else {
        console.error(`[AI Private Download] Failed: ${error}`);
        this.broadcastPrivateProgress(win, {
          filename,
          progress: 0,
          status: 'error',
          errorMessage: String(error)
        });
        await fs.remove(filePath); // 失败时清理残文件
      }
    }
  }

  // 单次下载执行逻辑
  private async performDownload(
    url: string,
    filePath: string,
    totalBytes: number,
    modelId: string,
    win: BrowserWindow,
    sourceType: 'mirror' | 'origin'
  ): Promise<void> {
    const writer = fs.createWriteStream(filePath);

    const response = await axios({
      method: 'get',
      url: url,
      responseType: 'stream',
      signal: this.downloadController!.signal,
      timeout: 10000, // 连接超时 10s，超时后自动换源
    });

    let downloadedLength = 0;
    let startTime = Date.now();
    let lastUpdate = 0;

    response.data.on('data', (chunk: Buffer) => {
      downloadedLength += chunk.length;
      const now = Date.now();

      if (now - lastUpdate > 500) {
        const duration = (now - startTime) / 1000;
        const speed = duration > 0 ? downloadedLength / duration : 0;

        this.broadcastProgress(win, {
          modelId,
          receivedBytes: downloadedLength,
          totalBytes: totalBytes,
          speedBytesPerSecond: speed,
          progress: Math.min(Math.round((downloadedLength / totalBytes) * 100), 99), // 99%封顶，完成时才100
          status: 'downloading',
          source: sourceType
        });
        lastUpdate = now;
      }
    });

    response.data.pipe(writer);

    return new Promise((resolve, reject) => {
      writer.on('finish', () => {
        this.broadcastProgress(win, {
          modelId,
          receivedBytes: totalBytes,
          totalBytes: totalBytes,
          speedBytesPerSecond: 0,
          progress: 100,
          status: 'completed',
          source: sourceType
        });
        resolve();
      });
      writer.on('error', reject);
      response.data.on('error', reject); // 网络断开等错误
    });
  }

  private async initStorage() {
    await fs.ensureDir(MODELS_DIR)
  }

  private broadcastProgress(win: BrowserWindow, status: DownloadProgress) {
    if (!win.isDestroyed()) {
      win.webContents.send('ai:download-progress', status);
    }
  }

  private broadcastPrivateProgress(win: BrowserWindow, status: any) {
    if (!win.isDestroyed()) {
      win.webContents.send('ai:private-download-progress', status);
    }
  }
}

export const modelManager = new ModelManager();
