import {defineStore} from 'pinia'
import {ref, computed} from 'vue'
import {useAuthStore} from './auth'
import {toast} from 'vue-sonner'
import {P2PMessage, SharedFile} from '../../../types/p2p'
import {v4 as uuidv4} from 'uuid'

// --- Types ---
export interface ExtendedPeer {
  id: string;
  username: string;
  ip: string;
  port: number;
  status: 'online' | 'offline' | 'connecting' | 'connected';
  isFavorite: boolean;
  lastSeen: number;
}

interface DownloadTask {
  fileId: string;
  fileName: string;
  progress: number;
  status: 'pending' | 'downloading' | 'completed' | 'error';
  path?: string;
}

export const useP2PStore = defineStore('p2p', () => {
  const authStore = useAuthStore();

  // --- State ---
  const isServiceRunning = ref(false);

  // 状态：当前使用的身份 ID（无论是登录还是 Guest）
  const currentIdentity = ref<{ id: string, username: string } | null>(null);

  const peers = ref<Map<string, ExtendedPeer>>(new Map());
  const chatHistory = ref<Map<string, P2PMessage[]>>(new Map());
  const activePeerId = ref<string | null>(null)

  const sharedDir = ref<string | null>(null)
  const sharedFileCount = ref(0)

  const searchQuery = ref('')
  const isSearching = ref(false)
  const searchResults = ref<SharedFile[]>([])

  const downloads = ref<Map<string, DownloadTask>>(new Map())

  let listeners: Function[] = []

  // --- Getters ---

  const sortedPeerList = computed(() => {
    // 防御性编程：如果因为某种原因 peers 不是 Map，回退到空数组，防止页面崩溃
    if (!peers.value || typeof peers.value.values !== 'function') {
      console.warn('Peers is not a Map, resetting...');
      return [];
    }

    const list = Array.from(peers.value.values());
    return list.sort((a, b) => {
      if (a.isFavorite !== b.isFavorite) return a.isFavorite ? -1 : 1;

      const getScore = (s: string) => {
        if (s === 'connected') return 3;
        if (s === 'connecting') return 2;
        if (s === 'online') return 1;
        return 0;
      }
      const scoreA = getScore(a.status);
      const scoreB = getScore(b.status);
      if (scoreA !== scoreB) return scoreB - scoreA;

      return (b.lastSeen || 0) - (a.lastSeen || 0);
    });
  });

  const activePeer = computed(() => activePeerId.value ? peers.value.get(activePeerId.value) : null)
  const currentChatMessages = computed(() =>
    activePeerId.value ? (chatHistory.value.get(activePeerId.value) || []) : [])
  const downloadList = computed(() => Array.from(downloads.value.values()))

  // --- Actions ---

  function toggleFavorite(peerId: string) {
    const peer = peers.value.get(peerId);
    if (peer) {
      peer.isFavorite = !peer.isFavorite;
      peers.value.set(peerId, {...peer});
    }
  }

  function removePeer(peerId: string) {
    if (peers.value.has(peerId)) {
      peers.value.delete(peerId);
      chatHistory.value.delete(peerId);
      if (activePeerId.value === peerId) activePeerId.value = null;
      toast.info('已移除该用户记录');
    }
  }

  function startP2PService() {
    console.log('Action startP2PService triggered')
    if (isServiceRunning.value) return;

    let userId: string;
    let username: string;

    // 优先使用已登录用户，否则读取/生成 Guest
    if (authStore.user) {
      userId = authStore.user.id;
      username = authStore.user.nickname || authStore.user.username;
    } else {
      userId = localStorage.getItem('guest_id') || uuidv4();
      username = localStorage.getItem('guest_name') || `Guest-${Math.floor(Math.random() * 1000)}`;
      localStorage.setItem('guest_id', userId);
      localStorage.setItem('guest_name', username);
    }

    // 保存当前身份到 State，供发送消息使用
    currentIdentity.value = {id: userId, username};

    // 重置所有节点状态为离线
    peers.value.forEach(p => {
      p.status = 'offline';
      peers.value.set(p.id, p);
    });

    window.p2p.startDiscovery({userId, username})
    registerListeners()
    isServiceRunning.value = true
  }

  function registerListeners() {
    const cleanFound = window.p2p.onPeerFound((rawPeer) => {
      const existing = peers.value.get(rawPeer.id);
      const newPeerData: ExtendedPeer = {
        ...rawPeer,
        status: existing?.status === 'connected' ? 'connected' : 'online',
        isFavorite: existing?.isFavorite || false,
        lastSeen: Date.now()
      };
      peers.value.set(rawPeer.id, newPeerData);

      if (!chatHistory.value.has(rawPeer.id)) {
        chatHistory.value.set(rawPeer.id, [])
      }
    });

    const cleanLost = window.p2p.onPeerLost((peerId) => {
      const peer = peers.value.get(peerId);
      if (peer) {
        peer.status = 'offline';
        peers.value.set(peerId, {...peer});
      }
    });

    const cleanMsg = window.p2p.onMessageReceived((msg) => {
      if (msg.type === 'chat') {
        const otherId = msg.senderId
        if (!chatHistory.value.has(otherId)) chatHistory.value.set(otherId, [])
        chatHistory.value.get(otherId)?.push(msg)
      } else if (msg.type === 'search_res') {
        const payload = msg.payload as { requestId: string, results: SharedFile[] }
        payload.results.forEach(file => {
          if (!searchResults.value.some(r => r.id === file.id)) {
            searchResults.value.push(file)
          }
        })
      }
    });

    const cleanStatus = window.p2p.onConnectionStatus(({userId, status}) => {
      const peer = peers.value.get(userId);
      if (peer) {
        if (status === 'disconnected') {
          peer.status = 'online';
        } else {
          peer.status = status as any;
        }
        peers.value.set(userId, {...peer});
      }
    });

    const cleanProgress = window.p2p.onDownloadProgress(({fileId, progress, fileName, completedPath}) => {
      const task = downloads.value.get(fileId) || {
        fileId, fileName, progress: 0, status: 'downloading'
      }
      task.progress = progress
      if (progress === 100) {
        task.status = 'completed'
        task.path = completedPath
        toast.success(`文件下载完成: ${fileName}`)
      }
      downloads.value.set(fileId, task)
    });

    listeners.push(cleanFound, cleanLost, cleanMsg, cleanStatus, cleanProgress)
  }

  async function setSharedDirectory() {
    try {
      const res = await window.p2p.setSharedDirectory()
      if (res) {
        sharedDir.value = res.dir
        sharedFileCount.value = res.count
        toast.success(`已索引 ${res.count} 个文件`)
      }
    } catch (e) {
      console.error(e)
      toast.error('设置共享目录失败')
    }
  }

  function performSearch() {
    if (!searchQuery.value.trim()) return
    isSearching.value = true
    searchResults.value = []
    window.p2p.startSearch(searchQuery.value)
    setTimeout(() => {
      isSearching.value = false
    }, 3000)
  }

  function downloadFile(file: SharedFile) {
    if (!file.ownerId) {
      toast.error('无法下载：未知拥有者')
      return
    }
    downloads.value.set(file.id, {
      fileId: file.id, fileName: file.name, progress: 0, status: 'pending'
    })
    window.p2p.downloadFile(file.ownerId, file.id)
    toast.info('开始下载...')
  }

  function connectToPeer(peerId: string) {
    const peer = peers.value.get(peerId)
    // 只有非离线状态才连接，避免无意义超时
    if (!peer || peer.status === 'offline') return;
    window.p2p.connectPeer(peer.id, peer.ip, peer.port)
  }

  function sendMessage(text: string) {
    if (!activePeerId.value) return

    // 安全检查：确保有发送者ID
    const senderId = authStore.user?.id || currentIdentity.value?.id;
    if (!senderId) {
      toast.error('身份验证失败，无法发送消息');
      return;
    }

    window.p2p.sendMessage(activePeerId.value, text)

    const myMsg: P2PMessage = {
      id: uuidv4(), // 使用 uuidv4 替代 crypto.randomUUID() 兼容性更好
      senderId: senderId,
      type: 'chat' as any,
      payload: text,
      timestamp: Date.now()
    }

    if (!chatHistory.value.has(activePeerId.value)) {
      chatHistory.value.set(activePeerId.value, [])
    }
    chatHistory.value.get(activePeerId.value)?.push(myMsg)
  }

  function selectPeer(peerId: string) {
    activePeerId.value = peerId
    const peer = peers.value.get(peerId);
    if (peer && peer.status === 'online') {
      connectToPeer(peerId)
    }
  }

  function stopP2PService() {
    window.p2p.stopDiscovery()
    listeners.forEach(fn => fn())
    listeners = []
    peers.value.clear()
    isServiceRunning.value = false
  }

  return {
    isServiceRunning,
    currentIdentity,
    peers,
    activePeerId,
    sharedDir,
    chatHistory,
    sortedPeerList,
    activePeer,
    currentChatMessages,
    downloadList,
    startP2PService,
    stopP2PService,
    selectPeer,
    connectToPeer,
    toggleFavorite,
    removePeer,
    setSharedDirectory,
    sendMessage,
    performSearch,
    downloadFile,
    searchQuery,
    isSearching,
    searchResults,
    sharedFileCount
  }
}, {
  persist: {

    pick: ['peers', 'sharedDir', 'chatHistory', 'currentIdentity', 'isServiceRunning'],
    storage: localStorage,
    // --- 关键修改：自定义序列化器 ---
    serializer: {
      serialize: (state) => {
        // 将 Map 转换为 Array 以便 JSON.stringify 存储
        const raw = {...state} as any;
        if (state.peers) raw.peers = Array.from(state.peers.entries());
        if (state.chatHistory) raw.chatHistory = Array.from(state.chatHistory.entries());
        return JSON.stringify(raw);
      },
      deserialize: (value) => {
        try {
          const raw = JSON.parse(value);

          // 1. 恢复 Map (之前的修复)
          if (Array.isArray(raw.peers)) {
            raw.peers = new Map(raw.peers);
          } else if (raw.peers && typeof raw.peers === 'object') {
            raw.peers = new Map(Object.entries(raw.peers));
          } else {
            raw.peers = new Map();
          }

          if (Array.isArray(raw.chatHistory)) {
            raw.chatHistory = new Map(raw.chatHistory);
          } else {
            raw.chatHistory = new Map();
          }

          raw.isServiceRunning = false;
          return raw;
        } catch (e) {
          console.error('State restore failed', e);
          return {
            peers: new Map(),
            chatHistory: new Map(),
            isServiceRunning: false // 失败兜底
          };
        }
      }
    },
    afterRestore: (ctx: any) => {
      if (ctx.store.peers instanceof Map) {
        ctx.store.peers.forEach((p: ExtendedPeer) => {
          p.status = 'offline';
        });
      }
    }
  }
})
