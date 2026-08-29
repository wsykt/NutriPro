<template>
  <div v-if="modelValue">
    <Teleport to="body">
      <!-- 无遮罩气泡弹窗：透明点击层（视觉无灰色蒙层），点击气泡外关闭 -->
      <div class="rk-tel">
        <div class="catcher" @click="closeGenerateDialog"></div>
        <div class="bubble scrollbar-hide" @click.stop>
          <!-- 头部 -->
          <div class="bhead">
            <span class="bcover"><Sparkles :size="18" /></span>
            <div class="bt">
              <h4>AI 炼星 · 生成食谱</h4>
              <p>描述你的需求，ASTRAL 为你炼制专属星宴</p>
            </div>
            <button class="bclose" @click="closeGenerateDialog"><X :size="13" /></button>
          </div>

          <div class="bbody">
            <!-- 需求描述 -->
            <div class="fld-lb">需求描述</div>
            <textarea
              v-model="generatePrompt"
              @input="promptError = ''"
              rows="3"
              placeholder="例如：适合减脂的午餐食谱，需要高蛋白低热量…"
              :class="{ bad: !!promptError }"
            ></textarea>

            <div v-if="promptError" class="warn">
              <Lightbulb :size="13" /><span>{{ promptError }}</span>
            </div>

            <!-- 身份星域 -->
            <div class="fld-lb">身份星域</div>
            <div class="fg-chips">
              <button
                v-for="tag in personaTags"
                :key="tag"
                class="fg-chip"
                :class="{ on: selectedPersona === tag }"
                @click="selectedPersona = tag"
              >
                {{ tag }}
              </button>
            </div>

            <!-- 炼成按钮 -->
            <button
              class="gold-btn"
              :disabled="!generatePrompt.trim() || isGenerating"
              @click="generateRecipe"
            >
              <Flame :size="13" />{{ isGenerating ? '炼成中，请稍候…' : '开始炼成' }}
            </button>

            <!-- 生成中 loading 反馈：云端生成通常需 30~60 秒，避免用户误以为卡死 -->
            <div v-if="isGenerating" class="loading">
              <span class="spin-ring"></span>
              <div>
                <p class="lt">AI 正在炼制你的专属星宴…</p>
                <p class="ld">通常需要 30 秒~2 分钟，请保持页面打开，勿重复点击</p>
              </div>
            </div>

            <!-- 炼成结果 -->
            <div v-if="generatedRecipe" class="result">
              <div class="r-head">
                <span class="r-cover">{{ generatedRecipe.name?.slice(0, 1) || '食' }}</span>
                <div class="r-tt">
                  <h5>{{ generatedRecipe.name }}</h5>
                  <p>{{ generatedRecipe.description }}</p>
                </div>
              </div>

              <div v-if="generatedRecipe.tags?.length" class="r-tags">
                <i v-for="tag in generatedRecipe.tags" :key="tag">{{ tag }}</i>
              </div>

              <!-- 食材清单（带数据库匹配信息） -->
              <div class="r-sec">
                <h6>星材 · 食材清单</h6>
                <div class="r-ings">
                  <span v-for="ing in generatedRecipe.ingredients" :key="ing.ingredient_name" class="ing">
                    {{ ing.ingredient_name }} {{ ing.amount }}{{ ing.unit }}
                    <em v-if="getIngredientDBLabel(ing.ingredient_name)" class="db">{{ getIngredientDBLabel(ing.ingredient_name) }}</em>
                    <em v-else class="todo">待录入</em>
                  </span>
                </div>
              </div>

              <!-- 烹饪步骤 -->
              <div v-if="generatedRecipe.steps && generatedRecipe.steps.length > 0" class="r-sec">
                <h6>炼制之法 · 烹饪步骤</h6>
                <ol>
                  <li v-for="(step, idx) in generatedRecipe.steps" :key="idx">{{ step }}</li>
                </ol>
              </div>

              <!-- 营养成分简表 -->
              <div class="r-ntr">
                <div class="cell"><b>{{ generatedRecipe.calories }}</b><span>千卡 KCAL</span></div>
                <div class="cell mp"><b>{{ generatedRecipe.protein }}g</b><span>蛋白</span></div>
                <div class="cell mf"><b>{{ generatedRecipe.fat }}g</b><span>脂肪</span></div>
                <div class="cell mc"><b>{{ generatedRecipe.carbs }}g</b><span>碳水</span></div>
                <div class="cell"><b>{{ generatedRecipe.fiber || 0 }}g</b><span>纤维</span></div>
              </div>

              <div class="r-foot">
                <button class="save" @click="saveGeneratedRecipe"><Heart :size="13" />保存到我的食谱</button>
                <button class="ghost" :disabled="!generatePrompt.trim() || isGenerating" @click="generateRecipe">重新炼制</button>
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
import { Sparkles, X, Lightbulb, Flame, Heart } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: boolean
  personaTags: string[]
  /** 由侧栏炼星炉预选的身份星域 */
  initialPersona?: string
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
  } catch (e: any) {
    console.error('生成食谱失败', e)
    promptError.value = e?.response?.data?.message || 'AI生成失败，请稍后重试'
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
    emit('update:modelValue', false)
    emit('generated')
    // 重置内部状态
    generatePrompt.value = ''
    promptError.value = ''
    selectedPersona.value = '普通用户'
    generatedRecipe.value = null
  } catch (e: any) {
    console.error('保存食谱失败', e)
    promptError.value = '保存失败：' + (e?.response?.data?.message || e?.message || '未知错误')
  }
}

// 弹窗打开时重置内部状态（避免上次残留），并应用侧栏预选的身份星域
watch(() => props.modelValue, (val) => {
  if (val) {
    generatePrompt.value = ''
    promptError.value = ''
    selectedPersona.value = props.initialPersona?.trim() ? props.initialPersona : '普通用户'
    generatedRecipe.value = null
  }
})
</script>

<style scoped>
/* ===== AI 炼星 · 无遮罩浅色气泡弹窗 ===== */
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
  position: relative; z-index: 10; width: min(620px, 100%); max-height: 84vh;
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
  display: flex; align-items: center; justify-content: center; color: #B8863B;
  background: radial-gradient(circle at 30% 22%, rgba(184, 134, 59, .18), transparent 70%),
    linear-gradient(160deg, #F5EDDA, #EFE2C4);
  border: 1px solid rgba(184, 134, 59, .4);
  box-shadow: 0 0 14px rgba(184, 134, 59, .18);
}
.bt h4 { font-family: 'Noto Serif SC', serif; font-size: 16px; font-weight: 900; color: #2E2A22; letter-spacing: .05em; }
.bt p { font-size: 10.5px; color: #847C63; margin-top: 3px; }
.bclose {
  margin-left: auto; width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  border: 1px solid rgba(184, 134, 59, .4); background: none; color: #A08F6E;
  display: flex; align-items: center; justify-content: center; transition: .25s; cursor: pointer;
}
.bclose:hover { color: #B8863B; border-color: #B8863B; transform: rotate(90deg); }

/* 主体 */
.bbody { padding: 14px 18px 18px; }
.fld-lb { font-size: 10.5px; letter-spacing: .2em; color: #A0722F; margin: 4px 0 8px; }
textarea {
  width: 100%; resize: none; outline: none;
  background: #F8F2E3; color: #55503F;
  border: 1px solid rgba(184, 134, 59, .35); border-radius: 12px;
  padding: 11px 13px; font-size: 12.5px; line-height: 1.8; font-family: inherit;
  transition: .25s;
}
textarea:focus { border-color: #B8863B; box-shadow: 0 0 0 3px rgba(184, 134, 59, .12); background: #FDFAF3; }
textarea.bad { border-color: #B5442E; }
textarea::placeholder { color: #A08F6E; }

.warn {
  display: flex; align-items: flex-start; gap: 7px; margin-top: 9px;
  padding: 9px 12px; border-radius: 10px; font-size: 11.5px; line-height: 1.7;
  color: #8A6D3B; background: rgba(224, 176, 78, .1); border: 1px solid rgba(224, 176, 78, .45);
}
.warn svg { flex-shrink: 0; margin-top: 2px; }

/* 身份星域芯片 */
.fg-chips { display: flex; gap: 5px; flex-wrap: wrap; }
.fg-chip {
  font-size: 10.5px; padding: 3.5px 12px; border-radius: 99px; cursor: pointer;
  border: 1px solid rgba(184, 134, 59, .35); background: rgba(184, 134, 59, .06);
  color: #8a6d3b; transition: .25s; font-family: inherit;
}
.fg-chip:hover { color: #B8863B; border-color: #B8863B; }
.fg-chip.on {
  color: #14110B; background: linear-gradient(135deg, #E8B973, #B36B2A);
  border-color: transparent; font-weight: 700;
}

.gold-btn {
  margin-top: 14px; width: 100%;
  display: inline-flex; align-items: center; justify-content: center; gap: 7px;
  border: none; border-radius: 11px; padding: 10px 0; cursor: pointer;
  font-size: 12.5px; font-weight: 700; letter-spacing: .08em; font-family: inherit;
  color: #14110B; background: linear-gradient(135deg, #E8B973, #B36B2A);
  transition: .25s; box-shadow: 0 8px 20px -8px rgba(184, 134, 59, .5);
}
.gold-btn:hover:not(:disabled) { filter: brightness(1.08); }
.gold-btn:disabled { opacity: .45; cursor: not-allowed; }

.loading {
  display: flex; align-items: center; gap: 11px; margin-top: 13px;
  padding: 12px 14px; border-radius: 12px;
  border: 1px dashed rgba(184, 134, 59, .35); background: rgba(184, 134, 59, .05);
}
.loading .lt { font-size: 12px; font-weight: 700; color: #2E2A22; }
.loading .ld { font-size: 10.5px; color: #847C63; margin-top: 2px; }
.spin-ring {
  width: 22px; height: 22px; flex-shrink: 0;
  border: 2px solid rgba(184, 134, 59, .25); border-top-color: #B8863B;
  border-radius: 50%; animation: rkSpin .8s linear infinite;
}
@keyframes rkSpin { to { transform: rotate(360deg); } }

/* 炼成结果 */
.result {
  margin-top: 16px; padding: 14px; border-radius: 14px;
  border: 1px solid rgba(184, 134, 59, .4);
  background: linear-gradient(165deg, rgba(184, 134, 59, .1), rgba(184, 134, 59, .03));
  animation: rkRise .5s ease backwards;
}
@keyframes rkRise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
.r-head { display: flex; gap: 11px; align-items: center; }
.r-cover {
  width: 42px; height: 42px; border-radius: 11px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Noto Serif SC', serif; font-size: 19px; font-weight: 900; color: #B8863B;
  background: radial-gradient(circle at 30% 22%, rgba(184, 134, 59, .18), transparent 70%),
    linear-gradient(160deg, #F5EDDA, #EFE2C4);
  border: 1px solid rgba(184, 134, 59, .4);
  text-shadow: 0 2px 10px rgba(184, 134, 59, .3);
}
.r-tt h5 { font-family: 'Noto Serif SC', serif; font-size: 15px; font-weight: 900; color: #2E2A22; }
.r-tt p { font-size: 10.8px; line-height: 1.7; color: #847C63; margin-top: 3px; }
.r-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 9px; }
.r-tags i {
  font-style: normal; font-size: 9px; padding: 1.5px 8px; border-radius: 99px;
  background: rgba(184, 134, 59, .1); color: #8a6d3b; border: 1px solid rgba(184, 134, 59, .28);
}
.r-sec { margin-top: 13px; }
.r-sec h6 {
  font-size: 10.5px; letter-spacing: .2em; color: #A0722F; margin-bottom: 8px;
  display: flex; align-items: center; gap: 7px;
}
.r-sec h6::before { content: ''; width: 14px; height: 1px; background: #B8863B; }
.r-ings { display: flex; gap: 5px; flex-wrap: wrap; }
.r-ings .ing {
  font-style: normal; font-size: 10px; padding: 3px 10px; border-radius: 99px;
  border: 1px solid rgba(184, 134, 59, .3); background: rgba(184, 134, 59, .06); color: #55503F;
}
.r-ings .db { font-style: normal; color: #5E8F5E; margin-left: 3px; font-size: 9px; }
.r-ings .todo { font-style: normal; color: #A08F6E; margin-left: 3px; font-size: 9px; }
.r-sec ol { list-style: none; counter-reset: gstp; }
.r-sec ol li {
  counter-increment: gstp; display: flex; gap: 9px;
  font-size: 11.5px; line-height: 1.85; color: #55503F; padding: 4px 0;
}
.r-sec ol li::before {
  content: counter(gstp, decimal-leading-zero);
  font-family: 'Noto Serif SC', serif; font-size: 11px; font-weight: 900;
  color: #B8863B; flex-shrink: 0; margin-top: 2px;
}
.r-ntr { display: grid; grid-template-columns: repeat(5, 1fr); gap: 7px; margin-top: 13px; }
.r-ntr .cell {
  border: 1px solid rgba(184, 134, 59, .28); border-radius: 10px;
  padding: 9px 4px; text-align: center; background: #F8F2E3;
}
.r-ntr .cell b { font-family: 'Noto Serif SC', serif; font-size: 16px; font-weight: 900; color: #B8863B; display: block; }
.r-ntr .cell span { font-size: 8.5px; color: #847C63; letter-spacing: .08em; }
.r-ntr .cell.mp b { color: #4A6FA5; }
.r-ntr .cell.mf b { color: #C08A2D; }
.r-ntr .cell.mc b { color: #5E8F5E; }
.r-foot { display: flex; gap: 9px; margin-top: 14px; }
.r-foot .save {
  flex: 1; display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  border: none; border-radius: 11px; padding: 9.5px 0; cursor: pointer;
  font-size: 12px; font-weight: 700; letter-spacing: .08em; font-family: inherit;
  color: #14110B; background: linear-gradient(135deg, #E8B973, #B36B2A); transition: .25s;
}
.r-foot .save:hover { filter: brightness(1.08); }
.r-foot .ghost {
  border: 1px solid rgba(184, 134, 59, .4); background: none; border-radius: 11px;
  padding: 0 18px; font-size: 12px; color: #8a6d3b; transition: .25s; cursor: pointer; font-family: inherit;
}
.r-foot .ghost:hover:not(:disabled) { color: #B8863B; border-color: #B8863B; }
.r-foot .ghost:disabled { opacity: .5; cursor: not-allowed; }

@media (max-width: 560px) {
  .r-ntr { grid-template-columns: repeat(3, 1fr); }
}
</style>
