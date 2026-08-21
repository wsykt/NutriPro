<template>
  <div class="home-page">
    <!-- ========== 问候区 ========== -->
    <div class="greeting-card">
      <div class="greeting-content">
        <p class="greeting-sub">个人健康管理系统</p>
        <h1 class="greeting-title">{{ greetingText }}，{{ userName }}</h1>
        <p class="greeting-desc">今天也是关注健康的一天</p>
        <div class="greeting-actions">
          <button class="action-btn primary" @click="goTo('/dashboard/food-input')">
            <Plus class="w-4 h-4" />
            记录今日饮食
          </button>
          <button class="action-btn ghost" @click="goTo('/dashboard/health-report')">
            查看健康报告
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
      <div class="greeting-decor">
        <div class="heartbeat-ring"></div>
        <div class="heartbeat-ring delay"></div>
        <div class="heartbeat-core">
          <Activity class="w-10 h-10 text-white" />
        </div>
      </div>
    </div>

    <!-- ========== 三大营养素 ========== -->
    <div class="section">
      <h2 class="section-title">三大营养素</h2>
      <div class="nutrient-grid">
        <div class="nutrient-card" v-for="item in nutrients" :key="item.key">
          <div class="nutrient-head">
            <div class="nutrient-icon" :style="{ background: item.bgColor }">
              <component :is="item.icon" class="w-5 h-5" :style="{ color: item.color }" />
            </div>
            <span class="nutrient-name">{{ item.name }}</span>
          </div>
          <div class="nutrient-body">
            <div class="nutrient-progress">
              <div class="progress-track">
                <div class="progress-fill" :style="{ width: item.percent + '%', background: item.color }"></div>
              </div>
              <span class="nutrient-percent">{{ item.percent }}%</span>
            </div>
            <p class="nutrient-value">{{ item.current }} / {{ item.target }} g</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 指标概览 ========== -->
    <div class="section">
      <h2 class="section-title">本周概览</h2>
      <div class="metric-grid">
        <div class="metric-card" v-for="m in metrics" :key="m.key">
          <div class="metric-icon" :style="{ background: m.bgColor }">
            <component :is="m.icon" class="w-5 h-5" :style="{ color: m.color }" />
          </div>
          <div class="metric-value-row">
            <span class="metric-value">{{ m.value }}</span>
            <span class="metric-unit">{{ m.unit }}</span>
          </div>
          <p class="metric-label">{{ m.label }}</p>
          <p class="metric-desc" :class="{ 'positive': m.trend.startsWith('+'), 'negative': m.trend.startsWith('-') }">
            {{ m.trend }}
          </p>
        </div>
      </div>
    </div>

    <!-- ========== 快捷操作 ========== -->
    <div class="section">
      <h2 class="section-title">快捷操作</h2>
      <div class="quick-grid">
        <div
          class="quick-card"
          v-for="q in quickActions"
          :key="q.key"
          @click="goTo(q.route)"
        >
          <div class="quick-icon" :style="{ background: q.bgColor }">
            <component :is="q.icon" class="w-5 h-5" :style="{ color: q.color }" />
          </div>
          <div class="quick-info">
            <p class="quick-name">{{ q.label }}</p>
            <p class="quick-desc">{{ q.desc }}</p>
          </div>
          <ChevronRight class="quick-arrow w-4 h-4" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'
import {
  Activity,
  User as UserIcon,
  Plus,
  ChevronRight,
  Leaf,
  Flame,
  Target,
  Dumbbell,
  Calendar,
  UtensilsCrossed,
  ChefHat,
  Stethoscope,
  Sparkles,
  Brain
} from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()

const userName = computed(() => {
  const u: any = userStore.user || {}
  return u?.username ? u.username : '用户'
})

const greetingText = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '凌晨好'
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})

/* ---- 今日营养素（从 API 获取，失败用 mock） ---- */
const todayNutrition = ref({ protein: 0, fat: 0, carb: 0 })
const todayCalories = ref(0)

const loadTodayNutrition = async () => {
  try {
    const today = new Date().toISOString().split('T')[0]
    const data: any = await api.diet.analyze(today)
    if (data) {
      todayNutrition.value = {
        protein: Math.round(data.protein || 0),
        fat: Math.round(data.fat || 0),
        carb: Math.round(data.carbohydrate || 0)
      }
      todayCalories.value = Math.round(data.calorie || 0)
    }
  } catch {
    // mock 数据
    todayNutrition.value = { protein: 45, fat: 32, carb: 180 }
    todayCalories.value = 1680
  }
}

const NUTRIENT_TARGETS = { protein: 75, fat: 55, carb: 250 }

const nutrients = computed(() => ([
  {
    key: 'protein',
    name: '蛋白质',
    icon: Activity,
    color: '#ef4444',
    bgColor: 'rgba(239,68,68,0.12)',
    current: todayNutrition.value.protein,
    target: NUTRIENT_TARGETS.protein,
    percent: Math.min(100, Math.round((todayNutrition.value.protein / NUTRIENT_TARGETS.protein) * 100))
  },
  {
    key: 'fat',
    name: '脂肪',
    icon: Flame,
    color: '#f59e0b',
    bgColor: 'rgba(245,158,11,0.12)',
    current: todayNutrition.value.fat,
    target: NUTRIENT_TARGETS.fat,
    percent: Math.min(100, Math.round((todayNutrition.value.fat / NUTRIENT_TARGETS.fat) * 100))
  },
  {
    key: 'carb',
    name: '碳水',
    icon: Target,
    color: '#10b981',
    bgColor: 'rgba(16,185,129,0.12)',
    current: todayNutrition.value.carb,
    target: NUTRIENT_TARGETS.carb,
    percent: Math.min(100, Math.round((todayNutrition.value.carb / NUTRIENT_TARGETS.carb) * 100))
  }
]))

/* ---- 指标（从健康报告 API 获取周统计） ---- */
const weeklyStats = ref({
  avgCalories: 1680,
  healthyDays: 5,
  exerciseDays: 3,
  checkinDays: 6,
  caloriesTrend: '+5%',
  healthyTrend: '+2天',
  exerciseTrend: '+1天',
  checkinTrend: '+1天'
})

const loadWeeklyStats = async () => {
  try {
    const end = new Date()
    const start = new Date()
    start.setDate(end.getDate() - 7)
    const fmt = (d: Date) => d.toISOString().split('T')[0]
    const data: any = await api.report.range(fmt(start), fmt(end))
    if (data) {
      weeklyStats.value = {
        avgCalories: data.avgCalories || 1680,
        healthyDays: data.healthyDays || 5,
        exerciseDays: data.exerciseDays || 3,
        checkinDays: data.checkinDays || 6,
        caloriesTrend: data.caloriesTrend || '+5%',
        healthyTrend: data.healthyTrend || '+2天',
        exerciseTrend: data.exerciseTrend || '+1天',
        checkinTrend: data.checkinTrend || '+1天'
      }
    }
  } catch {
    // 保持默认 mock 值
  }
}

const metrics = computed(() => ([
  {
    key: 'avgCalories',
    label: '平均热量',
    value: weeklyStats.value.avgCalories,
    unit: 'kcal',
    trend: weeklyStats.value.caloriesTrend,
    icon: Flame,
    color: '#ef4444',
    bgColor: 'rgba(239,68,68,0.12)'
  },
  {
    key: 'healthyDays',
    label: '健康饮食',
    value: weeklyStats.value.healthyDays,
    unit: '天',
    trend: weeklyStats.value.healthyTrend,
    icon: Leaf,
    color: '#10b981',
    bgColor: 'rgba(16,185,129,0.12)'
  },
  {
    key: 'exerciseDays',
    label: '运动天数',
    value: weeklyStats.value.exerciseDays,
    unit: '天',
    trend: weeklyStats.value.exerciseTrend,
    icon: Dumbbell,
    color: '#6366f1',
    bgColor: 'rgba(99,102,241,0.12)'
  },
  {
    key: 'checkinDays',
    label: '打卡天数',
    value: weeklyStats.value.checkinDays,
    unit: '天',
    trend: weeklyStats.value.checkinTrend,
    icon: Calendar,
    color: '#f59e0b',
    bgColor: 'rgba(245,158,11,0.12)'
  }
]))

/* ---- 快捷操作 ---- */
const quickActions = [
  {
    key: 'profile',
    label: '个人中心',
    desc: '账户与亲属管理',
    route: '/dashboard/profile',
    icon: UserIcon,
    color: '#a78bfa',
    bgColor: 'rgba(167,139,250,0.12)'
  },
  {
    key: 'nutrition',
    label: '营养分析',
    desc: '三大营养素分析',
    route: '/dashboard/nutrition',
    icon: Sparkles,
    color: '#ff8a65',
    bgColor: 'rgba(255,138,101,0.12)'
  },
  {
    key: 'recipe',
    label: '食谱库',
    desc: '搜索食谱与菜品',
    route: '/dashboard/recipe-library',
    icon: ChefHat,
    color: '#fbbf24',
    bgColor: 'rgba(251,191,36,0.12)'
  },
  {
    key: 'ai',
    label: 'AI健康咨询',
    desc: '智能健康建议',
    route: '/dashboard/ai-consult',
    icon: Brain,
    color: '#43b086',
    bgColor: 'rgba(67,176,134,0.12)'
  }
]

const goTo = (path: string) => {
  router.push(path)
}

onMounted(() => {
  loadTodayNutrition()
  loadWeeklyStats()
})
</script>

<style scoped>
.home-page {
  padding: 0;
}

/* ========== 问候区 ========== */
.greeting-card {
  position: relative;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0f9ff 100%);
  border-radius: 24px;
  padding: 36px 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.05);
  margin-bottom: 28px;
  animation: cardFadeIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}
@keyframes cardFadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.greeting-content {
  flex: 1;
  z-index: 2;
}
.greeting-sub {
  font-size: 12px;
  color: #64748b;
  letter-spacing: 1px;
  margin: 0 0 6px;
  font-weight: 500;
}
.greeting-title {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 6px;
  letter-spacing: -0.5px;
}
.greeting-desc {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 24px;
}
.greeting-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 11px 22px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  border: none;
}
.action-btn.primary {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.32);
}
.action-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4);
}
.action-btn.ghost {
  background: transparent;
  color: #059669;
  font-weight: 600;
}
.action-btn.ghost:hover {
  color: #047857;
  transform: translateX(4px);
}

/* 装饰圆 */
.greeting-decor {
  position: relative;
  width: 120px;
  height: 120px;
  flex-shrink: 0;
}
.heartbeat-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(14,165,233,0.15));
  animation: ringPulse 3s ease-in-out infinite;
}
.heartbeat-ring.delay {
  animation-delay: 0.5s;
  inset: 15px;
}
@keyframes ringPulse {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.1); opacity: 0.4; }
}
.heartbeat-core {
  position: absolute;
  inset: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 30px rgba(16, 185, 129, 0.35);
  animation: coreBeat 3s ease-in-out infinite;
}
@keyframes coreBeat {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.06); }
}

/* ========== 区块通用 ========== */
.section {
  margin-bottom: 28px;
  animation: cardFadeIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}
.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 16px;
}

/* ========== 营养素 ========== */
.nutrient-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}
.nutrient-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 20px 22px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.nutrient-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 30px -8px rgba(15, 23, 42, 0.1);
}
.nutrient-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}
.nutrient-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.nutrient-name {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}
.nutrient-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.nutrient-progress {
  display: flex;
  align-items: center;
  gap: 10px;
}
.progress-track {
  flex: 1;
  height: 8px;
  background: #f1f5f9;
  border-radius: 99px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}
.nutrient-percent {
  font-size: 12px;
  font-weight: 700;
  color: #334155;
  min-width: 36px;
  text-align: right;
}
.nutrient-value {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}

/* ========== 指标 ========== */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
}
.metric-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 20px 22px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.metric-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 30px -8px rgba(15, 23, 42, 0.1);
}
.metric-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}
.metric-value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 4px;
}
.metric-value {
  font-size: 30px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -1px;
}
.metric-unit {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}
.metric-label {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 4px;
}
.metric-desc {
  font-size: 12px;
  font-weight: 600;
  margin: 0;
}
.metric-desc.positive {
  color: #10b981;
}
.metric-desc.negative {
  color: #ef4444;
}

/* ========== 快捷操作 ========== */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
}
.quick-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 18px 20px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}
.quick-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 30px -8px rgba(15, 23, 42, 0.1);
  border-color: rgba(15, 23, 42, 0.12);
}
.quick-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.quick-info {
  flex: 1;
  min-width: 0;
}
.quick-name {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 2px;
}
.quick-desc {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}
.quick-arrow {
  color: #cbd5e1;
  flex-shrink: 0;
  transition: transform 0.25s ease, color 0.25s ease;
}
.quick-card:hover .quick-arrow {
  color: #10b981;
  transform: translateX(4px);
}

/* ========== 响应式 ========== */
@media (max-width: 1024px) {
  .metric-grid,
  .quick-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .nutrient-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .greeting-card {
    flex-direction: column;
    gap: 24px;
    text-align: center;
    padding: 28px;
  }
  .greeting-actions {
    justify-content: center;
  }
  .greeting-decor {
    width: 90px;
    height: 90px;
  }
  .metric-grid,
  .quick-grid {
    grid-template-columns: 1fr;
  }
}
</style>
