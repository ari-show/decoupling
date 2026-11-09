<script setup lang="ts">
// Decoder の時間帯カーブを PCA した 3 軸の模式図（実図が届いたら <img> に差し替える）
//   黒：平均カーブ　赤：+2SD　青破線：−2SD
//   各パネル：名前（軸の意味）→ 図 → 出たもの（note）→ 帰属（owner）→ 言えること（say, showSay で表示）
defineProps<{ showSay?: boolean }>()
const H = Array.from({ length: 24 }, (_, i) => i)
const g = (h: number, c: number, w: number) => Math.exp(-(((h - c) / w) ** 2))
const mean = (h: number) => 0.07 * g(h, 9, 1.6) + 0.04 * g(h, 16, 2.2) - 0.03 * g(h, 2, 3)
const panels = [
  {
    k: 'PC1', share: '82%', name: 'ピークの高さ', owner: '商品 0.86 ／ 店舗 −0.03', oc: '#6250d6',
    hi: (h: number) => 3.6 * mean(h), lo: (h: number) => -1.2 * mean(h), yS: 160,
    note: 'ピークの時刻は動かず、山全体が伸び縮みする',
    say: '系列間の形の違いは、<b>いつ売れるかではなく、ピークがどれだけ高いか</b>。ただし高さは売上水準にほぼ比例（水準を除くと商品 R² 0.21）。',
  },
  {
    k: 'PC2', share: '6%', name: '朝型 ⇔ 夕方型', owner: '商品 0.32 ／ 店舗 0.11', oc: '#6250d6',
    hi: (h: number) => mean(h) + 0.05 * g(h, 8, 1.5) - 0.03 * g(h, 17, 2.5), lo: (h: number) => mean(h) - 0.04 * g(h, 8, 1.5) + 0.05 * g(h, 16, 2.2), yS: 420,
    note: '朝が伸びると昼〜夜が沈むシーソー',
    say: 'ピークの<b>時刻</b>の違いはここに集まるが、分散の 6% と小さい。商品でも店舗でも決まりきらない。',
  },
  {
    k: 'PC3', share: '3%', name: '午後の山の有無', owner: '商品 −0.11 ／ 店舗 +0.16', oc: '#b4231f',
    hi: (h: number) => mean(h) + 0.06 * g(h, 15, 1.5) - 0.02 * g(h, 9, 1.6), lo: (h: number) => mean(h) - 0.01 * g(h, 15, 1.5) + 0.01 * g(h, 9, 1.6), yS: 420,
    note: '14〜16 時に山が立つ',
    say: '<b>店舗の性質として出る形はここだけ</b>。ただし店舗差は平均のずれで、店舗群として分離はしない。',
  },
]
const W = 260, Hh = 104, x0 = 10, y0 = 70
const X = (h: number) => x0 + (h / 23) * (W - x0 - 8)
const path = (f: (h: number) => number, yS: number) => H.map((h, i) => `${i ? 'L' : 'M'}${X(h).toFixed(1)},${(y0 - f(h) * yS).toFixed(1)}`).join(' ')
</script>

<template>
  <div class="pca">
    <div v-for="p in panels" :key="p.k" class="pane">
      <div class="hd"><span class="pc">{{ p.k }}</span><span class="sh">{{ p.share }}</span><span class="nm">{{ p.name }}</span></div>
      <svg :viewBox="`0 0 ${W} ${Hh}`" width="100%">
        <line :x1="x0" :x2="W - 6" :y1="y0" :y2="y0" stroke="#b8b8b2" />
        <path :d="path(p.lo, p.yS)" fill="none" stroke="#2b6cb0" stroke-width="1.8" stroke-dasharray="5 3" />
        <path :d="path(p.hi, p.yS)" fill="none" stroke="#b4231f" stroke-width="2" />
        <path :d="path(mean, p.yS)" fill="none" stroke="#0b0b0b" stroke-width="2" />
        <text :x="X(0)" :y="Hh - 3" class="tk">0時</text>
        <text :x="X(9)" :y="Hh - 3" class="tk" text-anchor="middle">9時</text>
        <text :x="X(16)" :y="Hh - 3" class="tk" text-anchor="middle">16時</text>
        <text :x="X(23)" :y="Hh - 3" class="tk" text-anchor="end">23時</text>
      </svg>
      <div class="note">{{ p.note }}</div>
      <div class="own" :style="{ color: p.oc }">帰属 R²：{{ p.owner }}</div>
      <div class="say transition-opacity duration-300" :class="showSay === false ? 'opacity-15' : ''" v-html="p.say"></div>
    </div>
  </div>
</template>

<style scoped>
.pca { display: flex; gap: 12px; }
.pane { flex: 1; border: 1.5px solid #d9d9d4; border-radius: 10px; padding: 5px 8px 6px; background: #fff; }
.hd { display: flex; align-items: baseline; gap: 6px; }
.pc { font-weight: 700; font-size: 0.9rem; }
.sh { font-weight: 700; font-size: 0.9rem; color: #b4231f; }
.nm { font-size: 0.85rem; font-weight: 700; color: #0b0b0b; }
.note { font-size: 0.74rem; color: #52514e; line-height: 1.3; }
.own { font-size: 0.74rem; font-weight: 700; margin-top: 1px; }
.say { font-size: 0.78rem; line-height: 1.35; margin-top: 4px; padding-top: 4px; border-top: 1px dashed #d9d9d4; color: #0b0b0b; }
.say :deep(b) { color: #b4231f; }
.tk { font-size: 10px; fill: #52514e; }
</style>
