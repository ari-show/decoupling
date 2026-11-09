<script setup lang="ts">
// 「量」と「形」が中心化の制約から排他的になることの模式図
//   左：日成分は 24 時間帯で同じ値 → 日内カーブを平行移動するだけ（形は変えられない）
//   右：交互作用はその日の 24 時間帯の合計が 0 → 時間帯の間で配分を移すだけ（総量は変えられない）
// part: 'day' | 'inter' を指定すると片方のパネルだけ描く（SVG 書き出し用）
defineProps<{ part?: 'day' | 'inter' }>()
const H = Array.from({ length: 24 }, (_, i) => i)
const g = (h: number, c: number, w: number) => Math.exp(-(((h - c) / w) ** 2))
const mean = (h: number) => 0.07 * g(h, 9, 1.6) + 0.045 * g(h, 16, 2.2) - 0.03 * g(h, 2, 3)
const shifted = (h: number) => mean(h) + 0.05
const moved = (h: number) => mean(h) + 0.05 * g(h, 8, 1.4) - 0.05 * g(h, 17, 1.4)
const W = 300, Hh = 120, x0 = 34, y0 = 100, yS = 420
const X = (h: number) => x0 + (h / 23) * (W - x0 - 12)
const Y = (v: number) => y0 - v * yS
const path = (f: (h: number) => number) => H.map((h, i) => `${i ? 'L' : 'M'}${X(h).toFixed(1)},${Y(f(h)).toFixed(1)}`).join(' ')
</script>

<template>
  <div class="qs">
    <div v-if="part !== 'inter'" class="pane">
      <div class="ttl" style="color:#eb6834">日成分：24 時間帯で同じ値</div>
      <svg :viewBox="`0 0 ${W} ${Hh}`" width="100%">
        <line :x1="x0" :x2="W - 10" :y1="Y(0)" :y2="Y(0)" stroke="#b8b8b2" />
        <path :d="path(mean)" fill="none" stroke="#0b0b0b" stroke-width="2" />
        <path :d="path(shifted)" fill="none" stroke="#eb6834" stroke-width="2.2" />
        <g v-for="h in [4, 12, 20]" :key="h">
          <line :x1="X(h)" :x2="X(h)" :y1="Y(mean(h)) - 1" :y2="Y(shifted(h)) + 1" stroke="#eb6834" stroke-width="1.5" />
          <path :d="`M${X(h) - 3},${Y(shifted(h)) + 5} L${X(h)},${Y(shifted(h))} L${X(h) + 3},${Y(shifted(h)) + 5}`" fill="none" stroke="#eb6834" stroke-width="1.5" />
        </g>
        <text :x="X(0)" :y="Hh - 4" class="tk">0時</text>
        <text :x="X(23)" :y="Hh - 4" class="tk" text-anchor="end">23時</text>
      </svg>
      <div class="cap2">カーブ全体を上下に動かす ＝ その日の<b>総量</b>＝<b>量</b></div>
    </div>
    <div v-if="part !== 'day'" class="pane">
      <div class="ttl" style="color:#008300">交互作用：その日の 24 時間帯の合計 = 0</div>
      <svg :viewBox="`0 0 ${W} ${Hh}`" width="100%">
        <line :x1="x0" :x2="W - 10" :y1="Y(0)" :y2="Y(0)" stroke="#b8b8b2" />
        <path :d="path(mean)" fill="none" stroke="#0b0b0b" stroke-width="2" />
        <path :d="path(moved)" fill="none" stroke="#008300" stroke-width="2.2" />
        <path :d="`M${X(17)},${Y(mean(17)) - 6} C ${X(13)},${Y(mean(17)) - 40} ${X(11)},${Y(mean(8)) - 40} ${X(8.4)},${Y(moved(8)) - 4}`" fill="none" stroke="#008300" stroke-width="1.5" stroke-dasharray="4 3" />
        <path :d="`M${X(8.4) - 4},${Y(moved(8)) - 10} L${X(8.4)},${Y(moved(8)) - 3} L${X(8.4) + 4},${Y(moved(8)) - 10}`" fill="none" stroke="#008300" stroke-width="1.5" />
        <text :x="X(12.5)" :y="Y(0.12)" class="tk" text-anchor="middle" fill="#008300" font-weight="700">時間帯の間で移すだけ</text>
        <text :x="X(0)" :y="Hh - 4" class="tk">0時</text>
        <text :x="X(23)" :y="Hh - 4" class="tk" text-anchor="end">23時</text>
      </svg>
      <div class="cap2">時間帯の間で配分を移す ＝ その日の<b>配分</b>＝<b>形</b></div>
    </div>
  </div>
</template>

<style scoped>
.qs { display: flex; gap: 14px; }
.pane { flex: 1; border: 1.5px solid #d9d9d4; border-radius: 10px; padding: 6px 8px; background: #fff; }
.ttl { font-size: 0.85rem; font-weight: 700; text-align: center; }
.cap2 { font-size: 0.8rem; color: #52514e; text-align: center; margin-top: 2px; }
.cap2 b { color: #0b0b0b; }
.tk { font-size: 10px; fill: #52514e; }
</style>
