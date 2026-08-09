<template>
  <div class="page-fade">
    <h2 class="text-2xl font-bold mb-2 text-morandi-text">亲属代录入饮食</h2>
    <p class="text-morandi-lightText mb-6 text-sm">为你的家人或亲属记录饮食情况</p>

    <div class="glass rounded-2xl p-6 mb-6">
      <h3 class="font-semibold mb-4">选择亲属</h3>
      <div v-if="wards.length === 0" class="text-sm text-morandi-sub">
        暂无可代录入的亲属，请先前往「亲属关系管理」添加亲属并等待对方确认。
      </div>
      <div v-else class="flex flex-wrap gap-3">
        <button
          v-for="w in wards"
          :key="w.wardId"
          @click="selectWard(w.wardId)"
          :class="[
            'px-4 py-2 rounded-xl text-sm transition-all border',
            selectedWardId === w.wardId
              ? 'bg-morandi-accent text-white border-morandi-accent'
              : 'bg-white/70 border-morandi-soft text-morandi-text hover:border-morandi-accent'
          ]"
        >
            {{ w.wardUsername }}
        </button>
        <button
          @click="selectWard(null)"
          :class="[
            'px-4 py-2 rounded-xl text-sm transition-all border',
            selectedWardId === null
              ? 'bg-gray-300 text-black border-gray-300'
              : 'bg-white/70 border-morandi-soft text-morandi-text hover:border-morandi-accent'
          ]"
        >
          取消
        </button>
      </div>
      <div v-if="selectedWardId !== null" class="mt-4 text-xs text-morandi-accent">
        提示：当前已进入为 {{ selectedWardName }} 操作模式，页面内的饮食记录、营养分析均会保存到该亲属账号。
      </div>
    </div>

    <div class="glass rounded-2xl p-6 mb-6">
      <h3 class="font-semibold mb-4">为「{{ selectedWardName || '—' }}」录入今日饮食</h3>
      <p class="text-xs text-morandi-sub mb-4">请前往「录入饮食」菜单</p>
      <button @click="goToFoodInput" class="px-4 py-2 rounded-lg bg-morandi-accent text-white text-sm">前往录入饮食</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const router = useRouter()

const selectedWardId = ref<number | null>(null)

const wards = computed(() => userStore.wards || [])

const selectedWardName = computed(() => {
  if (selectedWardId.value === null) return ''
  const w = wards.value.find((x: any) => x.wardId === selectedWardId.value)
  return (w && w.wardUsername) || ''
})

function selectWard(wardId: number | null) {
  selectedWardId.value = wardId
  userStore.setActAs(wardId)
}

function goToFoodInput() {
  router.push('/dashboard/food-input')
}

onMounted(() => {
  // 保持当前的 actAsUserId 不变
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
