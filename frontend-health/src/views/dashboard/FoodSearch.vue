<template>
  <div class="page-fade max-w-6xl mx-auto">
    <h2 class="text-2xl font-bold text-morandi-text mb-2">食物库浏览与搜索</h2>
    <p class="text-sm text-morandi-lightText mb-6">查询食物的热量与主要营养素构成，支持按分类筛选与名称搜索。</p>

    <!-- 筛选栏 -->
    <div class="glass rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-3">
      <label class="text-sm text-morandi-text whitespace-nowrap">分类：</label>
      <select v-model="selectedCategory" class="px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent">
        <option value="">全部</option>
        <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
      </select>
      <input
        v-model="keyword"
        @keyup.enter="loadFoods"
        type="text"
        placeholder="搜索食物名（如 米饭、鸡蛋、苹果）"
        class="flex-1 min-w-[240px] px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
      />
      <button @click="loadFoods" class="px-4 py-2 rounded-lg bg-morandi-accent text-white text-sm">刷新</button>
      <span class="text-xs text-morandi-lightText ml-auto">共 {{ allFoods.length }} 种 · 当前显示 {{ filteredFoods.length }} 种</span>
    </div>

    <div v-if="foodLoading" class="text-center text-sm text-morandi-lightText py-16">食物加载中...</div>

    <div v-else class="glass rounded-2xl overflow-hidden mb-6">
      <!-- 表格表头：独立在滚动区之外，避免被内容覆盖 -->
      <div class="food-table-head">
        <table class="min-w-full text-sm text-left text-morandi-text">
          <thead class="text-xs text-morandi-text">
            <tr>
              <th class="px-4 py-3 font-semibold">名称</th>
              <th class="px-4 py-3 font-semibold">分类</th>
              <th class="px-4 py-3 font-semibold text-right">热量 (kcal/100g)</th>
              <th class="px-4 py-3 font-semibold text-right">蛋白质 (g)</th>
              <th class="px-4 py-3 font-semibold text-right">脂肪 (g)</th>
              <th class="px-4 py-3 font-semibold text-right">碳水 (g)</th>
              <th class="px-4 py-3 font-semibold text-right">GI</th>
              <th class="px-4 py-3 font-semibold text-right">钙 (mg)</th>
            </tr>
          </thead>
        </table>
      </div>

      <!-- 表格内容：独立滚动，不会和表头重合 -->
      <div class="food-table-body">
        <table class="min-w-full text-sm text-left text-morandi-text">
          <tbody>
            <tr v-for="f in filteredFoods" :key="f.foodId" class="food-row">
              <td class="px-4 py-3 font-medium">{{ f.foodName }}</td>
              <td class="px-4 py-3 text-xs">{{ f.foodCategory || '-' }}</td>
              <td class="px-4 py-3 text-right">{{ num(f.calorie) }}</td>
              <td class="px-4 py-3 text-right">{{ num(f.protein) }}</td>
              <td class="px-4 py-3 text-right">{{ num(f.fat) }}</td>
              <td class="px-4 py-3 text-right">{{ num(f.carb) }}</td>
              <td class="px-4 py-3 text-right">{{ num(f.giValue) }}</td>
              <td class="px-4 py-3 text-right">{{ num(f.calcium) }}</td>
            </tr>
            <tr v-if="!filteredFoods.length">
              <td colspan="8" class="px-4 py-8 text-center text-morandi-lightText text-sm">没有匹配的食物，试试换个关键词或分类</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api'

const keyword = ref('')
const selectedCategory = ref('')
const foodLoading = ref(false)
const allFoods = ref<any[]>([])

const categories = computed(() => {
  const set = new Set<string>()
  allFoods.value.forEach((f: any) => {
    if (f.foodCategory) set.add(f.foodCategory)
  })
  return Array.from(set).sort()
})

const filteredFoods = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return allFoods.value.filter((f: any) => {
    const okCat = !selectedCategory.value || f.foodCategory === selectedCategory.value
    const okKw = !kw || (f.foodName && String(f.foodName).toLowerCase().indexOf(kw) >= 0)
    return okCat && okKw
  })
})

function num(v: any): string {
  const n = Number(v)
  if (!Number.isFinite(n)) return '-'
  return String(Math.round(n * 10) / 10)
}

async function loadFoods() {
  foodLoading.value = true
  try {
    const data = await api.food.list()
    allFoods.value = Array.isArray(data) ? data : []
  } catch (e: any) {
    console.warn('加载食物列表失败', e)
  } finally {
    foodLoading.value = false
  }
}

onMounted(() => {
  loadFoods()
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

.food-table-head {
  background: rgba(248, 246, 244, 0.9);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.food-table-body {
  max-height: 400px;
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

.food-table-head table,
.food-table-body table {
  table-layout: fixed;
}

.food-table-head table th:nth-child(1),
.food-table-body table td:nth-child(1) { width: 22%; }
.food-table-head table th:nth-child(2),
.food-table-body table td:nth-child(2) { width: 12%; }
.food-table-head table th:nth-child(3),
.food-table-body table td:nth-child(3),
.food-table-head table th:nth-child(4),
.food-table-body table td:nth-child(4),
.food-table-head table th:nth-child(5),
.food-table-body table td:nth-child(5),
.food-table-head table th:nth-child(6),
.food-table-body table td:nth-child(6),
.food-table-head table th:nth-child(7),
.food-table-body table td:nth-child(7),
.food-table-head table th:nth-child(8),
.food-table-body table td:nth-child(8) { width: 11%; }

.food-row {
  border-bottom: 1px solid rgba(210, 200, 190, 0.35);
  transition: background-color 0.15s ease;
}
.food-row:hover { background: rgba(255, 252, 248, 0.9); }
.food-row:last-child { border-bottom: none; }

.page-fade { animation: fadeIn 0.3s ease forwards; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
