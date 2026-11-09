<script setup lang="ts">
// 合成データ：真の成分と推定成分の相関（0 〜 1）
//   offP : 中心化なし（推定 4 成分に直交 Procrustes 回転をかけて真の成分に最も近づけた後）
//   on   : 中心化あり（回転なし）
import { COMP } from '../src/synth'
withDefaults(defineProps<{ stage?: number }>(), { stage: 2 })
const rows = [
  { k: 'g', n: '全期間成分', offP: 0.6393, on: 0.9994 },
  { k: 'a', n: '日成分', offP: 0.9673, on: 0.9979 },
  { k: 't', n: '時間帯成分', offP: 0.8403, on: 0.9990 },
  { k: 'u', n: '交互作用成分', offP: 0.3012, on: 0.9697 },
] as const
const W = 700, rowH = 46, mL = 130, mR = 130, top = 36, bh = 14
const pw = W - mL - mR
const x = (v: number) => mL + pw * v
const fmt = (v: number) => v.toFixed(4)
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${top + rows.length * rowH + 8}`" width="100%" class="cb">
    <text :x="x(0)" y="14" text-anchor="middle" class="tk">0</text>
    <text :x="x(0.5)" y="14" text-anchor="middle" class="tk">0.5</text>
    <text :x="x(1)" y="14" text-anchor="middle" class="tk">1</text>
    <text :x="x(0.5)" y="28" text-anchor="middle" class="tk" font-weight="700">真の成分との相関（1 に近いほど回復）</text>
    <line :x1="x(0)" :x2="x(0)" :y1="top" :y2="top + rows.length * rowH" stroke="#b8b8b2" />
    <line :x1="x(0.5)" :x2="x(0.5)" :y1="top" :y2="top + rows.length * rowH" stroke="#e8e8e4" />
    <line :x1="x(1)" :x2="x(1)" :y1="top" :y2="top + rows.length * rowH" stroke="#e8e8e4" />
    <g v-for="(r, i) in rows" :key="r.k" :transform="`translate(0, ${top + i * rowH})`">
      <text :x="mL - 10" y="26" text-anchor="end" class="lab" :fill="COMP[r.k]" font-weight="700">{{ r.n }}</text>
      <g :class="{ off: stage < 1 }">
        <rect :x="x(0)" y="5" :width="x(r.offP) - x(0)" :height="bh" fill="#eb6834" rx="3" />
        <text :x="x(r.offP) + 6" y="16" class="val" fill="#c2532a">なし {{ fmt(r.offP) }}</text>
      </g>
      <g :class="{ off: stage < 2 }">
        <rect :x="x(0)" y="24" :width="x(r.on) - x(0)" :height="bh" fill="#6250d6" rx="3" />
        <text :x="x(r.on) + 6" y="35" class="val" fill="#6250d6">あり {{ fmt(r.on) }}</text>
      </g>
    </g>
  </svg>
</template>

<style scoped>
.tk { font-size: 11px; fill: #52514e; }
.lab { font-size: 13px; }
.val { font-size: 11px; font-weight: 700; fill: #0b0b0b; }
.off { opacity: 0.1; }
g { transition: opacity .4s; }
</style>
