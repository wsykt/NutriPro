<template>
  <div class="feature-hub min-h-full relative">
    <!-- ===== 组合 E · 深壳中继 + 浅芯概览 ===== -->
    <div v-if="currentCategory" class="hc-wrap relative z-10">

      <!-- ===== 深壳星轨带（上半 · 承接首页深壳 Hero） ===== -->
      <div class="hc-band" ref="bandRef">
        <div class="hc-glow hc-glow--1" aria-hidden="true"></div>
        <div class="hc-glow hc-glow--2" aria-hidden="true"></div>

        <!-- 星座面包屑 -->
        <div class="hc-crumbs" data-anim>
          <button class="hc-crumb-home" @click="go('/dashboard/home')">
            <LayoutGrid class="hc-crumb-ic" :stroke-width="1.75" />
            <span>首页</span>
          </button>
          <ChevronRight class="hc-crumb-sep" />
          <b>{{ currentCategory.title }}</b>
        </div>

        <!-- 星轨带：核心恒星 + 功能站点 -->
        <div class="hc-const" data-anim>
          <svg class="hc-line" viewBox="0 0 1200 128" preserveAspectRatio="none" aria-hidden="true">
            <path d="M 150 64 C 300 8, 440 8, 560 64 S 830 120, 960 64 S 1130 10, 1200 64" />
          </svg>

          <!-- 核心恒星（当前分组） -->
          <div class="hc-core-wrap">
            <div class="hc-core">
              <div class="hc-star">
                <component :is="currentCategory.icon" class="hc-star-ic" :stroke-width="1.75" />
              </div>
              <div class="hc-core-tt">
                <b class="serif">{{ currentCategory.title }}</b>
                <span>{{ enName }}</span>
              </div>
            </div>
          </div>

          <!-- 功能站点（替代原入口卡片） -->
          <div
            v-for="(f, i) in currentCategory.items"
            :key="f.to"
            class="hc-station-wrap"
            :style="{ left: stationLeft(i) + '%', ...stationFloatStyle(i) }"
          >
            <div class="hc-station-float">
              <button class="hc-station" @click="go(f.to)" :aria-label="f.name">
                <component :is="f.icon" class="hc-station-ic" :stroke-width="1.75" />
                <span class="nm">{{ f.name }}</span>
                <span class="ds">{{ f.desc }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 浅芯概览工作区（下半） ===== -->
      <div class="hc-paper" ref="paperRef">
        <div class="sec-t" data-anim>分组实时概览</div>

        <div class="hc-grid4">
          <button class="hc-cell" data-anim @click="go('/dashboard/food-input')">
            <span class="hc-cell-label"><Flame class="w-3.5 h-3.5" style="color:#E07A3F" /> 今日摄入</span>
            <b class="serif">{{ overview.todayKcal ?? '—' }}<i v-if="overview.todayKcal != null">kcal</i></b>
            <span class="hc-cell-sub">{{ overview.todayKcal == null ? '今日暂无饮食记录' : '已记录三餐数据' }}</span>
          </button>
          <button class="hc-cell" data-anim @click="go('/dashboard/health-archive?tab=metrics')">
            <span class="hc-cell-label"><Activity class="w-3.5 h-3.5" style="color:#B8863B" /> BMI</span>
            <b class="serif" :class="bmiClass">{{ overview.bmi ?? '—' }}</b>
            <span class="hc-cell-sub">{{ overview.bmiText }}</span>
          </button>
          <button class="hc-cell" data-anim @click="go('/dashboard/health-archive?tab=metrics')">
            <span class="hc-cell-label"><Scale class="w-3.5 h-3.5" style="color:#6C8FBE" /> 当前体重</span>
            <b class="serif">{{ overview.weight ?? '—' }}<i v-if="overview.weight">kg</i></b>
            <span class="hc-cell-sub">{{ overview.bmr ? '基础代谢 BMR ' + overview.bmr + ' kcal' : '暂无代谢数据' }}</span>
          </button>
          <button class="hc-cell" data-anim @click="go('/dashboard/health-report')">
            <span class="hc-cell-label"><FileText class="w-3.5 h-3.5" style="color:#B8863B" /> 健康报告</span>
            <b class="serif">{{ overview.reportCount }}<i>份</i></b>
            <span class="hc-cell-sub">周报/月报累计</span>
          </button>
        </div>

        <div class="hc-row" data-anim>
          <Sparkles class="hc-row-ic" :stroke-width="1.75" />
          <span>{{ snapshotText }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watchEffect } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { gsap } from 'gsap'
import { api } from '@/api'
import {
  User, Users, Activity, FileText, UsersRound,
  Utensils, PlusCircle, PieChart, Search,
  HeartPulse, BarChart3, Dumbbell,
  BookOpen, Newspaper, MessageCircle, ClipboardList, ChefHat,
  Flame, Scale, LayoutGrid, ChevronRight, Sparkles
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const today = new Date().toISOString().slice(0, 10)

// 当前分组（来自 URL ?group=xxx）；无分组时回首页（首页轨道即一级导航）
const currentGroup = computed(() => (route.query.group as string) || '')
const allGroups = [
  { key: 'user', title: '用户中心', en: 'USER HUB', icon: Users, items: [
    { to: '/dashboard/profile', icon: User, name: '个人中心', desc: '资料 · 身高体重 · 人群设定' },
    { to: '/dashboard/health-archive?tab=metrics', icon: Activity, name: '指标历史', desc: '体重 / BMI 趋势与预测' },
    { to: '/dashboard/health-archive?tab=records', icon: FileText, name: '健康档案', desc: '历次健康快照回顾' },
    { to: '/dashboard/family', icon: UsersRound, name: '亲属管理', desc: '监护关系与代操作' },
  ]},
  { key: 'diet', title: '饮食管理', en: 'DIET HUB', icon: Utensils, items: [
    { to: '/dashboard/food-input', icon: Utensils, name: '饮食记录', desc: '按餐次记录三餐与加餐' },
    { to: '/dashboard/nutrition', icon: PieChart, name: '营养分析', desc: '热量 / 蛋白质 / 微量元素' },
    { to: '/dashboard/food-input?tab=search', icon: Search, name: '食物搜索', desc: '查询营养成分与 GI 值' },
    { to: '/dashboard/food-input?tab=add', icon: PlusCircle, name: '添加食材', desc: '录入新食材到库' },
    { to: '/dashboard/family?tab=input', icon: Users, name: '亲属代录', desc: '替家人记录饮食' },
  ]},
  { key: 'health', title: '健康监测', en: 'HEALTH HUB', icon: HeartPulse, items: [
    { to: '/dashboard/health-report', icon: BarChart3, name: '健康报告', desc: '周报 / 月报健康回顾' },
    { to: '/dashboard/muscle-chart?tab=chart', icon: Dumbbell, name: '运动管理', desc: '训练记录与围度变化' },
    { to: '/dashboard/health-archive', icon: FileText, name: '健康档案', desc: '身体指标与健康记录' },
  ]},
  { key: 'knowledge', title: '知识中心', en: 'KNOWLEDGE HUB', icon: BookOpen, items: [
    { to: '/dashboard/articles', icon: Newspaper, name: '科普文章', desc: '循证营养学主题阅读' },
    { to: '/dashboard/ai-consult', icon: MessageCircle, name: 'AI 咨询', desc: '饮食 / 慢病 / 运动问答' },
    { to: '/dashboard/muscle-chart?tab=training', icon: HeartPulse, name: '训练计划', desc: '个性化运动方案' },
  ]},
  { key: 'recipe', title: '菜谱美食', en: 'RECIPE HUB', icon: ChefHat, items: [
    { to: '/dashboard/recipe-library', icon: ChefHat, name: '菜谱库', desc: '根据档案推荐菜谱' },
    { to: '/dashboard/profile?tab=dietary', icon: ClipboardList, name: '饮食档案', desc: '过敏 / 忌口 / 口味偏好' },
  ]},
]
const currentCategory = computed(() => allGroups.find(x => x.key === currentGroup.value) || null)
const enName = computed(() => currentCategory.value?.en || '')

// 无分组或分组非法 → 回首页（首页恒星轨道即一级导航，中转页只承担分组内直达）
watchEffect(() => {
  if (!currentCategory.value) router.replace({ path: '/dashboard/home' })
})

// 站点沿星轨分布（自核心恒星向右延伸 28% ~ 92%；双站点缩短延伸距离）
function stationLeft(i: number): number {
  const n = currentCategory.value?.items.length || 1
  if (n === 1) return 60
  // 仅 2 个站点时紧随核心恒星自然向右延伸，不铺满全轨
  if (n === 2) return Math.round(28 + i * 20)
  return Math.round(28 + i * (64 / (n - 1)))
}
// 每颗站点各自漂浮节奏（周期/相位错开）
function stationFloatStyle(i: number): Record<string, string> {
  return {
    animationDuration: (4.6 + (i % 4) * 0.45) + 's',
    animationDelay: -(i * 0.9) + 's'
  }
}

function go(to: string) { router.push(to) }

// ===== 分组实时概览（真实数据） =====
const overview = ref<{ todayKcal: number | null; bmi: number | null; bmiText: string; weight: number | null; bmr: number | null; reportCount: number }>({
  todayKcal: null, bmi: null, bmiText: '—', weight: null, bmr: null, reportCount: 0
})
const bmiClass = computed(() => {
  const b = overview.value.bmi
  if (b == null) return ''
  if (b < 18.5) return 'is-warn'
  if (b < 24) return 'is-good'
  return 'is-bad'
})

const snapshotText = computed(() => {
  const o = overview.value
  if (o.weight == null && o.bmi == null && o.bmr == null) {
    return '暂无健康快照 · 可在「健康档案 → 身体指标」中记录一条'
  }
  const parts: string[] = []
  if (o.weight != null) parts.push(`体重 ${o.weight}kg`)
  if (o.bmi != null) parts.push(`BMI ${o.bmi}`)
  if (o.bmr != null) parts.push(`BMR ${o.bmr} kcal`)
  const dateText = new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })
  return `最近快照 · ${dateText}：${parts.join('，')}`
})

// ===== 入场动效（深壳先入 → 站点亮起 → 浅芯浮起） =====
const bandRef = ref<HTMLElement | null>(null)
const paperRef = ref<HTMLElement | null>(null)

function animateEntrance() {
  const band = bandRef.value
  const paper = paperRef.value
  if (band) {
    gsap.fromTo(band.querySelectorAll('[data-anim]'),
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.7, stagger: 0.1, ease: 'power3.out' })
    // 站点沿星轨依次点亮
    gsap.fromTo(band.querySelectorAll('.hc-station-wrap'),
      { scale: 0, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.5, stagger: 0.08, delay: 0.3, ease: 'back.out(1.7)', clearProps: 'opacity,transform' })
  }
  if (paper) {
    gsap.fromTo(paper.querySelectorAll('[data-anim]'),
      { opacity: 0, y: 26 },
      { opacity: 1, y: 0, duration: 0.75, stagger: 0.08, delay: 0.3, ease: 'power3.out' })
  }
}

onMounted(async () => {
  animateEntrance()
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
      const items = m?.items ?? m?.foods ?? []
      for (const it of items) {
        // 与首页一致：后端 item 的 calorie/protein 等均为「每100克」值，需按实际食用重量 eatWeight 折算
        const factor = Number(it?.eatWeight ?? it?.quantity ?? 0) / 100
        const c = Number(it?.calorie ?? it?.calories ?? 0) * factor
        kcal += c; if (c) has = true
      }
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
.hc-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ========== 深壳星轨带 ========== */
.hc-band {
  position: relative;
  padding: 20px 30px 14px;
  border-radius: 24px;
  overflow: hidden;
  isolation: isolate;
  background:
    radial-gradient(circle at 12% 24%, rgba(232, 185, 115, 0.1) 0%, transparent 44%),
    radial-gradient(circle at 88% 88%, rgba(179, 107, 42, 0.08) 0%, transparent 46%),
    linear-gradient(180deg, #14110C 0%, #0E0C0A 100%);
  border: 1px solid rgba(232, 185, 115, 0.14);
  color: #F6EAD6;
}
.hc-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(50px);
  pointer-events: none;
  z-index: 0;
}
.hc-glow--1 {
  width: 220px; height: 220px;
  right: -60px; top: -110px;
  background: rgba(232, 185, 115, 0.12);
  animation: hcGlowFloat 9s ease-in-out infinite alternate;
}
.hc-glow--2 {
  width: 180px; height: 180px;
  left: -70px; bottom: -100px;
  background: rgba(179, 107, 42, 0.1);
  animation: hcGlowFloat 11s ease-in-out infinite alternate-reverse;
}
@keyframes hcGlowFloat {
  from { transform: translate3d(0, 0, 0) scale(1); }
  to   { transform: translate3d(18px, 12px, 0) scale(1.12); }
}

/* ---- 星座面包屑 ---- */
.hc-crumbs {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #8C7A5E;
  letter-spacing: 0.08em;
}
.hc-crumb-home {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #8C7A5E;
  letter-spacing: 0.08em;
  transition: color 0.25s ease;
}
.hc-crumb-home:hover { color: #E8B973; }
.hc-crumb-ic { width: 13px; height: 13px; }
.hc-crumb-sep { width: 11px; height: 11px; color: rgba(140, 122, 94, 0.6); }
.hc-crumbs b {
  color: #E8B973;
  font-weight: 600;
  font-size: 12px;
}

/* ---- 星轨带 ---- */
.hc-const {
  position: relative;
  z-index: 1;
  height: 128px;
  margin-top: 10px;
}
.hc-line {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}
.hc-line path {
  fill: none;
  stroke: rgba(217, 162, 74, 0.35);
  stroke-width: 1.2;
  stroke-dasharray: 5 6;
  vector-effect: non-scaling-stroke;
}

/* ---- 核心恒星 ---- */
.hc-core-wrap {
  position: absolute;
  left: 6px;
  top: 50%;
  margin-top: -32px;
  z-index: 2;
}
.hc-core {
  display: flex;
  align-items: center;
  gap: 12px;
  animation: hcFloat 6.4s ease-in-out infinite alternate;
  animation-delay: -0.6s;
}
.hc-star {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(232, 185, 115, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #E8B973;
  box-shadow: 0 0 30px rgba(217, 162, 74, 0.4);
  animation: hcBreath 3.2s ease-in-out infinite;
}
@keyframes hcBreath {
  0%, 100% { box-shadow: 0 0 22px rgba(217, 162, 74, 0.32); }
  50% { box-shadow: 0 0 42px rgba(217, 162, 74, 0.55); }
}
.hc-star-ic { width: 24px; height: 24px; }
.hc-core-tt b {
  display: block;
  font-size: 15px;
  color: #F6EAD6;
  font-weight: 700;
  letter-spacing: 0.08em;
}
.hc-core-tt span {
  display: block;
  margin-top: 3px;
  font-size: 10px;
  color: #9A8A6C;
  letter-spacing: 0.14em;
}

/* ---- 功能站点（替代原入口卡片） ---- */
.hc-station-wrap {
  position: absolute;
  top: 50%;
  width: 50px;
  height: 50px;
  margin: -25px 0 0 -25px;
  z-index: 3;
}
.hc-station-float {
  width: 100%;
  height: 100%;
  animation: hcFloat 4.6s ease-in-out infinite alternate;
}
@keyframes hcFloat {
  from { transform: translateY(4px); }
  to   { transform: translateY(-8px); }
}
.hc-station {
  position: relative;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  cursor: pointer;
  background: rgba(24, 19, 12, 0.95);
  border: 1px solid rgba(217, 162, 74, 0.45);
  color: #E8B973;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.5, 0.5, 1), border-color 0.3s ease, box-shadow 0.3s ease;
}
.hc-station-ic { width: 18px; height: 18px; }
.hc-station .nm {
  position: absolute;
  top: -30px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10.5px;
  color: #F0E2C4;
  white-space: nowrap;
  letter-spacing: 0.06em;
  opacity: 0.75;
  transition: opacity 0.3s ease, color 0.3s ease;
}
.hc-station .ds {
  position: absolute;
  top: calc(100% + 12px);
  left: 50%;
  transform: translateX(-50%) translateY(4px);
  white-space: nowrap;
  font-size: 10px;
  color: #F6EAD6;
  background: rgba(24, 19, 12, 0.95);
  border: 1px solid rgba(217, 162, 74, 0.4);
  padding: 3px 10px;
  border-radius: 999px;
  opacity: 0;
  transition: opacity 0.28s ease, transform 0.28s ease;
  pointer-events: none;
}
.hc-station:hover {
  transform: scale(1.14);
  border-color: #E8B973;
  box-shadow: 0 0 0 6px rgba(217, 162, 74, 0.14), 0 12px 30px rgba(217, 162, 74, 0.32);
}
.hc-station:hover .ds {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
.hc-station:hover .nm {
  opacity: 1;
  color: #E8B973;
}

/* ========== 浅芯概览工作区 ========== */
.hc-paper {
  position: relative;
  background:
    radial-gradient(circle at 18% 0%, rgba(184, 134, 59, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 86% 100%, rgba(201, 143, 62, 0.06) 0%, transparent 44%),
    linear-gradient(180deg, #F8F4EA 0%, #F2EBDC 100%);
  border: 1px solid rgba(232, 185, 115, 0.24);
  border-radius: 24px;
  padding: 20px 24px 24px;
  box-shadow: 0 30px 60px -34px rgba(90, 70, 40, 0.28);
}
.sec-t {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #2A2620;
  letter-spacing: 0.02em;
}
.sec-t::before {
  content: '';
  width: 3px;
  height: 14px;
  border-radius: 99px;
  background: linear-gradient(180deg, #E8B973, #B8863B);
}

/* ---- 概览 4 格 ---- */
.hc-grid4 {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}
.hc-cell {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  text-align: left;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(184, 134, 59, 0.16);
  border-radius: 16px;
  padding: 14px 18px;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s ease, border-color 0.35s ease;
}
.hc-cell:hover {
  transform: translateY(-3px);
  border-color: rgba(184, 134, 59, 0.45);
  box-shadow: 0 20px 38px -20px rgba(90, 70, 40, 0.28);
}
.hc-cell-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: rgba(42, 38, 32, 0.55);
}
.hc-cell b {
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 900;
  color: #2A2620;
  line-height: 1.2;
}
.hc-cell b i {
  font-style: normal;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 11px;
  font-weight: 600;
  color: rgba(42, 38, 32, 0.45);
  margin-left: 5px;
}
.hc-cell b.is-good { color: #4E8D6E; }
.hc-cell b.is-warn { color: #B8863B; }
.hc-cell b.is-bad { color: #B36B2A; }
.hc-cell-sub {
  font-size: 11px;
  color: rgba(42, 38, 32, 0.45);
}

/* ---- 最近快照行 ---- */
.hc-row {
  margin-top: 14px;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(184, 134, 59, 0.14);
  border-radius: 14px;
  padding: 12px 18px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 11.5px;
  color: #6E6350;
}
.hc-row-ic {
  width: 13px;
  height: 13px;
  color: #B8863B;
  flex-shrink: 0;
}

/* ---- 响应式 ---- */
@media (max-width: 1100px) {
  .hc-grid4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .hc-grid4 { grid-template-columns: 1fr; }
}
</style>
