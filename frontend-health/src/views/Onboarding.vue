<template>
  <div class="min-h-screen flex items-center justify-center p-4" style="background: linear-gradient(160deg, #FAF8F3 0%, #F7F5F0 40%, #F4F2EA 75%, #F2F3EC 100%)">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl text-white text-3xl mb-4 shadow-lg" style="background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%); box-shadow: 0 12px 32px rgba(47,93,74,0.25)">✨</div>
        <h1 class="text-2xl font-bold text-gray-800" style="font-family: 'Noto Serif SC', serif">欢迎使用健康助手</h1>
        <p class="text-gray-500 text-sm mt-2">完成简单设置，开启你的健康之旅</p>
      </div>
      <div class="flex justify-center gap-2 mb-8">
        <div v-for="(step, index) in steps" :key="index" class="flex items-center">
          <div class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300" :class="currentStep >= index ? 'text-white shadow-md' : 'bg-gray-100 text-gray-400'" :style="currentStep >= index ? { background: 'linear-gradient(135deg, #2F5D4A, #1F4636)' } : {}">{{ index + 1 }}</div>
          <div v-if="index < steps.length - 1" class="w-12 md:w-16 h-1.5 mx-2 rounded-full transition-all duration-300" :class="currentStep > index ? '' : 'bg-gray-200'" :style="currentStep > index ? { background: '#2F5D4A' } : {}"></div>
        </div>
      </div>
      <div class="bg-white rounded-2xl shadow-xl p-6 md:p-8" style="box-shadow: 0 20px 50px rgba(31,42,36,0.1)">
        <transition name="fade" mode="out-in">
          <div v-if="currentStep === 0" key="step1" class="space-y-6">
            <div class="text-center">
              <h2 class="text-xl font-bold text-gray-800 mb-2">基本信息</h2>
              <p class="text-gray-500 text-sm">设置你的性别、身高、体重和年龄</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">性别</label>
              <div class="grid grid-cols-2 gap-3">
                <button @click="form.gender = '男'" class="py-3 rounded-xl border-2 transition-all duration-200 flex items-center justify-center gap-2" :class="form.gender === '男' ? 'text-white border-transparent' : 'border-gray-200 hover:border-gray-300'" :style="form.gender === '男' ? { background: '#2F5D4A' } : {}">
                  <span class="text-xl">👨</span><span class="font-medium">男</span>
                </button>
                <button @click="form.gender = '女'" class="py-3 rounded-xl border-2 transition-all duration-200 flex items-center justify-center gap-2" :class="form.gender === '女' ? 'text-white border-transparent' : 'border-gray-200 hover:border-gray-300'" :style="form.gender === '女' ? { background: '#2F5D4A' } : {}">
                  <span class="text-xl">👩</span><span class="font-medium">女</span>
                </button>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">身高 (cm)</label>
                <input v-model.number="form.height" type="number" min="50" max="300" class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none transition-all" placeholder="170" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">体重 (kg)</label>
                <input v-model.number="form.weight" type="number" min="20" max="300" class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none transition-all" placeholder="65" />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">年龄</label>
              <input v-model.number="form.age" type="number" min="1" max="150" class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none transition-all" placeholder="25" />
            </div>
            <button @click="nextStep" :disabled="!isStep1Valid" class="w-full py-3 rounded-xl text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed" style="background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%); box-shadow: 0 8px 24px rgba(47,93,74,0.25)">下一步</button>
          </div>
          <div v-else-if="currentStep === 1" key="step2" class="space-y-6">
            <div class="text-center">
              <h2 class="text-xl font-bold text-gray-800 mb-2">人群类型</h2>
              <p class="text-gray-500 text-sm">选择最适合你的人群类型</p>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <button v-for="type in crowdTypes" :key="type.value" @click="form.crowdType = type.value" class="py-4 rounded-xl border-2 transition-all duration-200 flex flex-col items-center gap-2 p-3" :class="form.crowdType === type.value ? 'text-white border-transparent' : 'border-gray-200 hover:border-gray-300'" :style="form.crowdType === type.value ? { background: '#2F5D4A' } : {}">
                <component :is="type.icon" class="w-8 h-8" />
                <span class="font-medium text-sm">{{ type.label }}</span>
              </button>
            </div>
            <div class="flex gap-3">
              <button @click="prevStep" class="flex-1 py-3 rounded-xl border border-gray-200 text-gray-600 font-medium hover:bg-gray-50 transition-all">返回</button>
              <button @click="nextStep" :disabled="!form.crowdType" class="flex-1 py-3 rounded-xl text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed" style="background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%)">下一步</button>
            </div>
          </div>
          <div v-else-if="currentStep === 2" key="step3" class="space-y-6">
            <div class="text-center">
              <h2 class="text-xl font-bold text-gray-800 mb-2">健康产品使用</h2>
              <p class="text-gray-500 text-sm">你使用过以下哪些健康类产品？</p>
            </div>
            <div class="space-y-3">
              <button v-for="product in healthProducts" :key="product" @click="toggleProduct(product)" class="w-full py-3 rounded-xl border-2 transition-all duration-200 flex items-center justify-between px-4" :class="selectedProducts.includes(product) ? 'border-transparent' : 'border-gray-200 hover:border-gray-300'" :style="selectedProducts.includes(product) ? { borderColor: '#2F5D4A', background: 'rgba(47,93,74,0.06)' } : {}">
                <span class="text-gray-700 font-medium">{{ product }}</span>
                <div class="w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all" :class="selectedProducts.includes(product) ? 'border-transparent' : 'border-gray-300'" :style="selectedProducts.includes(product) ? { background: '#2F5D4A' } : {}">
                  <component v-if="selectedProducts.includes(product)" :is="Check" class="w-3 h-3 text-white" />
                </div>
              </button>
            </div>
            <div class="flex gap-3">
              <button @click="prevStep" class="flex-1 py-3 rounded-xl border border-gray-200 text-gray-600 font-medium hover:bg-gray-50 transition-all">返回</button>
              <button @click="nextStep" class="flex-1 py-3 rounded-xl text-white font-medium transition-all" style="background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%)">下一步</button>
            </div>
          </div>
          <div v-else-if="currentStep === 3" key="step4" class="space-y-6 text-center">
            <div class="w-20 h-20 mx-auto rounded-full flex items-center justify-center text-white mb-4 shadow-lg" style="background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%); box-shadow: 0 12px 32px rgba(47,93,74,0.28)">
              <component :is="PartyPopper" class="w-10 h-10" />
            </div>
            <h2 class="text-2xl font-bold text-gray-800" style="font-family: 'Noto Serif SC', serif">欢迎加入！</h2>
            <p class="text-gray-500">恭喜你完成了所有设置<br />现在开始你的健康之旅吧</p>
            <div class="bg-gray-50 rounded-xl p-4 mt-6">
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div><p class="text-gray-400">性别</p><p class="font-medium text-gray-800">{{ form.gender }}</p></div>
                <div><p class="text-gray-400">年龄</p><p class="font-medium text-gray-800">{{ form.age }} 岁</p></div>
                <div><p class="text-gray-400">身高</p><p class="font-medium text-gray-800">{{ form.height }} cm</p></div>
                <div><p class="text-gray-400">体重</p><p class="font-medium text-gray-800">{{ form.weight }} kg</p></div>
              </div>
              <div class="mt-3 pt-3 border-t border-gray-200">
                <p class="text-gray-400 text-sm">人群类型</p>
                <p class="font-medium text-gray-800">{{ getCrowdTypeLabel(form.crowdType) }}</p>
              </div>
            </div>
            <button @click="completeOnboarding" :disabled="loading" class="w-full py-4 rounded-xl text-white font-bold text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed" style="background: linear-gradient(135deg, #2F5D4A 0%, #1F4636 100%); box-shadow: 0 10px 30px rgba(47,93,74,0.3)">{{ loading ? '正在进入...' : '开始我的健康之旅' }}</button>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { api } from '../api'
import { User, Heart, Baby, GraduationCap, Droplet, Dumbbell, Check, PartyPopper } from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()

const currentStep = ref(0)
const loading = ref(false)
const steps = ['基本信息', '人群类型', '健康产品', '完成']

const form = reactive({
  gender: '',
  height: null as number | null,
  weight: null as number | null,
  age: null as number | null,
  crowdType: '',
  usedProducts: [] as string[]
})
const selectedProducts = ref<string[]>([])

const crowdTypes = [
  { value: '普通人', label: '普通人', icon: User as Component },
  { value: '健身', label: '健身爱好者', icon: Dumbbell as Component },
  { value: '老年', label: '老年人', icon: Heart as Component },
  { value: '孕妇', label: '孕妇', icon: Baby as Component },
  { value: '青少年', label: '青少年', icon: GraduationCap as Component },
  { value: '糖尿病', label: '糖尿病患者', icon: Droplet as Component }
]

const healthProducts = ['小荷AI医生', '咕咚', '薄荷健康', 'Keep', '其他']

const isStep1Valid = computed(() => {
  return form.gender && form.height && form.weight && form.age
})

const toggleProduct = (product: string) => {
  const index = selectedProducts.value.indexOf(product)
  if (index === -1) selectedProducts.value.push(product)
  else selectedProducts.value.splice(index, 1)
}

const getCrowdTypeLabel = (value: string) => {
  const type = crowdTypes.find(t => t.value === value)
  return type ? type.label : value
}

const nextStep = () => {
  if (currentStep.value < steps.length - 1) currentStep.value++
}
const prevStep = () => {
  if (currentStep.value > 0) currentStep.value--
}

const completeOnboarding = async () => {
  loading.value = true
  // 无论后端保存是否成功，都先标记为已完成引导，避免退出登录后再登录重复进入引导页
  userStore.setFirstLogin(0)
  userStore.updateProfile({
    gender: form.gender,
    height: form.height ?? undefined,
    weight: form.weight ?? undefined,
    age: form.age ?? undefined,
    crowdType: form.crowdType
  })
  try {
    await api.profile.update({
      gender: form.gender,
      height: form.height ?? undefined,
      weight: form.weight ?? undefined,
      age: form.age ?? undefined,
      crowdType: form.crowdType
    })
    router.push('/dashboard/profile')
  } catch (e: any) {
    console.error('保存资料到后端失败（引导已完成，可在个人中心重新修改）', e)
    router.push('/dashboard/profile')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>