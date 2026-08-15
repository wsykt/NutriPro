<template>
  <div class="content-layer min-h-screen flex">
    <!-- 左侧侧边栏 -->
        <aside :class="['h-screen sticky top-0 shrink-0 overflow-y-auto bg-white/90 border-r border-morandi-soft/50 backdrop-blur-sm transition-all duration-200', sidebarCollapsed ? 'w-16' : 'w-64']">
      <div class="py-6 px-4 border-b border-morandi-soft mb-4 flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-morandi-accent flex items-center justify-center text-white font-bold shrink-0">健</div>
        <h2 v-show="!sidebarCollapsed" class="text-base font-bold text-morandi-text truncate">健康助手</h2>
      </div>
      <ul class="px-2 space-y-2">
        <li class="parent-menu">
          <div class="parent-title block px-4 py-3 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer flex justify-between items-center" @click="toggleSubMenu('user')">
            <span class="flex items-center gap-2"><Users class="w-5 h-5 shrink-0" /><span v-show="!sidebarCollapsed">用户中心</span></span>
            <span v-show="!sidebarCollapsed" class="arrow transition-transform duration-300 text-xs" :class="{ 'rotate-180': subMenuOpen.user }">▼</span>
          </div>
          <ul class="submenu space-y-1 mt-1 overflow-hidden transition-all" :class="{ open: subMenuOpen.user }">
            <li><RouterLink to="/dashboard/profile" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'profile' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('profile')"><UserIcon class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">个人中心</span></RouterLink></li>
            <li><RouterLink to="/dashboard/metrics-history" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'metrics-history' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('metrics-history')"><Activity class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">身体指标历史</span></RouterLink></li>
            <li><RouterLink to="/dashboard/health-history" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'health-history' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('health-history')"><FileText class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">健康档案历史</span></RouterLink></li>
            <li><RouterLink to="/dashboard/family-relation" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'family-relation' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('family-relation')"><UsersRound class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">亲属关系管理</span></RouterLink></li>
          </ul>
        </li>
        <li class="parent-menu">
          <div class="parent-title block px-4 py-3 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer flex justify-between items-center" @click="toggleSubMenu('food')">
            <span class="flex items-center gap-2"><Utensils class="w-5 h-5 shrink-0" /><span v-show="!sidebarCollapsed">饮食管理</span></span>
            <span v-show="!sidebarCollapsed" class="arrow transition-transform duration-300 text-xs" :class="{ 'rotate-180': subMenuOpen.food }">▼</span>
          </div>
          <ul class="submenu space-y-1 mt-1 overflow-hidden transition-all" :class="{ open: subMenuOpen.food }">
            <li><RouterLink to="/dashboard/food-input" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'food-input' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('food-input')"><PlusCircle class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">录入饮食</span></RouterLink></li>
            <li><RouterLink to="/dashboard/food-add" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'food-add' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('food-add')"><Plus class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">添加食材</span></RouterLink></li>
            <li><RouterLink to="/dashboard/nutrition" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'nutrition' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('nutrition')"><PieChart class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">营养分析</span></RouterLink></li>
            <li><RouterLink to="/dashboard/food-search" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'food-search' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('food-search')"><Search class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">食物搜索</span></RouterLink></li>
            <li><RouterLink to="/dashboard/family-input" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'family-input' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('family-input')"><UsersRound class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">亲属代录入饮食</span></RouterLink></li>
          </ul>
        </li>
        <li class="parent-menu">
          <div class="parent-title block px-4 py-3 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer flex justify-between items-center" @click="toggleSubMenu('recipe')">
            <span class="flex items-center gap-2"><ChefHat class="w-5 h-5 shrink-0" /><span v-show="!sidebarCollapsed">菜谱管理</span></span>
            <span v-show="!sidebarCollapsed" class="arrow transition-transform duration-300 text-xs" :class="{ 'rotate-180': subMenuOpen.recipe }">▼</span>
          </div>
          <ul class="submenu space-y-1 mt-1 overflow-hidden transition-all" :class="{ open: subMenuOpen.recipe }">
            <li><RouterLink to="/dashboard/recipe-library" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'recipe-library' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('recipe-library')"><BookOpen class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">菜谱库</span></RouterLink></li>
            <li><RouterLink to="/dashboard/dietary-profile" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'dietary-profile' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('dietary-profile')"><ClipboardList class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">饮食档案管理</span></RouterLink></li>
          </ul>
        </li>
        <li class="parent-menu">
          <div class="parent-title block px-4 py-3 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer flex justify-between items-center" @click="toggleSubMenu('health')">
            <span class="flex items-center gap-2"><HeartPulse class="w-5 h-5 shrink-0" /><span v-show="!sidebarCollapsed">健康生活</span></span>
            <span v-show="!sidebarCollapsed" class="arrow transition-transform duration-300 text-xs" :class="{ 'rotate-180': subMenuOpen.health }">▼</span>
          </div>
          <ul class="submenu space-y-1 mt-1 overflow-hidden transition-all" :class="{ open: subMenuOpen.health }">
            <li><RouterLink to="/dashboard/health-report" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'health-report' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('health-report')"><BarChart3 class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">健康报告</span></RouterLink></li>
            <li><RouterLink to="/dashboard/gym" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'gym' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('gym')"><MapPin class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">附近地图</span></RouterLink></li>
            <li><RouterLink to="/dashboard/muscle-chart" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'muscle-chart' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('muscle-chart')"><Dumbbell class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">运动管理</span></RouterLink></li>
          </ul>
        </li>
        <li class="parent-menu">
          <div class="parent-title block px-4 py-3 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer flex justify-between items-center" @click="toggleSubMenu('ai')">
            <span class="flex items-center gap-2"><Sparkles class="w-5 h-5 shrink-0" /><span v-show="!sidebarCollapsed">AI功能</span></span>
            <span v-show="!sidebarCollapsed" class="arrow transition-transform duration-300 text-xs" :class="{ 'rotate-180': subMenuOpen.ai }">▼</span>
          </div>
          <ul class="submenu space-y-1 mt-1 overflow-hidden transition-all" :class="{ open: subMenuOpen.ai }">
            <li><RouterLink to="/dashboard/ai-consult" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'ai-consult' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('ai-consult')"><MessageCircle class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">AI健康咨询</span></RouterLink></li>
            <li><RouterLink to="/dashboard/training-plan" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'training-plan' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('training-plan')"><Dumbbell class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">训练计划</span></RouterLink></li>
            <li><RouterLink to="/dashboard/articles" class="menu-item block px-4 py-2 rounded-lg hover:bg-morandi-soft text-morandi-text cursor-pointer text-sm flex items-center" :class="[{ 'menu-active': activeMenu === 'articles' }, sidebarCollapsed ? 'justify-center px-0' : '']" @click="setActiveMenu('articles')"><Newspaper class="w-5 h-5 mr-2 shrink-0" /><span v-show="!sidebarCollapsed">科普文章</span></RouterLink></li>
          </ul>
        </li>
      </ul>
    </aside>

    <!-- 右侧主区域 -->
    <div class="flex-1 flex flex-col h-screen overflow-hidden">
      <header class="sticky top-0 z-10 px-8 py-4 flex items-center justify-between shrink-0 gap-4 bg-white/95 backdrop-blur-sm border-b border-morandi-soft/50 shadow-sm">
        <div class="flex items-center gap-3">
          <button @click="sidebarCollapsed = !sidebarCollapsed" class="w-9 h-9 rounded-lg hover:bg-morandi-soft flex items-center justify-center text-morandi-text transition-colors" title="展开/收起侧边栏"><Menu class="w-5 h-5" /></button>
          <span class="text-sm text-morandi-text">当前操作：</span>
          <select
            v-model="selectedActAs"
            class="px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text text-sm outline-none focus:border-morandi-accent"
          >
            <option :value="-1">我自己</option>
            <option v-for="w in userStore.wards" :key="w.wardId" :value="w.wardId">
              替 {{ w.wardUsername }} 操作
            </option>
          </select>
          <span
            v-if="selectedActAs != -1"
            class="text-xs px-2 py-1 rounded-full bg-morandi-accent text-white"
          >
            亲属代操作模式
          </span>
        </div>
        <div class="flex items-center gap-5">
          <div class="w-10 h-10 rounded-full bg-morandi-accent flex items-center justify-center text-white font-bold text-lg overflow-hidden shrink-0">
            <img v-if="userAvatar" :src="userAvatar" class="w-full h-full object-cover" alt="头像" />
            <template v-else>{{ usernameInitial }}</template>
          </div>
          <span class="text-morandi-text font-medium">{{ usernameText }}</span>
          <button @click="handleLogout" class="px-4 py-2 rounded-lg bg-red-400 text-white hover:opacity-90 transition-opacity">
            退出登录
          </button>
        </div>
      </header>

      <!-- 内容渲染区，自带淡入动画 -->
      <main class="p-8 flex-1 overflow-auto content-fade">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter, RouterLink, useRoute } from 'vue-router'
import { useUserStore, type User } from '@/stores/user'
import { User as UserIcon, Users, Activity, FileText, UsersRound, Utensils, PlusCircle, Plus, PieChart, Search, ChefHat, BookOpen, Newspaper, ClipboardList, HeartPulse, BarChart3, MapPin, Dumbbell, Sparkles, MessageCircle, Menu } from 'lucide-vue-next'

type SubMenuKey = 'user' | 'food' | 'recipe' | 'health' | 'ai'
type MenuKey =
  | 'profile'
  | 'food-input'
  | 'food-add'
  | 'nutrition'
  | 'food-search'
  | 'family-input'
  | 'ai-consult'
  | 'training-plan'
  | 'articles'
  | 'gym'
  | 'family-relation'
  | 'metrics-history'
  | 'health-history'
  | 'recipe-library'
  | 'dietary-profile'
  | 'health-report'
  | 'muscle-chart'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const userInfo = computed(() => userStore.user || ({} as User))
const usernameText = computed(() => userInfo.value.username || '')
const userAvatar = computed(() => userStore.avatar)
const usernameInitial = computed(() => {
  const n = usernameText.value
  return n ? n.slice(0, 1).toUpperCase() : 'U'
})

// 操作身份：-1 表示自己；其他值是 ward.userId
const selectedActAs = computed({
  get: () => (userStore.actAsUserId != null ? userStore.actAsUserId : -1),
  set: (val: number) => {
    if (val === -1) {
      userStore.setActAs(null)
    } else {
      userStore.setActAs(val)
    }
    // 切换后刷新当前页面
    router.replace({ path: route.path, query: { ...(route.query || {}), _t: Date.now() } })
  }
})

// 侧边栏收起状态（默认收起）
const sidebarCollapsed = ref(true)

// 控制下拉菜单展开/收起
const subMenuOpen = reactive<Record<SubMenuKey, boolean>>({
  user: true,
  food: true,
  recipe: true,
  health: true,
  ai: true
})

// 当前激活菜单标识 - 从路由中自动提取
const pathToMenu: Record<string, MenuKey> = {
  profile: 'profile',
  'food-input': 'food-input',
  'food-add': 'food-add',
  nutrition: 'nutrition',
  'food-search': 'food-search',
  'family-input': 'family-input',
  'ai-consult': 'ai-consult',
  'training-plan': 'training-plan',
  articles: 'articles',
  gym: 'gym',
  'family-relation': 'family-relation',
  'metrics-history': 'metrics-history',
  'health-history': 'health-history',
  'recipe-library': 'recipe-library',
  'dietary-profile': 'dietary-profile',
  'health-report': 'health-report',
  'muscle-chart': 'muscle-chart'
}

const activeMenu = ref<MenuKey>('profile')

const setActiveMenu = (key: MenuKey) => {
  activeMenu.value = key
}

const toggleSubMenu = (key: SubMenuKey) => {
  // 收起态点击分组：先展开侧边栏
  if (sidebarCollapsed.value) { sidebarCollapsed.value = false }
  subMenuOpen[key] = !subMenuOpen[key]
}

watch(
  () => route.path,
  (p) => {
    const parts = p.split('/').filter(Boolean)
    const last = parts[parts.length - 1] || 'profile'
    if (pathToMenu[last]) activeMenu.value = pathToMenu[last]
  },
  { immediate: true }
)

// 退出登录
const handleLogout = () => {
  if (confirm('确定退出登录？')) {
    userStore.logout()
    router.push('/login')
  }
}

onMounted(() => {
  userStore.init()
})
</script>

<style scoped>
  .glass {
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.9);
  }
  .menu-active {
    background-color: #2F5D4A !important;
    color: white !important;
  }
  .submenu {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
  }
  .submenu.open {
    max-height: 400px;
  }
  .rotate-180 {
    transform: rotate(180deg);
  }
  .content-fade {
    animation: fadeIn 0.3s ease forwards;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>
