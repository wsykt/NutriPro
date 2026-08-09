<template>
  <div class="page-fade">
    <h2 class="text-2xl font-bold mb-2 text-morandi-text">个人中心</h2>
    <p class="text-morandi-lightText mb-6 text-sm">查看和更新你的个人信息。保存后，系统会自动在"身体指标历史"里保留一份今日快照。</p>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- 头像卡片 -->
      <div class="glass rounded-2xl p-6 text-center">
        <div class="w-20 h-20 mx-auto rounded-full bg-morandi-accent flex items-center justify-center text-white font-bold text-3xl mb-3 overflow-hidden">
          <template v-if="currentAvatar">
            <img :src="currentAvatar" class="w-full h-full object-cover" alt="头像" />
          </template>
          <template v-else>
            {{ usernameInitial }}
          </template>
        </div>
        <h3 class="font-bold text-lg">{{ usernameText }}</h3>
        <p class="text-morandi-lightText text-sm mt-1">用户 ID：#{{ userInfo.userId || '—' }}</p>
        <p class="text-xs text-morandi-accent mt-1 capitalize">{{ userInfo.role || 'user' }}</p>
        <p class="text-xs text-morandi-lightText mt-3">当前身份：{{ operateAsLabel }}</p>
      </div>

      <!-- 基本信息卡片 -->
      <div class="glass rounded-2xl p-6 md:col-span-2">
        <h3 class="font-semibold mb-4">基本信息</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">性别</label>
            <select v-model="form.gender" class="w-full px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm">
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">年龄</label>
            <input v-model.number="form.age" type="number" class="w-full px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm" />
          </div>
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">身高 (cm)</label>
            <input v-model.number="form.height" type="number" class="w-full px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm" />
          </div>
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">体重 (kg)</label>
            <input v-model.number="form.weight" type="number" class="w-full px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm" />
          </div>
          <div class="sm:col-span-2">
            <label class="block text-xs text-morandi-lightText mb-1">人群类型</label>
            <select v-model="form.crowdType" class="w-full px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm">
              <option v-for="c in crowdOptions" :key="c.value" :value="c.value">{{ c.label }}</option>
            </select>
          </div>
          <div class="sm:col-span-2">
            <label class="block text-xs text-morandi-lightText mb-1">BMI 指数（自动计算）</label>
            <div class="w-full px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm font-semibold text-morandi-accent">{{ bmiText }}</div>
          </div>
        </div>

        <div class="flex items-center gap-3 mt-5">
          <button @click="handleSave" :disabled="saving" class="px-5 py-2 rounded-lg bg-morandi-accent text-white text-sm hover:opacity-90 transition-opacity disabled:opacity-50">
            {{ saving ? '保存中...' : '保存信息' }}
          </button>
          <span v-if="saveMsg" class="text-xs text-morandi-accent">{{ saveMsg }}</span>
        </div>
        <p class="mt-3 text-xs text-morandi-lightText leading-relaxed">
          保存信息 = 更新资料 + 写入一条今日身体指标快照，方便在趋势线上查看变化。
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'
import { CROWD_OPTIONS } from '../../constants'

const crowdOptions = [...CROWD_OPTIONS]

const userStore = useUserStore()
const userInfo = ref<any>({})
const usernameText = computed(() => userInfo.value.username || userStore.user?.username || '')
const usernameInitial = computed(() => (usernameText.value ? usernameText.value.slice(0, 1).toUpperCase() : 'U'))
const currentAvatar = computed(() => userInfo.value.avatar || '')
const operateAsLabel = computed(() => {
  if (userStore.actAsUserId != null) {
    return `代 #${userStore.actAsUserId} 操作`
  }
  return '本人'
})

const form = ref<any>({
  gender: '男',
  age: 18,
  height: 165,
  weight: 65,
  crowdType: '普通人'
})
const saving = ref(false)
const saveMsg = ref('')

async function loadInfo() {
  try {
    const info: any = await api.profile.getInfo()
    if (info) {
      userInfo.value = info
      form.value.gender = info.gender || '男'
      form.value.age = toNumber(info.age, 18)
      form.value.height = toNumber(info.height, 165)
      form.value.weight = toNumber(info.weight, 65)
      form.value.crowdType = info.crowdType || info.crowd_type || '普通人'
    }
  } catch (e: any) {
    saveMsg.value = e?.message || '加载失败'
  }
}

function toNumber(v: any, fallback: number): number {
  const n = Number(v)
  return Number.isFinite(n) ? n : fallback
}

const bmiText = computed(() => {
  const h = Number(form.value.height) / 100
  const w = Number(form.value.weight)
  if (!h || !w) return '—'
  const bmi = w / (h * h)
  let category = ''
  if (bmi < 18.5) category = '（偏瘦）'
  else if (bmi < 24) category = '（正常）'
  else if (bmi < 28) category = '（超重）'
  else category = '（肥胖）'
  return `${bmi.toFixed(2)} ${category}`
})

async function handleSave() {
  saving.value = true
  saveMsg.value = ''
  try {
    await api.profile.update({
      gender: form.value.gender,
      age: Number(form.value.age) || null,
      height: Number(form.value.height) || null,
      weight: Number(form.value.weight) || null,
      crowdType: form.value.crowdType
    })
    saveMsg.value = '已保存，并写入今日身体指标快照'
    // 刷新 userStore 里的资料
    await userStore.loadUserProfile?.()
  } catch (e: any) {
    saveMsg.value = e?.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function handleSnapshot() {
  // 已移除此按钮：保存信息时会自动写入今日身体指标快照，不再提供独立的快照入口。
}
onMounted(async () => {
  await loadInfo()
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.9);
}
.page-fade {
  animation: fadeIn 0.3s ease forwards;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
