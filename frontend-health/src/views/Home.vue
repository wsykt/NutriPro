<template>
  <div class="c-root min-h-screen overflow-x-hidden relative">
    <!-- 顶部滚动进度条（琥珀渐变，仅首屏可见） -->
    <div class="c-scroll-progress" :style="{ width: scrollProgress + '%' }"></div>

    <!-- 全局 ambient 背景动画层（贯穿整页的细微粒子 + 脉冲） -->
    <div class="c-ambient-layer" aria-hidden="true">
      <div class="c-ambient-particles" ref="ambientParticlesRef"></div>
      <div class="c-ambient-pulse" ref="ambientPulseRef"></div>
      <div class="c-ambient-nebula c-ambient-nebula--1" ref="ambientNeb1Ref"></div>
      <div class="c-ambient-nebula c-ambient-nebula--2" ref="ambientNeb2Ref"></div>
    </div>

    <!-- ================ 顶部导航 · 刊期式 ================ -->
    <header class="c-nav">
      <div class="c-nav-inner">
        <a @click.prevent="scrollTo('top')" class="c-brand cursor-pointer">
          <span class="c-brand-name c-brand-name--video">
            <span class="c-brand-video-mask">
              <span class="c-brand-fallback" aria-hidden="true">NutriPro</span>
              <video class="c-brand-video" autoplay muted loop playsinline preload="auto">
                <source src="https://videos.pexels.com/video-files/5866263/5866263-hd_1280_720_25fps.mp4" type="video/mp4" />
              </video>
            </span>
          </span>
        </a>
        <nav class="c-links hidden md:flex">
          <a @click.prevent="scrollTo('features')" class="cursor-pointer">系统能力</a>
          <a @click.prevent="scrollTo('pillars')" class="cursor-pointer">为什么选择我们</a>
          <a @click.prevent="scrollTo('about')" class="cursor-pointer">关于系统</a>
        </nav>
      </div>
    </header>

    <main id="top" class="relative z-10">
      <!-- ================ HERO · M 方案（视频背景 + 视频填充标题 + 3D错位描边） ================ -->
      <section class="c-hero" ref="heroRef">
        <video class="c-hero-video" src="/assets/微信视频2026-08-27_212847_840.mp4" autoplay muted loop playsinline preload="auto"></video>
        <div class="c-hero-overlay" aria-hidden="true"></div>

        <div class="c-hero-inner">
          <p class="c-hero-eyebrow c-reveal">
            个人健康，是一份长期写作的底稿
          </p>
          <div class="c-hero-vt" ref="heroVtRef" role="img" aria-label="NutriPro">
            <div class="c-vt-inner" ref="heroVtInnerRef">
              <div class="c-vt-mask" ref="heroVtMaskRef">
                <video src="/assets/视频1.mp4" autoplay muted loop playsinline preload="auto"></video>
              </div>
              <!-- 3D 错位描边层由 JS 注入 -->
            </div>
          </div>
          <div class="c-cta-row c-hero-cta c-reveal">
            <router-link to="/login" class="c-cta c-cta-primary">
              登录体验
              <span class="c-cta-arrow">→</span>
            </router-link>
            <router-link to="/register" class="c-cta c-cta-ghost">
              免费注册
            </router-link>
          </div>
        </div>
        <!-- 底部向下滚动提示 -->
        <div class="c-hero-scroll-hint" aria-hidden="true">
          <span>向下滚动</span>
          <svg width="14" height="22" viewBox="0 0 14 22" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="7" y1="1" x2="7" y2="18"/>
            <polyline points="2,14 7,20 12,14"/>
          </svg>
        </div>
      </section>

      <!-- ================ Section 00 · 项目简介（原 Hero 内容降级 · 方案 D 组合式） ================ -->
      <section id="intro" class="c-intro" ref="introSectionRef">
        <div class="c-section-bg" aria-hidden="true">
          <div class="c-section-particles" ref="introParticlesRef"></div>
          <div class="c-section-pulse" ref="introPulseRef"></div>
          <div class="c-intro-nebula c-intro-nebula--1" ref="introNeb1Ref"></div>
          <div class="c-intro-nebula c-intro-nebula--2" ref="introNeb2Ref"></div>
        </div>
        <div class="c-intro-inner">
          <div class="c-intro-top c-intro-anim">
            <div class="c-intro-left">
              <p class="c-eyebrow"><span class="c-eyebrow-bar"></span>个人健康，是一份长期写作的底稿</p>
              <h2 class="c-intro-title">
                <span>记录</span>
                <span class="c-intro-title-accent">追踪 · 洞察</span>
              </h2>
              <div class="c-intro-stats">
                <div class="c-intro-stat">
                  <b data-count="3" data-suffix="">0</b>
                  <span>核心模块</span>
                </div>
                <div class="c-intro-stat">
                  <b data-count="365" data-suffix="">0</b>
                  <span>天连续回溯</span>
                </div>
                <div class="c-intro-stat">
                  <b data-count="100" data-suffix="%">0%</b>
                  <span>档案属于你</span>
                </div>
              </div>
            </div>
            <div class="c-intro-right">
              <p class="c-lead">
                专属于你的个人健康日志。记录三餐饮食、运动状态、日常节奏，留存血压、血糖等身体数据；依托档案沉淀，由 AI 生成个性化健康建议。以干净舒展的排版节奏，还给健康一份从容可读的体验。
              </p>
              <p class="c-sub">
                从体重到体检报告，从家庭长辈的远程监护到 AI 的个性化建议，所有维度被收敛进同一本可翻阅的档案。系统不是在替你"管理数据"，而是帮你书写一份年复一年、可以回溯、可以提醒、可以对比的健康底稿。
              </p>
            </div>
          </div>
          <div class="c-intro-rows c-intro-anim">
            <div v-for="r in introRows" :key="r.no" class="c-intro-row">
              <span class="c-intro-row-no">{{ r.no }}</span>
              <span class="c-intro-row-word">{{ r.word }}</span>
              <p class="c-intro-row-desc">{{ r.desc }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 分割齿线 -->
      <div class="c-rule"><span></span></div>

      <!-- ================ Section 01 · 系统核心特辑 ================ -->
      <section id="features" class="c-section c-section-features scroll-mt-24" ref="featuresSectionRef">
        <div class="c-section-bg" aria-hidden="true">
          <div class="c-section-particles" ref="featuresParticlesRef"></div>
          <div class="c-section-pulse" ref="featuresPulseRef"></div>
        </div>
        <header class="c-section-head">
          <div>
            <p class="c-section-kicker">Section · 01</p>
            <h2 class="c-section-title">系统核心特辑</h2>
          </div>
          <div class="c-section-meta">
            <div>04 Feature Cells</div>
            <div class="c-dot"></div>
            <div>Hover · Lift &amp; Glow</div>
          </div>
        </header>

        <!-- 2 列 × 2 行 Feature tiles -->
        <div class="c-tile-grid">
          <article v-for="(f, i) in features.slice(0, 4)" :key="'f-'+i"
                   class="c-tile c-tile-feature c-reveal"
                   :style="{ background: f.bg, transitionDelay: (i * 60) + 'ms' }">
            <img v-if="f.image" class="c-tile-img" :src="f.image" :alt="f.title" loading="lazy" />
            <div class="c-tile-no">Feature&nbsp;{{ String(i+1).padStart(2, '0') }}</div>
            <div class="c-tile-body">
              <h3 class="c-tile-title">{{ f.title }}</h3>
              <p class="c-tile-desc">{{ f.description }}</p>
            </div>
            <div class="c-tile-foot">
              <div class="c-tile-tag">{{ f.tag }}</div>
              <div class="c-tile-pages">Ch. 0{{ i+1 }} · pp. {{ f.pages }}</div>
            </div>
          </article>
        </div>

        <!-- 第 5 项：亲属监护 → 全宽跨页 Essay -->
        <article class="c-essay c-reveal">
          <div class="c-essay-left">
            <p class="c-section-kicker">Featured · 5</p>
            <h3 class="c-essay-title">{{ features[4].title }}</h3>
            <p class="c-essay-body">{{ features[4].description }} 支持监护人绑定被监护人，远程查看老人健康数据与身体指标变化，异常指标即时通知，把"不知道家里人身体怎么样"的焦虑从生活里拿掉。</p>
            <div class="c-essay-tag">{{ features[4].tag }}</div>
          </div>
          <div class="c-essay-right" aria-hidden="true">
            <div class="c-essay-orbit">
              <div class="c-orbit-ring"></div>
              <div class="c-orbit-ring c-orbit-ring-2"></div>
              <div class="c-orbit-core">家</div>
            </div>
          </div>
        </article>
      </section>

      <!-- 分割齿线 -->
      <div class="c-rule"><span></span></div>

      <!-- ================ Section 02 · 五论我们 ================ -->
      <section id="pillars" class="c-section c-section-pillars scroll-mt-24" ref="pillarsSectionRef">
        <div class="c-section-bg" aria-hidden="true">
          <div class="c-section-particles" ref="pillarsParticlesRef"></div>
          <div class="c-section-pulse c-section-pulse--alt" ref="pillarsPulseRef"></div>
        </div>
        <header class="c-section-head">
          <div>
            <p class="c-section-kicker">Section · 02</p>
            <h2 class="c-section-title">为什么选择我们·五论</h2>
          </div>
          <div class="c-section-meta">
            <div>05 Pillars</div>
            <div class="c-dot"></div>
            <div>Long-form Columns</div>
          </div>
        </header>

        <div class="c-pillars">
          <article v-for="(p, i) in pillars" :key="'p-'+i"
                   class="c-pillar c-reveal"
                   :style="{ transitionDelay: (i * 50) + 'ms' }">
            <div class="c-pillar-num">论&nbsp;{{ cnNum(i+1) }}</div>
            <h4 class="c-pillar-title">{{ p.title }}</h4>
            <p class="c-pillar-body">{{ p.description }}</p>
          </article>
        </div>
      </section>

      <!-- 分割齿线 -->
      <div class="c-rule"><span></span></div>

      <!-- ================ Section 03 · 关于本系统 ================ -->
      <section id="about" class="c-section c-section-about scroll-mt-24" ref="aboutSectionRef">
        <div class="c-section-bg" aria-hidden="true">
          <div class="c-section-particles" ref="aboutParticlesRef"></div>
          <div class="c-section-pulse c-section-pulse--third" ref="aboutPulseRef"></div>
        </div>
        <header class="c-section-head">
          <div>
            <p class="c-section-kicker">Section · 03</p>
            <h2 class="c-section-title">关于这份健康档案期刊</h2>
          </div>
          <div class="c-section-meta">
            <div>2-Column Prose</div>
            <div class="c-dot"></div>
            <div>pp. 94–106</div>
          </div>
        </header>

        <div class="c-about-grid">
          <p class="c-about-col c-reveal">
            NutriPro的出发点很朴素：医院、智能秤、运动 App、体检中心，把身体数据分散在太多地方。一个健康管理系统如果只能做"记录"，那它永远只是计算器。我们希望它同时完成三件事：第一，把体重、睡眠、饮食、运动、血压、血糖、体检报告收束到同一本档案里，不再翻遍抽屉和手机；第二，用可读的图表把它们变成趋势，让你一眼知道一年里身体在朝哪个方向走；第三，在所有沉淀下来的数据之上，让 AI 像一位认真读档的大夫，给出饮食搭配、运动计划、作息调整和每年体检该加做哪些项目的提醒。
          </p>
          <p class="c-about-col c-reveal">
            2026 年的第三期，我们把"亲属监护"写入了封面故事。子女未必和长辈住在一起，但每天看一眼他们的血压有没有波动、睡眠是不是还好，这件事本不该那么难。代录入、远程绑定、异常提醒、长期存档——每一项功能的背后，都是一个更安心的家庭。AI 的引入没有让系统变成一个冷冰冰的处方机，相反，它让每一条建议都有了完整的病史上下文。 NutriPro不是一份软件介绍，它是我们写给每一个愿意认真照顾自己身体的人的期刊。
          </p>
        </div>
      </section>

      <!-- ================ FOOTER · 刊尾 ================ -->
      <footer class="c-foot">
        <div class="c-foot-inner">
          <div class="c-foot-brand">
            <div class="c-foot-logo">
              <span class="c-brand-name c-brand-name--video">
                <span class="c-brand-video-mask">
                  <span class="c-brand-fallback" aria-hidden="true">NutriPro</span>
                  <video class="c-brand-video" autoplay muted loop playsinline preload="auto">
                    <source src="https://videos.pexels.com/video-files/5866263/5866263-hd_1280_720_25fps.mp4" type="video/mp4" />
                  </video>
                </span>
              </span>
            </div>
            <p class="c-foot-sub">让饮食更科学，让健康更有数</p>
          </div>
          <div class="c-foot-cols">
            <div>
              <h5>目次导航</h5>
              <ul>
                <li><a @click.prevent="scrollTo('features')" class="cursor-pointer">01 · 系统能力</a></li>
                <li><a @click.prevent="scrollTo('pillars')" class="cursor-pointer">02 · 五论我们</a></li>
                <li><a @click.prevent="scrollTo('about')" class="cursor-pointer">03 · 关于系统</a></li>
              </ul>
            </div>
            <div>
              <h5>加入阅读</h5>
              <ul>
                <li><router-link to="/login">订阅账户</router-link></li>
                <li><router-link to="/register">新读者</router-link></li>
                <li><router-link to="/forgot-password">找回订阅密码</router-link></li>
              </ul>
            </div>
          </div>
        </div>
        <div class="c-foot-rule"></div>
        <div class="c-foot-bottom">
          <span>© 2026 · NutriPro / 个人健康管理系统</span>
        </div>
      </footer>
    </main>

    <!-- ================================================================
         自定义光标 · 方案 B 柔光光斑（光斑自身呼吸脉动，无额外外环）
         两层：.hc-dot 针尖（紧追）/ .hc-halo 柔光（拖尾lerp + 自身尺寸+亮度呼吸 1.4s 循环）
         ================================================================ -->
    <div class="hc-layer" aria-hidden="true">
      <div class="hc-halo" ref="cursorHalo"></div>
      <div class="hc-dot" ref="cursorDot"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, nextTick } from 'vue'
import { gsap } from 'gsap'

/* ===================== 内容数据 · 严格保留原 5 features + 5 pillars + 2 about-paragraphs ===================== */

/* 项目简介区（方案 D）目录行数据 —— 原 Hero 文案降级重组 */
const introRows = [
  { no: '01', word: '记录', desc: '三餐逐笔、菜谱库、运动类型与时长，热量平衡的核算自动完成。' },
  { no: '02', word: '追踪', desc: '体重、血压、血糖的逐笔录入与月度回顾，趋势线取代零散数字。' },
  { no: '03', word: '洞察', desc: 'AI 阅读你的健康档案，生成饮食搭配、运动计划与作息调整建议。' }
]

const features = [
  {
    title: 'Health Dashboard · 数据仪表盘',
    description: '体重、运动时长、热量摄入消耗——所有身体数据在同一页面呈现，趋势线取代零散数字。',
    tag: 'Trends · Insights · Daily Review',
    pages: '14–27',
    bg: 'linear-gradient(135deg, #241c12 0%, #3c2d19 100%)',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Dark%20theme%20health%20dashboard%20UI%20mockup%2C%20floating%20above%20deep%20charcoal%20background%2C%20glassmorphism%20cards%20with%20subtle%20amber%20glow%2C%20golden%20line%20charts%20showing%20weight%20trend%2C%20calorie%20intake%2Fburn%20bars%2C%20blood%20pressure%20radial%20gauge%2C%20blood%20glucose%20sparkline%2C%20editorial%20magazine%20layout%2C%20professional%20SaaS%20product%20screenshot%2C%208k%20high%20detail%2C%20cinematic%20amber%20rim%20lighting%2C%20warm%20dark%20golden%20color%20scheme%2C%20sharp%20focus%2C%20no%20text%20artifacts&image_size=landscape_4_3'
  },
  {
    title: 'Body Metrics · 身体指标记录',
    description: '身高体重、血压、血糖的逐笔录入与月度回顾，忘记记一天也会在下一次提醒你。',
    tag: 'Weight · BP · BG',
    pages: '28–43',
    bg: 'linear-gradient(135deg, #1f1c11 0%, #332b12 100%)',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Minimalist%20medical%20journal%20infographic%2C%20dark%20amber%20background%2C%20human%20body%20silhouette%20outline%20in%20golden%20thin%20line%20art%2C%20measurement%20points%20highlighted%20with%20glowing%20amber%20dots%20at%20chest%20arm%20leg%20waist%2C%20weight%20blood%20pressure%20blood%20glucose%20small%20labels%20connected%20by%20thin%20lines%2C%20clean%20vector%20illustration%2C%20editorial%20plate%20style%2C%208k%20detailed%2C%20warm%20golden%20light%2C%20no%20gibberish%20text&image_size=landscape_4_3'
  },
  {
    title: 'Diet & Fitness · 饮食与运动台账',
    description: '三餐逐笔、菜谱库、运动类型与时长的记录，热量平衡的核算自动完成。',
    tag: 'Calorie Balance Engine',
    pages: '44–57',
    bg: 'linear-gradient(135deg, #1d170d 0%, #2b1f10 100%)',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Artistic%20food%20and%20fitness%20flat%20lay%2C%20top-down%20view%2C%20dark%20stone%20tabletop%2C%20golden%20amber%20cinematic%20overhead%20lighting%2C%20healthy%20meal%20bowl%20with%20leafy%20greens%20quinoa%20grilled%20chicken%20vegetables%2C%20pair%20of%20dumbbells%2C%20yoga%20mat%2C%20small%20calorie%20counter%20display%2C%20editorial%20magazine%20photography%20style%2C%20warm%20color%20grading%2C%20high%20detail%2C%208k&image_size=landscape_4_3'
  },
  {
    title: 'AI Health · AI 健康处方',
    description: '基于历史数据给出饮食搭配、运动计划、作息调整。它读档，然后给你真正有用的建议。',
    tag: 'Qwen2.5 · Personalized Rx',
    pages: '58–82',
    bg: 'linear-gradient(135deg, #1a140b 0%, #2e2414 100%)',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=AI%20health%20neural%20network%20concept%20art%2C%20dark%20amber%20background%2C%20abstract%20neural%20network%20lines%20forming%20a%20human%20silhouette%2C%20glowing%20golden%20data%20points%20connected%20by%20thin%20light%20lines%2C%20pulsing%20energy%20nodes%2C%20tech%20illustration%2C%20editorial%20style%2C%20warm%20amber%20color%20palette%2C%208k%20high%20detail%2C%20mystical%20atmosphere%2C%20no%20cyberpunk&image_size=landscape_4_3'
  },
  {
    title: 'Family Guard · 亲属监护',
    description: '为家庭而生的一整章。',
    tag: 'Remote Bind · Live Alerts · Cross-account',
    pages: '83–93',
    bg: ''
  }
]

const pillars = [
  {
    title: '一站式管理',
    description: '体重、饮食、运动、血压、血糖、体检档案统一记录。不再辗转于 App 之间，所有身体指标收敛成同一部时间线。'
  },
  {
    title: 'AI 深度分析',
    description: '模型读过数年间的完整档案，输出个性化的饮食搭配、运动规划和风险提醒，不是通用模板、是写给你一个人的建议。'
  },
  {
    title: '亲属监护模式',
    description: '远程绑定父母或子女账号，代录入饮食与指标、查看身体状态变化、设置异常提醒——让"异地照看"这件事变得具体。'
  },
  {
    title: '可视化洞察',
    description: '多维图表把健康趋势摊开来看，体重、饮食、运动一目了然。让趋势本身比数字更先说话。'
  },
  {
    title: '长期健康档案',
    description: '体检单长期存档，建立个人专属健康时间线，历年指标自动对比。年复一年，身体书写出它自己的底稿。'
  }
]

/* 把 1..5 转成中文数字（一/二/三/四/五） */
function cnNum(n: number) {
  return ['零','一','二','三','四','五','六','七','八','九','十'][n] ?? String(n)
}

/* ===================== 滚动进度 + 锚点滚动 ===================== */

const scrollProgress = ref(0)
const handleScroll = () => {
  const scrollTop = window.scrollY || document.documentElement.scrollTop
  const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight
  if (scrollHeight > 0) {
    scrollProgress.value = Math.min(100, Math.max(0, (scrollTop / scrollHeight) * 100))
  }
}
const scrollTo = (target: string) => {
  if (target === 'top') { window.scrollTo({ top: 0, behavior: 'smooth' }); return }
  const el = document.getElementById(target)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

/* ===================== 自定义光标 · 方案 B 柔光光斑（光斑自身呼吸脉动，无额外外环）
                  两层：.hc-dot 针尖（紧追）/ .hc-halo 柔光（拖尾lerp + 自身尺寸+亮度呼吸 1.4s 循环）
   ==================================================================================== */

const cursorDot  = ref<HTMLElement | null>(null)
const cursorHalo = ref<HTMLElement | null>(null)
const heroRef     = ref<HTMLElement | null>(null)

/* Hero M 方案 refs（视频填充标题 + 3D 错位描边 + ±30° 倾斜） */
const heroVtRef     = ref<HTMLElement | null>(null)
const heroVtInnerRef = ref<HTMLElement | null>(null)
const heroVtMaskRef  = ref<HTMLElement | null>(null)

/* 项目简介区（方案 D）refs */
const introSectionRef  = ref<HTMLElement | null>(null)
const introParticlesRef = ref<HTMLElement | null>(null)
const introPulseRef     = ref<HTMLElement | null>(null)
const introNeb1Ref      = ref<HTMLElement | null>(null)
const introNeb2Ref      = ref<HTMLElement | null>(null)

/* 全局 ambient 层 refs */
const ambientParticlesRef = ref<HTMLElement | null>(null)
const ambientPulseRef     = ref<HTMLElement | null>(null)
const ambientNeb1Ref      = ref<HTMLElement | null>(null)
const ambientNeb2Ref      = ref<HTMLElement | null>(null)

/* 各 section 背景层 refs */
const featuresParticlesRef = ref<HTMLElement | null>(null)
const featuresPulseRef     = ref<HTMLElement | null>(null)
const pillarsParticlesRef  = ref<HTMLElement | null>(null)
const pillarsPulseRef      = ref<HTMLElement | null>(null)
const aboutParticlesRef    = ref<HTMLElement | null>(null)
const aboutPulseRef        = ref<HTMLElement | null>(null)

let tx = 0, ty = 0
const pDot  = { x: 0, y: 0 }
const pHalo = { x: 0, y: 0 }

let rafId = 0
let hovered = false

const INTERACTIVE_SEL =
  'a, button, .c-cta, .c-tile, .c-pillar, .c-essay, .c-brand, .c-links a, ' +
  '[role="button"], label, input, textarea, select, summary, ' +
  'router-link, .c-foot-cols a, .c-nav-inner a, .c-essay-orbit, .c-intro-row'

function isInteractive(el: EventTarget | null): boolean {
  if (!el || !(el instanceof Element)) return false
  return el.matches(INTERACTIVE_SEL) || !!el.closest(INTERACTIVE_SEL)
}

function tick() {
  rafId = 0
  if (cursorDot.value) {
    pDot.x += (tx - pDot.x) * 0.26
    pDot.y += (ty - pDot.y) * 0.26
    cursorDot.value.style.transform = `translate3d(${pDot.x}px,${pDot.y}px,0) translate(-50%,-50%)`
  }
  if (cursorHalo.value) {
    pHalo.x += (tx - pHalo.x) * 0.16
    pHalo.y += (ty - pHalo.y) * 0.16
    cursorHalo.value.style.transform = `translate3d(${pHalo.x}px,${pHalo.y}px,0) translate(-50%,-50%)`
  }
  rafId = requestAnimationFrame(tick)
}

function setHover(on: boolean) {
  if (hovered === on) return
  hovered = on
  cursorDot.value?.classList.toggle('is-hover', on)
  cursorHalo.value?.classList.toggle('is-hover', on)
}

function onMove(e: PointerEvent) {
  tx = e.clientX
  ty = e.clientY
  if (pDot.x === 0 && pDot.y === 0) {
    pDot.x = pHalo.x = tx
    pDot.y = pHalo.y = ty
  }
  setHover(isInteractive(e.target))
}

function onDown(e: PointerEvent) {
  if (!cursorDot.value || !cursorHalo.value) return
  cursorDot.value.animate(
    [
      { width: hovered ? '8px' : '6px', height: hovered ? '8px' : '6px' },
      { width: '16px', height: '16px', offset: 0.45 },
      { width: hovered ? '8px' : '6px', height: hovered ? '8px' : '6px' }
    ],
    { duration: 280, easing: 'cubic-bezier(0.22,1,0.36,1)' }
  )
  cursorHalo.value.animate(
    [
      { opacity: 0.95, filter: 'blur(10px)' },
      { opacity: 1, filter: 'blur(12px)', offset: 0.5 },
      { opacity: 0.95, filter: 'blur(10px)' }
    ],
    { duration: 360, easing: 'cubic-bezier(0.22,1,0.36,1)' }
  )
}
function onUpOrCancel(_e: PointerEvent) {
}

/* ===================== IntersectionObserver 揭示动画 ===================== */

let revealObserver: IntersectionObserver | null = null
function initReveal() {
  revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('c-reveal-in')
        revealObserver?.unobserve(entry.target)
      }
    })
  }, { threshold: 0.10, rootMargin: '0px 0px -40px 0px' })
  document.querySelectorAll('.c-reveal').forEach(el => revealObserver?.observe(el))
}

/* ===================== Hero M 方案：视频填充标题 + 三层3D错位描边 + ±30° 倾斜 ===================== */
const VT_NS = 'http://www.w3.org/2000/svg'
const VT_FONT_MASK = 'Arial Black, HarmonyOS Sans SC, Microsoft YaHei, sans-serif'
const VT_FONT_SVG  = "'Arial Black','HarmonyOS Sans SC','Microsoft YaHei',sans-serif"
const VT_STROKES = [
  { color: 'rgba(217,162,74,0.22)',  width: 5.5, offset: 12, opacity: 1 },
  { color: 'rgba(232,185,115,0.5)',  width: 5.5, offset: 6,  opacity: 1 },
  { color: 'rgba(255,255,255,0.92)', width: 5.5, offset: 0,  opacity: 1 }
]

function buildVtMaskUrl(): string {
  const svg = `<svg xmlns="${VT_NS}" viewBox="0 0 1000 200"><text x="500" y="100" text-anchor="middle" dominant-baseline="central" font-family="${VT_FONT_MASK}" font-size="170" font-weight="900" letter-spacing="-0.04em" fill="#fff">NutriPro</text></svg>`
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`
}

function buildVtStroke(s: { color: string; width: number; offset: number; opacity: number }): SVGSVGElement {
  const svg = document.createElementNS(VT_NS, 'svg')
  svg.setAttribute('class', 'c-vt-stroke')
  svg.setAttribute('viewBox', '0 0 1000 200')
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet')
  const t = document.createElementNS(VT_NS, 'text')
  t.setAttribute('x', '50%')
  t.setAttribute('y', '50%')
  t.setAttribute('text-anchor', 'middle')
  t.setAttribute('dominant-baseline', 'central')
  t.setAttribute('font-family', VT_FONT_SVG)
  t.setAttribute('font-size', '170')
  t.setAttribute('font-weight', '900')
  t.setAttribute('letter-spacing', '-0.04em')
  t.setAttribute('fill', 'none')
  t.setAttribute('stroke', s.color)
  t.setAttribute('stroke-width', String(s.width))
  t.setAttribute('opacity', String(s.opacity))
  t.setAttribute('transform', `translate(0 ${s.offset})`)
  svg.appendChild(t)
  return svg
}

function renderHeroVt(withEntrance = true) {
  const maskEl = heroVtMaskRef.value
  const innerEl = heroVtInnerRef.value
  if (!maskEl || !innerEl) return
  const url = buildVtMaskUrl()
  maskEl.style.webkitMaskImage = url
  maskEl.style.maskImage = url
  innerEl.querySelectorAll('.c-vt-stroke').forEach(el => el.remove())
  VT_STROKES.forEach(s => innerEl.appendChild(buildVtStroke(s)))
  if (withEntrance) {
    gsap.fromTo(innerEl,
      { scale: 1.5, autoAlpha: 0, filter: 'blur(16px)' },
      { scale: 1, autoAlpha: 1, filter: 'blur(0px)', duration: 1.0, ease: 'back.out(1.4)' })
  } else {
    gsap.set(innerEl, { scale: 1, autoAlpha: 1, filter: 'blur(0px)' })
  }
}

let heroTiltMove: ((e: PointerEvent) => void) | null = null
let heroTiltLeave: (() => void) | null = null
function initHeroTilt() {
  const zone = heroRef.value
  const target = heroVtRef.value
  if (!zone || !target) return
  heroTiltMove = (e: PointerEvent) => {
    const r = zone.getBoundingClientRect()
    const nx = (e.clientX - r.left) / r.width - 0.5
    const ny = (e.clientY - r.top) / r.height - 0.5
    target.style.transition = 'transform 0.12s ease-out'
    target.style.transform = `rotateX(${(-ny * 30).toFixed(2)}deg) rotateY(${(nx * 30).toFixed(2)}deg)`
  }
  heroTiltLeave = () => {
    target.style.transition = 'transform 0.8s cubic-bezier(0.22,1.6,0.36,1)'
    target.style.transform = 'rotateX(0deg) rotateY(0deg)'
  }
  zone.addEventListener('pointermove', heroTiltMove, { passive: true })
  zone.addEventListener('pointerleave', heroTiltLeave)
}

/* 项目简介区入场（阶梯上浮 + 数字计数） */
let introObserver: IntersectionObserver | null = null
function initIntroEntrance() {
  const el = introSectionRef.value
  if (!el) return
  introObserver = new IntersectionObserver((entries) => {
    entries.forEach(en => {
      if (!en.isIntersecting) return
      el.classList.add('c-intro-play')
      el.querySelectorAll<HTMLElement>('[data-count]').forEach(node => {
        const target = Number(node.dataset.count || '0')
        const suffix = node.dataset.suffix || ''
        const obj = { v: 0 }
        gsap.to(obj, {
          v: target, duration: 1.6, ease: 'power2.out',
          onUpdate: () => { node.textContent = String(Math.round(obj.v)) + suffix }
        })
      })
      introObserver?.disconnect()
      introObserver = null
    })
  }, { threshold: 0.25 })
  introObserver.observe(el)
}

/* ===================== 全局 ambient 背景动画 ===================== */
let ambientGsapCtx: gsap.Context | null = null

function initAmbientBackgroundAnimation() {
  const partEl = ambientParticlesRef.value
  const pulseEl = ambientPulseRef.value
  const neb1 = ambientNeb1Ref.value
  const neb2 = ambientNeb2Ref.value
  if (!partEl || !pulseEl || !neb1 || !neb2) return

  partEl.innerHTML = ''

  ambientGsapCtx = gsap.context(() => {
    /* ambient 粒子（40 颗，更小更淡） */
    for (let i = 0; i < 40; i++) {
      const p = document.createElement('span')
      p.className = 'c-ambient-particle'
      const size = Math.random() * 2 + 1
      p.style.left = Math.random() * 100 + '%'
      p.style.top = Math.random() * 100 + '%'
      p.style.width = size + 'px'
      p.style.height = size + 'px'
      p.style.opacity = (Math.random() * 0.3 + 0.15).toFixed(2)
      partEl.appendChild(p)

      const dur = 5 + Math.random() * 10
      gsap.to(p, {
        x: (Math.random() - 0.5) * 30,
        y: (Math.random() - 0.5) * 40,
        duration: dur, ease: 'sine.inOut',
        yoyo: true, repeat: -1,
        delay: Math.random() * 3
      })
    }

    /* ambient 脉冲（全局缓慢呼吸） */
    const tlP = gsap.timeline({ repeat: -1 })
    tlP.to(pulseEl, {
      duration: 3, ease: 'sine.inOut',
      onUpdate() {
        const p = this.progress()
        pulseEl.style.setProperty('--apx', (30 + (70 - 30) * p) + '%')
        pulseEl.style.setProperty('--apy', (20 + (80 - 20) * p) + '%')
      }
    })
      .to(pulseEl, { opacity: 0.5, duration: 1.5, ease: 'sine.inOut' }, '<')
      .to(pulseEl, { opacity: 0.3, duration: 1.5, ease: 'sine.inOut' })
      .to(pulseEl, {
        duration: 3, ease: 'sine.inOut',
        onUpdate() {
          const p = this.progress()
          pulseEl.style.setProperty('--apx', (70 + (30 - 70) * p) + '%')
          pulseEl.style.setProperty('--apy', (80 + (20 - 80) * p) + '%')
        }
      })

    /* ambient 星云（超大周期） */
    gsap.set(neb1, { x: -20, y: -20 })
    gsap.set(neb2, { x: 30, y: 20 })
    gsap.to(neb1, { x: 30, y: 15, duration: 20, ease: 'sine.inOut', repeat: -1, yoyo: true })
    gsap.to(neb2, { x: -20, y: -25, duration: 24, ease: 'sine.inOut', repeat: -1, yoyo: true })
    gsap.to([neb1, neb2], { opacity: 0.35, duration: 12, ease: 'sine.inOut', repeat: -1, yoyo: true })
  })
}

/* ===================== Section 背景动画（features / pillars / about） ===================== */
let sectionGsapCtx: gsap.Context | null = null

function initSectionBackgroundAnimation() {
  const sections = [
    { particles: introParticlesRef.value,    pulse: introPulseRef.value,    count: 16, pulseDur: 5 },
    { particles: featuresParticlesRef.value, pulse: featuresPulseRef.value, count: 12, pulseDur: 4 },
    { particles: pillarsParticlesRef.value,  pulse: pillarsPulseRef.value,  count: 10, pulseDur: 6 },
    { particles: aboutParticlesRef.value,    pulse: aboutPulseRef.value,    count: 8,  pulseDur: 8 }
  ]

  sectionGsapCtx = gsap.context(() => {
    sections.forEach((s, idx) => {
      if (!s.particles || !s.pulse) return
      s.particles.innerHTML = ''

      /* per-section 粒子 */
      for (let i = 0; i < s.count; i++) {
        const p = document.createElement('span')
        p.className = 'c-section-particle'
        const size = Math.random() * 2 + 1.5
        p.style.left = Math.random() * 100 + '%'
        p.style.top = Math.random() * 100 + '%'
        p.style.width = size + 'px'
        p.style.height = size + 'px'
        p.style.opacity = (Math.random() * 0.35 + 0.2).toFixed(2)
        s.particles.appendChild(p)

        const dur = 6 + Math.random() * 8 + idx * 2
        gsap.to(p, {
          x: (Math.random() - 0.5) * 25,
          y: (Math.random() - 0.5) * 35,
          duration: dur, ease: 'sine.inOut',
          yoyo: true, repeat: -1,
          delay: Math.random() * 2
        })
      }

      /* per-section 脉冲（不同周期） */
      const tl = gsap.timeline({ repeat: -1, delay: idx * 1.2 })
      tl.to(s.pulse, {
        duration: s.pulseDur / 2, ease: 'sine.inOut',
        onUpdate() {
          const p = this.progress()
          s.pulse!.style.setProperty('--spx', (20 + (80 - 20) * p) + '%')
          s.pulse!.style.setProperty('--spy', (30 + (70 - 30) * p) + '%')
        }
      })
        .to(s.pulse, { opacity: 0.45, duration: 1, ease: 'sine.inOut' }, '<')
        .to(s.pulse, { opacity: 0.28, duration: s.pulseDur / 2, ease: 'sine.inOut' })
        .to(s.pulse, {
          duration: s.pulseDur / 2, ease: 'sine.inOut',
          onUpdate() {
            const p = this.progress()
            s.pulse!.style.setProperty('--spx', (80 + (20 - 80) * p) + '%')
            s.pulse!.style.setProperty('--spy', (70 + (30 - 70) * p) + '%')
          }
        })
    })

    /* 项目简介区星云流动（方案 D 第三层背景） */
    const inNeb1 = introNeb1Ref.value
    const inNeb2 = introNeb2Ref.value
    if (inNeb1 && inNeb2) {
      gsap.set(inNeb1, { x: -40, y: -30 })
      gsap.set(inNeb2, { x: 50, y: 30 })
      gsap.to(inNeb1, { x: 50, y: 20, duration: 16, ease: 'sine.inOut', repeat: -1, yoyo: true })
      gsap.to(inNeb2, { x: -30, y: -40, duration: 20, ease: 'sine.inOut', repeat: -1, yoyo: true })
      gsap.to([inNeb1, inNeb2], { opacity: 0.32, duration: 9, ease: 'sine.inOut', repeat: -1, yoyo: true })
    }
  })
}

/* ===================== 生命周期：切换根节点到 Direction C 主题（防止影响 Dashboard 浅色页） ===================== */

onMounted(() => {
  // 给 html 根打上 home-theme-c，覆盖掉 tailwind.css 的米色渐变 + App.vue 的墨绿柔光
  document.documentElement.classList.add('home-theme-c')
  // 首页全程使用自定义光标（只影响首页，onBeforeUnmount 会移除）
  document.documentElement.classList.add('hc-on')
  // 滚动监听
  window.addEventListener('scroll', handleScroll, { passive: true })
  handleScroll()
  // 光标：window 级指针事件 + rAF 循环
  window.addEventListener('pointermove',   onMove,           { passive: true })
  window.addEventListener('pointerdown',   onDown)
  window.addEventListener('pointerup',     onUpOrCancel)
  window.addEventListener('pointercancel', onUpOrCancel)
  rafId = requestAnimationFrame(tick)
  // 首帧滚动到锚点（兼容 hash 锚链）
  const hash = window.location.hash.replace(/^#\/?/, '')
  if (hash && document.getElementById(hash)) {
    requestAnimationFrame(() => scrollTo(hash))
  }
  initReveal()
  // Hero M 方案：视频填充标题渲染 + 冲击入场 + ±30° 倾斜
  renderHeroVt()
  initHeroTilt()
  // 项目简介区入场（阶梯上浮 + 数字计数）
  initIntroEntrance()
  // 全局 ambient 背景动画
  initAmbientBackgroundAnimation()
  // 各 section 背景动画（含简介区）
  initSectionBackgroundAnimation()
})
onBeforeUnmount(() => {
  document.documentElement.classList.remove('home-theme-c')
  document.documentElement.classList.remove('hc-on')
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('pointermove',   onMove)
  window.removeEventListener('pointerdown',   onDown)
  window.removeEventListener('pointerup',     onUpOrCancel)
  window.removeEventListener('pointercancel', onUpOrCancel)
  if (rafId) { cancelAnimationFrame(rafId); rafId = 0 }
  if (revealObserver) { revealObserver.disconnect(); revealObserver = null }
  if (introObserver) { introObserver.disconnect(); introObserver = null }
  // Hero 倾斜监听清理
  if (heroRef.value && heroTiltMove) heroRef.value.removeEventListener('pointermove', heroTiltMove)
  if (heroRef.value && heroTiltLeave) heroRef.value.removeEventListener('pointerleave', heroTiltLeave)
  heroTiltMove = null
  heroTiltLeave = null
  // Ambient + Section 背景动画清理
  if (ambientGsapCtx) { ambientGsapCtx.revert(); ambientGsapCtx = null }
  if (ambientParticlesRef.value) ambientParticlesRef.value.innerHTML = ''
  if (sectionGsapCtx) { sectionGsapCtx.revert(); sectionGsapCtx = null }
  ;[introParticlesRef, featuresParticlesRef, pillarsParticlesRef, aboutParticlesRef].forEach(ref => {
    if (ref.value) ref.value.innerHTML = ''
  })
})
</script>

<style>
/* =========================================================
   Direction C · 赤金 Amber Editorial
   全局根节点覆盖：.home-theme-c 挂在 <html> 上（onMounted 加入、离开 Home 时移除）
   —— 覆盖 tailwind.css 里的 #FAF8F3 米色渐变，以及 App.vue 的 ambient-glow 墨绿柔光
   ========================================================= */

/* 1. 画布 */
html.home-theme-c,
html.home-theme-c body,
html.home-theme-c #app {
  background: #0E0C0A !important;
  color: #F6EAD6;
}

/* 2. 把 App.vue 注入的墨绿/蓝色柔光改成金棕暖色呼吸 */
html.home-theme-c .ambient-glow-green {
  top: -220px; left: -180px;
  width: 680px; height: 680px;
  background: radial-gradient(circle, rgba(232,185,115,0.22) 0%, rgba(232,185,115,0) 70%) !important;
  animation: home-c-breath-a 10s ease-in-out infinite;
}
html.home-theme-c .ambient-glow-blue {
  bottom: -280px; right: -260px;
  width: 820px; height: 820px;
  background: radial-gradient(circle, rgba(217,162,74,0.18) 0%, rgba(179,107,42,0) 70%) !important;
  animation: home-c-breath-b 13s ease-in-out infinite reverse;
}
@keyframes home-c-breath-a {
  0%, 100% { opacity: 0.4; transform: scale(1) translate(0, 0); }
  50%      { opacity: 0.72; transform: scale(1.08) translate(30px, -20px); }
}
@keyframes home-c-breath-b {
  0%, 100% { opacity: 0.36; transform: scale(1) translate(0, 0); }
  50%      { opacity: 0.64; transform: scale(1.1) translate(-40px, 30px); }
}

/* 3. 全局字体：正文用系统干净 sans；大字用"斜体衬线 + 超粗 sans"混排 */
html.home-theme-c {
  font-family: "PingFang SC", "HarmonyOS Sans SC", "Hiragino Sans GB",
               "Microsoft YaHei", "Source Han Sans SC", "Noto Sans CJK SC",
               -apple-system, BlinkMacSystemFont, sans-serif;
  letter-spacing: 0.01em;
}
html.home-theme-c, html.home-theme-c * { color-scheme: dark; }

/* 4. 自定义光标全局开关（Home onMount 加 hc-on 类，onBeforeUnmount 移除 → Dashboard 不生效） */
html.hc-on,
html.hc-on *:not(.hc-layer):not(.hc-layer *) {
  cursor: none !important;
}
</style>

<style scoped>
/* =========================================================
   Home.vue scoped tokens — Direction C Amber Editorial
   ========================================================= */

/* ========== 基础 ========== */
.c-root {
  background: #0E0C0A;
  color: #F6EAD6;
  position: relative;
}
.c-root > main,
.c-root > footer {
  position: relative;
  z-index: 10;
}
.c-root > .c-nav {
  z-index: 40;
}
.c-accent { color: #D9A24A; }

/* ========== 顶部滚动进度（琥珀渐变细线） ========== */
.c-scroll-progress {
  position: fixed; top: 0; left: 0; height: 2px; z-index: 100;
  background: linear-gradient(90deg, #E8B973 0%, #D9A24A 50%, #B36B2A 100%);
  box-shadow: 0 0 12px rgba(217,162,74,0.35);
  transition: width 0.14s ease-out;
}

/* ========== 导航（刊头） ========== */
.c-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 40;
  border-bottom: 1px solid rgba(246,234,214,0.06);
  background: linear-gradient(180deg, rgba(14,12,10,0.65), rgba(14,12,10,0.25));
  backdrop-filter: saturate(160%) blur(12px);
}
.c-nav-inner {
  max-width: 1440px; margin: 0 auto;
  padding: 20px 40px;
  display: grid; grid-template-columns: auto 1fr; align-items: center; gap: 32px;
}
.c-brand { display: flex; align-items: center; gap: 12px; }
.c-brand-name--video {
  display: inline-flex; align-items: center; height: 36px;
  position: relative;
}
.c-brand-video-mask {
  display: block; width: 160px; height: 100%;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='36' viewBox='0 0 160 36'%3E%3Ctext x='0' y='29' font-size='29' font-weight='900' font-family='serif' fill='black'%3ENutriPro%3C/text%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='36' viewBox='0 0 160 36'%3E%3Ctext x='0' y='29' font-size='29' font-weight='900' font-family='serif' fill='black'%3ENutriPro%3C/text%3E%3C/svg%3E");
  -webkit-mask-size: 100% 100%; mask-size: 100% 100%;
  -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
  -webkit-mask-position: center; mask-position: center;
  position: relative;
}
.c-brand-fallback {
  position: absolute; inset: 0;
  display: flex; align-items: center;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-weight: 900; font-size: 27px;
  color: #F6EAD6;
  white-space: nowrap;
}
.c-brand-video {
  width: 100%; height: 100%;
  object-fit: cover; display: block; pointer-events: none;
}
.c-brand-name {
  font-weight: 700; letter-spacing: 0.02em; font-size: 15px;
  display: flex; align-items: baseline; gap: 6px;
}
.c-brand-sub {
  font-size: 11px; font-weight: 400; letter-spacing: 0.22em; text-transform: uppercase;
  color: rgba(246,234,214,0.5);
}
.c-links {
  justify-content: flex-end; gap: 34px;
  color: rgba(246,234,214,0.65);
  font-size: 12.5px; letter-spacing: 0.18em;
}
.c-links a {
  position: relative; padding: 4px 0;
  transition: color 0.3s ease;
}
.c-links a::after {
  content: ""; position: absolute; left: 0; right: 100%; bottom: 0; height: 1px;
  background: #D9A24A; transition: right 0.35s cubic-bezier(0.22,1,0.36,1);
}
.c-links a:hover { color: #F6EAD6; }
.c-links a:hover::after { right: 0; }
.c-issue {
  font-size: 11px; letter-spacing: 0.24em; text-transform: uppercase;
  color: rgba(246,234,214,0.45);
  padding: 7px 12px; border-radius: 999px;
  border: 1px solid rgba(246,234,214,0.1);
}

/* ========== HERO · M 方案（视频背景 + 视频填充标题） ========== */
.c-hero {
  position: relative;
  min-height: 100vh;
  max-width: none; margin: 0;
  padding: 110px 24px 90px;
  overflow: hidden;
  isolation: isolate;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  /* 保留深色渐变作为视频加载前的兜底背景 */
  background:
    radial-gradient(circle at 18% 22%, rgba(232,185,115,0.08) 0%, transparent 55%),
    radial-gradient(circle at 86% 78%, rgba(179,107,42,0.05) 0%, transparent 50%),
    linear-gradient(180deg, #14110C 0%, #0E0C0A 55%, #110E09 100%);
}
.c-hero-video {
  position: absolute; inset: 0; z-index: 0;
  width: 100%; height: 100%;
  object-fit: cover;
}
.c-hero-overlay {
  position: absolute; inset: 0; z-index: 1;
  background: radial-gradient(ellipse at 50% 42%,
    rgba(11,9,8,0.15) 0%,
    rgba(11,9,8,0.62) 78%);
}

/* 底部向下滚动提示 */
.c-hero-scroll-hint {
  position: absolute;
  bottom: 32px; left: 50%;
  transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  color: rgba(246,234,214,0.4);
  font-size: 10px; letter-spacing: 0.3em; text-transform: uppercase;
  pointer-events: none;
  z-index: 4;
  animation: c-scroll-bounce 2.2s ease-in-out infinite;
}
.c-hero-scroll-hint svg { opacity: 0.6; }
@keyframes c-scroll-bounce {
  0%, 100% { transform: translateX(-50%) translateY(0); opacity: 0.5; }
  50% { transform: translateX(-50%) translateY(6px); opacity: 1; }
}

/* ============ Hero 视频填充标题（M 方案：mask + 三层3D错位描边） ============ */
.c-hero-inner {
  position: relative; z-index: 3;
  display: flex; flex-direction: column; align-items: center;
  gap: 34px; width: 100%; max-width: 1280px; margin: 0 auto;
  text-align: center;
}
.c-hero-eyebrow {
  display: flex; align-items: center; gap: 14px;
  font-size: clamp(12px, 1.4vw, 15px);
  letter-spacing: 0.22em;
  color: rgba(246,234,214,0.85);
}
.c-hero-eyebrow::before,
.c-hero-eyebrow::after {
  content: '';
  width: 44px; height: 1px;
  background: rgba(232,185,115,0.55);
}
/* 倾斜层（外层 wrap，±30°） */
.c-hero-vt {
  position: relative;
  width: min(78vw, 1150px);
  aspect-ratio: 5.2 / 1;
  display: flex; align-items: center; justify-content: center;
  perspective: 900px;
  will-change: transform;
  /* 光晕 */
  filter: drop-shadow(0 0 26px rgba(232,185,115,0.5)) drop-shadow(0 0 60px rgba(232,185,115,0.25));
}
/* 入场/缩放层（内层，GSAP 驱动） */
.c-vt-inner {
  position: relative; width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  will-change: transform, opacity, filter;
}
/* 视频填充 mask（SVG data-URL 由 JS 注入） */
.c-vt-mask {
  position: absolute; inset: 0;
  -webkit-mask-size: contain; mask-size: contain;
  -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
  -webkit-mask-position: center; mask-position: center;
}
.c-vt-mask video {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  object-fit: cover;
}
/* 描边层（JS 注入 SVG） */
.c-vt-stroke {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
}
.c-hero-cta { margin-top: 0; justify-content: center; }

/* ============ 全局 ambient 背景动画层 ============ */
.c-ambient-layer {
  position: fixed; inset: 0; z-index: 0;
  pointer-events: none;
  overflow: hidden;
}
.c-ambient-particles {
  position: absolute; inset: 0;
}
.c-ambient-particle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle,
    rgba(232,185,115,0.7) 0%,
    rgba(232,185,115,0.1) 60%,
    transparent 100%);
  box-shadow: 0 0 4px rgba(232,185,115,0.3);
  will-change: transform, opacity;
}
.c-ambient-pulse {
  position: absolute; inset: 0;
  background: radial-gradient(circle at var(--apx,50%) var(--apy,50%),
    rgba(232,185,115,0.06) 0%,
    rgba(232,185,115,0.02) 25%,
    transparent 50%);
  opacity: 0.4;
  will-change: opacity;
}
.c-ambient-nebula {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  mix-blend-mode: screen;
  will-change: transform, opacity;
}
.c-ambient-nebula--1 {
  width: 320px; height: 320px;
  background: radial-gradient(circle,
    rgba(232,185,115,0.18) 0%,
    transparent 70%);
  top: 30%; left: -5%;
}
.c-ambient-nebula--2 {
  width: 280px; height: 280px;
  background: radial-gradient(circle,
    rgba(179,107,42,0.15) 0%,
    transparent 70%);
  bottom: 15%; right: -3%;
}

/* ============ Section 背景动画层 ============ */
.c-section-bg {
  position: absolute; inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}
.c-section-particles {
  position: absolute; inset: 0;
}
.c-section-particle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle,
    rgba(232,185,115,0.6) 0%,
    rgba(232,185,115,0.08) 60%,
    transparent 100%);
  box-shadow: 0 0 3px rgba(232,185,115,0.25);
  will-change: transform, opacity;
}
.c-section-pulse {
  position: absolute; inset: 0;
  background: radial-gradient(circle at var(--spx,50%) var(--spy,50%),
    rgba(232,185,115,0.08) 0%,
    rgba(232,185,115,0.02) 20%,
    transparent 45%);
  opacity: 0.4;
  will-change: opacity;
}
.c-section-pulse--alt {
  background: radial-gradient(circle at var(--spx,50%) var(--spy,50%),
    rgba(179,107,42,0.07) 0%,
    rgba(179,107,42,0.015) 20%,
    transparent 45%);
}
.c-section-pulse--third {
  background: radial-gradient(circle at var(--spx,50%) var(--spy,50%),
    rgba(232,185,115,0.06) 0%,
    rgba(212,142,55,0.02) 20%,
    transparent 45%);
}

/* ============ Section 容器确保背景层在后面 ============ */
.c-section {
  position: relative;
}
.c-section > *:not(.c-section-bg) {
  position: relative;
  z-index: 1;
}

.c-eyebrow {
  display: flex; align-items: center; gap: 14px;
  font-size: 11px; letter-spacing: 0.32em; text-transform: uppercase;
  color: #D9A24A; margin: 0 0 28px;
}
.c-eyebrow-bar {
  width: 42px; height: 1px;
  background: linear-gradient(90deg, #D9A24A, transparent);
}

.c-lead {
  font-size: 18px; line-height: 1.9;
  color: rgba(246,234,214,0.88);
  margin: 0;
  border-left: 2px solid rgba(217,162,74,0.6);
  padding-left: 20px;
}
.c-sub {
  font-size: 15px; line-height: 2;
  color: rgba(246,234,214,0.68);
  margin: 0; align-self: end;
}

.c-cta-row {
  display: flex; flex-wrap: wrap; gap: 14px;
  margin-top: 64px;
}
.c-cta {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 14px 22px 14px 24px;
  border-radius: 999px;
  font-size: 12.5px; font-weight: 600; letter-spacing: 0.18em; text-transform: uppercase;
  transition: transform 0.45s cubic-bezier(0.22,1,0.36,1), box-shadow 0.45s ease, background 0.35s ease, border-color 0.35s ease;
}
.c-cta-primary {
  background: linear-gradient(135deg, #E8B973 0%, #D9A24A 60%, #B36B2A 100%);
  color: #0E0C0A;
  box-shadow: 0 10px 30px rgba(217,162,74,0.28), inset 0 1px 0 rgba(255,255,255,0.3);
}
.c-cta-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 40px rgba(217,162,74,0.4), inset 0 1px 0 rgba(255,255,255,0.4);
}
.c-cta-arrow { display: inline-block; transition: transform 0.4s cubic-bezier(0.22,1,0.36,1); }
.c-cta-primary:hover .c-cta-arrow { transform: translateX(4px); }
.c-cta-ghost {
  border: 1px solid rgba(246,234,214,0.22);
  color: #F6EAD6;
}
.c-cta-ghost:hover {
  border-color: #D9A24A;
  color: #D9A24A;
  transform: translateY(-2px);
}

/* ========== 齿线分割 ========== */
.c-rule {
  max-width: 1440px; margin: 0 auto; padding: 0 40px;
}

/* ========== Section 00 · 项目简介（方案 D 组合式） ========== */
.c-intro {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  padding: clamp(70px, 9vw, 120px) 40px;
  background: linear-gradient(180deg, #0E0C0A 0%, #131009 55%, #0E0C0A 100%);
}
.c-intro-nebula {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  pointer-events: none;
  will-change: transform, opacity;
}
.c-intro-nebula--1 {
  width: 44vmax; height: 44vmax;
  background: radial-gradient(circle, rgba(201,143,62,0.18), transparent 65%);
  left: -12%; top: -18%;
}
.c-intro-nebula--2 {
  width: 40vmax; height: 40vmax;
  background: radial-gradient(circle, rgba(232,185,115,0.12), transparent 62%);
  right: -14%; bottom: -20%;
}
.c-intro-inner {
  position: relative; z-index: 2;
  max-width: 1280px; margin: 0 auto;
  display: flex; flex-direction: column;
  gap: clamp(36px, 5vw, 56px);
}
.c-intro-top {
  display: grid;
  grid-template-columns: minmax(280px, 0.85fr) 1.15fr;
  gap: clamp(28px, 4.5vw, 64px);
  align-items: center;
}
.c-intro-title {
  margin: 0;
  font-weight: 900;
  font-size: clamp(40px, 4.8vw, 60px);
  line-height: 1.22;
  letter-spacing: -0.02em;
  color: #F6EAD6;
}
.c-intro-title span { display: block; }
.c-intro-title-accent {
  background: linear-gradient(115deg, #F6EAD6 5%, #E8B973 60%, #C98F3E 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.c-intro-stats {
  display: flex;
  gap: clamp(22px, 3vw, 44px);
  margin-top: 24px;
}
.c-intro-stat b {
  font-family: 'Arial Black', 'HarmonyOS Sans SC', 'Microsoft YaHei', sans-serif;
  font-weight: 900;
  font-size: clamp(24px, 2.8vw, 36px);
  color: #E8B973;
  letter-spacing: -0.01em;
}
.c-intro-stat span {
  display: block;
  font-size: 11.5px;
  letter-spacing: 0.14em;
  color: rgba(246,234,214,0.5);
  margin-top: 4px;
}
.c-intro-right {
  display: flex; flex-direction: column; gap: 16px;
}
.c-intro-rows {
  border-top: 1px solid rgba(232,185,115,0.2);
}
.c-intro-row {
  position: relative;
  display: grid;
  grid-template-columns: 70px minmax(100px, 0.4fr) 1fr;
  gap: clamp(10px, 2vw, 28px);
  align-items: center;
  padding: 20px 8px;
  border-bottom: 1px solid rgba(232,185,115,0.2);
  overflow: hidden;
  transition: background 0.3s ease;
}
.c-intro-row::after {
  content: '';
  position: absolute; left: 0; bottom: 0;
  height: 2px; width: 0;
  background: linear-gradient(90deg, #E8B973, #C98F3E);
  transition: width 0.5s cubic-bezier(0.22,1,0.36,1);
}
.c-intro-row:hover { background: rgba(232,185,115,0.04); }
.c-intro-row:hover::after { width: 100%; }
.c-intro-row-no {
  font-family: Georgia, 'Noto Serif SC', serif;
  font-size: 19px;
  color: #E8B973;
  letter-spacing: 0.08em;
}
.c-intro-row-word {
  font-weight: 900;
  font-size: clamp(17px, 2vw, 23px);
  letter-spacing: 0.04em;
  color: #F6EAD6;
}
.c-intro-row-desc {
  font-size: 13.5px;
  line-height: 1.75;
  color: rgba(246,234,214,0.68);
  margin: 0;
}
/* 简介区入场（方案 D：阶梯上浮） */
.c-intro-anim {
  opacity: 0;
  transform: translateY(28px);
  transition: opacity 0.8s cubic-bezier(0.22,1,0.36,1), transform 0.8s cubic-bezier(0.22,1,0.36,1);
}
.c-intro-top.c-intro-anim { transition-delay: 0.05s; }
.c-intro-rows.c-intro-anim { transition-delay: 0.25s; }
.c-intro-play .c-intro-anim {
  opacity: 1;
  transform: translateY(0);
}
.c-rule > span {
  display: block; height: 1px;
  background-image: linear-gradient(90deg,
    rgba(246,234,214,0.28) 0, rgba(246,234,214,0.28) 4px,
    transparent 4px, transparent 10px
  );
  background-size: 10px 1px;
  background-repeat: repeat-x;
}

/* ========== 通用 Section ========== */
.c-section {
  max-width: 1440px; margin: 0 auto;
  padding: 110px 40px 0;
}
.c-section-head {
  display: flex; align-items: flex-end; justify-content: space-between; gap: 24px;
  margin-bottom: 56px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(246,234,214,0.08);
}
.c-section-kicker {
  margin: 0 0 10px;
  font-size: 11px; letter-spacing: 0.32em; text-transform: uppercase;
  color: #D9A24A;
}
.c-section-title {
  margin: 0;
  font-family: "Songti SC","Noto Serif SC","Times New Roman",Georgia,serif;
  font-weight: 500;
  font-size: clamp(28px, 3.2vw, 44px);
  letter-spacing: 0.01em;
  color: #F6EAD6;
}
.c-section-meta {
  display: flex; align-items: center; gap: 14px;
  font-size: 11px; letter-spacing: 0.24em; text-transform: uppercase;
  color: rgba(246,234,214,0.5);
  padding-bottom: 6px;
}
.c-dot { width: 4px; height: 4px; border-radius: 2px; background: rgba(246,234,214,0.4); }

/* ========== Section 01 · Feature Tiles ========== */
.c-tile-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;
}
.c-tile {
  border-radius: 20px;
  border: 1px solid rgba(246,234,214,0.06);
  padding: 28px 30px 24px;
  min-height: 220px;
  position: relative; overflow: hidden;
  display: flex; flex-direction: column; justify-content: space-between;
  transition: transform 0.55s cubic-bezier(0.22,1,0.36,1),
              box-shadow 0.6s cubic-bezier(0.22,1,0.36,1),
              border-color 0.5s ease,
              filter 0.5s ease,
              opacity 0.5s ease;
  transform: translateY(0) scale(1);
  filter: saturate(0.96);
  will-change: transform, box-shadow;
}
/* Active Theory 风格 Bloom：::before = 从中心向外辐射的琥珀光晕 */
.c-tile::before {
  content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 0;
  background: radial-gradient(circle at 50% 45%,
    rgba(217,162,74,0.42) 0%,
    rgba(217,162,74,0.20) 36%,
    rgba(217,162,74,0.04) 60%,
    rgba(217,162,74,0) 80%);
  opacity: 0;
  mix-blend-mode: screen;
  transition: opacity 0.6s cubic-bezier(0.22,1,0.36,1);
}
/* 内缘琥珀描边 */
.c-tile::after {
  content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 1;
  border-radius: inherit;
  box-shadow: inset 0 0 0 0 rgba(217,162,74,0);
  transition: box-shadow 0.6s cubic-bezier(0.22,1,0.36,1);
}
/* 内容在 bloom 层之上 */
.c-tile > * { position: relative; z-index: 2; }
.c-tile-img {
  position: absolute; inset: 0; width: 100%; height: 100%;
  object-fit: cover; z-index: 0;
  filter: blur(14px) brightness(0.3) saturate(0.5);
  transform: scale(1.08);
  transition: filter 0.75s cubic-bezier(0.22,1,0.36,1),
              transform 0.9s cubic-bezier(0.22,1,0.36,1);
  pointer-events: none;
}
.c-tile:hover .c-tile-img {
  filter: blur(0) brightness(0.55) saturate(0.85);
  transform: scale(1.02);
}

.c-tile:hover {
  transform: translateY(-6px) scale(1.012);
  border-color: rgba(217,162,74,0.55);
  box-shadow:
    0 40px 80px -24px rgba(0,0,0,0.75),
    0 12px 40px -6px rgba(217,162,74,0.32),
    0 0 0 1px rgba(217,162,74,0.18);
  filter: saturate(1.1);
}
.c-tile:hover::before { opacity: 1; }
.c-tile:hover::after  { box-shadow: inset 0 0 0 1px rgba(217,162,74,0.22); }

/* AT rack focus：同一栅格里，没被 hover 的格子压暗 + 轻微降饱和 */
.c-tile-grid:has(.c-tile:hover) .c-tile:not(:hover) {
  opacity: 0.58;
  filter: saturate(0.75) brightness(0.92);
  transform: scale(0.995);
}

.c-tile-no {
  font-size: 10.5px; letter-spacing: 0.28em; text-transform: uppercase;
  color: rgba(246,234,214,0.55);
  padding: 4px 10px; display: inline-block;
  border: 1px solid rgba(246,234,214,0.12);
  border-radius: 999px;
  align-self: flex-start;
  transition: color 0.4s ease, border-color 0.4s ease;
}
.c-tile:hover .c-tile-no {
  color: #F1CF92;
  border-color: rgba(217,162,74,0.45);
}
.c-tile-body { margin-top: 44px; }
.c-tile-title {
  margin: 0 0 10px;
  font-size: 24px; font-weight: 600; letter-spacing: -0.005em;
  color: #F6EAD6;
  transition: color 0.4s ease, transform 0.55s cubic-bezier(0.22,1,0.36,1);
}
.c-tile:hover .c-tile-title { transform: translateX(2px); color: #FFFFFF; }
.c-tile-desc {
  margin: 0;
  font-size: 14px; line-height: 1.85;
  color: rgba(246,234,214,0.65);
  max-width: 90%;
  transition: color 0.4s ease;
}
.c-tile:hover .c-tile-desc { color: rgba(246,234,214,0.85); }
.c-tile-foot {
  margin-top: 24px; padding-top: 16px;
  display: flex; align-items: center; justify-content: space-between;
  border-top: 1px dashed rgba(246,234,214,0.08);
  transition: border-color 0.4s ease;
}
.c-tile:hover .c-tile-foot { border-top-color: rgba(217,162,74,0.22); }
.c-tile-tag {
  font-size: 11px; letter-spacing: 0.1em;
  color: #D9A24A;
  transition: color 0.3s ease, text-shadow 0.4s ease;
}
.c-tile:hover .c-tile-tag { color: #F1CF92; text-shadow: 0 0 12px rgba(217,162,74,0.35); }
.c-tile-pages {
  font-family: "Songti SC","Noto Serif SC","Times New Roman",Georgia,serif;
  font-style: italic;
  font-size: 12px;
  color: rgba(246,234,214,0.45);
  transition: color 0.3s ease;
}
.c-tile:hover .c-tile-pages { color: rgba(246,234,214,0.72); }

/* Essay feature 5 · Full Active Theory Bloom */
.c-essay {
  margin-top: 22px;
  min-height: 280px;
  display: grid; grid-template-columns: 1.4fr 1fr;
  gap: 40px; align-items: stretch;
  border-radius: 22px; overflow: hidden;
  border: 1px solid rgba(246,234,214,0.07);
  background: linear-gradient(135deg, #161108 0%, #22180a 40%, #2e200e 100%);
  padding: 38px 40px;
  position: relative;
  transition: transform 0.6s cubic-bezier(0.22,1,0.36,1),
              box-shadow 0.6s cubic-bezier(0.22,1,0.36,1),
              border-color 0.5s ease,
              filter 0.5s ease;
  transform: translateY(0) scale(1);
  filter: saturate(0.96);
  will-change: transform, box-shadow;
}
.c-essay::before {
  content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 0;
  background: radial-gradient(circle at 28% 55%,
    rgba(232,185,115,0.30) 0%,
    rgba(217,162,74,0.16) 38%,
    rgba(179,107,42,0.04) 66%,
    rgba(179,107,42,0) 85%);
  opacity: 0; mix-blend-mode: screen;
  transition: opacity 0.6s cubic-bezier(0.22,1,0.36,1);
}
.c-essay::after {
  content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 1;
  border-radius: inherit;
  box-shadow: inset 0 0 0 0 rgba(217,162,74,0);
  transition: box-shadow 0.6s cubic-bezier(0.22,1,0.36,1);
}
.c-essay > * { position: relative; z-index: 2; }
.c-essay:hover {
  transform: translateY(-6px) scale(1.008);
  border-color: rgba(217,162,74,0.55);
  filter: saturate(1.1);
  box-shadow:
    0 50px 100px -28px rgba(0,0,0,0.8),
    0 18px 50px -8px rgba(217,162,74,0.30),
    0 0 0 1px rgba(217,162,74,0.2);
}
.c-essay:hover::before { opacity: 1; }
.c-essay:hover::after  { box-shadow: inset 0 0 0 1px rgba(217,162,74,0.28); }
.c-essay-left { display: flex; flex-direction: column; justify-content: center; }
.c-essay-title {
  margin: 10px 0 18px;
  font-family: "Songti SC","Noto Serif SC","Times New Roman",Georgia,serif;
  font-weight: 500; font-style: italic;
  font-size: clamp(30px, 2.8vw, 42px);
  line-height: 1.15; letter-spacing: 0.005em;
}
.c-essay-body {
  margin: 0;
  font-size: 15px; line-height: 2;
  color: rgba(246,234,214,0.75);
  max-width: 60ch;
}
.c-essay-tag {
  margin-top: 22px;
  font-size: 11px; letter-spacing: 0.24em; text-transform: uppercase;
  color: #D9A24A;
}
.c-essay-right { position: relative; overflow: hidden; border-radius: 16px; }
.c-essay-orbit {
  position: absolute; inset: 0;
  display: grid; place-items: center;
}
.c-orbit-ring {
  position: absolute; left: 50%; top: 50%; width: 68%; aspect-ratio: 1/1;
  border: 1px dashed rgba(217,162,74,0.35);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: c-spin 26s linear infinite;
}
.c-orbit-ring-2 {
  width: 42%;
  border-color: rgba(232,185,115,0.6);
  animation-duration: 14s;
  animation-direction: reverse;
}
.c-orbit-core {
  width: 76px; height: 76px; border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #F1CF92 0%, #D9A24A 55%, #B36B2A 100%);
  box-shadow: 0 0 40px rgba(217,162,74,0.45), inset 0 -8px 20px rgba(100,55,15,0.4);
  color: #0E0C0A;
  display: grid; place-items: center;
  font-family: "Songti SC","Noto Serif SC",serif; font-weight: 800; font-size: 28px;
  z-index: 2;
}
@keyframes c-spin { to { transform: translate(-50%, -50%) rotate(360deg); } }

/* ========== Section 02 · 5 Pillars 五论 · AT Bloom ========== */
.c-pillars {
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px;
}
.c-pillar {
  padding: 28px 22px 32px;
  border-radius: 16px;
  border: 1px solid rgba(246,234,214,0.06);
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0));
  min-height: 260px;
  display: flex; flex-direction: column; gap: 10px;
  position: relative; overflow: hidden;
  transition: transform 0.6s cubic-bezier(0.22,1,0.36,1),
              box-shadow 0.6s cubic-bezier(0.22,1,0.36,1),
              border-color 0.5s ease,
              filter 0.5s ease,
              opacity 0.5s ease;
  transform: translateY(0) scale(1);
  filter: saturate(0.96);
  will-change: transform, box-shadow;
}
.c-pillar::before {
  content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 0;
  background: radial-gradient(circle at 50% 30%,
    rgba(217,162,74,0.36) 0%,
    rgba(217,162,74,0.16) 40%,
    rgba(217,162,74,0.04) 66%,
    rgba(217,162,74,0) 82%);
  opacity: 0; mix-blend-mode: screen;
  transition: opacity 0.6s cubic-bezier(0.22,1,0.36,1);
}
.c-pillar > * { position: relative; z-index: 2; }
.c-pillar:hover {
  transform: translateY(-5px) scale(1.02);
  border-color: rgba(217,162,74,0.5);
  filter: saturate(1.1);
  box-shadow:
    0 32px 60px -20px rgba(0,0,0,0.72),
    0 12px 32px -6px rgba(217,162,74,0.28);
  background: linear-gradient(180deg, rgba(217,162,74,0.06), rgba(255,255,255,0));
}
.c-pillar:hover::before { opacity: 1; }

/* Rack focus：未 hover 的柱子整体压暗 */
.c-pillars:hover > .c-pillar:not(:hover) {
  opacity: 0.60;
  filter: saturate(0.72) brightness(0.92);
  transform: scale(0.992);
}

.c-pillar-num {
  font-family: "Songti SC","Noto Serif SC","Times New Roman",Georgia,serif;
  font-style: italic;
  color: #D9A24A;
  font-size: 13px; letter-spacing: 0.06em;
  padding-bottom: 14px; margin-bottom: 4px;
  border-bottom: 1px solid rgba(217,162,74,0.18);
  align-self: flex-start;
  width: 100%;
  transition: color 0.3s ease, border-color 0.4s ease, text-shadow 0.4s ease;
}
.c-pillar:hover .c-pillar-num {
  color: #F1CF92;
  border-color: rgba(217,162,74,0.5);
  text-shadow: 0 0 14px rgba(217,162,74,0.35);
}
.c-pillar-title {
  margin: 0;
  font-size: 17px; font-weight: 600; letter-spacing: 0.005em; line-height: 1.5;
  color: #F6EAD6;
  transition: color 0.4s ease, transform 0.55s cubic-bezier(0.22,1,0.36,1);
}
.c-pillar:hover .c-pillar-title { transform: translateY(-1px); color: #FFFFFF; }
.c-pillar-body {
  margin: 0;
  font-size: 13px; line-height: 1.95;
  color: rgba(246,234,214,0.62);
  transition: color 0.4s ease;
}
.c-pillar:hover .c-pillar-body { color: rgba(246,234,214,0.86); }

/* ========== Section 03 · About 2-Column Prose ========== */
.c-about-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 60px;
}
.c-about-col {
  margin: 0;
  font-size: 15.5px; line-height: 2.15;
  color: rgba(246,234,214,0.78);
  font-family: "Songti SC","Noto Serif SC",Georgia,serif;
}
.c-about-col::first-letter {
  font-size: 3.0em; float: left; line-height: 0.95;
  margin-right: 8px; margin-top: 6px;
  color: #D9A24A;
  font-weight: 700;
  font-family: "Songti SC","Noto Serif SC","Times New Roman",serif;
}

/* ========== Footer ========== */
.c-foot {
  margin-top: 140px;
  border-top: 1px solid rgba(246,234,214,0.08);
  background: linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.28) 100%);
}
.c-foot-inner {
  max-width: 1440px; margin: 0 auto;
  padding: 70px 40px 40px;
  display: grid; grid-template-columns: 1.4fr 1fr; gap: 60px;
}
.c-foot-logo {
  display: flex; align-items: center; gap: 12px;
  font-weight: 700; font-size: 16px; letter-spacing: 0.01em;
}
.c-foot-sub {
  margin: 18px 0 10px; max-width: 440px;
  color: rgba(246,234,214,0.58); font-size: 13.5px; line-height: 1.9;
}
.c-foot-issn {
  margin: 0;
  font-family: "Songti SC","Noto Serif SC","Times New Roman",Georgia,serif;
  font-style: italic; font-size: 12.5px;
  color: rgba(246,234,214,0.42); letter-spacing: 0.06em;
}
.c-foot-cols {
  display: grid; grid-template-columns: 1fr 1fr; gap: 40px;
}
.c-foot-cols h5 {
  margin: 0 0 18px;
  font-size: 11px; letter-spacing: 0.3em; text-transform: uppercase;
  color: #D9A24A; font-weight: 600;
}
.c-foot-cols ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 12px; }
.c-foot-cols ul li, .c-foot-cols ul li a {
  font-size: 13.5px; color: rgba(246,234,214,0.6);
  transition: color 0.3s ease;
}
.c-foot-cols ul li a:hover { color: #D9A24A; }

.c-foot-rule {
  max-width: 1360px; margin: 0 auto;
  height: 1px;
  background-image: linear-gradient(90deg,
    rgba(246,234,214,0.2) 0, rgba(246,234,214,0.2) 4px,
    transparent 4px, transparent 10px
  );
  background-size: 10px 1px;
  background-repeat: repeat-x;
}
.c-foot-bottom {
  max-width: 1440px; margin: 0 auto;
  padding: 22px 40px 40px;
  display: flex; justify-content: space-between; align-items: center;
  font-size: 11.5px; letter-spacing: 0.18em; text-transform: uppercase;
  color: rgba(246,234,214,0.4);
}

/* ========== Reveal · 滚动揭示（编辑风：小幅上浮 + 渐显，ease-out） ========== */
.c-reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.9s cubic-bezier(0.22,1,0.36,1),
              transform 0.9s cubic-bezier(0.22,1,0.36,1);
  will-change: transform, opacity;
}
.c-reveal-in {
  opacity: 1;
  transform: translateY(0);
}

/* ========== 响应式 · 保持杂志感但断行合理 ========== */
@media (max-width: 960px) {
  .c-nav-inner { grid-template-columns: auto auto; padding: 18px 24px; }
  .c-links { display: none !important; }
  .c-issue { display: none; }
  .c-hero { padding: 88px 24px 72px; }
  .c-hero-scroll-hint { bottom: 24px; }
  .c-hero-eyebrow { font-size: 11px; letter-spacing: 0.16em; }
  .c-hero-eyebrow::before, .c-hero-eyebrow::after { width: 26px; }
  .c-intro { padding: 64px 24px 0; }
  .c-intro-top { grid-template-columns: 1fr; gap: 28px; }
  .c-intro-row { grid-template-columns: 48px 1fr; padding: 16px 6px; }
  .c-intro-row-desc { grid-column: 2; grid-row: 2; }
  .c-intro-stats { gap: 22px; }
  .c-lead { font-size: 16.5px; }
  .c-section { padding: 70px 24px 0; }
  .c-section-head { flex-direction: column; align-items: flex-start; gap: 14px; margin-bottom: 40px; }
  .c-tile-grid { grid-template-columns: 1fr; }
  .c-essay { grid-template-columns: 1fr; padding: 28px 24px; }
  .c-essay-right { min-height: 240px; order: -1; }
  .c-pillars { grid-template-columns: 1fr 1fr; }
  .c-about-grid { grid-template-columns: 1fr; gap: 28px; }
  .c-foot-inner { grid-template-columns: 1fr; padding: 50px 24px 28px; }
  .c-foot-cols { gap: 28px; }
  .c-foot-bottom { flex-direction: column; gap: 10px; padding: 18px 24px 32px; text-align: center; }
}
@media (max-width: 560px) {
  .c-pillars { grid-template-columns: 1fr; }
}

/* =================================================================
   自定义光标 · 方案 B 柔光光斑（光斑自身呼吸脉动，无额外外环）
   两层结构：.hc-dot（针尖）/ .hc-halo（柔光 + 自体 1.4s 呼吸循环）
   ——常态：轻呼吸 110↔120px · 暖光柔和
   ——hover：强呼吸 160↔172px · 色温更亮
   ================================================================= */

.hc-layer {
  position: fixed; inset: 0;
  pointer-events: none;
  z-index: 99999;
}

/* B · 针尖：纯色实体，保证 1px 点击精度 */
.hc-dot {
  position: absolute; left: 0; top: 0;
  width: 6px; height: 6px; border-radius: 50%;
  background: #F1CF92;
  box-shadow:
    0 0 12px rgba(217,162,74,0.75),
    0 0 2px rgba(255,255,255,0.75),
    0 0 0 1px rgba(0,0,0,0.35);
  transform: translate(-50%, -50%);
  will-change: transform;
  transition:
    width 0.28s cubic-bezier(0.22,1,0.36,1),
    height 0.28s cubic-bezier(0.22,1,0.36,1),
    background-color 0.28s ease,
    box-shadow 0.28s ease;
}
.hc-dot.is-hover {
  width: 8px; height: 8px;
  background: #ffffff;
  box-shadow:
    0 0 16px rgba(255,255,255,0.7),
    0 0 10px rgba(217,162,74,0.85),
    0 0 0 1px rgba(0,0,0,0.45);
}

/* B · 柔光：径向暖色模糊光斑 + mix-blend-mode: screen
   ——离开 Hero 区后：尺寸依旧呼吸（一张一合 108↔122），但**亮度锁死 0.95**不再明暗脉冲闪光
   ——hover 档：尺寸升格呼吸（156↔170），亮度锁死 0.98 静态暖色
   ——拖尾靠 rAF lerp(0.16) 实现暖光跟随感 */
.hc-halo {
  position: absolute; left: 0; top: 0;
  width: 114px; height: 114px; border-radius: 50%;
  transform: translate(-50%, -50%);
  filter: blur(10px);
  mix-blend-mode: screen;
  will-change: transform, opacity;
  /* —— 只跑尺寸呼吸动画（108 ↔ 122，2.0s sine）——亮度完全静态，不脉冲 —— */
  animation: hc-halo-size-idle 2.0s cubic-bezier(0.25,0.1,0.25,1) infinite;
  opacity: 0.95;
  /* 静态暖金色渐变（取原来 bright-idle 0%/50% 的中间值 → 色温恒定） */
  background: radial-gradient(circle,
    rgba(228,180,108,0.35) 0%,
    rgba(215,163,90,0.185) 40%,
    rgba(205,151,82,0.055) 70%,
    rgba(205,151,82,0)    92%);
}
/* 尺寸呼吸：108 ↔ 122。
   和之前完全一致，但没有 brightness/gradient animation 叠在上面 → 视觉"一直亮 0.95 + 形状一张一合呼吸" */
@keyframes hc-halo-size-idle {
  0%, 100% { width: 108px; height: 108px; }
  50%      { width: 122px; height: 122px; }
}

/* ————— Hover 升格档：尺寸升格到 156↔170，亮度静态 0.98（只更暖一点，不脉冲闪光） ————— */
.hc-halo.is-hover {
  animation-name: hc-halo-size-hover;
  animation-duration: 2.0s;
  animation-timing-function: cubic-bezier(0.25,0.1,0.25,1);
  animation-iteration-count: infinite;
  opacity: 0.98;
  filter: blur(10.5px);
  /* hover 档静态暖光（更亮一级，但同样无脉冲） */
  background: radial-gradient(circle,
    rgba(242,202,134,0.46) 0%,
    rgba(228,180,108,0.24) 40%,
    rgba(220,170,98,0.075) 70%,
    rgba(220,170,98,0)    93%);
}
@keyframes hc-halo-size-hover {
  0%, 100% { width: 156px; height: 156px; }
  50%      { width: 170px; height: 170px; }
}

/* 移动端（触控）：隐藏自定义光标层 */
@media (hover: none) and (pointer: coarse) {
  .hc-layer { display: none !important; }
}
</style>
