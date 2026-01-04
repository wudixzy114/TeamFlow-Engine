// src/utils/theme.ts
/**
 * 获取当前 CSS 变量对应的颜色值 (用于 Three.js)
 */
export function useThemeColors() {
  // 辅助：从 getComputedStyle 读取 RGB 格式 "r, g, b" 并转为 hex 或 color 对象
  const getColor = (varName: string) => {
    if (typeof window === 'undefined') return '#ffffff'
    const style = getComputedStyle(document.documentElement)
    const val = style.getPropertyValue(varName).trim()
    if (!val) return '#ffffff'
    return `rgb(${val})`
  }

  // 这里我们并不需要实时响应每一帧，通常主题切换会触发重新渲染或通过 watch 处理
  // 简单起见，我们返回一个获取函数
  return {
    getPrimary: () => getColor('--c-primary'),
    getSecondary: () => getColor('--c-secondary'),
    getBg: () => getColor('--c-bg-main'),
  }
}

/**
 * 生成斐波那契球体分布坐标 (均匀分布在球面上)
 */
export function getFibonacciSpherePoints(samples: number, radius: number) {
  const points: any = []
  const phi = Math.PI * (3 - Math.sqrt(5)) // 黄金角

  for (let i = 0; i < samples; i++) {
    const y = 1 - (i / (samples - 1)) * 2 // y goes from 1 to -1
    const radiusAtY = Math.sqrt(1 - y * y) // radius at y

    const theta = phi * i

    const x = Math.cos(theta) * radiusAtY
    const z = Math.sin(theta) * radiusAtY

    points.push([x * radius, y * radius, z * radius] as const)
  }
  return points
}
