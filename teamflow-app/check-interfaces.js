const os = require('os');

const interfaces = os.networkInterfaces();
console.log('=== 系统网络接口列表 ===');

for (const name of Object.keys(interfaces)) {
  for (const iface of interfaces[name]) {
    // 这是一个简化过滤，只看 IPv4 且非内部回环
    if (iface.family === 'IPv4' && !iface.internal) {
      console.log(`[${name}]`);
      console.log(`  IP:   ${iface.address}`);
      console.log(`  Mac:  ${iface.mac}`);
      console.log(`  Mask: ${iface.netmask}`);
      console.log('-------------------------');
    }
  }
}
