<template>
  <div v-if="modelValue">
    <Teleport to="body">
      <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          class="absolute inset-0 bg-black/35 backdrop-blur-[3px] mask-layer transition-opacity duration-200"
          @click="emit('update:modelValue', false)"
        ></div>
        <div
          class="relative z-10 bg-white rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-auto shadow-xl dialog-fade scrollbar-hide"
          style="transform: translateZ(0);"
          @click.stop
        >
          <div class="p-8">
            <div class="flex items-center justify-between mb-6">
              <h3 class="text-xl font-bold text-morandi-text">{{ localRecipe?.name }}</h3>
              <button
                @click="emit('update:modelValue', false)"
                class="w-10 h-10 flex items-center justify-center rounded-full hover:bg-morandi-soft text-morandi-lightText hover:text-morandi-text transition-colors text-lg"
              >
                ✕
              </button>
            </div>
            <p class="text-morandi-lightText mb-6">{{ localRecipe?.description }}</p>
            <!-- 营养卡片：无替换显示每100g值，有替换显示总值+每100g值 -->
            <div class="mb-2">
              <div class="flex items-center justify-between text-xs text-morandi-lightText mb-2">
                <span v-if="!hasSubstitutions">每100g 营养值</span>
                <span v-else>替换后营养（总值 / 每100g）</span>
                <span class="text-gray-400">≈{{ estimatedTotalWeight }}g/份</span>
              </div>
              <div class="grid grid-cols-4 gap-4 p-5 rounded-xl bg-morandi-soft/30">
                <!-- 热量 -->
                <div class="text-center">
                  <template v-if="hasSubstitutions">
                    <div class="text-lg font-bold" :class="modifiedNutrition.calories < originalNutritionSum.calories ? 'text-green-600' : 'text-red-600'">
                      {{ modifiedNutrition.calories }} kcal
                    </div>
                    <div class="text-xs text-gray-400">每100g: {{ modifiedPer100g.calories }} kcal</div>
                  </template>
                  <template v-else>
                    <div class="text-2xl font-bold text-morandi-accent">{{ localRecipe?.calories }}</div>
                    <div class="text-xs text-morandi-lightText">热量 (kcal)</div>
                  </template>
                </div>
                <!-- 蛋白质 -->
                <div class="text-center">
                  <template v-if="hasSubstitutions">
                    <div class="text-lg font-bold" :class="modifiedNutrition.protein > originalNutritionSum.protein ? 'text-green-600' : 'text-morandi-text'">
                      {{ modifiedNutrition.protein }}g
                    </div>
                    <div class="text-xs text-gray-400">每100g: {{ modifiedPer100g.protein }}g</div>
                  </template>
                  <template v-else>
                    <div class="text-2xl font-bold text-morandi-text">{{ localRecipe?.protein }}</div>
                    <div class="text-xs text-morandi-lightText">蛋白质 (g)</div>
                  </template>
                </div>
                <!-- 脂肪 -->
                <div class="text-center">
                  <template v-if="hasSubstitutions">
                    <div class="text-lg font-bold" :class="modifiedNutrition.fat < originalNutritionSum.fat ? 'text-green-600' : 'text-red-600'">
                      {{ modifiedNutrition.fat }}g
                    </div>
                    <div class="text-xs text-gray-400">每100g: {{ modifiedPer100g.fat }}g</div>
                  </template>
                  <template v-else>
                    <div class="text-2xl font-bold text-morandi-text">{{ localRecipe?.fat }}</div>
                    <div class="text-xs text-morandi-lightText">脂肪 (g)</div>
                  </template>
                </div>
                <!-- 碳水 -->
                <div class="text-center">
                  <template v-if="hasSubstitutions">
                    <div class="text-lg font-bold text-morandi-text">{{ modifiedNutrition.carbs }}g</div>
                    <div class="text-xs text-gray-400">每100g: {{ modifiedPer100g.carbs }}g</div>
                  </template>
                  <template v-else>
                    <div class="text-2xl font-bold text-morandi-text">{{ localRecipe?.carbs }}</div>
                    <div class="text-xs text-morandi-lightText">碳水 (g)</div>
                  </template>
                </div>
              </div>
            </div>
            <div class="mb-6">
              <h4 class="font-semibold text-morandi-text mb-3 flex items-center gap-2">
                食材清单
                <span v-if="hasSubstitutions" class="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-normal">已智能替换</span>
              </h4>
              <ul class="space-y-2.5">
                <li
                  v-for="(ing, index) in hasSubstitutions ? modifiedIngredients : (localRecipe?.ingredients || [])"
                  :key="index"
                  class="flex items-center justify-between p-3.5 rounded-lg transition-all duration-200"
                  :class="ing.isSubstituted ? 'bg-green-50 border border-green-200' : (isIngredientNotSuitable(ing) ? 'bg-red-50 border border-red-200' : 'bg-morandi-soft/20')"
                >
                  <div class="flex items-center gap-2">
                    <!-- 已替换的食材 -->
                    <template v-if="ing.isSubstituted">
                      <span class="text-sm line-through text-gray-400">{{ ing.originalName }}</span>
                      <span class="text-gray-400">→</span>
                      <span class="text-green-700 font-medium">{{ ing.ingredientName }}</span>
                      <span class="px-1.5 py-0.5 text-xs font-bold bg-green-500 text-white rounded-full">已替换</span>
                    </template>
                    <!-- 未替换的食材 -->
                    <template v-else>
                      <span class="text-morandi-text">{{ ing.ingredientName || ing.ingredient_name }}</span>
                      <span v-if="isIngredientNotSuitable(ing)" class="px-1.5 py-0.5 text-xs font-bold bg-red-500 text-white rounded-full">
                        不适合
                      </span>
                    </template>
                  </div>
                  <div class="flex items-center gap-2">
                    <span v-if="!ing.isSubstituted && getIngredientDBLabel(ing.ingredientName || ing.ingredient_name || ing.name)" class="text-xs px-1.5 py-0.5 rounded bg-green-50 text-green-600">
                      {{ getIngredientDBLabel(ing.ingredientName || ing.ingredient_name || ing.name) }}
                    </span>
                    <span class="text-morandi-lightText">{{ ing.amount }}{{ ing.unit }}</span>
                  </div>
                </li>
              </ul>
            </div>

            <!-- 烹饪步骤 -->
            <div v-if="localRecipe?.steps && localRecipe.steps.length > 0" class="mb-6">
              <h4 class="font-semibold text-morandi-text mb-3">烹饪步骤</h4>
              <ol class="space-y-2">
                <li
                  v-for="(step, index) in localRecipe.steps"
                  :key="index"
                  class="flex items-start gap-3 p-3 rounded-lg bg-morandi-soft/20"
                >
                  <span class="flex-shrink-0 w-6 h-6 rounded-full bg-morandi-accent text-white text-xs flex items-center justify-center mt-0.5">{{ Number(index) + 1 }}</span>
                  <span class="text-morandi-text text-sm">{{ step }}</span>
                </li>
              </ol>
            </div>

            <!-- 规则基替换建议（过敏/口味） -->
            <div v-if="localRecipe?.substitutions?.length > 0" class="mb-6 p-4 rounded-xl bg-amber-50 border border-amber-200">
              <h4 class="font-semibold text-amber-800 mb-3 flex items-center gap-2">
                <component :is="AlertTriangle" class="w-4 h-4" /> 食材替换建议（基于您的饮食档案）
              </h4>
              <div v-for="sub in localRecipe.substitutions" :key="sub.ingredient?.ingredientId || sub.ingredientName"
                class="mb-3 p-3 rounded-lg bg-white/60 border border-amber-100 last:mb-0"
              >
                <div class="flex items-center gap-2 text-sm mb-2">
                  <span class="text-amber-700 font-medium">{{ sub.ingredient?.ingredientName || sub.ingredientName }}</span>
                  <span class="text-amber-500 text-xs">{{ sub.reason }}</span>
                </div>
                <div v-if="sub.alternatives?.length > 0" class="flex flex-wrap gap-1.5">
                  <span class="text-xs text-gray-500 mr-1">推荐替代：</span>
                  <button
                    v-for="(alt, idx) in sub.alternatives"
                    :key="idx"
                    @click="applyIngredientSub(sub.ingredient?.ingredientName || sub.ingredientName, typeof alt === 'string' ? alt : alt.name)"
                    class="px-2.5 py-1 rounded-lg text-xs bg-white border border-amber-300 text-amber-700 hover:bg-amber-100 transition-colors"
                  >
                    {{ typeof alt === 'string' ? alt : alt.name }}
                    <span v-if="typeof alt !== 'string' && alt.benefit" class="opacity-70 ml-0.5">· {{ alt.benefit }}</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- 食物数据库基替换建议（高脂/高GI/高热量） -->
            <div v-if="localRecipe?.foodDbSubstitutions?.length > 0" class="mb-6 p-4 rounded-xl bg-blue-50 border border-blue-200">
              <h4 class="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                <span>🔬</span> 营养优化建议
              </h4>
              <div v-for="sub in localRecipe.foodDbSubstitutions" :key="sub.ingredientName"
                class="mb-3 p-3 rounded-lg bg-white/60 border border-blue-100 last:mb-0"
              >
                <div class="flex items-center gap-2 text-sm mb-2">
                  <span class="text-blue-700 font-medium">{{ sub.ingredientName }}</span>
                  <span class="text-red-500 text-xs">⚠ {{ (sub.concerns || []).join('、') }}</span>
                </div>
                <div class="flex flex-wrap gap-1.5">
                  <span class="text-xs text-gray-500 mr-1">推荐替代：</span>
                  <button
                    v-for="(alt, idx) in sub.alternatives"
                    :key="idx"
                    @click="applyNutritionSub(sub.ingredientName, alt)"
                    class="px-2.5 py-1 rounded-lg text-xs bg-white border border-blue-300 text-blue-700 hover:bg-blue-100 transition-colors"
                  >
                    {{ alt.name }}
                    <span class="opacity-70 ml-0.5">{{ alt.reason }}</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- 已应用的替换 -->
            <div v-if="hasSubstitutions" class="mb-6 p-4 rounded-xl bg-green-50 border border-green-200">
              <h4 class="font-semibold text-green-800 mb-2 flex items-center gap-2">
                <component :is="Check" class="w-4 h-4" /> 已应用的替换
              </h4>
              <div v-for="(replaced, original) in appliedSubstitutions" :key="original"
                class="flex items-center justify-between py-1.5 text-sm"
              >
                <span class="text-gray-600">
                  <span class="line-through text-gray-400">{{ original }}</span>
                  <span class="mx-1.5">→</span>
                  <span class="text-green-700 font-medium">{{ typeof replaced === 'object' ? replaced.name : replaced }}</span>
                </span>
                <button @click="removeSubstitution(original)" class="text-xs text-red-400 hover:text-red-600">撤销</button>
              </div>
            </div>

            <!-- 营养变化对比 -->
            <div v-if="hasSubstitutions" class="mb-6 p-4 rounded-xl bg-blue-50 border border-blue-200">
              <h4 class="font-medium text-blue-800 mb-3 flex items-center gap-2">
                <component :is="BarChart3" class="w-4 h-4" /> 替换前后营养对比
              </h4>
              <div class="overflow-x-auto">
                <table class="w-full text-sm text-center">
                  <thead>
                    <tr class="text-xs text-gray-500 border-b border-blue-100">
                      <th class="py-1.5 px-2 text-left">项目</th>
                      <th class="py-1.5 px-2">替换前</th>
                      <th class="py-1.5 px-2">替换后</th>
                      <th class="py-1.5 px-2">变化</th>
                    </tr>
                  </thead>
                  <tbody class="text-xs">
                    <tr class="border-b border-blue-50">
                      <td class="py-2 px-2 text-left font-medium text-gray-600">热量</td>
                      <td class="py-2 px-2">{{ originalNutritionSum.calories }} kcal</td>
                      <td class="py-2 px-2 font-medium" :class="modifiedNutrition.calories < originalNutritionSum.calories ? 'text-green-600' : 'text-red-600'">{{ modifiedNutrition.calories }} kcal</td>
                      <td class="py-2 px-2" :class="(modifiedNutrition.calories - originalNutritionSum.calories) < 0 ? 'text-green-600' : 'text-red-600'">
                        {{ (modifiedNutrition.calories - originalNutritionSum.calories) > 0 ? '+' : '' }}{{ modifiedNutrition.calories - originalNutritionSum.calories }}
                      </td>
                    </tr>
                    <tr class="border-b border-blue-50">
                      <td class="py-2 px-2 text-left font-medium text-gray-600">蛋白质</td>
                      <td class="py-2 px-2">{{ originalNutritionSum.protein }}g</td>
                      <td class="py-2 px-2 font-medium" :class="modifiedNutrition.protein > originalNutritionSum.protein ? 'text-green-600' : 'text-morandi-text'">{{ modifiedNutrition.protein }}g</td>
                      <td class="py-2 px-2" :class="(modifiedNutrition.protein - originalNutritionSum.protein) > 0 ? 'text-green-600' : 'text-red-600'">
                        {{ (modifiedNutrition.protein - originalNutritionSum.protein) > 0 ? '+' : '' }}{{ (modifiedNutrition.protein - originalNutritionSum.protein).toFixed(1) }}
                      </td>
                    </tr>
                    <tr class="border-b border-blue-50">
                      <td class="py-2 px-2 text-left font-medium text-gray-600">脂肪</td>
                      <td class="py-2 px-2">{{ originalNutritionSum.fat }}g</td>
                      <td class="py-2 px-2 font-medium" :class="modifiedNutrition.fat < originalNutritionSum.fat ? 'text-green-600' : 'text-red-600'">{{ modifiedNutrition.fat }}g</td>
                      <td class="py-2 px-2" :class="(modifiedNutrition.fat - originalNutritionSum.fat) < 0 ? 'text-green-600' : 'text-red-600'">
                        {{ (modifiedNutrition.fat - originalNutritionSum.fat) > 0 ? '+' : '' }}{{ (modifiedNutrition.fat - originalNutritionSum.fat).toFixed(1) }}
                      </td>
                    </tr>
                    <tr class="border-b border-blue-50">
                      <td class="py-2 px-2 text-left font-medium text-gray-600">每100g热量</td>
                      <td class="py-2 px-2">{{ originalPer100g.calories }} kcal</td>
                      <td class="py-2 px-2 font-medium" :class="modifiedPer100g.calories < originalPer100g.calories ? 'text-green-600' : 'text-red-600'">{{ modifiedPer100g.calories }} kcal</td>
                      <td class="py-2 px-2" :class="(modifiedPer100g.calories - originalPer100g.calories) < 0 ? 'text-green-600' : 'text-red-600'">
                        {{ (modifiedPer100g.calories - originalPer100g.calories) > 0 ? '+' : '' }}{{ modifiedPer100g.calories - originalPer100g.calories }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p class="text-xs text-gray-400 mt-2">基于食材数据库估算，整份约 {{ estimatedTotalWeight }}g</p>
            </div>

            <div class="flex gap-3">
              <button
                @click="handleSave"
                class="flex-1 px-4 py-2.5 rounded-lg bg-morandi-accent text-white hover:opacity-90 transition-opacity"
              >
                保存到我的食谱
              </button>
              <button
                @click="emit('update:modelValue', false)"
                class="flex-1 px-4 py-2.5 rounded-lg border border-morandi-soft text-morandi-text hover:bg-morandi-soft transition-colors"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { api } from '@/api'
import { useRecipeSubstitution } from '@/composables/useRecipeSubstitution'
import { BarChart3, Check, AlertTriangle } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: boolean
  recipe: any
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', recipe: any): void
}>()

/** 本地食谱副本：详情接口会向其挂载 substitutions/ingredientNutrition 等字段 */
const localRecipe = ref<any>(null)

const {
  appliedSubstitutions,
  hasSubstitutions,
  modifiedIngredients,
  originalNutritionSum,
  estimatedTotalWeight,
  originalPer100g,
  modifiedPer100g,
  modifiedNutrition,
  isIngredientNotSuitable,
  applyIngredientSub,
  applyNutritionSub,
  removeSubstitution,
  resetSubstitutions
} = useRecipeSubstitution(localRecipe)

const enrichedIngredients = ref<Record<string, any>>({})

/** 从food数据库批量查找食材营养信息 */
const fetchIngredientDBInfo = async (names: string[]) => {
  if (!names || names.length === 0) return
  try {
    const data = await api.food.batchLookup(names)
    if (data) {
      enrichedIngredients.value = { ...enrichedIngredients.value, ...data }
    }
  } catch (e) {
    console.warn('食材数据库查询失败', e)
  }
}

/** 获取食材的数据库信息展示文本 */
function getIngredientDBLabel(name: string): string {
  const food = enrichedIngredients.value[name]
  if (!food) return ''
  const cal = food.calorie ?? '-'
  return `[${food.foodCategory || '?'}] ${cal}kcal/100g`
}

/**
 * 打开弹窗时获取食谱详情：替换建议、营养估算、食材DB信息。
 * 对应原 viewRecipe 中除 selectedRecipe 赋值 / showDetailDialog 之外的逻辑。
 */
async function fetchRecipeDetail(recipe: any) {
  if (!recipe) return
  // 已收藏的食谱（替换后的版本），直接使用保存的数据，不获取替换建议
  if (recipe.isSaved) return

  // 获取食材数据库信息
  if (recipe.ingredients?.length > 0) {
    const names = recipe.ingredients.map((i: any) => i.ingredient_name || i.ingredientName || i.name).filter(Boolean)
    if (names.length > 0) fetchIngredientDBInfo(names)
  }
  // 获取替换建议
  try {
    const detail = await api.recipe.getDetail(recipe.id || recipe.originalId)
    if (detail && localRecipe.value) {
      if (detail.ingredients) localRecipe.value.ingredients = detail.ingredients
      localRecipe.value.substitutions = detail.substitutions || []
      localRecipe.value.foodDbSubstitutions = detail.foodDbSubstitutions || []
      // 食材营养估算和营养变化
      localRecipe.value.ingredientNutrition = detail.ingredientNutrition || []
      localRecipe.value.nutritionChange = detail.nutritionChange || { hasChanges: false, calories: 0, fat: 0, protein: 0, replaceableCount: 0 }
      // 如有替换建议则同时查找食材DB
      const allSubNames = (detail.foodDbSubstitutions || []).flatMap((s: any) =>
        (s.alternatives || []).map((a: any) => a.name)
      )
      if (allSubNames.length > 0) fetchIngredientDBInfo(allSubNames)
    }
  } catch (e) {
    console.warn('获取食谱详情失败', e)
  }
}

/** 保存到我的食谱：把当前（可能含替换后字段）的食谱交给父组件处理 */
function handleSave() {
  if (!localRecipe.value) return
  emit('save', localRecipe.value)
}

// 弹窗打开时：同步父组件传入的 recipe，重置替换状态并拉取详情
watch(() => props.modelValue, (val) => {
  if (val && props.recipe) {
    localRecipe.value = props.recipe
    resetSubstitutions()
    fetchRecipeDetail(props.recipe)
  }
})

// 父组件在弹窗已打开时切换 recipe（保险场景）：同步并重新拉取
watch(() => props.recipe, (val) => {
  if (props.modelValue && val) {
    localRecipe.value = val
    resetSubstitutions()
    fetchRecipeDetail(val)
  }
})
</script>

<style scoped>
.dialog-fade {
  animation: dialogFade 0.25s ease forwards;
  will-change: opacity, transform;
}
@keyframes dialogFade {
  from { opacity: 0; transform: scale(0.96) translateZ(0); }
  to { opacity: 1; transform: scale(1) translateZ(0); }
}
.mask-layer {
  will-change: backdrop-filter, opacity;
}
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
@media (max-width: 768px) {
  .mask-layer { backdrop-filter: none !important; --tw-backdrop-blur: none !important; }
}
</style>
