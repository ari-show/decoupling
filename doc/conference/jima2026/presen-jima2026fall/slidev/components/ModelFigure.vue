<script setup lang="ts">
// 提案モデルの全体像（段階表示）
// stage 0: 入力 / 1: Encoder（集約方向） / 2: 潜在表現 / 3: Decoder→4成分 / 4: 中心化 / 5: 加算→推定残差
import { computed } from 'vue'
import { D, H, value, diverging, COMP, type Mode } from '../src/synth'
const props = withDefaults(defineProps<{ stage?: number }>(), { stage: 5 })

// 粗いミニグリッド（7日×12時間帯）
const MD = 7, MH = 12, CS = 7
function mini(mode: Mode, x: number, y: number, agg: 'none' | 'all' | 'row' | 'col' = 'none') {
  const cells: { x: number; y: number; f: string }[] = []
  for (let dd = 0; dd < MD; dd++)
    for (let hh = 0; hh < MH; hh++) {
      const d = Math.min(D - 1, dd * 4), h = Math.min(H - 1, hh * 2)
      cells.push({ x: x + hh * CS, y: y + dd * CS, f: diverging(value(mode, d, h), 1.2) })
    }
  return { cells, w: MH * CS, h: MD * CS, x, y, agg }
}
const on = (s: number) => props.stage >= s

const rows = [
  { k: 'g', y: 74,  enc: '全体で集約', net: 'MLP', agg: 'all', z: 'z_g' },
  { k: 'a', y: 174, enc: '日ごとに集約', net: 'MLP', agg: 'row', z: 'z_a,d' },
  { k: 't', y: 274, enc: '時間帯ごとに集約', net: 'MLP', agg: 'col', z: 'z_t,h' },
  { k: 'u', y: 374, enc: 'z_a ⊕ z_t', net: 'MLP', agg: 'none', z: 'z_u,d,h' },
] as const

const inGrid = mini('r', 18, 214)
const encGrids = computed(() => rows.map(r => (r.k === 'u' ? null : mini('r', 182, r.y - 4, r.agg))))
const outGrids = computed(() => rows.map(r => mini(r.k as Mode, 612, r.y - 4)))
const sumGrid = mini('r', 900, 214)
</script>

<template>
  <svg viewBox="0 0 1000 480" class="mf" width="100%">
    <defs>
      <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" fill="#52514e" />
      </marker>
    </defs>

    <!-- 領域 -->
    <rect x="160" y="28" width="330" height="420" rx="10" class="zone enc" :class="{ off: !on(1) }" />
    <text x="325" y="46" text-anchor="middle" class="zl" :class="{ off: !on(1) }">Encoder：共有範囲に合わせて集約</text>
    <rect x="520" y="28" width="200" height="420" rx="10" class="zone dec" :class="{ off: !on(3) }" />
    <text x="620" y="46" text-anchor="middle" class="zl" :class="{ off: !on(3) }">Decoder：4成分を推定</text>

    <!-- 入力 -->
    <g>
      <rect v-for="(c, i) in inGrid.cells" :key="i" :x="c.x" :y="c.y" width="6" height="6" :fill="c.f" />
      <rect :x="inGrid.x - 1" :y="inGrid.y - 1" :width="inGrid.w + 1" :height="inGrid.h + 1" fill="none" stroke="#0b0b0b" stroke-width="1.2" />
      <text :x="inGrid.x + inGrid.w / 2" :y="inGrid.y - 10" text-anchor="middle" class="t1">観測残差</text>
      <text :x="inGrid.x + inGrid.w / 2" :y="inGrid.y + inGrid.h + 14" text-anchor="middle" class="t2">28日 × 24時間帯</text>
      <text :x="inGrid.x + inGrid.w / 2" :y="inGrid.y + inGrid.h + 28" text-anchor="middle" class="t2">+ 共変量</text>
      <text :x="inGrid.x + inGrid.w / 2" :y="inGrid.y + inGrid.h + 41" text-anchor="middle" class="t2" font-size="9">（欠品・曜日・販促・天候）</text>
    </g>

    <!-- 各成分の行 -->
    <g v-for="(r, i) in rows" :key="r.k">
      <!-- 入力 → Encoder -->
      <path v-if="r.k !== 'u'" :d="`M${inGrid.x + inGrid.w + 2},${inGrid.y + inGrid.h / 2} C150,${inGrid.y + inGrid.h / 2} 150,${r.y + 20} 178,${r.y + 20}`" class="ln" :class="{ off: !on(1) }" marker-end="url(#arr)" />

      <!-- Encoder：集約方向つきミニグリッド -->
      <g v-if="encGrids[i]" :class="{ off: !on(1) }">
        <rect v-for="(c, j) in encGrids[i]!.cells" :key="j" :x="c.x" :y="c.y" width="6" height="6" :fill="c.f" opacity="0.9" />
        <!-- 集約の強調 -->
        <rect v-if="r.agg === 'all'" :x="encGrids[i]!.x - 2" :y="encGrids[i]!.y - 2" :width="encGrids[i]!.w + 3" :height="encGrids[i]!.h + 3" fill="none" :stroke="COMP.g" stroke-width="2.5" />
        <g v-if="r.agg === 'row'">
          <rect v-for="dd in MD" :key="dd" :x="encGrids[i]!.x - 2" :y="encGrids[i]!.y + (dd - 1) * CS - 1" :width="encGrids[i]!.w + 3" :height="CS" fill="none" :stroke="COMP.a" stroke-width="1.2" />
          <path :d="`M${encGrids[i]!.x + 2},${encGrids[i]!.y + encGrids[i]!.h + 8} h${encGrids[i]!.w - 4}`" :stroke="COMP.a" stroke-width="2" marker-end="url(#arr)" />
        </g>
        <g v-if="r.agg === 'col'">
          <rect v-for="hh in MH" :key="hh" :x="encGrids[i]!.x + (hh - 1) * CS - 1" :y="encGrids[i]!.y - 2" :width="CS" :height="encGrids[i]!.h + 3" fill="none" :stroke="COMP.t" stroke-width="1.2" />
          <path :d="`M${encGrids[i]!.x + encGrids[i]!.w + 8},${encGrids[i]!.y + 2} v${encGrids[i]!.h - 4}`" :stroke="COMP.t" stroke-width="2" marker-end="url(#arr)" />
        </g>
        <text :x="encGrids[i]!.x + encGrids[i]!.w / 2" :y="r.y - 12" text-anchor="middle" class="t2">{{ r.enc }}</text>
      </g>
      <!-- 交互作用：z_a と z_t を結合 -->
      <g v-else :class="{ off: !on(2) }">
        <path :d="`M410,${rows[1].y + 34} C410,${r.y - 10} 300,${r.y - 10} 300,${r.y + 6}`" class="ln u" />
        <path :d="`M410,${rows[2].y + 34} C410,${r.y - 10} 320,${r.y - 10} 320,${r.y + 6}`" class="ln u" marker-end="url(#arr)" />
        <rect x="262" :y="r.y + 6" width="100" height="28" rx="6" class="box" :stroke="COMP.u" />
        <text x="312" :y="r.y + 24" text-anchor="middle" class="t2">z_a と z_t を結合</text>
      </g>

      <!-- Encoder net -->
      <g :class="{ off: !on(1) }">
        <path v-if="r.k !== 'u'" :d="`M${182 + MH * CS + 14},${r.y + 20} h22`" class="ln" marker-end="url(#arr)" />
        <rect x="298" :y="r.y + 2" width="54" height="36" rx="6" class="box" v-if="r.k !== 'u'" />
        <text x="325" :y="r.y + 25" text-anchor="middle" class="t1" v-if="r.k !== 'u'">{{ r.net }}</text>
      </g>

      <!-- → 潜在表現 -->
      <g :class="{ off: !on(2) }">
        <path :d="`M${r.k === 'u' ? 362 : 352},${r.y + 20} h24`" class="ln" marker-end="url(#arr)" />
        <rect x="388" :y="r.y + 2" width="70" height="36" rx="18" class="zbox" :stroke="COMP[r.k]" />
        <text x="423" :y="r.y + 25" text-anchor="middle" class="t1" :fill="COMP[r.k]">{{ r.z }}</text>
        <!-- u 用：MLP -->
      </g>

      <!-- → Decoder → 成分 -->
      <g :class="{ off: !on(3) }">
        <path :d="`M458,${r.y + 20} h74`" class="ln" marker-end="url(#arr)" />
        <rect x="534" :y="r.y + 2" width="56" height="36" rx="6" class="box" />
        <text x="562" :y="r.y + 25" text-anchor="middle" class="t1">MLP</text>
        <path :d="`M590,${r.y + 20} h18`" class="ln" marker-end="url(#arr)" />
        <rect v-for="(c, j) in outGrids[i].cells" :key="j" :x="c.x" :y="c.y" width="6" height="6" :fill="c.f" />
        <rect :x="outGrids[i].x - 2" :y="outGrids[i].y - 2" :width="outGrids[i].w + 3" :height="outGrids[i].h + 3" fill="none" :stroke="COMP[r.k]" stroke-width="2.5" />
      </g>

      <!-- → 中心化 → Σ -->
      <g :class="{ off: !on(4) }">
        <path :d="`M${612 + MH * CS + 2},${r.y + 20} h20`" class="ln" marker-end="url(#arr)" />
        <rect x="720" :y="r.y + 4" width="56" height="32" rx="6" class="cbox" :class="{ none: r.k === 'g' }" />
        <text x="748" :y="r.y + 24" text-anchor="middle" class="t2" :fill="r.k === 'g' ? '#9a9a9a' : '#b4231f'" font-weight="700">{{ r.k === 'g' ? '―' : '平均 0' }}</text>
      </g>
      <g :class="{ off: !on(5) }">
        <path :d="`M776,${r.y + 20} C800,${r.y + 20} 800,244 826,244`" class="ln" />
      </g>
    </g>

    <!-- 中心化のラベル -->
    <text x="748" y="40" text-anchor="middle" class="zl red" :class="{ off: !on(4) }">中心化制約</text>
    <text x="748" y="55" text-anchor="middle" class="t2 red" :class="{ off: !on(4) }">成分の担当範囲を固定</text>

    <!-- Σ と出力 -->
    <g :class="{ off: !on(5) }">
      <path d="M826,244 h6" class="ln" marker-end="url(#arr)" />
      <circle cx="852" cy="244" r="18" class="box" />
      <text x="852" y="250" text-anchor="middle" class="t1" font-size="18">Σ</text>
      <path d="M870,244 h22" class="ln" marker-end="url(#arr)" />
      <rect v-for="(c, i) in sumGrid.cells" :key="i" :x="c.x" :y="c.y" width="6" height="6" :fill="c.f" />
      <rect :x="sumGrid.x - 1" :y="sumGrid.y - 1" :width="sumGrid.w + 1" :height="sumGrid.h + 1" fill="none" stroke="#0b0b0b" stroke-width="1.2" />
      <text :x="sumGrid.x + sumGrid.w / 2" :y="sumGrid.y - 10" text-anchor="middle" class="t1">推定残差</text>
      <text :x="sumGrid.x + sumGrid.w / 2" :y="sumGrid.y + sumGrid.h + 14" text-anchor="middle" class="t2">+ 基準値 → 売上推定</text>
    </g>
  </svg>
</template>

<style scoped>
.zone { stroke-width: 1.5; transition: opacity .4s; }
.zone.enc { fill: #eef7ee; stroke: #8fc48f; }
.zone.dec { fill: #eaf2fb; stroke: #8fb3e0; }
.zl { font-size: 13px; font-weight: 700; fill: #0b0b0b; transition: opacity .4s; }
.t1 { font-size: 12px; fill: #0b0b0b; font-weight: 600; }
.t2 { font-size: 10.5px; fill: #52514e; }
.red { fill: #b4231f; }
.ln { fill: none; stroke: #52514e; stroke-width: 1.4; transition: opacity .4s; }
.ln.u { stroke: #008300; stroke-width: 1.6; stroke-dasharray: 4 3; }
.box { fill: #fff; stroke: #52514e; stroke-width: 1.3; }
.zbox { fill: #fff; stroke-width: 2; }
.cbox { fill: #fff3f2; stroke: #b4231f; stroke-width: 1.6; stroke-dasharray: 5 3; }
.cbox.none { fill: #f6f6f4; stroke: #c9c9c4; stroke-dasharray: none; }
.off { opacity: 0.08; }
g.off, .off * { transition: opacity .4s; }
</style>
