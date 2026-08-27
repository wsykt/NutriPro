<template>
  <div class="min-h-screen bg-morandi-bg/30 py-8 md:py-10">
    <div class="mx-auto max-w-5xl px-4 space-y-6">
      <!-- 顶部卡片 -->
      <div class="bg-white rounded-3xl border border-morandi-soft/60 shadow-xl shadow-morandi-text/5 overflow-hidden">
        <div class="px-6 md:px-10 py-8 bg-gradient-to-br from-emerald-50 via-morandi-bg to-amber-50 border-b border-morandi-soft/40">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-12 h-12 rounded-2xl bg-white border border-morandi-soft/60 flex items-center justify-center text-lg font-bold">报</div>
            <div>
              <div class="text-xs font-semibold text-emerald-700 mb-0.5">AI 健康周报</div>
              <h1 class="text-2xl md:text-3xl font-bold text-morandi-text">{{ p.title || '本周健康报告' }}</h1>
            </div>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
            <Card v-for="(c, i) in headlineCards" :key="i" :data="c" />
          </div>
        </div>
        <div class="px-6 md:px-10 py-6 space-y-6">
          <section v-if="p.summary || p.overall">
            <h2 class="text-base font-bold text-morandi-text mb-3 flex items-center gap-2">
              <span class="w-1.5 h-5 rounded bg-morandi-accent inline-block" />整体评价
            </h2>
            <p class="text-sm text-morandi-text leading-7 whitespace-pre-wrap">{{ p.summary || p.overall }}</p>
          </section>
          <section v-if="p.highlights && p.highlights.length">
            <h2 class="text-base font-bold text-morandi-text mb-3">本周亮点</h2>
            <ul class="space-y-2">
              <li v-for="(h, i) in p.highlights" :key="i" class="flex gap-2 text-sm text-morandi-text">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2 shrink-0" />{{ h }}
              </li>
            </ul>
          </section>
          <section v-if="p.issues && p.issues.length">
            <h2 class="text-base font-bold text-morandi-text mb-3">需关注项目</h2>
            <ul class="space-y-2">
              <li v-for="(h, i) in p.issues" :key="i" class="flex gap-2 text-sm text-morandi-text">
                <span class="w-1.5 h-1.5 rounded-full bg-amber-500 mt-2 shrink-0" />{{ h }}
              </li>
            </ul>
          </section>
          <section v-if="p.suggestions && p.suggestions.length">
            <h2 class="text-base font-bold text-morandi-text mb-3">下周建议</h2>
            <div class="grid md:grid-cols-2 gap-3">
              <div v-for="(s, i) in p.suggestions" :key="i" class="p-4 rounded-2xl bg-morandi-bg/50 border border-morandi-soft/60 text-sm text-morandi-text leading-7">
                {{ s }}
              </div>
            </div>
          </section>
          <section v-if="p.nextAction">
            <h2 class="text-base font-bold text-morandi-text mb-3">下一步行动</h2>
            <div class="p-4 rounded-2xl bg-morandi-accent/8 border border-morandi-accent/30 text-sm text-morandi-text leading-7 whitespace-pre-wrap">
              {{ p.nextAction }}
            </div>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h } from 'vue'
const props = defineProps<{ payload: any }>()
const p = computed(() => (props.payload || {}) as Record<string, any>)

const Card = defineComponent({
  props: ['data'],
  setup(ps: any) {
    return () => h('div', { class: `p-4 rounded-2xl border ${ps.data.borderCls} ${ps.data.bgCls}` }, [
      h('div', { class: 'text-[11px] opacity-80' }, ps.data.label),
      h('div', { class: 'mt-1 flex items-baseline gap-1' }, [
        h('div', { class: 'text-2xl font-bold ' + (ps.data.textCls || '') }, ps.data.value),
        h('div', { class: 'text-[11px] opacity-70' }, ps.data.unit || ''),
      ]),
      ps.data.hint ? h('div', { class: 'text-[11px] opacity-70 mt-1' }, ps.data.hint) : null,
    ])
  }
})

const headlineCards = computed<any[]>(() => {
  const mk = (label: string, value: any, unit: string, tone: string, hint?: string) => {
    const toneMap: Record<string, any> = {
      green:  { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
      blue:   { bg: 'bg-sky-50',     text: 'text-sky-700',     border: 'border-sky-200' },
      amber:  { bg: 'bg-amber-50',   text: 'text-amber-700',   border: 'border-amber-200' },
      violet: { bg: 'bg-violet-50',  text: 'text-violet-700',  border: 'border-violet-200' }
    }[tone] || { bg: 'bg-morandi-bg', text: 'text-morandi-text', border: 'border-morandi-soft/60' }
    return { label, value, unit, hint, bgCls: toneMap.bg, textCls: toneMap.text, borderCls: toneMap.border }
  }
  if (p.value.headlineCards && Array.isArray(p.value.headlineCards)) return p.value.headlineCards
  return [
    mk('健康评分', p.value.score ?? 86, '/100', 'green', p.value.scoreDelta ? `较上周 ${p.value.scoreDelta}` : '较上周 +3'),
    mk('达标天数', p.value.goodDays ?? 5, '天', 'blue', '本周 7 天'),
    mk('总摄入热量', p.value.totalCalories ?? '13,200', 'kcal', 'amber'),
    mk('运动时长', p.value.exerciseMin ?? 210, '分钟', 'violet', '目标 ≥ 150 min'),
  ]
})
</script>
