<template>
  <div class="page-fade">
    <!-- 顶部标题 -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-morandi-accent/10 flex items-center justify-center">
            <Dumbbell class="w-6 h-6 text-morandi-accent" />
          </div>
          <div>
            <h2 class="text-2xl font-bold text-morandi-text">AI 训练计划</h2>
            <p class="text-sm text-morandi-lightText mt-0.5">基于近 7 日训练数据，与 AI 对话制定专属方案</p>
          </div>
        </div>
      </div>
      <div class="flex items-center gap-2 text-xs text-morandi-lightText bg-white/60 px-3 py-2 rounded-xl border border-morandi-soft/50">
        <Activity class="w-4 h-4 text-morandi-accent" />
        <span>本周 {{ weekStats.count }} 次训练 · {{ weekStats.duration }} 分钟</span>
      </div>
    </div>

    <!-- Tab 切换 -->
    <div class="flex gap-2 mb-6 border-b border-morandi-soft">
      <button
        v-for="tab in tabs" :key="tab.key"
        class="px-5 py-3 text-sm font-medium transition-all relative"
        :class="activeTab === tab.key ? 'text-morandi-accent' : 'text-morandi-lightText hover:text-morandi-text'"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
        <span v-if="activeTab === tab.key" class="absolute bottom-0 left-0 right-0 h-0.5 bg-morandi-accent rounded-full"></span>
      </button>
    </div>

    <!-- Tab 1: AI 对话生成计划 -->
    <div v-if="activeTab === 'chat'">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- 对话区 -->
        <div class="glass rounded-2xl p-6 lg:col-span-2 flex flex-col" style="min-height: 520px">
          <div ref="chatBoxRef" class="flex-1 overflow-y-auto mb-4 space-y-4 pr-2" style="max-height: 480px">
            <div v-if="chatMessages.length === 0" class="text-morandi-lightText text-sm text-center py-16">
              <div class="w-16 h-16 mx-auto mb-3 rounded-2xl bg-morandi-accent/10 flex items-center justify-center">
                <Dumbbell class="w-8 h-8 text-morandi-accent" />
              </div>
              <p class="font-medium text-morandi-text">你好！我是你的训练助手</p>
              <p class="mt-2">告诉我你的训练目标，结合你近 7 日的训练数据，我来制定专属计划</p>
              <div class="mt-4 text-xs text-morandi-lightText">
                你可以说："帮我调整训练计划"、"我想增加胸肌训练"、"最近腿部练得太多"
              </div>
            </div>
            <div v-for="(m, idx) in chatMessages" :key="idx" class="flex" :class="{ 'justify-end': m.role === 'user' }">
              <div :class="[
                'max-w-[85%] px-4 py-3 rounded-xl text-sm leading-relaxed',
                m.role === 'user' ? 'bg-morandi-accent text-white' : 'bg-white/70 text-morandi-text'
              ]">
                <div class="whitespace-pre-wrap">{{ m.content }}</div>
              </div>
            </div>
            <div v-if="chatLoading" class="flex">
              <div class="bg-white/70 text-morandi-text px-4 py-3 rounded-xl text-sm">
                <span class="inline-flex items-center gap-2">
                  <Loader2 class="w-4 h-4 animate-spin text-morandi-accent" />
                  正在分析你的训练数据...
                </span>
              </div>
            </div>
          </div>
          <form @submit.prevent="sendChat" class="flex gap-3">
            <input
              v-model="chatInput"
              class="flex-1 px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft text-sm outline-none focus:border-morandi-accent"
              placeholder="描述你的训练目标或想调整的方向..."
              :disabled="chatLoading"
            />
            <button
              type="submit" :disabled="chatLoading || !chatInput.trim()"
              class="px-5 py-3 rounded-xl bg-morandi-accent text-white text-sm hover:opacity-90 transition-opacity disabled:opacity-60 flex items-center gap-2"
            >
              <Send class="w-4 h-4" />
              {{ chatLoading ? '生成中...' : '发送' }}
            </button>
          </form>
        </div>

        <!-- 侧边栏 -->
        <div class="space-y-4">
          <!-- 快捷提问 -->
          <div class="glass rounded-2xl p-5">
            <h3 class="font-semibold mb-3 text-morandi-text flex items-center gap-2">
              <Zap class="w-4 h-4 text-morandi-accent" />
              快捷提问
            </h3>
            <div class="space-y-2">
              <button v-for="q in quickQuestions" :key="q" @click="askQuick(q)" :disabled="chatLoading" class="w-full text-left px-4 py-2 rounded-xl bg-white/70 text-morandi-text text-sm hover:bg-morandi-soft transition-colors disabled:opacity-60">
                {{ q }}
              </button>
            </div>
          </div>

          <!-- 近七日训练数据快照 -->
          <div class="glass rounded-2xl p-5">
            <h3 class="font-semibold mb-3 text-morandi-text flex items-center gap-2">
              <Calendar class="w-4 h-4 text-morandi-accent" />
              近七日训练数据快照
            </h3>
            <div v-if="weekStats.count > 0" class="text-xs text-morandi-text space-y-2.5 leading-relaxed">
              <div class="flex items-center gap-2">
                <Activity class="w-3.5 h-3.5 text-morandi-accent" />
                <span>训练次数：<span class="font-semibold">{{ weekStats.count }} 次</span></span>
              </div>
              <div class="flex items-center gap-2">
                <Clock class="w-3.5 h-3.5 text-morandi-accent" />
                <span>总时长：<span class="font-semibold">{{ weekStats.duration }} 分钟</span></span>
              </div>
              <div class="flex items-center gap-2">
                <Flame class="w-3.5 h-3.5 text-orange-500" />
                <span>消耗：<span class="font-semibold">{{ weekStats.calories }} kcal</span></span>
              </div>
              <div class="flex items-center gap-2">
                <Layers class="w-3.5 h-3.5 text-morandi-accent" />
                <span>总组数：<span class="font-semibold">{{ weekStats.sets }} 组</span></span>
              </div>

              <div v-if="weekStats.byGroup.length > 0" class="mt-3 pt-3 border-t border-morandi-soft/40">
                <div class="font-medium mb-2">部位分布：</div>
                <div class="space-y-1">
                  <div v-for="g in weekStats.byGroup" :key="g.name" class="flex items-center justify-between">
                    <span class="text-morandi-lightText">{{ g.name }}</span>
                    <span class="font-medium text-morandi-text">{{ g.count }} 次</span>
                  </div>
                </div>
              </div>

              <div v-if="weekStats.recent.length > 0" class="mt-3 pt-3 border-t border-morandi-soft/40">
                <div class="font-medium mb-2">最近训练：</div>
                <div class="space-y-1.5">
                  <div v-for="r in weekStats.recent.slice(0, 5)" :key="r.id" class="pl-2 border-l-2 border-morandi-accent/40">
                    <div class="font-medium text-morandi-text">
                      {{ r.exerciseName }}
                      <span class="text-morandi-lightText font-normal">
                        · {{ r.sets }}×{{ r.reps }}{{ r.weight > 0 ? `@${r.weight}kg` : '' }}
                      </span>
                    </div>
                    <div class="text-morandi-lightText">{{ r.date }} · {{ r.duration }}分钟</div>
                  </div>
                </div>
              </div>

              <div class="mt-3 pt-3 border-t border-morandi-soft/40 text-morandi-lightText">
                <User class="w-3.5 h-3.5 text-morandi-accent inline mr-1" />
                体重 {{ userWeight }} kg · 人群 {{ userCrowdLabel }}
              </div>
            </div>
            <div v-else class="text-xs text-morandi-lightText py-4 text-center">
              <Activity class="w-8 h-8 mx-auto mb-2 opacity-30" />
              近 7 日暂无训练记录
              <div class="mt-2">
                去 <router-link to="/dashboard/muscle-chart" class="text-morandi-accent hover:underline">运动管理</router-link> 记录训练
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 2: 运动记录 -->
    <div v-if="activeTab === 'records'">
      <!-- 统计卡片 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
        <div class="glass rounded-2xl p-4 text-center">
          <div class="text-xs text-morandi-lightText mb-1">本周运动</div>
          <div class="text-2xl font-bold text-morandi-accent">{{ weekStats.count }}<span class="text-xs font-normal text-morandi-lightText ml-1">次</span></div>
        </div>
        <div class="glass rounded-2xl p-4 text-center">
          <div class="text-xs text-morandi-lightText mb-1">本周时长</div>
          <div class="text-2xl font-bold text-morandi-text">{{ weekStats.duration }}<span class="text-xs font-normal text-morandi-lightText ml-1">分钟</span></div>
        </div>
        <div class="glass rounded-2xl p-4 text-center">
          <div class="text-xs text-morandi-lightText mb-1">本周消耗</div>
          <div class="text-2xl font-bold text-orange-500">{{ weekStats.calories }}<span class="text-xs font-normal text-morandi-lightText ml-1">千卡</span></div>
        </div>
        <div class="glass rounded-2xl p-4 text-center">
          <div class="text-xs text-morandi-lightText mb-1">连续打卡</div>
          <div class="text-2xl font-bold text-morandi-text">{{ streakDays }}<span class="text-xs font-normal text-morandi-lightText ml-1">天</span></div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <!-- 历史记录 -->
        <div class="glass rounded-2xl p-5 md:col-span-2">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-morandi-text flex items-center gap-2">
              <History class="w-4 h-4 text-morandi-accent" />
              历史运动记录
            </h3>
            <span class="text-xs text-morandi-lightText">共 {{ workoutRecords.length }} 条 · {{ totalRecordExercises }} 个动作</span>
          </div>
          <div v-if="workoutRecords.length" class="space-y-2 max-h-[420px] overflow-y-auto pr-1">
            <div v-for="r in workoutRecords" :key="r.id" class="p-3 rounded-xl bg-morandi-soft/30 hover:bg-morandi-soft/50 transition-colors">
              <div class="flex items-center justify-between">
                <div class="flex-1">
                  <button @click="showExerciseStepsByName(r.exerciseName)" class="font-medium text-morandi-text text-sm hover:text-morandi-accent transition-colors">
                    {{ r.exerciseName }}
                  </button>
                  <div class="text-xs text-morandi-lightText mt-0.5">
                    {{ r.date }} · {{ r.sets }}组×{{ r.reps }}次
                    <span v-if="r.weight > 0" class="text-morandi-accent">@{{ r.weight }}kg</span>
                    <span v-else class="text-morandi-lightText">· 自重</span>
                    · {{ r.duration }}分钟 · {{ intensityLabel(r.intensity) }}
                  </div>
                  <div class="text-[11px] text-morandi-lightText mt-0.5">
                    部位：{{ r.category }} · MET {{ getExerciseMet(r.exerciseId) }}
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-sm font-semibold text-orange-500">{{ r.calories }} kcal</span>
                  <button @click="removeRecord(r.id)" class="text-morandi-lightText hover:text-red-500 text-lg leading-none">×</button>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-10 text-morandi-lightText text-sm">
            <Activity class="w-10 h-10 mx-auto mb-2 opacity-30" />
            暂无运动记录
            <div class="mt-3">
              <router-link to="/dashboard/muscle-chart" class="inline-block px-4 py-2 bg-morandi-accent text-white rounded-lg text-sm hover:opacity-90">
                去运动管理记录
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 动作步骤弹窗 -->
    <div v-if="showStepsModal" class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" @click.self="showStepsModal = false">
      <div class="bg-white rounded-2xl max-w-lg w-full shadow-xl max-h-[85vh] overflow-hidden flex flex-col">
        <div class="flex items-center justify-between p-5 border-b border-morandi-soft">
          <div>
            <h3 class="text-lg font-semibold text-morandi-text">{{ currentExercise?.name }}</h3>
            <p class="text-xs text-morandi-lightText mt-0.5">动作步骤说明</p>
          </div>
          <button @click="showStepsModal = false" class="text-morandi-lightText hover:text-morandi-text text-2xl leading-none">×</button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'
import {
  Dumbbell, Activity, Send, Loader2, Zap, Calendar, Clock, Flame, Layers,
  User, History
} from 'lucide-vue-next'
import { EXERCISES, getExerciseById, type ExerciseDetail } from '@/data/exercises'
import { useWorkoutRecords, type WorkoutRecord } from '@/composables/useWorkoutRecords'
import { CROWD_LABELS, MUSCLE_GROUPS } from '@/constants'

const userStore = useUserStore()
const workout = useWorkoutRecords()

const tabs = [
  { key: 'chat' as const, label: 'AI 对话生成' },
  { key: 'records' as const, label: '运动记录' }
]
const activeTab = ref<'chat' | 'records'>('chat')

const userWeight = computed(() => Number(userStore.user?.weight) || 65)
const userCrowdLabel = computed(() => {
  const c = userStore.user?.crowd_type || userStore.user?.crowdType || '普通人'
  const map: Record<string, string> = {
    '普通人': '普通人群', '健身': '健身人群', '老年': '老年人',
    '孕妇': '孕妇', '青少年': '青少年', '糖尿病': '糖尿病患者'
  }
  return map[c] || c
})

// ===== 运动记录（来自共享存储） =====
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

function removeRecord(id: string) {
  workout.remove(id)
}

function intensityLabel(i: string): string {
  return i === 'low' ? '轻松' : i === 'high' ? '高强度' : '中等'
}

function getExerciseMet(id: number): number {
  return getExerciseById(id)?.met || 0
}

// ===== AI 对话 =====
interface ChatMessage {
  role: 'user' | 'ai'
  content: string
}

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
1. 基于用户的实际训练数据（动作、组数、次数、重量、部位分布）进行分析，指出训练中的不足（如部位不平衡、强度不足、过量训练等）
2. 给出具体的、可执行的调整建议，包括：推荐动作（可从卧推、深蹲、硬拉、引体向上、杠铃划船等中选择）、组数、次数、重量建议、训练频率
3. 注意人群适配（如老年人避免大重量、孕妇避免核心压迫、糖尿病患者注意低血糖等）
4. 回答简洁专业，使用要点列出，不要泛泛而谈

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
  } catch (e: any) {
    // 后端不可用时，使用本地规则生成兜底回复
    const fallback = localGenerate(question)
    chatMessages.value.push({ role: 'ai', content: fallback })
  } finally {
    chatLoading.value = false
    await scrollToBottom()
  }
}

function localGenerate(question: string): string {
  const stats = weekStats.value
  const recent = stats.recent
  if (recent.length === 0) {
    return `⚠ 后端 AI 暂时不可用，以下是本地建议：

你近 7 日还没有训练记录。建议从基础动作开始：
• 胸部：卧推 3组×8-12次
• 背部：引体向上/高位下拉 3组×8-12次
• 腿部：深蹲 3组×8-12次
每周训练 3 次，每次 40-60 分钟。

请在「运动管理」记录训练后，再来让我为你制定个性化计划。`
  }

  // 分析部位平衡
  const weakGroups: string[] = []
  const trained = new Set(recent.map(r => r.category))
  MUSCLE_GROUPS.forEach(g => {
    if (!trained.has(g)) weakGroups.push(g)
  })

  let advice = `⚠ 后端 AI 暂时不可用，以下是基于你训练数据的本地分析：\n\n`
  advice += `📊 近 7 日训练概况：\n`
  advice += `• 训练 ${stats.count} 次，共 ${stats.duration} 分钟，消耗 ${stats.calories} kcal\n`
  advice += `• 总组数 ${stats.sets} 组\n`
  advice += `• 训练部位：${stats.byGroup.map(g => `${g.name}(${g.count})`).join('、')}\n\n`

  if (weakGroups.length > 0) {
    advice += `⚠ 训练不足的部位：${weakGroups.join('、')}\n`
    advice += `建议下周增加这些部位的训练。\n\n`
  }

  advice += `💡 调整建议：\n`
  if (/增肌|肌肉|力量/.test(question)) {
    advice += `• 增肌期建议每个部位每周训练 2 次\n`
    advice += `• 复合动作优先：深蹲、硬拉、卧推、引体向上\n`
    advice += `• 重量选择：8-12RM（即每组只能做 8-12 次的重量）\n`
    advice += `• 每组休息 60-90 秒，保证蛋白质摄入 1.6-2.2 g/kg`
  } else if (/减脂|减肥|瘦身/.test(question)) {
    advice += `• 减脂期保持力量训练 + 增加有氧\n`
    advice += `• 力量训练后加 20-30 分钟中等强度有氧\n`
    advice += `• 重量适中，组数可增加，休息时间缩短到 30-60 秒\n`
    advice += `• 热量缺口控制在 300-500 kcal/天`
  } else {
    advice += `• 保持当前训练频率，注意部位均衡\n`
    advice += `• 循序渐进增加重量（每周 +2.5kg）\n`
    advice += `• 保证充足睡眠和蛋白质摄入`
  }

  return advice
}

async function scrollToBottom() {
  await nextTick()
  if (chatBoxRef.value) {
    chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight
  }
}

// ===== 动作步骤弹窗 =====
const showStepsModal = ref(false)
const currentExercise = ref<ExerciseDetail | null>(null)

function showExerciseSteps(id: number) {
  const ex = getExerciseById(id)
  if (ex) {
    currentExercise.value = ex
    showStepsModal.value = true
  }
}

function showExerciseStepsByName(name: string) {
  const ex = EXERCISES.find(e => e.name === name)
  if (ex) {
    currentExercise.value = ex
    showStepsModal.value = true
  }
}

// ===== 初始化 =====
onMounted(() => {
  try { userStore.init() } catch { /* ignore */ }
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.9);
}
.page-fade {
  animation: fadeIn 0.3s ease forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
