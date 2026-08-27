<template>
  <div class="min-h-screen bg-morandi-bg/30 py-8 md:py-10">
    <div class="mx-auto max-w-5xl px-4 space-y-6">
      <!-- 顶卡 -->
      <div class="bg-white rounded-3xl border border-morandi-soft/60 shadow-xl shadow-morandi-text/5 p-6 md:p-8">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-12 h-12 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-lg font-bold text-amber-700">膳</div>
          <div>
            <div class="text-xs font-semibold text-amber-700 mb-0.5">个性化膳食计划</div>
            <h1 class="text-2xl md:text-3xl font-bold text-morandi-text">{{ p.title || '本周膳食计划' }}</h1>
          </div>
        </div>
        <div class="mt-4 grid md:grid-cols-4 gap-3">
          <Metric label="每日热量" :value="p.targetCalories ?? '1800'" unit="kcal" tone="amber" />
          <Metric label="蛋白质" :value="p.proteinRatio ?? '25%'" unit="供能比" tone="blue" />
          <Metric label="碳水" :value="p.carbsRatio ?? '50%'" unit="供能比" tone="violet" />
          <Metric label="脂肪" :value="p.fatRatio ?? '25%'" unit="供能比" tone="emerald" />
        </div>
        <div v-if="p.summary || p.principle" class="mt-5 p-4 rounded-2xl bg-morandi-bg/60 border border-morandi-soft/60 text-sm text-morandi-text leading-7 whitespace-pre-wrap">
          {{ p.summary || p.principle }}
        </div>
      </div>

      <!-- 7 天 x 3 餐 -->
      <div class="space-y-4">
        <div v-for="(d, di) in days" :key="di" class="bg-white rounded-2xl border border-morandi-soft/60 p-5">
          <div class="flex items-center justify-between mb-4">
            <div class="font-semibold text-morandi-text">{{ d.day }}</div>
            <div class="text-xs text-morandi-lightText">{{ d.totalKcal }}</div>
          </div>
          <div class="grid md:grid-cols-3 gap-3">
            <MealCell icon="" title="早餐" :items="d.breakfast" kcalLabel="早餐 kcal" />
            <MealCell icon="" title="午餐" :items="d.lunch" kcalLabel="午餐 kcal" />
            <MealCell icon="" title="晚餐" :items="d.dinner" kcalLabel="晚餐 kcal" />
          </div>
          <div v-if="d.snack || d.extra" class="mt-3">
            <div class="text-xs font-semibold text-morandi-lightText mb-1.5">加餐</div>
            <div class="flex flex-wrap gap-2">
              <span v-for="(s, i) in snackList(d)" :key="i" class="text-xs px-3 py-1.5 rounded-full bg-amber-50 border border-amber-200 text-amber-800">
                {{ s }}
              </span>
            </div>
          </div>
          <div v-if="d.tip" class="mt-3 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 leading-6">
            {{ d.tip }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h } from 'vue'
const props = defineProps<{ payload: any }>()
const p = computed(() => (props.payload || {}) as Record<string, any>)

const Metric = defineComponent({
  props: ['label', 'value', 'unit', 'tone'],
  setup(ps: any) {
    const toneMap: Record<string, any> = {
      amber:   ['bg-amber-50', 'text-amber-700', 'border-amber-200'],
      blue:    ['bg-sky-50',   'text-sky-700',   'border-sky-200'],
      violet:  ['bg-violet-50','text-violet-700','border-violet-200'],
      emerald: ['bg-emerald-50','text-emerald-700','border-emerald-200'],
    }
    const [bg, tc, bc] = toneMap[ps.tone] || toneMap.amber
    return () => h('div', { class: `p-4 rounded-2xl border ${bc} ${bg}` }, [
      h('div', { class: 'text-[11px] opacity-80 ' + tc }, ps.label),
      h('div', { class: 'mt-1 flex items-baseline gap-1' }, [
        h('div', { class: 'text-2xl font-bold ' + tc }, ps.value),
        h('div', { class: 'text-[11px] opacity-70' }, ps.unit),
      ]),
    ])
  }
})

const MealCell = defineComponent({
  props: ['icon', 'title', 'items', 'kcalLabel'],
  setup(ps: any) {
    const items: string[] = (Array.isArray(ps.items) ? ps.items : (ps.items ? [ps.items] : []))
    return () => h('div', { class: 'p-4 rounded-2xl bg-morandi-bg/40 border border-morandi-soft/60' }, [
      h('div', { class: 'flex items-center gap-2 mb-2' }, [
        ...(ps.icon ? [h('div', { class: 'text-lg' }, ps.icon)] : []),
        h('div', { class: 'text-sm font-semibold text-morandi-text' }, ps.title),
      ]),
      items.length
        ? h('ul', { class: 'space-y-1.5 text-sm text-morandi-text' },
            items.map((it: any, i: number) =>
              h('li', { key: i, class: 'leading-6' }, typeof it === 'string' ? it : (it.name + (it.amount ? ' · ' + it.amount : '')))
            )
          )
        : h('div', { class: 'text-xs text-morandi-lightText' }, '（未安排）'),
    ])
  }
})

type Day = {
  day: string
  totalKcal: string
  breakfast: any[]
  lunch: any[]
  dinner: any[]
  snack?: string[]
  tip?: string
}

const days = computed<Day[]>(() => {
  const raw = p.value.days || p.value.week || p.value.schedule
  if (Array.isArray(raw) && raw.length) {
    return raw.map((d: any, i: number) => normalizeDay(d, i))
  }
  // fallback：如果只有单个 dayPlan
  const fallback = Array.from({ length: 7 }).map((_, i) => normalizeDay({}, i))
  return fallback
})

function normalizeDay(d: any, i: number): Day {
  const names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const brk = (b: any) => (Array.isArray(b) ? b : (b ? [b] : []))
  const kcal = d.totalKcal ?? d.kcal ?? d.calories ?? d.energy ?? '≈ 1800 kcal'
  return {
    day: d.day || names[i] || ('Day ' + (i + 1)),
    totalKcal: typeof kcal === 'number' ? kcal + ' kcal' : String(kcal),
    breakfast: brk(d.breakfast || d.bf || d.morning),
    lunch: brk(d.lunch || d.noon),
    dinner: brk(d.dinner || d.supper || d.evening),
    snack: Array.isArray(d.snack) ? d.snack : d.snack ? [d.snack] : undefined,
    tip: d.tip || d.note
  }
}
function snackList(d: Day): string[] {
  if (Array.isArray(d.snack)) return d.snack
  const ex: any[] = []
  const e = (d as any).extra; if (Array.isArray(e)) ex.push(...e); else if (e) ex.push(e)
  return ex.map((x: any) => typeof x === 'string' ? x : (x.name + (x.amount ? ' · ' + x.amount : '')))
}
</script>
