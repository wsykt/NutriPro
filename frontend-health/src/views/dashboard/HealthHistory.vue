<template>
  <div class="page-fade">
    <h2 class="text-2xl font-bold mb-2 text-morandi-text">历史健康记录</h2>
    <p class="text-morandi-lightText mb-6 text-sm">查看你的历史健康数据和趋势</p>

    <div class="glass rounded-2xl p-6 mb-6">
      <h3 class="font-semibold mb-4">健康数据概览</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-white/70 rounded-xl p-4 text-center">
          <p class="text-morandi-lightText text-xs mb-1">身高 (cm)</p>
          <p class="text-2xl font-bold text-morandi-accent">{{ userInfo.height || '—' }}</p>
        </div>
        <div class="bg-white/70 rounded-xl p-4 text-center">
          <p class="text-morandi-lightText text-xs mb-1">体重 (kg)</p>
          <p class="text-2xl font-bold text-morandi-accent">{{ userInfo.weight || '—' }}</p>
        </div>
        <div class="bg-white/70 rounded-xl p-4 text-center">
          <p class="text-morandi-lightText text-xs mb-1">BMI</p>
          <p class="text-2xl font-bold text-morandi-accent">{{ bmiText }}</p>
        </div>
        <div class="bg-white/70 rounded-xl p-4 text-center">
          <p class="text-morandi-lightText text-xs mb-1">记录总条数</p>
          <p class="text-2xl font-bold text-morandi-accent">{{ records.length }}</p>
        </div>
      </div>
    </div>

    <div class="glass rounded-2xl p-6">
      <h3 class="font-semibold mb-4">历史记录列表</h3>
      <div v-if="records.length === 0" class="text-morandi-lightText text-center py-8 text-sm">暂无历史记录</div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-morandi-lightText border-b border-morandi-soft">
              <th class="py-3 px-3">日期</th>
              <th class="py-3 px-3">类型</th>
              <th class="py-3 px-3">数值</th>
              <th class="py-3 px-3">备注</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, idx) in records" :key="idx" class="border-b border-morandi-soft/50 hover:bg-morandi-soft/40">
              <td class="py-3 px-3">{{ r.date }}</td>
              <td class="py-3 px-3">{{ r.type }}</td>
              <td class="py-3 px-3">{{ r.value }}</td>
              <td class="py-3 px-3 text-morandi-lightText">{{ r.remark || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const userInfo = computed<any>(() => userStore.user || {})

const bmiText = computed(() => {
  const h = Number(userInfo.value.height) / 100
  const w = Number(userInfo.value.weight)
  if (!h || !w) return '—'
  return (w / (h * h)).toFixed(2)
})

const records = ref<any[]>([
  { date: '2025-01-12', type: '身高', value: `${userInfo.value.height || 170} cm`, remark: '初始记录' },
  { date: '2025-01-12', type: '体重', value: `${userInfo.value.weight || 65} kg`, remark: '初始记录' }
])

onMounted(() => {
  userStore.init()
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.9);
}
.page-fade {
  animation: fadeIn 0.3s ease forwards;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
