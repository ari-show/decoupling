<script setup lang="ts">
// 加法分解の非一意性：成分間で値を「移して」も合計（残差）は変わらない
import { COMP } from '../src/synth'
withDefaults(defineProps<{ stage?: number }>(), { stage: 3 })
const target = [1, 2, 3]
const decomps = [
  { g: 2, a: [-1, 0, 1], label: '内訳 A', mean: 0 },
  { g: 0, a: [1, 2, 3], label: '内訳 B', mean: 2 },
  { g: 5, a: [-4, -3, -2], label: '内訳 C', mean: -3 },
]
const shifts = [
  'A → B：全期間から 2 を取り、各日に +2 ずつ移す',
  'A → C：各日から 3 ずつ取り、全期間に +3 移す',
]
const fmt = (v: number) => (v > 0 ? `+${v}` : v === 0 ? '0' : `−${-v}`)
</script>

<template>
  <div class="idf">
    <div class="row head">
      <div class="lbl"></div>
      <div class="tile g" style="opacity:0;border-color:transparent"></div>
      <div class="plus" style="opacity:0">+</div>
      <div class="tiles"><div class="th" v-for="d in 3" :key="d">{{ d }}日目</div></div>
      <div class="eq" style="opacity:0">=</div>
      <div class="tiles"><div class="th" v-for="d in 3" :key="d">{{ d }}日目</div></div>
      <div class="mean th" :style="{ color: COMP.a }">日成分の平均</div>
    </div>
    <template v-for="(dc, i) in decomps" :key="i">
      <div v-if="i > 0" class="shift" :class="{ off: stage < i + 1, lose: stage >= 4 }" :style="{ color: COMP.a }">
        <span class="sa">↓</span>{{ shifts[i - 1] }}<span class="same">→ 残差は変わらない</span>
      </div>
      <div class="row" :class="{ off: stage < i + 1, win: stage >= 4 && i === 0, lose: stage >= 4 && i !== 0 }">
        <div class="lbl">{{ dc.label }}</div>
        <div class="tile g" :style="{ borderColor: COMP.g }">
          <span class="k" :style="{ color: COMP.g }">全期間</span>{{ fmt(dc.g) }}
        </div>
        <div class="plus">+</div>
        <div class="tiles">
          <div class="tile a" v-for="(v, d) in dc.a" :key="d" :style="{ borderColor: COMP.a }">
            <span class="k" :style="{ color: COMP.a }">日</span>{{ fmt(v) }}
          </div>
        </div>
        <div class="eq">=</div>
        <div class="tiles">
          <div class="tile r" v-for="(v, d) in target" :key="d"><span class="k">残差</span>{{ fmt(v) }}</div>
        </div>
        <div class="mean">
          <div class="mv" :style="{ color: COMP.a, borderColor: COMP.a }">{{ fmt(dc.mean) }}</div>
          <div v-if="stage >= 4" class="chk" :class="dc.mean === 0 ? 'ok' : 'ng'">{{ dc.mean === 0 ? '✓ 制約を満たす' : '✗ 除外' }}</div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.idf { display: flex; flex-direction: column; gap: 6px; align-items: center; }
.row { display: flex; align-items: center; gap: 10px; transition: opacity .4s, transform .4s; }
.row.off, .shift.off { opacity: 0.1; }
.row.lose { opacity: 0.3; }
.shift.lose { opacity: 0.35; }
.row.win { transform: scale(1.03); }
.lbl { width: 70px; font-weight: 700; font-size: 15px; }
.tiles { display: flex; gap: 6px; }
.tile { width: 62px; height: 46px; border: 2.5px solid #0b0b0b; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 19px; font-weight: 700; background: #fff; line-height: 1; }
.tile.r { background: #f1f1ee; }
.k { font-size: 10px; font-weight: 600; margin-bottom: 3px; color: #52514e; }
.th { width: 62px; text-align: center; font-size: 11px; color: #52514e; }
.plus, .eq { font-size: 24px; color: #52514e; width: 20px; text-align: center; }
.mean { width: 120px; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.mean.th { width: 120px; font-weight: 700; }
.mv { width: 52px; height: 30px; border: 2px dashed; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 17px; font-weight: 700; background: #fff; }
.chk { font-size: 11px; font-weight: 700; }
.chk.ok { color: #b4231f; }
.chk.ng { color: #9a9a9a; }
.shift { font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px; transition: opacity .4s; margin-left: 80px; align-self: flex-start; }
.sa { font-size: 15px; }
.same { color: #52514e; font-weight: 400; margin-left: 4px; }
</style>
