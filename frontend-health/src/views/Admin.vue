<template>
  <div class="page-fade max-w-7xl mx-auto">
    <!-- 顶部栏 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-morandi-text">管理员系统</h2>
      </div>
      <button @click="handleLogout" class="px-4 py-2 rounded-lg border border-morandi-soft text-sm text-morandi-text hover:bg-morandi-soft transition">
        退出登录
      </button>
    </div>

    <!-- Tab 导航 -->
    <div class="flex gap-2 mb-6 glass rounded-2xl p-2">
      <button
        v-for="t in tabs"
        :key="t.key"
        :class="['flex-1 px-4 py-3 rounded-xl text-sm font-medium transition', tab === t.key ? 'bg-morandi-accent text-white' : 'text-morandi-text hover:bg-morandi-soft']"
        @click="switchTab(t.key)"
      >{{ t.label }}</button>
    </div>

    <!-- 子组件按需渲染 -->
    <AdminUserManager v-if="tab === 'users'" />
    <AdminFoodManager v-else-if="tab === 'food-management'" />
    <AdminArticleManager v-else-if="tab === 'articles'" />
    <AdminFlowDemo v-else-if="tab === 'preview'" />
    <AdminStats v-else-if="tab === 'stats'" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import AdminUserManager from './admin/AdminUserManager.vue'
import AdminFoodManager from './admin/AdminFoodManager.vue'
import AdminArticleManager from './admin/AdminArticleManager.vue'
import AdminFlowDemo from './admin/AdminFlowDemo.vue'
import AdminStats from './admin/AdminStats.vue'

const router = useRouter()
const userStore = useUserStore()

const tabs = [
  { key: 'users', label: '用户管理' },
  { key: 'food-management', label: '食物管理' },
  { key: 'articles', label: '文章管理' },
  { key: 'preview', label: '流程演示 · 先预览后发布' },
  { key: 'stats', label: '数据统计' }
]

const tab = ref<string>('preview')

const switchTab = (key: string) => {
  tab.value = key
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.08);
}

.page-fade { animation: fadeIn 0.3s ease forwards; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
