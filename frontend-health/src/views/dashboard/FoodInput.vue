<template>
  <div class="diet-page">
    <!-- ===== 深壳星轨带（四餐站点上下浮动） ===== -->
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
            <span class="crumb-node hot"><span class="nd"><ClipboardList :size="13" /></span>记录三餐</span>
          </span>
        </div>
        <div class="db-top-right">
          <label class="db-date">
            <Calendar :size="12" />
            <input v-model="form.date" type="date" />
          </label>
        </div>
      </div>

      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 104" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 52 C 300 8, 440 8, 560 52 S 830 96, 960 52 S 1130 8, 1200 52" />
        </svg>

        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><Utensils :size="19" /></span>
            <span class="tt"><b>饮食记录</b><span>DIET LOG</span></span>
          </div>
        </div>

        <div
          v-for="(meal, i) in meals"
          :key="meal.type"
          class="db-station-wrap"
          :style="{ left: stationLeft(i) + '%' }"
        >
          <div class="db-station-float" :style="floatStyle(i)">
            <button
              class="db-station"
              :class="{ now: currentMeal === meal.type }"
              @click="switchMeal(meal.type)"
              :aria-label="meal.label"
            >
              <component :is="meal.icon" :size="16" />
              <span class="nm">{{ meal.label }} · {{ mealTotalCalorie(meal.type) > 0 ? mealTotalCalorie(meal.type) : '待记录' }}</span>
              <span class="ds">{{ meal.time }} · 已记录 {{ mealItems(meal.type).length }} 项</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区（7:5） ===== -->
    <div class="db-paper" ref="paperRef">
      <div class="db-head" data-anim>
        <div class="sec-t">{{ currentMealLabel }}工作区</div>
        <div class="db-pills">
          <span class="pill"><Flame :size="11" />今日 <b>{{ totalCalories }}</b> kcal</span>
          <span class="pill">蛋白 <b>{{ totalProtein }}g</b></span>
          <span class="pill">脂肪 <b>{{ totalFat }}g</b></span>
          <span class="pill">碳水 <b>{{ totalCarbs }}g</b></span>
        </div>
      </div>

      <div class="db-blocks">
        <!-- 左：当前餐次明细 -->
        <div class="db-block main" data-anim ref="mainRef">
          <div class="db-block-head">
            <b>{{ currentMealLabel }}已记录 · {{ currentItems.length }} 项</b>
            <span class="db-block-kcal">{{ currentMealKcal }} kcal</span>
          </div>

          <div v-if="currentItems.length === 0" class="db-empty" @click="openAddDialog(currentMeal)">
            <Plus :size="14" />
            还没有记录，点这里添加
          </div>
          <div v-else class="db-items">
            <div v-for="(item, idx) in currentItems" :key="item.mealId + '-' + idx" class="db-item">
              <span class="nm">
                {{ item.foodName }}
                <em>{{ item.foodCategory }}</em>
              </span>
              <span class="meta">
                {{ item.eatWeight }} g · 蛋白 {{ roundOne(item.protein * item.eatWeight / 100) }} ·
                脂肪 {{ roundOne(item.fat * item.eatWeight / 100) }} ·
                碳水 {{ roundOne(item.carb * item.eatWeight / 100) }}
                <template v-if="item.giValue != null"> · GI {{ item.giValue }}</template>
              </span>
              <span class="k">{{ roundOne(item.calorie * item.eatWeight / 100) }} kcal</span>
              <button class="x" title="删除该餐" @click="handleDeleteMeal(item.mealId)"><X :size="11" /></button>
            </div>
          </div>

          <div class="db-foot">
            <button class="ghost-add" @click="openAddDialog(currentMeal)"><Plus :size="13" />添加食物</button>
            <button class="ghost-add solid" @click="toggleVoiceInput"><Mic :size="13" />语音报餐</button>
          </div>
          <div v-if="voiceParsing || voiceNote" class="voice-note" :class="{ busy: voiceParsing }">
            <template v-if="voiceParsing">语音识别并解析中…</template>
            <template v-else>{{ voiceNote }}</template>
          </div>
        </div>

        <!-- 右：今日小结 -->
        <div class="db-block side" data-anim>
          <div class="db-side-head">
            <b>今日小结</b>
            <span>{{ form.date }}</span>
          </div>
          <div class="db-macros">
            <div v-for="m in macroShares" :key="m.key" class="db-macro">
              <div class="lb"><i :style="{ background: m.color }"></i>{{ m.key }}<b>{{ m.g }} g · {{ m.pct }}%</b></div>
              <div class="bar"><i :style="{ width: m.pct + '%', background: m.color }"></i></div>
            </div>
          </div>
          <div class="db-dist">
            <div v-for="d in mealDist" :key="d.label" class="db-dist-row" :class="{ dim: d.kcal === 0 }">
              <span class="lb">{{ d.label }}</span>
              <div class="bar"><i :style="{ width: d.pct + '%' }"></i></div>
              <span class="k">{{ d.kcal > 0 ? d.kcal + ' kcal' : '待记录' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 语音报餐弹窗 ===== -->
    <teleport to="body">
      <div v-if="voiceActive" class="voice-mask" @click.self="dismissVoice">
        <div class="voice-dialog" :class="{ rec: isRecording }">
          <div class="vd-head">
            <b>语音报餐</b>
            <span class="vd-sub">说出食物即可自动添加</span>
            <button class="vd-close" @click="onCloseVoice" title="关闭"><X :size="16" /></button>
          </div>

          <button class="vd-mic" :class="{ on: isRecording }" @click="toggleVoiceInput" :title="isRecording ? '停止聆听' : '开始聆听'">
            <Mic :size="34" :class="{ pulse: isRecording }" />
            <span>{{ isRecording ? '点击停止' : '点击开始聆听' }}</span>
          </button>

          <div class="vd-status">
            <template v-if="isRecording">正在聆听… 请说出食物（例：一碗米饭、两个鸡蛋）</template>
            <template v-else-if="voiceParsing">AI 解析中，正在识别食物与克重…</template>
            <template v-else-if="voiceError">{{ voiceError }}</template>
            <template v-else-if="voiceItems.length">识别到「{{ voiceResult }}」→ 解析出 {{ voiceItems.length }} 项，请核对克重后确认添加</template>
            <template v-else-if="voiceResult">{{ voiceResult }}<template v-if="voiceNote"> · {{ voiceNote }}</template></template>
            <template v-else>{{ voiceNote || '点击麦克风开始语音报餐' }}</template>
          </div>

          <!-- AI 解析结果：待确认列表（食物 + 克重 + 匹配状态） -->
          <div v-if="!isRecording && voiceItems.length" class="vd-items">
            <div v-for="(it, i) in voiceItems" :key="i" class="vd-item" :class="{ miss: !it.foodId }">
              <span class="nm">{{ it.foodName }}</span>
              <span class="w">{{ it.weight }} g</span>
              <span class="st">{{ it.foodId ? '已匹配' : '库内未匹配' }}</span>
            </div>
          </div>

          <button v-if="!isRecording && voiceItems.length && !voiceParsing" class="vd-primary" :disabled="saving" @click="confirmVoiceAdd">
            {{ saving ? '添加中…' : '确认添加（' + voiceItems.filter(i => i.foodId).length + ' 项）' }}
          </button>
        </div>
      </div>
    </teleport>

    <!-- ===== 气泡弹窗（无灰遮罩 · 气泡弹出） ===== -->
    <div v-if="dialogOpen" class="pop-mask" @click.self="closeAddDialog">
      <div class="pop-bubble">
        <div class="pop-head">
          <h3>添加到「{{ currentMealLabel }}」</h3>
          <button class="pop-close" @click="closeAddDialog"><X :size="18" /></button>
        </div>

        <div class="pop-body">
          <!-- 分类 chips -->
          <div class="pop-chips">
            <button
              v-for="c in categories" :key="c"
              class="chip" :class="{ on: activeCategory === c }"
              @click="activeCategory = c"
            >{{ c }}</button>
          </div>

          <!-- 搜索 & GI 提示 -->
          <div class="pop-search">
            <div class="pop-search-box">
              <input v-model="keyword" placeholder="搜索食物名称" />
              <div class="pop-search-tools">
                <button
                  class="tool" :class="{ rec: isRecording }" :disabled="isRecording"
                  title="语音搜索" @click="toggleVoiceInput"
                ><Mic :size="16" /></button>
              </div>
            </div>
            <label v-if="isDiabetes" class="pop-gi-hint">⤴ 糖尿病用户：优先按低 GI 排序</label>
          </div>

          <!-- 语音识别结果 -->
          <div v-if="voiceResult" class="pop-voice">
            <MessageCircle :size="15" />
            <span>语音识别: {{ voiceResult }}</span>
            <div class="pop-voice-ops">
              <button class="mini-btn gold" @click="applyVoiceResult">使用</button>
              <button class="mini-btn" @click="clearVoiceResult">清除</button>
            </div>
          </div>

          <!-- 食物列表 -->
          <div class="food-pick-list">
            <div v-if="filteredFoods.length === 0" class="food-pick-none">没有匹配的食物</div>
            <div
              v-for="(f, idx) in filteredFoods" :key="f.foodId ?? idx"
              class="food-pick-item" :class="{ picked: selectedFood && selectedFood.foodId === f.foodId }"
              @click="pickFood(f)"
            >
              <div class="fp-top">
                <span class="fp-name">{{ f.foodName }} <em>({{ f.foodCategory }})</em></span>
                <span class="fp-kcal">{{ f.calorie }} kcal/100g · GI {{ f.giValue ?? '-' }}</span>
              </div>
              <div class="fp-sub">
                蛋白 {{ f.protein }} g · 脂肪 {{ f.fat }} g · 碳水 {{ f.carb }} g · 钙 {{ f.calcium ?? 0 }} mg · 叶酸 {{ f.folicAcid ?? 0 }} μg · DHA {{ f.dha ?? 0 }} mg
              </div>
            </div>
          </div>

          <!-- 选中食物的分量 -->
          <div v-if="selectedFood" class="pop-portion">
            <div class="pp-field">
              <label>食用重量（克）</label>
              <input v-model.number="form.amount" type="number" min="1" />
            </div>
            <div class="pp-field">
              <label>预计热量</label>
              <div class="pp-kcal">{{ roundOne((selectedFood.calorie ?? 0) * form.amount / 100) }} kcal</div>
            </div>
          </div>

          <!-- 智能食材替换建议 -->
          <div v-if="selectedFood && substitutionSuggestions.length > 0" class="pop-subst">
            <div class="ps-head"><Lightbulb :size="15" /><span>营养优化建议</span></div>
            <div
              v-for="suggestion in substitutionSuggestions" :key="suggestion.foodId"
              class="ps-row" @click="pickFood(suggestion)"
            >
              <span class="ps-badge">{{ suggestion.foodName.slice(0, 1) }}</span>
              <div class="ps-info">
                <p>{{ suggestion.foodName }}</p>
                <span>{{ suggestion.calorie }} kcal/100g · GI {{ suggestion.giValue ?? '-' }}</span>
              </div>
              <div class="ps-right">
                <i :class="suggestion.calorie < selectedFood.calorie ? 'down' : 'flat'">
                  {{ suggestion.calorie < selectedFood.calorie ? '更低热量' : '相近热量' }}
                </i>
                <span>蛋白 {{ suggestion.protein }}g · 碳水 {{ suggestion.carb }}g</span>
              </div>
            </div>
          </div>

          <div v-if="errorMessage" class="pop-error">{{ errorMessage }}</div>

          <div class="pop-foot">
            <button class="ghost-add solid" @click="closeAddDialog">取消</button>
            <button class="confirm-btn" :disabled="!selectedFood || saving" @click="confirmAddItem">
              {{ saving ? '添加中...' : '确认添加' }}
            </button>
          </div>
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
  Mic, X, MessageCircle, Lightbulb,
  LayoutGrid, Utensils, ClipboardList, Sunrise, Sun, Moon, Cookie,
  Calendar, Flame, Plus
} from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { useDietStore } from '@/stores/diet'
import { FOOD_CATEGORY_ORDER } from '@/constants'
import { api } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const dietStore = useDietStore()

const today = new Date().toISOString().slice(0, 10)

// ===== 四餐站点定义 =====
const meals = [
  { type: '早餐', label: '早餐', time: '06:00 – 10:00', icon: Sunrise },
  { type: '午餐', label: '午餐', time: '11:00 – 14:00', icon: Sun },
  { type: '晚餐', label: '晚餐', time: '17:00 – 20:00', icon: Moon },
  { type: '加餐', label: '加餐', time: '任意时段', icon: Cookie }
]

const form = ref({
  date: today,
  amount: 100
})

const foods = ref<any[]>([])
const categories = ref<string[]>([])
const activeCategory = ref<string>('全部')
const keyword = ref<string>('')
const selectedFood = ref<any | null>(null)
const dialogOpen = ref(false)
const currentMeal = ref<string>(defaultMeal())
const saving = ref(false)
const errorMessage = ref('')
const mealsData = computed(() => dietStore.currentMeals)

// 按当前时刻默认聚焦对应餐次
function defaultMeal(): string {
  const h = new Date().getHours()
  if (h < 10) return '早餐'
  if (h < 15) return '午餐'
  if (h < 21) return '晚餐'
  return '加餐'
}

const isRecording = ref(false)
const voiceResult = ref('')
const voiceNote = ref('')
const voiceParsing = ref(false)
const voiceError = ref('')
// AI 解析出的待确认项：{ foodName, weight, foodId }（foodId 为 null 表示库内未匹配）
const voiceItems = ref<Array<{ foodName: string; weight: number; foodId: number | null }>>([])

// 语音浮窗是否可见：聆听中 / 解析中 / 有结果或错误 任一态即可见，保证点语音后有明确反馈
const voiceActive = computed(() => isRecording.value || voiceParsing.value || !!voiceNote.value || !!voiceError.value || !!voiceResult.value)

const isDiabetes = computed(() => {
  const c = userStore.user?.crowdType || userStore.user?.crowd_type || ''
  return String(c).indexOf('糖尿') >= 0
})

const currentMealLabel = computed(() => (meals.find((m) => m.type === currentMeal.value) || meals[1]).label)

const substitutionSuggestions = computed(() => [] as Array<{ foodId: number; foodName: string; calorie: number; giValue?: number; protein: number; carb: number }>)

function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'diet' } }) }
function switchMeal(type: string) {
  if (dialogOpen.value) closeAddDialog()
  currentMeal.value = type
}

// ===== 星轨站点：横向分布 + 各自漂浮节奏 =====
function stationLeft(i: number): number {
  return 34 + i * 20
}
function floatStyle(i: number): Record<string, string> {
  return {
    animationDuration: (4.6 + (i % 4) * 0.45) + 's',
    animationDelay: -(i * 0.9) + 's'
  }
}

// ---- 载入食物库 ----
async function loadFoods() {
  try {
    const list: any = await api.food.list()
    if (Array.isArray(list)) {
      foods.value = list
      const cs = new Set<string>()
      list.forEach((f: any) => {
        if (f && f.foodCategory) cs.add(f.foodCategory)
      })
      categories.value = [
        '全部',
        ...FOOD_CATEGORY_ORDER.filter((x: string) => cs.has(x)),
        ...Array.from(cs).filter((x: string) => (FOOD_CATEGORY_ORDER as readonly string[]).indexOf(x) === -1)
      ]
    }
  } catch (e: any) {
    errorMessage.value = e?.message || '加载食物库失败'
  }
}

// ---- 分类 + 搜索 + 糖尿病人按 GI 升序 ----
const filteredFoods = computed(() => {
  let list = foods.value
  if (activeCategory.value !== '全部') {
    list = list.filter((f: any) => f && f.foodCategory === activeCategory.value)
  }
  const kw = keyword.value.trim()
  if (kw) {
    list = list.filter((f: any) => (f.foodName || '').indexOf(kw) >= 0)
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

// ---- 载入当日饮食记录 ----
async function loadRecords() {
  try {
    await dietStore.fetchTodayMeals(form.value.date)
  } catch (e: any) {
    errorMessage.value = e?.message || '获取记录失败'
  }
}

function mealItems(type: string): any[] {
  const result: any[] = []
  mealsData.value.forEach((m: any) => {
    // 兼容 mealType / meal_type 两种字段格式
    const mt = m.mealType || m.meal_type
    if (mt === type && Array.isArray(m.items)) {
      m.items.forEach((it: any) => result.push({ ...it, mealId: m.mealId }))
    }
  })
  return result
}

function mealTotalCalorie(type: string): number {
  let total = 0
  mealItems(type).forEach((it) => {
    total += (Number(it.calorie) || 0) * (Number(it.eatWeight) || 0) / 100
  })
  return Math.round(total)
}

const currentItems = computed(() => mealItems(currentMeal.value))
const currentMealKcal = computed(() => mealTotalCalorie(currentMeal.value))

// ---- 总汇总 ----
const totalCalories = computed(() => meals.reduce((sum, m) => sum + mealTotalCalorie(m.type), 0))
const totalProtein = computed(() => sumNutrient('protein'))
const totalFat = computed(() => sumNutrient('fat'))
const totalCarbs = computed(() => sumNutrient('carb'))

function sumNutrient(key: string): number {
  let total = 0
  mealsData.value.forEach((meal) => {
    if (meal.items) {
      meal.items.forEach((item: any) => {
        const base = Number(item[key]) || 0
        total += (base * (Number(item.eatWeight) || 0)) / 100
      })
    }
  })
  return Math.round(total)
}

// ---- 今日小结：三色宏量占比（蛋白蓝 / 脂肪黄 / 碳水绿） + 四餐分布 ----
const macroShares = computed(() => {
  const p = totalProtein.value * 4
  const f = totalFat.value * 9
  const c = totalCarbs.value * 4
  const total = p + f + c
  const mk = (key: string, g: number, kcalPart: number, color: string) => ({
    key, g, color,
    pct: total > 0 ? Math.max(2, Math.round((kcalPart / total) * 100)) : 0
  })
  return [
    mk('蛋白质', totalProtein.value, p, '#6C8FBE'),
    mk('脂肪', totalFat.value, f, '#D9A24A'),
    mk('碳水', totalCarbs.value, c, '#7FAE8E')
  ]
})

const mealDist = computed(() => {
  const total = totalCalories.value
  return meals.map((m) => {
    const k = mealTotalCalorie(m.type)
    return { label: m.label, kcal: k, pct: total > 0 ? Math.max(k > 0 ? 3 : 0, Math.round((k / total) * 100)) : 0 }
  })
})

function roundOne(n: number): number {
  return Math.round(n * 10) / 10
}

function pickFood(f: any) {
  selectedFood.value = f
  errorMessage.value = ''
}

function openAddDialog(mealType: string) {
  currentMeal.value = mealType
  selectedFood.value = null
  errorMessage.value = ''
  form.value.amount = 100
  dialogOpen.value = true
}

function closeAddDialog() {
  dialogOpen.value = false
  selectedFood.value = null
  errorMessage.value = ''
}

async function confirmAddItem() {
  if (!selectedFood.value) {
    errorMessage.value = '请先选择一个食物'
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    await dietStore.addMeal({
      eatDate: form.value.date,
      mealType: currentMeal.value,
      remark: '',
      items: [{ foodId: selectedFood.value.foodId, eatWeight: Number(form.value.amount) || 0 }]
    })
    closeAddDialog()
    await dietStore.fetchTodayMeals(form.value.date)
  } catch (e: any) {
    errorMessage.value = e?.response?.data?.message || e?.message || '添加失败'
  } finally {
    saving.value = false
  }
}

async function handleDeleteMeal(mealId: number) {
  if (mealId == null) return
  if (!window.confirm('确定删除这一餐的记录？')) return
  try {
    await dietStore.deleteMeal(mealId, form.value.date)
    await dietStore.fetchTodayMeals(form.value.date)
  } catch (e: any) {
    errorMessage.value = e?.message || '删除失败'
  }
}

// ---- 语音录入功能 ----
// 全局保存当前识别实例：startRecording 创建的实例必须可被 stopRecording 关闭（原代码在 stopRecording 里 new 了一个未启动的实例去调 stop，根本停不掉正在录制的识别器）
let activeRecognition: any = null

const toggleVoiceInput = () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

const startRecording = () => {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  voiceError.value = ''
  const unsupported = '当前浏览器不支持语音识别（SpeechRecognition 仅 Chrome / Edge 支持）。请更换浏览器，或在搜索框输入食物名称'
  if (!SpeechRecognition) {
    errorMessage.value = unsupported
    voiceError.value = unsupported
    return
  }
  // 语音识别仅在"安全上下文"（https 或 localhost/127.0.0.1）可用；通过局域网 IP 访问会静默失败，提前给出提示
  const isSecure = window.isSecureContext === true
  if (!isSecure) {
    const secMsg = '语音识别需要安全连接：请用 http://localhost:5173 访问本页面（当前非 localhost 打开，麦克风不可用）。或直接在搜索框输入食物名称'
    errorMessage.value = secMsg
    voiceError.value = secMsg
    return
  }

  // 切换 / 错误后确保上一次实例释放，避免重复 start 抛 InvalidStateError
  if (activeRecognition) { try { activeRecognition.abort() } catch (e) {} activeRecognition = null }

  let recognition: any
  try {
    recognition = new SpeechRecognition()
  } catch (e) {
    const initErr = '语音识别初始化失败。请更换浏览器，或直接在搜索框输入食物名称'
    errorMessage.value = initErr
    voiceError.value = initErr
    return
  }
  activeRecognition = recognition

  recognition.lang = 'zh-CN'
  recognition.continuous = false
  recognition.interimResults = false

  // start 可能同步抛异常（无效状态/权限/环境），必须捕获并给出反馈，否则点按钮会"毫无反应"
  recognition.onstart = () => {
    isRecording.value = true
    voiceError.value = ''
  }

  recognition.onresult = (event: any) => {
    const transcript = event.results[0][0]?.transcript
    if (transcript) {
      isRecording.value = false
      voiceResult.value = transcript
      handleVoiceText(transcript)
    }
  }

  recognition.onerror = () => {
    const msg = '语音识别失败（未检测到声音或浏览器无麦克风权限）。请重试，或直接在搜索框输入食物名称'
    errorMessage.value = msg
    voiceError.value = msg
    isRecording.value = false
    activeRecognition = null
  }

  recognition.onend = () => {
    isRecording.value = false
  }

  // start 抛异常时给出反馈而不是静默失败
  try {
    recognition.start()
  } catch (e: any) {
    const startErr = '无法开启麦克风（可能被系统拦截或当前环境不支持）。请检查浏览器麦克风权限，或直接在搜索框输入食物名称'
    errorMessage.value = startErr
    voiceError.value = startErr
    isRecording.value = false
    activeRecognition = null
    return
  }
  errorMessage.value = ''
}

const stopRecording = () => {
  if (activeRecognition) {
    try { activeRecognition.stop() } catch (e) {}
    try { activeRecognition.abort() } catch (e) {}
    activeRecognition = null
  }
  isRecording.value = false
}

// 手动关闭语音浮窗反馈（不打断识别；若在聆听中由 toggle 处理停止）
const dismissVoice = () => {
  voiceNote.value = ''
  voiceError.value = ''
  voiceResult.value = ''
  voiceItems.value = []
}

// 关闭语音弹窗：若正在聆听则先停止，再清空反馈
const onCloseVoice = () => {
  if (isRecording.value) stopRecording()
  dismissVoice()
}

// 重新解析已识别的文本（搜索框场景的「使用」按钮）
const applyVoiceResult = () => {
  const t = voiceResult.value
  if (t) handleVoiceText(t)
}

const clearVoiceResult = () => {
  voiceResult.value = ''
}

// 在食物库 foods.value 中按名称把 AI 解析出的食材匹配到具体 foodId
function matchFoodByName(rawName: string): any {
  const name = String(rawName || '').trim()
  if (!name) return null
  // 去掉（熟）（生）等状态后缀，提升"米饭（熟）"对"米饭"的命中
  const norm = name.replace(/[（(].*?[)）]/g, '').replace(/\s+/g, '')
  if (!norm) return null
  let best: any = null
  let bestScore = -1
  for (const f of foods.value) {
    const fnNorm = String(f?.foodName || '').replace(/[（(].*?[)）]/g, '').replace(/\s+/g, '')
    if (!fnNorm) continue
    if (fnNorm === norm) return f
    if (fnNorm.includes(norm) || norm.includes(fnNorm)) {
      const score = Math.min(fnNorm.length, norm.length)
      if (score > bestScore) { best = f; bestScore = score }
    }
  }
  return best
}

// 语音报餐核心：浏览器识别文本 → 调用 AI /ai/voice/parse（口语量词→克重）→ 匹配食物库 → 在弹窗内展示待确认列表
async function handleVoiceText(text: string) {
  const t = String(text || '').trim()
  if (!t || voiceParsing.value) return
  voiceParsing.value = true
  voiceNote.value = ''
  voiceItems.value = []
  try {
    const resp: any = await api.ai.voiceParse(t)
    const items = Array.isArray(resp?.items) ? resp.items : []
    if (!items.length) throw new Error('EMPTY')
    const parsed: Array<{ foodName: string; weight: number; foodId: number | null }> = []
    for (const it of items) {
      const food = matchFoodByName(it?.food_name)
      const w = Math.max(1, Number(it?.weight) || 0)
      parsed.push({ foodName: String(it?.food_name || '未知食物'), weight: w, foodId: food?.foodId ?? null })
    }
    voiceItems.value = parsed
  } catch (e: any) {
    // AI 解析暂不可用 → 退化为手动搜索
    keyword.value = t
    voiceNote.value = 'AI 解析暂不可用，已填入搜索框，请手动选择'
    clearVoiceResult()
  } finally {
    voiceParsing.value = false
  }
}

// 确认添加：把弹窗内待确认的解析结果批量写入当前餐次
async function confirmVoiceAdd() {
  const matched = voiceItems.value.filter((it) => it.foodId != null)
  const missed = voiceItems.value.filter((it) => it.foodId == null)
  if (!matched.length) {
    voiceNote.value = '解析结果均未匹配到库内食材，请在搜索框手动选择'
    return
  }
  saving.value = true
  try {
    await dietStore.addMeal({
      eatDate: form.value.date,
      mealType: currentMeal.value,
      remark: '语音报餐',
      items: matched.map((it) => ({ foodId: it.foodId as number, eatWeight: it.weight }))
    })
    await dietStore.fetchTodayMeals(form.value.date)
    voiceNote.value = `已通过语音添加 ${matched.length} 项` + (missed.length ? ` · 未匹配：${missed.map((m) => m.foodName).join('、')}` : '')
    voiceItems.value = []
    clearVoiceResult()
  } catch (e: any) {
    voiceError.value = e?.response?.data?.message || e?.message || '添加失败'
  } finally {
    saving.value = false
  }
}

// ===== 入场动效（面包屑点亮 → 站点弹出 → 浅芯浮起） =====
const bandRef = ref<HTMLElement | null>(null)
const paperRef = ref<HTMLElement | null>(null)
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
    // 站点沿星轨依次弹出
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

// 切换餐次时，主工作卡轻微浮起过渡
watch(currentMeal, () => {
  nextTick(() => {
    if (mainRef.value) {
      gsap.fromTo(mainRef.value, { opacity: 0.35, y: 10 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' })
    }
  })
})

watch(
  () => form.value.date,
  () => {
    loadRecords()
  }
)

onMounted(async () => {
  animateEntrance()
  userStore.init()
  await loadFoods()
  await loadRecords()
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

/* ---- 顶行：星座面包屑 + 日期 ---- */
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
.db-date input {
  background: transparent; border: none; outline: none;
  color: #F0E2C4; font-size: 11px; font-family: inherit;
  color-scheme: dark; cursor: pointer; letter-spacing: 0.03em;
}

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

/* ---- 四餐站点（wrapper 定位 / 内层上下浮动 / 按钮悬停缩放，三层分离避免冲突） ---- */
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
.db-block-head {
  display: flex; align-items: baseline; gap: 8px;
}
.db-block-head b { font-size: 13px; color: #2A2620; font-weight: 700; }
.db-block-kcal {
  margin-left: auto; font-family: 'Noto Serif SC', serif;
  font-size: 17px; font-weight: 900; color: #B8863B;
}
.db-empty {
  margin-top: 12px;
  border: 1px dashed rgba(184, 134, 59, 0.35);
  border-radius: 12px; padding: 22px 14px;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  font-size: 12px; color: #8C7A5E;
  cursor: pointer; transition: 0.25s;
}
.db-empty:hover {
  border-color: #B8863B; color: #B8863B;
  background: rgba(217, 162, 74, 0.06);
}
.db-items { margin-top: 6px; }
.db-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 2px;
  border-bottom: 1px dashed rgba(184, 134, 59, 0.18);
  font-size: 12.5px; color: #2A2620;
}
.db-item:last-child { border-bottom: none; }
.db-item .nm { font-weight: 700; white-space: nowrap; }
.db-item .nm em {
  font-style: normal; font-weight: 500;
  color: rgba(42, 38, 32, 0.45); font-size: 10.5px; margin-left: 5px;
}
.db-item .meta {
  color: rgba(42, 38, 32, 0.5); font-size: 10.5px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.db-item .k {
  font-size: 11.5px; color: #B8863B; font-weight: 700;
  white-space: nowrap; margin-left: auto;
}
.db-item .x {
  width: 22px; height: 22px; border-radius: 50%;
  border: none; background: none; color: #C98F6F;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: 0.2s; flex-shrink: 0;
}
.db-item .x:hover { background: rgba(201, 110, 80, 0.12); }
.db-foot {
  display: flex; align-items: center; gap: 8px; margin-top: 12px; flex-wrap: wrap;
}
.ghost-add {
  display: inline-flex; align-items: center; gap: 6px;
  border: 1px dashed rgba(184, 134, 59, 0.4);
  color: #B8863B; background: none; cursor: pointer;
  font-size: 12px; font-weight: 600; letter-spacing: 0.05em;
  border-radius: 10px; padding: 8px 14px; transition: 0.25s;
}
.ghost-add:hover { background: rgba(217, 162, 74, 0.1); border-color: #B8863B; }
.ghost-add.solid { border-style: solid; }

/* 语音报餐反馈 */
.voice-note {
  margin-top: 10px; font-size: 12px; color: #2F7D5D; font-weight: 600;
  background: rgba(47, 125, 93, 0.07); border-radius: 8px; padding: 7px 10px;
  display: flex; align-items: center; gap: 6px;
}
.voice-note.busy { color: #B8863B; background: rgba(184, 134, 59, 0.08); }

/* ---- 语音报餐弹窗 ---- */
.voice-mask {
  position: fixed; inset: 0; z-index: 1200;
  background: rgba(26, 24, 22, 0.42);
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(2px);
}
.voice-dialog {
  width: min(360px, 90vw);
  background: #fffdf7;
  border-radius: 18px;
  padding: 20px 22px 22px;
  box-shadow: 0 12px 40px rgba(40, 32, 20, 0.22);
  border: 1px solid rgba(184, 134, 59, 0.2);
  animation: vd-in 0.25s ease;
}
@keyframes vd-in { from { opacity: 0; transform: translateY(10px) scale(0.97); } to { opacity: 1; transform: none; } }
.voice-dialog.rec { border-color: #E8B973; }
.vd-head {
  display: flex; align-items: center; gap: 8px; margin-bottom: 16px;
}
.vd-head b { font-size: 15px; color: #2A2620; letter-spacing: 0.02em; }
.vd-sub { font-size: 11px; color: #9A8F7F; font-weight: 400; }
.vd-close {
  margin-left: auto; width: 28px; height: 28px; border-radius: 50%;
  border: none; background: rgba(184, 134, 59, 0.08); color: #8A7a62;
  cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s;
}
.vd-close:hover { background: rgba(184, 134, 59, 0.18); color: #2A2620; }
.vd-mic {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px;
  width: 88px; height: 88px; margin: 0 auto 14px; border-radius: 50%;
  border: 2px dashed rgba(184, 134, 59, 0.4); background: rgba(232, 185, 115, 0.08);
  color: #B8863B; cursor: pointer; transition: 0.25s;
}
.vd-mic span { font-size: 11px; color: #9A8F7F; margin-top: 2px; }
.vd-mic.on { border-style: solid; border-color: #E8B973; background: rgba(232, 185, 115, 0.18); }
.vd-mic .pulse { animation: vpulse 1.4s infinite; }
@keyframes vpulse { 0% { transform: scale(0.94); opacity: 0.7; } 50% { transform: scale(1.08); opacity: 1; } 100% { transform: scale(0.94); opacity: 0.7; } }
.vd-status {
  margin-top: 14px; font-size: 13px; line-height: 1.6; color: #4A4438;
  min-height: 44px; text-align: center;
  background: rgba(184, 134, 59, 0.06); border-radius: 10px; padding: 9px 12px;
}
.vd-primary {
  width: 100%; margin-top: 14px; padding: 10px;
  background: linear-gradient(135deg, #DCA14B, #B8863B); border: none; border-radius: 10px;
  color: #fff; font-weight: 700; font-size: 13px; letter-spacing: 0.05em; cursor: pointer; transition: 0.25s;
}
.vd-primary:hover { filter: brightness(1.05); transform: translateY(-1px); }
.vd-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.vd-items {
  margin-top: 12px;
  border: 1px solid rgba(184, 134, 59, 0.2);
  border-radius: 10px;
  background: #fff;
  overflow: hidden;
}
.vd-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; font-size: 12.5px; color: #2A2620;
  border-bottom: 1px dashed rgba(184, 134, 59, 0.18);
}
.vd-item:last-child { border-bottom: none; }
.vd-item .nm { font-weight: 700; }
.vd-item .w { color: #B8863B; font-weight: 700; }
.vd-item .st {
  margin-left: auto; font-size: 10px; padding: 2px 8px; border-radius: 99px;
  background: rgba(127, 174, 142, 0.16); color: #2F7D5B;
}
.vd-item.miss .st { background: rgba(201, 110, 80, 0.14); color: #C0522F; }

/* ---- 今日小结 ---- */
.db-side-head {
  display: flex; align-items: baseline; gap: 8px;
}
.db-side-head b { font-size: 13px; color: #2A2620; font-weight: 700; }
.db-side-head span { font-size: 10.5px; color: rgba(42, 38, 32, 0.45); }
.db-macros {
  display: flex; flex-direction: column; gap: 10px;
  margin-top: 12px;
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
.db-dist {
  margin-top: 14px; padding-top: 12px;
  border-top: 1px dashed rgba(184, 134, 59, 0.2);
  display: flex; flex-direction: column; gap: 8px;
}
.db-dist-row {
  display: flex; align-items: center; gap: 10px; font-size: 11px;
}
.db-dist-row .lb { width: 32px; color: rgba(42, 38, 32, 0.55); flex-shrink: 0; }
.db-dist-row .bar {
  flex: 1; height: 5px; border-radius: 99px;
  background: rgba(184, 134, 59, 0.1); overflow: hidden;
}
.db-dist-row .bar i {
  display: block; height: 100%; border-radius: 99px;
  background: linear-gradient(90deg, #E8B973, #B8863B);
  transition: width 0.6s cubic-bezier(0.34, 1.3, 0.64, 1);
}
.db-dist-row .k {
  width: 72px; text-align: right; color: #B8863B; font-weight: 700; flex-shrink: 0;
}
.db-dist-row.dim .k { color: rgba(42, 38, 32, 0.4); font-weight: 500; }

/* ========== 气泡弹窗（无灰遮罩 · 气泡弹出动画） ========== */
.pop-mask {
  position: fixed; inset: 0; z-index: 60;
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
  background: transparent;
}
.pop-bubble {
  width: 100%; max-width: 760px; max-height: 88vh;
  display: flex; flex-direction: column;
  background: #FDFBF4;
  border: 1px solid rgba(232, 185, 115, 0.45);
  border-radius: 20px;
  box-shadow: 0 30px 70px -20px rgba(90, 70, 40, 0.35), 0 0 0 6px rgba(217, 162, 74, 0.08);
  overflow: hidden;
}
/* 气泡弹出：scale + 上浮，带轻微回弹 */
.pop-mask-enter-active { transition: opacity 0.2s ease; }
.pop-mask-enter-from { opacity: 0; }
.pop-mask-leave-active { transition: opacity 0.18s ease; }
.pop-mask-leave-to { opacity: 0; }
.pop-mask-enter-active .pop-bubble {
  transition: transform 0.45s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
}
.pop-mask-enter-from .pop-bubble {
  transform: scale(0.7) translateY(36px); opacity: 0;
}
.pop-mask-leave-active .pop-bubble {
  transition: transform 0.18s ease, opacity 0.18s ease;
}
.pop-mask-leave-to .pop-bubble {
  transform: scale(0.92) translateY(12px); opacity: 0;
}
.pop-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid rgba(184, 134, 59, 0.16);
  background: #FDFBF4; flex-shrink: 0;
}
.pop-head h3 { font-size: 14px; font-weight: 700; color: #2A2620; }
.pop-close {
  border: none; background: none; color: rgba(42, 38, 32, 0.45);
  cursor: pointer; padding: 4px; border-radius: 8px; transition: 0.2s;
  display: flex; align-items: center; justify-content: center;
}
.pop-close:hover { color: #2A2620; background: rgba(184, 134, 59, 0.1); }
.pop-body {
  padding: 16px 20px 18px;
  overflow-y: auto;
  display: flex; flex-direction: column; gap: 14px;
}
.pop-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
  font-size: 11px; color: #6E6350;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(184, 134, 59, 0.2);
  padding: 5px 12px; border-radius: 999px;
  cursor: pointer; transition: 0.25s; font-family: inherit;
}
.chip:hover { border-color: #B8863B; color: #B8863B; background: rgba(217, 162, 74, 0.08); }
.chip.on {
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; border-color: transparent; font-weight: 600;
}
.pop-search { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.pop-search-box { position: relative; flex: 1; min-width: 240px; }
.pop-search-box input {
  width: 100%; padding: 8px 76px 8px 12px;
  border-radius: 10px; border: 1px solid rgba(184, 134, 59, 0.25);
  background: #fff; font-size: 12.5px; color: #2A2620; outline: none;
  transition: border-color 0.25s ease;
}
.pop-search-box input:focus { border-color: #B8863B; }
.pop-search-tools {
  position: absolute; right: 6px; top: 50%; transform: translateY(-50%);
  display: flex; gap: 2px;
}
.pop-search-tools .tool {
  border: none; background: none; padding: 5px; border-radius: 8px;
  color: rgba(42, 38, 32, 0.45); cursor: pointer; transition: 0.2s;
  display: flex; align-items: center; justify-content: center;
}
.pop-search-tools .tool:hover { background: rgba(184, 134, 59, 0.1); color: #B8863B; }
.pop-search-tools .tool.rec { color: #C0522F; background: rgba(201, 110, 80, 0.12); }
.pop-gi-hint { font-size: 11px; color: #B8863B; }
.pop-voice {
  display: flex; align-items: center; gap: 8px;
  background: rgba(217, 162, 74, 0.1);
  border: 1px solid rgba(217, 162, 74, 0.3);
  border-radius: 10px; padding: 9px 12px;
  font-size: 12px; color: #2A2620;
}
.pop-voice svg { color: #B8863B; flex-shrink: 0; }
.pop-voice-ops { margin-left: auto; display: flex; gap: 6px; }
.mini-btn {
  font-size: 11px; padding: 4px 12px; border-radius: 8px;
  border: 1px solid rgba(184, 134, 59, 0.25);
  background: rgba(255, 255, 255, 0.8); color: #6E6350;
  cursor: pointer; transition: 0.2s; font-family: inherit;
}
.mini-btn:hover { border-color: #B8863B; color: #B8863B; }
.mini-btn.gold {
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; border-color: transparent; font-weight: 600;
}
.mini-btn.gold:hover { opacity: 0.9; }
.mini-btn.gold.big { padding: 7px 16px; margin-top: 8px; }
.food-pick-list {
  max-height: 280px; overflow-y: auto;
  border: 1px solid rgba(184, 134, 59, 0.2);
  border-radius: 12px; background: #fff;
}
.food-pick-none {
  text-align: center; font-size: 12px; color: rgba(42, 38, 32, 0.45); padding: 22px 0;
}
.food-pick-item {
  padding: 9px 12px; cursor: pointer;
  border-bottom: 1px solid rgba(184, 134, 59, 0.12);
  transition: background-color 0.18s ease;
}
.food-pick-item:last-child { border-bottom: none; }
.food-pick-item:hover { background: rgba(217, 162, 74, 0.08); }
.food-pick-item.picked { background: linear-gradient(135deg, rgba(232, 185, 115, 0.22), rgba(184, 134, 59, 0.16)); }
.fp-top { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.fp-name { font-size: 12.5px; font-weight: 600; color: #2A2620; }
.fp-name em { font-style: normal; font-weight: 400; font-size: 10.5px; color: rgba(42, 38, 32, 0.45); }
.fp-kcal { font-size: 10.5px; color: rgba(42, 38, 32, 0.55); white-space: nowrap; }
.fp-sub { font-size: 10.5px; color: rgba(42, 38, 32, 0.45); margin-top: 2px; }
.food-pick-list::-webkit-scrollbar { width: 8px; }
.food-pick-list::-webkit-scrollbar-track { background: rgba(184, 134, 59, 0.08); border-radius: 4px; }
.food-pick-list::-webkit-scrollbar-thumb { background: rgba(184, 134, 59, 0.4); border-radius: 4px; }
.food-pick-list::-webkit-scrollbar-thumb:hover { background: rgba(150, 100, 40, 0.6); }
.pop-portion {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  background: rgba(217, 162, 74, 0.07);
  border: 1px solid rgba(184, 134, 59, 0.18);
  border-radius: 12px; padding: 12px 14px;
}
.pp-field label {
  display: block; font-size: 10.5px; color: rgba(42, 38, 32, 0.5); margin-bottom: 4px;
}
.pp-field input {
  width: 100%; padding: 8px 10px; border-radius: 10px;
  border: 1px solid rgba(184, 134, 59, 0.25);
  background: #fff; font-size: 12.5px; color: #2A2620; outline: none;
}
.pp-field input:focus { border-color: #B8863B; }
.pp-kcal {
  padding: 8px 10px; border-radius: 10px;
  border: 1px solid rgba(184, 134, 59, 0.25);
  background: #fff; font-size: 12.5px; font-weight: 700; color: #B8863B;
}
.pop-subst {
  background: rgba(108, 143, 190, 0.08);
  border: 1px solid rgba(108, 143, 190, 0.25);
  border-radius: 12px; padding: 12px 14px;
}
.ps-head {
  display: flex; align-items: center; gap: 7px; margin-bottom: 8px;
  font-size: 12px; font-weight: 600; color: #4A6FA0;
}
.ps-row {
  display: flex; align-items: center; gap: 10px;
  padding: 7px 6px; border-radius: 8px; cursor: pointer; transition: 0.2s;
}
.ps-row:hover { background: rgba(108, 143, 190, 0.1); }
.ps-badge {
  width: 28px; height: 28px; border-radius: 8px; flex-shrink: 0;
  background: rgba(108, 143, 190, 0.15); color: #4A6FA0;
  font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.ps-info p { font-size: 12px; font-weight: 600; color: #2A2620; }
.ps-info span { font-size: 10.5px; color: rgba(42, 38, 32, 0.5); }
.ps-right { margin-left: auto; text-align: right; }
.ps-right i {
  font-style: normal; font-size: 10px; padding: 2px 8px; border-radius: 99px;
}
.ps-right i.down { background: rgba(127, 174, 142, 0.16); color: #2F7D5B; }
.ps-right i.flat { background: rgba(217, 162, 74, 0.16); color: #B8863B; }
.ps-right > span { display: block; font-size: 10px; color: rgba(42, 38, 32, 0.5); margin-top: 3px; }
.pop-error { font-size: 11px; color: #C0522F; text-align: right; }
.pop-foot {
  display: flex; justify-content: flex-end; gap: 10px;
  padding-top: 12px; border-top: 1px solid rgba(184, 134, 59, 0.16);
}
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
  .db-item .meta { display: none; }
}
</style>
