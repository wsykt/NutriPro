<template>
  <div class="body-muscle-chart">
    <!-- 视图切换 -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-base font-semibold text-morandi-text">人体肌肉图</h3>
      <div class="flex items-center gap-2 bg-morandi-soft/40 rounded-full p-1">
        <button
          v-for="v in views"
          :key="v.value"
          :class="[
            'px-4 py-1.5 rounded-full text-xs font-medium transition-all duration-300',
            currentView === v.value ? 'bg-morandi-accent text-white shadow-sm' : 'text-morandi-lightText hover:text-morandi-text'
          ]"
          @click="switchView(v.value)"
        >{{ v.label }}</button>
      </div>
    </div>

    <!-- 肌肉图容器 -->
    <div
      ref="chartContainer"
      class="chart-container relative bg-gradient-to-b from-morandi-soft/20 to-white rounded-2xl border border-morandi-soft/40 overflow-hidden"
    >
      <!-- 背景装饰 -->
      <div class="absolute inset-0 pointer-events-none opacity-30">
        <div class="absolute top-4 left-4 w-16 h-16 rounded-full bg-morandi-accent/5"></div>
        <div class="absolute bottom-4 right-4 w-20 h-20 rounded-full bg-morandi-accent/5"></div>
      </div>

      <!-- SVG 渲染区域 -->
      <div ref="chartRef" class="chart-svg-wrapper w-full h-full flex items-center justify-center"></div>

      <!-- 悬停提示 -->
      <div
        v-if="hoveredMuscle"
        class="absolute top-3 left-3 px-3 py-1.5 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg border border-morandi-soft/50 text-xs font-medium text-morandi-accent"
      >
        {{ hoveredMuscle }}
      </div>

      <!-- 图例 -->
      <div class="absolute bottom-3 right-3 flex items-center gap-1">
        <span class="text-[10px] text-morandi-lightText mr-1">强度</span>
        <div v-for="(label, i) in intensityLabels" :key="i" class="w-3 h-3 rounded-sm" :style="{ background: intensityColors[i] }" :title="label"></div>
      </div>
    </div>

    <!-- 选中肌肉信息 -->
    <div v-if="selectedMuscle" class="mt-4 p-4 bg-morandi-accent/5 rounded-xl border border-morandi-accent/20">
      <div class="flex items-center justify-between">
        <div>
          <span class="text-sm font-medium text-morandi-text">{{ selectedMuscle.name }}</span>
          <span class="text-xs text-morandi-lightText ml-2">ID: {{ selectedMuscle.id }}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-morandi-lightText">强度</span>
          <input
            type="range"
            min="0"
            max="10"
            :value="selectedMuscleIntensity"
            @input="setIntensity(Number(($event.target as HTMLInputElement).value))"
            class="w-24 accent-morandi-accent"
          />
          <span class="text-sm font-semibold text-morandi-accent w-6 text-right">{{ selectedMuscleIntensity }}</span>
          <button
            @click="clearSelection"
            class="w-6 h-6 rounded-full bg-morandi-soft flex items-center justify-center text-morandi-lightText hover:bg-red-100 hover:text-red-500 transition-colors"
          >
            <X class="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { BodyChart, ViewSide } from 'body-muscles'
import { X } from 'lucide-vue-next'
import type { MuscleId, BodyState } from 'body-muscles'

const emit = defineEmits<{
  (e: 'muscle-clicked', id: string, name: string): void
}>()

interface SelectedMuscle {
  id: string
  name: string
}

const views = [
  { value: ViewSide.FRONT, label: '正面' },
  { value: ViewSide.BACK, label: '背面' }
]

const intensityColors = [
  '#f1f5f9', '#fef9c3', '#fef08a', '#fde047', '#fbbf24',
  '#f59e0b', '#f97316', '#ef4444', '#dc2626', '#b91c1c', '#7f1d1d'
]

const intensityLabels = ['0 无', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10 最大']

const chartRef = ref<HTMLElement | null>(null)
const chartContainer = ref<HTMLElement | null>(null)
const currentView = ref<ViewSide>(ViewSide.FRONT)
const bodyState = ref<BodyState>({})
const hoveredMuscle = ref<string | null>(null)
const selectedMuscle = ref<SelectedMuscle | null>(null)
const selectedMuscleIntensity = ref(0)

let chartInstance: BodyChart | null = null
let resizeObserver: ResizeObserver | null = null

// 可训练的肌肉 ID 前缀（与 trainingData 对应）
const trainablePrefixes = [
  'chest', 'shoulder', 'biceps', 'triceps', 'abs', 'obliques',
  'traps', 'lats', 'rhomboids', 'deltoid', 'deltoids',
  'hamstrings', 'quads', 'glutes', 'calves', 'adductors',
  'tibialis', 'neck', 'forearm'
]

function isTrainable(id: string): boolean {
  return trainablePrefixes.some(p => id.includes(p))
}

function applyUntrainableWhite() {
  if (!chartRef.value) return
  const svg = chartRef.value.querySelector('svg')
  if (!svg) return
  const paths = svg.querySelectorAll('path')
  paths.forEach(path => {
    const id = path.getAttribute('id') || ''
    if (id && !isTrainable(id)) {
      path.style.fill = '#ffffff'
      path.style.pointerEvents = 'none'
      path.style.cursor = 'default'
    }
  })
}

function initChart() {
  if (!chartRef.value) return

  chartInstance?.destroy()

  chartInstance = new BodyChart(chartRef.value, {
    view: currentView.value,
    bodyState: bodyState.value,
    showViewLabel: false,
    enableTransitions: true,
    className: 'body-muscle-svg',
    onMuscleClick: handleMuscleClick,
    onMuscleHover: handleMuscleHover
  })

  applySvgStyles()
  nextTick(applyUntrainableWhite)
}

function applySvgStyles() {
  if (!chartRef.value) return
  const svg = chartRef.value.querySelector('svg')
  if (svg) {
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet')
    svg.style.width = '100%'
    svg.style.height = '100%'
    svg.style.maxHeight = '100%'
    svg.style.display = 'block'
  }

  const wrappers = chartRef.value.querySelectorAll('div')
  wrappers.forEach(w => {
    const style = (w as HTMLElement).style
    if (style.position === 'relative' || style.position === 'absolute') {
      style.width = '100%'
      style.height = '100%'
    }
  })
}

function switchView(view: ViewSide) {
  currentView.value = view
  if (chartInstance) {
    chartInstance.update({ view })
    nextTick(() => {
      applySvgStyles()
      applyUntrainableWhite()
    })
  }
}

function handleMuscleClick(id: MuscleId, name: string) {
  selectedMuscle.value = { id, name }
  const cur = bodyState.value[id]
  selectedMuscleIntensity.value = cur?.intensity ?? 0

  const newState: BodyState = {}
  // 清除所有肌肉的选中状态
  for (const [key, val] of Object.entries(bodyState.value)) {
    if (val?.selected) {
      newState[key] = { ...val, selected: false }
    } else if (val) {
      newState[key] = val
    }
  }
  // 仅当前肌肉保持选中
  newState[id] = {
    intensity: cur?.intensity ?? selectedMuscleIntensity.value,
    selected: true
  }
  bodyState.value = newState
  updateChart()
  emit('muscle-clicked', id, name)
}

function handleMuscleHover(id: MuscleId | null) {
  hoveredMuscle.value = id ? getMuscleName(id) : null
}

function getMuscleName(id: string): string {
  const nameMap: Record<string, string> = {
    'biceps': '肱二头肌',
    'triceps': '肱三头肌',
    'chest': '胸部',
    'shoulder': '肩部',
    'abs': '腹肌',
    'obliques': '腹斜肌',
    'back': '背部',
    'latissimus': '背阔肌',
    'trapezius': '斜方肌',
    'hamstrings': '腘绳肌',
    'quadriceps': '股四头肌',
    'glutes': '臀大肌',
    'calves': '小腿肌肉',
    'neck': '颈部',
    'forearms': '前臂',
    'hands': '手部',
    'feet': '足部',
    'thighs': '大腿',
    'adductors': '内收肌',
    'deltoids': '三角肌'
  }

  for (const [key, val] of Object.entries(nameMap)) {
    if (id.includes(key)) return val
  }
  return id
}

function setIntensity(value: number) {
  if (!selectedMuscle.value) return
  selectedMuscleIntensity.value = value

  const cur = bodyState.value[selectedMuscle.value.id]
  bodyState.value = {
    ...bodyState.value,
    [selectedMuscle.value.id]: {
      intensity: value,
      selected: cur?.selected ?? true
    }
  }
  updateChart()
}

function clearSelection() {
  if (!selectedMuscle.value) return
  const id = selectedMuscle.value.id
  const cur = bodyState.value[id]
  if (cur) {
    bodyState.value = {
      ...bodyState.value,
      [id]: { ...cur, selected: false }
    }
    updateChart()
  }
  selectedMuscle.value = null
  selectedMuscleIntensity.value = 0
}

function updateChart() {
  if (chartInstance) {
    chartInstance.update({ bodyState: bodyState.value })
    nextTick(applyUntrainableWhite)
  }
}

onMounted(async () => {
  await nextTick()
  initChart()

  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      applySvgStyles()
      applyUntrainableWhite()
    })
    resizeObserver.observe(chartRef.value)
    if (chartContainer.value) {
      resizeObserver.observe(chartContainer.value)
    }
  }
})

onUnmounted(() => {
  chartInstance?.destroy()
  chartInstance = null
  resizeObserver?.disconnect()
})

watch(currentView, () => {
  nextTick(() => {
    applySvgStyles()
    applyUntrainableWhite()
  })
})

defineExpose({
  getBodyState: () => bodyState.value,
  setBodyState: (state: BodyState) => {
    bodyState.value = state
    updateChart()
  }
})
</script>

<style scoped>
.body-muscle-chart {
  width: 100%;
}

.chart-container {
  aspect-ratio: 3 / 4;
  max-height: 500px;
  min-height: 320px;
}

@media (max-width: 768px) {
  .chart-container {
    aspect-ratio: 2 / 3;
    max-height: 420px;
  }
}

.chart-svg-wrapper {
  padding: 12px;
}

.chart-svg-wrapper :deep(svg) {
  width: 100% !important;
  height: 100% !important;
  max-height: 100%;
}

.chart-svg-wrapper :deep(svg path) {
  transition: fill 0.2s ease, filter 0.2s ease;
}

.chart-svg-wrapper :deep(svg path:hover) {
  filter: brightness(0.9) drop-shadow(0 2px 4px rgba(47, 93, 74, 0.3));
  cursor: pointer;
}
</style>
