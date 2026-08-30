<template>
  <div class="nutri-page" ref="rootRef">
    <!-- ===== 深壳星轨带（宏量素星球上下浮动） ===== -->
    <div class="db-band" ref="bandRef">
      <div class="db-glow db-glow--1" aria-hidden="true"></div>
      <div class="db-glow db-glow--2" aria-hidden="true"></div>

      <div class="db-top">
        <div class="star-crumbs">
          <span class="crumb-wrap">
            <button class="crumb-node" @click="goHome">
              <span class="nd"><LayoutGrid :size="12" /></span>首页
            </button>
          </span>
          <span class="crumb-wrap">
            <span class="crumb-link"></span>
            <button class="crumb-node" @click="goHub"><span class="nd"><Utensils :size="12" /></span>饮食管理</button>
          </span>
          <span class="crumb-wrap">
            <span class="crumb-link"></span>
            <span class="crumb-node hot"><span class="nd"><PieChart :size="13" /></span>营养分析</span>
          </span>
        </div>
        <div class="db-top-right">
          <label class="db-date">
            <Calendar :size="12" />
            <input v-model="analyzeDate" type="date" @change="loadAnalysis" />
          </label>
          <span v-if="userStore.actAsUserId != null" class="db-date actas">
            <UsersRound :size="12" />当前对象：{{ operateAsLabel }}
          </span>
        </div>
      </div>

      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 104" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 52 C 300 8, 440 8, 560 52 S 830 96, 960 52 S 1130 8, 1200 52" />
        </svg>

        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><PieChart :size="19" /></span>
            <span class="tt"><b>营养分析</b><span>NUTRI SCOPE</span></span>
          </div>
        </div>

        <div
          v-for="(p, i) in macroPlanets"
          :key="p.key"
          class="db-station-wrap"
          :style="{ left: stationLeft(i) + '%' }"
        >
          <div class="db-station-float" :style="floatStyle(i)">
            <button
              class="db-station"
              :class="'st-' + p.key"
              :aria-label="p.name"
              @click="pulseLegend(p.key)"
            >
              <component :is="p.icon" :size="15" />
              <span class="nm">{{ p.name }} {{ p.grams }}g</span>
              <span class="ds">{{ p.kcal }} kcal · 占比 {{ p.pct }}%</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区（7:5 · 营养星盘） ===== -->
    <div class="db-paper" ref="paperRef">
      <div class="db-head" data-anim>
        <div class="sec-t">营养星盘 · 每日摄入解析</div>
        <div class="db-pills">
          <span class="pill"><Flame :size="11" />推荐 <b>{{ recommendCalorieMin }} ~ {{ recommendCalorieMax }}</b> kcal</span>
          <span class="pill">BMR <b>{{ bmr }}</b></span>
          <span class="pill">人群 <b>{{ userProfile.crowdType || '普通人' }}</b></span>
        </div>
      </div>

      <div v-if="errorMsg && !analysis" class="db-empty-msg" data-anim>
        <Info :size="16" />
        <span>{{ errorMsg }}</span>
        <button class="ghost-add solid" @click="loadAnalysis">重新加载</button>
      </div>

      <div v-if="loading" class="db-loading" data-anim>星盘计算中...</div>

      <template v-else-if="analysis">
        <div class="np-grid">
          <!-- 左：能量主卡 -->
          <div class="db-block np-energy" data-anim>
            <div class="db-block-head">
              <b>今日摄入</b>
              <span class="db-block-kcal np-big"><span class="kcal-num">{{ kcalDisplay }}</span> kcal</span>
            </div>
            <div class="np-bar-track np-bar-main"><i :style="{ width: Math.min(calorieRatioPct, 100) + '%' }"></i></div>
            <div class="np-status" :class="calorieStatus">
              已达推荐 <b>{{ calorieRatioPct }}%</b> —
              <span v-if="calorieStatus === 'low'">摄入偏少</span>
              <span v-else-if="calorieStatus === 'high'">摄入超标</span>
              <span v-else>基本合适</span>
            </div>
            <div class="np-chips">
              <span class="np-chip">身高 <b>{{ userProfile.height ?? '-' }}</b>cm · 体重 <b>{{ userProfile.weight ?? '-' }}</b>kg</span>
              <span class="np-chip">年龄 <b>{{ userProfile.age ?? '-' }}</b>岁 · {{ userProfile.gender ?? '-' }}</span>
            </div>
            <div class="np-dist">
              <div v-for="d in mealDist" :key="d.label" class="np-dist-row" :class="{ dim: d.kcal === 0 }">
                <span class="lb">{{ d.label }}</span>
                <div class="np-bar-track"><i :style="{ width: d.pct + '%' }"></i></div>
                <span class="k">{{ d.kcal > 0 ? d.kcal + ' kcal' : '待记录' }}</span>
              </div>
            </div>
          </div>

          <!-- 右：三大营养素环 -->
          <div class="db-block np-macro" data-anim>
            <div class="db-block-head" style="width: 100%">
              <b>三大营养素</b>
            </div>
            <div class="np-donut">
              <svg width="150" height="150" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="48" fill="none" stroke="rgba(184,134,59,.1)" stroke-width="13"></circle>
                <circle
                  v-for="(a, i) in donutArcs" :key="i"
                  cx="60" cy="60" r="48" fill="none"
                  :stroke="a.color" stroke-width="13" pathLength="100"
                  :stroke-dasharray="a.seg + ' ' + (100 - a.seg)"
                  :transform="'rotate(' + a.rot + ' 60 60)'"
                  class="np-arc"
                ></circle>
              </svg>
              <div class="ctr">
                <b>{{ totalCalorie || '—' }}</b>
                <span>KCAL 今日</span>
              </div>
            </div>
            <div class="np-legend">
              <div v-for="row in macroRows" :key="row.name" class="np-leg" :data-k="legKey(row.name)">
                <div class="lb">
                  <i :style="{ background: row.color }"></i>{{ row.name }}
                  <b>{{ row.grams.toFixed(1) }} g · {{ row.kcal.toFixed(0) }} kcal</b>
                </div>
                <div class="np-bar-track"><i :style="{ width: Math.min(row.ratioPct, 100) + '%', background: row.color }"></i></div>
                <p class="np-leg-tip" :class="row.status">
                  <b v-if="row.status === 'low'">摄入偏少：</b>
                  <b v-else-if="row.status === 'high'">摄入偏多：</b>
                  <b v-else>摄入合适：</b>
                  <span v-if="row.status === 'low'">{{ row.lowTip }}</span>
                  <span v-else-if="row.status === 'high'">{{ row.highTip }}</span>
                  <span v-else>每 kg 体重 {{ row.perKg.toFixed(2) }}g（推荐 {{ row.perKgRec[0].toFixed(2) }}~{{ row.perKgRec[1].toFixed(2) }}）</span>
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- 微量元素四星站 -->
        <div class="np-micro">
          <div v-for="m in microRows" :key="m.name" class="np-mi" data-anim>
            <div class="nm">{{ m.name }}</div>
            <div class="v">{{ m.grams.toFixed(1) }}<em>{{ m.unit }}</em></div>
            <div class="np-bar-track"><i :style="{ width: Math.min(m.ratioPct, 100) + '%' }"></i></div>
            <div class="st" :class="m.status === 'normal' ? 'ok' : 'warn'">
              <b v-if="m.status === 'low'">偏低</b>
              <b v-else-if="m.status === 'high'">偏高</b>
              <b v-else>合适</b>
              · 推荐 {{ m.recMin.toFixed(0) }}~{{ m.recMax.toFixed(0) }}{{ m.unit }}
            </div>
          </div>
        </div>

        <!-- 系统建议 -->
        <div class="np-advice" data-anim>
          <div class="sec-t" style="font-size: 12px">系统建议</div>
          <div class="np-adv-list">
            <div v-for="(val, key) in analysis.warnings" :key="key" class="np-adv-row">
              <CheckCircle :size="13" />
              <span><b>{{ nutrientLabel(key as string) }}</b>：{{ val || '正常' }}</span>
            </div>
          </div>
          <p class="np-note">注：推荐范围会根据「{{ userProfile.crowdType || '普通人' }}」人群参考值有所不同，仅供健康参考，不作为临床诊断。</p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import {
  LayoutGrid, Utensils, PieChart, Calendar, Flame, Info, CheckCircle,
  Egg, Droplet, Wheat, UsersRound
} from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { useDietStore } from '@/stores/diet'
import { api } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const dietStore = useDietStore()

const today = new Date().toISOString().slice(0, 10)
const analyzeDate = ref(today)
const loading = ref(false)
const errorMsg = ref('')
const analysis = ref<any>(null)

function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'diet' } }) }

const operateAsLabel = computed(() => {
  if (userStore.actAsUserId != null) return `亲属 #${userStore.actAsUserId}`
  return userStore.user?.username || '本人'
})

function asNumber(v: any, fallback = 0): number {
  const n = Number(v)
  return Number.isFinite(n) ? n : fallback
}

const totalCalorie = computed(() => asNumber(analysis.value?.total?.calorie))
const bmr = computed(() => asNumber(analysis.value?.user?.bmr))
const recommendCalorieMin = computed(() => Math.round(asNumber(analysis.value?.user?.recommendCalorieMin, bmr.value * 1.2)))
const recommendCalorieMax = computed(() => Math.round(asNumber(analysis.value?.user?.recommendCalorieMax, bmr.value * 1.5)))
const userProfile = computed(() => analysis.value?.user || {})

const calorieRatioPct = computed(() => {
  const mid = (recommendCalorieMin.value + recommendCalorieMax.value) / 2 || 1
  return Math.round((totalCalorie.value / mid) * 100)
})
const calorieStatus = computed(() => {
  if (calorieRatioPct.value < 80) return 'low'
  if (calorieRatioPct.value > 120) return 'high'
  return 'normal'
})

// ---- 三大营养素克数 -> 热量（统一三色：蛋白蓝 / 脂肪黄 / 碳水绿） ----
const COLOR = { protein: '#6C8FBE', fat: '#D9A24A', carb: '#7FAE8E' }
const proteinG = computed(() => asNumber(analysis.value?.total?.protein))
const fatG = computed(() => asNumber(analysis.value?.total?.fat))
const carbG = computed(() => asNumber(analysis.value?.total?.carb))
const proteinKcal = computed(() => Math.round(proteinG.value * 4))
const fatKcal = computed(() => Math.round(fatG.value * 9))
const carbKcal = computed(() => Math.round(carbG.value * 4))
const macroSumKcal = computed(() => proteinKcal.value + fatKcal.value + carbKcal.value)

const macroPlanets = computed(() => [
  { key: 'protein', name: '蛋白质', grams: proteinG.value.toFixed(1), kcal: proteinKcal.value, pct: pctOf(proteinKcal.value), icon: Egg },
  { key: 'fat', name: '脂肪', grams: fatG.value.toFixed(1), kcal: fatKcal.value, pct: pctOf(fatKcal.value), icon: Droplet },
  { key: 'carb', name: '碳水', grams: carbG.value.toFixed(1), kcal: carbKcal.value, pct: pctOf(carbKcal.value), icon: Wheat }
])
function pctOf(k: number): number {
  return macroSumKcal.value > 0 ? Math.round((k / macroSumKcal.value) * 100) : 0
}

// ---- 星轨站点分布 + 浮动节奏（与记录页同款） ----
function stationLeft(i: number): number {
  return 42 + i * 18
}
function floatStyle(i: number): Record<string, string> {
  return {
    animationDuration: (4.6 + (i % 4) * 0.45) + 's',
    animationDelay: -(i * 0.9) + 's'
  }
}

// ---- SVG 三色环（pathLength=100 归一化弧段） ----
const donutArcs = computed(() => {
  const total = macroSumKcal.value
  const colors = [COLOR.protein, COLOR.fat, COLOR.carb]
  if (total <= 0) {
    return colors.map((c) => ({ seg: 0, rot: -90, color: c }))
  }
  const fracs = [proteinKcal.value / total * 100, fatKcal.value / total * 100, carbKcal.value / total * 100]
  let acc = 0
  return fracs.map((f, i) => {
    const rot = acc * 3.6 - 90
    acc += f
    return { seg: Math.max(f - 1.2, 0), rot, color: colors[i] }
  })
})

// ---- 宏量素对比行（保留原推荐逻辑） ----
const macroRows = computed(() => {
  const recs: any = analysis.value?.recommendations || {}
  const w = asNumber(analysis.value?.user?.weight, 0) || 65
  type MacroRow = {
    name: string; grams: number; kcal: number; perKg: number;
    recMin: number; recMax: number; perKgRec: number[];
    ratioPct: number; status: string; color: string;
    lowTip: string; highTip: string
  }
  const build = (name: string, grams: number, kcal: number, perKgFromRec: number[] | undefined, ideal: number[], color: string, lowTip: string, highTip: string): MacroRow => {
    const minPerKg = perKgFromRec?.[0] ?? ideal[0]
    const maxPerKg = perKgFromRec?.[1] ?? ideal[1]
    const recMin = minPerKg * w
    const recMax = maxPerKg * w
    const perKg = grams / w
    const mid = (recMin + recMax) / 2 || 1
    const ratioPct = Math.max(0, Math.round((grams / mid) * 100))
    let status = 'normal'
    if (ratioPct < 80) status = 'low'
    else if (ratioPct > 120) status = 'high'
    return { name, grams, kcal, perKg, recMin, recMax, perKgRec: [minPerKg, maxPerKg], ratioPct, status, color, lowTip, highTip }
  }
  const proteinPerKg = typeof recs.proteinPerKg === 'object' && recs.proteinPerKg ? recs.proteinPerKg : undefined
  const fatPerKg = typeof recs.fatPerKg === 'object' && recs.fatPerKg ? recs.fatPerKg : undefined
  const carbPerKg = typeof recs.carbPerKg === 'object' && recs.carbPerKg ? recs.carbPerKg : undefined
  return [
    build('蛋白质', proteinG.value, proteinKcal.value, proteinPerKg, [1.0, 1.2], COLOR.protein,
      '优质来源不足会导致肌肉流失、免疫力下降、运动恢复差',
      '蛋白质过量会加重肾脏负担、可能诱发痛风、热量容易超标'),
    build('脂肪', fatG.value, fatKcal.value, fatPerKg, [0.8, 1.0], COLOR.fat,
      '脂肪摄入不足会影响脂溶性维生素吸收、激素合成原料缺失',
      '脂肪摄入超标会导致热量爆炸、高血脂、心血管负担增加'),
    build('碳水化合物', carbG.value, carbKcal.value, carbPerKg, [3.0, 4.0], COLOR.carb,
      '碳水摄入不足会导致大脑供能不足、头晕、运动无力、肌肉分解',
      '碳水摄入超标会引起血糖波动、胰岛素抵抗、内脏脂肪堆积')
  ]
})

function legKey(name: string): string {
  if (name.indexOf('蛋白') >= 0) return 'protein'
  if (name.indexOf('脂肪') >= 0) return 'fat'
  return 'carb'
}

// ---- 微量元素行（保留原逻辑） ----
const microRows = computed(() => {
  const total: any = analysis.value?.total || {}
  const recs: any = analysis.value?.recommendations || {}
  const statusMap: any = analysis.value?.status || {}
  const warnings: any = analysis.value?.warnings || {}
  const items = [
    { key: 'dietFiber', name: '膳食纤维', unit: 'g' },
    { key: 'calcium', name: '钙', unit: 'mg' },
    { key: 'dha', name: 'DHA', unit: 'mg' },
    { key: 'folicAcid', name: '叶酸', unit: 'μg' }
  ]
  return items.map((it) => {
    const grams = asNumber(total[it.key])
    const recMin = asNumber(recs[it.key + 'Min'])
    const recMax = asNumber(recs[it.key + 'Max'])
    const mid = (recMin + recMax) / 2 || 1
    const ratioPct = Math.max(0, Math.round((grams / mid) * 100))
    const status: string = statusMap[it.key] || (ratioPct < 80 ? 'low' : ratioPct > 120 ? 'high' : 'normal')
    const tip = warnings[it.key] || ''
    return {
      name: it.name, grams, unit: it.unit,
      recMin, recMax, ratioPct, status,
      lowTip: tip, highTip: tip
    }
  })
})

function nutrientLabel(key: string) {
  const map: Record<string, string> = {
    protein: '蛋白质', fat: '脂肪', carb: '碳水化合物',
    calcium: '钙', folicAcid: '叶酸', dietFiber: '膳食纤维', dha: 'DHA',
    calorie: '热量'
  }
  return map[key] || key
}

// ---- 四餐分布（从当日记录汇总，兼容 items/foods 两种字段） ----
const mealsData = computed(() => dietStore.currentMeals)
function mealKcalOf(m: any): number {
  let kcal = Number(m?.meal_calories_kcal) || 0
  const items = m?.items ?? m?.foods ?? []
  for (const it of items) {
    const per100 = Number(it?.calorie)
    const w = Number(it?.eatWeight)
    if (Number.isFinite(per100) && Number.isFinite(w) && w > 0) {
      kcal += per100 * w / 100
    } else {
      kcal += Number(it?.calories_kcal ?? it?.calories ?? it?.cal) || 0
    }
  }
  return kcal
}
const mealDist = computed(() => {
  const types = ['早餐', '午餐', '晚餐', '加餐']
  const totals: Record<string, number> = {}
  mealsData.value.forEach((m: any) => {
    const mt = m.mealType || m.meal_type
    if (mt && types.includes(mt)) totals[mt] = (totals[mt] || 0) + mealKcalOf(m)
  })
  const sum = types.reduce((s, t) => s + (totals[t] || 0), 0)
  return types.map((t) => {
    const k = Math.round(totals[t] || 0)
    return { label: t, kcal: k, pct: sum > 0 ? Math.max(k > 0 ? 3 : 0, Math.round((k / sum) * 100)) : 0 }
  })
})

// ---- 热量数字滚动 ----
const kcalDisplay = ref('0')
watch(totalCalorie, (t) => {
  const o = { v: Number(kcalDisplay.value) || 0 }
  gsap.to(o, { v: t, duration: 0.9, ease: 'power2.out', onUpdate: () => { kcalDisplay.value = String(Math.round(o.v)) } })
})

// ---- 星球点击 → 脉冲对应图例行 ----
const rootRef = ref<HTMLElement | null>(null)
function pulseLegend(key: string) {
  const el = rootRef.value?.querySelector('.np-leg[data-k="' + key + '"]')
  if (el) gsap.fromTo(el, { scale: 1 }, { scale: 1.04, duration: 0.22, yoyo: true, repeat: 1, ease: 'power2.out', transformOrigin: 'left center' })
}

async function loadAnalysis() {
  loading.value = true
  errorMsg.value = ''
  try {
    // 先从 store 拉取当日饮食（供四餐分布使用），再调用营养分析
    await dietStore.fetchTodayMeals(analyzeDate.value)
    const data: any = await api.diet.analyze(analyzeDate.value)
    if (data && (data.total || data.user)) {
      analysis.value = data
    } else {
      errorMsg.value = '暂无该日期的营养分析数据'
      analysis.value = null
    }
  } catch (e: any) {
    console.warn('营养分析API不可用', e)
    errorMsg.value = '营养分析暂不可用'
    analysis.value = null
  } finally {
    loading.value = false
  }
}

// ---- 入场动效 ----
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
  try { await userStore.init() } catch { /* ignore */ }
  loadAnalysis()
})
</script>

<style scoped>
.nutri-page {
  position: relative;
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
}

/* ========== 深壳星轨带（与记录页同款） ========== */
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
.db-glow { position: absolute; border-radius: 50%; filter: blur(50px); pointer-events: none; z-index: 0; }
.db-glow--1 { width: 200px; height: 200px; right: -60px; top: -110px; background: rgba(232, 185, 115, 0.12); animation: dbGlowFloat 9s ease-in-out infinite alternate; }
.db-glow--2 { width: 170px; height: 170px; left: -70px; bottom: -100px; background: rgba(179, 107, 42, 0.1); animation: dbGlowFloat 11s ease-in-out infinite alternate-reverse; }
@keyframes dbGlowFloat { from { transform: translate3d(0, 0, 0) scale(1); } to { transform: translate3d(16px, 10px, 0) scale(1.12); } }

.db-top { position: relative; z-index: 2; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.star-crumbs { display: flex; align-items: center; }
.crumb-wrap { display: flex; align-items: center; }
.crumb-link { width: 42px; height: 0; border-top: 1.5px dashed rgba(184, 134, 59, 0.45); margin: 0 5px; }
.crumb-node { display: inline-flex; align-items: center; gap: 7px; font-size: 11.5px; color: #8C7A5E; background: none; border: none; padding: 0; font-family: inherit; letter-spacing: 0.04em; }
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
.db-top-right { margin-left: auto; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.db-date {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px; color: #B9A78A;
  border: 1px solid rgba(217, 162, 74, 0.3);
  background: rgba(217, 162, 74, 0.08);
  border-radius: 999px; padding: 3px 10px;
}
.db-date svg { color: #E8B973; flex-shrink: 0; }
.db-date.actas { color: #E8C684; border-color: rgba(232, 185, 115, 0.5); }
.db-date input {
  background: transparent; border: none; outline: none;
  color: #F0E2C4; font-size: 11px; font-family: inherit;
  color-scheme: dark; cursor: pointer; letter-spacing: 0.03em;
}

.db-const { position: relative; z-index: 1; height: 104px; margin-top: 6px; }
.db-line { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }
.db-line path { fill: none; stroke: rgba(217, 162, 74, 0.35); stroke-width: 1.2; stroke-dasharray: 5 6; vector-effect: non-scaling-stroke; }

.db-core-wrap { position: absolute; left: 4px; top: 50%; margin-top: -23px; z-index: 2; }
.db-core { display: flex; align-items: center; gap: 10px; animation: dbFloat 6.4s ease-in-out infinite alternate; animation-delay: -0.6s; }
.db-core .star {
  width: 46px; height: 46px; border-radius: 50%;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(232, 185, 115, 0.55);
  display: flex; align-items: center; justify-content: center;
  color: #E8B973; box-shadow: 0 0 22px rgba(217, 162, 74, 0.32);
  animation: dbBreath 3.2s ease-in-out infinite;
}
@keyframes dbBreath { 0%, 100% { box-shadow: 0 0 18px rgba(217, 162, 74, 0.3); } 50% { box-shadow: 0 0 34px rgba(217, 162, 74, 0.52); } }
.db-core .tt b { display: block; font-size: 12.5px; color: #F6EAD6; font-weight: 700; letter-spacing: 0.08em; }
.db-core .tt span { display: block; margin-top: 2px; font-size: 9.5px; color: #9A8A6C; letter-spacing: 0.12em; }

.db-station-wrap { position: absolute; top: 50%; width: 44px; height: 44px; margin: -22px 0 0 -22px; z-index: 3; }
.db-station-float { width: 100%; height: 100%; animation: dbFloat 4.6s ease-in-out infinite alternate; }
@keyframes dbFloat { from { transform: translateY(4px); } to { transform: translateY(-8px); } }
.db-station {
  position: relative; width: 44px; height: 44px; border-radius: 50%; cursor: pointer;
  background: rgba(24, 19, 12, 0.95);
  border: 1px solid rgba(217, 162, 74, 0.45); color: #E8B973;
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.5, 0.5, 1), border-color 0.3s ease, box-shadow 0.3s ease;
}
.db-station .nm {
  position: absolute; top: -26px; left: 50%; transform: translateX(-50%);
  font-size: 10px; color: #F0E2C4; white-space: nowrap; letter-spacing: 0.06em;
  opacity: 0.72; transition: opacity 0.3s ease, color 0.3s ease;
}
.db-station .ds {
  position: absolute; top: calc(100% + 10px); left: 50%;
  transform: translateX(-50%) translateY(4px); white-space: nowrap;
  font-size: 9.5px; color: #F6EAD6;
  background: rgba(24, 19, 12, 0.95); border: 1px solid rgba(217, 162, 74, 0.4);
  padding: 2px 9px; border-radius: 999px;
  opacity: 0; transition: opacity 0.28s ease, transform 0.28s ease; pointer-events: none;
}
.db-station:hover { transform: scale(1.14); border-color: #E8B973; box-shadow: 0 0 0 5px rgba(217, 162, 74, 0.14), 0 10px 26px rgba(217, 162, 74, 0.32); }
.db-station:hover .ds { opacity: 1; transform: translateX(-50%) translateY(0); }
.db-station:hover .nm { opacity: 1; color: #E8B973; }
.db-station.st-protein { border-color: rgba(108, 143, 190, 0.75); color: #9FB8DE; box-shadow: 0 0 14px rgba(108, 143, 190, 0.35); }
.db-station.st-protein .nm { color: #B9CCE8; }
.db-station.st-fat { border-color: rgba(217, 162, 74, 0.8); color: #E8C684; }
.db-station.st-fat .nm { color: #EDD3A0; }
.db-station.st-carb { border-color: rgba(127, 174, 142, 0.8); color: #A5C7B1; box-shadow: 0 0 14px rgba(127, 174, 142, 0.3); }
.db-station.st-carb .nm { color: #BFD8C8; }

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
.db-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.sec-t { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; color: #2A2620; letter-spacing: 0.02em; }
.sec-t::before { content: ''; width: 3px; height: 14px; border-radius: 99px; background: linear-gradient(180deg, #E8B973, #B8863B); }
.db-pills { margin-left: auto; display: flex; gap: 8px; flex-wrap: wrap; }
.pill {
  font-size: 11px; color: #6E6350;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(184, 134, 59, 0.2);
  padding: 4px 12px; border-radius: 999px;
  display: inline-flex; align-items: center; gap: 5px;
}
.pill svg { color: #B8863B; }
.pill b { color: #B8863B; font-weight: 700; }
.db-loading { text-align: center; font-size: 12.5px; color: #8C7A5E; padding: 60px 0; }
.db-empty-msg {
  margin-top: 14px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  background: rgba(255, 255, 255, 0.75); border: 1px dashed rgba(184, 134, 59, 0.35);
  border-radius: 14px; padding: 16px 18px; font-size: 12.5px; color: #6E6350;
}
.db-empty-msg svg { color: #B8863B; flex-shrink: 0; }
.ghost-add {
  display: inline-flex; align-items: center; gap: 6px;
  border: 1px dashed rgba(184, 134, 59, 0.4);
  color: #B8863B; background: none; cursor: pointer;
  font-size: 12px; font-weight: 600; letter-spacing: 0.05em;
  border-radius: 10px; padding: 8px 14px; transition: 0.25s; font-family: inherit;
}
.ghost-add:hover { background: rgba(217, 162, 74, 0.1); border-color: #B8863B; }
.ghost-add.solid { border-style: solid; }

.db-block {
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(184, 134, 59, 0.16);
  border-radius: 16px;
  padding: 16px 18px;
}
.db-block-head { display: flex; align-items: baseline; gap: 8px; }
.db-block-head b { font-size: 13px; color: #2A2620; font-weight: 700; }
.db-block-kcal { margin-left: auto; font-family: 'Noto Serif SC', serif; font-size: 17px; font-weight: 900; color: #B8863B; }
.db-block-kcal.np-big { font-size: 30px; }

/* ---- 能量主卡 ---- */
.np-grid { display: grid; grid-template-columns: 7fr 5fr; gap: 12px; margin-top: 14px; }
.np-bar-track { height: 6px; border-radius: 99px; background: rgba(184, 134, 59, 0.1); overflow: hidden; }
.np-bar-track i { display: block; height: 100%; border-radius: 99px; background: linear-gradient(90deg, #E8B973, #B8863B); transition: width 0.8s cubic-bezier(0.34, 1.3, 0.64, 1); }
.np-bar-main { height: 8px; margin-top: 10px; }
.np-status { font-size: 11px; margin-top: 7px; font-weight: 600; }
.np-status.normal { color: #2F7D5B; }
.np-status.low { color: #C98F2F; }
.np-status.high { color: #C0522F; }
.np-status b { font-family: 'Noto Serif SC', serif; font-size: 13px; }
.np-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.np-chip { font-size: 10px; color: #6E6350; background: rgba(255, 255, 255, 0.6); border: 1px solid rgba(184, 134, 59, 0.16); padding: 2px 9px; border-radius: 99px; }
.np-chip b { color: #B8863B; }
.np-dist { margin-top: 13px; padding-top: 11px; border-top: 1px dashed rgba(184, 134, 59, 0.2); display: flex; flex-direction: column; gap: 6px; }
.np-dist-row { display: flex; align-items: center; gap: 8px; font-size: 10.5px; }
.np-dist-row .lb { width: 28px; color: rgba(42, 38, 32, 0.55); flex-shrink: 0; }
.np-dist-row .np-bar-track { flex: 1; height: 5px; }
.np-dist-row .k { width: 68px; text-align: right; color: #B8863B; font-weight: 700; flex-shrink: 0; }
.np-dist-row.dim .k { color: rgba(42, 38, 32, 0.4); font-weight: 500; }

/* ---- 三大营养素环 ---- */
.np-macro { display: flex; flex-direction: column; align-items: center; }
.np-donut { position: relative; width: 150px; height: 150px; margin-top: 8px; }
.np-donut .ctr { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.np-donut .ctr b { font-family: 'Noto Serif SC', serif; font-size: 22px; font-weight: 900; color: #B8863B; }
.np-donut .ctr span { font-size: 9px; color: #8C7A5E; letter-spacing: 0.1em; margin-top: 1px; }
.np-arc { transition: stroke-dasharray 0.8s cubic-bezier(0.34, 1.3, 0.64, 1); }
.np-legend { width: 100%; margin-top: 12px; display: flex; flex-direction: column; gap: 10px; }
.np-leg { border-radius: 8px; }
.np-leg .lb { display: flex; align-items: center; gap: 6px; font-size: 10.5px; color: rgba(42, 38, 32, 0.55); }
.np-leg .lb i { width: 8px; height: 8px; border-radius: 3px; flex-shrink: 0; }
.np-leg .lb b { margin-left: auto; color: #2A2620; font-size: 10.5px; }
.np-leg .np-bar-track { height: 5px; margin-top: 4px; }
.np-leg-tip { font-size: 10px; margin-top: 4px; line-height: 1.6; }
.np-leg-tip.normal { color: #2F7D5B; }
.np-leg-tip.low { color: #C98F2F; }
.np-leg-tip.high { color: #C0522F; }

/* ---- 微量元素 ---- */
.np-micro { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 12px; }
.np-mi { background: rgba(255, 255, 255, 0.75); border: 1px solid rgba(184, 134, 59, 0.16); border-radius: 13px; padding: 11px 13px; }
.np-mi .nm { font-size: 10.5px; color: rgba(42, 38, 32, 0.55); }
.np-mi .v { font-family: 'Noto Serif SC', serif; font-size: 16px; font-weight: 900; color: #2A2620; margin-top: 2px; }
.np-mi .v em { font-style: normal; font-size: 9px; color: #8C7A5E; margin-left: 2px; }
.np-mi .np-bar-track { height: 4px; margin-top: 5px; }
.np-mi .st { font-size: 9px; margin-top: 5px; font-weight: 700; }
.np-mi .st.ok { color: #2F7D5B; }
.np-mi .st.warn { color: #C0522F; }

/* ---- 系统建议 ---- */
.np-advice { margin-top: 12px; background: rgba(255, 255, 255, 0.75); border: 1px solid rgba(184, 134, 59, 0.16); border-radius: 16px; padding: 13px 16px; }
.np-adv-row { display: flex; align-items: flex-start; gap: 8px; padding: 6px 0; font-size: 11.5px; color: #2A2620; line-height: 1.7; }
.np-adv-row svg { color: #2F7D5B; flex-shrink: 0; margin-top: 2px; }
.np-adv-row b { color: #B8863B; }
.np-note { font-size: 10px; color: rgba(42, 38, 32, 0.4); margin-top: 6px; }

/* ---- 响应式 ---- */
@media (max-width: 1000px) {
  .np-grid { grid-template-columns: 1fr; }
  .np-micro { grid-template-columns: repeat(2, 1fr); }
}
</style>
