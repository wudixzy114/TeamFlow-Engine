// debug-mdns.js
// 使用最底层的 multicast-dns 库进行测试，绕过所有封装
const mdns = require('multicast-dns')()

const MY_ID = 'Debugger-' + Math.floor(Math.random() * 1000)

console.log(`🚀 [${MY_ID}] 开始监听 mDNS 数据包...`)

mdns.on('response', function (response) {
  // 只要收到任何 mDNS 响应，说明组播通道是通的
  console.log(`📩 [${MY_ID}] 收到来自 ${response.answers[0]?.name} 的响应`)
})

mdns.on('query', function (query) {
  // 收到查询请求
  console.log(`🔍 [${MY_ID}] 收到查询请求: ${query.questions[0]?.name}`)

  // 礼貌性回复一下
  if (query.questions[0] && query.questions[0].name === '_test-p2p._tcp.local') {
    mdns.respond({
      answers: [{
        name: '_test-p2p._tcp.local',
        type: 'TXT',
        data: 'Hello from ' + MY_ID
      }]
    })
  }
})

// 每 3 秒广播一次查询
setInterval(() => {
  console.log(`📡 [${MY_ID}] 发送查询广播...`)
  mdns.query({
    questions: [{
      name: '_test-p2p._tcp.local',
      type: 'TXT'
    }]
  })
}, 3000)
