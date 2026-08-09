import { defineStore } from 'pinia'
import { setCache, getCache } from '@/utils/storage'

const CACHE_KEY_ARTICLES = 'article_list'

export interface ArticleFilters {
  category?: string
  audience?: string
}

export const useArticleStore = defineStore('article', {
  state: () => ({
    articles: [] as any[],
    selectedArticle: null as any | null,
    loading: false as boolean,
    error: '' as string,
    filters: {
      category: '',
      audience: ''
    } as ArticleFilters,
    currentTopic: '' as string
  }),
  actions: {
    async fetchArticles(params?: any) {
      this.loading = true
      this.error = ''
      const cacheKey = params?.category
        ? `${CACHE_KEY_ARTICLES}_${params.category}`
        : CACHE_KEY_ARTICLES
      const cached = getCache<any[]>(cacheKey)
      if (cached) {
        this.articles = cached
        this.loading = false
        return
      }
      const { api } = await import('../api')
      try {
        const data: any = await api.article.list(params)
        this.articles = Array.isArray(data) ? data : []
        setCache(cacheKey, this.articles, 30)
      } catch (e: any) {
        console.warn('获取文章列表失败', e)
        this.error = e?.message || '无法连接后端服务，请确保后端已启动'
        this.articles = []
      } finally {
        this.loading = false
      }
    },
    async fetchArticleById(id: number) {
      const { api } = await import('../api')
      try {
        const data: any = await api.article.detail(id)
        this.selectedArticle = data
        return data
      } catch (e) {
        console.warn('获取文章详情失败', e)
        this.selectedArticle = null
        return null
      }
    },
    async fetchByCategory(category: string) {
      const cacheKey = `${CACHE_KEY_ARTICLES}_${category}`
      const cached = getCache<any[]>(cacheKey)
      if (cached) {
        this.articles = cached
        return
      }
      const { api } = await import('../api')
      try {
        const data: any = await api.article.list({ category })
        this.articles = Array.isArray(data) ? data : []
        setCache(cacheKey, this.articles, 30)
      } catch (e) {
        console.warn('按分类获取文章失败', e)
        this.articles = []
      }
    },
    async fetchByTopic(topic: string) {
      this.currentTopic = topic
      const cacheKey = `${CACHE_KEY_ARTICLES}_topic_${topic}`
      const cached = getCache<any[]>(cacheKey)
      if (cached) {
        this.articles = cached
        return
      }
      const { api } = await import('../api')
      try {
        // 优先用 topicGroup 接口获取同一话题的三版文章
        const data: any = await api.article.topicGroup(topic)
        this.articles = Array.isArray(data) ? data : []
        setCache(cacheKey, this.articles, 30)
      } catch {
        // 回退：用 list 接口按关键词搜索
        try {
          const { api } = await import('../api')
          const data: any = await api.article.search(topic)
          this.articles = Array.isArray(data) ? data : []
          setCache(cacheKey, this.articles, 30)
        } catch (e) {
          console.warn('按话题获取文章失败', e)
          this.articles = []
        }
      }
    },
    async fetchRelatedArticles(topicGroupId: string, excludeId?: number) {
      const { api } = await import('../api')
      try {
        const data: any = await api.article.related(topicGroupId, excludeId)
        return Array.isArray(data) ? data : []
      } catch (e) {
        console.warn('获取相关文章失败', e)
        return []
      }
    },
    async searchArticles(keyword: string) {
      const { api } = await import('../api')
      try {
        const data: any = await api.article.search(keyword)
        this.articles = Array.isArray(data) ? data : []
      } catch (e) {
        console.warn('搜索文章失败', e)
        this.articles = []
      }
    },
    setFilter(filter: Partial<ArticleFilters>) {
      this.filters = { ...this.filters, ...filter }
    },
    setTopic(topic: string) {
      this.currentTopic = topic
    },
    clearFilters() {
      this.filters = { category: '', audience: '' }
      this.currentTopic = ''
    }
  },
  getters: {
    filteredArticles: (state) => {
      let list = state.articles
      if (state.filters.category) {
        list = list.filter((a: any) => a.category === state.filters.category)
      }
      if (state.filters.audience) {
        list = list.filter((a: any) => a.audience === state.filters.audience)
      }
      return list
    },
    articleCount: (state) => state.articles.length,
    hasArticles: (state) => state.articles.length > 0
  }
})
