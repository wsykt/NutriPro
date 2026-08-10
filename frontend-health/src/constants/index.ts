/**
 * 项目共享常量
 * 集中管理各页面重复定义的业务常量，避免多份拷贝
 */

// ======================== 人群选项 ========================

/** 注册/档案页人群选择 */
export const CROWD_OPTIONS = [
  { value: '普通人', label: '普通人' },
  { value: '青少年', label: '青少年' },
  { value: '老年', label: '老年人' },
  { value: '孕妇', label: '孕妇' },
  { value: '健身', label: '健身人群' },
  { value: '糖尿病', label: '糖尿病患者' },
] as const

/** 后端 crowdType → 前端展示标签 */
export const CROWD_LABELS: Record<string, string> = {
  '普通人': '普通人群',
  '健身': '健身人群',
  '老年': '老年人',
  '孕妇': '孕妇',
  '青少年': '青少年',
  '糖尿病': '糖尿病患者',
}

/** 后端 crowdType → 适配的文章受众标签数组 */
export const CROWD_TO_AUDIENCE: Record<string, string[]> = {
  '普通人': ['普通人群'],
  '健身': ['健身人群'],
  '老年': ['老年人'],
  '孕妇': ['孕妇'],
  '青少年': ['青少年'],
  '糖尿病': ['糖尿病患者'],
}

// ======================== 食物分类 ========================

/** 完整食物分类列表（11 项） */
export const FOOD_CATEGORIES = [
  '主食',
  '肉蛋类',
  '奶制品',
  '蔬菜',
  '水果',
  '豆制品',
  '坚果',
  '油脂',
  '饮料',
  '调味品',
  '其他',
] as const

/** 饮食输入页排序顺序 */
export const FOOD_CATEGORY_ORDER = [
  '主食',
  '肉蛋类',
  '水产',
  '蔬菜',
  '水果',
  '豆制品',
  '奶类',
  '油脂类',
] as const

// ======================== 文章受众筛选 ========================

export const ARTICLE_AUDIENCE_FILTERS = [
  { key: '普通人群', label: '普通人群' },
  { key: '健身人群', label: '健身人群' },
  { key: '青少年', label: '青少年' },
  { key: '老年人', label: '老年人' },
  { key: '孕妇', label: '孕妇' },
  { key: '糖尿病患者', label: '糖尿病患者' },
] as const

// ======================== 食谱标签 ========================

export const RECIPE_TAGS = [
  '孕妇',
  '糖尿病',
  '老年人',
  '青少年',
  '减脂',
  '健身',
  '低GI',
  '高蛋白',
  '均衡',
] as const

export const RECIPE_PERSONA_TAGS = [
  '普通用户',
  '孕妇',
  '糖尿病患者',
  '老年人',
  '青少年',
  '健身人士',
  '减脂人群',
] as const

// ======================== 肌肉群 ========================

export const MUSCLE_GROUPS = [
  '胸部',
  '背部',
  '肩部',
  '手臂',
  '腹部',
  '臀部',
  '大腿',
  '小腿',
] as const
