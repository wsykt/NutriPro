<template>
  <div class="min-h-screen bg-morandi-bg/40">
    <div v-if="loading" class="py-32 text-center text-morandi-lightText text-sm">预览加载中…</div>
    <div v-else-if="errorMsg" class="py-20 text-center">
      <p class="text-red-600 mb-2">{{ errorMsg }}</p>
      <p class="text-morandi-lightText text-xs mb-4">
        可能是预览令牌已过期，请从管理员流程演示页重新点击【预览】按钮。
      </p>
      <button @click="() => window.close()" class="px-4 py-1.5 text-sm rounded-lg bg-morandi-accent text-white hover:bg-morandi-accent/90">
        关闭页面
      </button>
    </div>
    <div v-else class="previewer-root mx-auto">
      <!-- 顶部提示条（仅匿名/新标签页显示，嵌入 iframe 时父页面隐藏该条） -->
      <div v-if="showTopBar" class="px-5 py-3 border-b border-morandi-soft/60 bg-white/80 backdrop-blur flex items-center justify-between">
        <div class="text-sm text-morandi-text">
          <span class="inline-flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-morandi-accent" />
            <span class="text-morandi-lightText">预览模式 ·</span>
            <span class="font-semibold">{{ funcLabel }}</span>
            <span v-if="snap?.title" class="text-morandi-lightText">· {{ snap.title }}</span>
          </span>
        </div>
        <div class="text-xs text-morandi-lightText">
          数据来源：快照 #{{ snap?.id }} · 此预览仅用于效果校验
        </div>
      </div>

      <!-- 1:1 视觉权威视图 → 根据 funcType 分发到 7 个 viewer -->
      <ArticleViewer v-if="funcType==='article'" :payload="payload" />
      <RecipeViewer v-else-if="funcType==='recipe'" :payload="payload" />
      <TrainingViewer v-else-if="funcType==='training'" :payload="payload" />
      <ConsultViewer v-else-if="funcType==='consult'" :payload="payload" />
      <WeeklyReportViewer v-else-if="funcType==='weeklyReport'" :payload="payload" />
      <DietPlanViewer v-else-if="funcType==='dietPlan'" :payload="payload" />
      <NutritionViewer v-else-if="funcType==='nutrition'" :payload="payload" />
      <div v-else class="p-8 text-morandi-lightText">未知的 funcType：{{ funcType }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import ArticleViewer from '@/views/preview/components/ArticleViewer.vue'
import RecipeViewer from '@/views/preview/components/RecipeViewer.vue'
import TrainingViewer from '@/views/preview/components/TrainingViewer.vue'
import ConsultViewer from '@/views/preview/components/ConsultViewer.vue'
import WeeklyReportViewer from '@/views/preview/components/WeeklyReportViewer.vue'
import DietPlanViewer from '@/views/preview/components/DietPlanViewer.vue'
import NutritionViewer from '@/views/preview/components/NutritionViewer.vue'
import * as PreviewApi from '@/api/preview'

interface Props {
  /** 管理员内嵌模式：父组件直接把 payload 传进来，不请求后端 */
  payload?: any
  /** 管理员内嵌模式：指定 funcType */
  funcType?: string
  /** 管理员内嵌模式：快照对象 */
  snap?: any
  /** 是否显示顶部"预览模式"信息条 */
  showTopBar?: boolean
}
const props = withDefaults(defineProps<Props>(), { showTopBar: true })

const emit = defineEmits<{ (e: 'loaded', snap: any): void }>()

const route = useRoute()
const loading = ref(false)
const errorMsg = ref('')
const snap = ref<any>(props.snap || null)
const innerPayload = ref<any>(props.payload || null)
const innerFuncType = ref<string>(props.funcType || '')

const payload = computed(() => innerPayload.value || snap.value?.payload)
const funcType = computed(() => innerFuncType.value || snap.value?.funcType || route.query.funcType as string || '')

const FUNC_LABEL: Record<string, string> = {
  article: '科普文章',
  recipe: '食谱推荐',
  training: '训练方案',
  consult: 'AI 健康咨询',
  weeklyReport: '健康周报',
  dietPlan: '膳食计划',
  nutrition: '营养分析'
}
const funcLabel = computed(() => FUNC_LABEL[funcType.value] || funcType.value)

async function loadFromRoute() {
  // 两种路由：
  //  1) /admin/preview/open/:id?tok=...  → 匿名一次性 token 拉快照
  //  2) /admin/preview/:funcType          → 管理员内嵌：读 sessionStorage
  const idMatch = (route.params.id as string) || ''
  const tok = (route.query.tok as string) || ''
  if (idMatch && /^\d+$/.test(idMatch) && tok) {
    loading.value = true
    errorMsg.value = ''
    try {
      const r = await PreviewApi.openSnapshot(Number(idMatch), tok)
      snap.value = r
      emit('loaded', r)
    } catch (e: any) {
      errorMsg.value = e?.response?.data?.message || e?.message || '打开预览失败'
    } finally {
      loading.value = false
    }
    return
  }
  const ft = (route.params.funcType as string) || route.query.funcType as string
  if (ft) {
    innerFuncType.value = ft
    // 从 sessionStorage 读：管理员 iframe 内嵌时父页面先把 payload 存进去
    const key = 'admin_preview_payload__' + ft
    const raw = sessionStorage.getItem(key)
    if (raw) {
      try {
        innerPayload.value = JSON.parse(raw)
        snap.value = innerPayload.value?.__snap || null
        emit('loaded', snap.value)
      } catch { /* ignore */ }
    }
  }
}

onMounted(loadFromRoute)
watch(
  () => [route.fullPath, props.payload, props.funcType, props.snap],
  () => {
    if (props.payload) innerPayload.value = props.payload
    if (props.funcType) innerFuncType.value = props.funcType
    if (props.snap) snap.value = props.snap
    if (!props.payload && !props.snap) loadFromRoute()
  }
)
</script>
