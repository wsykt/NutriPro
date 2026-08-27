<template>
  <div class="min-h-screen bg-morandi-bg/30 py-8 md:py-10">
    <div class="mx-auto max-w-5xl px-4 space-y-6">
      <!-- 顶部概览 -->
      <div class="bg-white rounded-3xl border border-morandi-soft/60 shadow-xl shadow-morandi-text/5 p-6 md:p-8">
        <div class="flex items-start gap-4">
          <div class="w-14 h-14 rounded-2xl bg-morandi-accent/15 text-morandi-accent text-lg font-bold flex items-center justify-center">练</div>
          <div class="flex-1">
            <div class="text-xs font-semibold text-morandi-accent mb-1">个性化训练方案</div>
            <h1 class="text-2xl md:text-3xl font-bold text-morandi-text">{{ p.title || '我的专属训练方案' }}</h1>
            <div v-if="p.goal || p.crowdType || p.level" class="mt-3 flex flex-wrap gap-2">
              <Tag v-if="p.goal">{{ p.goal }}</Tag>
              <Tag v-if="p.crowdType">{{ p.crowdType }}</Tag>
              <Tag v-if="p.level">{{ p.level }}</Tag>
              <Tag v-if="p.durationPerSession">{{ p.durationPerSession }} / 次</Tag>
              <Tag v-if="p.frequency">每周 {{ p.frequency }} 次</Tag>
            </div>
          </div>
        </div>
        <div v-if="p.summary" class="mt-5 p-4 rounded-2xl bg-morandi-bg/60 border border-morandi-soft/60 text-sm text-morandi-text leading-7 whitespace-pre-wrap">
          {{ p.summary }}
        </div>
      </div>

      <!-- 7 天周计划卡片 -->
      <div class="grid md:grid-cols-2 gap-4">
        <div v-for="(d, idx) in weeklyPlan" :key="idx"
          class="bg-white rounded-2xl border border-morandi-soft/60 p-5 shadow-sm hover:shadow-md transition">
          <div class="flex items-center justify-between mb-3">
            <div class="font-semibold text-morandi-text">{{ d.day || ('Day ' + (idx + 1)) }}</div>
            <span :class="['text-[11px] px-2 py-0.5 rounded-full', d.rest ? 'bg-morandi-gray text-morandi-lightText' : 'bg-morandi-accent/15 text-morandi-accent']">
              {{ d.rest ? '休息日' : (d.theme || (d.exercises?.length ? '训练日' : '轻活动')) }}
            </span>
          </div>
          <div v-if="d.rest || !d.exercises?.length" class="text-sm text-morandi-lightText leading-7 p-4 rounded-xl bg-morandi-bg/50">
            {{ d.tip || '充分恢复，保持睡眠与营养。' }}
          </div>
          <ul v-else class="space-y-2.5">
            <li v-for="(ex, i) in d.exercises" :key="i" class="flex items-start gap-3 p-3 rounded-xl bg-morandi-bg/40 border border-morandi-soft/50">
              <div class="shrink-0 w-8 h-8 rounded-lg bg-white border border-morandi-soft/60 flex items-center justify-center text-lg">
                {{ ex.icon || defaultIcon(ex.name) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-semibold text-morandi-text">{{ ex.name || ('动作 ' + (i+1)) }}</div>
                <div class="text-xs text-morandi-lightText mt-0.5">
                  <span v-if="ex.sets">{{ ex.sets }}组 × </span>
                  <span v-if="ex.reps">{{ ex.reps }}次</span>
                  <span v-else-if="ex.duration">{{ ex.duration }}</span>
                  <span v-if="ex.rest" class="ml-2">· 休息 {{ ex.rest }}</span>
                </div>
                <div v-if="ex.tip" class="text-xs text-morandi-lightText mt-1 leading-5">{{ ex.tip }}</div>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <!-- 通用热身/冷身/注意事项 -->
      <div v-if="p.warmUp || p.coolDown || p.tips" class="bg-white rounded-3xl border border-morandi-soft/60 p-6 md:p-8 space-y-5">
        <section v-if="p.warmUp">
          <h3 class="text-sm font-bold text-morandi-text mb-2">热身安排</h3>
          <p class="text-sm text-morandi-text leading-7 whitespace-pre-wrap">{{ p.warmUp }}</p>
        </section>
        <section v-if="p.coolDown">
          <h3 class="text-sm font-bold text-morandi-text mb-2">冷身拉伸</h3>
          <p class="text-sm text-morandi-text leading-7 whitespace-pre-wrap">{{ p.coolDown }}</p>
        </section>
        <section v-if="p.tips">
          <h3 class="text-sm font-bold text-morandi-text mb-2">注意事项</h3>
          <p class="text-sm text-morandi-text leading-7 whitespace-pre-wrap">{{ p.tips }}</p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h } from 'vue'
const props = defineProps<{ payload: any }>()
const p = computed(() => (props.payload || {}) as Record<string, any>)

const Tag = defineComponent({
  setup(_, { slots }) {
    return () => h('span', { class: 'inline-flex items-center text-xs px-2.5 py-1 rounded-full bg-morandi-bg border border-morandi-soft/60 text-morandi-lightText' }, slots.default?.())
  }
})

function defaultIcon(name: string) {
  const n = String(name || '')
  if (/跑|跑|walk|jog|sprint|hiit|cardio/i.test(n)) return ''
  if (/蹲|leg|squat|lunge/i.test(n)) return ''
  if (/推|pushup|bench|chest|press/i.test(n)) return ''
  if (/拉|pull|row|deadlift|back/i.test(n)) return ''
  if (/核心|plank|crunch|core|abs|腹/i.test(n)) return ''
  if (/拉|伸|stretch|yoga|瑜伽/i.test(n)) return ''
  return ''
}

const weeklyPlan = computed<any[]>(() => {
  const raw = p.value.weeklyPlan || p.value.plan || p.value.schedule || p.value.days
  if (Array.isArray(raw) && raw.length) return raw
  // fallback：7 天空模板 + 部分覆盖
  const fallback: any[] = Array.from({ length: 7 }).map((_, i) => ({
    day: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][i],
    rest: (i === 6),
    theme: i === 6 ? '休息日' : '训练日',
    exercises: [] as any[]
  }))
  // 如果 payload 里是 exercises[]（平铺数组），摊到前 4 天
  const flat = p.value.exercises
  if (Array.isArray(flat)) {
    const per = Math.max(1, Math.ceil(flat.length / 5))
    for (let d = 0; d < 5; d++) fallback[d].exercises = flat.slice(d * per, (d + 1) * per)
    for (let d = 0; d < 5; d++) fallback[d].theme = ['上肢推', '下肢', '上肢拉', '核心/有氧', '全身循环'][d]
  }
  return fallback
})
</script>
