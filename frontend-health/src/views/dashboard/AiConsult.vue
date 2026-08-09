<template>
  <div class="page-fade">
    <h2 class="text-2xl font-bold mb-2 text-morandi-text">AI 健康咨询</h2>
    <p class="text-morandi-lightText mb-6 text-sm">
      基于您的个人资料、今日身体指标和饮食记录，专注饮食健康咨询
    </p>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="glass rounded-2xl p-6 lg:col-span-2 flex flex-col" style="min-height: 480px">
        <div class="flex-1 overflow-y-auto mb-4 space-y-4" style="max-height: 440px">
          <div v-if="messages.length === 0" class="text-morandi-lightText text-sm text-center py-16">
            👋 你好！我是健康助手，可以帮你分析饮食、运动和生活习惯。有什么想问的就尽管告诉我吧！
          </div>
          <div v-for="(m, idx) in messages" :key="idx" class="flex" :class="{ 'justify-end': m.role === 'user' }">
            <div :class="['max-w-[80%] px-4 py-3 rounded-xl text-sm leading-relaxed', m.role === 'user' ? 'bg-morandi-accent text-white' : 'bg-white/70 text-morandi-text']">
              <div v-if="m.role === 'ai' && m.recordId" class="text-xs opacity-60 mb-2">记录 ID: #{{ m.recordId }}</div>
              <div class="whitespace-pre-wrap">{{ m.content }}</div>
            </div>
          </div>
        </div>
        <form @submit.prevent="handleSend" class="flex gap-3">
          <input v-model="input" class="flex-1 px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft text-sm" placeholder="输入你的问题...（例：我今天吃了炸鸡，要注意什么？）" required :disabled="loading" />
          <button :disabled="loading" class="px-5 py-3 rounded-xl bg-morandi-accent text-white text-sm hover:opacity-90 transition-opacity disabled:opacity-60">
            {{ loading ? '发送中...' : '发送' }}
          </button>
        </form>
      </div>

      <div class="space-y-4">
        <div class="glass rounded-2xl p-5">
          <h3 class="font-semibold mb-3">快捷问题</h3>
          <div class="space-y-2">
            <button v-for="(q, idx) in quickQuestions" :key="idx" @click="ask(q)" :disabled="loading" class="w-full text-left px-4 py-2 rounded-xl bg-white/70 text-morandi-text text-sm hover:bg-morandi-soft transition-colors disabled:opacity-60">
              {{ q }}
            </button>
          </div>
        </div>

        <div class="glass rounded-2xl p-5">
          <h3 class="font-semibold mb-3">AI 智能功能</h3>
          <div class="space-y-2">
            <button @click="runAgent('nutrition')" :disabled="!!agentLoading" class="w-full flex items-center gap-2 px-4 py-2 rounded-xl bg-white/70 text-morandi-text text-sm hover:bg-morandi-accent/10 transition-colors disabled:opacity-60">
              <component :is="BarChart3" class="w-5 h-5 text-morandi-accent" />
              <span>营养分析</span>
              <component v-if="agentLoading === 'nutrition'" :is="Loader2" class="ml-auto w-4 h-4 text-morandi-lightText animate-spin" />
            </button>
            <button @click="runAgent('dietPlan')" :disabled="!!agentLoading" class="w-full flex items-center gap-2 px-4 py-2 rounded-xl bg-white/70 text-morandi-text text-sm hover:bg-morandi-accent/10 transition-colors disabled:opacity-60">
              <component :is="ListChecks" class="w-5 h-5 text-morandi-accent" />
              <span>膳食计划</span>
              <component v-if="agentLoading === 'dietPlan'" :is="Loader2" class="ml-auto w-4 h-4 text-morandi-lightText animate-spin" />
            </button>
            <button @click="runAgent('weeklyReport')" :disabled="!!agentLoading" class="w-full flex items-center gap-2 px-4 py-2 rounded-xl bg-white/70 text-morandi-text text-sm hover:bg-morandi-accent/10 transition-colors disabled:opacity-60">
              <component :is="TrendingUp" class="w-5 h-5 text-morandi-accent" />
              <span>周报生成</span>
              <component v-if="agentLoading === 'weeklyReport'" :is="Loader2" class="ml-auto w-4 h-4 text-morandi-lightText animate-spin" />
            </button>
          </div>
        </div>

        <div class="glass rounded-2xl p-5">
          <h3 class="font-semibold mb-3">今日数据快照</h3>
          <div v-if="lastSnapshot" class="text-xs text-morandi-text space-y-2 leading-relaxed">
            <div class="flex items-center gap-1"><component :is="Calendar" class="w-3 h-3 text-morandi-accent" />日期：{{ lastSnapshot.date }}</div>
            <div class="flex items-center gap-1"><component :is="User" class="w-3 h-3 text-morandi-accent" />{{ lastSnapshot.profile?.username }} · {{ lastSnapshot.profile?.gender }} · {{ lastSnapshot.profile?.age }}岁</div>
            <div class="flex items-center gap-1"><component :is="Ruler" class="w-3 h-3 text-morandi-accent" />身高 {{ lastSnapshot.profile?.height_cm }} cm · 体重 {{ lastSnapshot.profile?.weight_kg }} kg</div>
            <div class="flex items-center gap-1"><component :is="Scale" class="w-3 h-3 text-morandi-accent" />BMI：{{ lastSnapshot.profile?.bmi }}</div>
            <div>
              <component :is="UtensilsCrossed" class="w-3 h-3 text-morandi-accent inline mr-1" />今日饮食：
              <span v-if="lastSnapshot.today_diet_total?.total_food_items > 0">
                共 {{ lastSnapshot.today_diet_total.total_food_items }} 种食材
                <span v-if="lastSnapshot.today_diet_total.total_meals > 0">（{{ lastSnapshot.today_diet_total.total_meals }} 餐）</span>
              </span>
              <span v-else>暂无记录</span>
            </div>
            <div v-if="lastSnapshot.today_diet_total?.total_calories_kcal != null">
              <component :is="Calculator" class="w-3 h-3 text-morandi-accent inline mr-1" />今日热量：{{ lastSnapshot.today_diet_total.total_calories_kcal }} kcal
            </div>
            <div v-if="lastSnapshot.today_diet && lastSnapshot.today_diet.length > 0" class="mt-3 pt-3 border-t border-morandi-soft/40">
              <div class="font-medium mb-2">各餐明细：</div>
              <div v-for="(meal, idx) in lastSnapshot.today_diet" :key="idx" class="mb-2 pl-2 border-l-2 border-morandi-accent/40">
                <div class="font-medium">{{ meal.meal_type }} · {{ meal.food_items_count }} 项 · {{ meal.meal_calories_kcal }} kcal</div>
                <div class="text-morandi-lightText pl-2">
                  <span v-for="(f, fi) in meal.foods" :key="fi">
                    {{ f.food_name }}{{(fi as number) < (meal.foods.length - 1) ? '、' : '' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-xs text-morandi-lightText">
            提问后将显示您的健康数据快照
          </div>
        </div>
        <div class="glass rounded-2xl p-5">
          <h3 class="font-semibold mb-3">温馨提示</h3>
          <p class="text-morandi-lightText text-xs leading-relaxed">AI 建议仅供参考，如涉及用药、严重健康问题，请及时咨询专业医生。每次对话记录会存入数据库，方便日后回顾。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'
import { BarChart3, ListChecks, TrendingUp, Loader2, Calendar, User, Ruler, Scale, UtensilsCrossed, Calculator } from 'lucide-vue-next'

const userStore = useUserStore()
const input = ref('')
const loading = ref(false)
const agentLoading = ref<string | false>(false)
const messages = ref<Array<{ role: 'user' | 'ai'; content: string; recordId?: number }>>([])
const lastSnapshot = ref<any>(null)

const quickQuestions = [
  '根据我的情况，今天吃得怎么样？',
  '我想减肥，可以给我一些饮食建议吗？',
  '我的 BMI 是否正常？需要注意什么？',
  '请分析我今日的营养摄入是否均衡'
]

const ask = (q: string) => {
  input.value = q
  handleSend()
}

const handleSend = async () => {
  if (!input.value.trim() || loading.value) return
  const q = input.value.trim()
  input.value = ''
  messages.value.push({ role: 'user', content: q })
  loading.value = true
  // 预置 AI 消息气泡，流式逐字更新
  messages.value.push({ role: 'ai', content: '' })
  const aiIdx = messages.value.length - 1
  try {
    await new Promise<void>((resolve, reject) => {
      api.ai.consultStream(q, {
        onThinking: () => {
          if (!messages.value[aiIdx].content) {
            messages.value[aiIdx].content = '正在思考...'
          }
        },
        onDelta: (content: string) => {
          const cur = messages.value[aiIdx].content
          messages.value[aiIdx].content = cur === '正在思考...' ? content : cur + content
        },
        onDone: (payload: any) => {
          // done 事件 payload 为 AI 服务完整结果
          const response = payload?.response || payload?.content || ''
          const recordId = payload?.recordId || payload?.conversation_id
          if (response && messages.value[aiIdx].content === '正在思考...') {
            messages.value[aiIdx].content = response
          } else if (response) {
            // 流式增量已推送，若 done 带完整文本则以其为准（更完整）
            messages.value[aiIdx].content = response
          }
          if (recordId) messages.value[aiIdx].recordId = recordId
          const snapshot = payload?.snapshot
          if (snapshot) lastSnapshot.value = snapshot
          resolve()
        },
        onError: (message: string) => {
          messages.value[aiIdx].content = '[错误] ' + message
          resolve()
        }
      })
    })
  } catch (e: any) {
    const msg =
      e?.response?.data?.message ||
      e?.message ||
      '发送失败，请检查网络或稍后再试'
    messages.value[aiIdx].content = '[错误] ' + msg
  } finally {
    loading.value = false
  }
}

const runAgent = async (type: string) => {
  if (agentLoading.value) return
  agentLoading.value = type
  try {
    let result: any
    switch (type) {
      case 'nutrition':
        messages.value.push({ role: 'user', content: '[图表] 给我分析一下今天的营养摄入' })
        result = await api.ai.nutritionAnalyze()
        break
      case 'dietPlan':
        messages.value.push({ role: 'user', content: '[列表] 帮我制定一份膳食计划' })
        result = await api.ai.dietPlan('均衡饮食')
        break
      case 'weeklyReport':
        messages.value.push({ role: 'user', content: '[趋势] 生成本周健康周报' })
        result = await api.ai.weeklyReport()
        break
      default:
        return
    }
    const reply = formatAgentResult(type, result)
    messages.value.push({ role: 'ai', content: reply })
  } catch (e: any) {
    const msg = e?.response?.data?.message || e?.message || '功能暂时不可用，请稍后再试'
    messages.value.push({ role: 'ai', content: '[错误] ' + msg })
  } finally {
    agentLoading.value = false
  }
}

const formatAgentResult = (type: string, data: any): string => {
  if (!data) return '暂无数据返回'
  if (data.error) return '[警告] ' + data.error

  switch (type) {
    case 'nutrition': {
      let s = '[图表] **营养分析结果**\n\n'
      if (data.bmr) s += `基础代谢(BMR)：${data.bmr} kcal\n`
      if (data.bmr_status) s += `BMR状态：${data.bmr_status}\n`
      if (data.total_calories) s += `今日摄入：${data.total_calories} kcal\n`
      if (data.recommendations && data.recommendations.length > 0) {
        s += '\n[提示] 建议：\n'
        data.recommendations.forEach((r: string) => { s += `• ${r}\n` })
      }
      if (data.summary) s += `\n${data.summary}`
      return s
    }
    case 'dietPlan': {
      let s = '[列表] **膳食计划**\n\n'
      if (data.summary) s += `${data.summary}\n\n`
      if (data.plan && Array.isArray(data.plan)) {
        data.plan.forEach((item: any) => {
          s += `[餐食] ${item.meal_type || ''}：${item.description || ''}\n`
        })
      }
      if (typeof data.plan === 'string') s += data.plan
      return s
    }
    case 'weeklyReport': {
      let s = '[趋势] **本周健康周报**\n\n'
      if (data.summary) s += `${data.summary}\n\n`
      if (data.details) s += data.details
      return s
    }
    default:
      return JSON.stringify(data, null, 2)
  }
}

onMounted(() => {
  userStore.init()
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
