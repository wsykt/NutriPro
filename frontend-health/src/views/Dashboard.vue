<template>
  <div class="app-layout">
    <!-- ========== 顶栏（赭金深色壳，固定在顶部） ========== -->
    <header class="topbar h-20 w-full flex items-center z-50 fixed top-0 left-0 right-0">
      <div class="topbar-inner h-full w-full flex items-center">
        <!-- 左侧 -->
        <div class="topbar-left flex items-center h-full pl-5 pr-4" ref="topbarLeftRef">
          <!-- NutriPro 品牌视频文字 -->
          <span class="brand-name">
            <span class="nutripro-video-mask">
              <span class="nutripro-fallback" aria-hidden="true">NutriPro</span>
              <video class="nutripro-video" autoplay muted loop playsinline preload="auto">
                <source src="https://videos.pexels.com/video-files/5866263/5866263-hd_1280_720_25fps.mp4" type="video/mp4" />
              </video>
            </span>
          </span>
          <div class="topbar-divider mx-6 h-7 w-px"></div>
          <span class="topbar-page text-sm whitespace-nowrap font-medium">{{ currentPageTitle }}</span>
        </div>

        <!-- 右侧 -->
        <div class="topbar-right flex-1 flex items-center justify-end gap-1.5 pr-5 pl-4" ref="topbarRightRef">
          <select
            v-model="selectedActAs"
            class="act-select hidden md:block px-3.5 py-1.5 rounded-lg text-xs outline-none transition-all font-medium"
          >
            <option :value="-1">我自己</option>
            <option v-for="w in userStore.wards" :key="w.wardId" :value="w.wardId">
              替 {{ w.wardUsername }} 操作
            </option>
          </select>
          <span
            v-if="selectedActAs != -1"
            class="hidden md:inline-flex items-center text-[11px] px-2.5 py-1 rounded-full text-white font-medium act-badge"
          >
            亲属代操作
          </span>

          <div class="topbar-divider mx-1 h-6 w-px"></div>

          <div class="flex items-center gap-2.5">
            <div class="avatar-btn w-9 h-9 rounded-full flex items-center justify-center text-white font-semibold text-xs overflow-hidden shrink-0"
                 :style="{ background: 'linear-gradient(135deg, #E8B973 0%, #D9A24A 60%, #B36B2A 100%)' }">
              <img v-if="userAvatar" :src="userAvatar" class="w-full h-full object-cover" alt="头像" />
              <template v-else>{{ usernameInitial }}</template>
            </div>
            <div class="hidden sm:flex flex-col items-start">
              <span class="topbar-username text-xs font-semibold leading-tight">{{ usernameText }}</span>
              <span class="topbar-userrole text-[10px] font-medium">用户</span>
            </div>
            <button @click="handleLogout"
                    class="logout-btn ml-0.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap">
              退出
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- ========== 侧边栏（赭金深色壳 · 固定窄轨，点击图标进入二级导航） ========== -->
    <aside
      ref="sidebarRoot"
      class="sidebar-root fixed left-0 bottom-0 flex flex-col z-40"
    >
      <div class="sidebar-inner h-full w-full flex flex-col">
        <nav ref="navRef" class="nav-scroll flex-1 px-1 py-3 relative z-10">
          <!-- 首页入口 -->
          <button
            class="menu-item relative mb-1.5 flex items-center justify-center text-left rounded-xl"
            :class="isHubActive ? 'menu-active' : 'menu-inactive'"
            title="首页"
            @click="goHub()"
          >
            <span v-if="isHubActive" class="menu-indicator absolute left-0 top-1/2 -translate-y-1/2 pointer-events-none"></span>
            <div class="menu-icon-wrap w-9 h-9 rounded-xl flex items-center justify-center shrink-0 relative z-10">
              <LayoutGrid
                class="menu-icon w-[18px] h-[18px]"
                :style="{ color: isHubActive ? '#F6EAD6' : '#B9A78A' }"
                stroke-width="1.75"
              />
            </div>
            <div class="menu-flyout">
              <span class="menu-label text-[13px] font-semibold block whitespace-nowrap tracking-tight">首页</span>
            </div>
          </button>

          <!-- 分割线 -->
          <div class="sidebar-sep mx-3 my-2"></div>

          <template v-for="(group, groupIndex) in groups" :key="group.key">
            <button
              class="menu-item relative mb-1.5 flex items-center justify-center text-left rounded-xl"
              :class="isGroupActive(group.key) ? 'menu-active' : 'menu-inactive'"
              :title="group.name"
              @click="goGroup(group)"
            >
              <span v-if="isGroupActive(group.key)" class="menu-indicator absolute left-0 top-1/2 -translate-y-1/2 pointer-events-none"></span>

              <div class="menu-icon-wrap w-9 h-9 rounded-xl flex items-center justify-center shrink-0 relative z-10" :data-orbit-group="group.key">
                <component
                  :is="group.icon"
                  class="menu-icon w-[18px] h-[18px]"
                  :style="{ color: isGroupActive(group.key) ? '#F6EAD6' : '#B9A78A' }"
                  stroke-width="1.75"
                />
              </div>
              <div class="menu-flyout">
                <span class="menu-label text-[13px] font-semibold block whitespace-nowrap tracking-tight">{{ group.name }}</span>
              </div>
            </button>
          </template>
        </nav>

        <div class="sidebar-footer shrink-0 py-3 px-1 relative z-10">
          <button
            class="menu-item relative w-full flex items-center justify-center text-left rounded-xl mb-1.5"
            :class="isProfileActive ? 'menu-active' : 'menu-inactive'"
            title="个人中心"
            @click="router.push('/dashboard/profile')"
          >
            <span v-if="isProfileActive" class="menu-indicator absolute left-0 top-1/2 -translate-y-1/2 pointer-events-none"></span>

            <div class="menu-icon-wrap w-9 h-9 rounded-xl flex items-center justify-center shrink-0 relative z-10">
              <CircleUser
                class="menu-icon w-[18px] h-[18px]"
                :style="{ color: isProfileActive ? '#F6EAD6' : '#B9A78A' }"
                stroke-width="1.75"
              />
            </div>
            <div class="menu-flyout">
              <span class="menu-label text-[13px] font-semibold block whitespace-nowrap tracking-tight">个人中心</span>
            </div>
          </button>
        </div>
      </div>
    </aside>

    <!-- ========== 主内容区（浅色舞台，固定左边距 220px） ========== -->
    <main class="content-main">
      <div class="p-6 lg:p-8 min-h-screen relative">
        <div class="page-stage">
          <router-view v-slot="{ Component, route: r }">
            <!--
              页面切换：保留已验证稳定的 CSS 冒泡（out-in 模式）。
              GSAP 负责壳动画（侧栏/菜单/顶栏）+ 子页面 ScrollTrigger，不接管路由过渡以避免异步组件 done() 时序问题。
            -->
            <transition
              mode="out-in"
              appear
              enter-active-class="bubble-enter-active"
              leave-active-class="instant-leave-active"
              appear-active-class="bubble-enter-active">
              <component :is="Component" :key="r.fullPath + '|' + (userStore.actAsUserId ?? 'self')" />
            </transition>
          </router-view>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore, type User } from '@/stores/user'
import { useGsapAnim } from '@/composables/useGsapAnim'
import {
  CircleUser,
  Users,
  Utensils,
  HeartPulse,
  BookOpen,
  ChefHat,
  LayoutGrid
} from 'lucide-vue-next'
import type { Component } from 'vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const { menuEnter, topbarEnter } = useGsapAnim()

// GSAP 用的元素引用
const sidebarRoot = ref<HTMLElement | null>(null)
const navRef = ref<HTMLElement | null>(null)
const topbarLeftRef = ref<HTMLElement | null>(null)
const topbarRightRef = ref<HTMLElement | null>(null)

const userInfo = computed(() => userStore.user || ({} as User))
const usernameText = computed(() => userInfo.value.username || '')
const userAvatar = computed(() => userStore.avatar)
const usernameInitial = computed(() => {
  const n = usernameText.value
  return n ? n.slice(0, 1).toUpperCase() : 'U'
})

const selectedActAs = computed({
  get: () => (userStore.actAsUserId != null ? userStore.actAsUserId : -1),
  set: (val: number) => {
    if (val === -1) {
      userStore.setActAs(null)
    } else {
      userStore.setActAs(val)
    }
  }
})

interface GroupItem { name: string; to: string }
interface MenuGroup { key: string; name: string; icon: Component; items: GroupItem[] }
const groups: MenuGroup[] = [
  { key: 'user', name: '用户中心', icon: Users, items: [
    { name: '个人中心', to: '/dashboard/profile' },
    { name: '家庭管理', to: '/dashboard/family' },
  ]},
  { key: 'diet', name: '饮食管理', icon: Utensils, items: [
    { name: '饮食记录', to: '/dashboard/food-input' },
    { name: '营养分析', to: '/dashboard/nutrition' },
  ]},
  { key: 'health', name: '健康监测', icon: HeartPulse, items: [
    { name: '健康报告', to: '/dashboard/health-report' },
    { name: '健康档案', to: '/dashboard/health-archive' },
    { name: '运动管理', to: '/dashboard/muscle-chart' },
  ]},
  { key: 'knowledge', name: '知识中心', icon: BookOpen, items: [
    { name: '科普文章', to: '/dashboard/articles' },
    { name: 'AI 咨询', to: '/dashboard/ai-consult' },
  ]},
  { key: 'recipe', name: '菜谱美食', icon: ChefHat, items: [
    { name: '菜谱库', to: '/dashboard/recipe-library' },
  ]},
]

function goGroup(g: { key: string }) {
  router.push({ path: '/dashboard/hub', query: { group: g.key } })
}

function goHub() {
  router.push('/dashboard/home')
}

const routeToTitleMap: Record<string, string> = {
  hub: '首页',
  profile: '个人中心', 'metrics-history': '身体指标', 'health-history': '健康档案', 'family-relation': '亲属管理',
  'food-input': '饮食记录', 'food-add': '添加食材', nutrition: '营养分析',
  'food-search': '食物搜索', 'family-input': '亲属代录',
  'health-report': '健康报告', 'muscle-chart': '运动管理',
  articles: '科普文章', 'article-detail': '文章详情', 'ai-consult': 'AI 咨询', 'training-plan': '训练计划',
  'recipe-library': '菜谱库', 'dietary-profile': '饮食档案', 'recipe-detail': '菜谱详情'
}

const currentPageTitle = computed(() => {
  const pathSegments = route.path.split('/').filter(Boolean)
  const last = pathSegments[pathSegments.length - 1] || ''
  if (routeToTitleMap[last]) return routeToTitleMap[last]
  if (last === 'recipe-detail' || route.path.includes('/article-detail/')) return '详情'
  return '健康助手'
})

const isHubActive = computed(() => {
  return route.path === '/dashboard/home'
})

const isGroupActive = (groupKey: string) => {
  if (route.path === '/dashboard/hub' && route.query.group === groupKey) return true
  const group = groups.find(g => g.key === groupKey)
  if (!group) return false
  return group.items.some(it => {
    if (it.to === route.path) return true
    if (it.to.startsWith('/dashboard/recipe-detail') && route.path.startsWith('/dashboard/recipe-detail')) return true
    return false
  })
}

const isProfileActive = computed(() => {
  const r = route.path
  return r === '/dashboard/profile'
})

const handleLogout = () => {
  if (confirm('确定退出登录？')) {
    userStore.logout()
    router.push('/login')
  }
}

onMounted(() => {
  userStore.init()
  // 顶栏元素 stagger 下落
  nextTick(() => {
    const leftItems = topbarLeftRef.value?.children
      ? Array.from(topbarLeftRef.value.children)
      : []
    const rightItems = topbarRightRef.value?.children
      ? Array.from(topbarRightRef.value.children)
      : []
    if (leftItems.length) topbarEnter(leftItems as Element[])
    if (rightItems.length) topbarEnter(rightItems as Element[])
    // 菜单项 stagger 浮入
    const menuItems = navRef.value
      ? Array.from(navRef.value.querySelectorAll('.menu-item'))
      : []
    if (menuItems.length) menuEnter(menuItems as Element[])
  })
})
</script>

<style scoped>
/* ========== 布局（浅色舞台） ========== */
.app-layout {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  background: #F7F5F0;
}

/* ========== 顶栏（赭金深色壳） ========== */
.topbar {
  background: #14110C;
  border-bottom: 1px dashed rgba(217, 162, 74, 0.28);
}
.topbar-inner {
  position: relative;
}
.topbar-inner::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(circle at 12% 0%, rgba(232,185,115,0.10) 0%, transparent 45%);
}
.brand-name {
  display: inline-flex; align-items: center; height: 30px;
}
.topbar-divider {
  background: linear-gradient(to bottom, transparent, rgba(217, 162, 74, 0.35), transparent);
}
/* NutriPro 视频文字（SVG mask + 视频填充，深底仍可见彩色视频） */
.nutripro-video-mask {
  display: block;
  width: 140px;
  height: 30px;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='30' viewBox='0 0 140 30'%3E%3Ctext x='0' y='24' font-size='23' font-weight='800' font-family='serif' fill='black'%3ENutriPro%3C/text%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='30' viewBox='0 0 140 30'%3E%3Ctext x='0' y='24' font-size='23' font-weight='800' font-family='serif' fill='black'%3ENutriPro%3C/text%3E%3C/svg%3E");
  -webkit-mask-size: 100% 100%;
  mask-size: 100% 100%;
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  position: relative;
}
.nutripro-fallback {
  position: absolute; inset: 0;
  display: flex; align-items: center;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-weight: 800; font-size: 21px;
  color: #F6EAD6; /* 视频未加载时显示赭金文字，视频加载后覆盖 */
}
.nutripro-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  pointer-events: none;
}
.topbar-divider {
  background: linear-gradient(to bottom, transparent, rgba(217, 162, 74, 0.35), transparent);
}
.topbar-page {
  color: #B9A78A;
}
.act-select {
  background: rgba(14, 12, 10, 0.5);
  border: 1px solid rgba(217, 162, 74, 0.3);
  color: #F6EAD6;
  cursor: pointer;
}
.act-select:hover {
  border-color: rgba(217, 162, 74, 0.55);
  background: rgba(20, 17, 12, 0.7);
}
.act-select option {
  background: #14110C;
  color: #F6EAD6;
}
.act-badge {
  background: linear-gradient(135deg, #E8B973 0%, #D9A24A 60%, #B36B2A 100%) !important;
  color: #1F170E;
}
.avatar-btn {
  transition: transform 0.25s ease;
  box-shadow: 0 4px 14px rgba(217, 162, 74, 0.35);
}
.avatar-btn:hover {
  transform: scale(1.08);
}
.topbar-username {
  color: #F6EAD6;
}
.topbar-userrole {
  color: #8C7A5E;
}
.logout-btn {
  color: #B9A78A;
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.3s ease;
}
.logout-btn:hover {
  color: #F1CF92;
  border-color: rgba(217, 162, 74, 0.3);
  background: rgba(217, 162, 74, 0.06);
}

/* ========== 侧边栏（赭金深色壳，GSAP 接管 width/label） ========== */
.sidebar-root {
  left: 0;
  top: 80px;
  width: 60px;
  /* width transition 移除：交给 GSAP timeline 控制，避免双重动画 */
}
.sidebar-inner {
  height: 100%;
  background: linear-gradient(180deg, #14110C 0%, #110E09 100%);
  border-right: 1px solid rgba(217, 162, 74, 0.18);
  border-radius: 0;
  position: relative;
}
.sidebar-inner::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(circle at 80% 8%, rgba(232,185,115,0.10) 0%, transparent 40%),
    repeating-linear-gradient(0deg, rgba(217,162,74,0.022) 0 1px, transparent 1px 86px);
}
.sidebar-sep {
  border-top: 1px dashed rgba(217, 162, 74, 0.18);
  height: 0;
}

/* 菜单项（固定窄轨：图标统一居中于同一条竖线） */
.menu-item {
  width: 52px;
  min-height: 44px;
  padding: 4px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: visible; /* 允许悬停标签浮出竖轨右侧 */
  transition: background 0.3s ease;
}
.menu-inactive:hover {
  background: rgba(217, 162, 74, 0.1);
}
.menu-active {
  background: rgba(217, 162, 74, 0.12);
}
/* 选中指示竖条（琥珀渐变） */
.menu-indicator {
  width: 3px;
  height: 24px;
  border-radius: 0 999px 999px 0;
  background: linear-gradient(180deg, #E8B973 0%, #D9A24A 60%, #B36B2A 100%);
  box-shadow: 0 2px 8px rgba(217, 162, 74, 0.45);
  left: 3px;
}

/* 图标容器：悬停轻微放大 + 高亮光晕 */
.menu-icon-wrap {
  background: transparent;
  transition: transform 0.28s cubic-bezier(0.34, 1.4, 0.5, 1), background 0.28s ease, box-shadow 0.28s ease;
}
.menu-active .menu-icon-wrap {
  background: transparent;
}
.menu-item:hover .menu-icon-wrap {
  transform: scale(1.12);
  background: rgba(217, 162, 74, 0.16);
  box-shadow: 0 0 0 1px rgba(232, 185, 115, 0.35), 0 6px 18px rgba(217, 162, 74, 0.25);
}
/* 悬停时图标点亮（!important 覆盖内联色值） */
.menu-item:hover .menu-icon {
  color: #F6EAD6 !important;
}

/* 悬停浮出的名称标签（图标右侧胶囊） */
.menu-flyout {
  position: absolute;
  left: calc(100% + 12px);
  top: 50%;
  transform: translate(-6px, -50%);
  opacity: 0;
  pointer-events: none;
  background: rgba(24, 19, 12, 0.95);
  border: 1px solid rgba(217, 162, 74, 0.4);
  padding: 5px 12px;
  border-radius: 999px;
  white-space: nowrap;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.35);
  transition: opacity 0.22s ease, transform 0.22s cubic-bezier(0.34, 1.3, 0.5, 1);
  z-index: 80;
}
.menu-item:hover .menu-flyout,
.menu-item:focus-visible .menu-flyout {
  opacity: 1;
  transform: translate(0, -50%);
}
.menu-flyout .menu-label {
  color: #F0E2C4 !important;
  font-size: 12px;
}

/* StarOrbit 粒子飞入后的图标脉冲点亮（由 StarOrbit.vue 在粒子抵达时添加 class） */
@keyframes orbitIconPulse {
  0% { box-shadow: 0 0 0 0 rgba(232, 185, 115, 0.7); }
  100% { box-shadow: 0 0 0 14px rgba(232, 185, 115, 0); }
}
.menu-icon-wrap.orbit-pulse {
  animation: orbitIconPulse 0.6s ease-out;
}

/* 底部 */
.sidebar-footer {
  border-top: 1px solid rgba(217, 162, 74, 0.15);
}

/* ========== 主内容区（浅色舞台，固定窄轨布局） ========== */
.content-main {
  min-height: calc(100vh - 80px);
  margin-left: 60px; /* 侧栏固定窄轨宽度 */
  padding-top: 80px;
  position: relative;
  z-index: 1;
}

/* ========== 页面过渡动画（保留已稳定的 CSS 冒泡，out-in 模式） ========== */
.page-stage {
  min-height: 100%;
}
.bubble-enter-active {
  animation: pageBubbleIn 0.7s cubic-bezier(0.22, 1.2, 0.36, 1) both;
  will-change: transform, opacity;
}
.instant-leave-active {
  transition: opacity 0s;
}
@keyframes pageBubbleIn {
  0%   { opacity: 0;  transform: translate3d(0, 22px, 0) scale(0.92); }
  58%  { opacity: 1;  transform: translate3d(0, -3px, 0) scale(1.02); }
  80%  {              transform: translate3d(0, 0.5px, 0) scale(1.002); }
  100% { opacity: 1;  transform: translate3d(0, 0, 0)     scale(1);     }
}
</style>

<style>
body, html, #app {
  background: #F7F5F0;
  margin: 0;
  padding: 0;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
