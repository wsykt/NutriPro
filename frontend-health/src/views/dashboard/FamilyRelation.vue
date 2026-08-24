<template>
  <div class="max-w-4xl mx-auto">
    <h2 class="text-2xl font-bold text-morandi-text mb-6">亲属关系管理</h2>

    <!-- 添加亲属 -->
    <section class="glass-card rounded-2xl p-6 mb-6">
      <h3 class="text-lg font-semibold text-morandi-text mb-3">添加亲属</h3>
      <p class="text-sm text-morandi-sub mb-4">
        输入被监护人的用户名（对方注册时使用的账号名），发送邀请后对方需要确认，即可开始代录入饮食与查看报告。
      </p>
      <div class="flex items-center gap-3">
        <input
          v-model="wardUsername"
          placeholder="被监护人用户名（登录账号）"
          class="flex-1 px-4 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent"
        />
        <button
          @click="handleAdd"
          class="px-4 py-2 rounded-lg bg-morandi-accent text-white hover:opacity-90 transition-opacity"
        >
          发送邀请
        </button>
      </div>
      <p v-if="message" class="text-sm mt-3 px-2" :class="messageType === 'error' ? 'text-red-500' : 'text-morandi-accent'">
        {{ message }}
      </p>
    </section>

    <!-- 待确认邀请 -->
    <section v-if="pendingList.length" class="glass-card rounded-2xl p-6 mb-6">
      <h3 class="text-lg font-semibold text-morandi-text mb-3">待确认的邀请</h3>
      <ul class="space-y-3">
        <li v-for="item in pendingList" :key="item.relationId" class="flex items-center justify-between p-3 rounded-lg bg-morandi-soft/50">
          <div>
            <div class="text-morandi-text font-medium">
              来自：{{ item.guardianUsername }} → 邀请您作为被监护人
            </div>
            <div class="text-xs text-morandi-sub">
              {{ formatDate(item.createdAt) }}
            </div>
          </div>
          <div class="flex gap-2">
            <button @click="handleConfirm(item.relationId)" class="px-3 py-1.5 rounded-lg bg-morandi-accent text-white text-sm">
              接受
            </button>
            <button @click="handleReject(item.relationId)" class="px-3 py-1.5 rounded-lg bg-red-400 text-white text-sm">
              拒绝
            </button>
          </div>
        </li>
      </ul>
    </section>

    <!-- 我监护的亲属 -->
    <section class="glass-card rounded-2xl p-6 mb-6">
      <h3 class="text-lg font-semibold text-morandi-text mb-3">我监护的亲属</h3>
      <div v-if="wards.length === 0" class="text-sm text-morandi-sub">暂无监护中的亲属</div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div
          v-for="w in wards"
          :key="w.wardId"
          class="flex items-center justify-between p-3 rounded-lg bg-morandi-soft/40"
        >
          <div>
            <div class="text-morandi-text font-medium">{{ w.wardUsername }}</div>
            <div class="text-xs text-morandi-sub">ID: {{ w.wardId }}</div>
          </div>
          <button
            @click="handleRemove(w.relationId, w.wardUsername)"
            class="px-3 py-1.5 rounded-lg bg-red-400 text-white text-sm"
          >
            解除关系
          </button>
        </div>
      </div>
    </section>

    <!-- 我的监护人 -->
    <section class="glass-card rounded-2xl p-6">
      <h3 class="text-lg font-semibold text-morandi-text mb-3">我的监护人</h3>
      <div v-if="guardians.length === 0" class="text-sm text-morandi-sub">暂无监护人</div>
      <ul v-else class="space-y-2">
        <li v-for="g in guardians" :key="g.guardianId" class="p-3 rounded-lg bg-morandi-soft/40">
          <span class="text-morandi-text font-medium">{{ g.guardianUsername }}</span>
          <span class="text-xs text-morandi-sub ml-2">（可替您录入饮食 / 查看报告 / 修改资料）</span>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'

const userStore = useUserStore()

const wardUsername = ref('')
const message = ref('')
const messageType = ref<'info' | 'error'>('info')

const wards = ref<Array<{ relationId: number; wardId: number; wardUsername: string }>>([])
const guardians = ref<Array<{ guardianId: number; guardianUsername: string }>>([])
const pendingList = ref<any[]>([])

function showMsg(text: string, type: 'info' | 'error' = 'info') {
  message.value = text
  messageType.value = type
  setTimeout(() => {
    if (message.value === text) message.value = ''
  }, 5000)
}

async function handleAdd() {
  const name = wardUsername.value.trim()
  if (!name) {
    showMsg('请输入用户名', 'error')
    return
  }
  try {
    await api.relation.add(name)
    wardUsername.value = ''
    showMsg('邀请已发送，等待对方确认')
    await loadAll()
  } catch (e: any) {
    showMsg(e?.response?.data?.message || e?.message || '发送失败', 'error')
  }
}

async function handleConfirm(relationId: number) {
  try {
    await api.relation.confirm(relationId)
    showMsg('已接受邀请')
    await loadAll()
  } catch (e: any) {
    showMsg(e?.response?.data?.message || e?.message || '操作失败', 'error')
  }
}

async function handleReject(relationId: number) {
  try {
    await api.relation.reject(relationId)
    showMsg('已拒绝邀请')
    await loadAll()
  } catch (e: any) {
    showMsg(e?.response?.data?.message || e?.message || '操作失败', 'error')
  }
}

async function handleRemove(relationId: number, name: string) {
  if (!confirm(`确定要解除与 ${name} 的监护关系吗？`)) return
  try {
    await api.relation.remove(relationId)
    showMsg('关系已解除')
    await loadAll()
  } catch (e: any) {
    showMsg(e?.response?.data?.message || e?.message || '操作失败', 'error')
  }
}

async function loadAll() {
  try {
    const myWards: any = await api.relation.myWards()
    wards.value = (Array.isArray(myWards) ? myWards : []).map((r: any) => ({
      relationId: r.relationId ?? r.relation_id,
      wardId: r.wardId ?? r.ward_id,
      wardUsername: r.wardUsername ?? r.ward_username
    }))
  } catch {}
  try {
    const myGuardians: any = await api.relation.myGuardians()
    guardians.value = (Array.isArray(myGuardians) ? myGuardians : []).map((r: any) => ({
      guardianId: r.guardianId ?? r.guardian_id,
      guardianUsername: r.guardianUsername ?? r.guardian_username
    }))
  } catch {}
  try {
    const pending: any = await api.relation.pendingInvitations()
    pendingList.value = (Array.isArray(pending) ? pending : []).map((r: any) => ({
      relationId: r.relationId ?? r.relation_id,
      guardianId: r.guardianId ?? r.guardian_id,
      guardianUsername: r.guardianUsername ?? r.guardian_username,
      createdAt: r.createdAt ?? r.created_at
    }))
  } catch {}
}

function formatDate(v: any) {
  if (!v) return ''
  try {
    const d = new Date(v)
    return d.toLocaleString()
  } catch { return String(v) }
}

onMounted(() => {
  userStore.init().then(() => loadAll()).catch(() => loadAll())
})
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.1);
}
</style>
