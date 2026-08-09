<template>
  <div class="page-fade">
    <div class="mb-6">
      <h2 class="text-2xl font-bold mb-2 text-morandi-text">食谱库</h2>
      <p class="text-morandi-lightText mb-6 text-sm">浏览健康食谱，支持AI智能生成</p>
    </div>

    <!-- Tabs 切换 -->
    <div class="flex items-center gap-1 mb-6 bg-white/60 rounded-xl p-1 border border-morandi-soft/30 w-fit">
      <button
        @click="currentTab = 'all'"
        :class="[
          'px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200',
          currentTab === 'all'
            ? 'bg-morandi-accent text-white shadow-sm'
            : 'text-morandi-lightText hover:text-morandi-text'
        ]"
      >
        全部食谱
      </button>
      <button
        @click="currentTab = 'saved'; loadMySavedRecipes()"
        :class="[
          'px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200',
          currentTab === 'saved'
            ? 'bg-morandi-accent text-white shadow-sm'
            : 'text-morandi-lightText hover:text-morandi-text'
        ]"
      >
        我的收藏
      </button>
    </div>

    <!-- 搜索栏和操作区 -->
    <div class="flex flex-wrap items-center gap-4 mb-6">
      <div class="flex-1 max-w-md">
        <input
          v-if="currentTab === 'all'"
          v-model="searchKeyword"
          @input="handleSearch"
          type="text"
          placeholder="搜索食谱..."
          class="w-full px-4 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm outline-none transition-all focus:border-morandi-accent"
        />
        <input
          v-else
          v-model="savedSearchKeyword"
          type="text"
          placeholder="搜索收藏的食谱..."
          class="w-full px-4 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm outline-none transition-all focus:border-morandi-accent"
        />
      </div>
      <div v-if="currentTab === 'all'" class="flex flex-wrap gap-2">
        <button
          v-for="tag in recipeTags"
          :key="tag"
          @click="selectTag(tag)"
          :class="[
            'px-3 py-2 rounded-full text-sm transition-all duration-200',
            selectedTags.includes(tag)
              ? 'bg-morandi-accent text-white shadow-sm scale-[1.02]'
              : 'bg-white/70 border border-morandi-soft text-morandi-text hover:bg-morandi-soft'
          ]"
        >
          {{ tag }}
        </button>
      </div>
      <button
        @click="showGenerateDialog = true"
        class="px-4 py-2 rounded-lg bg-morandi-accent text-white text-sm hover:opacity-90 hover:scale-[1.02] transition-all shadow-sm"
      >
        AI生成食谱
      </button>
    </div>

    <!-- 食谱卡片列表 -->
    <div v-if="currentTab === 'all'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <RecipeCard
        v-for="recipe in recipes"
        :key="recipe.id"
        :recipe="recipe"
        @view="viewRecipe"
      />
    </div>

    <!-- 我的收藏卡片列表 -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <RecipeCard
        v-for="recipe in filteredSavedRecipes"
        :key="recipe.id"
        :recipe="recipe"
        show-delete
        @view="viewRecipe"
        @delete="deleteMyRecipe"
      />
    </div>

    <!-- 空状态 -->
    <div
      v-if="(currentTab === 'all' && recipes.length === 0) || (currentTab === 'saved' && filteredSavedRecipes.length === 0)"
      class="text-center py-16 text-morandi-lightText"
    >
      <div class="text-6xl mb-4 opacity-60"><component :is="BookOpen" class="w-16 h-16 mx-auto" /></div>
      <p class="text-base">{{ currentTab === 'all' ? '暂无食谱，点击右上角「AI生成食谱」快速创建' : '暂无收藏的食谱，浏览全部食谱并收藏' }}</p>
    </div>

    <!-- AI生成食谱弹窗 -->
    <RecipeGenerateDialog
      v-model="showGenerateDialog"
      :persona-tags="personaTags"
      @generated="loadRecipes"
    />

    <!-- 食谱详情弹窗 -->
    <RecipeDetailDialog
      v-model="showDetailDialog"
      :recipe="selectedRecipe"
      @save="saveRecipe"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '@/api'
import { useRecipeStore } from '@/stores/recipe'
import { RECIPE_TAGS, RECIPE_PERSONA_TAGS } from '@/constants'
import { BookOpen } from 'lucide-vue-next'
import RecipeCard from './RecipeCard.vue'
import RecipeGenerateDialog from './RecipeGenerateDialog.vue'
import RecipeDetailDialog from './RecipeDetailDialog.vue'

const recipeStore = useRecipeStore()

const recipeTags = RECIPE_TAGS as unknown as string[]
const personaTags = RECIPE_PERSONA_TAGS as unknown as string[]

const currentTab = ref<'all' | 'saved'>('all')
const searchKeyword = ref('')
const savedSearchKeyword = ref('')
const selectedTags = ref<string[]>([])
const recipes = ref<any[]>([])
const showGenerateDialog = ref(false)
const showDetailDialog = ref(false)
const selectedRecipe = ref<any>(null)
const mySavedRecipes = ref<any[]>([])

/** 搜索过滤我的收藏 */
const filteredSavedRecipes = computed(() => {
  if (!savedSearchKeyword.value.trim()) return mySavedRecipes.value
  const kw = savedSearchKeyword.value.toLowerCase().trim()
  return mySavedRecipes.value.filter((r: any) =>
    r.name?.toLowerCase().includes(kw) ||
    r.description?.toLowerCase().includes(kw) ||
    r.tags?.some((t: string) => t.toLowerCase().includes(kw))
  )
})

/** 转换系统食谱格式: recipeId→id, recipeName→name, tags字符串→数组 */
function normalizeRecipe(r: any): any {
  return {
    id: r.recipeId ?? r.id,
    name: r.recipeName ?? r.name ?? '',
    description: r.description ?? '',
    calories: r.calories ?? 0,
    protein: r.protein ?? 0,
    fat: r.fat ?? 0,
    carbs: r.carbs ?? 0,
    fiber: r.fiber ?? 0,
    tags: typeof r.tags === 'string' ? r.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : (r.tags || []),
    ingredients: r.ingredients || r.recipeIngredients || [],
    originalId: r.originalId,
    isSaved: r.isSaved
  }
}

/** 转换收藏食谱格式 */
function normalizeSavedRecipe(saved: any): any {
  let nutrition: any = {}
  if (saved.nutritionSummary) {
    try {
      nutrition = typeof saved.nutritionSummary === 'string' ? JSON.parse(saved.nutritionSummary) : saved.nutritionSummary
    } catch { nutrition = {} }
  }
  let ingredients: any[] = []
  if (saved.ingredients) {
    try {
      ingredients = typeof saved.ingredients === 'string' ? JSON.parse(saved.ingredients) : saved.ingredients
    } catch { ingredients = [] }
  }
  let steps: string[] = []
  if (saved.steps) {
    try {
      steps = typeof saved.steps === 'string' ? JSON.parse(saved.steps) : saved.steps
    } catch { steps = [] }
  }
  return {
    id: saved.id,
    name: saved.title,
    description: steps.length > 0 ? steps[0] : (nutrition.description || ''),
    steps: steps,
    calories: nutrition.calories || 0,
    protein: nutrition.protein || 0,
    fat: nutrition.fat || 0,
    carbs: nutrition.carbs || 0,
    fiber: nutrition.fiber || 0,
    tags: nutrition.tags || [],
    ingredients: ingredients,
    isSaved: true,
    originalId: saved.id,
    source: saved.source || ''
  }
}

const loadRecipes = async () => {
  try {
    const systemRecipes = await api.recipe.list()
    let allRecipes = systemRecipes.map(normalizeRecipe)

    try {
      const savedRecipesData = await api.recipe.mySaved()
      const savedRecipes = savedRecipesData
        .map(normalizeSavedRecipe)
        .filter((r: any) => r.source === 'generated')
      allRecipes = [...allRecipes, ...savedRecipes]
    } catch { /* ignore */ }

    recipes.value = allRecipes

    if (selectedTags.value.length > 0) {
      recipes.value = allRecipes.filter((r: any) =>
        r.tags?.some((t: string) => selectedTags.value.includes(t))
      )
    } else if (searchKeyword.value) {
      recipes.value = allRecipes.filter((r: any) =>
        r.name?.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
        r.description?.toLowerCase().includes(searchKeyword.value.toLowerCase())
      )
    }
  } catch (e) {
    console.error('加载食谱失败', e)
  }
}

const handleSearch = () => {
  selectedTags.value = []
  loadRecipes()
}

const selectTag = (tag: string) => {
  const index = selectedTags.value.indexOf(tag)
  if (index === -1) {
    selectedTags.value.push(tag)
  } else {
    selectedTags.value.splice(index, 1)
  }
  searchKeyword.value = ''
  loadRecipes()
}

const loadMySavedRecipes = async () => {
  try {
    await recipeStore.fetchFavorites()
    const data = await api.recipe.mySaved()
    mySavedRecipes.value = data.map(normalizeSavedRecipe)
  } catch (e) {
    console.error('加载我的食谱失败', e)
  }
}

const deleteMyRecipe = async (id: number) => {
  if (!confirm('确定删除这条食谱？')) return
  try {
    await api.recipe.deleteSaved(id)
    await loadMySavedRecipes()
    await loadRecipes()
    alert('删除成功')
  } catch (e: any) {
    console.error('删除食谱失败', e)
    alert('删除失败：' + (e?.response?.data?.message || e?.message || '未知错误'))
  }
}

const viewRecipe = (recipe: any) => {
  selectedRecipe.value = recipe
  showDetailDialog.value = true
}

const saveRecipe = async (recipe: any) => {
  if (!recipe) return
  try {
    await recipeStore.toggleFavorite(recipe)
    showDetailDialog.value = false
    loadRecipes()
  } catch (e: any) {
    console.error('保存食谱失败', e)
    alert('保存失败：' + (e?.response?.data?.message || e?.message || '未知错误'))
  }
}

watch([showGenerateDialog, showDetailDialog], (newVal) => {
  if (newVal[0] || newVal[1]) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

onMounted(() => {
  loadRecipes()
})
</script>

<style scoped>
.page-fade {
  animation: fadeIn 0.3s ease forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
