<template>
  <div class="glass rounded-2xl p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-morandi-text">科普文章管理</h3>
      <button @click="openCreateModal" class="px-4 py-2 rounded-lg bg-morandi-accent text-white text-sm hover:opacity-90 transition">
        + 生成新文章
      </button>
    </div>

    <div v-if="articleLoading" class="text-center text-sm text-morandi-lightText py-16">加载中...</div>

    <div v-else class="overflow-x-auto food-table-body rounded-xl">
      <table class="min-w-full text-sm text-left text-morandi-text">
        <thead class="text-xs text-morandi-lightText" style="background: rgba(248,246,244,0.9)">
          <tr>
            <th class="px-4 py-3 font-semibold">ID</th>
            <th class="px-4 py-3 font-semibold">标题</th>
            <th class="px-4 py-3 font-semibold">分类</th>
            <th class="px-4 py-3 font-semibold">人群</th>
            <th class="px-4 py-3 font-semibold text-right">浏览</th>
            <th class="px-4 py-3 font-semibold text-right">点赞</th>
            <th class="px-4 py-3 font-semibold text-center">状态</th>
            <th class="px-4 py-3 font-semibold text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="article in articles" :key="article.id" class="food-row">
            <td class="px-4 py-3">{{ article.id }}</td>
            <td class="px-4 py-3 font-medium max-w-xs truncate">{{ article.title }}</td>
            <td class="px-4 py-3">{{ article.category || '-' }}</td>
            <td class="px-4 py-3">{{ article.audience || '-' }}</td>
            <td class="px-4 py-3 text-right">{{ article.viewsCount || 0 }}</td>
            <td class="px-4 py-3 text-right">{{ article.likesCount || 0 }}</td>
            <td class="px-4 py-3 text-center">
              <span :class="['px-2 py-1 rounded text-xs font-medium', article.status === 'published' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700']">
                {{ article.status === 'published' ? '已发布' : '草稿' }}
              </span>
            </td>
            <td class="px-4 py-3 text-center">
              <div class="flex gap-1 justify-center flex-wrap">
                <button @click="editArticle(article)" class="px-2 py-1 text-xs rounded bg-morandi-accent text-white hover:opacity-90">编辑</button>
                <button @click="deleteArticle(article)" class="px-2 py-1 text-xs rounded border border-red-300 text-red-600 hover:bg-red-50">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="articles.length === 0">
            <td colspan="8" class="px-4 py-8 text-center text-morandi-lightText text-sm">暂无文章数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ===================== 生成/编辑文章弹窗 ===================== -->
  <div
    v-if="showArticleModal"
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    style="background: rgba(0, 0, 0, 0.4)"
    @click.self="showArticleModal = false"
  >
    <div class="glass rounded-2xl p-6 w-[720px] max-h-[92vh] flex flex-col">
      <div class="flex items-center justify-between pb-4 border-b border-morandi-soft flex-shrink-0">
        <h3 class="text-lg font-semibold text-morandi-text">{{ editingArticle ? '编辑文章' : '生成新文章' }}</h3>
        <button @click="closeArticleModal" class="text-morandi-lightText hover:text-morandi-text text-2xl leading-none">×</button>
      </div>

      <div class="flex-1 overflow-y-auto py-4">
        <!-- ===== 第一步：AI 智能生成（仅新建文章时显示） ===== -->
        <div v-if="!editingArticle" class="mb-5 rounded-xl border border-morandi-accent/40 bg-morandi-accent/5 p-4">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-base">🤖</span>
            <span class="text-sm font-semibold text-morandi-text">第一步 · AI 智能生成</span>
            <span class="text-[11px] px-2 py-0.5 rounded-full bg-morandi-accent/15 text-morandi-accent">本地大模型自动分类</span>
          </div>
          <p class="text-xs text-morandi-lightText leading-5 mb-3">
            只需填写「文章主题 + 目标人群」，由<strong>本地大模型</strong>自动识别分类，并生成
            标题 / 人群分类 / 主题 / 摘要 / 内容（约 2~3 分钟）。生成后可继续手动修改再保存。
          </p>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">文章主题 <span class="text-red-500">*</span></label>
              <input
                v-model="articleForm.topic"
                placeholder="例如：补钙与骨骼健康 / 孕期叶酸补充"
                class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent"
              />
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">目标人群 <span class="text-red-500">*</span></label>
              <select v-model="articleForm.audience" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent">
                <option value="">请选择人群</option>
                <option value="普通人群">普通人群</option>
                <option value="老年人">老年人</option>
                <option value="孕妇">孕妇</option>
                <option value="青少年">青少年</option>
                <option value="糖尿病">糖尿病</option>
                <option value="健身">健身</option>
              </select>
            </div>
          </div>
          <div class="mt-3 flex items-center gap-3">
            <button
              @click="generateByAI"
              :disabled="aiGenerating"
              class="px-5 py-2 rounded-lg bg-morandi-accent text-white text-sm font-semibold hover:opacity-90 transition shadow disabled:opacity-60"
            >
              {{ aiGenerating ? '⏳ AI 生成中（本地分类 + 云端外扩，约 2~3 分钟）...' : '✨ AI 智能生成' }}
            </button>
            <span v-if="aiGenerated" class="text-xs text-emerald-700 bg-emerald-50 px-2 py-1 rounded-lg">
              ✅ 已生成并回填，可修改后保存
            </span>
          </div>
          <div v-if="aiError" class="mt-2 text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2 leading-5">
            {{ aiError }}
          </div>
        </div>

        <!-- ===== 第二步：可编辑表单 ===== -->
        <div v-if="!editingArticle" class="mb-3">
          <div class="flex items-center gap-2 text-sm font-semibold text-morandi-text">
            <span class="text-base">✍️</span> 第二步 · 复核并保存（AI 已回填，可直接修改）
          </div>
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">文章标题 <span class="text-red-500">*</span></label>
            <input v-model="articleForm.title" placeholder="请输入文章标题" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">分类 <span v-if="!editingArticle" class="text-morandi-accent">（本地大模型已自动识别）</span></label>
              <select v-model="articleForm.category" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent">
                <option value="">请选择分类</option>
                <option value="营养知识">营养知识</option>
                <option value="运动健康">运动健康</option>
                <option value="疾病预防">疾病预防</option>
                <option value="生活方式">生活方式</option>
                <option value="饮食指南">饮食指南</option>
                <option value="心理健康">心理健康</option>
                <option value="老年人膳食">老年人膳食</option>
                <option value="孕期营养">孕期营养</option>
                <option value="儿童青少年健康">儿童青少年健康</option>
                <option value="糖尿病饮食">糖尿病饮食</option>
                <option value="膳食指南">膳食指南</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">目标人群</label>
              <select v-model="articleForm.audience" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent">
                <option value="">请选择人群</option>
                <option value="普通人群">普通人群</option>
                <option value="老年人">老年人</option>
                <option value="孕妇">孕妇</option>
                <option value="青少年">青少年</option>
                <option value="糖尿病">糖尿病</option>
                <option value="健身">健身</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">文章主题</label>
            <input v-model="articleForm.topic" placeholder="请输入文章主题" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
          </div>
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">文章摘要</label>
            <textarea v-model="articleForm.summary" rows="2" placeholder="请输入文章摘要" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent resize-none"></textarea>
          </div>
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">文章内容</label>
            <textarea v-model="articleForm.content" rows="8" placeholder="请输入文章内容（支持Markdown格式）" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent resize-none"></textarea>
          </div>
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">标签（逗号分隔）</label>
            <input v-model="articleForm.tags" placeholder="请输入标签，用逗号分隔" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between gap-3 pt-4 border-t border-morandi-soft flex-shrink-0">
        <div v-if="articleModalError" class="text-xs text-red-600">{{ articleModalError }}</div>
        <div v-else></div>
        <div class="flex gap-2">
          <button @click="closeArticleModal" class="px-4 py-2 rounded-lg border border-morandi-soft text-morandi-text text-sm hover:bg-morandi-soft transition">取消</button>
          <button
            @click="saveArticle"
            :disabled="articleModalSaving || aiGenerating"
            class="px-5 py-2 rounded-lg bg-morandi-accent text-white text-sm disabled:opacity-50 hover:opacity-90 transition shadow"
          >{{ articleModalSaving ? '保存中...' : (editingArticle ? '保存修改' : '保存文章') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { api } from '@/api'

// ============== 文章管理 ==============
const articles = ref<any[]>([])
const articleLoading = ref(false)
const showArticleModal = ref(false)
const articleModalSaving = ref(false)
const articleModalError = ref('')
const editingArticle = ref<any>(null)

// AI 智能生成状态
const aiGenerating = ref(false)
const aiGenerated = ref(false)
const aiError = ref('')

const articleForm = reactive<any>({
  title: '',
  topic: '',
  content: '',
  summary: '',
  tags: '',
  category: '',
  audience: ''
})

const loadArticles = async () => {
  articleLoading.value = true
  try {
    const data = await api.article.list()
    articles.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.warn('加载文章列表失败', e)
    articles.value = []
  } finally {
    articleLoading.value = false
  }
}

const openCreateModal = () => {
  editingArticle.value = null
  resetForm()
  showArticleModal.value = true
}

const resetForm = () => {
  articleForm.title = ''
  articleForm.topic = ''
  articleForm.content = ''
  articleForm.summary = ''
  articleForm.tags = ''
  articleForm.category = ''
  articleForm.audience = ''
  aiGenerating.value = false
  aiGenerated.value = false
  aiError.value = ''
  articleModalError.value = ''
}

const closeArticleModal = () => {
  showArticleModal.value = false
  articleModalSaving.value = false
  articleModalError.value = ''
  editingArticle.value = null
  resetForm()
}

const editArticle = (article: any) => {
  editingArticle.value = article
  articleForm.title = article.title || ''
  articleForm.topic = article.topic || ''
  articleForm.content = article.content || ''
  articleForm.summary = article.summary || ''
  articleForm.tags = article.tags || ''
  articleForm.category = article.category || ''
  articleForm.audience = article.audience || ''
  aiGenerating.value = false
  aiGenerated.value = false
  aiError.value = ''
  showArticleModal.value = true
}

const deleteArticle = async (article: any) => {
  if (!confirm(`确认删除文章「${article.title}」？此操作不可恢复。`)) return
  try {
    await api.article.delete(article.id)
    alert('已删除')
    loadArticles()
  } catch (e: any) {
    alert(e?.response?.data?.message || e?.message || '删除失败')
  }
}

/** 第一步：AI 智能生成 —— 主题 + 目标人群 → 本地大模型分类 → 自动回填标题/分类/摘要/内容 */
const generateByAI = async () => {
  if (!articleForm.topic.trim()) {
    aiError.value = '请先填写文章主题'
    return
  }
  if (!articleForm.audience) {
    aiError.value = '请选择目标人群'
    return
  }
  aiGenerating.value = true
  aiError.value = ''
  aiGenerated.value = false
  try {
    const res = await api.article.generateSmart(articleForm.topic.trim(), articleForm.audience)
    const list = res?.articles
    if (!Array.isArray(list) || list.length === 0) {
      throw new Error('AI 未返回文章数据，请查看后端日志')
    }
    // 取第一篇（速读版）作为编辑基准，其余两版已同主题自动入库
    const main = list[0]
    articleForm.title = main.title || articleForm.topic
    articleForm.category = main.category || ''
    articleForm.audience = main.audience || articleForm.audience
    articleForm.topic = main.topic || articleForm.topic
    articleForm.summary = main.summary || ''
    articleForm.content = main.content || ''
    articleForm.tags = Array.isArray(main.tags) ? main.tags.join(',') : (main.tags || '')
    aiGenerated.value = true
    // 同步刷新列表（另外两版已入库）
    loadArticles()
  } catch (e: any) {
    aiError.value = 'AI 生成失败：' + (e?.response?.data?.message || e?.message || '请稍后重试')
  } finally {
    aiGenerating.value = false
  }
}

const saveArticle = async () => {
  if (!articleForm.title.trim()) {
    articleModalError.value = '请输入文章标题'
    return
  }
  articleModalSaving.value = true
  articleModalError.value = ''
  try {
    if (editingArticle.value) {
      await api.article.update(editingArticle.value.id, {
        title: articleForm.title.trim(),
        topic: articleForm.topic.trim(),
        content: articleForm.content.trim(),
        summary: articleForm.summary.trim(),
        tags: articleForm.tags.trim(),
        category: articleForm.category.trim(),
        audience: articleForm.audience.trim()
      })
      alert('保存成功')
    } else {
      await api.article.create({
        title: articleForm.title.trim(),
        topic: articleForm.topic.trim(),
        content: articleForm.content.trim(),
        summary: articleForm.summary.trim(),
        tags: articleForm.tags.trim(),
        category: articleForm.category.trim(),
        audience: articleForm.audience.trim(),
        status: 'published'
      })
      alert('生成成功')
    }
    closeArticleModal()
    loadArticles()
  } catch (e: any) {
    articleModalError.value = e?.response?.data?.message || e?.message || '操作失败'
  } finally {
    articleModalSaving.value = false
  }
}

// ============== 初始化 ==============
onMounted(() => {
  loadArticles()
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
