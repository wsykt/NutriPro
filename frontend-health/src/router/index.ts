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
      // 首页（组件命名：HomePageDashboard）
      { path: 'home', component: () => import('@/views/dashboard/HomePageDashboard.vue') },
      { path: 'demo', redirect: '/dashboard/home' },

      // ===== 个人中心（Tab：个人资料 / 饮食偏好） =====
      { path: 'profile', component: () => import('@/views/dashboard/ProfileTab.vue') },
      { path: 'dietary-profile', redirect: { path: '/dashboard/profile', query: { tab: 'dietary' } } },

      // ===== 家庭管理（Tab：成员关系 / 代录饮食） =====
      { path: 'family', component: () => import('@/views/dashboard/FamilyManage.vue') },
      { path: 'family-relation', redirect: { path: '/dashboard/family', query: { tab: 'relation' } } },
      { path: 'family-input', redirect: { path: '/dashboard/family', query: { tab: 'input' } } },

      // ===== 饮食记录（Tab：记录三餐 / 食物查询 / 自定义食物） =====
      { path: 'food-input', component: () => import('@/views/dashboard/FoodInputTab.vue') },
      { path: 'food-search', redirect: { path: '/dashboard/food-input', query: { tab: 'search' } } },
      { path: 'food-add', redirect: { path: '/dashboard/food-input', query: { tab: 'add' } } },
      { path: 'nutrition', component: () => import('@/views/dashboard/Nutrition.vue') },

      // ===== 健康档案（Tab：身体指标 / 健康记录） =====
      { path: 'health-archive', component: () => import('@/views/dashboard/HealthArchive.vue') },
      { path: 'metrics-history', redirect: { path: '/dashboard/health-archive', query: { tab: 'metrics' } } },
      { path: 'health-history', redirect: { path: '/dashboard/health-archive', query: { tab: 'records' } } },

      // ===== 健康监测 =====
      { path: 'health-report', component: () => import('@/views/dashboard/HealthReport.vue') },
      // 运动管理（Tab：围度图表 / 训练计划）
      { path: 'muscle-chart', component: () => import('@/views/dashboard/MuscleChartTab.vue') },
      { path: 'training-plan', redirect: { path: '/dashboard/muscle-chart', query: { tab: 'training' } } },

      // ===== 知识中心 =====
      { path: 'articles', component: () => import('@/views/dashboard/Articles.vue') },
      { path: 'article-detail/:id', component: () => import('@/views/dashboard/ArticleDetail.vue') },
      { path: 'ai-consult', component: () => import('@/views/dashboard/AiConsult.vue') },

      // ===== 菜谱美食 =====
      { path: 'recipe-library', component: () => import('@/views/dashboard/RecipeLibrary.vue') },
      { path: 'recipe-detail/:id', component: () => import('@/views/dashboard/RecipeDetail.vue') },

      // 开发辅助页面（不在菜单中展示）
      { path: 'icon-gallery', component: () => import('@/views/dashboard/IconGallery.vue') },

      // ===== 已合并的历史 redirect =====
      { path: 'ai-chat', redirect: '/dashboard/ai-consult' },
      { path: 'feature-hub', redirect: '/dashboard/profile' },
      { path: 'health-education', redirect: '/dashboard/articles' },
      { path: 'recipe-search', redirect: '/dashboard/recipe-library' },
      { path: 'community', redirect: '/dashboard/profile' },
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

