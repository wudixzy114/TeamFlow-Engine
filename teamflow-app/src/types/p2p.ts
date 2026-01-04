export interface PeerInfo {
  id: string;
  username: string;
  ip: string;
  port: number;
  status?: string;
  avatar?: string;
  os?: string;
  lastSeen?: number;
}

export interface P2PConfig {
  username: string;
  userId: string;
}

export enum MessageType {
  CHAT = 'chat',
  SEARCH_REQUEST = 'search_req',
  SEARCH_RESPONSE = 'search_res',
  FILE_REQUEST = 'file_req',
  FILE_CHUNK = 'file_chunk',
  FILE_ERROR = 'file_error'
}

export interface P2PMessage {
  id: string;
  senderId: string;
  type: MessageType;
  payload: any;
  timestamp: number;
}

export enum P2P_EVENTS {
  START_DISCOVERY = 'p2p:start-discovery',
  STOP_DISCOVERY = 'p2p:stop-discovery',
  PEER_FOUND = 'p2p:peer-found',
  PEER_LOST = 'p2p:peer-lost',
  ERROR = 'p2p:error',

  CONNECT_PEER = 'p2p:connect-peer', // 前端请求连接某人
  SEND_MESSAGE = 'p2p:send-message', // 前端发送消息
  MESSAGE_RECEIVED = 'p2p:message-received', // 收到消息通知前端
  CONNECTION_STATUS = 'p2p:connection-status', // 连接状态变更

  SET_SHARE_DIR = 'p2p:set-share-dir', // 设置共享目录
  START_SEARCH = 'p2p:start-search',   // 发起搜索
  SEARCH_RESULT = 'p2p:search-result', // 收到搜索结果
  DOWNLOAD_FILE = 'p2p:download-file', // 请求下载
  DOWNLOAD_PROGRESS = 'p2p:download-progress' // 下载进度
}

export interface SharedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  lastModified: number;
  ownerId?: string;
}

export interface SearchRequestPayload {
  query: string;
  requestId: string;
}

export interface SearchResponsePayload {
  requestId: string;
  results: SharedFile[];
}

export interface FileRequestPayload {
  fileId: string
}

export interface FileChunkPayload {
  fileId: string;
  chunkIndex: number;
  totalChunks: number;
  data: ArrayBuffer; // 二进制数据
  fileName: string;
}


