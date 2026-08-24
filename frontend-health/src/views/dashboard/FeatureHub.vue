<template>
  <div class="feature-hub min-h-full relative">
    <div v-if="currentCategory || !currentGroup" class="max-w-5xl mx-auto relative z-10">
      <!-- 标题区 -->
      <div class="mb-10 pt-4 hub-header">
        <div class="flex items-center gap-5 mb-4">
          <div class="hub-icon-wrap w-14 h-14 rounded-2xl flex items-center justify-center text-white relative overflow-hidden"
               :style="{ background: grad(currentTheme.primary) }">
            <div class="hub-icon-glow absolute inset-0"
                 :style="{ background: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.25) 0%, transparent 60%)' }"></div>
            <component :is="currentCategory?.icon || LayoutGrid" class="w-7 h-7 relative z-10" :stroke-width="1.75" />
          </div>
          <div>
            <h1 class="text-[26px] font-bold text-slate-800 tracking-tight leading-none" style="font-family: 'Noto Serif SC', serif">{{ title }}</h1>
            <p class="text-sm text-slate-500 font-medium mt-1.5">{{ subtitle }} · {{ greeting }}，{{ username }}</p>
          </div>
        </div>
        <div class="hub-underline h-[3px] w-24 rounded-full relative overflow-hidden"
             :style="{ background: gradSoft(currentTheme.primary) }">
          <div class="underline-shine absolute inset-0"
               :style="{ background: gradShine(currentTheme.primary) }"></div>
        </div>
      </div>

      <!-- 实时概览（真实后端数据，仅首页显示） -->
      <div v-if="!currentGroup" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="stat-glass rounded-2xl p-5 relative overflow-hidden">
          <div class="stat-icon w-9 h-9 rounded-xl flex items-center justify-center mb-3" :style="{ background: currentTheme.soft, color: currentTheme.primary }">
            <Flame class="w-4.5 h-4.5" :size="18" stroke-width="1.75" />
          </div>
          <p class="text-xs text-slate-500">今日摄入</p>
          <p class="text-2xl font-bold mt-1 tabular" :style="{ color: currentTheme.primary }">{{ overview.todayKcal ?? '—' }}<span v-if="overview.todayKcal != null" class="text-sm font-normal text-slate-400"> kcal</span></p>
          <p class="text-xs text-slate-400 mt-1">{{ overview.todayKcal == null ? '今日暂无饮食记录' : '已记录' }}</p>
        </div>
        <div class="stat-glass rounded-2xl p-5 relative overflow-hidden">
          <div class="stat-icon w-9 h-9 rounded-xl flex items-center justify-center mb-3" :style="{ background: currentTheme.soft, color: currentTheme.primary }">
            <Activity class="w-4.5 h-4.5" :size="18" stroke-width="1.75" />
          </div>
          <p class="text-xs text-slate-500">BMI</p>
          <p class="text-2xl font-bold text-slate-700 mt-1 tabular">{{ overview.bmi ?? '—' }}</p>
          <p class="text-xs mt-1" :class="bmiClass">{{ overview.bmiText }}</p>
        </div>
        <div class="stat-glass rounded-2xl p-5 relative overflow-hidden">
          <div class="stat-icon w-9 h-9 rounded-xl flex items-center justify-center mb-3" :style="{ background: currentTheme.soft, color: currentTheme.primary }">
            <Scale class="w-4.5 h-4.5" :size="18" stroke-width="1.75" />
          </div>
          <p class="text-xs text-slate-500">当前体重</p>
          <p class="text-2xl font-bold text-slate-700 mt-1 tabular">{{ overview.weight ?? '—' }}<span v-if="overview.weight" class="text-sm font-normal text-slate-400"> kg</span></p>
          <p class="text-xs text-slate-400 mt-1">基础代谢 BMR {{ overview.bmr ?? '—' }} kcal</p>
        </div>
        <div class="stat-glass rounded-2xl p-5 relative overflow-hidden">
          <div class="stat-icon w-9 h-9 rounded-xl flex items-center justify-center mb-3" :style="{ background: currentTheme.soft, color: currentTheme.primary }">
            <FileText class="w-4.5 h-4.5" :size="18" stroke-width="1.75" />
          </div>
          <p class="text-xs text-slate-500">健康报告</p>
          <p class="text-2xl font-bold text-slate-700 mt-1 tabular">{{ overview.reportCount ?? 0 }}<span class="text-sm font-normal text-slate-400"> 份</span></p>
          <p class="text-xs text-slate-400 mt-1">周报/月报累计</p>
        </div>
      </div>

      <!-- 首页：一级功能卡片（5 个大分类） -->
      <div v-if="!currentGroup" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <div
          v-for="(group, idx) in allGroups" :key="group.key"
          class="feature-card group cursor-pointer p-6 rounded-2xl text-left relative overflow-hidden"
          :style="cardStyle(group, idx)"
          @click="goGroup(group)"
          @mouseenter="hoveredGroup = group.key"
          @mouseleave="hoveredGroup = null"
        >
          <!-- 卡片顶部渐变光条 -->
          <div class="card-top-bar" :style="{ background: topBarGrad(group.key) }"></div>

          <!-- 背景装饰图标 -->
          <div class="card-bg-icon absolute -right-4 -bottom-4 pointer-events-none" :style="getGroupBgIconStyle(group, idx)">
            <component :is="group.icon" class="w-32 h-32" :stroke-width="1" />
          </div>

          <!-- 背景光晕 -->
          <div class="card-glow"
               :style="hoveredGroup === group.key ? { background: glowGrad(group.key) } : {}"></div>

          <div class="relative z-10">
            <div class="card-icon-wrap w-14 h-14 rounded-2xl flex items-center justify-center mb-4 transition-all duration-300"
                 :style="getGroupIconStyle(group)">
              <component :is="group.icon" class="w-7 h-7" :stroke-width="1.75" />
            </div>

            <div class="card-label font-bold text-[19px] text-slate-800 transition-colors duration-300 tracking-tight leading-tight"
                 :style="hoveredGroup === group.key ? { color: groupTheme(group.key).primary } : {}">
              {{ group.title }}
            </div>
            <div class="card-desc text-sm text-slate-500 mt-2 leading-relaxed">
              {{ group.desc }}
            </div>
            <div class="mt-4 flex items-center gap-2 text-xs font-medium">
              <span class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">{{ group.items.length }} 个功能</span>
              <span class="card-action flex items-center text-xs font-semibold"
                    :style="hoveredGroup === group.key ? { color: groupTheme(group.key).primary } : { color: '#94a3b8' }">
                进入
                <component :is="ArrowRight" class="w-3.5 h-3.5 ml-1 transition-transform duration-300 group-hover:translate-x-1" />
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 二级：分类内功能卡片 -->
      <div v-else v-for="group in visibleGroups" :key="group.key" class="mb-8">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
          <div
            v-for="(f, idx) in group.items" :key="f.to"
            class="feature-card group cursor-pointer p-6 rounded-2xl text-left relative overflow-hidden"
            :style="cardStyle(group, idx)"
            @click="go(f.to)"
            @mouseenter="hoveredCard = f.to"
            @mouseleave="hoveredCard = null"
          >
            <!-- 卡片顶部渐变光条 -->
            <div class="card-top-bar" :style="{ background: topBarGrad(group.key) }"></div>

            <!-- 背景装饰图标 -->
            <div class="card-bg-icon absolute -right-4 -bottom-4 pointer-events-none" :style="getBgIconStyle(f, group.key, idx)">
              <component :is="f.icon" class="w-28 h-28" :stroke-width="1" />
            </div>

            <!-- 背景光晕 -->
            <div class="card-glow"
                 :style="hoveredCard === f.to ? { background: glowGrad(group.key) } : {}"></div>

            <div class="relative z-10">
              <div class="card-icon-wrap w-12 h-12 rounded-xl flex items-center justify-center mb-4 transition-all duration-300"
                   :style="getCardIconStyle(f, group.key)">
                <component :is="f.icon" class="w-6 h-6" :stroke-width="1.75" />
              </div>

              <div class="card-label font-bold text-[17px] text-slate-800 transition-colors duration-300 tracking-tight leading-tight"
                   :style="hoveredCard === f.to ? { color: groupTheme(group.key).primary } : {}">
                {{ f.name }}
              </div>
              <div class="card-desc text-sm text-slate-500 mt-2 leading-relaxed">
                {{ f.desc }}
              </div>
              <div class="card-action mt-5 flex items-center text-xs font-semibold transition-all duration-300"
                   :style="hoveredCard === f.to ? { color: groupTheme(group.key).primary } : { color: '#94a3b8' }">
                <span class="font-medium">进入功能</span>
                <component :is="ArrowRight" class="w-3.5 h-3.5 ml-1.5 transition-transform duration-300 group-hover:translate-x-2" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'
import {
  User, Users, Activity, FileText, UsersRound,
  Utensils, PlusCircle, PieChart, Search,
  HeartPulse, BarChart3, Dumbbell,
  BookOpen, Newspaper, MessageCircle, ClipboardList, ChefHat,
  Flame, Scale, LayoutGrid, ArrowRight
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const username = computed(() => userStore.user?.username || '朋友')
const today = new Date().toISOString().slice(0, 10)

// 当前分组（来自 URL ?group=xxx）
const currentGroup = computed(() => (route.query.group as string) || '')

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const title = computed(() => {
  const g = allGroups.find(x => x.key === currentGroup.value)
  return g ? g.title : '首页'
})
const subtitle = computed(() => {
  const g = allGroups.find(x => x.key === currentGroup.value)
  return g ? g.desc : '欢迎回来，从这里开始管理你的健康生活'
})

// 当前分组元信息（图标）
const currentCategory = computed(() => {
  const g = allGroups.find(x => x.key === currentGroup.value)
  return g || null
})

// 分组主题色（延续 morandi 墨绿/琥珀设计系统；每个分组一个主题，hover 时高亮）
interface GroupTheme { primary: string; soft: string }
const groupThemes: Record<string, GroupTheme> = {
  user: { primary: '#2F5D4A', soft: '#E4EDE7' },
  diet: { primary: '#2F5D4A', soft: '#E4EDE7' },
  health: { primary: '#2F5D4A', soft: '#E4EDE7' },
  knowledge: { primary: '#2F5D4A', soft: '#E4EDE7' },
  recipe: { primary: '#E07A3F', soft: '#FBE9DC' },
}
function groupTheme(key: string): GroupTheme {
  return groupThemes[key] || groupThemes.user
}
const currentTheme = computed<GroupTheme>(() => groupTheme(currentGroup.value || 'user'))

// 渐变辅助
function grad(primary: string): string {
  return 'linear-gradient(135deg, ' + primary + ' 0%, ' + primary + 'dd 100%)'
}
function gradSoft(primary: string): string {
  return 'linear-gradient(90deg, ' + primary + ' 0%, ' + primary + '20 100%)'
}
function gradShine(primary: string): string {
  return 'linear-gradient(90deg, transparent, ' + primary + '60, transparent)'
}
function topBarGrad(groupKey: string): string {
  const p = groupTheme(groupKey).primary
  return 'linear-gradient(90deg, ' + p + '00 0%, ' + p + ' 50%, ' + p + '00 100%)'
}
function glowGrad(groupKey: string): string {
  const p = groupTheme(groupKey).primary
  return 'radial-gradient(ellipse at 75% 25%, ' + p + '18 0%, transparent 60%)'
}

// 全部功能分组（与侧边栏 5 组对应）
const allGroups = [
  { key: 'user', title: '用户中心', desc: '个人资料与健康档案', icon: Users, items: [
    { to: '/dashboard/profile', icon: User, name: '个人中心', desc: '资料、身高体重、人群设定' },
    { to: '/dashboard/metrics-history', icon: Activity, name: '指标历史', desc: '体重/BMI 趋势曲线与预测' },
    { to: '/dashboard/health-history', icon: FileText, name: '健康档案', desc: '历次健康快照回顾' },
    { to: '/dashboard/family-relation', icon: UsersRound, name: '亲属管理', desc: '监护关系与代操作' },
  ]},
  { key: 'diet', title: '饮食管理', desc: '记录与分析每日饮食', icon: Utensils, items: [
    { to: '/dashboard/food-input', icon: Utensils, name: '饮食记录', desc: '按餐次记录三餐与加餐' },
    { to: '/dashboard/nutrition', icon: PieChart, name: '营养分析', desc: '热量/蛋白质/微量元素达标' },
    { to: '/dashboard/food-search', icon: Search, name: '食物搜索', desc: '查询营养成分与 GI 值' },
    { to: '/dashboard/food-add', icon: PlusCircle, name: '添加食材', desc: '录入新食材到库' },
    { to: '/dashboard/family-input', icon: Users, name: '亲属代录', desc: '替家人记录饮食' },
  ]},
  { key: 'health', title: '健康监测', desc: '报告与运动', icon: HeartPulse, items: [
    { to: '/dashboard/health-report', icon: BarChart3, name: '健康报告', desc: '周报/月报健康回顾' },
    { to: '/dashboard/muscle-chart', icon: Dumbbell, name: '运动管理', desc: '训练记录与围度变化' },
  ]},
  { key: 'knowledge', title: '知识中心', desc: '科普与智能助手', icon: BookOpen, items: [
    { to: '/dashboard/articles', icon: Newspaper, name: '科普文章', desc: '循证营养学主题阅读' },
    { to: '/dashboard/ai-consult', icon: MessageCircle, name: 'AI 咨询', desc: '饮食/慢病/运动问答' },
    { to: '/dashboard/training-plan', icon: HeartPulse, name: '训练计划', desc: '个性化运动方案' },
  ]},
  { key: 'recipe', title: '菜谱美食', desc: '菜谱与饮食偏好', icon: ChefHat, items: [
    { to: '/dashboard/recipe-library', icon: ChefHat, name: '菜谱库', desc: '根据档案推荐菜谱' },
    { to: '/dashboard/dietary-profile', icon: ClipboardList, name: '饮食档案', desc: '过敏/忌口/口味偏好' },
  ]},
]

// 按分组过滤（无分组显示全部）
const visibleGroups = computed(() => {
  if (currentGroup.value) return allGroups.filter(g => g.key === currentGroup.value)
  return allGroups
})

const hoveredCard = ref<string | null>(null)
const hoveredGroup = ref<string | null>(null)

const cardStyle = (group: any, idx: number) => {
  const theme = groupTheme(group.key)
  return {
    '--theme-color': theme.primary,
    '--delay': (idx * 80) + 'ms'
  } as Record<string, string>
}

// 一级卡片：点击进入分类
function goGroup(group: any) {
  router.push({ path: '/dashboard/hub', query: { group: group.key } })
}

// 一级卡片背景装饰图标
const getGroupBgIconStyle = (group: any, idx: number) => {
  const theme = groupTheme(group.key)
  const rotations = [-8, 6, -12, 10, -5]
  const rotation = rotations[idx % rotations.length]
  const isHovered = hoveredGroup.value === group.key
  return {
    color: theme.primary,
    opacity: isHovered ? 0.1 : 0.05,
    transform: 'rotate(' + (isHovered ? rotation + 5 : rotation) + 'deg) ' + (isHovered ? 'scale(1.12)' : 'scale(1)'),
    transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)'
  }
}

// 一级卡片图标
const getGroupIconStyle = (group: any) => {
  const theme = groupTheme(group.key)
  const isHovered = hoveredGroup.value === group.key
  if (isHovered) {
    return {
      background: 'linear-gradient(135deg, ' + theme.primary + ' 0%, ' + theme.primary + 'cc 100%)',
      color: '#fff',
      boxShadow: '0 10px 24px ' + theme.primary + '45'
    }
  }
  return {
    background: theme.primary + '10',
    color: theme.primary,
    border: '1px solid ' + theme.primary + '18'
  }
}

const getBgIconStyle = (card: any, groupKey: string, idx: number) => {
  const theme = groupTheme(groupKey)
  const rotations = [-8, 6, -12, 10, -5]
  const rotation = rotations[idx % rotations.length]
  const isHovered = hoveredCard.value === card.to
  return {
    color: theme.primary,
    opacity: isHovered ? 0.1 : 0.05,
    transform: 'rotate(' + (isHovered ? rotation + 5 : rotation) + 'deg) ' + (isHovered ? 'scale(1.12)' : 'scale(1)'),
    transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)'
  }
}

const getCardIconStyle = (card: any, groupKey: string) => {
  const theme = groupTheme(groupKey)
  const isHovered = hoveredCard.value === card.to
  if (isHovered) {
    return {
      background: 'linear-gradient(135deg, ' + theme.primary + ' 0%, ' + theme.primary + 'cc 100%)',
      color: '#fff',
      boxShadow: '0 10px 24px ' + theme.primary + '45'
    }
  }
  return {
    background: theme.primary + '10',
    color: theme.primary,
    border: '1px solid ' + theme.primary + '18'
  }
}

const overview = ref<{ todayKcal: number | null; bmi: number | null; bmiText: string; weight: number | null; bmr: number | null; reportCount: number }>({
  todayKcal: null, bmi: null, bmiText: '—', weight: null, bmr: null, reportCount: 0
})
const bmiClass = computed(() => {
  const b = overview.value.bmi
  if (b == null) return 'text-slate-400'
  if (b < 18.5) return 'text-amber-500'
  if (b < 24) return 'text-emerald-600'
  return 'text-red-500'
})

function go(to: string) { router.push(to) }

onMounted(async () => {
  const [diet, snap, reports] = await Promise.allSettled([
    api.diet.getByDate(today),
    api.profile.snapshot(),
    api.report.list(),
  ])
  if (diet.status === 'fulfilled') {
    const d = (diet.value as any)?.data ?? diet.value
    const meals = Array.isArray(d) ? d : []
    let kcal = 0, has = false
    for (const m of meals) {
      const items = m?.foods ?? m?.items ?? []
      for (const it of items) { const c = Number(it?.calories_kcal ?? it?.calories ?? it?.cal ?? 0); if (c) { kcal += c; has = true } }
      if (m?.meal_calories_kcal) { kcal += Number(m.meal_calories_kcal); has = true }
    }
    overview.value.todayKcal = has ? Math.round(kcal) : null
  }
  if (snap.status === 'fulfilled') {
    const s = (snap.value as any)?.data ?? snap.value
    const w = Number(s?.weight), h = Number(s?.height), bmr = Number(s?.bmr)
    if (w && h) {
      overview.value.weight = w
      const bmi = Math.round((w / Math.pow(h / 100, 2)) * 10) / 10
      overview.value.bmi = bmi
      overview.value.bmiText = bmi < 18.5 ? '偏瘦' : bmi < 24 ? '正常范围' : bmi < 28 ? '超重' : '肥胖'
    }
    if (bmr) overview.value.bmr = Math.round(bmr)
  }
  if (reports.status === 'fulfilled') {
    const r = (reports.value as any)?.data ?? reports.value
    overview.value.reportCount = Array.isArray(r) ? r.length : 0
  }
})
</script>

<style scoped>
.feature-hub {
  min-height: calc(100vh - 64px);
}

/* 标题动画 */
.hub-header {
  animation: hubFadeIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}
.hub-icon-wrap {
  animation: hubFadeIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.hub-icon-wrap:hover {
  transform: scale(1.05) rotate(-2deg);
}
@keyframes hubFadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
.hub-icon-glow {
  pointer-events: none;
}

/* 下划线 */
.hub-underline {
  position: relative;
}
.underline-shine {
  animation: shine 3s ease-in-out infinite;
}
@keyframes shine {
  0%, 100% { transform: translateX(-100%); }
  50% { transform: translateX(100%); }
}

/* 概览卡片 */
.stat-glass {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(16px) saturate(1.4);
  -webkit-backdrop-filter: blur(16px) saturate(1.4);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 10px rgba(31, 42, 36, 0.05);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
}
.stat-glass:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px -8px rgba(47, 93, 74, 0.18);
}

/* 功能卡片（参考 health1 卡片设计） */
.feature-card {
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(24px) saturate(1.5);
  -webkit-backdrop-filter: blur(24px) saturate(1.5);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 20px;
  opacity: 0;
  transform: translateY(20px) scale(0.97);
  animation: cardIn 0.55s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: var(--delay, 0s);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
              box-shadow 0.4s cubic-bezier(0.4, 0, 0.2, 1),
              border-color 0.4s ease,
              background 0.4s ease;
}

/* 渐变边框 */
.feature-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 20px;
  padding: 1px;
  background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(255,255,255,0.2));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  opacity: 0.8;
}

.feature-card:hover {
  transform: translateY(-6px) scale(1.02);
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 30px 60px -15px rgba(15, 23, 42, 0.15),
              0 10px 25px -5px rgba(15, 23, 42, 0.08),
              0 0 0 1px var(--theme-color, #10b981)30;
}

/* 顶部光条 */
.card-top-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  opacity: 0;
  transform: scaleX(0);
  transform-origin: left center;
  transition: opacity 0.4s ease, transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
.feature-card:hover .card-top-bar {
  opacity: 1;
  transform: scaleX(1);
}

@keyframes cardIn {
  0% {
    opacity: 0;
    transform: translateY(24px) scale(0.94);
  }
  60% {
    transform: translateY(-4px) scale(1.01);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.card-bg-icon {
  z-index: 0;
}

.card-glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.5s ease;
  z-index: 0;
}
.feature-card:hover .card-glow {
  opacity: 1;
}

.card-icon-wrap {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.feature-card:hover .card-icon-wrap {
  transform: scale(1.06);
}

/* 底部进入功能 */
.card-action {
  opacity: 0.85;
  transition: opacity 0.3s ease;
}
</style>