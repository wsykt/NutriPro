<template>
  <div class="page-fade max-w-7xl mx-auto">
    <!-- 顶部栏 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-morandi-text">管理员系统</h2>
      </div>
      <button @click="handleLogout" class="px-4 py-2 rounded-lg border border-morandi-soft text-sm text-morandi-text hover:bg-morandi-soft transition">
        退出登录
      </button>
    </div>

    <!-- Tab 导航 -->
    <div class="flex gap-2 mb-6 glass rounded-2xl p-2">
      <button
        v-for="t in tabs"
        :key="t.key"
        :class="['flex-1 px-4 py-3 rounded-xl text-sm font-medium transition', tab === t.key ? 'bg-morandi-accent text-white' : 'text-morandi-text hover:bg-morandi-soft']"
        @click="switchTab(t.key)"
      >{{ t.label }}</button>
    </div>

    <!-- ===================== 用户管理 ===================== -->
    <div v-if="tab === 'users'" class="glass rounded-2xl p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-morandi-text">用户管理</h3>
        <span class="text-xs text-morandi-lightText">共 {{ users.length }} 位用户</span>
      </div>

      <div v-if="userLoading" class="text-center text-sm text-morandi-lightText py-16">加载中...</div>

      <div v-else class="overflow-x-auto food-table-body rounded-xl">
        <table class="min-w-full text-sm text-left text-morandi-text">
          <thead class="text-xs text-morandi-lightText" style="background: rgba(248,246,244,0.9)">
            <tr>
              <th class="px-4 py-3 font-semibold">ID</th>
              <th class="px-4 py-3 font-semibold">用户名</th>
              <th class="px-4 py-3 font-semibold">性别</th>
              <th class="px-4 py-3 font-semibold">年龄</th>
              <th class="px-4 py-3 font-semibold">人群类型</th>
              <th class="px-4 py-3 font-semibold">监护人</th>
              <th class="px-4 py-3 font-semibold">被监护人</th>
              <th class="px-4 py-3 font-semibold text-right">角色</th>
              <th class="px-4 py-3 font-semibold text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.userId" class="food-row">
              <td class="px-4 py-3">{{ u.userId }}</td>
              <td class="px-4 py-3 font-medium">{{ u.username }}</td>
              <td class="px-4 py-3">{{ u.gender || '-' }}</td>
              <td class="px-4 py-3">{{ u.age || '-' }}</td>
              <td class="px-4 py-3">{{ u.crowdType || '-' }}</td>
              <td class="px-4 py-3 text-xs">
                <span v-if="u.guardians && u.guardians.length">{{ u.guardians.join(', ') }}</span>
                <span v-else class="text-morandi-lightText">无</span>
              </td>
              <td class="px-4 py-3 text-xs">
                <span v-if="u.wards && u.wards.length">{{ u.wards.join(', ') }}</span>
                <span v-else class="text-morandi-lightText">无</span>
              </td>
              <td class="px-4 py-3 text-right">
                <span :class="['px-2 py-1 rounded text-xs font-medium', u.role === 'admin' ? 'bg-morandi-accent text-white' : 'bg-morandi-soft text-morandi-text']">
                  {{ u.role === 'admin' ? '管理员' : '普通用户' }}
                </span>
              </td>
              <td class="px-4 py-3 text-center">
                <div class="flex gap-1 justify-center flex-wrap">
                  <button @click="viewUser(u.userId)" class="px-2 py-1 text-xs rounded bg-morandi-accent text-white hover:opacity-90">查看</button>
                  <button @click="deleteUser(u)" :disabled="u.role === 'admin'" :class="['px-2 py-1 text-xs rounded border', u.role === 'admin' ? 'border-morandi-soft text-morandi-lightText opacity-50 cursor-not-allowed' : 'border-red-300 text-red-600 hover:bg-red-50']">删除</button>
                </div>
              </td>
            </tr>
            <tr v-if="users.length === 0">
              <td colspan="9" class="px-4 py-8 text-center text-morandi-lightText text-sm">暂无用户数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ===================== 食物管理（统一） ===================== -->
    <div v-if="tab === 'food-management'" class="glass rounded-2xl p-6 min-h-[560px] flex flex-col">
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

    <!-- ===================== 文章管理 ===================== -->
    <div v-if="tab === 'articles'" class="glass rounded-2xl p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-morandi-text">科普文章管理</h3>
        <button @click="showArticleModal = true" class="px-4 py-2 rounded-lg bg-morandi-accent text-white text-sm hover:opacity-90 transition">
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
      <div class="glass rounded-2xl p-6 w-[640px] max-h-[90vh] flex flex-col">
        <div class="flex items-center justify-between pb-4 border-b border-morandi-soft flex-shrink-0">
          <h3 class="text-lg font-semibold text-morandi-text">{{ editingArticle ? '编辑文章' : '生成新文章' }}</h3>
          <button @click="closeArticleModal" class="text-morandi-lightText hover:text-morandi-text text-2xl leading-none">×</button>
        </div>

        <div class="flex-1 overflow-y-auto py-4">
          <div class="space-y-4">
            <div>
              <label class="block text-xs text-morandi-lightText mb-1">文章标题 <span class="text-red-500">*</span></label>
              <input v-model="articleForm.title" placeholder="请输入文章标题" class="w-full px-3 py-2 rounded-lg border border-morandi-soft bg-white text-morandi-text outline-none focus:border-morandi-accent" />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-morandi-lightText mb-1">分类</label>
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
              :disabled="articleModalSaving"
              class="px-5 py-2 rounded-lg bg-morandi-accent text-white text-sm disabled:opacity-50 hover:opacity-90 transition shadow"
            >{{ articleModalSaving ? '保存中...' : (editingArticle ? '保存修改' : '生成文章') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================== 数据统计 ===================== -->
    <div v-if="tab === 'stats'" class="space-y-6">
      <div class="glass rounded-2xl p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-morandi-text">用户人群分布</h3>
          <span class="text-xs text-morandi-lightText">总用户数：{{ crowdStats.total }}</span>
        </div>

        <div v-if="statsLoading" class="text-center text-sm text-morandi-lightText py-16">加载中...</div>

        <div v-else-if="crowdStats.data && crowdStats.data.length > 0" class="flex flex-col md:flex-row items-center gap-6">
          <div ref="pieChartRef" class="w-full md:w-1/2" style="min-height: 360px"></div>
          <div class="w-full md:w-1/2 space-y-3">
            <div
              v-for="(item, idx) in crowdStats.data"
              :key="item.name"
              class="flex items-center justify-between p-3 bg-white rounded-xl border border-morandi-soft"
            >
              <div class="flex items-center gap-3">
                <span class="w-4 h-4 rounded-full" :style="{ background: pieColors[(idx as number) % pieColors.length] }"></span>
                <span class="text-sm font-medium text-morandi-text">{{ item.name }}</span>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-sm text-morandi-lightText">{{ percent(item.value, crowdStats.total) }}%</span>
                <span class="text-sm font-semibold text-morandi-accent">{{ item.value }} 人</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center text-sm text-morandi-lightText py-16">暂无统计数据</div>
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

    <!-- ===================== 查看用户信息弹窗 ===================== -->
    <div
      v-if="viewUserModal.open"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      style="background: rgba(0, 0, 0, 0.4)"
      @click.self="closeViewUserModal"
    >
      <div class="glass rounded-2xl p-6 max-w-xl w-full max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-morandi-text">用户详细信息</h3>
          <button @click="closeViewUserModal" class="text-morandi-lightText hover:text-morandi-text text-2xl leading-none">×</button>
        </div>

        <div v-if="viewUserModal.loading" class="text-center text-sm text-morandi-lightText py-12">加载中...</div>

        <template v-else-if="viewUserModal.data">
          <div class="space-y-4">
            <div class="flex items-center gap-4 p-4 rounded-xl bg-white/70 border border-morandi-soft">
              <div class="w-14 h-14 rounded-full bg-morandi-accent flex items-center justify-center text-white font-bold text-xl">
                {{ (viewUserModal.data.username || 'U').charAt(0).toUpperCase() }}
              </div>
              <div>
                <p class="font-semibold text-morandi-text text-lg">{{ viewUserModal.data.username }}</p>
                <p class="text-xs text-morandi-lightText mt-1">
                  用户 ID：{{ viewUserModal.data.userId }} ·
                  角色：{{ viewUserModal.data.role === 'admin' ? '管理员' : '普通用户' }}
                </p>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="p-3 rounded-xl bg-white/70 border border-morandi-soft">
                <p class="text-xs text-morandi-lightText">性别</p>
                <p class="text-sm font-medium text-morandi-text mt-1">{{ viewUserModal.data.gender || '-' }}</p>
              </div>
              <div class="p-3 rounded-xl bg-white/70 border border-morandi-soft">
                <p class="text-xs text-morandi-lightText">年龄</p>
                <p class="text-sm font-medium text-morandi-text mt-1">{{ viewUserModal.data.age ?? '-' }}</p>
              </div>
              <div class="p-3 rounded-xl bg-white/70 border border-morandi-soft">
                <p class="text-xs text-morandi-lightText">身高 (cm)</p>
                <p class="text-sm font-medium text-morandi-text mt-1">{{ viewUserModal.data.height ?? '-' }}</p>
              </div>
              <div class="p-3 rounded-xl bg-white/70 border border-morandi-soft">
                <p class="text-xs text-morandi-lightText">体重 (kg)</p>
                <p class="text-sm font-medium text-morandi-text mt-1">{{ viewUserModal.data.weight ?? '-' }}</p>
              </div>
            </div>

            <div class="p-4 rounded-xl bg-white/70 border border-morandi-soft">
              <p class="text-sm font-medium text-morandi-text mb-3">身体指标计算</p>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <p class="text-xs text-morandi-lightText">BMI 指数</p>
                  <p class="text-xl font-bold text-morandi-accent mt-1">{{ viewUserModal.data.bmi ?? '-' }}</p>
                  <p class="text-xs text-morandi-lightText mt-1">{{ viewUserModal.data.bmiStatus || '-' }}</p>
                </div>
                <div>
                  <p class="text-xs text-morandi-lightText">基础代谢 BMR (kcal)</p>
                  <p class="text-xl font-bold text-morandi-accent mt-1">{{ viewUserModal.data.bmr ?? '-' }}</p>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="p-3 rounded-xl bg-white/70 border border-morandi-soft">
                <p class="text-xs text-morandi-lightText">人群类型</p>
                <p class="text-sm font-medium text-morandi-text mt-1">{{ viewUserModal.data.crowdType || '-' }}</p>
              </div>
              <div class="p-3 rounded-xl bg-white/70 border border-morandi-soft">
                <p class="text-xs text-morandi-lightText">注册时间</p>
                <p class="text-sm font-medium text-morandi-text mt-1">{{ viewUserModal.data.createdAt || '-' }}</p>
              </div>
            </div>
          </div>
        </template>

        <div v-if="viewUserModal.error" class="mt-4 text-xs text-red-600 p-3 rounded-lg bg-red-50 border border-red-200">{{ viewUserModal.error }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import * as echarts from 'echarts'
import { api } from '@/api'
import { FOOD_CATEGORIES } from '../constants'

const router = useRouter()
const userStore = useUserStore()

const tabs = [
  { key: 'users', label: '用户管理' },
  { key: 'food-management', label: '食物管理' },
  { key: 'articles', label: '文章管理' },
  { key: 'stats', label: '数据统计' }
]

const tab = ref<string>('users')
const switchTab = (key: string) => {
  tab.value = key
  if (key === 'users') loadUsers()
  else if (key === 'food-management') loadAllFoods()
  else if (key === 'articles') loadArticles()
  else if (key === 'stats') loadStats()
}

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

// ============== 用户管理 ==============
const users = ref<any[]>([])
const userLoading = ref(false)

const loadUsers = async () => {
  userLoading.value = true
  try {
    const data = await api.admin.listUsersWithRelations()
    users.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.warn('加载用户失败', e)
  } finally {
    userLoading.value = false
  }
}

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

// ============== 用户查看/删除 ==============
const viewUserModal = reactive({
  open: false,
  loading: false,
  error: '',
  data: null as any
})

const viewUser = async (userId: number) => {
  viewUserModal.open = true
  viewUserModal.loading = true
  viewUserModal.error = ''
  viewUserModal.data = null
  try {
    const data = await api.admin.getUserDetail(userId)
    viewUserModal.data = data
  } catch (e: any) {
    viewUserModal.error = e?.response?.data?.message || e?.message || '获取用户信息失败'
  } finally {
    viewUserModal.loading = false
  }
}

const closeViewUserModal = () => {
  viewUserModal.open = false
  viewUserModal.data = null
  viewUserModal.error = ''
}

const deleteUser = async (u: any) => {
  if (u.role === 'admin') {
    alert('管理员账号不能删除')
    return
  }
  if (!confirm(`确认删除用户「${u.username}」？此操作不可恢复。`)) return
  try {
    await api.admin.deleteUser(u.userId)
    alert('已删除')
    loadUsers()
  } catch (e: any) {
    alert(e?.response?.data?.message || e?.message || '删除失败')
  }
}

// ============== 统计数据 ==============
const statsLoading = ref(false)
const pieChartRef = ref<HTMLElement | null>(null)
const crowdStats = reactive<any>({ total: 0, data: [] })
let pieChartInstance: any = null

const pieColors = ['#8b7355', '#a68465', '#c9a66b', '#d9b38c', '#e6cfa7', '#8fbc8f', '#5d9b9b', '#9b7c5d']

const loadStats = async () => {
  statsLoading.value = true
  try {
    const data = await api.admin.getCrowdTypeStats()
    crowdStats.total = data.total || 0
    crowdStats.data = data.data || []
    await nextTick()
    renderPieChart()
  } catch (e) {
    console.warn('加载统计数据失败', e)
  } finally {
    statsLoading.value = false
  }
}

const renderPieChart = () => {
  if (!pieChartRef.value) return
  if (pieChartInstance) pieChartInstance.dispose()
  pieChartInstance = echarts.init(pieChartRef.value)
  const colors = ['#c0392b', '#e67e22', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6', '#1abc9c', '#e74c3c']
  pieChartInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 人 ({d}%)' },
    legend: { top: 'bottom' },
    series: [
      {
        name: '人群分布',
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['50%', '45%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
        label: { show: true, formatter: '{b}\n{d}%', fontSize: 11, color: '#5d4f3f' },
        labelLine: { length: 10, length2: 8 },
        data: crowdStats.data.map((d: any, i: number) => ({
          name: d.name,
          value: d.value,
          itemStyle: { color: colors[i % colors.length] }
        }))
      }
    ]
  })
  setTimeout(() => pieChartInstance && pieChartInstance.resize(), 100)
}

// ============== 工具函数 ==============
const num = (v: any): string => {
  if (v === null || v === undefined || v === '') return '-'
  const n = Number(v)
  if (!Number.isFinite(n)) return '-'
  return String(Math.round(n * 10) / 10)
}

const percent = (val: number, total: number) => {
  if (!total) return '0.0'
  return ((val / total) * 100).toFixed(1)
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

// ============== 初始化 ==============
onMounted(() => {
  loadUsers()
})

const onResize = () => {
  if (pieChartInstance) pieChartInstance.resize()
}
if (typeof window !== 'undefined') {
  window.addEventListener('resize', onResize)
}

watch(() => tab.value, (nv) => {
  if (nv === 'stats') {
    nextTick(() => {
      setTimeout(renderPieChart, 50)
    })
  }
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

.page-fade { animation: fadeIn 0.3s ease forwards; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
