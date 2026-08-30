<template>
  <div class="diet-page">
    <!-- ===== 深壳星轨带 ===== -->
    <div class="db-band" ref="bandRef">
      <div class="db-glow db-glow--1" aria-hidden="true"></div>
      <div class="db-glow db-glow--2" aria-hidden="true"></div>
      <div class="db-top">
        <div class="star-crumbs">
          <span class="crumb-wrap"><button class="crumb-node" @click="go('/dashboard/home')"><span class="nd"><FileText :size="14" /></span>首页</button></span>
          <span class="crumb-wrap"><span class="crumb-link"></span><span class="crumb-node hot"><span class="nd"><FileText :size="14" /></span>健康星报</span></span>
        </div>
        <div class="db-top-right">
          <span class="db-date"><Calendar :size="13" />当前 <b id="p6-cur-label">{{ reportType === 'weekly' ? '周报' : '月报' }}</b></span>
        </div>
      </div>
      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 108" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 54 C 400 10, 600 10, 700 54 S 900 98, 1050 54 S 1150 10, 1200 54" />
        </svg>
        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><FileText :size="19" /></span>
            <span class="tt"><b>健康星报</b><span>HEALTH BRIEFING</span></span>
          </div>
        </div>
        <div v-for="(s, i) in stations" :key="s.nm"
             class="db-station-wrap"
             :style="{ left: stationLeft(i, stations.length) + '%' }"
             @click="switchTab(s.mode)">
          <div class="db-station-float" :style="floatStyle(i)">
            <div class="db-station" :class="{ lit: s.mode === reportType }" :aria-label="s.nm">
              <span class="wb"><component :is="s.icon" :size="16" /></span>
              <span class="nm">{{ s.nm }}</span>
              <span class="ds">{{ s.ds }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区 ===== -->
    <div class="db-paper" ref="paperRef">
      <!-- 头部 -->
      <div class="m-head" data-anim>
        <div class="sec-t">星报总览 · {{ reportType === 'weekly' ? '本周' : '本月' }}饮食与运动健康报告</div>
        <div class="m-pills">
          <span class="pill"><UserRound :size="12" /><b>{{ userInfo.username || '你' }}</b> · BMI <b>{{ bmi || '--' }}</b></span>
          <button class="pill-btn" :disabled="aiPreparing" @click="askAI">
            <Sparkles :size="12" />{{ aiPreparing ? '整理中...' : 'AI 分析' }}
          </button>
          <button class="pill-btn" @click="go('/dashboard/recipe-library')">
            <ChefHat :size="12" />菜谱
          </button>
          <button class="pill-btn" @click="doPrint">
            <Printer :size="12" />打印
          </button>
          <button class="pill-btn save" @click="saveReport">
            <Download :size="12" />保存本期{{ reportType === 'weekly' ? '周报' : '月报' }}
          </button>
        </div>
      </div>

      <!-- 三卡：打卡 / 体重对比 / 运动汇总 -->
      <div class="rpt-top" data-anim>
        <div class="rpt-card">
          <div class="rh"><CalendarCheck :size="14" />{{ reportType === 'weekly' ? '本周' : '本月' }}打卡</div>
          <template v-if="reportType === 'weekly'">
            <div class="rpt-heat">
              <i v-for="(c, i) in weekHeatCells" :key="'w'+i" :class="c.checked ? 'lv1' : ''"></i>
            </div>
            <div class="rpt-heat-row"><span>一</span><span>{{ weekHeatCells.filter(c=>c.checked).length }} / {{ weekHeatCells.length }} 天</span><span>日</span></div>
          </template>
          <template v-else>
            <div class="rpt-heat-month">
              <span v-for="(c, i) in monthHeatCells" :key="'m'+i" class="mc" :class="[c.placeholder ? 'ph' : (c.checked ? 'lv1' : '')]">{{ c.day || '' }}</span>
            </div>
            <div class="rpt-heat-row"><span>月初</span><span>{{ monthHeatCells.filter(c=>c.checked).length }} / {{ monthHeatCells.filter(c=>!c.placeholder).length }} 天</span><span>月末</span></div>
          </template>
        </div>
        <div class="rpt-card">
          <div class="rh"><Scale :size="14" />体重对比</div>
          <div class="rpt-cmp">
            <div class="rr"><span>最高体重</span><b>{{ wCmp.max }} kg</b></div>
            <div class="rr"><span>最低体重</span><b>{{ wCmp.min }} kg</b></div>
            <div class="rr"><span>周期变化</span><b :class="wCmp.diff <= 0 ? 'down' : 'up'">{{ wCmp.diff > 0 ? '+' : '' }}{{ wCmp.diff }} kg</b></div>
            <div class="rr"><span>日均波动</span><b>{{ wCmp.avg }} kg</b></div>
          </div>
        </div>
        <div class="rpt-card">
          <div class="rh"><Dumbbell :size="14" />运动汇总</div>
          <div class="rpt-cmp">
            <div class="rr"><span>运动天数</span><b>{{ exCmp.days }} 天</b></div>
            <div class="rr"><span>总时长</span><b>{{ exCmp.totalMin }} min</b></div>
            <div class="rr"><span>平均每次</span><b>{{ exCmp.avgMin }} min</b></div>
            <div class="rr"><span>消耗热量</span><b>{{ exCmp.totalKcal }} kcal</b></div>
          </div>
        </div>
      </div>

      <!-- 体重趋势图 + 营养达标 -->
      <div class="m-blocks" data-anim>
        <div class="m-block">
          <div class="bl-head"><b>体重趋势</b><span>{{ reportType === 'weekly' ? '本周 7 天' : '本月记录' }}</span></div>
          <div class="chart-box" v-html="weightChartSvg"></div>
        </div>
        <div class="m-block">
          <div class="bl-head"><b>营养达标</b><span>蛋白质 / 脂肪 / 碳水</span></div>
          <div class="rpt-donut-row">
            <div v-for="(n, i) in nutriList" :key="'n'+i" class="rpt-donut">
              <svg viewBox="0 0 56 56">
                <circle cx="28" cy="28" r="22" fill="none" stroke="rgba(184,134,59,.15)" stroke-width="5" />
                <circle cx="28" cy="28" r="22" fill="none" :stroke="donutColor(n.level)" stroke-width="5"
                  :stroke-dasharray="donutCirc" :stroke-dashoffset="donutOffset(n.pct)"
                  transform="rotate(-90 28 28)" stroke-linecap="round" />
              </svg>
              <div class="dn">{{ n.avg }}<small>/{{ n.target }}</small></div>
              <div class="dl">{{ n.name }} {{ n.unit }}</div>
              <span class="dt" :class="n.level">{{ n.level === 'over' ? '偏高' : n.level === 'low' ? '偏低' : n.level === 'none' ? '未记录' : '达标' }}</span>
            </div>
          </div>
          <div class="sec-label">BMR 比例</div>
          <div style="font-size:11px;color:var(--txt);margin-top:6px">
            日均 <b style="font-family:'Noto Serif SC',serif">{{ bmrData.avgKcal }}</b> kcal / BMR <b style="font-family:'Noto Serif SC',serif">{{ bmrData.bmr }}</b> kcal = <b style="color:#B8863B;font-family:'Noto Serif SC',serif">{{ bmrData.ratio }}%</b>
            <span style="display:inline-block;font-size:9px;font-weight:700;padding:1px 7px;border-radius:99px;" :style="bmrStatusStyle">{{ bmrData.statusText }}</span>
          </div>
        </div>
      </div>

      <!-- 目标进度 + vs 上期 -->
      <div class="m-blocks" data-anim>
        <div class="m-block">
          <div class="bl-head"><b>目标进度</b><span>体重管理目标</span></div>
          <div class="rpt-goal-track">
            <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px">
              <span style="color:rgba(42,38,32,.5)">目标进度</span>
              <span style="font-family:'Noto Serif SC',serif;font-weight:900;color:#B8863B">{{ goalData.progressPct }}<small style="font-size:10px">%</small></span>
            </div>
            <div class="rpt-goal-bar"><div class="rpt-goal-fill" :style="{ width: goalData.progressPct + '%' }"></div></div>
            <div class="rpt-goal-ticks"><span>{{ goalData.start }} kg</span><span class="cur">{{ goalData.current }} kg</span><span>目标 {{ goalData.target }} kg</span></div>
            <div style="margin-top:8px;font-size:10.5px;color:rgba(42,38,32,.5)">已减 <b style="color:#2F7D5B">{{ goalData.lost }} kg</b> · {{ goalData.left > 0 ? '还差 ' + goalData.left + ' kg' : '恭喜达成目标' }}</div>
          </div>
        </div>
        <div class="m-block">
          <div class="bl-head"><b>vs 上期</b><span>对比上周 / 上月</span></div>
          <div class="rpt-vs">
            <div class="rpt-vs-cell">
              <div class="k">打卡天数</div>
              <div class="v">{{ vsData.checkin.cur }}<small> / 上期 {{ vsData.checkin.prev }}</small></div>
              <div class="t" :class="vsData.checkin.diff >= 0 ? 'up' : 'down'">较上期 {{ vsData.checkin.diff >= 0 ? '+' : '' }}{{ vsData.checkin.diff }} 天</div>
            </div>
            <div class="rpt-vs-sep"></div>
            <div class="rpt-vs-cell">
              <div class="k">平均热量</div>
              <div class="v">{{ vsData.cal.cur }}<small>kcal</small></div>
              <div class="t" :class="vsData.cal.diff <= 0 ? 'up' : 'down'">较上期 {{ vsData.cal.diff >= 0 ? '+' : '' }}{{ vsData.cal.diff }}</div>
            </div>
            <div class="rpt-vs-sep"></div>
            <div class="rpt-vs-cell">
              <div class="k">运动时长</div>
              <div class="v">{{ vsData.ex.cur }}<small>min</small></div>
              <div class="t" :class="vsData.ex.diff >= 0 ? 'up' : 'down'">较上期 {{ vsData.ex.diff >= 0 ? '+' : '' }}{{ vsData.ex.diff }} min</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 健康总结 -->
      <div class="m-block" data-anim>
        <div class="bl-head"><b>健康总结</b><span>{{ reportType === 'weekly' ? '本周' : '本月' }}</span></div>
        <ul class="rpt-advice">
          <li v-for="(a, i) in adviceList" :key="'a'+i">
            <component :is="a.icon" :size="14" :style="{ color: a.color }" />
            <span>{{ a.text }}</span>
          </li>
        </ul>
      </div>

      <!-- 文章推荐 -->
      <div v-if="articleRec" class="rpt-article" data-anim @click="go('/dashboard/article-detail/' + articleRec.id)">
        <div class="ar-ic"><BookOpen :size="18" /></div>
        <div>
          <div class="ar-tag">为你推荐 · 科普文章</div>
          <div class="ar-title">{{ articleRec.title }}</div>
          <div class="ar-desc">{{ articleRec.summary }}</div>
        </div>
      </div>

      <div id="p6-toast"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, reactive } from 'vue'
import { useRouter } from 'vue-router'
import {
  Download, Calendar, CalendarDays, Sparkles, ChefHat, Printer,
  CalendarCheck, Scale, Dumbbell, TrendingDown, Apple, Flame, BookOpen,
  User, UserRound, Target, ClipboardList, AlertTriangle, CheckCircle, Info,
  FileText, Loader2
} from 'lucide-vue-next'
import { useUserStore, type User as UserInfo } from '@/stores/user'
import { api } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const reportType = ref<'weekly' | 'monthly'>('weekly')
const loading = ref(false)
const bandRef = ref<HTMLElement | null>(null)
const paperRef = ref<HTMLElement | null>(null)

const userInfo = computed(() => userStore.user || ({} as UserInfo))
// 人群标签：user.crowd_type 存短名（普通人/健身/老年/...），文章 audience 存长名（普通人群/健身人群/老年人/...）
const CROWD_LABEL_MAP: Record<string, string> = {
  '普通人': '普通人群', '健身': '健身人群', '老年': '老年人',
  '孕妇': '孕妇', '青少年': '青少年', '糖尿病': '糖尿病患者',
}
const crowdTypeText = computed(() => {
  const raw = (userInfo.value as any).crowd_type || (userInfo.value as any).crowdType || '普通人'
  return CROWD_LABEL_MAP[raw] || raw || '普通人群'
})

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

/* -------------------- 星轨带数据球 -------------------- */
const stations = computed(() => [
  { nm: '周报', ds: '7天 · ' + R.checkinSet.size + '天打卡', icon: Calendar, mode: 'weekly' as const },
  { nm: '月报', ds: '30天 · ' + R.checkinSet.size + '天打卡', icon: CalendarDays, mode: 'monthly' as const },
])
function stationLeft(i: number, total: number): number {
  if (total <= 1) return 50
  return 28 + (i * 44) / (total - 1)
}
function floatStyle(i: number) {
  const durations = [4.6, 5.2]
  const delays = [-0.3, -1.2]
  return { animation: `tpFloat ${durations[i % 2]}s ease-in-out ${delays[i % 2]}s infinite alternate` }
}

/* -------------------- 数据：真实 API -------------------- */
interface ReportShape {
  checkinSet: Set<string>
  prevCheckin: number
  weights: Array<{ date: string; weight: number }>
  weightPred: Array<{ date: string; weight: number }>
  calories: number
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
  prevCheckin: 0,
  weights: [],
  weightPred: [],
  calories: 0,
  prevCalories: 0,
  nutrients: [
    { name: '蛋白质', key: 'protein', unit: 'g', avg: 0, targetMin: 65, targetMax: 78 },
    { name: '脂肪', key: 'fat', unit: 'g', avg: 0, targetMin: 52, targetMax: 65 },
    { name: '碳水化合物', key: 'carb', unit: 'g', avg: 0, targetMin: 195, targetMax: 260 },
    { name: '膳食纤维', key: 'dietFiber', unit: 'g', avg: 0, targetMin: 20, targetMax: 35 },
  ],
  exercise: { days: 0, totalMin: 0, totalKcal: 0, prevMin: 0 },
  bmr: 0,
  startWeight: 0,
  targetWeight: 0,
  advice: [],
})

function calcBmr(u: any): number {
  const w = Number(u.weight)
  const h = Number(u.height)
  const a = Number(u.age)
  if (!w || !h) return 0
  const g = (u.gender || '男')
  return Math.round(g === '女' ? 10 * w + 6.25 * h - 5 * (a || 0) - 161 : 10 * w + 6.25 * h - 5 * (a || 0) + 5)
}

const loadAll = async () => {
  loading.value = true
  try {
    // 周报/月报每次进入直接拉取真实数据，不使用 useReportCache：
    // fetchReport 无返回值会缓存 undefined，导致二次加载命中"空缓存"跳过请求，页面显示全空
    await fetchReport()
  } finally { loading.value = false }
}

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

  const checkinSet = new Set<string>()
  const exDates = new Set(exerciseRecords.map((r: any) => String(r.recordDate || '').slice(0, 10)))
  dates.forEach((date, idx) => {
    const a = analyses[idx]
    if (a && a.total && (a.total.calorie || a.totalCalories || 0) > 0) checkinSet.add(date)
  })
  exDates.forEach(d => checkinSet.add(d))
  R.checkinSet = checkinSet

  const prevCheckinSet = new Set<string>()
  prevAnalyses.forEach((a, idx) => {
    if (a && a.total && (a.total.calorie || a.totalCalories || 0) > 0) prevCheckinSet.add(prevDates[idx])
  })
  R.prevCheckin = prevCheckinSet.size

  const sortedWeights = (metricsList || [])
    .filter((m: any) => Number(m.weight) > 0)
    .map((m: any) => ({ date: String(m.recordDate || '').slice(0, 10), weight: Number(m.weight) }))
    .sort((a, b) => a.date.localeCompare(b.date))
  R.weights = sortedWeights

  if (predictRes && Array.isArray((predictRes as any).predictions) && (predictRes as any).predictions.length) {
    R.weightPred = (predictRes as any).predictions
      .filter((p: any) => p && p.date && p.weight)
      .slice(0, reportType.value === 'weekly' ? 2 : 7)
      .map((p: any) => ({ date: String(p.date).slice(0, 10), weight: +Number(p.weight).toFixed(1) }))
  }

  const validA = analyses.filter((a: any) => a && a.total && (a.total.calorie || a.totalCalories || 0) > 0) as any[]
  R.calories = validA.length > 0
    ? Math.round(validA.reduce((s, a) => s + (a.total?.calorie ?? a.totalCalories ?? 0), 0) / validA.length)
    : R.calories
  const prevValid = prevAnalyses.filter((a: any) => a && a.total && (a.total.calorie || a.totalCalories || 0) > 0) as any[]
  R.prevCalories = prevValid.length > 0
    ? Math.round(prevValid.reduce((s, a) => s + (a.total?.calorie ?? a.totalCalories ?? 0), 0) / prevValid.length)
    : R.prevCalories

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

  const exDays = exDates.size
  const totalMin = exerciseRecords.reduce((s: number, r: any) => s + (Number(r.durationMin) || 0), 0)
  const totalKcal = exerciseRecords.reduce((s: number, r: any) => s + (Number(r.caloriesBurned) || 0), 0)
  const prevMin = prevExerciseRecords.reduce((s: number, r: any) => s + (Number(r.durationMin) || 0), 0)
  R.exercise = { days: exDays, totalMin, totalKcal, prevMin }
  R.bmr = calcBmr(userInfo.value)
  const tw = Number((userInfo.value as any).targetWeight)
  R.targetWeight = tw || 0
  R.startWeight = R.weights.length > 0 ? Math.max(...R.weights.map(w => w.weight)) : 0

  const overList = R.nutrients.filter(n => n.avg > 0 && n.avg / n.targetMax > 1.05)
  const lowList = R.nutrients.filter(n => n.avg > 0 && n.avg / n.targetMin < 0.85)
  const keyword = (overList[0] || lowList[0])?.name
  // 人群匹配优先：先取当前用户人群的文章，其次营养关键词匹配，最后回退最新文章
  const articleArr = articlesList?.list || articlesList || []
  const crowdRecs = articleArr.filter((a: any) => String(a.audience || '') === crowdTypeText.value)
  const kwMatch = (list: any[]) => list.find((a: any) =>
    keyword && (String(a.title || '').includes(keyword) || String(a.summary || '').includes(keyword) || String(a.topic || '').includes(keyword))
  )
  let matched = kwMatch(crowdRecs) || crowdRecs[0] || kwMatch(articleArr) || articleArr[0]
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

onMounted(() => {
  loadAll()
  // GSAP 入场
  import('gsap').then(({ gsap }) => {
    const band = bandRef.value, paper = paperRef.value
    if (!band || !paper) return
    const tl = gsap.timeline()
    tl.from(band.querySelectorAll('.star-crumbs'), { opacity: 0, y: -10, duration: 0.4, ease: 'power2.out' })
      .from(band.querySelectorAll('.db-core-wrap'), { opacity: 0, scale: 0.8, duration: 0.5, ease: 'back.out(1.4)' }, '-=0.2')
      .from(band.querySelectorAll('.db-station-wrap'), { opacity: 0, y: 20, duration: 0.4, stagger: 0.08, ease: 'power2.out' }, '-=0.3')
      .from(paper.querySelectorAll('[data-anim]'), { opacity: 0, y: 16, duration: 0.4, stagger: 0.06, ease: 'power2.out' }, '-=0.2')
  }).catch(() => {})
})
watch(reportType, () => {
  loadAll()
  // 切换时淡入
  if (paperRef.value) {
    import('gsap').then(({ gsap }) => {
      gsap.fromTo(paperRef.value!, { opacity: 0.4, y: 8 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' })
    }).catch(() => {})
  }
})

/* -------------------- 视图计算 -------------------- */
const weekHeatCells = computed(() => {
  const today = new Date()
  const arr: { date: string; checked: boolean }[] = []
  // 最近 7 天（与 fetchReport 的 dates 一致），原实现多减了 dow 导致日期前移一周
  // 与 checkinSet 几乎不重叠，打卡格子显示 1 天/0 天
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today); d.setDate(today.getDate() - i)
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

/* 体重趋势 SVG — 光河星轨风格 */
const weightChartSvg = computed(() => {
  const allW = [...R.weights.map(w => w.weight), ...R.weightPred.map(w => w.weight)]
  if (allW.length === 0) return '<div class="chart-empty">暂无体重记录</div>'
  const minW = Math.min(...allW) - 0.5
  const maxW = Math.max(...allW) + 0.5
  const range = Math.max(1, maxW - minW)
  const W = 640, H = 240, pad = { l: 36, r: 20, t: 20, b: 28 }
  const iw = W - pad.l - pad.r, ih = H - pad.t - pad.b
  const all = [...R.weights.map(w => ({ ...w })), ...R.weightPred.map(w => ({ ...w, pred: true }))]
  const n = all.length
  const pts = all.map((a, i) => ({
    x: pad.l + (n > 1 ? i * iw / (n - 1) : iw / 2),
    y: pad.t + ih - ((a.weight - minW) / range) * ih,
    v: a.weight.toFixed(1),
    pred: (a as any).pred
  }))
  // 平滑路径
  const histPts = pts.filter(p => !p.pred)
  const predPts = pts.filter(p => p.pred)
  function smoothPath(points: typeof pts): string {
    if (points.length < 2) return points.length ? `M ${points[0].x} ${points[0].y}` : ''
    let d = `M ${points[0].x.toFixed(1)} ${points[0].y.toFixed(1)}`
    for (let i = 1; i < points.length; i++) {
      const p0 = points[i - 1], p1 = points[i]
      const cx = (p0.x + p1.x) / 2
      d += ` C ${cx.toFixed(1)} ${p0.y.toFixed(1)}, ${cx.toFixed(1)} ${p1.y.toFixed(1)}, ${p1.x.toFixed(1)} ${p1.y.toFixed(1)}`
    }
    return d
  }
  const histPath = smoothPath(histPts)
  const areaPath = histPts.length ? histPath + ` L ${histPts[histPts.length - 1].x.toFixed(1)} ${pad.t + ih} L ${histPts[0].x.toFixed(1)} ${pad.t + ih} Z` : ''
  const predPath = predPts.length ? smoothPath([histPts[histPts.length - 1], ...predPts].filter(Boolean)) : ''
  let svg = `<svg viewBox="0 0 ${W} ${H}">`
  svg += `<defs><linearGradient id="p6g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#D9A24A" stop-opacity=".22"/><stop offset="1" stop-color="#D9A24A" stop-opacity="0"/></linearGradient>`
  svg += `<filter id="p6glow"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>`
  if (areaPath) svg += `<path d="${areaPath}" fill="url(#p6g)"/>`
  if (histPath) svg += `<path d="${histPath}" fill="none" stroke="#D9A24A" stroke-width="2" stroke-linejoin="round" filter="url(#p6glow)"/>`
  if (predPath) svg += `<path d="${predPath}" fill="none" stroke="#E07A3F" stroke-width="2" stroke-dasharray="4 3" stroke-linejoin="round"/>`
  pts.forEach((p, i) => {
    if (p.pred) {
      svg += `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="#FFF4E8" stroke="#E07A3F" stroke-width="2"/>`
    } else {
      svg += `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="#fff" stroke="#B8863B" stroke-width="2"/>`
      if (i === histPts.length - 1) {
        svg += `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="8" fill="none" stroke="#D9A24A" stroke-width="1" opacity=".4"><animate attributeName="r" values="6;12;6" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" values=".5;0;.5" dur="2s" repeatCount="indefinite"/></circle>`
      }
      svg += `<text x="${p.x.toFixed(1)}" y="${(p.y - 10).toFixed(1)}" text-anchor="middle" font-size="9" fill="#2A2620" font-family="Noto Serif SC">${p.v}</text>`
    }
  })
  svg += `</svg>`
  return svg
})

const bmrData = computed(() => {
  const avg = R.calories
  const bmr = R.bmr
  const ratio = bmr > 0 && avg > 0 ? Math.round(avg / bmr * 100) : 0
  let statusClass = 'ok', statusText = '摄入均衡'
  if (!bmr || !avg) { statusClass = 'none'; statusText = '暂无记录' }
  else if (ratio > 110) { statusClass = 'over'; statusText = '摄入偏高' }
  else if (ratio < 90) { statusClass = 'low'; statusText = '摄入偏低' }
  return { avgKcal: avg, bmr, ratio, statusClass, statusText }
})
const bmrStatusStyle = computed(() => {
  const c = bmrData.value.statusClass
  const colors: Record<string, string> = { ok: '#2F7D5B', over: '#C9792F', low: '#4A90B8', none: '#8A958C' }
  const bgs: Record<string, string> = { ok: 'rgba(47,125,91,.12)', over: 'rgba(201,121,47,.1)', low: 'rgba(74,144,184,.1)', none: 'rgba(138,149,156,.1)' }
  return { color: colors[c], background: bgs[c] }
})

const nutriList = computed(() => R.nutrients.map(n => {
  const target = Math.round((n.targetMin + n.targetMax) / 2)
  const pct = target > 0 && n.avg > 0 ? Math.round(n.avg / target * 100) : 0
  let level: 'over' | 'low' | 'ok' | 'none' = 'ok', statusText = `达标 ${pct}%`
  if (n.avg <= 0) { level = 'none'; statusText = '未记录' }
  else if (n.avg / n.targetMax > 1.05) { level = 'over'; statusText = `超标 ${Math.round(n.avg / n.targetMax * 100)}%` }
  else if (n.avg / n.targetMin < 0.85) { level = 'low'; statusText = `偏低 ${pct}%` }
  return { ...n, target, pct, level, statusText }
}))

const donutCirc = (2 * Math.PI * 22).toFixed(1)
function donutOffset(pct: number) { return (2 * Math.PI * 22 * (1 - Math.min(pct, 100) / 100)).toFixed(1) }
function donutColor(level: string) {
  return level === 'ok' ? '#3B8A5E' : level === 'over' ? '#C0522F' : level === 'low' ? '#E0A84F' : '#D9D4C8'
}

const articleRec = computed(() => R.articleRec)

const goalData = computed(() => {
  const start = R.startWeight || Number(userInfo.value.weight) || 0
  const current = R.weights.length ? R.weights[R.weights.length - 1].weight : Number(userInfo.value.weight) || 0
  const target = R.targetWeight || 0
  const totalSpan = start - target
  const lost = Math.max(0, +(start - current).toFixed(1))
  const left = target > 0 ? Math.max(0, +(current - target).toFixed(1)) : 0
  const progressPct = target > 0 && totalSpan > 0 ? Math.max(0, Math.min(100, Math.round(lost / totalSpan * 100))) : 0
  return { start, current: +current.toFixed(1), target, lost, left, progressPct }
})

const vsData = computed(() => {
  const curCheckin = R.checkinSet.size
  const prevCheckin = R.prevCheckin
  return {
    checkin: { cur: curCheckin, prev: prevCheckin, diff: curCheckin - prevCheckin },
    cal: { cur: R.calories, prev: R.prevCalories, diff: R.calories - R.prevCalories },
    ex: { cur: R.exercise.totalMin, prev: R.exercise.prevMin, diff: R.exercise.totalMin - R.exercise.prevMin },
  }
})

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

/* 操作 */
function switchTab(t: 'weekly' | 'monthly') { reportType.value = t }
function go(url: string) { router.push(url) }
function saveReport() {
  // 直接导出当前报告数据快照（JSON），供离线保存/分享
  const snapshot = {
    type: reportType.value,
    generatedAt: new Date().toISOString().slice(0, 10),
    user: userInfo.value,
    report: JSON.parse(JSON.stringify(R)),
  }
  const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `健康报告_${reportType.value}_${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
}
function doPrint() { window.print() }

/* ---- AI 分析 ---- */
const aiPreparing = ref(false)
const AI_CONTEXT_KEY = 'AI_CONSULT_PENDING_PROMPT'

function buildIssueList(): { name: string; kind: 'over' | 'low'; pct: number }[] {
  return R.nutrients
    .map(n => {
      if (n.avg / n.targetMax > 1.05) return { name: n.name, kind: 'over' as const, pct: Math.round(n.avg / n.targetMax * 100) }
      if (n.avg / n.targetMin < 0.85) return { name: n.name, kind: 'low' as const, pct: Math.round(n.avg / n.targetMin * 100) }
      return null
    })
    .filter((x): x is { name: string; kind: 'over' | 'low'; pct: number } => x !== null)
}

async function retrieveKnowledgeForIssues(issues: { name: string; kind: 'over' | 'low' }[]): Promise<string> {
  if (!issues.length) return ''
  const kb: string[] = []
  const maxQueries = Math.min(3, issues.length)
  for (let i = 0; i < maxQueries; i++) {
    const q = issues[i]
    const action = q.kind === 'over' ? '摄入超标 健康风险 控制建议' : '摄入不足 补充建议'
    try {
      const res: any = await api.ai.knowledgeRetrieve({ query: `${q.name}${action}`, top_k: 3, target_crowd: crowdTypeText.value })
      const results: any[] = res?.results || []
      results.slice(0, 2).forEach(r => {
        const content = String(r?.content || '').trim()
        if (content) kb.push(`【${q.name}${q.kind === 'over' ? '超标' : '不足'} · 知识卡片】${content.slice(0, 500)}`)
      })
    } catch { /* skip */ }
  }
  return kb.join('\n')
}

function buildReportContext(issues: { name: string; kind: 'over' | 'low'; pct: number }[], kbText: string) {
  const periodLabel = reportType.value === 'weekly' ? '本周' : '本月'
  const periodDays = reportType.value === 'weekly' ? 7 : 30
  const nList = R.nutrients.map(n => `- ${n.name}：实际 ${n.avg}${n.unit}，目标区间 ${n.targetMin}-${n.targetMax}${n.unit}`).join('\n')
  const wStr = R.weights.length >= 2
    ? `最高 ${Math.max(...R.weights.map(w => w.weight)).toFixed(1)}kg，最低 ${Math.min(...R.weights.map(w => w.weight)).toFixed(1)}kg，较期初变化 ${(R.weights[R.weights.length - 1].weight - R.weights[0].weight).toFixed(1)}kg（记录 ${R.weights.length} 次）`
    : `共 ${R.weights.length} 次记录，数据不足无法比较`
  const weightDates = R.weights.length ? R.weights.map((w: any) => `${w.date || '??'} ${w.weight.toFixed(1)}kg`).join('、') : '无'
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

  const issueRows = issues.length
    ? issues.map(i => {
        const cfg = (i.kind === 'over' ? NUTRI_ADVICE[i.name]?.over : NUTRI_ADVICE[i.name]?.low) ?? (i.kind === 'over' ? DEFAULT_NUTRI_OVER : DEFAULT_NUTRI_LOW)
        const n = R.nutrients.find((x: any) => x.name === i.name)
        const actualTarget = n ? `${n.avg}${n.unit} / ${n.targetMin}-${n.targetMax}${n.unit}` : '--'
        const status = i.kind === 'over' ? `超标约 ${i.pct}%` : `仅约 ${i.pct}%，不足`
        return `| ${i.name} | ${status} | ${actualTarget} | ${cfg.foods} |`
      }).join('\n')
    : '|（暂无明显营养超标/不足问题）| - | - | - |'
  const issue_table = `| 营养素 | 状态 | 实际值 / 目标区间 | 必须针对的食物类别 |\n|---|---|---|---|\n${issueRows}`
  return { period_label: periodLabel, report_body, issue_table, kb_snippets: kbText || '（无本地知识库参考）' }
}

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
      prompt: displayText,
      actualQuestion: displayText,
      report_context: buildReportContext(issues, kbText),
      high_performance: userStore.highPerformance,
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
</script>

<style scoped>
.diet-page { font-family: 'Noto Sans SC', system-ui, sans-serif; --txt: #2A2620; }

/* ===== 深壳星轨带 ===== */
.db-band {
  background: linear-gradient(180deg, #1A140C 0%, #2A2018 60%, #1A140C 100%);
  border-radius: 18px; padding: 20px 28px 16px; position: relative; overflow: hidden;
  margin-bottom: 16px;
}
.db-glow { position: absolute; border-radius: 50%; filter: blur(60px); pointer-events: none; }
.db-glow--1 { width: 280px; height: 280px; background: rgba(217,162,74,.1); top: -80px; right: 10%; }
.db-glow--2 { width: 200px; height: 200px; background: rgba(184,134,59,.08); bottom: -60px; left: 5%; }
.db-top { display: flex; align-items: center; margin-bottom: 8px; }
.star-crumbs { display: flex; align-items: center; gap: 0; }
.crumb-wrap { display: inline-flex; align-items: center; }
.crumb-link { width: 24px; height: 1px; background: rgba(217,162,74,.3); margin: 0 4px; }
.crumb-node {
  display: inline-flex; align-items: center; gap: 5px; font-size: 11px; color: rgba(255,255,255,.5);
  background: none; border: none; cursor: pointer; font-family: inherit; transition: color .25s;
}
.crumb-node:hover { color: rgba(255,255,255,.8); }
.crumb-node.hot { color: #D9A24A; }
.crumb-node .nd {
  width: 18px; height: 18px; border-radius: 6px; background: rgba(217,162,74,.12);
  display: flex; align-items: center; justify-content: center; color: #D9A24A;
}
.crumb-node.hot .nd { background: rgba(217,162,74,.25); }
.db-top-right { margin-left: auto; display: flex; align-items: center; gap: 12px; }
.db-date { font-size: 11px; color: rgba(255,255,255,.6); display: flex; align-items: center; gap: 4px; }
.db-date b { color: #D9A24A; font-family: 'Noto Serif SC', serif; }

.db-const { position: relative; min-height: 90px; display: flex; align-items: center; justify-content: center; }
.db-line { position: absolute; inset: 0; width: 100%; height: 100%; opacity: .25; }
.db-line path { fill: none; stroke: #D9A24A; stroke-width: 1.5; stroke-dasharray: 4 6; }
.db-core-wrap { position: relative; z-index: 2; }
.db-core {
  display: flex; align-items: center; gap: 10px; padding: 8px 16px;
  background: rgba(26,20,12,.6); border: 1px solid rgba(217,162,74,.3); border-radius: 14px;
  backdrop-filter: blur(8px);
}
.db-core .star {
  width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center; justify-content: center;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%); color: #D9A24A;
  border: 1px solid rgba(217,162,74,.4);
}
.db-core .tt { display: flex; flex-direction: column; }
.db-core .tt b { font-size: 14px; color: #fff; font-family: 'Noto Serif SC', serif; }
.db-core .tt span { font-size: 8px; color: rgba(217,162,74,.5); letter-spacing: .12em; }

.db-station-wrap { position: absolute; top: 50%; transform: translateY(-50%); z-index: 3; cursor: pointer; }
.db-station {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  width: 72px; text-align: center;
}
.db-station .wb {
  width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  color: #D9A24A; font-family: 'Noto Serif SC', serif;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 2px solid rgba(217,162,74,.4); transition: .3s;
}
.db-station:hover .wb { border-color: #D9A24A; box-shadow: 0 0 12px rgba(217,162,74,.4); }
.db-station.lit .wb { border-color: #D9A24A; box-shadow: 0 0 16px rgba(217,162,74,.5); background: radial-gradient(circle at 34% 30%, #4A3A22, #1A140C 72%); }
.db-station .nm { font-size: 10px; color: rgba(255,255,255,.7); font-weight: 600; }
.db-station.lit .nm { color: #D9A24A; }
.db-station .ds { font-size: 9px; color: rgba(217,162,74,.6); }

@keyframes tpFloat { from { transform: translateY(-4px); } to { transform: translateY(4px); } }

/* ===== 浅芯工作区 ===== */
.db-paper {
  background: rgba(255,252,247,.92); border: 1px solid rgba(184,134,59,.14);
  border-radius: 18px; padding: 20px 24px;
}
.m-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 8px; }
.sec-t { font-size: 14px; font-weight: 700; color: #2A2620; }
.m-pills { display: flex; gap: 6px; flex-wrap: wrap; }
.pill {
  font-size: 10px; color: #B8863B; background: rgba(184,134,59,.1);
  padding: 3px 10px; border-radius: 99px; display: flex; align-items: center; gap: 4px; font-weight: 600;
}
.pill b { color: #2A2620; font-family: 'Noto Serif SC', serif; }
.pill-btn {
  font-size: 10px; color: #B8863B; background: rgba(184,134,59,.1);
  padding: 4px 10px; border-radius: 99px; border: 1px solid rgba(184,134,59,.2);
  display: flex; align-items: center; gap: 4px; font-weight: 600; cursor: pointer; font-family: inherit; transition: .2s;
}
.pill-btn:hover { background: rgba(184,134,59,.18); border-color: #B8863B; }
.pill-btn:disabled { opacity: .5; cursor: not-allowed; }
.pill-btn.save { background: linear-gradient(135deg, rgba(217,162,74,.2), rgba(184,134,59,.14)); }

/* 三卡 */
.rpt-top { display: grid; grid-template-columns: 1.25fr 1fr 1fr; gap: 10px; margin-bottom: 12px; }
@media (max-width: 900px) { .rpt-top { grid-template-columns: 1fr; } }
.rpt-card {
  background: rgba(255,255,255,.72); border: 1px solid rgba(184,134,59,.16);
  border-radius: 14px; padding: 14px;
}
.rpt-card .rh { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; color: #2A2620; margin-bottom: 10px; }
.rpt-card .rh svg { color: #B8863B; }
.rpt-heat { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }
.rpt-heat i { aspect-ratio: 1; border-radius: 3px; background: rgba(184,134,59,.1); }
.rpt-heat i.lv1 { background: linear-gradient(135deg, #D9A24A, #B8863B); }
.rpt-heat-month { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }
.rpt-heat-month .mc { aspect-ratio: 1; font-size: 7px; display: flex; align-items: center; justify-content: center; border-radius: 3px; background: rgba(184,134,59,.08); color: rgba(42,38,32,.3); font-weight: 600; }
.rpt-heat-month .mc.ph { background: transparent; color: transparent; }
.rpt-heat-month .mc.lv1 { background: linear-gradient(135deg, rgba(217,162,74,.3), rgba(184,134,59,.2)); color: #B8863B; }
.rpt-heat-row { display: flex; justify-content: space-between; font-size: 10px; color: rgba(42,38,32,.4); margin-top: 6px; }
.rpt-heat-row span:nth-child(2) { color: #B8863B; font-weight: 700; }

.rpt-cmp { display: flex; flex-direction: column; gap: 4px; }
.rpt-cmp .rr { display: flex; justify-content: space-between; font-size: 11.5px; padding: 3px 0; border-bottom: 1px dashed rgba(184,134,59,.1); }
.rpt-cmp .rr:last-child { border: none; }
.rpt-cmp .rr span { color: rgba(42,38,32,.5); }
.rpt-cmp .rr b { color: #2A2620; font-family: 'Noto Serif SC', serif; }
.rpt-cmp .rr b.down { color: #2F7D5B; }
.rpt-cmp .rr b.up { color: #C0522F; }

/* 区块网格 */
.m-blocks { display: grid; grid-template-columns: 7fr 5fr; gap: 10px; margin-bottom: 12px; }
@media (max-width: 900px) { .m-blocks { grid-template-columns: 1fr; } }
.m-block {
  background: rgba(255,255,255,.72); border: 1px solid rgba(184,134,59,.16);
  border-radius: 14px; padding: 14px;
}
.m-block .bl-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.m-block .bl-head b { font-size: 12.5px; color: #2A2620; font-family: 'Noto Serif SC', serif; }
.m-block .bl-head span { font-size: 10px; color: rgba(42,38,32,.4); }
.chart-box { width: 100%; }
.chart-box svg { width: 100%; height: auto; display: block; }
.chart-empty { text-align: center; padding: 40px 0; color: rgba(42,38,32,.3); font-size: 12px; }
.sec-label { font-size: 10px; color: rgba(42,38,32,.4); margin-top: 10px; font-weight: 600; }

/* 营养环形图 */
.rpt-donut-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.rpt-donut { display: flex; align-items: center; gap: 8px; padding: 6px; border-radius: 10px; background: rgba(255,255,255,.5); }
.rpt-donut svg { width: 48px; height: 48px; flex-shrink: 0; }
.rpt-donut .dn { font-size: 12px; font-weight: 800; color: #2A2620; font-family: 'Noto Serif SC', serif; }
.rpt-donut .dn small { font-size: 9px; color: rgba(42,38,32,.4); font-weight: 400; }
.rpt-donut .dl { font-size: 10px; color: rgba(42,38,32,.5); }
.rpt-donut .dt { font-size: 9px; font-weight: 700; padding: 1px 6px; border-radius: 99px; }
.rpt-donut .dt.ok { color: #2F7D5B; background: rgba(47,125,91,.1); }
.rpt-donut .dt.over { color: #C0522F; background: rgba(192,82,47,.1); }
.rpt-donut .dt.low { color: #E0A84F; background: rgba(224,168,79,.1); }
.rpt-donut .dt.none { color: #8A958C; background: rgba(138,149,156,.1); }

/* 目标进度 */
.rpt-goal-bar { height: 8px; background: rgba(184,134,59,.1); border-radius: 99px; overflow: hidden; }
.rpt-goal-fill { height: 100%; background: linear-gradient(90deg, #D9A24A, #B8863B); border-radius: 99px; transition: width .5s ease; }
.rpt-goal-ticks { display: flex; justify-content: space-between; font-size: 10px; color: rgba(42,38,32,.4); margin-top: 4px; }
.rpt-goal-ticks .cur { color: #B8863B; font-weight: 700; font-family: 'Noto Serif SC', serif; }

/* vs 上期 */
.rpt-vs { display: flex; align-items: stretch; }
.rpt-vs-cell { flex: 1; text-align: center; padding: 4px; }
.rpt-vs-cell .k { font-size: 10px; color: rgba(42,38,32,.4); }
.rpt-vs-cell .v { font-size: 14px; font-weight: 800; color: #2A2620; font-family: 'Noto Serif SC', serif; margin: 2px 0; }
.rpt-vs-cell .v small { font-size: 9px; color: rgba(42,38,32,.4); font-weight: 400; }
.rpt-vs-cell .t { font-size: 9.5px; font-weight: 600; }
.rpt-vs-cell .t.up { color: #2F7D5B; }
.rpt-vs-cell .t.down { color: #C0522F; }
.rpt-vs-sep { width: 1px; background: rgba(184,134,59,.12); margin: 4px 0; }

/* 健康总结 */
.rpt-advice { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.rpt-advice li { display: flex; align-items: flex-start; gap: 8px; font-size: 12px; color: #2A2620; line-height: 1.6; }
.rpt-advice li svg { flex-shrink: 0; margin-top: 2px; }

/* 文章推荐 */
.rpt-article {
  display: flex; align-items: center; gap: 12px; padding: 14px;
  background: rgba(255,255,255,.72); border: 1px solid rgba(184,134,59,.16);
  border-radius: 14px; cursor: pointer; transition: .25s;
}
.rpt-article:hover { border-color: #B8863B; transform: translateY(-2px); box-shadow: 0 8px 24px -10px rgba(184,134,59,.25); }
.rpt-article .ar-ic {
  width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center;
  background: rgba(184,134,59,.1); color: #B8863B; flex-shrink: 0;
}
.rpt-article .ar-tag { font-size: 9.5px; color: #B8863B; font-weight: 600; }
.rpt-article .ar-title { font-size: 13px; font-weight: 700; color: #2A2620; margin: 2px 0; }
.rpt-article .ar-desc { font-size: 11px; color: rgba(42,38,32,.5); line-height: 1.5; }
</style>
