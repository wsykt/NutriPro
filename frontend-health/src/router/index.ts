import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router'
import { getToken, setToken, setCurrentUserId } from '@/utils/storage'
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
  { path: '/admin', name: 'Admin', component: () => import('@/views/Admin.vue'), meta: { requiresAuth: true } },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true },
    redirect: '/dashboard/profile',
    children: [
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
      { path: 'gym', component: () => import('@/views/dashboard/NearGym.vue') },
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

// 登录鉴权守卫 - 开发模式：绕过登录，直接注入模拟用户
router.beforeEach((to, _from, next) => {
  // 开发模式：自动设置模拟登录态（仅 npm run dev 时生效，生产构建自动关闭）
  const DEV_MODE = import.meta.env.DEV
  if (DEV_MODE) {
    if (!getToken()) {
      setToken('dev-mock-token')
      setCurrentUserId(1)
    }
  }

  const token = getToken()
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/' && token) {
    // 已登录用户访问首页时，跳转到 dashboard，避免两个导航栏叠加
    next('/dashboard')
  } else {
    next()
  }
})

export default router
