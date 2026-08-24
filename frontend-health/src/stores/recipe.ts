import { defineStore } from 'pinia'
import { setCache, getCache, removeCache } from '@/utils/storage'

const CACHE_KEY_RECIPES = 'recipe_list'
const CACHE_KEY_FAVORITES = 'recipe_favorites'

export const useRecipeStore = defineStore('recipe', {
  state: () => ({
    recipes: [] as any[],
    selectedRecipe: null as any | null,
    favorites: [] as number[], // 收藏的展示ID集合（系统菜谱ID 或 收藏记录主键）
    savedMap: {} as Record<string, number> // 展示ID → 收藏记录主键(saved_recipe.id)，用于取消收藏时精确定位
  }),
  actions: {
    async fetchRecipes() {
      const cached = getCache<any[]>(CACHE_KEY_RECIPES)
      if (cached) {
        this.recipes = cached
        return
      }
      const { api } = await import('../api')
      try {
        const list: any = await api.recipe.list()
        const normalized = (Array.isArray(list) ? list : []).map((r: any) => ({
          id: r.recipeId ?? r.id,
          name: r.recipeName ?? r.name ?? r.title ?? '',
          description: r.description ?? '',
          calories: r.calories ?? 0,
          protein: r.protein ?? 0,
          fat: r.fat ?? 0,
          carbs: r.carbs ?? 0,
          fiber: r.fiber ?? 0,
          tags: typeof r.tags === 'string'
            ? r.tags.split(',').map((t: string) => t.trim()).filter(Boolean)
            : (r.tags || []),
          ingredients: r.ingredients || r.recipeIngredients || [],
          steps: r.steps || [],
          isSaved: r.isSaved || false
        }))
        this.recipes = normalized
        setCache(CACHE_KEY_RECIPES, normalized, 10)
      } catch (e) {
        console.warn('获取菜谱列表失败', e)
        this.recipes = []
      }
    },
    async fetchRecipeById(id: number) {
      const { api } = await import('../api')
      try {
        const data: any = await api.recipe.getDetail(id)
        this.selectedRecipe = data
        return data
      } catch (e) {
        console.warn('获取菜谱详情失败', e)
        this.selectedRecipe = null
        return null
      }
    },
    async toggleFavorite(recipe: any) {
      if (!recipe) return
      const id = recipe.id || recipe.recipeId
      if (id == null) return
      const isFav = this.favorites.includes(id)
      const { api } = await import('../api')
      try {
        if (isFav) {
          // 取消收藏：优先用"系统菜谱ID → 收藏记录主键"映射精确定位，
          // 映射丢失时后端也会按来源系统菜谱ID兜底删除，避免删错别的收藏
          const savedId = this.savedMap[String(id)] ?? id
          await api.recipe.deleteSaved(savedId)
          this.favorites = this.favorites.filter(fid => fid !== id)
          delete this.savedMap[String(id)]
        } else {
          const saved: any = await api.recipe.save({
            title: recipe.name || recipe.recipeName || '',
            steps: JSON.stringify(recipe.steps || []),
            ingredients: JSON.stringify(recipe.ingredients || recipe.recipeIngredients || []),
            nutritionSummary: JSON.stringify({
              calories: recipe.calories ?? 0,
              protein: recipe.protein ?? 0,
              fat: recipe.fat ?? 0,
              carbs: recipe.carbs ?? 0,
              fiber: recipe.fiber ?? 0,
              tags: recipe.tags || []
            }),
            source: 'system',
            // 记录来源系统菜谱ID，取消收藏时精确删除，避免用系统ID误删其他收藏
            originalRecipeId: id
          })
          this.favorites = [...this.favorites, id]
          if (saved?.id != null) {
            this.savedMap[String(id)] = saved.id
          }
        }
        // 清除收藏缓存
        removeCache(CACHE_KEY_FAVORITES)
      } catch (e) {
        console.warn('切换收藏状态失败', e)
      }
    },
    async fetchFavorites() {
      const cached = getCache<number[]>(CACHE_KEY_FAVORITES)
      if (cached) {
        this.favorites = cached
        return
      }
      const { api } = await import('../api')
      try {
        const data: any = await api.recipe.mySaved()
        const ids: number[] = []
        const map: Record<string, number> = {}
        ;(Array.isArray(data) ? data : []).forEach((r: any) => {
          // 收藏记录主键（AI生成/无原ID时作为展示ID）
          const pk = r.id
          // 系统菜谱：展示ID用原菜谱ID，并记录 pk 映射；否则用收藏主键
          const displayId = r.originalRecipeId ?? pk
          if (pk != null) map[String(displayId)] = pk
          if (displayId != null) ids.push(displayId)
        })
        this.favorites = ids
        this.savedMap = map
        setCache(CACHE_KEY_FAVORITES, ids, 10)
      } catch (e) {
        console.warn('获取收藏菜谱失败', e)
        this.favorites = []
        this.savedMap = {}
      }
    },
    async searchRecipes(keyword: string) {
      const { api } = await import('../api')
      try {
        const data: any = await api.recipe.search(keyword)
        this.recipes = (Array.isArray(data) ? data : []).map((r: any) => ({
          id: r.recipeId ?? r.id,
          name: r.recipeName ?? r.name ?? r.title ?? '',
          description: r.description ?? '',
          calories: r.calories ?? 0,
          protein: r.protein ?? 0,
          fat: r.fat ?? 0,
          carbs: r.carbs ?? 0,
          fiber: r.fiber ?? 0,
          tags: typeof r.tags === 'string'
            ? r.tags.split(',').map((t: string) => t.trim()).filter(Boolean)
            : (r.tags || []),
          ingredients: r.ingredients || r.recipeIngredients || [],
          steps: r.steps || []
        }))
      } catch (e) {
        console.warn('搜索菜谱失败', e)
        this.recipes = []
      }
    }
  },
  getters: {
    isFavorited: (state) => {
      return (recipeId: number) => state.favorites.includes(recipeId)
    },
    favoriteCount: (state) => state.favorites.length,
    recipeCount: (state) => state.recipes.length
  }
})
