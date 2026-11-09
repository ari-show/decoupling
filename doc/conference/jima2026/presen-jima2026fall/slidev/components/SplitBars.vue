<script setup lang="ts">
// 同じ合計を異なる内訳で表せる、を 2 本の積み上げ棒で示す
</script>

<template>
  <div class="sb">
    <svg viewBox="0 0 300 120" class="sbsvg">
      <text x="40" y="14" class="t2">内訳 A</text>
      <rect x="40" y="20" width="60" height="22" fill="#6b6b6b" rx="3" />
      <text x="70" y="35" class="tw" text-anchor="middle">全期間 2</text>
      <rect x="102" y="20" width="30" height="22" fill="#eb6834" rx="3" />
      <text x="117" y="35" class="tw" text-anchor="middle">日 1</text>
      <text x="156" y="36" class="t1" text-anchor="middle">=</text>
      <text x="180" y="14" class="t2">内訳 B</text>
      <rect x="180" y="20" width="30" height="22" fill="#6b6b6b" rx="3" />
      <text x="195" y="35" class="tw" text-anchor="middle">1</text>
      <rect x="212" y="20" width="60" height="22" fill="#eb6834" rx="3" />
      <text x="242" y="35" class="tw" text-anchor="middle">日 2</text>
      <rect x="40" y="62" width="232" height="22" fill="#f1f1ee" stroke="#0b0b0b" rx="3" />
      <text x="156" y="77" class="t2" text-anchor="middle" fill="#0b0b0b">合計の補正量はどちらも 3</text>
      <text x="156" y="108" class="tr" text-anchor="middle">成分間で値を移しても合計は変わらない</text>
    </svg>
  </div>
</template>

<style scoped>
.sb { width: 300px; }
.sbsvg { width: 100%; height: auto; display: block; }
.t1 { font-size: 14px; fill: #0b0b0b; }
.t2 { font-size: 11px; fill: #52514e; }
.tw { font-size: 11px; fill: #fff; }
.tr { font-size: 12px; fill: #b4231f; font-weight: 700; }
</style>
