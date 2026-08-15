<template>
  <div class="content-layer min-h-screen text-morandi-text relative overflow-x-hidden">
    <!-- 顶部滚动进度条 -->
    <div class="scroll-progress-bar" :style="{ width: scrollProgress + '%' }"></div>

    <!-- 顶部导航栏（不固定，随页面滚动） -->
    <header class="glass px-6 md:px-12 py-4 relative z-40">
      <nav class="max-w-7xl mx-auto flex items-center justify-between">
        <a @click.prevent="scrollTo('top')" class="text-xl font-bold tracking-tight cursor-pointer">HealthManage</a>
        <ul class="hidden md:flex gap-8 text-sm font-medium text-morandi-lightText">
          <li><a @click.prevent="scrollTo('projects')" class="cursor-pointer hover:text-morandi-accent transition-colors">系统功能</a></li>
          <li><a @click.prevent="scrollTo('whyus')" class="cursor-pointer hover:text-morandi-accent transition-colors">为什么选择我们</a></li>
          <li><a @click.prevent="scrollTo('about')" class="cursor-pointer hover:text-morandi-accent transition-colors">关于我们</a></li>
        </ul>
      </nav>
    </header>

    <main id="top" class="max-w-7xl mx-auto px-6 md:px-12 py-16 relative z-10">
      <!-- Hero首屏 -->
      <section class="py-20 md:py-32 flex flex-col gap-8 max-w-3xl mx-auto text-center items-center">
        <h1 class="text-[clamp(2.5rem,6vw,4.2rem)] font-bold leading-tight">
          <span class="title-line">
            <span v-for="(ch, i) in titleLine1" :key="'l1-'+i" class="title-char" :style="{ animationDelay: (i * 80) + 'ms' }">{{ ch }}</span>
          </span><br>
          <span class="title-line">
            <span v-for="(ch, i) in titleLine2" :key="'l2-'+i" class="title-char" :style="{ animationDelay: ((i + titleLine1.length) * 80) + 'ms' }">{{ ch }}</span>
          </span>
        </h1>
        <p class="hero-desc text-morandi-lightText text-lg leading-relaxed max-w-2xl">
          记录日常饮食运动、追踪身体指标变化，通过AI智能分析，帮助你建立长期健康档案，科学管理每一个健康维度
        </p>
        <div class="hero-buttons flex flex-wrap gap-4 mt-2 justify-center">
          <router-link to="/login" class="px-7 py-3 rounded-lg bg-morandi-accent text-white font-medium glow-btn transition-all">
            登录
          </router-link>
          <router-link to="/register" class="px-7 py-3 rounded-lg glass font-medium text-morandi-text glow-card transition-all">
            注册
          </router-link>
        </div>
      </section>

      <hr class="border-morandi-soft my-16">

      <!-- 系统核心功能：单卡片轮播 -->
      <section id="projects" class="mb-24 scroll-mt-24 scroll-reveal-item">
        <div class="mb-10 text-center">
          <h2 class="text-3xl font-bold mb-3">系统核心功能</h2>
          <p class="text-morandi-lightText">从数据记录到智能分析，提供全方位健康管理</p>
        </div>
        <div class="relative max-w-5xl mx-auto">
          <div class="slider-wrapper rounded-2xl glass overflow-hidden glow-card-hover">
            <div v-for="(slide, i) in projectSlides" :key="i"
                 class="slider-slot"
                 :class="{ 'is-active': sliderState.projects.current === i }"
                 :style="{ opacity: sliderState.projects.current === i ? 1 : 0 }">
              <div class="relative h-[540px] w-full">
                <img :src="slide.image" :alt="slide.title" class="absolute inset-0 w-full h-full object-contain" />
                <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/75 via-black/35 to-transparent p-8 pt-24">
                  <h3 class="font-semibold text-3xl mb-2 text-white">{{ slide.title }}</h3>
                  <p class="text-white/85 text-lg">{{ slide.description }}</p>
                </div>
              </div>
            </div>
          </div>
          <button @click="slideTo('projects', sliderState.projects.current - 1)" class="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 glass w-11 h-11 rounded-full flex items-center justify-center z-10 text-2xl font-bold text-morandi-text hover:bg-white">‹</button>
          <button @click="slideTo('projects', sliderState.projects.current + 1)" class="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 glass w-11 h-11 rounded-full flex items-center justify-center z-10 text-2xl font-bold text-morandi-text hover:bg-white">›</button>
          <div class="flex justify-center gap-2 mt-6">
            <button v-for="idx in projectSlides.length" :key="idx" @click="slideTo('projects', idx - 1)" class="w-3 h-3 rounded-full cursor-pointer transition-colors" :class="sliderState.projects.current === idx - 1 ? 'bg-morandi-accent' : 'bg-morandi-soft hover:bg-morandi-accent/50'"></button>
          </div>
        </div>
      </section>

      <!-- 为什么选择我们：单篇轮播 -->
      <section id="whyus" class="mb-24 scroll-mt-24 scroll-reveal-item">
        <div class="mb-10 text-center">
          <h2 class="text-3xl font-bold mb-3">为什么选择我们</h2>
          <p class="text-morandi-lightText">五大核心优势，构建专属个人健康管理闭环</p>
        </div>
        <div class="relative max-w-5xl mx-auto">
          <div class="slider-wrapper rounded-2xl glass overflow-hidden glow-card-hover">
            <div v-for="(slide, i) in whyUsSlides" :key="i"
                 class="slider-slot"
                 :class="{ 'is-active': sliderState.whyus.current === i }"
                 :style="{ opacity: sliderState.whyus.current === i ? 1 : 0 }">
              <div class="relative h-[540px] w-full">
                <img :src="slide.image" :alt="slide.title" class="absolute inset-0 w-full h-full object-contain" />
                <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/75 via-black/35 to-transparent p-8 pt-24">
                  <h3 class="font-semibold text-3xl mb-2 text-white">{{ slide.title }}</h3>
                  <p class="text-white/85 text-lg">{{ slide.description }}</p>
                </div>
              </div>
            </div>
          </div>
          <button @click="slideTo('whyus', sliderState.whyus.current - 1)" class="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 glass w-11 h-11 rounded-full flex items-center justify-center z-10 text-2xl font-bold text-morandi-text hover:bg-white">‹</button>
          <button @click="slideTo('whyus', sliderState.whyus.current + 1)" class="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 glass w-11 h-11 rounded-full flex items-center justify-center z-10 text-2xl font-bold text-morandi-text hover:bg-white">›</button>
          <div class="flex justify-center gap-2 mt-6">
            <button v-for="idx in whyUsSlides.length" :key="idx" @click="slideTo('whyus', idx - 1)" class="w-3 h-3 rounded-full cursor-pointer transition-colors" :class="sliderState.whyus.current === idx - 1 ? 'bg-morandi-accent' : 'bg-morandi-soft hover:bg-morandi-accent/50'"></button>
          </div>
        </div>
      </section>

      <!-- 关于我们区块 -->
      <section id="about" class="mb-24 scroll-mt-24 scroll-reveal-item">
        <div class="max-w-3xl mx-auto text-center">
          <h2 class="text-3xl font-bold mb-6">关于我们</h2>
          <p class="text-morandi-lightText leading-relaxed text-lg mb-4">
            个人健康管理系统主要用于帮助用户集中记录和管理日常健康数据，包括体重、睡眠、饮食、运动、血压、血糖及体检报告等信息。通过可视化图表展示健康趋势，用户可以更直观地了解自身身体状况，发现不良生活习惯，并为后续健康调整提供数据依据。
          </p>
          <p class="text-morandi-lightText leading-relaxed text-lg">
            在与 AI 结合方面，系统可以基于用户历史健康数据进行智能分析，自动生成个性化健康建议，例如饮食搭配、运动计划、作息调整和体检重点提醒。AI 的引入使系统不再只是简单的数据记录工具，而是能够根据不同用户的身体状态提供差异化指导，进一步提升健康管理的实用性和智能化程度。
          </p>
        </div>
      </section>
    </main>

    <!-- 底部页脚 -->
    <footer id="contact" class="glass px-6 md:px-12 py-12 relative z-10">
      <div class="max-w-7xl mx-auto">
        <div class="flex flex-col md:flex-row justify-between gap-10 mb-10">
          <div>
            <h3 class="text-xl font-bold mb-3">HealthManage 健康管理系统</h3>
            <p class="text-morandi-lightText max-w-sm">一站式个人健康数据管理平台，完整前后端开源项目，适合毕设与二次开发</p>
          </div>
          <div class="grid grid-cols-2 gap-12">
            <div>
              <h4 class="font-medium mb-4">页面导航</h4>
              <ul class="text-morandi-lightText space-y-2 text-sm">
                <li><a @click.prevent="scrollTo('projects')" class="cursor-pointer hover:text-morandi-accent transition-colors">系统功能</a></li>
                <li><a @click.prevent="scrollTo('whyus')" class="cursor-pointer hover:text-morandi-accent transition-colors">为什么选择我们</a></li>
                <li><a @click.prevent="scrollTo('about')" class="cursor-pointer hover:text-morandi-accent transition-colors">关于我们</a></li>
              </ul>
            </div>
            <div>
              <h4 class="font-medium mb-4">项目资源</h4>
              <ul class="text-morandi-lightText space-y-2 text-sm">
                <li><router-link to="/login" class="cursor-pointer hover:text-morandi-accent transition-colors">用户登录</router-link></li>
                <li><router-link to="/register" class="cursor-pointer hover:text-morandi-accent transition-colors">注册账号</router-link></li>
              </ul>
            </div>
          </div>
        </div>
        <hr class="border-morandi-soft mb-6">
        <p class="text-sm text-morandi-lightText text-center">© 2026 个人健康管理系统</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, reactive, nextTick, ref } from 'vue'

type SliderKey = 'projects' | 'whyus'
interface SliderItem {
  current: number
  total: number
}

// 标题两行文字 — 逐字淡入浮现，单字动画 0.6s，间隔 0.08s
const titleLine1 = Array.from('个人健康管理系统')
const titleLine2 = Array.from('一站式健康数据记录平台')

// 滚动进度
const scrollProgress = ref(0)
const handleScroll = () => {
  const scrollTop = window.scrollY || document.documentElement.scrollTop
  const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight
  if (scrollHeight > 0) {
    scrollProgress.value = Math.min(100, Math.max(0, (scrollTop / scrollHeight) * 100))
  }
}

const projectSlides = [
  {
    title: '健康数据仪表盘',
    description: 'ECharts 折线/柱状图表，体重、睡眠、运动趋势可视化',
    image: '/images/1.png'
  },
  {
    title: '身体指标记录模块',
    description: '录入身高体重、血压血糖，自动生成月度健康报告',
    image: '/images/2.png'
  },
  {
    title: '运动与饮食台账',
    description: '记录每日三餐、健身时长，计算热量摄入消耗',
    image: '/images/3.png'
  },
  {
    title: 'AI 健康分析助手',
    description: '基于健康数据智能生成专属运动、饮食调理方案',
    image: '/images/4.png'
  },
  {
    title: '体检档案管理',
    description: '上传体检单长期存档，自动对比历年指标变化',
    image: '/images/5.png'
  }
]

const whyUsSlides = [
  {
    title: '一站式健康数据管理',
    description: '体重、睡眠、饮食、运动、血压、血糖、体检档案统一记录，告别零散数据碎片化',
    image: '/images/s1.png'
  },
  {
    title: 'AI 智能健康分析',
    description: '基于用户历史健康数据进行智能分析，自动生成个性化饮食搭配与运动规划建议',
    image: '/images/s2.png'
  },
  {
    title: '亲属监护模式',
    description: '支持监护人绑定被监护人，远程查看老人健康数据与身体指标变化，及时掌握身体状态',
    image: '/images/s3.png'
  },
  {
    title: '可视化数据洞察',
    description: 'ECharts 多维图表直观展示健康趋势变化，体重睡眠运动一目了然，辅助科学健康决策',
    image: '/images/s4.png'
  },
  {
    title: '长期健康档案管理',
    description: '体检单长期存档，建立个人专属健康时间线，自动对比历年指标变化追踪身体状态',
    image: '/images/s5.png'
  }
]

const sliderState = reactive<Record<SliderKey, SliderItem>>({
  projects: { current: 0, total: projectSlides.length },
  whyus: { current: 0, total: whyUsSlides.length },
})

// 平滑滚动到指定区块
const scrollTo = (target: string) => {
  if (target === 'top') {
    window.scrollTo({ top: 0, behavior: 'smooth' })
    return
  }
  const el = document.getElementById(target)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// 页面首次加载时，如果 URL 带有 hash（例如 #projects），滚动到对应区块
const handleInitialHash = async () => {
  const hash = window.location.hash.replace(/^#\/?/, '')
  if (hash && document.getElementById(hash)) {
    await nextTick()
    scrollTo(hash)
  }
}

/**
 * 轮播切换核心方法：仅通过 opacity 控制渐显渐隐，250ms 平滑过渡
 */
const slideTo = (sliderId: SliderKey, targetIndex: number) => {
  const state = sliderState[sliderId]
  if (targetIndex < 0) targetIndex = state.total - 1
  if (targetIndex >= state.total) targetIndex = 0
  if (targetIndex === state.current) return
  state.current = targetIndex
}

onMounted(() => {
  handleInitialHash()
  // 启动滚动进度监听
  window.addEventListener('scroll', handleScroll, { passive: true })
  handleScroll()
  // 启动滚动渐入观察
  initScrollReveal()
})

// 滚动渐入动画：使用 IntersectionObserver
let observerInstance: IntersectionObserver | null = null
const initScrollReveal = () => {
  observerInstance = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible')
        observerInstance?.unobserve(entry.target)
      }
    })
  }, { threshold: 0.12, rootMargin: '0px 0px -50px 0px' })

  document.querySelectorAll('.scroll-reveal, .scroll-reveal-item').forEach(el => {
    observerInstance?.observe(el)
  })
}

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
  if (observerInstance) {
    observerInstance.disconnect()
    observerInstance = null
  }
})
</script>

<style scoped>
  /* ============ 顶部滚动进度条 ============ */
  .scroll-progress-bar {
    position: fixed;
    top: 0;
    left: 0;
    height: 3px;
    background: linear-gradient(90deg, #34d399 0%, #2F5D4A 50%, #059669 100%);
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
    transition: width 0.15s ease-out;
    z-index: 100;
    border-radius: 0 2px 2px 0;
  }

  /* ============ 标题逐字淡入：每个字 0.6s，字间隔 0.08s ============ */
  .title-line {
    display: inline-block;
  }
  .title-char {
    display: inline-block;
    opacity: 0;
    animation: title-char-fade 0.6s ease forwards;
  }
  @keyframes title-char-fade {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* ============ Hero 区描述、按钮依次淡入上移 ============ */
  .hero-desc {
    opacity: 0;
    transform: translateY(20px);
    animation: hero-fade-up 0.8s ease 1.5s forwards;
  }
  .hero-buttons {
    opacity: 0;
    transform: translateY(20px);
    animation: hero-fade-up 0.8s ease 2.0s forwards;
  }
  @keyframes hero-fade-up {
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* ============ 轮播：仅渐显渐隐 ============ */
  .slider-wrapper {
    position: relative;
    min-height: 280px;
  }
  .slider-slot {
    position: absolute;
    inset: 0;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: opacity 250ms ease;
    pointer-events: none;
  }
  .slider-slot.is-active {
    pointer-events: auto;
    position: relative;
  }

  /* ============ 滚动渐入：轮播卡片、文字区块 ============ */
  .scroll-reveal,
  .scroll-reveal-item {
    opacity: 0;
    transform: translateY(40px);
    transition: opacity 0.9s ease-out, transform 0.9s ease-out;
  }
  .scroll-reveal.is-visible,
  .scroll-reveal-item.is-visible {
    opacity: 1;
    transform: translateY(0);
  }
</style>
