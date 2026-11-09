<script setup lang="ts">
// 従来研究（Tonekaboni et al., 2022）: 1本の時系列を窓に分け、Global / Local 表現を学習
withDefaults(defineProps<{ stage?: number; compact?: boolean }>(), { stage: 3, compact: false })
const W = 640, nWin = 5
const pts = Array.from({ length: 120 }, (_, i) => {
  const x = 40 + (i / 119) * (W - 60)
  const y = 70 - 22 * Math.sin(i / 6) - 10 * Math.sin(i / 2.3) + 6 * Math.cos(i / 13)
  return `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`
}).join(' ')
const winW = (W - 60) / nWin
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${compact ? 232 : 272}`" width="100%" class="glr">
    <defs><marker id="ga" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#52514e" /></marker></defs>
    <text x="40" y="24" class="t1">1本の時系列</text>
    <path :d="pts" fill="none" stroke="#2f2f2f" stroke-width="2" />
    <line x1="40" :x2="W - 20" y1="118" y2="118" stroke="#b8b8b2" />
    <!-- 窓 -->
    <g v-for="k in nWin" :key="k" :class="{ off: stage < 1 }">
      <rect :x="40 + (k - 1) * winW + 2" y="32" :width="winW - 4" height="86" fill="#eb6834" opacity="0.08" rx="3" />
      <line :x1="40 + (k - 1) * winW" :x2="40 + (k - 1) * winW" y1="30" y2="118" stroke="#eb6834" stroke-dasharray="4 3" />
      <text :x="40 + (k - 0.5) * winW" y="130" text-anchor="middle" class="t2">窓 {{ k }}</text>
    </g>
    <!-- Local -->
    <g v-for="k in nWin" :key="'l' + k" :class="{ off: stage < 1 }">
      <rect :x="40 + (k - 1) * winW + 6" y="142" :width="winW - 12" height="30" rx="6" fill="#fff" stroke="#eb6834" stroke-width="2" />
      <text :x="40 + (k - 0.5) * winW" y="161" text-anchor="middle" class="t1" fill="#eb6834">Local {{ k }}</text>
    </g>
    <text :x="W - 14" y="161" text-anchor="end" class="t2" :class="{ off: stage < 1 }"></text>
    <!-- Global -->
    <g :class="{ off: stage < 2 }">
      <rect x="46" y="198" :width="W - 72" height="30" rx="6" fill="#fff" stroke="#6250d6" stroke-width="2" />
      <text :x="W / 2" y="217" text-anchor="middle" class="t1" fill="#6250d6">Global：系列全体で共通する時間不変の特徴</text>
    </g>
    <g :class="{ off: stage < 3 }" v-if="!compact">
      <path d="M60,176 v18" stroke="#b4231f" stroke-width="2" />
      <path d="M56,180 L60,174 L64,180 M56,190 L60,196 L64,190" fill="none" stroke="#b4231f" stroke-width="2" />
      <text x="70" y="189" class="t2" fill="#b4231f" font-weight="700">反実仮想正則化：Local と Global の情報の重複を抑える</text>
    </g>
    <text x="40" y="262" class="t2" v-if="!compact">Local：窓ごとに変化する状態（時間変動）</text>
  </svg>
</template>

<style scoped>
.t1 { font-size: 12px; font-weight: 700; fill: #0b0b0b; }
.t2 { font-size: 11px; fill: #52514e; }
.off { opacity: 0.1; }
g { transition: opacity .4s; }
</style>
