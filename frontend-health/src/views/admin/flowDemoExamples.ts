// 管理员"流程演示"页 · 空骨架。
// 不包含任何写死的示例数据：所有渲染内容都来自后端真实 AI 流水线返回的 payload。
// 前端只提供最小骨架（空对象），由后端 buildRealPayload 用真实生成内容填充，
// 保证右栏 1:1 预览展示的是真实 AI 结果，而非模板数据。

export type FuncType = 'article' | 'recipe' | 'training' | 'consult' | 'weeklyReport' | 'dietPlan' | 'nutrition'

/**
 * 空骨架对象：仅用于给后端流水线一个初始载体。
 * 后端会在执行完成后用真实 AI 结果（结构化字段）覆盖填充。
 */
export const EXAMPLE_PAYLOADS: Record<FuncType, any> = {
  article: {},
  recipe: {},
  training: {},
  consult: {},
  weeklyReport: {},
  dietPlan: {},
  nutrition: {},
}
