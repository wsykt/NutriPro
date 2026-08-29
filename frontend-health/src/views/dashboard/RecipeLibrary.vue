<template>
  <div class="rk-page">
    <!-- ===== 顶带 ===== -->
    <div class="rk-band">
      <div class="star-crumbs">
        <span class="crumb-wrap">
          <button class="crumb-node" @click="goHome"><span class="nd"><LayoutGrid :size="12" /></span>首页</button>
        </span>
        <span class="crumb-wrap">
          <span class="crumb-link"></span>
          <button class="crumb-node" @click="goHub"><span class="nd"><ChefHat :size="12" /></span>菜谱美食</button>
        </span>
        <span class="crumb-wrap">
          <span class="crumb-link"></span>
          <span class="crumb-node hot"><span class="nd"><UtensilsCrossed :size="13" /></span>星膳书阁</span>
        </span>
      </div>
      <div class="ttl"><UtensilsCrossed :size="15" />星膳书阁</div>
      <span class="date">{{ recipes.length }} 道星宴 · {{ mySavedRecipes.length }} 道私藏</span>
      <div class="rk-seg">
        <button :class="{ on: currentTab === 'all' }" @click="switchTab('all')">全部星宴</button>
        <button :class="{ on: currentTab === 'saved' }" @click="switchTab('saved')">我的收藏</button>
      </div>
      <button class="rk-forge" @click="openGenerate()"><Sparkles :size="12" />AI 炼星 · 生成食谱</button>
    </div>

    <!-- ===== 星轨食域带 ===== -->
    <div class="rk-orbit">
      <svg class="line" viewBox="0 0 1000 86" preserveAspectRatio="none" aria-hidden="true">
        <path d="M0,52 C120,20 210,74 330,44 C450,14 540,70 660,42 C780,16 880,66 1000,40" />
      </svg>
      <button
        v-for="(s, i) in orbitStars"
        :key="s.key"
        class="star-node"
        :class="{ on: selectedTag === s.key }"
        :style="{ left: s.left + '%', animationDelay: (0.1 + i * 0.05) + 's' }"
        @click="selectedTag = s.key"
      >
        <span class="nd">{{ s.ch }}</span><span class="lb">{{ s.lb }}</span>
      </button>
    </div>

    <!-- ===== 主体两栏 ===== -->
    <div class="rk-main">
      <div class="rk-list">
        <!-- 搜索 -->
        <div class="rk-tools">
          <div class="fld">
            <Search :size="13" />
            <input
              v-if="currentTab === 'all'"
              v-model="searchKeyword"
              placeholder="搜索星宴名或食材…"
            />
            <input
              v-else
              v-model="savedSearchKeyword"
              placeholder="搜索收藏的星宴…"
            />
          </div>
          <span class="rk-count">
            {{ currentTab === 'all' ? `共 ${filteredRecipes.length} 道` : `私藏 ${filteredSaved.length} 道` }}
          </span>
        </div>

        <!-- 全部星宴卡列 -->
        <div v-if="currentTab === 'all' && filteredRecipes.length > 0" class="rk-cards">
          <RecipeCard
            v-for="(recipe, i) in filteredRecipes"
            :key="recipe.id"
            :recipe="recipe"
            :style="{ animationDelay: cardDelay(i) }"
            @view="viewRecipe"
          />
        </div>

        <!-- 我的收藏卡列 -->
        <div v-else-if="currentTab === 'saved' && filteredSaved.length > 0" class="rk-cards">
          <RecipeCard
            v-for="(recipe, i) in filteredSaved"
            :key="recipe.id"
            :recipe="recipe"
            show-delete
            :style="{ animationDelay: cardDelay(i) }"
            @view="viewRecipe"
            @delete="deleteMyRecipe"
          />
        </div>

        <!-- 加载中 -->
        <div v-else-if="loading" class="rk-state">
          <div class="spin-ring"></div>
          <p class="st-ds">正在点亮书阁的星宴…</p>
        </div>
        <!-- 筛选无结果 -->
        <div v-else-if="(currentTab === 'all' && recipes.length > 0) || (currentTab === 'saved' && mySavedRecipes.length > 0)" class="rk-state">
          <BookOpen :size="26" class="st-ic" />
          <p class="st-tt">此星域暂无星宴</p>
          <button class="gold-btn" @click="clearFilters">清除筛选</button>
        </div>
        <!-- 空库 -->
        <div v-else-if="currentTab === 'all'" class="rk-state">
          <BookOpen :size="26" class="st-ic" />
          <p class="st-tt">书阁尚无星宴</p>
          <p class="st-ds">点击下方按钮，由 AI 炼星快速创建</p>
          <button class="gold-btn" @click="openGenerate()"><Sparkles :size="12" />AI 炼星 · 生成食谱</button>
        </div>
        <div v-else class="rk-state">
          <Archive :size="26" class="st-ic" />
          <p class="st-tt">星匣尚无私藏</p>
          <p class="st-ds">浏览全部星宴，把合意的收入星匣</p>
          <button class="gold-btn" @click="switchTab('all')">浏览全部星宴</button>
        </div>
      </div>

      <!-- ===== 侧栏 ===== -->
      <aside class="rk-side">
        <div class="side-h"><Sparkles :size="11" />ASTRAL 炼星炉</div>
        <div class="forge-card">
          <div class="orb"><span class="ring"></span><span class="core"><Sparkles :size="15" /></span></div>
          <b>以体质为引，炼一道星宴</b>
          <p>选择身份星域，AI 将按体质与目标生成专属食谱。</p>
          <div class="fg-chips">
            <button
              v-for="p in personaTags"
              :key="p"
              class="fg-chip"
              :class="{ on: forgePersona === p }"
              @click="forgePersona = p"
            >{{ p }}</button>
          </div>
          <button class="fg-btn" @click="openGenerate(forgePersona)"><Flame :size="12" />开始炼成</button>
        </div>

        <template v-if="todayPick">
          <div class="side-h"><ChefHat :size="11" />今日星宴 · 星厨推荐</div>
          <div class="pick reco" @click="viewRecipe(todayPick)">
            <div class="ph"><b>{{ todayPick.name }}</b><span>{{ todayPick.calories }} kcal</span></div>
            <p>{{ todayPick.description }}</p>
            <span class="reco-tag">星厨之选</span>
          </div>
        </template>

        <div class="side-h"><Archive :size="11" />收藏星匣</div>
        <div class="vault">
          <div class="vt">
            <b>私藏 {{ mySavedRecipes.length }} 道</b>
            <button class="vt-link" @click="switchTab('saved')">查看全部</button>
          </div>
          <div v-for="r in vaultRows" :key="r.id" class="row" @click="viewRecipe(r)">
            <span class="d">{{ r.name?.slice(0, 1) || '食' }}</span>
            <span class="vn">{{ r.name }}</span>
            <em>{{ r.calories }} kcal</em>
          </div>
          <div v-if="mySavedRecipes.length === 0" class="vault-empty">星匣尚空，浏览星宴并收藏</div>
        </div>

        <div class="side-note">带 <b>✦</b> 角标的星宴由 AI 炼星生成，收藏后与系统食谱同列。</div>
      </aside>
    </div>

    <!-- ===== Toast ===== -->
    <Teleport to="body">
      <Transition name="rk-toast">
        <div v-if="toastMsg" class="rk-toast"><Sparkles :size="13" />{{ toastMsg }}</div>
      </Transition>
    </Teleport>

    <!-- AI生成食谱气泡弹窗 -->
    <RecipeGenerateDialog
      v-model="showGenerateDialog"
      :persona-tags="personaTags"
      :initial-persona="pendingPersona"
      @generated="onGenerated"
    />

    <!-- 食谱详情气泡弹窗 -->
    <RecipeDetailDialog
      v-model="showDetailDialog"
      :recipe="selectedRecipe"
      @save="saveRecipe"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { useRecipeStore } from '@/stores/recipe'
import { RECIPE_TAGS, RECIPE_PERSONA_TAGS } from '@/constants'
import { UtensilsCrossed, Sparkles, Search, Flame, ChefHat, Archive, BookOpen, LayoutGrid } from 'lucide-vue-next'
import RecipeCard from './RecipeCard.vue'
import RecipeGenerateDialog from './RecipeGenerateDialog.vue'
import RecipeDetailDialog from './RecipeDetailDialog.vue'

const route = useRoute()
const router = useRouter()
const recipeStore = useRecipeStore()

// 星轨面包屑：首页 / 菜谱美食中转站
function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'recipe' } }) }

const recipeTags = RECIPE_TAGS as unknown as string[]
const personaTags = RECIPE_PERSONA_TAGS as unknown as string[]

const currentTab = ref<'all' | 'saved'>('all')
const searchKeyword = ref('')
const savedSearchKeyword = ref('')
const selectedTag = ref('')
const loading = ref(false)
const recipes = ref<any[]>([])
const mySavedRecipes = ref<any[]>([])
const showGenerateDialog = ref(false)
const showDetailDialog = ref(false)
const selectedRecipe = ref<any>(null)
const forgePersona = ref('普通用户')
const pendingPersona = ref('')

/* ===== 星轨食域带：全部 ✦ + 9 大标签 ===== */
const orbitStars = computed(() => {
  const stars = [
    { key: '', ch: '✦', lb: '全部' },
    ...recipeTags.map(t => ({ key: t, ch: t.slice(0, 1), lb: t }))
  ]
  const n = stars.length
  return stars.map((s, i) => ({ ...s, left: 4 + (i * 92) / (n - 1) }))
})

/** 食域 × 关键词 双重过滤 */
function filterList(list: any[], kw: string) {
  let out = list
  if (selectedTag.value) {
    out = out.filter(r => r.tags?.includes(selectedTag.value))
  }
  const k = kw.trim().toLowerCase()
  if (k) {
    out = out.filter((r: any) =>
      r.name?.toLowerCase().includes(k) ||
      r.description?.toLowerCase().includes(k) ||
      (Array.isArray(r.ingredients) && r.ingredients.some((ing: any) =>
        (ing.ingredientName || ing.ingredient_name || ing.name || '').toLowerCase().includes(k)
      ))
    )
  }
  return out
}

const filteredRecipes = computed(() => filterList(recipes.value, searchKeyword.value))
const filteredSaved = computed(() => filterList(mySavedRecipes.value, savedSearchKeyword.value))

/** 今日星宴：取列表首位作星厨推荐 */
const todayPick = computed(() => recipes.value[0] || null)
/** 星匣侧栏最多展示 4 道 */
const vaultRows = computed(() => mySavedRecipes.value.slice(0, 4))

/** 卡片入场：对角线波次延迟 */
function cardDelay(i: number) {
  return (0.14 + Math.floor(i / 2) * 0.09 + (i % 2) * 0.05).toFixed(2) + 's'
}

function clearFilters() {
  selectedTag.value = ''
  searchKeyword.value = ''
  savedSearchKeyword.value = ''
}

/* ===== Toast ===== */
const toastMsg = ref('')
let toastTimer: ReturnType<typeof setTimeout> | null = null
function showToast(msg: string) {
  toastMsg.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastMsg.value = '' }, 2600)
}

/* ===== Tab 切换（与 ?tab= 双向同步，保持历史链接） ===== */
function switchTab(tab: 'all' | 'saved') {
  currentTab.value = tab
  router.replace({ query: { ...route.query, tab } })
}

/** 转换系统食谱格式: recipeId→id, recipeName→name, tags字符串→数组 */
function normalizeRecipe(r: any): any {
  return {
    id: r.recipeId ?? r.id,
    name: r.recipeName ?? r.name ?? '',
    description: r.description ?? '',
    calories: r.calories ?? 0,
    protein: r.protein ?? 0,
    fat: r.fat ?? 0,
    carbs: r.carbs ?? 0,
    fiber: r.fiber ?? 0,
    tags: typeof r.tags === 'string' ? r.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : (r.tags || []),
    ingredients: r.ingredients || r.recipeIngredients || [],
    originalId: r.originalId,
    isSaved: r.isSaved
  }
}

/** 转换收藏食谱格式 */
function normalizeSavedRecipe(saved: any): any {
  let nutrition: any = {}
  if (saved.nutritionSummary) {
    try {
      nutrition = typeof saved.nutritionSummary === 'string' ? JSON.parse(saved.nutritionSummary) : saved.nutritionSummary
    } catch { nutrition = {} }
  }
  let ingredients: any[] = []
  if (saved.ingredients) {
    try {
      ingredients = typeof saved.ingredients === 'string' ? JSON.parse(saved.ingredients) : saved.ingredients
    } catch { ingredients = [] }
  }
  let steps: string[] = []
  if (saved.steps) {
    try {
      steps = typeof saved.steps === 'string' ? JSON.parse(saved.steps) : saved.steps
    } catch { steps = [] }
  }
  return {
    id: saved.id,
    name: saved.title,
    description: steps.length > 0 ? steps[0] : (nutrition.description || ''),
    steps: steps,
    calories: nutrition.calories || 0,
    protein: nutrition.protein || 0,
    fat: nutrition.fat || 0,
    carbs: nutrition.carbs || 0,
    fiber: nutrition.fiber || 0,
    tags: nutrition.tags || [],
    ingredients: ingredients,
    isSaved: true,
    originalId: saved.id,
    source: saved.source || ''
  }
}

const loadRecipes = async () => {
  loading.value = true
  try {
    const systemRecipes = await api.recipe.list()
    let allRecipes = systemRecipes.map(normalizeRecipe)

    try {
      const savedRecipesData = await api.recipe.mySaved()
      const savedRecipes = savedRecipesData
        .map(normalizeSavedRecipe)
        .filter((r: any) => r.source === 'generated')
      allRecipes = [...allRecipes, ...savedRecipes]
    } catch { /* ignore */ }

    recipes.value = allRecipes
  } catch (e) {
    console.error('加载食谱失败', e)
  } finally {
    loading.value = false
  }
}

const loadMySavedRecipes = async () => {
  try {
    await recipeStore.fetchFavorites()
    const data = await api.recipe.mySaved()
    mySavedRecipes.value = data.map(normalizeSavedRecipe)
  } catch (e) {
    console.error('加载我的食谱失败', e)
  }
}

const deleteMyRecipe = async (id: number) => {
  if (!confirm('确定删除这条食谱？')) return
  try {
    await api.recipe.deleteSaved(id)
    await loadMySavedRecipes()
    await loadRecipes()
    showToast('已从星匣移除')
  } catch (e: any) {
    console.error('删除食谱失败', e)
    showToast('删除失败：' + (e?.response?.data?.message || e?.message || '未知错误'))
  }
}

const viewRecipe = (recipe: any) => {
  selectedRecipe.value = recipe
  showDetailDialog.value = true
}

const saveRecipe = async (recipe: any) => {
  if (!recipe) return
  const wasSaved = !!recipe.isSaved
  try {
    await recipeStore.toggleFavorite(recipe)
    showDetailDialog.value = false
    await Promise.all([loadRecipes(), loadMySavedRecipes()])
    showToast(wasSaved ? '已移出星匣' : '「' + recipe.name + '」已收入星匣')
  } catch (e: any) {
    console.error('保存食谱失败', e)
    showToast('保存失败：' + (e?.response?.data?.message || e?.message || '未知错误'))
  }
}

/** AI 炼星保存成功后刷新列表 */
const onGenerated = async () => {
  await Promise.all([loadRecipes(), loadMySavedRecipes()])
  showToast('星宴已炼成，收入「全部星宴」')
}

/** 打开炼星弹窗，可携带侧栏预选的身份星域 */
function openGenerate(persona?: string) {
  pendingPersona.value = persona || ''
  showGenerateDialog.value = true
}

watch([showGenerateDialog, showDetailDialog], (newVal) => {
  if (newVal[0] || newVal[1]) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

onMounted(async () => {
  // 支持 /dashboard/recipe-library?tab=saved 深链
  if (route.query.tab === 'saved') currentTab.value = 'saved'
  await Promise.all([loadRecipes(), loadMySavedRecipes()])
})
</script>

<style scoped>
/* ================= P10-A 星膳书阁 ================= */
.rk-page {
  font-family: 'Noto Sans SC', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background:
    radial-gradient(ellipse at 78% -8%, rgba(217, 162, 74, .14), transparent 44%),
    linear-gradient(168deg, #1C1710, #12100A 62%);
  border-radius: 18px;
  color: #F0E2C4;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 620px;
}
.rk-page button { font-family: inherit; cursor: pointer; }

/* 入场动效（backwards：结束后归还 transform，hover 不受影响） */
@keyframes rkRise {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: none; }
}

/* ===== 顶带 ===== */
.rk-band {
  display: flex; align-items: center; gap: 13px; flex-wrap: wrap;
  padding: 15px 24px 12px;
  border-bottom: 1px solid rgba(217, 162, 74, .2);
  animation: rkRise .7s ease backwards;
}
.rk-band .ttl {
  font-size: 15px; font-weight: 900; letter-spacing: .1em; color: #F6EAD6;
  display: inline-flex; align-items: center; gap: 7px;
}
.rk-band .ttl svg { color: #E8B973; }
/* ---- 星轨面包屑导航 ---- */
.star-crumbs { display: flex; align-items: center; flex-shrink: 0; }
.crumb-wrap { display: flex; align-items: center; }
.crumb-link { width: 42px; height: 0; border-top: 1.5px dashed rgba(184, 134, 59, 0.45); margin: 0 5px; }
.crumb-node {
  display: inline-flex; align-items: center; gap: 7px;
  font-size: 11.5px; color: #8C7A5E;
  background: none; border: none; padding: 0;
  font-family: inherit; letter-spacing: 0.04em;
}
.crumb-node .nd {
  width: 22px; height: 22px; border-radius: 50%;
  border: 1px solid rgba(217, 162, 74, 0.4); color: #8C7A5E;
  display: flex; align-items: center; justify-content: center;
  background: rgba(24, 19, 12, 0.9); transition: 0.25s;
}
button.crumb-node { cursor: pointer; transition: color 0.25s ease; }
button.crumb-node:hover { color: #E8B973; }
.crumb-node.hot { color: #F6EAD6; font-weight: 700; }
.crumb-node.hot .nd {
  color: #E8B973; border-color: #E8B973;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  box-shadow: 0 0 14px rgba(217, 162, 74, 0.45);
}
.rk-band .date {
  font-size: 10.5px; color: #B9A78A; letter-spacing: .06em;
  border: 1px solid rgba(217, 162, 74, .3); background: rgba(217, 162, 74, .08);
  border-radius: 999px; padding: 3px 10px;
}
.rk-seg {
  margin-left: auto; display: flex;
  border: 1px solid rgba(217, 162, 74, .3); border-radius: 99px;
  padding: 2.5px; background: rgba(24, 19, 12, .7);
}
.rk-seg button {
  border: none; background: none; font-size: 11px; padding: 4.5px 14px;
  border-radius: 99px; color: #9A8A6C; transition: .25s; letter-spacing: .04em;
}
.rk-seg button.on { color: #14110B; background: linear-gradient(135deg, #E8B973, #B36B2A); font-weight: 700; }
.rk-forge {
  display: inline-flex; align-items: center; gap: 6px;
  border: 1px solid rgba(232, 185, 115, .55); border-radius: 99px;
  padding: 5.5px 15px; font-size: 11.5px; font-weight: 700; letter-spacing: .06em;
  color: #14110B; background: linear-gradient(135deg, #E8B973, #B36B2A);
  transition: .25s; box-shadow: 0 6px 18px -8px rgba(217, 162, 74, .6);
}
.rk-forge:hover { filter: brightness(1.08); transform: translateY(-1px); }

/* ===== 星轨食域带 ===== */
.rk-orbit {
  position: relative; height: 86px;
  border-bottom: 1px solid rgba(217, 162, 74, .14);
  overflow: hidden; flex-shrink: 0;
  animation: rkRise .7s ease .08s backwards;
}
.rk-orbit .line { position: absolute; inset: 0; width: 100%; height: 100%; }
.rk-orbit .line path {
  fill: none; stroke: rgba(217, 162, 74, .32); stroke-width: 1.1;
  stroke-dasharray: 4 7; vector-effect: non-scaling-stroke;
}
/* 星轨数据球入场：关键帧内链式保留 -50% 居中位移，避免动画期间丢失定位偏移 */
@keyframes rkStarIn {
  from { opacity: 0; transform: translate(-50%, -50%) translateY(16px); }
  to { opacity: 1; transform: translate(-50%, -50%); }
}
.star-node {
  position: absolute; top: 50%; transform: translate(-50%, -50%);
  display: flex; flex-direction: column; align-items: center; gap: 5px;
  background: none; border: none; z-index: 3;
  animation: rkStarIn .6s ease backwards;
}
.star-node .nd {
  width: 30px; height: 30px; border-radius: 50%;
  border: 1px solid rgba(217, 162, 74, .45); color: #9A8A6C;
  display: flex; align-items: center; justify-content: center;
  background: rgba(24, 19, 12, .92); transition: .3s;
  font-size: 10.5px; font-weight: 700; letter-spacing: .02em;
}
.star-node .lb {
  font-size: 10px; color: #8C7A5E; letter-spacing: .08em;
  transition: .3s; white-space: nowrap;
}
.star-node:hover .nd { color: #E8B973; border-color: #E8B973; box-shadow: 0 0 14px rgba(217, 162, 74, .4); }
.star-node.on .nd {
  color: #14110B; background: linear-gradient(135deg, #E8B973, #B36B2A);
  border-color: #E8B973; box-shadow: 0 0 18px rgba(217, 162, 74, .55);
}
.star-node.on .lb { color: #E8B973; }

/* ===== 主体两栏 ===== */
.rk-main {
  flex: 1; display: grid; grid-template-columns: 1fr 264px; gap: 0; min-height: 0;
  animation: rkRise .7s ease .16s backwards;
  /* 浅芯暖纸：细点纸纹 + 米纸底 */
  background:
    radial-gradient(rgba(46, 42, 34, .05) 1px, transparent 1.2px) 0 0 / 7px 7px,
    #FDFAF3;
  color: #55503F;
}
.rk-list { padding: 16px 20px 20px; min-width: 0; }
.rk-side {
  border-left: 1px solid rgba(184, 134, 59, .28);
  padding: 16px 16px 20px; background: #F8F2E3;
}

/* 搜索行 */
.rk-tools { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.rk-tools .fld {
  flex: 1; display: flex; align-items: center; gap: 8px;
  border: 1px solid rgba(184, 134, 59, .4); border-radius: 99px;
  padding: 0 14px; background: #F8F2E3; transition: .25s;
}
.rk-tools .fld:focus-within { border-color: #B8863B; box-shadow: 0 0 0 3px rgba(184, 134, 59, .15); }
.rk-tools .fld svg { color: #A08F6E; flex-shrink: 0; }
.rk-tools input {
  flex: 1; background: none; border: none; outline: none;
  color: #2E2A22; font-size: 12px; padding: 9px 0; font-family: inherit;
}
.rk-tools input::placeholder { color: #A89C80; }
.rk-count { font-size: 10.5px; color: #847C63; white-space: nowrap; }

/* 卡片列 */
.rk-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

/* 状态 */
.rk-state { text-align: center; padding: 52px 20px; color: #847C63; }
.rk-state .st-ic { color: rgba(184, 134, 59, .55); }
.rk-state .st-tt { font-size: 13.5px; color: #2E2A22; margin-top: 10px; font-weight: 700; }
.rk-state .st-ds { font-size: 11.5px; margin-top: 6px; color: #A08F6E; }
.rk-state .gold-btn {
  margin-top: 14px; display: inline-flex; align-items: center; gap: 6px;
  font-size: 12px; font-weight: 700; letter-spacing: .04em; font-family: inherit;
  color: #FDFAF3; background: linear-gradient(135deg, #C99A4B, #A0722F);
  border: none; border-radius: 999px; padding: 7px 16px; transition: .25s; cursor: pointer;
  box-shadow: 0 8px 20px -8px rgba(160, 114, 47, .6);
}
.rk-state .gold-btn:hover { filter: brightness(1.08); }
.spin-ring {
  width: 30px; height: 30px; margin: 0 auto;
  border: 2px solid rgba(184, 134, 59, .25); border-top-color: #B8863B;
  border-radius: 50%; animation: rkSpin .8s linear infinite;
}
@keyframes rkSpin { to { transform: rotate(360deg); } }

/* ===== 侧栏 ===== */
.side-h {
  font-size: 10.5px; letter-spacing: .2em; color: #A0722F;
  margin-bottom: 10px; display: flex; align-items: center; gap: 6px;
}
/* 炼星炉（浅芯金晕） */
.forge-card {
  border: 1px solid rgba(184, 134, 59, .5); border-radius: 14px;
  padding: 14px; margin-bottom: 16px; position: relative; overflow: hidden;
  background: linear-gradient(165deg, rgba(184, 134, 59, .16), rgba(184, 134, 59, .05));
}
.forge-card .orb { position: relative; width: 44px; height: 44px; margin-bottom: 10px; }
.forge-card .orb .core {
  position: absolute; inset: 7px; border-radius: 50%;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(184, 134, 59, .6);
  display: flex; align-items: center; justify-content: center;
  color: #E8B973; box-shadow: 0 0 16px rgba(184, 134, 59, .45);
}
.forge-card .orb .ring {
  position: absolute; inset: 0; border-radius: 50%;
  border: 1px dashed rgba(184, 134, 59, .5);
  animation: rkOrbitSpin 14s linear infinite;
}
.forge-card .orb .ring::after {
  content: ''; position: absolute; top: -3px; left: 50%;
  width: 5px; height: 5px; border-radius: 50%;
  background: #B8863B; box-shadow: 0 0 8px rgba(184, 134, 59, .9);
}
@keyframes rkOrbitSpin { to { transform: rotate(360deg); } }
.forge-card b { font-size: 12.5px; color: #2E2A22; letter-spacing: .06em; display: block; }
.forge-card p { font-size: 10.5px; line-height: 1.75; color: #847C63; margin-top: 5px; }
.fg-chips { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 9px; }
.fg-chip {
  font-size: 9.5px; padding: 2px 9px; border-radius: 99px; cursor: pointer;
  border: 1px solid rgba(184, 134, 59, .35); background: rgba(184, 134, 59, .07);
  color: #8a6d3b; transition: .25s; font-family: inherit;
}
.fg-chip:hover { color: #B8863B; border-color: #B8863B; }
.fg-chip.on { color: #FDFAF3; background: linear-gradient(135deg, #C99A4B, #A0722F); border-color: transparent; font-weight: 700; }
.fg-btn {
  margin-top: 11px; width: 100%;
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  border: none; border-radius: 10px; padding: 8.5px 0; cursor: pointer;
  font-size: 11.5px; font-weight: 700; letter-spacing: .08em; font-family: inherit;
  color: #FDFAF3; background: linear-gradient(135deg, #C99A4B, #A0722F);
  transition: .25s; box-shadow: 0 8px 20px -8px rgba(160, 114, 47, .6);
}
.fg-btn:hover { filter: brightness(1.08); }

/* 今日星宴 */
.pick {
  border: 1px solid rgba(184, 134, 59, .3); border-radius: 12px;
  padding: 11px 12px; margin-bottom: 16px; background: rgba(184, 134, 59, .05);
  transition: .3s; cursor: pointer;
}
.pick:hover { border-color: rgba(184, 134, 59, .8); background: rgba(184, 134, 59, .1); }
.pick.reco {
  border-color: rgba(184, 134, 59, .65);
  background: linear-gradient(160deg, rgba(184, 134, 59, .14), rgba(184, 134, 59, .04));
}
.pick .ph { display: flex; align-items: baseline; gap: 7px; }
.pick .ph b { font-size: 12.5px; color: #2E2A22; font-weight: 700; }
.pick .ph span { font-size: 9.5px; color: #A08F6E; margin-left: auto; white-space: nowrap; }
.pick p {
  font-size: 10.5px; line-height: 1.7; color: #847C63; margin-top: 4px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.pick .reco-tag {
  display: inline-block; margin-top: 7px; font-size: 9px; font-weight: 700;
  letter-spacing: .1em; color: #FDFAF3;
  background: linear-gradient(135deg, #C99A4B, #A0722F);
  padding: 2px 9px; border-radius: 99px;
}

/* 收藏星匣 */
.vault {
  border: 1px solid rgba(184, 134, 59, .3); border-radius: 12px;
  padding: 11px 12px; background: rgba(184, 134, 59, .05);
}
.vault .vt { display: flex; align-items: baseline; gap: 7px; margin-bottom: 4px; }
.vault .vt b { font-size: 12px; color: #2E2A22; }
.vault .vt-link {
  margin-left: auto; background: none; border: none; cursor: pointer;
  font-size: 9.5px; color: #B8863B; transition: .2s; font-family: inherit;
}
.vault .vt-link:hover { color: #A0722F; }
.vault .row {
  display: flex; align-items: center; gap: 8px; padding: 6px 0;
  border-top: 1px dashed rgba(184, 134, 59, .28);
  font-size: 11px; color: #55503F; cursor: pointer; transition: .2s;
}
.vault .row:hover { color: #B8863B; padding-left: 3px; }
.vault .row .d {
  width: 18px; height: 18px; border-radius: 6px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Noto Serif SC', serif; font-size: 10px; font-weight: 700;
  color: #B8863B; background: rgba(184, 134, 59, .14); border: 1px solid rgba(184, 134, 59, .3);
}
.vault .row .vn { min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.vault .row em { font-style: normal; margin-left: auto; font-size: 9.5px; color: #A08F6E; white-space: nowrap; }
.vault-empty { padding: 8px 0 2px; font-size: 10.5px; color: #A08F6E; }
.side-note {
  margin-top: 12px; padding: 10px 11px; border-radius: 10px;
  border: 1px dashed rgba(184, 134, 59, .4);
  font-size: 10.5px; line-height: 1.8; color: #847C63;
}
.side-note b { color: #B8863B; }

/* ===== Toast（无遮罩 · 气泡弹出） ===== */
.rk-toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 60;
  display: inline-flex; align-items: center; gap: 8px;
  border: 1px solid rgba(184, 134, 59, .55); border-radius: 99px;
  padding: 9px 18px; max-width: min(480px, 88vw);
  background: #FDFAF3;
  box-shadow: 0 14px 34px -12px rgba(46, 42, 34, .4);
  font-size: 11.5px; color: #55503F;
}
.rk-toast svg { color: #B8863B; flex-shrink: 0; }
.rk-toast-enter-active { animation: rkToastPop .45s cubic-bezier(.34, 1.56, .64, 1); }
.rk-toast-leave-active { transition: opacity .25s ease, transform .25s ease; }
.rk-toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(10px) scale(.9); }
@keyframes rkToastPop {
  from { opacity: 0; transform: translateX(-50%) scale(.7) translateY(12px); }
  to { opacity: 1; transform: translateX(-50%) scale(1); }
}

/* ===== 响应式 ===== */
@media (max-width: 1020px) {
  .rk-main { grid-template-columns: 1fr; }
  .rk-side {
    border-left: none; border-top: 1px solid rgba(184, 134, 59, .28);
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
  }
  .side-h, .rk-side .side-note { grid-column: 1 / -1; }
  .forge-card, .pick, .vault { margin-bottom: 0; }
}
@media (max-width: 760px) {
  .rk-cards { grid-template-columns: 1fr; }
  .rk-side { grid-template-columns: 1fr; }
  .rk-band .date { display: none; }
  .star-crumbs { display: none; }
  .rk-seg { margin-left: 0; }
  .star-node .lb { display: none; }
  .star-node .nd { width: 24px; height: 24px; font-size: 9px; }
}
</style>
