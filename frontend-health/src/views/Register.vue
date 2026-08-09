<template>
  <div class="content-layer min-h-screen text-morandi-text page-fade-in">
    <!-- 顶部导航 -->
    <header class="sticky top-0 z-50 glass px-6 md:px-12 py-4">
      <nav class="max-w-7xl mx-auto flex items-center justify-between">
        <router-link to="/" class="text-xl font-bold tracking-tight">HealthManage</router-link>
        <ul class="hidden md:flex gap-8 text-sm font-medium text-morandi-lightText">
          <li><router-link to="/" class="hover:text-morandi-accent">返回首页</router-link></li>
        </ul>
        <router-link to="/login" class="px-5 py-2 rounded-lg bg-morandi-accent text-white text-sm font-medium">
          去登录
        </router-link>
      </nav>
    </header>

    <!-- 主体 -->
    <main class="max-w-7xl mx-auto px-6 md:px-12 py-12 md:py-16">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
        <!-- 左侧介绍 -->
        <div class="hidden md:block md:sticky md:top-28">
          <h1 class="text-4xl font-bold leading-tight mb-6">
            开始你的健康之旅 ✨<br />
            <span class="text-morandi-accent">创建你的专属账号</span>
          </h1>
          <p class="text-morandi-lightText leading-relaxed mb-8 text-base">
            完善个人信息后，系统将为你计算每日推荐摄入量，并通过 AI 给出个性化健康建议。
          </p>

          <div class="space-y-4">
            <div class="glass rounded-2xl p-5 flex items-start gap-4">
              <div class="w-10 h-10 rounded-xl bg-morandi-accent/15 text-morandi-accent flex items-center justify-center text-xl">🍎</div>
              <div>
                <h3 class="font-semibold mb-1">膳食营养记录</h3>
                <p class="text-sm text-morandi-lightText">支持上百种食物的热量与营养计算</p>
              </div>
            </div>
            <div class="glass rounded-2xl p-5 flex items-start gap-4">
              <div class="w-10 h-10 rounded-xl bg-morandi-accent/15 text-morandi-accent flex items-center justify-center text-xl">🏃</div>
              <div>
                <h3 class="font-semibold mb-1">多样化人群适配</h3>
                <p class="text-sm text-morandi-lightText">青少年、老年人、孕妇等人群均可使用，记录个性化数据</p>
              </div>
            </div>
            <div class="glass rounded-2xl p-5 flex items-start gap-4">
              <div class="w-10 h-10 rounded-xl bg-morandi-accent/15 text-morandi-accent flex items-center justify-center text-xl">🧘</div>
              <div>
                <h3 class="font-semibold mb-1">个性化健康方案</h3>
                <p class="text-sm text-morandi-lightText">基于你的身高体重与人群类型</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧注册表单 -->
        <div class="glass rounded-2xl p-8 md:p-10 shadow-lg w-full max-w-lg mx-auto">
          <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-morandi-accent/15 text-morandi-accent text-2xl mb-4">🌱</div>
            <h1 class="text-2xl font-bold text-morandi-text mb-2">创建新账号</h1>
            <p class="text-sm text-morandi-lightText">完善以下信息，立即开启你的健康管理</p>
          </div>

          <form @submit.prevent="handleRegister" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-morandi-text mb-2">用户名</label>
              <input v-model="form.username" type="text" required
                class="w-full px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors"
                placeholder="请输入用户名" />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-morandi-text mb-2">密码</label>
                <div class="relative">
                  <input v-model="form.password" :type="showPassword ? 'text' : 'password'" required minlength="6"
                    class="w-full px-4 py-3 pr-11 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors"
                    placeholder="至少 6 位" />
                  <button type="button" @click="showPassword = !showPassword"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-morandi-lightText hover:text-morandi-accent text-sm select-none"
                    tabindex="-1">
                    {{ showPassword ? '隐藏' : '显示' }}
                  </button>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-morandi-text mb-2">性别</label>
                <select v-model="form.gender"
                  class="w-full px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors">
                  <option value="男">男</option>
                  <option value="女">女</option>
                </select>
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label class="block text-sm font-medium text-morandi-text mb-2">身高 (cm)</label>
                <input v-model.number="form.height" type="number" min="50" max="250"
                  class="w-full px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors" />
              </div>
              <div>
                <label class="block text-sm font-medium text-morandi-text mb-2">体重 (kg)</label>
                <input v-model.number="form.weight" type="number" min="20" max="300"
                  class="w-full px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors" />
              </div>
              <div>
                <label class="block text-sm font-medium text-morandi-text mb-2">年龄</label>
                <input v-model.number="form.age" type="number" min="1" max="120"
                  class="w-full px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors" />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-morandi-text mb-2">人群类型</label>
              <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <button
                  v-for="item in crowdOptions"
                  :key="item.value"
                  type="button"
                  @click="form.crowdType = item.value"
                  :class="[
                    'px-3 py-2 rounded-xl text-sm transition-all border',
                    form.crowdType === item.value
                      ? 'bg-morandi-accent text-white border-morandi-accent shadow-md'
                      : 'bg-white/70 border-morandi-soft text-morandi-text hover:border-morandi-accent'
                  ]"
                >
                  {{ item.label }}
                </button>
              </div>
            </div>

            <button type="submit" :disabled="loading"
              class="w-full py-3 rounded-xl bg-morandi-accent text-white font-medium hover:opacity-90 transition-all disabled:opacity-60 disabled:cursor-not-allowed shadow-md">
              {{ loading ? '注册中...' : '注 册' }}
            </button>

            <p v-if="error" class="text-center text-sm text-red-500">{{ error }}</p>
            <p v-if="successMsg" class="text-center text-sm text-morandi-accent">{{ successMsg }}</p>
          </form>

          <div class="text-center mt-6 text-sm text-morandi-lightText">
            已有账号？
            <router-link to="/login" class="text-morandi-accent font-medium hover:underline ml-1">立即登录</router-link>
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
import { CROWD_OPTIONS } from '../constants'

const router = useRouter()
const userStore = useUserStore()
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')
const successMsg = ref('')

const crowdOptions = [...CROWD_OPTIONS]

const form = ref({
  username: '',
  password: '',
  gender: '男',
  height: 170,
  weight: 65,
  age: 20,
  crowdType: '普通人'
})

const handleRegister = async () => {
  loading.value = true
  error.value = ''
  successMsg.value = ''
  try {
    const result: any = await userStore.register(form.value)
    if (result?.success) {
      successMsg.value = '注册成功，即将跳转登录页...'
      setTimeout(() => router.push('/login'), 1200)
    } else {
      error.value = result?.message || '注册失败，请稍后重试'
    }
  } catch (e: any) {
    error.value = e?.response?.data?.message || e?.message || '注册失败，请稍后再试'
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
    background: linear-gradient(135deg, #f8fbf9 0%, #eff7f3 100%);
  }
  .page-fade-in {
    animation: pageFade 0.8s ease-out forwards;
  }
  @keyframes pageFade {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>
