// 管理员"先预览后发布"流程快照 · 前后端接口封装
// 注意：axios 响应拦截器（api/index.ts）已把 {code,message,data} 剥离为 data，
// 因此这里不要再 .then(r => r.data)，直接返回 Promise<业务数据>。
import { instance } from '@/api/index'

export interface SnapshotPayload {
  id?: number
  sessionId: string
  userId?: number
  funcType: 'article' | 'recipe' | 'training' | 'consult' | 'weeklyReport' | 'dietPlan' | 'nutrition'
  mode?: 'normal' | 'high_performance' | 'offline'
  title?: string
  summary?: string
  note?: string
  payload: any // 权威组件所需完整 JSON
}

export interface SnapshotEntity {
  id: number
  sessionId: string
  userId?: number
  funcType: string
  mode: string
  title?: string
  summary?: string
  published: boolean
  publishedAt?: string
  targetId?: number
  note?: string
  createdAt?: string
  updatedAt?: string
  payload?: any
}

/** 管理员保存一份 AI 产出快照 */
export function saveSnapshot(data: SnapshotPayload) {
  return instance.post<any, SnapshotEntity>('/admin/preview/snapshot', data)
}

/** 管理员读取快照详情 */
export function getSnapshot(id: number) {
  return instance.get<any, SnapshotEntity>(`/admin/preview/snapshot/${id}`)
}

/** 管理员生成匿名预览一次性 token */
export function generatePreviewToken(id: number) {
  return instance.post<any, { id: number; previewToken: string; expireAt: string; url: string }>(
    `/admin/preview/snapshot/${id}/generateToken`
  )
}

/** 某个 session 下的快照列表（新→旧） */
export function listSnapshots(sessionId: string) {
  return instance.get<any, SnapshotEntity[]>('/admin/preview/list', { params: { sessionId } })
}

/** 管理员点"喜欢+发布"：
 *  - article → 真落 articles 主表（复用文章管理 createArticle）
 *  - 其他 → 只打 published=1 快照标记
 */
export function publishSnapshot(id: number) {
  return instance.post<any, any>(`/admin/preview/snapshot/${id}/publish`)
}

/** 匿名（一次性 tok）打开快照。用于 iframe / 新标签页 / PreviewerWrapper 路由 */
export function openSnapshot(id: number, tok: string) {
  return instance.get<any, SnapshotEntity>(`/preview/open/${id}`, { params: { tok } })
}

/** 匿名健康检查（调试用） */
export function previewPing() {
  return instance.get<any, any>('/preview/ping')
}

// ============== 新增：AI 生成"后端实时流水线"步骤追踪（管理员流程演示专用）==============

export interface PipelineStep {
  index: number
  title: string
  subtitle?: string
  status: 'pending' | 'running' | 'done' | 'error'
  startedAt?: string
  finishedAt?: string
  durationMs?: number
  input?: any
  output?: any
  note?: string
  last?: boolean
  extra?: any
}

export interface PipelineStartResult {
  traceId: string
  funcType: string
  sessionId: string
  mode: string
  createdAt: string
  totalSteps: number
  done: boolean
  steps: PipelineStep[]
}

export interface PipelineTraceResult {
  traceId: string
  funcType: string
  sessionId: string
  mode: string
  createdAt: string
  totalSteps: number
  done: boolean
  error?: string
  finalSnapshotId?: string
  steps: PipelineStep[]
}

export interface PipelineListEntry {
  traceId: string
  funcType: string
  sessionId: string
  createdAt: string
  totalSteps: number
  done: boolean
  error?: string
  finalSnapshotId?: string
}

/** 开启一次"真实 AI 执行"后端流水线，返回 traceId 用于轮询步骤。 */
export function startPipeline(data: SnapshotPayload) {
  return instance.post<any, PipelineStartResult>('/admin/preview/pipeline/start', data)
}

/** 轮询当前 trace 的最新步骤状态（建议 250–500ms 一次）。 */
export function pollPipelineTrace(traceId: string) {
  return instance.get<any, PipelineTraceResult>(`/admin/preview/pipeline/trace/${traceId}`)
}

/** 列所有或按 sessionId 过滤的 trace。 */
export function listPipelineTraces(sessionId?: string) {
  return instance.get<any, PipelineListEntry[]>('/admin/preview/pipeline/list', { params: sessionId ? { sessionId } : {} })
}
