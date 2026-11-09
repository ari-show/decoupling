<script setup lang="ts">
// 背景3枚を貫く進行バー。step が現在地（1始まり）
withDefaults(defineProps<{ step?: number }>(), { step: 1 })
const items = [
  '経営判断 ← 予測 ← 販売実績',
  '日次ではなく時間帯の「形」',
  '水準を分けて残差を見る',
  '日・時間帯のずれを別々に学習',
]
</script>

<template>
  <div class="story">
    <template v-for="(it, i) in items" :key="i">
      <span class="chip" :class="{ now: i + 1 === step, done: i + 1 < step }">{{ i + 1 }}. {{ it }}</span>
      <span v-if="i < items.length - 1" class="sep">›</span>
    </template>
  </div>
</template>

<style scoped>
.story {
  position: absolute; left: 2.4rem; right: 2.4rem; bottom: 0.5rem;
  display: flex; align-items: center; justify-content: center; gap: 0.35rem;
  font-size: 0.7rem; color: #9a9a9a;
}
.chip { padding: 0.05rem 0.55rem; border-radius: 999px; border: 1px solid #d9d9d4; background: #fff; white-space: nowrap; transition: all .3s; }
.chip.done { color: #52514e; border-color: #b8b8b2; }
.chip.now { background: #6250d6; border-color: #6250d6; color: #fff; font-weight: 700; }
.sep { color: #b8b8b2; }
</style>
