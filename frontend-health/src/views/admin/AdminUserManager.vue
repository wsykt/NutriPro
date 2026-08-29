<template>
  <div class="ad-card">
    <div class="ad-head">
      <h3 class="ad-h3">用户名册<span class="ad-h3-en">USER REGISTER</span></h3>
      <span class="ad-sub">共 {{ users.length }} 位用户</span>
    </div>

    <div v-if="userLoading" class="ad-empty">加载中...</div>

    <div v-else class="ad-table-wrap">
      <table class="ad-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>性别</th>
            <th>年龄</th>
            <th>人群类型</th>
            <th>监护人</th>
            <th>被监护人</th>
            <th class="ta-r">角色</th>
            <th class="ta-c">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.userId">
            <td class="small dim">{{ u.userId }}</td>
            <td class="strong">{{ u.username }}</td>
            <td>{{ u.gender || '-' }}</td>
            <td>{{ u.age || '-' }}</td>
            <td>{{ u.crowdType || '-' }}</td>
            <td>
              <span v-if="u.guardians && u.guardians.length" class="small">{{ u.guardians.join(', ') }}</span>
              <span v-else class="dim">无</span>
            </td>
            <td>
              <span v-if="u.wards && u.wards.length" class="small">{{ u.wards.join(', ') }}</span>
              <span v-else class="dim">无</span>
            </td>
            <td class="ta-r">
              <span :class="['ad-chip', u.role === 'admin' && 'gold']">{{ u.role === 'admin' ? '管理员' : '普通用户' }}</span>
            </td>
            <td class="ta-c">
              <div class="acts">
                <button class="ad-btn sm solid" @click="viewUser(u.userId)">查看</button>
                <button class="ad-btn sm red" :disabled="u.role === 'admin'" @click="deleteUser(u)">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="9" class="ad-empty">暂无用户数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ===================== 用户档案 · 无遮罩气泡弹窗 ===================== -->
  <div v-if="viewUserModal.open" class="ad-pop-wrap" @click.self="closeViewUserModal">
    <div class="ad-pop" style="width: 580px; max-width: 94vw;">
      <div class="ad-pop-head">
        <h3 class="ad-h3">用户档案<span class="ad-h3-en">PROFILE</span></h3>
        <button class="ad-x" @click="closeViewUserModal">×</button>
      </div>

      <div v-if="viewUserModal.loading" class="ad-empty">加载中...</div>

      <template v-else-if="viewUserModal.data">
        <div class="ad-head" style="margin-bottom: 14px;">
          <div class="u-idrow">
            <div class="ad-avatar">{{ (viewUserModal.data.username || 'U').charAt(0).toUpperCase() }}</div>
            <div>
              <p class="u-name">{{ viewUserModal.data.username }}</p>
              <p class="ad-sub" style="margin-top: 3px;">用户 ID：{{ viewUserModal.data.userId }}</p>
            </div>
          </div>
          <span :class="['ad-chip', viewUserModal.data.role === 'admin' ? 'gold' : '']">
            {{ viewUserModal.data.role === 'admin' ? 'ADMIN' : 'USER' }}
          </span>
        </div>

        <div class="ad-grid2">
          <div class="ad-cell"><p class="k">性别</p><p class="v">{{ viewUserModal.data.gender || '-' }}</p></div>
          <div class="ad-cell"><p class="k">年龄</p><p class="v">{{ viewUserModal.data.age ?? '-' }}</p></div>
          <div class="ad-cell"><p class="k">身高 (cm)</p><p class="v">{{ viewUserModal.data.height ?? '-' }}</p></div>
          <div class="ad-cell"><p class="k">体重 (kg)</p><p class="v">{{ viewUserModal.data.weight ?? '-' }}</p></div>
        </div>

        <div class="ad-section" style="margin-top: 12px;">
          <p class="ad-section-tt">身体指标推演</p>
          <div class="ad-grid2">
            <div>
              <p class="ad-label">BMI 指数</p>
              <p class="ad-num">{{ viewUserModal.data.bmi ?? '-' }}</p>
              <p class="ad-sub">{{ viewUserModal.data.bmiStatus || '-' }}</p>
            </div>
            <div>
              <p class="ad-label">基础代谢 BMR (kcal)</p>
              <p class="ad-num">{{ viewUserModal.data.bmr ?? '-' }}</p>
            </div>
          </div>
        </div>

        <div class="ad-grid2" style="margin-top: 12px;">
          <div class="ad-cell"><p class="k">人群类型</p><p class="v">{{ viewUserModal.data.crowdType || '-' }}</p></div>
          <div class="ad-cell"><p class="k">注册时间</p><p class="v">{{ viewUserModal.data.createdAt || '-' }}</p></div>
        </div>
      </template>

      <div v-if="viewUserModal.error" class="ad-err" style="margin-top: 14px;">{{ viewUserModal.error }}</div>
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
.u-idrow { display: flex; align-items: center; gap: 14px; }
.u-name {
  font-family: 'Noto Serif SC', serif;
  font-size: 18px; font-weight: 700; letter-spacing: 0.08em;
  color: var(--ad-title);
}
</style>
