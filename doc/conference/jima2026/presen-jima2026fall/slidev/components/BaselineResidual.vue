<script setup lang="ts">
// 店舗ごとの売上水準（基準値）を分けると、残差で売れ方の形を店舗横断で比べられる
// stage 0: 水準の違う生の売上 / 1: 店舗ごとの基準値 / 2: 残差を重ねる
import { computed } from 'vue'
const props = withDefaults(defineProps<{ stage?: number }>(), { stage: 2 })

const H = 24
const bump = (h: number, c: number, w: number) => Math.exp(-((h - c) ** 2) / w)
const shapes = [
  { name: 'A店（大型）', base: 30, amp: 10, f: (h: number) => 1.0 * bump(h, 9, 9) + 0.3 * bump(h, 17, 10) - 0.35, c: '#2a78d6' },
  { name: 'B店（小型）', base: 8, amp: 4, f: (h: number) => 0.3 * bump(h, 10, 10) + 1.0 * bump(h, 18, 9) - 0.35, c: '#eb6834' },
  { name: 'C店（中型）', base: 17, amp: 6, f: (h: number) => 0.8 * bump(h, 8, 7) + 0.8 * bump(h, 16, 9) - 0.4, c: '#008300' },
]
const stores = shapes.map(s => ({
  ...s,
  raw: Array.from({ length: H }, (_, h) => s.base + s.amp * s.f(h)),
  res: Array.from({ length: H }, (_, h) => s.amp * s.f(h)),
}))

const Lp = { x: 20, y: 36, w: 400, h: 240 }
const Rp = { x: 480, y: 36, w: 400, h: 240 }
const yMaxL = 44, yR = 11
const lx = (h: number) => Lp.x + 34 + (h / (H - 1)) * (Lp.w - 44)
const ly = (v: number) => Lp.y + Lp.h - (v / yMaxL) * (Lp.h - 10)
const rx = (h: number) => Rp.x + 34 + (h / (H - 1)) * (Rp.w - 44)
const ry = (v: number) => Rp.y + Rp.h / 2 - (v / yR) * (Rp.h / 2 - 10)
const pathL = (xs: number[]) => xs.map((v, h) => `${h ? 'L' : 'M'}${lx(h).toFixed(1)},${ly(v).toFixed(1)}`).join(' ')
const pathR = (xs: number[]) => xs.map((v, h) => `${h ? 'L' : 'M'}${rx(h).toFixed(1)},${ry(v).toFixed(1)}`).join(' ')
const on = (s: number) => props.stage >= s
const ticks = [0, 6, 12, 18, 23]

// stage 3: 同じ店（A店）の別の日の残差。形は似ているが日によって上下にずれる
const A = stores[0]
const dayOff = [3.2, 1.5, -1.3, -2.9]
const dayLines = dayOff.map((o, i) => A.res.map((v, h) => v + o + 0.45 * Math.sin(h * 1.3 + i * 2.1)))
const peakH = A.res.indexOf(Math.max(...A.res))
</script>

<template>
  <svg viewBox="0 0 900 300" width="100%" class="br">
    <!-- 左：生の売上 -->
    <text :x="Lp.x + Lp.w / 2" :y="Lp.y - 12" text-anchor="middle" class="ttl">時間帯別の売上（店舗ごとに水準が違う）</text>
    <line :x1="Lp.x + 34" :x2="Lp.x + Lp.w" :y1="ly(0)" :y2="ly(0)" class="axis" />
    <line :x1="Lp.x + 34" :x2="Lp.x + 34" :y1="Lp.y" :y2="ly(0)" class="axis" />
    <text v-for="k in ticks" :key="k" :x="lx(k)" :y="ly(0) + 13" text-anchor="middle" class="tick">{{ k }}</text>
    <text :x="Lp.x + 10" :y="Lp.y + Lp.h / 2" text-anchor="middle" class="lab" :transform="`rotate(-90 ${Lp.x + 10} ${Lp.y + Lp.h / 2})`">売上</text>
    <g v-for="s in stores" :key="s.name">
      <path :d="pathL(s.raw)" fill="none" :stroke="s.c" stroke-width="2.4" />
      <text :x="lx(H - 1) + 4" :y="ly(s.raw[H - 1]) + 4" class="val" :fill="s.c">{{ s.name.slice(0, 2) }}</text>
      <!-- 基準値 -->
      <g :class="{ off: !on(1) }">
        <line :x1="lx(0)" :x2="lx(H - 1)" :y1="ly(s.base)" :y2="ly(s.base)" :stroke="s.c" stroke-width="2" stroke-dasharray="6 4" opacity="0.9" />
        <text :x="lx(0) + 2" :y="ly(s.base) - 4" class="tick" :fill="s.c" font-weight="700">基準値 {{ s.base }}</text>
      </g>
    </g>

    <!-- 矢印 -->
    <g :class="{ off: !on(2) }">
      <path :d="`M${Lp.x + Lp.w + 14},${Lp.y + Lp.h / 2} h30`" class="arr" />
      <path :d="`M${Lp.x + Lp.w + 36},${Lp.y + Lp.h / 2 - 7} l10,7 l-10,7`" class="arr" fill="none" />
      <text :x="Lp.x + Lp.w + 30" :y="Lp.y + Lp.h / 2 - 14" text-anchor="middle" class="tick">− 基準値</text>
    </g>

    <!-- 右：残差 -->
    <g :class="{ off: !on(2) }">
      <text :x="Rp.x + Rp.w / 2" :y="Rp.y - 12" text-anchor="middle" class="ttl" :class="{ hide: on(3) }">基準値からの残差（水準をそろえて重ねる）</text>
      <rect :x="Rp.x + 34" :y="Rp.y" :width="Rp.w - 34" :height="Rp.h / 2" fill="#e34948" opacity="0.07" />
      <rect :x="Rp.x + 34" :y="Rp.y + Rp.h / 2" :width="Rp.w - 34" :height="Rp.h / 2" fill="#2a78d6" opacity="0.07" />
      <g :class="{ hide: on(3) }">
        <text :x="Rp.x + Rp.w - 4" :y="Rp.y + 14" text-anchor="end" class="band" fill="#b4231f">正の残差：基準値より売れた</text>
        <text :x="Rp.x + Rp.w - 4" :y="Rp.y + Rp.h - 6" text-anchor="end" class="band" fill="#1f5fb0">負の残差：基準値より売れなかった</text>
      </g>
      <line :x1="Rp.x + 34" :x2="Rp.x + Rp.w" :y1="ry(0)" :y2="ry(0)" stroke="#444" stroke-width="2" stroke-dasharray="6 4" />
      <line :x1="Rp.x + 34" :x2="Rp.x + 34" :y1="Rp.y" :y2="Rp.y + Rp.h" class="axis" />
      <text :x="Rp.x + 30" :y="ry(0) + 4" text-anchor="end" class="tick">0</text>
      <text v-for="k in ticks" :key="k" :x="rx(k)" :y="Rp.y + Rp.h + 13" text-anchor="middle" class="tick">{{ k }}</text>
      <path v-for="s in stores" :key="s.name" :d="pathR(s.res)" fill="none" :stroke="s.c" stroke-width="2.4" :style="{ opacity: on(3) && s !== A ? 0.18 : 1, transition: 'opacity .4s' }" />
    </g>

    <!-- stage 3: 同じ店でも日によって上下にずれる（stage 2 の表示を置き換えるので完全非表示から出す） -->
    <g :class="{ hide: !on(3) }">
      <path v-for="(d, i) in dayLines" :key="i" :d="pathR(d)" fill="none" :stroke="A.c" stroke-width="1.5" style="opacity: .45" />
      <line :x1="rx(H - 1) + 8" :x2="rx(H - 1) + 8" :y1="ry(A.res[H - 1] + dayOff[0])" :y2="ry(A.res[H - 1] + dayOff[3])" stroke="#eb6834" stroke-width="2.5" />
      <text :x="Rp.x + Rp.w - 4" :y="Rp.y + 14" text-anchor="end" class="band" fill="#eb6834">日によるずれ（上下）</text>
      <text :x="rx(peakH)" :y="ry(A.res[peakH] + dayOff[0]) - 8" text-anchor="middle" class="band" fill="#6250d6">時間帯によるずれ（形）</text>
      <text :x="Rp.x + Rp.w / 2" :y="Rp.y - 12" text-anchor="middle" class="ttl">A店の残差を 4 日分重ねる（形は似て、上下にずれる）</text>
    </g>
  </svg>
</template>

<style scoped>
.ttl { font-size: 14px; font-weight: 700; fill: #0b0b0b; }
.val { font-size: 12px; font-weight: 700; }
.lab { font-size: 11px; fill: #52514e; }
.tick { font-size: 10px; fill: #6b6b6b; }
.band { font-size: 11px; font-weight: 700; }
.axis { stroke: #b8b8b2; stroke-width: 1; }
.arr { stroke: #52514e; stroke-width: 2; }
.off { opacity: 0.08; }
.hide { opacity: 0; }
g, text { transition: opacity .4s; }
</style>
