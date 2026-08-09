<template>
  <div class="space-y-6">
    <!-- 顶部标题栏 -->
    <div class="flex items-center justify-between">
      <div>
        <div class="flex items-center gap-3">
          <button
            v-if="selectedTopic"
            @click="selectedTopic = null"
            class="w-9 h-9 rounded-lg bg-white border border-morandi-soft/60 shadow-sm flex items-center justify-center text-morandi-lightText hover:text-morandi-accent hover:border-morandi-accent/30 transition"
          >
            <ChevronLeft class="w-5 h-5" />
          </button>
          <h2 class="text-2xl font-bold text-morandi-text flex items-center gap-2">
            <Newspaper class="w-7 h-7 text-morandi-accent" />
            AI 科普文章
          </h2>
        </div>
        <p class="text-sm text-morandi-lightText mt-1">
          {{ selectedTopic ? '选择篇幅，开启深度阅读' : '选择主题，探索循证营养学科普' }}
        </p>
      </div>
    </div>

    <!-- 适配人群筛选 -->
    <div v-if="!selectedTopic" class="bg-white rounded-2xl border border-morandi-soft/60 shadow-sm p-4">
      <div class="flex items-center gap-3 flex-wrap">
        <span class="text-sm font-medium text-morandi-text whitespace-nowrap">适配人群：</span>
        <button
          v-for="item in audienceFilters"
          :key="item.key"
          @click="selectedAudience = item.key"
          :class="[
            'px-4 py-1.5 rounded-full text-sm font-medium transition-all',
            selectedAudience === item.key
              ? 'bg-morandi-accent text-white shadow-md'
              : 'bg-morandi-soft/60 text-morandi-text hover:bg-morandi-soft'
          ]"
        >
          <span v-if="item.isUser" class="mr-1">👤</span>
          {{ item.label }}
        </button>
        <span class="text-xs text-morandi-lightText ml-auto">
          共 {{ filteredTopicList.length }} 个主题
        </span>
      </div>
    </div>

    <!-- 主题列表视图 -->
    <div v-if="!selectedTopic" class="grid grid-cols-1 md:grid-cols-2 gap-5">
      <div
        v-for="topic in filteredTopicList"
        :key="topic.id"
        @click="selectTopic(topic)"
        class="group cursor-pointer bg-white rounded-2xl border border-morandi-soft/60 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 overflow-hidden"
      >
        <div class="p-6 flex gap-5">
          <div class="flex-shrink-0 w-16 h-16 rounded-2xl bg-gradient-to-br from-morandi-accent/10 to-morandi-soft/40 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
            <component :is="topic.icon" class="w-8 h-8 text-morandi-accent" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h3 class="text-lg font-semibold text-morandi-text group-hover:text-morandi-accent transition">{{ topic.label }}</h3>
              <span class="text-[11px] px-2 py-0.5 rounded-full bg-morandi-gray text-morandi-lightText">{{ topic.category }}</span>
            </div>
            <p class="text-sm text-morandi-lightText leading-relaxed line-clamp-2">{{ topic.description }}</p>
            <div class="mt-3 flex items-center gap-4 text-xs text-morandi-lightText">
              <span class="inline-flex items-center gap-1">
                <BookOpen class="w-3.5 h-3.5" /> 3 种篇幅
              </span>
              <span class="inline-flex items-center gap-1">
                <Users class="w-3.5 h-3.5" /> {{ topic.audience }}
              </span>
              <span class="inline-flex items-center gap-1 text-morandi-accent font-medium group-hover:gap-1.5 transition-all">
                开始阅读 <ChevronRight class="w-3.5 h-3.5" />
              </span>
            </div>
            <!-- 适配人群标签 -->
            <div class="mt-2 flex flex-wrap gap-1">
              <span
                v-for="a in topic.audiences"
                :key="a"
                class="text-[10px] px-1.5 py-0.5 rounded bg-morandi-accent/10 text-morandi-accent"
              >{{ a }}</span>
            </div>
          </div>
        </div>
      </div>
      <!-- 加载中 -->
      <div v-if="loading" class="col-span-full text-center py-16 text-morandi-lightText">
        <div class="inline-block w-8 h-8 border-2 border-morandi-accent/30 border-t-morandi-accent rounded-full animate-spin"></div>
        <p class="mt-3 text-sm">加载科普文章中...</p>
      </div>
      <!-- 加载出错 -->
      <div v-else-if="error" class="col-span-full text-center py-12">
        <p class="text-sm text-red-500 mb-2">{{ error }}</p>
        <button @click="articleStore.fetchArticles()" class="text-sm text-morandi-accent hover:underline">点击重试</button>
      </div>
      <!-- 数据库无文章 -->
      <div v-else-if="articles.length === 0" class="col-span-full text-center py-12 text-morandi-lightText">
        <p class="text-sm mb-2">数据库暂无科普文章</p>
        <p v-if="userStore.user?.role !== 'admin'" class="text-xs">请联系管理员初始化科普文章数据</p>
        <template v-else>
          <p class="text-xs mb-3">首次使用需初始化数据，点击下方按钮生成 Demo 文章</p>
          <button
            @click="resetDemo"
            :disabled="resetting"
            class="px-4 py-2 text-sm rounded-lg bg-morandi-accent text-white hover:opacity-90 disabled:opacity-50 transition"
          >{{ resetting ? '初始化中...' : '一键初始化 Demo 数据' }}</button>
        </template>
      </div>
      <!-- 筛选无结果 -->
      <div v-else-if="filteredTopicList.length === 0" class="col-span-full text-center py-12 text-morandi-lightText">
        <p class="text-sm">暂无适配「{{ currentAudienceLabel }}」的科普主题</p>
        <button @click="selectedAudience = 'all'" class="mt-2 text-morandi-accent text-sm hover:underline">查看全部主题</button>
      </div>
    </div>

    <!-- 篇幅选项视图 -->
    <div v-else class="space-y-6">
      <!-- 当前主题信息条 -->
      <div class="bg-white rounded-2xl border border-morandi-soft/60 shadow-sm p-5 flex items-center gap-5">
        <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-morandi-accent/10 to-morandi-soft/40 flex items-center justify-center">
          <component :is="selectedTopic.icon" class="w-7 h-7 text-morandi-accent" />
        </div>
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <h3 class="text-lg font-semibold text-morandi-text">{{ selectedTopic.label }}</h3>
            <span class="text-xs px-2 py-0.5 rounded-full bg-morandi-gray text-morandi-lightText">{{ selectedTopic.category }}</span>
          </div>
          <p class="text-sm text-morandi-lightText mt-0.5">{{ selectedTopic.description }}</p>
          <div class="mt-2 flex flex-wrap gap-1">
            <span
              v-for="a in selectedTopic.audiences"
              :key="a"
              class="text-[10px] px-1.5 py-0.5 rounded bg-morandi-accent/10 text-morandi-accent"
            >{{ a }}</span>
          </div>
        </div>
      </div>

      <!-- 三个篇幅选项卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div
          v-for="opt in lengthOptions"
          :key="opt.key"
          @click="openArticle(opt.key)"
          :class="[
            'group cursor-pointer bg-white rounded-2xl border-2 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 overflow-hidden',
            opt.recommended ? 'border-morandi-accent/50 ring-2 ring-morandi-accent/10' : 'border-morandi-soft/60 hover:border-morandi-accent/30'
          ]"
        >
          <!-- 推荐标签 -->
          <div v-if="opt.recommended" class="bg-morandi-accent text-white text-xs font-medium px-4 py-1.5 text-center">
            ⭐ {{ opt.recommendedLabel }}
          </div>

          <div class="p-5">
            <!-- 图标和标题 -->
            <div class="flex items-center gap-3 mb-3">
              <div :class="['w-11 h-11 rounded-xl flex items-center justify-center', opt.bgClass]">
                <component :is="opt.icon" :class="['w-5 h-5', opt.iconClass]" />
              </div>
              <div>
                <h4 class="font-semibold text-morandi-text">{{ opt.label }}</h4>
                <span class="text-xs text-morandi-lightText">{{ opt.wordCount }}</span>
              </div>
            </div>

            <!-- 描述 -->
            <p class="text-sm text-morandi-lightText leading-relaxed mb-4 line-clamp-3">{{ opt.description }}</p>

            <!-- 特点列表 -->
            <ul class="space-y-1.5 mb-4">
              <li v-for="(feature, i) in opt.features" :key="i" class="flex items-start gap-2 text-xs text-morandi-text/80">
                <CheckCircle class="w-3.5 h-3.5 text-morandi-accent flex-shrink-0 mt-0.5" />
                <span>{{ feature }}</span>
              </li>
            </ul>

            <!-- 适用场景 -->
            <div class="pt-3 border-t border-morandi-soft/40">
              <p class="text-[11px] text-morandi-lightText mb-1">适用场景</p>
              <p class="text-xs text-morandi-text font-medium leading-relaxed">{{ opt.useCase }}</p>
            </div>

            <!-- 阅读按钮 -->
            <div class="mt-4 flex items-center justify-between">
              <span class="text-xs text-morandi-lightText">{{ opt.readTime }}</span>
              <span class="inline-flex items-center gap-1 text-sm font-medium text-morandi-accent group-hover:gap-1.5 transition-all">
                开始阅读 <ChevronRight class="w-4 h-4" />
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部提示 -->
      <div class="text-center text-xs text-morandi-lightText bg-white/50 rounded-xl py-3">
        不确定选哪个？推荐从 <span class="text-morandi-accent font-medium">深度文</span> 开始，内容完整且篇幅适中
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useArticleStore } from '@/stores/article'
import { CROWD_TO_AUDIENCE, CROWD_LABELS, ARTICLE_AUDIENCE_FILTERS } from '@/constants'
import {
  Newspaper, ChevronRight, ChevronLeft, BookOpen, Users, CheckCircle,
  Zap, FlaskConical, GraduationCap, ShieldCheck, Flame, Dumbbell, UtensilsCrossed
} from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()
const articleStore = useArticleStore()

// 从 store 获取文章列表和状态
const articles = computed(() => articleStore.articles)
const loading = computed(() => articleStore.loading)
const error = computed(() => articleStore.error)

// 根据 category 映射默认图标
const CATEGORY_ICON_MAP: Record<string, Component> = {
  '慢病管理': ShieldCheck,
  '运动营养': Dumbbell,
  '消化健康': UtensilsCrossed,
}
const DEFAULT_TOPIC_ICON: Component = Newspaper

function getIconForCategory(category: string): Component {
  return CATEGORY_ICON_MAP[category] || DEFAULT_TOPIC_ICON
}

// ===== 适配人群筛选 =====
interface AudienceFilter {
  key: string
  label: string
  isUser?: boolean
}

const selectedAudience = ref<string>('all')

const audienceFilters = computed<AudienceFilter[]>(() => {
  const filters: AudienceFilter[] = [{ key: 'all', label: '全部' }]
  const userCrowd = userStore.user?.crowdType
  const userLabel = CROWD_LABELS[userCrowd || '普通人'] || '普通人群'

  if (userCrowd && CROWD_TO_AUDIENCE[userCrowd]) {
    filters.push({ key: 'user', label: `我的人群(${userLabel})`, isUser: true })
  }

  for (const item of ARTICLE_AUDIENCE_FILTERS) {
    filters.push({ key: item.key, label: item.label })
  }
  return filters
})

const currentAudienceLabel = computed(() => {
  const f = audienceFilters.value.find(x => x.key === selectedAudience.value)
  return f?.label || '全部'
})

// ===== 主题数据（从后端文章动态提取） =====
interface TopicMeta {
  id: string
  label: string
  icon: Component
  category: string
  description: string
  audience: string
  audiences: string[]
}

const topicList = computed<TopicMeta[]>(() => {
  const arts = articles.value
  if (!arts || arts.length === 0) return []

  const topicMap = new Map<string, TopicMeta>()
  for (const a of arts) {
    const key = a.topic
    if (!topicMap.has(key)) {
      topicMap.set(key, {
        id: key,
        label: a.topic,
        icon: getIconForCategory(a.category),
        category: a.category || '',
        description: a.summary || '',
        audience: a.audience || '',
        audiences: [a.audience].filter(Boolean) as string[]
      })
    } else {
      const existing = topicMap.get(key)!
      if (a.audience && !existing.audiences.includes(a.audience)) {
        existing.audiences.push(a.audience)
      }
    }
  }
  return Array.from(topicMap.values())
})

// 筛选后的主题列表
const filteredTopicList = computed(() => {
  const all = topicList.value
  if (selectedAudience.value === 'all') return all
  if (selectedAudience.value === 'user') {
    const userCrowd = userStore.user?.crowdType || '普通人'
    const audiences = CROWD_TO_AUDIENCE[userCrowd] || ['普通人群']
    return all.filter(t => t.audiences.some(a => audiences.includes(a)))
  }
  return all.filter(t => t.audiences.includes(selectedAudience.value))
})

const selectedTopic = ref<TopicMeta | null>(null)

const lengthOptions = computed(() => [
  {
    key: 'short' as const,
    label: '速读卡',
    icon: Zap,
    wordCount: '约 300 字',
    description: '快速掌握核心要点，适合碎片化阅读',
    features: [
      '1分钟速览',
      '核心数据一览',
      '关键结论前置'
    ],
    useCase: '没时间但想了解要点时',
    readTime: '预计阅读 1 分钟',
    bgClass: 'bg-sky-50',
    iconClass: 'text-sky-600',
    recommended: false,
    recommendedLabel: '经典入门'
  },
  {
    key: 'medium' as const,
    label: '深度文',
    icon: FlaskConical,
    wordCount: '约 1500 字',
    description: '循证论证 + 实操方案，内容完整且篇幅适中',
    features: [
      '循证医学依据',
      '分步实操指南',
      '适用人群分析',
      '常见误区避坑'
    ],
    useCase: '想系统了解并实际应用时',
    readTime: '预计阅读 5-8 分钟',
    bgClass: 'bg-morandi-accent/10',
    iconClass: 'text-morandi-accent',
    recommended: true,
    recommendedLabel: '推荐首选',
    color: 'medium'
  },
  {
    key: 'long' as const,
    label: '综述文',
    icon: GraduationCap,
    wordCount: '约 2500 字',
    description: '含学术争议与前沿研究，深度探究主题全貌',
    features: [
      '完整知识体系',
      '学术争议解析',
      '最新研究进展',
      'Meta分析支持'
    ],
    useCase: '需要深入研究或教学参考时',
    readTime: '预计阅读 10-15 分钟',
    bgClass: 'bg-violet-50',
    iconClass: 'text-violet-600',
    recommended: false,
    recommendedLabel: '学术进阶'
  }
])

function selectTopic(topic: TopicMeta) {
  selectedTopic.value = topic
}

function openArticle(lengthType: 'short' | 'medium' | 'long') {
  if (!selectedTopic.value) return
  const topicArticles = articles.value.filter(
    a => a.topic === selectedTopic.value!.id && a.lengthType === lengthType
  )
  if (topicArticles.length > 0) {
    router.push(`/dashboard/article-detail/${topicArticles[0].id}`)
  }
}

const resetting = ref(false)

async function resetDemo() {
  resetting.value = true
  try {
    const { api } = await import('@/api')
    await api.article.generate('钙与骨骼健康', '老年人')
    await api.article.generate('高血压科学控盐', '高血压')
    await api.article.generate('健身蛋白质摄入指南', '健身')
    await articleStore.fetchArticles()
  } catch (e: any) {
    console.warn('初始化 Demo 失败', e)
  } finally {
    resetting.value = false
  }
}

onMounted(async () => {
  try { userStore.init() } catch { /* ignore */ }
  await articleStore.fetchArticles()
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
