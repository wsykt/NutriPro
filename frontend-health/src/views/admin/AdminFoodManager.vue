<template>
  <div class="ad-card">
    <div class="ad-head">
      <h3 class="ad-h3">食库司衡<span class="ad-h3-en">FOOD AUDIT</span></h3>
      <span class="ad-sub">共 {{ allFoods.length }} 条 · 当前显示 {{ filteredFoods.length }} 条</span>
    </div>

    <!-- 筛选栏 -->
    <div class="ad-filters">
      <select v-model="foodStatusFilter" class="ad-select">
        <option value="">全部状态</option>
        <option value="approved">已审核</option>
        <option value="pending">待审核</option>
        <option value="rejected">已拒绝</option>
      </select>
      <select v-model="foodCategoryFilter" class="ad-select">
        <option value="">全部分类</option>
        <option v-for="c in foodCategories" :key="c" :value="c">{{ c }}</option>
      </select>
      <input v-model="foodKeyword" type="text" placeholder="搜索食物名..." class="ad-input" style="flex: 1; min-width: 200px;" />
      <button class="ad-btn" @click="loadAllFoods">刷新</button>
    </div>

    <div v-if="foodLoading" class="ad-empty">加载中...</div>

    <div v-else class="ad-table-wrap" style="max-height: 560px;">
      <table class="ad-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>分类</th>
            <th class="ta-r">热量</th>
            <th class="ta-r">蛋白</th>
            <th class="ta-r">脂肪</th>
            <th class="ta-r">碳水</th>
            <th class="ta-r">GI</th>
            <th class="ta-r">钙</th>
            <th class="ta-c">状态</th>
            <th class="ta-c">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="f in filteredFoods" :key="f.foodId">
            <td class="strong">{{ f.foodName }}</td>
            <td class="small">{{ f.foodCategory || '-' }}</td>
            <td class="ta-r">{{ num(f.calorie) }}</td>
            <td class="ta-r">{{ num(f.protein) }}</td>
            <td class="ta-r">{{ num(f.fat) }}</td>
            <td class="ta-r">{{ num(f.carb) }}</td>
            <td class="ta-r">{{ num(f.giValue) }}</td>
            <td class="ta-r">{{ num(f.calcium) }}</td>
            <td class="ta-c"><span :class="['ad-chip', statusClass(f.status)]">{{ statusLabel(f.status) }}</span></td>
            <td class="ta-c">
              <div class="acts">
                <button class="ad-btn sm solid" @click="openEditModal(f)">编辑</button>
                <button v-if="f.status !== 'approved'" class="ad-btn sm green" @click="handleApprove(f)">通过</button>
                <button v-if="f.status !== 'rejected'" class="ad-btn sm red" @click="handleReject(f)">拒绝</button>
                <button class="ad-btn sm red" @click="handleDelete(f)">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredFoods.length === 0">
            <td colspan="10" class="ad-empty">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ===================== 编辑食物 · 无遮罩气泡弹窗 ===================== -->
  <div v-if="editModal.open" class="ad-pop-wrap" @click.self="closeEditModal">
    <div class="ad-pop" style="width: 720px; max-width: 94vw;">
      <div class="ad-pop-head">
        <h3 class="ad-h3">校准食料<span class="ad-h3-en">EDIT FOOD</span></h3>
        <button class="ad-x" @click="closeEditModal">×</button>
      </div>

      <div style="max-height: 58vh; overflow-y: auto; padding-right: 4px;">
        <!-- 基本信息 -->
        <div class="ad-section">
          <p class="ad-section-tt">基本信息</p>
          <div class="ad-grid3">
            <div style="grid-column: 1 / -1;">
              <label class="ad-label">食物名称 *</label>
              <input v-model="editForm.foodName" placeholder="请输入食物名称" class="ad-input" style="width: 100%;" />
            </div>
            <div>
              <label class="ad-label">分类</label>
              <select v-model="editForm.foodCategory" class="ad-select" style="width: 100%;">
                <option value="">请选择</option>
                <option v-for="c in foodCategories" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div>
              <label class="ad-label">审核状态</label>
              <select v-model="editForm.status" class="ad-select" style="width: 100%;">
                <option value="pending">待审核</option>
                <option value="approved">已审核</option>
                <option value="rejected">已拒绝</option>
              </select>
            </div>
            <div>
              <label class="ad-label">热量 (kcal/100g)</label>
              <input v-model.number="editForm.calorie" type="number" step="0.1" min="0" class="ad-input" style="width: 100%;" />
            </div>
          </div>
        </div>

        <!-- 营养成分 -->
        <div class="ad-section" style="margin-top: 12px;">
          <p class="ad-section-tt">营养成分（每 100g）</p>
          <div class="ad-grid3">
            <div>
              <label class="ad-label">蛋白质 (g)</label>
              <input v-model.number="editForm.protein" type="number" step="0.1" min="0" class="ad-input" style="width: 100%;" />
            </div>
            <div>
              <label class="ad-label">脂肪 (g)</label>
              <input v-model.number="editForm.fat" type="number" step="0.1" min="0" class="ad-input" style="width: 100%;" />
            </div>
            <div>
              <label class="ad-label">碳水化合物 (g)</label>
              <input v-model.number="editForm.carb" type="number" step="0.1" min="0" class="ad-input" style="width: 100%;" />
            </div>
            <div>
              <label class="ad-label">膳食纤维 (g)</label>
              <input v-model.number="editForm.dietFiber" type="number" step="0.1" min="0" class="ad-input" style="width: 100%;" />
            </div>
            <div>
              <label class="ad-label">GI 值</label>
              <input v-model.number="editForm.giValue" type="number" step="1" min="0" class="ad-input" style="width: 100%;" />
            </div>
            <div>
              <label class="ad-label">钙 (mg)</label>
              <input v-model.number="editForm.calcium" type="number" step="1" min="0" class="ad-input" style="width: 100%;" />
            </div>
            <div>
              <label class="ad-label">DHA (mg)</label>
              <input v-model.number="editForm.dha" type="number" step="1" min="0" class="ad-input" style="width: 100%;" />
            </div>
            <div style="grid-column: span 2;">
              <label class="ad-label">叶酸 (μg)</label>
              <input v-model.number="editForm.folicAcid" type="number" step="1" min="0" class="ad-input" style="width: 100%;" />
            </div>
          </div>
        </div>
      </div>

      <div class="ad-pop-foot">
        <div v-if="editModal.error" class="ad-err">{{ editModal.error }}</div>
        <div v-else></div>
        <div style="display: flex; gap: 10px;">
          <button class="ad-btn" @click="closeEditModal">取消</button>
          <button class="ad-btn solid" :disabled="editModal.saving" @click="saveEdit">{{ editModal.saving ? '保存中...' : '保存修改' }}</button>
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
  if (status === 'approved') return 'green'
  if (status === 'pending') return 'warn'
  if (status === 'rejected') return 'red'
  return ''
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
