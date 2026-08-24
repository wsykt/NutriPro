<template>
  <div class="page-fade">
    <h2 class="text-2xl font-bold mb-2 text-morandi-text">录入饮食</h2>
    <p class="text-morandi-lightText mb-6 text-sm">按餐次记录今天的食物摄入。支持监护人代亲属录入。</p>

    <!-- 日期 & 总览 -->
    <div class="glass rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-4">
      <div>
        <label class="block text-xs text-morandi-lightText mb-1">日期</label>
        <input v-model="form.date" type="date" class="px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm" />
      </div>
      <div class="flex-1 grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="text-center">
          <div class="text-xs text-morandi-lightText">总热量</div>
          <div class="text-xl font-bold text-morandi-accent">{{ totalCalories }} kcal</div>
        </div>
        <div class="text-center">
          <div class="text-xs text-morandi-lightText">蛋白质</div>
          <div class="text-xl font-bold text-morandi-text">{{ totalProtein }} g</div>
        </div>
        <div class="text-center">
          <div class="text-xs text-morandi-lightText">脂肪</div>
          <div class="text-xl font-bold text-morandi-text">{{ totalFat }} g</div>
        </div>
        <div class="text-center">
          <div class="text-xs text-morandi-lightText">碳水</div>
          <div class="text-xl font-bold text-morandi-text">{{ totalCarbs }} g</div>
        </div>
      </div>
    </div>

    <!-- 四个餐次分组 -->
    <div class="space-y-6">
      <section v-for="meal in meals" :key="meal.type" class="glass rounded-2xl p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="font-semibold text-lg text-morandi-text">{{ meal.label }}</h3>
            <p class="text-xs text-morandi-lightText">约 {{ mealTotalCalorie(meal.type) }} kcal · 共 {{ mealItems(meal.type).length }} 项</p>
          </div>
          <button
            @click="openAddDialog(meal.type)"
            class="px-4 py-2 rounded-lg bg-morandi-accent text-white text-sm hover:opacity-90 transition-opacity"
          >+ 添加食物</button>
        </div>

        <div v-if="mealItems(meal.type).length === 0" class="text-sm text-morandi-lightText text-center py-6 border border-dashed border-morandi-soft rounded-xl">
          还没有记录，点右上角添加
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="(item, idx) in mealItems(meal.type)" :key="item.mealId + '-' + idx"
            class="flex items-center justify-between bg-white/70 rounded-xl px-4 py-3"
          >
            <div>
              <p class="text-sm font-medium text-morandi-text">{{ item.foodName }} <span class="text-xs text-morandi-lightText ml-1">{{ item.foodCategory }}</span></p>
              <p class="text-xs text-morandi-lightText mt-0.5">
                {{ item.eatWeight }} g · 蛋白 {{ roundOne(item.protein * item.eatWeight / 100) }} g ·
                脂肪 {{ roundOne(item.fat * item.eatWeight / 100) }} g ·
                碳水 {{ roundOne(item.carb * item.eatWeight / 100) }} g
                <span v-if="item.giValue != null" class="ml-2">GI {{ item.giValue }}</span>
              </p>
            </div>
            <div class="text-right">
              <div class="text-sm font-semibold text-morandi-accent">{{ roundOne(item.calorie * item.eatWeight / 100) }} kcal</div>
              <button
                @click="handleDeleteMeal(item.mealId)"
                class="text-xs text-red-500 mt-1 hover:underline"
              >删除该餐</button>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- 添加食物弹窗 -->
    <div v-if="dialogOpen" class="fixed inset-0 bg-black/40 z-40 flex items-center justify-center p-4" @click.self="closeAddDialog">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[92vh] overflow-y-auto">
        <div class="sticky top-0 bg-white rounded-t-2xl border-b border-morandi-soft px-6 py-4 flex items-center justify-between">
          <h3 class="font-semibold text-morandi-text">添加到「{{ currentMealLabel }}」</h3>
          <button @click="closeAddDialog" class="text-morandi-lightText hover:text-morandi-text text-2xl leading-none">×</button>
        </div>

        <div class="p-6 space-y-4">
          <!-- 分类 tab -->
          <div class="flex flex-wrap gap-2">
            <button
              v-for="c in categories" :key="c"
              @click="activeCategory = c"
              :class="['px-3 py-1.5 text-xs rounded-full border transition-all', activeCategory === c ? 'bg-morandi-accent text-white border-morandi-accent' : 'bg-white border-morandi-soft text-morandi-text hover:border-morandi-accent']"
            >{{ c }}</button>
          </div>

          <!-- 搜索 & GI 提示 & 语音/图片录入 -->
          <div class="flex flex-wrap items-center gap-3">
            <div class="relative flex-1">
              <input v-model="keyword" placeholder="搜索食物名称" class="w-full pl-3 pr-12 py-2 rounded-lg bg-white border border-morandi-soft text-sm" />
              <div class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <button 
                  @click="toggleVoiceInput"
                  :disabled="isRecording"
                  class="p-1.5 rounded-lg hover:bg-morandi-soft transition-colors"
                  :class="isRecording ? 'bg-red-100 text-red-500' : 'text-morandi-lightText'"
                  title="语音搜索"
                >
                  <Mic :size="18" />
                </button>
                <button 
                  @click="triggerImageUpload"
                  class="p-1.5 rounded-lg hover:bg-morandi-soft text-morandi-lightText transition-colors"
                  title="拍照识别"
                >
                  <ImagePlus :size="18" />
                </button>
              </div>
            </div>
            <label v-if="isDiabetes" class="text-xs text-morandi-accent">⤴ 糖尿病用户：优先按低 GI 排序</label>
          </div>
          
          <!-- 语音识别结果 -->
          <div v-if="voiceResult" class="p-3 bg-amber-50 rounded-lg border border-amber-200">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <MessageCircle class="w-4 h-4 text-amber-600" />
                <span class="text-sm text-gray-700">语音识别: {{ voiceResult }}</span>
              </div>
              <div class="flex items-center gap-2">
                <button @click="applyVoiceResult" class="px-3 py-1 text-sm bg-morandi-accent text-white rounded-md hover:opacity-90 transition-opacity">
                  使用
                </button>
                <button @click="clearVoiceResult" class="px-3 py-1 text-sm bg-gray-200 text-gray-600 rounded-md hover:bg-gray-300 transition-colors">
                  清除
                </button>
              </div>
            </div>
          </div>
          
          <!-- 图片识别结果 -->
          <div v-if="imageAnalysisResult" class="p-4 bg-green-50 rounded-xl border border-green-200">
            <div class="flex items-start gap-3">
              <div class="w-10 h-10 flex items-center justify-center bg-green-100 rounded-lg shrink-0">
                <CheckCircle class="w-5 h-5 text-green-600" />
              </div>
              <div class="flex-1">
                <h4 class="font-medium text-green-800">识别成功</h4>
                <p class="text-sm text-green-700 mt-1">识别为：<span class="font-bold">{{ imageAnalysisResult.foodName }}</span></p>
                <div class="mt-2 flex flex-wrap gap-2">
                  <span 
                    v-for="(item, index) in imageAnalysisResult.alternatives" 
                    :key="index"
                    class="px-2 py-1 text-xs bg-green-200 text-green-700 rounded-md"
                  >
                    {{ item }}
                  </span>
                </div>
                <button 
                  @click="applyImageResult" 
                  class="mt-3 px-4 py-2 bg-morandi-accent text-white rounded-lg hover:opacity-90 transition-opacity text-sm"
                >
                  确认使用
                </button>
              </div>
            </div>
          </div>
          
          <!-- 图片上传区域 -->
          <div v-if="showImageUpload" class="relative border-2 border-dashed border-morandi-accent rounded-xl p-6 text-center">
            <input 
              ref="imageInput"
              type="file" 
              accept="image/*" 
              class="absolute inset-0 opacity-0 cursor-pointer"
              @change="handleImageChange"
            />
            <ImagePlus :size="48" class="mx-auto text-morandi-accent mb-3" />
            <p class="text-sm text-morandi-text">点击上传食物图片</p>
            <p class="text-xs text-morandi-lightText mt-1">支持 JPG、PNG 格式</p>
          </div>

          <!-- 食物列表 -->
          <div class="food-pick-list">
            <div v-if="filteredFoods.length === 0" class="text-center text-sm text-morandi-lightText py-6">没有匹配的食物</div>
            <div
              v-for="(f, idx) in filteredFoods" :key="f.foodId ?? idx"
              @click="pickFood(f)"
              :class="['food-pick-item', selectedFood && selectedFood.foodId === f.foodId ? 'bg-morandi-accent text-white' : 'hover:bg-morandi-soft text-morandi-text']"
            >
              <div class="flex justify-between items-center">
                <span class="font-medium">{{ f.foodName }} <span class="opacity-70 text-xs">({{ f.foodCategory }})</span></span>
                <span class="text-xs opacity-80">{{ f.calorie }} kcal/100g · GI {{ f.giValue ?? '-' }}</span>
              </div>
              <div class="text-xs opacity-80">
                蛋白 {{ f.protein }} g · 脂肪 {{ f.fat }} g · 碳水 {{ f.carb }} g · 钙 {{ f.calcium ?? 0 }} mg · 叶酸 {{ f.folicAcid ?? 0 }} μg · DHA {{ f.dha ?? 0 }} mg
              </div>
            </div>
          </div>

          <!-- 选中食物的分量 -->
          <div v-if="selectedFood" class="grid grid-cols-1 md:grid-cols-3 gap-3 bg-morandi-soft/40 rounded-xl p-4">
            <div class="md:col-span-2">
              <label class="block text-xs text-morandi-lightText mb-1">食用重量（克）</label>
              <input v-model.number="form.amount" type="number" min="1" class="w-full px-3 py-2 rounded-lg bg-white border border-morandi-soft text-sm" />
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">预计热量</label>
              <div class="px-3 py-2 rounded-lg bg-white border border-morandi-soft text-sm font-semibold text-morandi-accent">
                {{ roundOne((selectedFood.calorie ?? 0) * form.amount / 100) }} kcal
              </div>
            </div>
          </div>
          
          <!-- 智能食材替换建议（隐形设计，选中食物后自动显示） -->
          <div v-if="selectedFood && substitutionSuggestions.length > 0" class="bg-blue-50 rounded-xl p-4 border border-blue-100">
            <div class="flex items-center gap-2 mb-3">
              <Lightbulb :size="16" class="text-blue-500" />
              <span class="text-sm font-medium text-blue-700">营养优化建议</span>
            </div>
            <div class="space-y-2">
              <div 
                v-for="suggestion in substitutionSuggestions" 
                :key="suggestion.foodId"
                @click="pickFood(suggestion)"
                class="flex items-center justify-between p-2 rounded-lg hover:bg-blue-100 cursor-pointer transition-colors"
              >
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 flex items-center justify-center bg-blue-100 rounded-lg text-xs font-bold text-blue-600">
                    {{ suggestion.foodName.slice(0, 1) }}
                  </div>
                  <div>
                    <p class="text-sm font-medium text-blue-800">{{ suggestion.foodName }}</p>
                    <p class="text-xs text-blue-600">{{ suggestion.calorie }} kcal/100g · GI {{ suggestion.giValue ?? '-' }}</p>
                  </div>
                </div>
                <div class="text-right">
                  <div 
                    class="text-xs font-medium px-2 py-1 rounded-full"
                    :class="suggestion.calorie < selectedFood.calorie ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'"
                  >
                    {{ suggestion.calorie < selectedFood.calorie ? '更低热量' : '相近热量' }}
                  </div>
                  <p class="text-xs text-blue-600 mt-1">
                    蛋白 {{ suggestion.protein }}g · 碳水 {{ suggestion.carb }}g
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div v-if="errorMessage" class="text-xs text-red-500 text-right">{{ errorMessage }}</div>

          <div class="flex justify-end gap-3 pt-2 border-t border-morandi-soft">
            <button @click="closeAddDialog" class="px-5 py-2 rounded-lg bg-morandi-soft text-morandi-text text-sm hover:opacity-90">取消</button>
            <button :disabled="!selectedFood || saving" @click="confirmAddItem" class="px-5 py-2 rounded-lg bg-morandi-accent text-white text-sm hover:opacity-90 disabled:opacity-50">
              {{ saving ? '添加中...' : '确认添加' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Mic, ImagePlus, X, CheckCircle, MessageCircle, Lightbulb } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { useDietStore } from '@/stores/diet'
import { FOOD_CATEGORY_ORDER } from '@/constants'
import { api } from '@/api'

const userStore = useUserStore()
const dietStore = useDietStore()

const today = new Date().toISOString().slice(0, 10)

const meals = [
  { type: '早餐', label: '早餐' },
  { type: '午餐', label: '午餐' },
  { type: '晚餐', label: '晚餐' },
  { type: '加餐', label: '加餐' }
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
const currentMeal = ref<string>('午餐')
const saving = ref(false)
const errorMessage = ref('')
const mealsData = computed(() => dietStore.currentMeals)

const isRecording = ref(false)
const voiceResult = ref('')
const showImageUpload = ref(false)
const imageInput = ref<HTMLInputElement | null>(null)
const imageAnalysisResult = ref<{ foodName: string; alternatives: string[] } | null>(null)

const isDiabetes = computed(() => {
  const c = userStore.user?.crowdType || userStore.user?.crowd_type || ''
  return String(c).indexOf('糖尿') >= 0
})

const currentMealLabel = computed(() => (meals.find((m) => m.type === currentMeal.value) || meals[1]).label)

const substitutionSuggestions = computed(() => [] as Array<{ foodId: number; foodName: string; calorie: number; giValue?: number; protein: number; carb: number }>)

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
    if (m.mealType === type && Array.isArray(m.items)) {
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
const toggleVoiceInput = () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

const startRecording = () => {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    errorMessage.value = '您的浏览器不支持语音识别功能'
    return
  }
  
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  const recognition = new SpeechRecognition()
  
  recognition.lang = 'zh-CN'
  recognition.continuous = false
  recognition.interimResults = false
  
  recognition.onresult = (event: any) => {
    const transcript = event.results[0][0].transcript
    voiceResult.value = transcript
  }
  
  recognition.onerror = (event: any) => {
    errorMessage.value = '语音识别失败，请重试'
    isRecording.value = false
  }
  
  recognition.onend = () => {
    isRecording.value = false
  }
  
  recognition.start()
  isRecording.value = true
  errorMessage.value = ''
}

const stopRecording = () => {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  const recognition = new SpeechRecognition()
  recognition.stop()
}

const applyVoiceResult = () => {
  if (voiceResult.value) {
    keyword.value = voiceResult.value
    clearVoiceResult()
  }
}

const clearVoiceResult = () => {
  voiceResult.value = ''
}

// ---- 图片识别功能 ----
const triggerImageUpload = () => {
  showImageUpload.value = !showImageUpload.value
  imageAnalysisResult.value = null
}

const handleImageChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    analyzeImage(file)
  }
}

const analyzeImage = async (_file: File) => {
  imageAnalysisResult.value = null
  errorMessage.value = '图片识别暂不可用'
}

const applyImageResult = () => {
  if (imageAnalysisResult.value) {
    keyword.value = imageAnalysisResult.value.foodName
    imageAnalysisResult.value = null
    showImageUpload.value = false
  }
}

watch(
  () => form.value.date,
  () => {
    loadRecords()
  }
)

onMounted(async () => {
  userStore.init()
  await loadFoods()
  await loadRecords()
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.9);
}

.food-pick-list {
  max-height: 320px;
  overflow-y: auto;
  border: 1px solid rgba(210, 200, 190, 0.5);
  border-radius: 0.5rem;
}

.food-pick-item {
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  border-bottom: 1px solid rgba(210, 200, 190, 0.35);
  cursor: pointer;
  transition: background-color 0.15s ease;
}
.food-pick-item:last-child { border-bottom: none; }

.food-pick-list::-webkit-scrollbar {
  width: 8px;
}
.food-pick-list::-webkit-scrollbar-track {
  background: rgba(210, 200, 190, 0.15);
  border-radius: 4px;
}
.food-pick-list::-webkit-scrollbar-thumb {
  background: rgba(180, 160, 145, 0.55);
  border-radius: 4px;
}
.food-pick-list::-webkit-scrollbar-thumb:hover {
  background: rgba(150, 130, 115, 0.75);
}
.page-fade {
  animation: fadeIn 0.3s ease forwards;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
