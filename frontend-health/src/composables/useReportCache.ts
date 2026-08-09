/**
 * 图表数据缓存组合函数（阶段一 · 图表缓存）
 *
 * 三项能力：
 * 1. 防抖加载：切换报表周期（周/月）等高频操作时合并连续请求
 * 2. 前端缓存：按作用域 + 参数生成 key，会话内（sessionStorage）短 TTL 缓存
 * 3. 增量失效：跨天自动失效（key 内携带日期）；数据变更后调用 invalidateReportCache 主动失效
 *
 * 说明：
 * - 缓存以「当天日期 + 报表周期」为粒度，同日重复进入页面直接读缓存，避免重复请求
 * - TTL 兜底（默认 30 分钟），防止页面长时间挂起导致数据过旧
 */
import { ref, type Ref } from 'vue'

const CACHE_PREFIX = 'report_cache_'
const DEFAULT_TTL_MS = 30 * 60 * 1000 // 30 分钟

interface CacheEntry {
  data: unknown
  ts: number
}

/** 生成稳定缓存 key：scope|k1=v1|k2=v2 */
function buildCacheKey(scope: string, params: Record<string, unknown>): string {
  const parts = [CACHE_PREFIX + scope]
  for (const k of Object.keys(params).sort()) {
    parts.push(`${k}=${params[k]}`)
  }
  return parts.join('|')
}

function readCache(key: string, ttlMs: number): unknown | null {
  try {
    const raw = sessionStorage.getItem(key)
    if (!raw) return null
    const entry = JSON.parse(raw) as CacheEntry
    if (Date.now() - entry.ts > ttlMs) {
      sessionStorage.removeItem(key)
      return null
    }
    return entry.data
  } catch {
    // sessionStorage 不可用或解析失败时直接视为未命中
    return null
  }
}

function writeCache(key: string, data: unknown) {
  try {
    sessionStorage.setItem(key, JSON.stringify({ data, ts: Date.now() }))
  } catch {
    // 存储满/隐私模式下静默失败，不影响功能
  }
}

/** 清除某作用域下的全部缓存（数据变更后调用） */
export function invalidateReportCache(scope: string) {
  const prefix = CACHE_PREFIX + scope
  const toRemove: string[] = []
  for (let i = 0; i < sessionStorage.length; i++) {
    const k = sessionStorage.key(i)
    if (k && k.startsWith(prefix)) toRemove.push(k)
  }
  toRemove.forEach((k) => sessionStorage.removeItem(k))
}

export interface CacheLoaderOptions {
  /** 缓存 TTL 毫秒，默认 30 分钟 */
  ttlMs?: number
  /** 防抖毫秒数，默认 300；传 0 表示不防抖 */
  debounceMs?: number
}

export interface CacheLoaderResult<T> {
  /** 是否正在请求中 */
  loading: Ref<boolean>
  /** 带缓存与防抖的数据加载 */
  load: (params: Record<string, unknown>, loader: () => Promise<T>) => Promise<T | null>
  /** 清除本作用域缓存 */
  invalidate: () => void
}

/**
 * 创建作用域化的图表数据加载器
 * @param scope 缓存作用域（如 'health-report'），同类图表共用同一作用域以便整体失效
 */
export function useReportCache<T = unknown>(scope: string, options: CacheLoaderOptions = {}): CacheLoaderResult<T> {
  const ttlMs = options.ttlMs ?? DEFAULT_TTL_MS
  const debounceMs = options.debounceMs ?? 300
  const loading = ref(false)

  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  const load = (params: Record<string, unknown>, loader: () => Promise<T>): Promise<T | null> => {
    return new Promise((resolve) => {
      const doLoad = async () => {
        const key = buildCacheKey(scope, params)

        // ① 缓存命中直接返回
        const cached = readCache(key, ttlMs)
        if (cached !== null) {
          resolve(cached as T)
          return
        }

        // ② 未命中则真实请求并回写缓存
        loading.value = true
        try {
          const data = await loader()
          writeCache(key, data)
          resolve(data)
        } catch {
          resolve(null)
        } finally {
          loading.value = false
        }
      }

      // ③ 防抖：连续调用只执行最后一次
      if (debounceTimer) clearTimeout(debounceTimer)
      if (debounceMs > 0) {
        debounceTimer = setTimeout(doLoad, debounceMs)
      } else {
        doLoad()
      }
    })
  }

  const invalidate = () => invalidateReportCache(scope)

  return { loading, load, invalidate }
}
