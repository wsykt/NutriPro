<template>
  <div class="weekly-report-wrapper min-h-screen bg-gradient-to-b from-gray-50 to-white">
    <div class="flex justify-center gap-3 mb-6 pt-4">
      <button 
        @click="reportType = 'weekly'"
        class="px-6 py-2.5 rounded-xl font-medium text-sm transition-all duration-300 shadow-md"
        :class="reportType === 'weekly' ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg shadow-green-200' : 'bg-white text-gray-600 hover:bg-gray-100'"
      >
        <component :is="Calendar" class="w-4 h-4 inline mr-2" />周报
      </button>
      <button 
        @click="reportType = 'monthly'"
        class="px-6 py-2.5 rounded-xl font-medium text-sm transition-all duration-300 shadow-md"
        :class="reportType === 'monthly' ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg shadow-green-200' : 'bg-white text-gray-600 hover:bg-gray-100'"
      >
        <component :is="CalendarDays" class="w-4 h-4 inline mr-2" />月报
      </button>
    </div>
    
    <div class="max-w-4xl mx-auto px-4 pb-8">
      <div class="scroll-reveal-item" :class="{ 'is-visible': visibleSections >= 1 }">
        <div class="text-center py-6">
          <span class="inline-block px-4 py-1.5 bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 rounded-full text-xs font-semibold mb-3">
            {{ reportType === 'weekly' ? '本周健康报告' : '本月健康报告' }}
          </span>
          <h2 class="text-2xl font-bold text-gray-800">{{ userInfo.username }}的饮食&运动健康打卡</h2>
          <p class="text-gray-500 mt-2 text-sm">身高 {{ userInfo.height || '--' }} cm · 体重 {{ userInfo.weight || '--' }} kg · BMI {{ bmi || '--' }}</p>
        </div>
      </div>

      <div class="scroll-reveal-item" :class="{ 'is-visible': visibleSections >= 2 }">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div class="bg-gradient-to-br from-red-50 to-pink-50 rounded-xl p-4 border border-red-100">
            <div class="flex items-center gap-2 mb-2">
              <div class="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                <Heart class="w-4 h-4 text-red-500" />
              </div>
              <span class="text-gray-500 text-xs font-medium">{{ reportType === 'weekly' ? '本周' : '本月' }}打卡</span>
            </div>
            <p class="text-3xl font-bold text-gray-800">{{ reportData.checkinDays }}</p>
            <p class="text-green-600 text-xs mt-1 font-medium">{{ reportData.checkinTrend }}</p>
          </div>
          <div class="bg-gradient-to-br from-orange-50 to-amber-50 rounded-xl p-4 border border-orange-100">
            <div class="flex items-center gap-2 mb-2">
              <div class="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                <Flame class="w-4 h-4 text-orange-500" />
              </div>
              <span class="text-gray-500 text-xs font-medium">平均热量</span>
            </div>
            <p class="text-3xl font-bold text-gray-800">{{ reportData.avgCalories }}</p>
            <p class="text-green-600 text-xs mt-1 font-medium">{{ reportData.caloriesTrend }}</p>
          </div>
          <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100">
            <div class="flex items-center gap-2 mb-2">
              <div class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                <Leaf class="w-4 h-4 text-green-500" />
              </div>
              <span class="text-gray-500 text-xs font-medium">健康饮食</span>
            </div>
            <p class="text-3xl font-bold text-gray-800">{{ reportData.healthyDays }}</p>
            <p class="text-green-600 text-xs mt-1 font-medium">{{ reportData.healthyPercent }}%</p>
          </div>
          <div class="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4 border border-blue-100">
            <div class="flex items-center gap-2 mb-2">
              <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <Dumbbell class="w-4 h-4 text-blue-500" />
              </div>
              <span class="text-gray-500 text-xs font-medium">运动天数</span>
            </div>
            <p class="text-3xl font-bold text-gray-800">{{ reportData.exerciseDays }}</p>
            <p class="text-blue-600 text-xs mt-1 font-medium">{{ reportData.exerciseMinutes }}min/天</p>
          </div>
        </div>
      </div>

      <div class="scroll-reveal-item" :class="{ 'is-visible': visibleSections >= 3 }">
        <div class="mb-6">
          <HealthHeatmap :report-type="reportType" :year="currentYear" :month="currentMonth" />
        </div>
      </div>

      <div class="scroll-reveal-item" :class="{ 'is-visible': visibleSections >= 4 }">
        <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
          <div class="flex items-center gap-2 mb-3">
            <div class="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
              <Heart class="w-4 h-4 text-red-500" />
            </div>
            <span class="font-bold text-gray-800 text-sm">健康档案</span>
          </div>
          <div class="space-y-2.5">
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">姓名</span>
              <span class="text-gray-800 font-medium">{{ userInfo.username }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">年龄</span>
              <span class="text-gray-800 font-medium">{{ userInfo.age || '--' }}岁</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">身高</span>
              <span class="text-gray-800 font-medium">{{ userInfo.height || '--' }} cm</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">体重</span>
              <span class="text-gray-800 font-medium">{{ userInfo.weight || '--' }} kg</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">BMI</span>
              <span class="text-gray-800 font-medium">{{ bmi || '--' }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">目标体重</span>
              <span class="text-gray-800 font-medium">{{ reportData.targetWeight }}kg</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">血压</span>
              <span class="text-gray-800 font-medium">{{ reportData.bloodPressure }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">血糖</span>
              <span class="text-gray-800 font-medium">{{ reportData.bloodSugar }}</span>
            </div>
          </div>
          <div class="mt-4 pt-3 border-t border-gray-200">
            <p class="text-xs text-gray-600 font-medium">目标 {{ reportData.targetWeight }}kg · 还差 {{ reportData.weightDiff }}kg</p>
          </div>
        </div>
      </div>

      <div class="scroll-reveal-item" :class="{ 'is-visible': visibleSections >= 5 }">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
            <div class="flex items-center gap-2 mb-3">
              <div class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                <TrendingDown class="w-4 h-4 text-green-500" />
              </div>
              <span class="font-bold text-gray-800 text-sm">{{ reportType === 'weekly' ? '本周' : '近4周' }}体重趋势</span>
            </div>
            <div class="space-y-3">
              <div v-for="(item, idx) in reportData.weightHistory" :key="idx">
                <div class="flex justify-between text-xs mb-1">
                  <span class="text-gray-500 font-medium">{{ item.label }}</span>
                  <span class="text-gray-800 font-bold">{{ item.weight }} kg</span>
                </div>
                <div class="h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div class="h-full bg-gradient-to-r from-green-400 to-emerald-500 rounded-full transition-all duration-500" :style="{ width: `${item.percent}%` }"></div>
                </div>
              </div>
            </div>
            <div class="mt-4 pt-3 border-t border-gray-200">
              <p class="text-xs text-green-600 font-medium">{{ reportData.weightProgressText }}</p>
            </div>
          </div>

          <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
            <div class="flex items-center gap-2 mb-3">
              <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <Activity class="w-4 h-4 text-blue-500" />
              </div>
              <span class="font-bold text-gray-800 text-sm">{{ reportType === 'weekly' ? '本周' : '本月' }}营养达标</span>
            </div>
            <div class="space-y-3">
              <div v-for="(item, idx) in reportData.nutritionGoals" :key="idx">
                <div class="flex justify-between text-xs mb-1">
                  <span class="text-gray-500 font-medium">{{ item.name }}</span>
                  <span class="text-gray-800 font-bold">{{ item.current }}/{{ item.target }}</span>
                </div>
                <div class="h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    class="h-full rounded-full transition-all duration-500"
                    :class="item.percent >= 80 ? 'bg-gradient-to-r from-green-400 to-emerald-500' : item.percent >= 50 ? 'bg-gradient-to-r from-green-300 to-green-400' : 'bg-gradient-to-r from-amber-300 to-amber-400'"
                    :style="{ width: `${item.percent}%` }"
                  ></div>
                </div>
              </div>
            </div>
            <div class="mt-4 pt-3 border-t border-gray-200">
              <p class="text-xs text-green-600 font-medium">{{ reportData.nutritionProgressText }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="scroll-reveal-item" :class="{ 'is-visible': visibleSections >= 6 }">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-5">
          <button class="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-bold text-sm hover:from-green-600 hover:to-emerald-700 transition-all duration-300 shadow-lg shadow-green-200 flex items-center justify-center gap-2">
            <Search class="w-4 h-4" />
            搜索健康菜谱
          </button>
          <button class="w-full py-3 bg-gray-100 text-gray-700 rounded-xl font-bold text-sm hover:bg-gray-200 transition-all duration-300">
            返回菜谱助手
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { Heart, Flame, Leaf, Dumbbell, TrendingDown, Activity, Search, Calendar, CalendarDays } from 'lucide-vue-next'
import { useUserStore, type User } from '@/stores/user'
import { useDietStore } from '@/stores/diet'
import { api } from '@/api'
import { useReportCache } from '@/composables/useReportCache'
import HealthHeatmap from '@/components/HealthHeatmap.vue'

const userStore = useUserStore()
const dietStore = useDietStore()
const reportType = ref<'weekly' | 'monthly'>('weekly')
const visibleSections = ref(0)

const userInfo = computed(() => userStore.user || ({} as User))

const bmi = computed(() => {
  if (!userInfo.value.height || !userInfo.value.weight) return '--'
  const heightM = (userInfo.value.height as number) / 100
  const weight = userInfo.value.weight as number
  return (weight / (heightM * heightM)).toFixed(1)
})

const currentYear = computed(() => new Date().getFullYear())
const currentMonth = computed(() => new Date().getMonth() + 1)

interface WeightHistoryItem {
  label: string
  weight: number
  percent: number
}

interface NutritionGoal {
  name: string
  current: string
  target: string
  percent: number
}

interface ReportData {
  checkinDays: number
  checkinTrend: string
  avgCalories: number
  caloriesTrend: string
  healthyDays: number
  healthyPercent: number
  exerciseDays: number
  exerciseMinutes: number
  targetWeight: number
  weightDiff: number
  bloodPressure: string
  bloodSugar: string
  weightHistory: WeightHistoryItem[]
  weightProgressText: string
  nutritionGoals: NutritionGoal[]
  nutritionProgressText: string
}

const reportData = ref<ReportData>({
  checkinDays: 0,
  checkinTrend: '',
  avgCalories: 0,
  caloriesTrend: '',
  healthyDays: 0,
  healthyPercent: 0,
  exerciseDays: 0,
  exerciseMinutes: 0,
  targetWeight: 60,
  weightDiff: 0,
  bloodPressure: '--/--',
  bloodSugar: '-- mmol/L',
  weightHistory: [],
  weightProgressText: '',
  nutritionGoals: [],
  nutritionProgressText: ''
})

// 图表缓存加载器：防抖 + 会话内缓存 + 按天粒度增量失效（阶段一 · 图表缓存）
const reportCache = useReportCache<Partial<ReportData>>('health-report')

const fetchReport = async (): Promise<Partial<ReportData>> => {
  // 从 dietStore 获取当前饮食数据（仅缓存未命中时才拉取）
  const today = new Date().toISOString().split('T')[0]
  await dietStore.fetchTodayMeals(today)

  const days = reportType.value === 'weekly' ? 7 : 30
  const endDate = today
  const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

  const result = await api.report.range(startDate, endDate)
  return result && Object.keys(result).length > 0 ? result : {}
}

const loadReportData = async () => {
  const today = new Date().toISOString().split('T')[0]
  // 缓存 key 含 操作身份 + 周期 + 日期：切换用户/切换周期/跨天 自动重新请求（增量更新）
  const data = await reportCache.load(
    { user: userStore.actAsUserId ?? 'self', type: reportType.value, date: today },
    fetchReport
  )
  if (data) {
    reportData.value = { ...reportData.value, ...data }
  }
  // API 不可用时保持空的 reportData，不生成假数据
}

let revealTimer: ReturnType<typeof setTimeout> | null = null

const revealSections = () => {
  const totalSections = 6
  const delay = 300
  
  for (let i = 1; i <= totalSections; i++) {
    revealTimer = setTimeout(() => {
      visibleSections.value = i
    }, i * delay)
  }
}

watch(reportType, () => {
  loadReportData()
  visibleSections.value = 0
  setTimeout(revealSections, 500)
})

onMounted(() => {
  loadReportData()
  setTimeout(revealSections, 800)
})

onBeforeUnmount(() => {
  if (revealTimer) {
    clearTimeout(revealTimer)
    revealTimer = null
  }
})
</script>

<style scoped>
.weekly-report-wrapper {
  min-height: 100vh;
}

.scroll-reveal-item {
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 0.9s ease-out, transform 0.9s ease-out;
}

.scroll-reveal-item.is-visible {
  opacity: 1;
  transform: translateY(0);
}
</style>
