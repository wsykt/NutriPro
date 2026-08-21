<template>
  <div class="app-layout">
    <!-- ========== 顶栏（固定在顶部，不随滚动移动） ========== -->
    <header class="topbar h-20 w-full flex items-center z-50 fixed top-0 left-0 right-0">
      <div class="topbar-inner h-full w-full flex items-center">
        <!-- 左侧 -->
        <div class="flex items-center h-full pl-5 pr-4">
          <!-- NutriPro 小卡片（视频文字加大，替代叶子图标） -->
          <div class="nutripro-card">
            <span class="nutripro-name font-bold tracking-tight whitespace-nowrap">
              <span class="nutripro-video-mask">
                <span class="nutripro-fallback" aria-hidden="true"></span>
                <video class="nutripro-video" autoplay muted loop playsinline preload="auto">
                  <source src="https://videos.pexels.com/video-files/5866263/5866263-hd_1280_720_25fps.mp4" type="video/mp4" />
                </video>
              </span>
              <span class="nutripro-text sr-only">NutriPro</span>
            </span>
          </div>
          <div class="mx-6 h-7 w-px bg-gradient-to-b from-transparent via-slate-300 to-transparent"></div>
          <span class="text-sm text-slate-600 whitespace-nowrap font-medium">{{ currentPageTitle }}</span>
        </div>

        <!-- 右侧 -->
        <div class="flex-1 flex items-center justify-end gap-1.5 pr-5 pl-4">
          <select
            v-model="selectedActAs"
            class="hidden md:block px-3.5 py-1.5 rounded-lg text-xs text-slate-600 outline-none transition-all bg-white/70 border border-slate-200 hover:border-slate-300 hover:bg-white cursor-pointer font-medium"
          >
            <option :value="-1">我自己</option>
            <option v-for="w in userStore.wards" :key="w.wardId" :value="w.wardId">
              替 {{ w.wardUsername }} 操作
            </option>
          </select>
          <span
            v-if="selectedActAs != -1"
            class="hidden md:inline-flex items-center text-[11px] px-2.5 py-1 rounded-full text-white font-medium"
            :style="{ background: 'linear-gradient(135deg, #E07A3F 0%, #C9642A 100%)' }"
          >
            亲属代操作
          </span>

          <div class="mx-1 h-6 w-px bg-gradient-to-b from-transparent via-slate-300 to-transparent"></div>

          <div class="flex items-center gap-2.5">
            <div class="avatar-btn w-9 h-9 rounded-full flex items-center justify-center text-white font-semibold text-xs overflow-hidden shrink-0 ring-2 ring-white shadow-md"
                 :style="{ background: 'linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%)' }">
              <img v-if="userAvatar" :src="userAvatar" class="w-full h-full object-cover" alt="头像" />
              <template v-else>{{ usernameInitial }}</template>
            </div>
            <div class="hidden sm:flex flex-col items-start">
              <span class="text-xs font-semibold text-slate-700 leading-tight">{{ usernameText }}</span>
              <span class="text-[10px] text-slate-400 font-medium">用户</span>
            </div>
            <button @click="handleLogout"
                    class="ml-0.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-500 hover:text-red-500 hover:bg-red-50 transition-colors whitespace-nowrap">
              退出
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- ========== 侧边栏 ========== -->
    <aside
      class="sidebar-root fixed left-0 bottom-0 flex flex-col z-40 overflow-hidden"
      :class="{ 'sidebar-expanded': sidebarHover }"
      @mouseenter="sidebarHover = true"
      @mouseleave="sidebarHover = false"
    >
      <div class="sidebar-inner h-full w-full flex flex-col">
        <nav class="nav-scroll flex-1 overflow-y-auto sidebar-scrollbar py-3 relative z-10">
          <!-- 首页入口（独立于菜单组，固定在最上方） -->
          <button
            class="menu-item relative mb-1.5 pl-0 pr-2 flex items-center text-left rounded-xl"
            :class="isHubActive ? 'menu-active' : 'menu-inactive'"
            @click="goHub()"
            :style="{ '--item-delay': '0s' }"
          >
            <span v-if="isHubActive" class="menu-indicator absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-r-full bg-emerald-500 pointer-events-none"></span>
            <div class="menu-icon-wrap w-9 h-9 rounded-xl flex items-center justify-center shrink-0 relative z-10">
              <LayoutGrid
                class="menu-icon w-[18px] h-[18px]"
                :style="{ color: isHubActive ? '#0f172a' : '#64748b' }"
                stroke-width="1.75"
              />
            </div>
            <div class="menu-label-wrap overflow-hidden ml-2.5 shrink-1 min-w-0 flex-1 relative z-10">
              <span class="menu-label text-[13px] font-semibold block whitespace-nowrap tracking-tight"
                    :style="{ color: isHubActive ? '#0f172a' : '#64748b' }">
                首页
              </span>
            </div>
          </button>

          <!-- 分割线 -->
          <div class="mx-3 my-2 border-t border-slate-200/40"></div>

          <template v-for="(group, groupIndex) in groups" :key="group.key">
            <button
              class="menu-item relative mb-1.5 pl-0 pr-2 flex items-center text-left rounded-xl"
              :class="isGroupActive(group.key) ? 'menu-active' : 'menu-inactive'"
              @click="goGroup(group)"
              :style="{ '--item-delay': (0.05 + groupIndex * 0.03) + 's' }"
            >
              <!-- 选中左侧竖条指示器 -->
              <span v-if="isGroupActive(group.key)" class="menu-indicator absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-r-full bg-emerald-500 pointer-events-none"></span>

              <div class="menu-icon-wrap w-9 h-9 rounded-xl flex items-center justify-center shrink-0 relative z-10">
                <component
                  :is="group.icon"
                  class="menu-icon w-[18px] h-[18px]"
                  :style="{ color: isGroupActive(group.key) ? '#0f172a' : '#64748b' }"
                  stroke-width="1.75"
                />
              </div>
              <div class="menu-label-wrap overflow-hidden ml-2.5 shrink-1 min-w-0 flex-1 relative z-10">
                <span class="menu-label text-[13px] font-semibold block whitespace-nowrap tracking-tight"
                      :style="{ color: isGroupActive(group.key) ? '#0f172a' : '#64748b' }">
                  {{ group.name }}
                </span>
              </div>
            </button>
          </template>
        </nav>

        <div class="sidebar-footer shrink-0 py-3 px-2 relative z-10 border-t border-slate-100/60">
          <button
            class="menu-item relative w-full flex items-center text-left rounded-xl mb-1.5 pl-0 pr-2 py-1.5"
            :class="isProfileActive ? 'menu-active' : 'menu-inactive'"
            @click="router.push('/dashboard/profile')"
          >
            <!-- 选中左侧竖条指示器 -->
            <span v-if="isProfileActive" class="menu-indicator absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-r-full bg-emerald-500 pointer-events-none"></span>

            <div class="menu-icon-wrap w-9 h-9 rounded-xl flex items-center justify-center shrink-0 relative z-10">
              <CircleUser
                class="w-[18px] h-[18px]"
                :style="{ color: isProfileActive ? '#0f172a' : '#64748b' }"
                stroke-width="1.75"
              />
            </div>
            <div class="menu-label-wrap overflow-hidden ml-2.5 shrink-1 min-w-0 flex-1 relative z-10">
              <span class="text-[13px] font-semibold block whitespace-nowrap tracking-tight"
                    :style="{ color: isProfileActive ? '#0f172a' : '#64748b' }">{{ usernameText }}</span>
              <span class="text-[10px] text-slate-400 font-medium block whitespace-nowrap">个人中心</span>
            </div>
          </button>
        </div>
      </div>
    </aside>

    <!-- ========== 主内容区（固定尺寸：左边距固定 220px，不随侧边栏变化） ========== -->
    <main class="content-main">
      <div class="p-6 lg:p-8 min-h-screen relative">
        <div class="page-stage" :class="{ 'bubble-playing': bubbleAnimating }">
          <router-view v-slot="{ Component }">
            <transition name="page-fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore, type User } from '@/stores/user'
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

const sidebarHover = ref(false)

const userInfo = computed(() => userStore.user || ({} as User))
const usernameText = computed(() => userInfo.value.username || '')
const userAvatar = computed(() => userStore.avatar)
const usernameInitial = computed(() => {
  const n = usernameText.value
  return n ? n.slice(0, 1).toUpperCase() : 'U'
})

// 操作身份：-1 表示自己；其他值是 ward.userId（亲属代操作，保留原逻辑）
const selectedActAs = computed({
  get: () => (userStore.actAsUserId != null ? userStore.actAsUserId : -1),
  set: (val: number) => {
    if (val === -1) {
      userStore.setActAs(null)
    } else {
      userStore.setActAs(val)
      router.replace({ path: route.path, query: { ...(route.query || {}), _t: Date.now() } })
    }
  }
})

// 功能分组：点击进入对应分组的功能卡片页（保留 health 原分组与路由）
interface GroupItem { name: string; to: string }
interface MenuGroup { key: string; name: string; icon: Component; items: GroupItem[] }
const groups: MenuGroup[] = [
  { key: 'user', name: '用户中心', icon: Users, items: [
    { name: '个人中心', to: '/dashboard/profile' },
    { name: '身体指标', to: '/dashboard/metrics-history' },
    { name: '健康档案', to: '/dashboard/health-history' },
    { name: '亲属管理', to: '/dashboard/family-relation' },
  ]},
  { key: 'diet', name: '饮食管理', icon: Utensils, items: [
    { name: '饮食记录', to: '/dashboard/food-input' },
    { name: '营养分析', to: '/dashboard/nutrition' },
    { name: '食物搜索', to: '/dashboard/food-search' },
    { name: '添加食材', to: '/dashboard/food-add' },
    { name: '亲属代录', to: '/dashboard/family-input' },
  ]},
  { key: 'health', name: '健康监测', icon: HeartPulse, items: [
    { name: '健康报告', to: '/dashboard/health-report' },
    { name: '运动管理', to: '/dashboard/muscle-chart' },
    { name: '附近地图', to: '/dashboard/gym' },
  ]},
  { key: 'knowledge', name: '知识中心', icon: BookOpen, items: [
    { name: '科普文章', to: '/dashboard/articles' },
    { name: 'AI 咨询', to: '/dashboard/ai-consult' },
    { name: '训练计划', to: '/dashboard/training-plan' },
  ]},
  { key: 'recipe', name: '菜谱美食', icon: ChefHat, items: [
    { name: '菜谱库', to: '/dashboard/recipe-library' },
    { name: '饮食档案', to: '/dashboard/dietary-profile' },
  ]},
]

// 点击分组 → 进入该分组的功能卡片页（保留原逻辑：/dashboard/hub?group=xxx）
function goGroup(g: { key: string }) {
  router.push({ path: '/dashboard/hub', query: { group: g.key } })
}

// 首页入口 → demo 首页（与 /dashboard 默认重定向保持一致）
function goHub() {
  router.push('/dashboard/demo')
}

// 顶栏标题映射
const routeToTitleMap: Record<string, string> = {
  hub: '首页',
  profile: '个人中心', 'metrics-history': '身体指标', 'health-history': '健康档案', 'family-relation': '亲属管理',
  'food-input': '饮食记录', 'food-add': '添加食材', nutrition: '营养分析',
  'food-search': '食物搜索', 'family-input': '亲属代录',
  'health-report': '健康报告', 'muscle-chart': '运动管理', gym: '附近地图',
  articles: '科普文章', 'article-detail': '文章详情', 'ai-consult': 'AI 咨询', 'training-plan': '训练计划',
  'recipe-library': '菜谱库', 'dietary-profile': '饮食档案', 'recipe-detail': '菜谱详情'
}

const currentPageTitle = computed(() => {
  const pathSegments = route.path.split('/').filter(Boolean)
  const last = pathSegments[pathSegments.length - 1] || ''
  if (routeToTitleMap[last]) return routeToTitleMap[last]
  // 动态详情路由
  if (last === 'recipe-detail' || route.path.includes('/article-detail/')) return '详情'
  return '健康助手'
})

const isHubActive = computed(() => {
  return route.path === '/dashboard/demo'
})

const isGroupActive = (groupKey: string) => {
  if (route.path === '/dashboard/hub' && route.query.group === groupKey) return true
  const group = groups.find(g => g.key === groupKey)
  if (!group) return false
  return group.items.some(it => {
    if (it.to === route.path) return true
    // 动态路由（recipe-detail/:id）
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
  triggerBubble()
})

const bubbleAnimating = ref(false)
function triggerBubble() {
  bubbleAnimating.value = false
  nextTick(() => {
    bubbleAnimating.value = true
    setTimeout(() => { bubbleAnimating.value = false }, 520)
  })
}
watch(() => route.fullPath, () => {
  triggerBubble()
})
</script>

<style scoped>
/* ========== 布局 ========== */
.app-layout {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  background: #F7F5F0;
}

/* ========== 顶栏 ========== */
.topbar {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(24px) saturate(1.8);
  -webkit-backdrop-filter: blur(24px) saturate(1.8);
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}
.serif-mark {
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif;
}
/* ===== NutriPro 视频文字（SVG mask + 视频填充） ===== */
.nutripro-name {
  position: relative;
  display: inline-flex;
  align-items: center;
  height: 30px;
  overflow: hidden;
}
.nutripro-video-mask {
  display: block;
  width: 112px;
  height: 100%;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='112' height='30' viewBox='0 0 112 30'%3E%3Ctext x='0' y='23' font-size='24' font-weight='800' font-family='serif' fill='black'%3ENutriPro%3C/text%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='112' height='30' viewBox='0 0 112 30'%3E%3Ctext x='0' y='23' font-size='24' font-weight='800' font-family='serif' fill='black'%3ENutriPro%3C/text%3E%3C/svg%3E");
  -webkit-mask-size: 100% 100%;
  mask-size: 100% 100%;
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
}
.nutripro-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  pointer-events: none;
}
.nutripro-text {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.logo-wrap {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
  box-shadow: 0 6px 20px rgba(47, 93, 74, 0.28);
}
.logo-wrap:hover {
  transform: scale(1.08) rotate(-3deg);
  box-shadow: 0 8px 24px rgba(47, 93, 74, 0.38);
}
.logo-anim {
  animation: logoIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}
@keyframes logoIn {
  from { opacity: 0; transform: scale(0.7) rotate(-10deg); }
  to { opacity: 1; transform: scale(1) rotate(0); }
}
.avatar-btn {
  transition: transform 0.25s ease;
}
.avatar-btn:hover {
  transform: scale(1.08);
}

/* ========== 侧边栏 ========== */
.sidebar-root {
  left: 0;
  top: 80px;
  width: 60px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.sidebar-inner {
  height: 100%;
  background: #ffffff;
  border-right: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 0 24px 24px 0;
  transition: box-shadow 0.4s ease, border-color 0.4s ease;
  position: relative;
}
.sidebar-root.sidebar-expanded .sidebar-inner {
  border-right-color: rgba(15, 23, 42, 0.08);
}
.sidebar-root.sidebar-expanded {
  width: 220px;
}

/* 菜单项 */
.menu-item {
  min-height: 42px;
  padding: 5px 4px;
  width: 52px;
  position: relative;
  overflow: hidden;
  transition: background 0.25s ease, width 0.4s cubic-bezier(0.4, 0, 0.2, 1), transform 0.25s ease;
  animation: menuItemIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: var(--item-delay, 0s);
}
@keyframes menuItemIn {
  from { opacity: 0; transform: translateX(-8px); }
  to { opacity: 1; transform: translateX(0); }
}
.menu-inactive:hover {
  background: rgba(15, 23, 42, 0.05);
  transform: translateX(2px);
}
.menu-active {
  background: rgba(47, 93, 74, 0.07);
}
/* 选中指示竖条 */
.menu-indicator {
  left: 3px;
  box-shadow: 0 2px 8px rgba(47, 93, 74, 0.35);
}
.sidebar-root.sidebar-expanded .menu-item {
  width: 100%;
}
.sidebar-root.sidebar-expanded .menu-indicator {
  left: 0;
}

/* 图标容器 */
.menu-icon-wrap {
  background: transparent;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.menu-active .menu-icon-wrap {
  background: transparent;
}
.sidebar-root.sidebar-expanded .menu-active .menu-icon-wrap {
  transform: scale(1);
}
.sidebar-root.sidebar-expanded .menu-item:hover .menu-icon-wrap {
  transform: scale(1.05);
}

/* 标签文字 */
.menu-label-wrap {
  max-width: 0;
  opacity: 0;
  margin-left: 0;
  transition: max-width 0.4s cubic-bezier(0.4, 0, 0.2, 1),
              opacity 0.35s cubic-bezier(0.4, 0, 0.2, 1),
              margin-left 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  transition-delay: var(--delay, 0s);
  pointer-events: none;
}
.menu-label {
  white-space: nowrap;
  overflow: hidden;
}
.sidebar-root.sidebar-expanded .menu-label-wrap {
  max-width: 160px;
  opacity: 1;
  margin-left: 10px;
  pointer-events: auto;
}

/* 底部 */
.sidebar-footer {
  border-color: transparent;
}
.sidebar-root.sidebar-expanded .sidebar-footer {
  border-color: rgba(15, 23, 42, 0.06);
}

/* ========== 主内容区 ========== */
.content-main {
  min-height: calc(100vh - 80px);
  margin-left: 220px;
  padding-top: 80px;
  position: relative;
  z-index: 1;
}

/* ========== 页面过渡动画 ========== */
.page-stage {
  min-height: 100%;
}
.bubble-playing > * {
  animation: pageBubbleIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes pageBubbleIn {
  0% { opacity: 0; transform: translate3d(0, 28px, 0) scale(0.88); }
  55% { opacity: 1; transform: translate3d(0, -6px, 0) scale(1.04); }
  78% { transform: translate3d(0, 1px, 0) scale(0.99); }
  100% { opacity: 1; transform: translate3d(0, 0, 0) scale(1); }
}
.page-fade-enter-active, .page-fade-leave-active {
  transition: opacity 0.18s ease;
}
.page-fade-enter-from, .page-fade-leave-to {
  opacity: 0;
}

/* ========== 滚动条 ========== */
.sidebar-scrollbar::-webkit-scrollbar { width: 4px; }
.sidebar-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.08);
  border-radius: 2px;
}
.sidebar-scrollbar::-webkit-scrollbar-track { background: transparent; }
.sidebar-root:not(.sidebar-expanded) .sidebar-scrollbar::-webkit-scrollbar-thumb {
  background: transparent;
}
.sidebar-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgba(15, 23, 42, 0.08) transparent;
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