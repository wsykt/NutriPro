/**
 * 文章渲染工具集（从 ArticleDetail.vue 拆分）
 * 纯函数，无状态，供文章详情页复用
 */
import type { Component } from 'vue'
import { Zap, FlaskConical, GraduationCap } from 'lucide-vue-next'
import type { LengthType } from '@/api/articleMock'

// ===== 篇幅配置 =====
export const LEN_BADGE: Record<string, string> = {
  short: 'bg-sky-50 text-sky-700 border-sky-200',
  medium: 'bg-morandi-accent/10 text-morandi-accent border-morandi-accent/30',
  long: 'bg-violet-50 text-violet-700 border-violet-200'
}
export const LEN_TABS: { key: LengthType; label: string; icon: Component }[] = [
  { key: 'short', label: '速读卡', icon: Zap },
  { key: 'medium', label: '深度文', icon: FlaskConical },
  { key: 'long', label: '综述文', icon: GraduationCap }
]
const LEN_ICON: Record<LengthType, Component> = {
  short: Zap, medium: FlaskConical, long: GraduationCap
}
export function lenIcon(k: LengthType) { return LEN_ICON[k] }

// ===== 学术术语词典 =====
export const GLOSSARY: Record<string, { def: string; alias?: string }> = {
  '脂肪酸': { def: '构成脂肪的基本单位，分为饱和、单不饱和、多不饱和三类，对健康影响不同。' },
  '饱和脂肪酸': { def: '碳链上没有双键的脂肪酸，主要存在于动物脂肪和热带植物油中，摄入过多会升高血脂。', alias: 'SFA' },
  '单不饱和脂肪酸': { def: '含一个双键的脂肪酸，以油酸为代表，橄榄油、茶籽油中含量丰富，有助于心血管健康。', alias: 'MUFA' },
  '多不饱和脂肪酸': { def: '含两个及以上双键的脂肪酸，包括 Omega-3 和 Omega-6，人体不能自行合成。', alias: 'PUFA' },
  'Omega-3': { def: '一类多不饱和脂肪酸，主要包括 EPA、DHA、ALA，深海鱼和亚麻籽中含量高，有抗炎和心血管保护作用。' },
  'EPA': { def: '二十碳五烯酸，Omega-3 家族成员，主要来源于深海鱼，有抗炎和降甘油三酯作用。' },
  'DHA': { def: '二十二碳六烯酸，Omega-3 家族成员，对大脑和视网膜发育至关重要。' },
  '低密度脂蛋白胆固醇': { def: '俗称"坏胆固醇"，水平过高会导致血管斑块沉积，是心血管疾病的重要危险指标。', alias: 'LDL-C' },
  '高密度脂蛋白胆固醇': { def: '俗称"好胆固醇"，有助于将胆固醇从外周组织运回肝脏代谢，水平高有益心血管。', alias: 'HDL-C' },
  '甘油三酯': { def: '血液中主要的脂肪形式，水平过高是心血管疾病和胰腺炎的危险因素。', alias: 'TG' },
  '反式脂肪酸': { def: '不饱和脂肪酸的异构体，主要来自工业氢化植物油，心血管危害最大。', alias: 'TFA' },
  '动脉粥样硬化': { def: '脂质在动脉壁沉积形成斑块，导致血管狭窄、弹性下降，是冠心病和脑梗死的病理基础。' },
  '随机对照试验': { def: '最高级别的临床证据类型，通过随机分组对照评估干预效果，结果最可靠。', alias: 'RCT' },
  'Meta分析': { def: '对多个独立研究结果进行统计学合并分析的方法，能提高结论的统计效力和可靠性。' },
  '地中海饮食': { def: '以蔬果、全谷、橄榄油、鱼类为主的传统饮食模式，被多项研究证实可降低心血管风险。' },
  '胰岛素抵抗': { def: '细胞对胰岛素敏感性下降，是2型糖尿病和代谢综合征的核心病理机制。' },
  '血糖生成指数': { def: '衡量食物引起血糖升高程度的指标，GI值越高，对血糖影响越大。', alias: 'GI' },
  '基础代谢率': { def: '人体在静息状态下维持基本生命活动所需的最低能量消耗。', alias: 'BMR' },
  '体质量指数': { def: '体重（kg）除以身高（m）的平方，用于评估体重是否正常的常用指标。', alias: 'BMI' },
  '膳食纤维': { def: '人体不能消化吸收的植物性成分，可促进肠道蠕动、调节血糖和血脂。' },
  '抗氧化剂': { def: '能清除体内自由基、减轻氧化损伤的物质，如维生素C、E、多酚类等。' },
  '益生菌': { def: '对宿主有益的活性微生物，可调节肠道菌群平衡，常见于酸奶、发酵食品。' },
  '叶酸': { def: 'B族维生素之一，对胎儿神经管发育和红细胞生成至关重要，孕期需重点补充。' },
  '钙': { def: '人体含量最多的矿物质，99%存在于骨骼和牙齿中，对骨骼健康和神经肌肉功能至关重要。' },
  '铁': { def: '合成血红蛋白的必需微量元素，缺乏会导致缺铁性贫血，女性和儿童更易缺乏。' },
  '维生素D': { def: '脂溶性维生素，促进钙吸收和骨骼健康，阳光照射是主要来源之一。' }
}

// 按长度降序排列，避免短词先匹配
export const GLOSSARY_KEYS = Object.keys(GLOSSARY).sort((a, b) => b.length - a.length)

// ===== Markdown 渲染 =====
export function renderMarkdown(md: string): string {
  if (!md) return ''
  let html = md

  // 转义 HTML
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  // 代码块
  html = html.replace(/```([\s\S]*?)```/g, (_, code) =>
    `<pre class="code-block"><code>${code.trim()}</code></pre>`)

  // 表格
  html = html.replace(/^\|(.+)\|\n\|([-:\s|]+)\|\n((?:\|.+\|\n?)*)/gm, (_, header, _sep, body) => {
    const heads = header.split('|').map((h: string) => h.trim()).filter(Boolean)
    const rows = body.trim().split('\n').map((r: string) =>
      r.split('|').map((c: string) => c.trim()).filter(Boolean))
    const thead = `<thead><tr>${heads.map((h: string) => `<th>${h}</th>`).join('')}</tr></thead>`
    const tbody = `<tbody>${rows.map((r: string[]) =>
      `<tr>${r.map((c: string) => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody>`
    return `<div class="table-wrap"><table>${thead}${tbody}</table></div>`
  })

  // ===== 模板标记残留清理（必须最先）：模型将 build_mother_format 提示词中的占位说明行原样写入正文 → 清洗
  // 历史问题实锤（数据库文章73-76）：如"通用引言（2~3句话）：点明健身人士人群核心痛点+1条流行病学数据"、
  // "共识基础内容（400~900字，参考约600字）：…"、"一级标题：一、…；二级标题：（一）…"、
  // "深度拓展（600~1350字，参考约900字）：…"、"深度文结论：内容总结+核心膳食建议" 等

  // 1) 整行删除：纯占位说明行（其后正文才是真实内容，标题无内容价值）
  //    注意：行级正则一律用 [ \t] 与 [^\n] 限定，避免 \s* 跨行吞掉正文
  const TEMPLATE_LABEL_PATTERNS = [
    /^[ \t]*通用引言[ \t]*(?:（[^\n）]*）)?[ \t]*[:：][^\n]*$/gm,
    /^[ \t]*共识基础内容[ \t]*(?:（[^\n）]*）)?[ \t]*[:：][^\n]*$/gm,
    /^[ \t]*板块标题单独一行[^\n]*$/gm,
    /^[ \t]*(?:速读卡摘要|深度文摘要|综述摘要)[ \t]*(?:（[^\n）]*）)?[ \t]*[:：][^\n]*$/gm
  ]
  for (const p of TEMPLATE_LABEL_PATTERNS) {
    html = html.replace(p, '')
  }

  // 2) 板块说明行 → 规范化为独立 ## 标题（让结论/深度拓展/学术争议成为独立卡片，而非并入上一板块）
  const SECTION_HEADING_RULES: { pattern: RegExp; heading: string }[] = [
    // 结论类：速读卡结论/深度文结论/综述结论 → ## 结论
    { pattern: /^[ \t]*(?:速读卡结论|深度文结论|综述结论|核心结论|研究结论|总结)[ \t]*(?:（[^\n）]*）)?[ \t]*[:：][^\n]*$/gm, heading: '结论' },
    { pattern: /^[ \t]*细分场景深度拓展[ \t]*(?:（[^\n）]*）)?[ \t]*[:：][^\n]*$/gm, heading: '细分场景深度拓展' },
    { pattern: /^[ \t]*深度拓展[ \t]*(?:（[^\n）]*）)?[ \t]*[:：][^\n]*$/gm, heading: '深度拓展' },
    { pattern: /^[ \t]*学术争议[ \t]*(?:（[^\n）]*）)?[ \t]*[:：][^\n]*$/gm, heading: '学术争议' },
    { pattern: /^[ \t]*参考文献[ \t]*[0-9]*~?[0-9]*条?[ \t]*[:：][^\n]*$/gm, heading: '参考文献' }
  ]
  for (const rule of SECTION_HEADING_RULES) {
    html = html.replace(rule.pattern, `\n## ${rule.heading}\n`)
  }

  // 3) 一级标题说明行：从"一级标题：一、增肌期蛋白质摄入的重要性；二级标题：（一）…"中
  //    提取真实一级标题，恢复被模板说明行吞掉的章节结构
  //    「一级标题：一、二、三」纯编号序列（无实义标题）→ 整行删除
  html = html.replace(
    /^[ \t]*一级标题[ \t]*[:：][ \t]*([一二三四五六七八九十百]+、[^\n；;]*?)[ \t]*(?:[；;][^\n；;]*)?$/gm,
    (_, h2Text) => {
      const t = h2Text.trim()
      const rest = t.replace(/^[一二三四五六七八九十百]+、/, '').trim()
      if (!rest || /^[一二三四五六七八九十百]+、/.test(rest)) return '' // 纯编号序列
      return `\n## ${t}\n`
    }
  )

  // 3.5) 兜底删除：多分号「一级标题：一、A；二、B；三、C」说明行（正文已含真实标题）→ 整行删除
  html = html.replace(/^[ \t]*一级标题[ \t]*[:：][ \t]*[^\n]*$/gm, '')

  // 4) 裸标题残留兜底（无括号无冒号的裸行）：标题行"通用引言"（正文已作为导读卡片展示）、
  //    "共识基础内容"（只是板块组名，非内容标题）→ 直接删除
  const TEMPLATE_LABEL_LINES = ['通用引言', '共识基础内容']
  for (const lbl of TEMPLATE_LABEL_LINES) {
    const escaped = lbl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    html = html.replace(new RegExp(`^[ \\t]*${escaped}[ \\t]*$`, 'gm'), '')
  }

  // ===== 板块型裸标题预处理（必须放在 MD 标题转换之前）：学术争议/结论/深度拓展/特殊人群等单独成行 → 转成 ## 标题 =====
  const STANDALONE_SECTIONS = ['学术争议', '核心结论', '研究结论', '结论', '总结与展望', '总结', '参考文献', '引言', '摘要', '深度拓展', '细分场景深度拓展', '细分场景', '特殊人群']
  for (const sec of STANDALONE_SECTIONS) {
    const escaped = sec.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const pattern = new RegExp(`^([ \\t]*)(${escaped})([ \\t]*)$`, 'gm')
    html = html.replace(pattern, `\n## $2\n`)  // 转成 md 二级标题，下面的 ## 正则会接
  }

  // ===== 深度拓展板块子标题降级 =====
  // 「深度拓展」与其后裸板块（学术争议/结论等）之间的一级编号章节（一、特殊人群 / 二、细分场景深度拓展）
  // → 降为二级编号（（一）（二）），使它们作为「深度拓展」卡片的子章节合并展示：
  //   ① 深度拓展成为独立卡片（不再残留到上一卡片「通用行动清单」尾部）
  //   ② 消除与前面共识板块「一、…」「二、…」的编号冲突（TOC 不再出现重复的一/二）
  html = html.replace(/(##\s*深度拓展[^\n]*\n)([\s\S]*?)(?=\n##\s|$)/, (whole, head, inner) => {
    const degraded = inner
      .replace(/^###[ \t]*([一二三四五六七八九十百]+)、(.*)$/gm, '### （$1）$2')
      .replace(/^([一二三四五六七八九十百]+)、(.*)$/gm, '（$1）$2')
    return head + degraded
  })

  // 标题（带 ID 用于 TOC 跳转）
  // 「### 一、xxx」：科普文章一级章节（模型偶用三级标题书写）→ 提升为 h2 独立成卡
  html = html.replace(/^###\s+([一二三四五六七八九十百]+、.+)$/gm, (_, text) => {
    const id = 'h-' + text.replace(/[^\w\u4e00-\u9fa5]/g, '').slice(0, 20)
    return `<h2 id="${id}" class="scroll-mt-24">${text}</h2>`
  })
  html = html.replace(/^###\s+(.+)$/gm, (_, text) => {
    const id = 'h-' + text.replace(/[^\w\u4e00-\u9fa5]/g, '').slice(0, 20)
    return `<h3 id="${id}" class="scroll-mt-24">${text}</h3>`
  })
  // 「#### xxx」：模型偶用四级标题 → 统一转 h3（进 TOC 且有样式）
  html = html.replace(/^####\s+(.+)$/gm, (_, text) => {
    const id = 'h-' + text.replace(/[^\w\u4e00-\u9fa5]/g, '').slice(0, 20)
    return `<h3 id="${id}" class="scroll-mt-24">${text}</h3>`
  })
  html = html.replace(/^##\s+(.+)$/gm, (_, text) => {
    const id = 'h-' + text.replace(/[^\w\u4e00-\u9fa5]/g, '').slice(0, 20)
    return `<h2 id="${id}" class="scroll-mt-24">${text}</h2>`
  })
  html = html.replace(/^#\s+(.+)$/gm, (_, text) => `<h1>${text}</h1>`)

  // 中文编号标题（科普文章规范：一级"一、"，二级"（一）"）→ 转 h2/h3，支持 TOC 与卡片化
  // 注意："（一）最佳补充方式：目前存在两种观点..."  这整行原文标题内容后直接跟正文（用"："连接）
  //     → h3 里只取冒号/句号前作为标题文字，冒号后内容保留为同段 p 文本，避免整段加粗变标题
  html = html.replace(/^（([一二三四五六七八九十百]+)）(.+)$/gm, (_, _n, text) => {
    // 找第一个 冒号、句号、问号。把前面当标题，后面当正文
    const m = text.match(/^(.+?)([：:。？?!！])(.*)$/s)
    let titleText: string, bodyRest: string
    if (m) {
      titleText = m[1].trim()  // 如 "最佳补充方式"
      bodyRest = (m[3]).trim()  // 只保留标点"之后"的真正文，不把 ：。？等作为开头（标题和正文断开后连接符已无意义）
    } else {
      titleText = text.trim()
      bodyRest = ''
    }
    const id = 'h-' + titleText.replace(/[^\w\u4e00-\u9fa5]/g, '').slice(0, 20)
    const h3 = `<h3 id="${id}" class="scroll-mt-24">${titleText}</h3>`
    return bodyRest ? `${h3}\n\n${bodyRest}` : h3
  })
  html = html.replace(/^([一二三四五六七八九十百]+)、(.+)$/gm, (_, _n, text) => {
    // h2 同理做冒号截断
    const m = text.match(/^(.+?)([：:。？?!！])(.*)$/s)
    let titleText: string, bodyRest: string
    if (m) {
      titleText = m[1].trim()
      bodyRest = (m[3]).trim()  // 吞掉连接符 ：。？！
    } else {
      titleText = text.trim()
      bodyRest = ''
    }
    const id = 'h-' + titleText.replace(/[^\w\u4e00-\u9fa5]/g, '').slice(0, 20)
    const h2 = `<h2 id="${id}" class="scroll-mt-24">${titleText}</h2>`
    return bodyRest ? `${h2}\n\n${bodyRest}` : h2
  })

  // 引用块
  html = html.replace(/^&gt;\s(.+)$/gm, '<blockquote>$1</blockquote>')

  // 列表
  html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
  html = html.replace(/^[-*]\s+(.+)$/gm, '<li class="ul-item">$1</li>')
  html = html.replace(/(<li[^>]*>.*<\/li>\n?)+/g, (m) => {
    if (m.includes('ul-item')) {
      return '<ul>' + m.replace(/ class="ul-item"/g, '') + '</ul>'
    }
    return '<ol>' + m + '</ol>'
  })

  // 粗体和斜体
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')

  // 段落：先强制在块级元素前后插入 \n\n 分隔符，避免 <p> 非法嵌套 <h2>/<h3>/<blockquote> 等
  // （场景：中文编号标题截断后的正文可能与 h3 同行或仅 \n 相隔，导致 split('\n\n') 不拆开）
  html = html
    .replace(/(<(h[1-3]|ul|ol|pre|blockquote|div|table)[^>]*>)/g, '\n\n$1')
    .replace(/(<\/(h[1-3]|ul|ol|pre|blockquote|div|table)>)/g, '$1\n\n')
    // 清理连续 3+ 换行 -> 只保留 2 个
    .replace(/\n{3,}/g, '\n\n');

  html = html.split('\n\n').map(block => {
    if (block.match(/^<(h[1-3]|ul|ol|pre|blockquote|div|table)/)) return block
    if (block.trim() === '') return ''
    return `<p>${block.replace(/\n/g, '<br>')}</p>`
  }).join('\n')

  return html
}

// ===== 术语自动链接 + 引用角标 =====
export function linkTermsAndRefs(html: string): string {
  // 1. 将 [1] [2] 或 （1）（2）等引用标记转为可点击角标
  html = html.replace(/[\[［]\s*(\d+)\s*[\]］]/g, (_, n) => {
    return `<sup class="cite-badge" data-ref="${n}" onclick="document.getElementById('ref-${n}')?.scrollIntoView({behavior:'smooth',block:'center'})">[${n}]</sup>`
  })

  // 2. 用 DOM 扫描文本节点，包裹 GLOSSARY 术语（每篇内容仅标记术语首次出现）
  const firstOccurrence = new Set<string>()
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = html
  walkAndWrapTerms(tempDiv, firstOccurrence)
  return tempDiv.innerHTML
}

function walkAndWrapTerms(node: Node, firstOccurrence: Set<string>) {
  const children = Array.from(node.childNodes)
  for (const child of children) {
    if (child.nodeType === Node.TEXT_NODE) {
      const text = child.textContent || ''
      if (text.length < 2) continue
      const parentTag = (child.parentElement?.tagName || '').toLowerCase()
      if (['script', 'style', 'code', 'pre', 'sup', 'a'].includes(parentTag)) continue

      let replaced = text
      const replacements: { term: string; html: string; placeholder: string }[] = []

      // 否定/限制前缀保护：术语前紧邻「不」「非」等限制词时，整个复合词不打标，
      // 避免子串误命中。例如「不饱和脂肪酸」不能命中「饱和脂肪酸」词条。
      // 仅当「不/非」+术语不构成更长 GLOSSARY 术语时才保护，
      // 从而不影响「多不饱和脂肪酸」等合法词条。
      // 如需扩展前缀（如「无」「反」），在 NEG_PREFIX 中追加即可。
      const NEG_PREFIX = '不非'
      const negGuard = new Map<string, string>()
      let negIdx = 0
      const negPattern = new RegExp(`[${NEG_PREFIX}](${GLOSSARY_KEYS.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'g')
      const negHits: { index: number; length: number; full: string }[] = []
      let negMatch: RegExpExecArray | null
      while ((negMatch = negPattern.exec(replaced)) !== null) {
        const full = negMatch[0]
        const idx = negMatch.index
        const prev = idx > 0 ? replaced[idx - 1] : ''
        // 前缀+复合词若构成更长术语（如 多+不饱和脂肪酸=多不饱和脂肪酸），不保护
        if (prev && GLOSSARY_KEYS.some(k => k === prev + full)) continue
        negHits.push({ index: idx, length: full.length, full })
      }
      // 从后往前替换，避免索引偏移
      for (let i = negHits.length - 1; i >= 0; i--) {
        const h = negHits[i]
        const ph = `\x00NEG${negIdx++}\x00`
        negGuard.set(ph, h.full)
        replaced = replaced.slice(0, h.index) + ph + replaced.slice(h.index + h.length)
      }

      for (const term of GLOSSARY_KEYS) {
        // 已经标记过首次出现的术语，跳过
        if (firstOccurrence.has(term)) continue
        if (!replaced.includes(term)) continue

        const entry = GLOSSARY[term]
        // 匹配两种形式："术语（alias）" 或纯 "术语"
        const escapedTerm = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        // 如果有 alias，优先匹配已经带 alias 括号的完整形式
        const pattern = entry.alias
          ? new RegExp(`${escapedTerm}（${entry.alias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}）|${escapedTerm}`)
          : new RegExp(escapedTerm)
        const match = replaced.match(pattern)
        if (!match) continue

        const matchedText = match[0]
        const placeholder = `\x00TERM${replacements.length}\x00`
        const replacementHtml = `<span class="term-mark" data-term="${term}">${matchedText}</span>`
        replaced = replaced.replace(pattern, placeholder)
        replacements.push({ term, html: replacementHtml, placeholder })
        firstOccurrence.add(term)
      }

      if (replacements.length > 0 || negGuard.size > 0) {
        replacements.forEach(r => {
          replaced = replaced.replace(r.placeholder, r.html)
        })
        negGuard.forEach((full, ph) => {
          replaced = replaced.replace(ph, full)
        })
        const span = document.createElement('span')
        span.innerHTML = replaced
        node.replaceChild(span, child)
      }
    } else if (child.nodeType === Node.ELEMENT_NODE) {
      const tag = (child as HTMLElement).tagName.toLowerCase()
      if (!['script', 'style', 'code', 'pre', 'sup'].includes(tag)) {
        walkAndWrapTerms(child, firstOccurrence)
      }
    }
  }
}
