<script setup lang="ts">
// 中心化制約：どの方向の平均を 0 にするか
import { COMP } from '../src/synth'
withDefaults(defineProps<{ stage?: number }>(), { stage: 3 })
</script>

<template>
  <div class="ccf">
    <div class="panel" :class="{ off: stage < 1 }">
      <div class="name" :style="{ color: COMP.a }">日成分 <span class="f">a<sub>i,d</sub></span></div>
      <div class="fig">
        <div class="frame" :style="{ borderColor: COMP.a }"><ResidualGrid mode="a" :cell="5" /></div>
        <svg width="70" height="140" viewBox="0 0 70 140" class="arr">
          <path d="M14,6 v128" :stroke="COMP.a" stroke-width="3" />
          <path d="M8,124 L14,134 L20,124" fill="none" :stroke="COMP.a" stroke-width="3" />
          <text x="28" y="66" class="t" :fill="COMP.a">日方向の</text>
          <text x="28" y="82" class="t" :fill="COMP.a">平均 = 0</text>
        </svg>
      </div>
      <div class="eq">Σ<sub>d</sub> a<sub>i,d</sub> = 0</div>
    </div>

    <div class="panel" :class="{ off: stage < 2 }">
      <div class="name" :style="{ color: COMP.t }">時間帯成分 <span class="f">t<sub>i,h</sub></span></div>
      <div class="fig col">
        <div class="frame" :style="{ borderColor: COMP.t }"><ResidualGrid mode="t" :cell="5" /></div>
        <svg width="140" height="40" viewBox="0 0 140 40" class="arr">
          <path d="M6,12 h128" :stroke="COMP.t" stroke-width="3" />
          <path d="M124,6 L134,12 L124,18" fill="none" :stroke="COMP.t" stroke-width="3" />
          <text x="70" y="34" class="t" text-anchor="middle" :fill="COMP.t">時間帯方向の平均 = 0</text>
        </svg>
      </div>
      <div class="eq">Σ<sub>h</sub> t<sub>i,h</sub> = 0</div>
    </div>

    <div class="panel" :class="{ off: stage < 3 }">
      <div class="name" :style="{ color: COMP.u }">交互作用成分 <span class="f">u<sub>i,d,h</sub></span></div>
      <div class="fig">
        <div class="col">
          <div class="frame" :style="{ borderColor: COMP.u }"><ResidualGrid mode="u" :cell="5" /></div>
          <svg width="130" height="34" viewBox="0 0 130 34" class="arr">
            <path d="M6,10 h118" :stroke="COMP.u" stroke-width="3" /><path d="M114,4 L124,10 L114,16" fill="none" :stroke="COMP.u" stroke-width="3" />
            <text x="65" y="30" class="t" text-anchor="middle" :fill="COMP.u">各日で平均 = 0</text>
          </svg>
        </div>
        <svg width="70" height="140" viewBox="0 0 70 140" class="arr">
          <path d="M14,6 v128" :stroke="COMP.u" stroke-width="3" /><path d="M8,124 L14,134 L20,124" fill="none" :stroke="COMP.u" stroke-width="3" />
          <text x="26" y="60" class="t" :fill="COMP.u">各時間帯で</text>
          <text x="26" y="76" class="t" :fill="COMP.u">平均 = 0</text>
        </svg>
      </div>
      <div class="eq">Σ<sub>d</sub> u = 0 (∀h),&nbsp; Σ<sub>h</sub> u = 0 (∀d)</div>
    </div>
  </div>
</template>

<style scoped>
.ccf { display: flex; justify-content: center; gap: 28px; align-items: flex-start; }
.panel { display: flex; flex-direction: column; align-items: center; gap: 6px; transition: opacity .4s; }
.panel.off { opacity: 0.1; }
.name { font-weight: 700; font-size: 15px; }
.f { font-family: KaTeX_Math, serif; font-style: italic; font-weight: 400; color: #0b0b0b; }
.fig { display: flex; align-items: flex-start; gap: 4px; }
.col { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.frame { border: 2.5px solid; border-radius: 4px; padding: 2px; line-height: 0; }
.t { font-size: 11px; font-weight: 700; }
.eq { font-size: 13px; color: #0b0b0b; background: #fff3f2; border: 1.5px dashed #b4231f; border-radius: 6px; padding: 2px 10px; }
</style>
