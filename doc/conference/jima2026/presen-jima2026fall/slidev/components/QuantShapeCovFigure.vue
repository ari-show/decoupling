<script setup lang="ts">
// 「量」「形」と共変量の相関が何を測っているかの模式図（1 系列の 28 日分）
//   上段：その日の共変量（休日＝網掛け、割引の深さ＝紫の棒）
//   中段：量 = その日の日成分 a_{i,d}（橙の棒）と、実測のみの日平均（灰点）
//   下段：形 = その日の交互作用の RMS（緑の棒）と、実測のみの RMS（灰点）
//   相関は (系列, 日) を 1 点として、同じ日の共変量と縦の値を突き合わせる
const D = 28
const days = Array.from({ length: D }, (_, i) => i + 1)
const holiday = (d: number) => d % 7 === 6 || d % 7 === 0
const discount = (d: number) => ({ 3: 0.3, 10: 0.25, 17: 0.35, 24: 0.2, 12: 0.1, 21: 0.12 } as Record<number, number>)[d] ?? 0
// 決定的な擬似乱数（図が毎回同じになるように）
const rnd = (d: number, k: number) => { const x = Math.sin(d * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x) - 0.5 }
const amount = (d: number) => 0.012 + (holiday(d) ? 0.045 : 0) + 0.02 * discount(d) + 0.012 * rnd(d, 1)
const amountRaw = (d: number) => amount(d) + 0.03 * rnd(d, 2)
const shape = (d: number) => 0.015 + 0.09 * discount(d) + (holiday(d) ? 0.008 : 0) + 0.006 * rnd(d, 3)
const shapeRaw = (d: number) => shape(d) + 0.025 + 0.02 * rnd(d, 4)

const W = 640, x0 = 86, x1 = W - 10
const X = (d: number) => x0 + ((d - 1) / (D - 1)) * (x1 - x0)
const bw = (x1 - x0) / (D - 1) * 0.6
const rows = [
  { y: 18, h: 44, label: 'その日の共変量' },
  { y: 84, h: 70, label: '量' },
  { y: 176, h: 70, label: '形' },
]
const base = (r: { y: number; h: number }) => r.y + r.h
const bar = (d: number, r: { y: number; h: number }, v: number, s: number) => ({ x: X(d) - bw / 2, y: base(r) - Math.max(v, 0) * s, width: bw, height: Math.max(v, 0) * s })
</script>

<template>
  <svg :viewBox="`0 0 ${W} 262`" width="100%" font-family="inherit">
    <!-- 休日の網掛け（全行に通す） -->
    <g v-for="d in days" :key="'h' + d">
      <rect v-if="holiday(d)" :x="X(d) - bw / 2 - 2" y="14" :width="bw + 4" height="236" fill="#f2f2ee" />
    </g>
    <!-- 上段：共変量 -->
    <text :x="x0 - 6" :y="rows[0].y + 14" class="lab" text-anchor="end">休日</text>
    <text :x="x0 - 6" :y="rows[0].y + 40" class="lab" text-anchor="end" fill="#6250d6">割引の深さ</text>
    <g v-for="d in days" :key="'c' + d">
      <rect v-if="holiday(d)" :x="X(d) - bw / 2" :y="rows[0].y + 4" :width="bw" height="12" fill="#9a9a94" />
      <rect v-if="discount(d) > 0" v-bind="bar(d, { y: rows[0].y + 22, h: 22 }, discount(d), 60)" fill="#6250d6" />
    </g>
    <line :x1="x0" :x2="x1" :y1="base(rows[0])" :y2="base(rows[0])" stroke="#d9d9d4" />
    <!-- 中段：量 -->
    <text :x="x0 - 6" :y="rows[1].y + 30" class="lab2" text-anchor="end" fill="#eb6834">量</text>
    <text :x="x0 - 6" :y="rows[1].y + 44" class="lab" text-anchor="end">その日の日成分</text>
    <g v-for="d in days" :key="'a' + d">
      <rect v-bind="bar(d, rows[1], amount(d), 900)" fill="#eb6834" />
      <circle :cx="X(d)" :cy="base(rows[1]) - Math.max(amountRaw(d), 0) * 900" r="2.4" fill="#9a9a94" />
    </g>
    <line :x1="x0" :x2="x1" :y1="base(rows[1])" :y2="base(rows[1])" stroke="#b8b8b2" />
    <!-- 下段：形 -->
    <text :x="x0 - 6" :y="rows[2].y + 30" class="lab2" text-anchor="end" fill="#008300">形</text>
    <text :x="x0 - 6" :y="rows[2].y + 44" class="lab" text-anchor="end">交互作用の RMS</text>
    <g v-for="d in days" :key="'u' + d">
      <rect v-bind="bar(d, rows[2], shape(d), 1300)" fill="#008300" />
      <circle :cx="X(d)" :cy="base(rows[2]) - Math.max(shapeRaw(d), 0) * 1300" r="2.4" fill="#9a9a94" />
    </g>
    <line :x1="x0" :x2="x1" :y1="base(rows[2])" :y2="base(rows[2])" stroke="#b8b8b2" />
    <!-- x 軸 -->
    <text :x="X(1)" y="258" class="tk" text-anchor="middle">1日</text>
    <text :x="X(14)" y="258" class="tk" text-anchor="middle">14日</text>
    <text :x="X(28)" y="258" class="tk" text-anchor="middle">28日</text>
    <!-- 注釈 -->
    <text :x="x1" :y="rows[1].y + 10" class="note" text-anchor="end" fill="#eb6834">休日の日に高い → 休日×量 +</text>
    <text :x="x1" :y="rows[2].y + 10" class="note" text-anchor="end" fill="#008300">割引の日に高い → 割引×形 +</text>
  </svg>
</template>

<style scoped>
.lab { font-size: 9.5px; fill: #52514e; }
.lab2 { font-size: 13px; font-weight: 700; }
.tk { font-size: 9.5px; fill: #52514e; }
.note { font-size: 10.5px; font-weight: 700; }
</style>
