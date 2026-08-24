<template>
  <div class="content-layer min-h-screen text-morandi-text page-fade-in">
    <!-- 顶部导航 -->
    <header class="sticky top-0 z-50 glass px-6 md:px-12 py-4">
      <nav class="max-w-7xl mx-auto flex items-center justify-between">
        <router-link to="/" class="text-xl font-bold tracking-tight">HealthManage</router-link>
        <div class="flex items-center gap-4">
          <router-link to="/login" class="text-sm text-morandi-lightText hover:text-morandi-accent">返回登录</router-link>
          <router-link to="/register" class="px-5 py-2 rounded-lg bg-morandi-accent text-white text-sm font-medium">
            去注册
          </router-link>
        </div>
      </nav>
    </header>

    <!-- 主体 -->
    <main class="max-w-7xl mx-auto px-6 md:px-12 py-12 md:py-20">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
        <!-- 左侧说明 -->
        <div class="hidden md:block">
          <h1 class="text-4xl font-bold leading-tight mb-6">
            重置密码 <br />
            <span class="text-morandi-accent">快速恢复你的账号</span>
          </h1>
          <p class="text-morandi-lightText leading-relaxed mb-8 text-base">
            输入用户名、当前密码和新密码，系统将校验身份并帮你重置登录密码。
          </p>

          <div class="space-y-4">
            <div class="glass rounded-2xl p-5 flex items-start gap-4">
              <div class="w-10 h-10 rounded-xl bg-morandi-accent/15 text-morandi-accent flex items-center justify-center text-xl">1</div>
              <div>
                <h3 class="font-semibold mb-1">输入用户名</h3>
                <p class="text-sm text-morandi-lightText">请填写你之前注册时使用的用户名</p>
              </div>
            </div>
            <div class="glass rounded-2xl p-5 flex items-start gap-4">
              <div class="w-10 h-10 rounded-xl bg-morandi-accent/15 text-morandi-accent flex items-center justify-center text-xl">2</div>
              <div>
                <h3 class="font-semibold mb-1">设置新密码</h3>
                <p class="text-sm text-morandi-lightText">两次输入一致，长度至少 6 位</p>
              </div>
            </div>
            <div class="glass rounded-2xl p-5 flex items-start gap-4">
              <div class="w-10 h-10 rounded-xl bg-morandi-accent/15 text-morandi-accent flex items-center justify-center text-xl">3</div>
              <div>
                <h3 class="font-semibold mb-1">提交重置</h3>
                <p class="text-sm text-morandi-lightText">成功后会自动跳转到登录页面</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧表单 -->
        <div class="glass rounded-2xl p-8 md:p-10 shadow-lg w-full max-w-md mx-auto">
          <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-morandi-accent/15 text-morandi-accent text-2xl mb-4"></div>
            <h1 class="text-2xl font-bold text-morandi-text mb-2">重置密码</h1>
            <p class="text-sm text-morandi-lightText">输入用户名与新密码以完成密码重置</p>
          </div>

          <form @submit.prevent="handleReset" class="space-y-5">
            <div>
              <label class="block text-sm font-medium text-morandi-text mb-2">用户名</label>
              <input
                v-model="form.username"
                type="text"
                required
                class="w-full px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors"
                placeholder="请输入用户名"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-morandi-text mb-2">当前密码</label>
              <input
                v-model="form.oldPassword"
                type="password"
                required
                class="w-full px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors"
                placeholder="为保护账号安全，需验证当前密码"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-morandi-text mb-2">新密码</label>
              <input
                v-model="form.newPassword"
                type="password"
                required
                minlength="6"
                class="w-full px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors"
                placeholder="至少 6 位"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-morandi-text mb-2">确认新密码</label>
              <input
                v-model="form.confirmPassword"
                type="password"
                required
                minlength="6"
                class="w-full px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors"
                placeholder="请再次输入新密码"
              />
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full py-3 rounded-xl bg-morandi-accent text-white font-medium hover:opacity-90 transition-all disabled:opacity-60 disabled:cursor-not-allowed shadow-md"
            >
              {{ loading ? '提交中...' : '重置密码' }}
            </button>

            <p v-if="error" class="text-center text-sm text-red-500">{{ error }}</p>
            <p v-if="successMsg" class="text-center text-sm text-morandi-accent">{{ successMsg }}</p>
          </form>

          <div class="text-center mt-6 text-sm text-morandi-lightText">
            想起来了？
            <router-link to="/login" class="text-morandi-accent font-medium hover:underline ml-1">返回登录</router-link>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const successMsg = ref('')

const form = ref({
  username: '',
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const handleReset = async () => {
  error.value = ''
  successMsg.value = ''

  if (!form.value.oldPassword) {
    error.value = '请输入当前密码'
    return
  }
  if (form.value.newPassword !== form.value.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }
  if (form.value.newPassword.length < 6) {
    error.value = '新密码长度至少 6 位'
    return
  }

  loading.value = true
  try {
    const result: any = await api.auth.resetPassword({
      username: form.value.username,
      oldPassword: form.value.oldPassword,
      newPassword: form.value.newPassword
    })
    successMsg.value = '密码重置成功，即将跳转登录页...'
    setTimeout(() => router.push('/login'), 1200)
  } catch (e: any) {
    error.value = e?.response?.data?.message || e?.message || '重置失败，请稍后重试'
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
