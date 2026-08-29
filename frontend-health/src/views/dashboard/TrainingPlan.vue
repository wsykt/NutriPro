<template>
  <div class="diet-page">
    <!-- ===== 深壳星轨带（训练星阵 · 统计星球） ===== -->
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
            <span class="crumb-node hot"><span class="nd"><Flame :size="13" /></span>训练计划</span>
          </span>
        </div>
        <div class="db-top-right">
          <span class="db-date"><Activity :size="12" />本周 <b>{{ weekStats.count }}</b> 次训练</span>
        </div>
      </div>

      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 104" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 52 C 300 8, 440 8, 560 52 S 830 96, 960 52 S 1130 8, 1200 52" />
        </svg>

        <!-- 核心恒星（左侧主体） -->
        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><Flame :size="26" /></span>
            <span class="tt"><b>训练星阵</b><span>TRAINING MATRIX</span></span>
          </div>
        </div>

        <!-- 统计站点：标签在上 · 图星球居波线 · 数值在下 -->
        <div
          v-for="(s, i) in stations" :key="s.nm"
          class="db-station-wrap"
          :style="{ left: stationLeft(i, stations.length) + '%' }"
        >
          <span class="nm">{{ s.nm }}</span>
          <div class="db-station-float" :style="floatStyle(i)">
            <div class="db-station" :aria-label="s.nm">
              <component :is="s.icon" :size="18" :stroke-width="1.75" />
            </div>
          </div>
          <span class="ds">{{ s.ds }}</span>
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区（训练星阵） ===== -->
    <div class="db-paper" ref="paperRef">
      <div class="db-head" data-anim>
        <div class="sec-t">训练星阵 · 本周训练总览与 AI 计划</div>
      </div>

      <!-- 统计四格 -->
      <div class="tp-stats" data-anim>
        <div class="tp-stat"><div class="sl">本周训练</div><div class="sv">{{ weekStats.count }}<small>次</small></div></div>
        <div class="tp-stat"><div class="sl">总时长</div><div class="sv">{{ weekStats.duration }}<small>min</small></div></div>
        <div class="tp-stat"><div class="sl">消耗热量</div><div class="sv">{{ weekStats.calories }}<small>kcal</small></div></div>
        <div class="tp-stat"><div class="sl">连续打卡</div><div class="sv">{{ streakDays }}<small>天</small></div></div>
      </div>

      <!-- 本周训练日历 -->
      <div class="db-block" style="margin-top:12px" data-anim>
        <div class="bl-head"><b>本周训练日历</b></div>
        <div class="tp-week-bar">
          <div v-for="w in weekDays" :key="w.d" class="tp-week-day" :class="{ on: w.on }">
            <span>{{ w.d }}</span>
            <span class="dn">{{ w.on ? '✦' : '—' }}</span>
          </div>
        </div>
      </div>

      <!-- 部位分布训练卡片星阵 -->
      <div v-if="weekStats.byGroup.length > 0" class="tp-grid" data-anim>
        <div v-for="g in weekStats.byGroup" :key="g.name" class="tp-card">
          <div class="th">
            <div class="ic"><Dumbbell :size="15" /></div>
            <b>{{ g.name }}</b>
            <span class="grp">{{ g.count }} 次</span>
          </div>
          <div v-for="r in groupExercises(g.name)" :key="r.id" class="tp-ex">
            <span class="en">{{ r.exerciseName }}</span>
            <span class="es">{{ r.sets }}×{{ r.reps }}{{ r.weight > 0 ? `@${r.weight}kg` : '·自重' }}</span>
            <span class="ek">{{ r.calories }} kcal</span>
          </div>
          <div v-if="groupExercises(g.name).length === 0" class="tp-ex">
            <span class="en" style="color:rgba(42,38,32,.4)">暂无动作记录</span>
          </div>
        </div>
      </div>

      <!-- AI 对话区 -->
      <div class="tp-chat" data-anim>
        <div class="tp-chat-head"><Sparkles :size="13" />AI 训练助手 · 基于近 7 日数据制定方案</div>
        <div ref="chatBoxRef" class="tp-chat-body">
          <div v-if="chatMessages.length === 0" class="tp-msg ai">
            <div class="who">训练助手</div>
            <div class="bubble">你好！我是你的训练助手。结合你近 7 日训练数据（{{ weekStats.byGroup.map(g => `${g.name} ${g.count}次`).join('、') || '暂无记录' }}），告诉我你的目标，我来制定专属计划。</div>
          </div>
          <div v-for="(m, idx) in chatMessages" :key="idx" class="tp-msg" :class="m.role">
            <div class="who">{{ m.role === 'user' ? '你' : '训练助手' }}</div>
            <div class="bubble">{{ m.content }}</div>
          </div>
          <div v-if="chatLoading" class="tp-msg ai">
            <div class="who">训练助手</div>
            <div class="bubble">
              <Loader2 :size="13" class="spin" /> 正在分析你的训练数据...
            </div>
          </div>
        </div>
        <div class="tp-chat-input">
          <input v-model="chatInput" placeholder="描述你的训练目标..." @keydown.enter="sendChat" :disabled="chatLoading" />
          <button @click="sendChat" :disabled="chatLoading || !chatInput.trim()">
            <Send :size="12" />{{ chatLoading ? '生成中' : '发送' }}
          </button>
        </div>
      </div>

      <!-- 快捷提问 + AI 建议 -->
      <div class="db-blocks" style="margin-top:12px">
        <div class="db-block" data-anim>
          <div class="bl-head"><b>快捷提问</b><span>一键发送常见训练问题</span></div>
          <div class="quick-list">
            <button v-for="q in quickQuestions" :key="q" @click="askQuick(q)" :disabled="chatLoading" class="quick-btn">
              {{ q }}
            </button>
          </div>

          <div class="sec-label" style="margin-top:12px">AI 运动建议</div>
          <div class="advice-list">
            <button v-for="g in adviceGoals" :key="g.value" @click="getExerciseAdvice(g.value)" :disabled="!!adviceLoading" class="advice-btn">
              <component :is="g.icon" :size="13" />
              <span>{{ g.label }}</span>
              <Loader2 v-if="adviceLoading === g.value" :size="12" class="spin" style="margin-left:auto" />
            </button>
          </div>
          <div v-if="exerciseAdviceResult" class="advice-result">{{ exerciseAdviceResult }}</div>
        </div>

        <!-- 运动记录 -->
        <div class="db-block" data-anim>
          <div class="bl-head"><b>运动记录</b><span>共 {{ workoutRecords.length }} 条 · {{ totalRecordExercises }} 个动作</span></div>
          <div v-if="workoutRecords.length" class="record-list">
            <div v-for="r in workoutRecords.slice(0, 10)" :key="r.id" class="record-item">
              <div class="ri-main">
                <button @click="showExerciseStepsByName(r.exerciseName)" class="ri-name">{{ r.exerciseName }}</button>
                <span class="ri-meta">{{ r.date }} · {{ r.sets }}×{{ r.reps }}{{ r.weight > 0 ? `@${r.weight}kg` : '·自重' }} · {{ r.duration }}min</span>
                <span class="ri-cat">{{ r.category }} · {{ intensityLabel(r.intensity) }}</span>
              </div>
              <div class="ri-right">
                <span class="ri-kcal">{{ r.calories }} kcal</span>
                <button @click="removeRecord(r.id)" class="ri-del">×</button>
              </div>
            </div>
          </div>
          <div v-else class="record-empty">
            <Activity :size="28" style="opacity:.3" />
            <span>暂无运动记录</span>
            <router-link to="/dashboard/muscle-chart" class="go-link">去运动管理记录</router-link>
          </div>
        </div>
      </div>

      <!-- 动作步骤弹窗（气泡式，无灰罩） -->
      <Transition name="bubble">
        <div v-if="showStepsModal" class="step-bubble" @click.self="showStepsModal = false">
          <div class="sb-card">
            <div class="sb-head">
              <div>
                <h3>{{ currentExercise?.name }}</h3>
                <p>动作步骤说明</p>
              </div>
              <button @click="showStepsModal = false" class="sb-close">×</button>
            </div>
            <div v-if="currentExercise" class="sb-body">
              <div class="sb-tags">
                <span class="sb-tag">{{ currentExercise.category }}</span>
                <span class="sb-tag">MET {{ currentExercise.met }}</span>
                <span class="sb-tag">{{ currentExercise.difficulty }}</span>
              </div>
              <div class="sb-equip">所需器械：{{ currentExercise.equipment }}</div>
              <ol class="sb-steps">
                <li v-for="(step, i) in currentExercise.steps" :key="i">
                  <span class="step-num">{{ i + 1 }}</span>
                  <div>
                    <div class="step-title">{{ step.title }}</div>
                    <div class="step-desc">{{ step.description }}</div>
                  </div>
                </li>
              </ol>
              <div v-if="currentExercise.tips?.length" class="sb-tips">
                <div class="tips-label">训练提示</div>
                <ul>
                  <li v-for="(tip, i) in currentExercise.tips" :key="i">{{ tip }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'
import { Dumbbell, Activity, Send, Loader2, Flame, Sparkles, LayoutGrid, Calendar, Clock, Gauge } from 'lucide-vue-next'
import { EXERCISES, getExerciseById, type ExerciseDetail } from '@/data/exercises'
import { useWorkoutRecords, type WorkoutRecord } from '@/composables/useWorkoutRecords'
import { MUSCLE_GROUPS } from '@/constants'

const router = useRouter()
const userStore = useUserStore()
const workout = useWorkoutRecords()

function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'health' } }) }

// ===== 星轨带统计站点 =====
const stations = computed(() => [
  { nm: '本周训练', ds: weekStats.value.count + ' 次', icon: Calendar },
  { nm: '总时长', ds: weekStats.value.duration + ' min', icon: Clock },
  { nm: '消耗热量', ds: weekStats.value.calories + ' kcal', icon: Flame },
  { nm: '平均强度', ds: avgIntensityLabel.value, icon: Gauge }
])

const avgIntensityLabel = computed(() => {
  const recent = workout.recentDays(7)
  if (recent.length === 0) return '—'
  const high = recent.filter(r => r.intensity === 'high').length
  const low = recent.filter(r => r.intensity === 'low').length
  if (high > recent.length / 2) return '高强度'
  if (low > recent.length / 2) return '轻松'
  return '中等'
})

function stationLeft(i: number, total: number): number {
  if (total <= 1) return 60
  // 自核心恒星向右延伸，与中转站星轨带同节奏（28% ~ 92%）
  return Math.round(28 + (i * 64) / (total - 1))
}
function floatStyle(i: number) {
  const durations = [4.6, 5.2, 5.6, 4.95]
  const delays = [-0.3, -1.2, -2.1, -0.8]
  return {
    animation: `tpFloat ${durations[i % 4]}s ease-in-out ${delays[i % 4]}s infinite alternate`
  }
}

// ===== 本周训练日历 =====
const weekDays = computed(() => {
  const recent = workout.recentDays(7)
  const dayMap: Record<string, boolean> = {}
  recent.forEach(r => { dayMap[r.date] = true })
  const today = new Date()
  const labels = ['日', '一', '二', '三', '四', '五', '六']
  const result: { d: string; on: boolean }[] = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const ds = d.toISOString().slice(0, 10)
    result.push({ d: labels[d.getDay()], on: !!dayMap[ds] })
  }
  return result
})

// ===== 用户数据 =====
const userWeight = computed(() => Number(userStore.user?.weight) || 65)
const userCrowdLabel = computed(() => {
  const c = userStore.user?.crowd_type || userStore.user?.crowdType || '普通人'
  const map: Record<string, string> = {
    '普通人': '普通人群', '健身': '健身人群', '老年': '老年人',
    '孕妇': '孕妇', '青少年': '青少年', '糖尿病': '糖尿病患者'
  }
  return map[c] || c
})

// ===== AI 运动建议 =====
const adviceGoals = [
  { value: '减脂', label: '减脂塑形', icon: Flame },
  { value: '增肌', label: '增肌力量', icon: Dumbbell },
  { value: '体态改善', label: '体态改善', icon: Activity },
  { value: '保持健康', label: '保持健康', icon: Sparkles }
]
const adviceLoading = ref<string | null>(null)
const exerciseAdviceResult = ref('')
async function getExerciseAdvice(goal: string) {
  if (adviceLoading.value) return
  adviceLoading.value = goal
  exerciseAdviceResult.value = ''
  try {
    const res: any = await api.ai.exerciseAdvice(goal)
    const content = res?.content || res?.response || res?.answer || (typeof res === 'string' ? res : '')
    exerciseAdviceResult.value = String(content || '未获取到建议，请稍后重试')
  } catch (e: any) {
    exerciseAdviceResult.value = '生成失败：' + (e?.message || '未知错误，请稍后重试')
  } finally {
    adviceLoading.value = null
  }
}

// ===== 运动记录 =====
const workoutRecords = computed<WorkoutRecord[]>(() => workout.records.value)

const weekStats = computed(() => {
  const recent = workout.recentDays(7)
  const byGroupMap: Record<string, number> = {}
  recent.forEach(r => {
    const g = r.category || '其他'
    byGroupMap[g] = (byGroupMap[g] || 0) + 1
  })
  const byGroup = Object.entries(byGroupMap)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
  return {
    count: recent.length,
    duration: recent.reduce((s, r) => s + r.duration, 0),
    calories: recent.reduce((s, r) => s + r.calories, 0),
    sets: recent.reduce((s, r) => s + r.sets, 0),
    byGroup,
    recent
  }
})

const streakDays = computed(() => {
  const list = workoutRecords.value
  if (list.length === 0) return 0
  const sorted = [...list].sort((a, b) => b.date.localeCompare(a.date))
  let streak = 1
  for (let i = 1; i < sorted.length; i++) {
    const prev = new Date(sorted[i - 1].date)
    const cur = new Date(sorted[i].date)
    const diff = (prev.getTime() - cur.getTime()) / (1000 * 60 * 60 * 24)
    if (diff <= 2) streak++
    else break
  }
  return streak
})

const totalRecordExercises = computed(() => {
  const names = new Set(workoutRecords.value.map(r => r.exerciseName))
  return names.size
})

function groupExercises(groupName: string): WorkoutRecord[] {
  return workoutRecords.value.filter(r => (r.category || '其他') === groupName).slice(0, 4)
}

function removeRecord(id: string) { workout.remove(id) }

function intensityLabel(i: string): string {
  return i === 'low' ? '轻松' : i === 'high' ? '高强度' : '中等'
}

// ===== AI 对话 =====
interface ChatMessage { role: 'user' | 'ai'; content: string }
const chatMessages = ref<ChatMessage[]>([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatBoxRef = ref<HTMLElement | null>(null)

const quickQuestions = [
  '根据我最近训练，帮我调整本周计划',
  '我想增加肌肉量，怎么调整训练？',
  '我最近哪些部位练得不够？',
  '帮我制定一个减脂训练方案',
  '如何提高我的训练强度？'
]

function buildPrompt(userQuestion: string): string {
  const snapshot = workout.buildSnapshotText(userWeight.value)
  const profile = `【用户画像】
- 性别：${userStore.user?.gender || '未设置'}
- 年龄：${userStore.user?.age || '未设置'} 岁
- 身高：${userStore.user?.height || '未设置'} cm
- 体重：${userWeight.value} kg
- 人群类型：${userCrowdLabel.value}`
  return `你是一名专业的健身训练教练，请根据用户的身体数据和近 7 日训练记录，回答用户关于训练计划的问题。

${profile}

${snapshot}

要求：
1. 基于用户的实际训练数据进行分析，指出训练中的不足
2. 给出具体的、可执行的调整建议，包括推荐动作、组数、次数、重量建议、训练频率
3. 注意人群适配
4. 回答简洁专业，使用要点列出

用户问题：${userQuestion}`
}

async function sendChat() {
  const text = chatInput.value.trim()
  if (!text || chatLoading.value) return
  chatInput.value = ''
  await askQuick(text)
}

async function askQuick(question: string) {
  chatMessages.value.push({ role: 'user', content: question })
  chatLoading.value = true
  await scrollToBottom()
  try {
    const prompt = buildPrompt(question)
    const raw: any = await api.ai.consult(prompt)
    const reply = raw?.reply || (typeof raw === 'string' ? raw : '未返回内容，请稍后再试')
    chatMessages.value.push({ role: 'ai', content: reply })
  } catch {
    chatMessages.value.push({ role: 'ai', content: localGenerate(question) })
  } finally {
    chatLoading.value = false
    await scrollToBottom()
  }
}

function localGenerate(question: string): string {
  const stats = weekStats.value
  const recent = stats.recent
  if (recent.length === 0) {
    return `后端 AI 暂时不可用，以下是本地建议：\n\n你近 7 日还没有训练记录。建议从基础动作开始：\n• 胸部：卧推 3组×8-12次\n• 背部：引体向上 3组×8-12次\n• 腿部：深蹲 3组×8-12次\n每周训练 3 次，每次 40-60 分钟。`
  }
  const weakGroups: string[] = []
  const trained = new Set(recent.map(r => r.category))
  MUSCLE_GROUPS.forEach(g => { if (!trained.has(g)) weakGroups.push(g) })
  let advice = `后端 AI 暂时不可用，以下是基于你训练数据的本地分析：\n\n近 7 日训练概况：\n• 训练 ${stats.count} 次，共 ${stats.duration} 分钟，消耗 ${stats.calories} kcal\n• 总组数 ${stats.sets} 组\n• 训练部位：${stats.byGroup.map(g => `${g.name}(${g.count})`).join('、')}\n\n`
  if (weakGroups.length > 0) { advice += `训练不足的部位：${weakGroups.join('、')}\n建议下周增加这些部位的训练。\n\n` }
  advice += `调整建议：\n`
  if (/增肌|肌肉|力量/.test(question)) {
    advice += `• 增肌期建议每个部位每周训练 2 次\n• 复合动作优先：深蹲、硬拉、卧推、引体向上\n• 重量选择：8-12RM\n• 每组休息 60-90 秒，保证蛋白质摄入 1.6-2.2 g/kg`
  } else if (/减脂|减肥|瘦身/.test(question)) {
    advice += `• 减脂期保持力量训练 + 增加有氧\n• 力量训练后加 20-30 分钟中等强度有氧\n• 重量适中，组数可增加，休息时间缩短到 30-60 秒\n• 热量缺口控制在 300-500 kcal/天`
  } else {
    advice += `• 保持当前训练频率，注意部位均衡\n• 循序渐进增加重量（每周 +2.5kg）\n• 保证充足睡眠和蛋白质摄入`
  }
  return advice
}

async function scrollToBottom() {
  await nextTick()
  if (chatBoxRef.value) chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight
}

// ===== 动作步骤弹窗 =====
const showStepsModal = ref(false)
const currentExercise = ref<ExerciseDetail | null>(null)

function showExerciseStepsByName(name: string) {
  const ex = EXERCISES.find(e => e.name === name)
  if (ex) { currentExercise.value = ex; showStepsModal.value = true }
}

// ===== GSAP 入场 =====
const bandRef = ref<HTMLElement | null>(null)
const paperRef = ref<HTMLElement | null>(null)

onMounted(() => {
  try { userStore.init() } catch { /* ignore */ }
  // 入场动画
  nextTick(() => {
    if (!bandRef.value || !paperRef.value) return
    const band = bandRef.value
    const paper = paperRef.value
    const tl = (window as any).gsap?.timeline?.() || null
    if (tl) {
      tl.from(band.querySelectorAll('.star-crumbs'), { opacity: 0, y: -10, duration: 0.4, ease: 'power2.out' })
        .from(band.querySelectorAll('.db-core-wrap'), { opacity: 0, scale: 0.8, duration: 0.5, ease: 'back.out(1.4)' }, '-=0.2')
        .from(band.querySelectorAll('.db-station-wrap'), { opacity: 0, y: 20, duration: 0.4, stagger: 0.08, ease: 'power2.out' }, '-=0.3')
        .from(paper.querySelectorAll('[data-anim]'), { opacity: 0, y: 16, duration: 0.4, stagger: 0.06, ease: 'power2.out' }, '-=0.2')
    } else {
      // 无 GSAP 时 CSS fallback
      paper.querySelectorAll('[data-anim]').forEach((el) => { (el as HTMLElement).style.opacity = '1' })
    }
  })
})
</script>

<style scoped>
.diet-page { font-family: 'Noto Sans SC', system-ui, sans-serif; }

/* ===== 深壳星轨带 ===== */
.db-band {
  background: linear-gradient(180deg, #1A140C 0%, #2A2018 60%, #1A140C 100%);
  border-radius: 18px; padding: 20px 28px 16px; position: relative; overflow: hidden;
  margin-bottom: 16px;
}
.db-glow { position: absolute; border-radius: 50%; filter: blur(60px); pointer-events: none; }
.db-glow--1 { width: 280px; height: 280px; background: rgba(217,162,74,.1); top: -80px; right: 10%; }
.db-glow--2 { width: 200px; height: 200px; background: rgba(184,134,59,.08); bottom: -60px; left: 5%; }

.db-top { display: flex; align-items: center; margin-bottom: 8px; }
.star-crumbs { display: flex; align-items: center; gap: 0; }
.crumb-wrap { display: inline-flex; align-items: center; }
.crumb-link { width: 24px; height: 1px; background: rgba(217,162,74,.3); margin: 0 4px; }
.crumb-node {
  display: inline-flex; align-items: center; gap: 5px; font-size: 11px; color: rgba(255,255,255,.5);
  background: none; border: none; cursor: pointer; font-family: inherit; transition: color .25s;
}
.crumb-node:hover { color: rgba(255,255,255,.8); }
.crumb-node.hot { color: #D9A24A; }
.crumb-node .nd {
  width: 18px; height: 18px; border-radius: 6px; background: rgba(217,162,74,.12);
  display: flex; align-items: center; justify-content: center; color: #D9A24A;
}
.crumb-node.hot .nd { background: rgba(217,162,74,.25); }

.db-top-right { margin-left: auto; display: flex; align-items: center; gap: 12px; }
.db-date { font-size: 11px; color: rgba(255,255,255,.6); display: flex; align-items: center; gap: 4px; }
.db-date b { color: #D9A24A; font-family: 'Noto Serif SC', serif; }

.db-const { position: relative; min-height: 104px; }
.db-line { position: absolute; inset: 0; width: 100%; height: 100%; opacity: .3; }
.db-line path { fill: none; stroke: #D9A24A; stroke-width: 1.5; stroke-dasharray: 4 6; }

/* 核心恒星（左侧主体） */
.db-core-wrap { position: absolute; left: 0; top: 50%; transform: translateY(-50%); z-index: 2; }
.db-core { display: flex; align-items: center; gap: 14px; }
.db-core .star {
  width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%); color: #E8B973;
  border: 1.5px solid rgba(217,162,74,.55);
  box-shadow: 0 0 26px rgba(217,162,74,.28), inset 0 0 14px rgba(217,162,74,.14);
}
.db-core .tt { display: flex; flex-direction: column; gap: 3px; }
.db-core .tt b { font-size: 20px; color: #F6EAD6; font-family: 'Noto Serif SC', serif; letter-spacing: .06em; }
.db-core .tt span { font-size: 9px; color: rgba(217,162,74,.55); letter-spacing: .22em; }

/* 统计站点：标签在上 · 图星球居波线 · 数值在下 */
.db-station-wrap {
  position: absolute; top: 50%; transform: translate(-50%, -50%);
  z-index: 3; display: flex; flex-direction: column; align-items: center; gap: 7px; width: 96px;
}
.db-station-float { }
.db-station {
  width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  color: #E8B973;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1.5px solid rgba(217,162,74,.45); transition: .3s;
}
.db-station:hover { border-color: #E8B973; box-shadow: 0 0 14px rgba(217,162,74,.45); }
.db-station-wrap .nm { font-size: 10.5px; color: rgba(255,255,255,.78); font-weight: 600; letter-spacing: .04em; }
.db-station-wrap .ds { font-size: 9.5px; color: rgba(217,162,74,.75); font-family: 'Noto Serif SC', serif; }

@keyframes tpFloat {
  from { transform: translateY(-4px); }
  to { transform: translateY(4px); }
}

/* ===== 浅芯工作区 ===== */
.db-paper {
  background: rgba(255,252,247,.92); border: 1px solid rgba(184,134,59,.14);
  border-radius: 18px; padding: 20px 24px;
}
.db-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.sec-t { font-size: 14px; font-weight: 700; color: #2A2620; }

/* 统计四格 */
.tp-stats { display: grid; grid-template-columns: repeat(4,1fr); gap: 8px; }
.tp-stat {
  background: rgba(255,255,255,.72); border: 1px solid rgba(184,134,59,.16);
  border-radius: 11px; padding: 9px 11px; text-align: center;
}
.tp-stat .sl { font-size: 9.5px; color: rgba(42,38,32,.45); }
.tp-stat .sv { font-family: 'Noto Serif SC', serif; font-size: 18px; font-weight: 900; color: #2A2620; margin-top: 2px; }
.tp-stat .sv small { font-size: 10px; color: rgba(42,38,32,.45); }

/* 本周日历 */
.tp-week-bar { display: flex; gap: 4px; }
.tp-week-day {
  flex: 1; text-align: center; padding: 6px 0; border-radius: 8px;
  background: rgba(255,255,255,.5); border: 1px solid rgba(184,134,59,.12);
  font-size: 9.5px; color: rgba(42,38,32,.45);
}
.tp-week-day.on {
  background: linear-gradient(135deg, rgba(217,162,74,.2), rgba(184,134,59,.12));
  border-color: #B8863B; color: #B8863B; font-weight: 700;
}
.tp-week-day .dn { display: block; font-size: 11px; font-family: 'Noto Serif SC', serif; font-weight: 800; color: #2A2620; margin-top: 2px; }
.tp-week-day.on .dn { color: #B8863B; }

/* 训练卡片 */
.tp-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 10px; margin-top: 12px; }
.tp-card {
  background: rgba(255,255,255,.72); border: 1px solid rgba(184,134,59,.16);
  border-radius: 14px; padding: 14px; position: relative; overflow: hidden; transition: .25s;
}
.tp-card:hover { border-color: #B8863B; transform: translateY(-2px); box-shadow: 0 8px 24px -10px rgba(184,134,59,.25); }
.tp-card::after { content: ''; position: absolute; right: -14px; top: -14px; width: 48px; height: 48px; border-radius: 50%; background: radial-gradient(circle, rgba(217,162,74,.12), transparent 70%); }
.tp-card .th { display: flex; align-items: center; gap: 8px; }
.tp-card .th .ic {
  width: 32px; height: 32px; border-radius: 10px;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(217,162,74,.4); color: #D9A24A;
  display: flex; align-items: center; justify-content: center;
}
.tp-card .th b { font-size: 12.5px; color: #2A2620; }
.tp-card .th .grp { margin-left: auto; font-size: 9px; font-weight: 700; color: #B8863B; background: rgba(184,134,59,.12); padding: 2px 8px; border-radius: 99px; }
.tp-ex { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px dashed rgba(184,134,59,.12); font-size: 11px; }
.tp-ex:last-child { border: none; }
.tp-ex .en { flex: 1; color: #2A2620; }
.tp-ex .es { font-size: 9.5px; color: rgba(42,38,32,.4); }
.tp-ex .ek { font-family: 'Noto Serif SC', serif; font-weight: 800; color: #B8863B; }

/* AI 对话 */
.tp-chat { margin-top: 14px; border: 1px solid rgba(184,134,59,.2); border-radius: 14px; background: rgba(255,255,255,.6); overflow: hidden; }
.tp-chat-head { padding: 10px 14px; background: rgba(184,134,59,.08); font-size: 11.5px; font-weight: 700; color: #2A2620; display: flex; align-items: center; gap: 7px; }
.tp-chat-body { padding: 10px 14px; max-height: 220px; overflow-y: auto; }
.tp-msg { margin-bottom: 8px; }
.tp-msg .who { font-size: 9.5px; color: rgba(42,38,32,.4); margin-bottom: 2px; }
.tp-msg .bubble { display: inline-block; font-size: 11.5px; line-height: 1.7; padding: 7px 12px; border-radius: 12px; max-width: 88%; white-space: pre-wrap; }
.tp-msg.user .who { text-align: right; }
.tp-msg.user .bubble { background: linear-gradient(135deg, #D9A24A, #B8863B); color: #fff; }
.tp-msg.ai .bubble { background: #fff; border: 1px solid rgba(184,134,59,.2); color: #2A2620; }
.tp-chat-input { display: flex; gap: 8px; padding: 10px 14px; border-top: 1px solid rgba(184,134,59,.14); }
.tp-chat-input input {
  flex: 1; padding: 8px 11px; border-radius: 10px; border: 1px solid rgba(184,134,59,.25);
  background: #fff; font-size: 12px; color: #2A2620; outline: none; font-family: inherit;
}
.tp-chat-input input:focus { border-color: #B8863B; }
.tp-chat-input button {
  padding: 8px 16px; border-radius: 10px; border: none;
  background: linear-gradient(135deg, #D9A24A, #B8863B); color: #fff; font-size: 11.5px; font-weight: 600;
  cursor: pointer; display: flex; align-items: center; gap: 5px; transition: opacity .2s;
}
.tp-chat-input button:disabled { opacity: .5; cursor: not-allowed; }

/* 快捷提问 */
.quick-list { display: flex; flex-direction: column; gap: 5px; }
.quick-btn {
  text-align: left; padding: 7px 12px; border-radius: 9px; border: 1px solid rgba(184,134,59,.14);
  background: rgba(255,255,255,.6); font-size: 11.5px; color: #2A2620; cursor: pointer; font-family: inherit; transition: .2s;
}
.quick-btn:hover { background: rgba(184,134,59,.08); border-color: #B8863B; }
.quick-btn:disabled { opacity: .5; cursor: not-allowed; }

/* AI 建议 */
.advice-list { display: flex; flex-wrap: wrap; gap: 6px; }
.advice-btn {
  display: flex; align-items: center; gap: 5px; padding: 6px 12px; border-radius: 99px;
  border: 1px solid rgba(184,134,59,.2); background: rgba(255,255,255,.6);
  font-size: 11px; color: #2A2620; cursor: pointer; font-family: inherit; transition: .2s;
}
.advice-btn:hover { background: rgba(184,134,59,.1); border-color: #B8863B; }
.advice-btn:disabled { opacity: .5; cursor: not-allowed; }
.advice-btn svg { color: #B8863B; }
.advice-result {
  margin-top: 8px; padding: 10px 12px; border-radius: 10px; background: rgba(255,255,255,.6);
  border: 1px solid rgba(184,134,59,.14); font-size: 11.5px; color: #2A2620; white-space: pre-wrap; line-height: 1.7; max-height: 200px; overflow-y: auto;
}

/* 运动记录 */
.record-list { max-height: 280px; overflow-y: auto; }
.record-item {
  display: flex; align-items: center; justify-content: space-between; padding: 8px 10px;
  border-radius: 10px; background: rgba(255,255,255,.5); border: 1px solid rgba(184,134,59,.1); margin-bottom: 5px;
}
.ri-main { flex: 1; }
.ri-name { font-size: 12px; font-weight: 600; color: #2A2620; cursor: pointer; background: none; border: none; font-family: inherit; padding: 0; }
.ri-name:hover { color: #B8863B; }
.ri-meta { display: block; font-size: 10px; color: rgba(42,38,32,.45); margin-top: 1px; }
.ri-cat { display: block; font-size: 9.5px; color: rgba(42,38,32,.35); }
.ri-right { display: flex; align-items: center; gap: 8px; }
.ri-kcal { font-size: 11.5px; font-weight: 700; color: #C0522F; font-family: 'Noto Serif SC', serif; }
.ri-del { font-size: 16px; color: rgba(42,38,32,.3); cursor: pointer; background: none; border: none; padding: 0; line-height: 1; }
.ri-del:hover { color: #C0522F; }

.record-empty { text-align: center; padding: 24px 0; color: rgba(42,38,32,.4); display: flex; flex-direction: column; align-items: center; gap: 6px; }
.go-link { margin-top: 4px; padding: 6px 16px; border-radius: 8px; background: linear-gradient(135deg, #D9A24A, #B8863B); color: #fff; font-size: 12px; text-decoration: none; }

/* 通用 */
.db-blocks { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.db-block { }
.bl-head { display: flex; align-items: baseline; gap: 8px; margin-bottom: 8px; }
.bl-head b { font-size: 12.5px; color: #2A2620; }
.bl-head span { font-size: 10px; color: rgba(42,38,32,.4); }
.sec-label { font-size: 10px; font-weight: 700; color: rgba(42,38,32,.5); margin-top: 10px; margin-bottom: 5px; letter-spacing: .06em; }

/* 动作步骤弹窗（气泡式） */
.step-bubble {
  position: fixed; inset: 0; z-index: 50; display: flex; align-items: center; justify-content: center;
  background: rgba(26,20,12,.15); backdrop-filter: blur(2px);
}
.sb-card {
  background: rgba(255,252,247,.98); border: 1px solid rgba(184,134,59,.2); border-radius: 16px;
  max-width: 480px; width: 92%; max-height: 80vh; overflow: hidden; display: flex; flex-direction: column;
  box-shadow: 0 12px 48px -12px rgba(26,20,12,.2);
}
.sb-head { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-bottom: 1px solid rgba(184,134,59,.14); }
.sb-head h3 { font-size: 15px; font-weight: 700; color: #2A2620; font-family: 'Noto Serif SC', serif; margin: 0; }
.sb-head p { font-size: 10px; color: rgba(42,38,32,.4); margin: 0; }
.sb-close { font-size: 20px; color: rgba(42,38,32,.3); cursor: pointer; background: none; border: none; line-height: 1; }
.sb-close:hover { color: #2A2620; }
.sb-body { padding: 14px 18px; overflow-y: auto; }
.sb-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px; }
.sb-tag { padding: 2px 8px; border-radius: 99px; background: rgba(184,134,59,.1); color: #B8863B; font-size: 10px; font-weight: 600; }
.sb-equip { font-size: 11px; color: rgba(42,38,32,.5); margin-bottom: 10px; }
.sb-steps { list-style: none; padding: 0; margin: 0 0 10px 0; }
.sb-steps li { display: flex; gap: 10px; margin-bottom: 10px; }
.step-num { width: 24px; height: 24px; border-radius: 50%; background: linear-gradient(135deg, #D9A24A, #B8863B); color: #fff; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.step-title { font-size: 12px; font-weight: 600; color: #2A2620; }
.step-desc { font-size: 11px; color: rgba(42,38,32,.5); line-height: 1.6; margin-top: 2px; }
.sb-tips { margin-top: 8px; }
.tips-label { font-size: 11px; font-weight: 700; color: #B8863B; margin-bottom: 5px; }
.sb-tips ul { list-style: none; padding: 0; margin: 0; }
.sb-tips li { font-size: 11px; color: rgba(42,38,32,.6); padding: 4px 8px; border-radius: 6px; background: rgba(184,134,59,.06); margin-bottom: 4px; }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* 气泡弹窗动画 */
.bubble-enter-active, .bubble-leave-active { transition: all 0.25s ease; }
.bubble-enter-from { opacity: 0; transform: scale(0.9); }
.bubble-leave-to { opacity: 0; transform: scale(0.95); }

[data-anim] { opacity: 0; }
</style>
