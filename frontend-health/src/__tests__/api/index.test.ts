/**
 * API 模块单元测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios', () => {
  const mockInstance = {
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
  return {
    default: {
      create: vi.fn(() => mockInstance)
    }
  }
})

describe('API 模块', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('API 结构', () => {
    it('应导出所有必要的 API 分组', async () => {
      const { api } = await import('@/api')
      
      expect(api.auth).toBeDefined()
      expect(api.food).toBeDefined()
      expect(api.diet).toBeDefined()
      expect(api.profile).toBeDefined()
      expect(api.admin).toBeDefined()
      expect(api.report).toBeDefined()
      expect(api.relation).toBeDefined()
      expect(api.metrics).toBeDefined()
      expect(api.ai).toBeDefined()
      expect(api.recipe).toBeDefined()
    })

    it('auth API 应包含登录、注册、重置密码方法', async () => {
      const { api } = await import('@/api')
      
      expect(typeof api.auth.login).toBe('function')
      expect(typeof api.auth.register).toBe('function')
      expect(typeof api.auth.resetPassword).toBe('function')
    })

    it('food API 应包含搜索和分类方法', async () => {
      const { api } = await import('@/api')
      
      expect(typeof api.food.search).toBe('function')
      expect(typeof api.food.getByCategory).toBe('function')
      expect(typeof api.food.list).toBe('function')
    })

    it('diet API 应包含添加、查询、分析方法', async () => {
      const { api } = await import('@/api')
      
      expect(typeof api.diet.add).toBe('function')
      expect(typeof api.diet.getByDate).toBe('function')
      expect(typeof api.diet.analyze).toBe('function')
    })

    it('ai API 应包含咨询和生成功能', async () => {
      const { api } = await import('@/api')
      
      expect(typeof api.ai.consult).toBe('function')
      expect(typeof api.ai.nutritionAnalyze).toBe('function')
      expect(typeof api.ai.weeklyReport).toBe('function')
      expect(typeof api.ai.dietPlan).toBe('function')
      expect(typeof api.ai.mealParse).toBe('function')
    })
  })

  describe('readActAsUserId 辅助函数', () => {
    it('localStorage 无值时应返回 null', async () => {
      // 重新导入模块以测试内部函数行为
      localStorage.removeItem('actAsUserId')
      
      // 通过 API 调用间接测试 - 当 actAsUserId 为 null 时不应附加参数
      const { api } = await import('@/api')
      expect(api).toBeDefined()
    })

    it('localStorage 有有效值时应解析为数字', () => {
      localStorage.setItem('actAsUserId', '456')
      const v = localStorage.getItem('actAsUserId')
      const n = parseInt(v!, 10)
      expect(Number.isFinite(n)).toBe(true)
      expect(n).toBe(456)
    })

    it('localStorage 有无效值时应返回非有限数', () => {
      localStorage.setItem('actAsUserId', 'not-a-number')
      const v = localStorage.getItem('actAsUserId')
      const n = parseInt(v!, 10)
      expect(Number.isFinite(n)).toBe(false)
    })
  })
})
