<template>
  <div class="page-fade max-w-6xl mx-auto">
    <h2 class="text-2xl font-bold text-morandi-text mb-2">营养分析</h2>
    <p class="text-sm text-morandi-lightText mb-6">汇总所选日期的饮食记录，与你的基础代谢/推荐摄入量对比。</p>

    <!-- 日期选择 -->
    <div class="glass rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-3">
      <label class="text-sm text-morandi-text">分析日期：</label>
      <input v-model="analyzeDate" type="date" class="px-3 py-1.5 rounded-lg border border-morandi-soft bg-white text-morandi-text" />
      <button @click="loadAnalysis" class="px-4 py-2 rounded-lg bg-morandi-accent text-white text-sm">刷新</button>
      <span v-if="errorMsg" class="text-xs text-red-500 ml-3">{{ errorMsg }}</span>
      <span v-if="analyzeDate" class="text-xs text-morandi-lightText ml-auto">当前对象：{{ operateAsLabel }}</span>
    </div>

    <div v-if="loading" class="text-center text-sm text-morandi-lightText py-16">加载中...</div>

    <template v-else-if="analysis">
      <!-- 顶部：热量 / BMR / 推荐 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="glass rounded-2xl p-5">
          <p class="text-xs text-morandi-lightText">今日摄入热量</p>
          <p class="text-3xl font-bold text-morandi-accent mt-2">{{ totalCalorie }} <span class="text-sm font-normal text-morandi-text">kcal</span></p>
          <p class="text-xs text-morandi-lightText mt-2">基础代谢 (BMR)：{{ bmr }} kcal</p>
          <p class="text-xs text-morandi-lightText">推荐：{{ recommendCalorieMin }} ~ {{ recommendCalorieMax }} kcal</p>
        </div>
        <div class="glass rounded-2xl p-5">
          <p class="text-xs text-morandi-lightText">摄入 / 推荐</p>
          <div class="mt-3">
            <div class="w-full h-3 rounded-full bg-morandi-soft overflow-hidden">
              <div class="h-full bg-morandi-accent transition-all" :style="{ width: calorieRatioPct + '%' }"></div>
            </div>
            <p class="text-xs text-morandi-text mt-2">
              已达推荐的 <b>{{ calorieRatioPct }}%</b> —
              <span v-if="calorieStatus === 'low'" class="text-orange-500">摄入偏少</span>
              <span v-else-if="calorieStatus === 'high'" class="text-red-500">摄入超标</span>
              <span v-else class="text-morandi-accent">基本合适</span>
            </p>
          </div>
        </div>
        <div class="glass rounded-2xl p-5">
          <p class="text-xs text-morandi-lightText">身体概况</p>
          <p class="text-sm text-morandi-text mt-2">身高：{{ userProfile.height ?? '-' }} cm · 体重：{{ userProfile.weight ?? '-' }} kg</p>
          <p class="text-sm text-morandi-text">年龄：{{ userProfile.age ?? '-' }} 岁 · {{ userProfile.gender ?? '-' }}</p>
          <p class="text-sm text-morandi-text">人群：<b>{{ userProfile.crowdType || '普通人' }}</b></p>
        </div>
      </div>

      <!-- 三大营养素热量占比 饼图 + 克数 -->
      <div class="glass rounded-2xl p-6 mb-6">
        <h3 class="text-lg font-semibold text-morandi-text mb-4">三大营养素</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
          <div class="flex flex-col items-center">
            <p class="text-xs text-morandi-lightText mb-2">热量来源比例 (kcal)</p>
            <div ref="macroChartRef" class="w-64 h-64"></div>
            <div class="flex flex-wrap gap-4 justify-center mt-3 text-xs text-morandi-text">
              <div class="flex items-center gap-1"><span class="inline-block w-3 h-3 rounded" style="background:#4a90d9"></span>蛋白质 {{ macroPcts.protein }}%</div>
              <div class="flex items-center gap-1"><span class="inline-block w-3 h-3 rounded" style="background:#e6b74b"></span>脂肪 {{ macroPcts.fat }}%</div>
              <div class="flex items-center gap-1"><span class="inline-block w-3 h-3 rounded" style="background:#5ba87a"></span>碳水 {{ macroPcts.carb }}%</div>
            </div>
          </div>
          <div class="space-y-4">
            <div v-for="(row, i) in macroRows" :key="i" class="rounded-xl bg-white/60 p-4">
              <div class="flex justify-between items-center">
              <p class="font-medium text-morandi-text">{{ row.name }}</p>
              <p class="text-sm font-semibold" :style="{ color: row.color }">{{ row.grams.toFixed(1) }} g / {{ row.kcal.toFixed(0) }} kcal</p>
              </div>
              <p class="text-xs text-morandi-lightText mt-1">
                每 kg 体重 {{ row.perKg.toFixed(2) }} g · 推荐 {{ row.recMin.toFixed(1) }}~{{ row.recMax.toFixed(1) }} g ({{ row.perKgRec[0].toFixed(2) }}~{{ row.perKgRec[1].toFixed(2) }} g/kg)
              </p>
              <div class="w-full h-2 rounded-full bg-morandi-soft mt-2 overflow-hidden">
                <div class="h-full" :style="{ width: row.ratioPct + '%', background: row.color }"></div>
              </div>
              <p class="text-xs mt-2" v-if="row.lowTip" :class="row.status === 'normal' ? 'text-morandi-accent' : (row.status === 'low' ? 'text-orange-500' : 'text-red-500')">
                <b v-if="row.status === 'low'">摄入偏少：</b>
                <b v-else-if="row.status === 'high'">摄入偏多：</b>
                <b v-else>摄入合适：</b>
                <span v-if="row.status === 'low'">{{ row.lowTip }}</span>
                <span v-else-if="row.status === 'high'">{{ row.highTip }}</span>
                <span v-else>比例合理，继续保持</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- 微量元素 -->
      <div class="glass rounded-2xl p-6 mb-6">
        <h3 class="text-lg font-semibold text-morandi-text mb-4">微量元素摄入</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="(m, i) in microRows" :key="i" class="rounded-xl bg-white/60 p-4">
            <div class="flex justify-between items-center">
              <p class="font-medium text-morandi-text">{{ m.name }}</p>
              <p class="text-sm font-semibold text-morandi-accent">{{ m.grams.toFixed(1) }} {{ m.unit }}</p>
            </div>
            <p class="text-xs text-morandi-lightText mt-1">推荐：{{ m.recMin.toFixed(0) }} ~ {{ m.recMax.toFixed(0) }} {{ m.unit }}</p>
            <div class="w-full h-2 rounded-full bg-morandi-soft mt-2 overflow-hidden">
              <div class="h-full bg-morandi-accent" :style="{ width: Math.min(m.ratioPct, 200) + '%' }"></div>
            </div>
            <p class="text-xs mt-2" :class="m.status === 'normal' ? 'text-morandi-accent' : (m.status === 'low' ? 'text-orange-500' : 'text-red-500')">
              <b v-if="m.status === 'low'">摄入不足：</b>
              <b v-else-if="m.status === 'high'">摄入偏高：</b>
              <b v-else>摄入合适：</b>
              <span v-if="m.status === 'low'">{{ m.lowTip }}</span>
              <span v-else-if="m.status === 'high'">{{ m.highTip }}</span>
              <span v-else>摄入量合适</span>
            </p>
          </div>
        </div>
        <p class="text-xs text-morandi-lightText mt-3">注：推荐范围会根据 <b>{{ userProfile.crowdType || '普通人' }}</b> 人群参考值有所不同，仅供健康参考，不作为临床诊断。</p>
      </div>

      <!-- 警告 & 建议 -->
      <div class="glass rounded-2xl p-6 mb-6">
        <h3 class="text-lg font-semibold text-morandi-text mb-3">系统建议</h3>
        <ul class="list-disc list-inside space-y-2 text-sm text-morandi-text">
          <li v-for="(val, key) in analysis.warnings" :key="key">
            <b>{{ nutrientLabel(key as string) }}</b>：{{ val || '正常' }}
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import echarts from '@/utils/echarts'
import type { ECharts } from '@/utils/echarts'
import { useUserStore } from '@/stores/user'
import { useDietStore } from '@/stores/diet'
import { api } from '@/api'

const userStore = useUserStore()
const dietStore = useDietStore()

const today = new Date().toISOString().slice(0, 10)
const analyzeDate = ref(today)
const loading = ref(false)
const errorMsg = ref('')
const analysis = ref<any>(null)

// ECharts 饼图
const macroChartRef = ref<HTMLDivElement | null>(null)
let macroChart: ECharts | null = null
let resizeHandler: (() => void) | null = null

function renderMacroChart() {
  if (!macroChartRef.value) return
  if (!macroChart) {
    macroChart = echarts.init(macroChartRef.value)
  }
  macroChart.setOption({
    legend: { top: 'bottom' },
    toolbox: {
      show: true,
      feature: {
        mark: { show: true },
        dataView: { show: true, readOnly: false },
        restore: { show: true },
        saveAsImage: { show: true }
      }
    },
    series: [
      {
        name: '营养素占比',
        type: 'pie',
        radius: ['25%', '55%'],
        center: ['50%', '45%'],
        roseType: 'area',
        itemStyle: { borderRadius: 6 },
        label: { fontSize: 11 },
        data: [
          { value: Math.round(proteinKcal.value || 0), name: '蛋白质', itemStyle: { color: '#4a90d9' } },
          { value: Math.round(fatKcal.value || 0), name: '脂肪', itemStyle: { color: '#e6b74b' } },
          { value: Math.round(carbKcal.value || 0), name: '碳水化合物', itemStyle: { color: '#5ba87a' } }
        ]
      }
    ]
  }, true)
}

function disposeMacroChart() {
  if (macroChart) {
    macroChart.dispose()
    macroChart = null
  }
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    resizeHandler = null
  }
}

const operateAsLabel = computed(() => {
  if (userStore.actAsUserId != null) return `亲属 #${userStore.actAsUserId}`
  return userStore.user?.username || '本人'
})

function asNumber(v: any, fallback = 0): number {
  const n = Number(v)
  return Number.isFinite(n) ? n : fallback
}

const totalCalorie = computed(() => asNumber(analysis.value?.total?.calorie))
const bmr = computed(() => asNumber(analysis.value?.user?.bmr))
const recommendCalorieMin = computed(() => Math.round(asNumber(analysis.value?.user?.recommendCalorieMin, bmr.value * 1.2)))
const recommendCalorieMax = computed(() => Math.round(asNumber(analysis.value?.user?.recommendCalorieMax, bmr.value * 1.5)))
const userProfile = computed(() => analysis.value?.user || {})

const calorieRatioPct = computed(() => {
  const mid = (recommendCalorieMin.value + recommendCalorieMax.value) / 2 || 1
  return Math.round((totalCalorie.value / mid) * 100)
})
const calorieStatus = computed(() => {
  if (calorieRatioPct.value < 80) return 'low'
  if (calorieRatioPct.value > 120) return 'high'
  return 'normal'
})

// 三大营养素克数 -> 热量
const proteinG = computed(() => asNumber(analysis.value?.total?.protein))
const fatG = computed(() => asNumber(analysis.value?.total?.fat))
const carbG = computed(() => asNumber(analysis.value?.total?.carb))
const proteinKcal = computed(() => Math.round(proteinG.value * 4))
const fatKcal = computed(() => Math.round(fatG.value * 9))
const carbKcal = computed(() => Math.round(carbG.value * 4))
const macroSumKcal = computed(() => proteinKcal.value + fatKcal.value + carbKcal.value)

const macroPcts = computed(() => {
  const total = macroSumKcal.value || 1
  return {
    protein: Math.round((proteinKcal.value / total) * 100),
    fat: Math.round((fatKcal.value / total) * 100),
    carb: Math.round((carbKcal.value / total) * 100)
  }
})

// ECharts 饼图数据刷新：数据变化后等到 DOM 可再渲染
function scheduleRender() {
  nextTick(() => {
    renderMacroChart()
  })
}

const macroRows = computed(() => {
  const recs: any = analysis.value?.recommendations || {}
  const w = asNumber(analysis.value?.user?.weight, 0) || 65
  type MacroRow = {
    name: string; grams: number; kcal: number; perKg: number;
    recMin: number; recMax: number; perKgRec: number[];
    ratioPct: number; status: string; color: string;
    lowTip: string; highTip: string
  }
  const build = (name: string, grams: number, kcal: number, perKgFromRec: number[] | undefined, ideal: number[], color: string, lowTip: string, highTip: string): MacroRow => {
    const minPerKg = perKgFromRec?.[0] ?? ideal[0]
    const maxPerKg = perKgFromRec?.[1] ?? ideal[1]
    const recMin = minPerKg * w
    const recMax = maxPerKg * w
    const perKg = grams / w
    const mid = (recMin + recMax) / 2 || 1
    const ratioPct = Math.max(0, Math.round((grams / mid) * 100))
    let status = 'normal'
    if (ratioPct < 80) status = 'low'
    else if (ratioPct > 120) status = 'high'
    return { name, grams, kcal, perKg, recMin, recMax, perKgRec: [minPerKg, maxPerKg], ratioPct, status, color, lowTip, highTip }
  }
  const proteinPerKg = typeof recs.proteinPerKg === 'object' && recs.proteinPerKg ? recs.proteinPerKg : undefined
  const fatPerKg = typeof recs.fatPerKg === 'object' && recs.fatPerKg ? recs.fatPerKg : undefined
  const carbPerKg = typeof recs.carbPerKg === 'object' && recs.carbPerKg ? recs.carbPerKg : undefined
  return [
    build('蛋白质', proteinG.value, proteinKcal.value, proteinPerKg, [1.0, 1.2], '#4a90d9',
      '优质来源不足会导致肌肉流失、免疫力下降、运动恢复差',
      '蛋白质过量会加重肾脏负担、可能诱发痛风、热量容易超标'),
    build('脂肪', fatG.value, fatKcal.value, fatPerKg, [0.8, 1.0], '#e6b74b',
      '脂肪摄入不足会影响脂溶性维生素吸收、激素合成原料缺失',
      '脂肪摄入超标会导致热量爆炸、高血脂、心血管负担增加'),
    build('碳水化合物', carbG.value, carbKcal.value, carbPerKg, [3.0, 4.0], '#5ba87a',
      '碳水摄入不足会导致大脑供能不足、头晕、运动无力、肌肉分解',
      '碳水摄入超标会引起血糖波动、胰岛素抵抗、内脏脂肪堆积')
  ]
})

const microRows = computed(() => {
  const total: any = analysis.value?.total || {}
  const recs: any = analysis.value?.recommendations || {}
  const statusMap: any = analysis.value?.status || {}
  const warnings: any = analysis.value?.warnings || {}
  const items = [
    { key: 'dietFiber', name: '膳食纤维', unit: 'g' },
    { key: 'calcium', name: '钙', unit: 'mg' },
    { key: 'dha', name: 'DHA', unit: 'mg' },
    { key: 'folicAcid', name: '叶酸', unit: 'μg' }
  ]
  return items.map((it) => {
    const grams = asNumber(total[it.key])
    // 推荐范围来自后端 recommendations（按人群不同而不同），不再硬编码 0
    const recMin = asNumber(recs[it.key + 'Min'])
    const recMax = asNumber(recs[it.key + 'Max'])
    const mid = (recMin + recMax) / 2 || 1
    const ratioPct = Math.max(0, Math.round((grams / mid) * 100))
    // 状态优先取后端 status 计算结果，兼容旧后端无 status 时按比例兜底
    const status: string = statusMap[it.key] || (ratioPct < 80 ? 'low' : ratioPct > 120 ? 'high' : 'normal')
    const tip = warnings[it.key] || ''
    return {
      name: it.name, grams, unit: it.unit,
      recMin, recMax, ratioPct, status,
      lowTip: tip, highTip: tip
    }
  })
})

function nutrientLabel(key: string) {
  const map: Record<string, string> = {
    protein: '蛋白质', fat: '脂肪', carb: '碳水化合物',
    calcium: '钙', folicAcid: '叶酸', dietFiber: '膳食纤维', dha: 'DHA',
    calorie: '热量'
  }
  return map[key] || key
}

async function loadAnalysis() {
  loading.value = true
  errorMsg.value = ''
  try {
    // 先从 store 拉取当日饮食，再调用营养分析
    await dietStore.fetchTodayMeals(analyzeDate.value)
    const data: any = await api.diet.analyze(analyzeDate.value)
    if (data && (data.total || data.user)) {
      analysis.value = data
    } else {
      errorMsg.value = '暂无该日期的营养分析数据'
      analysis.value = null
    }
    scheduleRender()
  } catch (e: any) {
    console.warn('营养分析API不可用', e)
    errorMsg.value = '营养分析暂不可用'
    analysis.value = null
  } finally {
    loading.value = false
  }
}

function loadMockAnalysis() {
  // 已移除 mock 数据，API 失败时显示错误提示
}

watch(analysis, () => {
  if (analysis.value) scheduleRender()
})

onMounted(async () => {
  try { await userStore.init() } catch { /* ignore */ }
  loadAnalysis()
  if (!resizeHandler) {
    resizeHandler = () => macroChart?.resize()
    window.addEventListener('resize', resizeHandler)
  }
})

onBeforeUnmount(() => {
  disposeMacroChart()
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
.page-fade { animation: fadeIn 0.3s ease forwards; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
