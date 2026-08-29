<template>
  <div class="diet-page">
    <!-- ===== 深壳星轨带（体征星轨 · 快照数据球上下浮动） ===== -->
    <div class="db-band" ref="bandRef">
      <div class="db-glow db-glow--1" aria-hidden="true"></div>
      <div class="db-glow db-glow--2" aria-hidden="true"></div>

      <div class="db-top">
        <div class="star-crumbs">
          <span class="crumb-wrap">
            <button class="crumb-node" @click="goHome">
              <span class="nd"><Home :size="12" /></span>首页
            </button>
          </span>
          <span class="crumb-wrap">
            <span class="crumb-link"></span>
            <button class="crumb-node" @click="goHub"><span class="nd"><UsersRound :size="12" /></span>用户中心</button>
          </span>
          <span class="crumb-wrap">
            <span class="crumb-link"></span>
            <span class="crumb-node hot"><span class="nd"><HeartPulse :size="13" /></span>身体指标</span>
          </span>
        </div>
        <div class="db-top-right">
          <span class="db-date"><Database :size="12" />快照 <b>{{ records.length }}</b> 条</span>
        </div>
      </div>

      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 104" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 52 C 300 8, 440 8, 560 52 S 830 96, 960 52 S 1130 8, 1200 52" />
        </svg>

        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><HeartPulse :size="19" /></span>
            <span class="tt"><b>体征星轨</b><span>METRIC ORBIT</span></span>
          </div>
        </div>

        <!-- 快照数据球：体重 / 身高 / BMI 可切换趋势，BMR 实时计算 -->
        <div
          v-for="(s, i) in stations" :key="s.k"
          class="db-station-wrap"
          :style="{ left: stationLeft(i, stations.length) + '%' }"
        >
          <div class="db-station-float" :style="floatStyle(i)">
            <button
              class="db-station"
              :class="{ lit: metric === s.k }"
              :aria-label="s.nm"
              @click="pickMetric(s.k)"
            >
              <component :is="s.icon" :size="15" />
              <span class="nm">{{ s.nm }}</span>
              <span class="ds">{{ s.ds }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区（指标星轨） ===== -->
    <div class="db-paper" ref="paperRef">
      <div class="db-head" data-anim>
        <div class="sec-t">指标星轨 · 每一次保存都是一颗快照星</div>
      </div>

      <div v-if="toastMsg" class="kr-toast" :class="{ err: toastErr }" data-anim>{{ toastMsg }}</div>

      <div class="db-blocks">
        <!-- 左：指标趋势图 + 2x2 汇总格 -->
        <div class="db-block main" data-anim>
          <div class="bl-head wrap">
            <b>{{ metricName }}</b>
            <span class="rk-pills">
              <button
                v-for="r in RANGES" :key="r.v"
                class="rk-pill" :class="{ on: range === r.v }"
                @click="range = r.v"
              >{{ r.n }}</button>
            </span>
            <span class="p4-hint">{{ metricUnit }} · 点击圆点载入当日数据</span>
          </div>
          <div class="chart-box" ref="chartBoxRef" @mousemove="onChartMove" @mouseleave="onChartLeave" @click="onChartClick">
            <div v-if="!chartData.svg" class="kin-empty">
              还没有快照星 · 在右侧写入第一颗，趋势线上就会亮起一颗星
            </div>
            <div v-else v-html="chartData.svg"></div>
            <div v-if="tip.show" class="ct-tip" :style="{ left: tip.left + 'px', top: tip.top + 'px' }">
              <b>{{ tip.title }}</b>
              <span class="v">{{ tip.value }}<small>{{ tip.unit }}</small></span>
              <span class="d" :class="tip.cls">{{ tip.diff }}</span>
            </div>
          </div>
          <div class="mt-cells inblock" data-anim>
            <div v-for="c in cells" :key="c.lb" class="mt-cell">
              <div class="lb">{{ c.lb }}</div>
              <div class="vl">{{ c.vl }}<small>{{ c.un }}</small></div>
              <div class="sub" :class="c.cls">{{ c.sub }}</div>
            </div>
          </div>
        </div>

        <!-- 右：补录历史快照 + 体重预测 -->
        <div class="db-block side" data-anim ref="fblockRef">
          <div class="bl-head"><b>补录历史快照</b><span>同日记录将被更新</span></div>
          <div class="mt-form">
            <div class="ff"><label>日期 *</label><input v-model="form.recordDate" type="date" /></div>
            <div class="ff"><label>年龄（岁）</label><input v-model.number="form.age" type="number" /></div>
            <div class="ff"><label>身高（cm）</label><input v-model.number="form.height" type="number" step="0.1" /></div>
            <div class="ff"><label>体重（kg）</label><input v-model.number="form.weight" type="number" step="0.1" /></div>
          </div>
          <button class="btn-gold full" :disabled="saving" @click="saveSnapshot">
            <Save :size="13" />{{ saving ? '写入中…' : '写入快照' }}
          </button>
          <button v-if="formDateExists" class="btn-ghost full" @click="askDelete">
            <Trash2 :size="12" />删除该日快照
          </button>
          <div class="mt-note">建议补录早于今天的日期，避免覆盖「个人中心」保存时生成的今日记录。</div>

          <div class="sec-label">未来 <span>{{ predDays }}</span> 天体重预测</div>
          <div class="pred-wrap">
            <div class="pred-head">
              线性外推 · 置信区间随距离放宽
              <span v-if="pred" class="pred-chip" :class="pred.trend">{{ pred.trendLabel }}</span>
            </div>
            <div class="chart-box" v-html="pred?.svg"></div>
            <div v-if="pred" class="pred-msg">{{ pred.msg }}</div>
            <div v-else class="pred-msg">暂无足够数据进行预测（至少 2 条体重记录）</div>
            <div class="pred-ops">
              <button @click="changePred(-7)">-7天</button>
              <button @click="changePred(7)">+7天</button>
              <span>基于历史体重线性回归，仅供参考</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除快照 · 气泡二次确认（无遮罩） -->
    <div v-if="showDelete" class="kr-bubble">
      <b>删除该日快照？</b>
      <span>确认后将删除 {{ form.recordDate }} 的指标记录，趋势线上对应的那颗星会熄灭。</span>
      <div class="kr-bubble-op">
        <button class="btn-mini red" @click="confirmDelete">确认删除</button>
        <button class="btn-mini plain" @click="showDelete = false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import {
  Home, UsersRound, HeartPulse, Database, Save, Trash2,
  Weight, Ruler, Gauge, Flame
} from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'

const userStore = useUserStore()
const router = useRouter()

interface MetricRecord {
  historyId: number | null
  recordDate: string
  height: number | null
  weight: number | null
  age: number | null
}

const RANGES = [
  { v: 14, n: '近14天' },
  { v: 30, n: '近30天' },
  { v: 0, n: '全部' }
]
const METRIC_META: Record<string, { name: string; u: string }> = {
  w: { name: '体重变化', u: 'kg' },
  h: { name: '身高走势', u: 'cm' },
  bmi: { name: 'BMI 走势', u: '比' }
}

const records = ref<MetricRecord[]>([])
const metric = ref<'w' | 'h' | 'bmi'>('w')
const range = ref(30)
const predDays = ref(14)
const loading = ref(false)
const saving = ref(false)
const toastMsg = ref('')
const toastErr = ref(false)
const showDelete = ref(false)

const form = reactive<{ recordDate: string; age: number | null; height: number | null; weight: number | null }>({
  recordDate: '',
  age: null,
  height: null,
  weight: null
})

// ---------- 工具 ----------
function popToast(msg: string, isErr = false) {
  toastMsg.value = msg
  toastErr.value = isErr
  setTimeout(() => { if (toastMsg.value === msg) toastMsg.value = '' }, 3200)
}
function errMsg(e: any) {
  return e?.response?.data?.message || e?.message || '操作失败'
}
function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'user' } }) }
function todayStr(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
function fix1(v: any): number | null {
  const n = Number(v)
  return Number.isFinite(n) ? Math.round(n * 10) / 10 : null
}
function fixInt(v: any): number | null {
  const n = Number(v)
  return Number.isFinite(n) ? Math.round(n) : null
}

// ---------- 数据加载 ----------
async function loadData() {
  const uid = userStore.activeUserId || userStore.user?.user_id
  if (!uid) { records.value = []; return }
  loading.value = true
  try {
    const list: any = await api.metrics.history(uid)
    records.value = (Array.isArray(list) ? list : []).map((r: any) => ({
      historyId: r.historyId ?? r.history_id ?? null,
      recordDate: String(r.recordDate ?? r.record_date ?? '').slice(0, 10),
      height: fix1(r.height),
      weight: fix1(r.weight),
      age: fixInt(r.age)
    })).filter(r => r.recordDate)
  } catch (e: any) {
    console.warn('加载指标失败', e)
    records.value = []
  } finally {
    loading.value = false
  }
}

// 按日期升序的时间序列
const chrono = computed<MetricRecord[]>(() =>
  [...records.value].sort((a, b) => (a.recordDate < b.recordDate ? -1 : 1))
)
const latest = computed<MetricRecord | null>(() =>
  chrono.value.length ? chrono.value[chrono.value.length - 1] : null
)

// ---------- BMR / BMI ----------
function calcBmr(w?: number | null, h?: number | null, age?: number | null): number | null {
  const W = Number(w), H = Number(h), A = Number(age)
  if (!Number.isFinite(W) || !Number.isFinite(H) || !Number.isFinite(A) || W <= 0 || H <= 0) return null
  const gender = String(userStore.user?.gender || userStore.user?.sex || '男')
  const isFemale = gender.includes('女') || gender.toLowerCase() === 'f' || gender.toLowerCase() === 'female'
  return Math.round(10 * W + 6.25 * H - 5 * A + (isFemale ? -161 : 5))
}
function calcBmi(r?: MetricRecord | null): number | null {
  if (!r) return null
  const w = Number(r.weight), h = Number(r.height)
  if (!Number.isFinite(w) || !Number.isFinite(h) || w <= 0 || h <= 0) return null
  const hm = h / 100
  return Math.round((w / (hm * hm)) * 10) / 10
}

// ---------- 星轨带数据球 ----------
const stations = computed(() => {
  const r = latest.value
  const bmi = calcBmi(r)
  const bmr = r ? calcBmr(r.weight, r.height, r.age) : null
  return [
    { k: 'w' as const, icon: Weight, nm: '体重 · ' + (r?.weight != null ? r.weight.toFixed(1) : '-') + 'kg', ds: '点击切换体重趋势' },
    { k: 'h' as const, icon: Ruler, nm: '身高 · ' + (r?.height != null ? r.height.toFixed(1) : '-') + 'cm', ds: '点击切换身高走势' },
    { k: 'bmi' as const, icon: Gauge, nm: 'BMI · ' + (bmi != null ? bmi.toFixed(1) : '-'), ds: '点击切换 BMI 走势' },
    { k: 'bmr' as const, icon: Flame, nm: 'BMR · ' + (bmr != null ? bmr.toLocaleString() : '-'), ds: '实时计算 · 不参与切换' }
  ]
})
function pickMetric(k: 'w' | 'h' | 'bmi' | 'bmr') {
  if (k === 'bmr') { popToast('BMR 由身高 / 体重 / 年龄实时计算，不参与切换'); return }
  metric.value = k
}
const metricName = computed(() => METRIC_META[metric.value].name)
const metricUnit = computed(() => METRIC_META[metric.value].u)

function stationLeft(i: number, total: number): number {
  if (total <= 1) return 64
  if (total <= 5) return 34 + i * (60 / (total - 1))
  return 30 + i * (66 / (total - 1))
}
function floatStyle(i: number): Record<string, string> {
  return {
    animationDuration: (4.6 + (i % 4) * 0.45) + 's',
    animationDelay: -(i * 0.9) + 's'
  }
}

// ---------- 指标取值 / 过滤 ----------
function valOf(r: MetricRecord): number | null {
  if (metric.value === 'w') return r.weight
  if (metric.value === 'h') return r.height
  return calcBmi(r)
}
const filteredRecords = computed<MetricRecord[]>(() => {
  let list = chrono.value
  if (range.value) {
    const cut = new Date()
    cut.setDate(cut.getDate() - range.value)
    const cutStr = `${cut.getFullYear()}-${String(cut.getMonth() + 1).padStart(2, '0')}-${String(cut.getDate()).padStart(2, '0')}`
    list = list.filter(r => r.recordDate >= cutStr)
  }
  return list.filter(r => valOf(r) != null)
})

// ---------- SVG 绘制工具 ----------
function smoothPath(pts: Array<{ x: number; y: number }>): string {
  if (!pts.length) return ''
  if (pts.length < 2) return 'M' + pts[0].x.toFixed(1) + ' ' + pts[0].y.toFixed(1)
  let d = 'M' + pts[0].x.toFixed(1) + ' ' + pts[0].y.toFixed(1)
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)]
    d += ' C' + (p1.x + (p2.x - p0.x) / 6).toFixed(1) + ' ' + (p1.y + (p2.y - p0.y) / 6).toFixed(1) + ' '
      + (p2.x - (p3.x - p1.x) / 6).toFixed(1) + ' ' + (p2.y - (p3.y - p1.y) / 6).toFixed(1) + ' '
      + p2.x.toFixed(1) + ' ' + p2.y.toFixed(1)
  }
  return d
}
function starPath(cx: number, cy: number, r: number): string {
  const k = r * 0.18
  return 'M' + cx.toFixed(1) + ' ' + (cy - r).toFixed(1)
    + ' Q' + (cx + k).toFixed(1) + ' ' + (cy - k).toFixed(1) + ' ' + (cx + r).toFixed(1) + ' ' + cy.toFixed(1)
    + ' Q' + (cx + k).toFixed(1) + ' ' + (cy + k).toFixed(1) + ' ' + cx.toFixed(1) + ' ' + (cy + r).toFixed(1)
    + ' Q' + (cx - k).toFixed(1) + ' ' + (cy + k).toFixed(1) + ' ' + (cx - r).toFixed(1) + ' ' + cy.toFixed(1)
    + ' Q' + (cx - k).toFixed(1) + ' ' + (cy - k).toFixed(1) + ' ' + cx.toFixed(1) + ' ' + (cy - r).toFixed(1) + ' Z'
}

// ---------- 主图：光河星轨 ----------
const chartData = computed<{ svg: string; pts: Array<{ x: number; y: number; r: MetricRecord }> }>(() => {
  const data = filteredRecords.value
  if (!data.length) return { svg: '', pts: [] }
  const W = 640, H = 480, L = 46, R = 20, T = 30, B = 40
  const vals = data.map(r => valOf(r) as number)
  let mn = Math.min(...vals), mx = Math.max(...vals)
  if (mx - mn < 1) { const m = (mx + mn) / 2; mn = m - 0.6; mx = m + 0.6 }
  const pad = (mx - mn) * 0.18
  mn -= pad; mx += pad
  const X = (i: number) => L + (W - L - R) * (data.length === 1 ? 0.5 : i / (data.length - 1))
  const Y = (v: number) => T + (H - T - B) * (1 - (v - mn) / (mx - mn))
  const pts = data.map((r, i) => ({ x: X(i), y: Y(valOf(r) as number), r }))
  const line = smoothPath(pts)
  const area = line + ' L ' + pts[pts.length - 1].x.toFixed(1) + ' ' + (H - B) + ' L ' + pts[0].x.toFixed(1) + ' ' + (H - B) + ' Z'

  // 星环透视地板（同心椭圆弧取代横向网格）
  let rings = ''
  for (let k = 0; k < 4; k++) {
    rings += '<ellipse cx="' + (W / 2) + '" cy="' + (H - 2) + '" rx="' + ((W - L - R) * 0.55 + k * 46) + '" ry="' + (20 + k * 15) + '" fill="none" stroke="rgba(184,134,59,' + (0.11 - k * 0.02) + ')" stroke-dasharray="2 6"/>'
  }
  // 星尘背景（确定性伪随机）
  let dust = ''
  for (let s = 0; s < 20; s++) {
    const dx = L + (s * 89.7) % (W - L - R), dy = T + (s * 53.3) % (H - T - B - 30)
    dust += '<circle cx="' + dx.toFixed(1) + '" cy="' + dy.toFixed(1) + '" r="' + (0.8 + (s % 3) * 0.35).toFixed(1) + '" fill="rgba(184,134,59,' + (0.06 + (s % 3) * 0.03) + ')"/>'
  }
  // y 轴微刻度
  const yLab = [mx, mn + (mx - mn) / 2, mn].map(v =>
    '<text x="' + (L - 7) + '" y="' + (Y(v) + 3).toFixed(1) + '" text-anchor="end" font-size="8.5" fill="rgba(42,38,32,.35)">' + v.toFixed(1) + '</text>'
  ).join('')
  // 数据星：历史星错峰闪烁，最新一颗呼吸光环
  const stars = data.map((r, i) => {
    const last = i === data.length - 1
    let s = '<path d="' + starPath(pts[i].x, pts[i].y, last ? 6.5 : 4.2) + '" fill="' + (last ? '#B8863B' : 'rgba(184,134,59,.78)') + '">'
    if (!last) s += '<animate attributeName="opacity" values=".35;1;.35" dur="2.6s" begin="' + (i * 0.28).toFixed(2) + 's" repeatCount="indefinite"/>'
    s += '</path>'
    if (last) {
      s += '<circle cx="' + pts[i].x.toFixed(1) + '" cy="' + pts[i].y.toFixed(1) + '" r="9" fill="none" stroke="rgba(217,162,74,.55)" stroke-width="1.2">'
        + '<animate attributeName="r" values="8;17" dur="2.2s" repeatCount="indefinite"/>'
        + '<animate attributeName="opacity" values=".7;0" dur="2.2s" repeatCount="indefinite"/></circle>'
        + '<text x="' + pts[i].x.toFixed(1) + '" y="' + (pts[i].y - 17).toFixed(1) + '" text-anchor="middle" font-size="12.5" font-weight="900" font-family="Noto Serif SC,serif" fill="#8A6428">' + (valOf(r) as number).toFixed(1) + '</text>'
    }
    s += '<circle data-gi="' + i + '" cx="' + pts[i].x.toFixed(1) + '" cy="' + pts[i].y.toFixed(1) + '" r="12" fill="transparent" style="cursor:pointer"/>'
    return s
  }).join('')
  // 峰谷注解
  const iMax = vals.indexOf(Math.max(...vals)), iMin = vals.indexOf(Math.min(...vals))
  let ann = ''
  if (data.length > 2 && iMax !== data.length - 1 && iMax !== iMin) {
    ann += '<text x="' + pts[iMax].x.toFixed(1) + '" y="' + (pts[iMax].y - 12).toFixed(1) + '" text-anchor="middle" font-size="8.5" font-weight="700" fill="#8A6428">峰 ' + vals[iMax].toFixed(1) + '</text>'
  }
  if (data.length > 2 && iMin !== data.length - 1 && iMin !== iMax) {
    ann += '<text x="' + pts[iMin].x.toFixed(1) + '" y="' + (pts[iMin].y + 18).toFixed(1) + '" text-anchor="middle" font-size="8.5" font-weight="700" fill="#8A6428">谷 ' + vals[iMin].toFixed(1) + '</text>'
  }
  // 日期刻度（约4个，去重）
  const tickN = Math.min(4, data.length)
  let ticks = '', seen: Record<string, number> = {}
  for (let t = 0; t < tickN; t++) {
    const i = Math.round(t * (data.length - 1) / Math.max(1, tickN - 1))
    const lb = data[i].recordDate.slice(5)
    if (seen[lb]) continue
    seen[lb] = 1
    ticks += '<text x="' + pts[i].x.toFixed(1) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="9" fill="rgba(42,38,32,.4)">' + lb + '</text>'
  }
  const svg =
    '<svg viewBox="0 0 ' + W + ' ' + H + '">'
    + '<defs>'
    + '<linearGradient id="p4lg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#E8C98F"/><stop offset=".55" stop-color="#D9A24A"/><stop offset="1" stop-color="#B8863B"/></linearGradient>'
    + '<linearGradient id="p4g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="rgba(217,162,74,.30)"/><stop offset="1" stop-color="rgba(217,162,74,0)"/></linearGradient>'
    + '<filter id="p4glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="4"/></filter>'
    + '</defs>'
    + dust + rings + yLab
    + '<path d="' + area + '" fill="url(#p4g)"/>'
    + '<path d="' + line + '" fill="none" stroke="#D9A24A" stroke-width="3.6" filter="url(#p4glow)" opacity=".45"/>'
    + '<path d="' + line + '" fill="none" stroke="url(#p4lg)" stroke-width="2.4" stroke-linecap="round"/>'
    // 流星脉冲：一段流光沿星河周期掠过
    + '<path d="' + line + '" fill="none" stroke="rgba(255,243,218,.95)" stroke-width="1.9" stroke-linecap="round" stroke-dasharray="26 2400" opacity=".9">'
    + '<animate attributeName="stroke-dashoffset" from="2426" to="0" dur="5.2s" repeatCount="indefinite"/></path>'
    + ticks + stars + ann
    + '<line class="p4-xh" y1="' + T + '" y2="' + (H - B) + '" stroke="rgba(184,134,59,.45)" stroke-dasharray="3 4" style="opacity:0"/>'
    + '<path class="p4-xd" d="" fill="#D9A24A" style="opacity:0"/>'
    + '</svg>'
  return { svg, pts }
})

// ---------- 悬停：十字准星 + 深壳气泡 ----------
const chartBoxRef = ref<HTMLElement | null>(null)
const tip = reactive({ show: false, left: 0, top: 0, title: '', value: '', unit: '', diff: '', cls: 'flat' })
const VBW = 640, VBH = 480

function onChartMove(e: MouseEvent) {
  const pts = chartData.value.pts
  const box = chartBoxRef.value
  if (!pts.length || !box) { onChartLeave(); return }
  const svg = box.querySelector('svg')
  if (!svg) return
  const xh = svg.querySelector('.p4-xh'), xd = svg.querySelector('.p4-xd')
  const rect = svg.getBoundingClientRect()
  const vx = (e.clientX - rect.left) / rect.width * VBW
  let best = pts[0], bd = Infinity
  pts.forEach(p => { const d = Math.abs(p.x - vx); if (d < bd) { bd = d; best = p } })
  const gi = chrono.value.findIndex(r => r.recordDate === best.r.recordDate)
  const prev = gi > 0 ? chrono.value[gi - 1] : null
  const val = valOf(best.r) as number
  let diffHtml = '→ 首颗快照星', cls = 'flat'
  if (prev) {
    const p = valOf(prev)
    if (p != null) {
      const diff = val - p
      cls = diff < -0.005 ? 'down' : diff > 0.005 ? 'up' : 'flat'
      const arrow = diff < 0 ? '↓' : diff > 0 ? '↑' : '→'
      diffHtml = arrow + ' ' + Math.abs(diff).toFixed(1) + ' 较前次'
    }
  }
  tip.title = best.r.recordDate + ' · 快照星'
  tip.value = val.toFixed(1)
  tip.unit = metricUnit.value
  tip.diff = diffHtml
  tip.cls = cls
  const px = best.x / VBW * rect.width, py = best.y / VBH * rect.height
  nextTick(() => {
    const tipEl = box.querySelector('.ct-tip') as HTMLElement | null
    const tw = tipEl?.offsetWidth || 120
    tip.left = (px + 16 + tw > rect.width ? px - 16 - tw : px + 16)
  })
  tip.top = Math.max(2, py - 24)
  tip.show = true
  xh?.setAttribute('x1', best.x.toFixed(1))
  xh?.setAttribute('x2', best.x.toFixed(1))
  if (xh) (xh as SVGElement).style.opacity = '1'
  xd?.setAttribute('d', starPath(best.x, best.y, 7))
  if (xd) (xd as SVGElement).style.opacity = '1'
}
function onChartLeave() {
  tip.show = false
  const svg = chartBoxRef.value?.querySelector('svg')
  svg?.querySelectorAll('.p4-xh, .p4-xd').forEach(el => { (el as SVGElement).style.opacity = '0' })
}

// ---------- 点击星：载入当日数据到表单 ----------
const fblockRef = ref<HTMLElement | null>(null)
function onChartClick(e: MouseEvent) {
  const el = (e.target as Element).closest('[data-gi]')
  if (!el) return
  const i = Number(el.getAttribute('data-gi'))
  const r = filteredRecords.value[i]
  if (!r) return
  form.recordDate = r.recordDate
  form.weight = r.weight
  form.height = r.height
  form.age = r.age
  popToast('已载入 ' + r.recordDate.slice(5) + ' 快照 · 修改后点击「写入快照」')
  gsap.fromTo(fblockRef.value, { scale: 0.985 }, { scale: 1, duration: 0.4, ease: 'back.out(2)', clearProps: 'transform' })
}

// ---------- 保存 / 删除 ----------
const formDateExists = computed(() =>
  !!form.recordDate && records.value.some(r => r.recordDate === form.recordDate)
)
async function saveSnapshot() {
  if (!form.recordDate) { popToast('请先选择日期', true); return }
  const w = form.weight, h = form.height
  if (w == null || !Number.isFinite(w) || w < 20 || w > 300) { popToast('请输入 20 ~ 300 的体重', true); return }
  if (h == null || !Number.isFinite(h) || h < 80 || h > 250) { popToast('请输入 80 ~ 250 的身高', true); return }
  const exists = formDateExists.value
  saving.value = true
  try {
    const payload: any = { recordDate: form.recordDate, weight: fix1(w), height: fix1(h) }
    if (form.age != null && Number.isFinite(form.age)) payload.age = fixInt(form.age)
    await api.metrics.save(payload)
    popToast(exists ? '同日快照已更新 · 趋势线上的星被重新校准' : '新快照已写入 · 趋势线新增一颗星')
    await loadData()
    gsap.fromTo(fblockRef.value, { scale: 1 }, { scale: 1.015, duration: 0.18, yoyo: true, repeat: 1, clearProps: 'transform' })
  } catch (e: any) {
    popToast(errMsg(e), true)
  } finally {
    saving.value = false
  }
}
function askDelete() {
  if (!form.recordDate) return
  if (!formDateExists.value) { popToast('该日期暂无快照', true); return }
  showDelete.value = true
}
async function confirmDelete() {
  if (!form.recordDate) return
  showDelete.value = false
  try {
    await api.metrics.deleteByDate(form.recordDate)
    popToast('已删除 ' + form.recordDate.slice(5) + ' 的快照 · 星已熄灭')
    await loadData()
  } catch (e: any) {
    popToast(errMsg(e), true)
  }
}

// ---------- 2x2 汇总格 ----------
function weeklyDelta(key: 'weight' | 'height'): { txt: string; cls: string } {
  const arr = chrono.value.filter(r => r[key] != null)
  if (arr.length < 2) return { txt: '记录积累中', cls: 'flat' }
  const b = arr[arr.length - 1]
  let ai = 0
  for (let i = arr.length - 2; i >= 0; i--) {
    const dd = (new Date(b.recordDate).getTime() - new Date(arr[i].recordDate).getTime()) / 86400000
    if (dd >= 7) { ai = i; break }
  }
  const a = arr[ai]
  const dd = Math.max(1, (new Date(b.recordDate).getTime() - new Date(a.recordDate).getTime()) / 86400000)
  const rate = ((b[key] as number) - (a[key] as number)) * 7 / dd
  if (Math.abs(rate) < 0.05) return { txt: '稳定 ±0.0', cls: 'flat' }
  return { txt: (rate < 0 ? '↓ ' : '↑ ') + Math.abs(rate).toFixed(1) + ' /周', cls: rate < 0 ? 'down' : 'up' }
}
const cells = computed(() => {
  const r = latest.value
  const wD = weeklyDelta('weight')
  const hD = weeklyDelta('height')
  const bmr = r ? calcBmr(r.weight, r.height, r.age) : null
  return [
    { lb: '最近体重', vl: r?.weight != null ? r.weight.toFixed(1) : '-', un: 'kg', sub: wD.txt, cls: wD.cls },
    { lb: '最近身高', vl: r?.height != null ? r.height.toFixed(1) : '-', un: 'cm', sub: hD.txt, cls: hD.cls },
    { lb: '最近年龄', vl: r?.age != null ? String(Math.round(r.age)) : '-', un: '岁', sub: '自我记录', cls: 'flat' },
    { lb: 'BMR 实时', vl: bmr != null ? bmr.toLocaleString() : '-', un: 'kcal', sub: 'Mifflin-St Jeor', cls: 'flat' }
  ]
})

// ---------- 彗尾预测图 ----------
const pred = computed<{ svg: string; msg: string; trend: string; trendLabel: string } | null>(() => {
  const arr = chrono.value.filter(r => r.weight != null)
  if (arr.length < 2) return null
  const days = predDays.value
  const hist = arr.slice(-5)
  const b = arr[arr.length - 1]
  const a = arr[Math.max(0, arr.length - 3)]
  const dd = (new Date(b.recordDate).getTime() - new Date(a.recordDate).getTime()) / 86400000
  if (!dd) return null
  const rate = ((b.weight as number) - (a.weight as number)) / dd
  const end = (b.weight as number) + rate * days
  const W = 300, H = 118, L = 38, R = 44, T = 14, B = 24
  const span = (new Date(b.recordDate).getTime() - new Date(hist[0].recordDate).getTime()) / 86400000
  const X = (d: number) => L + (W - L - R) * (d / (span + days))
  const vals = hist.map(r => r.weight as number).concat([end])
  const mn = Math.min(...vals) - 0.6, mx = Math.max(...vals) + 0.6
  const Y = (v: number) => T + (H - T - B) * (1 - (v - mn) / (mx - mn))
  const pastPts = hist.map(r => ({
    x: X((new Date(r.recordDate).getTime() - new Date(hist[0].recordDate).getTime()) / 86400000),
    y: Y(r.weight as number)
  }))
  const lastP = pastPts[pastPts.length - 1]
  const fut: Array<{ x: number; y: number }> = []
  for (let k = 1; k <= 4; k++) {
    const off = span + days * k / 4
    fut.push({ x: X(off), y: Y((b.weight as number) + rate * days * k / 4) })
  }
  const endX = X(span + days), endY = Y(end)
  // 置信带：彗尾渐宽渐淡
  const band = 'M' + lastP.x.toFixed(1) + ' ' + lastP.y.toFixed(1) + ' '
    + fut.map((f, k) => 'L' + f.x.toFixed(1) + ' ' + (f.y - (5 + k * 2.2)).toFixed(1)).join(' ') + ' '
    + fut.map((f, k) => 'L' + f.x.toFixed(1) + ' ' + (f.y + (5 + k * 2.2)).toFixed(1)).reverse().join(' ') + ' Z'
  const pastLine = smoothPath(pastPts)
  const futLine = 'M' + lastP.x.toFixed(1) + ' ' + lastP.y.toFixed(1) + ' ' + fut.map(f => 'L' + f.x.toFixed(1) + ' ' + f.y.toFixed(1)).join(' ')
  // 星尘
  let dust = ''
  for (let s = 0; s < 7; s++) {
    const dx = L + (s * 47.3) % (W - L - R), dy = T + (s * 29.1) % (H - T - B - 20)
    dust += '<circle cx="' + dx.toFixed(1) + '" cy="' + dy.toFixed(1) + '" r="0.7" fill="rgba(184,134,59,.10)"/>'
  }
  const stars = pastPts.map((p, i) => {
    const last = i === pastPts.length - 1
    return '<path d="' + starPath(p.x, p.y, last ? 4.6 : 3.1) + '" fill="' + (last ? '#B8863B' : 'rgba(184,134,59,.72)') + '"/>'
  }).join('')
  const svg = '<svg viewBox="0 0 ' + W + ' ' + H + '">'
    + '<defs>'
    + '<linearGradient id="p4pl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#B8863B" stop-opacity=".85"/><stop offset="1" stop-color="#B8863B" stop-opacity=".1"/></linearGradient>'
    + '<linearGradient id="p4pb" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="rgba(180,127,95,.16)"/><stop offset="1" stop-color="rgba(180,127,95,.04)"/></linearGradient>'
    + '<filter id="p4pglow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="2.2"/></filter>'
    + '</defs>'
    + dust
    + '<path d="' + band + '" fill="url(#p4pb)"/>'
    + '<path d="' + pastLine + '" fill="none" stroke="#D9A24A" stroke-width="2.6" filter="url(#p4pglow)" opacity=".4"/>'
    + '<path d="' + pastLine + '" fill="none" stroke="#B8863B" stroke-width="1.8" stroke-linecap="round"/>'
    + '<path d="' + futLine + '" fill="none" stroke="url(#p4pl)" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>'
    + stars
    // 彗星头：终点星 + 呼吸光环
    + '<circle cx="' + endX.toFixed(1) + '" cy="' + endY.toFixed(1) + '" r="5" fill="none" stroke="rgba(217,162,74,.5)" stroke-width="1">'
    + '<animate attributeName="r" values="5;11" dur="2.2s" repeatCount="indefinite"/>'
    + '<animate attributeName="opacity" values=".65;0" dur="2.2s" repeatCount="indefinite"/>'
    + '</circle>'
    + '<path d="' + starPath(endX, endY, 4.8) + '" fill="#D9A24A"/>'
    + '<text x="' + endX.toFixed(1) + '" y="' + (endY - 11).toFixed(1) + '" text-anchor="middle" font-size="9.5" font-weight="900" font-family="Noto Serif SC,serif" fill="#8A6428">' + end.toFixed(1) + '</text>'
    + '<text x="' + L + '" y="' + (H - 8) + '" font-size="8.5" fill="rgba(42,38,32,.4)">' + hist[0].recordDate.slice(5) + '</text>'
    + '<text x="' + endX.toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="8.5" fill="rgba(42,38,32,.4)">+' + days + '天</text>'
    + '</svg>'
  const trend = rate < -0.003 ? 'down' : rate > 0.003 ? 'up' : 'flat'
  const trendLabel = rate < -0.003 ? '↓ 下降趋势' : rate > 0.003 ? '↑ 上升趋势' : '→ 平稳'
  const msg = '按近期速率（' + (rate * 7).toFixed(2) + ' kg/周），预计 ' + days + ' 天后约 ' + end.toFixed(1) + ' kg（±' + (0.05 * Math.sqrt(days) * 2).toFixed(1) + '）。'
  return { svg, msg, trend, trendLabel }
})
function changePred(delta: number) {
  predDays.value = Math.max(7, Math.min(28, predDays.value + delta))
}

// ---------- 入场动效 ----------
const bandRef = ref<HTMLElement | null>(null)
const paperRef = ref<HTMLElement | null>(null)
function animateEntrance() {
  const band = bandRef.value
  const paper = paperRef.value
  if (band) {
    gsap.fromTo(band.querySelectorAll('.crumb-node'),
      { opacity: 0, y: 12, scale: 0.6 },
      { opacity: 1, y: 0, scale: 1, duration: 0.45, stagger: 0.15, ease: 'back.out(2)' })
    gsap.fromTo(band.querySelectorAll('.db-top-right, .db-core-wrap'),
      { opacity: 0, y: 14 },
      { opacity: 1, y: 0, duration: 0.6, delay: 0.15, ease: 'power3.out' })
    gsap.fromTo(band.querySelectorAll('.db-station-wrap'),
      { scale: 0, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.5, stagger: 0.08, delay: 0.35, ease: 'back.out(1.7)', clearProps: 'opacity,transform' })
  }
  if (paper) {
    gsap.fromTo(paper.querySelectorAll('[data-anim]'),
      { opacity: 0, y: 24 },
      { opacity: 1, y: 0, duration: 0.7, stagger: 0.1, delay: 0.35, ease: 'power3.out' })
  }
}

onMounted(async () => {
  animateEntrance()
  form.recordDate = todayStr()
  try { await userStore.init() } catch { /* ignore */ }
  loadData()
})

// 替亲属查看身份切换时重新加载
watch(() => userStore.activeUserId, () => { loadData() })
</script>

<style scoped>
.diet-page {
  position: relative;
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
}

/* ========== 深壳星轨带 ========== */
.db-band {
  position: relative;
  padding: 14px 24px 10px;
  border-radius: 20px;
  overflow: hidden;
  isolation: isolate;
  background:
    radial-gradient(circle at 12% 24%, rgba(232, 185, 115, 0.1) 0%, transparent 44%),
    radial-gradient(circle at 88% 88%, rgba(179, 107, 42, 0.08) 0%, transparent 46%),
    linear-gradient(180deg, #14110C 0%, #0E0C0A 100%);
  border: 1px solid rgba(232, 185, 115, 0.14);
  color: #F6EAD6;
}
.db-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(50px);
  pointer-events: none;
  z-index: 0;
}
.db-glow--1 {
  width: 200px; height: 200px;
  right: -60px; top: -110px;
  background: rgba(232, 185, 115, 0.12);
  animation: dbGlowFloat 9s ease-in-out infinite alternate;
}
.db-glow--2 {
  width: 170px; height: 170px;
  left: -70px; bottom: -100px;
  background: rgba(179, 107, 42, 0.1);
  animation: dbGlowFloat 11s ease-in-out infinite alternate-reverse;
}
@keyframes dbGlowFloat {
  from { transform: translate3d(0, 0, 0) scale(1); }
  to   { transform: translate3d(16px, 10px, 0) scale(1.12); }
}

/* ---- 顶行 ---- */
.db-top {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 10px;
}
.star-crumbs { display: flex; align-items: center; }
.crumb-wrap { display: flex; align-items: center; }
.crumb-link { width: 42px; height: 0; border-top: 1.5px dashed rgba(184, 134, 59, 0.45); margin: 0 5px; }
.crumb-node {
  display: inline-flex; align-items: center; gap: 7px;
  font-size: 11.5px; color: #8C7A5E;
  background: none; border: none; padding: 0;
  font-family: inherit; letter-spacing: 0.04em;
}
.crumb-node .nd {
  width: 22px; height: 22px; border-radius: 50%;
  border: 1px solid rgba(217, 162, 74, 0.4); color: #8C7A5E;
  display: flex; align-items: center; justify-content: center;
  background: rgba(24, 19, 12, 0.9); transition: 0.25s;
}
button.crumb-node { cursor: pointer; transition: color 0.25s ease; }
button.crumb-node:hover { color: #E8B973; }
.crumb-node.hot { color: #F6EAD6; font-weight: 700; }
.crumb-node.hot .nd {
  color: #E8B973; border-color: #E8B973;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  box-shadow: 0 0 14px rgba(217, 162, 74, 0.45);
}
.db-top-right { margin-left: auto; display: flex; align-items: center; gap: 12px; }
.db-date {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px; color: #B9A78A;
  border: 1px solid rgba(217, 162, 74, 0.3);
  background: rgba(217, 162, 74, 0.08);
  border-radius: 999px; padding: 3px 10px;
}
.db-date svg { color: #E8B973; flex-shrink: 0; }
.db-date b { color: #F0E2C4; }

/* ---- 星轨带 ---- */
.db-const {
  position: relative;
  z-index: 1;
  height: 104px;
  margin-top: 6px;
}
.db-line {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  overflow: visible;
}
.db-line path {
  fill: none;
  stroke: rgba(217, 162, 74, 0.35);
  stroke-width: 1.2;
  stroke-dasharray: 5 6;
  vector-effect: non-scaling-stroke;
}

/* ---- 核心恒星 ---- */
.db-core-wrap {
  position: absolute; left: 4px; top: 50%;
  margin-top: -23px; z-index: 2;
}
.db-core {
  display: flex; align-items: center; gap: 10px;
  animation: dbFloat 6.4s ease-in-out infinite alternate;
  animation-delay: -0.6s;
}
.db-core .star {
  width: 46px; height: 46px; border-radius: 50%;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(232, 185, 115, 0.55);
  display: flex; align-items: center; justify-content: center;
  color: #E8B973;
  box-shadow: 0 0 22px rgba(217, 162, 74, 0.32);
  animation: dbBreath 3.2s ease-in-out infinite;
}
@keyframes dbBreath {
  0%, 100% { box-shadow: 0 0 18px rgba(217, 162, 74, 0.3); }
  50% { box-shadow: 0 0 34px rgba(217, 162, 74, 0.52); }
}
.db-core .tt b {
  display: block; font-size: 12.5px; color: #F6EAD6;
  font-weight: 700; letter-spacing: 0.08em;
}
.db-core .tt span {
  display: block; margin-top: 2px; font-size: 9.5px;
  color: #9A8A6C; letter-spacing: 0.12em;
}

/* ---- 快照数据球 ---- */
.db-station-wrap {
  position: absolute; top: 50%;
  width: 44px; height: 44px;
  margin: -22px 0 0 -22px;
  z-index: 3;
}
.db-station-float {
  width: 100%; height: 100%;
  animation: dbFloat 4.6s ease-in-out infinite alternate;
}
@keyframes dbFloat {
  from { transform: translateY(4px); }
  to   { transform: translateY(-8px); }
}
.db-station {
  position: relative;
  width: 44px; height: 44px;
  border-radius: 50%;
  cursor: pointer;
  background: rgba(24, 19, 12, 0.95);
  border: 1px solid rgba(217, 162, 74, 0.45);
  color: #E8B973;
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.5, 0.5, 1), border-color 0.3s ease, box-shadow 0.3s ease;
  font-family: inherit;
}
.db-station .nm {
  position: absolute; top: -26px; left: 50%;
  transform: translateX(-50%);
  font-size: 10px; color: #F0E2C4;
  white-space: nowrap; letter-spacing: 0.06em;
  opacity: 0.72; transition: opacity 0.3s ease, color 0.3s ease;
}
.db-station .ds {
  position: absolute; top: calc(100% + 10px); left: 50%;
  transform: translateX(-50%) translateY(4px);
  white-space: nowrap;
  font-size: 9.5px; color: #F6EAD6;
  background: rgba(24, 19, 12, 0.95);
  border: 1px solid rgba(217, 162, 74, 0.4);
  padding: 2px 9px; border-radius: 999px;
  opacity: 0; transition: opacity 0.28s ease, transform 0.28s ease;
  pointer-events: none;
}
.db-station:hover {
  transform: scale(1.14);
  border-color: #E8B973;
  box-shadow: 0 0 0 5px rgba(217, 162, 74, 0.14), 0 10px 26px rgba(217, 162, 74, 0.32);
}
.db-station:hover .ds { opacity: 1; transform: translateX(-50%) translateY(0); }
.db-station:hover .nm { opacity: 1; color: #E8B973; }
.db-station.lit {
  border-color: #E8B973;
  box-shadow: 0 0 0 5px rgba(217, 162, 74, 0.16), 0 0 20px rgba(217, 162, 74, 0.4);
}

/* ========== 浅芯工作区 ========== */
.db-paper {
  position: relative;
  background:
    radial-gradient(circle at 18% 0%, rgba(184, 134, 59, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 86% 100%, rgba(201, 143, 62, 0.06) 0%, transparent 44%),
    linear-gradient(180deg, #F8F4EA 0%, #F2EBDC 100%);
  border: 1px solid rgba(232, 185, 115, 0.24);
  border-radius: 20px;
  padding: 18px 22px 22px;
  box-shadow: 0 30px 60px -34px rgba(90, 70, 40, 0.28);
}
.db-head {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.sec-t {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 700; color: #2A2620;
  letter-spacing: 0.02em;
}
.sec-t::before {
  content: ''; width: 3px; height: 14px; border-radius: 99px;
  background: linear-gradient(180deg, #E8B973, #B8863B);
}

/* ---- 气泡提示（无遮罩） ---- */
.kr-toast {
  margin-top: 12px;
  display: inline-flex; align-items: center;
  background: rgba(127, 174, 142, 0.12);
  border: 1px solid rgba(127, 174, 142, 0.35);
  border-radius: 999px; padding: 8px 16px;
  font-size: 12px; color: #2F7D5B; font-weight: 600;
  animation: toastPop 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.kr-toast.err {
  background: rgba(201, 110, 80, 0.12);
  border-color: rgba(201, 110, 80, 0.4);
  color: #C0522F;
}
@keyframes toastPop {
  from { transform: scale(0.85) translateY(-8px); opacity: 0; }
  to   { transform: scale(1) translateY(0); opacity: 1; }
}

.db-blocks {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 12px;
  margin-top: 14px;
}
.db-block {
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(184, 134, 59, 0.16);
  border-radius: 16px;
  padding: 16px 18px;
}
.bl-head {
  display: flex; align-items: baseline; gap: 8px;
}
.bl-head.wrap { flex-wrap: wrap; align-items: center; row-gap: 6px; }
.bl-head b { font-size: 13px; color: #2A2620; font-weight: 700; }
.bl-head span { font-size: 10px; color: rgba(42, 38, 32, 0.4); }

/* ---- 区间胶囊 ---- */
.rk-pills { display: flex; gap: 7px; }
.rk-pill {
  font-size: 10.5px; color: #6E6350;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(184, 134, 59, 0.25);
  padding: 3px 11px; border-radius: 999px;
  cursor: pointer; transition: 0.25s; font-family: inherit;
}
.rk-pill:hover { border-color: #B8863B; color: #B8863B; }
.rk-pill.on {
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; border-color: transparent; font-weight: 600;
}
.p4-hint { font-size: 10px; color: rgba(42, 38, 32, 0.45); }

/* ---- 图表 ---- */
.chart-box { margin-top: 12px; position: relative; }
.chart-box :deep(svg) { width: 100%; height: auto; display: block; }

/* 悬停深壳气泡 */
.ct-tip {
  position: absolute; z-index: 30; pointer-events: none;
  background: rgba(24, 19, 12, 0.95);
  border: 1px solid rgba(217, 162, 74, 0.5);
  border-radius: 12px; padding: 8px 12px;
  display: block; box-shadow: 0 14px 34px -12px rgba(0, 0, 0, 0.55);
  min-width: 104px;
}
.ct-tip b {
  display: block; font-size: 9.5px; color: #B9A78A; letter-spacing: 0.06em;
}
.ct-tip .v {
  display: block; font-family: 'Noto Serif SC', serif;
  font-size: 17px; font-weight: 900; color: #F6EAD6; margin-top: 2px;
}
.ct-tip .v small {
  font-size: 10px; color: rgba(246, 234, 214, 0.5); margin-left: 2px;
  font-weight: 600; font-family: 'Noto Sans SC', sans-serif;
}
.ct-tip .d {
  display: inline-block; margin-top: 5px;
  font-size: 9.5px; font-weight: 700; padding: 1px 8px; border-radius: 999px;
}
.ct-tip .d.down { background: rgba(127, 174, 142, 0.18); color: #9FBF8F; }
.ct-tip .d.up { background: rgba(201, 110, 80, 0.2); color: #F0B9AE; }
.ct-tip .d.flat { background: rgba(246, 234, 214, 0.12); color: #B9A78A; }

/* ---- 2x2 汇总格 ---- */
.mt-cells { display: grid; gap: 10px; margin-top: 12px; }
.mt-cells.inblock { grid-template-columns: repeat(2, 1fr); }
.mt-cell {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(184, 134, 59, 0.16);
  border-radius: 14px; padding: 12px 14px;
  position: relative; overflow: hidden;
}
.mt-cell::after {
  content: ''; position: absolute; right: -18px; top: -18px;
  width: 56px; height: 56px; border-radius: 50%;
  background: radial-gradient(circle, rgba(217, 162, 74, 0.16), transparent 70%);
}
.mt-cell .lb { font-size: 10px; color: rgba(42, 38, 32, 0.45); letter-spacing: 0.04em; }
.mt-cell .vl {
  margin-top: 3px; font-family: 'Noto Serif SC', serif;
  font-size: 21px; font-weight: 900; color: #2A2620;
}
.mt-cell .vl small { font-size: 11px; font-weight: 600; color: rgba(42, 38, 32, 0.5); margin-left: 3px; }
.mt-cell .sub { margin-top: 3px; font-size: 10px; font-weight: 700; }
.mt-cell .sub.down { color: #2F7D5B; }
.mt-cell .sub.up { color: #C0522F; }
.mt-cell .sub.flat { color: rgba(42, 38, 32, 0.45); font-weight: 500; }

/* ---- 补录表单 ---- */
.mt-form { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; margin-top: 12px; }
.mt-form .ff { display: flex; flex-direction: column; gap: 4px; }
.mt-form label { font-size: 10px; color: rgba(42, 38, 32, 0.45); letter-spacing: 0.04em; }
.mt-form input {
  padding: 8px 10px; border-radius: 9px;
  border: 1px solid rgba(184, 134, 59, 0.28);
  background: #fff; font-size: 12px; color: #2A2620;
  outline: none; font-family: inherit;
}
.mt-form input:focus { border-color: #B8863B; }
.mt-note { margin-top: 10px; font-size: 10.5px; color: rgba(42, 38, 32, 0.45); line-height: 1.7; }

.sec-label {
  margin-top: 16px; margin-bottom: 4px;
  font-size: 10.5px; color: #B8863B;
  letter-spacing: 0.08em; font-weight: 600;
  display: flex; align-items: center; gap: 10px;
}
.sec-label::before, .sec-label::after {
  content: ''; flex: 1; height: 0;
  border-top: 1px dashed rgba(184, 134, 59, 0.3);
}

/* ---- 预测 ---- */
.pred-wrap {
  margin-top: 4px;
  border: 1px dashed rgba(184, 134, 59, 0.3);
  border-radius: 12px; padding: 12px 14px;
  background: rgba(255, 255, 255, 0.5);
}
.pred-head {
  display: flex; align-items: center; gap: 8px;
  font-size: 11.5px; font-weight: 700; color: #2A2620;
}
.pred-chip {
  font-size: 9.5px; font-weight: 700; padding: 2px 9px;
  border-radius: 999px; margin-left: auto;
}
.pred-chip.down { background: rgba(127, 174, 142, 0.15); color: #2F7D5B; }
.pred-chip.up { background: rgba(201, 110, 80, 0.14); color: #C0522F; }
.pred-chip.flat { background: rgba(42, 38, 32, 0.08); color: #6E6350; }
.pred-msg { margin-top: 8px; font-size: 10.5px; color: rgba(42, 38, 32, 0.5); line-height: 1.6; }
.pred-ops { margin-top: 8px; display: flex; align-items: center; gap: 6px; }
.pred-ops button {
  font-size: 10px; padding: 3px 10px; border-radius: 8px;
  border: 1px solid rgba(184, 134, 59, 0.3);
  background: #fff; color: #6E6350;
  cursor: pointer; transition: 0.2s; font-family: inherit;
}
.pred-ops button:hover { border-color: #B8863B; color: #B8863B; }
.pred-ops span { font-size: 9.5px; color: rgba(42, 38, 32, 0.38); }

/* ---- 通用按钮 ---- */
.btn-gold {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 9px 20px; border-radius: 10px; border: none; cursor: pointer;
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; font-size: 12.5px; font-weight: 600; letter-spacing: 0.04em;
  transition: 0.25s; font-family: inherit;
}
.btn-gold:hover { opacity: 0.9; transform: translateY(-1px); }
.btn-gold:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
.btn-gold.full { margin-top: 12px; width: 100%; justify-content: center; }
.btn-ghost {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  border: 1px dashed rgba(201, 110, 80, 0.4); color: #C0522F;
  background: none; cursor: pointer; font-size: 11.5px; font-weight: 600;
  border-radius: 10px; padding: 8px 14px; transition: 0.25s; font-family: inherit;
  width: 100%; margin-top: 8px;
}
.btn-ghost:hover { background: rgba(201, 110, 80, 0.08); border-color: #C0522F; }
.btn-mini {
  padding: 5px 13px; border-radius: 8px;
  font-size: 11px; font-weight: 600; cursor: pointer;
  border: none; transition: 0.2s; font-family: inherit;
}
.btn-mini.red { background: rgba(201, 110, 80, 0.12); color: #C0522F; border: 1px solid rgba(201, 110, 80, 0.4); }
.btn-mini.plain { background: none; color: #6E6350; border: 1px solid rgba(184, 134, 59, 0.3); }
.btn-mini:hover { opacity: 0.85; }

.kin-empty {
  border: 1px dashed rgba(184, 134, 59, 0.3);
  border-radius: 12px; padding: 22px 14px;
  font-size: 11.5px; color: #8C7A5E; line-height: 1.7;
  text-align: center;
}

/* ---- 删除气泡（居中弹出 · 无遮罩） ---- */
.kr-bubble {
  position: fixed; z-index: 60;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 290px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(184, 134, 59, 0.45);
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 24px 54px -18px rgba(90, 70, 40, 0.5);
  animation: bubblePop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes bubblePop {
  from { transform: translate(-50%, -50%) scale(0.7); opacity: 0; }
  to   { transform: translate(-50%, -50%) scale(1); opacity: 1; }
}
.kr-bubble b { display: block; font-size: 13px; color: #2A2620; font-weight: 700; }
.kr-bubble > span {
  display: block; margin-top: 6px;
  font-size: 11.5px; color: rgba(42, 38, 32, 0.6); line-height: 1.7;
}
.kr-bubble-op { display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px; }

/* ---- 响应式 ---- */
@media (max-width: 1000px) {
  .db-blocks { grid-template-columns: 1fr; }
}
</style>
