/**
 * API 领域类型定义（与后端 DTO 字段对齐）。
 * 说明：axios 响应拦截器会剥离 {code,message,data} 包装，故各 API 方法实际返回 data 载荷本身，
 * 类型声明直接以载荷为准。
 */

/** 后端统一响应包装（拦截器已剥离，此处仅作参考/泛型约束） */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 登录/注册返回 */
export interface LoginResult {
  access_token: string
  /** 后端恒返回 bearer；部分测试 mock 省略，故设为可选 */
  token_type?: string
  user_id: number
  username: string
  crowd_type?: string
  role?: string
  avatar?: string
  height?: number
  weight?: number
  age?: number
  gender?: string
}

/** 用户资料（/profile/info） */
export interface UserInfo {
  userId: number
  username: string
  gender?: string
  height?: number
  weight?: number
  age?: number
  crowdType?: string
  role?: string
  createdAt?: string
  allergicFoods?: string
  dietaryRestrictions?: string
  tastePreference?: string
  elderlyMode?: boolean
  bmr?: number
  bmi?: number
  bmiStatus?: string
  avatar?: string
}

/** 食物条目（food 表，100g 营养素） */
export interface FoodItem {
  foodId: number
  foodName: string
  foodCategory: string
  calorie: number
  protein: number
  fat: number
  carb: number
  dietFiber?: number
  calcium?: number
  dha?: number
  folicAcid?: number
  giValue?: number | null
  priority?: number
  status?: string
  showGi?: number
  showDha?: number
  showFolicAcid?: number
}

/** 饮食记录项（一餐内一种食物） */
export interface DietMealItem {
  foodId?: number
  foodName?: string
  foodCategory?: string
  eatWeight?: number
  calorie?: number
  protein?: number
  fat?: number
  carb?: number
  dietFiber?: number
  calcium?: number
  dha?: number
  folicAcid?: number
  giValue?: number | null
}

/** 一餐 */
export interface DietMeal {
  mealId?: number
  mealType?: string
  items?: DietMealItem[]
}

/** 营养分析结果（/diet/analyze/{date}） */
export interface DietAnalysis {
  user?: {
    weight?: number
    height?: number
    age?: number
    gender?: string
    crowdType?: string
    bmr?: number
    intakeBmrRatio?: number
    recommendCalorieMin?: number
    recommendCalorieMax?: number
  }
  total?: Record<string, number>
  recommendations?: Record<string, number | number[]>
  status?: Record<string, string>
  warnings?: Record<string, string>
  meals?: DietMeal[]
}

/** 收藏菜谱记录（saved_recipe 表） */
export interface SavedRecipeItem {
  id: number
  userId: number
  title: string
  ingredients?: string
  steps?: string
  nutritionSummary?: string
  personaTag?: string
  source?: string
  originalRecipeId?: number | null
  createdAt?: string
}

/** 系统菜谱（recipes 表） */
export interface RecipeItem {
  recipeId: number
  recipeName: string
  description?: string
  coverImageUrl?: string
  calories?: number
  protein?: number
  fat?: number
  carbs?: number
  fiber?: number
  tags?: string
  source?: string
  createdBy?: number
  createdAt?: string
}

/** 科普文章 */
export interface ArticleItem {
  id: number
  title: string
  topic?: string
  topicGroupId?: string
  lengthType?: string
  content?: string
  contentShort?: string
  contentMedium?: string
  contentLong?: string
  summary?: string
  tags?: string
  category?: string
  audience?: string
  wordCount?: number
  viewsCount?: number
  likesCount?: number
  createdAt?: string
  status?: string
  source?: string
  qualityScore?: number
  /** 兼容前后端别名，未枚举字段允许透传 */
  [key: string]: any
}

/** 亲属关系（监护人/被监护人） */
export interface WardRelation {
  relationId?: number
  guardianId?: number
  wardId?: number
  status?: string
  guardianUsername?: string
  wardUsername?: string
}

/** 身体指标历史 */
export interface MetricsRecord {
  id?: number
  userId?: number
  recordDate?: string
  height?: number
  weight?: number
  bmi?: number
  bmr?: number
  [key: string]: any
}

/** 运动记录 */
export interface ExerciseRecord {
  id?: number
  exerciseType?: string
  durationMin?: number
  note?: string
  recordDate?: string
  calories?: number
  [key: string]: any
}

/** AI 咨询/建议结果（含 thinking、exercise、diet 等子字段，字段名以各 agent 实际返回为准） */
export interface AiResult {
  thinking?: string
  answer?: string
  exercise?: any
  diet?: any
  article?: any
  [key: string]: any
}
