<script setup lang="ts">
import { computed } from 'vue'
import { D, H, value, diverging, type Mode } from '../src/synth'

const props = withDefaults(defineProps<{
  mode?: Mode
  cell?: number
  gap?: number
  highlight?: 'none' | 'row' | 'col' | 'cell' | 'rowcol' | 'all'
  hiRow?: number
  hiCol?: number
  axes?: boolean
  scale?: number
  dim?: boolean
}>(), {
  mode: 'r', cell: 9, gap: 1, highlight: 'none', hiRow: 9, hiCol: 17, axes: false, scale: 1.2, dim: true,
})

const mL = computed(() => (props.axes ? 26 : 0))
const mT = computed(() => (props.axes ? 18 : 0))
const W = computed(() => mL.value + H * props.cell)
const Hh = computed(() => mT.value + D * props.cell)

function isHi(d: number, h: number) {
  switch (props.highlight) {
    case 'row': return d === props.hiRow
    case 'col': return h === props.hiCol
    case 'cell': return d === props.hiRow && h === props.hiCol
    case 'rowcol': return d === props.hiRow || h === props.hiCol
    case 'all': return true
    default: return true
  }
}
const cells = computed(() => {
  const out: { x: number; y: number; f: string; o: number }[] = []
  for (let d = 0; d < D; d++)
    for (let h = 0; h < H; h++)
      out.push({
        x: mL.value + h * props.cell,
        y: mT.value + d * props.cell,
        f: diverging(value(props.mode, d, h), props.scale),
        o: props.highlight === 'none' || !props.dim || isHi(d, h) ? 1 : 0.18,
      })
  return out
})
const sw = computed(() => props.cell - props.gap)
</script>

<template>
  <svg :width="W" :height="Hh" :viewBox="`0 0 ${W} ${Hh}`" class="rg">
    <g v-if="axes" class="ax">
      <text :x="mL + (H * cell) / 2" y="11" text-anchor="middle">時間帯 0 → 23</text>
      <text :x="9" :y="mT + (D * cell) / 2" text-anchor="middle" :transform="`rotate(-90 9 ${mT + (D * cell) / 2})`">日 1 → 28</text>
    </g>
    <rect v-for="(c, i) in cells" :key="i" :x="c.x" :y="c.y" :width="sw" :height="sw" :fill="c.f" :opacity="c.o" rx="1" />
    <g v-if="highlight === 'row' || highlight === 'rowcol'">
      <rect :x="mL - 1" :y="mT + hiRow * cell - 1" :width="H * cell + 1" :height="cell + 1" fill="none" stroke="#eb6834" stroke-width="2.5" rx="2" />
    </g>
    <g v-if="highlight === 'col' || highlight === 'rowcol'">
      <rect :x="mL + hiCol * cell - 1" :y="mT - 1" :width="cell + 1" :height="D * cell + 1" fill="none" stroke="#6250d6" stroke-width="2.5" rx="2" />
    </g>
    <g v-if="highlight === 'cell'">
      <rect :x="mL + hiCol * cell - 2" :y="mT + hiRow * cell - 2" :width="cell + 3" :height="cell + 3" fill="none" stroke="#008300" stroke-width="3" rx="2" />
    </g>
  </svg>
</template>

<style scoped>
.ax text { font-size: 10px; fill: #6b6b6b; }
</style>
