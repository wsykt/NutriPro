<template>
  <div id="app">
    <!-- 全局底层呼吸柔光 -->
    <div class="ambient-glow ambient-glow-green"></div>
    <div class="ambient-glow ambient-glow-blue"></div>

    <!-- 顶部导航（内部应用） -->
    <nav v-if="userStore.isLoggedIn && !$route.path.startsWith('/dashboard') && !$route.path.startsWith('/admin')" class="sticky top-0 z-50 bg-white/95 backdrop-blur-sm px-6 md:px-12 py-3 border-b border-morandi-soft/50 shadow-sm">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <router-link to="/" class="text-lg font-bold text-morandi-text">HealthManage</router-link>
        <div class="hidden md:flex gap-6 text-sm font-medium">
          <router-link to="/" class="text-morandi-lightText hover:text-morandi-accent transition-colors">首页</router-link>
          <router-link to="/dashboard/food-search" class="text-morandi-lightText hover:text-morandi-accent transition-colors">食物搜索</router-link>
          <router-link to="/dashboard/food-input" class="text-morandi-lightText hover:text-morandi-accent transition-colors">录入饮食</router-link>
          <router-link to="/dashboard/nutrition" class="text-morandi-lightText hover:text-morandi-accent transition-colors">营养分析</router-link>
          <router-link to="/dashboard/profile" class="text-morandi-lightText hover:text-morandi-accent transition-colors">个人中心</router-link>
          <router-link v-if="userStore.isAdmin" to="/admin" class="text-morandi-lightText hover:text-morandi-accent transition-colors">管理后台</router-link>
        </div>
        <button @click="handleLogout" class="text-sm text-morandi-lightText hover:text-morandi-accent cursor-pointer">
          退出登录
        </button>
      </div>
    </nav>

    <div class="min-h-screen content-layer" :class="(userStore.isLoggedIn && !$route.path.startsWith('/dashboard') && !$route.path.startsWith('/admin')) ? 'py-6 md:py-8' : ''">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'

const router = useRouter()
const userStore = useUserStore()

onMounted(() => { userStore.init() })

const handleLogout = () => {
  userStore.logout()
  router.push('/')
}
</script>

<style>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
