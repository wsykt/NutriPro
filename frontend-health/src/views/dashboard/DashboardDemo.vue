<template>
  <div class="dashboard-demo min-h-full relative">
    <div class="max-w-6xl mx-auto relative z-10">

      <!-- ===== 问候区 ===== -->
      <div class="mb-8 pt-4 flex items-center gap-4">
        <div class="greet-mark w-12 h-12 rounded-2xl flex items-center justify-center text-white shrink-0"
             style="background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%); box-shadow: 0 10px 24px rgba(47,93,74,0.25)">
          <Leaf class="w-6 h-6" />
        </div>
        <div>
          <h1 class="text-[28px] font-bold text-slate-800 tracking-tight leading-tight" style="font-family: 'Noto Serif SC', serif">
            <span class="text-animate-char" v-for="(c, i) in greetChars" :key="i" :style="{ animationDelay: (i * 0.05) + 's' }">{{ c }}</span>
          </h1>
          <p class="text-sm text-slate-500 mt-1 text-animate-fade" style="animation-delay: 0.8s">{{ todayText }}</p>
        </div>
      </div>

      <!-- ===== 顶部双区：左(摄入+体重) / 右(科普+待办) ===== -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">

        <!-- 左侧大卡：今日摄入 + 体重趋势（合并） -->
        <div class="col-span-12 lg:col-span-7 feature-panel rounded-2xl p-6 relative overflow-visible blur-fade-card flex flex-col h-full" style="--bf-delay:0s">
          <div class="panel-bg-icon absolute -right-6 -bottom-6 pointer-events-none opacity-[0.05]"><Activity class="w-44 h-44" /></div>
          <!-- 今日摄入（flex-1，和体重各占一半） -->
          <div class="flex-1 min-h-0 flex flex-col relative">
            <!-- 右下角火焰背景（和卡片统一） -->
            <div class="absolute -right-4 -bottom-4 pointer-events-none opacity-[0.05]"><Flame class="w-40 h-40" /></div>
            <div class="flex items-center justify-between mb-4 shrink-0">
              <h3 class="font-semibold text-slate-800 flex items-center gap-2 text-[15px]">
                <span class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:#E07A3F15;color:#E07A3F"><Flame class="w-4 h-4" /></span>
                今日摄入
              </h3>
              <button @click="go('/dashboard/food-input')" class="text-xs text-morandi-accent hover:underline flex items-center gap-1">记录饮食 <ArrowRight class="w-3 h-3" /></button>
            </div>
            <div class="flex items-stretch justify-center gap-5 flex-1 pb-3">
              <!-- 大圈：热量（红色，独立磨砂玻璃背景） -->
              <div class="ring-tile flex flex-col items-center justify-center gap-1.5 shrink-0 rounded-2xl px-4 py-3 self-center"
                   style="background:rgba(255,255,255,0.35);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.6);box-shadow:0 2px 12px rgba(31,42,36,0.05)">
                <div class="relative w-28 h-28 shrink-0">
                  <svg viewBox="0 0 112 112" class="w-28 h-28 -rotate-90">
                    <circle cx="56" cy="56" r="46" fill="none" stroke="rgba(224,82,82,0.12)" stroke-width="10"/>
                    <circle cx="56" cy="56" r="46" fill="none" :stroke="ringData.heat.color" stroke-width="10" stroke-linecap="round"
                          :stroke-dasharray="(ringData.heat.percent * 289.0 / 100) + ' 289.0'"/>
                  </svg>
                  <div class="absolute inset-0 flex items-center justify-center flex-col">
                    <span class="text-[20px] font-bold text-slate-800 tabular-nums" style="font-family: 'Noto Serif SC', serif">{{ ringData.heat.display }}</span>
                    <span class="text-[10px] text-slate-400">kcal</span>
                  </div>
                </div>
                <span class="text-xs font-medium text-slate-600">热量</span>
                <span class="text-[10px] text-slate-400 tabular-nums">{{ ringData.heat.percent }}%</span>
              </div>
              <!-- 4 个小圈：各带独立磨砂玻璃小方块背景 -->
              <div class="grid grid-cols-2 gap-x-3 gap-y-2 flex-1 content-center">
                <div v-for="ring in ringData.small" :key="ring.key"
                     class="ring-tile flex flex-col items-center justify-center gap-0.5 rounded-xl py-2"
                     style="background:rgba(255,255,255,0.3);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.55);box-shadow:0 2px 10px rgba(31,42,36,0.04)">
                  <div class="relative w-14 h-14 shrink-0">
                    <svg viewBox="0 0 56 56" class="w-14 h-14 -rotate-90">
                      <circle cx="28" cy="28" r="22" fill="none" stroke="rgba(0,0,0,0.05)" stroke-width="6"/>
                      <circle cx="28" cy="28" r="22" fill="none" :stroke="ring.color" stroke-width="6" stroke-linecap="round"
                            :stroke-dasharray="(ring.percent * 138.2 / 100) + ' 138.2'"/>
                    </svg>
                    <div class="absolute inset-0 flex items-center justify-center flex-col">
                      <span class="text-[11px] font-bold text-slate-700 tabular-nums">{{ ring.display }}</span>
                    </div>
                  </div>
                  <span class="text-[11px] text-slate-600">{{ ring.label }}</span>
                  <span class="text-[10px] text-slate-400 tabular-nums">{{ ring.percent }}%</span>
                </div>
              </div>
            </div>
          </div>
          <!-- 分隔线（绝对居中虚线，不占 flex 空间，对齐右卡缝隙） -->
          <div class="absolute left-6 right-6 top-1/2 -translate-y-1/2 border-t border-dashed pointer-events-none" style="border-color:#E7E2D8"></div>
          <!-- 体重趋势（flex-1，和今日摄入各占一半） -->
          <div class="flex-1 min-h-0 flex flex-col justify-center pt-3">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-slate-800 flex items-center gap-2 text-[15px]">
                <span class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:#2F5D4A15;color:#2F5D4A"><TrendingDown class="w-4 h-4" /></span>
                体重趋势
              </h3>
              <span class="text-xs px-2 py-1 rounded-full" :class="weightChangeTrend === 'down' ? 'bg-emerald-50 text-emerald-600' : weightChangeTrend === 'up' ? 'bg-amber-50 text-amber-600' : 'bg-slate-50 text-slate-500'">{{ weightChangeText }}</span>
            </div>
            <!-- 体重趋势折线图（vue-echarts，autoresize 自动监听尺寸） -->
            <v-chart :option="weightChartOption" autoresize class="w-full" style="height:148px" />
            <!-- 指标 3 栏：体重 / BMI / BMR -->
            <div class="mt-3 grid grid-cols-3 gap-3 relative">
              <div class="bg-slate-50 rounded-xl py-2 text-center">
                <div class="text-[10px] text-slate-400">体重</div>
                <div class="font-bold text-slate-800 tabular-nums text-sm">{{ currentWeight || '—' }}<span class="text-[9px] font-normal text-slate-400"> kg</span></div>
              </div>
              <!-- BMI：绿字 + 悬停弹窗（向上弹出，利用折线图区域空白避免底部导航遮挡） -->
              <div class="metric-tip relative bg-slate-50 rounded-xl py-2 text-center cursor-help">
                <div class="text-[10px] font-semibold" style="color:#2F5D4A">BMI</div>
                <div class="font-bold text-slate-800 tabular-nums text-sm" :class="bmiClass">{{ bmi || '—' }}</div>
                <div class="metric-tooltip absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 p-3 rounded-xl text-left z-50 hidden" style="background:#fff;box-shadow:0 10px 30px rgba(31,42,36,0.15);border:1px solid #F1EDE4">
                  <div class="text-xs font-semibold text-slate-800 mb-1">BMI 身体质量指数</div>
                  <div class="text-[11px] text-slate-500 leading-relaxed mb-1.5">衡量体重与身高关系的指标，用于评估体重是否在健康范围。</div>
                  <div class="text-[11px] text-slate-600 font-medium mb-1">公式</div>
                  <div class="text-[10px] text-slate-500 leading-relaxed">BMI = 体重(kg) ÷ 身高(m)²</div>
                  <div class="text-[10px] text-slate-500 leading-relaxed mt-1">18.5–23.9 正常 · 24–27.9 超重 · ≥28 肥胖</div>
                </div>
              </div>
              <!-- BMR：绿字 + 悬停弹窗（向上弹出，折线图 148px 空白足够承载 w-56 内容） -->
              <div class="metric-tip relative bg-slate-50 rounded-xl py-2 text-center cursor-help">
                <div class="text-[10px] font-semibold" style="color:#2F5D4A">BMR</div>
                <div class="font-bold text-slate-800 tabular-nums text-sm">{{ bmr || '—' }}<span class="text-[9px] font-normal text-slate-400"> kcal</span></div>
                <div class="metric-tooltip absolute bottom-full right-0 mb-2 w-56 p-3 rounded-xl text-left z-50 hidden" style="background:#fff;box-shadow:0 10px 30px rgba(31,42,36,0.15);border:1px solid #F1EDE4">
                  <div class="text-xs font-semibold text-slate-800 mb-1">BMR 基础代谢率</div>
                  <div class="text-[11px] text-slate-500 leading-relaxed mb-1.5">身体静息时维持生命所需的热量，是计算每日推荐摄入的基准。</div>
                  <div class="text-[11px] text-slate-600 font-medium mb-1">公式（Mifflin-St Jeor）</div>
                  <div class="text-[10px] text-slate-500 leading-relaxed">男性：10×体重 + 6.25×身高 − 5×年龄 + 5<br/>女性：10×体重 + 6.25×身高 − 5×年龄 − 161</div>
                  <div class="text-[11px] text-slate-600 font-medium mt-1.5 mb-0.5">与推荐摄入的关系</div>
                  <div class="text-[10px] text-slate-500 leading-relaxed">推荐摄入 = BMR × 活动系数（久坐 1.2 / 轻度 1.375 / 中度 1.55）</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：科普文章 + 今日待办 -->
        <div class="col-span-12 lg:col-span-5 space-y-5 flex flex-col">

          <!-- 科普文章展示 -->
          <div class="feature-panel rounded-2xl p-6 relative overflow-hidden blur-fade-card flex-1" style="--bf-delay:0.12s">
            <div class="panel-bg-icon absolute -right-6 -bottom-6 pointer-events-none opacity-[0.05]"><BookOpen class="w-40 h-40" /></div>
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-slate-800 flex items-center gap-2 text-[15px]">
                <span class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:#60a5fa15;color:#60a5fa"><BookOpen class="w-4 h-4" /></span>
                科普文章
              </h3>
              <button @click="go('/dashboard/articles')" class="text-xs text-morandi-accent hover:underline flex items-center gap-1">更多 <ArrowRight class="w-3 h-3" /></button>
            </div>
            <!-- 人群筛选 -->
            <div class="flex items-center gap-1.5 mb-3 flex-wrap">
              <span class="text-[11px] text-slate-400 whitespace-nowrap">人群</span>
              <button
                v-for="af in articleAudienceFilters" :key="af.key"
                @click="articleAudience = af.key"
                class="px-2 py-0.5 rounded-full text-[11px] font-medium transition-all whitespace-nowrap"
                :class="articleAudience === af.key ? 'text-white shadow-sm' : 'bg-slate-50 text-slate-500 hover:bg-slate-100 border border-slate-100'"
                :style="articleAudience === af.key ? { background: '#60a5fa' } : {}"
              >{{ af.label }}</button>
            </div>
            <!-- 文章窄条列表（可滚动） -->
            <div class="article-scroll space-y-2 max-h-[240px] overflow-y-auto pr-1">
              <div v-for="(art, i) in filteredArticles" :key="i"
                   @click="go('/dashboard/articles')"
                   class="article-row group relative flex items-center gap-3 p-2.5 rounded-xl border border-slate-100 hover:border-morandi-accent/30 hover:bg-white transition-all cursor-pointer overflow-hidden">
                <!-- 悬停蓝色光条（从右侧滑入，仅色带无文字） -->
                <div class="article-expand absolute right-0 top-0 bottom-0 w-0 overflow-hidden opacity-0 transition-all duration-300"
                     style="background:linear-gradient(90deg,transparent 0%,rgba(96,165,250,0.08) 45%,rgba(96,165,250,0.16) 100%);border-left:2px solid rgba(96,165,250,0.45)"></div>
                <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style="background:#60a5fa15;color:#60a5fa">
                  <Newspaper class="w-4 h-4" />
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-[13px] font-medium text-slate-700 truncate">{{ art.title }}</div>
                  <div class="text-[10px] text-slate-400 mt-0.5 flex items-center gap-2">
                    <span v-if="art.audience" class="px-1.5 py-px rounded-full" style="background:#60a5fa12;color:#60a5fa">{{ art.audience }}</span>
                    <span class="truncate">{{ art.summary || '点击阅读' }}</span>
                  </div>
                </div>
                <ArrowRight class="w-3.5 h-3.5 text-slate-300 shrink-0 transition-all duration-200 group-hover:translate-x-0.5 group-hover:text-blue-500" />
              </div>
              <div v-if="!filteredArticles.length" class="text-center py-4 text-xs text-slate-400">该人群暂无文章</div>
            </div>
          </div>
          <!-- 今日待办 -->
          <div class="feature-panel rounded-2xl p-6 relative overflow-hidden blur-fade-card flex-1" style="--bf-delay:0.24s">
            <div class="panel-bg-icon absolute -right-6 -bottom-6 pointer-events-none opacity-[0.05]"><CheckCircle2 class="w-40 h-40" /></div>
            <h3 class="font-semibold text-slate-800 mb-4 flex items-center gap-2 text-[15px]">
              <span class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:#E07A3F15;color:#E07A3F"><CheckCircle2 class="w-4 h-4" /></span>
              今日待办
            </h3>
            <div class="space-y-2.5">
              <div v-for="(todo, i) in todos" :key="i" class="flex items-center gap-3 p-2.5 rounded-xl border border-slate-100 hover:border-morandi-accent/30 hover:bg-white transition-all cursor-pointer"
                   @click="todo.to && go(todo.to)">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" :style="{ background: todo.color + '15', color: todo.color }">
                  <component :is="todo.icon" class="w-4 h-4" />
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-slate-700 truncate">{{ todo.text }}</div>
                  <div class="text-[11px] text-slate-400 mt-0.5 truncate">{{ todo.detail }}</div>
                </div>
                <ArrowRight class="w-3.5 h-3.5 text-slate-300 shrink-0" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 快捷操作 ===== -->
      <div class="mt-5 mb-2">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-slate-800 text-[15px] flex items-center gap-2">
            <span class="w-7 h-7 rounded-lg flex items-center justify-center" style="background:#E07A3F18;color:#E07A3F"><Zap class="w-4 h-4" /></span>
            快捷操作
          </h3>
          <span class="text-xs text-slate-400">常用功能直达</span>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button v-for="(act, i) in quickActions" :key="i" @click="go(act.to)"
            class="feature-panel rounded-2xl p-4 flex items-center gap-3 text-left transition-all hover:-translate-y-1 relative overflow-hidden blur-fade-card" style="--bf-delay:0.1s">
            <div class="panel-bg-icon absolute -right-4 -bottom-4 pointer-events-none opacity-[0.05]"><component :is="act.icon" class="w-20 h-20" /></div>
            <div class="relative z-10 flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0" :style="{ background: act.color + '15', color: act.color }">
                <component :is="act.icon" class="w-5 h-5" />
              </div>
              <div>
                <div class="text-sm font-semibold text-slate-800">{{ act.label }}</div>
                <div class="text-[11px] text-slate-400">{{ act.desc }}</div>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- ===== 全部功能（5 个一级卡） ===== -->
      <div class="mt-6 mb-2">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-slate-800 text-[15px] flex items-center gap-2">
            <span class="w-7 h-7 rounded-lg flex items-center justify-center" style="background:#2F5D4A18;color:#2F5D4A"><LayoutGrid class="w-4 h-4" /></span>
            全部功能
          </h3>
          <span class="text-xs text-slate-400">点击进入对应模块</span>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <button v-for="(group, i) in allGroups" :key="group.key" @click="goGroup(group)"
            class="feature-panel rounded-2xl p-4 text-left transition-all hover:-translate-y-1 relative overflow-hidden blur-fade-card" style="--bf-delay:0.2s">
            <div class="panel-bg-icon absolute -right-4 -bottom-4 pointer-events-none opacity-[0.05] transition-opacity group-hover:opacity-[0.09]">
              <component :is="group.icon" class="w-20 h-20" />
            </div>
            <div class="relative z-10">
              <div class="w-11 h-11 rounded-xl flex items-center justify-center mb-3" :style="groupIconStyle(group, i)">
                <component :is="group.icon" class="w-5.5 h-5.5" :size="22" />
              </div>
              <div class="text-[15px] font-semibold text-slate-800">{{ group.title }}</div>
              <div class="text-[11px] text-slate-400 mt-0.5">{{ group.desc }}</div>
              <div class="mt-2.5 flex items-center justify-between">
                <span class="text-[10px] px-2 py-0.5 rounded-full" :style="{ background: groupColor(group) + '12', color: groupColor(group) }">{{ group.items.length }} 个功能</span>
                <ArrowRight class="w-3.5 h-3.5 text-slate-300" />
              </div>
            </div>
          </button>
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
import echarts, { VChart } from '@/utils/echarts'
import {
  User, Users, Activity, FileText, UsersRound,
  Utensils, PlusCircle, PieChart, Search,
  HeartPulse, BarChart3, MapPin, Dumbbell,
  BookOpen, Newspaper, MessageCircle, ClipboardList, ChefHat,
  Flame, Scale, LayoutGrid, ArrowRight, TrendingDown, CheckCircle2,
  Camera, Mic, Sparkles, Calendar, Leaf, Zap, Info
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const username = computed(() => userStore.user?.username || '朋友')
const today = new Date().toISOString().slice(0, 10)

const greetChars = computed(() => {
  const base = greeting.value + '，' + username.value
  return base.split('')
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})
const todayText = new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })

// ===== 数据 =====
const overview = ref({
  todayKcal: null as number | null, protein: 0, fat: 0, carb: 0, fiber: 0,
  weight: null as number | null, height: null as number | null,
  bmi: null as number | null, bmr: null as number | null,
  reportCount: 0
})
const weightHistory = ref<number[]>([])
const weightDates = ref<string[]>([])
const articles = ref<any[]>([])
// 科普文章人群筛选
const userCrowdType = computed(() => userStore.user?.crowdType || userStore.user?.crowd_type || '普通人')
const myAudienceLabel = computed(() => {
  const crowdLabel: Record<string, string> = {
    '普通人': '普通人群', '健身': '健身人群', '老年': '老年人',
    '孕妇': '孕妇', '青少年': '青少年', '糖尿病': '糖尿病患者'
  }
  return crowdLabel[userCrowdType.value] || '普通人群'
})
// 默认选中我的人群（直接呈现当前用户人群的文章）
const articleAudience = ref('mine')
const articleAudienceFilters = computed(() => {
  const filters: any[] = [{ key: 'mine', label: myAudienceLabel.value }]
  // 全部可选人群（不含当前用户人群）
  for (const l of ['普通人群', '健身人群', '老年人', '孕妇', '青少年', '糖尿病患者']) {
    if (l !== myAudienceLabel.value) filters.push({ key: l, label: l })
  }
  return filters
})
const filteredArticles = computed(() => {
  const all = articles.value
  if (!all || !all.length) return []
  if (articleAudience.value === 'mine') {
    // 当前用户人群的文章，没有则回退全部
    const mine = all.filter((a: any) => a.audience === myAudienceLabel.value)
    return mine.length ? mine.slice(0, 8) : all.slice(0, 8)
  }
  return all.filter((a: any) => a.audience === articleAudience.value).slice(0, 8)
})

const calorieTarget = 2200
const proteinTarget = 110
const fatTarget = 80
const carbTarget = 300

const todayKcal = computed(() => overview.value.todayKcal ?? 0)
const proteinG = computed(() => overview.value.protein)
const fatG = computed(() => overview.value.fat)
const carbG = computed(() => overview.value.carb)
const caloriePercent = computed(() => Math.min(100, Math.round(todayKcal.value / calorieTarget * 100)))
const proteinPercent = computed(() => Math.min(100, Math.round(proteinG.value / proteinTarget * 100)))
const fatPercent = computed(() => Math.min(100, Math.round(fatG.value / fatTarget * 100)))
const carbPercent = computed(() => Math.min(100, Math.round(carbG.value / carbTarget * 100)))
const fiberG = computed(() => overview.value.fiber || 0)
const fiberPercent = computed(() => Math.min(100, Math.round(fiberG.value / 30 * 100)))
const currentWeight = computed(() => overview.value.weight)
const bmi = computed(() => overview.value.bmi)
const bmr = computed(() => overview.value.bmr)
const reportCount = computed(() => overview.value.reportCount)
const bmiClass = computed(() => {
  const b = overview.value.bmi
  if (b == null) return 'text-slate-400'
  if (b < 18.5) return 'text-amber-500'
  if (b < 24) return 'text-emerald-600'
  return 'text-red-500'
})

const nutritionBars = computed(() => [
  { label: '蛋白质', value: proteinG.value, target: proteinTarget, color: '#2F5D4A', percent: proteinPercent.value },
  { label: '脂肪', value: fatG.value, target: fatTarget, color: '#E07A3F', percent: fatPercent.value },
  { label: '碳水', value: carbG.value, target: carbTarget, color: '#8A928C', percent: carbPercent.value },
])

// 5 个圆环：热量大圈红 + 蛋白棕/脂肪黄/碳水蓝/纤维绿
const ringData = computed(() => ({
  heat: { display: todayKcal.value ? String(todayKcal.value) : '—', percent: caloriePercent.value, color: '#D97B6C' },
  small: [
    { key: 'protein', label: '蛋白质', display: proteinG.value + 'g', percent: proteinPercent.value, color: '#B89B84' },
    { key: 'carb', label: '碳水', display: carbG.value + 'g', percent: carbPercent.value, color: '#8FAFD6' },
    { key: 'fat', label: '脂肪', display: fatG.value + 'g', percent: fatPercent.value, color: '#D9BC6B' },
    { key: 'fiber', label: '膳食纤维', display: fiberG.value + 'g', percent: fiberPercent.value, color: '#92BFA0' },
  ]
}))

// ===== 体重趋势（ECharts 折线：历史实线 + 预测虚线） =====
const WEIGHT_DAYS = 15
const prediction = ref<any>(null)
const predictDays = ref(7)

// 历史体重（按 15 天补齐，从右→左为最新→最旧），含每天对应日期标签
const weightPadded = computed(() => {
  const hist = [...weightHistory.value]
  while (hist.length < WEIGHT_DAYS) hist.unshift(hist[0] ?? null)
  return hist.slice(0, WEIGHT_DAYS)
})
// X 轴：历史 15 天日期 + 预测 7 天日期
const weightXLabels = computed(() => {
  const arr: string[] = []
  const now = new Date()
  for (let i = WEIGHT_DAYS - 1; i >= 0; i--) {
    const d = new Date(now); d.setDate(d.getDate() - i)
    arr.push(String(d.getMonth() + 1) + '/' + String(d.getDate()).padStart(2, '0'))
  }
  for (let i = 1; i <= predictDays.value; i++) {
    const d = new Date(now); d.setDate(d.getDate() + i)
    arr.push(String(d.getMonth() + 1) + '/' + String(d.getDate()).padStart(2, '0'))
  }
  return arr
})
// 历史 series 数据（15 项，预测部分 null）
const historySeriesData = computed(() => {
  const arr: (number | null)[] = weightPadded.value.map(v => (v == null ? null : v))
  for (let i = 0; i < predictDays.value; i++) arr.push(null)
  return arr
})
// 预测 series 数据（末位衔接历史最后有效值）
const predictionSeriesData = computed(() => {
  const hist = weightPadded.value.filter((v): v is number => v != null)
  const predPts: number[] = prediction.value?.points || []
  const arr: (number | null)[] = new Array(WEIGHT_DAYS + predictDays.value).fill(null)
  if (!hist.length || !predPts.length) return arr
  // 预测起点：接在历史最后一个值后（索引 = WEIGHT_DAYS - 1 之后那一格）
  const startIdx = WEIGHT_DAYS - 1
  // 衔接点：把历史最后一个值填入预测 series，使虚线和实线在末点视觉连接
  arr[startIdx] = hist[hist.length - 1]
  predPts.slice(0, predictDays.value).forEach((v, i) => { arr[startIdx + 1 + i] = v })
  return arr
})

const weightChange = computed(() => {
  const arr = weightPadded.value.filter((v): v is number => v != null)
  if (arr.length < 2) return 0
  return arr[arr.length - 1] - arr[0]
})
const weightChangeTrend = computed(() => weightChange.value > 0 ? 'up' : weightChange.value < 0 ? 'down' : 'flat')
const weightChangeText = computed(() => {
  const d = weightChange.value
  if (!d) return '保持平稳'
  return d > 0 ? '上升 ' + d.toFixed(1) + ' kg' : '下降 ' + Math.abs(d).toFixed(1) + ' kg'
})
// 预测文案
const predictText = computed(() => {
  const pred = prediction.value
  if (!pred || pred.status !== 'ok') return ''
  if (pred.trend === 'down') return '预测趋势：下降'
  if (pred.trend === 'up') return '预测趋势：上升'
  return '预测趋势：平稳'
})

// ===== ECharts 体重趋势图配置（vue-echarts，computed 自动响应数据变化） =====
const weightChartOption = computed(() => {
  const xData = weightXLabels.value
  const histData = historySeriesData.value
  const predData = predictionSeriesData.value
  // 历史末值 → 末点高亮
  const histIdx: number[] = []
  histData.forEach((v, i) => { if (v != null) histIdx.push(i) })
  const lastHistIdx = histIdx.length ? histIdx[histIdx.length - 1] : -1
  const lastHistValue: number | null = lastHistIdx >= 0 ? (histData[lastHistIdx] as number) : null
  return {
    grid: { left: 40, right: 16, top: 12, bottom: 26 },
    legend: { show: false },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#fff',
      borderColor: '#F1EDE4',
      borderWidth: 1,
      textStyle: { color: '#475569', fontSize: 11 },
      axisPointer: { type: 'line', lineStyle: { color: '#E07A3F', type: 'dashed', width: 1 } },
      formatter: (params: any) => {
        const items = (params || []).filter((p: any) => p.value != null && !Number.isNaN(p.value))
        if (!items.length) return ''
        const head = '<div style="font-size:11px;color:#94a3b8;margin-bottom:4px">' + items[0].axisValue + '</div>'
        const rows = items.map((p: any) => {
          const color = p.color?.colorStops ? p.color.colorStops[0].color : p.color
          return '<div style="display:flex;align-items:center;justify-content:space-between;gap:18px;font-size:12px">'
            + '<span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + color + ';margin-right:6px"></span>' + p.seriesName + '</span>'
            + '<span style="font-weight:600;color:#1e293b;font-variant-numeric:tabular-nums">' + Number(p.value).toFixed(1) + ' kg</span>'
            + '</div>'
        }).join('')
        return head + rows
      },
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xData,
      axisLine: { lineStyle: { color: '#E7E2D8' } },
      axisTick: { show: false },
      axisLabel: {
        color: '#A8A29E',
        fontSize: 10,
        interval: Math.max(0, Math.ceil(xData.length / 5) - 1),
        hideOverlap: true,
      },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      scale: true,
      minInterval: 0.5,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#A8A29E',
        fontSize: 10,
        formatter: (v: number) => v.toFixed(1),
      },
      splitLine: {
        lineStyle: { color: '#F1EDE4', type: 'dashed' },
      },
    },
    series: [
      // 历史：实线 + 渐变填充 + 首尾标记
      {
        name: '历史',
        type: 'line',
        smooth: true,
        smoothMonotone: 'x',
        showSymbol: true,
        symbol: 'circle',
        symbolSize: (v: number, p: any) => (p?.dataIndex === lastHistIdx ? 11 : 7),
        itemStyle: {
          color: (p: any) => (p.dataIndex === lastHistIdx ? '#E07A3F' : '#fff'),
          borderColor: (p: any) => (p.dataIndex === lastHistIdx ? '#fff' : '#2F5D4A'),
          borderWidth: (p: any) => (p.dataIndex === lastHistIdx ? 2.5 : 2),
        },
        lineStyle: { color: '#2F5D4A', width: 2.5, cap: 'round' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(47,93,74,0.22)' },
            { offset: 1, color: 'rgba(47,93,74,0.0)' },
          ]),
        },
        markPoint: lastHistValue != null ? {
          symbol: 'circle',
          symbolSize: 26,
          symbolOffset: [0, 0],
          itemStyle: { color: 'rgba(224,122,63,0.12)', borderColor: 'rgba(224,122,63,0.2)', borderWidth: 1 },
          data: [{ coord: [lastHistIdx, lastHistValue] }],
          label: { show: false },
        } : undefined,
        data: histData,
      },
      // 预测：虚线 + 浅色填充，无标记除点
      {
        name: '预测',
        type: 'line',
        smooth: true,
        smoothMonotone: 'x',
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#fff', borderColor: '#E07A3F', borderWidth: 1.8 },
        lineStyle: { color: '#E07A3F', width: 2.2, type: 'dashed', dashOffset: 0 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(224,122,63,0.16)' },
            { offset: 1, color: 'rgba(224,122,63,0.0)' },
          ]),
          origin: 'auto',
        },
        markPoint: {
          symbol: 'pin',
          symbolSize: 36,
          symbolOffset: [0, -16],
          itemStyle: { color: '#E07A3F' },
          label: { color: '#fff', fontSize: 10, fontWeight: 600, formatter: '预测' },
          data: (() => {
            const indices: number[] = []
            predData.forEach((v, i) => { if (v != null) indices.push(i) })
            if (!indices.length) return []
            const idx = indices[indices.length - 1]
            return [{ coord: [idx, predData[idx]] }]
          })(),
        },
        data: predData,
      },
    ],
  }
})

// 今日待办
const todos = computed(() => {
  const list: any[] = []
  list.push({
    icon: Utensils, color: '#E07A3F',
    text: todayKcal.value === 0 ? '还没有记录今天的饮食' : '今日摄入 ' + todayKcal.value + ' kcal',
    detail: todayKcal.value === 0 ? '点此记录第一餐，让数据开始说话' : '目标 ' + calorieTarget + ' kcal' + (todayKcal.value < calorieTarget ? '，还可摄入 ' + (calorieTarget - todayKcal.value) + ' kcal' : '，已超目标'),
    to: '/dashboard/food-input'
  })
  if (proteinPercent.value < 60) {
    list.push({
      icon: Sparkles, color: '#2F5D4A',
      text: '蛋白质摄入不足',
      detail: '今日 ' + proteinG.value + 'g / 目标 ' + proteinTarget + 'g，建议补充鸡胸/鱼虾/豆腐',
      to: '/dashboard/food-search'
    })
  }
  list.push({
    icon: Calendar, color: '#8A928C',
    text: reportCount.value ? '查看你的健康报告' : '生成本周健康报告',
    detail: reportCount.value ? '已有 ' + reportCount.value + ' 份报告可回顾' : '记录饮食后自动生成周报',
    to: '/dashboard/health-report'
  })
  list.push({
    icon: MessageCircle, color: '#60a5fa',
    text: '让 AI 分析今日饮食',
    detail: '基于身体数据生成个性化建议',
    to: '/dashboard/ai-consult'
  })
  return list.slice(0, 4)
})

// 快捷操作
const quickActions = [
  { label: '记录饮食', desc: '快速记录三餐', icon: Camera, color: '#E07A3F', to: '/dashboard/food-input' },
  { label: 'AI 咨询', desc: '个性化建议', icon: Sparkles, color: '#2F5D4A', to: '/dashboard/ai-consult' },
  { label: '营养分析', desc: '三大营养素', icon: PieChart, color: '#60a5fa', to: '/dashboard/nutrition' },
  { label: '运动管理', desc: '记录与围度', icon: Dumbbell, color: '#8b5cf6', to: '/dashboard/muscle-chart' },
]

// 一级功能（5 个）
const allGroups = [
  { key: 'user', title: '用户中心', icon: Users, desc: '资料与档案', items: [{}, {}, {}, {}] },
  { key: 'diet', title: '饮食管理', icon: Utensils, desc: '记录与分析', items: [{}, {}, {}, {}, {}] },
  { key: 'health', title: '健康监测', icon: HeartPulse, desc: '报告与运动', items: [{}, {}, {}] },
  { key: 'knowledge', title: '知识中心', icon: BookOpen, desc: '科普与AI', items: [{}, {}, {}] },
  { key: 'recipe', title: '菜谱美食', icon: ChefHat, desc: '食谱与偏好', items: [{}, {}] },
]
const groupColors: Record<string, string> = {
  user: '#2F5D4A', diet: '#E07A3F', health: '#2F5D4A', knowledge: '#60a5fa', recipe: '#E07A3F'
}
const groupColor = (group: any) => groupColors[group.key] || '#2F5D4A'
const groupIconStyle = (group: any, i: number) => {
  const c = groupColor(group)
  return { background: c + '15', color: c }
}
function goGroup(group: any) {
  router.push({ path: '/dashboard/hub', query: { group: group.key } })
}
function go(to: string) { router.push(to) }

onMounted(async () => {
  const [diet, snap, reports, hist, arts, pred] = await Promise.allSettled([
    api.diet.getByDate(today),
    api.profile.snapshot(),
    api.report.list(),
    api.metrics.range ? api.metrics.range(today, 7) : Promise.resolve(null),
    api.article.list({}).catch(() => []),
    api.metrics.predict ? api.metrics.predict(userStore.activeUserId || userStore.user?.user_id || 1, 7).catch(() => null) : Promise.resolve(null),
  ])
  if (diet.status === 'fulfilled') {
    const d = (diet.value as any)?.data ?? diet.value
    const meals = Array.isArray(d) ? d : []
    let kcal = 0, protein = 0, fat = 0, carb = 0, has = false
    for (const m of meals) {
      const items = m?.foods ?? m?.items ?? []
      for (const it of items) {
        const c = Number(it?.calories_kcal ?? it?.calories ?? it?.cal ?? 0)
        kcal += c; if (c) has = true
        protein += Number(it?.protein ?? 0)
        fat += Number(it?.fat ?? 0)
        carb += Number(it?.carb ?? it?.carbohydrate ?? 0)
      }
    }
    overview.value.todayKcal = has ? Math.round(kcal) : null
    overview.value.protein = Math.round(protein)
    overview.value.fat = Math.round(fat)
    overview.value.carb = Math.round(carb)
  }
  if (snap.status === 'fulfilled') {
    const s = (snap.value as any)?.data ?? snap.value
    const w = Number(s?.weight), h = Number(s?.height), bmr = Number(s?.bmr)
    if (w) overview.value.weight = w
    if (w && h) overview.value.bmi = Math.round(w / Math.pow(h / 100, 2) * 10) / 10
    if (bmr) overview.value.bmr = Math.round(bmr)
  }
  if (reports.status === 'fulfilled') {
    const r = (reports.value as any)?.data ?? reports.value
    overview.value.reportCount = Array.isArray(r) ? r.length : 0
  }
  if (hist.status === 'fulfilled') {
    const h = (hist.value as any)?.data ?? hist.value
    if (Array.isArray(h)) {
      weightHistory.value = h.map((x: any) => Number(x?.weight ?? x?.value ?? 0)).filter(Boolean)
      weightDates.value = h.map((x: any) => x?.date ?? x?.recordDate ?? '')
    }
  }
  if (arts.status === 'fulfilled') {
    const a = (arts.value as any)?.data ?? arts.value
    if (Array.isArray(a)) articles.value = a.slice(0, 3)
    else if (a?.list) articles.value = a.list.slice(0, 3)
  }
  if (pred.status === 'fulfilled') {
    const p = (pred.value as any)?.data ?? pred.value
    if (p && p.status === 'ok') prediction.value = p
  }
  if (!weightHistory.value.length && overview.value.weight) {
    weightHistory.value = [Number(overview.value.weight)]
    weightDates.value = [today]
  }

  // ===== 演示数据兜底（无真实数据时预览效果用，可删除） =====
  const hasAnyData = overview.value.todayKcal != null || overview.value.weight != null
  if (!hasAnyData) {
    overview.value.todayKcal = 1845
    overview.value.protein = 86
    overview.value.fat = 62
    overview.value.carb = 205
    overview.value.weight = 70.1
    overview.value.height = 175
    overview.value.bmi = 22.9
    overview.value.bmr = 1580
    overview.value.reportCount = 3
    weightHistory.value = [71.2, 71.0, 70.8, 70.9, 70.5, 70.3, 70.1]
    weightDates.value = ['2026-08-09', '2026-08-10', '2026-08-11', '2026-08-12', '2026-08-13', '2026-08-14', '2026-08-15']
    prediction.value = {
      status: 'ok', days: 7, trend: 'down', message: '基于近 7 日数据线性回归预测',
      points: [69.9, 69.8, 69.6, 69.5, 69.4, 69.2, 69.1]
    }
    articles.value = [
      { title: '膳食纤维：被忽视的第七营养素', summary: '25-30g/天怎么吃够，水溶与不溶来源清单', audience: '普通人群' },
      { title: '每天喝水多少才健康？', summary: '饮水建议量、时机与误区', audience: '普通人群' },
      { title: '三餐怎么搭配更均衡？', summary: '中国居民膳食餐盘法详解', audience: '普通人群' },
      { title: '减脂期蛋白质怎么吃才不流失肌肉？', summary: '每公斤体重 1.2-1.6g，三餐分配', audience: '健身人群' },
      { title: '增肌期碳水摄入策略', summary: '训练日与休息日的碳水分配', audience: '健身人群' },
      { title: '糖尿病患者早餐的升糖避坑指南', summary: '低GI主食选择与进食顺序', audience: '糖尿病患者' },
      { title: '老年人补钙：食物与补剂如何选择？', summary: '骨密度与钙摄入的循证关系', audience: '老年人' },
      { title: '孕妇孕期营养补充要点', summary: '叶酸、铁、DHA 的摄入建议', audience: '孕妇' },
      { title: '青少年长高期的营养需求', summary: '钙、蛋白质与生长激素', audience: '青少年' },
    ]
  }
})
</script>

<style scoped>
.feature-panel {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(16px) saturate(1.4);
  -webkit-backdrop-filter: blur(16px) saturate(1.4);
  border: 1px solid rgba(231, 226, 216, 0.8);
  box-shadow: 0 1px 3px rgba(31, 42, 36, 0.06), 0 4px 14px rgba(31, 42, 36, 0.05);
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s ease, border-color 0.35s ease;
}
.feature-panel:hover {
  transform: translateY(-3px);
  border-color: rgba(47, 93, 74, 0.2);
  box-shadow: 0 16px 36px -12px rgba(47, 93, 74, 0.16);
}
.panel-bg-icon {
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
}
.feature-panel:hover .panel-bg-icon {
  transform: scale(1.1);
}
.bmr-tip:hover .bmr-tooltip { display: block; }
/* BMI/BMR 悬停弹窗 */
.metric-tip:hover .metric-tooltip { display: block; }
/* 文章悬停展开 */
.article-row:hover .article-expand {
  width: 60%;
  opacity: 1;
}
.article-scroll::-webkit-scrollbar { width: 4px; }
.article-scroll::-webkit-scrollbar-thumb { background: rgba(15,23,42,0.1); border-radius: 2px; }
.article-scroll::-webkit-scrollbar-track { background: transparent; }
.greet-mark {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.greet-mark:hover {
  transform: scale(1.05) rotate(-3deg);
}
</style>
