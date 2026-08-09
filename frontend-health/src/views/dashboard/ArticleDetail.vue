<template>
  <div v-if="loading" class="py-24 text-center text-morandi-lightText text-sm">加载中...</div>

  <div v-else-if="!article" class="py-24 text-center">
    <p class="text-morandi-lightText">文章不存在</p>
    <button @click="goBack" class="mt-4 text-morandi-accent text-sm hover:underline">返回列表</button>
  </div>

  <div v-else class="min-h-screen bg-morandi-bg/30">
    <div class="mx-auto max-w-[1200px] px-4 py-8 md:py-10">
      <div class="flex gap-8">

        <!-- ============ 主文章区 ============ -->
        <div class="flex-1 min-w-0">

          <!-- 返回 / 操作栏 -->
          <div class="flex items-center justify-between mb-6">
            <button @click="goBack" class="inline-flex items-center gap-1.5 text-sm text-morandi-lightText hover:text-morandi-accent transition">
              <ArrowLeft class="w-4 h-4" />
              返回文章列表
            </button>
            <div class="flex items-center gap-2">
              <button
                @click="toggleLike"
                :class="['p-2 rounded-xl border transition-all duration-200', liked ? 'bg-red-50 text-red-500 border-red-200' : 'border-morandi-soft text-morandi-lightText hover:bg-red-50 hover:border-red-200 hover:text-red-500']"
              >
                <Heart :class="['w-4 h-4', liked ? 'fill-current' : '']" />
              </button>
              <button @click="handleShare" class="p-2 rounded-xl border border-morandi-soft text-morandi-lightText hover:bg-morandi-soft/40 hover:text-morandi-text transition">
                <Share2 class="w-4 h-4" />
              </button>
              <button @click="showReport = !showReport" class="p-2 rounded-xl border border-morandi-soft text-morandi-lightText hover:bg-amber-50 hover:border-amber-200 hover:text-amber-600 transition">
                <Flag class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- 举报面板 -->
          <div v-if="showReport" class="mb-6 bg-amber-50 border border-amber-200 rounded-2xl p-5">
            <div v-if="reportSubmitted" class="flex items-center gap-2 text-morandi-accent text-sm">
              <CheckCircle class="w-4 h-4" />
              已提交，我们会尽快核实，谢谢反馈
            </div>
            <div v-else class="space-y-3">
              <div class="flex items-center gap-2 text-amber-800 font-medium text-sm">
                <AlertTriangle class="w-4 h-4" />
                报告内容有误
              </div>
              <select v-model="reportReason" class="w-full text-sm px-3 py-2 rounded-lg border border-amber-200 bg-white outline-none focus:border-morandi-accent">
                <option value="">请选择问题类型</option>
                <option>数据/数值错误</option>
                <option>参考文献虚假/不准确</option>
                <option>医疗建议不当</option>
                <option>排版混乱</option>
                <option>其他</option>
              </select>
              <textarea v-model="reportDetail" placeholder="详细描述（选填）" rows="3" class="w-full text-sm px-3 py-2 rounded-lg border border-amber-200 bg-white outline-none focus:border-morandi-accent resize-none" />
              <div class="flex justify-end gap-2">
                <button @click="showReport = false" class="px-4 py-1.5 text-xs rounded-lg text-morandi-lightText hover:bg-white/60">取消</button>
                <button @click="submitReport" :disabled="!reportReason" class="px-4 py-1.5 text-xs rounded-lg bg-amber-600 text-white disabled:opacity-50 hover:bg-amber-700">提交</button>
              </div>
            </div>
          </div>

          <!-- ============ 主卡片容器 ============ -->
          <article class="bg-white rounded-3xl border border-morandi-soft/60 shadow-xl shadow-morandi-text/5 overflow-hidden">

            <!-- 头部信息区 -->
            <header class="px-6 md:px-10 pt-8 md:pt-10 pb-6 border-b border-morandi-soft/40">
              <div class="flex flex-wrap items-center gap-2 mb-4">
                <span :class="['inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border', LEN_BADGE[currentLen]]">
                  <component :is="lenIcon(currentLen)" class="w-3 h-3" />
                  {{ LEN_LABEL[currentLen] }}
                </span>
                <span class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-morandi-gray text-morandi-lightText border border-morandi-soft/60">
                  <Tag class="w-3 h-3" />{{ article.category || '综合营养' }}
                </span>
                <span v-if="article.audience" class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-morandi-accent/10 text-morandi-accent border border-morandi-accent/30">
                  <Users class="w-3 h-3" />{{ article.audience }}
                </span>

              </div>

              <h1 class="text-2xl md:text-3xl font-bold text-morandi-text leading-tight tracking-tight">
                {{ displayTitle }}
              </h1>
              <p class="mt-2 text-base text-morandi-lightText leading-relaxed">{{ displaySummary }}</p>

              <div class="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-morandi-lightText">
                <span class="inline-flex items-center gap-1.5"><Calendar class="w-3.5 h-3.5" />{{ formatDate(article.createdAt) }}</span>
                <span class="inline-flex items-center gap-1.5"><FileText class="w-3.5 h-3.5" />{{ displayWordCount }} 字</span>
                <span class="inline-flex items-center gap-1.5"><Eye class="w-3.5 h-3.5" />{{ article.viewsCount?.toLocaleString?.() ?? article.viewsCount }} 阅读</span>
                <span class="inline-flex items-center gap-1.5"><Heart class="w-3.5 h-3.5" />{{ article.likesCount }} 收藏</span>
                <span class="inline-flex items-center gap-1.5"><Sparkles class="w-3.5 h-3.5 text-morandi-accent" />作者：{{ article.authorName || 'AI 健康助手' }}</span>
              </div>
            </header>

            <!-- 正文区 -->
            <div ref="contentRef" class="px-6 md:px-10 py-8 md:py-10">
              <!-- 移动端篇幅切换 -->
              <div class="lg:hidden mb-6">
                <div class="grid grid-cols-3 gap-2 p-1.5 rounded-2xl bg-morandi-gray border border-morandi-soft/60">
                  <button
                    v-for="t in LEN_TABS"
                    :key="t.key"
                    @click="switchLen(t.key)"
                    :class="[
                      'rounded-xl p-3 text-center transition-all duration-200 border-2',
                      currentLen === t.key
                        ? 'bg-white shadow-sm border-morandi-accent/40'
                        : 'bg-transparent border-transparent text-morandi-lightText hover:bg-white/60'
                    ]"
                  >
                    <component :is="t.icon" class="w-4 h-4 mx-auto mb-1" />
                    <div class="text-xs font-medium">{{ t.label }}</div>
                  </button>
                </div>
              </div>

              <!-- 卡片化正文内容 -->
              <div v-if="contentCards.length" class="space-y-4">
                <div
                  v-for="(card, idx) in contentCards"
                  :key="card.id"
                  :id="card.h2Id"
                  class="content-card rounded-2xl border border-morandi-soft/60 overflow-hidden bg-white"
                >
                  <!-- 卡片头部：标题 + 展开/收起 -->
                  <button
                    class="w-full flex items-center justify-between px-5 py-4 hover:bg-morandi-gray/40 transition-colors"
                    @click="toggleCard(card.id, idx)"
                  >
                    <div class="flex items-center gap-3 min-w-0">
                      <span class="w-1 h-5 rounded-full bg-morandi-accent flex-shrink-0"></span>
                      <span class="text-base font-bold text-morandi-text text-left truncate">{{ card.title }}</span>
                    </div>
                    <component
                      :is="card.expanded ? ChevronUp : ChevronDown"
                      class="w-4 h-4 text-morandi-lightText flex-shrink-0 transition-transform duration-300"
                    />
                  </button>
                  <!-- 卡片内容 -->
                  <transition name="card-collapse">
                    <div
                      v-show="card.expanded"
                      class="card-body article-body px-5 py-5 border-t border-morandi-soft/40"
                      v-html="card.html"
                    />
                  </transition>
                </div>
              </div>
              <!-- Fallback for articles without h2 headings -->
              <div v-else class="article-body" v-html="processedContent" />
            </div>

            <!-- ============ 参考文献区 ============ -->
            <footer v-if="sources.length" class="px-6 md:px-10 py-8 bg-gradient-to-br from-morandi-bg/30 to-morandi-bg/10 border-t border-morandi-soft/40">
              <div class="flex items-center gap-2 mb-5">
                <div class="w-8 h-8 rounded-xl bg-morandi-accent/15 flex items-center justify-center">
                  <BookMarked class="w-4 h-4 text-morandi-accent" />
                </div>
                <div>
                  <h3 class="text-base font-bold text-morandi-text">参考文献</h3>
                  <p class="text-xs text-morandi-lightText">共 {{ sources.length }} 篇权威来源 · 点击文中角标可跳转</p>
                </div>
                <button @click="showSources = !showSources" class="ml-auto text-xs text-morandi-lightText hover:text-morandi-accent flex items-center gap-1">
                  {{ showSources ? '收起' : '展开' }}
                  <component :is="showSources ? ChevronUp : ChevronDown" class="w-3.5 h-3.5" />
                </button>
              </div>
              <transition name="expand">
                <div v-show="showSources" class="space-y-3">
                  <div
                    v-for="(s, i) in sources"
                    :key="i"
                    :id="`ref-${i + 1}`"
                    class="flex gap-4 p-4 rounded-xl bg-white border border-morandi-soft/50 hover:border-morandi-accent/30 hover:shadow-sm transition-all cursor-pointer"
                  >
                    <span class="flex-shrink-0 w-7 h-7 rounded-lg bg-morandi-accent/10 text-morandi-accent text-xs font-bold flex items-center justify-center border border-morandi-accent/20">
                      {{ i + 1 }}
                    </span>
                    <p class="text-sm text-morandi-lightText leading-relaxed flex-1">{{ s }}</p>
                  </div>
                </div>
              </transition>
            </footer>
          </article>

          <!-- 跳转提示：查看其他篇幅 -->
          <div class="mt-8 text-center">
            <p class="text-sm text-morandi-lightText mb-4">想深入了解该话题？</p>
            <div class="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                v-for="t in otherTabs"
                :key="t.key"
                @click="switchLen(t.key); scrollToTop()"
                class="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-white border border-morandi-soft hover:border-morandi-accent hover:bg-morandi-accent/5 transition-all duration-200 text-sm text-morandi-text hover:text-morandi-accent group"
              >
                <component :is="t.icon" class="w-4 h-4" />
                查看{{ t.label }}
                <ChevronRight class="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          </div>

          <!-- 免责声明 -->
          <div class="mt-6 p-4 rounded-xl bg-amber-50/50 border border-amber-100 flex gap-3">
            <Info class="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <p class="text-xs text-morandi-lightText leading-relaxed">
              本文为 AI 生成的膳食科普参考，仅用于一般性健康知识普及，不构成任何医疗诊断或治疗建议。涉及疾病、药物、特殊人群等专业问题，请务必咨询医生或注册营养师。
            </p>
          </div>

          <!-- 相关阅读 -->
          <div v-if="relatedArticles.length" class="mt-8">
            <h3 class="text-base font-bold text-morandi-text mb-4 flex items-center gap-2">
              <Sparkles class="w-4 h-4 text-morandi-accent" />
              同主题其它篇幅
            </h3>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <button
                v-for="a in relatedArticles"
                :key="a.id"
                @click="goDetail(a.id)"
                class="text-left p-4 rounded-2xl border border-morandi-soft/60 bg-white hover:border-morandi-accent/40 hover:shadow-md transition group"
              >
                <div class="flex items-center gap-2 mb-2">
                  <span :class="['text-[10px] font-semibold px-2 py-0.5 rounded-full border', LEN_BADGE[a.lengthType as LengthType] || '']">
                    {{ LEN_LABEL[a.lengthType as LengthType] || '文章' }}
                  </span>
                  <span class="ml-auto text-[10px] text-morandi-lightText">{{ a.wordCount }}字</span>
                </div>
                <div class="text-sm font-medium text-morandi-text group-hover:text-morandi-accent transition line-clamp-2">{{ a.title.replace(/【.+】$/, '') }}</div>
                <div class="flex items-center justify-between mt-2 text-[11px] text-morandi-lightText">
                  <span class="inline-flex items-center gap-0.5"><Eye class="w-3 h-3" />{{ a.viewsCount }}</span>
                  <span class="inline-flex items-center gap-0.5 text-morandi-accent opacity-0 group-hover:opacity-100 transition-all">查看<ChevronRight class="w-3 h-3" /></span>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- ============ 右侧跟随栏 ============ -->
        <aside class="hidden lg:block w-60 flex-shrink-0">
          <div class="sticky top-6 space-y-4">

            <!-- 篇幅切换器（竖排） -->
            <div class="bg-white rounded-2xl border border-morandi-soft/60 shadow-sm p-2">
              <div class="text-xs font-semibold text-morandi-lightText uppercase tracking-wider mb-2 px-2 pt-1 flex items-center gap-1.5">
                <Layers class="w-3.5 h-3.5 text-morandi-accent" />
                篇幅切换
              </div>
              <div class="flex flex-col gap-1">
                <button
                  v-for="t in LEN_TABS"
                  :key="t.key"
                  @click="switchLen(t.key)"
                  :class="[
                    'flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all',
                    currentLen === t.key
                      ? 'bg-morandi-accent text-white shadow-sm'
                      : 'text-morandi-lightText hover:bg-morandi-gray hover:text-morandi-text'
                  ]"
                >
                  <component :is="t.icon" class="w-4 h-4 flex-shrink-0" />
                  <span class="flex-1 text-left">{{ t.label }}</span>
                  <span v-if="currentLen === t.key" class="w-1.5 h-1.5 rounded-full bg-white"></span>
                </button>
              </div>
            </div>

            <!-- 跟随式目录 -->
            <div v-if="toc.length" class="bg-white rounded-2xl border border-morandi-soft/60 shadow-sm p-4">
              <div class="text-xs font-semibold text-morandi-lightText uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <List class="w-3.5 h-3.5 text-morandi-accent" />
                文章目录
              </div>
              <nav class="space-y-0.5">
                <button
                  v-for="item in toc"
                  :key="item.id"
                  @click="jumpTo(item.id)"
                  :class="[
                    'w-full text-left transition-all duration-200 rounded-lg flex items-center gap-2 whitespace-nowrap overflow-hidden text-ellipsis',
                    item.level === 2 ? 'pl-7 pr-3 py-1.5 text-[13px]' : 'px-3 py-2 text-sm font-medium',
                    activeId === item.id
                      ? 'bg-morandi-accent/10 text-morandi-accent border-l-2 border-morandi-accent'
                      : 'text-morandi-lightText hover:bg-morandi-gray hover:text-morandi-text border-l-2 border-transparent'
                  ]"
                >
                  <span class="overflow-hidden text-ellipsis">{{ item.text }}</span>
                </button>
              </nav>
            </div>

          </div>
        </aside>

      </div>
    </div>

    <!-- 术语 Tooltip 浮层 -->
    <Teleport to="body">
      <div
        v-if="termTooltip.show"
        class="fixed z-[100] max-w-xs p-4 rounded-xl bg-white shadow-2xl border border-morandi-soft pointer-events-auto"
        :style="{ top: termTooltip.y + 'px', left: termTooltip.x + 'px' }"
        @mouseenter="keepTooltip"
        @mouseleave="hideTooltip"
      >
        <div class="flex items-center gap-2 mb-1.5">
          <span class="w-5 h-5 rounded-md bg-morandi-accent/15 text-morandi-accent flex items-center justify-center">
            <BookA class="w-3 h-3" />
          </span>
          <span class="text-sm font-bold text-morandi-text">{{ termTooltip.term }}</span>
        </div>
        <p class="text-xs text-morandi-lightText leading-relaxed">{{ termTooltip.def }}</p>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, Eye, Heart, Share2, Flag, AlertTriangle, Calendar,
  BookOpen, Zap, FlaskConical, GraduationCap,
  BookMarked, ChevronRight, ChevronUp, ChevronDown, CheckCircle, FileText,
  Sparkles, Star, Tag, Users, Info, List, BookA, Layers
} from 'lucide-vue-next'
import { api } from '@/api'
import {
  fetchArticleDetail, fetchRelatedArticles, parseSources,
  LEN_LABEL,
  type Article, type LengthType
} from '@/api/articleMock'

const route = useRoute()
const router = useRouter()

const article = ref<Article | null>(null)
const loading = ref(false)
const currentLen = ref<LengthType>('medium')
const liked = ref(false)
const showReport = ref(false)
const reportReason = ref('')
const reportDetail = ref('')
const reportSubmitted = ref(false)
const showSources = ref(true)
const contentRef = ref<HTMLElement | null>(null)
const toc = ref<{ id: string; text: string; level: number }[]>([])
const relatedArticles = ref<Article[]>([])
const activeId = ref('')
const cardExpanded = ref<Record<string, boolean>>({})

// ===== 篇幅配置 =====
const LEN_BADGE: Record<string, string> = {
  short: 'bg-sky-50 text-sky-700 border-sky-200',
  medium: 'bg-morandi-accent/10 text-morandi-accent border-morandi-accent/30',
  long: 'bg-violet-50 text-violet-700 border-violet-200'
}
const LEN_TABS: { key: LengthType; label: string; icon: Component }[] = [
  { key: 'short', label: '速读卡', icon: Zap },
  { key: 'medium', label: '深度文', icon: FlaskConical },
  { key: 'long', label: '综述文', icon: GraduationCap }
]
const LEN_ICON: Record<LengthType, Component> = {
  short: Zap, medium: FlaskConical, long: GraduationCap
}
function lenIcon(k: LengthType) { return LEN_ICON[k] }
const otherTabs = computed(() => LEN_TABS.filter(t => t.key !== currentLen.value))

// ===== 学术术语词典 =====
const GLOSSARY: Record<string, { def: string; alias?: string }> = {
  '脂肪酸': { def: '构成脂肪的基本单位，分为饱和、单不饱和、多不饱和三类，对健康影响不同。' },
  '饱和脂肪酸': { def: '碳链上没有双键的脂肪酸，主要存在于动物脂肪和热带植物油中，摄入过多会升高血脂。', alias: 'SFA' },
  '单不饱和脂肪酸': { def: '含一个双键的脂肪酸，以油酸为代表，橄榄油、茶籽油中含量丰富，有助于心血管健康。', alias: 'MUFA' },
  '多不饱和脂肪酸': { def: '含两个及以上双键的脂肪酸，包括 Omega-3 和 Omega-6，人体不能自行合成。', alias: 'PUFA' },
  'Omega-3': { def: '一类多不饱和脂肪酸，主要包括 EPA、DHA、ALA，深海鱼和亚麻籽中含量高，有抗炎和心血管保护作用。' },
  'EPA': { def: '二十碳五烯酸，Omega-3 家族成员，主要来源于深海鱼，有抗炎和降甘油三酯作用。' },
  'DHA': { def: '二十二碳六烯酸，Omega-3 家族成员，对大脑和视网膜发育至关重要。' },
  '低密度脂蛋白胆固醇': { def: '俗称"坏胆固醇"，水平过高会导致血管斑块沉积，是心血管疾病的重要危险指标。', alias: 'LDL-C' },
  '高密度脂蛋白胆固醇': { def: '俗称"好胆固醇"，有助于将胆固醇从外周组织运回肝脏代谢，水平高有益心血管。', alias: 'HDL-C' },
  '甘油三酯': { def: '血液中主要的脂肪形式，水平过高是心血管疾病和胰腺炎的危险因素。', alias: 'TG' },
  '反式脂肪酸': { def: '不饱和脂肪酸的异构体，主要来自工业氢化植物油，心血管危害最大。', alias: 'TFA' },
  '动脉粥样硬化': { def: '脂质在动脉壁沉积形成斑块，导致血管狭窄、弹性下降，是冠心病和脑梗死的病理基础。' },
  '随机对照试验': { def: '最高级别的临床证据类型，通过随机分组对照评估干预效果，结果最可靠。', alias: 'RCT' },
  'Meta分析': { def: '对多个独立研究结果进行统计学合并分析的方法，能提高结论的统计效力和可靠性。' },
  '地中海饮食': { def: '以蔬果、全谷、橄榄油、鱼类为主的传统饮食模式，被多项研究证实可降低心血管风险。' },
  '胰岛素抵抗': { def: '细胞对胰岛素敏感性下降，是2型糖尿病和代谢综合征的核心病理机制。' },
  '血糖生成指数': { def: '衡量食物引起血糖升高程度的指标，GI值越高，对血糖影响越大。', alias: 'GI' },
  '基础代谢率': { def: '人体在静息状态下维持基本生命活动所需的最低能量消耗。', alias: 'BMR' },
  '体质量指数': { def: '体重（kg）除以身高（m）的平方，用于评估体重是否正常的常用指标。', alias: 'BMI' },
  '膳食纤维': { def: '人体不能消化吸收的植物性成分，可促进肠道蠕动、调节血糖和血脂。' },
  '抗氧化剂': { def: '能清除体内自由基、减轻氧化损伤的物质，如维生素C、E、多酚类等。' },
  '益生菌': { def: '对宿主有益的活性微生物，可调节肠道菌群平衡，常见于酸奶、发酵食品。' },
  '叶酸': { def: 'B族维生素之一，对胎儿神经管发育和红细胞生成至关重要，孕期需重点补充。' },
  '钙': { def: '人体含量最多的矿物质，99%存在于骨骼和牙齿中，对骨骼健康和神经肌肉功能至关重要。' },
  '铁': { def: '合成血红蛋白的必需微量元素，缺乏会导致缺铁性贫血，女性和儿童更易缺乏。' },
  '维生素D': { def: '脂溶性维生素，促进钙吸收和骨骼健康，阳光照射是主要来源之一。' }
}

// 按长度降序排列，避免短词先匹配
const GLOSSARY_KEYS = Object.keys(GLOSSARY).sort((a, b) => b.length - a.length)

// ===== 术语 Tooltip =====
const termTooltip = ref({ show: false, term: '', def: '', x: 0, y: 0 })
let hideTimer: any = null

function showTermTooltip(term: string, event: MouseEvent) {
  clearTimeout(hideTimer)
  const entry = GLOSSARY[term]
  if (!entry) return
  const rect = (event.target as HTMLElement).getBoundingClientRect()
  const tooltipW = 320
  let x = rect.left + rect.width / 2 - tooltipW / 2
  x = Math.max(8, Math.min(x, window.innerWidth - tooltipW - 8))
  let y = rect.bottom + 8
  if (y + 160 > window.innerHeight) y = rect.top - 168
  const displayTerm = entry.alias ? `${term}（${entry.alias}）` : term
  termTooltip.value = { show: true, term: displayTerm, def: entry.def, x, y }
}
function keepTooltip() { clearTimeout(hideTimer) }
function hideTooltip() {
  hideTimer = setTimeout(() => { termTooltip.value.show = false }, 200)
}

// ===== 数据加载 =====
async function load() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const data = await fetchArticleDetail(id)
    article.value = data
    if (article.value) currentLen.value = article.value.lengthType || 'medium'
    if (article.value?.topicGroupId) {
      fetchRelatedArticles(article.value.topicGroupId, article.value?.id).then(list => {
        relatedArticles.value = list
      })
    } else {
      relatedArticles.value = []
    }
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => route.params.id, load)

// ===== 内容显示 =====
const displayContent = computed(() => {
  if (!article.value) return ''
  if (currentLen.value === 'short') return article.value.contentShort || article.value.content
  if (currentLen.value === 'long') return article.value.contentLong || article.value.content
  return article.value.contentMedium || article.value.content
})
const displaySummary = computed(() => {
  if (!article.value) return ''
  if (currentLen.value === 'short') return article.value.summaryShort || article.value.summary
  if (currentLen.value === 'long') return article.value.summaryLong || article.value.summary
  return article.value.summaryMedium || article.value.summary
})
const displayTitle = computed(() => {
  if (!article.value) return ''
  return article.value.title.replace(/【.+】$/, '')
})
const displayWordCount = computed(() => {
  const c = displayContent.value || ''
  return c.replace(/[^\u4e00-\u9fa5]/g, '').length
})
const sources = computed(() => parseSources(article.value?.sourcesJson))

// ===== Markdown 渲染 =====
function renderMarkdown(md: string): string {
  if (!md) return ''
  let html = md

  // 转义 HTML
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  // 代码块
  html = html.replace(/```([\s\S]*?)```/g, (_, code) =>
    `<pre class="code-block"><code>${code.trim()}</code></pre>`)

  // 表格
  html = html.replace(/^\|(.+)\|\n\|([-:\s|]+)\|\n((?:\|.+\|\n?)*)/gm, (_, header, _sep, body) => {
    const heads = header.split('|').map((h: string) => h.trim()).filter(Boolean)
    const rows = body.trim().split('\n').map((r: string) =>
      r.split('|').map((c: string) => c.trim()).filter(Boolean))
    const thead = `<thead><tr>${heads.map((h: string) => `<th>${h}</th>`).join('')}</tr></thead>`
    const tbody = `<tbody>${rows.map((r: string[]) =>
      `<tr>${r.map((c: string) => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody>`
    return `<div class="table-wrap"><table>${thead}${tbody}</table></div>`
  })

  // 标题（带 ID 用于 TOC 跳转）
  html = html.replace(/^###\s+(.+)$/gm, (_, text) => {
    const id = 'h-' + text.replace(/[^\w\u4e00-\u9fa5]/g, '').slice(0, 20)
    return `<h3 id="${id}" class="scroll-mt-24">${text}</h3>`
  })
  html = html.replace(/^##\s+(.+)$/gm, (_, text) => {
    const id = 'h-' + text.replace(/[^\w\u4e00-\u9fa5]/g, '').slice(0, 20)
    return `<h2 id="${id}" class="scroll-mt-24">${text}</h2>`
  })
  html = html.replace(/^#\s+(.+)$/gm, (_, text) => `<h1>${text}</h1>`)

  // 引用块
  html = html.replace(/^&gt;\s(.+)$/gm, '<blockquote>$1</blockquote>')

  // 列表
  html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
  html = html.replace(/^[-*]\s+(.+)$/gm, '<li class="ul-item">$1</li>')
  html = html.replace(/(<li[^>]*>.*<\/li>\n?)+/g, (m) => {
    if (m.includes('ul-item')) {
      return '<ul>' + m.replace(/ class="ul-item"/g, '') + '</ul>'
    }
    return '<ol>' + m + '</ol>'
  })

  // 粗体和斜体
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')

  // 段落
  html = html.split('\n\n').map(block => {
    if (block.match(/^<(h[1-3]|ul|ol|pre|blockquote|div)/)) return block
    if (block.trim() === '') return ''
    return `<p>${block.replace(/\n/g, '<br>')}</p>`
  }).join('\n')

  return html
}

// ===== 术语自动链接 + 引用角标 =====
function linkTermsAndRefs(html: string): string {
  // 1. 将 [1] [2] 或 （1）（2）等引用标记转为可点击角标
  html = html.replace(/[\[［]\s*(\d+)\s*[\]］]/g, (_, n) => {
    return `<sup class="cite-badge" data-ref="${n}" onclick="document.getElementById('ref-${n}')?.scrollIntoView({behavior:'smooth',block:'center'})">[${n}]</sup>`
  })

  // 2. 用 DOM 扫描文本节点，包裹 GLOSSARY 术语（每篇内容仅标记术语首次出现）
  const firstOccurrence = new Set<string>()
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = html
  walkAndWrapTerms(tempDiv, firstOccurrence)
  return tempDiv.innerHTML
}

function walkAndWrapTerms(node: Node, firstOccurrence: Set<string>) {
  const children = Array.from(node.childNodes)
  for (const child of children) {
    if (child.nodeType === Node.TEXT_NODE) {
      const text = child.textContent || ''
      if (text.length < 2) continue
      const parentTag = (child.parentElement?.tagName || '').toLowerCase()
      if (['script', 'style', 'code', 'pre', 'sup', 'a'].includes(parentTag)) continue

      let replaced = text
      const replacements: { term: string; html: string; placeholder: string }[] = []

      for (const term of GLOSSARY_KEYS) {
        // 已经标记过首次出现的术语，跳过
        if (firstOccurrence.has(term)) continue
        if (!replaced.includes(term)) continue

        const entry = GLOSSARY[term]
        // 匹配两种形式："术语（alias）" 或纯 "术语"
        const escapedTerm = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        // 如果有 alias，优先匹配已经带 alias 括号的完整形式
        const pattern = entry.alias
          ? new RegExp(`${escapedTerm}（${entry.alias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}）|${escapedTerm}`)
          : new RegExp(escapedTerm)
        const match = replaced.match(pattern)
        if (!match) continue

        const matchedText = match[0]
        const placeholder = `\x00TERM${replacements.length}\x00`
        const replacementHtml = `<span class="term-mark" data-term="${term}">${matchedText}</span>`
        replaced = replaced.replace(pattern, placeholder)
        replacements.push({ term, html: replacementHtml, placeholder })
        firstOccurrence.add(term)
      }

      if (replacements.length > 0) {
        replacements.forEach(r => {
          replaced = replaced.replace(r.placeholder, r.html)
        })
        const span = document.createElement('span')
        span.innerHTML = replaced
        node.replaceChild(span, child)
      }
    } else if (child.nodeType === Node.ELEMENT_NODE) {
      const tag = (child as HTMLElement).tagName.toLowerCase()
      if (!['script', 'style', 'code', 'pre', 'sup'].includes(tag)) {
        walkAndWrapTerms(child, firstOccurrence)
      }
    }
  }
}

// ===== 处理后的内容 =====
const processedContent = computed(() => {
  const raw = displayContent.value
  if (!raw) return ''
  let html = renderMarkdown(raw)
  if (typeof document !== 'undefined') {
    html = linkTermsAndRefs(html)
  }
  return html
})

// ===== 卡片化内容（按 h2 分割为可折叠卡片） =====
interface ContentCard {
  id: string
  title: string
  html: string
  expanded: boolean
  h2Id: string
}

const contentCards = computed<ContentCard[]>(() => {
  const html = processedContent.value
  if (!html) return []

  const h2Regex = /<h2[^>]*id="([^"]+)"[^>]*>.*?<\/h2>/g
  const matches: { id: string; start: number; end: number; title: string }[] = []
  let m: RegExpExecArray | null
  while ((m = h2Regex.exec(html)) !== null) {
    const id = m[1]
    const title = m[0].replace(/<[^>]*>/g, '').trim()
    matches.push({ id, start: m.index, end: m.index + m[0].length, title })
  }

  if (matches.length === 0) {
    return [{ id: 'intro', title: '全文', html, expanded: true, h2Id: '' }]
  }

  const cards: ContentCard[] = []
  if (matches[0].start > 0) {
    const introHtml = html.substring(0, matches[0].start).trim()
    if (introHtml) {
      cards.push({ id: 'intro', title: '导读', html: introHtml, expanded: true, h2Id: '' })
    }
  }

  for (let i = 0; i < matches.length; i++) {
    const start = matches[i].start
    const end = i + 1 < matches.length ? matches[i + 1].start : html.length
    let cardHtml = html.substring(start, end).trim()
    // Remove the h2 tag from card body (it's shown in the card header)
    cardHtml = cardHtml.replace(/<h2[^>]*>.*?<\/h2>/, '').trim()
    const cardId = `card-${i}`
    const expanded = cardExpanded.value[cardId] ?? (cards.length < 2)
    cards.push({ id: cardId, title: matches[i].title, html: cardHtml, expanded, h2Id: matches[i].id })
  }

  return cards
})

function toggleCard(cardId: string, idx: number) {
  const current = cardExpanded.value[cardId] ?? (idx < 2)
  cardExpanded.value = { ...cardExpanded.value, [cardId]: !current }
  nextTick(() => {
    extractToc()
    setupObserver()
    bindTermEvents()
    bindCiteEvents()
  })
}

// ===== TOC 提取 =====
watch(processedContent, () => {
  nextTick(() => {
    extractToc()
    setupObserver()
    bindTermEvents()
    bindCiteEvents()
  })
})
watch(contentCards, () => {
  nextTick(() => {
    extractToc()
    setupObserver()
    bindTermEvents()
    bindCiteEvents()
  })
}, { deep: true })

function extractToc() {
  if (!contentRef.value) return
  const items: { id: string; text: string; level: number }[] = []

  // 按卡片顺序：每个 h2 后紧跟其下属的 h3，确保层级关系正确
  contentCards.value.forEach(card => {
    if (!card.h2Id) return
    items.push({ id: card.h2Id, text: card.title, level: 1 })

    const h3Regex = /<h3[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/h3>/g
    let h3m: RegExpExecArray | null
    while ((h3m = h3Regex.exec(card.html)) !== null) {
      const h3Id = h3m[1]
      const h3Text = h3m[2].replace(/<[^>]*>/g, '').trim()
      items.push({ id: h3Id, text: h3Text, level: 2 })
    }
  })

  toc.value = items
}

// ===== 滚动跟随目录 =====
let observer: IntersectionObserver | null = null
function setupObserver() {
  if (observer) observer.disconnect()
  observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const id = (e.target as HTMLElement).id
        if (id) activeId.value = id
      }
    })
  }, { rootMargin: '-80px 0px -70% 0px', threshold: 0 })

  nextTick(() => {
    // Observe all h2 (card divs) and h3 elements
    contentCards.value.forEach(card => {
      if (card.h2Id) {
        const el = document.getElementById(card.h2Id)
        if (el) observer!.observe(el)
      }
    })
    const h3s = contentRef.value?.querySelectorAll('.card-body h3[id]')
    h3s?.forEach(h => {
      observer!.observe(h)
    })
  })
}

// ===== 术语事件绑定 =====
function bindTermEvents() {
  if (!contentRef.value) return
  const terms = contentRef.value.querySelectorAll('.term-mark')
  terms.forEach(el => {
    const term = (el as HTMLElement).dataset.term
    if (!term) return
    el.addEventListener('mouseenter', (e: Event) => showTermTooltip(term, e as MouseEvent))
    el.addEventListener('mouseleave', hideTooltip)
    el.addEventListener('click', (e: Event) => showTermTooltip(term, e as MouseEvent))
  })
}

// ===== 引用角标事件 =====
function bindCiteEvents() {
  if (!contentRef.value) return
  const cites = contentRef.value.querySelectorAll('.cite-badge')
  cites.forEach(el => {
    const n = (el as HTMLElement).dataset.ref
    if (!n) return
    el.addEventListener('click', () => {
      showSources.value = true
      nextTick(() => {
        const refEl = document.getElementById(`ref-${n}`)
        if (refEl) {
          refEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
          refEl.classList.add('ring-2', 'ring-morandi-accent', 'ring-offset-2', 'rounded-xl')
          setTimeout(() => refEl?.classList.remove('ring-2', 'ring-morandi-accent', 'ring-offset-2', 'rounded-xl'), 2500)
        }
      })
    })
  })
}

onUnmounted(() => observer?.disconnect())

// ===== 导航 =====
function switchLen(len: LengthType) {
  currentLen.value = len
  cardExpanded.value = {}
  nextTick(() => {
    scrollToTop()
  })
}
function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }) }
function jumpTo(id: string) {
  // Auto-expand the card containing this id
  const cards = contentCards.value
  for (let i = 0; i < cards.length; i++) {
    if (cards[i].h2Id === id || cards[i].html.includes(`id="${id}"`)) {
      cardExpanded.value = { ...cardExpanded.value, [cards[i].id]: true }
      break
    }
  }
  nextTick(() => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      activeId.value = id
      setupObserver()
      bindTermEvents()
      bindCiteEvents()
    }
  })
}
function goBack() { router.push('/dashboard/articles') }
function goDetail(id: number) { router.push(`/dashboard/article-detail/${id}`) }

function toggleLike() {
  liked.value = !liked.value
  if (liked.value && article.value) {
    api.article.like(article.value.id).catch(() => {})
  }
}
function handleShare() {
  if (navigator.share) {
    navigator.share({ title: article.value?.title, url: window.location.href })
  } else {
    navigator.clipboard?.writeText(window.location.href)
  }
}
function submitReport() {
  reportSubmitted.value = true
  setTimeout(() => { showReport.value = false; reportSubmitted.value = false }, 2000)
}
function formatDate(d: any): string {
  if (!d) return ''
  return String(d).replace(/T.*$/, '').replace(/-/g, '-')
}
</script>

<style scoped>
.expand-enter-active, .expand-leave-active { transition: all 0.3s ease; overflow: hidden; }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; }
.expand-enter-to, .expand-leave-from { opacity: 1; max-height: 2000px; }
.card-collapse-enter-active, .card-collapse-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
.card-collapse-enter-from, .card-collapse-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-4px);
}
.card-collapse-enter-to, .card-collapse-leave-from {
  opacity: 1;
  max-height: 5000px;
  transform: translateY(0);
}
</style>

<style>
/* ===== 文章正文样式 ===== */
.article-body { font-size: 15px; color: #2d3142; line-height: 1.9; }
.article-body h1 { font-size: 1.6rem; font-weight: 700; margin: 1.5rem 0 1rem; color: #2d3142; }
.article-body h2 {
  font-size: 1.25rem; font-weight: 700; margin: 2rem 0 1rem; color: #2d3142;
  padding-left: 0.75rem; border-left: 4px solid #43b086;
}
.article-body h3 {
  font-size: 1.05rem; font-weight: 600; margin: 1.5rem 0 0.75rem; color: #2d3142;
}
.article-body p { margin: 0.75rem 0; }
.article-body strong { font-weight: 600; color: #2d3142; }
.article-body em { font-style: italic; }
.article-body ul, .article-body ol { margin: 0.75rem 0; padding-left: 1.5rem; }
.article-body li { margin: 0.4rem 0; }
.article-body ul li { list-style: disc; }
.article-body ol li { list-style: decimal; }
.article-body blockquote {
  margin: 1rem 0; padding: 0.75rem 1rem; border-left: 3px solid #43b086;
  background: #f0fdf4; border-radius: 0 0.5rem 0.5rem 0; color: #4b5563;
}
.article-body .table-wrap { overflow-x: auto; margin: 1rem 0; border-radius: 0.75rem; border: 1px solid #e5e7eb; }
.article-body table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.article-body th { background: #f9fafb; padding: 0.625rem 1rem; text-align: left; font-weight: 600; border-bottom: 1px solid #e5e7eb; color: #2d3142; }
.article-body td { padding: 0.625rem 1rem; border-bottom: 1px solid #f3f4f6; color: #4b5563; }
.article-body tr:nth-child(even) { background: #fafafa; }
.article-body .code-block { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; margin: 1rem 0; font-size: 0.875rem; }
.article-body .code-block code { background: none; color: inherit; }

/* ===== 术语标记（Lucide BookA 图标替代 emoji） ===== */
.term-mark {
  display: inline-flex; align-items: center; gap: 2px;
  padding: 0 0.25rem; margin: 0 0.125rem; border-radius: 0.25rem;
  background: rgba(67, 176, 134, 0.08); color: #43b086;
  font-weight: 500; cursor: help;
  border-bottom: 1px dashed rgba(67, 176, 134, 0.4);
  transition: background 0.2s;
}
.term-mark:hover { background: rgba(67, 176, 134, 0.15); }
.term-mark::after {
  content: '';
  width: 12px; height: 12px; flex-shrink: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2343b086' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 19.5A2.5 2.5 0 0 1 6.5 17H20'/%3E%3Cpath d='M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-size: contain;
  background-position: center;
  opacity: 0.6;
}

/* ===== 引用角标 ===== */
.cite-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 1rem; height: 1rem; margin: 0 0.125rem; border-radius: 9999px;
  background: rgba(67, 176, 134, 0.15); color: #43b086;
  font-size: 0.625rem; font-weight: 700; cursor: pointer;
  vertical-align: super; transition: all 0.2s;
}
.cite-badge:hover { background: #43b086; color: white; }

/* ===== 行数限制 ===== */
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
