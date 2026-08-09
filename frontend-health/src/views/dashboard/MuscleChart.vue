<template>
  <div class="max-w-5xl mx-auto">
    <div class="glass-card rounded-2xl shadow-lg overflow-hidden">
      <div class="flex items-center justify-between p-4 border-b border-morandi-soft">
        <div class="flex items-center gap-2">
          <Dumbbell class="w-5 h-5 text-morandi-accent" />
          <h3 class="text-lg font-bold text-morandi-text">运动管理</h3>
          <span class="text-xs text-morandi-lightText ml-2">点击肌肉选择部位，点击动作查看步骤说明</span>
        </div>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <button @click="currentView = 'front'"
              class="px-3 py-1.5 text-sm rounded-lg transition-colors font-medium"
              :class="currentView === 'front' ? 'bg-morandi-accent text-white' : 'bg-morandi-soft text-morandi-text hover:bg-morandi-soft/80'">
              正面
            </button>
            <button @click="currentView = 'back'"
              class="px-3 py-1.5 text-sm rounded-lg transition-colors font-medium"
              :class="currentView === 'back' ? 'bg-morandi-accent text-white' : 'bg-morandi-soft text-morandi-text hover:bg-morandi-soft/80'">
              背面
            </button>
          </div>
          <div class="flex items-center gap-2 text-xs text-morandi-lightText">
            <div class="flex items-center gap-1">
              <span class="w-3 h-3 rounded border border-morandi-accent"></span>
              <span>可训练</span>
            </div>
            <div class="flex items-center gap-1">
              <span class="w-3 h-3 rounded border border-gray-300 bg-white"></span>
              <span>不可训练</span>
            </div>
          </div>
        </div>
      </div>

      <div class="flex flex-col lg:flex-row">
        <div class="lg:w-1/2 p-4 border-b lg:border-b-0 lg:border-r">
          <div ref="chartContainerRef" class="w-full aspect-square relative chart-container" @mousemove="onMouseMove">
            <Transition name="fade">
              <div v-if="tooltipData"
                class="absolute pointer-events-none z-30 bg-white/95 backdrop-blur-sm px-3 py-2 rounded-lg shadow-xl border border-morandi-accent/20"
                :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }"
              >
                <p class="font-bold text-morandi-text text-sm whitespace-nowrap">{{ tooltipData.name }}</p>
                <p class="text-xs text-morandi-accent">{{ tooltipData.group }}</p>
              </div>
            </Transition>
          </div>
        </div>

        <div class="lg:w-1/2 p-4">
          <div v-if="selectedGroup" class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="font-bold text-morandi-text text-lg">
                  {{ muscleGroupNameMap[selectedGroup] || selectedGroup }}
                </h4>
                <p class="text-sm text-morandi-lightText">
                  <span class="text-morandi-accent">{{ matchedExercises.length }}</span> 个可训练动作
                </p>
              </div>
              <button @click="clearSelection" class="text-sm text-morandi-lightText hover:text-morandi-text px-3 py-1 rounded-lg hover:bg-morandi-soft transition-colors">
                取消选择
              </button>
            </div>

            <div class="space-y-2 max-h-[280px] overflow-y-auto pr-1 scrollbar-thin">
              <div v-for="exercise in matchedExercises" :key="exercise.id"
                class="flex items-center justify-between p-3 bg-morandi-soft/30 rounded-xl cursor-pointer hover:bg-morandi-accent/10 hover:ring-1 hover:ring-morandi-accent/20 transition-all"
                :class="{ 'ring-2 ring-morandi-accent bg-morandi-accent/10': selectedExercise?.id === exercise.id }"
                @click="selectedExercise = exercise"
              >
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 flex items-center justify-center bg-morandi-accent/10 rounded-lg shrink-0">
                    <Activity class="w-5 h-5 text-morandi-accent" />
                  </div>
                  <div>
                    <p class="font-medium text-morandi-text">{{ exercise.name }}</p>
                    <p class="text-xs text-morandi-lightText">MET {{ exercise.met }} · {{ exercise.difficulty }}</p>
                  </div>
                </div>
                <button
                  @click.stop="openStepsModal(exercise.id)"
                  class="px-2 py-1 rounded-lg bg-morandi-accent/10 text-morandi-accent text-xs hover:bg-morandi-accent/20 transition-colors whitespace-nowrap"
                >
                  步骤说明
                </button>
              </div>
            </div>

            <Transition name="fade">
              <div v-if="selectedExercise" class="p-4 bg-gradient-to-br from-morandi-accent/5 to-teal-50 rounded-xl border border-morandi-accent/10">
                <div class="flex items-center justify-between mb-3">
                  <h4 class="font-bold text-morandi-text">{{ selectedExercise.name }}</h4>
                  <button @click="openStepsModal(selectedExercise.id)" class="text-xs text-morandi-accent hover:underline">
                    查看完整步骤 →
                  </button>
                </div>

                <div class="flex flex-wrap gap-2 mb-3">
                  <span class="px-2 py-1 rounded-full bg-morandi-accent/10 text-morandi-accent text-xs">{{ selectedExercise.category }}</span>
                  <span class="px-2 py-1 rounded-full bg-morandi-soft text-morandi-text text-xs">{{ selectedExercise.difficulty }}</span>
                  <span class="px-2 py-1 rounded-full bg-morandi-soft text-morandi-text text-xs">{{ selectedExercise.equipment }}</span>
                </div>

                <!-- 训练参数输入 -->
                <div class="grid grid-cols-2 gap-3 mb-3">
                  <div class="flex items-center justify-between text-sm bg-white/60 rounded-lg px-3 py-2">
                    <span class="text-morandi-lightText">时长</span>
                    <div class="flex items-center gap-2">
                      <button @click="duration = Math.max(5, duration - 5)" class="w-7 h-7 flex items-center justify-center bg-white rounded-lg hover:bg-morandi-soft transition-colors shadow-sm">
                        <Minus class="w-3.5 h-3.5 text-morandi-text" />
                      </button>
                      <span class="font-bold w-12 text-center text-morandi-text tabular-nums">{{ duration }}</span>
                      <button @click="duration = Math.min(180, duration + 5)" class="w-7 h-7 flex items-center justify-center bg-white rounded-lg hover:bg-morandi-soft transition-colors shadow-sm">
                        <Plus class="w-3.5 h-3.5 text-morandi-text" />
                      </button>
                      <span class="text-morandi-lightText text-xs w-8">分钟</span>
                    </div>
                  </div>
                  <div class="flex items-center justify-between text-sm bg-white/60 rounded-lg px-3 py-2">
                    <span class="text-morandi-lightText">重量</span>
                    <div class="flex items-center gap-2">
                      <button @click="weight = Math.max(0, round(weight - 2.5))" class="w-7 h-7 flex items-center justify-center bg-white rounded-lg hover:bg-morandi-soft transition-colors shadow-sm">
                        <Minus class="w-3.5 h-3.5 text-morandi-text" />
                      </button>
                      <span class="font-bold w-12 text-center text-morandi-text tabular-nums">{{ weight > 0 ? weight : '自重' }}</span>
                      <button @click="weight = round(weight + 2.5)" class="w-7 h-7 flex items-center justify-center bg-white rounded-lg hover:bg-morandi-soft transition-colors shadow-sm">
                        <Plus class="w-3.5 h-3.5 text-morandi-text" />
                      </button>
                      <span class="text-morandi-lightText text-xs w-8" v-if="weight > 0">kg</span>
                      <span class="text-morandi-lightText text-xs w-8" v-else></span>
                    </div>
                  </div>
                  <div class="flex items-center justify-between text-sm bg-white/60 rounded-lg px-3 py-2">
                    <span class="text-morandi-lightText">组数</span>
                    <div class="flex items-center gap-2">
                      <button @click="sets = Math.max(1, sets - 1)" class="w-7 h-7 flex items-center justify-center bg-white rounded-lg hover:bg-morandi-soft transition-colors shadow-sm">
                        <Minus class="w-3.5 h-3.5 text-morandi-text" />
                      </button>
                      <span class="font-bold w-12 text-center text-morandi-text tabular-nums">{{ sets }}</span>
                      <button @click="sets = Math.min(10, sets + 1)" class="w-7 h-7 flex items-center justify-center bg-white rounded-lg hover:bg-morandi-soft transition-colors shadow-sm">
                        <Plus class="w-3.5 h-3.5 text-morandi-text" />
                      </button>
                      <span class="text-morandi-lightText text-xs w-8">组</span>
                    </div>
                  </div>
                  <div class="flex items-center justify-between text-sm bg-white/60 rounded-lg px-3 py-2">
                    <span class="text-morandi-lightText">每组</span>
                    <div class="flex items-center gap-2">
                      <button @click="reps = Math.max(1, reps - 2)" class="w-7 h-7 flex items-center justify-center bg-white rounded-lg hover:bg-morandi-soft transition-colors shadow-sm">
                        <Minus class="w-3.5 h-3.5 text-morandi-text" />
                      </button>
                      <span class="font-bold w-12 text-center text-morandi-text tabular-nums">{{ reps }}</span>
                      <button @click="reps = Math.min(30, reps + 2)" class="w-7 h-7 flex items-center justify-center bg-white rounded-lg hover:bg-morandi-soft transition-colors shadow-sm">
                        <Plus class="w-3.5 h-3.5 text-morandi-text" />
                      </button>
                      <span class="text-morandi-lightText text-xs w-8">次</span>
                    </div>
                  </div>
                </div>

                <!-- 日期选择 -->
                <div class="flex items-center gap-3 mb-3">
                  <span class="text-xs text-morandi-lightText">训练日期</span>
                  <input v-model="recordDate" type="date" class="flex-1 px-3 py-1.5 rounded-lg bg-white/70 border border-morandi-soft text-sm outline-none focus:border-morandi-accent" />
                </div>

                <div class="grid grid-cols-3 gap-3 mb-3 text-center">
                  <div class="bg-white/60 rounded-lg py-2">
                    <div class="text-[11px] text-morandi-lightText">总组数</div>
                    <div class="font-bold text-morandi-text">{{ sets }}</div>
                  </div>
                  <div class="bg-white/60 rounded-lg py-2">
                    <div class="text-[11px] text-morandi-lightText">总次数</div>
                    <div class="font-bold text-morandi-text">{{ sets * reps }}</div>
                  </div>
                  <div class="bg-white/60 rounded-lg py-2">
                    <div class="text-[11px] text-morandi-lightText">消耗</div>
                    <div class="font-bold text-morandi-accent">{{ calories }} <span class="text-[10px]">kcal</span></div>
                  </div>
                </div>

                <button @click="saveRecord" class="w-full py-2.5 bg-morandi-accent text-white rounded-xl hover:bg-morandi-accentDark transition-colors font-medium shadow-sm hover:shadow-md active:scale-[0.98]">
                  保存训练记录
                </button>
              </div>
            </Transition>
          </div>

          <div v-else class="h-full min-h-[300px] flex flex-col items-center justify-center text-morandi-lightText">
            <MousePointerClick class="w-12 h-12 mb-3 opacity-50" />
            <p class="text-sm">点击左侧肌肉选择训练部位</p>
            <p class="text-xs mt-1">记录将同步到「训练计划」页</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 动作步骤说明弹窗 -->
    <div v-if="showSteps" class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" @click.self="showSteps = false">
      <div class="bg-white rounded-2xl max-w-lg w-full shadow-xl max-h-[85vh] overflow-hidden flex flex-col">
        <div class="flex items-center justify-between p-5 border-b border-morandi-soft">
          <div>
            <h3 class="text-lg font-semibold text-morandi-text">{{ currentExercise?.name }}</h3>
            <p class="text-xs text-morandi-lightText mt-0.5">动作步骤说明</p>
          </div>
          <button @click="showSteps = false" class="text-morandi-lightText hover:text-morandi-text text-2xl leading-none">×</button>
        </div>
        <div v-if="currentExercise" class="p-5 overflow-y-auto space-y-4">
          <div class="flex flex-wrap gap-2">
            <span class="px-2 py-1 rounded-full bg-morandi-accent/10 text-morandi-accent text-xs">{{ currentExercise.category }}</span>
            <span class="px-2 py-1 rounded-full bg-morandi-soft text-morandi-text text-xs">MET {{ currentExercise.met }}</span>
            <span class="px-2 py-1 rounded-full bg-morandi-soft text-morandi-text text-xs">{{ currentExercise.difficulty }}</span>
          </div>

          <div class="bg-morandi-soft/20 rounded-xl p-3">
            <div class="text-xs text-morandi-lightText mb-1">所需器械</div>
            <div class="text-sm text-morandi-text font-medium">{{ currentExercise.equipment }}</div>
          </div>

          <div>
            <div class="flex items-center gap-2 mb-3">
              <div class="w-1 h-4 bg-morandi-accent rounded-full"></div>
              <div class="text-sm font-semibold text-morandi-text">动作步骤</div>
            </div>
            <ol class="space-y-3">
              <li v-for="(step, i) in currentExercise.steps" :key="i" class="flex gap-3">
                <span class="w-7 h-7 flex items-center justify-center rounded-full bg-morandi-accent text-white text-xs font-semibold shrink-0">{{ i + 1 }}</span>
                <div class="flex-1">
                  <div class="text-sm font-medium text-morandi-text">{{ step.title }}</div>
                  <div class="text-xs text-morandi-lightText mt-0.5 leading-relaxed">{{ step.description }}</div>
                </div>
              </li>
            </ol>
          </div>

          <div v-if="currentExercise.tips?.length">
            <div class="flex items-center gap-2 mb-3">
              <div class="w-1 h-4 bg-amber-500 rounded-full"></div>
              <div class="text-sm font-semibold text-morandi-text">训练提示</div>
            </div>
            <ul class="space-y-2">
              <li v-for="(tip, i) in currentExercise.tips" :key="i" class="flex gap-2 text-xs text-amber-800 bg-amber-50 px-3 py-2 rounded-lg">
                <span class="text-amber-500 shrink-0">⚠</span>
                <span>{{ tip }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- 保存成功提示 -->
    <Transition name="fade">
      <div v-if="savedTip" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-morandi-accent text-white px-5 py-2.5 rounded-xl shadow-lg text-sm font-medium">
        ✓ 训练记录已保存，可在「训练计划」查看
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Dumbbell, Activity, MousePointerClick, Plus, Minus } from 'lucide-vue-next'
import { BodyChart, ViewSide, extractMuscleGroup, filterMuscles, INTENSITY_COLORS } from 'body-muscles'
import { EXERCISES, getExercisesByMuscle, type ExerciseDetail } from '@/data/exercises'
import { useUserStore } from '@/stores/user'
import { useWorkoutRecords, type Intensity } from '@/composables/useWorkoutRecords'

INTENSITY_COLORS[1] = '#ffffff'

const userStore = useUserStore()
const workout = useWorkoutRecords()

const currentView = ref<'front' | 'back'>('front')
const selectedGroup = ref<string | null>(null)
const hoveredGroup = ref<string | null>(null)
const selectedExercise = ref<ExerciseDetail | null>(null)
const tooltipData = ref<{ name: string; group: string } | null>(null)
const tooltipPos = ref({ x: 0, y: 0 })

// 训练参数
const duration = ref(30)
const weight = ref(0)
const sets = ref(3)
const reps = ref(10)
const recordDate = ref(new Date().toISOString().slice(0, 10))

// 保存成功提示
const savedTip = ref(false)

const chartContainerRef = ref<HTMLElement | null>(null)
let bodyChart: BodyChart | null = null

const trainableGroups: string[] = [
  'chest', 'shoulder', 'deltoid', 'biceps', 'triceps', 'forearm',
  'abs', 'obliques', 'serratus', 'lats', 'traps', 'lower',
  'gluteus', 'quads', 'adductors', 'hamstrings', 'calves', 'tibialis', 'hip',
]

const muscleGroupNameMap: Record<string, string> = {
  'chest': '胸肌', 'shoulder': '三角肌', 'deltoid': '三角肌后束',
  'biceps': '肱二头肌', 'triceps': '肱三头肌', 'forearm': '前臂',
  'abs': '腹肌', 'obliques': '侧腹肌', 'serratus': '前锯肌',
  'lats': '背阔肌', 'traps': '斜方肌', 'lower': '下背部',
  'gluteus': '臀肌', 'quads': '股四头肌', 'adductors': '内收肌',
  'hamstrings': '腘绳肌', 'calves': '小腿肌', 'tibialis': '胫骨前肌', 'hip': '髋屈肌',
}

const muscleGroupCategoryMap: Record<string, string> = {
  'chest': '胸部', 'shoulder': '肩部', 'deltoid': '肩部',
  'biceps': '手臂', 'triceps': '手臂', 'forearm': '手臂',
  'abs': '腹部', 'obliques': '腹部', 'serratus': '腹部',
  'lats': '背部', 'traps': '背部', 'lower': '背部',
  'gluteus': '臀部', 'quads': '大腿', 'adductors': '大腿', 'hamstrings': '大腿',
  'calves': '小腿', 'tibialis': '小腿', 'hip': '臀部',
}

const matchedExercises = computed(() => {
  if (!selectedGroup.value) return []
  return getExercisesByMuscle(selectedGroup.value)
})

const userWeight = computed(() => Number(userStore.user?.weight) || 65)

const calories = computed(() => {
  if (!selectedExercise.value) return 0
  return workout.calcCalories(selectedExercise.value.met, userWeight.value, duration.value)
})

function round(n: number): number {
  return Math.round(n * 10) / 10
}

// ===== 动作步骤弹窗 =====
const showSteps = ref(false)
const currentExercise = ref<ExerciseDetail | null>(null)

function openStepsModal(id: number) {
  const ex = EXERCISES.find(e => e.id === id)
  if (ex) {
    currentExercise.value = ex
    showSteps.value = true
  }
}

// ===== 保存训练记录 =====
function saveRecord() {
  if (!selectedExercise.value) return
  const ex = selectedExercise.value
  // 根据重量/组数推断强度
  let intensity: Intensity = 'medium'
  if (weight.value > 0) {
    if (weight.value >= userWeight.value * 0.8 || sets.value * reps.value >= 40) intensity = 'high'
    else if (weight.value < userWeight.value * 0.3 && sets.value <= 2) intensity = 'low'
  } else {
    if (duration.value >= 40 && sets.value >= 4) intensity = 'high'
    else if (duration.value <= 20 && sets.value <= 2) intensity = 'low'
  }

  workout.add({
    exerciseId: ex.id,
    exerciseName: ex.name,
    muscleGroup: ex.muscleGroup,
    category: ex.category,
    date: recordDate.value,
    duration: duration.value,
    sets: sets.value,
    reps: reps.value,
    weight: weight.value,
    intensity,
    calories: calories.value
  })

  // 提示
  savedTip.value = true
  setTimeout(() => { savedTip.value = false }, 2200)

  // 重置选择，保留参数
  clearSelection()
}

let groupToIds: Record<string, string[]> = {}

function buildSymmetryMap() {
  groupToIds = {}
  const allFront = filterMuscles(ViewSide.FRONT) as { id: string }[]
  const allBack = filterMuscles(ViewSide.BACK) as { id: string }[]
  const allIds = [...allFront.map(m => m.id), ...allBack.map(m => m.id)]

  allIds.forEach(id => {
    const group = extractMuscleGroup(id) || id
    if (!groupToIds[group]) groupToIds[group] = []
    if (!groupToIds[group].includes(id)) groupToIds[group].push(id)
  })
}

let cachedState: Record<string, { intensity: number; selected: boolean }> = {}

function stateChanged(newState: Record<string, { intensity: number; selected: boolean }>): boolean {
  const newKeys = Object.keys(newState)
  const cachedKeys = Object.keys(cachedState)
  if (newKeys.length !== cachedKeys.length) return true
  for (const key of newKeys) {
    const newVal = newState[key]
    const cachedVal = cachedState[key]
    if (!cachedVal || newVal.intensity !== cachedVal.intensity || newVal.selected !== cachedVal.selected) return true
  }
  return false
}

function setMuscleColors() {
  if (!bodyChart) return
  const state: Record<string, { intensity: number; selected: boolean }> = {}
  Object.keys(groupToIds).forEach(group => {
    groupToIds[group].forEach(id => {
      state[id] = { intensity: trainableGroups.includes(group) ? 0 : 1, selected: false }
    })
  })
  if (stateChanged(state)) {
    cachedState = { ...state }
    bodyChart.update({ bodyState: state })
    setTimeout(setNonTrainableStyles, 50)
  }
}

function setNonTrainableStyles() {
  if (!chartContainerRef.value) return
  const container = chartContainerRef.value!
  container.querySelectorAll('[data-muscle-id]').forEach(el => {
    const id = el.getAttribute('data-muscle-id')
    const svgEl = el as unknown as HTMLElement
    if (id) {
      const group = extractMuscleGroup(id) || id
      if (!trainableGroups.includes(group)) {
        svgEl.style.setProperty('stroke', '#d1d5db', 'important')
        svgEl.style.setProperty('stroke-width', '0.5', 'important')
        svgEl.style.setProperty('pointer-events', 'none', 'important')
      }
    }
  })
}

function updateMuscleStates(group: string | null, intensity: number, selected: boolean) {
  if (!group || !bodyChart) return
  const state: Record<string, { intensity: number; selected: boolean }> = {}
  Object.keys(groupToIds).forEach(g => {
    groupToIds[g].forEach(id => {
      if (g === group) {
        state[id] = { intensity, selected }
      } else {
        const isSelectedGroup = g === selectedGroup.value
        state[id] = { intensity: isSelectedGroup ? 8 : (trainableGroups.includes(g) ? 0 : 1), selected: isSelectedGroup }
      }
    })
  })
  if (stateChanged(state)) {
    cachedState = { ...state }
    bodyChart.update({ bodyState: state })
    setTimeout(setNonTrainableStyles, 50)
  }
}

function clearMuscleStates() {
  setMuscleColors()
}

function handleMuscleClick(id: string) {
  const group = extractMuscleGroup(id) || id
  if (!trainableGroups.includes(group)) return
  if (selectedGroup.value === group) {
    clearMuscleStates()
    selectedGroup.value = null
    selectedExercise.value = null
  } else {
    clearMuscleStates()
    updateMuscleStates(group, 8, true)
    selectedGroup.value = group
    selectedExercise.value = null
  }
}

function handleMuscleHover(id: string | null) {
  if (id) {
    const group = extractMuscleGroup(id) || id
    if (!trainableGroups.includes(group)) {
      tooltipData.value = null
      return
    }
    if (selectedGroup.value === group) {
      hoveredGroup.value = group
      tooltipData.value = { name: muscleGroupNameMap[group] || group, group: muscleGroupCategoryMap[group] || '其他' }
      return
    }
    if (hoveredGroup.value && hoveredGroup.value !== selectedGroup.value) {
      updateMuscleStates(hoveredGroup.value, 0, false)
    }
    updateMuscleStates(group, 4, false)
    hoveredGroup.value = group
    tooltipData.value = { name: muscleGroupNameMap[group] || group, group: muscleGroupCategoryMap[group] || '其他' }
  } else {
    if (hoveredGroup.value && hoveredGroup.value !== selectedGroup.value) {
      updateMuscleStates(hoveredGroup.value, 0, false)
    }
    hoveredGroup.value = null
    tooltipData.value = null
  }
}

function onMouseMove(event: MouseEvent) {
  const container = chartContainerRef.value
  if (!container) return
  const rect = container.getBoundingClientRect()
  tooltipPos.value = { x: event.clientX - rect.left + 10, y: event.clientY - rect.top - 40 }
}

function clearSelection() {
  clearMuscleStates()
  selectedGroup.value = null
  selectedExercise.value = null
}

watch(currentView, (view) => {
  clearMuscleStates()
  selectedGroup.value = null
  selectedExercise.value = null
  if (bodyChart) {
    bodyChart.update({ view: view === 'front' ? ViewSide.FRONT : ViewSide.BACK })
    setTimeout(setMuscleColors, 300)
  }
})

onMounted(() => {
  try { userStore.init() } catch { /* ignore */ }
  buildSymmetryMap()
  if (chartContainerRef.value) {
    bodyChart = new BodyChart(chartContainerRef.value, {
      view: ViewSide.FRONT,
      bodyState: {},
      onMuscleClick: handleMuscleClick,
      onMuscleHover: handleMuscleHover,
    })
    setTimeout(setMuscleColors, 500)
  }
})

onUnmounted(() => {
  if (bodyChart) bodyChart.destroy()
})
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.chart-container {
  min-height: 400px;
}

.chart-container :deep(svg) {
  overflow: visible;
}

.chart-container :deep([data-muscle-id]) {
  transition: transform 0.15s ease;
  transform-box: fill-box;
  transform-origin: center;
}

.chart-container :deep([data-muscle-id]:hover) {
  transform: scale(1.1);
  cursor: pointer;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.scrollbar-thin::-webkit-scrollbar {
  width: 4px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background: #e5e7eb;
  border-radius: 2px;
}
</style>
