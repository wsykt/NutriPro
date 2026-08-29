<template>
  <div class="ad-card">
    <div class="ad-head">
      <h3 class="ad-h3">众相星图<span class="ad-h3-en">CROWD MAP</span></h3>
      <span class="ad-sub">总用户数：{{ crowdStats.total }}</span>
    </div>

    <div v-if="statsLoading" class="ad-empty">加载中...</div>

    <div v-else-if="crowdStats.data && crowdStats.data.length > 0" class="st-flex">
      <div ref="pieChartRef" class="st-chart"></div>
      <div class="st-list">
        <div
          v-for="(item, idx) in crowdStats.data"
          :key="item.name"
          class="st-row"
        >
          <div class="st-row-l">
            <span class="st-dot" :style="{ background: pieColors[(idx as number) % pieColors.length] }"></span>
            <span class="st-name">{{ item.name }}</span>
          </div>
          <div class="st-row-r">
            <span class="st-pct">{{ percent(item.value, crowdStats.total) }}%</span>
            <span class="st-val">{{ item.value }} 人</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="ad-empty">暂无统计数据</div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, inject, watch, nextTick, onMounted, onBeforeUnmount, type Ref } from 'vue'
import echarts from '@/utils/echarts'
import { api } from '@/api'

// ============== 昼夜模式（方案F） ==============
const adminMode = inject<Ref<'night' | 'day'>>('adminMode', ref<'night' | 'day'>('night'))

// ============== 统计数据 ==============
const statsLoading = ref(false)
const pieChartRef = ref<HTMLElement | null>(null)
const crowdStats = reactive<any>({ total: 0, data: [] })
let pieChartInstance: any = null

const pieColors = ['#B8863B', '#D9A24A', '#8a6d3b', '#C4553B', '#5d7052', '#e8c98c', '#a67c48', '#d98a76']

const loadStats = async () => {
  statsLoading.value = true
  try {
    const data = await api.admin.getCrowdTypeStats()
    crowdStats.total = data.total || 0
    crowdStats.data = data.data || []
    // 先结束 loading 让图表容器挂载，再渲染，否则 pieChartRef 为 null 会跳过绘制
    statsLoading.value = false
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
  const night = adminMode.value === 'night'
  const labelColor = night ? 'rgba(203, 191, 168, 0.92)' : '#55503f'
  const legendColor = night ? 'rgba(203, 191, 168, 0.6)' : '#847c63'
  const borderColor = night ? '#241b10' : '#fdfaf3'
  pieChartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 人 ({d}%)',
      backgroundColor: night ? 'rgba(32, 24, 15, 0.95)' : '#fdfaf3',
      borderColor: night ? 'rgba(217, 162, 74, 0.3)' : 'rgba(184, 134, 59, 0.4)',
      textStyle: { color: night ? '#f6ead6' : '#55503f', fontSize: 12 }
    },
    legend: { top: 'bottom', textStyle: { color: legendColor, fontSize: 11 } },
    series: [
      {
        name: '人群分布',
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['50%', '44%'],
        itemStyle: { borderRadius: 6, borderColor, borderWidth: 3 },
        label: { show: true, formatter: '{b}\n{d}%', fontSize: 11, color: labelColor },
        labelLine: { length: 10, length2: 8, lineStyle: { color: legendColor } },
        data: crowdStats.data.map((d: any, i: number) => ({
          name: d.name,
          value: d.value,
          itemStyle: { color: pieColors[i % pieColors.length] }
        }))
      }
    ]
  })
  setTimeout(() => pieChartInstance && pieChartInstance.resize(), 100)
}

// 昼夜切换时重绘图表
watch(adminMode, () => {
  if (!statsLoading.value && crowdStats.data.length) renderPieChart()
})

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
.st-flex { display: flex; flex-direction: column; align-items: center; gap: 20px; }
.st-chart { width: 100%; min-height: 360px; }
.st-list { width: 100%; display: flex; flex-direction: column; gap: 10px; }
.st-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 11px 15px; border-radius: 12px;
  border: 1px solid var(--ad-line); background: var(--ad-card-2);
  transition: background 0.3s;
}
.st-row:hover { background: var(--ad-hover); }
.st-row-l { display: flex; align-items: center; gap: 11px; }
.st-dot { width: 13px; height: 13px; border-radius: 50%; flex: none; box-shadow: 0 0 8px var(--ad-accent-soft); }
.st-name { font-size: 13px; font-weight: 600; color: var(--ad-title); }
.st-row-r { display: flex; align-items: center; gap: 12px; }
.st-pct { font-size: 12px; color: var(--ad-sub); }
.st-val { font-size: 13px; font-weight: 700; color: var(--ad-accent); }
@media (min-width: 860px) {
  .st-flex { flex-direction: row; }
  .st-chart, .st-list { width: 50%; }
}
</style>
