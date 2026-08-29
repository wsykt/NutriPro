import axios from 'axios'
import { getToken, clearSession, resolveActAsUserId } from '@/utils/storage'
import { extractSSEEvents, parseSSEPayload } from '@/utils/sse'
import type {
  LoginResult, UserInfo, FoodItem, DietAnalysis, SavedRecipeItem,
  RecipeItem, ArticleItem, WardRelation, MetricsRecord, AiResult
} from './types'

export const instance = axios.create({
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
//    - 统一响应 {code,message,data}：仅当业务成功(code==200 或无 code 字段)时才剥离 data 让前端直接访问；
//      后端存在"HTTP 200 + code 500/400"的错误路径，若不检查 code 会把错误静默吞成 null/错误形状，
//      导致登录失败只显示"登录失败，请稍后重试"、头像上传收不到真实 message。此处显式把业务错误抛出。
//    - 401/403 时清除登录态与"替谁操作"标记，跳转到登录页。
instance.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object') {
      if (typeof body.code === 'number' && body.code !== 200) {
        const err: any = new Error(body.message || `请求失败(${body.code})`)
        err.code = body.code
        err.biz = body
        return Promise.reject(err)
      }
      if ('data' in body) {
        return body.data
      }
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
      // 应用使用 createWebHashHistory，登录路由实际是 /#/login；
      // window.location.pathname 在 hash 模式下始终是 '/'，无法用来判断当前页。
      if (window.location.hash !== '#/login' && window.location.hash !== '#/register') {
        window.location.hash = '#/login'
      }
    }
    return Promise.reject(error)
  }
)

export const api = {
  auth: {
    login: (data: { username: string; password: string }) => instance.post<LoginResult, LoginResult>('/auth/login', data),
    register: (data: { username: string; password: string; gender?: string; height?: number; weight?: number; age?: number; crowdType?: string }) =>
      instance.post<LoginResult, LoginResult>('/auth/register', data),
    resetPassword: (data: { username: string; oldPassword?: string; newPassword: string }) =>
      instance.post<null, null>('/auth/reset-password', data)
  },
  food: {
    list: () => instance.get<FoodItem[], FoodItem[]>('/food/list'),
    search: (keyword: string) => instance.get<FoodItem[], FoodItem[]>('/food/search', { params: { keyword } }),
    getByCategory: (category: string) => instance.get<FoodItem[], FoodItem[]>(`/food/category/${category}`),
    add: (data: any) => instance.post('/food/add', data),
    getPending: () => instance.get<any[], any[]>('/food/pending'),
    approve: (id: number) => instance.post(`/food/approve/${id}`),
    reject: (id: number) => instance.post(`/food/reject/${id}`),
    batchLookup: (names: string[]) => instance.post('/food/batch-lookup', { names })
  },
  diet: {
    add: (data: any) => instance.post('/diet/add', data),
    getByDate: (date: string) => instance.get<any, any>(`/diet/date/${date}`),
    analyze: (date: string) => instance.get<DietAnalysis, DietAnalysis>(`/diet/analyze/${date}`),
    deleteMeal: (mealId: number) => instance.delete(`/diet/meal/${mealId}`)
  },
  profile: {
    getInfo: () => instance.get<UserInfo, UserInfo>('/profile/info'),
    update: (data: any) => instance.put('/profile/update', data),
    // 饮食档案（过敏/忌口/口味偏好）
    updateDietary: (data: { allergicFoods?: string; dietaryRestrictions?: string; tastePreference?: string }) =>
      instance.put<any, any>('/profile/dietary', data),
    snapshot: (date?: string) => instance.post<any, any>('/profile/snapshot', null, { params: { date } })
  },
  file: {
    // 上传头像：FormData（avatar blob + userId）
    uploadAvatar: (formData: FormData) =>
      instance.post<any, any>('/file/uploadAvatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000
      }).then((res: any) => {
        // 响应拦截器可能已剥离 data，也可能返回完整响应
        const d = res?.data ?? res
        if (d && typeof d === 'string') return d
        if (d && d.url) return d.url
        if (d && d.avatar) return d.avatar
        return d
      })
  },
  admin: {
    listUsers: () => instance.get<any[], any[]>('/admin/users'),
    listUsersWithRelations: () => instance.get<any[], any[]>('/admin/users-with-relations'),
    getUserDetail: (userId: number) => instance.get<any, any>(`/admin/users/${userId}`),
    // AI 流程展示：取目标用户的实时健康上下文（体征/饮食/运动），供流水线作为目标人群注入
    getFlowUserDetail: (userId: number) => instance.get<any, any>(`/admin/flow/user-detail/${userId}`),
    deleteUser: (userId: number) => instance.delete(`/admin/users/${userId}`),
    listFoods: () => instance.get<FoodItem[], FoodItem[]>('/admin/food/list'),
    updateFood: (id: number, data: any) => instance.put(`/admin/food/update/${id}`, data),
    deleteFood: (id: number) => instance.delete(`/admin/food/${id}`),
    approveFood: (id: number) => instance.post(`/admin/food/approve/${id}`),
    rejectFood: (id: number) => instance.post(`/admin/food/reject/${id}`),
    getCrowdTypeStats: () => instance.get<any, any>('/admin/stats/crowd-type')
  },
  report: {
    save: (data: any) => instance.post('/report/save', data),
    getByDate: (date: string) => instance.get<any, any>(`/report/date/${date}`),
    list: () => instance.get<any[], any[]>('/report/list'),
    range: (startDate: string, endDate: string) => instance.get<any[], any[]>('/report/range', { params: { startDate, endDate } }),
    delete: (id: number) => instance.delete(`/report/${id}`)
  },
  // 亲属关系
  relation: {
    add: (wardUsername: string) => instance.post<any, any>('/relation/add', { wardUsername }),
    confirm: (relationId: number) => instance.post<any, any>(`/relation/confirm/${relationId}`),
    reject: (relationId: number) => instance.post<any, any>(`/relation/reject/${relationId}`),
    myWards: () => instance.get<WardRelation[], WardRelation[]>('/relation/my-wards'),
    myGuardians: () => instance.get<WardRelation[], WardRelation[]>('/relation/my-guardians'),
    pendingInvitations: () => instance.get<WardRelation[], WardRelation[]>('/relation/pending-invitations'),
    remove: (relationId: number) => instance.delete(`/relation/${relationId}`)
  },
  // 身体指标历史
  metrics: {
    history: (userId: number) => instance.get<MetricsRecord[], MetricsRecord[]>(`/metrics/history/${userId}`),
    range: (userId: number, startDate: string, endDate: string) =>
      instance.get<MetricsRecord[], MetricsRecord[]>(`/metrics/history/${userId}/range`, { params: { startDate, endDate } }),
    save: (payload: any) => instance.post('/metrics/save', payload),
    deleteByDate: (recordDate: string) => instance.delete('/metrics/delete', { params: { recordDate } }),
    predict: (userId: number, days = 7) => instance.get<any, any>(`/metrics/predict/${userId}`, { params: { days } })
  },
  // 运动记录
  exercise: {
    getRecords: () => instance.get<any, any>('/exercise/records'),
    recordsRange: (startDate: string, endDate: string) =>
      instance.get<any[], any[]>('/exercise/records/range', { params: { startDate, endDate } }),
    statsWeek: () => instance.get<any, any>('/exercise/stats/week'),
    statsToday: () => instance.get<any, any>('/exercise/stats/today')
  },
  // AI 健康咨询
  ai: {
    consult: (question: string) => instance.post<AiResult, AiResult>('/ai/consult', { question }),
    // 本地知识库检索：按营养问题检索知识卡片，供 AI 分析注入提示词
    knowledgeRetrieve: (data: { query: string; top_k?: number; target_crowd?: string }) =>
      instance.post<any, any>('/ai/knowledge/retrieve', data),
    // SSE 流式咨询：fetch 原生实现，支持 thinking/delta/done/error 事件回调
    consultStream: (
      question: string,
      handlers: {
        onThinking?: () => void
        onDelta?: (content: string) => void
        onDone?: (payload: any) => void
        onError?: (message: string) => void
      },
      options?: { high_performance?: boolean; report_context?: any }
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

      const body: Record<string, any> = {
        question,
        high_performance: options?.high_performance ?? false,
      }
      if (options?.report_context != null) {
        body._report_context = options.report_context
      }

      fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
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
    generateRecipe: (prompt: string) => instance.post<any, any>('/ai/generate-recipe', { prompt }, { timeout: 300000 }),
    // 营养分析
    nutritionAnalyze: () => instance.post<any, any>('/ai/nutrition/analyze'),
    // 食物审核
    foodAudit: (foodData: any) => instance.post<any, any>('/ai/food/audit', foodData),
    // 语音文本解析
    voiceParse: (text: string) => instance.post<any, any>('/ai/voice/parse', { text }),
    // 周报生成
    weeklyReport: () => instance.post<any, any>('/ai/report/weekly'),
    // 文章生成
    articleGenerate: (topic: string, targetCrowd?: string) => instance.post<any, any>('/ai/article/generate', { topic, target_crowd: targetCrowd || '' }),
    // 膳食计划
    dietPlan: (goal?: string) => instance.post<any, any>('/ai/diet/plan', { goal: goal || '' }),
    // 菜谱推荐
    recipeRecommend: (ingredients: string[], crowdType?: string, goal?: string) =>
      instance.post<any, any>('/ai/recipe/recommend', { ingredients, crowd_type: crowdType || '普通人', goal: goal || '健康饮食' }),
    // 运动建议
    exerciseAdvice: (goal?: string, preferences?: string) =>
      instance.post<any, any>('/ai/exercise/advice', { goal: goal || '保持健康', preferences: preferences || '' }),
    // NLU 饮食解析
    mealParse: (text: string, mealType?: string) =>
      instance.post<any, any>('/ai/meal/parse', { text, meal_type: mealType || '' }),
  },
  // 菜谱管理
  recipe: {
    search: (keyword: string) => instance.get<RecipeItem[], RecipeItem[]>('/recipes', { params: { keyword } }),
    list: () => instance.get<RecipeItem[], RecipeItem[]>('/recipes'),
    getDetail: (recipeId: number, userId?: number) => instance.get<any, any>(`/recipes/${recipeId}/detail`, { params: { userId } }),
    getIngredients: (recipeId: number) => instance.get<any[], any[]>(`/recipes/${recipeId}/ingredients`),
    create: (data: any) => instance.post('/recipes', data),
    update: (id: number, data: any) => instance.put(`/recipes/${id}`, data),
    delete: (id: number) => instance.delete(`/recipes/${id}`),
    mySaved: () => instance.get<SavedRecipeItem[], SavedRecipeItem[]>('/recipe/my-saved'),
    save: (data: any) => instance.post<SavedRecipeItem, SavedRecipeItem>('/recipe/save', data),
    deleteSaved: (id: number) => instance.delete(`/recipe/my-saved/${id}`)
  },
  // 科普文章
  article: {
    list: (params?: any) => instance.get<ArticleItem[], ArticleItem[]>('/articles', { params }),
    detail: (id: number) => instance.get<ArticleItem, ArticleItem>(`/articles/${id}`),
    create: (data: any) => instance.post('/articles', data),
    update: (id: number, data: any) => instance.put(`/articles/${id}`, data),
    delete: (id: number) => instance.delete(`/articles/${id}`),
    search: (keyword: string) => instance.get<ArticleItem[], ArticleItem[]>('/articles/search', { params: { keyword } }),
    categories: () => instance.get<string[], string[]>('/articles/categories'),
    topics: () => instance.get<any[], any[]>('/articles/topics'),
    like: (id: number) => instance.post(`/articles/${id}/like`),
    // AI 生成：主题 + 人群 → 母稿 → 拆分三版 → 入库
    // B方案双模型流水线（本地框架→云端外扩→本地校验）实测约 2~3 分钟，需单独放宽超时
    generate: (topic: string, persona?: string) =>
      instance.post<any, any>('/articles/generate', { topic, persona: persona || '普通人群' }, { timeout: 320000 }),
    // 同主题不同篇幅的相关文章
    related: (topicGroupId: string, excludeId?: number) =>
      instance.get<ArticleItem[], ArticleItem[]>(`/articles/related/${topicGroupId}`, { params: { excludeId } }),
    // 按主题分组ID获取三版
    topicGroup: (topicGroupId: string) => instance.get<ArticleItem[], ArticleItem[]>(`/articles/topic-group/${topicGroupId}`)
  }
}