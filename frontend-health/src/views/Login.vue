<template>
  <div class="content-layer min-h-screen text-morandi-text page-fade-in">
    <!-- 顶部导航 -->
    <header class="sticky top-0 z-50 glass px-6 md:px-12 py-4">
      <nav class="max-w-7xl mx-auto flex items-center justify-between">
        <router-link to="/" class="text-xl font-bold tracking-tight flex items-center gap-2.5">
          <span class="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-base" style="background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%)">健</span>
          <span>HealthManage</span>
        </router-link>
        <ul class="hidden md:flex gap-8 text-sm font-medium text-morandi-lightText">
          <li><router-link to="/" class="hover:text-morandi-accent transition-colors">返回首页</router-link></li>
        </ul>
        <router-link to="/register" class="px-5 py-2 rounded-lg text-white text-sm font-medium transition-all hover:opacity-90 shadow-md" style="background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%)">
          立即注册
        </router-link>
      </nav>
    </header>

    <!-- 主体 -->
    <main class="max-w-7xl mx-auto px-6 md:px-12 py-12 md:py-20">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
        <!-- 左侧介绍 -->
        <div class="hidden md:block">
          <h1 class="text-4xl font-bold leading-tight mb-6" style="font-family: 'Noto Serif SC', 'Source Han Serif SC', serif">
            欢迎回来 👋<br />
            <span class="text-morandi-accent">继续记录你的健康数据</span>
          </h1>
          <p class="text-morandi-lightText leading-relaxed mb-8 text-base">
            登录后你可以查看你的体重趋势、每日营养摄入、运动记录等数据，并获得基于 AI 的个性化健康建议。
          </p>

          <div class="space-y-4">
            <div class="glass rounded-2xl p-5 flex items-start gap-4 hover:-translate-y-0.5 transition-transform duration-300">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background:#E4EDE7;color:#2F5D4A"><component :is="BarChart3" class="w-5 h-5" /></div>
              <div>
                <h3 class="font-semibold mb-1">营养与运动分析</h3>
                <p class="text-sm text-morandi-lightText">自动统计每日热量、蛋白质、脂肪、碳水摄入</p>
              </div>
            </div>
            <div class="glass rounded-2xl p-5 flex items-start gap-4 hover:-translate-y-0.5 transition-transform duration-300">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background:#FBE9DC;color:#E07A3F"><component :is="Brain" class="w-5 h-5" /></div>
              <div>
                <h3 class="font-semibold mb-1">AI 健康建议</h3>
                <p class="text-sm text-morandi-lightText">基于你的身体数据，智能生成个性化建议</p>
              </div>
            </div>
            <div class="glass rounded-2xl p-5 flex items-start gap-4 hover:-translate-y-0.5 transition-transform duration-300">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background:#E4EDE7;color:#2F5D4A"><component :is="TrendingUp" class="w-5 h-5" /></div>
              <div>
                <h3 class="font-semibold mb-1">亲属代录入</h3>
                <p class="text-sm text-morandi-lightText">可记录父母、子女等家属的健康数据，统一管理</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧登录表单 -->
        <div class="glass rounded-2xl p-8 md:p-10 shadow-lg w-full max-w-md mx-auto">
          <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4" style="background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%)"><component :is="Shield" class="w-7 h-7 text-white" /></div>
            <h1 class="text-2xl font-bold text-morandi-text mb-2" style="font-family: 'Noto Serif SC', serif">登录账号</h1>
            <p class="text-sm text-morandi-lightText">输入你的用户名和密码以继续</p>
          </div>

          <form @submit.prevent="handleLogin" class="space-y-5">
            <div>
              <label class="block text-sm font-medium text-morandi-text mb-2">用户名</label>
              <input
                v-model="username"
                type="text"
                required
                class="w-full px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors"
                placeholder="请输入用户名"
              />
            </div>

            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="block text-sm font-medium text-morandi-text">密码</label>
                <button type="button" @click="router.push('/forgot-password')" class="text-xs text-morandi-lightText hover:text-morandi-accent">忘记密码？</button>
              </div>
              <input
                v-model="password"
                type="password"
                required
                @keydown.enter.prevent="handleLogin"
                class="w-full px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors"
                placeholder="请输入密码"
              />
            </div>

            <button
              type="button"
              @click="handleLogin"
              :disabled="loading"
              class="w-full py-3 rounded-xl text-white font-medium transition-all disabled:opacity-60 disabled:cursor-not-allowed shadow-md hover:opacity-90"
              style="background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%)"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </button>

            <p v-if="error" class="text-center text-sm text-red-500">{{ error }}</p>
          </form>

          <div class="text-center mt-6 text-sm text-morandi-lightText">
            还没有账号？
            <router-link to="/register" class="text-morandi-accent font-medium hover:underline ml-1">立即注册</router-link>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { BarChart3, Brain, Shield, TrendingUp } from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    const result: any = await userStore.login(username.value, password.value)
    if (result?.success) {
      if (userStore.isAdmin) {
        router.push('/admin')
      } else {
        // 首次登录引导：读 localStorage + 后端 first_login 字段（移植自 health1）
        await userStore.loadUserProfile?.()
        const userId = userStore.user?.user_id || userStore.user?.userId || userStore.user?.id
        const uname = userStore.user?.username

        let storedFirstLogin: string | null = null
        if (userId != null && uname) {
          const raw = localStorage.getItem(`first_login_${userId}`)
          if (raw) {
            try {
              const parsed = JSON.parse(raw)
              if (parsed && parsed.username === uname && parsed.value != null) {
                storedFirstLogin = String(parsed.value)
              }
            } catch {
              const byUser = localStorage.getItem(`first_login_user_${uname}`)
              if (byUser !== null) storedFirstLogin = byUser
            }
          }
        }
        if (storedFirstLogin === null && uname) {
          storedFirstLogin = localStorage.getItem(`first_login_user_${uname}`)
        }

        const backendFirstLogin = (userStore.user as any)?.first_login ?? (userStore.user as any)?.firstLogin

        if (storedFirstLogin === '0') {
          router.push('/dashboard')
        } else if (backendFirstLogin === 1 || storedFirstLogin === '1') {
          router.push('/onboarding')
        } else {
          userStore.setFirstLogin(0)
          router.push('/dashboard')
        }
      }
    } else {
      error.value = result?.message || '用户名或密码错误'
    }
  } catch (e: any) {
    error.value = e?.response?.data?.message || e?.message || '登录失败，请稍后再试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
  .glass {
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.9);
  }
  .gradient-bg {
    background: #ffffff;
  }
  .page-fade-in {
    animation: pageFade 0.8s ease-out forwards;
  }
  @keyframes pageFade {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>