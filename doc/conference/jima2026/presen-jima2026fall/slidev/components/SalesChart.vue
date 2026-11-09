<script setup lang="ts">
// 背景用：観測売上 → 基準値 → 残差の色付け を段階表示
import { computed } from 'vue'
import { a, t } from '../src/synth'

const props = withDefaults(defineProps<{
  kind?: 'hour' | 'day'
  stage?: number        // 0: 観測のみ, 1: +基準値, 2: +残差色付け, 3: +凡例
  width?: number
  height?: number
  title?: string
}>(), { kind: 'hour', stage: 0, width: 420, height: 230, title: '' })

const base = 10
const mL = 34, mR = 12, mT = 26, mB = 30
const pw = computed(() => props.width - mL - mR)
const ph = computed(() => props.height - mT - mB)

const hourVals = t.map((v, h) => base + 5.5 * v + 0.9 * Math.sin(h * 1.7))
const dayVals = a.slice(0, 14).map((v, d) => base + 4.2 * v + 0.7 * Math.cos(d * 2.3))

const vals = computed(() => (props.kind === 'hour' ? hourVals : dayVals))
const n = computed(() => vals.value.length)
const yMax = 20
const sx = (i: number) => mL + (props.kind === 'hour' ? (i / (n.value - 1)) * pw.value : ((i + 0.5) / n.value) * pw.value)
const sy = (v: number) => mT + ph.value * (1 - v / yMax)

// 折れ線
const linePath = computed(() => vals.value.map((v, i) => `${i ? 'L' : 'M'}${sx(i)},${sy(v)}`).join(' '))

// 基準値との間を符号で塗り分け（交点で分割）
const fills = computed(() => {
  const segs: { d: string; pos: boolean }[] = []
  const v = vals.value
  for (let i = 0; i < v.length - 1; i++) {
    const r0 = v[i] - base, r1 = v[i + 1] - base
    const x0 = sx(i), x1 = sx(i + 1)
    if (r0 * r1 >= 0) {
      segs.push({ pos: r0 + r1 >= 0, d: `M${x0},${sy(base)} L${x0},${sy(v[i])} L${x1},${sy(v[i + 1])} L${x1},${sy(base)} Z` })
    } else {
      const k = r0 / (r0 - r1)
      const xc = x0 + (x1 - x0) * k
      segs.push({ pos: r0 >= 0, d: `M${x0},${sy(base)} L${x0},${sy(v[i])} L${xc},${sy(base)} Z` })
      segs.push({ pos: r1 >= 0, d: `M${xc},${sy(base)} L${x1},${sy(v[i + 1])} L${x1},${sy(base)} Z` })
    }
  }
  return segs
})
const barW = computed(() => (pw.value / n.value) * 0.62)
const ticksX = computed(() => (props.kind === 'hour' ? [0, 6, 12, 18, 23] : [0, 3, 6, 9, 12]))
</script>

<template>
  <svg :width="width" :height="height" :viewBox="`0 0 ${width} ${height}`" class="sc">
    <text v-if="title" :x="mL" y="14" class="ttl">{{ title }}</text>
    <!-- 軸 -->
    <line :x1="mL" :x2="mL + pw" :y1="mT + ph" :y2="mT + ph" class="axis" />
    <line :x1="mL" :x2="mL" :y1="mT" :y2="mT + ph" class="axis" />
    <text v-for="k in ticksX" :key="k" :x="sx(k)" :y="mT + ph + 14" text-anchor="middle" class="tick">{{ kind === 'hour' ? k : k + 1 }}</text>
    <text :x="mL + pw / 2" :y="height - 4" text-anchor="middle" class="lab">{{ kind === 'hour' ? '時間帯' : '日付' }}</text>
    <text :x="10" :y="mT + ph / 2" text-anchor="middle" class="lab" :transform="`rotate(-90 10 ${mT + ph / 2})`">売上</text>

    <!-- 残差の塗り（stage>=2） -->
    <g v-if="stage >= 2 && kind === 'hour'" class="fade">
      <path v-for="(s, i) in fills" :key="i" :d="s.d" :fill="s.pos ? '#e34948' : '#2a78d6'" opacity="0.55" />
    </g>

    <!-- 日：棒 -->
    <g v-if="kind === 'day'">
      <template v-for="(v, i) in vals" :key="i">
        <template v-if="stage >= 2">
          <rect :x="sx(i) - barW / 2" :y="sy(Math.min(v, base))" :width="barW" :height="Math.abs(sy(v) - sy(base))" :fill="v >= base ? '#e34948' : '#2a78d6'" opacity="0.8" rx="2" />
          <rect :x="sx(i) - barW / 2" :y="sy(Math.min(v, base))" :width="barW" :height="sy(0) - sy(Math.min(v, base))" fill="#c9c9c4" opacity="0.6" rx="2" />
        </template>
        <rect v-else :x="sx(i) - barW / 2" :y="sy(v)" :width="barW" :height="sy(0) - sy(v)" fill="#9a9a9a" rx="2" />
      </template>
    </g>

    <!-- 時間帯：折れ線 -->
    <g v-if="kind === 'hour'">
      <path :d="linePath" fill="none" stroke="#2f2f2f" stroke-width="2.2" stroke-linejoin="round" />
      <circle v-for="(v, i) in vals" :key="i" :cx="sx(i)" :cy="sy(v)" r="2.6" fill="#2f2f2f" />
    </g>

    <!-- 基準値（stage>=1） -->
    <g v-if="stage >= 1" class="fade">
      <line :x1="mL" :x2="mL + pw" :y1="sy(base)" :y2="sy(base)" stroke="#444" stroke-width="2" stroke-dasharray="6 4" />
      <text :x="mL + pw" :y="sy(base) - 5" text-anchor="end" class="base">基準値</text>
    </g>

    <!-- 凡例（stage>=3） -->
    <g v-if="stage >= 3" class="fade" :transform="`translate(${mL + 6}, ${mT + 2})`">
      <rect width="11" height="11" fill="#e34948" opacity="0.7" rx="2" /><text x="15" y="10" class="tick">正の残差（基準値を上回る）</text>
      <rect y="16" width="11" height="11" fill="#2a78d6" opacity="0.7" rx="2" /><text x="15" y="26" class="tick">負の残差（基準値を下回る）</text>
    </g>
  </svg>
</template>

<style scoped>
.axis { stroke: #b8b8b2; stroke-width: 1; }
.tick { font-size: 10px; fill: #6b6b6b; }
.lab { font-size: 11px; fill: #52514e; }
.ttl { font-size: 13px; fill: #0b0b0b; font-weight: 600; }
.base { font-size: 11px; fill: #444; font-weight: 600; }
.fade { animation: fin .4s ease; }
@keyframes fin { from { opacity: 0 } to { opacity: 1 } }
</style>
