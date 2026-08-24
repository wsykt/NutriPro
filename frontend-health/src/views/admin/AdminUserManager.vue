<template>
  <div class="glass rounded-2xl p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-morandi-text">用户管理</h3>
      <span class="text-xs text-morandi-lightText">共 {{ users.length }} 位用户</span>
    </div>

    <div v-if="userLoading" class="text-center text-sm text-morandi-lightText py-16">加载中...</div>

    <div v-else class="overflow-x-auto food-table-body rounded-xl">
      <table class="min-w-full text-sm text-left text-morandi-text">
        <thead class="text-xs text-morandi-lightText" style="background: rgba(248,246,244,0.9)">
          <tr>
            <th class="px-4 py-3 font-semibold">ID</th>
            <th class="px-4 py-3 font-semibold">用户名</th>
            <th class="px-4 py-3 font-semibold">性别</th>
            <th class="px-4 py-3 font-semibold">年龄</th>
            <th class="px-4 py-3 font-semibold">人群类型</th>
            <th class="px-4 py-3 font-semibold">监护人</th>
            <th class="px-4 py-3 font-semibold">被监护人</th>
            <th class="px-4 py-3 font-semibold text-right">角色</th>
            <th class="px-4 py-3 font-semibold text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.userId" class="food-row">
            <td class="px-4 py-3">{{ u.userId }}</td>
            <td class="px-4 py-3 font-medium">{{ u.username }}</td>
            <td class="px-4 py-3">{{ u.gender || '-' }}</td>
            <td class="px-4 py-3">{{ u.age || '-' }}</td>
            <td class="px-4 py-3">{{ u.crowdType || '-' }}</td>
            <td class="px-4 py-3 text-xs">
              <span v-if="u.guardians && u.guardians.length">{{ u.guardians.join(', ') }}</span>
              <span v-else class="text-morandi-lightText">无</span>
            </td>
            <td class="px-4 py-3 text-xs">
              <span v-if="u.wards && u.wards.length">{{ u.wards.join(', ') }}</span>
              <span v-else class="text-morandi-lightText">无</span>
            </td>
            <td class="px-4 py-3 text-right">
              <span :class="['px-2 py-1 rounded text-xs font-medium', u.role === 'admin' ? 'bg-morandi-accent text-white' : 'bg-morandi-soft text-morandi-text']">
                {{ u.role === 'admin' ? '管理员' : '普通用户' }}
              </span>
            </td>
            <td class="px-4 py-3 text-center">
              <div class="flex gap-1 justify-center flex-wrap">
                <button @click="viewUser(u.userId)" class="px-2 py-1 text-xs rounded bg-morandi-accent text-white hover:opacity-90">查看</button>
                <button @click="deleteUser(u)" :disabled="u.role === 'admin'" :class="['px-2 py-1 text-xs rounded border', u.role === 'admin' ? 'border-morandi-soft text-morandi-lightText opacity-50 cursor-not-allowed' : 'border-red-300 text-red-600 hover:bg-red-50']">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="9" class="px-4 py-8 text-center text-morandi-lightText text-sm">暂无用户数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ===================== 查看用户信息弹窗 ===================== -->
  <div
    v-if="viewUserModal.open"
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    style="background: rgba(0, 0, 0, 0.4)"
    @click.self="closeViewUserModal"
  >
    <div class="glass rounded-2xl p-6 max-w-xl w-full max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-morandi-text">用户详细信息</h3>
        <button @click="closeViewUserModal" class="text-morandi-lightText hover:text-morandi-text text-2xl leading-none">×</button>
      </div>

      <div v-if="viewUserModal.loading" class="text-center text-sm text-morandi-lightText py-12">加载中...</div>

      <template v-else-if="viewUserModal.data">
        <div class="space-y-4">
          <div class="flex items-center gap-4 p-4 rounded-xl bg-white/70 border border-morandi-soft">
            <div class="w-14 h-14 rounded-full bg-morandi-accent flex items-center justify-center text-white font-bold text-xl">
              {{ (viewUserModal.data.username || 'U').charAt(0).toUpperCase() }}
            </div>
            <div>
              <p class="font-semibold text-morandi-text text-lg">{{ viewUserModal.data.username }}</p>
              <p class="text-xs text-morandi-lightText mt-1">
                用户 ID：{{ viewUserModal.data.userId }} ·
                角色：{{ viewUserModal.data.role === 'admin' ? '管理员' : '普通用户' }}
              </p>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="p-3 rounded-xl bg-white/70 border border-morandi-soft">
              <p class="text-xs text-morandi-lightText">性别</p>
              <p class="text-sm font-medium text-morandi-text mt-1">{{ viewUserModal.data.gender || '-' }}</p>
            </div>
            <div class="p-3 rounded-xl bg-white/70 border border-morandi-soft">
              <p class="text-xs text-morandi-lightText">年龄</p>
              <p class="text-sm font-medium text-morandi-text mt-1">{{ viewUserModal.data.age ?? '-' }}</p>
            </div>
            <div class="p-3 rounded-xl bg-white/70 border border-morandi-soft">
              <p class="text-xs text-morandi-lightText">身高 (cm)</p>
              <p class="text-sm font-medium text-morandi-text mt-1">{{ viewUserModal.data.height ?? '-' }}</p>
            </div>
            <div class="p-3 rounded-xl bg-white/70 border border-morandi-soft">
              <p class="text-xs text-morandi-lightText">体重 (kg)</p>
              <p class="text-sm font-medium text-morandi-text mt-1">{{ viewUserModal.data.weight ?? '-' }}</p>
            </div>
          </div>

          <div class="p-4 rounded-xl bg-white/70 border border-morandi-soft">
            <p class="text-sm font-medium text-morandi-text mb-3">身体指标计算</p>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <p class="text-xs text-morandi-lightText">BMI 指数</p>
                <p class="text-xl font-bold text-morandi-accent mt-1">{{ viewUserModal.data.bmi ?? '-' }}</p>
                <p class="text-xs text-morandi-lightText mt-1">{{ viewUserModal.data.bmiStatus || '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-morandi-lightText">基础代谢 BMR (kcal)</p>
                <p class="text-xl font-bold text-morandi-accent mt-1">{{ viewUserModal.data.bmr ?? '-' }}</p>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="p-3 rounded-xl bg-white/70 border border-morandi-soft">
              <p class="text-xs text-morandi-lightText">人群类型</p>
              <p class="text-sm font-medium text-morandi-text mt-1">{{ viewUserModal.data.crowdType || '-' }}</p>
            </div>
            <div class="p-3 rounded-xl bg-white/70 border border-morandi-soft">
              <p class="text-xs text-morandi-lightText">注册时间</p>
              <p class="text-sm font-medium text-morandi-text mt-1">{{ viewUserModal.data.createdAt || '-' }}</p>
            </div>
          </div>
        </div>
      </template>

      <div v-if="viewUserModal.error" class="mt-4 text-xs text-red-600 p-3 rounded-lg bg-red-50 border border-red-200">{{ viewUserModal.error }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { api } from '@/api'

// ============== 用户管理 ==============
const users = ref<any[]>([])
const userLoading = ref(false)

const loadUsers = async () => {
  userLoading.value = true
  try {
    const data = await api.admin.listUsersWithRelations()
    users.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.warn('加载用户失败', e)
  } finally {
    userLoading.value = false
  }
}

// ============== 用户查看/删除 ==============
const viewUserModal = reactive({
  open: false,
  loading: false,
  error: '',
  data: null as any
})

const viewUser = async (userId: number) => {
  viewUserModal.open = true
  viewUserModal.loading = true
  viewUserModal.error = ''
  viewUserModal.data = null
  try {
    const data = await api.admin.getUserDetail(userId)
    viewUserModal.data = data
  } catch (e: any) {
    viewUserModal.error = e?.response?.data?.message || e?.message || '获取用户信息失败'
  } finally {
    viewUserModal.loading = false
  }
}

const closeViewUserModal = () => {
  viewUserModal.open = false
  viewUserModal.data = null
  viewUserModal.error = ''
}

const deleteUser = async (u: any) => {
  if (u.role === 'admin') {
    alert('管理员账号不能删除')
    return
  }
  if (!confirm(`确认删除用户「${u.username}」？此操作不可恢复。`)) return
  try {
    await api.admin.deleteUser(u.userId)
    alert('已删除')
    loadUsers()
  } catch (e: any) {
    alert(e?.response?.data?.message || e?.message || '删除失败')
  }
}

// ============== 初始化 ==============
onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.08);
}

.food-table-body {
  max-height: 500px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.6);
}

.food-table-body::-webkit-scrollbar {
  width: 8px;
}
.food-table-body::-webkit-scrollbar-track {
  background: rgba(210, 200, 190, 0.15);
  border-radius: 4px;
}
.food-table-body::-webkit-scrollbar-thumb {
  background: rgba(180, 160, 145, 0.55);
  border-radius: 4px;
}
.food-table-body::-webkit-scrollbar-thumb:hover {
  background: rgba(150, 130, 115, 0.75);
}

.food-row {
  border-bottom: 1px solid rgba(210, 200, 190, 0.35);
  transition: background-color 0.15s ease;
}
.food-row:hover { background: rgba(255, 252, 248, 0.9); }
.food-row:last-child { border-bottom: none; }
</style>
