import {contextBridge, ipcRenderer} from 'electron'
import {electronAPI} from '@electron-toolkit/preload'
import {P2P_EVENTS, P2PConfig, P2PMessage, PeerInfo} from "../types/p2p";
import {AI_IPC_CHANNELS} from "../types/ai"

// Custom APIs for renderer
const p2pAPI = {
  startDiscovery: (config: P2PConfig) => {
    // 1. 打印参数和事件名，确认没传错
    console.log('[Preload Debug] Calling startDiscovery')
    console.log('[Preload Debug] Event Name:', P2P_EVENTS.START_DISCOVERY)
    console.log('[Preload Debug] Payload:', config)

    try {
      // 2. 执行发送
      ipcRenderer.send(P2P_EVENTS.START_DISCOVERY, config)
      console.log('[Preload Debug] ipcRenderer.send executed')
    } catch (e) {
      // 3. 捕获任何可能的 IPC 错误
      console.error('[Preload Debug] ipcRenderer.send CRASHED:', e)
    }
  },
  stopDiscovery: () => ipcRenderer.send(P2P_EVENTS.STOP_DISCOVERY),

  onPeerFound: (callback: (peer: PeerInfo) => void) => {
    const subscription = (_event: any, peer: PeerInfo) => callback(peer)
    ipcRenderer.on(P2P_EVENTS.PEER_FOUND, subscription)
    return () => ipcRenderer.removeListener(P2P_EVENTS.PEER_FOUND, subscription)
  },

  onPeerLost: (callback: (peerId: string) => void) => {
    const subscription = (_event: any, id: string) => callback(id)
    ipcRenderer.on(P2P_EVENTS.PEER_LOST, subscription)
    return () => ipcRenderer.removeListener(P2P_EVENTS.PEER_LOST, subscription)
  },

  connectPeer: (peerId: string, ip: string, port: number) =>
    ipcRenderer.send(P2P_EVENTS.CONNECT_PEER, {peerId, ip, port}),

  sendMessage: (targetId: string, text: string) =>
    ipcRenderer.send(P2P_EVENTS.SEND_MESSAGE, {targetId, text}),

  onMessageReceived: (callback: (msg: P2PMessage) => void) => {
    const sub = (_e: any, msg: P2PMessage) => callback(msg)
    ipcRenderer.on(P2P_EVENTS.MESSAGE_RECEIVED, sub)
    return () => ipcRenderer.removeListener(P2P_EVENTS.MESSAGE_RECEIVED, sub)
  },

  onConnectionStatus: (callback: (status: { userId: string, status: string }) => void) => {
    const sub = (_e: any, val: any) => callback(val)
    ipcRenderer.on(P2P_EVENTS.CONNECTION_STATUS, sub)
    return () => ipcRenderer.removeListener(P2P_EVENTS.CONNECTION_STATUS, sub)
  },

  onError: (callback: (error: any) => void) => {
    const subscription = (_event: any, err: any) => callback(err)
    ipcRenderer.on(P2P_EVENTS.ERROR, subscription)
    return () => ipcRenderer.removeListener(P2P_EVENTS.ERROR, subscription)
  },

  setSharedDirectory: () => ipcRenderer.invoke(P2P_EVENTS.SET_SHARE_DIR),

  // 使用 send，结果通过 message received 异步返回
  startSearch: (query: string) => ipcRenderer.send(P2P_EVENTS.START_SEARCH, query),

  // 使用 send 请求下载
  downloadFile: (targetPeerId: string, fileId: string) =>
    ipcRenderer.send(P2P_EVENTS.DOWNLOAD_FILE, {targetPeerId, fileId}),

  // 监听下载进度
  onDownloadProgress: (callback: (data: any) => void) => {
    const sub = (_e: any, data: any) => callback(data)
    ipcRenderer.on(P2P_EVENTS.DOWNLOAD_PROGRESS, sub)
    return () => ipcRenderer.removeListener(P2P_EVENTS.DOWNLOAD_PROGRESS, sub)
  }
}

const aiAPI = {
  getModels: () => ipcRenderer.invoke(AI_IPC_CHANNELS.GET_MODELS),
  downloadModel: (modelId: string) => ipcRenderer.invoke(AI_IPC_CHANNELS.DOWNLOAD_MODEL, modelId),
  cancelDownload: () => ipcRenderer.invoke(AI_IPC_CHANNELS.CANCEL_DOWNLOAD),
  onDownloadProgress: (callback: (data: any) => void) => {
    const subscription = (_event: any, data: any) => callback(data)
    ipcRenderer.on(AI_IPC_CHANNELS.ON_DOWNLOAD_PROGRESS, subscription)
    return () => {
      ipcRenderer.removeListener(AI_IPC_CHANNELS.ON_DOWNLOAD_PROGRESS, subscription)
    }
  },
  initSession: (modelId?: string) => ipcRenderer.invoke(AI_IPC_CHANNELS.INIT_SESSION, modelId),
  chat: (message: string) => ipcRenderer.invoke(AI_IPC_CHANNELS.CHAT_STREAM, message),
  resetSession: () => ipcRenderer.invoke(AI_IPC_CHANNELS.RESET_SESSION),
  onChatReply: (callback: (chunk: string) => void) => {
    const subscription = (_event: any, chunk: string) => callback(chunk)
    ipcRenderer.on(AI_IPC_CHANNELS.CHAT_REPLY_CHUNK, subscription)
    return () => {
      ipcRenderer.removeListener(AI_IPC_CHANNELS.CHAT_REPLY_CHUNK, subscription)
    }
  },
  onRendererAction: (callback: (payload: { action: string, args: any }) => void) => {
    const subscription = (_event: any, payload: any) => callback(payload)
    ipcRenderer.on(AI_IPC_CHANNELS.EXECUTE_RENDERER_ACTION, subscription)
    return () => {
      ipcRenderer.removeListener(AI_IPC_CHANNELS.EXECUTE_RENDERER_ACTION, subscription)
    }
  },
}

const layoutAPI = {
  minimize: () => ipcRenderer.send('window-minimize'),
  maximize: () => ipcRenderer.send('window-maximize'),
  close: () => ipcRenderer.send('window-close'),
  isMaximized: () => ipcRenderer.invoke('window-is-maximized'),
  onWindowStateChange: (callback: (state: 'maximized' | 'normal') => void) => {
    const subscription = (_event: any, state: string) => callback(state as 'maximized' | 'normal')
    ipcRenderer.on('window-state-change', subscription)
    return () => ipcRenderer.removeListener('window-state-change', subscription)
  }
}


// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('layout', layoutAPI)
    contextBridge.exposeInMainWorld('p2p', p2pAPI)
    contextBridge.exposeInMainWorld('ai', aiAPI)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.p2p = p2pAPI
  // @ts-ignore (define in dts)
  window.ai = aiAPI
  // @ts-ignore
  window.layout = layoutAPI
}
