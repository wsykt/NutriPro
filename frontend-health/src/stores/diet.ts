import { defineStore } from 'pinia'
import { setCache, getCache, removeCache } from '@/utils/storage'

const CACHE_KEY_MEALS = 'diet_meals'
const CACHE_KEY_NUTRITION = 'diet_nutrition'
const CACHE_KEY_SEARCH = 'diet_search'

export const useDietStore = defineStore('diet', {
  state: () => ({
    currentMeals: [] as any[],
    nutritionSummary: null as any | null,
    foodSearchResults: [] as any[],
    selectedMealType: '' as string
  }),
  actions: {
    async fetchTodayMeals(date?: string) {
      const today = date || new Date().toISOString().slice(0, 10)
      const cacheKey = `${CACHE_KEY_MEALS}_${today}`
      const cached = getCache<any[]>(cacheKey)
      if (cached) {
        this.currentMeals = cached
        return
      }
      const { api } = await import('../api')
      try {
        const data: any = await api.diet.getByDate(today)
        this.currentMeals = Array.isArray(data) ? data : []
        setCache(cacheKey, this.currentMeals, 5)
      } catch (e) {
        console.warn('获取当日饮食记录失败', e)
        this.currentMeals = []
      }
    },
    async addMeal(payload: { eatDate: string; mealType: string; remark?: string; items: any[] }) {
      const { api } = await import('../api')
      await api.diet.add(payload)
      // 清除当日缓存，下次 fetchTodayMeals 会重新拉取
      const today = payload.eatDate || new Date().toISOString().slice(0, 10)
      removeCache(`${CACHE_KEY_MEALS}_${today}`)
      removeCache(`${CACHE_KEY_NUTRITION}_${today}`)
    },
    async deleteMeal(mealId: number, date?: string) {
      const { api } = await import('../api')
      await api.diet.deleteMeal(mealId)
      const today = date || new Date().toISOString().slice(0, 10)
      removeCache(`${CACHE_KEY_MEALS}_${today}`)
      removeCache(`${CACHE_KEY_NUTRITION}_${today}`)
      // 从当前列表中移除
      this.currentMeals = this.currentMeals.filter((m: any) => m.mealId !== mealId)
    },
    async searchFood(keyword: string) {
      if (!keyword.trim()) {
        this.foodSearchResults = []
        return
      }
      const cacheKey = `${CACHE_KEY_SEARCH}_${keyword.trim()}`
      const cached = getCache<any[]>(cacheKey)
      if (cached) {
        this.foodSearchResults = cached
        return
      }
      const { api } = await import('../api')
      try {
        const data: any = await api.food.search(keyword.trim())
        this.foodSearchResults = Array.isArray(data) ? data : []
        setCache(cacheKey, this.foodSearchResults, 5)
      } catch (e) {
        console.warn('搜索食物失败', e)
        this.foodSearchResults = []
      }
    },
    async fetchNutritionSummary(date?: string) {
      const today = date || new Date().toISOString().slice(0, 10)
      const cacheKey = `${CACHE_KEY_NUTRITION}_${today}`
      const cached = getCache<any>(cacheKey)
      if (cached) {
        this.nutritionSummary = cached
        return
      }
      const { api } = await import('../api')
      try {
        const data: any = await api.diet.analyze(today)
        this.nutritionSummary = data
        setCache(cacheKey, data, 5)
      } catch (e) {
        console.warn('获取营养分析失败', e)
        this.nutritionSummary = null
      }
    },
    setMealType(type: string) {
      this.selectedMealType = type
    }
  },
  getters: {
    mealCount: (state) => state.currentMeals.length,
    hasMeals: (state) => state.currentMeals.length > 0
  }
})
