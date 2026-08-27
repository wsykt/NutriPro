<template>
  <div class="min-h-screen bg-morandi-bg/30 py-8 md:py-10">
    <div class="mx-auto max-w-4xl px-4">
      <div class="bg-white rounded-3xl border border-morandi-soft/60 shadow-xl shadow-morandi-text/5 overflow-hidden">
        <!-- 顶部 -->
        <div class="px-6 md:px-10 py-6 border-b border-morandi-soft/40 bg-gradient-to-r from-morandi-accent/10 to-amber-50">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-2xl bg-white border border-morandi-soft/60 flex items-center justify-center text-lg font-bold">AI</div>
            <div class="flex-1">
              <div class="text-xs font-semibold text-morandi-accent mb-1">AI 健康咨询 · 对话快照</div>
              <h1 class="text-xl md:text-2xl font-bold text-morandi-text">{{ p.title || p.topic || '健康咨询会话' }}</h1>
            </div>
          </div>
          <div v-if="p.summary" class="mt-4 p-4 rounded-2xl bg-white/70 border border-morandi-soft/60 text-sm text-morandi-text leading-7 whitespace-pre-wrap">
            {{ p.summary }}
          </div>
        </div>
        <!-- 对话 -->
        <div class="px-4 md:px-8 py-6 space-y-4">
          <div v-for="(m, i) in messages" :key="i" :class="['flex gap-3', m.role === 'user' ? 'justify-end' : 'justify-start']">
            <div v-if="m.role !== 'user'" class="shrink-0 w-9 h-9 rounded-full bg-morandi-accent/15 text-morandi-accent text-lg flex items-center justify-center">AI</div>
            <div :class="['max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-7 whitespace-pre-wrap shadow-sm',
              m.role === 'user'
                ? 'bg-morandi-accent text-white rounded-br-md'
                : 'bg-white border border-morandi-soft/60 text-morandi-text rounded-bl-md']">
              {{ m.content }}
            </div>
            <div v-if="m.role === 'user'" class="shrink-0 w-9 h-9 rounded-full bg-morandi-text/10 text-morandi-text text-lg flex items-center justify-center">我</div>
          </div>
          <div v-if="!messages.length" class="py-20 text-center text-morandi-lightText text-sm">该快照未附带对话内容。</div>
        </div>
        <!-- 诊断/建议 -->
        <div v-if="p.advice || p.suggestion || p.conclusion" class="px-6 md:px-10 pb-8">
          <div class="rounded-2xl bg-amber-50 border border-amber-200 p-5">
            <div class="text-xs font-semibold text-amber-700 mb-2">AI 结论与建议</div>
            <p class="text-sm text-amber-900 leading-7 whitespace-pre-wrap">
              {{ p.advice || p.suggestion || p.conclusion }}
            </p>
            <div v-if="p.disclaimer" class="mt-3 pt-3 border-t border-amber-200/60 text-[11px] text-amber-700/80">
              {{ p.disclaimer }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ payload: any }>()
const p = computed(() => (props.payload || {}) as Record<string, any>)

type Msg = { role: 'user' | 'ai' | 'assistant' | 'system'; content: string }
const messages = computed<Msg[]>(() => {
  const raw = p.value.messages || p.value.chat || p.value.dialogue
  if (Array.isArray(raw)) {
    return raw.map((x: any) => ({
      role: (x.role === 'assistant' ? 'ai' : x.role) || 'ai',
      content: x.content || x.text || x.message || String(x)
    })).filter((m: Msg) => m.role !== 'system')
  }
  // fallback：如果 payload 是 { question, answer }
  const q = p.value.question || p.value.userInput
  const a = p.value.answer || p.value.response || p.value.reply
  const list: Msg[] = []
  if (q) list.push({ role: 'user', content: q })
  if (a) list.push({ role: 'ai', content: a })
  return list
})
</script>
