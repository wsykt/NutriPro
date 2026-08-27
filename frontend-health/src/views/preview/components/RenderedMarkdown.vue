<template>
  <!-- 极简 markdown-like 纯文本渲染：h1/h2/h3、列表、粗体、引用、段落。
       故意不引外部 markdown 库，保持"预览即权威组件最终观感 1:1" 且不引入额外构建依赖。 -->
  <div class="rendered-md">
    <template v-for="(blk, idx) in blocks" :key="idx">
      <h1 v-if="blk.type==='h1'" class="text-xl font-bold text-morandi-text mt-6 mb-3 pb-2 border-b border-morandi-soft/60">
        <Inliner :text="blk.text" />
      </h1>
      <h2 v-else-if="blk.type==='h2'" class="text-lg font-bold text-morandi-text mt-6 mb-3 flex items-center gap-2">
        <span class="w-1.5 h-5 rounded bg-morandi-accent inline-block" />
        <Inliner :text="blk.text" />
      </h2>
      <h3 v-else-if="blk.type==='h3'" class="text-base font-semibold text-morandi-text mt-5 mb-2">
        <Inliner :text="blk.text" />
      </h3>
      <ul v-else-if="blk.type==='ul'" class="list-disc pl-6 space-y-1.5 my-3 text-[15px]">
        <li v-for="(li, i) in blk.items" :key="i"><Inliner :text="li" /></li>
      </ul>
      <ol v-else-if="blk.type==='ol'" class="list-decimal pl-6 space-y-1.5 my-3 text-[15px]">
        <li v-for="(li, i) in blk.items" :key="i"><Inliner :text="li" /></li>
      </ol>
      <blockquote v-else-if="blk.type==='quote'" class="my-4 border-l-4 border-morandi-accent/50 bg-morandi-bg/60 rounded-r-xl px-4 py-3 text-morandi-lightText italic">
        <Inliner :text="blk.text" />
      </blockquote>
      <div v-else-if="blk.type==='hr'" class="my-6 border-t border-morandi-soft/60" />
      <p v-else class="my-3 leading-8 whitespace-pre-wrap"><Inliner :text="blk.text" /></p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'

const props = defineProps<{ text: string }>()

type Block = { type: 'h1'|'h2'|'h3'|'ul'|'ol'|'quote'|'p'|'hr'; text?: string; items?: string[] }

const blocks = computed<Block[]>(() => {
  const lines = String(props.text || '').replace(/\r\n/g, '\n').split('\n')
  const out: Block[] = []
  let i = 0
  let pBuf: string[] = []
  const flushP = () => {
    if (pBuf.length) { out.push({ type: 'p', text: pBuf.join('\n').trim() }); pBuf = [] }
  }
  while (i < lines.length) {
    const line = lines[i]
    if (/^\s*---+\s*$/.test(line)) { flushP(); out.push({ type: 'hr' }); i++; continue }
    if (/^\s*>\s?/.test(line)) {
      flushP()
      const txts: string[] = []
      while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
        txts.push(lines[i].replace(/^\s*>\s?/, ''))
        i++
      }
      out.push({ type: 'quote', text: txts.join(' ') })
      continue
    }
    const h1 = line.match(/^#\s+(.*)$/)
    if (h1) { flushP(); out.push({ type: 'h1', text: h1[1] }); i++; continue }
    const h2 = line.match(/^##\s+(.*)$/)
    if (h2) { flushP(); out.push({ type: 'h2', text: h2[1] }); i++; continue }
    const h3 = line.match(/^###\s+(.*)$/)
    if (h3) { flushP(); out.push({ type: 'h3', text: h3[1] }); i++; continue }
    const ul = line.match(/^\s*[-*+]\s+(.*)$/)
    if (ul) {
      flushP()
      const items: string[] = []
      while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*+]\s+/, ''))
        i++
      }
      out.push({ type: 'ul', items })
      continue
    }
    const ol = line.match(/^\s*\d+\.\s+(.*)$/)
    if (ol) {
      flushP()
      const items: string[] = []
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ''))
        i++
      }
      out.push({ type: 'ol', items })
      continue
    }
    if (/^\s*$/.test(line)) { flushP(); i++ }
    else { pBuf.push(line); i++ }
  }
  flushP()
  return out
})

// 行内粗体 / 斜体 / 行内 code
const Inliner = (p: { text: string }) => {
  const raw = p.text || ''
  const parts: any[] = []
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g
  let last = 0, m: RegExpExecArray | null
  while ((m = re.exec(raw)) !== null) {
    if (m.index > last) parts.push(raw.slice(last, m.index))
    const token = m[0]
    if (token.startsWith('**')) parts.push(h('strong', { class: 'font-bold text-morandi-text' }, token.slice(2, -2)))
    else if (token.startsWith('`')) parts.push(h('code', { class: 'px-1.5 py-0.5 mx-0.5 rounded bg-morandi-bg text-morandi-accent text-[13px] border border-morandi-soft/60' }, token.slice(1, -1)))
    else parts.push(h('em', { class: 'italic text-morandi-text/90' }, token.slice(1, -1)))
    last = m.index + token.length
  }
  if (last < raw.length) parts.push(raw.slice(last))
  return h('span', null, parts)
}
</script>
