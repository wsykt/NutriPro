/**
 * 本地存储统一入口
 *
 * 分两层：
 * 1. 缓存（带 TTL）：setCache / getCache / removeCache / clearAllCache
 * 2. 会话状态：token / 当前用户 ID / 替亲属操作（actAs）
 *
 * 会话状态收敛说明：早期代码把 token 同时写入 user_token 与 token 两个键，
 * 现已统一为单一事实源 user_token（setToken 只写它）；getToken 兼容读取旧 token 键，
 * 以便未刷新页面（旧存储）的用户平滑过渡。
 */

// ============ 缓存（带 TTL） ============

const PREFIX = 'health_'

interface CacheItem<T> {
  data: T
  expiresAt: number
}

export function setCache(key: string, value: any, ttlMinutes: number = 30): void {
  try {
    const item: CacheItem<any> = {
      data: value,
      expiresAt: Date.now() + ttlMinutes * 60 * 1000
    }
    localStorage.setItem(PREFIX + key, JSON.stringify(item))
  } catch {
    // 存储空间不足时静默失败
  }
}

export function getCache<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(PREFIX + key)
    if (!raw) return null
    const item: CacheItem<T> = JSON.parse(raw)
    if (Date.now() > item.expiresAt) {
      localStorage.removeItem(PREFIX + key)
      return null
    }
    return item.data
  } catch {
    return null
  }
}

export function removeCache(key: string): void {
  try {
    localStorage.removeItem(PREFIX + key)
  } catch { /* ignore */ }
}

export function clearAllCache(): void {
  try {
    const keysToRemove: string[] = []
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i)
      if (k && k.startsWith(PREFIX)) {
        keysToRemove.push(k)
      }
    }
    keysToRemove.forEach(k => localStorage.removeItem(k))
  } catch { /* ignore */ }
}

// ============ 会话状态 ============

const TOKEN_KEY = 'user_token'
const LEGACY_TOKEN_KEY = 'token'
const CURRENT_USER_ID_KEY = 'currentUserId'
const ACT_AS_USER_ID_KEY = 'actAsUserId'

function readNumberKey(key: string): number | null {
  try {
    const v = localStorage.getItem(key)
    if (!v) return null
    const n = parseInt(v, 10)
    return Number.isFinite(n) ? n : null
  } catch {
    return null
  }
}

/** 读取登录令牌（优先 user_token，兼容历史 token 键） */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY) || localStorage.getItem(LEGACY_TOKEN_KEY)
}

/** 写入登录令牌（单一事实源：只写 user_token，不再双写） */
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

/** 当前登录用户 ID */
export function getCurrentUserId(): number | null {
  return readNumberKey(CURRENT_USER_ID_KEY)
}

export function setCurrentUserId(id: number | null): void {
  if (id == null) {
    localStorage.removeItem(CURRENT_USER_ID_KEY)
  } else {
    localStorage.setItem(CURRENT_USER_ID_KEY, String(id))
  }
}

/** 当前"替谁操作"的 userId（null = 操作自己） */
export function getActAsUserId(): number | null {
  return readNumberKey(ACT_AS_USER_ID_KEY)
}

export function setActAsUserId(id: number | null): void {
  if (id == null) {
    localStorage.removeItem(ACT_AS_USER_ID_KEY)
  } else {
    localStorage.setItem(ACT_AS_USER_ID_KEY, String(id))
  }
}

/**
 * 解析最终生效的"目标用户 ID"：
 * 仅在处于替亲属操作状态（actAs 存在且不同于当前用户）时返回该 ID，否则返回 null。
 * 供请求拦截器与 SSE 流式调用共用，避免两处重复解析逻辑。
 */
export function resolveActAsUserId(): number | null {
  const actAs = getActAsUserId()
  const current = getCurrentUserId()
  if (actAs != null && current != null && actAs !== current) {
    return actAs
  }
  return null
}

/** 清除全部会话状态（登出 / 401 时调用） */
export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(LEGACY_TOKEN_KEY)
  localStorage.removeItem(CURRENT_USER_ID_KEY)
  localStorage.removeItem(ACT_AS_USER_ID_KEY)
}
