<template>
  <div class="ar-page">
    <!-- ===== 顶带 ===== -->
    <div class="ar-band">
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
          <span class="crumb-node hot"><span class="nd"><Newspaper :size="13" /></span>科普文章</span>
        </span>
      </div>
      <div class="ttl"><Library :size="15" />科普星文 · 书阁</div>
      <span class="date"><Calendar :size="11" />{{ todayLabel }} · 第{{ volumeNo }}卷</span>
    </div>

    <!-- ===== 书架视图 ===== -->
    <template v-if="!selectedTopic">
      <!-- 星轨主题带 -->
      <div v-if="topicList.length > 0" class="ar-orbit">
        <svg class="line" viewBox="0 0 1000 86" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0,52 C120,20 210,74 330,44 C450,14 540,70 660,42 C780,16 880,66 1000,40" />
        </svg>
        <button
          v-for="(s, i) in orbitStars"
          :key="s.key"
          class="star-node"
          :class="{ on: topicFilter === s.key }"
          :style="{ left: s.left + '%', animationDelay: (0.1 + i * 0.05) + 's' }"
          @click="topicFilter = s.key"
        >
          <span class="nd">{{ s.ch }}</span><span class="lb">{{ s.lb }}</span>
        </button>
      </div>

      <!-- 主体两栏 -->
      <div class="ar-main">
        <div class="ar-list">
          <!-- 星域筛选 -->
          <div v-if="!loading && !error && topicList.length > 0" class="ar-chips">
            <button
              v-for="item in audienceFilters"
              :key="item.key"
              class="chip"
              :class="{ on: selectedAudience === item.key }"
              @click="selectedAudience = item.key"
            >
              <span v-if="item.isUser">✦ </span>{{ item.label }}
            </button>
            <span class="ar-count">{{ filteredTopicList.length }} 个主题</span>
          </div>

          <!-- 书卡 -->
          <div v-if="!loading && !error && filteredTopicList.length > 0" class="ar-cards">
            <button
              v-for="(topic, i) in filteredTopicList"
              :key="topic.id"
              class="bk"
              :style="{ animationDelay: (0.14 + i * 0.06) + 's' }"
              @click="selectTopic(topic)"
            >
              <span class="cover">
                <b>{{ topic.id.slice(0, 1) }}</b>
                <i class="tag">{{ topic.category || '科普' }}</i>
              </span>
              <span class="meta">
                <h5>{{ topic.label }} <BadgeCheck :size="11" /></h5>
                <p>{{ topic.description }}</p>
                <span class="auds"><i v-for="a in topic.audiences" :key="a">{{ a }}</i></span>
                <span class="go">3 种篇幅 · 开始阅读 <ChevronRight :size="11" /></span>
              </span>
            </button>
          </div>

          <!-- 加载中 -->
          <div v-if="loading" class="ar-state">
            <div class="spin-ring"></div>
            <p class="mt-3 text-sm">正在点亮书阁的星辰...</p>
          </div>
          <!-- 加载出错 -->
          <div v-else-if="error" class="ar-state">
            <AlertTriangle :size="26" class="st-ic warn" />
            <p class="st-tt">{{ error }}</p>
            <button class="gold-btn" @click="articleStore.fetchArticles()">点击重试</button>
          </div>
          <!-- 数据库无文章 -->
          <div v-else-if="articles.length === 0" class="ar-state">
            <BookOpen :size="26" class="st-ic" />
            <p class="st-tt">书阁暂无藏书</p>
            <p v-if="userStore.user?.role !== 'admin'" class="st-ds">请联系管理员初始化科普文章数据</p>
            <template v-else>
              <p class="st-ds">首次使用需初始化数据，点击下方按钮生成 Demo 文章</p>
              <button class="gold-btn" :disabled="resetting" @click="resetDemo">
                {{ resetting ? '初始化中...' : '✦ 一键初始化 Demo 数据' }}
              </button>
            </template>
          </div>
          <!-- 筛选无结果 -->
          <div v-else-if="filteredTopicList.length === 0" class="ar-state">
            <BookOpen :size="26" class="st-ic" />
            <p class="st-tt">暂无适配「{{ currentAudienceLabel }}」的科普主题</p>
            <button class="gold-btn" @click="selectedAudience = 'all'">查看全部主题</button>
          </div>
        </div>

        <!-- 篇牍侧栏（静态预览） -->
        <aside class="ar-side">
          <div class="side-h"><ScrollText :size="11" />篇牍 · 篇幅选择</div>
          <div
            v-for="opt in lengthOptions"
            :key="opt.key"
            class="pick"
            :class="{ reco: opt.recommended }"
          >
            <div class="ph"><b>{{ opt.label }}</b><span>{{ opt.wordCount }}</span></div>
            <p>{{ opt.description }}</p>
            <span v-if="opt.recommended" class="reco-tag">✦ 星标推荐</span>
            <div class="rt"><Clock :size="10" />{{ opt.readTime }}</div>
          </div>
          <div class="side-note">
            从书架选一册藏书，篇牍随即点亮 —— 不确定选哪个？推荐从 <b>深度文</b> 开始。
          </div>
        </aside>
      </div>
    </template>

    <!-- ===== 篇牍视图 ===== -->
    <template v-else>
      <div class="ar-viewbar">
        <button class="backlink" @click="selectedTopic = null"><ChevronLeft :size="11" />返回书架</button>
        <b class="vb-tt">{{ selectedTopic.category }} · {{ selectedTopic.label }}</b>
        <span class="crumb">书阁 / 篇牍</span>
      </div>
      <div class="ar-lenwrap">
        <div class="len-grid">
          <button
            v-for="opt in lengthOptions"
            :key="opt.key"
            class="len"
            :class="{ reco: opt.recommended }"
            @click="openArticle(opt.key)"
          >
            <span v-if="opt.recommended" class="seal">✦ 星标推荐</span>
            <div class="ic"><component :is="opt.icon" :size="16" /></div>
            <h5>{{ opt.label }}</h5>
            <div class="wc">{{ opt.wordCount }} · {{ opt.readTime.replace('预计阅读 ', '') }}</div>
            <p>{{ opt.description }}</p>
            <ul>
              <li v-for="(f, fi) in opt.features" :key="fi"><CheckCircle :size="11" />{{ f }}</li>
            </ul>
            <div class="foot">
              <span>{{ opt.readTime.replace('预计阅读 ', '') }}</span>
              <b>开始阅读 <ChevronRight :size="11" /></b>
            </div>
          </button>
        </div>
        <div class="len-note">不确定选哪个？推荐从 <b>深度文</b> 开始，内容完整且篇幅适中</div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useArticleStore } from '@/stores/article'
import { CROWD_TO_AUDIENCE, CROWD_LABELS, ARTICLE_AUDIENCE_FILTERS } from '@/constants'
import {
  Library, Calendar, ChevronRight, ChevronLeft, BadgeCheck, ScrollText, Clock,
  CheckCircle, Zap, FlaskConical, GraduationCap, BookOpen, AlertTriangle,
  LayoutGrid, Newspaper
} from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()
const articleStore = useArticleStore()

// 星轨面包屑：首页 / 知识中心中转站
function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'knowledge' } }) }

// 从 store 获取文章列表和状态
const articles = computed(() => articleStore.articles)
const loading = computed(() => articleStore.loading)
const error = computed(() => articleStore.error)

// ===== 书阁日期 / 卷号 =====
const _now = new Date()
const _start = new Date(_now.getFullYear(), 0, 1)
const todayLabel = `${_now.getFullYear()}-${String(_now.getMonth() + 1).padStart(2, '0')}-${String(_now.getDate()).padStart(2, '0')}`
const volumeNo = Math.ceil(((_now.getTime() - _start.getTime()) / 86400000 + _start.getDay() + 1) / 7)

// ===== 适配人群筛选（星域） =====
interface AudienceFilter {
  key: string
  label: string
  isUser?: boolean
}

const selectedAudience = ref<string>('all')

const audienceFilters = computed<AudienceFilter[]>(() => {
  const filters: AudienceFilter[] = [{ key: 'all', label: '全部星域' }]
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

// ===== 星轨主题带：全部 ✦ + 各主题星标 =====
const topicFilter = ref<string>('all')

const orbitStars = computed(() => {
  const stars = [
    { key: 'all', ch: '✦', lb: '全部' },
    ...topicList.value.map(t => ({ key: t.id, ch: t.id.slice(0, 1), lb: t.category || t.id }))
  ]
  const n = stars.length
  return stars.map((s, i) => ({ ...s, left: n === 1 ? 50 : 4 + (i * 92) / (n - 1) }))
})

// 筛选后的主题列表（星轨 × 星域双重筛选）
const filteredTopicList = computed(() => {
  let all = topicList.value
  if (topicFilter.value !== 'all') {
    all = all.filter(t => t.id === topicFilter.value)
  }
  if (selectedAudience.value === 'all') return all
  if (selectedAudience.value === 'user') {
    const userCrowd = userStore.user?.crowdType || '普通人'
    const audiences = CROWD_TO_AUDIENCE[userCrowd] || ['普通人群']
    return all.filter(t => t.audiences.some(a => audiences.includes(a)))
  }
  return all.filter(t => t.audiences.includes(selectedAudience.value))
})

const selectedTopic = ref<TopicMeta | null>(null)

function selectTopic(topic: TopicMeta) {
  selectedTopic.value = topic
}

// ===== 篇牍（篇幅选项） =====
const lengthOptions = computed(() => [
  {
    key: 'short' as const,
    label: '速读卡',
    icon: Zap,
    wordCount: '约 300 字',
    description: '快速掌握核心要点，适合碎片化阅读，三句话讲清「是什么、吃多少、怎么选」。',
    features: ['1分钟速览', '核心数据一览', '关键结论前置'],
    readTime: '预计阅读 1 分钟',
    recommended: false
  },
  {
    key: 'medium' as const,
    label: '深度文',
    icon: FlaskConical,
    wordCount: '约 1500 字',
    description: '循证论证 + 实操方案，机制讲透、内容完整且篇幅适中，读完即可落地。',
    features: ['循证医学依据', '分步实操指南', '适用人群分析', '常见误区避坑'],
    readTime: '预计阅读 5-8 分钟',
    recommended: true
  },
  {
    key: 'long' as const,
    label: '综述文',
    icon: GraduationCap,
    wordCount: '约 2500 字',
    description: '含学术争议与前沿研究，全景综述：剂量、时机、人群差异一网打尽。',
    features: ['完整知识体系', '学术争议解析', '最新研究进展', 'Meta分析支持'],
    readTime: '预计阅读 10-15 分钟',
    recommended: false
  }
])

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
/* ================= P8-A 星藏书阁 ================= */
.ar-page {
  font-family: 'Noto Sans SC', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background:
    radial-gradient(ellipse at 78% -8%, rgba(217, 162, 74, .14), transparent 44%),
    linear-gradient(168deg, #1C1710, #12100A 62%);
  border-radius: 18px;
  color: #F0E2C4;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 620px;
}
.ar-page button { font-family: inherit; cursor: pointer; }

/* 入场动效（backwards：结束后归还 transform，hover 不受影响） */
@keyframes arRise {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: none; }
}

/* ===== 顶带 ===== */
.ar-band {
  display: flex; align-items: center; gap: 12px;
  padding: 16px 24px 12px;
  border-bottom: 1px solid rgba(217, 162, 74, .2);
  animation: arRise .7s ease backwards;
}
.ar-band .ttl {
  font-size: 15px; font-weight: 900; letter-spacing: .1em; color: #F6EAD6;
  display: inline-flex; align-items: center; gap: 7px;
}
.ar-band .ttl svg { color: #E8B973; }
/* ---- 星轨面包屑导航 ---- */
.star-crumbs { display: flex; align-items: center; flex-shrink: 0; }
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
.ar-band .date {
  margin-left: auto; display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px; color: #B9A78A;
  border: 1px solid rgba(217, 162, 74, .3); background: rgba(217, 162, 74, .08);
  border-radius: 999px; padding: 3px 10px;
}
.ar-band .date svg { color: #E8B973; }

/* ===== 星轨主题带 ===== */
.ar-orbit {
  position: relative; height: 86px;
  border-bottom: 1px solid rgba(217, 162, 74, .14);
  overflow: hidden;
  animation: arRise .7s ease .08s backwards;
}
.ar-orbit .line { position: absolute; inset: 0; width: 100%; height: 100%; }
.ar-orbit .line path {
  fill: none; stroke: rgba(217, 162, 74, .32); stroke-width: 1.1;
  stroke-dasharray: 4 7; vector-effect: non-scaling-stroke;
}
/* 星轨数据球入场：关键帧内链式保留 -50% 居中位移，避免动画期间丢失定位偏移 */
@keyframes arStarIn {
  from { opacity: 0; transform: translate(-50%, -50%) translateY(16px); }
  to { opacity: 1; transform: translate(-50%, -50%); }
}
.star-node {
  position: absolute; top: 50%; transform: translate(-50%, -50%);
  display: flex; flex-direction: column; align-items: center; gap: 5px;
  background: none; border: none; z-index: 3;
  animation: arStarIn .6s ease backwards;
}
.star-node .nd {
  width: 30px; height: 30px; border-radius: 50%;
  border: 1px solid rgba(217, 162, 74, .45); color: #9A8A6C;
  display: flex; align-items: center; justify-content: center;
  background: rgba(24, 19, 12, .92); transition: .3s;
  font-size: 10.5px; font-weight: 700; letter-spacing: .02em;
}
.star-node .lb {
  font-size: 10px; color: #8C7A5E; letter-spacing: .08em;
  transition: .3s; white-space: nowrap;
}
.star-node:hover .nd { color: #E8B973; border-color: #E8B973; box-shadow: 0 0 14px rgba(217, 162, 74, .4); }
.star-node.on .nd {
  color: #14110B; background: linear-gradient(135deg, #E8B973, #B36B2A);
  border-color: #E8B973; box-shadow: 0 0 18px rgba(217, 162, 74, .55);
}
.star-node.on .lb { color: #E8B973; }

/* ===== 主体两栏（浅芯暖纸） ===== */
.ar-main {
  flex: 1; display: grid; grid-template-columns: 1fr 264px; gap: 0; min-height: 0;
  animation: arRise .7s ease .16s backwards;
  background:
    radial-gradient(rgba(46, 42, 34, .05) 1px, transparent 1.2px) 0 0 / 7px 7px,
    #FDFAF3;
  color: #55503F;
}
.ar-list { padding: 16px 20px 20px; min-width: 0; }
.ar-side {
  border-left: 1px solid rgba(184, 134, 59, .28);
  padding: 16px 16px 20px; background: #F8F2E3;
}

/* 星域筛选 */
.ar-chips { display: flex; gap: 7px; flex-wrap: wrap; margin-bottom: 14px; }
.chip {
  font-size: 11.5px; padding: 5px 13px; border-radius: 999px;
  border: 1px solid rgba(184, 134, 59, .35); background: rgba(184, 134, 59, .06);
  color: #8a6d3b; transition: .25s; letter-spacing: .04em;
}
.chip:hover { color: #B8863B; border-color: #B8863B; }
.chip.on {
  color: #FDFAF3; background: linear-gradient(135deg, #C99A4B, #A0722F);
  border-color: transparent; font-weight: 700;
}
.ar-count { font-size: 10.5px; color: #847C63; margin-left: auto; align-self: center; }

/* 书卡（字纹藏书封面） */
.ar-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.bk {
  position: relative; border: 1px solid rgba(184, 134, 59, .35); border-radius: 14px;
  overflow: hidden; background: #FDFAF3;
  transition: transform .35s, border-color .35s, box-shadow .35s;
  display: flex; cursor: pointer; text-align: left; padding: 0;
  animation: arRise .55s ease backwards;
}
.bk:hover {
  transform: translateY(-3px); border-color: rgba(184, 134, 59, .7);
  box-shadow: 0 16px 32px -16px rgba(46, 42, 34, .35), 0 0 18px rgba(184, 134, 59, .12);
}
.bk .cover {
  width: 74px; flex-shrink: 0; position: relative;
  display: flex; align-items: center; justify-content: center;
  background:
    radial-gradient(circle at 30% 22%, rgba(184, 134, 59, .16), transparent 68%),
    linear-gradient(160deg, #F5EDDA, #EFE2C4);
}
.bk .cover::after {
  content: ''; position: absolute; inset: 0;
  background-image: radial-gradient(rgba(184, 134, 59, .35) 1px, transparent 1.5px);
  background-size: 17px 17px; opacity: .3;
}
.bk .cover b {
  position: relative; z-index: 2;
  font-family: 'Noto Serif SC', serif; font-size: 30px; font-weight: 900;
  color: #B8863B; text-shadow: 0 2px 10px rgba(184, 134, 59, .3);
}
.bk .cover .tag {
  position: absolute; bottom: 5px; left: 0; right: 0; z-index: 2;
  text-align: center; font-style: normal; font-size: 8.5px;
  letter-spacing: .18em; color: #A08F6E;
}
.bk .meta { padding: 11px 12px; min-width: 0; display: block; }
.bk .meta h5 {
  font-size: 13.5px; font-weight: 700; color: #2E2A22; letter-spacing: .03em;
  display: flex; align-items: center; gap: 6px;
}
.bk .meta h5 svg { color: #A0722F; flex-shrink: 0; }
.bk .meta p {
  font-size: 10.8px; line-height: 1.7; color: #847C63; margin-top: 4px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.bk .auds { margin-top: 7px; display: flex; gap: 4px; flex-wrap: wrap; }
.bk .auds i {
  font-style: normal; font-size: 9px; padding: 1.5px 7px; border-radius: 99px;
  background: rgba(184, 134, 59, .1); color: #8a6d3b; border: 1px solid rgba(184, 134, 59, .28);
}
.bk .go {
  margin-top: 8px; font-size: 10.5px; color: #B8863B;
  display: inline-flex; align-items: center; gap: 3px; font-weight: 600;
}
.bk .go svg { transition: .25s; }
.bk:hover .go svg { transform: translateX(3px); }

/* 空态 / 加载态 */
.ar-state { text-align: center; padding: 52px 20px; color: #847C63; }
.ar-state .st-ic { color: rgba(184, 134, 59, .75); }
.ar-state .st-ic.warn { color: #B5442E; }
.ar-state .st-tt { font-size: 13.5px; color: #2E2A22; margin-top: 10px; font-weight: 700; }
.ar-state .st-ds { font-size: 11.5px; margin-top: 6px; color: #847C63; }
.ar-state .gold-btn {
  margin-top: 14px; font-size: 12px; font-weight: 700; letter-spacing: .04em;
  color: #FDFAF3; background: linear-gradient(135deg, #C99A4B, #A0722F);
  border: none; border-radius: 999px; padding: 7px 16px; transition: .25s;
  box-shadow: 0 8px 20px -8px rgba(184, 134, 59, .5);
}
.ar-state .gold-btn:hover { filter: brightness(1.08); }
.ar-state .gold-btn:disabled { opacity: .55; cursor: not-allowed; }
.spin-ring {
  width: 30px; height: 30px; margin: 0 auto;
  border: 2px solid rgba(184, 134, 59, .25); border-top-color: #B8863B;
  border-radius: 50%; animation: arSpin .8s linear infinite;
}
@keyframes arSpin { to { transform: rotate(360deg); } }

/* 篇牍侧栏 */
.side-h {
  font-size: 10.5px; letter-spacing: .2em; color: #A0722F;
  margin-bottom: 10px; display: flex; align-items: center; gap: 6px;
}
.pick {
  border: 1px solid rgba(184, 134, 59, .3); border-radius: 12px;
  padding: 11px 12px; margin-bottom: 10px; background: rgba(184, 134, 59, .05);
}
.pick.reco {
  border-color: rgba(184, 134, 59, .65);
  background: linear-gradient(160deg, rgba(184, 134, 59, .14), rgba(184, 134, 59, .04));
}
.pick .ph { display: flex; align-items: baseline; gap: 7px; }
.pick .ph b { font-size: 12.5px; color: #2E2A22; font-weight: 700; }
.pick .ph span { font-size: 9.5px; color: #A08F6E; margin-left: auto; }
.pick p { font-size: 10.5px; line-height: 1.7; color: #847C63; margin-top: 4px; }
.pick .reco-tag {
  display: inline-block; margin-top: 7px; font-size: 9px; font-weight: 700;
  letter-spacing: .1em; color: #FDFAF3;
  background: linear-gradient(135deg, #C99A4B, #A0722F);
  padding: 2px 9px; border-radius: 99px;
}
.pick .rt {
  margin-top: 7px; font-size: 10px; color: #847C63;
  display: flex; align-items: center; gap: 5px;
}
.pick .rt svg { color: #B8863B; }
.side-note {
  margin-top: 12px; padding: 10px 11px; border-radius: 10px;
  border: 1px dashed rgba(184, 134, 59, .4);
  font-size: 10.5px; line-height: 1.8; color: #847C63;
}
.side-note b { color: #B8863B; }

/* ===== 篇牍视图 ===== */
.ar-viewbar {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 24px; border-bottom: 1px solid rgba(217, 162, 74, .18);
  animation: arRise .6s ease backwards;
}
.ar-viewbar .vb-tt { font-size: 13.5px; color: #F6EAD6; letter-spacing: .06em; }
.ar-viewbar .crumb { font-size: 10.5px; color: #8C7A5E; margin-left: auto; }
.backlink {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 11.5px; color: #B9A78A; background: none;
  border: 1px solid rgba(217, 162, 74, .3); border-radius: 99px;
  padding: 4px 12px; transition: .25s;
}
.backlink:hover { color: #E8B973; border-color: #D9A24A; }
.ar-lenwrap {
  flex: 1; padding: 20px 24px 24px; animation: arRise .7s ease .08s backwards;
  background:
    radial-gradient(rgba(46, 42, 34, .05) 1px, transparent 1.2px) 0 0 / 7px 7px,
    #FDFAF3;
  color: #55503F;
}
.len-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.len {
  border: 1px solid rgba(184, 134, 59, .35); border-radius: 16px; padding: 16px;
  background: #FDFAF3;
  cursor: pointer; transition: transform .35s, border-color .35s, box-shadow .35s;
  position: relative; text-align: left;
}
.len:hover {
  transform: translateY(-4px); border-color: rgba(184, 134, 59, .75);
  box-shadow: 0 18px 36px -18px rgba(46, 42, 34, .4), 0 0 18px rgba(184, 134, 59, .12);
}
.len.reco { border-color: rgba(184, 134, 59, .75); box-shadow: 0 0 22px rgba(184, 134, 59, .14); }
.len .seal {
  position: absolute; top: -9px; right: 12px;
  font-size: 9px; font-weight: 700; letter-spacing: .12em; color: #FDFAF3;
  background: linear-gradient(135deg, #C99A4B, #A0722F);
  padding: 3px 11px; border-radius: 99px;
}
.len .ic {
  width: 34px; height: 34px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  background: #F8F2E3; border: 1px solid rgba(184, 134, 59, .4);
  margin-bottom: 10px; color: #B8863B;
}
.len h5 { font-size: 14px; font-weight: 700; color: #2E2A22; }
.len .wc { font-size: 10px; color: #A08F6E; margin-top: 2px; }
.len p { font-size: 10.8px; line-height: 1.75; color: #847C63; margin-top: 8px; }
.len ul { list-style: none; margin-top: 9px; padding: 0; }
.len li {
  font-size: 10.3px; color: #55503F; display: flex; gap: 6px;
  align-items: flex-start; line-height: 1.7;
}
.len li svg { color: #5E8F5E; flex-shrink: 0; margin-top: 3px; }
.len .foot {
  margin-top: 11px; padding-top: 9px; border-top: 1px dashed rgba(184, 134, 59, .3);
  display: flex; justify-content: space-between; align-items: center;
  font-size: 10.5px; color: #847C63;
}
.len .foot b {
  color: #A0722F; font-size: 11px;
  display: inline-flex; align-items: center; gap: 4px;
}
.len-note {
  margin-top: 16px; text-align: center; font-size: 11px; color: #847C63;
}
.len-note b { color: #B8863B; }

/* ===== 响应式 ===== */
@media (max-width: 1020px) {
  .ar-main { grid-template-columns: 1fr; }
  .ar-side {
    border-left: none; border-top: 1px solid rgba(184, 134, 59, .28);
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
  }
  .side-h, .ar-side .side-note { grid-column: 1 / -1; }
  .ar-side .pick { margin-bottom: 0; }
}
@media (max-width: 760px) {
  .ar-cards { grid-template-columns: 1fr; }
  .len-grid { grid-template-columns: 1fr; }
  .ar-side { grid-template-columns: 1fr; }
  .star-crumbs { display: none; }
  .star-node .lb { display: none; }
  .star-node .nd { width: 24px; height: 24px; font-size: 9px; }
}
</style>
