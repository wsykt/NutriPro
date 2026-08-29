<template>
  <div class="diet-page">
    <!-- ===== 深壳星轨带（健康星档 · 类型星球 = 筛选器） ===== -->
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
            <span class="crumb-node hot"><span class="nd"><BookOpen :size="13" /></span>健康记录</span>
          </span>
        </div>
        <div class="db-top-right">
          <span class="db-date"><NotebookPen :size="12" />记录 <b>{{ records.length }}</b> 条</span>
        </div>
      </div>

      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 104" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 52 C 300 8, 440 8, 560 52 S 830 96, 960 52 S 1130 8, 1200 52" />
        </svg>

        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><BookOpen :size="19" /></span>
            <span class="tt"><b>健康星档</b><span>HEALTH ARCHIVE</span></span>
          </div>
        </div>

        <!-- 类型星球：血压 / 血糖 / 心率 / 体重，点击即筛选 -->
        <div
          v-for="(s, i) in stations" :key="s.t"
          class="db-station-wrap"
          :style="{ left: stationLeft(i, stations.length) + '%' }"
        >
          <div class="db-station-float" :style="floatStyle(i)">
            <button
              class="db-station"
              :class="{ lit: filter === s.t }"
              :aria-label="s.nm"
              @click="toggleFilter(s.t)"
            >
              <component :is="s.icon" :size="15" />
              <span class="nm">{{ s.nm }}</span>
              <span class="ds">{{ s.ds }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区（星档管理） ===== -->
    <div class="db-paper" ref="paperRef">
      <div class="db-head" data-anim>
        <div class="sec-t">星档管理 · 记录由你手动保存，不自动生成</div>
      </div>

      <div v-if="toastMsg" class="kr-toast" :class="{ err: toastErr }" data-anim>{{ toastMsg }}</div>

      <div class="db-blocks">
        <!-- 左：时间星层 -->
        <div class="db-block main" data-anim>
          <div class="bl-head"><b>时间星层</b><span>按日期倒序 · 点击星球筛选类型</span></div>
          <div class="chips">
            <button
              v-for="t in filterOptions" :key="t"
              class="chip" :class="{ on: filter === t }"
              @click="filter = t"
            >{{ t }}</button>
          </div>
          <div ref="timelineRef">
            <div v-if="!filteredRecords.length" class="kin-empty">
              该类型暂无记录 · 在右侧手动保存一条吧
            </div>
            <div v-else class="tl">
              <template v-for="(group, gi) in groupedRecords" :key="group.d">
                <div class="tl-date">{{ group.d.slice(5) }} · {{ relLabel(group.d) }}</div>
                <div v-for="r in group.items" :key="r.id" class="tl-item">
                  <span class="tl-orb"><component :is="typeMeta(r.t).icon" :size="13" /></span>
                  <div class="tx">
                    <b>{{ r.t }}</b>
                    <span>{{ r.note ? '备注：' + r.note : '手动保存入档' }}</span>
                  </div>
                  <span class="tl-val">{{ r.v }}<small v-if="typeMeta(r.t).unit"> {{ typeMeta(r.t).unit }}</small></span>
                  <span class="st-chip" :class="statusOf(r.t, r.v).cls">{{ statusOf(r.t, r.v).label }}</span>
                </div>
              </template>
            </div>
          </div>
        </div>

        <!-- 右：手动保存 + 健康概览 -->
        <div class="db-block side" data-anim>
          <div class="bl-head"><b>手动保存一条记录</b><span>保存后立即入档</span></div>
          <div class="chips">
            <button
              v-for="tp in TYPES" :key="tp.t"
              class="chip" :class="{ on: saveType === tp.t }"
              @click="saveType = tp.t"
            >
              <component :is="saveType === tp.t ? Check : Plus" :size="11" />{{ tp.t }}
            </button>
          </div>
          <div class="mt-form">
            <div class="ff">
              <label>数值 *</label>
              <input v-model="saveVal" type="text" :placeholder="typeMeta(saveType).ph" @keyup.enter="saveRecord" />
              <span class="unit-hint">单位：<b>{{ typeMeta(saveType).unit }}</b></span>
            </div>
            <div class="ff"><label>日期</label><input v-model="saveDate" type="date" /></div>
            <div class="ff span2"><label>备注</label><input v-model="saveNote" type="text" placeholder="如 晨起测量 / 空腹" /></div>
          </div>
          <button class="btn-gold full" @click="saveRecord">
            <Save :size="13" />保存入档
          </button>

          <div class="sec-label">健康概览</div>
          <div class="ov-cells">
            <div class="ov-cell"><div class="lb">身高</div><div class="vl">{{ ovHeight }}<small>cm</small></div></div>
            <div class="ov-cell"><div class="lb">体重</div><div class="vl">{{ ovWeight }}<small>kg</small></div></div>
            <div class="ov-cell"><div class="lb">BMI</div><div class="vl">{{ ovBmi.v }}<small>{{ ovBmi.cls }}</small></div></div>
            <div class="ov-cell"><div class="lb">档案总数</div><div class="vl">{{ records.length }}<small>条</small></div></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import {
  Home, UsersRound, BookOpen, NotebookPen, Save, Check, Plus,
  HeartPulse, Droplet, Activity, Weight
} from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const router = useRouter()

interface HealthRecord {
  id: number
  d: string
  t: string
  v: string
  note: string
}

const TYPES = [
  { t: '血压', icon: HeartPulse, unit: 'mmHg', ph: '如 118/76' },
  { t: '血糖', icon: Droplet, unit: 'mmol/L', ph: '如 5.4' },
  { t: '心率', icon: Activity, unit: 'bpm', ph: '如 72' },
  { t: '体重', icon: Weight, unit: 'kg', ph: '如 65.0' }
]
const filterOptions = ['全部', ...TYPES.map(t => t.t)]

const records = ref<HealthRecord[]>([])
const filter = ref('全部')
const saveType = ref('血压')
const saveVal = ref('')
const saveDate = ref('')
const saveNote = ref('')
const toastMsg = ref('')
const toastErr = ref(false)

function typeMeta(t: string) {
  return TYPES.find(x => x.t === t) || { t, icon: BookOpen, unit: '', ph: '' }
}

// ---------- 工具 ----------
function popToast(msg: string, isErr = false) {
  toastMsg.value = msg
  toastErr.value = isErr
  setTimeout(() => { if (toastMsg.value === msg) toastMsg.value = '' }, 3200)
}
function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'user' } }) }
function todayStr(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
function relLabel(d: string): string {
  const diff = Math.round((new Date(todayStr()).getTime() - new Date(d).getTime()) / 86400000)
  return diff <= 0 ? '今天' : diff === 1 ? '昨天' : diff + '天前'
}

// ---------- 状态章（自动判定） ----------
function statusOf(t: string, v: string): { cls: string; label: string } {
  if (t === '血压') {
    const m = v.match(/(\d+)\s*\/\s*(\d+)/)
    if (m) {
      const s = Number(m[1]), d2 = Number(m[2])
      if (s >= 130 || d2 >= 85) return { cls: 'warn', label: '偏高' }
      if (s > 0 && s < 90) return { cls: 'info', label: '参考' }
      return { cls: 'ok', label: '正常' }
    }
    return { cls: 'info', label: '参考' }
  }
  const n = parseFloat(v)
  if (t === '血糖') {
    if (Number.isFinite(n) && n > 6.1) return { cls: 'warn', label: '偏高' }
    if (Number.isFinite(n) && n < 3.9) return { cls: 'info', label: '参考' }
    return { cls: 'ok', label: '正常' }
  }
  if (t === '心率') {
    if (Number.isFinite(n) && n > 100) return { cls: 'warn', label: '偏高' }
    if (Number.isFinite(n) && n > 0 && n < 60) return { cls: 'info', label: '参考' }
    return { cls: 'ok', label: '正常' }
  }
  return { cls: 'ok', label: '正常' }
}

// ---------- 本地持久化（按查看的用户隔离） ----------
const uid = computed(() => String(userStore.activeUserId ?? userStore.user?.user_id ?? 'guest'))
const STORAGE_PREFIX = 'p5-health-records::'

function loadLocal() {
  try {
    const raw = localStorage.getItem(STORAGE_PREFIX + uid.value)
    records.value = raw ? JSON.parse(raw) : []
  } catch {
    records.value = []
  }
}
function persist() {
  try {
    localStorage.setItem(STORAGE_PREFIX + uid.value, JSON.stringify(records.value))
  } catch { /* ignore */ }
}

// ---------- 星轨带类型星球 ----------
const stations = computed(() => TYPES.map(tp => ({
  t: tp.t,
  icon: tp.icon,
  nm: tp.t + ' · ' + records.value.filter(r => r.t === tp.t).length + '条',
  ds: '点击只看' + tp.t + '记录'
})))
function toggleFilter(t: string) {
  filter.value = filter.value === t ? '全部' : t
}
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

// ---------- 时间星层 ----------
const filteredRecords = computed<HealthRecord[]>(() => {
  const list = filter.value === '全部' ? records.value : records.value.filter(r => r.t === filter.value)
  return [...list].sort((a, b) => (a.d === b.d ? b.id - a.id : a.d < b.d ? 1 : -1))
})
const groupedRecords = computed<Array<{ d: string; items: HealthRecord[] }>>(() => {
  const groups: Array<{ d: string; items: HealthRecord[] }> = []
  filteredRecords.value.forEach(r => {
    const g = groups.find(x => x.d === r.d)
    if (g) g.items.push(r)
    else groups.push({ d: r.d, items: [r] })
  })
  return groups
})

// ---------- 保存入档 ----------
const timelineRef = ref<HTMLElement | null>(null)
function saveRecord() {
  const v = saveVal.value.trim()
  if (!v) { popToast('请输入记录数值', true); return }
  const d = saveDate.value || todayStr()
  const note = saveNote.value.trim()
  records.value.unshift({ id: Date.now(), d, t: saveType.value, v, note })
  records.value.sort((a, b) => (a.d === b.d ? b.id - a.id : a.d < b.d ? 1 : -1))
  persist()
  saveVal.value = ''
  saveNote.value = ''
  popToast('已保存 · ' + saveType.value + ' ' + v + ' 入档')
  nextTick(() => {
    gsap.fromTo(timelineRef.value?.querySelectorAll('.tl-item') || [],
      { opacity: 0, y: 10 },
      { opacity: 1, y: 0, duration: 0.4, stagger: 0.04, ease: 'power2.out', clearProps: 'opacity,transform' })
  })
}

// ---------- 健康概览 ----------
const ovHeight = computed(() => {
  const h = Number(userStore.user?.height)
  return Number.isFinite(h) && h > 0 ? String(Math.round(h * 10) / 10) : '—'
})
const ovWeight = computed(() => {
  const wr = [...records.value].filter(r => r.t === '体重').sort((a, b) => (a.d < b.d ? 1 : -1))[0]
  if (wr) {
    const n = parseFloat(wr.v)
    if (Number.isFinite(n)) return String(Math.round(n * 10) / 10)
  }
  const w = Number(userStore.user?.weight)
  return Number.isFinite(w) && w > 0 ? String(Math.round(w * 10) / 10) : '—'
})
const ovBmi = computed<{ v: string; cls: string }>(() => {
  const h = Number(userStore.user?.height), w = parseFloat(ovWeight.value)
  if (!Number.isFinite(h) || h <= 0 || !Number.isFinite(w) || w <= 0) return { v: '—', cls: '' }
  const bmi = w / Math.pow(h / 100, 2)
  const cls = bmi < 18.5 ? '偏瘦' : bmi < 24 ? '正常范围' : bmi < 28 ? '偏胖' : '肥胖'
  return { v: bmi.toFixed(1), cls }
})

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
  saveDate.value = todayStr()
  try { await userStore.init() } catch { /* ignore */ }
  loadLocal()
})

// 替亲属查看身份切换时切换档案
watch(uid, () => { loadLocal() })
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

/* ---- 类型星球 ---- */
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
.bl-head b { font-size: 13px; color: #2A2620; font-weight: 700; }
.bl-head span { font-size: 10px; color: rgba(42, 38, 32, 0.4); }

/* ---- 筛选 / 类型 chips ---- */
.chips { display: flex; gap: 7px; flex-wrap: wrap; margin-top: 10px; }
.chip {
  font-size: 11px; color: #6E6350;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(184, 134, 59, 0.25);
  padding: 4px 13px; border-radius: 999px;
  cursor: pointer; transition: 0.25s;
  display: inline-flex; align-items: center; gap: 5px;
  font-family: inherit;
}
.chip:hover { border-color: #B8863B; color: #B8863B; }
.chip.on {
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; border-color: transparent; font-weight: 600;
}

/* ---- 时间星层 ---- */
.tl { margin-top: 12px; position: relative; padding-left: 14px; }
.tl::before {
  content: ''; position: absolute; left: 3px; top: 6px; bottom: 6px;
  width: 0; border-left: 1.5px dashed rgba(184, 134, 59, 0.35);
}
.tl-date {
  position: relative; font-size: 10px; font-weight: 700; color: #B8863B;
  letter-spacing: 0.08em; margin: 10px 0 6px;
}
.tl-date::before {
  content: ''; position: absolute; left: -14px; top: 3px;
  width: 7px; height: 7px; border-radius: 50%;
  background: radial-gradient(circle, #F1CF92, #D9A24A);
  box-shadow: 0 0 8px rgba(232, 185, 115, 0.7);
}
.tl-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 11px; border-radius: 11px;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(184, 134, 59, 0.14);
  transition: 0.25s;
  animation: tagPop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tl-item + .tl-item { margin-top: 6px; }
.tl-item:hover { border-color: rgba(184, 134, 59, 0.35); transform: translateX(2px); }
@keyframes tagPop {
  from { transform: scale(0.92) translateY(6px); opacity: 0; }
  to   { transform: scale(1) translateY(0); opacity: 1; }
}
.tl-orb {
  width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(217, 162, 74, 0.4);
  color: #E8B973;
  display: flex; align-items: center; justify-content: center;
}
.tl-item .tx { min-width: 0; }
.tl-item .tx b { display: block; font-size: 12px; color: #2A2620; }
.tl-item .tx span { font-size: 10px; color: rgba(42, 38, 32, 0.45); }
.tl-val {
  margin-left: auto; font-family: 'Noto Serif SC', serif;
  font-size: 15px; font-weight: 800; color: #2A2620; white-space: nowrap;
}
.tl-val small { font-size: 10px; font-weight: 600; color: rgba(42, 38, 32, 0.45); }
.st-chip { font-size: 9px; font-weight: 700; padding: 2px 8px; border-radius: 999px; flex-shrink: 0; }
.st-chip.ok { background: rgba(127, 174, 142, 0.15); color: #2F7D5B; }
.st-chip.warn { background: rgba(201, 110, 80, 0.14); color: #C0522F; }
.st-chip.info { background: rgba(108, 143, 190, 0.16); color: #5C7DA8; }

/* ---- 保存表单 ---- */
.mt-form { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; margin-top: 12px; }
.mt-form .ff { display: flex; flex-direction: column; gap: 4px; }
.mt-form .ff.span2 { grid-column: 1 / -1; }
.mt-form label { font-size: 10px; color: rgba(42, 38, 32, 0.45); letter-spacing: 0.04em; }
.mt-form input {
  padding: 8px 10px; border-radius: 9px;
  border: 1px solid rgba(184, 134, 59, 0.28);
  background: #fff; font-size: 12px; color: #2A2620;
  outline: none; font-family: inherit;
}
.mt-form input:focus { border-color: #B8863B; }
.unit-hint { font-size: 9.5px; color: rgba(42, 38, 32, 0.4); }
.unit-hint b { color: #B8863B; }

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

/* ---- 健康概览 ---- */
.ov-cells { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; }
.ov-cell {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(184, 134, 59, 0.16);
  border-radius: 11px; padding: 9px 11px;
}
.ov-cell .lb { font-size: 9.5px; color: rgba(42, 38, 32, 0.45); }
.ov-cell .vl {
  margin-top: 2px; font-family: 'Noto Serif SC', serif;
  font-size: 16px; font-weight: 900; color: #2A2620;
}
.ov-cell .vl small { font-size: 10px; font-weight: 600; color: rgba(42, 38, 32, 0.5); margin-left: 3px; }

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

.kin-empty {
  margin-top: 12px;
  border: 1px dashed rgba(184, 134, 59, 0.3);
  border-radius: 12px; padding: 22px 14px;
  font-size: 11.5px; color: #8C7A5E; line-height: 1.7;
  text-align: center;
}

/* ---- 响应式 ---- */
@media (max-width: 1000px) {
  .db-blocks { grid-template-columns: 1fr; }
}
</style>
