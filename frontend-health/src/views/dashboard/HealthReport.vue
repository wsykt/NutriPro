<template>
  <div class="health-report min-h-screen">
    <!-- 操作按钮 -->
    <div class="flex flex-wrap items-center gap-2 mb-3 pt-1">
      <button class="save-btn inline-flex items-center gap-1.5">
        <component :is="Download" class="w-4 h-4" />
        保存本期{{ reportType === 'weekly' ? '周报' : '月报' }}
      </button>
      <div class="tabs inline-flex gap-2">
        <button class="tab" :class="{ active: reportType === 'weekly' }" @click="switchTab('weekly')">
          <component :is="Calendar" class="w-3.5 h-3.5" />周报
        </button>
        <button class="tab" :class="{ active: reportType === 'monthly' }" @click="switchTab('monthly')">
          <component :is="CalendarDays" class="w-3.5 h-3.5" />月报
        </button>
      </div>
      <div class="ml-auto flex flex-wrap gap-2">
        <button class="ai-btn" :disabled="aiPreparing" @click="askAI">
          <component :is="Sparkles" class="w-3.5 h-3.5" />
          <span>{{ aiPreparing ? '正在整理数据...' : aiBtnText }}</span>
          <small class="ai-btn-sub">{{ aiPreparing ? '稍候' : '跳转到 AI 咨询页' }}</small>
        </button>
        <button class="sec-btn" @click="go('/dashboard/recipe-library')">
          <component :is="ChefHat" class="w-3.5 h-3.5" />搜索健康菜谱
        </button>
        <button class="sec-btn" @click="doPrint">
          <component :is="Printer" class="w-3.5 h-3.5" />打印 / 保存 PDF
        </button>
      </div>
    </div>

    <!-- 标题 -->
    <div class="hero-panel">
      <div class="hero-mark">
        <component :is="Activity" class="w-5 h-5" />
      </div>
      <div>
        <h1 class="hero-title">{{ userInfo.username || '你' }}的饮食 & 运动{{ reportType === 'weekly' ? '周' : '月' }}报</h1>
        <p class="hero-sub">
          身高 <b>{{ userInfo.height || '--' }} cm</b> · 体重 <b>{{ userInfo.weight || '--' }} kg</b> ·
          BMI <b>{{ bmi || '--' }}</b> · <b>{{ crowdTypeText }}</b>
        </p>
      </div>
    </div>

    <!-- 三卡：打卡 / 体重对比 / 运动对比 -->
    <div class="top-row">
      <div class="panel">
        <component :is="CalendarCheck" class="bg-icon w-24 h-24" />
        <div class="card-head">
          <div class="icon-box"><component :is="CalendarCheck" class="w-4 h-4" /></div>
          <h3>{{ reportType === 'weekly' ? '本周' : '本月' }}打卡记录</h3>
        </div>
        <!-- 周报：7 格一排紧凑日历 -->
        <template v-if="reportType === 'weekly'">
          <div class="week-head">
            <span v-for="n in weekNumberHead" :key="'n'+n">{{ n }}</span>
          </div>
          <div class="heat-row">
            <button
              v-for="(c, i) in weekHeatCells"
              :key="'w'+i"
              class="heat-cell"
              :class="c.checked ? 'lv1' : 'lv0'"
            >
              <span v-if="c.checked">✓</span>
            </button>
          </div>
          <div class="heat-dow">
            <span v-for="d in ['一','二','三','四','五','六','日']" :key="'d'+d">{{ d }}</span>
          </div>
          <div class="heat-foot">
            <span class="hf-lbl">打卡</span>
            <span class="hf-val">{{ weekHeatCells.filter(c=>c.checked).length }} / {{ weekHeatCells.length }} 天</span>
          </div>
        </template>
        <!-- 月报：5×7 日历 -->
        <template v-else>
          <div class="heat-calendar">
            <div v-for="(d,i) in ['一','二','三','四','五','六','日']" :key="'hd'+i"
                 class="cal-dow" :class="{ we: i >= 5 }">{{ d }}</div>
            <button
              v-for="(c, i) in monthHeatCells"
              :key="'m'+i"
              class="heat-cell"
              :class="[
                c.placeholder ? 'placeholder' : (c.checked ? 'lv1' : 'lv0')
              ]"
            >{{ c.day || '' }}</button>
          </div>
          <div class="heat-foot">
            <span class="hf-lbl">打卡</span>
            <span class="hf-val">{{ monthHeatCells.filter(c=>c.checked).length }} / {{ monthHeatCells.filter(c=>!c.placeholder).length }} 天</span>
          </div>
        </template>
      </div>

      <div class="panel">
        <component :is="Scale" class="bg-icon w-24 h-24" />
        <div class="card-head">
          <div class="icon-box"><component :is="Scale" class="w-4 h-4" /></div>
          <h3>{{ reportType === 'weekly' ? '本周' : '本月' }}体重对比</h3>
        </div>
        <div class="cmp-item">
          <div class="row"><span>最高体重</span><b>{{ wCmp.max }} kg</b></div>
          <div class="row"><span>最低体重</span><b>{{ wCmp.min }} kg</b></div>
          <div class="row"><span>周期变化</span><b :class="wCmp.diff < 0 ? 'down' : wCmp.diff > 0 ? 'up' : ''">{{ wCmp.diff > 0 ? '+' : '' }}{{ wCmp.diff }} kg</b></div>
          <div class="row"><span>{{ wCmp.diff <= 0 ? '减重' : '增重' }}</span><b>{{ Math.abs(wCmp.diff) }} kg</b></div>
          <div class="row"><span>日均波动</span><b>{{ wCmp.avg }} kg</b></div>
        </div>
      </div>

      <div class="panel">
        <component :is="Dumbbell" class="bg-icon w-24 h-24" />
        <div class="card-head">
          <div class="icon-box"><component :is="Dumbbell" class="w-4 h-4" /></div>
          <h3>{{ reportType === 'weekly' ? '本周' : '本月' }}运动对比</h3>
        </div>
        <div class="ex-summary">
          本周共消耗 <b>{{ exCmp.totalKcal }} kcal</b> ·
          运动 <b>{{ exCmp.days }} 天</b> ·
          总时长 <b>{{ exCmp.totalMin }} min</b> ·
          平均每次 <b>{{ exCmp.avgMin }} min</b> ·
          平均每次消耗 <b>{{ exCmp.avgKcal }} kcal</b>
        </div>
        <div class="cmp-item">
          <div class="row"><span>运动天数</span><b>{{ exCmp.days }} 天</b></div>
          <div class="row"><span>总时长</span><b>{{ exCmp.totalMin }} min <em>达标</em></b></div>
          <div class="row"><span>平均每次</span><b>{{ exCmp.avgMin }} min</b></div>
          <div class="row"><span>消耗热量</span><b>{{ exCmp.totalKcal }} kcal</b></div>
        </div>
      </div>
    </div>

    <!-- 第二行：体重趋势 + 营养达标（两卡并排一行） -->
    <div class="mid-row">

    <!-- 体重趋势 -->
    <div class="panel">
      <component :is="TrendingDown" class="bg-icon w-24 h-24" />
      <div class="card-head">
        <div class="icon-box"><component :is="TrendingDown" class="w-4 h-4" /></div>
        <h3>{{ reportType === 'weekly' ? '本周' : '本月' }}体重趋势</h3>
      </div>
      <svg viewBox="0 0 380 200" preserveAspectRatio="xMidYMid meet" class="w-svg">
        <!-- Y 轴标签 -->
        <g class="y-label">
          <text v-for="(y,i) in yLabels" :key="'yl'+i" :x="8" :y="y.y">{{ y.v }}</text>
        </g>
        <!-- 网格线 -->
        <g stroke="#EEEBE0" stroke-width="1">
          <line v-for="(y,i) in yLabels" :key="'yg'+i" :x1="50" :y1="y.y" :x2="372" :y2="y.y" />
        </g>
        <!-- 分隔 -->
        <line v-if="weightPredDots.length" :x1="splitX" y1="26" :x2="splitX" y2="172" stroke="#E0DCD0" stroke-width="1" stroke-dasharray="3 3" />
        <text v-if="weightPredDots.length" class="split-label" :x="splitX + 4" y="40">预测</text>
        <!-- 历史实线 -->
        <polyline :points="weightHistPoints" fill="none" stroke="#3B8A5E" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" />
        <!-- 预测虚线 -->
        <polyline v-if="weightPredDots.length" :points="weightPredLine" fill="none" stroke="#E07A3F" stroke-width="2" stroke-dasharray="4 3" stroke-linejoin="round" stroke-linecap="round" />
        <!-- 历史圆点 -->
        <g v-for="(p,i) in weightHistDots" :key="'whd'+i">
          <circle :cx="p.x" :cy="p.y" r="4" fill="#fff" stroke="#3B8A5E" stroke-width="2" />
          <text class="pt-label" :x="p.x" :y="p.y - 8">{{ p.v }}</text>
        </g>
        <!-- 预测点：空心 + hover 显示 -->
        <g v-for="(p,i) in weightPredDots" :key="'wpd'+i">
          <circle :cx="p.x" :cy="p.y" r="4" fill="#FFF4E8" stroke="#E07A3F" stroke-width="2" />
          <circle class="hit" :cx="p.x" :cy="p.y" r="10" fill="transparent">
            <title>预测体重：{{ p.v }} kg</title>
          </circle>
        </g>
        <!-- X 轴标签 -->
        <g class="x-label">
          <text v-for="(x,i) in xLabels" :key="'xl'+i" :x="x.x" :y="194">{{ x.v }}</text>
        </g>
      </svg>
    </div>

    <!-- 营养达标（环形图 + BMR + 警告 + 文章） -->
    <div class="panel">
      <component :is="Apple" class="bg-icon w-24 h-24" />
      <div class="card-head">
        <div class="icon-box"><component :is="Apple" class="w-4 h-4" /></div>
        <h3>{{ reportType === 'weekly' ? '本周' : '本月' }}营养达标</h3>
      </div>
      <!-- BMR 纯文字 -->
      <div class="bmr-ratio">
        <component :is="Flame" class="w-4 h-4" style="color:#E07A3F;flex-shrink:0" />
        <span>
          日均 <b>{{ bmrData.avgKcal }} kcal</b> / BMR <b>{{ bmrData.bmr }} kcal</b> = <b>{{ bmrData.ratio }}%</b>
          <span class="bmr-status" :class="bmrData.statusClass">{{ bmrData.statusText }}</span>
        </span>
      </div>
      <!-- 环形图网格 -->
      <div class="nutri-donut">
        <div v-for="(n, i) in nutriList" :key="'n'+i" class="nd-item">
          <v-chart :option="donutOpts[i]" autoresize class="nd-chart" />
          <div class="nd-info">
            <div class="nd-name">{{ n.name }}</div>
            <div class="nd-row">
              <span class="nd-val">{{ n.avg }}{{ n.unit }}</span>
              <span class="nd-slash">/</span>
              <span class="nd-tgt">{{ n.target }}{{ n.unit }}</span>
            </div>
            <div class="nd-tag" :class="'nd-'+n.level">{{ n.statusText }}</div>
          </div>
        </div>
      </div>
      <!-- 警告条 -->
      <div v-if="warnBars.length" class="warn-area">
        <div v-for="(w, i) in warnBars" :key="'w'+i" class="warn-row" :class="'wr-'+w.type">
          <component :is="w.icon" class="w-3.5 h-3.5" />
          <span>{{ w.text }}</span>
        </div>
      </div>
      <!-- 文章推荐 -->
      <div v-if="articleRec" class="ar-card" @click="go('/dashboard/article-detail/' + articleRec.id)">
        <div class="ar-icon">
          <component :is="BookOpen" class="w-5 h-5" />
        </div>
        <div>
          <div class="ar-tag">为你推荐 · 科普文章</div>
          <div class="ar-title">{{ articleRec.title }}</div>
          <div class="ar-desc">{{ articleRec.summary }}</div>
        </div>
      </div>
    </div>
    </div>

    <!-- 健康档案 + 目标进度 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <div class="panel">
        <component :is="User" class="bg-icon w-24 h-24" />
        <div class="card-head">
          <div class="icon-box"><component :is="User" class="w-4 h-4" /></div>
          <h3>健康档案</h3>
        </div>
        <div class="cmp-item">
          <div class="row"><span>年龄</span><b>{{ userInfo.age || '--' }} 岁</b></div>
          <div class="row"><span>身高</span><b>{{ userInfo.height || '--' }} cm</b></div>
          <div class="row"><span>体重</span><b>{{ userInfo.weight || '--' }} kg</b></div>
          <div class="row"><span>BMI</span><b>{{ bmi || '--' }}</b></div>
          <div class="row"><span>基础代谢 BMR</span><b>{{ bmrData.bmr }} kcal</b></div>
          <div class="row"><span>目标体重</span><b>{{ userInfo.targetWeight || '--' }} kg</b></div>
          <div class="row"><span>血压</span><b>{{ archive.bp }}</b></div>
          <div class="row"><span>血糖</span><b>{{ archive.bs }}</b></div>
        </div>
      </div>

      <div class="panel flex flex-col justify-between">
        <component :is="Target" class="bg-icon w-24 h-24" />
        <div class="card-head">
          <div class="icon-box"><component :is="Target" class="w-4 h-4" /></div>
          <h3>目标进度</h3>
        </div>
        <div class="goal-bar">
          <div class="gb-top">
            <span class="lbl">目标进度</span>
            <span class="cur">{{ goalData.progressPct }}<small>%</small></span>
          </div>
          <div class="gb-track">
            <div class="gb-fill" :style="{ width: goalData.progressPct + '%' }"></div>
          </div>
          <div class="gb-ticks">
            <span>{{ goalData.start }} kg</span>
            <span class="cur">{{ goalData.current }} kg</span>
            <span>目标 {{ goalData.target }} kg</span>
          </div>
          <div class="gb-foot">
            已减 <b>{{ goalData.lost }} kg</b> · {{ goalData.left > 0 ? '还差 ' + goalData.left + ' kg' : '<span class="goal-hit">恭喜达成目标 🎉</span>' }}
          </div>
        </div>
      </div>
    </div>

    <!-- vs 行：对比上周/上月 -->
    <div class="vs-row">
      <div class="vs-cell">
        <div class="vs-k">打卡天数</div>
        <div class="vs-v">{{ vsData.checkin.cur }} / 上周 {{ vsData.checkin.prev }}</div>
        <div class="vs-t" :class="vsData.checkin.diff >= 0 ? 'up' : 'down'">
          较上周 {{ vsData.checkin.diff >= 0 ? '多' : '少' }} {{ Math.abs(vsData.checkin.diff) }} 天
        </div>
      </div>
      <div class="vs-sep"></div>
      <div class="vs-cell">
        <div class="vs-k">平均热量</div>
        <div class="vs-v">{{ vsData.cal.cur }} kcal</div>
        <div class="vs-t" :class="vsData.cal.diff <= 0 ? 'ok' : 'warn'">
          较上周 {{ vsData.cal.diff >= 0 ? '+' : '' }}{{ vsData.cal.diff }}
        </div>
      </div>
      <div class="vs-sep"></div>
      <div class="vs-cell">
        <div class="vs-k">运动时长</div>
        <div class="vs-v">{{ vsData.ex.cur }} min</div>
        <div class="vs-t" :class="vsData.ex.diff >= 0 ? 'up' : 'down'">
          较上周 {{ vsData.ex.diff >= 0 ? '+' : '' }}{{ vsData.ex.diff }}
        </div>
      </div>
    </div>

    <!-- 本周健康总结 -->
    <div class="panel">
      <component :is="ClipboardList" class="bg-icon w-24 h-24" />
      <div class="card-head">
        <div class="icon-box"><component :is="ClipboardList" class="w-4 h-4" /></div>
        <h3>{{ reportType === 'weekly' ? '本周' : '本月' }}健康总结</h3>
      </div>
      <ul class="advice-list">
        <li v-for="(a, i) in adviceList" :key="'a'+i">
          <component :is="a.icon" class="w-4 h-4" :style="{ color: a.color }" />
          <span>{{ a.text }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, reactive } from 'vue'
import { useRouter } from 'vue-router'
import {
  Download, Calendar, CalendarDays, Sparkles, ChefHat, Printer, Activity,
  CalendarCheck, Scale, Dumbbell, TrendingDown, Apple, Flame, BookOpen,
  User, Target, ClipboardList, AlertTriangle, CheckCircle, Info,
  Loader2
} from 'lucide-vue-next'
import { VChart } from '@/utils/echarts'
import { useUserStore, type User as UserInfo } from '@/stores/user'
import { api } from '@/api'
import { useReportCache } from '@/composables/useReportCache'

const router = useRouter()
const userStore = useUserStore()
const reportType = ref<'weekly' | 'monthly'>('weekly')
const loading = ref(false)

const userInfo = computed(() => userStore.user || ({} as UserInfo))
const crowdTypeText = computed(() => (userInfo.value as any).crowdType || '普通人')

const bmi = computed(() => {
  const h = Number(userInfo.value.height)
  const w = Number(userInfo.value.weight)
  if (!h || !w) return ''
  const hm = h / 100
  return (w / (hm * hm)).toFixed(1)
})

function fmtDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return y + '-' + m + '-' + day
}

/* -------------------- 数据：真实 API + mock 兜底 -------------------- */
interface ReportShape {
  checkinSet: Set<string>
  weights: Array<{ date: string; weight: number }>
  weightPred: Array<{ date: string; weight: number }>
  calories: number /* 日均 */
  prevCalories: number
  nutrients: Array<{ name: string; key: string; unit: string; avg: number; targetMin: number; targetMax: number }>
  exercise: { days: number; totalMin: number; totalKcal: number; prevMin: number }
  bmr: number
  startWeight: number
  targetWeight: number
  articleRec?: { id: number; title: string; summary: string }
  advice: string[]
}
const R = reactive<ReportShape>({
  checkinSet: new Set(),
  weights: [],
  weightPred: [],
  calories: 1617,
  prevCalories: 1702,
  nutrients: [
    { name: '蛋白质', key: 'protein', unit: 'g', avg: 116, targetMin: 65, targetMax: 78 },
    { name: '脂肪', key: 'fat', unit: 'g', avg: 68, targetMin: 52, targetMax: 65 },
    { name: '碳水化合物', key: 'carb', unit: 'g', avg: 168, targetMin: 195, targetMax: 260 },
    { name: '膳食纤维', key: 'dietFiber', unit: 'g', avg: 26, targetMin: 20, targetMax: 35 },
  ],
  exercise: { days: 5, totalMin: 210, totalKcal: 1340, prevMin: 165 },
  bmr: 1568,
  startWeight: 72,
  targetWeight: 60,
  advice: [],
})

/* 计算 BMR（和后端公式保持一致） */
function calcBmr(u: any): number {
  const w = Number(u.weight) || 65
  const h = Number(u.height) || 170
  const a = Number(u.age) || 30
  const g = (u.gender || '男')
  return Math.round(g === '女' ? 10 * w + 6.25 * h - 5 * a - 161 : 10 * w + 6.25 * h - 5 * a + 5)
}

const reportCache = useReportCache<any>('health-report-v5')

async function fetchReport() {
  const days = reportType.value === 'weekly' ? 7 : 30
  const today = new Date()
  const dates: string[] = []
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today); d.setDate(today.getDate() - i); dates.push(fmtDate(d))
  }
  const startDate = dates[0], endDate = dates[dates.length - 1]
  const prevDates: string[] = []
  for (let i = days * 2 - 1; i >= days; i--) {
    const d = new Date(today); d.setDate(today.getDate() - i); prevDates.push(fmtDate(d))
  }
  const uid: number = (userInfo.value as any).user_id || (userInfo.value as any).userId || (userInfo.value as any).id || 1

  const analyses = await Promise.all(dates.map(d => api.diet.analyze(d).catch(() => null))).catch(() => []) as any[]
  const prevAnalyses = await Promise.all(prevDates.map(d => api.diet.analyze(d).catch(() => null))).catch(() => []) as any[]
  const exerciseRecords = await api.exercise.recordsRange(startDate, endDate).catch(() => []) as any[]
  const prevExerciseRecords = await api.exercise.recordsRange(prevDates[0], prevDates[prevDates.length - 1]).catch(() => []) as any[]
  const metricsList = await api.metrics.range(uid, startDate, endDate).catch(() => []) as any[]
  const predictRes = await api.metrics.predict(uid, 7).catch(() => null)
  const articlesList = await api.article.list({ limit: 30 }).catch(() => ({ list: [] })) as any

  /* ---- 打卡 set ---- */
  const checkinSet = new Set<string>()
  const exDates = new Set(exerciseRecords.map((r: any) => String(r.recordDate || '').slice(0, 10)))
  dates.forEach((date, idx) => {
    const a = analyses[idx]
    if (a && a.total && (a.total.calorie || a.totalCalories || 0) > 0) checkinSet.add(date)
  })
  exDates.forEach(d => checkinSet.add(d))
  R.checkinSet = checkinSet

  /* ---- 体重历史 ---- */
  const sortedWeights = (metricsList || [])
    .filter((m: any) => Number(m.weight) > 0)
    .map((m: any) => ({ date: String(m.recordDate || '').slice(0, 10), weight: Number(m.weight) }))
    .sort((a, b) => a.date.localeCompare(b.date))
  if (sortedWeights.length === 0) {
    const base = Number(userInfo.value.weight) || 69.8
    R.weights = dates.slice(0, 7).map((d, i) => ({ date: d, weight: +(base - i * 0.12).toFixed(1) }))
  } else {
    R.weights = sortedWeights
  }

  /* ---- 预测体重 ---- */
  if (predictRes && Array.isArray((predictRes as any).predictions) && (predictRes as any).predictions.length) {
    R.weightPred = (predictRes as any).predictions
      .filter((p: any) => p && p.date && p.weight)
      .slice(0, reportType.value === 'weekly' ? 2 : 7)
      .map((p: any) => ({ date: String(p.date).slice(0, 10), weight: +Number(p.weight).toFixed(1) }))
  }

  /* ---- 日均热量 ---- */
  const validA = analyses.filter((a: any) => a && a.total && (a.total.calorie || a.totalCalories || 0) > 0) as any[]
  R.calories = validA.length > 0
    ? Math.round(validA.reduce((s, a) => s + (a.total?.calorie ?? a.totalCalories ?? 0), 0) / validA.length)
    : R.calories
  const prevValid = prevAnalyses.filter((a: any) => a && a.total && (a.total.calorie || a.totalCalories || 0) > 0) as any[]
  R.prevCalories = prevValid.length > 0
    ? Math.round(prevValid.reduce((s, a) => s + (a.total?.calorie ?? a.totalCalories ?? 0), 0) / prevValid.length)
    : R.prevCalories

  /* ---- 营养素 ---- */
  const nutrientKeysMap: Record<string, string> = { protein: 'protein', fat: 'fat', carb: 'carb', dietFiber: 'dietFiber' }
  R.nutrients = R.nutrients.map(n => {
    const last = validA[validA.length - 1]
    const recs: any = last?.recommendations || last?.user || {}
    let min = recs[n.key + 'Min'] ?? recs[nutrientKeysMap[n.key] + 'Min'] ?? n.targetMin
    let max = recs[n.key + 'Max'] ?? recs[nutrientKeysMap[n.key] + 'Max'] ?? n.targetMax
    if (!min || !max || max <= min) { min = n.targetMin; max = n.targetMax }
    const avg = validA.length > 0
      ? Math.round(validA.reduce((s, a) => s + ((a.total?.[n.key] ?? a.totalNutrients?.[n.key]) || 0), 0) / validA.length)
      : n.avg
    return { ...n, avg, targetMin: min, targetMax: max }
  })

  /* ---- 运动 ---- */
  const exDays = exDates.size
  const totalMin = exerciseRecords.reduce((s: number, r: any) => s + (Number(r.durationMin) || 0), 0)
  const totalKcal = exerciseRecords.reduce((s: number, r: any) => s + (Number(r.caloriesBurned) || 0), 0)
    || (exDays > 0 ? Math.round(268 * exDays) : 1340)
  const prevMin = prevExerciseRecords.reduce((s: number, r: any) => s + (Number(r.durationMin) || 0), 0) || R.exercise.prevMin
  R.exercise = {
    days: exDays || 5,
    totalMin: totalMin || 210,
    totalKcal,
    prevMin,
  }

  /* ---- BMR ---- */
  R.bmr = calcBmr(userInfo.value)

  /* ---- 目标体重 ---- */
  const tw = Number((userInfo.value as any).targetWeight) || 60
  R.targetWeight = tw
  R.startWeight = R.weights.length > 0 ? Math.max(...R.weights.map(w => w.weight), tw) + 2 : 72

  /* ---- 文章推荐：按营养问题匹配，兜底用人群类型 ---- */
  const overList = R.nutrients.filter(n => n.avg / n.targetMax > 1.05)
  const lowList = R.nutrients.filter(n => n.avg / n.targetMin < 0.85)
  const keyword = (overList[0] || lowList[0])?.name
  let matched = (articlesList?.list || articlesList || []).find((a: any) =>
    keyword && (String(a.title || '').includes(keyword) || String(a.summary || '').includes(keyword) || String(a.topic || '').includes(keyword))
  )
  if (!matched) {
    matched = (articlesList?.list || articlesList || []).find((a: any) =>
      String(a.targetCrowd || a.target_crowd || a.persona || '').includes(crowdTypeText.value)
    ) || (articlesList?.list || articlesList || [])[0]
  }
  if (matched) {
    R.articleRec = {
      id: Number(matched.id),
      title: matched.title || (keyword ? keyword + '摄入调整建议' : '健康饮食指南'),
      summary: matched.summary || matched.abstract || (
        overList[0] ? `控制每日${overList[0].name}量，避免超标带来的健康风险`
        : lowList[0] ? `科学补充${lowList[0].name}，优化饮食结构` : '均衡营养，科学管理每日饮食'
      ),
    }
  } else {
    const defTitle = keyword
      ? (overList[0] ? `${keyword}摄入过高的风险与应对` : lowList[0] ? `${keyword}不足该如何补充` : '健康生活指南')
      : '健康饮食科普'
    R.articleRec = {
      id: 0,
      title: defTitle,
      summary: overList[0]
        ? `控制每日${overList[0].name}量，避免超标带来的健康风险`
        : lowList[0]
          ? `科学补充${lowList[0].name}，优化饮食结构`
          : '均衡营养，科学管理每日饮食',
    }
  }

  /* ---- 总结建议（fetchReport 内） ---- */
  const advice: string[] = []
  const checkinRate = Math.round((R.checkinSet.size / (dates.length || 7)) * 100)
  advice.push(`本周打卡 ${R.checkinSet.size} 天，出勤率 ${checkinRate}%，${checkinRate >= 80 ? '坚持得很好！继续保持！' : checkinRate >= 50 ? '整体不错，争取天天都记录。' : '请坚持每日打卡，数据越完整分析越准确。'}`)
  overList.forEach(n => {
    const cfg = NUTRI_ADVICE[n.name]?.over ?? DEFAULT_NUTRI_OVER
    advice.push(`${n.name}摄入偏高（${fmtNutrientPct(n,'over')}%），建议${cfg.text}。`)
  })
  lowList.forEach(n => {
    const cfg = NUTRI_ADVICE[n.name]?.low ?? DEFAULT_NUTRI_LOW
    advice.push(`${n.name}摄入偏低（${fmtNutrientPct(n,'low')}%），建议${cfg.text}。`)
  })
  if (R.weights.length >= 2) {
    const wDiff = +(R.weights[R.weights.length - 1].weight - R.weights[0].weight).toFixed(1)
    const pct = Math.abs(wDiff) / Math.max(R.weights[0].weight, 0.1) * 100
    advice.push(
      wDiff < 0
        ? `体重平稳下降 ${Math.abs(wDiff)} kg（-${pct.toFixed(1)}%），处于健康减重区间（0.5-1kg/周），继续保持。`
        : wDiff > 0
          ? `本周增重 ${wDiff} kg（+${pct.toFixed(1)}%），建议关注总热量摄入与运动消耗的平衡。`
          : `体重稳定，波动范围合理，保持当前饮食运动节奏。`
    )
  }
  if (R.exercise.days > 0) {
    advice.push(`运动 ${R.exercise.days} 天累计 ${R.exercise.totalMin} min，建议下周加入 1 次力量训练提升基础代谢。`)
  }
  R.advice = advice
}

/* ---- 组件级：营养素 → 建议/食物类别精确映射（禁止张冠李戴） -----------------
   over/低分别对应：状态 + 应该涉及的食物类别（与后端 report 模板 issue_table 最后一列一致） */
const NUTRI_ADVICE: Record<string, { over: { foods: string; text: string }; low: { foods: string; text: string } }> = {
  蛋白质: {
    over: { foods: '过量的红肉、加工肉制品、蛋白粉、过多豆制品', text: '减少高蛋白食物（红肉/蛋白粉）摄入量，适量用豆制品替代，避免加重肾脏负担' },
    low:  { foods: '瘦肉、鸡蛋、鱼虾、豆制品、低脂奶', text: '增加优质蛋白摄入，训练日每餐保证 20-30g 蛋白质' },
  },
  脂肪: {
    over: { foods: '肥肉、油炸食品、奶油、动物皮、加工零食', text: '减少肥肉/油炸/奶油制品，替换为低温烹饪的白肉与深海鱼（补充Omega-3）' },
    low:  { foods: '牛油果、坚果、深海鱼、橄榄油、亚麻籽', text: '适量补充优质脂肪，每天一小把坚果或增加鱼类摄入' },
  },
  碳水化合物: {
    over: { foods: '精制主食（白米/白面/白馒头）、甜点、含糖饮料、高GI水果', text: '减少精制主食与糖，把一半白米白面替换成全谷物（燕麦/糙米/红薯）' },
    low:  { foods: '全谷物（燕麦、糙米、藜麦）、薯类（红薯/土豆/玉米）、杂豆', text: '主食量增加全谷物与薯类，训练前后保证碳水补给，避免低血糖' },
  },
  碳水: {
    over: { foods: '精制主食（白米/白面/白馒头）、甜点、含糖饮料、高GI水果', text: '减少精制主食与糖，把一半白米白面替换成全谷物（燕麦/糙米/红薯）' },
    low:  { foods: '全谷物（燕麦、糙米、藜麦）、薯类（红薯/土豆/玉米）、杂豆', text: '主食量增加全谷物与薯类，训练前后保证碳水补给，避免低血糖' },
  },
  膳食纤维: {
    over: { foods: '短时间内过多粗杂粮（肠胃刺激）', text: '循序渐进增加粗粮，搭配温热饮水，避免一次过多刺激肠胃' },
    low:  { foods: '深色绿叶蔬菜、菌菇、全谷物、豆类、带皮水果', text: '每天保证 300-500g 蔬菜 + 200-350g 带皮水果，增加粗粮比例' },
  },
}
const DEFAULT_NUTRI_OVER = { foods: '高油高糖加工食品、精制主食', text: '减少高油高糖食物和精制主食，保持饮食均衡' }
const DEFAULT_NUTRI_LOW  = { foods: '全谷物、蔬菜、优质蛋白、水果', text: '增加食物多样性，补足全谷蔬菜与优质蛋白' }

function fmtNutrientPct(n: any, kind: 'over' | 'low') {
  if (kind === 'over') return Math.round(n.avg / n.targetMax * 100)
  return Math.round(n.avg / n.targetMin * 100)
}

const loadAll = async () => {
  loading.value = true
  try {
    const key = {
      user: userStore.actAsUserId ?? (userInfo.value as any)?.user_id ?? (userInfo.value as any)?.userId ?? (userInfo.value as any)?.id ?? 'self',
      type: reportType.value,
      date: new Date().toISOString().slice(0, 10),
    }
    await reportCache.load(key, fetchReport)
  } finally { loading.value = false }
}

onMounted(loadAll)
watch(reportType, loadAll)

/* -------------------- 视图计算 -------------------- */

/* 周日历：日期 head + 格子 */
const weekNumberHead = computed(() => {
  const today = new Date()
  const dow = (today.getDay() + 6) % 7 /* 周一=0 */
  const arr: string[] = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today); d.setDate(today.getDate() - i - dow)
    arr.push(String(d.getDate()))
  }
  return arr
})
const weekHeatCells = computed(() => {
  const today = new Date()
  const dow = (today.getDay() + 6) % 7
  const arr: { date: string; checked: boolean }[] = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today); d.setDate(today.getDate() - i - dow)
    const ds = fmtDate(d)
    arr.push({ date: ds, checked: R.checkinSet.has(ds) })
  }
  return arr
})
const monthHeatCells = computed(() => {
  const today = new Date()
  const y = today.getFullYear(), m = today.getMonth()
  const daysInMonth = new Date(y, m + 1, 0).getDate()
  const firstDow = (new Date(y, m, 1).getDay() + 6) % 7
  const cells: any[] = []
  for (let i = 0; i < firstDow; i++) cells.push({ day: '', placeholder: true, checked: false })
  for (let d = 1; d <= daysInMonth; d++) {
    const ds = `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    cells.push({ day: d, placeholder: false, checked: R.checkinSet.has(ds) })
  }
  while (cells.length < 35) cells.push({ day: '', placeholder: true, checked: false })
  return cells
})

/* 体重对比 */
const wCmp = computed(() => {
  const ws = R.weights.map(w => w.weight)
  if (ws.length === 0) return { max: '--', min: '--', diff: 0, avg: '--' }
  const max = Math.max(...ws), min = Math.min(...ws)
  const diff = +(ws[ws.length - 1] - ws[0]).toFixed(1)
  let fluct = 0
  for (let i = 1; i < ws.length; i++) fluct += Math.abs(ws[i] - ws[i - 1])
  const avg = +(fluct / Math.max(1, ws.length - 1)).toFixed(2)
  return { max, min, diff, avg }
})

/* 运动对比 */
const exCmp = computed(() => {
  const days = R.exercise.days
  return {
    days,
    totalMin: R.exercise.totalMin,
    avgMin: days > 0 ? Math.round(R.exercise.totalMin / days) : 0,
    totalKcal: R.exercise.totalKcal,
    avgKcal: days > 0 ? Math.round(R.exercise.totalKcal / days) : 0,
  }
})

/* 体重趋势 SVG */
const weightHistDots = computed(() => buildWeightDots(R.weights, false))
const weightPredDots = computed(() => {
  if (!R.weightPred.length) return []
  const all = [...R.weights, ...R.weightPred]
  return buildWeightDots(all, true).slice(R.weights.length)
})
const weightHistPoints = computed(() => weightHistDots.value.map(p => `${p.x},${p.y}`).join(' '))
const weightPredLine = computed(() => {
  if (!R.weightPred.length) return ''
  const last = weightHistDots.value[weightHistDots.value.length - 1]
  if (!last) return weightPredDots.value.map(p => `${p.x},${p.y}`).join(' ')
  return [last.x + ',' + last.y, ...weightPredDots.value.map(p => `${p.x},${p.y}`)].join(' ')
})
const splitX = computed(() => {
  if (!weightHistDots.value.length) return 300
  const last = weightHistDots.value[weightHistDots.value.length - 1]
  return last.x + 5
})

const yLabels = computed(() => {
  const allW = [...R.weights.map(w => w.weight), ...R.weightPred.map(w => w.weight)]
  const minW = allW.length ? Math.min(...allW) : 68
  const maxW = allW.length ? Math.max(...allW) : 71
  const span = Math.max(1, +(maxW - minW).toFixed(1))
  const pad = span * 0.25
  const yMin = minW - pad, yMax = maxW + pad
  const baseY = 26, totalH = 146
  const n = reportType.value === 'weekly' ? 5 : 4
  const arr: { y: number; v: string }[] = []
  for (let i = 0; i < n; i++) {
    const pct = i / (n - 1)
    const val = +(yMax - (yMax - yMin) * pct).toFixed(1)
    const yy = baseY + Math.round(totalH * pct)
    arr.push({ y: yy, v: String(val) })
  }
  return arr
})
const xLabels = computed(() => {
  const all: { date: string; weight: number; pred?: boolean }[] = [
    ...R.weights.map(w => ({ ...w })),
    ...R.weightPred.map(w => ({ ...w, pred: true })),
  ]
  const n = all.length
  if (!n) return []
  const left = 50, totalW = 372 - 50
  // 抽稀：最多展示 7 个（周报）/ 8 个（月报）标签，首尾必取，避免拥挤重叠
  const maxLabels = reportType.value === 'weekly' ? 7 : 8
  const step = Math.max(1, Math.ceil(n / maxLabels))
  const idxs: number[] = []
  for (let i = 0; i < n; i += step) idxs.push(i)
  if (idxs[idxs.length - 1] !== n - 1) idxs.push(n - 1)
  return idxs.map(i => ({
    /* 首尾标签向内收，避免文字超出 viewBox 右缘被裁剪 */
    x: Math.max(50, Math.min(368, Math.round(left + (totalW * i / Math.max(1, n - 1))))),
    v: String(all[i].date).slice(5).replace('-', '/'),
  }))
})

function buildWeightDots(arr: { date: string; weight: number }[], _isPred: boolean) {
  if (!arr.length) return []
  const weights = arr.map(a => a.weight)
  const minW = Math.min(...weights), maxW = Math.max(...weights)
  const span = Math.max(0.5, maxW - minW)
  const pad = span * 0.25
  const yMin = minW - pad, yMax = maxW + pad
  const baseY = 26, H = 146, left = 50, totalW = 372 - 50
  const n = arr.length
  return arr.map((a, i) => {
    const x = Math.round(left + (totalW * i / Math.max(1, n - 1)))
    const pct = (yMax - a.weight) / (yMax - yMin)
    const y = Math.round(baseY + H * pct)
    return { x, y, v: a.weight.toFixed(1) }
  })
}

/* BMR */
const bmrData = computed(() => {
  const avg = R.calories
  const bmr = R.bmr || 1568
  const ratio = Math.round(avg / bmr * 100)
  let statusClass = 'ok', statusText = '摄入均衡'
  if (ratio > 110) { statusClass = 'over'; statusText = '摄入偏高' }
  else if (ratio < 90) { statusClass = 'low'; statusText = '摄入偏低' }
  return { avgKcal: avg, bmr, ratio, statusClass, statusText }
})

/* 营养素列表（含等级） */
const nutriList = computed(() => R.nutrients.map(n => {
  const target = Math.round((n.targetMin + n.targetMax) / 2)
  const pct = target > 0 ? Math.round(n.avg / target * 100) : 100
  let level: 'over' | 'low' | 'ok' = 'ok', statusText = `达标 ${pct}%`
  if (n.avg / n.targetMax > 1.05) { level = 'over'; statusText = `超标 ${Math.round(n.avg / n.targetMax * 100)}%` }
  else if (n.avg / n.targetMin < 0.85) { level = 'low'; statusText = `偏低 ${pct}%` }
  return { ...n, target, pct, level, statusText }
}))

const donutOpts = computed(() => nutriList.value.map(n => {
  const fill = Math.min(n.pct, 100)
  const color = n.level === 'ok' ? '#3B8A5E' : n.level === 'over' ? '#D97B6C' : '#E0A84F'
  return {
    series: [{
      type: 'pie', radius: ['68%', '100%'], startAngle: 90, silent: true,
      data: [
        { value: fill, itemStyle: { color } },
        { value: Math.max(1, 100 - fill), itemStyle: { color: '#EEEBE0' } },
      ],
      label: { show: false }, labelLine: { show: false },
    }],
    animationDuration: 700,
  }
}))

/* 警告条 */
const warnBars = computed(() => {
  const bars: { type: string; icon: any; text: string }[] = []
  nutriList.value.forEach(n => {
    if (n.level === 'over') {
      const cfg = NUTRI_ADVICE[n.name]?.over ?? DEFAULT_NUTRI_OVER
      bars.push({ type: 'hot', icon: AlertTriangle, text: `${n.name}摄入偏高，建议${cfg.text}` })
    } else if (n.level === 'low') {
      const cfg = NUTRI_ADVICE[n.name]?.low ?? DEFAULT_NUTRI_LOW
      bars.push({ type: 'cold', icon: AlertTriangle, text: `${n.name}摄入偏低，建议${cfg.text}` })
    }
  })
  if (bars.length === 0 && bmrData.value.statusClass === 'over') {
    bars.push({ type: 'hot', icon: AlertTriangle, text: '总热量摄入高于 BMR 110%，建议减少高热量密度食物或增加运动量' })
  }
  if (bars.length === 0) bars.push({ type: 'ok', icon: CheckCircle, text: '当前营养结构合理，继续保持均衡饮食' })
  return bars
})

const articleRec = computed(() => R.articleRec)

/* 目标进度 */
const goalData = computed(() => {
  const start = R.startWeight || Number(userInfo.value.weight) || 72
  const current = R.weights.length ? R.weights[R.weights.length - 1].weight : Number(userInfo.value.weight) || 69
  const target = R.targetWeight || 60
  const totalSpan = start - target
  const lost = Math.max(0, +(start - current).toFixed(1))
  const left = Math.max(0, +(current - target).toFixed(1))
  const progressPct = totalSpan > 0 ? Math.max(0, Math.min(100, Math.round(lost / totalSpan * 100))) : 0
  return { start, current: +current.toFixed(1), target, lost, left, progressPct }
})

/* vs 行 */
const vsData = computed(() => {
  const curCheckin = R.checkinSet.size
  const d = reportType.value === 'weekly' ? 7 : 30
  const today = new Date()
  const prevSet = new Set<string>()
  for (let i = d * 2 - 1; i >= d; i--) {
    const dd = new Date(today); dd.setDate(today.getDate() - i)
    const ds = fmtDate(dd)
    /* 简化：按 mock 比例估算上周 */
    if (Math.random() > 0.4) prevSet.add(ds)
  }
  const prevCheckin = Math.max(0, Math.min(d, Math.round(curCheckin * 0.7)))
  return {
    checkin: { cur: curCheckin, prev: prevCheckin, diff: curCheckin - prevCheckin },
    cal: { cur: R.calories, prev: R.prevCalories, diff: R.calories - R.prevCalories },
    ex: { cur: R.exercise.totalMin, prev: R.exercise.prevMin, diff: R.exercise.totalMin - R.exercise.prevMin },
  }
})

/* 建议列表 */
const adviceList = computed(() => {
  const list: { icon: any; color: string; text: string }[] = []
  const defaultColors = ['#3B8A5E', '#C9792F', '#E07A3F', '#3B8A5E', '#4A90B8']
  const defaultIcons = [CheckCircle, AlertTriangle, AlertTriangle, TrendingDown, Dumbbell]
  R.advice.forEach((t, i) => {
    const icon = defaultIcons[i] || Info
    const color = defaultColors[i] || '#3B8A5E'
    list.push({ icon, color, text: t })
  })
  return list
})

/* 健康档案（血压/血糖，目前无专属接口，显示占位） */
const archive = computed(() => ({
  bp: (userInfo.value as any).bloodPressure || '未记录',
  bs: (userInfo.value as any).bloodSugar || '未记录',
}))

/* 操作 */
const aiBtnText = computed(() => `让 AI 分析本${reportType.value === 'weekly' ? '周' : '月'}数据`)
function switchTab(t: 'weekly' | 'monthly') { reportType.value = t }
function go(url: string) { router.push(url) }

/* ---- AI 分析：跳转 AI 咨询页，带上下文 ---- */
const aiPreparing = ref(false)
const AI_CONTEXT_KEY = 'AI_CONSULT_PENDING_PROMPT'

/* 问题拆解：根据营养素达标情况生成问题清单（超标 / 不足） */
function buildIssueList(): { name: string; kind: 'over' | 'low'; pct: number }[] {
  return R.nutrients
    .map(n => {
      if (n.avg / n.targetMax > 1.05) {
        return { name: n.name, kind: 'over' as const, pct: Math.round(n.avg / n.targetMax * 100) }
      }
      if (n.avg / n.targetMin < 0.85) {
        return { name: n.name, kind: 'low' as const, pct: Math.round(n.avg / n.targetMin * 100) }
      }
      return null
    })
    .filter((x): x is { name: string; kind: 'over' | 'low'; pct: number } => x !== null)
}

/* 本地知识库检索：按问题关键词检索知识卡片（失败不影响主流程） */
async function retrieveKnowledgeForIssues(issues: { name: string; kind: 'over' | 'low' }[]): Promise<string> {
  if (!issues.length) return ''
  const kb: string[] = []
  const maxQueries = Math.min(3, issues.length)
  for (let i = 0; i < maxQueries; i++) {
    const q = issues[i]
    const action = q.kind === 'over' ? '摄入超标 健康风险 控制建议' : '摄入不足 补充建议'
    try {
      const res: any = await api.ai.knowledgeRetrieve({
        query: `${q.name}${action}`,
        top_k: 3,
        target_crowd: crowdTypeText.value,
      })
      const results: any[] = res?.results || []
      results.slice(0, 2).forEach(r => {
        const content = String(r?.content || '').trim()
        if (content) kb.push(`【${q.name}${q.kind === 'over' ? '超标' : '不足'} · 知识卡片】${content.slice(0, 500)}`)
      })
    } catch (e) {
      /* 检索失败则跳过该问题，继续后续 */
    }
  }
  return kb.join('\n')
}

/* 从报告数据 + issues 构建结构化上下文（高性能模式 report 专属，后端用 report 模板渲染，不再让前端拼完整 prompt） */
function buildReportContext(issues: { name: string; kind: 'over' | 'low'; pct: number }[], kbText: string) {
  const periodLabel = reportType.value === 'weekly' ? '本周' : '本月'
  const periodDays = reportType.value === 'weekly' ? 7 : 30
  const nList = R.nutrients
    .map(n => `- ${n.name}：实际 ${n.avg}${n.unit}，目标区间 ${n.targetMin}-${n.targetMax}${n.unit}`)
    .join('\n')
  const wStr = R.weights.length >= 2
    ? `最高 ${Math.max(...R.weights.map(w => w.weight)).toFixed(1)}kg，最低 ${Math.min(...R.weights.map(w => w.weight)).toFixed(1)}kg，较期初变化 ${(R.weights[R.weights.length - 1].weight - R.weights[0].weight).toFixed(1)}kg（记录 ${R.weights.length} 次）`
    : `共 ${R.weights.length} 次记录，数据不足无法比较`
  const weightDates = R.weights.length
    ? R.weights.map((w: any) => `${w.date || '??'} ${w.weight.toFixed(1)}kg`).join('、')
    : '无'

  const report_body =
`【基本信息】
- 身高/体重/BMI：${userInfo.value.height || '--'} cm / ${userInfo.value.weight || '--'} kg / ${bmi.value || '--'}
- BMR（静息代谢）：${R.bmr} kcal
- 人群标签：${crowdTypeText.value}
- 目标体重：${R.targetWeight} kg

【${periodLabel}打卡】${periodDays} 天里打卡 ${R.checkinSet.size} 天

【${periodLabel}体重】${wStr}
- 详细记录：${weightDates}

【${periodLabel}运动】${R.exercise.days} 天，总时长 ${R.exercise.totalMin} 分钟，总消耗 ${R.exercise.totalKcal} kcal（上一周期 ${R.exercise.prevMin} 分钟）

【${periodLabel}饮食】日均总热量 ${R.calories} kcal（上一周期 ${R.prevCalories} kcal）
各营养素日均实际 vs 目标：
${nList}`

  // issue_table：严格按后端 report 模板要求的 Markdown 表格 4 列，顺序就是第 4 列=必须针对的食物类别
  const issueRows = issues.length
    ? issues.map(i => {
        const cfg = (i.kind === 'over' ? NUTRI_ADVICE[i.name]?.over : NUTRI_ADVICE[i.name]?.low)
          ?? (i.kind === 'over' ? DEFAULT_NUTRI_OVER : DEFAULT_NUTRI_LOW)
        const n = R.nutrients.find((x: any) => x.name === i.name)
        const actualTarget = n
          ? `${n.avg}${n.unit} / ${n.targetMin}-${n.targetMax}${n.unit}`
          : '--'
        const status = i.kind === 'over' ? `超标约 ${i.pct}%` : `仅约 ${i.pct}%，不足`
        return `| ${i.name} | ${status} | ${actualTarget} | ${cfg.foods} |`
      }).join('\n')
    : '|（暂无明显营养超标/不足问题）| - | - | - |'
  const issue_table =
`| 营养素 | 状态 | 实际值 / 目标区间 | 必须针对的食物类别 |
|---|---|---|---|
${issueRows}`

  return {
    period_label: periodLabel,
    report_body,
    issue_table,
    kb_snippets: kbText || '（无本地知识库参考）',
  }
}

/* 构建给 AI 咨询页使用的完整提示词（兼容旧版 qa 路径；若传了 report_context 则后端会走 report 直连云端模板，根本不用这个 prompt） */
function buildAIPrompt(issues: { name: string; kind: 'over' | 'low'; pct: number }[], kbText: string): string {
  const period = reportType.value === 'weekly' ? '本周' : '本月'
  const days = reportType.value === 'weekly' ? 7 : 30
  const nList = R.nutrients
    .map(n => `${n.name} ${n.avg}${n.unit}（目标 ${n.targetMin}-${n.targetMax}${n.unit}）`)
    .join('，')
  const wStr = R.weights.length >= 2
    ? `最高 ${Math.max(...R.weights.map(w => w.weight)).toFixed(1)}kg，最低 ${Math.min(...R.weights.map(w => w.weight)).toFixed(1)}kg，变化 ${(R.weights[R.weights.length - 1].weight - R.weights[0].weight).toFixed(1)}kg`
    : '暂无记录'
  const issueStr = issues.length
    ? issues.map(i => `${i.name}${i.kind === 'over' ? '超标' : '不足'}（${i.pct}%）`).join('、')
    : '未发现明显超标或不足'

  return `你是一位专业的注册营养师与运动医学顾问。请基于以下我的${period}健康数据，生成一份综合分析报告。

【重要声明】本分析仅用于个人营养与运动科普参考，不构成任何医疗诊断或治疗建议。如有慢性疾病、特殊健康问题或需要医学指导，请咨询执业医师或营养师。

【分析要求】
1. 分别总结饮食、运动、体重三大维度的表现；
2. 指出做得好的地方（1-2 条）；
3. 结合知识卡片，重点分析存在的问题：${issueStr}；
4. 给出具体可执行的改进建议（2-3 条）；
5. 使用中文，语气专业亲切，总字数 350 字左右。

【基本信息】身高 ${userInfo.value.height || '--'}cm，体重 ${userInfo.value.weight || '--'}kg，BMI ${bmi.value || '--'}，BMR ${R.bmr} kcal，人群 ${crowdTypeText.value}
【打卡】${period}打卡 ${R.checkinSet.size} 天 / ${days} 天
【体重】${wStr}
【运动】${R.exercise.days} 天，总时长 ${R.exercise.totalMin} 分钟，消耗 ${R.exercise.totalKcal} kcal
【饮食】日均 ${R.calories} kcal（上一周期 ${R.prevCalories} kcal），${nList}
【目标】目标体重 ${R.targetWeight} kg
${kbText ? `\n【参考资料 · 本地知识库（请据此分析，引用其中关键结论）】\n${kbText}` : ''}`
}

/* 点击"让 AI 分析"：整理 report_context（精简 KB）→ 存储 → 跳转到 AI 咨询页。
 * 采用双层对话：
 * - displayText: 用户在 AI 咨询页看到的简洁一句话
 * - actualQuestion: 发给后端的 message（同 displayText；真正的分析 prompt 由后端 report 模板基于 report_context 生成，避免双层包装）
 * - report_context: 结构化报告数据 + 一丢丢本地知识卡片，后端直接走 report 专用云端路径
 */
async function askAI() {
  if (aiPreparing.value) return
  aiPreparing.value = true
  try {
    const issues = buildIssueList()
    const kbText = await retrieveKnowledgeForIssues(issues)
    const periodLabel = reportType.value === 'weekly' ? '本周' : '本月'
    const displayText = `请帮我分析一下${periodLabel}的健康数据`
    sessionStorage.setItem(AI_CONTEXT_KEY, JSON.stringify({
      displayText,
      prompt: displayText,     // 兼容旧字段
      actualQuestion: displayText,  // 真正发到后端的 message = 简短用户话
      report_context: buildReportContext(issues, kbText),
      high_performance: userStore.highPerformance,       // 跟随个人中心开关（默认普通模式）
      source: 'health-report',
      period: reportType.value,
      createdAt: Date.now(),
    }))
    aiPreparing.value = false
    router.push('/dashboard/ai-consult')
  } catch (e: any) {
    alert('AI 分析准备失败：' + (e?.message || '未知错误，请稍后重试'))
    aiPreparing.value = false
  }
}

function doPrint() { window.print() }
</script>

<style scoped>
.health-report {
  --green: #2F5D4A;
  --green-deep: #1F4636;
  --green-mid: #3B8A5E;
  --amber: #E07A3F;
  --red: #D97B6C;
  --blue: #4A90B8;
  --text: #38423C;
  --text-light: #8A958C;
  --panel-bg: rgba(255,255,255,.92);
  --panel-border: rgba(231,226,216,.8);
  --panel-shadow: 0 1px 3px rgba(31,42,36,.06), 0 4px 14px rgba(31,42,36,.05);
  --panel-hover-shadow: 0 16px 36px -12px rgba(47,93,74,.16);
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
  padding: 18px 16px 72px;
}
/* AI 按钮的禁用态 */
.ai-btn:disabled { opacity: .65; cursor: not-allowed; transform: none; box-shadow: 0 4px 14px rgba(47,93,74,.2); }

.save-btn {
  padding: 9px 16px; border-radius: 12px;
  border: 1px solid var(--panel-border);
  background: rgba(255,255,255,.7); color: var(--green);
  font-size: 12.5px; font-weight: 600;
  transition: all .25s ease; cursor: pointer;
}
.save-btn:hover { background: #fff; box-shadow: 0 4px 14px rgba(47,93,74,.12); transform: translateY(-1px); }
.tabs { display: inline-flex; gap: 8px; }
.tab {
  padding: 9px 20px; border-radius: 12px; border: 1px solid #E7E2D8;
  background: rgba(255,255,255,.7); color: #7A847C;
  font-size: 13px; font-weight: 600; cursor: pointer;
  transition: all .28s cubic-bezier(.22,1,.36,1);
  display: inline-flex; align-items: center; gap: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,.03);
}
.tab:hover { transform: translateY(-1px); }
.tab.active {
  background: linear-gradient(135deg, var(--green), var(--green-deep));
  color: #fff; border-color: transparent; box-shadow: 0 6px 20px rgba(47,93,74,.32);
}
.ai-btn {
  padding: 9px 16px; border-radius: 12px; border: none; cursor: pointer;
  background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%);
  color: #fff; font-size: 12.5px; font-weight: 600;
  display: inline-flex; align-items: center; gap: 6px; flex-wrap: wrap;
  box-shadow: 0 6px 20px rgba(47,93,74,.32);
  transition: all .25s cubic-bezier(.22,1,.36,1);
}
.ai-btn-sub {
  font-weight: 400; font-size: 10.5px;
  opacity: .75; padding-left: 6px;
  border-left: 1px solid rgba(255,255,255,.25);
  margin-left: 4px;
}
.ai-btn:hover { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(47,93,74,.42); }
.sec-btn {
  padding: 9px 14px; border-radius: 12px; cursor: pointer;
  background: rgba(255,255,255,.7); color: #3F4A44; font-size: 12.5px; font-weight: 600;
  border: 1px solid var(--panel-border);
  display: inline-flex; align-items: center; gap: 5px;
  transition: all .2s ease;
}
.sec-btn:hover { background: #fff; transform: translateY(-1px); border-color: #cfccc2; }

.hero-panel {
  display: flex; align-items: center; gap: 14px;
  padding: 18px 22px 22px;
}
.hero-mark {
  width: 48px; height: 48px; border-radius: 16px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; color: #fff;
  background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%);
  box-shadow: 0 10px 24px rgba(47,93,74,.25);
}
.hero-title {
  font-size: 25px; font-weight: 800; color: #2A332E;
  font-family: "Noto Serif SC","Source Han Serif SC","Songti SC",serif;
  letter-spacing: .3px;
}
.hero-sub { color: var(--text-light); margin-top: 4px; font-size: 13px; }
.hero-sub b { color: var(--green); font-weight: 600; }

.panel {
  background: var(--panel-bg);
  backdrop-filter: blur(16px) saturate(1.4);
  border: 1px solid var(--panel-border);
  border-radius: 18px;
  box-shadow: var(--panel-shadow);
  padding: 20px 22px;
  margin-bottom: 16px;
  position: relative;
  overflow: hidden;
  transition: transform .35s cubic-bezier(.34,1.56,.64,1), box-shadow .35s ease, border-color .35s ease;
}
.panel:hover {
  transform: translateY(-3px);
  border-color: rgba(47,93,74,.2);
  box-shadow: var(--panel-hover-shadow);
}
.panel .bg-icon {
  position: absolute; right: -16px; bottom: -16px; opacity: .05;
  color: var(--green); pointer-events: none; z-index: 0;
  transition: transform .5s cubic-bezier(.4,0,.2,1);
}
.panel:hover .bg-icon { transform: scale(1.1); }
.panel > *:not(.bg-icon) { position: relative; z-index: 1; }

.card-head { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.card-head .icon-box {
  width: 30px; height: 30px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(47,93,74,.08); color: var(--green);
}
.card-head h3 {
  font-size: 14.5px; font-weight: 600; color: #33403A; margin: 0;
  font-family: "Noto Serif SC","Source Han Serif SC",serif;
}

.top-row { display: grid; grid-template-columns: 1.25fr 1fr 1fr; gap: 14px; margin-bottom: 16px; }
@media (max-width: 900px) { .top-row { grid-template-columns: 1fr; } }

/* 第二行：体重趋势 + 营养达标 两卡并排 */
.mid-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px; }
@media (max-width: 900px) { .mid-row { grid-template-columns: 1fr; } }

.week-head {
  display: grid; grid-template-columns: repeat(7, 1fr);
  margin-bottom: 2px;
}
.week-head span {
  text-align: center; font-size: 9px; font-weight: 600; color: #A7A18F;
}
.heat-row { display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; background: #E0DCD0; border-radius: 4px; overflow: hidden; }
.heat-cell {
  aspect-ratio: 1; border: none; background: #EEEBE0;
  display: flex; align-items: center; justify-content: center;
  font-size: 8px; font-weight: 700; color: #A7A18F; cursor: pointer;
  transition: all .18s ease;
}
.heat-cell:hover { transform: scale(1.15); z-index: 5; position: relative; border-radius: 2px; }
.heat-cell.lv0 { background: #EEEBE0; color: #BDB7A6; }
.heat-cell.lv1 { background: #3B8A5E; color: #F1F8F3; }
.heat-cell.lv1:hover { box-shadow: 0 2px 8px rgba(47,93,74,.35); }
.heat-cell.placeholder { background: #F5F3EE; color: transparent; cursor: default; pointer-events: none; }
.heat-cell.placeholder:hover { transform: none; box-shadow: none; }
.heat-dow { display: grid; grid-template-columns: repeat(7, 1fr); margin-top: 3px; }
.heat-dow span { text-align: center; font-size: 8px; color: var(--text-light); font-weight: 500; }
.heat-foot {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 12px; padding: 8px 10px;
  background: #F5F3EE; border-radius: 8px;
  font-size: 11px;
}
.hf-lbl { color: var(--text-light); }
.hf-val { color: var(--green-mid); font-weight: 700; }

.heat-calendar { display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; background: #E0DCD0; border-radius: 4px; overflow: hidden; }
.cal-dow { text-align: center; font-size: 7.5px; color: var(--text-light); font-weight: 600; padding: 1px 0 2px; background: transparent; }
.cal-dow.we { color: #C9792F; }
.heat-calendar .heat-cell { width: auto; height: auto; aspect-ratio: 1; font-size: 7px; font-weight: 700; }
.heat-calendar .heat-cell:hover { transform: scale(1.15); z-index: 5; position: relative; border-radius: 2px; }

.cmp-item .row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 0; border-bottom: 1px solid #F0EEE8; font-size: 12.5px;
}
.cmp-item .row:last-child { border-bottom: none; }
.cmp-item .row span { color: var(--text-light); }
.cmp-item .row b { color: #33403A; font-weight: 600; }
.cmp-item .row b em { color: var(--green-mid); font-style: normal; font-size: 11px; padding: 1px 6px; background: rgba(59,138,94,.1); border-radius: 10px; margin-left: 4px; }
.cmp-item .row b.down { color: var(--green-mid); }
.cmp-item .row b.up { color: #C9792F; }

.ex-summary {
  padding: 10px 12px; margin-bottom: 12px;
  background: linear-gradient(135deg, rgba(59,138,94,.06) 0%, rgba(96,165,250,.05) 100%);
  border-radius: 10px; font-size: 12px; line-height: 1.7; color: #3F4A44;
}
.ex-summary b { color: var(--green); font-weight: 700; }

.w-svg { width: 100%; height: auto; display: block; }
.w-svg .y-label { fill: var(--text-light); font-size: 9px; font-weight: 500; }
.w-svg .pt-label { fill: #3F4A44; font-size: 9px; font-weight: 600; text-anchor: middle; }
.w-svg .split-label { fill: var(--amber); font-size: 9px; font-weight: 600; }
.w-svg .x-label { fill: var(--text-light); font-size: 10px; font-weight: 500; text-anchor: middle; }
.w-svg .hit { cursor: pointer; }

.bmr-ratio {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; background: #F5F3EE; border-radius: 8px;
  margin-bottom: 10px; font-size: 11px; color: var(--text-light); line-height: 1.5;
}
.bmr-ratio b { color: var(--text); font-weight: 600; }
.bmr-ratio .bmr-status { font-weight: 600; margin-left: 6px; padding: 1px 7px; border-radius: 10px; }
.bmr-ratio .bmr-status.ok { color: #3B8A5E; background: rgba(59,138,94,.08); }
.bmr-ratio .bmr-status.over { color: #C9792F; background: rgba(224,122,63,.08); }
.bmr-ratio .bmr-status.low { color: #4A90B8; background: rgba(74,144,184,.08); }

.nutri-donut { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px 4px; margin: 4px 0; }
.nd-item { display: flex; align-items: center; gap: 6px; padding: 4px 6px; border-radius: 8px; background: #FAF8F3; }
.nd-chart { width: 50px; height: 50px; flex-shrink: 0; }
.nd-info { flex: 1; min-width: 0; }
.nd-info .nd-name { font-size: 11px; font-weight: 600; color: var(--text); margin-bottom: 1px; }
.nd-row { font-size: 10px; color: var(--text-light); }
.nd-row .nd-val { color: #3F4A44; font-weight: 700; }
.nd-row .nd-slash { margin: 0 2px; opacity: .4; }
.nd-row .nd-tgt { opacity: .7; }
.nd-tag { display: inline-block; margin-top: 2px; padding: 1px 6px; border-radius: 10px; font-size: 9.5px; font-weight: 600; }
.nd-tag.nd-ok { color: #3B8A5E; background: rgba(59,138,94,.08); }
.nd-tag.nd-over { color: #C95A4C; background: rgba(217,123,108,.1); }
.nd-tag.nd-low { color: #C9792F; background: rgba(224,168,79,.12); }

.warn-area { margin-top: 8px; padding-top: 10px; border-top: 1px dashed #ECE7DA; display: flex; flex-direction: column; gap: 6px; }
.warn-row {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 10px; border-radius: 8px; font-size: 11.5px; font-weight: 500;
}
.warn-row.wr-hot { color: #8E4A22; background: rgba(224,122,63,.08); }
.warn-row.wr-cold { color: #1E6A91; background: rgba(74,144,184,.08); }
.warn-row.wr-ok { color: #2A6347; background: rgba(59,138,94,.06); }

.ar-card {
  margin-top: 10px; padding: 12px;
  border-radius: 12px; cursor: pointer;
  background: linear-gradient(135deg, rgba(96,165,250,.05) 0%, rgba(96,165,250,.09) 100%);
  border: 1px solid rgba(96,165,250,.18);
  display: flex; align-items: flex-start; gap: 12px;
  transition: all .25s ease;
}
.ar-card:hover { transform: translateY(-2px); border-color: rgba(96,165,250,.4); box-shadow: 0 8px 20px rgba(96,165,250,.15); }
.ar-icon {
  width: 36px; height: 36px; border-radius: 9px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: #fff; color: #3B7DD2;
  box-shadow: 0 2px 8px rgba(96,165,250,.18);
}
.ar-tag { font-size: 10px; color: #3B7DD2; font-weight: 600; letter-spacing: .5px; }
.ar-title { font-size: 13px; color: var(--text); font-weight: 600; margin-top: 2px; }
.ar-desc { font-size: 11px; color: var(--text-light); margin-top: 3px; line-height: 1.5; }

.goal-bar { margin-top: 4px; padding: 12px; background: linear-gradient(135deg, #F5F3EE 0%, #EFF2EC 100%); border-radius: 10px; }
.gb-top { display: flex; justify-content: space-between; align-items: baseline; font-size: 12px; }
.gb-top .lbl { color: #8A8578; }
.gb-top .cur { color: #33403A; font-weight: 700; font-size: 18px; }
.gb-top .cur small { font-size: 11px; font-weight: 500; color: #A5A090; margin-left: 2px; }
.gb-track { height: 8px; background: #E0DCD0; border-radius: 4px; margin: 8px 0; overflow: hidden; }
.gb-fill { height: 100%; background: linear-gradient(90deg, #7FBF9A, #3B8A5E); border-radius: 4px; transition: width 1s cubic-bezier(.22,1,.36,1); }
.gb-ticks { display: flex; justify-content: space-between; font-size: 9.5px; color: #A5A090; }
.gb-ticks span { text-align: center; width: 33.3%; }
.gb-ticks span.cur { color: #3B8A5E; font-weight: 600; }
.gb-foot { margin-top: 8px; padding-top: 8px; border-top: 1px dashed #E0DCD0; font-size: 11px; color: var(--text-light); }
.gb-foot b { color: var(--green-mid); font-weight: 700; }
.goal-hit { color: var(--green); font-weight: 600; }

.vs-row {
  display: grid; grid-template-columns: 1fr auto 1fr auto 1fr;
  align-items: center;
  padding: 16px 20px; margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(47,93,74,.03) 0%, rgba(224,122,63,.02) 100%);
  border: 1px solid rgba(47,93,74,.08);
  border-radius: 18px;
}
.vs-cell { text-align: center; padding: 4px 8px; }
.vs-k { font-size: 11px; color: var(--text-light); font-weight: 500; }
.vs-v { font-size: 18px; font-weight: 800; color: #33403A; margin-top: 4px; letter-spacing: -.5px; }
.vs-t { font-size: 11px; margin-top: 5px; font-weight: 600; }
.vs-t.up { color: var(--green-mid); }
.vs-t.down { color: #C9792F; }
.vs-t.ok { color: var(--green-mid); }
.vs-t.warn { color: #C9792F; }
.vs-sep { width: 1px; height: 38px; background: #E5E1D3; }

.advice-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 12px; }
.advice-list li {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 12px 14px; border-radius: 10px;
  background: linear-gradient(135deg, #FAFAF7 0%, #F4F6F3 100%);
  border-left: 3px solid rgba(59,138,94,.4);
  font-size: 12.5px; line-height: 1.65; color: #3F4A44;
}
.advice-list li:nth-child(2) { border-left-color: rgba(201,121,47,.45); }
.advice-list li:nth-child(3) { border-left-color: rgba(224,122,63,.45); }
.advice-list li:nth-child(5) { border-left-color: rgba(74,144,184,.4); }

@media print {
  .health-report { padding: 0; }
  .save-btn, .tabs, .ai-btn, .sec-btn { display: none !important; }
  .panel { break-inside: avoid; box-shadow: none; border-color: #ddd; }
}
</style>
