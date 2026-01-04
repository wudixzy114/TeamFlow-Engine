import {Server as SocketServer, Socket as ServerSocket} from 'socket.io'
import {io as ClientIO, Socket as ClientSocket} from 'socket.io-client'
import {createServer, Server as HttpServer} from 'http'
import {BrowserWindow} from "electron";
import {P2P_EVENTS, P2PMessage, MessageType, FileChunkPayload} from "../../types/p2p";
import {v4 as uuidv4} from 'uuid';
import fs from 'fs-extra'
import path from "path";
import EventEmitter from "events";

const CHUNK_SIZE = 1024 * 64

export class P2PTransport extends EventEmitter {
  private ioServer: SocketServer | null = null;
  private httpServer: HttpServer | null = null;
  private outgoingConnections: Map<string, ClientSocket> = new Map();
  private incomingConnections: Map<string, ServerSocket> = new Map();

  private mainWindow: BrowserWindow;
  private selfId: string = ''

  constructor(mainWindow: BrowserWindow) {
    super()
    this.mainWindow = mainWindow;
  }

  public getSelfId(): string {
    return this.selfId
  }

  public async startServer(userId: string): Promise<number> {
    this.selfId = userId

    this.httpServer = createServer()
    this.ioServer = new SocketServer(this.httpServer, {
      cors: {origin: '*'},
      serveClient: false,
      maxHttpBufferSize: 1e8
    })

    this.ioServer.on('connection', (socket: ServerSocket) => {
      this.handleIncomingConnection(socket)
    })

    return new Promise((resolve, reject) => {
      this.httpServer?.listen(0, () => {
        const addr = this.httpServer?.address();
        if (addr && typeof addr !== 'string') {
          console.log(`[P2P Transport] Server listening on port ${addr.port}`)
          resolve(addr.port)
        } else {
          reject(new Error('Failed to get server port'))
        }
      })
    })
  }

  public connectToPeer(peerId: string, ip: string, port: number) {
    if (this.outgoingConnections.has(peerId)) {
      console.log(`[P2P Transport] Already connected to ${peerId}`)
      return
    }

    const url = `http://${ip}:${port}`
    console.log(`[P2P Transport] Connecting to ${url}...`)

    const socket = ClientIO(url, {
      auth: {userId: this.selfId},
      reconnection: false
    })

    socket.on('connect', () => {
      console.log(`[P2P Transport] Connected to outgoing peer: ${peerId}`)
      this.outgoingConnections.set(peerId, socket)
      this.notifyConnectionStatus(peerId, 'connected')
    })

    socket.on('message', (message: P2PMessage) => {
      // 理论上客户端主要发消息，但也可能收到服务端的回复
      this.handleMessageReceived(message)
    })

    socket.on('connect_error', (err) => {
      console.error(`[P2P Transport] Connection error to ${peerId}:`, err.message)
      this.notifyConnectionStatus(peerId, 'error')
    })

    socket.on('disconnect', () => {
      this.outgoingConnections.delete(peerId)
      this.notifyConnectionStatus(peerId, 'disconnected')
    })
  }

  public sendMessage(targetUserId: string, type: MessageType, payload: any) {
    const message: P2PMessage = {
      id: uuidv4(),
      senderId: this.selfId,
      type,
      payload,
      timestamp: Date.now()
    }

    let socket = this.outgoingConnections.get(targetUserId);
    if (!socket) {
      // @ts-ignore - ServerSocket 和 ClientSocket 都有 emit 方法，这里简化处理
      socket = this.incomingConnections.get(targetUserId);
    }

    if (socket) {
      socket.emit('message', message)
      console.log(`[P2P Transport] Sent message to ${targetUserId}`)
    } else {
      console.warn(`[P2P Transport] Cannot send message: No connection to ${targetUserId}`)
    }
  }

  public stop() {
    this.ioServer?.close()
    this.httpServer?.close()
    this.outgoingConnections.forEach(s => s.disconnect())
    this.outgoingConnections.clear()
    this.incomingConnections.clear()
    this.removeAllListeners()
  }

  public broadcastMessage(type: MessageType, payload: any) {
    this.outgoingConnections.forEach((socket, _peerId) => {
      const message: P2PMessage = {
        id: uuidv4(),
        senderId: this.selfId,
        type,
        payload,
        timestamp: Date.now()
      }
      socket.emit('message', message)
    })

    this.incomingConnections.forEach((socket, peerId) => {
      if (!this.outgoingConnections.has(peerId)) {
        const message: P2PMessage = {
          id: uuidv4(),
          senderId: this.selfId,
          type,
          payload,
          timestamp: Date.now()
        }
        socket.emit('message', message)
      }
    })

    console.log(`[P2P Transport] Broadcast ${type} to network.`)
  }

  public async sendFile(targetPeerId: string, filePath: string, fileId: string) {
    let socket = this.outgoingConnections.get(targetPeerId) || this.incomingConnections.get(targetPeerId)
    if (!socket) {
      console.warn(`[P2P File] Cannot send file, peer ${targetPeerId} not connected.`)
      return
    }

    try {
      const stats = await fs.stat(filePath)
      const totalChunks = Math.ceil(stats.size / CHUNK_SIZE)
      const fileName = path.basename(filePath)

      const stream = fs.createReadStream(filePath, {highWaterMark: CHUNK_SIZE})
      let chunkIndex = 0;
      for await (const chunk of stream) {
        const payload: FileChunkPayload = {
          fileId,
          chunkIndex,
          totalChunks,
          data: chunk, // Socket.io 会自动处理 Buffer
          fileName
        }

        const message: P2PMessage = {
          id: uuidv4(),
          senderId: this.selfId,
          type: MessageType.FILE_CHUNK,
          payload,
          timestamp: Date.now()
        }

        socket.emit('message', message)
        chunkIndex++

        if (chunkIndex % 100 === 0) {
          await new Promise(r => setTimeout(r, 10))
        }
      }

      console.log(`[P2P File] Transfer complete: ${fileName}`)
    } catch (e) {
      console.error('[P2P File] Transfer failed:', e)
    }
  }

  private handleIncomingConnection(socket: ServerSocket) {
    const remoteUserId: string | null = socket.handshake.auth.userId;
    if (!remoteUserId) {
      console.warn('[P2P Transport] Incoming connection rejected: No UserID')
      socket.disconnect()
      return
    }

    console.log(`[P2P Transport] Incoming connection from: ${remoteUserId}`)
    this.incomingConnections.set(remoteUserId, socket)

    socket.on('message', (message: P2PMessage) => {
      this.handleMessageReceived(message)
    })

    socket.on('disconnect', () => {
      console.log(`[P2P Transport] Peer disconnected: ${remoteUserId}`)
      this.incomingConnections.delete(remoteUserId)
      this.notifyConnectionStatus(remoteUserId, 'disconnected')
    })

    this.notifyConnectionStatus(remoteUserId, 'connected')
  }

  private handleMessageReceived(message: P2PMessage) {
    console.log(`[P2P Transport] Received ${message.type} from ${message.senderId}`)
    this.emit('message', message)
  }

  private notifyConnectionStatus(userId: string, status: string) {
    this.mainWindow.webContents.send(P2P_EVENTS.CONNECTION_STATUS, {userId, status})
  }
}
