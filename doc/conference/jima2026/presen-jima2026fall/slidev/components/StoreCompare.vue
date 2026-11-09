<script setup lang="ts">
// 同じ日次売上でも、時間帯の分布が違えば打ち手が変わる
// stage 0: 日次（A店・B店は同じ）/ 1: 時間帯の分布 / 2: 打ち手の違い
import { computed } from 'vue'
const props = withDefaults(defineProps<{ stage?: number }>(), { stage: 2 })

const H = 24
const bump = (h: number, c: number, w: number) => Math.exp(-((h - c) ** 2) / w)
const rawA = Array.from({ length: H }, (_, h) => 0.15 + 1.0 * bump(h, 9, 9) + 0.25 * bump(h, 17, 10))
const rawB = Array.from({ length: H }, (_, h) => 0.15 + 0.25 * bump(h, 10, 10) + 1.0 * bump(h, 18, 9))
const TOTAL = 120
const norm = (xs: number[]) => { const s = xs.reduce((a, b) => a + b, 0); return xs.map(v => (v / s) * TOTAL) }
const A = norm(rawA), B = norm(rawB)

// 左：日次棒
const L = { x: 20, y: 40, w: 220, h: 200 }
// 右：時間帯
const R = { x: 320, y: 40, w: 560, h: 200 }
const yMax = 16
const sx = (h: number) => R.x + 30 + (h / (H - 1)) * (R.w - 40)
const sy = (v: number) => R.y + R.h - (v / yMax) * (R.h - 10)
const path = (xs: number[]) => xs.map((v, h) => `${h ? 'L' : 'M'}${sx(h).toFixed(1)},${sy(v).toFixed(1)}`).join(' ')
const area = (xs: number[]) => `${path(xs)} L${sx(H - 1)},${sy(0)} L${sx(0)},${sy(0)} Z`
const cA = '#2a78d6', cB = '#eb6834'
const on = (s: number) => props.stage >= s
const peakA = computed(() => A.indexOf(Math.max(...A)))
const peakB = computed(() => B.indexOf(Math.max(...B)))
</script>

<template>
  <svg viewBox="0 0 900 330" width="100%" class="sc">
    <!-- 左：日次売上 -->
    <text :x="L.x + L.w / 2" :y="L.y - 14" text-anchor="middle" class="ttl">日次で見ると</text>
    <line :x1="L.x + 20" :x2="L.x + L.w" :y1="L.y + L.h" :y2="L.y + L.h" class="axis" />
    <rect :x="L.x + 50" :y="L.y + 30" width="60" :height="L.h - 30" :fill="cA" rx="4" />
    <rect :x="L.x + 140" :y="L.y + 30" width="60" :height="L.h - 30" :fill="cB" rx="4" />
    <text :x="L.x + 80" :y="L.y + 20" text-anchor="middle" class="val">120 個</text>
    <text :x="L.x + 170" :y="L.y + 20" text-anchor="middle" class="val">120 個</text>
    <text :x="L.x + 80" :y="L.y + L.h + 18" text-anchor="middle" class="lab">A店</text>
    <text :x="L.x + 170" :y="L.y + L.h + 18" text-anchor="middle" class="lab">B店</text>
    <text :x="L.x + L.w / 2" :y="L.y + L.h + 40" text-anchor="middle" class="note">同じ商品・同じ日の売上は同じ</text>

    <!-- 矢印 -->
    <g :class="{ off: !on(1) }">
      <path :d="`M${L.x + L.w + 22},${L.y + L.h / 2} h36`" class="arr" />
      <path :d="`M${L.x + L.w + 50},${L.y + L.h / 2 - 7} l10,7 l-10,7`" class="arr" fill="none" />
    </g>

    <!-- 右：時間帯別 -->
    <g :class="{ off: !on(1) }">
      <text :x="R.x + R.w / 2" :y="R.y - 14" text-anchor="middle" class="ttl">時間帯で見ると</text>
      <line :x1="R.x + 30" :x2="R.x + R.w" :y1="sy(0)" :y2="sy(0)" class="axis" />
      <line :x1="R.x + 30" :x2="R.x + 30" :y1="R.y" :y2="sy(0)" class="axis" />
      <text v-for="k in [0, 6, 12, 18, 23]" :key="k" :x="sx(k)" :y="sy(0) + 14" text-anchor="middle" class="tick">{{ k }}</text>
      <text :x="R.x + R.w / 2" :y="sy(0) + 30" text-anchor="middle" class="lab">時間帯</text>
      <path :d="area(A)" :fill="cA" opacity="0.12" />
      <path :d="area(B)" :fill="cB" opacity="0.12" />
      <path :d="path(A)" fill="none" :stroke="cA" stroke-width="2.5" />
      <path :d="path(B)" fill="none" :stroke="cB" stroke-width="2.5" />
      <text :x="sx(peakA)" :y="sy(A[peakA]) - 8" text-anchor="middle" class="val" :fill="cA">A店：朝に集中</text>
      <text :x="sx(peakB)" :y="sy(B[peakB]) - 8" text-anchor="middle" class="val" :fill="cB">B店：夕方に集中</text>
    </g>

    <!-- 打ち手 -->
    <g :class="{ off: !on(2) }">
      <rect :x="R.x + 20" y="276" width="255" height="44" rx="8" fill="#fff" :stroke="cA" stroke-width="1.5" />
      <text :x="R.x + 147" y="294" text-anchor="middle" class="act" :fill="cA">A店の打ち手</text>
      <text :x="R.x + 147" y="311" text-anchor="middle" class="note">開店前に補充、朝の人員を厚く</text>
      <rect :x="R.x + 295" y="276" width="255" height="44" rx="8" fill="#fff" :stroke="cB" stroke-width="1.5" />
      <text :x="R.x + 422" y="294" text-anchor="middle" class="act" :fill="cB">B店の打ち手</text>
      <text :x="R.x + 422" y="311" text-anchor="middle" class="note">夕方前に補充、夕方の人員を厚く</text>
      <text :x="L.x + L.w / 2" y="308" text-anchor="middle" class="warn">日次だけでは</text>
      <text :x="L.x + L.w / 2" y="324" text-anchor="middle" class="warn">区別がつかない</text>
    </g>
  </svg>
</template>

<style scoped>
.ttl { font-size: 14px; font-weight: 700; fill: #0b0b0b; }
.val { font-size: 12px; font-weight: 700; fill: #0b0b0b; }
.lab { font-size: 12px; fill: #52514e; }
.tick { font-size: 10px; fill: #6b6b6b; }
.note { font-size: 11px; fill: #52514e; }
.act { font-size: 12px; font-weight: 700; }
.warn { font-size: 13px; font-weight: 700; fill: #b4231f; }
.axis { stroke: #b8b8b2; stroke-width: 1; }
.arr { stroke: #52514e; stroke-width: 2; }
.off { opacity: 0.08; }
g { transition: opacity .4s; }
</style>
