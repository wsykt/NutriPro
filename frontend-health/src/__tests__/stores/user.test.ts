/**
 * User Store 单元测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'

// Mock API 模块
vi.mock('@/api', () => ({
  api: {
    auth: {
      login: vi.fn(),
      register: vi.fn()
    },
    profile: {
      getInfo: vi.fn()
    },
    relation: {
      myWards: vi.fn()
    }
  }
}))

describe('User Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该初始化为未登录状态', () => {
      const store = useUserStore()
      expect(store.user).toBeNull()
      expect(store.isLogin).toBe(false)
      expect(store.isLoggedIn).toBe(false)
      expect(store.isAdmin).toBe(false)
    })

    it('应该从 localStorage 读取 actAsUserId', () => {
      localStorage.setItem('actAsUserId', '123')
      setActivePinia(createPinia())
      const store = useUserStore()
      expect(store.actAsUserId).toBe(123)
    })
  })

  describe('login action', () => {
    it('登录成功应设置用户信息', async () => {
      const { api } = await import('@/api')
      vi.mocked(api.auth.login).mockResolvedValue({
        access_token: 'test-token',
        user_id: 1,
        username: 'testuser',
        role: 'user',
        crowd_type: '普通人'
      })
      vi.mocked(api.relation.myWards).mockResolvedValue([])

      const store = useUserStore()
      const result = await store.login('testuser', 'password')

      expect(result.success).toBe(true)
      expect(store.user).not.toBeNull()
      expect(store.user?.username).toBe('testuser')
      expect(store.user?.token).toBe('test-token')
      expect(localStorage.getItem('user_token')).toBe('test-token')
    })

    it('登录失败应返回错误信息', async () => {
      const { api } = await import('@/api')
      vi.mocked(api.auth.login).mockRejectedValue(new Error('网络错误'))

      const store = useUserStore()
      const result = await store.login('testuser', 'wrong')

      expect(result.success).toBe(false)
      expect(result.message).toContain('网络错误')
    })

    it('无 token 响应应返回失败', async () => {
      const { api } = await import('@/api')
      vi.mocked(api.auth.login).mockResolvedValue({})

      const store = useUserStore()
      const result = await store.login('testuser', 'password')

      expect(result.success).toBe(false)
    })
  })

  describe('logout action', () => {
    it('登出应清除所有状态', async () => {
      const { api } = await import('@/api')
      vi.mocked(api.auth.login).mockResolvedValue({
        access_token: 'test-token',
        user_id: 1,
        username: 'testuser'
      })
      vi.mocked(api.relation.myWards).mockResolvedValue([])

      const store = useUserStore()
      await store.login('testuser', 'password')
      
      expect(store.isLogin).toBe(true)
      
      store.logout()
      
      expect(store.user).toBeNull()
      expect(store.isLogin).toBe(false)
      expect(localStorage.getItem('user_token')).toBeNull()
    })
  })

  describe('setActAs action', () => {
    it('设置操作身份应更新 localStorage', () => {
      const store = useUserStore()
      
      store.setActAs(456)
      expect(store.actAsUserId).toBe(456)
      expect(localStorage.getItem('actAsUserId')).toBe('456')
      
      store.setActAs(null)
      expect(store.actAsUserId).toBeNull()
      expect(localStorage.getItem('actAsUserId')).toBeNull()
    })
  })

  describe('getters', () => {
    it('isAdmin 应正确判断管理员角色', () => {
      const store = useUserStore()
      store.user = { username: 'admin', token: 'x', role: 'admin' }
      expect(store.isAdmin).toBe(true)
      
      store.user = { username: 'user', token: 'x', role: 'user' }
      expect(store.isAdmin).toBe(false)
    })

    it('activeUserId 应返回当前操作的用户 ID', () => {
      const store = useUserStore()
      store.user = { username: 'test', token: 'x', user_id: 1 }
      
      // 未设置 actAs 时返回自己的 ID
      expect(store.activeUserId).toBe(1)
      
      // 设置 actAs 后返回被监护人 ID
      store.setActAs(999)
      expect(store.activeUserId).toBe(999)
    })

    it('activeUserLabel 应返回正确的显示名', () => {
      const store = useUserStore()
      store.user = { username: '张三', token: 'x', user_id: 1 }
      expect(store.activeUserLabel).toBe('张三')
      
      store.wards = [{ wardId: 999, wardUsername: '李四' }]
      store.setActAs(999)
      expect(store.activeUserLabel).toBe('替 李四 操作')
      
      store.setActAs(888)
      expect(store.activeUserLabel).toBe('替 #888 操作')
    })

    it('未登录时 activeUserLabel 应返回"未登录"', () => {
      const store = useUserStore()
      expect(store.activeUserLabel).toBe('未登录')
    })
  })
})
