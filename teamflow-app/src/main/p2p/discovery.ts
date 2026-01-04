import mDNS from 'multicast-dns'
import {BrowserWindow} from 'electron'
import {P2P_EVENTS, PeerInfo} from '../../types/p2p'
import {getLocalIP} from '../utils/network'

const SERVICE_ID = '_teamflow-engine._tcp.local'

export class ServiceDiscovery {
  private mdns: any
  private mainWindow: BrowserWindow
  private selfInfo: PeerInfo | null = null
  private knownPeers: Map<string, PeerInfo> = new Map()
  private destroyHook: (() => void) | null = null

  constructor(mainWindow: BrowserWindow) {
    this.mainWindow = mainWindow
  }

  public start(username: string, userId: string, port: number): void {
    const localIp = getLocalIP()

    if (!localIp) {
      console.error('[P2P Discovery] Failed to find a valid LAN IP')
      return
    }

    this.selfInfo = {
      id: userId,
      username,
      ip: localIp,
      port,
      status: 'online',
      os: process.platform
    }

    console.log(`[P2P Discovery] Starting mDNS on ${localIp}`)

    // 初始化 mDNS 实例
    this.mdns = mDNS({
      multicast: true,
      interface: localIp,
      port: 5353,
      ip: '224.0.0.251',
      reuseAddr: true,
      loopback: true
    })

    // 1. 监听收到的数据包
    this.mdns.on('response', (packet: any) => this.handleResponse(packet))
    this.mdns.on('query', (packet: any) => this.handleQuery(packet))

    // 2. 主动广播自己 (Advertise)
    this.broadcastPresence()

    // 3. 搜索别人 (Query)
    this.queryPeers()

    let burstCount = 0
    const burstInterval = setInterval(() => {
      if (burstCount >= 4) {
        clearInterval(burstInterval)
        return
      }
      console.log('[P2P Discovery] Burst broadcasting...')
      this.broadcastPresence()
      this.queryPeers() // 同时也询问一下网络
      burstCount++
    }, 1000)

    // 定时广播 (心跳机制，每 30 秒广播一次，防止被遗忘)
    const interval = setInterval(() => {
      this.queryPeers() // 同时也询问一下网络
      this.broadcastPresence()
    }, 30000)

    this.destroyHook = () => {
      clearInterval(interval)
      // 发送 Bye 包 (TTL=0) 逻辑太复杂暂略，直接依赖 Socket 断连检测
      this.mdns.destroy()
    }
  }

  public stop(): void {
    if (this.destroyHook) {
      this.destroyHook()
      this.destroyHook = null
    }
    this.knownPeers.clear()
    this.selfInfo = null
  }

  /**
   * 处理别人的查询请求
   * 如果有人问 "_teamflow-engine"，我就回复我的信息
   */
  private handleQuery(packet: any) {
    const questions = packet.questions || []
    const isAskingForUs = questions.some((q: any) => q.name === SERVICE_ID)

    if (isAskingForUs && this.selfInfo) {
      this.broadcastPresence()
    }
  }

  /**
   * 处理别人的响应 (发现节点)
   */
  private handleResponse(packet: any) {
    if (!this.selfInfo) return

    // 1. 检查是否包含我们的服务标识
    const ptrRecord = packet.answers.find((a: any) => a.name === SERVICE_ID && a.type === 'PTR')
    if (!ptrRecord) return

    // 这里的 ptrRecord.data 是服务的实例全名，例如: "Alice._teamflow-engine._tcp.local"
    const instanceName = ptrRecord.data

    // 2. 解析关联记录 (SRV, TXT, A)
    // 注意：mDNS 包可能把这些放在 answers 或 additionals 里
    const allRecords = [...(packet.answers || []), ...(packet.additionals || [])]

    const srv = allRecords.find((r: any) => r.name === instanceName && r.type === 'SRV')
    const txt = allRecords.find((r: any) => r.name === instanceName && r.type === 'TXT')
    const a = allRecords.find((r: any) => r.type === 'A' && (r.name === instanceName || r.name === srv?.data?.target))

    if (!srv || !txt || !a) return

    // 3. 提取数据
    // TXT data 可能是 Buffer 数组或对象，multicast-dns 默认解析为 buffer 数组，需要转换
    const txtData = this.parseTxtRecord(txt.data)

    // 如果是自己，忽略
    if (txtData.id === this.selfInfo.id) return

    // 构造 PeerInfo
    const peer: PeerInfo = {
      id: txtData.id,
      username: txtData.username,
      ip: a.data, // 这里就是对方强制指定的 IP，不再是 VPN IP
      port: srv.data.port,
      os: txtData.os,
      lastSeen: Date.now()
    }

    // 4. 更新
    if (!this.knownPeers.has(peer.id) || this.hasInfoChanged(this.knownPeers.get(peer.id)!, peer)) {
      this.knownPeers.set(peer.id, peer)
      console.log(`[P2P Discovery] Discovered: ${peer.username} at ${peer.ip}:${peer.port}`)
      this.mainWindow.webContents.send(P2P_EVENTS.PEER_FOUND, peer)
    }
  }

  /**
   * 发送广播包
   */
  private broadcastPresence() {
    if (!this.selfInfo) return

    const instanceName = `${this.selfInfo.username}.${SERVICE_ID}`
    const hostName = `${this.selfInfo.id}.local` // 虚拟主机名

    this.mdns.respond({
      answers: [
        {
          name: SERVICE_ID,
          type: 'PTR',
          data: instanceName,
          ttl: 120
        },
        {
          name: instanceName,
          type: 'SRV',
          data: {
            port: this.selfInfo.port,
            weight: 0,
            priority: 10,
            target: hostName
          },
          ttl: 120
        },
        {
          name: instanceName,
          type: 'TXT',
          data: [
            `id=${this.selfInfo.id}`,
            `username=${this.selfInfo.username}`,
            `os=${this.selfInfo.os || 'unknown'}`
          ],
          ttl: 120
        },
        {
          name: hostName,
          type: 'A',
          ttl: 120,
          data: this.selfInfo.ip // <--- 关键：强制写入我们筛选出的 IP
        }
      ]
    })
  }

  /**
   * 发送查询请求
   */
  private queryPeers() {
    this.mdns.query({
      questions: [{
        name: SERVICE_ID,
        type: 'PTR'
      }]
    })
  }

  /**
   * 辅助：解析 TXT 记录 (Buffer[] -> Object)
   */
  private parseTxtRecord(data: any): any {
    const result: any = {}
    if (Array.isArray(data)) {
      data.forEach((buf: Buffer) => {
        const str = buf.toString()
        const [key, value] = str.split('=')
        if (key && value) {
          result[key] = value
        }
      })
    }
    return result
  }

  private hasInfoChanged(oldPeer: PeerInfo, newPeer: PeerInfo): boolean {
    return oldPeer.ip !== newPeer.ip || oldPeer.port !== newPeer.port
  }
}
