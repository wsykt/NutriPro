<template>
  <div v-if="modelValue">
    <Teleport to="body">
      <!-- 无遮罩气泡弹窗：透明点击层（视觉无灰色蒙层），点击气泡外关闭 -->
      <div class="rk-tel">
        <div class="catcher" @click="emit('update:modelValue', false)"></div>
        <div class="bubble scrollbar-hide" @click.stop>
          <!-- 头部 -->
          <div class="bhead">
            <span class="bcover">{{ localRecipe?.name?.slice(0, 1) || '食' }}</span>
            <div class="bt">
              <h4>{{ localRecipe?.name }}</h4>
              <div class="tags">
                <i v-for="t in (localRecipe?.tags || [])" :key="t">{{ t }}</i>
                <i v-if="localRecipe?.source === 'generated'" class="ai">✦ AI 炼成</i>
              </div>
            </div>
            <button class="bclose" @click="emit('update:modelValue', false)"><X :size="13" /></button>
          </div>

          <div class="bbody">
            <p class="desc">{{ localRecipe?.description }}</p>

            <!-- 营养卡片：无替换显示每100g值，有替换显示总值+每100g值 -->
            <div class="sec">
              <div class="sec-h">
                <span v-if="!hasSubstitutions">每100g 营养值</span>
                <span v-else>替换后营养（总值 / 每100g）</span>
                <em class="wt">≈{{ estimatedTotalWeight }}g/份</em>
              </div>
              <div class="ntr">
                <!-- 热量 -->
                <div class="cell">
                  <template v-if="hasSubstitutions">
                    <b :class="modifiedNutrition.calories < originalNutritionSum.calories ? 'good' : 'badv'">{{ modifiedNutrition.calories }}</b>
                    <span>每100g: {{ modifiedPer100g.calories }} kcal</span>
                  </template>
                  <template v-else>
                    <b>{{ localRecipe?.calories }}</b><span>热量 (kcal)</span>
                  </template>
                </div>
                <!-- 蛋白质 -->
                <div class="cell mp">
                  <template v-if="hasSubstitutions">
                    <b :class="modifiedNutrition.protein > originalNutritionSum.protein ? 'good' : ''">{{ modifiedNutrition.protein }}g</b>
                    <span>每100g: {{ modifiedPer100g.protein }}g</span>
                  </template>
                  <template v-else>
                    <b>{{ localRecipe?.protein }}g</b><span>蛋白质</span>
                  </template>
                </div>
                <!-- 脂肪 -->
                <div class="cell mf">
                  <template v-if="hasSubstitutions">
                    <b :class="modifiedNutrition.fat < originalNutritionSum.fat ? 'good' : 'badv'">{{ modifiedNutrition.fat }}g</b>
                    <span>每100g: {{ modifiedPer100g.fat }}g</span>
                  </template>
                  <template v-else>
                    <b>{{ localRecipe?.fat }}g</b><span>脂肪</span>
                  </template>
                </div>
                <!-- 碳水 -->
                <div class="cell mc">
                  <template v-if="hasSubstitutions">
                    <b>{{ modifiedNutrition.carbs }}g</b>
                    <span>每100g: {{ modifiedPer100g.carbs }}g</span>
                  </template>
                  <template v-else>
                    <b>{{ localRecipe?.carbs }}g</b><span>碳水</span>
                  </template>
                </div>
              </div>
            </div>

            <!-- 食材清单 -->
            <div class="sec">
              <h6>星材 · 食材清单 <span v-if="hasSubstitutions" class="subed">已智能替换</span></h6>
              <ul class="ings">
                <li
                  v-for="(ing, index) in hasSubstitutions ? modifiedIngredients : (localRecipe?.ingredients || [])"
                  :key="index"
                  :class="{ rep: ing.isSubstituted, unfit: !ing.isSubstituted && isIngredientNotSuitable(ing) }"
                >
                  <div class="il">
                    <template v-if="ing.isSubstituted">
                      <s>{{ ing.originalName }}</s><em class="arrow">→</em><b>{{ ing.ingredientName }}</b>
                      <i class="pill g">已替换</i>
                    </template>
                    <template v-else>
                      <span>{{ ing.ingredientName || ing.ingredient_name }}</span>
                      <i v-if="isIngredientNotSuitable(ing)" class="pill r">不适合</i>
                    </template>
                  </div>
                  <div class="ir">
                    <em v-if="!ing.isSubstituted && getIngredientDBLabel(ing.ingredientName || ing.ingredient_name || ing.name)" class="db">
                      {{ getIngredientDBLabel(ing.ingredientName || ing.ingredient_name || ing.name) }}
                    </em>
                    <span class="amt">{{ ing.amount }}{{ ing.unit }}</span>
                  </div>
                </li>
              </ul>
            </div>

            <!-- 烹饪步骤 -->
            <div v-if="localRecipe?.steps && localRecipe.steps.length > 0" class="sec">
              <h6>炼制之法 · 烹饪步骤</h6>
              <ol>
                <li v-for="(step, index) in localRecipe.steps" :key="index">
                  <span class="no">{{ Number(index) + 1 }}</span>{{ step }}
                </li>
              </ol>
            </div>

            <!-- 规则基替换建议（过敏/口味） -->
            <div v-if="localRecipe?.substitutions?.length > 0" class="note amber">
              <h6><AlertTriangle :size="13" /> 食材替换建议（基于您的饮食档案）</h6>
              <div v-for="sub in localRecipe.substitutions" :key="sub.ingredient?.ingredientId || sub.ingredientName" class="note-item">
                <div class="ni-h">
                  <b>{{ sub.ingredient?.ingredientName || sub.ingredientName }}</b>
                  <em>{{ sub.reason }}</em>
                </div>
                <div v-if="sub.alternatives?.length > 0" class="alts">
                  <span class="alt-lb">推荐替代：</span>
                  <button
                    v-for="(alt, idx) in sub.alternatives"
                    :key="idx"
                    class="alt"
                    @click="applyIngredientSub(sub.ingredient?.ingredientName || sub.ingredientName, typeof alt === 'string' ? alt : alt.name)"
                  >
                    {{ typeof alt === 'string' ? alt : alt.name }}
                    <em v-if="typeof alt !== 'string' && alt.benefit">· {{ alt.benefit }}</em>
                  </button>
                </div>
              </div>
            </div>

            <!-- 食物数据库基替换建议（高脂/高GI/高热量） -->
            <div v-if="localRecipe?.foodDbSubstitutions?.length > 0" class="note blue">
              <h6><Sparkles :size="13" /> 营养优化建议</h6>
              <div v-for="sub in localRecipe.foodDbSubstitutions" :key="sub.ingredientName" class="note-item">
                <div class="ni-h">
                  <b>{{ sub.ingredientName }}</b>
                  <em class="badv"> {{ (sub.concerns || []).join('、') }}</em>
                </div>
                <div class="alts">
                  <span class="alt-lb">推荐替代：</span>
                  <button
                    v-for="(alt, idx) in sub.alternatives"
                    :key="idx"
                    class="alt"
                    @click="applyNutritionSub(sub.ingredientName, alt)"
                  >
                    {{ alt.name }}
                    <em>{{ alt.reason }}</em>
                  </button>
                </div>
              </div>
            </div>

            <!-- 已应用的替换 -->
            <div v-if="hasSubstitutions" class="note green">
              <h6><Check :size="13" /> 已应用的替换</h6>
              <div v-for="(replaced, original) in appliedSubstitutions" :key="original" class="applied">
                <span>
                  <s>{{ original }}</s><em class="arrow">→</em>
                  <b>{{ typeof replaced === 'object' ? replaced.name : replaced }}</b>
                </span>
                <button class="undo" @click="removeSubstitution(original)">撤销</button>
              </div>
            </div>

            <!-- 营养变化对比 -->
            <div v-if="hasSubstitutions" class="note blue">
              <h6><BarChart3 :size="13" /> 替换前后营养对比</h6>
              <div class="cmp-wrap">
                <table class="cmp">
                  <thead>
                    <tr>
                      <th class="tl">项目</th><th>替换前</th><th>替换后</th><th>变化</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td class="tl">热量</td>
                      <td>{{ originalNutritionSum.calories }} kcal</td>
                      <td class="strong">{{ modifiedNutrition.calories }} kcal</td>
                      <td :class="(modifiedNutrition.calories - originalNutritionSum.calories) < 0 ? 'good' : 'badv'">
                        {{ (modifiedNutrition.calories - originalNutritionSum.calories) > 0 ? '+' : '' }}{{ modifiedNutrition.calories - originalNutritionSum.calories }}
                      </td>
                    </tr>
                    <tr>
                      <td class="tl">蛋白质</td>
                      <td>{{ originalNutritionSum.protein }}g</td>
                      <td class="strong">{{ modifiedNutrition.protein }}g</td>
                      <td :class="(modifiedNutrition.protein - originalNutritionSum.protein) > 0 ? 'good' : 'badv'">
                        {{ (modifiedNutrition.protein - originalNutritionSum.protein) > 0 ? '+' : '' }}{{ (modifiedNutrition.protein - originalNutritionSum.protein).toFixed(1) }}
                      </td>
                    </tr>
                    <tr>
                      <td class="tl">脂肪</td>
                      <td>{{ originalNutritionSum.fat }}g</td>
                      <td class="strong">{{ modifiedNutrition.fat }}g</td>
                      <td :class="(modifiedNutrition.fat - originalNutritionSum.fat) < 0 ? 'good' : 'badv'">
                        {{ (modifiedNutrition.fat - originalNutritionSum.fat) > 0 ? '+' : '' }}{{ (modifiedNutrition.fat - originalNutritionSum.fat).toFixed(1) }}
                      </td>
                    </tr>
                    <tr>
                      <td class="tl">每100g热量</td>
                      <td>{{ originalPer100g.calories }} kcal</td>
                      <td class="strong">{{ modifiedPer100g.calories }} kcal</td>
                      <td :class="(modifiedPer100g.calories - originalPer100g.calories) < 0 ? 'good' : 'badv'">
                        {{ (modifiedPer100g.calories - originalPer100g.calories) > 0 ? '+' : '' }}{{ modifiedPer100g.calories - originalPer100g.calories }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p class="cmp-note">基于食材数据库估算，整份约 {{ estimatedTotalWeight }}g</p>
            </div>

            <!-- 底部操作 -->
            <div class="bfoot">
              <button class="save" @click="handleSave">
                <Heart :size="13" />{{ localRecipe?.isSaved ? '移出星匣' : '保存到我的食谱' }}
              </button>
              <button class="ghost" @click="emit('update:modelValue', false)">收起</button>
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
import { X, Heart, Check, Sparkles, AlertTriangle, BarChart3 } from 'lucide-vue-next'

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
/* ===== 星宴详情 · 无遮罩暗金气泡弹窗 ===== */
@keyframes rkPop {
  0% { opacity: 0; transform: scale(.6) translateY(18px); }
  62% { opacity: 1; transform: scale(1.04); }
  100% { opacity: 1; transform: scale(1); }
}
.rk-tel {
  position: fixed; inset: 0; z-index: 50;
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.catcher { position: absolute; inset: 0; }
.bubble {
  position: relative; z-index: 10; width: min(680px, 100%); max-height: 84vh;
  overflow: auto; color: #55503F;
  background: #FDFAF3;
  border: 1px solid rgba(184, 134, 59, .5); border-radius: 20px;
  box-shadow: 0 30px 70px -28px rgba(46, 42, 34, .45);
  animation: rkPop .5s cubic-bezier(.34, 1.56, .64, 1) backwards;
}
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }

/* 头部 */
.bhead {
  display: flex; align-items: center; gap: 12px;
  padding: 16px 18px 12px; border-bottom: 1px dashed rgba(184, 134, 59, .3);
  position: sticky; top: 0; z-index: 2;
  background: #FDFAF3;
}
.bcover {
  width: 46px; height: 46px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Noto Serif SC', serif; font-size: 20px; font-weight: 900; color: #B8863B;
  background: radial-gradient(circle at 30% 22%, rgba(184, 134, 59, .18), transparent 70%),
    linear-gradient(160deg, #F5EDDA, #EFE2C4);
  border: 1px solid rgba(184, 134, 59, .4);
  text-shadow: 0 2px 10px rgba(184, 134, 59, .3);
}
.bt { min-width: 0; }
.bt h4 { font-family: 'Noto Serif SC', serif; font-size: 17px; font-weight: 900; color: #2E2A22; letter-spacing: .04em; }
.bt .tags { display: flex; gap: 4px; margin-top: 5px; flex-wrap: wrap; }
.bt .tags i {
  font-style: normal; font-size: 9px; padding: 1.5px 8px; border-radius: 99px;
  background: rgba(184, 134, 59, .1); color: #8a6d3b; border: 1px solid rgba(184, 134, 59, .28);
}
.bt .tags i.ai { color: #B8863B; border-color: rgba(184, 134, 59, .5); }
.bclose {
  margin-left: auto; width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  border: 1px solid rgba(184, 134, 59, .4); background: none; color: #A08F6E;
  display: flex; align-items: center; justify-content: center; transition: .25s; cursor: pointer;
}
.bclose:hover { color: #B8863B; border-color: #B8863B; transform: rotate(90deg); }

/* 主体 */
.bbody { padding: 14px 18px 18px; }
.desc { font-size: 12px; line-height: 1.85; color: #55503F; margin-bottom: 13px; }

.sec { margin-bottom: 15px; }
.sec-h {
  display: flex; align-items: baseline; gap: 9px; margin-bottom: 8px;
  font-size: 10.5px; letter-spacing: .12em; color: #847C63;
}
.sec-h .wt { font-style: normal; margin-left: auto; }
h6 {
  font-size: 10.5px; letter-spacing: .2em; color: #A0722F; margin-bottom: 8px;
  display: flex; align-items: center; gap: 7px;
}
h6::before { content: ''; width: 14px; height: 1px; background: #B8863B; }
h6 .subed {
  font-size: 9px; font-weight: 700; letter-spacing: .06em; padding: 1.5px 8px; border-radius: 99px;
  color: #5E8F5E; background: rgba(94, 143, 94, .1); border: 1px solid rgba(94, 143, 94, .4);
}

/* 营养四格：热量金 / 蛋白蓝 / 脂肪金 / 碳水绿 */
.ntr { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.ntr .cell {
  border: 1px solid rgba(184, 134, 59, .28); border-radius: 10px;
  padding: 10px 6px; text-align: center; background: #F8F2E3;
}
.ntr .cell b { font-family: 'Noto Serif SC', serif; font-size: 17px; font-weight: 900; color: #B8863B; display: block; }
.ntr .cell span { font-size: 9px; color: #847C63; letter-spacing: .06em; }
.ntr .cell.mp b { color: #4A6FA5; }
.ntr .cell.mf b { color: #C08A2D; }
.ntr .cell.mc b { color: #5E8F5E; }
.good { color: #5E8F5E !important; }
.badv { color: #B5442E !important; }

/* 食材列表 */
.ings { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.ings li {
  display: flex; align-items: center; gap: 9px; flex-wrap: wrap;
  padding: 8.5px 12px; border-radius: 10px; font-size: 11.5px;
  border: 1px solid rgba(184, 134, 59, .25); background: rgba(184, 134, 59, .05);
}
.ings li.rep { border-color: rgba(94, 143, 94, .45); background: rgba(94, 143, 94, .08); }
.ings li.unfit { border-color: rgba(181, 68, 46, .4); background: rgba(181, 68, 46, .06); }
.ings .il { display: flex; align-items: center; gap: 6px; min-width: 0; flex-wrap: wrap; color: #55503F; }
.ings .il s { color: #A08F6E; }
.ings .il b { color: #5E8F5E; font-weight: 700; }
.ings .arrow { font-style: normal; color: #A08F6E; }
.ings .ir { margin-left: auto; display: flex; align-items: center; gap: 8px; }
.ings .db { font-style: normal; font-size: 9.5px; color: #5E8F5E; }
.ings .amt { font-size: 11px; color: #847C63; white-space: nowrap; }
.pill {
  font-style: normal; font-size: 9px; font-weight: 700; padding: 1.5px 8px; border-radius: 99px;
}
.pill.g { color: #5E8F5E; background: rgba(94, 143, 94, .12); border: 1px solid rgba(94, 143, 94, .45); }
.pill.r { color: #B5442E; background: rgba(181, 68, 46, .1); border: 1px solid rgba(181, 68, 46, .45); }

/* 步骤 */
ol { list-style: none; counter-reset: dstp; }
ol li {
  counter-increment: dstp; display: flex; gap: 10px;
  font-size: 11.5px; line-height: 1.85; color: #55503F; padding: 5px 0;
}
ol li .no {
  counter-increment: none;
  width: 20px; height: 20px; border-radius: 50%; flex-shrink: 0; margin-top: 2px;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; color: #14110B;
  background: linear-gradient(135deg, #E8B973, #B36B2A);
}

/* 替换建议盒（暗金三态） */
.note {
  margin-bottom: 15px; padding: 12px 14px; border-radius: 12px;
}
.note h6 { margin-bottom: 9px; }
.note h6::before { display: none; }
.note h6 svg { flex-shrink: 0; }
.note.amber { border: 1px solid rgba(224, 176, 78, .35); background: rgba(224, 176, 78, .07); }
.note.amber h6 { color: #8A6D3B; }
.note.blue { border: 1px solid rgba(108, 143, 190, .35); background: rgba(108, 143, 190, .08); }
.note.blue h6 { color: #4A6FA5; }
.note.green { border: 1px solid rgba(127, 174, 142, .4); background: rgba(127, 174, 142, .08); }
.note.green h6 { color: #5E8F5E; }
.note-item { padding: 8px 10px; border-radius: 9px; background: rgba(184, 134, 59, .07); margin-bottom: 7px; }
.note-item:last-child { margin-bottom: 0; }
.ni-h { display: flex; align-items: center; gap: 8px; font-size: 11.5px; flex-wrap: wrap; }
.ni-h b { font-weight: 700; }
.note.amber .ni-h b { color: #A0722F; }
.note.blue .ni-h b { color: #4A6FA5; }
.ni-h em { font-style: normal; font-size: 10.5px; color: #847C63; }
.alts { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; margin-top: 7px; }
.alt-lb { font-size: 10.5px; color: #847C63; }
.alt {
  font-size: 10.5px; padding: 3px 10px; border-radius: 99px; cursor: pointer; font-family: inherit;
  background: rgba(184, 134, 59, .07); color: #55503F;
  border: 1px solid rgba(184, 134, 59, .38); transition: .25s;
}
.alt:hover { color: #B8863B; border-color: #B8863B; background: rgba(184, 134, 59, .12); }
.alt em { font-style: normal; opacity: .7; font-size: 9.5px; }
.applied {
  display: flex; align-items: center; justify-content: space-between; gap: 9px;
  padding: 5px 2px; font-size: 11.5px;
}
.applied s { color: #847C63; }
.applied .arrow { font-style: normal; color: #847C63; margin: 0 5px; }
.applied b { color: #5E8F5E; }
.undo {
  font-size: 10.5px; background: none; border: none; cursor: pointer; font-family: inherit;
  color: #B5442E; transition: .2s;
}
.undo:hover { color: #8F2F1D; }

/* 对比表 */
.cmp-wrap { overflow-x: auto; }
.cmp { width: 100%; border-collapse: collapse; font-size: 11px; text-align: center; }
.cmp th {
  font-size: 9.5px; font-weight: 600; letter-spacing: .06em; color: #847C63;
  padding: 6px 8px; border-bottom: 1px solid rgba(184, 134, 59, .35);
}
.cmp td { padding: 7px 8px; color: #55503F; border-bottom: 1px solid rgba(184, 134, 59, .15); }
.cmp td.tl { text-align: left; color: #847C63; }
.cmp td.strong { color: #2E2A22; font-weight: 700; }
.cmp-note { font-size: 10px; color: #847C63; margin-top: 7px; }

/* 底部 */
.bfoot { display: flex; gap: 9px; margin-top: 16px; }
.bfoot .save {
  flex: 1; display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  border: none; border-radius: 11px; padding: 9.5px 0; cursor: pointer;
  font-size: 12px; font-weight: 700; letter-spacing: .08em; font-family: inherit;
  color: #14110B; background: linear-gradient(135deg, #E8B973, #B36B2A); transition: .25s;
}
.bfoot .save:hover { filter: brightness(1.1); }
.bfoot .ghost {
  border: 1px solid rgba(184, 134, 59, .4); background: none; border-radius: 11px;
  padding: 0 20px; font-size: 12px; color: #8a6d3b; transition: .25s; cursor: pointer; font-family: inherit;
}
.bfoot .ghost:hover { color: #B8863B; border-color: #B8863B; }

@media (max-width: 560px) {
  .ntr { grid-template-columns: repeat(2, 1fr); }
  .bfoot .ghost { padding: 0 14px; }
}
</style>
