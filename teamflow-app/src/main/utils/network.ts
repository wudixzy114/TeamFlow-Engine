import os from 'os';

export function getLocalIP(): string {
  const interfaces = os.networkInterfaces()
  let fallbackIP = '127.0.0.1'

  for (const name of Object.keys(interfaces)) {
    const lowerName = name.toLowerCase()

    // --- 黑名单过滤 (关键！) ---
    // 遇到这些名字，直接跳过，看都不要看
    if (
      lowerName.includes('radmin') ||
      lowerName.includes('vpn') ||
      lowerName.includes('tun') ||
      lowerName.includes('tap') ||
      lowerName.includes('vmware') ||
      lowerName.includes('virtual') ||
      lowerName.includes('wsl')
    ) {
      continue
    }

    const ifaceList = interfaces[name] || []

    for (const iface of ifaceList) {
      // 只看 IPv4 且非回环
      if (iface.family === 'IPv4' && !iface.internal) {

        // --- 白名单优先 ---
        // 如果名字里带有 WLAN 或 Wi-Fi 或 Ethernet，直接选中返回
        // 你的网卡名叫 "WLAN"，这里会命中
        if (
          lowerName.includes('wlan') ||
          lowerName.includes('wi-fi') ||
          lowerName.includes('ethernet') ||
          lowerName.includes('en') || // Mac/Linux 常见
          lowerName.includes('eth')   // Linux 常见
        ) {
          return iface.address
        }

        // 如果没命中白名单，但也没在黑名单，先存着作为备选
        fallbackIP = iface.address
      }
    }
  }

  console.log(`[Network Debug] Selected IP: ${fallbackIP}`)
  return fallbackIP
}
