<template>
  <div class="min-h-screen bg-morandi-bg/30 py-8 md:py-10">
    <div class="mx-auto max-w-5xl px-4 space-y-6">
      <!-- 顶部总览 -->
      <div class="bg-white rounded-3xl border border-morandi-soft/60 shadow-xl shadow-morandi-text/5 overflow-hidden">
        <div class="px-6 md:px-10 py-8 bg-gradient-to-br from-sky-50 to-morandi-bg border-b border-morandi-soft/40">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-12 h-12 rounded-2xl bg-white border border-morandi-soft/60 flex items-center justify-center text-lg font-bold">养</div>
            <div>
              <div class="text-xs font-semibold text-sky-700 mb-0.5">营养分析</div>
              <h1 class="text-2xl md:text-3xl font-bold text-morandi-text">{{ p.title || '近期营养摄入分析' }}</h1>
            </div>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mt-5">
            <TopStat label="热量" :value="p.totalCalories ?? '12,600'" unit="kcal" tone="rose" />
            <TopStat label="蛋白质" :value="p.protein ?? '560'" unit="g" tone="sky" />
            <TopStat label="脂肪" :value="p.fat ?? '380'" unit="g" tone="amber" />
            <TopStat label="碳水" :value="p.carbs ?? '1680'" unit="g" tone="violet" />
            <TopStat label="膳食纤维" :value="p.fiber ?? '182'" unit="g" tone="emerald" />
          </div>
        </div>
        <!-- 三大营养素圆环（纯 CSS） -->
        <div class="px-6 md:px-10 py-6">
          <h2 class="text-base font-bold text-morandi-text mb-4 flex items-center gap-2">
            <span class="w-1.5 h-5 rounded bg-morandi-accent inline-block" />三大营养素供能比
          </h2>
          <div class="flex flex-wrap items-center gap-6">
            <div class="relative w-40 h-40 shrink-0">
              <div class="absolute inset-0 rounded-full" :style="donutStyle"></div>
              <div class="absolute inset-3 rounded-full bg-white border border-morandi-soft/60 flex flex-col items-center justify-center">
                <div class="text-[11px] text-morandi-lightText">总供能</div>
                <div class="text-xl font-bold text-morandi-text">{{ p.totalCalories ?? '12,600' }}</div>
                <div class="text-[10px] text-morandi-lightText">kcal</div>
              </div>
            </div>
            <div class="space-y-2 text-sm">
              <Legend color="#f43f5e" label="蛋白质" :ratio="macro.protein" />
              <Legend color="#f59e0b" label="脂肪" :ratio="macro.fat" />
              <Legend color="#8b5cf6" label="碳水化合物" :ratio="macro.carbs" />
            </div>
          </div>
        </div>
      </div>

      <!-- 维生素矿物质 -->
      <section v-if="microItems && microItems.length" class="bg-white rounded-3xl border border-morandi-soft/60 p-6 md:p-8">
        <h2 class="text-base font-bold text-morandi-text mb-4 flex items-center gap-2">
          <span class="w-1.5 h-5 rounded bg-morandi-accent inline-block" />维生素 & 矿物质达标情况
        </h2>
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
          <div v-for="(m, i) in microItems" :key="i" class="p-4 rounded-2xl bg-morandi-bg/40 border border-morandi-soft/60">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-semibold text-morandi-text">{{ m.name }}</span>
              <span :class="['text-[11px] px-2 py-0.5 rounded-full', m.status === 'ok' ? 'bg-emerald-50 text-emerald-700' : (m.status === 'low' ? 'bg-amber-50 text-amber-700' : 'bg-rose-50 text-rose-700')]">
                {{ m.status === 'ok' ? '达标' : (m.status === 'low' ? '偏低' : '偏高') }}
              </span>
            </div>
            <div class="h-2 w-full rounded-full bg-morandi-soft/60 overflow-hidden">
              <div class="h-full rounded-full bg-morandi-accent transition-all" :style="{ width: Math.min(130, m.percent ?? 0) + '%' }" />
            </div>
            <div class="mt-1.5 text-[11px] text-morandi-lightText flex justify-between">
              <span>实际 {{ m.actual ?? '—' }}</span>
              <span>推荐 {{ m.target ?? '—' }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 建议 -->
      <section v-if="p.advice || p.suggestions" class="bg-white rounded-3xl border border-morandi-soft/60 p-6 md:p-8">
        <h2 class="text-base font-bold text-morandi-text mb-3">营养师建议</h2>
        <div v-if="Array.isArray(p.suggestions)" class="grid md:grid-cols-2 gap-3">
          <div v-for="(s, i) in p.suggestions" :key="i" class="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-sm text-emerald-900 leading-7">{{ s }}</div>
        </div>
        <p v-else class="text-sm text-morandi-text leading-7 whitespace-pre-wrap">{{ p.advice }}</p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h } from 'vue'
const props = defineProps<{ payload: any }>()
const p = computed(() => (props.payload || {}) as Record<string, any>)

const TopStat = defineComponent({
  props: ['label', 'value', 'unit', 'tone'],
  setup(ps: any) {
    const toneMap: Record<string, any> = {
      rose:    ['bg-rose-50',    'text-rose-700',    'border-rose-200'],
      sky:     ['bg-sky-50',     'text-sky-700',     'border-sky-200'],
      amber:   ['bg-amber-50',   'text-amber-700',   'border-amber-200'],
      violet:  ['bg-violet-50',  'text-violet-700',  'border-violet-200'],
      emerald: ['bg-emerald-50', 'text-emerald-700', 'border-emerald-200'],
    }
    const [bg, tc, bc] = toneMap[ps.tone] || toneMap.sky
    return () => h('div', { class: `p-4 rounded-2xl border ${bc} ${bg}` }, [
      h('div', { class: 'text-[11px] opacity-80 ' + tc }, ps.label),
      h('div', { class: 'mt-1 flex items-baseline gap-1' }, [
        h('div', { class: 'text-2xl font-bold ' + tc }, ps.value),
        h('div', { class: 'text-[11px] opacity-70' }, ps.unit),
      ]),
    ])
  }
})

const Legend = defineComponent({
  props: ['color', 'label', 'ratio'],
  setup(ps: any) {
    return () => h('div', { class: 'flex items-center gap-2' }, [
      h('span', { class: 'w-3 h-3 rounded-sm inline-block', style: { background: ps.color } }),
      h('span', { class: 'text-morandi-text w-24' }, ps.label),
      h('span', { class: 'font-semibold text-morandi-lightText' }, ps.ratio + '%'),
    ])
  }
})

const macro = computed(() => {
  if (p.value.macro) return p.value.macro
  if (p.value.macros) return p.value.macros
  return { protein: 25, fat: 25, carbs: 50 }
})
const donutStyle = computed(() => {
  // 蛋白质(红) 脂肪(琥珀) 碳水(紫)
  const { protein = 25, fat = 25, carbs = 50 } = macro.value
  const p = Number(protein), f = Number(fat), c = Number(carbs)
  const total = p + f + c || 100
  const a = (p / total) * 360
  const b = (f / total) * 360
  // conic-gradient 顺时针: rose → amber → violet
  return {
    background: `conic-gradient(#f43f5e 0deg ${a}deg, #f59e0b ${a}deg ${a + b}deg, #8b5cf6 ${a + b}deg 360deg)`
  }
})

type Micro = { name: string; actual?: string; target?: string; percent?: number; status?: 'ok'|'low'|'high' }
const microItems = computed<Micro[]>(() => {
  if (Array.isArray(p.value.micros)) return p.value.micros
  if (Array.isArray(p.value.microItems)) return p.value.microItems
  if (Array.isArray(p.value.vitamins)) return p.value.vitamins
  return [
    { name: '维生素 C', actual: '85 mg', target: '100 mg', percent: 85, status: 'ok' as const },
    { name: '维生素 D', actual: '6 μg', target: '10 μg', percent: 60, status: 'low' as const },
    { name: '钙',      actual: '720 mg', target: '800 mg', percent: 90, status: 'ok' as const },
    { name: '铁',      actual: '18 mg',  target: '15 mg',  percent: 120, status: 'ok' as const },
    { name: '钾',      actual: '1800 mg', target: '2000 mg', percent: 90, status: 'ok' as const },
    { name: '钠',      actual: '5800 mg', target: '2000 mg', percent: 290, status: 'high' as const },
  ]
})
</script>
