import {P2PConfig, PeerInfo} from './p2p'
import {P2PMessage} from "../types/p2p";
import {ElectronAPI} from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI; // 或者引入 ElectronAPI 类型

    // P2P 模块接口
    p2p: {
      startDiscovery: (config: P2PConfig) => void;
      stopDiscovery: () => void;
      connectPeer: (peerId: string, ip: string, port: number) => void;
      sendMessage: (targetId: string, text: string) => void;

      // 监听器返回 unsubscribe 函数
      onPeerFound: (callback: (peer: PeerInfo) => void) => () => void;
      onPeerLost: (callback: (peerId: string) => void) => () => void;
      onMessageReceived: (callback: (msg: P2PMessage) => void) => () => void;
      onConnectionStatus: (callback: (status: { userId: string, status: string }) => void) => () => void;
      onError: (callback: (error: any) => void) => () => void;
      onDownloadProgress: (callback: (data: {
        fileId: string,
        progress: number,
        fileName: string,
        completedPath?: string
      }) => void) => () => void;

      setSharedDirectory: () => Promise<{ dir: string; count: number } | null>;
      startSearch: (query: string) => void;
      downloadFile: (targetPeerId: string, fileId: string) => void;
    };
    ai: {
      getModels: () => Promise<any[]>;
      downloadModel: (modelId: string) => Promise<void>;
      cancelDownload: () => Promise<void>;
      onDownloadProgress: (callback: (data: any) => void) => () => void;

      initSession: (modelId?: string) => Promise<{ status: string; modelName?: string; error?: string }>;
      chat: (message: string) => Promise<{ status: string; fullResponse?: string; error?: string }>;
      resetSession: () => Promise<{ status: string }>;
      onChatReply: (callback: (chunk: string) => void) => () => void;
      onRendererAction: (callback: (payload: { action: string, args: any }) => void) => () => void;
    };
    clock: {
      setProgressBar: (value: number) => void; // value: 0 - 1
      sendNotification: (title: string, body: string) => void;
    };
    layout: {
      minimize: () => void
      maximize: () => void
      close: () => void
      isMaximized: () => Promise<boolean>
      onWindowStateChange: (callback: (state: 'maximized' | 'normal') => void) => () => void
    }
  }
}



