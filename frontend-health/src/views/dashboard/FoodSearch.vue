<template>
  <div class="diet-page">
    <!-- ===== 深壳星轨带（分类星球上下浮动） ===== -->
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
            <span class="crumb-node hot"><span class="nd"><Search :size="13" /></span>食物查询</span>
          </span>
        </div>
        <div class="db-top-right">
          <span class="db-date"><BookOpen :size="12" />星表收录 <b>{{ allFoods.length }}</b> 种</span>
        </div>
      </div>

      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 104" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 52 C 300 8, 440 8, 560 52 S 830 96, 960 52 S 1130 8, 1200 52" />
        </svg>

        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><Search :size="19" /></span>
            <span class="tt"><b>食物星表</b><span>FOOD ATLAS</span></span>
          </div>
        </div>

        <div
          v-for="(c, i) in orbitCategories"
          :key="c.name"
          class="db-station-wrap"
          :style="{ left: stationLeft(i, orbitCategories.length) + '%' }"
        >
          <div class="db-station-float" :style="floatStyle(i)">
            <button
              class="db-station"
              :class="{ now: activeCategory === c.name }"
              :aria-label="c.name"
              @click="pickCategory(c.name)"
            >
              <component :is="c.icon" :size="15" />
              <span class="nm">{{ c.name }}</span>
              <span class="ds">{{ c.count }} 种食材 · 点击筛选</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区（7:5） ===== -->
    <div class="db-paper" ref="paperRef">
      <div class="db-head" data-anim>
        <div class="sec-t">营养速查 · 每一种食材都是一颗星</div>
        <div class="db-pills">
          <span class="pill"><Search :size="11" />共 <b>{{ allFoods.length }}</b> 种</span>
          <span class="pill">当前显示 <b>{{ filteredFoods.length }}</b> 种</span>
        </div>
      </div>

      <div class="db-blocks">
        <!-- 左：搜索 + 分类 chips + 星表列表 -->
        <div class="db-block main" data-anim ref="mainRef">
          <div class="fs-search-row">
            <div class="fs-search-box">
              <Search :size="14" class="fs-search-ic" />
              <input
                v-model="keyword"
                type="text"
                placeholder="搜索食物名（如 米饭、鸡蛋、苹果）"
              />
              <button v-if="keyword" class="fs-clear" @click="keyword = ''"><X :size="12" /></button>
            </div>
            <button class="ghost-add solid" :disabled="foodLoading" @click="loadFoods">
              <RefreshCw :size="13" :class="{ spinning: foodLoading }" />刷新星表
            </button>
          </div>

          <div class="fs-chips">
            <button
              v-for="c in categories" :key="c"
              class="chip" :class="{ on: activeCategory === c }"
              @click="pickCategory(c)"
            >{{ c }}</button>
          </div>

          <div v-if="foodLoading" class="db-empty-msg">星表检索中...</div>
          <div v-else-if="filteredFoods.length === 0" class="db-empty-msg">
            没有匹配的食材，换个关键词或分类试试
          </div>

          <div v-else class="fs-list">
            <div
              v-for="f in filteredFoods" :key="f.foodId"
              class="fs-row" :class="{ picked: selectedFood && selectedFood.foodId === f.foodId }"
              @click="pickFood(f)"
            >
              <span class="fs-badge">{{ (f.foodName || '·').slice(0, 1) }}</span>
              <span class="fs-info">
                <b>{{ f.foodName }} <em>{{ f.foodCategory || '-' }}</em></b>
                <span>蛋白 {{ num(f.protein) }} · 脂肪 {{ num(f.fat) }} · 碳水 {{ num(f.carb) }} · GI {{ f.giValue ?? '-' }}</span>
              </span>
              <span class="k">{{ num(f.calorie) }} <i>kcal/100g</i></span>
            </div>
          </div>
        </div>

        <!-- 右：选中食材的星卡 -->
        <div class="db-block side" data-anim>
          <template v-if="selectedFood">
            <div class="db-side-head">
              <b>{{ selectedFood.foodName }}</b>
              <span>{{ selectedFood.foodCategory || '-' }}</span>
            </div>
            <div class="fs-hero-kcal">
              <b>{{ num(selectedFood.calorie) }}</b>
              <span>kcal / 100g</span>
            </div>

            <div class="fs-gi-line">
              <span class="fs-gi-chip" :class="giLevel.cls">GI {{ selectedFood.giValue ?? '-' }} · {{ giLevel.label }}</span>
              <span class="fs-gi-note">血糖生成指数</span>
            </div>

            <div class="db-macros">
              <div v-for="m in selectedMacros" :key="m.key" class="db-macro">
                <div class="lb"><i :style="{ background: m.color }"></i>{{ m.key }}<b>{{ num(m.g) }} g</b></div>
                <div class="bar"><i :style="{ width: m.pct + '%', background: m.color }"></i></div>
              </div>
            </div>

            <div class="fs-minis">
              <div class="fs-mini"><span>钙</span><b>{{ selectedFood.calcium ?? '-' }} <i>mg</i></b></div>
              <div class="fs-mini"><span>DHA</span><b>{{ selectedFood.dha ?? '-' }} <i>mg</i></b></div>
              <div class="fs-mini"><span>叶酸</span><b>{{ selectedFood.folicAcid ?? '-' }} <i>μg</i></b></div>
              <div class="fs-mini"><span>膳食纤维</span><b>{{ selectedFood.dietFiber ?? '-' }} <i>g</i></b></div>
            </div>
          </template>
          <template v-else>
            <div class="fs-side-empty">
              <span class="fs-side-orb"><Sparkles :size="22" /></span>
              <b>营养星卡</b>
              <p>在左侧点击任意食材，<br />这里会亮起它的营养画像</p>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import {
  LayoutGrid, Utensils, Search, X, RefreshCw, BookOpen, Sparkles,
  Wheat, Beef, Fish, Carrot, Apple, Milk, Droplet, Layers
} from 'lucide-vue-next'
import { FOOD_CATEGORY_ORDER } from '@/constants'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'

const router = useRouter()
const userStore = useUserStore()

const keyword = ref('')
const activeCategory = ref('全部')
const foodLoading = ref(false)
const allFoods = ref<any[]>([])
const selectedFood = ref<any | null>(null)

function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'diet' } }) }

// ---- 分类 → 星球图标 ----
const CATEGORY_ICONS: Record<string, any> = {
  '主食': Wheat,
  '肉蛋类': Beef,
  '水产': Fish,
  '蔬菜': Carrot,
  '水果': Apple,
  '豆制品': Layers,
  '奶类': Milk,
  '奶制品': Milk,
  '油脂类': Droplet,
  '油脂': Droplet
}
function iconOf(name: string): any {
  return CATEGORY_ICONS[name] || Layers
}

const categories = computed(() => {
  const cs = new Set<string>()
  allFoods.value.forEach((f: any) => {
    if (f && f.foodCategory) cs.add(f.foodCategory)
  })
  return [
    '全部',
    ...FOOD_CATEGORY_ORDER.filter((x: string) => cs.has(x)),
    ...Array.from(cs).filter((x: string) => (FOOD_CATEGORY_ORDER as readonly string[]).indexOf(x) === -1)
  ]
})

// ---- 星轨星球：取食材数量最多的前 5 个分类 ----
const orbitCategories = computed(() => {
  const countMap = new Map<string, number>()
  allFoods.value.forEach((f: any) => {
    const c = f && f.foodCategory
    if (c) countMap.set(c, (countMap.get(c) || 0) + 1)
  })
  return Array.from(countMap.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name, count]) => ({ name, count, icon: iconOf(name) }))
})

function pickCategory(name: string) {
  activeCategory.value = activeCategory.value === name ? '全部' : name
}

// ---- 星轨站点：横向分布 + 各自漂浮节奏 ----
function stationLeft(i: number, total: number): number {
  if (total <= 1) return 64
  return 34 + i * (60 / (total - 1))
}
function floatStyle(i: number): Record<string, string> {
  return {
    animationDuration: (4.6 + (i % 4) * 0.45) + 's',
    animationDelay: -(i * 0.9) + 's'
  }
}

// ---- 载入食物库 ----
async function loadFoods() {
  foodLoading.value = true
  try {
    const data = await api.food.list()
    allFoods.value = Array.isArray(data) ? data : []
  } catch (e: any) {
    console.warn('加载食物列表失败', e)
  } finally {
    foodLoading.value = false
  }
}

// ---- 分类 + 搜索 + 糖尿病人按 GI 升序 ----
const isDiabetes = computed(() => {
  const c = userStore.user?.crowdType || userStore.user?.crowd_type || ''
  return String(c).indexOf('糖尿') >= 0
})

const filteredFoods = computed(() => {
  let list = allFoods.value
  if (activeCategory.value !== '全部') {
    list = list.filter((f: any) => f && f.foodCategory === activeCategory.value)
  }
  const kw = keyword.value.trim().toLowerCase()
  if (kw) {
    list = list.filter((f: any) => f.foodName && String(f.foodName).toLowerCase().indexOf(kw) >= 0)
  }
  const sorted = [...list]
  if (isDiabetes.value) {
    sorted.sort((a: any, b: any) => {
      const ga = Number(a.giValue) || 9999
      const gb = Number(b.giValue) || 9999
      return ga - gb
    })
  }
  return sorted
})

function num(v: any): string {
  const n = Number(v)
  if (!Number.isFinite(n)) return '-'
  return String(Math.round(n * 10) / 10)
}

function pickFood(f: any) {
  selectedFood.value = f
  nextTick(() => {
    if (sideRef.value) {
      gsap.fromTo(sideRef.value, { opacity: 0.4, y: 8 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' })
    }
  })
}

// ---- 星卡：三色宏量条（蛋白蓝 / 脂肪黄 / 碳水绿） + GI 分级 ----
const selectedMacros = computed(() => {
  const f = selectedFood.value
  if (!f) return []
  const p = Number(f.protein) || 0
  const ft = Number(f.fat) || 0
  const c = Number(f.carb) || 0
  const total = p + ft + c
  const mk = (key: string, g: number, color: string) => ({
    key, g, color,
    pct: total > 0 ? Math.max(g > 0 ? 4 : 0, Math.round((g / total) * 100)) : 0
  })
  return [mk('蛋白质', p, '#6C8FBE'), mk('脂肪', ft, '#D9A24A'), mk('碳水', c, '#7FAE8E')]
})

const giLevel = computed(() => {
  const gi = Number(selectedFood.value?.giValue)
  if (!Number.isFinite(gi) || gi <= 0) return { cls: 'lv-none', label: '未标注' }
  if (gi <= 55) return { cls: 'lv-low', label: '低 GI' }
  if (gi <= 70) return { cls: 'lv-mid', label: '中 GI' }
  return { cls: 'lv-high', label: '高 GI' }
})

// ===== 入场动效（面包屑点亮 → 星球弹出 → 浅芯浮起） =====
const bandRef = ref<HTMLElement | null>(null)
const paperRef = ref<HTMLElement | null>(null)
const sideRef = ref<HTMLElement | null>(null)
const mainRef = ref<HTMLElement | null>(null)

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

// 切换分类时，主工作卡轻微浮起过渡
watch(activeCategory, () => {
  nextTick(() => {
    if (mainRef.value) {
      gsap.fromTo(mainRef.value, { opacity: 0.35, y: 10 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' })
    }
  })
})

onMounted(async () => {
  animateEntrance()
  userStore.init()
  await loadFoods()
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

/* ---- 顶行：星座面包屑 + 收录数 ---- */
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

/* ---- 核心恒星（上下浮动） ---- */
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

/* ---- 分类星球（wrapper 定位 / 内层上下浮动 / 按钮悬停缩放） ---- */
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
.db-station.now {
  border-color: #E8B973;
  box-shadow: 0 0 0 6px rgba(217, 162, 74, 0.14), 0 0 22px rgba(217, 162, 74, 0.4);
}
.db-station.now .nm { opacity: 1; color: #E8B973; font-weight: 700; }

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

/* ---- 左：搜索行 + chips ---- */
.fs-search-row {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.fs-search-box {
  position: relative; flex: 1; min-width: 220px;
}
.fs-search-ic {
  position: absolute; left: 11px; top: 50%; transform: translateY(-50%);
  color: rgba(42, 38, 32, 0.35); pointer-events: none;
}
.fs-search-box input {
  width: 100%; padding: 8px 32px 8px 32px;
  border-radius: 10px; border: 1px solid rgba(184, 134, 59, 0.25);
  background: #fff; font-size: 12.5px; color: #2A2620; outline: none;
  font-family: inherit; transition: border-color 0.25s ease;
}
.fs-search-box input:focus { border-color: #B8863B; }
.fs-clear {
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  width: 20px; height: 20px; border-radius: 50%;
  border: none; background: rgba(184, 134, 59, 0.12); color: #8C7A5E;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: 0.2s;
}
.fs-clear:hover { background: rgba(184, 134, 59, 0.25); color: #B8863B; }
.fs-chips {
  display: flex; flex-wrap: wrap; gap: 7px;
  margin-top: 12px;
}
.chip {
  font-size: 11px; color: #6E6350;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(184, 134, 59, 0.2);
  padding: 4px 12px; border-radius: 999px;
  cursor: pointer; transition: 0.25s; font-family: inherit;
}
.chip:hover { border-color: #B8863B; color: #B8863B; background: rgba(217, 162, 74, 0.08); }
.chip.on {
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; border-color: transparent; font-weight: 600;
}

/* ---- 星表列表 ---- */
.db-empty-msg {
  margin-top: 14px;
  border: 1px dashed rgba(184, 134, 59, 0.35);
  border-radius: 12px; padding: 26px 14px;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  font-size: 12px; color: #8C7A5E;
}
.fs-list {
  margin-top: 12px;
  max-height: 380px; overflow-y: auto;
  display: flex; flex-direction: column;
}
.fs-list::-webkit-scrollbar { width: 8px; }
.fs-list::-webkit-scrollbar-track { background: rgba(184, 134, 59, 0.08); border-radius: 4px; }
.fs-list::-webkit-scrollbar-thumb { background: rgba(184, 134, 59, 0.4); border-radius: 4px; }
.fs-list::-webkit-scrollbar-thumb:hover { background: rgba(150, 100, 40, 0.6); }
.fs-row {
  display: flex; align-items: center; gap: 11px;
  padding: 9px 8px; border-radius: 10px;
  cursor: pointer; transition: background-color 0.2s ease, box-shadow 0.2s ease;
}
.fs-row:hover { background: rgba(217, 162, 74, 0.09); }
.fs-row.picked {
  background: linear-gradient(135deg, rgba(232, 185, 115, 0.2), rgba(184, 134, 59, 0.12));
  box-shadow: inset 0 0 0 1px rgba(184, 134, 59, 0.3);
}
.fs-badge {
  width: 30px; height: 30px; border-radius: 9px; flex-shrink: 0;
  background: rgba(184, 134, 59, 0.12); color: #B8863B;
  font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.fs-info { min-width: 0; }
.fs-info b {
  display: block; font-size: 12.5px; color: #2A2620; font-weight: 700;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.fs-info b em {
  font-style: normal; font-weight: 500;
  color: rgba(42, 38, 32, 0.45); font-size: 10.5px; margin-left: 4px;
}
.fs-info > span {
  display: block; margin-top: 1px;
  font-size: 10.5px; color: rgba(42, 38, 32, 0.5);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.fs-row .k {
  margin-left: auto; flex-shrink: 0; text-align: right;
  font-family: 'Noto Serif SC', serif;
  font-size: 14px; font-weight: 900; color: #B8863B;
}
.fs-row .k i {
  font-style: normal; font-family: inherit;
  font-size: 9px; font-weight: 500; color: rgba(42, 38, 32, 0.4);
  margin-left: 2px;
}

/* ---- 右：营养星卡 ---- */
.db-side-head {
  display: flex; align-items: baseline; gap: 8px;
}
.db-side-head b { font-size: 13px; color: #2A2620; font-weight: 700; }
.db-side-head span { font-size: 10.5px; color: rgba(42, 38, 32, 0.45); }
.fs-hero-kcal {
  margin-top: 10px;
  display: flex; align-items: baseline; gap: 6px;
}
.fs-hero-kcal b {
  font-family: 'Noto Serif SC', serif;
  font-size: 34px; font-weight: 900; color: #B8863B;
  line-height: 1;
}
.fs-hero-kcal span { font-size: 10.5px; color: rgba(42, 38, 32, 0.45); letter-spacing: 0.04em; }
.fs-gi-line {
  display: flex; align-items: center; gap: 8px;
  margin-top: 10px;
}
.fs-gi-chip {
  font-size: 10.5px; font-weight: 700;
  padding: 3px 10px; border-radius: 999px;
}
.fs-gi-chip.lv-low { background: rgba(127, 174, 142, 0.16); color: #2F7D5B; }
.fs-gi-chip.lv-mid { background: rgba(217, 162, 74, 0.16); color: #B8863B; }
.fs-gi-chip.lv-high { background: rgba(201, 110, 80, 0.14); color: #C0522F; }
.fs-gi-chip.lv-none { background: rgba(42, 38, 32, 0.08); color: rgba(42, 38, 32, 0.45); }
.fs-gi-note { font-size: 10px; color: rgba(42, 38, 32, 0.4); }

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

.fs-minis {
  margin-top: 14px; padding-top: 12px;
  border-top: 1px dashed rgba(184, 134, 59, 0.2);
  display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
}
.fs-mini {
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(184, 134, 59, 0.14);
  border-radius: 10px; padding: 8px 11px;
  display: flex; align-items: center; justify-content: space-between; gap: 6px;
}
.fs-mini span { font-size: 10.5px; color: rgba(42, 38, 32, 0.5); }
.fs-mini b { font-size: 12px; color: #2A2620; font-weight: 700; }
.fs-mini b i {
  font-style: normal; font-size: 9px; font-weight: 500;
  color: rgba(42, 38, 32, 0.4); margin-left: 1px;
}

/* ---- 空态星卡 ---- */
.fs-side-empty {
  height: 100%; min-height: 240px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; gap: 8px;
}
.fs-side-orb {
  width: 58px; height: 58px; border-radius: 50%;
  background: radial-gradient(circle at 34% 30%, rgba(232, 185, 115, 0.35), rgba(184, 134, 59, 0.12) 72%);
  border: 1px dashed rgba(184, 134, 59, 0.4);
  color: #B8863B;
  display: flex; align-items: center; justify-content: center;
  animation: dbFloat 4.6s ease-in-out infinite alternate;
}
.fs-side-empty b { font-size: 12.5px; color: #2A2620; font-weight: 700; }
.fs-side-empty p { font-size: 11px; color: rgba(42, 38, 32, 0.45); line-height: 1.7; }

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
.ghost-add.solid { border-style: solid; }
.ghost-add:disabled { opacity: 0.55; cursor: not-allowed; }
.spinning { animation: spin 0.9s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ---- 响应式 ---- */
@media (max-width: 1000px) {
  .db-blocks { grid-template-columns: 1fr; }
  .fs-info > span { display: none; }
}
</style>
