<script setup lang="ts">
// r = g + a + t + u を 5 枚のグリッドで示す
import { COMP, COMP_NAME } from '../src/synth'
withDefaults(defineProps<{ stage?: number; cell?: number; captions?: boolean; hl?: boolean }>(), { stage: 4, cell: 6, captions: true, hl: false })
const parts = [
  { k: 'g', share: '全期間で共通', hi: 'all', sym: '\\hat g_i' },
  { k: 'a', share: '同じ日 × 全時間帯', hi: 'row', sym: '\\hat a_{i,d}' },
  { k: 't', share: '全日 × 同じ時間帯', hi: 'col', sym: '\\hat t_{i,h}' },
  { k: 'u', share: '特定の日 × 時間帯', hi: 'cell', sym: '\\hat u_{i,d,h}' },
] as const
</script>

<template>
  <div class="df">
    <div class="item">
      <div class="name" style="color:#0b0b0b">残差 <span class="sym">r</span></div>
      <ResidualGrid mode="r" :cell="cell" />
      <div v-if="captions" class="cap">観測 − 基準値</div>
    </div>
    <template v-for="(p, i) in parts" :key="p.k">
      <div class="op" :class="{ off: stage < i + 1 }">{{ i === 0 ? '=' : '+' }}</div>
      <div class="item" :class="{ off: stage < i + 1 }">
        <div class="name" :style="{ color: COMP[p.k] }">{{ COMP_NAME[p.k] }}</div>
        <div class="frame" :style="{ borderColor: COMP[p.k] }">
          <ResidualGrid :mode="p.k" :cell="cell" :highlight="hl ? p.hi : 'none'" :dim="false" />
        </div>
        <div v-if="captions" class="cap">{{ p.share }}</div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.df { display: flex; align-items: center; justify-content: center; gap: 10px; }
.item { display: flex; flex-direction: column; align-items: center; gap: 4px; transition: opacity .4s; }
.frame { border: 2.5px solid; border-radius: 4px; padding: 2px; line-height: 0; }
.name { font-weight: 700; font-size: 14px; }
.sym { font-family: KaTeX_Math, serif; font-style: italic; }
.cap { font-size: 12px; color: #52514e; }
.op { font-size: 28px; color: #52514e; transition: opacity .4s; }
.off { opacity: 0.12; }
</style>
