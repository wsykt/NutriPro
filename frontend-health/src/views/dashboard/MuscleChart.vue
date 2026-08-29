<template>
  <div class="diet-page">
    <!-- ===== 深壳星轨带（双面星盘 · 统计星球） ===== -->
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
            <button class="crumb-node" @click="goHub"><span class="nd"><Dumbbell :size="12" /></span>运动管理</button>
          </span>
          <span class="crumb-wrap">
            <span class="crumb-link"></span>
            <span class="crumb-node hot"><span class="nd"><Compass :size="13" /></span>双面星盘</span>
          </span>
        </div>
        <div class="db-top-right">
          <span class="db-date"><RefreshCw :size="12" />当前 <b id="pf-face-t">{{ currentView === 'front' ? '正面' : '背面' }}</b></span>
        </div>
      </div>

      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 104" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 52 C 300 8, 440 8, 560 52 S 830 96, 960 52 S 1130 8, 1200 52" />
        </svg>

        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><Compass :size="19" /></span>
            <span class="tt"><b>双面星盘</b><span>DUAL CONSTELLATION</span></span>
          </div>
        </div>

        <!-- 四颗统计星球 -->
        <div
          v-for="(s, i) in stations" :key="s.nm"
          class="db-station-wrap"
          :style="{ left: stationLeft(i, stations.length) + '%' }"
        >
          <div class="db-station-float" :style="floatStyle(i)">
            <div class="db-station" :aria-label="s.nm">
              <span class="wb"><component :is="s.icon" :size="15" /></span>
              <span class="nm">{{ s.nm }}</span>
              <span class="ds">{{ s.ds }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区（双面星盘） ===== -->
    <div class="db-paper" ref="paperRef">
      <div class="db-head" data-anim>
        <div class="sec-t">双面星盘 · 点击金色星座节点联动围度</div>
        <div class="db-pills">
          <button class="pf-flip-btn" @click="flipView">
            <RefreshCw :size="13" />翻转星盘
          </button>
          <span class="pf-face-tag">
            <CircleDot :size="12" />{{ currentView === 'front' ? '正面' : '背面' }} · {{ currentFaceMuscleCount }} 组
          </span>
        </div>
      </div>

      <div class="m-blocks">
        <!-- ===== 左 7：双面星盘 + 围度卡片 ===== -->
        <div class="m-block astro-block" data-anim>
          <div class="bl-head"><b>双面星盘 · 肌群星座</b></div>

          <div class="pf-astro">
            <div class="pf-astro-glow" aria-hidden="true"></div>
            <div class="pf-astro-ring" v-html="ringSvg"></div>
            <div class="pf-flip" :class="{ 'is-back': currentView === 'back' }">
              <!-- 正面 -->
              <div class="pf-face front">
                <span class="face-label">FRONT · 正面</span>
                <div class="pf-face-dust" v-html="dustSvg"></div>
                <div class="body-svg-wrap">
                  <div ref="frontChartRef" class="body-chart-container" @mousemove="onMouseMoveFront"></div>
                  <Transition name="fade">
                    <div v-if="tooltipData && currentView === 'front'"
                      class="mtip show"
                      :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }">
                      <b>{{ tooltipData.name }}</b> <i>{{ tooltipData.group }}</i>
                    </div>
                  </Transition>
                </div>
              </div>
              <!-- 背面 -->
              <div class="pf-face back">
                <span class="face-label">BACK · 背面</span>
                <div class="pf-face-dust" v-html="dustSvg"></div>
                <div class="body-svg-wrap">
                  <div ref="backChartRef" class="body-chart-container" @mousemove="onMouseMoveBack"></div>
                  <Transition name="fade">
                    <div v-if="tooltipData && currentView === 'back'"
                      class="mtip show"
                      :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }">
                      <b>{{ tooltipData.name }}</b> <i>{{ tooltipData.group }}</i>
                    </div>
                  </Transition>
                </div>
              </div>
            </div>
          </div>

          <!-- 围度卡片 3×2 -->
          <div class="circ-grid">
            <div
              v-for="p in CIRC" :key="p.key"
              class="circ-card"
              :class="{ on: selectedPart === p.key }"
              @click="selectPart(p.key)"
            >
              <div class="cl"><component :is="p.icon" :size="12" />{{ p.nm }}</div>
              <div class="cv">{{ latestCircVal(p.key) }}<small>cm</small></div>
              <div class="cd" :class="circDiffClass(p.key)">{{ circDiffText(p.key) }}</div>
            </div>
          </div>
        </div>

        <!-- ===== 右 5：训练推荐 + 趋势 + 表单 + 记录 ===== -->
        <div class="m-block" data-anim>
          <div class="bl-head">
            <b>{{ selectedGroup ? (muscleGroupNameMap[selectedGroup] || selectedGroup) + ' 训练推荐' : '训练推荐' }}</b>
            <span v-if="selectedGroup">{{ currentTabActions.length }} 个动作</span>
          </div>

          <!-- 细分切换 -->
          <div v-if="currentSubdivisions" class="subdiv-row">
            <span class="subdiv-label">细分</span>
            <button
              v-for="sub in currentSubdivisions" :key="sub.key"
              @click="selectSubdivision(sub.key)"
              class="subdiv-btn"
              :class="{ active: selectedSubdivision === sub.key }"
            >{{ sub.label }}</button>
          </div>

          <!-- 训练水平 -->
          <div class="level-panel">
            <div class="level-head">
              <span class="level-title"><Target :size="13" />我的{{ selectedGroup ? (muscleGroupNameMap[selectedGroup] || '') : '' }}训练水平</span>
              <span v-if="currentLevel" class="level-cur">可练到：<b>{{ currentLevel }}</b></span>
            </div>
            <div class="level-btns">
              <button
                v-for="lv in LEVEL_OPTIONS" :key="lv.value"
                @click="setMuscleLevel(lv.value)"
                class="level-btn"
                :class="{ active: currentLevel === lv.value }"
              >{{ lv.label }}</button>
              <button
                @click="setMuscleLevel('')"
                class="level-btn dashed"
                :class="{ active: !currentLevel }"
              >未设置</button>
            </div>
          </div>

          <!-- 部位快速切换 -->
          <div v-if="relatedTrainingGroups.length" class="quick-groups">
            <button
              v-for="mg in relatedTrainingGroups" :key="mg.key"
              @click="selectTrainingGroup(mg.key)"
              class="quick-btn"
              :class="{ active: selectedTrainingKey === mg.key }"
              :style="selectedTrainingKey === mg.key ? { background: mg.color } : {}"
            >{{ mg.label }}</button>
          </div>

          <!-- 难度筛选 -->
          <div class="level-filter">
            <span class="filter-label">筛选：</span>
            <button
              v-for="lv in levelOptions" :key="lv"
              @click="selectedLevel = lv"
              class="filter-btn"
              :class="{ active: selectedLevel === lv }"
            >{{ lv }}</button>
          </div>

          <!-- 动作卡片 -->
          <div class="tx-list">
            <div
              v-for="ex in currentTabActions" :key="ex.name"
              class="tx-card"
              @click="openRecordModal(ex)"
            >
              <div class="txh">
                <b>{{ ex.name }}</b>
                <span class="txs">{{ ex.sets || '' }}</span>
              </div>
              <div class="txm">
                MET {{ Number(ex.met).toFixed(1) }} · {{ muscleGroupCategoryMap[selectedGroup || 'chest'] || '训练' }}
                <span class="lv" :style="{ background: getLevelColor(ex.level) }">{{ ex.level }}</span>
              </div>
              <button class="tx-explain" @click.stop="openExplainModal(ex)">讲解</button>
            </div>
            <div v-if="currentTabActions.length === 0" class="tx-empty">
              <MousePointerClick :size="30" />
              <span>点击左侧肌肉选择训练部位</span>
              <span class="tx-empty-sub">当前水平下暂无推荐动作，可降低难度筛选或调整训练水平</span>
            </div>
          </div>

          <!-- 围度趋势 -->
          <div class="sec-label"><Activity :size="12" />围度趋势</div>
          <div class="bl-head" style="margin-top:6px">
            <b>{{ currentCircPart.nm }}变化</b>
            <span class="p4-hint">cm · 点击圆点载入</span>
          </div>
          <div class="chart-box" v-html="circChartSvg"></div>

          <!-- 围度录入 -->
          <div class="sec-label"><PencilLine :size="12" />补录围度</div>
          <div class="circ-form">
            <div class="ff">
              <label>部位</label>
              <select v-model="formPart" @change="onFormPartChange">
                <option v-for="p in CIRC" :key="p.key" :value="p.key">{{ p.nm }}</option>
              </select>
            </div>
            <div class="ff">
              <label>围度（cm）</label>
              <input v-model.number="formVal" type="number" step="0.1" />
            </div>
            <div class="ff ff-full">
              <label>日期</label>
              <input v-model="formDate" type="date" />
            </div>
          </div>
          <button class="btn-gold btn-save" @click="saveCirc">
            <Save :size="13" />写入围度
          </button>

          <!-- 最近记录 -->
          <div class="sec-label"><History :size="12" />最近记录</div>
          <div class="circ-log">
            <div v-for="(r, i) in recentCircLogs" :key="i" class="circ-log-item">
              <span class="dt">{{ r.d.slice(5) }}</span>
              <span class="nm">{{ currentCircPart.nm }}</span>
              <span class="vl">{{ r.val }} cm</span>
            </div>
            <div v-if="recentCircLogs.length === 0" class="circ-log-item empty">
              <span>暂无记录</span>
            </div>
          </div>
        </div>
      </div>

      <div id="pf-toast" class="toast-host" v-if="toastMsg">
        <div class="toast" :class="{ err: toastErr }">
          <component :is="toastErr ? AlertCircle : CheckCircle2" :size="13" />
          {{ toastMsg }}
        </div>
      </div>
    </div>

    <!-- 动作讲解弹窗 -->
    <div v-if="explainTarget" class="modal-overlay" @click.self="closeExplainModal">
      <div class="modal-card">
        <div class="modal-head">
          <div>
            <h3>{{ explainTarget.name }}</h3>
            <p class="modal-sub">动作讲解 · {{ explainTarget.level }}</p>
          </div>
          <button class="modal-close" @click="closeExplainModal">×</button>
        </div>
        <div class="modal-body">
          <div class="modal-tags">
            <span class="tag" :style="{ background: getLevelColor(explainTarget.level) + '22', color: getLevelColor(explainTarget.level) }">{{ explainTarget.level }}</span>
            <span class="tag tag-default">MET {{ Number(explainTarget.met).toFixed(1) }}</span>
          </div>
          <p class="modal-desc">{{ explainTarget.description }}</p>
          <div class="step-section">
            <div class="step-title"><div class="step-bar"></div>动作步骤</div>
            <ol class="step-list">
              <li v-for="(step, i) in getExplainSteps(explainTarget)" :key="i" class="step-item">
                <span class="step-num">{{ i + 1 }}</span>
                <div class="step-text">
                  <div class="step-text-title">{{ step.title }}</div>
                  <div class="step-text-desc">{{ step.description }}</div>
                </div>
              </li>
            </ol>
          </div>
          <div v-if="getExplainTips(explainTarget).length" class="tip-section">
            <div class="step-title"><div class="step-bar tip-bar"></div>训练提示</div>
            <ul class="tip-list">
              <li v-for="(tip, i) in getExplainTips(explainTarget)" :key="i">
                <span class="tip-dot"></span>{{ tip }}
              </li>
            </ul>
          </div>
          <button class="btn-gold btn-full" @click="openRecordModal(explainTarget); closeExplainModal()">
            记录本次训练
          </button>
        </div>
      </div>
    </div>

    <!-- 记录训练弹窗 -->
    <div v-if="recordModalOpen" class="modal-overlay" @click.self="closeRecordModal">
      <div class="modal-card">
        <div class="modal-head">
          <div>
            <h3>{{ recordTarget?.name }}</h3>
            <p class="modal-sub">记录本次训练，同步到「训练计划」页</p>
          </div>
          <button class="modal-close" @click="closeRecordModal">×</button>
        </div>
        <div class="modal-body">
          <div class="modal-tags">
            <span class="tag" :style="{ background: getLevelColor(recordTarget?.level) + '22', color: getLevelColor(recordTarget?.level) }">{{ recordTarget?.level }}</span>
            <span class="tag tag-default">MET {{ Number(recordTarget?.met || 0).toFixed(1) }}</span>
          </div>
          <div class="record-grid">
            <div class="record-item">
              <span class="ri-label">时长</span>
              <div class="ri-ctrl">
                <button @click="duration = Math.max(5, duration - 5)"><Minus :size="14" /></button>
                <span class="ri-val">{{ duration }}</span>
                <button @click="duration = Math.min(180, duration + 5)"><Plus :size="14" /></button>
                <span class="ri-unit">分钟</span>
              </div>
            </div>
            <div class="record-item">
              <span class="ri-label">组数</span>
              <div class="ri-ctrl">
                <button @click="sets = Math.max(1, sets - 1)"><Minus :size="14" /></button>
                <span class="ri-val">{{ sets }}</span>
                <button @click="sets = Math.min(10, sets + 1)"><Plus :size="14" /></button>
                <span class="ri-unit">组</span>
              </div>
            </div>
            <div class="record-item">
              <span class="ri-label">每组</span>
              <div class="ri-ctrl">
                <button @click="reps = Math.max(1, reps - 2)"><Minus :size="14" /></button>
                <span class="ri-val">{{ reps }}</span>
                <button @click="reps = Math.min(30, reps + 2)"><Plus :size="14" /></button>
                <span class="ri-unit">次</span>
              </div>
            </div>
            <div class="record-item">
              <span class="ri-label">重量</span>
              <div class="ri-ctrl">
                <button @click="weight = Math.max(0, round(weight - 2.5))"><Minus :size="14" /></button>
                <span class="ri-val">{{ weight > 0 ? weight : '自重' }}</span>
                <button @click="weight = round(weight + 2.5)"><Plus :size="14" /></button>
                <span class="ri-unit" v-if="weight > 0">kg</span>
              </div>
            </div>
          </div>
          <div class="record-date">
            <span class="ri-label">训练日期</span>
            <input v-model="recordDate" type="date" class="date-input" />
          </div>
          <div class="record-summary">
            <div class="rs-item"><div class="rs-label">总组数</div><div class="rs-val">{{ sets }}</div></div>
            <div class="rs-item"><div class="rs-label">总次数</div><div class="rs-val">{{ sets * reps }}</div></div>
            <div class="rs-item"><div class="rs-label">消耗</div><div class="rs-val accent">{{ recordCalories }} <small>kcal</small></div></div>
          </div>
          <button class="btn-gold btn-full" @click="saveLibraryRecord">保存训练记录</button>
        </div>
      </div>
    </div>

    <!-- 保存成功提示 -->
    <Transition name="fade">
      <div v-if="savedTip" class="saved-tip">训练记录已保存，可在「训练计划」查看</div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, reactive, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  Dumbbell, Activity, MousePointerClick, Plus, Minus, Target,
  LayoutGrid, Compass, RefreshCw, CircleDot, PencilLine, Save, History,
  CheckCircle2, AlertCircle, Circle, Gauge, Weight, Percent, Flame, Clock
} from 'lucide-vue-next'
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

const router = useRouter()
const userStore = useUserStore()
const workout = useWorkoutRecords()

/* ========== 视图状态 ========== */
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

const savedTip = ref(false)
const bandRef = ref<HTMLElement | null>(null)
const paperRef = ref<HTMLElement | null>(null)
const frontChartRef = ref<HTMLElement | null>(null)
const backChartRef = ref<HTMLElement | null>(null)

let frontChart: BodyChart | null = null
let backChart: BodyChart | null = null

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

/* ========== 难度筛选 / 训练水平 ========== */
const selectedLevel = ref<string>('全部')
const levelOptions = ['全部', '入门', '入门 - 中级', '中级', '中高级', '高级']

const groupToTrainingKey: Record<string, string> = {
  chest: 'chest',
  shoulder: 'deltoid-middle',
  deltoid: 'deltoid-posterior',
  biceps: 'biceps',
  triceps: 'triceps',
  forearm: 'forearms',
  abs: 'abs',
  obliques: 'obliques',
  serratus: 'serratus',
  lats: 'upper-back',
  traps: 'upper-back',
  lower: 'lower-back',
  gluteus: 'glutes',
  quads: 'quadriceps',
  hip: 'hip-flexors',
  adductors: 'adductors',
  hamstrings: 'hamstrings',
  calves: 'calves',
  tibialis: 'tibialis-anterior'
}

const selectedTrainingKey = ref<string>('chest')

/* ========== 肌肉细分 ========== */
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

/* ========== 训练水平 ========== */
const LEVEL_ORDER = ['入门', '入门 - 中级', '中级', '中高级', '高级']
const LEVEL_OPTIONS = LEVEL_ORDER.map(v => ({ value: v, label: v }))

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

const relatedTrainingGroups = computed<TrainingMuscleGroup[]>(() => {
  const keyToTk: Record<string, string> = {}
  for (const [g, k] of Object.entries(groupToTrainingKey)) keyToTk[g] = k
  const currentTk = keyToTk[selectedGroup.value || ''] || selectedTrainingKey.value
  const primary = trainingMuscleGroups.find(g => g.key === currentTk)
  if (!primary) return []
  return trainingMuscleGroups.filter(g => g.key === currentTk)
})

function selectTrainingGroup(key: string) {
  selectedTrainingKey.value = key
}

const trainingFiltered = computed<TrainingExercise[]>(() => {
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
  const tk = groupToTrainingKey[selectedGroup.value || ''] || selectedTrainingKey.value
  const group = trainingMuscleGroups.find(g => g.key === tk)
  return group ? group.exercises : []
})

function levelRank(lv: string): number {
  const idx = LEVEL_ORDER.indexOf(lv)
  return idx === -1 ? 99 : idx
}

const currentTabActions = computed<TrainingExercise[]>(() => {
  let list = [...trainingFiltered.value]
  const lv = currentLevel.value
  const maxRank = lv ? levelRank(lv) : 99

  if (selectedLevel.value !== '全部') {
    list = list.filter(ex => ex.level === selectedLevel.value)
    return list.sort((a, b) => levelRank(a.level) - levelRank(b.level))
  }

  if (lv) {
    list = list.filter(ex => levelRank(ex.level) <= maxRank)
    list.sort((a, b) => {
      const aHit = levelRank(a.level) === maxRank ? 0 : 1
      const bHit = levelRank(b.level) === maxRank ? 0 : 1
      if (aHit !== bHit) return aHit - bHit
      return levelRank(a.level) - levelRank(b.level)
    })
  } else {
    list.sort((a, b) => levelRank(a.level) - levelRank(b.level))
  }
  return list
})

/* ========== 动作讲解模板 ========== */
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
      { title: '控制还原', description: '缓慢回到起始位置，保持肘部固定' }
    ],
    tips: ['肘部始终贴紧身体', '避免耸肩', '专注三头肌发力']
  },
  abs: {
    steps: [
      { title: '准备姿势', description: '仰卧，双腿屈膝，脚平放地面' },
      { title: '卷腹', description: '呼气，上背部抬起，感受腹肌收缩' },
      { title: '下放', description: '吸气缓慢下放，避免颈部代偿' }
    ],
    tips: ['下颌微收，不要抱头拉颈', '下背部贴紧地面', '动作要慢，感受腹肌发力']
  },
  quads: {
    steps: [
      { title: '准备姿势', description: '双脚与肩同宽，脚尖略外展' },
      { title: '下蹲', description: '臀部后坐，膝盖与脚尖同向' },
      { title: '站起', description: '脚跟发力站起，保持核心收紧' }
    ],
    tips: ['膝盖不要内扣', '下蹲时吸气、站起时呼气', '保持背部中立位']
  },
  lats: {
    steps: [
      { title: '准备姿势', description: '双手宽握单杠，肩胛骨下沉' },
      { title: '拉引', description: '背部发力，将胸部拉向单杠' },
      { title: '下放', description: '缓慢下放至手臂完全伸展' }
    ],
    tips: ['避免只用手臂拉', '肩胛骨先下沉再发力', '动作要控制']
  },
  glutes: {
    steps: [
      { title: '准备姿势', description: '仰卧屈膝，脚跟踩地' },
      { title: '臀桥', description: '脚跟发力顶髋，臀部收缩' },
      { title: '下放', description: '缓慢下放，保持张力' }
    ],
    tips: ['顶峰停顿 1-2 秒', '避免腰部代偿', '专注臀部发力']
  },
  hamstrings: {
    steps: [
      { title: '准备姿势', description: '俯卧于腿弯举机上，脚踝卡住垫板' },
      { title: '弯举', description: '腘绳肌发力，将垫板拉向臀部' },
      { title: '还原', description: '缓慢放回起始位置' }
    ],
    tips: ['避免臀部抬起代偿', '控制离心阶段', '全程感受腘绳肌张力']
  },
  calves: {
    steps: [
      { title: '准备姿势', description: '前脚掌站于垫板上，脚跟悬空' },
      { title: '提踵', description: '小腿发力，脚跟抬高' },
      { title: '下放', description: '缓慢下放至小腿完全拉伸' }
    ],
    tips: ['动作要慢', '顶峰停顿 1 秒', '完整拉伸与收缩']
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

/* ========== 训练记录（动作库适配） ========== */
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

/* ========== 动作讲解弹窗 ========== */
const explainTarget = ref<any | null>(null)

function openExplainModal(ex: any) {
  explainTarget.value = ex
}
function closeExplainModal() {
  explainTarget.value = null
}

/* ========== BodyChart 肌群交互逻辑 ========== */
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

// 每张图独立缓存上次渲染状态（共用缓存会导致背面初始配色被误判"未变化"而跳过）
const cachedStates = new WeakMap<BodyChart, Record<string, { intensity: number; selected: boolean }>>()

function stateChanged(chart: BodyChart | null, newState: Record<string, { intensity: number; selected: boolean }>): boolean {
  const cached = chart ? cachedStates.get(chart) : undefined
  if (!cached) return true
  const newKeys = Object.keys(newState)
  const cachedKeys = Object.keys(cached)
  if (newKeys.length !== cachedKeys.length) return true
  for (const key of newKeys) {
    const newVal = newState[key]
    const cachedVal = cached[key]
    if (!cachedVal || newVal.intensity !== cachedVal.intensity || newVal.selected !== cachedVal.selected) return true
  }
  return false
}

function setMuscleColors(target: BodyChart | null, container: HTMLElement | null) {
  if (!target) return
  const state: Record<string, { intensity: number; selected: boolean }> = {}
  Object.keys(groupToIds).forEach(group => {
    groupToIds[group].forEach(id => {
      state[id] = { intensity: trainableGroups.includes(group) ? 0 : 1, selected: false }
    })
  })
  if (stateChanged(target, state)) {
    cachedStates.set(target, state)
    target.update({ bodyState: state })
    if (container) setTimeout(() => setNonTrainableStyles(target), 50)
  }
}

function setNonTrainableStyles(chart: BodyChart | null) {
  if (!chart) return
  // 库的路径元素没有 data-muscle-id 属性，须通过实例的 musclePaths Map 拿 id -> path
  const paths = (chart as unknown as { musclePaths?: Map<string, SVGPathElement> }).musclePaths
  if (!paths) return
  paths.forEach((el, id) => {
    const group = extractMuscleGroup(id) || id
    if (!trainableGroups.includes(group)) {
      el.style.setProperty('stroke', '#d1d5db', 'important')
      el.style.setProperty('stroke-width', '0.5', 'important')
      el.style.setProperty('pointer-events', 'none', 'important')
    }
  })
}

function updateMuscleStates(group: string | null, intensity: number, selected: boolean) {
  if (!group) return
  const target = currentView.value === 'front' ? frontChart : backChart
  const container = currentView.value === 'front' ? frontChartRef.value : backChartRef.value
  if (!target) return
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
  if (stateChanged(target, state)) {
    cachedStates.set(target, state)
    target.update({ bodyState: state })
    if (container) setTimeout(() => setNonTrainableStyles(target), 50)
  }
}

function clearMuscleStates() {
  const target = currentView.value === 'front' ? frontChart : backChart
  const container = currentView.value === 'front' ? frontChartRef.value : backChartRef.value
  setMuscleColors(target, container)
}

function getMuscleDetailGroup(id: string): string {
  const base = extractMuscleGroup(id) || id
  if (id.includes('lower-back') || id.includes('erectors') || id.includes('ql')) return 'lower'
  return base
}

function handleMuscleClick(id: string) {
  const group = getMuscleDetailGroup(id)
  if (!trainableGroups.includes(group)) return
  const highlightGroup = extractMuscleGroup(id) || group
  if (selectedGroup.value === group) {
    clearMuscleStates()
    selectedGroup.value = null
    selectedExercise.value = null
  } else {
    // 先清空选中引用再重绘：否则 updateMuscleStates 会按旧的 selectedGroup 把上一组再次点亮
    selectedGroup.value = null
    clearMuscleStates()
    updateMuscleStates(highlightGroup, 8, true)
    selectedGroup.value = group
    selectedExercise.value = null
    selectedSubdivision.value = 'all'
    const tk = groupToTrainingKey[group]
    if (tk) selectedTrainingKey.value = tk
    // 联动围度部位
    const circMap: Record<string, string> = {
      chest: 'chest', abs: 'waist', gluteus: 'hip',
      biceps: 'arm', quads: 'thigh', calves: 'calf'
    }
    if (circMap[group]) selectPart(circMap[group])
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

function onMouseMoveFront(event: MouseEvent) {
  onMouseMove(event, frontChartRef.value)
}
function onMouseMoveBack(event: MouseEvent) {
  onMouseMove(event, backChartRef.value)
}
function onMouseMove(event: MouseEvent, container: HTMLElement | null) {
  if (!container) return
  const rect = container.getBoundingClientRect()
  tooltipPos.value = { x: event.clientX - rect.left + 10, y: event.clientY - rect.top - 40 }
}

function clearSelection() {
  clearMuscleStates()
  selectedGroup.value = null
  selectedExercise.value = null
}

/* ========== 翻转星盘 ========== */
function flipView() {
  currentView.value = currentView.value === 'front' ? 'back' : 'front'
  showToast('已翻转到 · ' + (currentView.value === 'front' ? '正面' : '背面'))
}

watch(currentView, (view) => {
  // 翻转时清空选中肌群（避免跨面残留）
  clearMuscleStates()
  selectedGroup.value = null
  selectedExercise.value = null
  hoveredGroup.value = null
  tooltipData.value = null
  // 翻转动画结束后重绘当前面颜色
  setTimeout(() => {
    const target = view === 'front' ? frontChart : backChart
    const container = view === 'front' ? frontChartRef.value : backChartRef.value
    setMuscleColors(target, container)
  }, 480)
})

/* ========== 星轨带统计球 ========== */
const stations = computed(() => [
  { nm: '肌群总数', ds: '15 组', icon: LayoutGrid },
  { nm: '本周训练', ds: weekStats.value.count + ' 次', icon: Dumbbell },
  { nm: '总时长', ds: weekStats.value.duration + ' min', icon: Clock },
  { nm: '消耗热量', ds: weekStats.value.calories + ' kcal', icon: Flame },
])

const weekStats = computed(() => {
  const recs = workout.records.value || []
  const now = new Date()
  const weekAgo = new Date(now); weekAgo.setDate(now.getDate() - 7)
  const weekRecs = recs.filter((r: any) => new Date(r.date) >= weekAgo)
  return {
    count: weekRecs.length,
    duration: weekRecs.reduce((s: number, r: any) => s + (Number(r.duration) || 0), 0),
    calories: weekRecs.reduce((s: number, r: any) => s + (Number(r.calories) || 0), 0),
  }
})

const currentFaceMuscleCount = computed(() => {
  // 正面 8 组，背面 7 组（与预览一致）
  return currentView.value === 'front' ? 8 : 7
})

function stationLeft(i: number, total: number): number {
  if (total <= 1) return 64
  return 34 + (i * 60) / (total - 1)
}
function floatStyle(i: number) {
  const durations = [4.6, 5.05, 5.5, 5.95]
  const delays = [-0.3, -0.9, -1.5, -2.1]
  return { animation: `dbFloat ${durations[i % 4]}s ease-in-out ${delays[i % 4]}s infinite alternate` }
}

function goHome() {
  router.push('/dashboard/home')
}
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'health' } }) }

/* ========== 双面星盘 · 外环刻度（静态，不依赖响应式数据） ========== */
function buildRingSvg(): string {
  let ticks = ''
  for (let i = 0; i < 60; i++) {
    const a = i * 6, rad = a * Math.PI / 180, R = 178
    const x1 = 180 + Math.cos(rad) * R, y1 = 180 + Math.sin(rad) * R
    const x2 = 180 + Math.cos(rad) * (i % 5 === 0 ? 164 : 172), y2 = 180 + Math.sin(rad) * (i % 5 === 0 ? 164 : 172)
    ticks += `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="rgba(217,162,74,${i % 5 === 0 ? .55 : .28})" stroke-width="${i % 5 === 0 ? 1.2 : 0.8}"/>`
  }
  ticks += `<circle cx="180" cy="180" r="178" fill="none" stroke="rgba(217,162,74,.32)" stroke-width="1"/>`
  ticks += `<circle cx="180" cy="180" r="170" fill="none" stroke="rgba(217,162,74,.2)" stroke-width="1" stroke-dasharray="2 6"/>`
  for (let i = 0; i < 12; i++) {
    const a = i * 30 - 90, rad = a * Math.PI / 180, x = 180 + Math.cos(rad) * 192, y = 180 + Math.sin(rad) * 192 + 3
    ticks += `<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" text-anchor="middle" font-size="8" fill="rgba(232,185,115,.55)" font-family="Noto Serif SC">${i * 30}°</text>`
  }
  for (let i = 0; i < 4; i++) {
    const a = i * 90 + 45, rad = a * Math.PI / 180, x = 180 + Math.cos(rad) * 150, y = 180 + Math.sin(rad) * 150
    ticks += `<path d="${starPath(x, y, 4)}" fill="rgba(232,185,115,.6)"/>`
  }
  return `<svg viewBox="0 0 360 360">${ticks}</svg>`
}
const ringSvg = buildRingSvg()

function starPath(cx: number, cy: number, r: number): string {
  const k = r * 0.18
  return `M${cx.toFixed(1)} ${(cy - r).toFixed(1)}` +
    ` Q${(cx + k).toFixed(1)} ${(cy - k).toFixed(1)} ${(cx + r).toFixed(1)} ${cy.toFixed(1)}` +
    ` Q${(cx + k).toFixed(1)} ${(cy + k).toFixed(1)} ${cx.toFixed(1)} ${(cy + r).toFixed(1)}` +
    ` Q${(cx - k).toFixed(1)} ${(cy + k).toFixed(1)} ${(cx - r).toFixed(1)} ${cy.toFixed(1)}` +
    ` Q${(cx - k).toFixed(1)} ${(cy - k).toFixed(1)} ${cx.toFixed(1)} ${(cy - r).toFixed(1)} Z`
}

const dustSvg = (() => {
  let s = ''
  for (let i = 0; i < 30; i++) {
    const dx = 20 + (i * 43.7) % 260, dy = 15 + (i * 37.1) % 490, r = (0.7 + (i % 3) * 0.4).toFixed(1)
    s += `<circle cx="${dx.toFixed(1)}" cy="${dy.toFixed(1)}" r="${r}" fill="rgba(232,185,115,${(0.08 + (i % 3) * 0.05).toFixed(2)})"/>`
  }
  return `<svg class="pf-face-dust-svg" viewBox="0 0 300 520" preserveAspectRatio="none">${s}</svg>`
})()

/* ========== 围度数据 ========== */
interface CircRecord { d: string; part: string; val: string }
const CIRC = [
  { key: 'chest', nm: '胸围', icon: Circle, def: 92.0, dy: -0.5 },
  { key: 'waist', nm: '腰围', icon: Circle, def: 74.0, dy: -0.8 },
  { key: 'hip', nm: '臀围', icon: Circle, def: 92.0, dy: 0.3 },
  { key: 'arm', nm: '上臂', icon: Circle, def: 32.0, dy: 0.2 },
  { key: 'thigh', nm: '大腿', icon: Circle, def: 52.0, dy: -0.3 },
  { key: 'calf', nm: '小腿', icon: Circle, def: 36.0, dy: -0.1 },
]

const CIRC_STORAGE_KEY = 'circ_records_v1'
const circRecords = ref<CircRecord[]>(loadCircRecords())

function loadCircRecords(): CircRecord[] {
  try {
    const raw = localStorage.getItem(CIRC_STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  // 初始化示例数据（最近 5 个时间点 × 6 部位）
  const init: CircRecord[] = []
  CIRC.forEach(p => {
    for (let i = 0; i < 5; i++) {
      const d = new Date(); d.setDate(d.getDate() - i * 5)
      init.push({
        d: d.toISOString().slice(0, 10),
        part: p.key,
        val: (p.def + p.dy * i + Math.random() * 0.3).toFixed(1),
      })
    }
  })
  return init
}

function saveCircRecords() {
  localStorage.setItem(CIRC_STORAGE_KEY, JSON.stringify(circRecords.value))
}

const selectedPart = ref<string>('chest')
const formPart = ref<string>('chest')
const formVal = ref<number>(92.0)
const formDate = ref<string>(new Date().toISOString().slice(0, 10))

const currentCircPart = computed(() => CIRC.find(p => p.key === selectedPart.value) || CIRC[0])

function latestCircVal(part: string): string {
  const recs = circRecords.value.filter(r => r.part === part).sort((a, b) => a.d < b.d ? 1 : -1)
  return recs.length ? recs[0].val : (CIRC.find(p => p.key === part)?.def.toFixed(1) || '--')
}

function circDiffClass(part: string): string {
  const recs = circRecords.value.filter(r => r.part === part).sort((a, b) => a.d < b.d ? 1 : -1)
  if (recs.length < 2) return 'flat'
  const diff = parseFloat(recs[0].val) - parseFloat(recs[1].val)
  if (diff < 0) return 'down'
  if (diff > 0) return 'up'
  return 'flat'
}

function circDiffText(part: string): string {
  const recs = circRecords.value.filter(r => r.part === part).sort((a, b) => a.d < b.d ? 1 : -1)
  if (recs.length < 2) return '0.0 cm / 周'
  const diff = (parseFloat(recs[0].val) - parseFloat(recs[1].val)).toFixed(1)
  return (parseFloat(diff) > 0 ? '+' : '') + diff + ' cm / 周'
}

function selectPart(key: string) {
  selectedPart.value = key
  formPart.value = key
  const latest = circRecords.value.filter(r => r.part === key).sort((a, b) => a.d < b.d ? 1 : -1)[0]
  formVal.value = latest ? parseFloat(latest.val) : (CIRC.find(p => p.key === key)?.def || 0)
}

function onFormPartChange() {
  selectPart(formPart.value)
}

const recentCircLogs = computed(() => {
  return circRecords.value
    .filter(r => r.part === selectedPart.value)
    .sort((a, b) => a.d < b.d ? 1 : -1)
    .slice(0, 6)
})

const circChartSvg = computed(() => {
  const recs = circRecords.value.filter(r => r.part === selectedPart.value).sort((a, b) => a.d < b.d ? -1 : 1)
  if (recs.length < 2) return '<div class="chart-empty">暂无趋势数据</div>'
  const vals = recs.map(r => parseFloat(r.val))
  const W = 420, H = 180, pad = { l: 30, r: 14, t: 14, b: 22 }
  const iw = W - pad.l - pad.r, ih = H - pad.t - pad.b
  const min = Math.min(...vals) - 0.5, max = Math.max(...vals) + 0.5, range = max - min || 1
  const pts = vals.map((v, i) => ({
    x: pad.l + i * (iw / (vals.length - 1)),
    y: pad.t + ih - ((v - min) / range) * ih,
    v: v.toFixed(1),
  }))
  const path = smoothPath(pts)
  const areaPath = path + ` L ${pts[pts.length - 1].x.toFixed(1)} ${(pad.t + ih)} L ${pts[0].x.toFixed(1)} ${(pad.t + ih)} Z`
  let svg = `<svg viewBox="0 0 ${W} ${H}"><defs><linearGradient id="pfg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#D9A24A" stop-opacity=".22"/><stop offset="1" stop-color="#D9A24A" stop-opacity="0"/></linearGradient></defs>`
  svg += `<path d="${areaPath}" fill="url(#pfg)"/>`
  svg += `<path d="${path}" fill="none" stroke="#D9A24A" stroke-width="2" stroke-linejoin="round"/>`
  pts.forEach(p => {
    svg += `<g class="pt"><circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="#fff" stroke="#B8863B" stroke-width="2"/><text x="${p.x.toFixed(1)}" y="${(p.y - 10).toFixed(1)}" text-anchor="middle" font-size="9" fill="#2A2620" font-family="Noto Serif SC">${p.v}</text></g>`
  })
  svg += `</svg>`
  return svg
})

function smoothPath(pts: { x: number; y: number }[]): string {
  if (pts.length < 2) return pts.length ? `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}` : ''
  let d = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)]
    d += ` C ${(p1.x + (p2.x - p0.x) / 6).toFixed(1)} ${(p1.y + (p2.y - p0.y) / 6).toFixed(1)} ${(p2.x - (p3.x - p1.x) / 6).toFixed(1)} ${(p2.y - (p3.y - p1.y) / 6).toFixed(1)} ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`
  }
  return d
}

function saveCirc() {
  if (!formVal.value && formVal.value !== 0) {
    showToast('请输入围度数值', true)
    return
  }
  const existIdx = circRecords.value.findIndex(r => r.part === formPart.value && r.d === formDate.value)
  if (existIdx >= 0) circRecords.value[existIdx].val = formVal.value.toFixed(1)
  else circRecords.value.push({ d: formDate.value, part: formPart.value, val: formVal.value.toFixed(1) })
  circRecords.value.sort((a, b) => a.d < b.d ? 1 : -1)
  saveCircRecords()
  selectedPart.value = formPart.value
  const partName = CIRC.find(p => p.key === formPart.value)?.nm || ''
  showToast('已写入 · ' + partName + ' ' + formVal.value.toFixed(1) + ' cm')
}

/* ========== Toast ========== */
const toastMsg = ref('')
const toastErr = ref(false)
let toastTimer: any = null
function showToast(msg: string, isErr = false) {
  toastMsg.value = msg
  toastErr.value = isErr
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastMsg.value = '' }, 2600)
}

/* ========== 生命周期 ========== */
onMounted(() => {
  try { userStore.init() } catch { /* ignore */ }
  buildSymmetryMap()
  nextTick(() => {
    // 正面立即创建
    if (frontChartRef.value) {
      frontChart = new BodyChart(frontChartRef.value, {
        view: ViewSide.FRONT,
        bodyState: {},
        onMuscleClick: handleMuscleClick,
        onMuscleHover: handleMuscleHover,
      })
      setTimeout(() => setMuscleColors(frontChart, frontChartRef.value), 60)
    }
    // 背面延迟 800ms 创建，避免 backface-visibility:hidden 导致容器尺寸为 0
    setTimeout(() => {
      if (backChartRef.value && !backChart) {
        backChart = new BodyChart(backChartRef.value, {
          view: ViewSide.BACK,
          bodyState: {},
          onMuscleClick: handleMuscleClick,
          onMuscleHover: handleMuscleHover,
        })
        setTimeout(() => setMuscleColors(backChart, backChartRef.value), 60)
      }
    }, 800)
  })

  // 初始化表单
  selectPart('chest')

  // GSAP 入场动画
  import('gsap').then(({ gsap }) => {
    const band = bandRef.value, paper = paperRef.value
    if (!band || !paper) return
    const tl = gsap.timeline()
    tl.fromTo(band.querySelectorAll('.crumb-node'),
      { opacity: 0, y: 12, scale: 0.6 },
      { opacity: 1, y: 0, scale: 1, duration: 0.45, stagger: 0.15, ease: 'back.out(2)' })
      .fromTo(band.querySelectorAll('.db-top-right, .db-core-wrap'),
        { opacity: 0, y: 14 },
        { opacity: 1, y: 0, duration: 0.6, delay: 0.15, ease: 'power3.out' }, '-=0.4')
      .fromTo(band.querySelectorAll('.db-station-wrap'),
        { scale: 0, opacity: 0 },
        { scale: 1, opacity: 1, duration: 0.5, stagger: 0.08, delay: 0.35, ease: 'back.out(1.7)' }, '-=0.3')
      .fromTo(paper.querySelectorAll('[data-anim]'),
        { opacity: 0, y: 24 },
        { opacity: 1, y: 0, duration: 0.7, stagger: 0.1, delay: 0.35, ease: 'power3.out' }, '-=0.2')
    // 星盘 + 环入场（注意：不能动画 transform，否则会覆盖 .pf-flip.is-back 的 CSS transform）
    const flipEl = paper.querySelector('.pf-flip')
    if (flipEl) gsap.fromTo(flipEl,
      { opacity: 0 },
      { opacity: 1, duration: 0.7, delay: 0.5, ease: 'power2.out' })
    const ringEl = paper.querySelector('.pf-astro-ring')
    if (ringEl) gsap.fromTo(ringEl,
      { opacity: 0, scale: 0.7 },
      { opacity: 1, scale: 1, duration: 0.85, delay: 0.4, ease: 'power3.out' })
    const glowEl = paper.querySelector('.pf-astro-glow')
    if (glowEl) gsap.fromTo(glowEl,
      { opacity: 0, scale: 0.6 },
      { opacity: 1, scale: 1, duration: 0.9, delay: 0.45, ease: 'power3.out' })
  }).catch(() => { /* ignore */ })
})

onUnmounted(() => {
  if (frontChart) frontChart.destroy()
  if (backChart) backChart.destroy()
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<style scoped>
.diet-page {
  font-family: 'Noto Sans SC', system-ui, sans-serif;
  --txt: #2A2620;
  --gold-l: #D9A24A;
  --gold-d: #B8863B;
}

/* ================= 深壳星轨带 ================= */
.db-band {
  position: relative;
  padding: 14px 22px 8px;
  background:
    radial-gradient(ellipse at 12% 20%, rgba(217,162,74,.16), transparent 42%),
    linear-gradient(165deg, #1C1710, #12100A);
  border-radius: 18px;
  margin-bottom: 16px;
  overflow: hidden;
}
.db-glow {
  position: absolute; border-radius: 50%; filter: blur(46px); pointer-events: none; z-index: 0;
}
.db-glow--1 {
  width: 180px; height: 180px; right: -50px; top: -100px;
  background: rgba(232,185,115,.12);
  animation: dbGlowFloat 9s ease-in-out infinite alternate;
}
.db-glow--2 {
  width: 150px; height: 150px; left: -60px; bottom: -90px;
  background: rgba(179,107,42,.1);
  animation: dbGlowFloat 11s ease-in-out infinite alternate-reverse;
}
@keyframes dbGlowFloat {
  from { transform: translate3d(0,0,0) scale(1); }
  to { transform: translate3d(14px,9px,0) scale(1.12); }
}
.db-top {
  position: relative; z-index: 2;
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  margin-bottom: 8px;
}
.star-crumbs { display: flex; align-items: center; }
.crumb-wrap { display: flex; align-items: center; }
.crumb-link {
  width: 42px; height: 0;
  border-top: 1.5px dashed rgba(184,134,59,.45);
  margin: 0 5px;
}
.crumb-node {
  display: inline-flex; align-items: center; gap: 7px;
  font-size: 11px; color: #8C7A5E;
  background: none; border: none; cursor: pointer;
  font-family: inherit; transition: color 0.25s;
}
.crumb-node:hover { color: rgba(255,255,255,.8); }
.crumb-node .nd {
  width: 21px; height: 21px; border-radius: 50%;
  border: 1px solid rgba(217,162,74,.4);
  color: #8C7A5E;
  display: flex; align-items: center; justify-content: center;
  background: rgba(24,19,12,.9);
  transition: 0.25s;
}
.crumb-node.hot { color: #F6EAD6; font-weight: 700; }
.crumb-node.hot .nd {
  color: var(--gold-l);
  border-color: var(--gold-l);
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  box-shadow: 0 0 14px rgba(217,162,74,.45);
}
.db-top-right {
  margin-left: auto;
  display: flex; align-items: center; gap: 12px;
}
.db-date {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px; color: #B9A78A;
  border: 1px solid rgba(217,162,74,.3);
  background: rgba(217,162,74,.08);
  border-radius: 999px; padding: 3px 10px;
}
.db-date b { color: var(--gold-l); font-family: 'Noto Serif SC', serif; }


.db-const {
  position: relative; z-index: 1;
  height: 108px; margin-top: 6px;
}
.db-line {
  position: absolute; inset: 0;
  width: 100%; height: 100%; overflow: visible;
}
.db-line path {
  fill: none; stroke: rgba(217,162,74,.35);
  stroke-width: 1.2; stroke-dasharray: 5 6;
  vector-effect: non-scaling-stroke;
}
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
  border: 1px solid rgba(232,185,115,.55);
  display: flex; align-items: center; justify-content: center;
  color: var(--gold-l);
  box-shadow: 0 0 22px rgba(217,162,74,.32);
  animation: dbBreath 3.2s ease-in-out infinite;
}
@keyframes dbBreath {
  0%, 100% { box-shadow: 0 0 18px rgba(217,162,74,.3); }
  50% { box-shadow: 0 0 34px rgba(217,162,74,.52); }
}
.db-core .tt b {
  display: block; font-size: 12.5px;
  color: #F6EAD6; font-weight: 700; letter-spacing: 0.08em;
}
.db-core .tt span {
  display: block; margin-top: 2px;
  font-size: 9.5px; color: #9A8A6C; letter-spacing: 0.12em;
}

.db-station-wrap {
  position: absolute; top: 50%;
  width: 44px; height: 44px;
  margin: -22px 0 0 -22px; z-index: 3;
}
.db-station-float {
  width: 100%; height: 100%;
  animation: dbFloat 4.6s ease-in-out infinite alternate;
}
@keyframes dbFloat {
  from { transform: translateY(4px); }
  to { transform: translateY(-8px); }
}
.db-station {
  position: relative; width: 44px; height: 44px;
  border-radius: 50%; cursor: pointer;
  background: rgba(24,19,12,.95);
  border: 1px solid rgba(217,162,74,.45);
  color: var(--gold-l);
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.3s cubic-bezier(.34,1.5,.5,1), border-color 0.3s, box-shadow 0.3s;
}
.db-station .wb {
  width: 30px; height: 30px; border-radius: 50%;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(217,162,74,.35);
  display: flex; align-items: center; justify-content: center;
}
.db-station .nm {
  position: absolute; top: -26px; left: 50%;
  transform: translateX(-50%);
  font-size: 10px; color: #F0E2C4;
  white-space: nowrap; letter-spacing: 0.06em;
  opacity: 0.72; transition: 0.3s;
}
.db-station .ds {
  position: absolute; top: calc(100% + 10px); left: 50%;
  transform: translateX(-50%) translateY(4px);
  white-space: nowrap; font-size: 9.5px;
  color: #F6EAD6; background: rgba(24,19,12,.95);
  border: 1px solid rgba(217,162,74,.4);
  padding: 2px 9px; border-radius: 999px;
  opacity: 0; transition: 0.28s; pointer-events: none;
}
.db-station:hover {
  transform: scale(1.14);
  border-color: var(--gold-l);
  box-shadow: 0 0 0 5px rgba(217,162,74,.14), 0 10px 26px rgba(217,162,74,.32);
}
.db-station:hover .ds { opacity: 1; transform: translateX(-50%) translateY(0); }
.db-station:hover .nm { opacity: 1; color: var(--gold-l); }

/* ================= 浅芯工作区 ================= */
.db-paper {
  position: relative;
  background:
    radial-gradient(circle at 18% 0%, rgba(184,134,59,.08), transparent 40%),
    radial-gradient(circle at 86% 100%, rgba(201,143,62,.06), transparent 44%),
    linear-gradient(180deg, #F8F4EA, #F2EBDC);
  border-radius: 18px;
  padding: 18px 22px 22px;
  color: var(--txt);
}
.db-head {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  margin-bottom: 14px;
}
.sec-t {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 700; color: var(--txt);
}
.sec-t::before {
  content: ''; width: 3px; height: 14px; border-radius: 99px;
  background: linear-gradient(180deg, var(--gold-l), var(--gold-d));
}

.pf-flip-btn {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 7px 16px; border-radius: 999px;
  border: 1px solid rgba(184,134,59,.45);
  background: linear-gradient(135deg, rgba(232,185,115,.22), rgba(184,134,59,.14));
  color: #8A6428; font-size: 11.5px; font-weight: 700;
  cursor: pointer; letter-spacing: 0.05em; transition: 0.25s;
  font-family: inherit;
}
.pf-flip-btn:hover {
  background: linear-gradient(135deg, rgba(232,185,115,.32), rgba(184,134,59,.22));
  transform: translateY(-1px);
}
.pf-face-tag {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px; color: var(--gold-d);
  border: 1px solid rgba(184,134,59,.35);
  background: rgba(217,162,74,.08);
  border-radius: 999px; padding: 4px 12px; font-weight: 600;
}

.m-blocks {
  display: grid; grid-template-columns: 7fr 5fr;
  gap: 12px; margin-top: 14px;
}
.m-block {
  background: rgba(255,255,255,.75);
  border: 1px solid rgba(184,134,59,.16);
  border-radius: 16px; padding: 16px 18px;
}
.astro-block {
  background: linear-gradient(180deg, rgba(248,244,234,.78), rgba(242,235,220,.55));
  min-height: 760px;
}
.bl-head {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.bl-head b { font-size: 13px; color: var(--txt); font-weight: 700; }
.bl-head span { font-size: 10px; color: rgba(42,38,32,.4); }
.sec-label {
  margin-top: 16px; font-size: 10.5px;
  color: var(--gold-d); letter-spacing: 0.08em;
  font-weight: 600;
  display: flex; align-items: center; gap: 10px;
}
.sec-label::before, .sec-label::after {
  content: ''; flex: 1; height: 0;
  border-top: 1px dashed rgba(184,134,59,.3);
}
.btn-gold {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 9px 20px; border-radius: 10px;
  border: none; cursor: pointer;
  background: linear-gradient(135deg, var(--gold-l), var(--gold-d));
  color: #fff; font-size: 12.5px; font-weight: 600;
  letter-spacing: 0.04em; transition: 0.25s;
  font-family: inherit;
}
.btn-gold:hover { opacity: 0.9; transform: translateY(-1px); }
.btn-save { margin-top: 10px; width: 100%; justify-content: center; }
.btn-full { width: 100%; justify-content: center; margin-top: 8px; }
.chart-box { margin-top: 12px; position: relative; }
.chart-box svg { width: 100%; height: auto; display: block; }
.chart-box :deep(.pt) { cursor: pointer; }
.p4-hint { font-size: 10px; color: rgba(42,38,32,.45); }
.chart-empty {
  text-align: center; padding: 30px 0;
  color: rgba(42,38,32,.4); font-size: 12px;
}

/* ================= 双面星盘 ================= */
.pf-astro {
  position: relative;
  display: flex; align-items: center; justify-content: center;
  min-height: 620px; perspective: 1400px;
  margin-top: 12px;
}
.pf-astro-glow {
  position: absolute; left: 50%; top: 50%;
  width: 480px; height: 480px;
  margin: -240px 0 0 -240px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(217,162,74,.18), transparent 65%);
  filter: blur(20px); pointer-events: none;
  animation: dbBreath 5s ease-in-out infinite;
}
.pf-astro-ring {
  position: absolute; left: 50%; top: 50%;
  width: 540px; height: 540px;
  margin: -270px 0 0 -270px;
  pointer-events: none;
  animation: pfRingSpin 70s linear infinite;
}
.pf-astro-ring :deep(svg) { width: 100%; height: 100%; overflow: visible; }
@keyframes pfRingSpin { to { transform: rotate(360deg); } }

.pf-flip {
  position: relative;
  width: 300px; height: 520px;
  transform-style: preserve-3d;
  transition: transform 0.9s cubic-bezier(.5,.05,.3,1);
}
.pf-flip.is-back { transform: rotateY(180deg); }
/* 关键修复：backface-visibility 只保证视觉隐藏，共面 3D 卡面的命中测试不可靠
 * （翻转后真实鼠标点击会穿透到被隐藏的正面，导致背面点击拿到正面肌群 ID 而无高亮）。
 * 非活动卡面必须显式禁用指针事件；活动卡面显式恢复。 */
.pf-flip:not(.is-back) .pf-face.back { pointer-events: none; }
.pf-flip.is-back .pf-face.front { pointer-events: none; }
.pf-flip.is-back .pf-face.back,
.pf-flip:not(.is-back) .pf-face.front { pointer-events: auto; }
.pf-face {
  position: absolute; inset: 0;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  border-radius: 18px; overflow: hidden;
  background: radial-gradient(ellipse at 50% 35%, rgba(40,30,18,.7), rgba(20,15,9,.95));
  border: 1px solid rgba(232,185,115,.4);
  box-shadow: 0 0 40px rgba(217,162,74,.18) inset, 0 18px 40px -16px rgba(0,0,0,.6);
}
.pf-face.back { transform: rotateY(180deg); }
.pf-face .face-label {
  position: absolute; top: 8px; left: 50%;
  transform: translateX(-50%);
  font-size: 9.5px; letter-spacing: 0.16em;
  color: rgba(232,185,115,.75); font-weight: 700;
  z-index: 5;
}
.pf-face .pf-face-dust {
  position: absolute; inset: 0;
  pointer-events: none; opacity: 0.7;
}
.pf-face .pf-face-dust :deep(svg) {
  width: 100%; height: 100%;
}
.pf-face .body-svg-wrap {
  position: relative; z-index: 2;
  padding-top: 18px;
  display: flex; justify-content: center;
  height: 100%;
}
.body-chart-container {
  position: relative;
  width: 250px; height: 480px;
}
.body-chart-container :deep(div) {
  padding: 0 !important;
}
.body-chart-container :deep(svg) {
  width: auto !important; height: 100% !important;
  max-height: none !important;
  max-width: none !important;
  overflow: visible;
  filter: drop-shadow(0 0 10px rgba(217,162,74,.25));
}
.body-chart-container :deep([data-muscle-id]) {
  transition: transform 0.15s ease, filter 0.25s;
  transform-box: fill-box; transform-origin: center;
  cursor: pointer;
}
.body-chart-container :deep([data-muscle-id]:hover) {
  transform: scale(1.1);
  filter: drop-shadow(0 0 8px rgba(232,185,115,.95));
}
.body-chart-container :deep([data-muscle-id][style*="intensity: 8"]) {
  filter: drop-shadow(0 0 12px rgba(232,185,115,1));
}
.mtip {
  position: absolute; z-index: 30;
  background: rgba(255,255,255,.97);
  border: 1px solid rgba(184,134,59,.45);
  border-radius: 10px;
  padding: 6px 10px; font-size: 11px;
  color: var(--txt);
  box-shadow: 0 10px 24px -8px rgba(90,70,40,.4);
  pointer-events: none;
  transform: translate(-50%, -115%);
  white-space: nowrap;
}
.mtip b { font-weight: 700; }
.mtip i { font-style: normal; color: var(--gold-d); }

/* ================= 围度卡片 / 表单 / 记录 ================= */
.circ-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 10px; margin-top: 28px;
}
.circ-card {
  background: rgba(255,255,255,.75);
  border: 1px solid rgba(184,134,59,.16);
  border-radius: 14px;
  padding: 12px 14px;
  position: relative; overflow: hidden;
  cursor: pointer; transition: 0.25s;
}
.circ-card:hover {
  border-color: var(--gold-d);
  box-shadow: 0 6px 20px -8px rgba(184,134,59,.3);
}
.circ-card.on {
  border-color: var(--gold-l);
  box-shadow: 0 0 0 3px rgba(217,162,74,.16), 0 6px 20px -8px rgba(184,134,59,.35);
}
.circ-card::after {
  content: ''; position: absolute;
  right: -16px; top: -16px;
  width: 52px; height: 52px; border-radius: 50%;
  background: radial-gradient(circle, rgba(217,162,74,.12), transparent 70%);
}
.circ-card .cl {
  display: flex; align-items: center; gap: 6px;
  font-size: 10.5px; color: rgba(42,38,32,.5);
}
.circ-card .cv {
  font-family: 'Noto Serif SC', serif;
  font-size: 22px; font-weight: 900;
  color: var(--txt); margin-top: 3px;
}
.circ-card .cv small {
  font-size: 11px; font-weight: 600;
  color: rgba(42,38,32,.45);
}
.circ-card .cd {
  font-size: 10px; font-weight: 700;
  margin-top: 2px;
}
.circ-card .cd.down { color: #2F7D5B; }
.circ-card .cd.up { color: #C0522F; }
.circ-card .cd.flat { color: rgba(42,38,32,.4); }

.circ-form {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 9px; margin-top: 12px;
}
.circ-form .ff { display: flex; flex-direction: column; gap: 4px; }
.circ-form .ff-full { grid-column: 1 / -1; }
.circ-form label {
  font-size: 10px; color: rgba(42,38,32,.5);
}
.circ-form select,
.circ-form input {
  padding: 8px 10px; border-radius: 9px;
  border: 1px solid rgba(184,134,59,.28);
  background: #fff; font-size: 12px;
  color: var(--txt); outline: none;
  font-family: inherit; width: 100%;
}
.circ-form select:focus,
.circ-form input:focus {
  border-color: var(--gold-l);
  box-shadow: 0 0 0 2px rgba(217,162,74,.15);
}

.circ-log {
  margin-top: 12px; max-height: 200px;
  overflow-y: auto;
}
.circ-log-item {
  display: flex; align-items: center; gap: 10px;
  padding: 7px 10px; border-radius: 10px;
  background: rgba(255,255,255,.6);
  border: 1px solid rgba(184,134,59,.12);
  font-size: 11.5px;
}
.circ-log-item + .circ-log-item { margin-top: 6px; }
.circ-log-item.empty {
  justify-content: center;
  color: rgba(140,122,94,.75);
}
.circ-log-item .dt {
  font-size: 9.5px; color: rgba(42,38,32,.45);
  width: 56px; flex-shrink: 0;
}
.circ-log-item .nm {
  flex: 1; color: var(--txt); font-weight: 600;
}
.circ-log-item .vl {
  font-family: 'Noto Serif SC', serif;
  font-weight: 800; color: var(--txt);
}

/* ================= 训练推荐 ================= */
.subdiv-row {
  display: flex; align-items: center; gap: 6px;
  flex-wrap: wrap; margin-top: 12px;
}
.subdiv-label {
  font-size: 11px; font-weight: 500;
  color: var(--txt); margin-right: 2px;
}
.subdiv-btn {
  padding: 5px 12px; border-radius: 8px;
  font-size: 11px; font-weight: 500;
  background: #fff; color: #6E6350;
  border: 1px solid rgba(184,134,59,.2);
  cursor: pointer; transition: 0.2s;
  font-family: inherit;
}
.subdiv-btn:hover {
  background: rgba(217,162,74,.08);
  border-color: var(--gold-d);
}
.subdiv-btn.active {
  background: linear-gradient(135deg, var(--gold-l), var(--gold-d));
  color: #fff; border-color: transparent;
  box-shadow: 0 2px 8px -2px rgba(184,134,59,.4);
}

.level-panel {
  margin-top: 12px; padding: 12px;
  background: rgba(217,162,74,.05);
  border: 1px solid rgba(184,134,59,.15);
  border-radius: 12px;
}
.level-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}
.level-title {
  font-size: 11px; font-weight: 500;
  color: var(--txt);
  display: flex; align-items: center; gap: 6px;
}
.level-cur { font-size: 10px; color: rgba(42,38,32,.5); }
.level-cur b { color: var(--gold-d); }
.level-btns { display: flex; flex-wrap: wrap; gap: 5px; }
.level-btn {
  padding: 4px 10px; border-radius: 999px;
  font-size: 10.5px; font-weight: 500;
  background: #fff; color: #6E6350;
  border: 1px solid rgba(184,134,59,.2);
  cursor: pointer; transition: 0.2s;
  font-family: inherit;
}
.level-btn:hover { background: rgba(217,162,74,.08); }
.level-btn.active {
  background: linear-gradient(135deg, var(--gold-l), var(--gold-d));
  color: #fff; border-color: transparent;
  box-shadow: 0 2px 6px -2px rgba(184,134,59,.4);
}
.level-btn.dashed { border-style: dashed; }

.quick-groups {
  display: flex; flex-wrap: wrap; gap: 5px;
  margin-top: 10px;
}
.quick-btn {
  padding: 4px 10px; border-radius: 8px;
  font-size: 10.5px; font-weight: 500;
  background: #fff; color: #6E6350;
  border: 1px solid rgba(184,134,59,.2);
  cursor: pointer; transition: 0.2s;
  font-family: inherit;
}
.quick-btn:hover { background: rgba(217,162,74,.08); }
.quick-btn.active {
  color: #fff; border-color: transparent;
}

.level-filter {
  display: flex; align-items: center; gap: 5px;
  flex-wrap: wrap; margin-top: 10px;
}
.filter-label {
  font-size: 10.5px; color: rgba(42,38,32,.5);
  margin-right: 2px;
}
.filter-btn {
  padding: 4px 10px; border-radius: 999px;
  font-size: 10.5px; font-weight: 500;
  background: rgba(217,162,74,.06);
  color: #6E6350;
  border: none; cursor: pointer; transition: 0.2s;
  font-family: inherit;
}
.filter-btn:hover { background: rgba(217,162,74,.14); }
.filter-btn.active {
  background: linear-gradient(135deg, var(--gold-l), var(--gold-d));
  color: #fff;
  box-shadow: 0 2px 6px -2px rgba(184,134,59,.4);
}

/* 训练推荐卡片 */
.tx-list {
  display: flex; flex-direction: column; gap: 8px;
  margin-top: 12px; max-height: 320px;
  overflow-y: auto; padding-right: 2px;
}
.tx-list::-webkit-scrollbar { width: 4px; }
.tx-list::-webkit-scrollbar-thumb { background: #e5d9bf; border-radius: 2px; }
.tx-card {
  position: relative;
  background: rgba(255,255,255,.8);
  border: 1px solid rgba(184,134,59,.18);
  border-radius: 12px;
  padding: 10px 13px;
  transition: 0.25s; cursor: pointer;
}
.tx-card:hover {
  border-color: var(--gold-d);
  box-shadow: 0 6px 18px -8px rgba(184,134,59,.3);
  transform: translateY(-1px);
}
.tx-card .txh {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px;
}
.tx-card .txh b {
  font-size: 12.5px; color: var(--txt); font-weight: 700;
}
.tx-card .txh .txs {
  font-size: 10.5px; color: var(--gold-d); font-weight: 600;
}
.tx-card .txm {
  margin-top: 4px;
  font-size: 10px; color: rgba(42,38,32,.5);
}
.tx-card .txm .lv {
  display: inline-block; margin-left: 6px;
  padding: 1px 7px; border-radius: 99px;
  font-size: 9px; font-weight: 700; color: #fff;
}
.tx-card .tx-explain {
  position: absolute; top: 8px; right: 8px;
  padding: 2px 8px; border-radius: 6px;
  font-size: 10px; font-weight: 500;
  background: rgba(217,162,74,.1);
  color: var(--gold-d);
  border: none; cursor: pointer;
  transition: 0.2s; font-family: inherit;
}
.tx-card .tx-explain:hover { background: rgba(217,162,74,.2); }
.tx-empty {
  margin-top: 14px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 6px; min-height: 180px;
  color: rgba(42,38,32,.4);
  text-align: center; font-size: 12px;
}
.tx-empty svg { opacity: 0.5; }
.tx-empty .tx-empty-sub {
  font-size: 10.5px; color: rgba(42,38,32,.35);
  margin-top: 4px; max-width: 240px;
}

/* ================= 弹窗 ================= */
.modal-overlay {
  position: fixed; inset: 0; z-index: 50;
  background: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center;
  padding: 16px;
  backdrop-filter: blur(2px);
}
.modal-card {
  background: #fff;
  border-radius: 18px;
  max-width: 480px; width: 100%;
  max-height: 85vh; overflow: hidden;
  display: flex; flex-direction: column;
  box-shadow: 0 24px 50px -12px rgba(0,0,0,.3);
  animation: modalPop 0.4s cubic-bezier(.34,1.56,.64,1);
}
@keyframes modalPop {
  from { transform: scale(0.85); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.modal-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid rgba(184,134,59,.18);
}
.modal-head h3 {
  font-size: 16px; font-weight: 700;
  color: var(--txt); margin: 0;
}
.modal-sub {
  font-size: 11px; color: rgba(42,38,32,.5);
  margin-top: 2px;
}
.modal-close {
  background: none; border: none;
  font-size: 24px; line-height: 1;
  color: rgba(42,38,32,.5); cursor: pointer;
  padding: 0 4px;
  transition: 0.2s;
}
.modal-close:hover { color: var(--txt); }
.modal-body {
  padding: 18px 22px;
  overflow-y: auto;
}
.modal-tags {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-bottom: 12px;
}
.modal-tags .tag {
  padding: 3px 10px; border-radius: 999px;
  font-size: 10.5px; font-weight: 600;
}
.modal-tags .tag-default {
  background: rgba(184,134,59,.1);
  color: var(--gold-d);
}
.modal-desc {
  font-size: 13px; color: rgba(42,38,32,.7);
  line-height: 1.7; margin-bottom: 16px;
}
.step-section { margin-bottom: 16px; }
.step-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 600; color: var(--txt);
  margin-bottom: 12px;
}
.step-bar {
  width: 4px; height: 16px; border-radius: 99px;
  background: linear-gradient(180deg, var(--gold-l), var(--gold-d));
}
.tip-bar {
  background: linear-gradient(180deg, #F59E0B, #D97706);
}
.step-list {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 10px;
}
.step-item {
  display: flex; gap: 12px;
  align-items: flex-start;
}
.step-num {
  flex-shrink: 0;
  width: 28px; height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--gold-l), var(--gold-d));
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
}
.step-text-title {
  font-size: 13px; font-weight: 600;
  color: var(--txt);
}
.step-text-desc {
  font-size: 11.5px; color: rgba(42,38,32,.6);
  line-height: 1.6; margin-top: 2px;
}
.tip-section { margin-bottom: 16px; }
.tip-list {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 6px;
}
.tip-list li {
  display: flex; align-items: flex-start; gap: 8px;
  font-size: 11.5px; color: #92400E;
  background: rgba(245,158,11,.08);
  padding: 6px 10px; border-radius: 8px;
}
.tip-dot {
  flex-shrink: 0;
  width: 3px; height: 12px;
  background: #F59E0B; border-radius: 99px;
  margin-top: 3px;
}

/* 记录训练弹窗 */
.record-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 10px; margin-bottom: 12px;
}
.record-item {
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(248,244,234,.7);
  border: 1px solid rgba(184,134,59,.18);
  border-radius: 10px;
  padding: 8px 12px;
}
.ri-label {
  font-size: 11px; color: rgba(42,38,32,.5);
}
.ri-ctrl {
  display: flex; align-items: center; gap: 6px;
}
.ri-ctrl button {
  width: 24px; height: 24px;
  border-radius: 6px; border: none;
  background: #fff; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  color: var(--txt);
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
  transition: 0.2s;
}
.ri-ctrl button:hover { background: rgba(217,162,74,.1); }
.ri-val {
  font-weight: 700; width: 40px; text-align: center;
  color: var(--txt); font-variant-numeric: tabular-nums;
}
.ri-unit {
  font-size: 10px; color: rgba(42,38,32,.5);
  width: 28px;
}
.record-date {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 12px;
}
.date-input {
  flex: 1;
  padding: 6px 10px; border-radius: 8px;
  border: 1px solid rgba(184,134,59,.2);
  background: rgba(255,255,255,.7);
  font-size: 12px; color: var(--txt);
  outline: none; font-family: inherit;
}
.record-summary {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 8px; margin-bottom: 14px;
}
.rs-item {
  background: rgba(248,244,234,.7);
  border: 1px solid rgba(184,134,59,.18);
  border-radius: 10px;
  padding: 8px; text-align: center;
}
.rs-label {
  font-size: 10px; color: rgba(42,38,32,.5);
}
.rs-val {
  font-weight: 700; color: var(--txt);
  margin-top: 2px;
}
.rs-val.accent { color: var(--gold-d); }
.rs-val small { font-size: 9px; font-weight: 600; }

/* ================= Toast ================= */
.toast-host {
  position: absolute; top: 14px; left: 50%;
  transform: translateX(-50%);
  z-index: 50; pointer-events: none;
}
.toast {
  display: inline-flex; align-items: center; gap: 7px;
  background: rgba(24,19,12,.94);
  border: 1px solid rgba(217,162,74,.45);
  color: #F6EAD6;
  font-size: 11.5px;
  padding: 8px 16px; border-radius: 999px;
  box-shadow: 0 14px 30px -10px rgba(0,0,0,.5);
  animation: toastPop 0.45s cubic-bezier(.34,1.56,.64,1);
  color: #F6EAD6;
}
.toast :deep(svg) { color: #9FBF8F; }
@keyframes toastPop {
  from { transform: scale(0.8) translateY(-8px); opacity: 0; }
  to { transform: scale(1) translateY(0); opacity: 1; }
}
.toast.err {
  border-color: rgba(224,101,90,.6);
  color: #F0B9AE;
}
.toast.err :deep(svg) { color: #E0655A; }

/* ================= 保存提示 ================= */
.saved-tip {
  position: fixed; bottom: 24px; left: 50%;
  transform: translateX(-50%);
  z-index: 50;
  background: linear-gradient(135deg, var(--gold-l), var(--gold-d));
  color: #fff;
  padding: 10px 20px; border-radius: 12px;
  box-shadow: 0 12px 30px -8px rgba(184,134,59,.5);
  font-size: 13px; font-weight: 500;
  animation: savedPop 0.4s cubic-bezier(.34,1.56,.64,1);
}
@keyframes savedPop {
  from { transform: translateX(-50%) translateY(20px); opacity: 0; }
  to { transform: translateX(-50%) translateY(0); opacity: 1; }
}

/* ================= 过渡 ================= */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.25s, transform 0.25s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0; transform: translateY(-4px);
}

/* ================= 响应式 ================= */
@media (max-width: 880px) {
  .m-blocks { grid-template-columns: 1fr; }
  .circ-grid { grid-template-columns: repeat(2, 1fr); }
  .record-grid { grid-template-columns: 1fr; }
  .db-top-right { display: none; }
}
</style>
