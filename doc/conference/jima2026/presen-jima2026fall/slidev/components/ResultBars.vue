<script setup lang="ts">
// 実データ結果：MAE と 残差Top10 MAE（値が小さいほど良い）
withDefaults(defineProps<{ stage?: number }>(), { stage: 2 })
const methods = [
  { n: '基準値のみ', c: '#9a9a9a' },
  { n: '中心化なし', c: '#eb6834' },
  { n: '提案（中心化あり）', c: '#6250d6' },
]
const panels = [
  { title: 'MAE', vals: [0.06966, 0.05422, 0.04828], max: 0.1, fmt: (v: number) => v.toFixed(5) },
  { title: '残差 Top10 MAE', vals: [0.27883, 0.23057, 0.19418], max: 0.42, fmt: (v: number) => v.toFixed(3) },
]
const pct = (a: number, b: number) => `−${Math.round((1 - b / a) * 100)}%`
const W = 300, Hh = 230, mL = 10, mB = 34, mT = 30
const bw = 56, gapx = 34
const x = (i: number) => mL + 30 + i * (bw + gapx)
const y = (v: number, max: number) => mT + (Hh - mT - mB) * (1 - v / max)
</script>

<template>
  <div class="rb">
    <div v-for="(p, pi) in panels" :key="p.title" class="panel" :class="{ off: stage < pi }">
      <svg :viewBox="`0 0 ${W} ${Hh}`" :width="W" :height="Hh">
        <text :x="W / 2" y="16" text-anchor="middle" class="ttl">{{ p.title }}（小さいほど良い）</text>
        <line :x1="mL + 10" :x2="W - 10" :y1="Hh - mB" :y2="Hh - mB" stroke="#b8b8b2" />
        <g v-for="(v, i) in p.vals" :key="i">
          <rect :x="x(i)" :y="y(v, p.max)" :width="bw" :height="Hh - mB - y(v, p.max)" :fill="methods[i].c" rx="3" />
          <text :x="x(i) + bw / 2" :y="y(v, p.max) - 6" text-anchor="middle" class="val">{{ p.fmt(v) }}</text>
          <text :x="x(i) + bw / 2" :y="Hh - mB + 14" text-anchor="middle" class="lab">{{ methods[i].n.replace('（', '\n（').split('\n')[0] }}</text>
          <text v-if="i === 2" :x="x(i) + bw / 2" :y="Hh - mB + 27" text-anchor="middle" class="lab">（中心化あり）</text>
        </g>
        <!-- 改善率の注釈 -->
        <g v-if="stage >= 2" class="fade">
          <path :d="`M${x(0) + bw / 2},${y(p.vals[0], p.max) - 20} C${x(0) + bw / 2},${y(p.vals[0], p.max) - 42} ${x(2) + bw / 2},${y(p.vals[0], p.max) - 42} ${x(2) + bw / 2},${y(p.vals[2], p.max) - 20}`" fill="none" stroke="#b4231f" stroke-width="1.5" />
          <rect :x="(x(0) + x(2) + bw) / 2 - 24" :y="y(p.vals[0], p.max) - 44" width="48" height="16" rx="8" fill="#b4231f" />
          <text :x="(x(0) + x(2) + bw) / 2" :y="y(p.vals[0], p.max) - 32" text-anchor="middle" class="pct">{{ pct(p.vals[0], p.vals[2]) }}</text>
          <rect :x="(x(1) + x(2) + bw) / 2 - 22" :y="y(p.vals[1], p.max) - 32" width="44" height="16" rx="8" fill="#fff" stroke="#b4231f" />
          <text :x="(x(1) + x(2) + bw) / 2" :y="y(p.vals[1], p.max) - 20" text-anchor="middle" class="pct2">{{ pct(p.vals[1], p.vals[2]) }}</text>
        </g>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.rb { display: flex; justify-content: center; gap: 24px; }
.panel { transition: opacity .4s; }
.panel.off { opacity: 0.1; }
.ttl { font-size: 13px; font-weight: 700; fill: #0b0b0b; }
.val { font-size: 12px; font-weight: 700; fill: #0b0b0b; }
.lab { font-size: 11px; fill: #52514e; }
.pct { font-size: 11px; font-weight: 700; fill: #fff; }
.pct2 { font-size: 11px; font-weight: 700; fill: #b4231f; }
.fade { animation: fin .4s ease; }
@keyframes fin { from { opacity: 0 } to { opacity: 1 } }
</style>
