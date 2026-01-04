// src/main/p2p/ipc.ts
import {BrowserWindow, ipcMain, dialog} from 'electron'
import {ServiceDiscovery} from './discovery'
import {P2PTransport} from './transport'
import {
  FileChunkPayload,
  FileRequestPayload,
  MessageType,
  P2P_EVENTS, P2PConfig,
  P2PMessage,
  SearchRequestPayload, SearchResponsePayload
} from '../../types/p2p'
import {P2PFileManager} from './file-manager'
import path from 'path'
import fs from 'fs-extra'
import os from 'os'

console.log('[Main/P2P] ipc.ts module loaded!')

let discoveryService: ServiceDiscovery | null = null
let transportService: P2PTransport | null = null
let fileManager: P2PFileManager | null = null

const downloadBuffer = new Map<string, { total: number, written: number, path: string, stream: fs.WriteStream }>()

export function setupP2PIPC(mainWindow: BrowserWindow) {
  discoveryService = new ServiceDiscovery(mainWindow)
  transportService = new P2PTransport(mainWindow)
  fileManager = new P2PFileManager()

  if (transportService) {
    transportService.on('status', (status) => {
      mainWindow.webContents.send(P2P_EVENTS.CONNECTION_STATUS, status)
    })

    transportService.on('message', async (msg: P2PMessage) => {
      const {type, payload, senderId} = msg;
      switch (type) {
        case MessageType.SEARCH_REQUEST: {
          const {query, requestId} = payload as SearchRequestPayload
          const results = await fileManager?.search(query)
          if (results && results.length > 0) {
            const myId = transportService?.getSelfId() || '';
            const response: SearchResponsePayload = {
              requestId,
              results: results.map(r => ({...r, ownerId: myId}))
            }
            transportService?.sendMessage(senderId, MessageType.SEARCH_RESPONSE, response);
          }
          break
        }
        case MessageType.FILE_REQUEST: {
          const {fileId} = payload as FileRequestPayload
          const realPath = fileManager?.getFilePath(fileId)
          if (realPath) {
            transportService?.sendFile(senderId, realPath, fileId)
          }
          break
        }
        case MessageType.FILE_CHUNK: {
          await handleIncomingChunk(payload as FileChunkPayload, mainWindow)
          break
        }
        case MessageType.CHAT:
        case MessageType.SEARCH_RESPONSE:
        default:
          mainWindow.webContents.send(P2P_EVENTS.MESSAGE_RECEIVED, msg)
          break
      }
    })
  }

  ipcMain.on(P2P_EVENTS.START_DISCOVERY, async (_event, config: P2PConfig) => {
    if (!transportService || !discoveryService) return
    try {
      const port = await transportService.startServer(config.userId)
      discoveryService.start(config.username, config.userId, port)
    } catch (e) {
      console.error('Failed to start P2P:', e)
    }
  })

  ipcMain.on(P2P_EVENTS.STOP_DISCOVERY, () => {
    discoveryService?.stop()
    transportService?.stop()
  })

  ipcMain.on(P2P_EVENTS.CONNECT_PEER, (_event, {peerId, ip, port}) => {
    transportService?.connectToPeer(peerId, ip, port)
  })

  ipcMain.on(P2P_EVENTS.SEND_MESSAGE, (_event, {targetId, text}) => {
    transportService?.sendMessage(targetId, MessageType.CHAT, text)
  })

  ipcMain.handle(P2P_EVENTS.SET_SHARE_DIR, async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory']
    })
    if (result.canceled || result.filePaths.length === 0) return null
    const dir = result.filePaths[0]
    const count = await fileManager?.setSharedDirectory(dir)
    return {dir, count}
  })

  ipcMain.on(P2P_EVENTS.START_SEARCH, (_e, query: string) => {
    // 生成 ID 并在本地记录（或者前端记录）
    const requestId = crypto.randomUUID()
    const payload: SearchRequestPayload = {query, requestId}
    transportService?.broadcastMessage(MessageType.SEARCH_REQUEST, payload)
    // 也可以把 requestId 返回给前端
  })

  ipcMain.on(P2P_EVENTS.DOWNLOAD_FILE, (_e, {targetPeerId, fileId}) => {
    const payload: FileRequestPayload = {fileId}
    transportService?.sendMessage(targetPeerId, MessageType.FILE_REQUEST, payload)
  })
}

export function cleanupP2P() {
  try {
    discoveryService?.stop()
    transportService?.stop()
  } catch (e) {
    console.error('Error during cleanup:', e)
  }
}

async function handleIncomingChunk(payload: FileChunkPayload, mainWindow: BrowserWindow) {
  const {fileId, totalChunks, data, fileName} = payload

  try {
    // 1. 初始化写入流
    if (!downloadBuffer.has(fileId)) {
      const downloadsDir = path.join(os.homedir(), 'Downloads', 'TeamFlow')
      await fs.ensureDir(downloadsDir)

      // 处理同名文件：自动重命名
      let savePath = path.join(downloadsDir, fileName)
      if (await fs.pathExists(savePath)) {
        const ext = path.extname(fileName)
        const name = path.basename(fileName, ext)
        savePath = path.join(downloadsDir, `${name}_${Date.now()}${ext}`)
      }

      const stream = fs.createWriteStream(savePath)
      downloadBuffer.set(fileId, {
        total: totalChunks,
        written: 0,
        path: savePath,
        stream
      })
    }

    const bufferInfo = downloadBuffer.get(fileId)!

    // 2. 写入数据
    // data 从 IPC 过来可能是 Uint8Array 或 Buffer，确保兼容性
    const bufferData = Buffer.isBuffer(data) ? data : Buffer.from(data)

    // 写入并等待 drain (背压处理，防止内存爆涨)
    if (!bufferInfo.stream.write(bufferData)) {
      await new Promise<void>(resolve => bufferInfo.stream.once('drain', resolve))
    }

    bufferInfo.written++

    // 3. 通知进度 (每 10 个块或完成时通知)
    if (bufferInfo.written % 10 === 0 || bufferInfo.written === totalChunks) {
      const progress = Math.round((bufferInfo.written / totalChunks) * 100)
      mainWindow.webContents.send(P2P_EVENTS.DOWNLOAD_PROGRESS, {fileId, progress, fileName})
    }

    // 4. 完成
    if (bufferInfo.written >= totalChunks) {
      bufferInfo.stream.end()
      downloadBuffer.delete(fileId)
      console.log(`[P2P File] Download finished: ${bufferInfo.path}`)
      // 发送 100% 进度并提示完成
      mainWindow.webContents.send(P2P_EVENTS.DOWNLOAD_PROGRESS, {
        fileId,
        progress: 100,
        fileName,
        completedPath: bufferInfo.path
      })
    }

  } catch (error) {
    console.error('[P2P File] Write error:', error)
    // 错误处理：清理流
    if (downloadBuffer.has(fileId)) {
      downloadBuffer.get(fileId)?.stream.end()
      downloadBuffer.delete(fileId)
    }
  }
}
