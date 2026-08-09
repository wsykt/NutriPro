import { reactive, computed, type Ref } from 'vue'

/**
 * 食谱食材替换 + 营养计算逻辑
 *
 * 接收一个指向"当前查看的食谱"的 ref，返回替换状态、营养计算和方法。
 * 调用方负责在切换食谱时调用 reset（通过 reassign recipe.value 或显式调用）。
 */
export function useRecipeSubstitution(recipe: Ref<any>) {
  /** 已应用的替换：原始食材名 → 替代品（字符串或带营养的对象） */
  const appliedSubstitutions = reactive<Record<string, any>>({})

  /** 是否有替换已应用 */
  const hasSubstitutions = computed(() => Object.keys(appliedSubstitutions).length > 0)

  /** 替换后的食材列表（原始食材 + 替换后结果） */
  const modifiedIngredients = computed(() => {
    const base = recipe.value?.ingredients || []
    if (!hasSubstitutions.value) return base
    return base.map((ing: any) => {
      const name = ing.ingredientName || ing.ingredient_name || ing.name
      const sub = appliedSubstitutions[name]
      if (!sub) return ing
      return {
        ...ing,
        ingredientName: sub.name || sub,
        originalName: name,
        isSubstituted: true
      }
    })
  })

  /** 食材营养总和（原始值，用于对比基线） */
  const originalNutritionSum = computed(() => {
    const r = recipe.value
    if (!r) return { calories: 0, protein: 0, fat: 0, carbs: 0 }
    let cal = 0, pro = 0, fat = 0, carb = 0
    for (const n of (r.ingredientNutrition || [])) {
      cal += (n.calories || 0)
      pro += (n.protein || 0)
      fat += (n.fat || 0)
      carb += (n.carbs || 0)
    }
    return {
      calories: Math.round(cal),
      protein: Math.round(pro * 10) / 10,
      fat: Math.round(fat * 10) / 10,
      carbs: Math.round(carb * 10) / 10
    }
  })

  /** 估算整份菜品的总重量（g） */
  const estimatedTotalWeight = computed(() => {
    const r = recipe.value
    if (!r?.ingredients) return 0
    let total = 0
    for (const ing of r.ingredients) {
      const amt = parseFloat(ing.amount) || 0
      const unit = (ing.unit || '').toLowerCase()
      if (unit === 'g' || unit === 'ml') total += amt
    }
    return total || 1 // 避免除零
  })

  /** 原始营养每 100g 值 */
  const originalPer100g = computed(() => {
    const total = originalNutritionSum.value
    const w = estimatedTotalWeight.value
    return {
      calories: Math.round(total.calories / w * 100),
      protein: Math.round(total.protein / w * 100 * 10) / 10,
      fat: Math.round(total.fat / w * 100 * 10) / 10,
      carbs: Math.round(total.carbs / w * 100 * 10) / 10
    }
  })

  /** 替换后营养每 100g 值 */
  const modifiedPer100g = computed(() => {
    const total = modifiedNutrition.value
    const w = estimatedTotalWeight.value
    return {
      calories: Math.round(total.calories / w * 100),
      protein: Math.round(total.protein / w * 100 * 10) / 10,
      fat: Math.round(total.fat / w * 100 * 10) / 10,
      carbs: Math.round(total.carbs / w * 100 * 10) / 10
    }
  })

  /** 替换后的营养总值（以 ingredientNutrition 实际食材数据为基数计算） */
  const modifiedNutrition = computed(() => {
    const r = recipe.value
    if (!r || !hasSubstitutions.value) {
      return { calories: 0, protein: 0, fat: 0, carbs: 0 }
    }

    // 以 ingredientNutrition 总和为基数（不依赖 recipe.calories，那可能是份数估值而非实际食材和）
    let cal = 0, pro = 0, fat = 0, carb = 0

    // 建立食材名 → 营养值映射
    const nutritionMap = new Map<string, any>()
    for (const n of (r.ingredientNutrition || [])) {
      nutritionMap.set(n.ingredientName, n)
      cal += (n.calories || 0)
      pro += (n.protein || 0)
      fat += (n.fat || 0)
      carb += (n.carbs || 0)
    }

    // 逐个替换：减去原食材营养，加上替代品营养
    for (const [origName, sub] of Object.entries(appliedSubstitutions)) {
      const origNut = nutritionMap.get(origName)
      if (origNut) {
        cal -= (origNut.calories || 0)
        pro -= (origNut.protein || 0)
        fat -= (origNut.fat || 0)
        carb -= (origNut.carbs || 0)
      }

      // 替代品营养：per 100g × 用量
      const amount = origNut?.amount || 0
      const unit = origNut?.unit || 'g'
      const ratio = (unit === 'g' && amount > 0) ? amount / 100 : 1

      const subObj = typeof sub === 'object' ? sub : { name: sub }
      if (subObj.calories != null) cal += subObj.calories * ratio
      if (subObj.protein != null) pro += subObj.protein * ratio
      if (subObj.fat != null) fat += subObj.fat * ratio
      if (subObj.carbs != null) carb += subObj.carbs * ratio
    }

    return {
      calories: Math.round(cal),
      protein: Math.round(pro * 10) / 10,
      fat: Math.round(fat * 10) / 10,
      carbs: Math.round(carb * 10) / 10
    }
  })

  /** 判断食材是否被标记为"不适合" */
  function isIngredientNotSuitable(ing: any): boolean {
    const name = ing.ingredientName || ing.ingredient_name || ing.name
    if (!name || !recipe.value?.substitutions) return false
    return recipe.value.substitutions.some((s: any) => {
      const subName = s.ingredient?.ingredientName || s.ingredient?.ingredient_name || s.ingredientName
      return subName === name && s.isNotSuitable
    })
  }

  /** 营养变化预估值（合并后端 + 已选替换） */
  const nutritionChangeValue = computed(() => {
    const base = recipe.value?.nutritionChange || { calories: 0, fat: 0, protein: 0 }
    return {
      calories: base.calories || 0,
      fat: base.fat || 0,
      protein: base.protein || 0
    }
  })

  function applyIngredientSub(original: string, replaced: string) {
    // 尝试从 foodDbSubstitutions 查找该替代品的营养数据
    let altData: any = { name: replaced }
    if (recipe.value?.foodDbSubstitutions) {
      const dbSub = recipe.value.foodDbSubstitutions.find((s: any) => s.ingredientName === original)
      if (dbSub?.alternatives) {
        const matched = dbSub.alternatives.find((a: any) => a.name === replaced || a.name?.includes(replaced))
        if (matched) {
          altData = { name: matched.name, calories: matched.calories, protein: matched.protein, fat: matched.fat }
        }
      }
    }
    // 后备：尝试从食物数据库直接查找替代品的营养数据
    if (altData.calories == null && recipe.value?.ingredientDBInfo) {
      const info = recipe.value.ingredientDBInfo.find((i: any) =>
        i.name?.includes(replaced) || replaced.includes(i.name || '')
      )
      if (info) {
        altData = { name: info.name, calories: info.calories, protein: info.protein, fat: info.fat, carbs: info.carbs }
      }
    }
    // 仍无营养数据 → 保留原食材营养计算（使替换前后营养不变，比错误归零更合理）
    if (altData.calories == null) {
      const origNut = (recipe.value?.ingredientNutrition || []).find((n: any) => n.ingredientName === original)
      if (origNut) {
        altData = { name: replaced, calories: origNut.calories, protein: origNut.protein, fat: origNut.fat, carbs: origNut.carbs }
      }
    }
    appliedSubstitutions[original] = altData
  }

  function applyNutritionSub(original: string, replaced: any) {
    // replaced 来自 foodDbSubstitutions.alternatives，已含 name/calories/protein/fat
    appliedSubstitutions[original] = {
      name: replaced.name,
      calories: replaced.calories,
      protein: replaced.protein,
      fat: replaced.fat,
      carbs: replaced.carbs || 0
    }
  }

  function removeSubstitution(original: string) {
    delete appliedSubstitutions[original]
  }

  /** 重置所有已应用的替换 */
  function resetSubstitutions() {
    Object.keys(appliedSubstitutions).forEach(k => delete appliedSubstitutions[k])
  }

  return {
    appliedSubstitutions,
    hasSubstitutions,
    modifiedIngredients,
    originalNutritionSum,
    estimatedTotalWeight,
    originalPer100g,
    modifiedPer100g,
    modifiedNutrition,
    nutritionChangeValue,
    isIngredientNotSuitable,
    applyIngredientSub,
    applyNutritionSub,
    removeSubstitution,
    resetSubstitutions
  }
}
