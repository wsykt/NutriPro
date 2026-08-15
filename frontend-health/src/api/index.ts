import axios from 'axios'
import { getToken, clearSession, resolveActAsUserId } from '@/utils/storage'
import { extractSSEEvents, parseSSEPayload } from '@/utils/sse'

const instance = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 1) 请求拦截：把 token 放进 header；
//    如果当前用户处于"替亲属操作"状态，自动把 targetUserId 附加到请求参数。
instance.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    const actAs = resolveActAsUserId()
    if (actAs != null) {
      // GET 请求用 params；其他请求把 targetUserId 加到 URL 查询串
      const method = (config.method || 'get').toLowerCase()
      if (method === 'get') {
        config.params = { ...(config.params || {}), targetUserId: actAs }
      } else {
        const sep = config.url && config.url.indexOf('?') >= 0 ? '&' : '?'
        config.url = `${config.url || ''}${sep}targetUserId=${actAs}`
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 2) 响应拦截：
//    - body.code==200 时自动把 data 字段剥离，让前端能直接访问；
//    - 401/403 时清除登录态与"替谁操作"标记，跳转到登录页。
instance.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object' && 'data' in body) {
      return body.data
    }
    return body
  },
  (error) => {
    const status = error?.response?.status
    const url = error?.config?.url || ''
    // 开发模式：profile/info 用 mock token 会返回 403，不跳登录页，避免无法预览页面
    const isDevProfileProbe = url.includes('/profile/info')
    if ((status === 401 || status === 403) && !isDevProfileProbe) {
      clearSession()
      if (
        window.location.pathname !== '/login' &&
        window.location.pathname !== '/register'
      ) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export const api = {
  auth: {
    login: (data: { username: string; password: string }) => instance.post('/auth/login', data),
    register: (data: any) => instance.post('/auth/register', data),
    resetPassword: (data: { username: string; newPassword: string }) => instance.post('/auth/reset-password', data)
  },
  food: {
    list: () => instance.get('/food/list'),
    search: (keyword: string) => instance.get('/food/search', { params: { keyword } }),
    getByCategory: (category: string) => instance.get(`/food/category/${category}`),
    add: (data: any) => instance.post('/food/add', data),
    getPending: () => instance.get('/food/pending'),
    approve: (id: number) => instance.post(`/food/approve/${id}`),
    reject: (id: number) => instance.post(`/food/reject/${id}`),
    batchLookup: (names: string[]) => instance.post('/food/batch-lookup', { names })
  },
  diet: {
    add: (data: any) => instance.post('/diet/add', data),
    getByDate: (date: string) => instance.get(`/diet/date/${date}`),
    analyze: (date: string) => instance.get(`/diet/analyze/${date}`),
    deleteMeal: (mealId: number) => instance.delete(`/diet/meal/${mealId}`)
  },
  profile: {
    getInfo: () => instance.get('/profile/info'),
    update: (data: any) => instance.put('/profile/update', data),
    snapshot: (date?: string) => instance.post('/profile/snapshot', null, { params: { date } })
  },
  admin: {
    listUsers: () => instance.get('/admin/users'),
    listUsersWithRelations: () => instance.get('/admin/users-with-relations'),
    getUserDetail: (userId: number) => instance.get(`/admin/users/${userId}`),
    deleteUser: (userId: number) => instance.delete(`/admin/users/${userId}`),
    listFoods: () => instance.get('/admin/food/list'),
    updateFood: (id: number, data: any) => instance.put(`/admin/food/update/${id}`, data),
    deleteFood: (id: number) => instance.delete(`/admin/food/${id}`),
    approveFood: (id: number) => instance.post(`/admin/food/approve/${id}`),
    rejectFood: (id: number) => instance.post(`/admin/food/reject/${id}`),
    getCrowdTypeStats: () => instance.get('/admin/stats/crowd-type')
  },
  report: {
    save: (data: any) => instance.post('/report/save', data),
    getByDate: (date: string) => instance.get(`/report/date/${date}`),
    list: () => instance.get('/report/list'),
    range: (startDate: string, endDate: string) => instance.get('/report/range', { params: { startDate, endDate } }),
    delete: (id: number) => instance.delete(`/report/${id}`)
  },
  // 亲属关系
  relation: {
    add: (wardUsername: string) => instance.post('/relation/add', { wardUsername }),
    confirm: (relationId: number) => instance.post(`/relation/confirm/${relationId}`),
    reject: (relationId: number) => instance.post(`/relation/reject/${relationId}`),
    myWards: () => instance.get('/relation/my-wards'),
    myGuardians: () => instance.get('/relation/my-guardians'),
    pendingInvitations: () => instance.get('/relation/pending-invitations'),
    remove: (relationId: number) => instance.delete(`/relation/${relationId}`)
  },
  // 身体指标历史
  metrics: {
    history: (userId: number) => instance.get(`/metrics/history/${userId}`),
    range: (userId: number, startDate: string, endDate: string) =>
      instance.get(`/metrics/history/${userId}/range`, { params: { startDate, endDate } }),
    save: (payload: any) => instance.post('/metrics/save', payload),
    deleteByDate: (recordDate: string) => instance.delete('/metrics/delete', { params: { recordDate } }),
    predict: (userId: number, days = 7) => instance.get(`/metrics/predict/${userId}`, { params: { days } })
  },
  // AI 健康咨询
  ai: {
    consult: (question: string) => instance.post('/ai/consult', { question }),
    // SSE 流式咨询：fetch 原生实现，支持 thinking/delta/done/error 事件回调
    consultStream: (
      question: string,
      handlers: {
        onThinking?: () => void
        onDelta?: (content: string) => void
        onDone?: (payload: any) => void
        onError?: (message: string) => void
      },
      options?: { high_performance?: boolean }
    ): { abort: () => void } => {
      const controller = new AbortController()
      const actAs = resolveActAsUserId()
      let url = '/api/ai/consult/stream'
      if (actAs != null) {
        url += `?targetUserId=${actAs}`
      }
      const token = getToken()
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (token) headers['Authorization'] = `Bearer ${token}`

      fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({ question, high_performance: options?.high_performance ?? false }),
        signal: controller.signal
      })
        .then(async (res) => {
          if (!res.ok || !res.body) {
            let errText = `HTTP ${res.status}`
            try {
              const j = await res.json()
              errText = j?.message || j?.data?.message || errText
            } catch { /* ignore */ }
            handlers.onError?.(errText)
            return
          }
          const reader = res.body.getReader()
          const decoder = new TextDecoder('utf-8')
          let buffer = ''
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            buffer += decoder.decode(value, { stream: true })
            // 解析逻辑统一走 utils/sse.ts（可单测，避免重复实现）
            const { events, rest } = extractSSEEvents(buffer)
            buffer = rest
            for (const ev of events) {
              const payload = parseSSEPayload(ev.data)
              if (ev.event === 'thinking') handlers.onThinking?.()
              else if (ev.event === 'delta') handlers.onDelta?.(String(payload.content ?? ''))
              else if (ev.event === 'done') handlers.onDone?.(payload)
              else if (ev.event === 'error') handlers.onError?.(String(payload.message ?? '未知错误'))
            }
          }
          // 处理无尾部空行的最后一条（补 \n\n 强制终止）
          const { events: tailEvents } = extractSSEEvents(buffer + '\n\n')
          for (const ev of tailEvents) {
            const payload = parseSSEPayload(ev.data)
            if (ev.event === 'done') handlers.onDone?.(payload)
            else if (ev.event === 'error') handlers.onError?.(String(payload.message ?? '未知错误'))
            else if (ev.event === 'delta') handlers.onDelta?.(String(payload.content ?? ''))
          }
        })
        .catch((e: any) => {
          if (e?.name === 'AbortError') return
          handlers.onError?.(e?.message || '网络异常，请稍后再试')
        })
      return { abort: () => controller.abort() }
    },
    generateRecipe: (prompt: string) => instance.post('/ai/generate-recipe', { prompt }),
    // 营养分析
    nutritionAnalyze: () => instance.post('/ai/nutrition/analyze'),
    // 食物审核
    foodAudit: (foodData: any) => instance.post('/ai/food/audit', foodData),
    // 语音文本解析
    voiceParse: (text: string) => instance.post('/ai/voice/parse', { text }),
    // 周报生成
    weeklyReport: () => instance.post('/ai/report/weekly'),
    // 文章生成
    articleGenerate: (topic: string, targetCrowd?: string) => instance.post('/ai/article/generate', { topic, target_crowd: targetCrowd || '' }),
    // 膳食计划
    dietPlan: (goal?: string) => instance.post('/ai/diet/plan', { goal: goal || '' }),
    // 菜谱推荐
    recipeRecommend: (ingredients: string[], crowdType?: string, goal?: string) =>
      instance.post('/ai/recipe/recommend', { ingredients, crowd_type: crowdType || '普通人', goal: goal || '健康饮食' }),
    // 运动建议
    exerciseAdvice: (goal?: string, preferences?: string) =>
      instance.post('/ai/exercise/advice', { goal: goal || '保持健康', preferences: preferences || '' }),
    // NLU 饮食解析
    mealParse: (text: string, mealType?: string) =>
      instance.post('/ai/meal/parse', { text, meal_type: mealType || '' }),
  },
  // 菜谱管理
  recipe: {
    search: (keyword: string) => instance.get('/recipes', { params: { keyword } }),
    list: () => instance.get('/recipes'),
    getDetail: (recipeId: number, userId?: number) => instance.get(`/recipes/${recipeId}/detail`, { params: { userId } }),
    getIngredients: (recipeId: number) => instance.get(`/recipes/${recipeId}/ingredients`),
    create: (data: any) => instance.post('/recipes', data),
    update: (id: number, data: any) => instance.put(`/recipes/${id}`, data),
    delete: (id: number) => instance.delete(`/recipes/${id}`),
    mySaved: () => instance.get('/recipe/my-saved'),
    save: (data: any) => instance.post('/recipe/save', data),
    deleteSaved: (id: number) => instance.delete(`/recipe/my-saved/${id}`)
  },
  // 科普文章
  article: {
    list: (params?: any) => instance.get('/articles', { params }),
    detail: (id: number) => instance.get(`/articles/${id}`),
    create: (data: any) => instance.post('/articles', data),
    update: (id: number, data: any) => instance.put(`/articles/${id}`, data),
    delete: (id: number) => instance.delete(`/articles/${id}`),
    search: (keyword: string) => instance.get('/articles/search', { params: { keyword } }),
    categories: () => instance.get('/articles/categories'),
    topics: () => instance.get('/articles/topics'),
    like: (id: number) => instance.post(`/articles/${id}/like`),
    // AI 生成：主题 + 人群 → 母稿 → 拆分三版 → 入库
    // B方案双模型流水线（本地框架→云端外扩→本地校验）实测约 2~3 分钟，需单独放宽超时
    generate: (topic: string, persona?: string) =>
      instance.post('/articles/generate', { topic, persona: persona || '普通人群' }, { timeout: 320000 }),
    // 同主题不同篇幅的相关文章
    related: (topicGroupId: string, excludeId?: number) =>
      instance.get(`/articles/related/${topicGroupId}`, { params: { excludeId } }),
    // 按主题分组ID获取三版
    topicGroup: (topicGroupId: string) => instance.get(`/articles/topic-group/${topicGroupId}`)
  }
} as Record<string, any>
