<template>
  <div class="cs-page">
    <!-- ===== 顾问台星轨头像带 ===== -->
    <div class="cs-band">
      <div class="star-crumbs">
        <span class="crumb-wrap">
          <button class="crumb-node" @click="goHome"><span class="nd"><LayoutGrid :size="12" /></span>首页</button>
        </span>
        <span class="crumb-wrap">
          <span class="crumb-link"></span>
          <button class="crumb-node" @click="goHub"><span class="nd"><BookOpen :size="12" /></span>知识中心</button>
        </span>
        <span class="crumb-wrap">
          <span class="crumb-link"></span>
          <span class="crumb-node hot"><span class="nd"><MessageCircle :size="13" /></span>AI 咨询</span>
        </span>
      </div>
      <div class="cs-avatar">
        <span class="orb"></span>
        <span class="core"><Sparkles :size="15" /></span>
      </div>
      <div class="tt">
        <b>星语顾问</b>
        <span><i></i>在线 · 已读取你的健康档案</span>
      </div>
      <span class="model">ASTRAL · 诊档引擎</span>
    </div>

    <div class="cs-body">
      <!-- ===== 对话区 ===== -->
      <div class="cs-chat">
        <div ref="msgsRef" class="cs-msgs">
          <div v-if="welcomeBadge" class="welcome-badge">
            <Sparkles :size="12" />
            <span>正在分析{{ welcomeBadge === 'weekly' ? '本周' : '本月' }}健康数据（来自健康星报）</span>
          </div>

          <!-- 空态欢迎 -->
          <div v-if="messages.length === 0 && !loading" class="msg">
            <span class="mavatar"><Sparkles :size="12" /></span>
            <div class="bub">
              你好，星语顾问已就位。我可以基于你的<b>个人档案、今日指标与饮食记录</b>做饮食健康分析——点击右侧「星问」快速提问，或直接输入你的问题。
            </div>
          </div>

          <div
            v-for="(m, idx) in messages"
            :key="idx"
            class="msg"
            :class="{ user: m.role === 'user', 'agent-card': !!m.agent }"
          >
            <span class="mavatar"><component :is="m.role === 'user' ? User : Sparkles" :size="12" /></span>
            <!-- 打字星点 -->
            <div v-if="isTyping(m, idx)" class="bub bub-typing">
              <span class="tdots"><i></i><i></i><i></i></span>
            </div>
            <div v-else class="bub">
              <div v-if="m.role === 'ai' && m.recordId" class="rec-chip">记录 ID #{{ m.recordId }}</div>
              <!-- 仪轨结果卡 -->
              <div v-if="m.agent" class="agent-frame">
                <div class="ar-h"><component :is="agentIcon(m.agent)" :size="13" />{{ agentTitle(m.agent) }}</div>
                <div class="ar-b markdown-body" v-html="renderMd(stripAgentHeader(m.content))"></div>
              </div>
              <template v-else>
                <div v-if="m.role === 'user'" class="whitespace-pre-wrap">{{ m.content }}</div>
                <div v-else class="markdown-body" v-html="renderMd(m.content)"></div>
              </template>
            </div>
          </div>
        </div>

        <form class="cs-input" @submit.prevent="handleSend">
          <div class="fld">
            <PenLine :size="14" />
            <input
              v-model="input"
              placeholder="向星语顾问提问…（例：我今天吃了炸鸡，要注意什么？）"
              required
              :disabled="loading"
            />
          </div>
          <button type="submit" class="cs-send" :disabled="loading">
            <Send :size="14" />{{ loading ? '星算中…' : '发送' }}
          </button>
        </form>
      </div>

      <!-- ===== 右栏星轨 ===== -->
      <aside class="cs-rail">
        <div class="rail-h"><Orbit :size="11" />星问 · 快捷提问</div>
        <button
          v-for="(q, idx) in quickQuestions"
          :key="idx"
          class="qstar"
          :disabled="loading"
          @click="ask(q)"
        >
          <span class="qn">✦</span>{{ q }}
        </button>

        <div class="rail-h mt"><Orbit :size="11" />AI 仪轨</div>
        <div class="ag-grid">
          <button
            v-for="a in agents"
            :key="a.key"
            class="ag"
            :disabled="!!agentLoading"
            @click="runAgent(a.key)"
          >
            <component :is="a.icon" :size="15" />
            <span class="ag-lb">{{ a.label }}</span>
            <Loader2 v-if="agentLoading === a.key" class="ag-spin" :size="12" />
          </button>
        </div>

        <div class="rail-h mt"><Gauge :size="11" />今日星盘快照</div>
        <div class="snap">
          <template v-if="lastSnapshot">
            <div class="srow"><Calendar :size="12" />日期<b>{{ lastSnapshot.date }}</b></div>
            <div class="srow"><User :size="12" />档案<b>{{ lastSnapshot.profile?.username }} · {{ lastSnapshot.profile?.gender }} · {{ lastSnapshot.profile?.age }}岁</b></div>
            <div class="srow"><Ruler :size="12" />体征<b>{{ lastSnapshot.profile?.height_cm }} cm · {{ lastSnapshot.profile?.weight_kg }} kg</b></div>
            <div class="srow"><Scale :size="12" />BMI<b>{{ lastSnapshot.profile?.bmi }}</b></div>
            <div class="sdiv"></div>
            <div class="srow">
              <UtensilsCrossed :size="12" />今日饮食
              <b v-if="lastSnapshot.today_diet_total?.total_food_items > 0">
                {{ lastSnapshot.today_diet_total.total_food_items }} 种食材<template v-if="lastSnapshot.today_diet_total.total_meals > 0"> · {{ lastSnapshot.today_diet_total.total_meals }} 餐</template>
              </b>
              <b v-else>暂无记录</b>
            </div>
            <div v-if="lastSnapshot.today_diet_total?.total_calories_kcal != null" class="srow">
              <Calculator :size="12" />今日热量<b>{{ lastSnapshot.today_diet_total.total_calories_kcal }} kcal</b>
            </div>
            <template v-if="lastSnapshot.today_diet && lastSnapshot.today_diet.length > 0">
              <div class="sdiv"></div>
              <div v-for="(meal, idx) in lastSnapshot.today_diet" :key="'m' + idx" class="meal">
                <div class="meal-h"><b>{{ meal.meal_type }}</b><span>{{ meal.food_items_count }} 项 · {{ meal.meal_calories_kcal }} kcal</span></div>
                <p>
                  <span v-for="(f, fi) in meal.foods" :key="fi">{{ f.food_name }}{{ Number(fi) < (meal.foods as any[]).length - 1 ? '、' : '' }}</span>
                </p>
              </div>
            </template>
          </template>
          <div v-else class="snap-empty">提问后将显示你的健康数据快照</div>
        </div>

        <div class="rail-note">
          AI 建议仅供参考，如涉及用药、严重健康问题，请及时咨询专业医生。每次对话记录会存入数据库，方便日后回顾。
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'
import {
  BarChart3, ListChecks, TrendingUp, Activity, Loader2, Send, PenLine, Orbit, Gauge,
  Calendar, User, Ruler, Scale, UtensilsCrossed, Calculator, Sparkles,
  LayoutGrid, BookOpen, MessageCircle
} from 'lucide-vue-next'
import { marked } from 'marked'
import type { Component } from 'vue'

const router = useRouter()

// 星轨面包屑：首页 / 知识中心中转站
function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'knowledge' } }) }

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
const messages = ref<Array<{ role: 'user' | 'ai'; content: string; recordId?: number; agent?: string }>>([])
const lastSnapshot = ref<any>(null)
const msgsRef = ref<HTMLElement | null>(null)

/* 消息自动滚到底部（流式增量也跟随） */
watch(messages, () => {
  nextTick(() => {
    const el = msgsRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}, { deep: true })

/* 打字星点：最后一条 ai 消息尚无实质内容时显示 */
function isTyping(m: { role: string; content: string }, idx: number): boolean {
  return loading.value && m.role === 'ai' &&
    idx === messages.value.length - 1 &&
    (m.content === '' || m.content === '正在思考...')
}

/* ===== AI 仪轨配置 ===== */
const agents: Array<{ key: string; label: string; icon: Component }> = [
  { key: 'nutrition', label: '营养分析', icon: BarChart3 },
  { key: 'dietPlan', label: '膳食计划', icon: ListChecks },
  { key: 'weeklyReport', label: '周报生成', icon: TrendingUp },
  { key: 'exercise', label: '运动建议', icon: Activity }
]

const AGENT_META: Record<string, { title: string; icon: Component }> = {
  nutrition: { title: '营养分析 · 今日', icon: BarChart3 },
  dietPlan: { title: '膳食计划', icon: ListChecks },
  weeklyReport: { title: '健康周报', icon: TrendingUp },
  exercise: { title: '运动建议', icon: Activity }
}

function agentTitle(key: string): string {
  return AGENT_META[key]?.title || 'AI 仪轨结果'
}
function agentIcon(key: string): Component {
  return AGENT_META[key]?.icon || Sparkles
}
/* 仪轨卡头部已展示标题，正文中去掉首行的「[图表] **xxx**」标记 */
function stripAgentHeader(text: string): string {
  return String(text || '').replace(/^\[[^\]]*\]\s*\*\*[^*]+\*\*\s*\n?/, '')
}

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
        messages.value.push({ role: 'user', content: '给我分析一下今天的营养摄入' })
        result = await api.ai.nutritionAnalyze()
        break
      case 'dietPlan':
        messages.value.push({ role: 'user', content: '帮我制定一份膳食计划' })
        result = await api.ai.dietPlan('均衡饮食')
        break
      case 'weeklyReport':
        messages.value.push({ role: 'user', content: '生成本周健康周报' })
        result = await api.ai.weeklyReport()
        break
      case 'exercise':
        messages.value.push({ role: 'user', content: '给我一份运动建议' })
        result = await api.ai.exerciseAdvice()
        break
      default:
        return
    }
    const reply = formatAgentResult(type, result)
    messages.value.push({ role: 'ai', content: reply, agent: type })
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
        s += '\n建议：\n'
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
          s += `· ${item.meal_type || ''}：${item.description || ''}\n`
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
          s += `· ${item.exercise || item.name || ''}：${item.description || item.duration || ''}\n`
        })
      }
      if (typeof data.plan === 'string') s += data.plan
      if (data.recommendations && data.recommendations.length > 0) {
        s += '\n建议：\n'
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
/* ================= P9-C 星语顾问台 ================= */
.cs-page {
  font-family: 'Noto Sans SC', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background:
    radial-gradient(ellipse at 12% 0%, rgba(217, 162, 74, .13), transparent 40%),
    linear-gradient(168deg, #1C1710, #12100A 60%);
  border-radius: 18px;
  color: #F0E2C4;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 620px;
}
.cs-page button { font-family: inherit; cursor: pointer; }

@keyframes csRise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: none; }
}

/* ===== 星轨头像带 ===== */
.cs-band {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 22px;
  border-bottom: 1px solid rgba(217, 162, 74, .2);
  animation: csRise .6s ease backwards;
}
/* ---- 星轨面包屑导航 ---- */
.star-crumbs { display: flex; align-items: center; flex-shrink: 0; margin-right: 6px; }
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
.cs-avatar { position: relative; width: 40px; height: 40px; flex-shrink: 0; }
.cs-avatar .core {
  position: absolute; inset: 6px; border-radius: 50%;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(232, 185, 115, .6);
  display: flex; align-items: center; justify-content: center;
  color: #E8B973;
  box-shadow: 0 0 18px rgba(217, 162, 74, .4);
  animation: csBreath 3.2s ease-in-out infinite;
}
@keyframes csBreath { 50% { box-shadow: 0 0 26px rgba(217, 162, 74, .62); } }
.cs-avatar .orb {
  position: absolute; inset: -3px; border-radius: 50%;
  border: 1px dashed rgba(217, 162, 74, .35);
  animation: csSpin 14s linear infinite;
}
.cs-avatar .orb::after {
  content: ''; position: absolute; top: -3px; left: 50%;
  width: 5px; height: 5px; border-radius: 50%;
  background: #E8B973; box-shadow: 0 0 8px rgba(232, 185, 115, .9);
}
@keyframes csSpin { to { transform: rotate(360deg); } }
.cs-band .tt b {
  display: block; font-size: 14.5px; font-weight: 900;
  letter-spacing: .1em; color: #F6EAD6;
  font-family: 'Noto Serif SC', serif;
}
.cs-band .tt span {
  display: flex; align-items: center; gap: 5px;
  font-size: 10px; color: #9A8A6C; margin-top: 2px;
}
.cs-band .tt span i {
  width: 6px; height: 6px; border-radius: 50%;
  background: #8FBF7F; box-shadow: 0 0 8px rgba(143, 191, 127, .8);
  animation: csBlink 2.4s ease-in-out infinite;
}
@keyframes csBlink { 50% { opacity: .35; } }
.cs-band .model {
  margin-left: auto; font-size: 10px; letter-spacing: .14em; color: #B9A78A;
  border: 1px solid rgba(217, 162, 74, .3); border-radius: 99px;
  padding: 4px 12px; background: rgba(217, 162, 74, .07);
}

/* ===== 主体两栏 ===== */
.cs-body {
  flex: 1; display: grid; grid-template-columns: 1fr 288px; min-height: 0;
  animation: csRise .7s ease .1s backwards;
}
.cs-chat { display: flex; flex-direction: column; min-width: 0; }
.cs-msgs {
  flex: 1; overflow-y: auto; min-height: 380px; max-height: 560px;
  padding: 20px 24px; display: flex; flex-direction: column; gap: 16px;
}
.msg { display: flex; gap: 11px; max-width: 86%; }
.msg.user { align-self: flex-end; flex-direction: row-reverse; }
.msg.agent-card { width: 86%; }
.mavatar {
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(232, 185, 115, .5); color: #E8B973;
}
.msg.user .mavatar {
  background: linear-gradient(135deg, #E8B973, #B36B2A);
  color: #14110B; border: none;
}
.bub {
  border: 1px solid rgba(217, 162, 74, .22);
  background: rgba(217, 162, 74, .05);
  border-radius: 4px 14px 14px 14px;
  padding: 11px 14px; font-size: 12.5px; line-height: 1.95; color: #D8C9A8;
  min-width: 0; overflow-wrap: break-word;
}
.msg.user .bub {
  background: linear-gradient(135deg, #E8B973, #C98F4A);
  color: #14110B; border: none; font-weight: 600;
  border-radius: 14px 4px 14px 14px;
}
.bub b { color: #E8B973; }
.msg.user .bub b { color: #14110B; }
.rec-chip {
  display: inline-block; font-size: 9.5px; color: #8C7A5E;
  border: 1px solid rgba(217, 162, 74, .25); border-radius: 99px;
  padding: 1px 8px; margin-bottom: 7px;
}
.bub-typing { display: flex; align-items: center; padding: 14px 16px; }
.tdots { display: inline-flex; gap: 6px; }
.tdots i {
  width: 7px; height: 7px; border-radius: 50%;
  background: #D9A24A; opacity: .4;
  animation: csType 1.1s ease-in-out infinite;
}
.tdots i:nth-child(2) { animation-delay: .18s; }
.tdots i:nth-child(3) { animation-delay: .36s; }
@keyframes csType { 50% { opacity: 1; transform: translateY(-4px); } }

/* 仪轨结果卡 */
.agent-frame {
  border: 1px solid rgba(217, 162, 74, .3); border-radius: 12px;
  overflow: hidden; background: linear-gradient(170deg, #221B10, #16110A);
}
.agent-frame .ar-h {
  display: flex; align-items: center; gap: 8px;
  padding: 9px 13px; border-bottom: 1px dashed rgba(217, 162, 74, .25);
  font-size: 11.5px; font-weight: 700; color: #E8B973; letter-spacing: .06em;
}
.agent-frame .ar-h svg { color: #E8B973; }
.agent-frame .ar-b { padding: 11px 13px; font-size: 11.5px; line-height: 1.9; color: #C9B896; }

/* 输入区 */
.cs-input {
  display: flex; gap: 10px;
  padding: 14px 22px;
  border-top: 1px solid rgba(217, 162, 74, .18);
  background: rgba(10, 8, 5, .3);
}
.cs-input .fld {
  flex: 1; display: flex; align-items: center; gap: 9px;
  border: 1px solid rgba(217, 162, 74, .35); border-radius: 12px;
  padding: 0 14px; background: rgba(24, 19, 12, .8); transition: .25s;
}
.cs-input .fld:focus-within { border-color: #D9A24A; box-shadow: 0 0 0 3px rgba(217, 162, 74, .12); }
.cs-input .fld svg { color: #8C7A5E; flex-shrink: 0; }
.cs-input input {
  flex: 1; background: none; border: none; outline: none;
  color: #F0E2C4; font-size: 12.5px; padding: 12px 0; font-family: inherit;
}
.cs-input input::placeholder { color: #6E6049; }
.cs-send {
  display: inline-flex; align-items: center; gap: 7px;
  border: none; border-radius: 12px; padding: 0 18px;
  font-size: 12.5px; font-weight: 700; letter-spacing: .06em; color: #14110B;
  background: linear-gradient(135deg, #E8B973, #B36B2A);
  transition: .25s; box-shadow: 0 8px 20px -8px rgba(217, 162, 74, .55);
}
.cs-send:hover { filter: brightness(1.1); }
.cs-send:disabled { opacity: .6; cursor: not-allowed; }

/* ===== 右栏星轨 ===== */
.cs-rail {
  border-left: 1px solid rgba(217, 162, 74, .14);
  padding: 16px; background: rgba(10, 8, 5, .35);
  overflow-y: auto; max-height: 640px;
}
.rail-h {
  font-size: 10.5px; letter-spacing: .2em; color: #D9A24A;
  margin: 0 0 10px; display: flex; align-items: center; gap: 6px;
}
.rail-h.mt { margin-top: 18px; }
.qstar {
  width: 100%; display: flex; align-items: center; gap: 9px; text-align: left;
  border: 1px solid rgba(217, 162, 74, .22); background: rgba(217, 162, 74, .05);
  color: #C9B896; font-size: 11.5px; padding: 9px 12px;
  border-radius: 11px; margin-bottom: 8px; transition: .25s; line-height: 1.5;
}
.qstar:hover {
  border-color: rgba(232, 185, 115, .6); background: rgba(217, 162, 74, .11);
  color: #F0E2C4; transform: translateX(3px);
}
.qstar:disabled { opacity: .55; cursor: not-allowed; }
.qstar .qn {
  width: 18px; height: 18px; border-radius: 50%;
  border: 1px solid rgba(217, 162, 74, .45);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; font-size: 9px; color: #E8B973;
}
.ag-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.ag {
  border: 1px solid rgba(217, 162, 74, .22); border-radius: 11px;
  background: rgba(217, 162, 74, .05); padding: 10px 8px;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  color: #C9B896; font-size: 10.5px; transition: .25s; position: relative;
}
.ag:hover {
  border-color: rgba(232, 185, 115, .6); background: rgba(217, 162, 74, .12);
  color: #F0E2C4; transform: translateY(-2px);
}
.ag:disabled { opacity: .6; cursor: not-allowed; }
.ag svg { color: #E8B973; }
.ag .ag-spin { position: absolute; top: 5px; right: 7px; animation: csSpin 1s linear infinite; }

/* 快照 */
.snap {
  border: 1px solid rgba(217, 162, 74, .22); border-radius: 12px;
  padding: 12px; background: rgba(217, 162, 74, .05);
}
.srow {
  display: flex; align-items: center; gap: 9px;
  font-size: 11px; color: #C9B896; padding: 5.5px 0;
}
.srow svg { color: #D9A24A; flex-shrink: 0; }
.srow b { margin-left: auto; color: #F0E2C4; font-weight: 700; text-align: right; }
.sdiv { height: 1px; background: rgba(217, 162, 74, .15); margin: 6px 0; }
.snap .meal { padding: 5px 0 5px 8px; border-left: 2px solid rgba(217, 162, 74, .35); margin-bottom: 4px; }
.snap .meal:last-child { margin-bottom: 0; }
.snap .meal-h { display: flex; align-items: baseline; gap: 8px; font-size: 10.5px; }
.snap .meal-h b { color: #E8B973; font-weight: 700; }
.snap .meal-h span { color: #8C7A5E; font-size: 9.5px; margin-left: auto; }
.snap .meal p { font-size: 10px; color: #A89572; line-height: 1.7; margin: 2px 0 0; }
.snap-empty { font-size: 11px; color: #8C7A5E; text-align: center; padding: 14px 0; }
.rail-note {
  margin-top: 14px; padding: 10px 11px; border-radius: 10px;
  border: 1px dashed rgba(217, 162, 74, .3);
  font-size: 10px; line-height: 1.8; color: #9A8A6C;
}

/* 报告徽章 */
.welcome-badge {
  display: inline-flex; align-self: flex-start; align-items: center; gap: 6px;
  padding: 6px 12px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(217, 162, 74, .16), rgba(217, 162, 74, .06));
  border: 1px solid rgba(217, 162, 74, .35);
  color: #E8B973;
  font-size: 11px; font-weight: 600;
  animation: csRise .4s cubic-bezier(.22, 1, .36, 1);
}

/* ===== Markdown 暗金主题 ===== */
.markdown-body {
  font-size: 12.5px; line-height: 1.9; color: #D8C9A8;
  word-break: break-word;
}
.markdown-body > *:first-child { margin-top: 0; }
.markdown-body > *:last-child { margin-bottom: 0; }
.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 {
  font-weight: 700; margin: 14px 0 8px; line-height: 1.3;
  color: #E8B973; font-family: 'Noto Serif SC', serif;
}
.markdown-body h1 { font-size: 17px; }
.markdown-body h2 { font-size: 15px; border-bottom: 1px solid rgba(217, 162, 74, .2); padding-bottom: 4px; }
.markdown-body h3 { font-size: 14px; }
.markdown-body h4 { font-size: 13px; }
.markdown-body p { margin: 6px 0; }
.markdown-body ul, .markdown-body ol { padding-left: 20px; margin: 6px 0; }
.markdown-body ul li { list-style: disc; }
.markdown-body ol li { list-style: decimal; }
.markdown-body li { margin: 2px 0; }
.markdown-body strong { font-weight: 700; color: #E8B973; }
.markdown-body em { font-style: italic; opacity: .92; }
.markdown-body table {
  width: 100%; border-collapse: collapse; margin: 10px 0;
  font-size: 11.5px; display: block; overflow-x: auto;
}
.markdown-body table th, .markdown-body table td {
  border: 1px solid rgba(217, 162, 74, .25);
  padding: 6px 8px; text-align: left; vertical-align: top;
}
.markdown-body table th {
  background: rgba(217, 162, 74, .1); font-weight: 700;
  color: #E8B973; white-space: nowrap;
}
.markdown-body table tr:nth-child(even) td { background: rgba(217, 162, 74, .04); }
.markdown-body blockquote {
  border-left: 3px solid #D9A24A; padding: 4px 10px; margin: 8px 0;
  background: rgba(217, 162, 74, .07); color: #C9B896; font-size: 12px;
}
.markdown-body code {
  background: rgba(217, 162, 74, .12); padding: 1px 4px; border-radius: 4px;
  font-size: 11px; font-family: Menlo, Consolas, monospace; color: #E8B973;
}
.markdown-body hr { border: none; border-top: 1px dashed rgba(217, 162, 74, .3); margin: 10px 0; }
.markdown-body a { color: #E8B973; }

/* ===== 响应式 ===== */
@media (max-width: 1020px) {
  .cs-body { grid-template-columns: 1fr; }
  .cs-rail {
    border-left: none; border-top: 1px solid rgba(217, 162, 74, .14);
    max-height: none;
  }
  .msg, .msg.agent-card { max-width: 96%; }
  .star-crumbs { display: none; }
}
</style>
