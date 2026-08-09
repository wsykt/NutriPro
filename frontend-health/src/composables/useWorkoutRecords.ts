import { ref, computed } from 'vue'
import { setCache, getCache } from '@/utils/storage'

/**
 * 训练记录共享存储 —— MuscleChart（运动管理）保存记录，
 * TrainingPlan（训练计划）读取并展示，实现两个页面间的数据流通。
 *
 * 存储位置：localStorage（key: health_workout_records）
 */

export type Intensity = 'low' | 'medium' | 'high'

export interface WorkoutRecord {
  id: string
  exerciseId: number
  exerciseName: string
  muscleGroup: string
  category: string
  date: string            // YYYY-MM-DD
  duration: number        // 分钟
  sets: number
  reps: number            // 每组次数
  weight: number          // kg，0 表示自重
  intensity: Intensity
  calories: number
  createdAt: string       // ISO 时间戳
}

const STORAGE_KEY = 'workout_records'

const PREFIX = 'health_'
const FULL_KEY = PREFIX + STORAGE_KEY

// 模块级单例，跨组件共享
const records = ref<WorkoutRecord[]>([])

let loaded = false
function load() {
  if (loaded) return
  loaded = true
  const cached = getCache<WorkoutRecord[]>(STORAGE_KEY)
  if (cached && Array.isArray(cached)) records.value = cached
}

function persist() {
  setCache(STORAGE_KEY, records.value, 60 * 24) // 训练记录缓存24小时
}

// 事件通知：跨页面同步时使用
const STORAGE_EVENT = 'workout-records-changed'

function notify() {
  window.dispatchEvent(new CustomEvent(STORAGE_EVENT))
}

export function useWorkoutRecords() {
  load()

  // 监听其他页面写入
  if (typeof window !== 'undefined') {
    window.addEventListener('storage', (e) => {
      if (e.key === FULL_KEY) {
        try {
          const arr = e.newValue ? JSON.parse(e.newValue) : null
          if (arr && Array.isArray(arr.data)) records.value = arr.data
          else if (Array.isArray(arr)) records.value = arr
        } catch { /* ignore */ }
      }
    })
  }

  const all = computed(() =>
    [...records.value].sort((a, b) => b.date.localeCompare(a.date))
  )

  function add(r: Omit<WorkoutRecord, 'id' | 'createdAt'>): WorkoutRecord {
    const rec: WorkoutRecord = {
      ...r,
      id: `wk-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      createdAt: new Date().toISOString()
    }
    records.value = [rec, ...records.value]
    persist()
    notify()
    return rec
  }

  function remove(id: string) {
    records.value = records.value.filter(r => r.id !== id)
    persist()
    notify()
  }

  function clear() {
    records.value = []
    persist()
    notify()
  }

  /** 获取最近 N 天的训练记录 */
  function recentDays(days: number): WorkoutRecord[] {
    const now = new Date()
    const start = new Date(now)
    start.setDate(now.getDate() - days + 1)
    start.setHours(0, 0, 0, 0)
    return records.value.filter(r => new Date(r.date) >= start)
  }

  /** 计算消耗热量 */
  function calcCalories(met: number, weightKg: number, durationMin: number): number {
    return Math.round(met * weightKg * (durationMin / 60))
  }

  /** 生成近 7 日训练数据快照文本（发给 AI） */
  function buildSnapshotText(weightKg: number): string {
    const recent = recentDays(7)
    if (recent.length === 0) return '近 7 日无训练记录。'

    const totalCal = recent.reduce((s, r) => s + r.calories, 0)
    const totalMin = recent.reduce((s, r) => s + r.duration, 0)
    const totalSets = recent.reduce((s, r) => s + r.sets, 0)

    // 按部位汇总
    const byGroup: Record<string, { count: number; exercises: Set<string> }> = {}
    recent.forEach(r => {
      const g = r.category || r.muscleGroup || '其他'
      if (!byGroup[g]) byGroup[g] = { count: 0, exercises: new Set() }
      byGroup[g].count++
      byGroup[g].exercises.add(r.exerciseName)
    })

    // 按日期汇总
    const byDate: Record<string, WorkoutRecord[]> = {}
    recent.forEach(r => {
      if (!byDate[r.date]) byDate[r.date] = []
      byDate[r.date].push(r)
    })

    const dateLines = Object.entries(byDate)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([date, list]) => {
        const items = list.map(r =>
          `${r.exerciseName}(${r.sets}组×${r.reps}次${r.weight > 0 ? `@${r.weight}kg` : '自重'},${r.duration}分钟)`
        ).join('、')
        return `  ${date}: ${items}`
      }).join('\n')

    const groupLines = Object.entries(byGroup)
      .map(([g, info]) => `${g}(${info.count}次: ${Array.from(info.exercises).join('/')})`)
      .join('、')

    return `【近 7 日训练数据快照】
- 训练次数：${recent.length} 次
- 总时长：${totalMin} 分钟
- 总组数：${totalSets} 组
- 估算消耗：${totalCal} kcal
- 训练部位分布：${groupLines}
- 体重：${weightKg} kg
- 明细：
${dateLines}`
  }

  return {
    records: all,
    add,
    remove,
    clear,
    recentDays,
    calcCalories,
    buildSnapshotText
  }
}
