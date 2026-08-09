<template>
  <div class="page-fade max-w-7xl mx-auto">
    <h2 class="text-2xl font-bold text-morandi-text mb-2">身体指标历史</h2>
    <p class="text-sm text-morandi-lightText mb-6">
      在个人中心保存资料或在下方手动录入都会在趋势线上新增一个点。
      <span v-if="userStore.actAsUserId != null" class="text-morandi-accent ml-1">当前查看的是亲属 #{{ userStore.actAsUserId }} 的数据。</span>
    </p>

    <div class="grid grid-cols-1 gap-6 mb-6">
      <!-- 日期范围 & 操作 -->
      <div class="glass rounded-2xl p-4 flex flex-wrap items-center gap-3">
      <label class="text-sm text-morandi-text">起始日期：</label>
      <div class="date-picker-wrap">
        <input v-model="startDate" type="date" class="date-picker-input" />
        <span v-if="startDate" class="date-picker-value">{{ startDate }}</span>
        <span v-else class="date-picker-placeholder">请选择起始日期</span>
      </div>
      <label class="text-sm text-morandi-text ml-2">结束日期：</label>
      <div class="date-picker-wrap">
        <input v-model="endDate" type="date" class="date-picker-input" />
        <span v-if="endDate" class="date-picker-value">{{ endDate }}</span>
        <span v-else class="date-picker-placeholder">请选择结束日期</span>
      </div>
      <button @click="loadData" class="px-4 py-2 rounded-lg bg-morandi-accent text-white text-sm">刷新</button>
      <button @click="showManualForm = !showManualForm" class="px-4 py-2 rounded-lg bg-morandi-accent/20 text-morandi-accent text-sm">
        {{ showManualForm ? '收起手动录入' : '录入历史指标' }}
      </button>
      <span v-if="hintMsg" class="text-xs text-morandi-accent ml-2">{{ hintMsg }}</span>
      </div>

        <!-- 手动录入 -->
        <section v-if="showManualForm" class="glass rounded-2xl p-5 mb-6">
      <h3 class="text-base font-semibold text-morandi-text mb-3">补充 / 更新一条身体指标记录</h3>
      <p class="text-xs text-morandi-lightText mb-4">同一天的记录会被更新。建议录入的日期早于今天，以避免覆盖在"个人中心"保存时生成的今日记录。</p>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-xs text-morandi-lightText mb-1">日期 *</label>
          <input v-model="manualForm.recordDate" type="date" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text" />
        </div>
        <div>
          <label class="block text-xs text-morandi-lightText mb-1">身高 (cm)</label>
          <input v-model.number="manualForm.height" type="number" step="0.1" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text" />
        </div>
        <div>
          <label class="block text-xs text-morandi-lightText mb-1">体重 (kg)</label>
          <input v-model.number="manualForm.weight" type="number" step="0.1" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text" />
        </div>
        <div>
          <label class="block text-xs text-morandi-lightText mb-1">年龄</label>
          <input v-model.number="manualForm.age" type="number" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text" />
        </div>
      </div>
      <div class="flex items-center gap-3 mt-5">
        <button @click="saveManual" :disabled="savingManual" class="px-5 py-2 rounded-lg bg-morandi-accent text-white text-sm disabled:opacity-60">
          {{ savingManual ? '保存中...' : '保存' }}
        </button>
        <button @click="resetManualForm" class="px-5 py-2 rounded-lg bg-morandi-soft text-morandi-text text-sm">重置</button>
      </div>
    </section>
    </div>

    <!-- 汇总卡片 -->
    <div v-if="records.length" class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
      <div class="glass rounded-2xl p-4">
        <div class="text-xs text-morandi-lightText">最近体重</div>
        <div class="text-2xl font-semibold text-morandi-text">{{ latestRecord.weight != null ? Number(latestRecord.weight).toFixed(1) : '-' }} <span class="text-sm">kg</span></div>
      </div>
      <div class="glass rounded-2xl p-4">
        <div class="text-xs text-morandi-lightText">最近身高</div>
        <div class="text-2xl font-semibold text-morandi-text">{{ latestRecord.height != null ? Number(latestRecord.height).toFixed(1) : '-' }} <span class="text-sm">cm</span></div>
      </div>
      <div class="glass rounded-2xl p-4">
        <div class="text-xs text-morandi-lightText">最近年龄</div>
        <div class="text-2xl font-semibold text-morandi-text">{{ latestRecord.age != null ? Math.round(latestRecord.age) : '-' }} <span class="text-sm">岁</span></div>
      </div>
      <div class="glass rounded-2xl p-4">
        <div class="text-xs text-morandi-lightText">最近 BMR (实时)</div>
        <div class="text-2xl font-semibold text-morandi-accent">{{ latestBmrText }}</div>
      </div>
    </div>

    <!-- 体重折线图 -->
    <section v-if="records.length > 1" class="glass rounded-2xl p-6 mb-6">
      <h3 class="text-lg font-semibold text-morandi-text mb-3">体重变化（kg）· 点击圆点修改当日数据</h3>
      <svg :viewBox="`0 0 ${svgW} 240`" class="w-full h-60">
        <polyline :points="weightLine" fill="none" :stroke="accentColor" stroke-width="2" />
        <g v-for="(p, i) in weightPoints" :key="i" class="cursor-pointer" @click="editPoint(p.record)">
          <circle :cx="p.x" :cy="p.y" r="6" :fill="accentColor" opacity="0.25" />
          <circle :cx="p.x" :cy="p.y" r="4" :fill="accentColor" />
          <text :x="p.x" y="225" text-anchor="middle" font-size="10" fill="#555">{{ p.label }}</text>
          <text :x="p.x" :y="p.y - 8" text-anchor="middle" font-size="10" :fill="accentColor">{{ p.value }}</text>
        </g>
      </svg>
    </section>

    <!-- 健康时序预测 -->
    <section v-if="prediction && prediction.status === 'ok'" class="glass rounded-2xl p-6 mb-6">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-lg font-semibold text-morandi-text">未来 {{ prediction.days }} 天体重预测</h3>
        <span class="text-xs px-3 py-1 rounded-full" :class="prediction.trend === 'down' ? 'bg-green-100 text-green-700' : prediction.trend === 'up' ? 'bg-amber-100 text-amber-700' : 'bg-morandi-soft text-morandi-text'">
          {{ prediction.trend === 'down' ? '下降趋势' : prediction.trend === 'up' ? '上升趋势' : '平稳' }}
        </span>
      </div>
      <p class="text-sm text-morandi-lightText mb-4">{{ prediction.message }}</p>
      <svg :viewBox="`0 0 ${svgW} 200`" class="w-full h-52">
        <!-- 置信区间带 -->
        <path :d="confidenceBandPath" fill="rgba(180,127,95,0.12)" stroke="none" />
        <!-- 预测线（虚线） -->
        <polyline :points="predictionLine" fill="none" :stroke="accentColor" stroke-width="2" stroke-dasharray="6 4" />
        <g v-for="(p, i) in predictionPoints" :key="i">
          <circle :cx="p.x" :cy="p.y" r="3" :fill="accentColor" />
          <text :x="p.x" y="190" text-anchor="middle" font-size="10" fill="#555">{{ p.label }}</text>
          <text :x="p.x" :y="p.y - 8" text-anchor="middle" font-size="10" :fill="accentColor">{{ p.value }}</text>
        </g>
      </svg>
      <div class="flex items-center gap-2 mt-2">
        <button @click="changePredictDays(-7)" class="px-2 py-1 rounded bg-morandi-soft text-morandi-text text-xs">-7天</button>
        <button @click="changePredictDays(7)" class="px-2 py-1 rounded bg-morandi-soft text-morandi-text text-xs">+7天</button>
        <span class="text-xs text-morandi-lightText ml-1">预测基于历史体重线性回归，置信区间随预测距离放宽，仅供参考。</span>
      </div>
    </section>
    <section v-else-if="records.length > 1" class="glass rounded-2xl p-4 mb-6">
      <p class="text-sm text-morandi-lightText">{{ prediction?.message || '暂无足够数据进行预测（至少 2 条体重记录）' }}</p>
    </section>

    <!-- 身高折线图 -->
    <section v-if="recordsWithHeight > 1" class="glass rounded-2xl p-6 mb-6">
      <h3 class="text-lg font-semibold text-morandi-text mb-3">身高变化（cm）· 点击圆点修改当日数据</h3>
      <svg :viewBox="`0 0 ${svgW} 240`" class="w-full h-60">
        <polyline :points="heightLine" fill="none" stroke="#43b086" stroke-width="2" />
        <g v-for="(p, i) in heightPoints" :key="i" class="cursor-pointer" @click="editPoint(p.record)">
          <circle :cx="p.x" :cy="p.y" r="6" fill="#43b086" opacity="0.25" />
          <circle :cx="p.x" :cy="p.y" r="4" fill="#43b086" />
          <text :x="p.x" y="225" text-anchor="middle" font-size="10" fill="#555">{{ p.label }}</text>
          <text :x="p.x" :y="p.y - 8" text-anchor="middle" font-size="10" fill="#43b086">{{ p.value }}</text>
        </g>
      </svg>
    </section>

    <!-- 表格 -->
    <section class="glass rounded-2xl p-4 overflow-auto">
      <table class="min-w-full text-sm text-left text-morandi-text">
        <thead class="text-xs uppercase bg-morandi-soft/50">
          <tr>
            <th class="px-4 py-2">日期</th>
            <th class="px-4 py-2">身高 (cm)</th>
            <th class="px-4 py-2">体重 (kg)</th>
            <th class="px-4 py-2">年龄</th>
            <th class="px-4 py-2">BMR (kcal, 实时)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in records" :key="r.historyId" class="border-t border-morandi-soft/50">
            <td class="px-4 py-2">{{ r.recordDate }}</td>
            <td class="px-4 py-2">{{ r.height != null ? Number(r.height).toFixed(1) : '-' }}</td>
            <td class="px-4 py-2">{{ r.weight != null ? Number(r.weight).toFixed(1) : '-' }}</td>
            <td class="px-4 py-2">{{ r.age != null ? Math.round(r.age) : '-' }}</td>
            <td class="px-4 py-2">{{ calcBmr(r) }}</td>
          </tr>
          <tr v-if="!records.length">
            <td colspan="5" class="px-4 py-6 text-center text-morandi-sub">
              暂无历史数据。去"个人中心"保存一次资料，或点击上方"录入历史指标"即可建立第一个点。
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- 编辑弹窗 -->
    <div v-if="editing" class="fixed inset-0 z-40 bg-black/40 flex items-center justify-center p-4" @click.self="editing = null">
      <div class="glass rounded-2xl w-full max-w-md p-6 shadow-xl">
        <h3 class="text-lg font-semibold text-morandi-text mb-1">修改当日指标</h3>
        <p class="text-xs text-morandi-lightText mb-4">可查看并修改该日期的历史数据。</p>
        <div class="grid grid-cols-1 gap-4">
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">日期 *</label>
            <input v-model="editForm.recordDate" type="date" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">身高 (cm)</label>
              <input v-model.number="editForm.height" type="number" step="0.1" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text" />
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">体重 (kg)</label>
              <input v-model.number="editForm.weight" type="number" step="0.1" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text" />
            </div>
          </div>
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">年龄（整数）</label>
            <input v-model.number="editForm.age" type="number" step="1" min="0" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text" />
          </div>
          <div class="bg-morandi-soft/40 rounded-lg p-3 text-sm">
            <div class="flex justify-between text-morandi-text mb-1"><span>BMR（实时 Mifflin-St Jeor）</span><span class="font-semibold text-morandi-accent">{{ calcBmr(editForm) }} kcal</span></div>
            <div class="text-xs text-morandi-lightText">公式：男 = 10×体重 + 6.25×身高 − 5×年龄 + 5；女 = 10×体重 + 6.25×身高 − 5×年龄 − 161</div>
          </div>
        </div>
        <div class="flex items-center justify-between mt-5">
          <button @click="deleteRecord" :disabled="savingEdit" class="px-4 py-2 rounded-lg bg-red-100 text-red-700 text-sm disabled:opacity-60">删除该条记录</button>
          <div class="flex gap-2">
            <button @click="editing = null" class="px-5 py-2 rounded-lg bg-morandi-soft text-morandi-text text-sm">取消</button>
            <button @click="saveEdit" :disabled="savingEdit" class="px-5 py-2 rounded-lg bg-morandi-accent text-white text-sm disabled:opacity-60">
              {{ savingEdit ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'

const userStore = useUserStore()
const accentColor = '#b47f5f'

function fix1(v: any): number {
  const n = Number(v)
  return Number.isFinite(n) ? Math.round(n * 10) / 10 : 0
}
function fixInt(v: any): number {
  const n = Number(v)
  return Number.isFinite(n) ? Math.round(n) : 0
}

const startDate = ref('')
const endDate = ref('')
const records = ref<any[]>([])
const hintMsg = ref('')
const prediction = ref<any>(null)
const predictDays = ref(7)

const showManualForm = ref(false)
const savingManual = ref(false)
const manualForm = reactive({
  recordDate: '',
  height: null as number | null,
  weight: null as number | null,
  age: null as number | null
})
function resetManualForm() {
  manualForm.recordDate = ''
  manualForm.height = null
  manualForm.weight = null
  manualForm.age = null
}

// 编辑
const editing = ref<any>(null)
const savingEdit = ref(false)
const editForm = reactive({
  historyId: null as number | null,
  recordDate: '',
  height: null as number | null,
  weight: null as number | null,
  age: null as number | null
})

function editPoint(record: any) {
  if (!record) return
  editing.value = record
  editForm.historyId = record.historyId
  editForm.recordDate = record.recordDate
  editForm.height = record.height
  editForm.weight = record.weight
  editForm.age = record.age
}

// BMR 实时计算 (Mifflin-St Jeor)
function calcBmr(r: any): string {
  if (!r) return '-'
  const h = Number(r.height)
  const w = Number(r.weight)
  const a = Number(r.age)
  if (!Number.isFinite(h) || !Number.isFinite(w) || !Number.isFinite(a)) return '-'
  const gender = (userStore.user?.gender || userStore.user?.sex || '男').toString()
  const isFemale = gender.includes('女') || gender.toLowerCase() === 'f' || gender.toLowerCase() === 'female'
  const raw = 10 * w + 6.25 * h - 5 * a + (isFemale ? -161 : 5)
  return Math.round(raw).toString()
}

const latestRecord = computed(() => records.value[0] || {})
const recordsWithHeight = computed(() => records.value.filter((r) => typeof r.height === 'number').length)
const latestBmrText = computed(() => calcBmr(latestRecord.value))

const svgW = 720

function buildPoints(key: 'weight' | 'height') {
  const chrono = [...records.value].reverse()
  const values = chrono
    .map((r) => ({ record: r, date: r.recordDate, value: Number(r[key]) }))
    .filter((x) => Number.isFinite(x.value))
  if (values.length === 0) return { points: [], line: '' }
  const min = Math.min(...values.map((x) => x.value))
  const max = Math.max(...values.map((x) => x.value))
  const span = max - min || 1
  const points = values.map((v, i) => ({
    x: values.length === 1 ? svgW / 2 : (svgW - 40) * (i / (values.length - 1)) + 20,
    y: 200 - ((v.value - min) / span) * 170,
    label: String(v.date).slice(5),
    value: Number(v.value).toFixed(1),
    record: v.record
  }))
  const line = points.map((p) => `${p.x},${p.y}`).join(' ')
  return { points, line }
}

const weightPoints = computed(() => buildPoints('weight').points)
const weightLine = computed(() => buildPoints('weight').line)
const heightPoints = computed(() => buildPoints('height').points)
const heightLine = computed(() => buildPoints('height').line)

// ============ 健康时序预测展示 ============
const predictionPoints = computed<{ x: number; y: number; label: string; value: string }[]>(() => {
  const pts = prediction.value?.points || []
  if (!pts.length) return []
  const values = pts.map((p: any) => Number(p.predictedWeight)).filter(Number.isFinite)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1
  return pts.map((p: any, i: number) => ({
    x: pts.length === 1 ? svgW / 2 : (svgW - 40) * (i / (pts.length - 1)) + 20,
    y: 160 - ((Number(p.predictedWeight) - min) / span) * 120,
    label: String(p.date).slice(5),
    value: Number(p.predictedWeight).toFixed(1)
  }))
})
const predictionLine = computed(() => predictionPoints.value.map((p) => `${p.x},${p.y}`).join(' '))
const confidenceBandPath = computed(() => {
  const pts = prediction.value?.points || []
  const lps = predictionPoints.value
  if (!pts.length || lps.length < 2) return ''
  const values = pts.map((p: any) => Number(p.predictedWeight)).filter(Number.isFinite)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1
  const upper = pts.map((p: any, i: number) => {
    const x = lps[i].x
    const y = 160 - ((Number(p.upper) - min) / span) * 120
    return `${x},${Math.min(199, y)}`
  })
  const lower = [...pts].reverse().map((p: any, i: number) => {
    const idx = pts.length - 1 - i
    const x = lps[idx].x
    const y = 160 - ((Number(p.lower) - min) / span) * 120
    return `${x},${Math.max(1, y)}`
  })
  return `M ${upper.join(' L ')} L ${lower.join(' L ')} Z`
})

async function loadPredict() {
  try {
    const uid = userStore.activeUserId || userStore.user?.user_id
    if (!uid) { prediction.value = null; return }
    const resp: any = await api.metrics.predict(uid, predictDays.value)
    prediction.value = resp?.data ?? resp ?? null
  } catch (e: any) {
    console.warn('加载预测失败', e)
    prediction.value = null
  }
}

function changePredictDays(delta: number) {
  const next = Math.min(30, Math.max(7, predictDays.value + delta))
  if (next === predictDays.value) return
  predictDays.value = next
  loadPredict()
}

async function loadData() {
  try {
    const uid = userStore.activeUserId || userStore.user?.user_id
    if (!uid) { records.value = []; return }
    let list: any
    if (startDate.value && endDate.value) {
      list = await api.metrics.range(uid, startDate.value, endDate.value)
    } else {
      list = await api.metrics.history(uid)
    }
    records.value = (Array.isArray(list) ? list : []).map((r: any) => ({
      historyId: r.historyId ?? r.history_id,
      recordDate: r.recordDate ?? r.record_date,
      height: fix1(r.height),
      weight: fix1(r.weight),
      age: fixInt(r.age),
      crowdType: r.crowdType ?? r.crowd_type
    }))
    loadPredict()
  } catch (e: any) {
    console.warn('加载指标失败', e)
    records.value = []
  }
}

async function saveManual() {
  if (!manualForm.recordDate) {
    hintMsg.value = '请填写日期'
    return
  }
  savingManual.value = true
  hintMsg.value = ''
  try {
    const payload: any = { recordDate: manualForm.recordDate }
    if (manualForm.height != null && Number.isFinite(manualForm.height)) payload.height = manualForm.height
    if (manualForm.weight != null && Number.isFinite(manualForm.weight)) payload.weight = manualForm.weight
    if (manualForm.age != null && Number.isFinite(manualForm.age)) payload.age = manualForm.age
    await api.metrics.save(payload)
    hintMsg.value = '已保存历史指标'
    resetManualForm()
    await loadData()
  } catch (e: any) {
    hintMsg.value = e?.response?.data?.message || e?.message || '保存失败'
  } finally {
    savingManual.value = false
  }
}

async function saveEdit() {
  if (!editForm.recordDate) return
  savingEdit.value = true
  hintMsg.value = ''
  try {
    const payload: any = { recordDate: editForm.recordDate }
    if (editForm.height != null && Number.isFinite(editForm.height)) payload.height = fix1(editForm.height)
    if (editForm.weight != null && Number.isFinite(editForm.weight)) payload.weight = fix1(editForm.weight)
    if (editForm.age != null && Number.isFinite(editForm.age)) payload.age = fixInt(editForm.age)
    await api.metrics.save(payload)
    hintMsg.value = '已更新'
    editing.value = null
    await loadData()
  } catch (e: any) {
    hintMsg.value = e?.response?.data?.message || e?.message || '保存失败'
  } finally {
    savingEdit.value = false
  }
}

async function deleteRecord() {
  if (!editForm.recordDate) return
  if (!confirm(`确认删除 ${editForm.recordDate} 的指标记录吗？`)) return
  savingEdit.value = true
  try {
    await api.metrics.deleteByDate(editForm.recordDate)
    hintMsg.value = '已删除'
    editing.value = null
    await loadData()
  } catch (e: any) {
    hintMsg.value = e?.response?.data?.message || e?.message || '删除失败'
  } finally {
    savingEdit.value = false
  }
}

onMounted(async () => {
  try { await userStore.init() } catch { /* ignore */ }
  loadData()
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.08);
}
.page-fade {
  animation: fadeIn 0.3s ease forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ============ 日期选择器：透明原生输入 + 自定义显示文字 ============ */
.date-picker-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  height: 36px;
  min-width: 180px;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
}
.date-picker-wrap:hover {
  border-color: #10b981;
}

/* 原生日期输入框：透明覆盖层，完全可点击，文字颜色与背景相同 */
.date-picker-input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: none;
  background: transparent;
  color: transparent;
  font-size: 0.875rem;
  cursor: pointer;
  outline: none;
  z-index: 10;
  padding: 0 0.75rem;
}

/* 原生日期选择器内部元素隐藏（浏览器差异处理） */
.date-picker-input::-webkit-datetime-edit,
.date-picker-input::-webkit-datetime-edit-text,
.date-picker-input::-webkit-datetime-edit-month-field,
.date-picker-input::-webkit-datetime-edit-day-field,
.date-picker-input::-webkit-datetime-edit-year-field {
  color: transparent !important;
  background: transparent !important;
}
.date-picker-input::-webkit-calendar-picker-indicator {
  cursor: pointer;
  /* 将日历图标向右推，并让其对点击有效 */
  margin-left: auto;
  opacity: 0;
  width: 100%;
  height: 100%;
  position: absolute;
  right: 0;
  top: 0;
}

/* 自定义显示层：我们自己的文字（在原生输入下方） */
.date-picker-value {
  position: relative;
  z-index: 1;
  padding: 0 0.75rem;
  font-size: 0.875rem;
  color: #374151;
  pointer-events: none;
  width: 100%;
  white-space: nowrap;
}
.date-picker-placeholder {
  position: relative;
  z-index: 1;
  padding: 0 0.75rem;
  font-size: 0.875rem;
  color: #9ca3af;
  pointer-events: none;
  width: 100%;
  white-space: nowrap;
}
</style>
