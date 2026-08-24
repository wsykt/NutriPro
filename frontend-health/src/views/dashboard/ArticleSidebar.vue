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

    <!-- 跟随式目录（一级可展开/收起，避免目录过长） -->
    <div v-if="groups.length" class="bg-white rounded-2xl border border-morandi-soft/60 shadow-sm p-4">
      <div class="text-xs font-semibold text-morandi-lightText uppercase tracking-wider mb-3 flex items-center gap-1.5">
        <List class="w-3.5 h-3.5 text-morandi-accent" />
        文章目录
      </div>
      <nav class="space-y-0.5">
        <div v-for="g in groups" :key="g.id" class="space-y-0.5">
          <!-- 一级目录：点击文字跳转，点击箭头展开/收起 -->
          <div
            class="flex items-center gap-1.5 rounded-lg transition-all duration-200 border-l-2"
            :class="activeId === g.id
              ? 'bg-morandi-accent/10 border-morandi-accent'
              : 'border-transparent hover:bg-morandi-gray'"
          >
            <button
              class="shrink-0 w-6 h-6 flex items-center justify-center rounded text-morandi-lightText hover:text-morandi-accent"
              :title="collapsedIds[g.id] ? '展开' : '收起'"
              @click.stop="toggleGroup(g.id)"
            >
              <ChevronDown class="w-4 h-4 transition-transform" :class="collapsedIds[g.id] ? '-rotate-90' : ''" />
            </button>
            <button
              class="flex-1 min-w-0 px-1 py-2 text-sm font-medium text-left truncate"
              :class="activeId === g.id ? 'text-morandi-accent' : 'text-morandi-lightText'"
              @click="jump(g.id)"
            >
              {{ g.text }}
            </button>
          </div>
          <!-- 二级目录：随一级展开/收起 -->
          <template v-if="g.children.length && !collapsedIds[g.id]">
            <button
              v-for="c in g.children"
              :key="c.id"
              @click="jump(c.id)"
              :class="[
                'w-full text-left transition-all duration-200 rounded-lg flex items-center gap-2 pl-8 pr-3 py-1.5 text-[13px] truncate',
                activeId === c.id
                  ? 'bg-morandi-accent/10 text-morandi-accent border-l-2 border-morandi-accent'
                  : 'text-morandi-lightText hover:bg-morandi-gray hover:text-morandi-text border-l-2 border-transparent'
              ]"
            >
              <span class="truncate">{{ c.text }}</span>
            </button>
          </template>
        </div>
      </nav>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Layers, List, ChevronDown } from 'lucide-vue-next'
import { LEN_TABS } from '@/utils/articleRendering'
import type { LengthType } from '@/api/articleMock'

const props = defineProps<{
  currentLen: LengthType
  toc: { id: string; text: string; level: number }[]
  activeId: string
}>()

const emit = defineEmits<{
  (e: 'switch-len', len: LengthType): void
  (e: 'jump', id: string): void
}>()

// 把扁平 toc 按一级标题分组：level 1 为组头，其后紧跟的 level 2 为子项
const groups = computed(() => {
  const out: { id: string; text: string; children: { id: string; text: string }[] }[] = []
  for (const item of props.toc) {
    if (item.level === 1) {
      out.push({ id: item.id, text: item.text, children: [] })
    } else {
      const last = out[out.length - 1]
      if (last) last.children.push({ id: item.id, text: item.text })
    }
  }
  return out
})

// 收起状态（默认全部展开，仅记录手动折叠的一级标题 id）
const collapsedIds = ref<Record<string, boolean>>({})
function toggleGroup(id: string) {
  collapsedIds.value = { ...collapsedIds.value, [id]: !collapsedIds.value[id] }
}
function jump(id: string) {
  emit('jump', id)
}
</script>
