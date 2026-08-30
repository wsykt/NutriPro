<template>
  <div class="ad-card">
    <div class="ad-head">
      <h3 class="ad-h3">书阁文牍<span class="ad-h3-en">ARTICLES</span></h3>
      <button class="ad-btn solid" @click="showArticleModal = true">+ 生成新文章</button>
    </div>

    <div v-if="articleLoading" class="ad-empty">加载中...</div>

    <div v-else class="ad-table-wrap">
      <table class="ad-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>标题</th>
            <th>分类</th>
            <th>人群</th>
            <th class="ta-r">浏览</th>
            <th class="ta-r">点赞</th>
            <th class="ta-c">状态</th>
            <th class="ta-c">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="article in articles" :key="article.id">
            <td class="small dim">{{ article.id }}</td>
            <td class="strong" style="max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ article.title }}</td>
            <td>{{ article.category || '-' }}</td>
            <td>{{ article.audience || '-' }}</td>
            <td class="ta-r">{{ article.viewsCount || 0 }}</td>
            <td class="ta-r">{{ article.likesCount || 0 }}</td>
            <td class="ta-c">
              <span :class="['ad-chip', article.status === 'published' ? 'green' : 'warn']">
                {{ article.status === 'published' ? '已发布' : '草稿' }}
              </span>
            </td>
            <td class="ta-c">
              <div class="acts">
                <button class="ad-btn sm solid" @click="editArticle(article)">编辑</button>
                <button class="ad-btn sm red" @click="deleteArticle(article)">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="articles.length === 0">
            <td colspan="8" class="ad-empty">暂无文章数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ===================== 生成/编辑文章 · 无遮罩气泡弹窗 ===================== -->
  <div v-if="showArticleModal" class="ad-pop-wrap" @click.self="showArticleModal = false">
    <div class="ad-pop" style="width: 660px; max-width: 94vw;">
      <div class="ad-pop-head">
        <h3 class="ad-h3">{{ editingArticle ? '修纂文牍' : '炼制新文' }}<span class="ad-h3-en">{{ editingArticle ? 'EDIT' : 'COMPOSE' }}</span></h3>
        <button class="ad-x" @click="closeArticleModal">×</button>
      </div>

      <div style="max-height: 58vh; overflow-y: auto; padding-right: 4px;">
        <!-- 生成新文章：只需主题 + 目标人群，标题/分类/摘要/内容/标签由 AI 自动生成 -->
        <div v-if="!editingArticle" class="ad-grid2">
          <div style="grid-column: 1 / -1;">
            <label class="ad-label">文章主题 *</label>
            <input v-model="articleForm.topic" placeholder="请输入文章主题，如：孕期叶酸补充" class="ad-input" style="width: 100%;" />
            <div style="font-size: 12px; color: #8a94a6; margin-top: 6px; line-height: 1.5;">
              标题、分类、摘要、正文与标签均由 AI 自动生成（约 2~3 分钟）
            </div>
          </div>
          <div style="grid-column: 1 / -1;">
            <label class="ad-label">目标人群</label>
            <select v-model="articleForm.audience" class="ad-select" style="width: 100%;">
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

        <!-- 编辑已有文章：完整字段 -->
        <div v-else class="ad-grid2">
          <div style="grid-column: 1 / -1;">
            <label class="ad-label">文章标题 *</label>
            <input v-model="articleForm.title" placeholder="请输入文章标题" class="ad-input" style="width: 100%;" />
          </div>
          <div>
            <label class="ad-label">分类</label>
            <select v-model="articleForm.category" class="ad-select" style="width: 100%;">
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
            <label class="ad-label">目标人群</label>
            <select v-model="articleForm.audience" class="ad-select" style="width: 100%;">
              <option value="">请选择人群</option>
              <option value="普通人群">普通人群</option>
              <option value="老年人">老年人</option>
              <option value="孕妇">孕妇</option>
              <option value="青少年">青少年</option>
              <option value="糖尿病">糖尿病</option>
              <option value="健身">健身</option>
            </select>
          </div>
          <div style="grid-column: 1 / -1;">
            <label class="ad-label">文章主题</label>
            <input v-model="articleForm.topic" placeholder="请输入文章主题" class="ad-input" style="width: 100%;" />
          </div>
          <div style="grid-column: 1 / -1;">
            <label class="ad-label">文章摘要</label>
            <textarea v-model="articleForm.summary" rows="2" placeholder="请输入文章摘要" class="ad-input" style="width: 100%; resize: none;"></textarea>
          </div>
          <div style="grid-column: 1 / -1;">
            <label class="ad-label">文章内容</label>
            <textarea v-model="articleForm.content" rows="8" placeholder="请输入文章内容（支持Markdown格式）" class="ad-input" style="width: 100%; resize: none; line-height: 1.7;"></textarea>
          </div>
          <div style="grid-column: 1 / -1;">
            <label class="ad-label">标签（逗号分隔）</label>
            <input v-model="articleForm.tags" placeholder="请输入标签，用逗号分隔" class="ad-input" style="width: 100%;" />
          </div>
        </div>
      </div>

      <div class="ad-pop-foot">
        <div v-if="articleModalError" class="ad-err">{{ articleModalError }}</div>
        <div v-else></div>
        <div style="display: flex; gap: 10px;">
          <button class="ad-btn" @click="closeArticleModal">取消</button>
          <button class="ad-btn solid" :disabled="articleModalSaving" @click="saveArticle">
            {{ articleModalSaving ? (editingArticle ? '保存中...' : '生成中...') : (editingArticle ? '保存修改' : '生成文章') }}
          </button>
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

const closeArticleModal = () => {
  showArticleModal.value = false
  articleModalSaving.value = false
  articleModalError.value = ''
  editingArticle.value = null
  articleForm.title = ''
  articleForm.topic = ''
  articleForm.content = ''
  articleForm.summary = ''
  articleForm.tags = ''
  articleForm.category = ''
  articleForm.audience = ''
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

const saveArticle = async () => {
  articleModalSaving.value = true
  articleModalError.value = ''
  try {
    if (editingArticle.value) {
      if (!articleForm.title.trim()) {
        articleModalError.value = '请输入文章标题'
        return
      }
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
      // 生成新文章：只填主题 + 目标人群，标题/分类/摘要/内容/标签由 AI 自动生成
      if (!articleForm.topic.trim()) {
        articleModalError.value = '请输入文章主题'
        return
      }
      const res: any = await api.article.generate(
        articleForm.topic.trim(),
        articleForm.audience.trim() || '普通人群'
      )
      const data = Array.isArray(res?.articles) ? res : (res?.data || res || {})
      const list: any[] = Array.isArray(data?.articles) ? data.articles : []
      const score = data?.qualityScore
      alert(
        `生成完成：共 ${list.length} 篇` +
        (score != null ? `，质量分 ${score}` : '') +
        (data?.passed === false ? '，存在质量问题需人工复核' : '')
      )
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
