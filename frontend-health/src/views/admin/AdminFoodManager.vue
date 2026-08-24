<template>
  <div class="glass rounded-2xl p-6 min-h-[560px] flex flex-col">
    <div class="flex items-center justify-between mb-4 flex-shrink-0">
      <h3 class="text-lg font-semibold text-morandi-text">食物管理</h3>
      <span class="text-xs text-morandi-lightText">共 {{ allFoods.length }} 条 · 当前显示 {{ filteredFoods.length }} 条</span>
    </div>

    <!-- 筛选栏 -->
    <div class="flex flex-wrap items-center gap-2 mb-4 flex-shrink-0">
      <select
        v-model="foodStatusFilter"
        class="px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
      >
        <option value="">全部状态</option>
        <option value="approved">已审核</option>
        <option value="pending">待审核</option>
        <option value="rejected">已拒绝</option>
      </select>

      <select
        v-model="foodCategoryFilter"
        class="px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
      >
        <option value="">全部分类</option>
        <option v-for="c in foodCategories" :key="c" :value="c">{{ c }}</option>
      </select>

      <input
        v-model="foodKeyword"
        type="text"
        placeholder="搜索食物名..."
        class="flex-1 min-w-[200px] px-3 py-2 rounded-lg border border-morandi-soft bg-white text-sm text-morandi-text outline-none focus:border-morandi-accent"
      />
      <button @click="loadAllFoods" class="px-3 py-2 rounded-lg bg-morandi-soft text-morandi-text text-sm hover:bg-morandi-accent hover:text-white transition">刷新</button>
    </div>

    <div v-if="foodLoading" class="text-center text-sm text-morandi-lightText py-16 flex-shrink-0">加载中...</div>

    <div v-else class="flex-1 overflow-y-auto food-table-body rounded-xl min-h-0">
      <table class="min-w-full text-sm text-left text-morandi-text">
        <thead class="text-xs text-morandi-lightText sticky top-0" style="background: rgba(248,246,244,0.95); z-index: 1;">
          <tr>
            <th class="px-3 py-3 font-semibold">名称</th>
            <th class="px-3 py-3 font-semibold">分类</th>
            <th class="px-3 py-3 font-semibold text-right">热量</th>
            <th class="px-3 py-3 font-semibold text-right">蛋白</th>
            <th class="px-3 py-3 font-semibold text-right">脂肪</th>
            <th class="px-3 py-3 font-semibold text-right">碳水</th>
            <th class="px-3 py-3 font-semibold text-right">GI</th>
            <th class="px-3 py-3 font-semibold text-right">钙</th>
            <th class="px-3 py-3 font-semibold text-center">状态</th>
            <th class="px-3 py-3 font-semibold text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="f in filteredFoods" :key="f.foodId" class="food-row">
            <td class="px-3 py-3 font-medium">{{ f.foodName }}</td>
            <td class="px-3 py-3 text-xs">{{ f.foodCategory || '-' }}</td>
            <td class="px-3 py-3 text-right">{{ num(f.calorie) }}</td>
            <td class="px-3 py-3 text-right">{{ num(f.protein) }}</td>
            <td class="px-3 py-3 text-right">{{ num(f.fat) }}</td>
            <td class="px-3 py-3 text-right">{{ num(f.carb) }}</td>
            <td class="px-3 py-3 text-right">{{ num(f.giValue) }}</td>
            <td class="px-3 py-3 text-right">{{ num(f.calcium) }}</td>
            <td class="px-3 py-3 text-center">
              <span :class="['px-2 py-1 rounded text-xs font-medium', statusClass(f.status)]">
                {{ statusLabel(f.status) }}
              </span>
            </td>
            <td class="px-3 py-3 text-center">
              <div class="flex gap-1 justify-center flex-wrap">
                <button @click="openEditModal(f)" class="px-2 py-1 text-xs rounded bg-morandi-accent text-white hover:opacity-90">编辑</button>
                <button v-if="f.status !== 'approved'" @click="handleApprove(f)" class="px-2 py-1 text-xs rounded bg-green-600 text-white hover:bg-green-700">通过</button>
                <button v-if="f.status !== 'rejected'" @click="handleReject(f)" class="px-2 py-1 text-xs rounded border border-red-300 text-red-600 hover:bg-red-50">拒绝</button>
                <button @click="handleDelete(f)" class="px-2 py-1 text-xs rounded border border-red-300 text-red-600 hover:bg-red-50">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredFoods.length === 0">
            <td colspan="10" class="px-4 py-8 text-center text-morandi-lightText text-sm">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ===================== 编辑食物弹窗 ===================== -->
  <div
    v-if="editModal.open"
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    style="background: rgba(0, 0, 0, 0.4)"
    @click.self="closeEditModal"
  >
    <div class="glass rounded-2xl p-6 w-[720px] h-[560px] flex flex-col">
      <!-- 顶部标题（固定） -->
      <div class="flex items-center justify-between pb-4 border-b border-morandi-soft flex-shrink-0">
        <h3 class="text-lg font-semibold text-morandi-text">编辑食物信息</h3>
        <button @click="closeEditModal" class="text-morandi-lightText hover:text-morandi-text text-2xl leading-none">×</button>
      </div>

      <!-- 内容区（可滚动） -->
      <div class="flex-1 overflow-y-auto py-4">
        <!-- 基本信息 -->
        <div class="mb-4 p-4 rounded-xl bg-white/70 border border-morandi-soft">
          <p class="text-sm font-medium text-morandi-text mb-3">基本信息</p>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <div class="md:col-span-3">
              <label class="block text-xs text-morandi-lightText mb-1">食物名称 <span class="text-red-500">*</span></label>
              <input v-model="editForm.foodName" placeholder="请输入食物名称" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">分类</label>
              <select v-model="editForm.foodCategory" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent">
                <option value="">请选择</option>
                <option v-for="c in foodCategories" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">审核状态</label>
              <select v-model="editForm.status" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent">
                <option value="pending">待审核</option>
                <option value="approved">已审核</option>
                <option value="rejected">已拒绝</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">热量 (kcal/100g)</label>
              <input v-model.number="editForm.calorie" type="number" step="0.1" min="0" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
            </div>
          </div>
        </div>

        <!-- 营养成分 -->
        <div class="p-4 rounded-xl bg-white/70 border border-morandi-soft">
          <p class="text-sm font-medium text-morandi-text mb-3">营养成分（每 100g）</p>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">蛋白质 (g)</label>
              <input v-model.number="editForm.protein" type="number" step="0.1" min="0" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">脂肪 (g)</label>
              <input v-model.number="editForm.fat" type="number" step="0.1" min="0" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">碳水化合物 (g)</label>
              <input v-model.number="editForm.carb" type="number" step="0.1" min="0" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">膳食纤维 (g)</label>
              <input v-model.number="editForm.dietFiber" type="number" step="0.1" min="0" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">GI 值</label>
              <input v-model.number="editForm.giValue" type="number" step="1" min="0" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">钙 (mg)</label>
              <input v-model.number="editForm.calcium" type="number" step="1" min="0" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">DHA (mg)</label>
              <input v-model.number="editForm.dha" type="number" step="1" min="0" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
            </div>
            <div class="col-span-2">
              <label class="block text-xs text-morandi-lightText mb-1">叶酸 (μg)</label>
              <input v-model.number="editForm.folicAcid" type="number" step="1" min="0" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
            </div>
          </div>
        </div>
      </div>

      <!-- 底部按钮栏（固定） -->
      <div class="flex items-center justify-between gap-3 pt-4 border-t border-morandi-soft flex-shrink-0">
        <div v-if="editModal.error" class="text-xs text-red-600">{{ editModal.error }}</div>
        <div v-else></div>
        <div class="flex gap-2">
          <button @click="closeEditModal" class="px-4 py-2 rounded-lg border border-morandi-soft text-morandi-text text-sm hover:bg-morandi-soft transition">取消</button>
          <button
            @click="saveEdit"
            :disabled="editModal.saving"
            class="px-5 py-2 rounded-lg bg-morandi-accent text-white text-sm disabled:opacity-50 hover:opacity-90 transition shadow"
          >{{ editModal.saving ? '保存中...' : '保存修改' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { api } from '@/api'
import { FOOD_CATEGORIES } from '../../constants'

// ============== 食物管理 ==============
const allFoods = ref<any[]>([])
const foodLoading = ref(false)
const foodKeyword = ref('')
const foodCategoryFilter = ref('')
const foodStatusFilter = ref('')

const foodCategories = computed(() => {
  const set = new Set<string>()
  allFoods.value.forEach((f: any) => {
    if (f && f.foodCategory) set.add(f.foodCategory)
  })
  ;(FOOD_CATEGORIES as readonly string[]).forEach((c: string) => set.add(c))
  return Array.from(set).sort()
})

const filteredFoods = computed(() => {
  const kw = foodKeyword.value.trim().toLowerCase()
  return allFoods.value.filter((f: any) => {
    if (!f) return false
    const okStatus = !foodStatusFilter.value || f.status === foodStatusFilter.value
    const okCat = !foodCategoryFilter.value || f.foodCategory === foodCategoryFilter.value
    const okKw = !kw || (f.foodName && String(f.foodName).toLowerCase().indexOf(kw) >= 0)
    return okStatus && okCat && okKw
  })
})

const loadAllFoods = async () => {
  foodLoading.value = true
  try {
    const data = await api.admin.listFoods()
    allFoods.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.warn('加载食物列表失败', e)
  } finally {
    foodLoading.value = false
  }
}

const statusLabel = (status: string) => {
  if (status === 'approved') return '已审核'
  if (status === 'pending') return '待审核'
  if (status === 'rejected') return '已拒绝'
  return status || '-'
}

const statusClass = (status: string) => {
  if (status === 'approved') return 'bg-green-100 text-green-700'
  if (status === 'pending') return 'bg-yellow-100 text-yellow-700'
  if (status === 'rejected') return 'bg-red-100 text-red-700'
  return 'bg-morandi-soft text-morandi-text'
}

// ============== 编辑弹窗 ==============
const editModal = reactive({
  open: false,
  saving: false,
  error: '',
  foodId: null as number | null
})
const editForm = reactive<any>({
  foodName: '',
  foodCategory: '',
  status: 'pending',
  calorie: null,
  protein: null,
  fat: null,
  carb: null,
  dietFiber: null,
  giValue: null,
  calcium: null,
  dha: null,
  folicAcid: null
})

const openEditModal = (f: any) => {
  editModal.foodId = f.foodId
  editForm.foodName = f.foodName || ''
  editForm.foodCategory = f.foodCategory || ''
  editForm.status = f.status || 'pending'
  editForm.calorie = f.calorie != null ? Number(f.calorie) : null
  editForm.protein = f.protein != null ? Number(f.protein) : null
  editForm.fat = f.fat != null ? Number(f.fat) : null
  editForm.carb = f.carb != null ? Number(f.carb) : null
  editForm.dietFiber = f.dietFiber != null ? Number(f.dietFiber) : null
  editForm.giValue = f.giValue != null ? Number(f.giValue) : null
  editForm.calcium = f.calcium != null ? Number(f.calcium) : null
  editForm.dha = f.dha != null ? Number(f.dha) : null
  editForm.folicAcid = f.folicAcid != null ? Number(f.folicAcid) : null
  editModal.error = ''
  editModal.open = true
}

const closeEditModal = () => {
  editModal.open = false
  editModal.saving = false
  editModal.foodId = null
}

const saveEdit = async () => {
  if (!editForm.foodName.trim()) {
    editModal.error = '请输入食物名称'
    return
  }
  editModal.saving = true
  editModal.error = ''
  try {
    if (editModal.foodId == null) {
      throw new Error('缺少食物ID，无法保存')
    }
    await api.admin.updateFood(editModal.foodId, {
      foodName: editForm.foodName.trim(),
      foodCategory: editForm.foodCategory || '',
      status: editForm.status || 'pending',
      calorie: editForm.calorie,
      protein: editForm.protein,
      fat: editForm.fat,
      carb: editForm.carb,
      dietFiber: editForm.dietFiber,
      giValue: editForm.giValue,
      calcium: editForm.calcium,
      dha: editForm.dha,
      folicAcid: editForm.folicAcid
    })
    alert('保存成功')
    closeEditModal()
    loadAllFoods()
  } catch (e: any) {
    editModal.error = e?.response?.data?.message || e?.message || '保存失败'
  } finally {
    editModal.saving = false
  }
}

// ============== 食物审核/拒绝/删除 ==============
const handleApprove = async (f: any) => {
  if (!confirm(`确认将「${f.foodName}」审核通过？通过后将出现在用户食物库中。`)) return
  try {
    await api.admin.approveFood(f.foodId)
    alert('已审核通过')
    loadAllFoods()
  } catch (e: any) {
    alert(e?.response?.data?.message || e?.message || '操作失败')
  }
}

const handleReject = async (f: any) => {
  if (!confirm(`确认拒绝「${f.foodName}」？`)) return
  try {
    await api.admin.rejectFood(f.foodId)
    alert('已拒绝')
    loadAllFoods()
  } catch (e: any) {
    alert(e?.response?.data?.message || e?.message || '操作失败')
  }
}

const handleDelete = async (f: any) => {
  if (!confirm(`确认删除「${f.foodName}」？此操作不可恢复。`)) return
  try {
    await api.admin.deleteFood(f.foodId)
    alert('已删除')
    loadAllFoods()
  } catch (e: any) {
    alert(e?.response?.data?.message || e?.message || '操作失败')
  }
}

// ============== 工具函数 ==============
const num = (v: any): string => {
  if (v === null || v === undefined || v === '') return '-'
  const n = Number(v)
  if (!Number.isFinite(n)) return '-'
  return String(Math.round(n * 10) / 10)
}

// ============== 初始化 ==============
onMounted(() => {
  loadAllFoods()
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.08);
}

.food-table-body {
  max-height: 500px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.6);
}

.food-table-body::-webkit-scrollbar {
  width: 8px;
}
.food-table-body::-webkit-scrollbar-track {
  background: rgba(210, 200, 190, 0.15);
  border-radius: 4px;
}
.food-table-body::-webkit-scrollbar-thumb {
  background: rgba(180, 160, 145, 0.55);
  border-radius: 4px;
}
.food-table-body::-webkit-scrollbar-thumb:hover {
  background: rgba(150, 130, 115, 0.75);
}

.food-row {
  border-bottom: 1px solid rgba(210, 200, 190, 0.35);
  transition: background-color 0.15s ease;
}
.food-row:hover { background: rgba(255, 252, 248, 0.9); }
.food-row:last-child { border-bottom: none; }
</style>
