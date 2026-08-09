import { defineStore } from 'pinia'
import { setCache, getCache, removeCache } from '@/utils/storage'

const CACHE_KEY_RECIPES = 'recipe_list'
const CACHE_KEY_FAVORITES = 'recipe_favorites'

export const useRecipeStore = defineStore('recipe', {
  state: () => ({
    recipes: [] as any[],
    selectedRecipe: null as any | null,
    favorites: [] as number[] // 收藏的菜谱ID集合
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
          await api.recipe.deleteSaved(id)
          this.favorites = this.favorites.filter(fid => fid !== id)
        } else {
          await api.recipe.save({
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
            source: 'system'
          })
          this.favorites = [...this.favorites, id]
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
        const ids = (Array.isArray(data) ? data : [])
          .map((r: any) => r.recipeId ?? r.id ?? r.originalId)
          .filter((id: any) => id != null)
        this.favorites = ids
        setCache(CACHE_KEY_FAVORITES, ids, 10)
      } catch (e) {
        console.warn('获取收藏菜谱失败', e)
        this.favorites = []
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
