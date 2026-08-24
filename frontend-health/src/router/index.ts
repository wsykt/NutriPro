import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router'
import { getToken, setToken, setCurrentUserId } from '@/utils/storage'
import { useUserStore } from '@/stores/user'
import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import ForgotPassword from '@/views/ForgotPassword.vue'
import Dashboard from '@/views/Dashboard.vue'

const routes: Array<RouteRecordRaw> = [
  { path: '/', name: 'Home', component: Home },
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register },
  { path: '/forgot-password', name: 'ForgotPassword', component: ForgotPassword },
  { path: '/onboarding', name: 'Onboarding', component: () => import('@/views/Onboarding.vue'), meta: { requiresAuth: true } },
  { path: '/admin', name: 'Admin', component: () => import('@/views/Admin.vue'), meta: { requiresAuth: true } },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true },
    redirect: '/dashboard/home',
    children: [
      { path: 'hub', component: () => import('@/views/dashboard/FeatureHub.vue') },
      // 首页（原 demo 命名，已更名 home；保留旧路径重定向兼容历史链接）
      { path: 'home', component: () => import('@/views/dashboard/DashboardDemo.vue') },
      { path: 'demo', redirect: '/dashboard/home' },
      { path: 'profile', component: () => import('@/views/dashboard/Profile.vue') },
      { path: 'food-input', component: () => import('@/views/dashboard/FoodInput.vue') },
      { path: 'food-add', component: () => import('@/views/dashboard/FoodAdd.vue') },
      { path: 'nutrition', component: () => import('@/views/dashboard/Nutrition.vue') },
      { path: 'food-search', component: () => import('@/views/dashboard/FoodSearch.vue') },
      { path: 'family-input', component: () => import('@/views/dashboard/FamilyFoodInput.vue') },
      { path: 'ai-consult', component: () => import('@/views/dashboard/AiConsult.vue') },
      { path: 'training-plan', component: () => import('@/views/dashboard/TrainingPlan.vue') },
      // 已合并：AI对话助手 → AI健康咨询
      { path: 'ai-chat', redirect: '/dashboard/ai-consult' },
      // 已合并：功能中心 → 个人中心
      { path: 'feature-hub', redirect: '/dashboard/profile' },
      // 已合并：健康教育 → 科普文章
      { path: 'health-education', redirect: '/dashboard/articles' },
      { path: 'family-relation', component: () => import('@/views/dashboard/FamilyRelation.vue') },
      { path: 'metrics-history', component: () => import('@/views/dashboard/MetricsHistory.vue') },
      { path: 'health-history', component: () => import('@/views/dashboard/HealthHistory.vue') },
      // 已合并：菜谱搜索 → 菜谱库
      { path: 'recipe-search', redirect: '/dashboard/recipe-library' },
      { path: 'recipe-detail/:id', component: () => import('@/views/dashboard/RecipeDetail.vue') },
      { path: 'recipe-library', component: () => import('@/views/dashboard/RecipeLibrary.vue') },
      { path: 'dietary-profile', component: () => import('@/views/dashboard/DietaryProfile.vue') },
      { path: 'health-report', component: () => import('@/views/dashboard/HealthReport.vue') },
      { path: 'muscle-chart', component: () => import('@/views/dashboard/MuscleChart.vue') },
      { path: 'articles', component: () => import('@/views/dashboard/Articles.vue') },
      { path: 'article-detail/:id', component: () => import('@/views/dashboard/ArticleDetail.vue') },
      // 开发辅助页面（不在菜单中展示）
      { path: 'icon-gallery', component: () => import('@/views/dashboard/IconGallery.vue') },
      // 已移除：社区交流 → 个人中心
      { path: 'community', redirect: '/dashboard/profile' }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,

  scrollBehavior() {
    return { top: 0 }
  }
})

// 登录鉴权守卫 - 开发模式：仅在访问受保护路由且无 token 时注入模拟登录态
// （不对公开页/项目介绍首页(/)/登录页强制注入，否则未登录永远看不到介绍页，且登出后立刻被 mock 复活）
router.beforeEach(async (to, _from, next) => {
  const DEV_MODE = import.meta.env.DEV
  let justInjected = false
  if (DEV_MODE && to.meta.requiresAuth && !getToken()) {
    setToken('dev-mock-token')
    setCurrentUserId(1)
    justInjected = true
  }

  const token = getToken()
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }

  // 管理后台路由守卫：仅 admin 角色可访问
  if (to.path === '/admin') {
    const userStore = useUserStore()
    // 刷新页面时 store 尚未初始化，先拉取用户信息再判断
    if (!userStore.user && token) {
      await userStore.init()
    }
    if (!userStore.isAdmin) {
      next('/dashboard')
      return
    }
  }

  if (to.path === '/' && token && !justInjected) {
    // 已登录用户访问首页时，跳转到 dashboard，避免两个导航栏叠加
    next('/dashboard')
    return
  }
  next()
})

export default router

