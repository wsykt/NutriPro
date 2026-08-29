<template>
  <div class="dashboard-demo min-h-full relative">
    <div class="dk-wrap relative z-10">

      <!-- ===== 墨玉问候横幅（深壳 · 方案E 观星台背景） ===== -->
      <div class="dk-hero" ref="heroRef">
        <!-- 观星台背景层：星盘刻线 / 星河微尘 / 噪点肌理 / 掠面光泽 / 暗角 -->
        <div class="dk-hero-astro" aria-hidden="true">
          <svg width="620" height="300" viewBox="0 0 620 300">
            <g stroke="rgba(217,162,74,.2)" stroke-width="1">
              <line
                v-for="(t, i) in heroAstroTicks" :key="'t' + i"
                :x1="t.x1" :y1="t.y1" :x2="t.x2" :y2="t.y2" :opacity="t.o"
              />
            </g>
            <circle cx="310" cy="150" r="118" fill="none" stroke="rgba(217,162,74,.12)" stroke-width="1" />
            <circle cx="310" cy="150" r="96" fill="none" stroke="rgba(217,162,74,.09)" stroke-width="1" stroke-dasharray="2 6" />
            <circle cx="310" cy="150" r="142" fill="none" stroke="rgba(217,162,74,.07)" stroke-width="1" />
            <g class="dk-hero-astro-rot">
              <circle cx="310" cy="150" r="108" fill="none" stroke="rgba(217,162,74,.22)" stroke-width="1" stroke-dasharray="3 9" />
              <circle
                v-for="(p, i) in heroAstroPlanets" :key="'p' + i"
                :cx="p.cx" :cy="p.cy" :r="p.r" :fill="'rgba(232,185,115,' + p.o + ')'"
              />
            </g>
          </svg>
        </div>
        <div class="dk-hero-stars" aria-hidden="true">
          <i v-for="(s, i) in heroStars" :key="i" :class="{ big: s.big }" :style="s.style"></i>
        </div>
        <div class="dk-hero-grain" aria-hidden="true"></div>
        <div class="dk-hero-sheen" aria-hidden="true"></div>
        <div class="dk-hero-vign" aria-hidden="true"></div>
        <div class="dk-hero-main">
          <div class="dk-eyebrow" data-anim>NutriPro · Health Desk</div>
          <h1 class="dk-hello"><span class="dk-char" v-for="(c, i) in greetChars" :key="i">{{ c }}</span></h1>
          <p class="dk-hello-sub" data-anim>{{ todayText }}</p>
        </div>
        <!-- 方案 F · 数据恒星：中心热量环 + 5 分组轨道导航 -->
        <StarOrbit :percent="caloriePercent" />
        <div class="dk-datecard" data-anim>
          <span class="num">{{ todayDateNum }}</span>
          <span class="lab"><span>{{ monthLab }}</span><span>本周第 {{ weekDayIdx }} 天打卡</span></span>
        </div>
      </div>

      <!-- ===== 方案 F · 指标速览行（4 卡铺满一行，衔接深壳与浅芯） ===== -->
      <div class="stat-row" ref="statRowRef">
        <button class="stat-card" data-anim @click="go('/dashboard/food-input')">
          <span class="stat-label"><Flame class="w-3.5 h-3.5" style="color:#E07A3F" /> 今日摄入</span>
          <span class="stat-value">{{ todayKcal || '—' }}<i>kcal</i></span>
          <span class="stat-sub">早 {{ mealKcal.breakfast }} · 午 {{ mealKcal.lunch }} · 晚 {{ mealKcal.dinner }} kcal</span>
          <span class="stat-bar"><i :style="{ width: caloriePercent + '%', background: 'linear-gradient(90deg,#E07A3F,#D9A24A)' }"></i></span>
        </button>
        <button class="stat-card" data-anim @click="go('/dashboard/health-archive?tab=metrics')">
          <span class="stat-label"><Activity class="w-3.5 h-3.5" style="color:#B8863B" /> BMI</span>
          <span class="stat-value" :class="bmiClass">{{ bmi || '—' }}</span>
          <span class="stat-sub">{{ bmiLabel }}</span>
          <span class="stat-bar"><i :style="{ width: bmiBarPercent + '%', background: 'linear-gradient(90deg,#7FAE8E,#B8CE9E)' }"></i></span>
        </button>
        <button class="stat-card" data-anim @click="go('/dashboard/health-archive?tab=metrics')">
          <span class="stat-label"><Scale class="w-3.5 h-3.5" style="color:#6C8FBE" /> 当前体重</span>
          <span class="stat-value">{{ currentWeight || '—' }}<i>kg</i></span>
          <span class="stat-sub" :style="{ color: weightWeekly < 0 ? '#4E8D6E' : weightWeekly > 0 ? '#B36B2A' : 'rgba(42,38,32,0.45)' }">{{ weightWeeklyText }}</span>
          <span class="stat-bar"><i :style="{ width: '100%', background: 'linear-gradient(90deg,#6C8FBE,#8FA8C8)', opacity: currentWeight ? 0.35 : 0.12 }"></i></span>
        </button>
        <button class="stat-card" data-anim @click="go('/dashboard/health-report')">
          <span class="stat-label"><FileText class="w-3.5 h-3.5" style="color:#B8863B" /> 健康报告</span>
          <span class="stat-value">{{ reportCount }}<i>份</i></span>
          <span class="stat-sub">{{ reportSub }}</span>
          <span class="stat-bar"><i :style="{ width: reportCount ? '100%' : '8%', background: 'linear-gradient(90deg,#B8863B,#D9A24A)', opacity: reportCount ? 0.5 : 0.2 }"></i></span>
        </button>
      </div>

      <!-- ===== 暖纸浅芯面板（浅色工作区） ===== -->
      <div class="dk-sheet" ref="sheetRef">

      <!-- ===== 方案 H · Bento 网格 ===== -->
      <div class="grid grid-cols-1 md:grid-cols-12 gap-4">

        <!-- 大格：体重趋势（含预测） -->
        <div class="md:col-span-7 feature-panel rounded-2xl p-6 relative overflow-visible flex flex-col" data-anim>
          <div class="panel-bg-icon absolute -right-6 -bottom-6 pointer-events-none opacity-[0.05]"><Activity class="w-44 h-44" /></div>
          <div class="flex items-center justify-between mb-3 relative z-10 flex-wrap gap-y-2">
            <h3 class="font-semibold text-slate-800 flex items-center gap-2 text-[15px]">
              <span class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:#B8863B15;color:#B8863B"><TrendingDown class="w-4 h-4" /></span>
              体重趋势
            </h3>
            <div class="flex items-center gap-2">
              <span class="legend-dot" style="background:#B8863B"></span>
              <span class="text-[10px] text-slate-400 mr-1.5">历史</span>
              <span class="legend-dot" style="background:#E07A3F"></span>
              <span class="text-[10px] text-slate-400 mr-2">预测</span>
              <span class="text-xs px-2 py-1 rounded-full" :class="weightChangeTrend === 'down' ? 'bg-emerald-50 text-emerald-600' : weightChangeTrend === 'up' ? 'bg-amber-50 text-amber-600' : 'bg-slate-50 text-slate-500'">{{ weightChangeText }}</span>
            </div>
          </div>
          <!-- 体重趋势折线图（vue-echarts：历史实线 + 预测虚线） -->
          <div class="relative z-10 flex-1 min-h-[280px]">
            <v-chart :option="weightChartOption" autoresize class="w-full h-full" />
          </div>
          <!-- 指标 3 栏：体重 / BMI / BMR -->
          <div class="mt-3 grid grid-cols-3 gap-3 relative z-10">
            <div class="bg-slate-50 rounded-xl py-2 text-center">
              <div class="text-[10px] text-slate-400">体重</div>
              <div class="font-bold text-slate-800 tabular-nums text-sm">{{ currentWeight || '—' }}<span class="text-[9px] font-normal text-slate-400"> kg</span></div>
            </div>
            <!-- BMI：绿字 + 悬停弹窗（向上弹出，利用折线图区域空白避免底部导航遮挡） -->
            <div class="metric-tip relative bg-slate-50 rounded-xl py-2 text-center cursor-help">
              <div class="text-[10px] font-semibold" style="color:#B8863B">BMI</div>
              <div class="font-bold text-slate-800 tabular-nums text-sm" :class="bmiClass">{{ bmi || '—' }}</div>
              <div class="metric-tooltip absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 p-3 rounded-xl text-left z-50 hidden" style="background:#fff;box-shadow:0 10px 30px rgba(90,70,40,0.18);border:1px solid rgba(184,134,59,0.2)">
                <div class="text-xs font-semibold text-slate-800 mb-1">BMI 身体质量指数</div>
                <div class="text-[11px] text-slate-500 leading-relaxed mb-1.5">衡量体重与身高关系的指标，用于评估体重是否在健康范围。</div>
                <div class="text-[11px] text-slate-600 font-medium mb-1">公式</div>
                <div class="text-[10px] text-slate-500 leading-relaxed">BMI = 体重(kg) ÷ 身高(m)²</div>
                <div class="text-[10px] text-slate-500 leading-relaxed mt-1">18.5–23.9 正常 · 24–27.9 超重 · ≥28 肥胖</div>
              </div>
            </div>
            <!-- BMR：绿字 + 悬停弹窗（向上弹出，折线图空白足够承载 w-56 内容） -->
            <div class="metric-tip relative bg-slate-50 rounded-xl py-2 text-center cursor-help">
              <div class="text-[10px] font-semibold" style="color:#B8863B">BMR</div>
              <div class="font-bold text-slate-800 tabular-nums text-sm">{{ bmr || '—' }}<span class="text-[9px] font-normal text-slate-400"> kcal</span></div>
              <div class="metric-tooltip absolute bottom-full right-0 mb-2 w-56 p-3 rounded-xl text-left z-50 hidden" style="background:#fff;box-shadow:0 10px 30px rgba(90,70,40,0.18);border:1px solid rgba(184,134,59,0.2)">
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

        <!-- 营养素速览格 -->
        <div class="md:col-span-5 feature-panel rounded-2xl p-6 relative overflow-hidden flex flex-col" data-anim>
          <div class="panel-bg-icon absolute -right-6 -bottom-6 pointer-events-none opacity-[0.05]"><PieChart class="w-40 h-40" /></div>
          <div class="flex items-center justify-between mb-4 relative z-10">
            <h3 class="font-semibold text-slate-800 flex items-center gap-2 text-[15px]">
              <span class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:#6C8FBE15;color:#6C8FBE"><PieChart class="w-4 h-4" /></span>
              营养素速览
            </h3>
            <button @click="go('/dashboard/nutrition')" class="text-xs text-morandi-accent hover:underline flex items-center gap-1">详细分析 <ArrowRight class="w-3 h-3" /></button>
          </div>
          <div class="grid grid-cols-2 gap-3 flex-1 relative z-10">
            <div v-for="ring in ringData.small" :key="ring.key" class="nutri-tile flex items-center gap-3 rounded-xl px-3 py-2.5">
              <div class="relative w-14 h-14 shrink-0">
                <svg viewBox="0 0 56 56" class="w-14 h-14 -rotate-90">
                  <circle cx="28" cy="28" r="22" fill="none" stroke="rgba(0,0,0,0.05)" stroke-width="6"/>
                  <circle cx="28" cy="28" r="22" fill="none" data-ring :stroke="ring.color" stroke-width="6" stroke-linecap="round"
                        :stroke-dasharray="(ring.percent * 138.2 / 100) + ' 138.2'"/>
                </svg>
                <div class="absolute inset-0 flex items-center justify-center">
                  <span class="text-[10px] font-bold text-slate-700 tabular-nums">{{ ring.percent }}%</span>
                </div>
              </div>
              <div class="min-w-0">
                <div class="text-[12px] font-medium text-slate-700 truncate">{{ ring.label }}</div>
                <div class="text-[10px] text-slate-400 tabular-nums">{{ ring.display }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 今日待办格 -->
        <div class="md:col-span-5 feature-panel rounded-2xl p-6 relative overflow-hidden" data-anim>
          <div class="panel-bg-icon absolute -right-6 -bottom-6 pointer-events-none opacity-[0.05]"><CheckCircle2 class="w-40 h-40" /></div>
          <h3 class="font-semibold text-slate-800 mb-4 flex items-center gap-2 text-[15px] relative z-10">
            <span class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:#E07A3F15;color:#E07A3F"><CheckCircle2 class="w-4 h-4" /></span>
            今日待办
          </h3>
          <div class="space-y-2.5 relative z-10">
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

        <!-- 科普文章格 -->
        <div class="md:col-span-7 feature-panel rounded-2xl p-6 relative overflow-hidden flex flex-col" data-anim>
          <div class="panel-bg-icon absolute -right-6 -bottom-6 pointer-events-none opacity-[0.05]"><BookOpen class="w-40 h-40" /></div>
          <div class="flex items-center justify-between mb-3 relative z-10">
            <h3 class="font-semibold text-slate-800 flex items-center gap-2 text-[15px]">
              <span class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:#B8863B15;color:#B8863B"><BookOpen class="w-4 h-4" /></span>
              科普文章
            </h3>
            <button @click="go('/dashboard/articles')" class="text-xs text-morandi-accent hover:underline flex items-center gap-1">更多 <ArrowRight class="w-3 h-3" /></button>
          </div>
          <!-- 人群筛选 -->
          <div class="flex items-center gap-1.5 mb-3 flex-wrap relative z-10">
            <span class="text-[11px] text-slate-400 whitespace-nowrap">人群</span>
            <button
              v-for="af in articleAudienceFilters" :key="af.key"
              @click="articleAudience = af.key"
              class="px-2 py-0.5 rounded-full text-[11px] font-medium transition-all whitespace-nowrap"
              :class="articleAudience === af.key ? 'text-white shadow-sm' : 'bg-slate-50 text-slate-500 hover:bg-slate-100 border border-slate-100'"
              :style="articleAudience === af.key ? { background: '#B8863B' } : {}"
            >{{ af.label }}</button>
          </div>
          <!-- 文章窄条列表（可滚动） -->
          <div class="article-scroll space-y-2 max-h-[240px] overflow-y-auto pr-1 relative z-10 flex-1">
            <div v-for="(art, i) in filteredArticles" :key="i"
                 @click="go('/dashboard/articles')"
                 class="article-row group relative flex items-center gap-3 p-2.5 rounded-xl border border-slate-100 hover:border-morandi-accent/30 hover:bg-white transition-all cursor-pointer overflow-hidden">
              <!-- 悬停金色光条（从右侧滑入，仅色带无文字） -->
              <div class="article-expand absolute right-0 top-0 bottom-0 w-0 overflow-hidden opacity-0 transition-all duration-300"
                   style="background:linear-gradient(90deg,transparent 0%,rgba(184,134,59,0.08) 45%,rgba(184,134,59,0.16) 100%);border-left:2px solid rgba(184,134,59,0.45)"></div>
              <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style="background:#B8863B15;color:#B8863B">
                <Newspaper class="w-4 h-4" />
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-[13px] font-medium text-slate-700 truncate">{{ art.title }}</div>
                <div class="text-[10px] text-slate-400 mt-0.5 flex items-center gap-2">
                  <span v-if="art.audience" class="px-1.5 py-px rounded-full" style="background:#B8863B12;color:#B8863B">{{ art.audience }}</span>
                  <span class="truncate">{{ art.summary || '点击阅读' }}</span>
                </div>
              </div>
              <ArrowRight class="w-3.5 h-3.5 text-slate-300 shrink-0 transition-all duration-200 group-hover:translate-x-0.5 group-hover:text-amber-600" />
            </div>
            <div v-if="!filteredArticles.length" class="text-center py-4 text-xs text-slate-400">该人群暂无文章</div>
          </div>
        </div>

        <!-- 下一步行动卡（习惯闭环收尾） -->
        <div v-if="nextAction" class="act-card md:col-span-12 flex-wrap" data-anim @click="go(nextAction.to)">
          <span class="act-dot" aria-hidden="true"></span>
          <span class="act-chip">下一步</span>
          <div class="flex-1 min-w-0">
            <div class="act-title truncate">{{ nextAction.text }}</div>
            <div class="act-sub truncate">{{ actSub }} · {{ nextAction.detail }}</div>
          </div>
          <span class="act-cta">去完成 <i>→</i></span>
        </div>

      </div><!-- /bento -->

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
            class="feature-panel rounded-2xl p-4 flex items-center gap-3 text-left transition-all hover:-translate-y-1 relative overflow-hidden" data-anim>
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

      </div><!-- /dk-sheet -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { gsap } from 'gsap'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'
import StarOrbit from './StarOrbit.vue'
import echarts, { VChart } from '@/utils/echarts'
import {
  User, Activity, FileText, UsersRound,
  Utensils, PlusCircle, PieChart, Search,
  BarChart3, Dumbbell,
  BookOpen, Newspaper, MessageCircle, ClipboardList,
  Flame, Scale, ArrowRight, TrendingDown, CheckCircle2,
  Camera, Mic, Sparkles, Calendar, Zap, Info
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const username = computed(() => userStore.user?.username || '朋友')
const today = new Date().toISOString().slice(0, 10)

/* ===== 方案E 观星台：Hero 背景图层数据（稳定种子随机，刷新布局不变） ===== */
function mulberry32(a: number) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/* 星盘刻线：60 根刻度（每 5 根加长） */
const heroAstroTicks = Array.from({ length: 60 }, (_, i) => {
  const a = (i / 60) * Math.PI * 2
  const long = i % 5 === 0
  const r1 = long ? 128 : 133
  return {
    x1: +(310 + Math.cos(a) * r1).toFixed(1),
    y1: +(150 + Math.sin(a) * r1).toFixed(1),
    x2: +(310 + Math.cos(a) * 138).toFixed(1),
    y2: +(150 + Math.sin(a) * 138).toFixed(1),
    o: long ? 0.9 : 0.45
  }
})

/* 旋转虚线大环上的行星点 */
const heroPlanet = (deg: number, r: number, size: number, o: number) => {
  const a = (deg * Math.PI) / 180
  return { cx: +(310 + Math.cos(a) * r).toFixed(1), cy: +(150 + Math.sin(a) * r).toFixed(1), r: size, o }
}
const heroAstroPlanets = [heroPlanet(30, 108, 2.6, 0.55), heroPlanet(168, 108, 1.8, 0.4), heroPlanet(285, 108, 1.4, 0.3)]

/* 42 颗星尘（大小 / 相位错开） */
const heroStars = (() => {
  const rnd = mulberry32(7)
  return Array.from({ length: 42 }, () => {
    const big = rnd() > 0.86
    const size = big ? 2.4 : 1 + rnd() * 1.2
    return {
      big,
      style: `left:${(rnd() * 100).toFixed(2)}%;top:${(rnd() * 100).toFixed(2)}%;width:${size.toFixed(1)}px;height:${size.toFixed(1)}px;--o:${(0.22 + rnd() * 0.58).toFixed(2)};--d:${(2.6 + rnd() * 2.6).toFixed(2)}s;--dl:${(rnd() * -5).toFixed(2)}s`
    }
  })
})()

// ===== 墨玉问候横幅 =====
const heroRef = ref<HTMLElement | null>(null)
const sheetRef = ref<HTMLElement | null>(null)
const statRowRef = ref<HTMLElement | null>(null)
const todayDateNum = new Date().getDate()
const monthLab = new Date().toLocaleDateString('zh-CN', { month: 'long', weekday: 'long' })
const weekDayIdx = (() => { const d = new Date().getDay(); return d === 0 ? 7 : d })()

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

// ===== 方案 F · 指标速览行 =====
// 三餐热量分解（早餐/午餐/晚餐）
const mealKcal = ref({ breakfast: 0, lunch: 0, dinner: 0 })
function classifyMeal(t: any): 'breakfast' | 'lunch' | 'dinner' {
  const s = String(t ?? '')
  if (/早|breakfast/i.test(s)) return 'breakfast'
  if (/晚|dinner|supper/i.test(s)) return 'dinner'
  return 'lunch'
}
// BMI 分类文案 + 速览条百分比（18.5~23.9 正常区间映射到 40~80%）
const bmiLabel = computed(() => {
  const b = overview.value.bmi
  if (b == null) return '记录身高体重后生成'
  if (b < 18.5) return '偏瘦 · 建议均衡增重'
  if (b < 24) return '正常范围 · 保持'
  if (b < 28) return '超重 · 注意控糖控油'
  return '肥胖 · 建议循序渐进干预'
})
const bmiBarPercent = computed(() => {
  const b = overview.value.bmi
  if (b == null) return 6
  return Math.max(6, Math.min(100, 40 + (b - 18.5) / (23.9 - 18.5) * 40))
})
// 体重周变化（15 天窗口 ≈ 2 周）
const weightWeekly = computed(() => {
  const c = weightChange.value
  if (!c) return 0
  return Math.round(c / 2 * 10) / 10
})
const weightWeeklyText = computed(() => {
  const w = weightWeekly.value
  if (!w) return '近期保持平稳'
  return (w < 0 ? '↓ ' : '↑ ') + Math.abs(w).toFixed(1) + ' kg / 周'
})
const reportSub = computed(() => reportCount.value ? '周报已生成 · 可回顾' : '记录饮食后自动生成')

const nutritionBars = computed(() => [
  { label: '蛋白质', value: proteinG.value, target: proteinTarget, color: '#2F5D4A', percent: proteinPercent.value },
  { label: '脂肪', value: fatG.value, target: fatTarget, color: '#E07A3F', percent: fatPercent.value },
  { label: '碳水', value: carbG.value, target: carbTarget, color: '#8A928C', percent: carbPercent.value },
])

// 5 个圆环：热量大圈红 + 蛋白蓝/脂肪黄/碳水绿/纤维暖灰
const ringData = computed(() => ({
  heat: { display: todayKcal.value ? String(todayKcal.value) : '—', percent: caloriePercent.value, color: '#D97B6C' },
  small: [
    { key: 'protein', label: '蛋白质', display: proteinG.value + 'g', percent: proteinPercent.value, color: '#6C8FBE' },
    { key: 'carb', label: '碳水', display: carbG.value + 'g', percent: carbPercent.value, color: '#7FAE8E' },
    { key: 'fat', label: '脂肪', display: fatG.value + 'g', percent: fatPercent.value, color: '#D9BC6B' },
    { key: 'fiber', label: '膳食纤维', display: fiberG.value + 'g', percent: fiberPercent.value, color: '#A8998A' },
  ]
}))

// 体重趋势（ECharts 折线：历史实线 + 预测虚线）
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
          borderColor: (p: any) => (p.dataIndex === lastHistIdx ? '#fff' : '#B8863B'),
          borderWidth: (p: any) => (p.dataIndex === lastHistIdx ? 2.5 : 2),
        },
        lineStyle: { color: '#B8863B', width: 2.5, cap: 'round' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(184,134,59,0.22)' },
            { offset: 1, color: 'rgba(184,134,59,0.0)' },
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
      icon: Sparkles, color: '#B8863B',
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
    icon: MessageCircle, color: '#6C8FBE',
    text: '让 AI 分析今日饮食',
    detail: '基于身体数据生成个性化建议',
    to: '/dashboard/ai-consult'
  })
  return list.slice(0, 4)
})

// ===== 行动卡（下一步）：取第一项待办，聚合数据副文案 =====
const remainKcal = computed(() => Math.max(0, calorieTarget - todayKcal.value))
const nextAction = computed(() => todos.value[0] || null)
const actSub = computed(() => {
  const parts: string[] = []
  parts.push(todayKcal.value < calorieTarget ? '还可摄入 ' + remainKcal.value + ' kcal' : '已达到今日目标')
  parts.push('今日 ' + todos.value.length + ' 项待办')
  return parts.join(' · ')
})

// 快捷操作
const quickActions = [
  { label: '记录饮食', desc: '快速记录三餐', icon: Camera, color: '#E07A3F', to: '/dashboard/food-input' },
  { label: 'AI 咨询', desc: '个性化建议', icon: Sparkles, color: '#B8863B', to: '/dashboard/ai-consult' },
  { label: '营养分析', desc: '三大营养素', icon: PieChart, color: '#6C8FBE', to: '/dashboard/nutrition' },
  { label: '运动管理', desc: '记录与围度', icon: Dumbbell, color: '#B36B2A', to: '/dashboard/muscle-chart' },
]

function go(to: string) { router.push(to) }

// ===== GSAP 入场：横幅 → 指标速览行 → 浅芯面板逐块浮现 =====
function animateEntrance() {
  const hero = heroRef.value
  const sheet = sheetRef.value
  const statRow = statRowRef.value
  if (hero) {
    gsap.fromTo(hero.querySelectorAll('[data-anim]'),
      { opacity: 0, y: 24 },
      { opacity: 1, y: 0, duration: 0.7, stagger: 0.09, ease: 'power3.out' })
    gsap.fromTo(hero.querySelectorAll('.dk-char'),
      { opacity: 0, y: 16, filter: 'blur(8px)' },
      { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.55, stagger: 0.035, delay: 0.18, ease: 'power2.out' })
  }
  if (statRow) {
    gsap.fromTo(statRow.querySelectorAll('[data-anim]'),
      { opacity: 0, y: 26 },
      { opacity: 1, y: 0, duration: 0.7, stagger: 0.07, delay: 0.2, ease: 'power3.out' })
  }
  if (sheet) {
    gsap.fromTo(sheet.querySelectorAll('[data-anim]'),
      { opacity: 0, y: 26 },
      { opacity: 1, y: 0, duration: 0.75, stagger: 0.07, delay: 0.34, ease: 'power3.out' })
  }
}

onMounted(() => {
  animateEntrance()
})

onMounted(async () => {
  const [diet, snap, reports, hist, arts, pred] = await Promise.allSettled([
    api.diet.getByDate(today),
    api.profile.snapshot(),
    api.report.list(),
    // metrics.range(userId, startDate, endDate)：修复旧代码把 today 当 userId、把 7 当 startDate 的参数错位
    api.metrics.range ? api.metrics.range(userStore.activeUserId || userStore.user?.user_id || 1, new Date(Date.now() - 7 * 864e5).toISOString().slice(0, 10), today) : Promise.resolve(null),
    api.article.list({}).catch(() => []),
    api.metrics.predict ? api.metrics.predict(userStore.activeUserId || userStore.user?.user_id || 1, 7).catch(() => null) : Promise.resolve(null),
  ])
  if (diet.status === 'fulfilled') {
    const d = (diet.value as any)?.data ?? diet.value
    const meals = Array.isArray(d) ? d : []
    let kcal = 0, protein = 0, fat = 0, carb = 0, has = false
    const slots = { breakfast: 0, lunch: 0, dinner: 0 }
    for (const m of meals) {
      const items = m?.items ?? m?.foods ?? []
      const slot = classifyMeal(m?.mealType ?? m?.meal_type)
      for (const it of items) {
        // 后端返回的 calorie/protein/fat/carb 均为「每100克」的营养值，需按实际食用重量 eatWeight 折算
        const factor = Number(it?.eatWeight ?? it?.quantity ?? 0) / 100
        const c = Number(it?.calorie ?? it?.calories ?? 0) * factor
        kcal += c; if (c) has = true
        if (slot === 'breakfast') slots.breakfast += c
        else if (slot === 'dinner') slots.dinner += c
        else slots.lunch += c
        protein += Number(it?.protein ?? 0) * factor
        fat += Number(it?.fat ?? 0) * factor
        carb += Number(it?.carb ?? it?.carbohydrate ?? 0) * factor
      }
    }
    mealKcal.value = { breakfast: Math.round(slots.breakfast), lunch: Math.round(slots.lunch), dinner: Math.round(slots.dinner) }
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
  // 注意：不再注入演示假数据。无真实数据时页面显示空态（— / 暂无数据）
})
</script>

<style scoped>
/* ========== 墨玉问候横幅（深壳） ========== */
.dk-wrap {
  padding: 18px 26px 48px;
}
.dk-hero {
  position: relative;
  display: flex;
  align-items: center; /* 文字块垂直居中，避免沉底偏下 */
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
  padding: 30px 34px;
  border-radius: 24px;
  overflow: hidden;
  isolation: isolate;
  background:
    radial-gradient(circle at 14% 10%, rgba(232, 185, 115, .11) 0%, transparent 42%),
    radial-gradient(circle at 88% 88%, rgba(179, 107, 42, .09) 0%, transparent 46%),
    radial-gradient(ellipse at 72% -24%, rgba(126, 92, 46, .16) 0%, transparent 52%),
    linear-gradient(168deg, #17130D 0%, #100D0A 52%, #0B0908 100%);
  border: 1px solid rgba(232, 185, 115, 0.14);
  color: #F6EAD6;
  margin-bottom: 18px;
  /* 方案E · 观星台：顶缘金线 + 内侧描边 + 落影 */
  box-shadow:
    inset 0 1px 0 rgba(232, 185, 115, .13),
    inset 0 0 0 1px rgba(232, 185, 115, .04),
    0 24px 60px -32px rgba(46, 42, 34, .5);
}
/* 文字侧墨玉压暗，保证问候语可读性 */
.dk-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(90deg, rgba(9, 7, 5, .5), transparent 52%);
}
/* ===== 方案E · 观星台背景图层 ===== */
.dk-hero-astro,
.dk-hero-stars,
.dk-hero-grain,
.dk-hero-sheen,
.dk-hero-vign {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}
/* 星盘刻线：置于轨道导航后方 */
.dk-hero-astro svg {
  position: absolute;
  right: -70px;
  top: 50%;
  transform: translateY(-50%);
}
.dk-hero-astro-rot {
  animation: dkAstroRot 75s linear infinite;
  transform-origin: 310px 150px;
}
@keyframes dkAstroRot {
  to { transform: rotate(360deg); }
}
/* 星河微尘：缓慢明灭 */
.dk-hero-stars i {
  position: absolute;
  border-radius: 50%;
  background: rgba(232, 185, 115, .9);
  animation: dkStarTwinkle var(--d, 3.4s) ease-in-out var(--dl, 0s) infinite;
}
.dk-hero-stars i.big {
  box-shadow: 0 0 7px rgba(232, 185, 115, .85);
}
@keyframes dkStarTwinkle {
  0%, 100% { opacity: var(--o, .5); transform: scale(1); }
  50% { opacity: calc(var(--o, .5) * .18); transform: scale(.82); }
}
/* 墨玉噪点肌理 */
.dk-hero-grain {
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/><feColorMatrix type='saturate' values='0'/></filter><rect width='160' height='160' filter='url(%23n)' opacity='0.5'/></svg>");
  opacity: .055;
  mix-blend-mode: overlay;
}
/* 掠面光泽：每 9.5s 扫过一次 */
.dk-hero-sheen {
  background: linear-gradient(105deg, transparent 42%, rgba(232, 185, 115, .055) 50%, transparent 58%);
  background-size: 320% 100%;
  background-repeat: no-repeat;
  animation: dkSheen 9.5s ease-in-out infinite;
}
@keyframes dkSheen {
  0%, 56% { background-position: 130% 0; }
  88%, 100% { background-position: -70% 0; }
}
/* 暗角聚焦 */
.dk-hero-vign {
  background: radial-gradient(ellipse at 46% 40%, transparent 56%, rgba(5, 4, 3, .52) 100%);
}
.dk-hero-main { position: relative; z-index: 1; flex: 1; min-width: 260px; }
.dk-eyebrow {
  font-size: 10px;
  letter-spacing: 0.4em;
  text-transform: uppercase;
  color: #D9A24A;
  margin-bottom: 12px;
}
.dk-hello {
  font-family: 'Noto Serif SC', serif;
  font-size: clamp(26px, 3.2vw, 38px);
  font-weight: 900;
  line-height: 1.2;
  color: #F6EAD6;
}
.dk-hello em,
.dk-hello .dk-char {
  font-style: normal;
}
.dk-hello .dk-char {
  display: inline-block;
  will-change: transform, opacity, filter;
}
.dk-hello-sub {
  font-size: 12px;
  color: rgba(246, 234, 214, 0.45);
  margin-top: 8px;
  letter-spacing: 0.06em;
}
.dk-datecard {
  position: relative;
  z-index: 1;
  align-self: flex-end; /* 日期卡保持右下角锚点，不随文字居中抬升 */
  display: flex;
  align-items: center;
  gap: 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(232, 185, 115, 0.16);
  border-radius: 16px;
  padding: 12px 20px;
  backdrop-filter: blur(10px);
}
.dk-datecard .num {
  font-family: 'Noto Serif SC', serif;
  font-size: 30px;
  font-weight: 900;
  color: #E8B973;
  line-height: 1;
}
.dk-datecard .lab {
  font-size: 11px;
  color: rgba(246, 234, 214, 0.45);
  line-height: 1.6;
}
.dk-datecard .lab span { display: block; }

/* ---- 方案 F · 指标速览行（4 卡铺满） ---- */
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}
.stat-card {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 16px 20px 15px;
  border-radius: 18px;
  text-align: left;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px) saturate(1.3);
  -webkit-backdrop-filter: blur(12px) saturate(1.3);
  border: 1px solid rgba(184, 134, 59, 0.18);
  box-shadow: 0 1px 3px rgba(90, 70, 40, 0.05), 0 10px 28px -14px rgba(90, 70, 40, 0.12);
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s ease, border-color 0.35s ease;
}
.stat-card:hover {
  transform: translateY(-3px);
  border-color: rgba(184, 134, 59, 0.45);
  box-shadow: 0 24px 44px -22px rgba(90, 70, 40, 0.28);
}
.stat-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: rgba(42, 38, 32, 0.55);
}
.stat-value {
  font-family: 'Noto Serif SC', serif;
  font-size: 28px;
  font-weight: 900;
  color: #2A2620;
  line-height: 1.15;
}
.stat-value i {
  font-style: normal;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 12px;
  font-weight: 600;
  color: rgba(42, 38, 32, 0.45);
  margin-left: 5px;
}
.stat-sub {
  font-size: 11px;
  color: rgba(42, 38, 32, 0.45);
  font-variant-numeric: tabular-nums;
}
.stat-bar {
  width: 100%;
  height: 4px;
  border-radius: 99px;
  background: rgba(184, 134, 59, 0.12);
  margin-top: 3px;
  overflow: hidden;
}
.stat-bar i {
  display: block;
  height: 100%;
  border-radius: 99px;
  transition: width 1.2s cubic-bezier(0.22, 1, 0.36, 1) 0.3s;
}
@media (max-width: 1100px) {
  .stat-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .stat-row { grid-template-columns: 1fr; }
}

/* ========== 暖纸浅芯面板（浅色工作区） ========== */
.dk-sheet {
  position: relative;
  background:
    radial-gradient(circle at 18% 0%, rgba(184, 134, 59, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 86% 100%, rgba(201, 143, 62, 0.06) 0%, transparent 44%),
    linear-gradient(180deg, #F8F4EA 0%, #F2EBDC 100%);
  border: 1px solid rgba(232, 185, 115, 0.24);
  border-radius: 24px;
  padding: 22px 22px 26px;
  box-shadow: 0 30px 60px -34px rgba(90, 70, 40, 0.28);
}

/* ---- 卡片（暖纸玻璃） ---- */
.feature-panel {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px) saturate(1.3);
  -webkit-backdrop-filter: blur(12px) saturate(1.3);
  border: 1px solid rgba(184, 134, 59, 0.18);
  box-shadow: 0 1px 3px rgba(90, 70, 40, 0.05), 0 10px 28px -14px rgba(90, 70, 40, 0.12);
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s ease, border-color 0.35s ease;
}
.feature-panel:hover {
  transform: translateY(-3px);
  border-color: rgba(184, 134, 59, 0.45);
  box-shadow: 0 24px 44px -22px rgba(90, 70, 40, 0.28);
}
.panel-bg-icon {
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
}
.feature-panel:hover .panel-bg-icon {
  transform: scale(1.1);
}

/* ---- 圆环：数据到达时平滑绘制 ---- */
circle[data-ring] {
  transition: stroke-dasharray 1.2s cubic-bezier(0.22, 1, 0.36, 1) 0.2s;
}

/* ---- 行动卡（下一步 · 习惯闭环收尾） ---- */
.act-card {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 15px 20px;
  border-radius: 16px;
  cursor: pointer;
  background: linear-gradient(100deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.62));
  border: 1px solid rgba(224, 122, 63, 0.35);
  box-shadow: 0 1px 3px rgba(90, 70, 40, 0.05), 0 10px 28px -14px rgba(224, 122, 63, 0.28);
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s ease, border-color 0.35s ease;
}
.act-card:hover {
  transform: translateY(-3px);
  border-color: rgba(224, 122, 63, 0.6);
  box-shadow: 0 24px 44px -20px rgba(224, 122, 63, 0.38);
}
.act-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, #E07A3F, #D9A24A);
}
.act-dot {
  position: relative;
  width: 10px; height: 10px;
  border-radius: 50%;
  background: #E07A3F;
  flex-shrink: 0;
  margin-right: 3px;
}
.act-dot::after {
  content: '';
  position: absolute;
  inset: -5px;
  border-radius: 50%;
  border: 1.5px solid rgba(224, 122, 63, 0.55);
  animation: actPulse 1.8s ease-out infinite;
}
@keyframes actPulse {
  0%   { transform: scale(0.55); opacity: 1; }
  100% { transform: scale(1.7); opacity: 0; }
}
.act-chip {
  font-size: 10px;
  letter-spacing: 0.22em;
  color: #A8632B;
  background: rgba(224, 122, 63, 0.1);
  border: 1px solid rgba(224, 122, 63, 0.3);
  border-radius: 999px;
  padding: 4px 11px;
  white-space: nowrap;
  flex-shrink: 0;
}
.act-title { font-size: 14px; font-weight: 700; color: #2A2620; }
.act-sub { font-size: 11px; color: rgba(42, 38, 32, 0.5); margin-top: 2px; }
.act-cta {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #F8F4EA;
  background: linear-gradient(120deg, #D9A24A, #B8863B);
  border-radius: 999px;
  padding: 9px 18px;
  box-shadow: 0 6px 16px -6px rgba(184, 134, 59, 0.55);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
  white-space: nowrap;
  flex-shrink: 0;
}
.act-card:hover .act-cta {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 10px 22px -8px rgba(184, 134, 59, 0.65);
}
.act-cta i { font-style: normal; transition: transform 0.3s ease; }
.act-card:hover .act-cta i { transform: translateX(3px); }

/* ---- 趋势图例点 / 营养素小格 ---- */
.legend-dot { width: 14px; height: 2px; border-radius: 2px; display: inline-block; }
.nutri-tile {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(184, 134, 59, 0.14);
  transition: border-color 0.3s ease, transform 0.3s ease;
}
.nutri-tile:hover { border-color: rgba(184, 134, 59, 0.4); transform: translateY(-2px); }

/* ---- 暖纸色系覆盖（Tailwind slate → 暖炭墨） ---- */
.dk-sheet .text-slate-800 { color: #2A2620; }
.dk-sheet .text-slate-700 { color: #3A342B; }
.dk-sheet .text-slate-600 { color: rgba(42, 38, 32, 0.66); }
.dk-sheet .text-slate-500 { color: rgba(42, 38, 32, 0.55); }
.dk-sheet .text-slate-400 { color: rgba(42, 38, 32, 0.45); }
.dk-sheet .text-slate-300 { color: rgba(42, 38, 32, 0.32); }
.dk-sheet .bg-slate-50 { background: rgba(255, 255, 255, 0.6); }
.dk-sheet .bg-slate-100 { background: rgba(184, 134, 59, 0.08); }
.dk-sheet .border-slate-100 { border-color: rgba(184, 134, 59, 0.16); }
.dk-sheet .text-morandi-accent { color: #B8863B; }
.dk-sheet .hover\:border-morandi-accent\/30:hover { border-color: rgba(184, 134, 59, 0.45); }

/* ---- BMI/BMR 悬停弹窗 ---- */
.metric-tip:hover .metric-tooltip { display: block; }
/* ---- 文章悬停展开 ---- */
.article-row:hover .article-expand {
  width: 60%;
  opacity: 1;
}
.article-scroll::-webkit-scrollbar { width: 4px; }
.article-scroll::-webkit-scrollbar-thumb { background: rgba(184, 134, 59, 0.25); border-radius: 2px; }
.article-scroll::-webkit-scrollbar-track { background: transparent; }
</style>
