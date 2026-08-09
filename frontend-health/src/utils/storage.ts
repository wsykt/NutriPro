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
