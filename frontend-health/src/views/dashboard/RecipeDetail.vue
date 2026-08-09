<template>
  <div :class="['recipe-detail', { 'elderly-mode': elderlyMode }]">
    <button class="back-btn" @click="goBack">← 返回</button>
    
    <div v-if="recipe" class="recipe-content">
      <div class="recipe-header">
        <div class="recipe-title">
          <h1>{{ recipe.recipeName }}</h1>
          <p>{{ recipe.description }}</p>
          <div class="nutrition-summary">
            <span>热量: {{ recipe.calories }} kcal</span>
            <span>蛋白质: {{ recipe.protein }}g</span>
            <span>脂肪: {{ recipe.fat }}g</span>
            <span>碳水: {{ recipe.carbs }}g</span>
          </div>
          <div class="tags" v-if="recipe.tags">
            <span v-for="tag in recipe.tags.split(',')" :key="tag" class="tag">{{ tag.trim() }}</span>
          </div>
        </div>
      </div>
      
      <div class="section">
        <h2>食材清单</h2>
        <table class="ingredients-table">
          <thead>
            <tr>
              <th>食材名称</th>
              <th>用量</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ingredient in ingredients" :key="ingredient.ingredientId">
              <td>{{ ingredient.ingredientName }}</td>
              <td>{{ ingredient.amount }}{{ ingredient.unit }}</td>
              <td>
                <span v-if="isNotSuitable(ingredient.ingredientName)" class="not-suitable">不适合</span>
                <span v-else class="suitable">适合</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div v-if="substitutions.length > 0" class="section substitutions-section">
        <h2>智能食材替换建议</h2>
        <div v-for="sub in substitutions" :key="sub.ingredient.ingredientId" class="substitution-card">
          <div class="original-ingredient">
            <component :is="AlertTriangle" class="warning-icon w-4 h-4 text-amber-500" />
            <span>{{ sub.ingredient.ingredientName }} ({{ sub.ingredient.amount }}{{ sub.ingredient.unit }})</span>
            <span class="reason">{{ sub.reason }}</span>
          </div>
          <div class="alternatives">
            <span class="alt-label">推荐替代：</span>
            <button 
              v-for="(alt, index) in sub.alternatives" 
              :key="index"
              class="alt-btn"
              @click="applySubstitution(sub.ingredient.ingredientName, alt)"
            >
              {{ alt }}
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="appliedSubstitutions.length > 0" class="section">
        <h2>已应用的替换</h2>
        <div class="applied-list">
          <div v-for="(sub, index) in appliedSubstitutions" :key="index" class="applied-item">
            <span>{{ sub.original }} → {{ sub.replaced }}</span>
            <button @click="removeSubstitution(index)" class="remove-btn">取消</button>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="loading">
      <span>加载中...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '@/api'
import { getCache } from '@/utils/storage'
import { AlertTriangle } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const recipe = ref<any>(null)
const ingredients = ref<any[]>([])
const substitutions = ref<any[]>([])
const appliedSubstitutions = ref<{ original: string; replaced: string }[]>([])
const elderlyMode = ref(false)

const recipeId = computed(() => parseInt(route.params.id as string))

onMounted(() => {
  loadRecipeDetail()
  const mode = getCache<number>('elderlyMode')
  elderlyMode.value = mode === 1
})

async function loadRecipeDetail() {
  try {
    const currentUserId = localStorage.getItem('currentUserId')
    const userId = currentUserId ? parseInt(currentUserId) : undefined
    const data = await api.recipe.getDetail(recipeId.value, userId)
    recipe.value = data.recipe
    ingredients.value = data.ingredients || []
    substitutions.value = data.substitutions || []
  } catch (e) {
    console.error('加载菜谱详情失败', e)
  }
}

function goBack() {
  router.push('/dashboard/recipe-library')
}

function isNotSuitable(ingredientName: string): boolean {
  return substitutions.value.some(s => s.ingredient.ingredientName === ingredientName && s.isNotSuitable)
}

function applySubstitution(original: string, replaced: string) {
  const existing = appliedSubstitutions.value.find(s => s.original === original)
  if (!existing) {
    appliedSubstitutions.value.push({ original, replaced })
  }
}

function removeSubstitution(index: number) {
  appliedSubstitutions.value.splice(index, 1)
}
</script>

<style scoped>
.recipe-detail {
  padding: 20px;
}

.recipe-detail.elderly-mode {
  font-size: 18px;
}

.back-btn {
  padding: 10px 20px;
  background: #f5f5f5;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  margin-bottom: 20px;
}

.recipe-content {
  max-width: 800px;
  margin: 0 auto;
}

.recipe-header {
  padding: 24px;
  margin-bottom: 30px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.recipe-title h1 {
  font-size: 28px;
  margin-bottom: 10px;
  color: #333;
}

.recipe-title p {
  font-size: 14px;
  color: #666;
  margin-bottom: 15px;
}

.nutrition-summary {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #555;
  margin-bottom: 15px;
}

.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  padding: 4px 10px;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 4px;
  font-size: 12px;
}

.section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.section h2 {
  font-size: 20px;
  margin-bottom: 20px;
  color: #333;
  padding-bottom: 10px;
  border-bottom: 2px solid #f0f0f0;
}

.ingredients-table {
  width: 100%;
  border-collapse: collapse;
}

.ingredients-table th, .ingredients-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.ingredients-table th {
  background: #fafafa;
  font-weight: 600;
  color: #555;
}

.not-suitable {
  color: #d32f2f;
  font-weight: 600;
  padding: 4px 8px;
  background: #ffebee;
  border-radius: 4px;
}

.suitable {
  color: #388e3c;
  font-weight: 600;
  padding: 4px 8px;
  background: #e8f5e9;
  border-radius: 4px;
}

.substitutions-section {
  background: #fff8e1;
  border: 1px solid #ffe082;
}

.substitution-card {
  background: white;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  border-left: 4px solid #ff9800;
}

.substitution-card:last-child {
  margin-bottom: 0;
}

.original-ingredient {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.warning-icon {
  font-size: 20px;
}

.reason {
  margin-left: auto;
  padding: 4px 8px;
  background: #ffeb3b;
  color: #f57c00;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.alternatives {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.alt-label {
  font-size: 14px;
  color: #666;
}

.alt-btn {
  padding: 8px 16px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.alt-btn:hover {
  background: #388e3c;
}

.applied-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.applied-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #e3f2fd;
  border-radius: 8px;
  font-size: 14px;
}

.remove-btn {
  padding: 4px 12px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.loading {
  text-align: center;
  padding: 60px;
  font-size: 18px;
  color: #666;
}

.elderly-mode .back-btn {
  font-size: 20px;
  padding: 14px 28px;
}

.elderly-mode .recipe-title h1 {
  font-size: 36px;
}

.elderly-mode .recipe-title p {
  font-size: 18px;
}

.elderly-mode .nutrition-summary {
  font-size: 18px;
  gap: 25px;
}

.elderly-mode .tag {
  font-size: 16px;
  padding: 6px 12px;
}

.elderly-mode .section h2 {
  font-size: 28px;
}

.elderly-mode .ingredients-table th, .elderly-mode .ingredients-table td {
  font-size: 18px;
  padding: 16px;
}

.elderly-mode .not-suitable, .elderly-mode .suitable {
  font-size: 16px;
  padding: 8px 12px;
}

.elderly-mode .substitution-card {
  padding: 20px;
}

.elderly-mode .alt-btn {
  font-size: 18px;
  padding: 12px 24px;
}

.elderly-mode .applied-item {
  font-size: 18px;
}

.elderly-mode .remove-btn {
  font-size: 16px;
  padding: 8px 16px;
}
</style>