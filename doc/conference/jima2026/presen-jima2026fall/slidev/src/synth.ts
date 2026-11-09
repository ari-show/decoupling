// 発表用の疑似データ（決定的）。残差 r = g + a[d] + t[h] + u[d][h]
export const D = 28
export const H = 24

function mulberry32(seed: number) {
  let a = seed
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
const rnd = mulberry32(20261024)
const mean = (xs: number[]) => xs.reduce((s, x) => s + x, 0) / xs.length

// 全期間成分
export const g = 0.25

// 日成分（週周期 + ゆらぎ、平均0）
const a0 = Array.from({ length: D }, (_, d) => 0.55 * Math.sin((2 * Math.PI * d) / 7 - 1.2) + (rnd() - 0.5) * 0.5)
const aMean = mean(a0)
export const a = a0.map(v => v - aMean)

// 時間帯成分（朝・夕の二山、深夜は負、平均0）
const t0 = Array.from({ length: H }, (_, h) => {
  const p1 = Math.exp(-((h - 9) ** 2) / 6)
  const p2 = Math.exp(-((h - 17) ** 2) / 8)
  const night = h < 6 || h > 21 ? -0.55 : -0.15
  return 1.1 * p1 + 0.95 * p2 + night
})
const tMean = mean(t0)
export const t = t0.map(v => v - tMean)

// 交互作用成分（弱いノイズ + 数個のスパイク、行・列ともに平均0）
const u0 = Array.from({ length: D }, () => Array.from({ length: H }, () => (rnd() - 0.5) * 0.25))
const spikes: [number, number, number][] = [
  [3, 18, 1.0], [9, 17, 1.1], [12, 8, -0.9], [16, 20, 0.9], [20, 10, -1.0], [24, 19, 1.0], [6, 12, -0.8],
]
for (const [d, h, v] of spikes) u0[d][h] += v
const rowM = u0.map(mean)
const colM = Array.from({ length: H }, (_, h) => mean(u0.map(row => row[h])))
const allM = mean(rowM)
export const u = u0.map((row, d) => row.map((v, h) => v - rowM[d] - colM[h] + allM))

export const r = (d: number, h: number) => g + a[d] + t[h] + u[d][h]

export type Mode = 'r' | 'g' | 'a' | 't' | 'u'
export function value(mode: Mode, d: number, h: number): number {
  switch (mode) {
    case 'g': return g
    case 'a': return a[d]
    case 't': return t[h]
    case 'u': return u[d][h]
    default: return r(d, h)
  }
}

// 発散カラー：負 = 青, 0 = ほぼ白, 正 = 赤
const POS = [227, 73, 72]
const NEG = [42, 120, 214]
const MID = [247, 247, 245]
export function diverging(v: number, scale = 1.2): string {
  const x = Math.max(-1, Math.min(1, v / scale))
  const to = x >= 0 ? POS : NEG
  const k = Math.abs(x)
  const c = MID.map((m, i) => Math.round(m + (to[i] - m) * k))
  return `rgb(${c[0]},${c[1]},${c[2]})`
}

// 成分カラー（a=橙, t=紫, u=緑, g=灰）
export const COMP = {
  g: '#6b6b6b',
  a: '#eb6834',
  t: '#6250d6',
  u: '#008300',
} as const
export const COMP_NAME = {
  g: '全期間成分',
  a: '日成分',
  t: '時間帯成分',
  u: '交互作用成分',
} as const
