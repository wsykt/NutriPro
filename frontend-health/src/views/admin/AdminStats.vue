<template>
  <div class="space-y-6">
    <div class="glass rounded-2xl p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-morandi-text">用户人群分布</h3>
        <span class="text-xs text-morandi-lightText">总用户数：{{ crowdStats.total }}</span>
      </div>

      <div v-if="statsLoading" class="text-center text-sm text-morandi-lightText py-16">加载中...</div>

      <div v-else-if="crowdStats.data && crowdStats.data.length > 0" class="flex flex-col md:flex-row items-center gap-6">
        <div ref="pieChartRef" class="w-full md:w-1/2" style="min-height: 360px"></div>
        <div class="w-full md:w-1/2 space-y-3">
          <div
            v-for="(item, idx) in crowdStats.data"
            :key="item.name"
            class="flex items-center justify-between p-3 bg-white rounded-xl border border-morandi-soft"
          >
            <div class="flex items-center gap-3">
              <span class="w-4 h-4 rounded-full" :style="{ background: pieColors[(idx as number) % pieColors.length] }"></span>
              <span class="text-sm font-medium text-morandi-text">{{ item.name }}</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-sm text-morandi-lightText">{{ percent(item.value, crowdStats.total) }}%</span>
              <span class="text-sm font-semibold text-morandi-accent">{{ item.value }} 人</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center text-sm text-morandi-lightText py-16">暂无统计数据</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted, onBeforeUnmount } from 'vue'
import echarts from '@/utils/echarts'
import { api } from '@/api'

// ============== 统计数据 ==============
const statsLoading = ref(false)
const pieChartRef = ref<HTMLElement | null>(null)
const crowdStats = reactive<any>({ total: 0, data: [] })
let pieChartInstance: any = null

const pieColors = ['#8b7355', '#a68465', '#c9a66b', '#d9b38c', '#e6cfa7', '#8fbc8f', '#5d9b9b', '#9b7c5d']

const loadStats = async () => {
  statsLoading.value = true
  try {
    const data = await api.admin.getCrowdTypeStats()
    crowdStats.total = data.total || 0
    crowdStats.data = data.data || []
    await nextTick()
    renderPieChart()
  } catch (e) {
    console.warn('加载统计数据失败', e)
  } finally {
    statsLoading.value = false
  }
}

const renderPieChart = () => {
  if (!pieChartRef.value) return
  if (pieChartInstance) pieChartInstance.dispose()
  pieChartInstance = echarts.init(pieChartRef.value)
  const colors = ['#c0392b', '#e67e22', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6', '#1abc9c', '#e74c3c']
  pieChartInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 人 ({d}%)' },
    legend: { top: 'bottom' },
    series: [
      {
        name: '人群分布',
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['50%', '45%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
        label: { show: true, formatter: '{b}\n{d}%', fontSize: 11, color: '#5d4f3f' },
        labelLine: { length: 10, length2: 8 },
        data: crowdStats.data.map((d: any, i: number) => ({
          name: d.name,
          value: d.value,
          itemStyle: { color: colors[i % colors.length] }
        }))
      }
    ]
  })
  setTimeout(() => pieChartInstance && pieChartInstance.resize(), 100)
}

// ============== 工具函数 ==============
const percent = (val: number, total: number) => {
  if (!total) return '0.0'
  return ((val / total) * 100).toFixed(1)
}

// ============== resize 监听 ==============
const onResize = () => {
  if (pieChartInstance) pieChartInstance.resize()
}

// ============== 初始化与清理 ==============
onMounted(() => {
  loadStats()
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', onResize)
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', onResize)
  }
  if (pieChartInstance) {
    pieChartInstance.dispose()
    pieChartInstance = null
  }
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.08);
}
</style>
