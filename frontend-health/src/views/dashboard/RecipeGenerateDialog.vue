<template>
  <div v-if="modelValue">
    <Teleport to="body">
      <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          class="absolute inset-0 bg-black/35 backdrop-blur-[3px] mask-layer transition-opacity duration-200"
          @click="closeGenerateDialog"
        ></div>
        <div
          class="relative z-10 bg-white rounded-2xl w-full max-w-[680px] max-h-[80vh] overflow-auto shadow-xl dialog-fade scrollbar-hide"
          style="transform: translateZ(0);"
          @click.stop
        >
          <div class="p-8">
            <div class="flex items-center justify-between mb-6">
              <h3 class="text-xl font-bold text-morandi-text">AI生成食谱</h3>
              <button
                @click="closeGenerateDialog"
                class="w-10 h-10 flex items-center justify-center rounded-full hover:bg-morandi-soft text-morandi-lightText hover:text-morandi-text transition-colors text-lg"
              >
                ✕
              </button>
            </div>

            <textarea
              v-model="generatePrompt"
              @input="promptError = ''"
              rows="4"
              placeholder="请描述您想要的食谱，例如：适合减脂的午餐食谱，需要高蛋白低热量..."
              class="w-full px-4 py-3 rounded-lg bg-white/70 border text-sm outline-none transition-all mb-2 resize-none"
              :class="promptError ? 'border-red-300 focus:border-red-500' : 'border-morandi-soft focus:border-morandi-accent'"
            ></textarea>

            <!-- 校验提示 -->
            <div
              v-if="promptError"
              class="flex items-start gap-2 mb-4 px-3 py-2.5 rounded-lg bg-amber-50 border border-amber-200 text-sm"
            >
              <component :is="Lightbulb" class="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
              <span class="text-amber-700">{{ promptError }}</span>
            </div>

            <div class="mb-8">
              <p class="text-xs text-morandi-lightText mb-3">人群标签：</p>
              <div class="flex flex-wrap gap-2.5">
                <button
                  v-for="tag in personaTags"
                  :key="tag"
                  @click="selectedPersona = tag"
                  :class="[
                    'px-3 py-1.5 rounded-full text-xs transition-all duration-200',
                    selectedPersona === tag
                      ? 'bg-morandi-accent text-white shadow-sm'
                      : 'bg-morandi-soft text-morandi-text hover:bg-morandi-soft/70'
                  ]"
                >
                  {{ tag }}
                </button>
              </div>
            </div>

            <button
              @click="generateRecipe"
              :disabled="!generatePrompt.trim() || isGenerating"
              class="w-full px-4 py-3 rounded-lg bg-morandi-accent text-white font-medium hover:opacity-90 hover:scale-[1.01] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isGenerating ? '生成中...' : '生成食谱' }}
            </button>

            <div
              v-if="generatedRecipe"
              class="mt-6 p-5 rounded-xl bg-morandi-soft/30 border border-morandi-soft/50"
            >
              <h4 class="font-semibold text-morandi-text mb-2 text-lg">{{ generatedRecipe.name }}</h4>
              <p class="text-sm text-morandi-lightText mb-3">{{ generatedRecipe.description }}</p>
              <div class="flex flex-wrap gap-2 mb-4">
                <span
                  v-for="tag in generatedRecipe.tags"
                  :key="tag"
                  class="px-2 py-1 rounded-full bg-morandi-soft text-morandi-text text-xs"
                >
                  {{ tag }}
                </span>
              </div>

              <!-- 食材清单（带数据库匹配信息） -->
              <div class="text-sm mb-4">
                <div class="font-medium text-morandi-text mb-2">食材清单：</div>
                <ul class="text-morandi-lightText space-y-1.5">
                  <li
                    v-for="ing in generatedRecipe.ingredients"
                    :key="ing.ingredient_name"
                    class="flex items-center justify-between"
                  >
                    <span>{{ ing.ingredient_name }} {{ ing.amount }}{{ ing.unit }}</span>
                    <span v-if="getIngredientDBLabel(ing.ingredient_name)" class="text-xs px-1.5 py-0.5 rounded bg-green-50 text-green-600 ml-2 flex-shrink-0">
                      {{ getIngredientDBLabel(ing.ingredient_name) }}
                    </span>
                    <span v-else class="text-xs text-morandi-lightText italic ml-2 flex-shrink-0">
                      待录入
                    </span>
                  </li>
                </ul>
              </div>

              <!-- 烹饪步骤 -->
              <div v-if="generatedRecipe.steps && generatedRecipe.steps.length > 0" class="text-sm mb-4">
                <div class="font-medium text-morandi-text mb-2">烹饪步骤：</div>
                <ol class="text-morandi-lightText space-y-2 list-decimal list-inside">
                  <li v-for="(step, idx) in generatedRecipe.steps" :key="idx">
                    {{ step }}
                  </li>
                </ol>
              </div>

              <!-- 营养成分简表 -->
              <div class="grid grid-cols-5 gap-2 text-center text-sm p-3 rounded-lg bg-white/50 mb-4">
                <div>
                  <div class="text-xs text-morandi-lightText">热量</div>
                  <div class="font-bold text-morandi-accent">{{ generatedRecipe.calories }}kcal</div>
                </div>
                <div>
                  <div class="text-xs text-morandi-lightText">蛋白</div>
                  <div class="font-medium text-morandi-text">{{ generatedRecipe.protein }}g</div>
                </div>
                <div>
                  <div class="text-xs text-morandi-lightText">脂肪</div>
                  <div class="font-medium text-morandi-text">{{ generatedRecipe.fat }}g</div>
                </div>
                <div>
                  <div class="text-xs text-morandi-lightText">碳水</div>
                  <div class="font-medium text-morandi-text">{{ generatedRecipe.carbs }}g</div>
                </div>
                <div>
                  <div class="text-xs text-morandi-lightText">纤维</div>
                  <div class="font-medium text-morandi-text">{{ generatedRecipe.fiber }}g</div>
                </div>
              </div>

              <div class="flex gap-3 mt-5">
                <button
                  @click="saveGeneratedRecipe"
                  class="flex-1 px-4 py-2.5 rounded-lg bg-morandi-accent text-white text-sm hover:opacity-90 transition-opacity"
                >
                  保存到我的食谱
                </button>
                <button
                  @click="generateRecipe"
                  :disabled="!generatePrompt.trim() || isGenerating"
                  class="flex-1 px-4 py-2.5 rounded-lg border border-morandi-soft text-morandi-text text-sm hover:bg-morandi-soft transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  重新生成
                </button>
              </div>
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
import { Lightbulb } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: boolean
  personaTags: string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'generated'): void
}>()

const generatePrompt = ref('')
const promptError = ref('')
const selectedPersona = ref('普通用户')
const isGenerating = ref(false)
const generatedRecipe = ref<any>(null)
const enrichedIngredients = ref<Record<string, any>>({})

/** 校验AI生成食谱的输入 */
function validatePrompt(text: string): string {
  const trimmed = text.trim()
  if (trimmed.length < 4) {
    return '请输入更详细的需求描述，例如：「适合减脂的午餐，高蛋白低热量」或「用鸡胸肉和蔬菜做一道晚餐」'
  }
  // 纯数字/符号检测
  if (/^[\d\s\.\,\!\?\。\，\！\？\、\;\:\-\+\#\@\$\%\^\&\*\(\)\[\]\{\}]+$/.test(trimmed)) {
    return '请输入文字描述，例如说明想要的食谱类型（早/午/晚餐）、食材偏好和饮食目标'
  }
  // 检测是否包含食物相关关键词（如果完全没有，给出友好提示）
  const foodKeywords = /食|餐|饭|菜|肉|蛋|奶|豆|蔬|水|果|汤|粉|面|米|包|饺|炖|炒|炸|煎|蒸|煮|烤|拌|卤|低|高|减|增|健|营|养|热|蛋|白|脂|维|钙|铁|/
  if (!foodKeywords.test(trimmed)) {
    return '请描述您想要的食谱类型，例如：适合什么人群、想要什么口味、是否需要控制热量或蛋白质'
  }
  return '' // 校验通过
}

const closeGenerateDialog = () => {
  emit('update:modelValue', false)
  generatePrompt.value = ''
  promptError.value = ''
  selectedPersona.value = '普通用户'
  generatedRecipe.value = null
}

const generateRecipe = async () => {
  // 输入校验
  const error = validatePrompt(generatePrompt.value)
  if (error) {
    promptError.value = error
    return
  }
  promptError.value = ''
  isGenerating.value = true
  try {
    let result = await api.ai.generateRecipe(generatePrompt.value)
    if (typeof result === 'string') {
      try {
        const jsonMatch = result.match(/```json\s*([\s\S]*?)\s*```/)
        if (jsonMatch) {
          result = JSON.parse(jsonMatch[1])
        } else {
          result = JSON.parse(result)
        }
      } catch {
        // fallback if not valid JSON string
      }
    }
    generatedRecipe.value = result
    // 生成成功后查找食材数据库信息
    if (result?.ingredients?.length > 0) {
      fetchIngredientDBInfo(result.ingredients.map((i: any) => i.ingredient_name))
    }
  } catch (e) {
    console.error('生成食谱失败', e)
    promptError.value = 'AI生成失败，请稍后重试'
  } finally {
    isGenerating.value = false
  }
}

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

const saveGeneratedRecipe = async () => {
  if (!generatedRecipe.value) return
  try {
    await api.recipe.save({
      title: generatedRecipe.value.name,
      steps: JSON.stringify(generatedRecipe.value.steps || []),
      ingredients: JSON.stringify(generatedRecipe.value.ingredients || []),
      nutritionSummary: JSON.stringify({
        calories: generatedRecipe.value.calories,
        protein: generatedRecipe.value.protein,
        fat: generatedRecipe.value.fat,
        carbs: generatedRecipe.value.carbs,
        fiber: generatedRecipe.value.fiber || 0,
        tags: generatedRecipe.value.tags || []
      }),
      source: 'generated'
    })
    alert('保存成功')
    emit('update:modelValue', false)
    emit('generated')
    // 重置内部状态
    generatePrompt.value = ''
    promptError.value = ''
    selectedPersona.value = '普通用户'
    generatedRecipe.value = null
  } catch (e: any) {
    console.error('保存食谱失败', e)
    alert('保存失败：' + (e?.response?.data?.message || e?.message || '未知错误'))
  }
}

// 弹窗打开时重置内部状态（避免上次残留）
watch(() => props.modelValue, (val) => {
  if (val) {
    generatePrompt.value = ''
    promptError.value = ''
    selectedPersona.value = '普通用户'
    generatedRecipe.value = null
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
