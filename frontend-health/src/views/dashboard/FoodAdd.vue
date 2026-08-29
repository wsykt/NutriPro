<template>
  <div class="diet-page">
    <!-- ===== 深壳星轨带（与首页/记录页/星表同构 · 炼成要素星球上下浮动） ===== -->
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
            <span class="crumb-node hot"><span class="nd"><FlaskConical :size="13" /></span>自定义食物</span>
          </span>
        </div>
        <div class="db-top-right">
          <span class="db-date"><ShieldCheck :size="12" />提交后由管理员审核</span>
        </div>
      </div>

      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 104" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 52 C 300 8, 440 8, 560 52 S 830 96, 960 52 S 1130 8, 1200 52" />
        </svg>

        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><FlaskConical :size="19" /></span>
            <span class="tt"><b>星料炼成</b><span>STAR FORGE</span></span>
          </div>
        </div>

        <div
          v-for="(p, i) in forgePlanets"
          :key="p.key"
          class="db-station-wrap"
          :style="{ left: stationLeft(i) + '%' }"
        >
          <div class="db-station-float" :style="floatStyle(i)">
            <button
              class="db-station"
              :class="['st-' + p.key, { lit: p.grams > 0 }]"
              :aria-label="p.name"
            >
              <component :is="p.icon" :size="15" />
              <span class="nm">{{ p.name }} {{ p.grams }}g</span>
              <span class="ds">{{ p.kcal }} kcal · 占比 {{ p.pct }}%</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区（7:5 · 星料炼成） ===== -->
    <div class="db-paper" ref="paperRef">
      <div class="db-head" data-anim>
        <div class="sec-t">炼成工作台 · 提交一颗新星</div>
        <div class="db-pills">
          <span class="pill"><FlaskConical :size="11" />预估热量 <b>{{ kcalPreview }}</b> kcal</span>
          <span class="pill">分类库 <b>{{ categories.length }}</b> 类</span>
        </div>
      </div>

      <div v-if="successMsg" class="fa-toast" data-anim>
        <CheckCircle :size="16" />
        <span>{{ successMsg }}</span>
      </div>

      <div class="db-blocks">
        <!-- 左：炼成表单 -->
        <div class="db-block main" data-anim>
          <div class="db-block-head"><b>星料档案</b></div>

          <div class="fa-form">
            <div class="fa-field fa-span2">
              <label>食材名称 <i>*</i></label>
              <input v-model="form.foodName" type="text" placeholder="如 南瓜子" />
            </div>
            <div class="fa-field">
              <label>食物分类 <i>*</i></label>
              <select v-model="form.foodCategory" :class="{ placeholder: !form.foodCategory }">
                <option value="">请选择分类</option>
                <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div class="fa-field">
              <label>GI 值</label>
              <input v-model.number="form.giValue" type="number" step="1" placeholder="如 70" />
            </div>

            <div class="fa-divider"><span>三大炼成要素（每 100g）</span></div>

            <div class="fa-field">
              <label><i class="dot protein"></i>蛋白质 g</label>
              <input v-model.number="form.protein" type="number" step="0.1" placeholder="如 20" />
            </div>
            <div class="fa-field">
              <label><i class="dot fat"></i>脂肪 g</label>
              <input v-model.number="form.fat" type="number" step="0.1" placeholder="如 15" />
            </div>
            <div class="fa-field">
              <label><i class="dot carb"></i>碳水 g</label>
              <input v-model.number="form.carb" type="number" step="0.1" placeholder="如 30" />
            </div>
            <div class="fa-field">
              <label>膳食纤维 g</label>
              <input v-model.number="form.dietFiber" type="number" step="0.1" placeholder="如 5" />
            </div>
            <div class="fa-field">
              <label>钙 mg</label>
              <input v-model.number="form.calcium" type="number" step="1" placeholder="如 100" />
            </div>
            <div class="fa-field">
              <label>DHA mg</label>
              <input v-model.number="form.dha" type="number" step="1" placeholder="如 0" />
            </div>
            <div class="fa-field">
              <label>叶酸 μg</label>
              <input v-model.number="form.folicAcid" type="number" step="1" placeholder="如 50" />
            </div>
          </div>
        </div>

        <!-- 右：实时炼成环 + 提交 -->
        <div class="db-block side" data-anim>
          <div class="db-side-head"><b>实时炼成环</b></div>

          <div class="fa-ring-wrap">
            <svg class="fa-ring" viewBox="0 0 100 100" aria-hidden="true">
              <circle class="ring-track" cx="50" cy="50" r="40" />
              <circle
                v-for="(a, i) in ringArcs" :key="i"
                class="ring-seg"
                cx="50" cy="50" r="40"
                :stroke="a.color"
                :stroke-dasharray="a.dash"
                :transform="'rotate(' + a.rot + ' 50 50)'"
              />
            </svg>
            <div class="fa-ring-center">
              <b>{{ kcalPreview }}</b>
              <span>kcal / 100g</span>
            </div>
          </div>

          <div class="db-macros">
            <div v-for="m in macroRows" :key="m.key" class="db-macro">
              <div class="lb"><i :style="{ background: m.color }"></i>{{ m.key }}<b>{{ num(m.g) }} g · {{ m.pct }}%</b></div>
              <div class="bar"><i :style="{ width: m.pct + '%', background: m.color }"></i></div>
            </div>
          </div>

          <div v-if="errorMsg" class="fa-error">{{ errorMsg }}</div>

          <div class="fa-actions">
            <button class="ghost-add" @click="resetForm">重置</button>
            <button class="confirm-btn" :disabled="submitting" @click="submitFood">
              {{ submitting ? '炼成中...' : '提交审核' }}
            </button>
          </div>
          <p class="fa-note">提交后进入待审核状态，管理员审核通过后才会出现在星表中。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import {
  LayoutGrid, Utensils, FlaskConical, ShieldCheck, CheckCircle,
  Beef, Droplet, Wheat
} from 'lucide-vue-next'
import { FOOD_CATEGORIES } from '../../constants'
import { api } from '../../api'

const router = useRouter()
const categories = [...FOOD_CATEGORIES]

const form = reactive({
  foodName: '',
  foodCategory: '',
  protein: null as number | null,
  fat: null as number | null,
  carb: null as number | null,
  dietFiber: null as number | null,
  giValue: null as number | null,
  calcium: null as number | null,
  dha: null as number | null,
  folicAcid: null as number | null
})

const submitting = ref(false)
const successMsg = ref('')
const errorMsg = ref('')

function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'diet' } }) }

function num(v: number | null): number {
  const n = Number(v)
  if (!Number.isFinite(n)) return 0
  return Math.round(n * 10) / 10
}

// ---- 三大炼成要素星球（蛋白蓝 / 脂肪黄 / 碳水绿） ----
const COLOR = { protein: '#6C8FBE', fat: '#D9A24A', carb: '#7FAE8E' }

const proteinKcal = computed(() => (Number(form.protein) || 0) * 4)
const fatKcal = computed(() => (Number(form.fat) || 0) * 9)
const carbKcal = computed(() => (Number(form.carb) || 0) * 4)
const macroSumKcal = computed(() => proteinKcal.value + fatKcal.value + carbKcal.value)
const kcalPreview = computed(() => Math.round(macroSumKcal.value))

function pctOf(kcal: number): number {
  return macroSumKcal.value > 0 ? Math.round((kcal / macroSumKcal.value) * 100) : 0
}

const forgePlanets = computed(() => [
  { key: 'protein', name: '蛋白质', grams: num(form.protein), kcal: Math.round(proteinKcal.value), pct: pctOf(proteinKcal.value), icon: Beef },
  { key: 'fat', name: '脂肪', grams: num(form.fat), kcal: Math.round(fatKcal.value), pct: pctOf(fatKcal.value), icon: Droplet },
  { key: 'carb', name: '碳水', grams: num(form.carb), kcal: Math.round(carbKcal.value), pct: pctOf(carbKcal.value), icon: Wheat }
])

// ---- 星轨站点：横向分布 + 各自漂浮节奏 ----
function stationLeft(i: number): number {
  return 34 + i * 20
}
function floatStyle(i: number): Record<string, string> {
  return {
    animationDuration: (4.6 + (i % 4) * 0.45) + 's',
    animationDelay: -(i * 0.9) + 's'
  }
}

// ---- 实时炼成环：SVG 三色弧段（与营养星盘同实现） ----
const CIRC = 2 * Math.PI * 40

const ringArcs = computed(() => {
  const total = macroSumKcal.value
  const colors = [COLOR.protein, COLOR.fat, COLOR.carb]
  if (total <= 0) {
    return colors.map((c) => ({ dash: '0 ' + CIRC, rot: -90, color: c }))
  }
  const fracs = [proteinKcal.value / total, fatKcal.value / total, carbKcal.value / total]
  let acc = 0
  return fracs.map((f, i) => {
    const rot = acc * 360 - 90
    acc += f
    const seg = Math.max(f * CIRC - 2.5, 0)
    return { dash: seg + ' ' + CIRC, rot, color: colors[i] }
  })
})

const macroRows = computed(() => [
  { key: '蛋白质', g: Number(form.protein) || 0, pct: pctOf(proteinKcal.value), color: COLOR.protein },
  { key: '脂肪', g: Number(form.fat) || 0, pct: pctOf(fatKcal.value), color: COLOR.fat },
  { key: '碳水', g: Number(form.carb) || 0, pct: pctOf(carbKcal.value), color: COLOR.carb }
])

const resetForm = () => {
  form.foodName = ''
  form.foodCategory = ''
  form.protein = null
  form.fat = null
  form.carb = null
  form.dietFiber = null
  form.giValue = null
  form.calcium = null
  form.dha = null
  form.folicAcid = null
  successMsg.value = ''
  errorMsg.value = ''
}

const submitFood = async () => {
  if (!form.foodName.trim()) {
    errorMsg.value = '请输入食材名称'
    return
  }
  if (!form.foodCategory) {
    errorMsg.value = '请选择食物分类'
    return
  }
  errorMsg.value = ''
  submitting.value = true
  try {
    await api.food.add({
      foodName: form.foodName.trim(),
      foodCategory: form.foodCategory,
      calorie: macroSumKcal.value > 0 ? Math.round(macroSumKcal.value * 10) / 10 : null,
      protein: form.protein,
      fat: form.fat,
      carb: form.carb,
      dietFiber: form.dietFiber,
      giValue: form.giValue,
      calcium: form.calcium,
      dha: form.dha,
      folicAcid: form.folicAcid
    })
    successMsg.value = `新星「${form.foodName.trim()}」已炼成，等待管理员审核后加入星表。`
    resetFormKeepToast()
    setTimeout(() => { successMsg.value = '' }, 4000)
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.message || e?.message || '提交失败，请稍后再试。'
  } finally {
    submitting.value = false
  }
}

function resetFormKeepToast() {
  form.foodName = ''
  form.foodCategory = ''
  form.protein = null
  form.fat = null
  form.carb = null
  form.dietFiber = null
  form.giValue = null
  form.calcium = null
  form.dha = null
  form.folicAcid = null
  errorMsg.value = ''
}

// ===== 入场动效（与首页/记录页同节奏：面包屑点亮 → 星球弹出 → 浅芯浮起） =====
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

onMounted(() => {
  animateEntrance()
})
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

/* ---- 三大要素星球 ---- */
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
  cursor: default;
  background: rgba(24, 19, 12, 0.95);
  border: 1px solid rgba(217, 162, 74, 0.45);
  color: #E8B973;
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.5, 0.5, 1), border-color 0.3s ease, box-shadow 0.3s ease;
}
.db-station.lit { transform: scale(1.06); }
.db-station.st-protein.lit { border-color: #6C8FBE; box-shadow: 0 0 18px rgba(108, 143, 190, 0.45); color: #9DB9DE; }
.db-station.st-fat.lit { border-color: #D9A24A; box-shadow: 0 0 18px rgba(217, 162, 74, 0.45); color: #E8B973; }
.db-station.st-carb.lit { border-color: #7FAE8E; box-shadow: 0 0 18px rgba(127, 174, 142, 0.45); color: #9FC9AC; }
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

.fa-toast {
  margin-top: 12px;
  display: flex; align-items: center; gap: 8px;
  background: rgba(127, 174, 142, 0.12);
  border: 1px solid rgba(127, 174, 142, 0.35);
  border-radius: 12px; padding: 10px 14px;
  font-size: 12px; color: #2F7D5B; font-weight: 600;
  animation: toastPop 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.fa-toast svg { flex-shrink: 0; }
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
.db-block-head b, .db-side-head b { font-size: 13px; color: #2A2620; font-weight: 700; }
.db-side-head {
  display: flex; align-items: baseline; gap: 8px;
}

/* ---- 左：表单 ---- */
.fa-form {
  margin-top: 12px;
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px 14px;
}
.fa-field label {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; color: rgba(42, 38, 32, 0.55); margin-bottom: 5px;
}
.fa-field label i { font-style: normal; color: #C0522F; }
.fa-field label .dot {
  width: 8px; height: 8px; border-radius: 3px; display: inline-block;
}
.fa-field label .dot.protein { background: #6C8FBE; }
.fa-field label .dot.fat { background: #D9A24A; }
.fa-field label .dot.carb { background: #7FAE8E; }
.fa-field input, .fa-field select {
  width: 100%; padding: 8px 10px; border-radius: 10px;
  border: 1px solid rgba(184, 134, 59, 0.25);
  background: #fff; font-size: 12.5px; color: #2A2620; outline: none;
  font-family: inherit; transition: border-color 0.25s ease;
}
.fa-field input:focus, .fa-field select:focus { border-color: #B8863B; }
.fa-field select.placeholder { color: rgba(42, 38, 32, 0.35); }
.fa-span2 { grid-column: span 2; }
.fa-divider {
  grid-column: span 2;
  display: flex; align-items: center; gap: 10px;
  margin-top: 2px;
  font-size: 10.5px; color: #B8863B; letter-spacing: 0.08em; font-weight: 600;
}
.fa-divider::before, .fa-divider::after {
  content: ''; flex: 1; height: 0;
  border-top: 1px dashed rgba(184, 134, 59, 0.3);
}

/* ---- 右：炼成环 ---- */
.fa-ring-wrap {
  position: relative;
  width: 150px; height: 150px;
  margin: 14px auto 4px;
}
.fa-ring { width: 100%; height: 100%; }
.ring-track {
  fill: none; stroke: rgba(184, 134, 59, 0.12); stroke-width: 9;
}
.ring-seg {
  fill: none; stroke-width: 9; stroke-linecap: round;
  transition: stroke-dasharray 0.55s cubic-bezier(0.34, 1.3, 0.64, 1);
}
.fa-ring-center {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 2px; pointer-events: none;
}
.fa-ring-center b {
  font-family: 'Noto Serif SC', serif;
  font-size: 26px; font-weight: 900; color: #B8863B; line-height: 1;
}
.fa-ring-center span { font-size: 9px; color: rgba(42, 38, 32, 0.45); letter-spacing: 0.05em; }

.db-macros {
  display: flex; flex-direction: column; gap: 10px;
  margin-top: 14px;
}
.db-macro .lb {
  display: flex; align-items: center; gap: 6px;
  font-size: 10.5px; color: rgba(42, 38, 32, 0.55);
}
.db-macro .lb i { width: 8px; height: 8px; border-radius: 3px; flex-shrink: 0; }
.db-macro .lb b { margin-left: auto; color: #2A2620; font-size: 11px; }
.db-macro .bar {
  height: 6px; border-radius: 99px;
  background: rgba(184, 134, 59, 0.1); margin-top: 4px;
  overflow: hidden;
}
.db-macro .bar i {
  display: block; height: 100%; border-radius: 99px;
  transition: width 0.6s cubic-bezier(0.34, 1.3, 0.64, 1);
}

.fa-error { margin-top: 10px; font-size: 11px; color: #C0522F; text-align: center; }
.fa-actions {
  display: flex; gap: 10px; justify-content: flex-end;
  margin-top: 14px; padding-top: 12px;
  border-top: 1px dashed rgba(184, 134, 59, 0.2);
}
.fa-note { margin-top: 10px; font-size: 10px; color: rgba(42, 38, 32, 0.4); line-height: 1.6; }

/* ---- 通用 ---- */
.ghost-add {
  display: inline-flex; align-items: center; gap: 6px;
  border: 1px dashed rgba(184, 134, 59, 0.4);
  color: #B8863B; background: none; cursor: pointer;
  font-size: 12px; font-weight: 600; letter-spacing: 0.05em;
  border-radius: 10px; padding: 8px 14px; transition: 0.25s;
  font-family: inherit;
}
.ghost-add:hover { background: rgba(217, 162, 74, 0.1); border-color: #B8863B; }
.confirm-btn {
  padding: 8px 20px; border-radius: 10px; border: none; cursor: pointer;
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; font-size: 12.5px; font-weight: 600; letter-spacing: 0.04em;
  transition: 0.25s; font-family: inherit;
}
.confirm-btn:hover { opacity: 0.9; transform: translateY(-1px); }
.confirm-btn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }

/* ---- 响应式 ---- */
@media (max-width: 1000px) {
  .db-blocks { grid-template-columns: 1fr; }
  .fa-span2 { grid-column: span 1; }
  .fa-divider { grid-column: span 1; }
}
</style>
