<template>
  <div class="page-fade max-w-4xl mx-auto">
    <h2 class="text-2xl font-bold text-morandi-text mb-2">添加新食材</h2>
    <p class="text-sm text-morandi-lightText mb-6">提交的食材需要管理员审核通过后才会出现在食物库中。</p>

    <div v-if="successMsg" class="glass rounded-2xl p-4 mb-6 text-sm text-green-700 bg-green-50 border border-green-200">
      {{ successMsg }}
    </div>

    <div class="glass rounded-2xl p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-morandi-text mb-1">食材名称 <span class="text-red-500">*</span></label>
          <input
            v-model="form.foodName"
            type="text"
            placeholder="如 南瓜子"
            class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-morandi-text mb-1">食物分类 <span class="text-red-500">*</span></label>
          <select
            v-model="form.foodCategory"
            class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
          >
            <option value="">请选择分类</option>
            <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-morandi-text mb-1">热量 (kcal/100g)</label>
          <input
            v-model.number="form.calorie"
            type="number"
            step="0.1"
            placeholder="如 350"
            class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-morandi-text mb-1">蛋白质 (g/100g)</label>
          <input
            v-model.number="form.protein"
            type="number"
            step="0.1"
            placeholder="如 20"
            class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-morandi-text mb-1">脂肪 (g/100g)</label>
          <input
            v-model.number="form.fat"
            type="number"
            step="0.1"
            placeholder="如 15"
            class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-morandi-text mb-1">碳水化合物 (g/100g)</label>
          <input
            v-model.number="form.carb"
            type="number"
            step="0.1"
            placeholder="如 30"
            class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-morandi-text mb-1">膳食纤维 (g/100g)</label>
          <input
            v-model.number="form.dietFiber"
            type="number"
            step="0.1"
            placeholder="如 5"
            class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-morandi-text mb-1">GI 值</label>
          <input
            v-model.number="form.giValue"
            type="number"
            step="1"
            placeholder="如 70"
            class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-morandi-text mb-1">钙 (mg/100g)</label>
          <input
            v-model.number="form.calcium"
            type="number"
            step="1"
            placeholder="如 100"
            class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-morandi-text mb-1">DHA (mg/100g)</label>
          <input
            v-model.number="form.dha"
            type="number"
            step="1"
            placeholder="如 0"
            class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
          />
        </div>

        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-morandi-text mb-1">叶酸 (μg/100g)</label>
          <input
            v-model.number="form.folicAcid"
            type="number"
            step="1"
            placeholder="如 50"
            class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
          />
        </div>
      </div>

      <div class="flex items-center justify-between mt-6 pt-4 border-t border-morandi-soft">
        <span class="text-xs text-morandi-lightText">提交后将进入待审核状态，由管理员审核通过后方可使用。</span>
        <div class="flex gap-3">
          <button
            @click="resetForm"
            class="px-4 py-2 rounded-lg border border-morandi-soft text-morandi-text text-sm hover:bg-morandi-soft transition"
          >重置</button>
          <button
            @click="submitFood"
            :disabled="submitting"
            class="px-6 py-2 rounded-lg bg-morandi-accent text-white text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >{{ submitting ? '提交中...' : '提交审核' }}</button>
        </div>
      </div>

      <div v-if="errorMsg" class="mt-4 text-sm text-red-600">{{ errorMsg }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { api } from '../../api'
import { FOOD_CATEGORIES } from '../../constants'

const categories = [...FOOD_CATEGORIES]

const form = reactive({
  foodName: '',
  foodCategory: '',
  calorie: null as number | null,
  protein: null as number | null,
  fat: null as number | null,
  carb: null as number | null,
  dietFiber: null as number | null,
  giValue: null as number | null,
  calcium: null as number | null,
  dha: null as number | null,
  folicAcid: null as number | null
})

const submitting = ref(false)
const successMsg = ref('')
const errorMsg = ref('')

const resetForm = () => {
  form.foodName = ''
  form.foodCategory = ''
  form.calorie = null
  form.protein = null
  form.fat = null
  form.carb = null
  form.dietFiber = null
  form.giValue = null
  form.calcium = null
  form.dha = null
  form.folicAcid = null
  successMsg.value = ''
  errorMsg.value = ''
}

const submitFood = async () => {
  if (!form.foodName.trim()) {
    errorMsg.value = '请输入食材名称'
    return
  }
  if (!form.foodCategory) {
    errorMsg.value = '请选择食物分类'
    return
  }
  errorMsg.value = ''
  submitting.value = true
  try {
    await api.food.add({
      foodName: form.foodName.trim(),
      foodCategory: form.foodCategory,
      calorie: form.calorie,
      protein: form.protein,
      fat: form.fat,
      carb: form.carb,
      dietFiber: form.dietFiber,
      giValue: form.giValue,
      calcium: form.calcium,
      dha: form.dha,
      folicAcid: form.folicAcid
    })
    successMsg.value = `食材「${form.foodName.trim()}」已提交，等待管理员审核。`
    resetForm()
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.message || e?.message || '提交失败，请稍后再试。'
  } finally {
    submitting.value = false
  }
}
</script>
