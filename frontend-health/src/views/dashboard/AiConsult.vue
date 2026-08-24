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
             你好！我是健康助手，可以帮你分析饮食、运动和生活习惯。有什么想问的就尽管告诉我吧！
          </div>
          <div v-if="welcomeBadge" class="welcome-badge">
            <component :is="Sparkles" class="w-3.5 h-3.5" />
            <span>正在分析{{ welcomeBadge === 'weekly' ? '本周' : '本月' }}健康数据（来自健康报告）</span>
          </div>
          <div v-for="(m, idx) in messages" :key="idx" class="flex" :class="{ 'justify-end': m.role === 'user' }">
            <div :class="['max-w-[80%] px-4 py-3 rounded-xl text-sm leading-relaxed', m.role === 'user' ? 'bg-morandi-accent text-white' : 'bg-white/70 text-morandi-text']">
              <div v-if="m.role === 'ai' && m.recordId" class="text-xs opacity-60 mb-2">记录 ID: #{{ m.recordId }}</div>
              <div v-if="m.role === 'user'" class="whitespace-pre-wrap">{{ m.content }}</div>
              <div v-else class="markdown-body" v-html="renderMd(m.content)"></div>
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
            <button @click="runAgent('exercise')" :disabled="!!agentLoading" class="w-full flex items-center gap-2 px-4 py-2 rounded-xl bg-white/70 text-morandi-text text-sm hover:bg-morandi-accent/10 transition-colors disabled:opacity-60">
              <component :is="Activity" class="w-5 h-5 text-morandi-accent" />
              <span>运动建议</span>
              <component v-if="agentLoading === 'exercise'" :is="Loader2" class="ml-auto w-4 h-4 text-morandi-lightText animate-spin" />
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
import { ref, onMounted, nextTick, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'
import { BarChart3, ListChecks, TrendingUp, Loader2, Calendar, User, Ruler, Scale, UtensilsCrossed, Calculator, Activity, Sparkles } from 'lucide-vue-next'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

/* 安全消毒：marked v18 默认把输入中的原始 HTML 原样透传，AI 输出（或回放的对话记录）可能被
 * 提示词注入成 <img onerror>/<script> 等，导致存储型 XSS。这里用 DOMParser 构建 DOM 后剔除
 * 危险标签与 on* 事件属性、javascript:/data: 伪协议，再序列化。
 */
function sanitizeHtml(html: string): string {
  if (!html) return ''
  if (typeof DOMParser === 'undefined') return String(html).replace(/</g, '&lt;')
  const doc = new DOMParser().parseFromString(html, 'text/html')
  const dangerous = ['script', 'iframe', 'object', 'embed', 'link', 'base', 'meta', 'form', 'input']
  dangerous.forEach((tag) => doc.querySelectorAll(tag).forEach((el) => el.remove()))
  doc.querySelectorAll('*').forEach((el) => {
    Array.from(el.attributes).forEach((attr) => {
      const name = attr.name.toLowerCase()
      const value = attr.value.trim().toLowerCase()
      if (name.startsWith('on')) {
        el.removeAttribute(attr.name)
      } else if ((name === 'href' || name === 'src' || name === 'xlink:href') &&
                 (value.startsWith('javascript:') || value.startsWith('vbscript:') || value.startsWith('data:text/html'))) {
        el.removeAttribute(attr.name)
      }
    })
  })
  return doc.body.innerHTML
}

function renderMd(text: string): string {
  if (!text) return ''
  // 流式渲染时，如果最后一个字符是换行，marked 会把它吃掉，追加 0 宽空格让视觉连贯
  const t = text + (text.endsWith('\n') ? '\u200b' : '')
  try {
    return sanitizeHtml(String(marked.parse(t)))
  } catch {
    return String(text).replace(/</g, '&lt;')
  }
}

const userStore = useUserStore()
const input = ref('')
const loading = ref(false)
const welcomeBadge = ref<string | null>(null)
const agentLoading = ref<string | false>(false)
const messages = ref<Array<{ role: 'user' | 'ai'; content: string; recordId?: number }>>([])
const lastSnapshot = ref<any>(null)

/* 报告页带来的徽章：AI 回复完成后自动清除 */
watch(loading, (v) => {
  if (!v && welcomeBadge.value && messages.value.length >= 2) {
    welcomeBadge.value = null
  }
})

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

/* 双层发送：
 * - displayText: 用户气泡里看到的简洁问题
 * - actualQuestion: 真正发给 AI 的完整 prompt（含数据/知识库）
 * - report_context: （可选）来自健康报告的结构化数据；后端走 report 专属云端模板，不再双层包装 qa
 * 普通调用只传 displayText，实际发送内容 = displayText。
 * 报告页带过来的上下文会传 { displayText, actualQuestion, report_context, high_performance } 四个值。
 */
const pendingReportContext = ref<any>(null)
const pendingHighPerformance = ref<boolean | null>(null)
const handleSend = async (override?: { displayText?: string; actualQuestion?: string; report_context?: any; high_performance?: boolean } | Event) => {
  if (loading.value) return
  // 表单 @submit.prevent="handleSend" 会把 SubmitEvent 当第一个参数传入，这里判空忽略
  const o = (override && typeof override === 'object' && ('displayText' in override || 'actualQuestion' in override || 'report_context' in override))
    ? (override as { displayText?: string; actualQuestion?: string; report_context?: any; high_performance?: boolean })
    : undefined
  const displayText = (o?.displayText ?? input.value).trim()
  if (!displayText) return
  const actualQuestion = (o?.actualQuestion ?? displayText).trim()
  const reportCtx = o?.report_context ?? pendingReportContext.value
  const highPerf = o?.high_performance ?? pendingHighPerformance.value ?? userStore.highPerformance
  // 本次用完清空，避免后续普通咨询继续带 report_ctx
  pendingReportContext.value = null
  pendingHighPerformance.value = null
  if (!o) input.value = ''
  messages.value.push({ role: 'user', content: displayText })
  loading.value = true
  // 预置 AI 消息气泡，流式逐字更新
  messages.value.push({ role: 'ai', content: '' })
  const aiIdx = messages.value.length - 1
  try {
    await new Promise<void>((resolve, reject) => {
      const opts: { high_performance?: boolean; report_context?: any } = { high_performance: highPerf }
      if (reportCtx != null) opts.report_context = reportCtx
      api.ai.consultStream(actualQuestion, {
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
      }, opts)
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
      case 'exercise':
        messages.value.push({ role: 'user', content: '[运动] 给我一份运动建议' })
        result = await api.ai.exerciseAdvice()
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
    case 'exercise': {
      let s = '[运动] **运动建议**\n\n'
      if (data.summary) s += `${data.summary}\n\n`
      if (data.plan && Array.isArray(data.plan)) {
        data.plan.forEach((item: any) => {
          s += `[项目] ${item.exercise || item.name || ''}：${item.description || item.duration || ''}\n`
        })
      }
      if (typeof data.plan === 'string') s += data.plan
      if (data.recommendations && data.recommendations.length > 0) {
        s += '\n[提示] 建议：\n'
        data.recommendations.forEach((r: string) => { s += `• ${r}\n` })
      }
      return s
    }
    default:
      return JSON.stringify(data, null, 2)
  }
}

onMounted(async () => {
  userStore.init()
  /* 读取来自周报/月报的待分析上下文，自动作为首条对话流式输出。
   * 采用"双层对话"：
   * - displayText: 展示在用户气泡里的简洁一句话（用户可见）
   * - actualQuestion: 真正发送给后端的消息（简短用户话语即可）
   * - report_context: 结构化报告数据 + 一丢丢知识库，后端直接走 report 云端模板
   */
  const KEY = 'AI_CONSULT_PENDING_PROMPT'
  const raw = sessionStorage.getItem(KEY)
  if (raw) {
    sessionStorage.removeItem(KEY)
    try {
      const ctx = JSON.parse(raw)
      if (ctx && (ctx.prompt || ctx.report_context)) {
        const periodLabel = ctx.period === 'monthly' ? '本月' : '本周'
        const displayText = ctx.displayText || `请帮我分析一下${periodLabel}的健康数据`
        welcomeBadge.value = ctx.period || 'weekly'
        // 如果带了 report_context，就直接用 report 专属路径（高性能云端直连）
        if (ctx.report_context) {
          pendingReportContext.value = ctx.report_context
          pendingHighPerformance.value = ctx.high_performance ?? userStore.highPerformance
          await nextTick()
          handleSend({
            displayText,
            actualQuestion: ctx.actualQuestion || displayText,
            report_context: ctx.report_context,
            high_performance: ctx.high_performance ?? userStore.highPerformance,
          })
        } else {
          // 兼容旧版：完整 prompt 走 qa 路径
          await nextTick()
          handleSend({ displayText, actualQuestion: ctx.prompt })
        }
      }
    } catch {
      /* 格式异常则忽略，不影响普通咨询 */
    }
  }
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.9);
}
.welcome-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; margin-bottom: 12px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(47,93,74,.1), rgba(224,122,63,.08));
  border: 1px solid rgba(47,93,74,.22);
  color: #2F5D4A;
  font-size: 12px; font-weight: 600;
  animation: badgeIn .4s cubic-bezier(.22,1,.36,1);
}
.welcome-badge svg { color: #E07A3F; }
@keyframes badgeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
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

/* Markdown 渲染样式（报告分析结构化输出） */
.markdown-body {
  font-size: 13.5px;
  line-height: 1.7;
  color: inherit;
  word-break: break-word;
}
.markdown-body > *:first-child { margin-top: 0; }
.markdown-body > *:last-child { margin-bottom: 0; }
.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 {
  font-weight: 700;
  margin: 14px 0 8px;
  line-height: 1.3;
  color: #2F5D4A;
}
.markdown-body h1 { font-size: 18px; }
.markdown-body h2 { font-size: 16px; border-bottom: 1px solid rgba(47,93,74,.15); padding-bottom: 4px; }
.markdown-body h3 { font-size: 14.5px; }
.markdown-body h4 { font-size: 13.5px; }
.markdown-body p { margin: 6px 0; }
.markdown-body ul, .markdown-body ol { padding-left: 20px; margin: 6px 0; }
.markdown-body ul li { list-style: disc; }
.markdown-body ol li { list-style: decimal; }
.markdown-body li { margin: 2px 0; }
.markdown-body strong { font-weight: 700; color: #1F4636; }
.markdown-body em { font-style: italic; opacity: 0.92; }
.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0;
  font-size: 12.5px;
  display: block;
  overflow-x: auto;
}
.markdown-body table th, .markdown-body table td {
  border: 1px solid rgba(47,93,74,.2);
  padding: 6px 8px;
  text-align: left;
  vertical-align: top;
}
.markdown-body table th {
  background: rgba(47,93,74,.08);
  font-weight: 700;
  color: #2F5D4A;
  white-space: nowrap;
}
.markdown-body table tr:nth-child(even) td {
  background: rgba(47,93,74,.03);
}
.markdown-body blockquote {
  border-left: 3px solid #E07A3F;
  padding: 4px 10px;
  margin: 8px 0;
  background: rgba(224,122,63,.05);
  color: #6F4720;
  font-size: 12.5px;
}
.markdown-body code {
  background: rgba(47,93,74,.08);
  padding: 1px 4px;
  border-radius: 4px;
  font-size: 12px;
  font-family: Menlo, Consolas, monospace;
  color: #1F4636;
}
.markdown-body hr {
  border: none;
  border-top: 1px dashed rgba(47,93,74,.25);
  margin: 10px 0;
}
</style>
