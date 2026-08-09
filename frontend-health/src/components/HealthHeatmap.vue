<template>
  <div class="heatmap-container bg-white rounded-xl p-4 shadow-sm border border-gray-100">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <Calendar class="w-5 h-5 text-emerald-500" />
        <h3 class="text-base font-bold text-gray-800">{{ heatmapLabel }}</h3>
      </div>
      <div class="flex items-center gap-3">
        <div v-for="item in legend" :key="item.label" class="flex items-center gap-1">
          <span class="w-3 h-3 rounded-sm transition-transform hover:scale-110" :class="item.color"></span>
          <span class="text-xs text-gray-500">{{ item.label }}</span>
        </div>
      </div>
    </div>
    
    <div class="flex gap-[6px] mb-2">
      <div 
        v-for="day in weekDays" 
        :key="day" 
        class="w-[32px] text-center text-[12px] font-semibold text-gray-400 py-1"
      >
        {{ day }}
      </div>
    </div>
    
    <div class="space-y-[6px]">
      <div 
        v-for="(week, weekIndex) in weeks" 
        :key="weekIndex"
        class="flex gap-[6px]"
      >
        <div 
          v-for="(cell, dayIndex) in week" 
          :key="dayIndex"
          class="w-[32px] h-[32px] rounded-lg flex items-center justify-center transition-all duration-200"
          :class="getCellClass(cell)"
          @click="cell.day && showDetail(cell)"
        >
          <span v-if="cell.day" class="text-[12px] font-semibold">{{ cell.day }}</span>
        </div>
      </div>
    </div>
    
    <div class="mt-4 flex items-center justify-between text-sm">
      <div class="flex items-center gap-3">
        <span class="text-gray-500">{{ reportType === 'weekly' ? '本周' : '本月' }}打卡:</span>
        <span class="text-xl font-bold text-emerald-600">{{ checkedDays }}</span>
        <span class="text-gray-400">/{{ totalDays }}天</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-gray-500">平均评分:</span>
        <span class="text-xl font-bold text-amber-500">{{ averageScore }}分</span>
      </div>
    </div>
    
    <div 
      v-if="selectedDetail" 
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm"
      @click.self="selectedDetail = null"
    >
      <div class="bg-white rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl transform transition-all duration-300 scale-100">
        <div class="flex items-center gap-3 mb-5">
          <div 
            class="w-12 h-12 rounded-full flex items-center justify-center"
            :class="selectedDetail.bgClass"
          >
            <component :is="selectedDetail.icon" class="w-6 h-6" :class="selectedDetail.iconClass" />
          </div>
          <div>
            <h4 class="font-bold text-gray-800 text-lg">{{ selectedDetail.date }}</h4>
            <p class="text-sm text-gray-500">{{ selectedDetail.status }}</p>
          </div>
        </div>
        
        <div class="bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl p-4 mb-4">
          <div class="flex items-center justify-between">
            <span class="text-gray-600 font-medium">健康评分</span>
            <span class="text-3xl font-bold" :class="selectedDetail.scoreClass">{{ selectedDetail.score }}分</span>
          </div>
        </div>
        
        <div v-if="selectedDetail.scoreBreakdown" class="space-y-3 mb-4">
          <p class="text-sm font-semibold text-gray-700 pb-2 border-b border-gray-100">评分详情</p>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">营养摄入达标</span>
              <div class="flex items-center gap-2">
                <div class="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    class="h-full rounded-full" 
                    :class="selectedDetail.scoreBreakdown.nutrition >= 30 ? 'bg-green-500' : 'bg-amber-400'"
                    :style="{ width: `${(selectedDetail.scoreBreakdown.nutrition / 40) * 100}%` }"
                  ></div>
                </div>
                <span class="text-xs font-medium w-12 text-right" :class="selectedDetail.scoreBreakdown.nutrition >= 30 ? 'text-green-600' : 'text-amber-600'">{{ selectedDetail.scoreBreakdown.nutrition }}/40</span>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">无超标营养素</span>
              <div class="flex items-center gap-2">
                <div class="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    class="h-full rounded-full" 
                    :class="selectedDetail.scoreBreakdown.noExcess >= 25 ? 'bg-green-500' : 'bg-amber-400'"
                    :style="{ width: `${(selectedDetail.scoreBreakdown.noExcess / 30) * 100}%` }"
                  ></div>
                </div>
                <span class="text-xs font-medium w-12 text-right" :class="selectedDetail.scoreBreakdown.noExcess >= 25 ? 'text-green-600' : 'text-amber-600'">{{ selectedDetail.scoreBreakdown.noExcess }}/30</span>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">符合用户画像</span>
              <div class="flex items-center gap-2">
                <div class="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    class="h-full rounded-full" 
                    :class="selectedDetail.scoreBreakdown.profile >= 25 ? 'bg-green-500' : 'bg-amber-400'"
                    :style="{ width: `${(selectedDetail.scoreBreakdown.profile / 30) * 100}%` }"
                  ></div>
                </div>
                <span class="text-xs font-medium w-12 text-right" :class="selectedDetail.scoreBreakdown.profile >= 25 ? 'text-green-600' : 'text-amber-600'">{{ selectedDetail.scoreBreakdown.profile }}/30</span>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="selectedDetail.meals" class="space-y-3 mb-4">
          <p class="text-sm font-semibold text-gray-700 pb-2 border-b border-gray-100">三餐详情</p>
          <div class="grid grid-cols-3 gap-2">
            <div class="bg-orange-50 rounded-lg p-2 text-center">
              <p class="text-xs text-orange-600 font-medium mb-1">早餐</p>
              <p class="text-lg font-bold text-gray-800">{{ selectedDetail.meals.breakfast }}分</p>
              <p class="text-[10px] text-gray-400">占比30%</p>
            </div>
            <div class="bg-blue-50 rounded-lg p-2 text-center">
              <p class="text-xs text-blue-600 font-medium mb-1">午餐</p>
              <p class="text-lg font-bold text-gray-800">{{ selectedDetail.meals.lunch }}分</p>
              <p class="text-[10px] text-gray-400">占比40%</p>
            </div>
            <div class="bg-purple-50 rounded-lg p-2 text-center">
              <p class="text-xs text-purple-600 font-medium mb-1">晚餐</p>
              <p class="text-lg font-bold text-gray-800">{{ selectedDetail.meals.dinner }}分</p>
              <p class="text-[10px] text-gray-400">占比30%</p>
            </div>
          </div>
        </div>
        
        <div v-if="selectedDetail.exercise" class="bg-blue-50 rounded-xl p-3 mb-4 flex items-center gap-3">
          <Dumbbell class="w-5 h-5 text-blue-500" />
          <div>
            <p class="text-sm font-semibold text-blue-700">今日运动</p>
            <p class="text-xs text-blue-600">{{ selectedDetail.exercise }}</p>
          </div>
        </div>
        
        <button 
          @click="selectedDetail = null" 
          class="w-full py-2.5 bg-gradient-to-r from-emerald-500 to-green-600 text-white rounded-xl font-semibold text-sm hover:from-emerald-600 hover:to-green-700 transition-all duration-200 shadow-lg shadow-emerald-200 hover:shadow-xl hover:shadow-emerald-300"
        >
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, type Component } from 'vue'
import { Calendar, Dumbbell, AlertCircle, XCircle, CheckCircle, Sparkles } from 'lucide-vue-next'

const weekDays = ['一', '二', '三', '四', '五', '六', '日']

interface ScoreBreakdown {
  nutrition: number
  noExcess: number
  profile: number
}

interface DayMeals {
  breakfast: number
  lunch: number
  dinner: number
}

interface HeatmapDay {
  date: string
  dayOfMonth: number
  score?: number
  scoreBreakdown?: ScoreBreakdown
  meals?: DayMeals
  hasExercise: boolean
  exercise?: string
}

interface CalendarCell {
  day?: number
  dayData?: HeatmapDay
}

const props = withDefaults(defineProps<{
  reportType: 'weekly' | 'monthly'
  year?: number
  month?: number
}>(), {
  year: () => new Date().getFullYear(),
  month: () => new Date().getMonth() + 1
})

const legend = [
  { label: '健康', color: 'bg-green-500' },
  { label: '良好', color: 'bg-amber-400' },
  { label: '一般', color: 'bg-blue-400' },
  { label: '较差', color: 'bg-red-400' },
  { label: '未记录', color: 'bg-gray-200' },
]

const generateDayData = (dateStr: string, dayOfMonth: number): HeatmapDay => {
  const hasRecord = Math.random() > 0.15
  
  if (!hasRecord) {
    return {
      date: dateStr,
      dayOfMonth,
      hasExercise: false
    }
  }
  
  const breakfastScore = Math.floor(Math.random() * 15) + 28
  const lunchScore = Math.floor(Math.random() * 15) + 28
  const dinnerScore = Math.floor(Math.random() * 15) + 28
  
  const nutritionScore = Math.round((breakfastScore * 0.3 + lunchScore * 0.4 + dinnerScore * 0.3) * 10) / 10
  
  const random = Math.random()
  let noExcessScore: number
  let profileScore: number
  
  if (random > 0.65) {
    noExcessScore = Math.floor(Math.random() * 10) + 20
    profileScore = Math.floor(Math.random() * 10) + 20
  } else if (random > 0.35) {
    noExcessScore = Math.floor(Math.random() * 6) + 24
    profileScore = Math.floor(Math.random() * 6) + 24
  } else {
    noExcessScore = 28 + Math.floor(Math.random() * 3)
    profileScore = 28 + Math.floor(Math.random() * 3)
  }
  
  const totalScore = Math.round(nutritionScore + noExcessScore + profileScore)
  const hasExercise = Math.random() > 0.4
  
  return {
    date: dateStr,
    dayOfMonth,
    score: totalScore,
    scoreBreakdown: { nutrition: nutritionScore, noExcess: noExcessScore, profile: profileScore },
    meals: { breakfast: breakfastScore, lunch: lunchScore, dinner: dinnerScore },
    hasExercise,
    exercise: hasExercise ? ['散步30分钟', '慢跑45分钟', '瑜伽30分钟', '游泳60分钟', '骑行45分钟', '健身1小时', '跳绳20分钟'][Math.floor(Math.random() * 7)] : undefined
  }
}

const generateWeekData = (): HeatmapDay[] => {
  const days: HeatmapDay[] = []
  const today = new Date()
  const dayOfWeek = today.getDay() || 7
  const monday = new Date(today)
  monday.setDate(today.getDate() - dayOfWeek + 1)
  
  for (let i = 0; i < 7; i++) {
    const date = new Date(monday)
    date.setDate(monday.getDate() + i)
    const dateStr = date.toISOString().split('T')[0]
    const dayData = generateDayData(dateStr, date.getDate())
    days.push(dayData)
  }
  
  return days
}

const generateMonthData = (): HeatmapDay[] => {
  const days: HeatmapDay[] = []
  const daysInMonth = new Date(props.year, props.month, 0).getDate()
  
  for (let i = 1; i <= daysInMonth; i++) {
    const dateStr = `${props.year}-${String(props.month).padStart(2, '0')}-${String(i).padStart(2, '0')}`
    const dayData = generateDayData(dateStr, i)
    days.push(dayData)
  }
  
  return days
}

const days = ref<HeatmapDay[]>([])

const loadData = () => {
  if (props.reportType === 'weekly') {
    days.value = generateWeekData()
  } else {
    days.value = generateMonthData()
  }
}

watch(() => props.reportType, loadData)
watch([() => props.year, () => props.month], loadData)

onMounted(loadData)

const selectedDetail = ref<{
  date: string
  score: number
  status: string
  icon: Component
  iconClass: string
  bgClass: string
  scoreClass: string
  statusClass: string
  scoreBreakdown?: ScoreBreakdown
  meals?: DayMeals
  exercise?: string
} | null>(null)

const heatmapLabel = computed(() => {
  if (props.reportType === 'weekly') {
    const today = new Date()
    const dayOfWeek = today.getDay() || 7
    const monday = new Date(today)
    monday.setDate(today.getDate() - dayOfWeek + 1)
    const sunday = new Date(monday)
    sunday.setDate(monday.getDate() + 6)
    return `${monday.getMonth() + 1}月${monday.getDate()}日-${sunday.getMonth() + 1}月${sunday.getDate()}日 健康打卡`
  }
  return `${props.year}年${props.month}月 健康打卡`
})

const totalDays = computed(() => days.value.length)

const checkedDays = computed(() => {
  return days.value.filter(day => day.score !== undefined && day.score > 0).length
})

const averageScore = computed(() => {
  let total = 0
  let count = 0
  days.value.forEach(day => {
    if (day.score && day.score > 0) {
      total += day.score
      count++
    }
  })
  return count > 0 ? Math.round(total / count) : 0
})

const weeks = computed(() => {
  const result: CalendarCell[][] = []
  
  if (props.reportType === 'weekly') {
    let currentWeek: CalendarCell[] = []
    days.value.forEach(dayData => {
      currentWeek.push({
        day: dayData.dayOfMonth,
        dayData
      })
    })
    result.push(currentWeek)
    return result
  }
  
  const firstDayOfMonth = new Date(props.year, props.month - 1, 1).getDay()
  const startPadding = firstDayOfMonth === 0 ? 6 : firstDayOfMonth - 1
  
  let currentWeek: CalendarCell[] = []
  
  for (let i = 0; i < startPadding; i++) {
    currentWeek.push({})
  }
  
  days.value.forEach(dayData => {
    currentWeek.push({
      day: dayData.dayOfMonth,
      dayData
    })
    
    if (currentWeek.length === 7) {
      result.push(currentWeek)
      currentWeek = []
    }
  })
  
  if (currentWeek.length > 0) {
    while (currentWeek.length < 7) {
      currentWeek.push({})
    }
    result.push(currentWeek)
  }
  
  return result
})

const getColorClass = (day: HeatmapDay): string => {
  if (day.score === undefined || day.score === 0) return 'bg-gray-200'
  if (day.score >= 80) {
    return 'bg-green-500'
  } else if (day.score >= 60) {
    return day.hasExercise ? 'bg-amber-400' : 'bg-blue-400'
  }
  return day.hasExercise ? 'bg-blue-400' : 'bg-red-400'
}

const getCellClass = (cell: CalendarCell): string => {
  if (!cell.day) {
    return 'bg-gray-100'
  }
  
  const dayData = cell.dayData
  if (!dayData) {
    return 'bg-gray-100'
  }
  
  const colorClass = getColorClass(dayData)
  
  return `${colorClass} text-white cursor-pointer hover:opacity-80 hover:scale-105 transition-all shadow-md`
}

const getHealthStatus = (score: number, hasExercise: boolean): string => {
  if (score >= 80) return hasExercise ? '健康饮食+运动' : '健康饮食'
  if (score >= 60) return hasExercise ? '良好+运动' : '良好'
  return hasExercise ? '一般+运动' : '较差'
}

const getStatusIcon = (score: number, hasExercise: boolean): Component => {
  if (score >= 80) return CheckCircle
  if (score >= 60) return Sparkles
  return hasExercise ? Dumbbell : XCircle
}

const getStatusClass = (score: number, hasExercise: boolean): string => {
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-amber-600'
  return hasExercise ? 'text-blue-600' : 'text-red-600'
}

const getBgClass = (score: number, hasExercise: boolean): string => {
  if (score >= 80) return 'bg-green-100'
  if (score >= 60) return 'bg-amber-100'
  return hasExercise ? 'bg-blue-100' : 'bg-red-100'
}

const showDetail = (cell: CalendarCell) => {
  if (!cell.dayData || !cell.dayData.score || cell.dayData.score === 0) return
  
  const dayData = cell.dayData
  const score = dayData.score!
  
  const status = getHealthStatus(score, dayData.hasExercise)
  const icon = getStatusIcon(score, dayData.hasExercise)
  const statusClass = getStatusClass(score, dayData.hasExercise)
  const scoreClass = statusClass
  const bgClass = getBgClass(score, dayData.hasExercise)
  
  selectedDetail.value = {
    date: dayData.date,
    score: score,
    status,
    icon,
    iconClass: statusClass,
    bgClass,
    scoreClass,
    statusClass,
    scoreBreakdown: dayData.scoreBreakdown,
    meals: dayData.meals,
    exercise: dayData.exercise
  }
}
</script>
