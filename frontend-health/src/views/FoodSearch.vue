<template>
  <div class="page-fade-in max-w-5xl mx-auto px-4 md:px-8 py-6">
    <h2 class="text-2xl font-bold text-morandi-text mb-6"> 食物搜索</h2>

    <div class="glass rounded-2xl p-6 mb-6">
      <input
        v-model="keyword"
        type="text"
        placeholder="搜索食物名称..."
        @input="handleSearch"
        class="w-full px-5 py-3 rounded-xl bg-white/70 border border-morandi-soft focus:outline-none focus:border-morandi-accent transition-colors"
      />
    </div>

    <div class="flex flex-wrap gap-2 mb-6">
      <button
        v-for="cat in categories"
        :key="cat"
        @click="selectCategory(cat)"
        class="px-4 py-2 rounded-full text-sm transition-all"
        :class="selectedCategory === cat
          ? 'bg-morandi-accent text-white shadow-md'
          : 'bg-white/70 text-morandi-text hover:bg-morandi-accent hover:text-white border border-morandi-soft'"
      >
        {{ cat }}
      </button>
    </div>

    <div v-if="foods.length === 0" class="text-center py-12 text-morandi-lightText">
      暂无数据
    </div>

    <div class="grid gap-4">
      <div
        v-for="food in foods"
        :key="food.foodId"
        class="glass rounded-2xl p-6 hover:shadow-lg transition-shadow"
      >
        <div class="flex justify-between items-center mb-4">
          <h4 class="text-lg font-semibold text-morandi-text">{{ food.foodName }}</h4>
          <span class="px-3 py-1 rounded-full text-xs bg-morandi-soft text-morandi-text">{{ food.foodCategory }}</span>
        </div>
        <div class="grid grid-cols-3 md:grid-cols-5 gap-3 text-center">
          <div>
            <div class="text-xs text-morandi-lightText mb-1">热量</div>
            <div class="font-semibold text-morandi-accent">{{ food.calorie }} kcal</div>
          </div>
          <div>
            <div class="text-xs text-morandi-lightText mb-1">蛋白质</div>
            <div class="font-semibold text-morandi-text">{{ food.protein }}g</div>
          </div>
          <div>
            <div class="text-xs text-morandi-lightText mb-1">脂肪</div>
            <div class="font-semibold text-morandi-text">{{ food.fat }}g</div>
          </div>
          <div>
            <div class="text-xs text-morandi-lightText mb-1">碳水</div>
            <div class="font-semibold text-morandi-text">{{ food.carb }}g</div>
          </div>
          <div>
            <div class="text-xs text-morandi-lightText mb-1">GI 值</div>
            <div class="font-semibold text-morandi-text">{{ food.giValue || '-' }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api'

const keyword = ref('')
const foods = ref<any[]>([])
const categories = ['全部', '主食', '肉蛋类', '水产', '蔬菜', '水果', '豆制品', '奶类', '油脂类']
const selectedCategory = ref('全部')
let searchTimer: any = null

const loadFoods = async () => {
  try { const data: any = await api.food.list(); foods.value = data || [] }
  catch (e) { console.error('加载食物失败', e) }
}

const handleSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    if (keyword.value.trim()) {
      try { const data: any = await api.food.search(keyword.value); foods.value = data || [] }
      catch (e) { console.error('搜索失败', e) }
    } else { loadFoods() }
  }, 300)
}

const selectCategory = async (cat: string) => {
  selectedCategory.value = cat
  if (cat === '全部') loadFoods()
  else { try { const data: any = await api.food.getByCategory(cat); foods.value = data || [] } catch (e) { console.error('加载失败', e) } }
}

onMounted(() => { loadFoods() })
</script>
