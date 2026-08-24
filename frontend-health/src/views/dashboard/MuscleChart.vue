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
                  <span class="text-morandi-accent">{{ currentTabActions.length }}</span> 个推荐动作
                </p>
              </div>
              <button @click="clearSelection" class="text-sm text-morandi-lightText hover:text-morandi-text px-3 py-1 rounded-lg hover:bg-morandi-soft transition-colors">
                取消选择
              </button>
            </div>

            <!-- ========== 训练推荐（部位 tab + 水平设置 + 难度筛选 + 卡片） ========== -->
              <!-- 细分切换（整体名 + 手动细分） -->
              <div v-if="currentSubdivisions" class="flex items-center gap-1.5 flex-wrap">
                <span class="text-xs font-medium text-morandi-text">细分</span>
                <button
                  v-for="sub in currentSubdivisions" :key="sub.key"
                  @click="selectSubdivision(sub.key)"
                  class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                  :class="selectedSubdivision === sub.key ? 'text-white shadow-sm' : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'"
                  :style="selectedSubdivision === sub.key ? { background: '#2F5D4A' } : {}"
                >{{ sub.label }}</button>
              </div>

              <!-- 我的训练水平设置 -->
              <div class="p-3 rounded-xl bg-morandi-accent/5 border border-morandi-accent/15">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs font-medium text-morandi-text flex items-center gap-1.5">
                    <Target class="w-3.5 h-3.5 text-morandi-accent" />
                    我的{{ muscleGroupNameMap[selectedGroup] || '' }}训练水平
                  </span>
                  <span v-if="currentLevel" class="text-[11px] text-morandi-lightText">可练到：<b class="text-morandi-accent">{{ currentLevel }}</b></span>
                </div>
                <div class="flex flex-wrap gap-1.5">
                  <button
                    v-for="lv in LEVEL_OPTIONS" :key="lv.value"
                    @click="setMuscleLevel(lv.value)"
                    class="px-2.5 py-1 rounded-full text-[11px] font-medium transition-all"
                    :class="currentLevel === lv.value ? 'text-white shadow-sm' : 'bg-white text-slate-500 hover:bg-slate-100 border border-slate-200'"
                    :style="currentLevel === lv.value ? { background: '#2F5D4A' } : {}"
                  >{{ lv.label }}</button>
                  <button
                    @click="setMuscleLevel('')"
                    class="px-2.5 py-1 rounded-full text-[11px] font-medium transition-all"
                    :class="!currentLevel ? 'text-white shadow-sm' : 'bg-white text-slate-400 hover:bg-slate-100 border border-dashed border-slate-300'"
                    :style="!currentLevel ? { background: '#2F5D4A' } : {}"
                  >未设置</button>
                </div>
                <p class="text-[11px] text-morandi-lightText mt-2 leading-relaxed">
                  <span v-if="currentLevel">已按你的水平筛选：仅显示难度 ≤ {{ currentLevel }} 的动作，从入门开始递进。</span>
                  <span v-else>未设置：显示该部位全部动作，按入门 → 高级递进排序。</span>
                </p>
              </div>

              <!-- 部位快速切换 -->
              <div class="flex flex-wrap gap-1.5">
                <button
                  v-for="mg in relatedTrainingGroups" :key="mg.key"
                  @click="selectTrainingGroup(mg.key)"
                  class="px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all"
                  :class="selectedTrainingKey === mg.key ? 'text-white shadow-sm' : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'"
                  :style="selectedTrainingKey === mg.key ? { background: mg.color } : {}"
                >{{ mg.label }}</button>
              </div>

              <!-- 难度筛选 -->
              <div class="flex items-center gap-1.5">
                <span class="text-xs text-slate-400">筛选：</span>
                <button
                  v-for="lv in levelOptions" :key="lv"
                  @click="selectedLevel = lv"
                  class="px-2.5 py-1 rounded-full text-[11px] font-medium transition-all"
                  :class="selectedLevel === lv ? 'text-white shadow-sm' : 'text-slate-500 bg-slate-100 hover:bg-slate-200'"
                  :style="selectedLevel === lv ? { background: '#2F5D4A' } : {}"
                >{{ lv }}</button>
              </div>

              <!-- 动作卡片网格 -->
              <div class="space-y-2 max-h-[380px] overflow-y-auto pr-1 scrollbar-thin">
                <div
                  v-for="(ex, idx) in currentTabActions" :key="ex.name"
                  class="p-3 bg-white/80 rounded-xl border border-slate-200/70 hover:border-morandi-accent/30 hover:shadow-sm transition-all cursor-pointer"
                  @click="openRecordModal(ex)"
                >
                  <div class="flex items-start justify-between gap-2">
                    <div>
                      <p class="font-medium text-morandi-text text-sm">{{ ex.name }}</p>
                      <p class="text-[11px] text-morandi-lightText mt-0.5">
                        MET {{ Number(ex.met).toFixed(1) }}
                        <span class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] font-medium text-white" :style="{ background: getLevelColor(ex.level) }">{{ ex.level }}</span>
                      </p>
                    </div>
                    <button
                      @click.stop="openExplainModal(ex)"
                      class="px-2 py-0.5 rounded-lg text-[11px] font-medium whitespace-nowrap shrink-0 transition-all text-morandi-accent bg-morandi-accent/10 hover:bg-morandi-accent/20"
                    >
                      讲解
                    </button>
                  </div>
                  <p class="text-[11px] text-slate-500 leading-relaxed mt-1 line-clamp-2">{{ ex.description }}</p>
                </div>
<div v-if="currentTabActions.length === 0" class="text-center py-6 text-xs text-morandi-lightText">
                  当前水平下暂无推荐动作，可降低难度筛选或调整训练水平
                </div>
              </div>
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
                <span class="w-1 h-3 bg-amber-500 rounded-full shrink-0"></span>
                <span>{{ tip }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- 动作讲解弹窗 -->
    <div v-if="explainTarget" class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" @click.self="closeExplainModal">
      <div class="bg-white rounded-2xl max-w-lg w-full shadow-xl max-h-[85vh] overflow-hidden flex flex-col">
        <div class="flex items-center justify-between p-5 border-b border-morandi-soft">
          <div>
            <h3 class="text-lg font-semibold text-morandi-text">{{ explainTarget.name }}</h3>
            <p class="text-xs text-morandi-lightText mt-0.5">动作讲解 · {{ explainTarget.level }}</p>
          </div>
          <button @click="closeExplainModal" class="text-morandi-lightText hover:text-morandi-text text-2xl leading-none">×</button>
        </div>
        <div v-if="explainTarget" class="p-5 overflow-y-auto space-y-4">
          <div class="flex flex-wrap gap-2">
            <span class="px-2 py-1 rounded-full text-xs" :style="{ background: getLevelColor(explainTarget.level) + '22', color: getLevelColor(explainTarget.level) }">{{ explainTarget.level }}</span>
            <span class="px-2 py-1 rounded-full bg-morandi-soft text-morandi-text text-xs">MET {{ Number(explainTarget.met).toFixed(1) }}</span>
          </div>

          <p class="text-sm text-morandi-lightText leading-relaxed">{{ explainTarget.description }}</p>

          <div>
            <div class="flex items-center gap-2 mb-3">
              <div class="w-1 h-4 bg-morandi-accent rounded-full"></div>
              <div class="text-sm font-semibold text-morandi-text">动作步骤</div>
            </div>
            <ol class="space-y-3">
              <li v-for="(step, i) in getExplainSteps(explainTarget)" :key="i" class="flex gap-3">
                <span class="w-7 h-7 flex items-center justify-center rounded-full text-white text-xs font-semibold shrink-0" :style="{ background: '#2F5D4A' }">{{ i + 1 }}</span>
                <div class="flex-1">
                  <div class="text-sm font-medium text-morandi-text">{{ step.title }}</div>
                  <div class="text-xs text-morandi-lightText mt-0.5 leading-relaxed">{{ step.description }}</div>
                </div>
              </li>
            </ol>
          </div>

          <div v-if="getExplainTips(explainTarget).length">
            <div class="flex items-center gap-2 mb-3">
              <div class="w-1 h-4 bg-amber-500 rounded-full"></div>
              <div class="text-sm font-semibold text-morandi-text">训练提示</div>
            </div>
            <ul class="space-y-2">
              <li v-for="(tip, i) in getExplainTips(explainTarget)" :key="i" class="flex gap-2 text-xs text-amber-800 bg-amber-50 px-3 py-2 rounded-lg">
                <span class="w-1 h-3 bg-amber-500 rounded-full shrink-0"></span>
                <span>{{ tip }}</span>
              </li>
            </ul>
          </div>

          <button @click="openRecordModal(explainTarget); closeExplainModal()" class="w-full py-2.5 bg-morandi-accent text-white rounded-xl hover:bg-morandi-accentDark transition-colors font-medium shadow-sm">
            记录本次训练
          </button>
        </div>
      </div>
    </div>

    <!-- 记录训练弹窗 -->
    <div v-if="recordModalOpen" class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" @click.self="closeRecordModal">
      <div class="bg-white rounded-2xl max-w-md w-full shadow-xl max-h-[85vh] overflow-hidden flex flex-col">
        <div class="flex items-center justify-between p-5 border-b border-morandi-soft">
          <div>
            <h3 class="text-lg font-semibold text-morandi-text">{{ recordTarget?.name }}</h3>
            <p class="text-xs text-morandi-lightText mt-0.5">记录本次训练，同步到「训练计划」页</p>
          </div>
          <button @click="closeRecordModal" class="text-morandi-lightText hover:text-morandi-text text-2xl leading-none">×</button>
        </div>
        <div v-if="recordTarget" class="p-5 overflow-y-auto space-y-4">
          <div class="flex flex-wrap gap-2">
            <span class="px-2 py-1 rounded-full text-xs" :style="{ background: getLevelColor(recordTarget.level) + '22', color: getLevelColor(recordTarget.level) }">{{ recordTarget.level }}</span>
            <span class="px-2 py-1 rounded-full bg-morandi-soft text-morandi-text text-xs">MET {{ Number(recordTarget.met).toFixed(1) }}</span>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="flex items-center justify-between text-sm bg-white/60 rounded-lg px-3 py-2 border border-morandi-soft/40">
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
            <div class="flex items-center justify-between text-sm bg-white/60 rounded-lg px-3 py-2 border border-morandi-soft/40">
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
            <div class="flex items-center justify-between text-sm bg-white/60 rounded-lg px-3 py-2 border border-morandi-soft/40">
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
            <div class="flex items-center justify-between text-sm bg-white/60 rounded-lg px-3 py-2 border border-morandi-soft/40">
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
          </div>

          <div class="flex items-center gap-3">
            <span class="text-xs text-morandi-lightText">训练日期</span>
            <input v-model="recordDate" type="date" class="flex-1 px-3 py-1.5 rounded-lg bg-white/70 border border-morandi-soft text-sm outline-none focus:border-morandi-accent" />
          </div>

          <div class="grid grid-cols-3 gap-3 text-center">
            <div class="bg-white/60 rounded-lg py-2 border border-morandi-soft/40">
              <div class="text-[11px] text-morandi-lightText">总组数</div>
              <div class="font-bold text-morandi-text">{{ sets }}</div>
            </div>
            <div class="bg-white/60 rounded-lg py-2 border border-morandi-soft/40">
              <div class="text-[11px] text-morandi-lightText">总次数</div>
              <div class="font-bold text-morandi-text">{{ sets * reps }}</div>
            </div>
            <div class="bg-white/60 rounded-lg py-2 border border-morandi-soft/40">
              <div class="text-[11px] text-morandi-lightText">消耗</div>
              <div class="font-bold text-morandi-accent">{{ recordCalories }} <span class="text-[10px]">kcal</span></div>
            </div>
          </div>

          <button @click="saveLibraryRecord" class="w-full py-2.5 bg-morandi-accent text-white rounded-xl hover:bg-morandi-accentDark transition-colors font-medium shadow-sm hover:shadow-md active:scale-[0.98]">
            保存训练记录
          </button>
        </div>
      </div>
    </div>

    <!-- 保存成功提示 -->
    <Transition name="fade">
      <div v-if="savedTip" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-morandi-accent text-white px-5 py-2.5 rounded-xl shadow-lg text-sm font-medium">
         训练记录已保存，可在「训练计划」查看
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Dumbbell, Activity, MousePointerClick, Plus, Minus, Target } from 'lucide-vue-next'
import { BodyChart, ViewSide, extractMuscleGroup, filterMuscles, INTENSITY_COLORS } from 'body-muscles'
import { EXERCISES, getExercisesByMuscle, type ExerciseDetail } from '@/data/exercises'
import {
  trainingMuscleGroups,
  getLevelColor,
  getMetLevel,
  type TrainingExercise,
  type TrainingMuscleGroup
} from '@/config/trainingData'
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
  'chest': '胸肌',
  'shoulder': '三角肌', 'deltoid': '三角肌',
  'biceps': '肱二头肌', 'triceps': '肱三头肌', 'forearm': '前臂',
  'abs': '腹肌', 'obliques': '侧腹肌', 'serratus': '前锯肌',
  'lats': '背阔肌', 'traps': '斜方肌', 'lower': '下背部',
  'gluteus': '臀肌', 'quads': '股四头肌', 'adductors': '内收肌',
  'hamstrings': '腘绳肌', 'calves': '小腿肌', 'tibialis': '胫骨前肌', 'hip': '髋屈肌',
}

const muscleGroupCategoryMap: Record<string, string> = {
  'chest': '胸部',
  'shoulder': '肩部', 'deltoid': '肩部',
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


// 难度筛选（训练推荐 tab 内）
const selectedLevel = ref<string>('全部')
const levelOptions = ['全部', '入门', '入门 - 中级', '中级', '中高级', '高级']

// 肌肉 group → trainingData 部位 key 映射
const groupToTrainingKey: Record<string, string> = {
  // 胸
  chest: 'chest',
  // 肩（整体：三角肌，动作库合并中束+后束）
  shoulder: 'deltoid-middle',
  deltoid: 'deltoid-posterior',
  // 手臂
  biceps: 'biceps',
  triceps: 'triceps',
  forearm: 'forearms',
  // 核心
  abs: 'abs',
  obliques: 'obliques',
  serratus: 'serratus',
  // 背
  lats: 'upper-back',
  traps: 'upper-back',
  lower: 'lower-back',
  // 臀腿
  gluteus: 'glutes',
  quads: 'quadriceps',
  hip: 'hip-flexors',
  adductors: 'adductors',
  hamstrings: 'hamstrings',
  // 小腿
  calves: 'calves',
  tibialis: 'tibialis-anterior'
}

// 当前选中的动作库部位（可手动切换，也可跟随肌肉图）
const selectedTrainingKey = ref<string>('chest')



// ===== 肌肉细分（点击肌肉显示整体名，可再手动细分） =====
interface Subdivision {
  key: string
  label: string
  trainingKeys: string[]
  filter?: (name: string) => boolean
}
interface SubdivisionDef {
  groupKeys: string[]
  subdivisions: Subdivision[]
}

const SUBDIVISION_DEFS: Record<string, SubdivisionDef> = {
  shoulder: {
    groupKeys: ['shoulder', 'deltoid'],
    subdivisions: [
      { key: 'all', label: '全部', trainingKeys: ['deltoid-middle', 'deltoid-posterior'] },
      { key: 'front', label: '前束', trainingKeys: ['deltoid-middle'], filter: (n) => /推举|卧推|前/.test(n) },
      { key: 'mid', label: '中束', trainingKeys: ['deltoid-middle'], filter: (n) => /侧平举|直立划船|中束/.test(n) },
      { key: 'post', label: '后束', trainingKeys: ['deltoid-posterior'] },
    ]
  },
  chest: {
    groupKeys: ['chest'],
    subdivisions: [
      { key: 'all', label: '全部', trainingKeys: ['chest'] },
      { key: 'upper', label: '上胸', trainingKeys: ['chest'], filter: (n) => /上斜|上胸/.test(n) },
      { key: 'lower', label: '下胸', trainingKeys: ['chest'], filter: (n) => /下斜|下胸|双杠/.test(n) },
    ]
  },
  abs: {
    groupKeys: ['abs'],
    subdivisions: [
      { key: 'all', label: '全部', trainingKeys: ['abs'] },
      { key: 'upper', label: '上腹', trainingKeys: ['abs'], filter: (n) => /卷腹|触膝|触足|站立/.test(n) },
      { key: 'lower', label: '下腹', trainingKeys: ['abs'], filter: (n) => /抬腿|举腿|蹬车|反向/.test(n) },
    ]
  }
}

const selectedSubdivision = ref<string>('all')

const currentSubdivisions = computed<Subdivision[] | null>(() => {
  if (!selectedGroup.value) return null
  for (const def of Object.values(SUBDIVISION_DEFS)) {
    if (def.groupKeys.includes(selectedGroup.value)) return def.subdivisions
  }
  return null
})

function selectSubdivision(key: string) {
  selectedSubdivision.value = key
}

// 细分 → 动作库组 + 过滤
const subdivisionTrainingKeys = computed<string[]>(() => {
  const subs = currentSubdivisions.value
  if (!subs) return []
  const cur = subs.find(s => s.key === selectedSubdivision.value)
  return cur ? cur.trainingKeys : []
})
const subdivisionFilter = computed<((name: string) => boolean) | null>(() => {
  const subs = currentSubdivisions.value
  if (!subs) return null
  const cur = subs.find(s => s.key === selectedSubdivision.value)
  return cur?.filter || null
})

// 训练水平选项（递进顺序：入门 → 高级）
const LEVEL_ORDER = ['入门', '入门 - 中级', '中级', '中高级', '高级']
const LEVEL_OPTIONS = LEVEL_ORDER.map(v => ({ value: v, label: v }))

// 每块肌肉的训练水平（localStorage 持久化，key: muscle_level_{trainingKey}）
const muscleLevels = ref<Record<string, string>>(loadMuscleLevels())
function loadMuscleLevels(): Record<string, string> {
  try {
    const raw = localStorage.getItem('muscle_levels')
    return raw ? JSON.parse(raw) : {}
  } catch { return {} }
}
function saveMuscleLevels() {
  localStorage.setItem('muscle_levels', JSON.stringify(muscleLevels.value))
}
const currentLevel = computed<string>(() => {
  return muscleLevels.value[selectedTrainingKey.value] || ''
})
function setMuscleLevel(lv: string) {
  if (lv) muscleLevels.value[selectedTrainingKey.value] = lv
  else delete muscleLevels.value[selectedTrainingKey.value]
  saveMuscleLevels()
}

// 与当前肌肉相关的动作库部位组（同大类）
const relatedTrainingGroups = computed<TrainingMuscleGroup[]>(() => {
  // 该部位所属大类的全部训练组
  const keyToTk: Record<string, string> = {}
  for (const [g, k] of Object.entries(groupToTrainingKey)) keyToTk[g] = k
  const currentTk = keyToTk[selectedGroup.value || ''] || selectedTrainingKey.value
  const primary = trainingMuscleGroups.find(g => g.key === currentTk)
  if (!primary) return []
  // 返回当前部位 + 相邻部位（同类别）
  return trainingMuscleGroups.filter(g => g.key === currentTk)
})

function selectTrainingGroup(key: string) {
  selectedTrainingKey.value = key
}

// 当前部位动作：按训练水平过滤 + 递进排序
const trainingFiltered = computed<TrainingExercise[]>(() => {
  // 有细分：按细分取多个组 + 可选过滤
  if (subdivisionTrainingKeys.value.length) {
    let list: TrainingExercise[] = []
    for (const tk of subdivisionTrainingKeys.value) {
      const group = trainingMuscleGroups.find(g => g.key === tk)
      if (group) list = list.concat(group.exercises)
    }
    const fn = subdivisionFilter.value
    if (fn) list = list.filter(ex => fn(ex.name))
    return list
  }
  // 无细分：跟随肌肉图映射
  const tk = groupToTrainingKey[selectedGroup.value || ''] || selectedTrainingKey.value
  const group = trainingMuscleGroups.find(g => g.key === tk)
  return group ? group.exercises : []
})

// 难度排序权重
function levelRank(lv: string): number {
  const idx = LEVEL_ORDER.indexOf(lv)
  return idx === -1 ? 99 : idx
}

// 当前展示动作：按训练水平过滤 + 递进排序
const currentTabActions = computed<TrainingExercise[]>(() => {
  let list = [...trainingFiltered.value]
  const lv = currentLevel.value
  const maxRank = lv ? levelRank(lv) : 99

  // 1) 难度筛选优先：若下方选了具体级别，只显示该级别
  if (selectedLevel.value !== '全部') {
    list = list.filter(ex => ex.level === selectedLevel.value)
    return list.sort((a, b) => levelRank(a.level) - levelRank(b.level))
  }

  // 2) 已设置水平：只显示难度 ≤ 该水平的动作
  if (lv) {
    list = list.filter(ex => levelRank(ex.level) <= maxRank)
    // 排序：当前水平级别的动作置顶，其余按入门 → 递进
    list.sort((a, b) => {
      const aHit = levelRank(a.level) === maxRank ? 0 : 1
      const bHit = levelRank(b.level) === maxRank ? 0 : 1
      if (aHit !== bHit) return aHit - bHit
      return levelRank(a.level) - levelRank(b.level)
    })
  } else {
    // 3) 未设置：按入门 → 高级递进排序
    list.sort((a, b) => levelRank(a.level) - levelRank(b.level))
  }
  return list
})

// 动作讲解
const explainOpen = ref<string | null>(null)
function toggleExplain(name: string) {
  explainOpen.value = explainOpen.value === name ? null : name
}

interface ExplainStep { title: string; description: string }

const EXPLAIN_TEMPLATES: Record<string, { steps: ExplainStep[]; tips: string[] }> = {
  chest: {
    steps: [
      { title: '准备姿势', description: '保持躯干稳定，肩胛骨后收下沉，核心收紧' },
      { title: '动作过程', description: '缓慢下放至胸部有拉伸感，再用力推起，全程控制节奏' },
      { title: '顶峰收缩', description: '推起至顶端时停顿 1 秒，感受胸部挤压' },
      { title: '还原', description: '缓慢回到起始位置，保持肌肉张力，不要完全放松' }
    ],
    tips: ['保持手腕中立，避免过度外展', '下放吸气、发力呼气', '新手先用轻重量建立发力感']
  },
  'deltoid-middle': {
    steps: [
      { title: '准备姿势', description: '站姿或坐姿，背部挺直，核心收紧' },
      { title: '侧向抬起', description: '手臂微屈，向两侧抬起至与肩同高' },
      { title: '控制下落', description: '缓慢下放，感受三角肌中束持续受力' }
    ],
    tips: ['避免耸肩借力', '肘部略高于手腕', '用较轻重量做高次数更安全']
  },
  biceps: {
    steps: [
      { title: '准备姿势', description: '站姿，双手握器械，肘部贴紧身体两侧' },
      { title: '弯举', description: '呼气，前臂向上弯举，感受肱二头肌收缩' },
      { title: '缓慢还原', description: '吸气，缓慢放下，保持肘部位置不变' }
    ],
    tips: ['不要借助身体晃动借力', '肘部始终固定', '全程控制离心阶段']
  },
  triceps: {
    steps: [
      { title: '准备姿势', description: '握稳器械或绳索，肘部固定于身体两侧' },
      { title: '下压/伸展', description: '伸直手臂，感受肱三头肌收缩' },
      { title: '缓慢还原', description: '控制回到起始位置，保持张力' }
    ],
    tips: ['大臂保持不动，只有前臂活动', '避免锁定肘关节过猛', '专注三头肌发力']
  },
  abs: {
    steps: [
      { title: '准备姿势', description: '仰卧或悬垂，核心收紧，腰部贴地' },
      { title: '卷腹/抬腿', description: '呼气，卷起腹部或抬起双腿，感受腹肌收缩' },
      { title: '缓慢还原', description: '吸气，缓慢回到起始位置，保持腹肌张力' }
    ],
    tips: ['避免用颈部发力', '动作要慢，不要借惯性', '全程保持核心收紧']
  },
  obliques: {
    steps: [
      { title: '准备姿势', description: '保持躯干稳定，核心收紧' },
      { title: '侧向转体', description: '呼气，向一侧旋转躯干，感受腹斜肌收缩' },
      { title: '控制还原', description: '缓慢回到中间，换另一侧' }
    ],
    tips: ['转动来自胸椎而非腰部', '骨盆保持稳定', '避免快速甩动']
  },
  'upper-back': {
    steps: [
      { title: '准备姿势', description: '坐姿或俯身，背部挺直，肩胛骨下沉' },
      { title: '拉/划', description: '呼气，将重量拉向身体，肩胛骨后收' },
      { title: '顶峰收缩', description: '在顶端停顿，感受背部挤压' },
      { title: '缓慢还原', description: '控制放回，保持背部张力' }
    ],
    tips: ['用肩胛骨带动，而不是手臂发力', '避免含胸驼背', '控制节奏，不要甩动']
  },
  hamstrings: {
    steps: [
      { title: '准备姿势', description: '站姿或俯卧，保持核心稳定' },
      { title: '弯腿/屈髋', description: '感受腘绳肌发力，缓慢完成动作' },
      { title: '控制还原', description: '缓慢回到起始位置，保持张力' }
    ],
    tips: ['膝关节方向与脚尖一致', '动作幅度以无痛为准', '避免腰部代偿']
  },
  quadriceps: {
    steps: [
      { title: '准备姿势', description: '站姿，双脚与肩同宽，核心收紧' },
      { title: '下蹲/伸膝', description: '缓慢下蹲或伸直膝盖，感受股四头肌发力' },
      { title: '蹬起', description: '呼气，用力蹬起回到起始位置' }
    ],
    tips: ['膝盖不要内扣', '保持背部平直', '下蹲深度以舒适为准']
  },
  glutes: {
    steps: [
      { title: '准备姿势', description: '仰卧或站立，核心收紧' },
      { title: '顶髋/后踢', description: '呼气，收紧臀部完成动作' },
      { title: '顶峰收缩', description: '顶端停顿 1-2 秒，感受臀肌挤压' },
      { title: '缓慢还原', description: '控制下放，保持臀部张力' }
    ],
    tips: ['用臀部发力而非腰部', '动作顶端充分收缩', '避免过度弓腰']
  },
  calves: {
    steps: [
      { title: '准备姿势', description: '站姿，前脚掌踩在台阶或器械上' },
      { title: '提踵', description: '呼气，踮起脚尖至最高点' },
      { title: '拉伸还原', description: '缓慢下放脚跟至小腿有拉伸感' }
    ],
    tips: ['动作幅度尽量大', '顶端停顿感受收缩', '避免突然弹跳']
  },
  adductors: {
    steps: [
      { title: '准备姿势', description: '坐姿或站姿，核心稳定' },
      { title: '内收', description: '呼气，双腿向内夹紧，感受内收肌收缩' },
      { title: '缓慢还原', description: '控制打开，保持张力' }
    ],
    tips: ['动作缓慢有控制', '避免爆发式发力', '保持躯干稳定']
  },
  'tibialis-anterior': {
    steps: [
      { title: '准备姿势', description: '坐姿或站姿，脚跟固定' },
      { title: '勾脚', description: '呼气，脚尖向上勾起，感受胫骨前肌收缩' },
      { title: '缓慢还原', description: '控制放下，保持张力' }
    ],
    tips: ['动作幅度完整', '避免借力', '可以配合提踵训练']
  },
  neck: {
    steps: [
      { title: '准备姿势', description: '坐姿，背部挺直，核心收紧' },
      { title: '抗阻训练', description: '用手或器械施加阻力，颈部缓慢对抗' },
      { title: '控制还原', description: '缓慢回到中立位' }
    ],
    tips: ['颈部训练重量要非常轻', '全程无痛', '不要快速甩动头部']
  },
  forearms: {
    steps: [
      { title: '准备姿势', description: '坐姿，前臂置于大腿或支撑面' },
      { title: '腕屈伸', description: '呼气，手腕向上或向下屈伸' },
      { title: '缓慢还原', description: '控制回到起始位置' }
    ],
    tips: ['动作幅度完整', '保持前臂固定', '避免手腕过度扭转']
  }
}

function getExplainSteps(ex: any): ExplainStep[] {
  const tk = selectedGroup.value ? groupToTrainingKey[selectedGroup.value] : ''
  const tpl = EXPLAIN_TEMPLATES[tk || 'chest'] || EXPLAIN_TEMPLATES.chest
  return tpl.steps
}

function getExplainTips(ex: any): string[] {
  const tk = selectedGroup.value ? groupToTrainingKey[selectedGroup.value] : ''
  const tpl = EXPLAIN_TEMPLATES[tk || 'chest'] || EXPLAIN_TEMPLATES.chest
  return tpl.tips
}

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

// ===== 动作库记录训练（trainingData 动作适配） =====
const recordTarget = ref<any | null>(null)
const recordModalOpen = ref(false)

function openRecordModal(ex: any) {
  recordTarget.value = ex
  recordModalOpen.value = true
}
function closeRecordModal() {
  recordModalOpen.value = false
}

const recordCalories = computed(() => {
  if (!recordTarget.value) return 0
  return workout.calcCalories(Number(recordTarget.value.met) || 0, userWeight.value, duration.value)
})

function saveLibraryRecord() {
  const ex = recordTarget.value
  if (!ex) return
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
    exerciseId: Number(ex.id) || 0,
    exerciseName: ex.name,
    muscleGroup: selectedGroup.value || 'chest',
    category: muscleGroupCategoryMap[selectedGroup.value || 'chest'] || '训练',
    date: recordDate.value,
    duration: duration.value,
    sets: sets.value,
    reps: reps.value,
    weight: weight.value,
    intensity,
    calories: recordCalories.value
  })

  savedTip.value = true
  setTimeout(() => { savedTip.value = false }, 2200)
  closeRecordModal()
}

// ===== 动作讲解弹窗 =====
const explainTarget = ref<any | null>(null)

function openExplainModal(ex: any) {
  explainTarget.value = ex
}
function closeExplainModal() {
  explainTarget.value = null
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

// 肌肉分组：返回整体大组名（点击肌肉用整体名，如胸肌/三角肌）
function getMuscleDetailGroup(id: string): string {
  const base = extractMuscleGroup(id) || id
  // 背部下段（竖脊肌/腰方肌）归下背
  if (id.includes('lower-back') || id.includes('erectors') || id.includes('ql')) return 'lower'
  return base
}

function handleMuscleClick(id: string) {
  const group = getMuscleDetailGroup(id)
  if (!trainableGroups.includes(group)) return
  // 高亮整组（如点击三角肌前束，高亮整个肩部）
  const highlightGroup = extractMuscleGroup(id) || group
  if (selectedGroup.value === group) {
    clearMuscleStates()
    selectedGroup.value = null
    selectedExercise.value = null
  } else {
    clearMuscleStates()
    updateMuscleStates(highlightGroup, 8, true)
    selectedGroup.value = group
    selectedExercise.value = null
    // 点击肌肉重置细分为全部（显示整体名 + 全部动作）
    selectedSubdivision.value = 'all'
    // 同步动作库部位
    const tk = groupToTrainingKey[group]
    if (tk) selectedTrainingKey.value = tk
  }
}

function handleMuscleHover(id: string | null) {
  if (id) {
    const group = getMuscleDetailGroup(id)
    if (!trainableGroups.includes(group)) {
      tooltipData.value = null
      return
    }
    const highlightGroup = extractMuscleGroup(id) || group
    if (selectedGroup.value === group) {
      hoveredGroup.value = group
      tooltipData.value = { name: muscleGroupNameMap[group] || group, group: muscleGroupCategoryMap[group] || '其他' }
      return
    }
    if (hoveredGroup.value && hoveredGroup.value !== selectedGroup.value) {
      updateMuscleStates(extractMuscleGroup(hoveredGroup.value) || hoveredGroup.value, 0, false)
    }
    updateMuscleStates(highlightGroup, 4, false)
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
