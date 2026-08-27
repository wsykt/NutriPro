<template>
  <div class="min-h-screen bg-morandi-bg/30">
    <div class="mx-auto max-w-[1200px] px-4 py-8 md:py-10">
      <div class="flex gap-8">
        <!-- ============ 主文章区 ============ -->
        <div class="flex-1 min-w-0">
          <article class="bg-white rounded-3xl border border-morandi-soft/60 shadow-xl shadow-morandi-text/5 overflow-hidden">
            <!-- 头部信息区 -->
            <header class="px-6 md:px-10 pt-8 md:pt-10 pb-6 border-b border-morandi-soft/40">
              <div class="flex flex-wrap items-center gap-2 mb-4">
                <span :class="['inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border', lenColor(len)]">
                  {{ lenLabel(len) }}
                </span>
                <span class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-morandi-gray text-morandi-lightText border border-morandi-soft/60">
                  {{ a.category || '综合营养' }}
                </span>
                <span v-if="a.audience" class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-morandi-accent/10 text-morandi-accent border border-morandi-accent/30">
                  {{ a.audience }}
                </span>
                <span v-if="a.qualityScore" class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  质量分 {{ a.qualityScore }}
                </span>
                <span class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
                  ≈{{ wordCount }}字
                </span>
              </div>
              <h1 class="text-2xl md:text-3xl font-bold text-morandi-text leading-snug mb-4">
                {{ a.title }}
              </h1>
              <div class="flex flex-wrap items-center gap-4 text-xs text-morandi-lightText">
                <span class="inline-flex items-center gap-1.5">
                  <span class="w-5 h-5 rounded-full bg-morandi-accent/20 text-morandi-accent text-[10px] font-bold flex items-center justify-center">{{ (a.authorName || 'AI').slice(0,1) }}</span>
                  {{ a.authorName || 'AI健康助手' }}
                </span>
                <span>{{ a.createdAt || today }}</span>
                <span v-if="a.topic" class="px-2 py-0.5 rounded bg-morandi-bg border border-morandi-soft/60">
                  #{{ a.topic }}
                </span>
                <span class="inline-flex items-center gap-1">{{ a.viewsCount ?? 0 }}</span>
                <span class="inline-flex items-center gap-1">{{ a.likesCount ?? 0 }}</span>
              </div>
            </header>

            <!-- 摘要区 -->
            <section v-if="summaryText" class="px-6 md:px-10 py-6 border-b border-morandi-soft/40 bg-morandi-bg/30">
              <div class="text-xs font-semibold text-morandi-accent mb-2">一句话摘要</div>
              <p class="text-sm md:text-base text-morandi-text leading-7 whitespace-pre-wrap">
                {{ summaryText }}
              </p>
            </section>

            <!-- 正文 markdown-like 渲染（保留 # / - / ** 等纯文本结构，与 ArticleDetail 权威组件相同的排版） -->
            <section class="px-6 md:px-10 py-8 md:py-10 markdown-body text-morandi-text leading-8 text-[15px]">
              <RenderedMarkdown :text="bodyText" />
            </section>

            <!-- 参考文献 -->
            <section v-if="sources && sources.length" class="px-6 md:px-10 py-6 border-t border-morandi-soft/40 bg-amber-50/30">
              <div class="text-xs font-semibold text-amber-700 mb-3">参考文献</div>
              <ul class="space-y-2">
                <li v-for="(s, i) in sources" :key="i" class="text-xs text-morandi-lightText leading-6 pl-5 -indent-5">
                  <span class="inline-block w-4 text-morandi-accent mr-1 font-bold">[{{ i + 1 }}]</span>{{ s }}
                </li>
              </ul>
            </section>

            <!-- 标签 -->
            <section v-if="tagList && tagList.length" class="px-6 md:px-10 py-5 border-t border-morandi-soft/40 flex flex-wrap gap-2">
              <span v-for="(t, i) in tagList" :key="i" class="text-xs px-2.5 py-1 rounded-full bg-morandi-soft/40 text-morandi-lightText border border-morandi-soft/60">
                # {{ t }}
              </span>
            </section>
          </article>
        </div>

        <!-- ============ 侧栏：篇幅切换（mock 只读） ============ -->
        <aside class="w-72 shrink-0 hidden lg:block">
          <div class="bg-white rounded-3xl border border-morandi-soft/60 p-5 sticky top-8">
            <div class="text-xs text-morandi-lightText mb-3 font-semibold">篇幅切换</div>
            <div class="space-y-2">
              <div v-for="(tab, k) in lenTabs" :key="k"
                :class="['p-3 rounded-2xl border text-xs transition', len===k ? 'bg-morandi-accent/10 border-morandi-accent/40 text-morandi-accent' : 'border-morandi-soft/60 text-morandi-lightText']">
                <div class="font-semibold">{{ tab.label }} · {{ tab.approx }}</div>
                <div class="mt-1 opacity-70">{{ tab.desc }}</div>
              </div>
            </div>
            <div class="mt-5 pt-5 border-t border-morandi-soft/40 text-[11px] text-morandi-lightText leading-6">
              预览态仅作视觉校验。点击管理员页面的【喜欢+发布】后，
              <span v-if="funcType==='article'">文章会被真正写入「文章管理」并设置为已发布。</span>
              <span v-else>快照会被打"已发布"标记（演示阶段暂不写主业务表）。</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import RenderedMarkdown from './RenderedMarkdown.vue'

interface Props {
  payload: any
  funcType?: string
}
const props = defineProps<Props>()

type L = 'short' | 'medium' | 'long'
const len = ref<L>((props.payload?.lengthType as L) || 'medium')
const today = new Date().toISOString().slice(0, 10)

const a = computed(() => (props.payload || {}) as Record<string, any>)

const lenLabel = (l: L) => ({ short: '速读卡', medium: '深度文', long: '综述文' }[l])
const lenColor = (l: L) => ({
  short: 'bg-sky-50 text-sky-700 border-sky-200',
  medium: 'bg-morandi-accent/10 text-morandi-accent border-morandi-accent/30',
  long: 'bg-violet-50 text-violet-700 border-violet-200'
}[l])
const lenTabs = {
  short: { label: '速读卡', approx: '≈300字', desc: '1分钟速览核心要点' },
  medium: { label: '深度文', approx: '≈1500字', desc: '循证论证 + 实操方案' },
  long: { label: '综述文', approx: '≈2500字', desc: '含学术争议 + 前沿' }
} as Record<L, { label: string; approx: string; desc: string }>

const summaryText = computed(() => {
  const pick = { short: a.value.summaryShort, medium: a.value.summaryMedium, long: a.value.summaryLong } as Record<L, string | undefined>
  return pick[len.value] || a.value.summary || ''
})

const bodyText = computed(() => {
  const pick = { short: a.value.contentShort, medium: a.value.contentMedium, long: a.value.contentLong } as Record<L, string | undefined>
  return pick[len.value] || a.value.content || a.value.contentMedium || '（暂无正文）'
})

const wordCount = computed(() => a.value.wordCount ?? (String(bodyText.value || '').replace(/\s/g, '').length))

const sources = computed<string[]>(() => {
  const raw = a.value.sourcesJson
  if (!raw) return []
  if (Array.isArray(raw)) return raw
  if (typeof raw === 'string') {
    try {
      const p = JSON.parse(raw)
      return Array.isArray(p) ? p : [raw]
    } catch {
      return [raw]
    }
  }
  return []
})

const tagList = computed<string[]>(() => {
  const raw = a.value.tags
  if (!raw) return []
  if (Array.isArray(raw)) return raw
  return String(raw).split(/[,，#\s]+/).filter(Boolean)
})
</script>
