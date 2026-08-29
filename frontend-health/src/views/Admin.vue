<template>
  <div class="ad-root" :data-mode="mode">
    <div class="ad-shell">
      <!-- ===== 星枢顶栏 ===== -->
      <header class="ad-top">
        <div class="ad-brand">
          <div class="ad-orb"><Shield :size="22" :stroke-width="1.7" /></div>
          <div class="ad-brand-tt">
            <b>管理星枢</b>
            <span>ADMIN CONSOLE</span>
          </div>
        </div>
        <div class="ad-top-r">
          <span class="ad-chip gold ad-me"><Shield :size="12" />{{ userStore.user?.username || userStore.activeUserLabel || 'admin' }}</span>
          <button class="ad-toggle" @click="toggleMode" :title="mode === 'night' ? '切换至昼阙' : '切换至夜阙'">
            <span class="ad-toggle-txt">{{ mode === 'night' ? '夜阙 NIGHT' : '昼阙 DAY' }}</span>
            <span class="ad-toggle-track" :class="{ day: mode === 'day' }"><i></i></span>
          </button>
          <button class="ad-btn" @click="handleLogout"><LogOut :size="13" />退出登录</button>
        </div>
      </header>

      <!-- ===== 模块星站导航 ===== -->
      <nav class="ad-tabs">
        <button
          v-for="t in tabs"
          :key="t.key"
          :class="['ad-tab', tab === t.key && 'hot']"
          @click="switchTab(t.key)"
        >
          <component :is="t.icon" :size="15" :stroke-width="1.8" />
          {{ t.label }}
        </button>
      </nav>

      <!-- ===== 模块内容 ===== -->
      <main class="ad-main">
        <AdminUserManager v-if="tab === 'users'" />
        <AdminFoodManager v-else-if="tab === 'food-management'" />
        <AdminArticleManager v-else-if="tab === 'articles'" />
        <AdminStats v-else-if="tab === 'stats'" />
        <AdminFlowDemo v-else-if="tab === 'ai-preview'" />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, provide, type Ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Shield, LogOut, Users, UtensilsCrossed, BookOpen, BarChart3, GitBranch } from 'lucide-vue-next'
import AdminUserManager from './admin/AdminUserManager.vue'
import AdminFoodManager from './admin/AdminFoodManager.vue'
import AdminArticleManager from './admin/AdminArticleManager.vue'
import AdminStats from './admin/AdminStats.vue'
import AdminFlowDemo from './admin/AdminFlowDemo.vue'
import './admin/admin-theme.css'

const router = useRouter()
const userStore = useUserStore()

const tabs = [
  { key: 'users', label: '用户管理', icon: Users },
  { key: 'food-management', label: '食物管理', icon: UtensilsCrossed },
  { key: 'articles', label: '文章管理', icon: BookOpen },
  { key: 'stats', label: '数据统计', icon: BarChart3 },
  { key: 'ai-preview', label: 'AI 流程展示', icon: GitBranch }
]

const tab = ref<string>('users')

// ===== 昼夜双阙换肤（方案F） =====
const MODE_KEY = 'admin-theme-mode'
const mode = ref<'night' | 'day'>(
  localStorage.getItem(MODE_KEY) === 'day' ? 'day' : 'night'
)
provide('adminMode', mode as Ref<'night' | 'day'>)

const toggleMode = () => {
  mode.value = mode.value === 'night' ? 'day' : 'night'
  localStorage.setItem(MODE_KEY, mode.value)
}

const switchTab = (key: string) => {
  tab.value = key
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
/* ===== 顶栏 ===== */
.ad-top { display: flex; align-items: center; gap: 16px; }
.ad-brand { display: flex; align-items: center; gap: 15px; }
.ad-orb {
  width: 52px; height: 52px; border-radius: 50%;
  display: grid; place-items: center;
  background: var(--ad-orb); color: var(--ad-orb-ic);
  border: 1px solid var(--ad-line);
  box-shadow: 0 0 26px var(--ad-accent-soft), inset 0 0 12px var(--ad-accent-soft);
}
.ad-brand-tt b {
  display: block; font-family: 'Noto Serif SC', serif;
  font-size: 21px; color: var(--ad-title); letter-spacing: 0.14em; line-height: 1.25;
}
.ad-brand-tt span { font-size: 9.5px; letter-spacing: 0.42em; color: var(--ad-sub); }
.ad-top-r { margin-left: auto; display: flex; align-items: center; gap: 12px; }
.ad-me { font-size: 12px; padding: 6px 14px; }

/* ===== 昼夜切换 ===== */
.ad-toggle {
  display: inline-flex; align-items: center; gap: 10px;
  background: none; border: none; cursor: pointer;
  color: var(--ad-sub); font-size: 12px; letter-spacing: 0.1em; font-family: inherit;
}
.ad-toggle-txt { min-width: 78px; text-align: right; }
.ad-toggle-track {
  width: 50px; height: 26px; border-radius: 999px;
  background: var(--ad-accent-soft); border: 1px solid var(--ad-accent);
  position: relative; display: inline-block; transition: 0.35s;
}
.ad-toggle-track i {
  position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%;
  background: var(--ad-accent); box-shadow: 0 0 8px var(--ad-accent);
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.ad-toggle-track.day i { left: 27px; box-shadow: none; }
.ad-toggle:hover .ad-toggle-txt { color: var(--ad-accent); }

/* ===== 模块星站导航 ===== */
.ad-tabs { display: flex; gap: 10px; margin: 26px 0 20px; }
.ad-tab {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 13px; border-radius: 14px;
  border: 1px solid var(--ad-line); background: var(--ad-card);
  color: var(--ad-sub); font-size: 13.5px; letter-spacing: 0.15em;
  cursor: pointer; transition: all 0.3s; font-family: inherit;
}
.ad-tab:hover { color: var(--ad-accent); transform: translateY(-2px); }
.ad-tab.hot {
  color: var(--ad-accent); border-color: var(--ad-accent);
  background: var(--ad-accent-soft); font-weight: 600;
  box-shadow: 0 0 20px var(--ad-accent-soft);
}

/* ===== 内容入场 ===== */
.ad-main > :deep(*) { animation: adRise 0.5s cubic-bezier(0.22, 0.68, 0.36, 1) backwards; }
@keyframes adRise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: none; }
}

@media (max-width: 860px) {
  .ad-root { padding: 22px 16px 48px; }
  .ad-tabs { flex-wrap: wrap; }
  .ad-tab { flex: 1 1 40%; }
  .ad-toggle-txt { display: none; }
}
</style>
