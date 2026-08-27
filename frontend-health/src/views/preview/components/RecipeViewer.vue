<template>
  <div class="min-h-screen bg-morandi-bg/30 py-8 md:py-10">
    <div class="mx-auto max-w-4xl px-4">
      <!-- ============ 单食谱形态（flat：recipeName + ingredients + steps） ============ -->
      <div v-if="!mealPlan.length" class="bg-white rounded-3xl border border-morandi-soft/60 shadow-xl shadow-morandi-text/5 overflow-hidden">
        <!-- 封面 -->
        <div class="h-52 md:h-64 relative bg-gradient-to-br from-morandi-accent/20 via-amber-100/50 to-morandi-bg">
          <div class="absolute inset-0 flex items-end px-6 md:px-10 pb-6">
            <div class="ml-4">
              <div class="text-xs font-semibold text-morandi-accent mb-1">AI 食谱推荐</div>
              <h1 class="text-2xl md:text-3xl font-bold text-morandi-text">{{ r.recipeName || r.title || '未命名食谱' }}</h1>
            </div>
          </div>
        </div>
        <!-- 头部 info -->
        <div class="px-6 md:px-10 pt-6">
          <p v-if="r.description" class="text-morandi-text leading-7">{{ r.description }}</p>
          <div class="mt-4 grid grid-cols-2 md:grid-cols-5 gap-3">
            <Stat label="热量" :value="(r.calories ?? '—')" unit="kcal" color="bg-rose-50 text-rose-700" />
            <Stat label="蛋白质" :value="(r.protein ?? '—')" unit="g" color="bg-sky-50 text-sky-700" />
            <Stat label="脂肪" :value="(r.fat ?? '—')" unit="g" color="bg-amber-50 text-amber-700" />
            <Stat label="碳水" :value="(r.carbs ?? '—')" unit="g" color="bg-violet-50 text-violet-700" />
            <Stat label="膳食纤维" :value="(r.fiber ?? '—')" unit="g" color="bg-emerald-50 text-emerald-700" />
          </div>
          <div v-if="r.personaTag || r.tags" class="mt-4 flex flex-wrap gap-2">
            <span v-for="(t, i) in tags" :key="i" class="text-xs px-2.5 py-1 rounded-full bg-morandi-bg text-morandi-lightText border border-morandi-soft/60">
              # {{ t }}
            </span>
          </div>
        </div>
        <!-- 食材 -->
        <section v-if="ingredients && ingredients.length" class="px-6 md:px-10 mt-8">
          <h2 class="text-base font-bold text-morandi-text mb-4 flex items-center gap-2">
            <span class="w-1.5 h-5 rounded bg-morandi-accent inline-block" />食材清单
          </h2>
          <div class="grid md:grid-cols-2 gap-3">
            <div v-for="(ing, i) in ingredients" :key="i" class="flex items-center justify-between px-4 py-3 rounded-2xl border border-morandi-soft/60 bg-morandi-bg/30">
              <span class="text-sm text-morandi-text">{{ ing.name }}</span>
              <span class="text-xs text-morandi-lightText">{{ ing.amount }}</span>
            </div>
          </div>
        </section>
        <!-- 步骤 -->
        <section v-if="steps && steps.length" class="px-6 md:px-10 mt-8 mb-10">
          <h2 class="text-base font-bold text-morandi-text mb-4 flex items-center gap-2">
            <span class="w-1.5 h-5 rounded bg-morandi-accent inline-block" />做法步骤
          </h2>
          <ol class="space-y-3">
            <li v-for="(s, i) in steps" :key="i" class="flex gap-3">
              <div class="shrink-0 w-7 h-7 rounded-full bg-morandi-accent/15 text-morandi-accent font-bold text-sm flex items-center justify-center">{{ i + 1 }}</div>
              <div class="flex-1 px-4 py-3 rounded-2xl border border-morandi-soft/60 bg-white text-morandi-text text-sm leading-7 whitespace-pre-wrap">
                {{ s }}
              </div>
            </li>
          </ol>
        </section>
        <!-- 营养点评 -->
        <section v-if="r.nutritionSummary" class="px-6 md:px-10 mb-10">
          <div class="rounded-2xl bg-emerald-50 border border-emerald-200 p-5">
            <div class="text-xs font-semibold text-emerald-700 mb-2">营养师点评</div>
            <p class="text-sm text-emerald-900 leading-7 whitespace-pre-wrap">{{ r.nutritionSummary }}</p>
          </div>
        </section>
      </div>

      <!-- ============ AI 三餐膳食形态（meal_plan：早餐/午餐/晚餐 + 汇总） ============ -->
      <div v-else class="bg-white rounded-3xl border border-morandi-soft/60 shadow-xl shadow-morandi-text/5 overflow-hidden">
        <!-- 封面 -->
        <div class="h-52 md:h-64 relative bg-gradient-to-br from-morandi-accent/20 via-amber-100/50 to-morandi-bg">
          <div class="absolute inset-0 flex items-end px-6 md:px-10 pb-6">
            <div class="ml-4">
              <div class="text-xs font-semibold text-morandi-accent mb-1">AI 三餐食谱推荐</div>
              <h1 class="text-2xl md:text-3xl font-bold text-morandi-text">{{ r.recipeName || r.title || 'AI 食谱推荐' }}</h1>
            </div>
          </div>
        </div>
        <!-- 汇总指标 -->
        <div class="px-6 md:px-10 pt-6">
          <p v-if="r.description" class="text-morandi-text leading-7">{{ r.description }}</p>
          <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat label="总热量" :value="(r.totalCalories ?? totalCaloriesSum)" unit="kcal" color="bg-rose-50 text-rose-700" />
            <Stat label="总蛋白质" :value="(r.totalProtein ?? totalProteinSum)" unit="g" color="bg-sky-50 text-sky-700" />
            <Stat label="餐次" :value="mealPlan.length" unit="餐" color="bg-violet-50 text-violet-700" />
            <Stat label="模式" :value="(r.modeLabel || '标准')" unit="" color="bg-emerald-50 text-emerald-700" />
          </div>
        </div>
        <!-- 三餐卡片 -->
        <div class="px-6 md:px-10 mt-8 space-y-4 pb-4">
          <div v-for="(m, i) in mealPlan" :key="i" class="rounded-2xl border border-morandi-soft/60 bg-morandi-bg/30 p-5">
            <div class="flex items-center justify-between flex-wrap gap-2 mb-3">
              <div class="flex items-center gap-3">
                <span class="text-xs font-semibold px-2.5 py-1 rounded-full bg-morandi-accent/15 text-morandi-accent">{{ m.meal_type || ('餐 ' + (i + 1)) }}</span>
                <div class="font-bold text-morandi-text">{{ m.name }}</div>
              </div>
              <div class="flex gap-2 text-xs text-morandi-lightText">
                <span v-if="m.calories_estimate != null">{{ m.calories_estimate }} kcal</span>
                <span v-if="m.protein_estimate != null">蛋白 {{ m.protein_estimate }}g</span>
              </div>
            </div>
            <div v-if="m.ingredients && m.ingredients.length" class="flex flex-wrap gap-2 mb-3">
              <span v-for="(ig, j) in m.ingredients" :key="j"
                    class="text-xs px-3 py-1.5 rounded-full bg-white border border-morandi-soft/60 text-morandi-text">
                {{ ig.name || ig }}{{ ig.amount ? ' ' + ig.amount : '' }}
              </span>
            </div>
            <p v-if="m.cook_method || m.steps" class="text-sm text-morandi-text leading-7 whitespace-pre-wrap">
              {{ m.cook_method || (Array.isArray(m.steps) ? m.steps.join('\n') : m.steps) }}
            </p>
            <div v-if="m.tags && m.tags.length" class="mt-2 flex flex-wrap gap-2">
              <span v-for="(t, k) in m.tags" :key="k" class="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800">
                # {{ t }}
              </span>
            </div>
          </div>
        </div>
        <!-- 营养师点评 -->
        <section v-if="tipsText" class="px-6 md:px-10 mb-10 mt-2">
          <div class="rounded-2xl bg-emerald-50 border border-emerald-200 p-5">
            <div class="text-xs font-semibold text-emerald-700 mb-2">营养师点评</div>
            <p class="text-sm text-emerald-900 leading-7 whitespace-pre-wrap">{{ tipsText }}</p>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h } from 'vue'
const props = defineProps<{ payload: any }>()
const r = computed(() => (props.payload || {}) as Record<string, any>)

const Stat = defineComponent({
  props: ['label', 'value', 'unit', 'color'],
  setup(ps: any) {
    return () => h('div', { class: `px-4 py-3 rounded-2xl border border-morandi-soft/60 ${ps.color}` }, [
      h('div', { class: 'text-[11px] opacity-70' }, ps.label),
      h('div', { class: 'mt-1 flex items-baseline gap-1' }, [
        h('div', { class: 'text-lg font-bold' }, ps.value),
        h('div', { class: 'text-[11px] opacity-80' }, ps.unit),
      ]),
    ])
  }
})

const tags = computed<string[]>(() => {
  const src: string[] = []
  if (r.value.personaTag) src.push(r.value.personaTag)
  const t = r.value.tags
  if (t) {
    if (Array.isArray(t)) src.push(...t)
    else src.push(...String(t).split(/[,，#\s]+/).filter(Boolean))
  }
  return Array.from(new Set(src))
})

const ingredients = computed<{ name: string; amount: string }[]>(() => {
  const raw = r.value.ingredients
  if (!raw) return []
  if (Array.isArray(raw)) return raw.map((x: any) => typeof x === 'string' ? parseIngStr(x) : { name: x.name || x.title || String(x), amount: x.amount || x.quantity || '' })
  return String(raw).split(/\n/).filter(Boolean).map(parseIngStr)
})
function parseIngStr(s: string): { name: string; amount: string } {
  // "鸡蛋 2 个 / 鸡胸肉 200g / 菠菜：1 把"
  const cleaned = s.replace(/^[-*+0-9.、\s]+/, '')
  const m = cleaned.match(/^(.*?)([:：/／\s]{1,})(\d.*)?$/)
  if (!m) return { name: cleaned, amount: '' }
  return { name: (m[1] || '').trim() || cleaned, amount: (m[3] || '').trim() || (m[2] + '').trim() }
}

const steps = computed<string[]>(() => {
  const raw = r.value.steps
  if (!raw) return []
  if (Array.isArray(raw)) return raw.map((x: any) => typeof x === 'string' ? x : (x.text || x.content || x.step || String(x)))
  return String(raw).split(/\n/).map((s: string) => s.replace(/^\s*\d+\.\s*/, '').replace(/^[-*+]\s*/, '')).filter(Boolean)
})

// ============ AI 三餐膳食形态（meal_plan） ============
const mealPlan = computed<any[]>(() => {
  const mp = r.value.meal_plan || r.value.mealPlan
  if (!mp) return []
  if (Array.isArray(mp)) return mp
  return []
})
const totalCaloriesSum = computed(() => {
  let sum = 0
  for (const m of mealPlan.value) {
    const c = Number(m.calories_estimate ?? m.calories ?? 0)
    if (!Number.isNaN(c)) sum += c
  }
  return sum || '—'
})
const totalProteinSum = computed(() => {
  let sum = 0
  for (const m of mealPlan.value) {
    const p = Number(m.protein_estimate ?? m.protein ?? 0)
    if (!Number.isNaN(p)) sum += p
  }
  return sum || '—'
})
const tipsText = computed<string>(() => {
  const t = r.value.tips
  if (!t) return r.value.nutritionSummary || ''
  if (Array.isArray(t)) return t.join('\n')
  return String(t)
})
</script>
