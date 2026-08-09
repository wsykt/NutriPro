<!-- 文章右侧跟随栏：篇幅切换器 + 文章目录（从 ArticleDetail.vue 拆分） -->
<template>
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
          @click="$emit('switch-len', t.key)"
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
          @click="$emit('jump', item.id)"
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
</template>

<script setup lang="ts">
import { Layers, List } from 'lucide-vue-next'
import { LEN_TABS } from '@/utils/articleRendering'
import type { LengthType } from '@/api/articleMock'

defineProps<{
  currentLen: LengthType
  toc: { id: string; text: string; level: number }[]
  activeId: string
}>()

defineEmits<{
  (e: 'switch-len', len: LengthType): void
  (e: 'jump', id: string): void
}>()
</script>
