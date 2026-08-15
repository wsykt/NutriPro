import { describe, it, expect } from 'vitest'
import {
  getToken, setToken, clearSession,
  getCurrentUserId, setCurrentUserId,
  getActAsUserId, setActAsUserId, resolveActAsUserId,
  setCache, getCache
} from '@/utils/storage'

describe('token 单一事实源', () => {
  it('setToken 只写 user_token（不再双写 token 键）', () => {
    setToken('abc')
    expect(localStorage.getItem('user_token')).toBe('abc')
    expect(localStorage.getItem('token')).toBeNull()
    expect(getToken()).toBe('abc')
  })

  it('getToken 兼容历史 token 键（未刷新旧数据平滑过渡）', () => {
    localStorage.setItem('token', 'legacy-token')
    expect(getToken()).toBe('legacy-token')
  })
})

describe('当前用户 / 替亲属操作', () => {
  it('setCurrentUserId / getCurrentUserId 往返', () => {
    setCurrentUserId(7)
    expect(getCurrentUserId()).toBe(7)
  })

  it('setActAsUserId null 时移除', () => {
    setActAsUserId(5)
    expect(getActAsUserId()).toBe(5)
    setActAsUserId(null)
    expect(getActAsUserId()).toBeNull()
  })

  it('resolveActAsUserId 仅在替他人操作时返回', () => {
    setCurrentUserId(1)
    setActAsUserId(1) // 与自己相同 → 视为操作自己
    expect(resolveActAsUserId()).toBeNull()

    setActAsUserId(2) // 替亲属 → 返回目标 ID
    expect(resolveActAsUserId()).toBe(2)

    setActAsUserId(null)
    expect(resolveActAsUserId()).toBeNull()
  })
})

describe('clearSession', () => {
  it('清除全部会话键（含历史 token 键）', () => {
    setToken('a')
    setCurrentUserId(1)
    setActAsUserId(2)
    localStorage.setItem('token', 'legacy')
    clearSession()
    expect(getToken()).toBeNull()
    expect(getCurrentUserId()).toBeNull()
    expect(getActAsUserId()).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
  })
})

describe('缓存功能保持不变', () => {
  it('setCache / getCache 在 TTL 内可用', () => {
    setCache('demo', { a: 1 }, 30)
    expect(getCache('demo')).toEqual({ a: 1 })
  })

  it('getCache 未知键返回 null', () => {
    expect(getCache('not-exist')).toBeNull()
  })
})
