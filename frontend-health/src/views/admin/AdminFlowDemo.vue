<template>
  <div class="flow-demo page-fade space-y-5">
    <!-- 顶部横幅 -->
    <div class="bg-gradient-to-r from-morandi-accent/15 via-amber-50 to-sky-50 rounded-3xl border border-morandi-soft/60 p-5 md:p-6">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div class="text-xs font-semibold text-morandi-accent mb-1">AI 功能 · 流程演示</div>
          <h3 class="text-xl md:text-2xl font-bold text-morandi-text leading-snug">
            选择 AI 功能 → 填写真实输入 → 「我开始执行」→ 实时查看后端流水线
          </h3>
          <p class="mt-2 text-sm text-morandi-lightText leading-6 max-w-4xl">
            与前端用户操作完全一致：点开一个 AI 功能，先看到<strong>它做什么</strong>，填写<strong>真实输入</strong>（如科普文章的「文章主题 + 目标人群」），
            再点【我开始执行】。后端按 <strong>入队 → 画像 → RAG 检索 → Prompt → 大模型生成 → 校验 → 落快照</strong> 真实执行；
            左边窗口实时展示每一步的<strong>输入数据 / 产出 / 耗时 / token 消耗</strong>，执行完成后右侧展示最终产出结果。
            测试账号为 test001-006（覆盖六种人群），点【详情】可查看账号的身高体重、饮食与运动记录。
          </p>
        </div>
        <div class="text-right">
          <div class="text-[11px] text-morandi-lightText">会话编号（一次流程演示一个 sessionId）</div>
          <div class="mt-1 px-3 py-1.5 rounded-xl bg-white border border-morandi-soft/60 text-xs font-mono text-morandi-text shadow-sm">
            {{ sessionId }}
          </div>
        </div>
      </div>
    </div>

    <!-- 操作区：功能选择 + 模式 + 用户身份 -->
    <div class="bg-white rounded-3xl border border-morandi-soft/60 p-5">
      <div class="grid lg:grid-cols-[1fr_auto] gap-4 items-start">
        <div>
          <Label>① 选择 AI 功能（点击后先看说明与真实输入，再执行）</Label>
          <div class="grid grid-cols-4 gap-2 mt-2">
            <button v-for="f in funcList" :key="f.key"
              @click="openInputModal(f.key)"
              :class="['px-3 py-2.5 rounded-xl border text-xs font-medium transition text-left',
                funcType===f.key
                  ? 'bg-morandi-accent text-white border-morandi-accent shadow'
                  : 'border-morandi-soft/60 text-morandi-text hover:bg-morandi-bg'
              ]">
              {{ f.label }}
              <div class="text-[10px] mt-0.5 opacity-70">{{ f.hint }}</div>
            </button>
          </div>
        </div>
        <div class="lg:w-72 space-y-3">
          <div>
            <Label>② 生成模式</Label>
            <div class="grid grid-cols-3 gap-2 mt-1.5">
              <button v-for="m in modes" :key="m.key"
                @click="mode = m.key"
                :class="['px-2 py-2 rounded-xl border text-[11px] font-medium transition',
                  mode===m.key
                    ? 'bg-sky-50 text-sky-700 border-sky-200'
                    : 'border-morandi-soft/60 text-morandi-lightText hover:bg-morandi-bg'
                ]">{{ m.label }}</button>
            </div>
          </div>
          <div>
            <Label>③ 用户身份（可选）</Label>
            <div class="mt-1.5 flex gap-2">
              <select v-model="userId" class="w-full text-sm px-3 py-2 rounded-xl bg-morandi-bg/50 border border-morandi-soft/60 outline-none focus:border-morandi-accent">
                <option :value="null">— 无特定用户（演示用）—</option>
                <option v-for="u in exampleUsers" :key="u.value" :value="u.value">{{ u.label }}</option>
              </select>
              <button @click="openDetail" :disabled="!userId || detailLoading"
                class="shrink-0 px-3 py-2 rounded-xl bg-morandi-accent/10 border border-morandi-accent/40 text-morandi-accent text-xs font-semibold hover:bg-morandi-accent/20 transition disabled:opacity-50">
                <span v-if="detailLoading">加载中…</span>
                <span v-else>详情</span>
              </button>
            </div>
            <div class="mt-1 text-[11px] text-morandi-lightText leading-5">
              选择 test 账号后点【详情】，可查看该账号的身高体重、今日饮食与近三日运动记录。
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== 左右两栏：左=后端流水线，右=1:1 呈现 ==================== -->
    <div class="grid lg:grid-cols-2 gap-5 items-start">
      <!-- ===== 左栏：后端实时流水线 ===== -->
      <div class="bg-white rounded-3xl border border-morandi-soft/60 p-5 space-y-3 lg:sticky lg:top-4 max-h-[calc(100vh-140px)] overflow-auto">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <span class="text-sm font-bold text-morandi-text">后端实时流水线</span>
            <span v-if="traceId" class="text-[10px] font-mono text-morandi-lightText bg-morandi-bg px-1.5 py-0.5 rounded">
              {{ traceId }}
            </span>
            <span v-if="currentTrace" class="ml-1 text-[10px] px-1.5 py-0.5 rounded"
              :class="currentTrace.done
                ? (currentTrace.error ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700')
                : 'bg-amber-50 text-amber-700'">
              {{ currentTrace.error ? '失败' : (currentTrace.done ? '完成' : `执行中 ${doneStepCount}/${currentTrace.totalSteps}`) }}
            </span>
          </div>
        </div>

        <div v-if="!currentTrace && !traceId"
          class="px-3 py-6 text-center text-[11px] rounded-xl border border-dashed border-morandi-soft/60 text-morandi-lightText leading-5">
          先在上方选择一个 AI 功能，填写真实输入并点【我开始执行】。<br />
          这里会按真实后端执行顺序，把 <b>入队 → 画像 → RAG → Prompt → 大模型 → 校验 → 落快照</b><br />
          每一步的 <b>输入数据 / 产出结果 / 耗时</b> 实时展开。
        </div>

        <template v-else>
          <div v-for="(step, i) in currentTraceSteps" :key="step.index">
            <div class="border rounded-xl overflow-hidden transition"
              :class="stepClass(step.status)">
              <div class="flex items-center gap-2 px-3 py-2 cursor-pointer select-none"
                @click="toggleStepOpen(step.index)">
                <span class="w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0"
                  :class="stepDotClass(step.status)">
                  <template v-if="step.status==='running'">…</template>
                  <template v-else-if="step.status==='done'">√</template>
                  <template v-else-if="step.status==='error'">!</template>
                  <template v-else>{{ step.index }}</template>
                </span>
                <div class="min-w-0 flex-1">
                  <div class="text-xs font-semibold text-morandi-text truncate">{{ step.title }}</div>
                  <div class="text-[11px] text-morandi-lightText truncate">
                    {{ step.subtitle }}
                    <span v-if="step.status==='done' && step.durationMs" class="ml-1">· 耗时 {{ step.durationMs }}ms</span>
                  </div>
                </div>
                <span class="text-[11px] text-morandi-lightText shrink-0 ml-1">
                  {{ pipelineStepOpen.has(step.index) ? '收起' : '展开' }}
                </span>
              </div>
              <transition name="fade-slide">
                <div v-if="pipelineStepOpen.has(step.index) && step.status==='done'"
                  class="border-t border-morandi-soft/40 bg-morandi-bg/40 px-3 py-3 space-y-3 text-[11px] leading-5">
                  <div v-if="step.note" class="px-3 py-2 rounded-lg bg-sky-50 border border-sky-100 text-sky-800">
                    {{ step.note }}
                  </div>
                  <div v-if="stepTokens(step)" class="flex flex-wrap gap-2">
                    <span class="px-2 py-1 rounded-lg bg-violet-50 border border-violet-100 text-violet-800">
                      本地 {{ stepTokens(step).local?.total ?? 0 }} tokens
                      <template v-if="stepTokens(step).local?.calls"> · {{ stepTokens(step).local.calls }} 次调用</template>
                    </span>
                    <span class="px-2 py-1 rounded-lg bg-sky-50 border border-sky-100 text-sky-800">
                      云端 {{ stepTokens(step).cloud?.total ?? 0 }} tokens
                      <template v-if="stepTokens(step).cloud?.calls"> · {{ stepTokens(step).cloud.calls }} 次调用</template>
                      <template v-if="stepTokens(step).cloud?.cached"> · 缓存命中 {{ stepTokens(step).cloud.cached }}</template>
                    </span>
                    <span class="px-2 py-1 rounded-lg bg-emerald-50 border border-emerald-100 text-emerald-700">
                      合计 {{ stepTokens(step).total ?? 0 }} tokens
                    </span>
                    <span v-if="stepTokens(step).estimated" class="px-2 py-1 rounded-lg bg-amber-50 border border-amber-100 text-amber-700">
                      本地为估算值
                    </span>
                  </div>
                  <div>
                    <div class="text-[10px] font-semibold text-morandi-lightText uppercase mb-1">输入（本步放入了什么数据）</div>
                    <pre class="whitespace-pre-wrap break-all bg-white rounded-lg p-2 border border-morandi-soft/60 text-morandi-text text-[11px] font-mono overflow-auto max-h-40">{{ prettyJson(step.input) }}</pre>
                  </div>
                  <div>
                    <div class="text-[10px] font-semibold text-morandi-lightText uppercase mb-1">输出（本步得到了什么结果）</div>
                    <pre class="whitespace-pre-wrap break-all bg-white rounded-lg p-2 border border-morandi-soft/60 text-morandi-text text-[11px] font-mono overflow-auto max-h-48">{{ prettyJson(stripTokens(step.output)) }}</pre>
                  </div>
                  <div class="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-morandi-lightText">
                    <span v-if="step.startedAt">启动 @ {{ step.startedAt }}</span>
                    <span v-if="step.finishedAt">结束 @ {{ step.finishedAt }}</span>
                    <span v-if="step.durationMs">耗时 {{ step.durationMs }} ms</span>
                    <span v-if="step.last" class="px-1.5 py-0.5 rounded bg-morandi-accent/15 text-morandi-accent font-semibold">FINAL · 已落快照</span>
                  </div>
                </div>
              </transition>
            </div>
            <div v-if="i < currentTraceSteps.length - 1" class="ml-3 h-2 w-px bg-morandi-soft/60"></div>
          </div>
        </template>
      </div>

      <!-- ===== 右栏：最终产出结果（只读展示，不做预览/发布） ===== -->
      <div class="space-y-4 min-w-0">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-xs text-morandi-lightText mb-1">最终产出结果（流水线完成后展示）</div>
            <div class="text-lg font-bold text-morandi-text">
              {{ funcLabel(funcType) }}
              <span class="ml-2 text-[11px] px-2 py-0.5 rounded-full align-middle"
                :class="mode==='high_performance' ? 'bg-sky-50 text-sky-700' : mode==='offline' ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'">
                {{ modeLabel(mode) }}
              </span>
              <span v-if="finalResult" class="ml-2 text-sm font-normal text-morandi-lightText">· 快照 #{{ finalResult.id }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-3xl border border-morandi-soft/60 shadow-lg shadow-morandi-text/5 overflow-hidden">
          <div v-if="!finalResult" class="py-20 md:py-28 text-center text-morandi-lightText text-sm leading-8">
            暂无产出结果。<br />
            请在上方选择一个 AI 功能 → 填写真实输入 → 点【我开始执行】。<br />
            后端流水线执行完成后，最终产出会在这里展示（标题 / 摘要 / 详细内容）。
          </div>
          <div v-else class="p-4 md:p-5 space-y-4">
            <div v-if="finalResult.title" class="text-base font-bold text-morandi-text leading-6">{{ finalResult.title }}</div>
            <div v-if="finalResult.summary" class="text-sm text-morandi-lightText leading-6 bg-morandi-bg/50 rounded-xl px-4 py-3">
              {{ finalResult.summary }}
            </div>
            <div>
              <div class="text-[10px] font-semibold text-morandi-lightText uppercase mb-1">产出数据（JSON）</div>
              <pre class="whitespace-pre-wrap break-all bg-morandi-bg/40 rounded-lg p-3 border border-morandi-soft/60 text-morandi-text text-[11px] font-mono overflow-auto max-h-[480px]">{{ prettyJson(finalResult.payload) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== 说明 + 真实输入 弹窗 ==================== -->
    <div
      v-if="inputModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      style="background: rgba(0, 0, 0, 0.4)"
      @click.self="closeInputModal"
    >
      <div class="bg-white rounded-3xl p-6 w-[620px] max-h-[92vh] flex flex-col shadow-2xl">
        <div class="flex items-center justify-between pb-4 border-b border-morandi-soft/60 flex-shrink-0">
          <div class="flex items-center gap-2">
            <h3 class="text-lg font-bold text-morandi-text">{{ currentForm?.title }}</h3>
            <span class="text-[11px] px-2 py-0.5 rounded-full bg-morandi-accent/15 text-morandi-accent">{{ funcLabel(funcType) }}</span>
          </div>
          <button @click="closeInputModal" class="text-morandi-lightText hover:text-morandi-text text-2xl leading-none">×</button>
        </div>

        <div class="flex-1 overflow-y-auto py-4 space-y-4">
          <!-- 说明：这个 AI 功能在真实前端是做什么的 -->
          <div class="rounded-xl bg-sky-50 border border-sky-100 px-4 py-3 text-xs text-sky-900 leading-6">
            <div class="font-semibold mb-1">这个功能在真实前端是做什么的？</div>
            {{ currentForm?.desc }}
          </div>

          <!-- 真实输入表单 -->
          <div class="space-y-3">
            <div class="text-xs font-semibold text-morandi-text">填写真实输入（与前端操作一致）</div>
            <template v-for="f in (currentForm?.fields || [])" :key="f.key">
              <div v-if="f.type === 'select'">
                <label class="block text-xs text-morandi-lightText mb-1">{{ f.label }} <span v-if="f.required" class="text-red-500">*</span></label>
                <select v-model="inputForm[f.key]" class="w-full px-3 py-2 rounded-xl border border-morandi-soft bg-white text-morandi-text text-sm outline-none focus:border-morandi-accent">
                  <option value="">请选择</option>
                  <option v-for="o in f.options" :key="o" :value="o">{{ o }}</option>
                </select>
              </div>
              <div v-else>
                <label class="block text-xs text-morandi-lightText mb-1">{{ f.label }} <span v-if="f.required" class="text-red-500">*</span></label>
                <textarea
                  v-if="f.textarea"
                  v-model="inputForm[f.key]"
                  :placeholder="f.placeholder"
                  rows="3"
                  class="w-full px-3 py-2 rounded-xl border border-morandi-soft bg-white text-morandi-text text-sm outline-none focus:border-morandi-accent resize-none"
                ></textarea>
                <input
                  v-else
                  v-model="inputForm[f.key]"
                  :placeholder="f.placeholder"
                  class="w-full px-3 py-2 rounded-xl border border-morandi-soft bg-white text-morandi-text text-sm outline-none focus:border-morandi-accent"
                />
              </div>
            </template>
            <div v-if="(currentForm?.fields || []).length === 0" class="text-xs text-morandi-lightText leading-5 px-3 py-2 rounded-xl bg-morandi-bg/60">
              本功能无需额外输入，直接使用你在右上角选择的<strong>用户身份</strong>的真实数据（如画像 / 今日饮食 / 本周运动）执行。
            </div>
          </div>

          <div v-if="inputError" class="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{{ inputError }}</div>
        </div>

        <div class="flex items-center justify-between gap-3 pt-4 border-t border-morandi-soft/60 flex-shrink-0">
          <div class="text-[11px] text-morandi-lightText leading-5">
            {{ currentForm?.note }}
          </div>
          <div class="flex gap-2 shrink-0">
            <button @click="closeInputModal" class="px-4 py-2 rounded-xl border border-morandi-soft text-morandi-text text-sm hover:bg-morandi-bg transition">取消</button>
            <button @click="handleStartExecute" :disabled="executing"
              class="px-6 py-2 rounded-xl bg-morandi-accent text-white text-sm font-bold hover:bg-morandi-accent/90 transition shadow disabled:opacity-60">
              {{ executing ? '正在启动...' : '我开始执行' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== 用户详情弹窗（test 账号的身高体重 + 饮食 + 运动） ==================== -->
    <div
      v-if="detailOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      style="background: rgba(0, 0, 0, 0.4)"
      @click.self="detailOpen = false"
    >
      <div class="bg-white rounded-3xl p-6 w-[760px] max-h-[92vh] flex flex-col shadow-2xl">
        <div class="flex items-center justify-between pb-4 border-b border-morandi-soft/60 flex-shrink-0">
          <div class="flex items-center gap-2">
            <h3 class="text-lg font-bold text-morandi-text">用户详情 · {{ detail?.username || '' }}</h3>
            <span class="text-[11px] px-2 py-0.5 rounded-full bg-morandi-accent/15 text-morandi-accent">{{ detail?.crowdType || '' }}</span>
          </div>
          <button @click="detailOpen = false" class="text-morandi-lightText hover:text-morandi-text text-2xl leading-none">×</button>
        </div>

        <div class="flex-1 overflow-y-auto py-4 space-y-5">
          <!-- 基本信息 -->
          <div>
            <div class="text-xs font-semibold text-morandi-text mb-2">基本信息</div>
            <div class="grid grid-cols-3 md:grid-cols-6 gap-2 text-center">
              <div class="rounded-xl bg-morandi-bg/60 px-2 py-2.5">
                <div class="text-[11px] text-morandi-lightText">性别</div>
                <div class="mt-0.5 text-sm font-semibold text-morandi-text">{{ detail?.gender || '-' }}</div>
              </div>
              <div class="rounded-xl bg-morandi-bg/60 px-2 py-2.5">
                <div class="text-[11px] text-morandi-lightText">年龄</div>
                <div class="mt-0.5 text-sm font-semibold text-morandi-text">{{ detail?.age ?? '-' }} 岁</div>
              </div>
              <div class="rounded-xl bg-morandi-bg/60 px-2 py-2.5">
                <div class="text-[11px] text-morandi-lightText">身高</div>
                <div class="mt-0.5 text-sm font-semibold text-morandi-text">{{ detail?.height ?? '-' }} cm</div>
              </div>
              <div class="rounded-xl bg-morandi-bg/60 px-2 py-2.5">
                <div class="text-[11px] text-morandi-lightText">体重</div>
                <div class="mt-0.5 text-sm font-semibold text-morandi-text">{{ detail?.weight ?? '-' }} kg</div>
              </div>
              <div class="rounded-xl bg-morandi-bg/60 px-2 py-2.5">
                <div class="text-[11px] text-morandi-lightText">BMI</div>
                <div class="mt-0.5 text-sm font-semibold text-morandi-text">{{ fmtNum(detail?.bmi) }}</div>
              </div>
              <div class="rounded-xl bg-morandi-bg/60 px-2 py-2.5">
                <div class="text-[11px] text-morandi-lightText">基础代谢</div>
                <div class="mt-0.5 text-sm font-semibold text-morandi-text">{{ fmtNum(detail?.bmr) }}</div>
              </div>
            </div>
            <div class="mt-2 flex flex-wrap gap-2 text-[11px]">
              <span class="px-2 py-1 rounded-lg bg-sky-50 text-sky-700 border border-sky-100">口味：{{ detail?.tastePreference || '无' }}</span>
              <span class="px-2 py-1 rounded-lg bg-violet-50 text-violet-700 border border-violet-100">忌口：{{ detail?.dietaryRestrictions || '无' }}</span>
              <span class="px-2 py-1 rounded-lg bg-rose-50 text-rose-700 border border-rose-100">过敏：{{ detail?.allergicFoods || '无' }}</span>
            </div>
          </div>

          <!-- 饮食记录 -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <div class="text-xs font-semibold text-morandi-text">饮食记录（近两日）</div>
              <span class="text-[11px] text-morandi-lightText">{{ (detail?.diet || []).length ? (detail.diet[0]?.eatDate || '') + ' 起' : '' }}</span>
            </div>
            <div v-if="!detail?.diet || detail.diet.length === 0" class="text-xs text-morandi-lightText px-3 py-4 rounded-xl bg-morandi-bg/50">暂无饮食记录</div>
            <div v-else class="space-y-3">
              <div v-for="meal in detail.diet" :key="meal.mealId"
                class="rounded-xl border border-morandi-soft/60 overflow-hidden">
                <div class="flex items-center justify-between px-3 py-2 bg-morandi-bg/40">
                  <div class="text-xs font-semibold text-morandi-text">{{ meal.mealType }}</div>
                  <div class="text-[11px] text-morandi-lightText">{{ meal.eatDate }}<span v-if="meal.remark"> · {{ meal.remark }}</span></div>
                </div>
                <table class="w-full text-[11px]">
                  <thead>
                    <tr class="text-morandi-lightText bg-morandi-bg/20">
                      <th class="text-left px-3 py-1.5 font-medium">食物</th>
                      <th class="text-right px-3 py-1.5 font-medium">份量(g)</th>
                      <th class="text-right px-3 py-1.5 font-medium">热量(kcal)</th>
                      <th class="text-right px-3 py-1.5 font-medium">蛋白质(g)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="it in meal.items" :key="it.itemId" class="border-t border-morandi-soft/40">
                      <td class="px-3 py-1.5 text-morandi-text">{{ it.foodName }}<span class="ml-1 text-[10px] text-morandi-lightText">{{ it.foodCategory }}</span></td>
                      <td class="text-right px-3 py-1.5 text-morandi-text">{{ it.eatWeight }}</td>
                      <td class="text-right px-3 py-1.5 text-morandi-text">{{ fmtNum(calcKcal(it)) }}</td>
                      <td class="text-right px-3 py-1.5 text-morandi-text">{{ fmtNum(calcNutrient(it, 'protein')) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- 运动记录 -->
          <div>
            <div class="text-xs font-semibold text-morandi-text mb-2">运动记录（近 5 条）</div>
            <div v-if="!detail?.exercise || detail.exercise.length === 0" class="text-xs text-morandi-lightText px-3 py-4 rounded-xl bg-morandi-bg/50">暂无运动记录</div>
            <div v-else class="grid md:grid-cols-2 gap-2">
              <div v-for="ex in detail.exercise" :key="ex.id"
                class="rounded-xl border border-morandi-soft/60 px-3 py-2.5 flex items-center justify-between">
                <div>
                  <div class="text-xs font-semibold text-morandi-text">{{ ex.exerciseType }}</div>
                  <div class="mt-0.5 text-[11px] text-morandi-lightText">{{ ex.recordDate }}<span v-if="ex.note"> · {{ ex.note }}</span></div>
                </div>
                <div class="text-right shrink-0">
                  <div class="text-xs font-semibold text-sky-700">{{ ex.durationMin }} 分钟</div>
                  <div class="mt-0.5 text-[11px] text-emerald-700">{{ fmtNum(ex.caloriesBurned) }} kcal</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="pt-4 border-t border-morandi-soft/60 flex-shrink-0 flex justify-end">
          <button @click="detailOpen = false" class="px-5 py-2 rounded-xl bg-morandi-accent text-white text-sm font-semibold hover:bg-morandi-accent/90 transition">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import * as PreviewApi from '@/api/preview'
import type { PipelineStep, PipelineTraceResult } from '@/api/preview'
import { api } from '@/api/index'
import { EXAMPLE_PAYLOADS, type FuncType } from './flowDemoExamples'
import { ElMessage } from 'element-plus'

// 不用 JSX（项目未启用 jsx transform），用 defineComponent + h
const Label = defineComponent({
  setup(_, { slots }) {
    return () => h('label', { class: 'block text-xs font-semibold text-morandi-lightText' }, slots.default?.())
  }
})

// ==== 配置项 ====
interface FlowField {
  key: string
  label: string
  type: 'text' | 'select'
  textarea?: boolean
  required?: boolean
  placeholder?: string
  options?: string[]
}
interface FlowForm {
  title: string
  hint: string
  desc: string
  note: string
  fields: FlowField[]
}

const funcList: { key: FuncType; label: string; hint: string }[] = [
  { key: 'article',      label: '科普文章', hint: '主题 + 人群' },
  { key: 'recipe',       label: '食谱推荐', hint: '食材需求' },
  { key: 'dietPlan',     label: '膳食计划', hint: '膳食目标' },
  { key: 'nutrition',    label: '营养分析', hint: '今日饮食' },
  { key: 'training',     label: '训练方案', hint: '训练目标' },
  { key: 'weeklyReport', label: '健康周报', hint: '本周数据' },
  { key: 'consult',      label: 'AI 咨询', hint: '输入问题' },
]

/** 各 AI 功能在真实前端入口 + 输入表单（贴合真实操作流程） */
const FLOW_FORMS: Record<FuncType, FlowForm> = {
  article: {
    title: '科普文章生成',
    hint: '主题 + 人群',
    desc: '对应真实前端入口：首页 → 科普文章 → 选择适配人群 → 浏览主题列表 → 选择篇幅（速读卡 / 深度文 / 综述文）→ 阅读文章。\n本演示只需「文章主题 + 目标人群」：本地大模型自动分类，并生成 标题 / 人群分类 / 摘要 / 内容（拆分三版入库）。',
    note: '生成约 2~3 分钟（本地出框架 → 云端外扩 → 本地校验）。',
    fields: [
      { key: 'topic', label: '文章主题', type: 'text', required: true, placeholder: '例如：孕期如何补叶酸 / 骨质疏松的饮食预防' },
      { key: 'audience', label: '目标人群', type: 'select', required: true, options: ['普通人群', '老年人', '孕妇', '青少年', '糖尿病', '健身'] },
    ],
  },
  recipe: {
    title: '食谱推荐',
    hint: '食材需求',
    desc: '对应真实前端入口：首页 → 食材菜谱推荐 → 输入你的需求（如"适合减脂的午餐，高蛋白低热量"）→ 选择人群 → 生成食谱（含食材 / 热量 / 步骤 / 营养点评）→ 可收藏。',
    note: '将按你选择的用户画像 + 需求调用 AI 生成。',
    fields: [
      { key: 'description', label: '食谱需求描述', type: 'text', textarea: true, required: true, placeholder: '例如：适合减脂的午餐，需要高蛋白低热量' },
      { key: 'goal', label: '目标', type: 'select', required: false, options: ['减脂', '增肌', '控糖', '均衡营养', '孕妇营养', '清淡饮食'] },
    ],
  },
  dietPlan: {
    title: '膳食计划',
    hint: '膳食目标',
    desc: '对应真实前端入口：首页 → AI 智能功能 → 膳食计划（也可在 AI 咨询页一键生成）。基于你的画像与目标，输出一周膳食计划（每日三餐 + 加餐 + 总热量）。',
    note: '将按你选择的用户画像 + 目标调用 AI 生成。',
    fields: [
      { key: 'goal', label: '膳食目标', type: 'select', required: true, options: ['减脂', '增肌', '均衡饮食', '控糖', '孕妇营养'] },
    ],
  },
  nutrition: {
    title: '营养分析',
    hint: '今日饮食',
    desc: '对应真实前端入口：首页 → AI 智能功能 → 营养分析（也可在 AI 咨询页一键生成）。基于今日饮食记录，分析热量 / 三大营养素 / 微量元素的达标情况并给出建议。',
    note: '需选择真实用户（右上角③），将读取该用户今日饮食数据。',
    fields: [],
  },
  training: {
    title: '个性化运动方案',
    hint: '训练目标',
    desc: '对应真实前端入口：首页 → 训练计划 → 输入训练目标或想调整的方向 → AI 结合近 7 日训练数据生成个性化方案（周计划 / 动作 / 组次 / 恢复建议）。',
    note: '将按你选择的用户画像 + 目标调用 AI 生成。',
    fields: [
      { key: 'goal', label: '训练目标', type: 'select', required: true, options: ['减脂', '增肌', '塑形', '保持健康', '康复恢复'] },
      { key: 'preferences', label: '偏好（可选）', type: 'text', required: false, placeholder: '例如：居家可做 / 器械齐全 / 每次 30 分钟' },
    ],
  },
  weeklyReport: {
    title: '健康周报',
    hint: '本周数据',
    desc: '对应真实前端入口：首页 → 健康报告 → 生成周报。AI 汇总本周饮食 / 运动 / 体重数据，输出健康评分、亮点、问题与下周建议（含图表）。',
    note: '需选择真实用户（右上角③），将读取该用户本周数据。',
    fields: [],
  },
  consult: {
    title: 'AI 健康咨询',
    hint: '输入问题',
    desc: '对应真实前端入口：首页 → AI 咨询。像聊天一样输入你的问题，AI 结合用户画像、今日身体指标、7 天趋势与知识库给出营养 / 饮食 / 运动建议。',
    note: '将按你选择的用户画像 + 问题调用 AI 咨询。',
    fields: [
      { key: 'question', label: '你的问题', type: 'text', textarea: true, required: true, placeholder: '例如：我今天吃了炸鸡，要注意什么？' },
    ],
  },
}

const modes = [
  { key: 'normal',           label: '标准模式' },
  { key: 'high_performance', label: '高性能' },
  { key: 'offline',          label: '离线演示' },
] as const

/** 真实 demo 用户：仅 test001-006（覆盖六种人群；除孕妇为女性外全部为男性）。 */
const exampleUsers = ref<{ label: string; value: number }[]>([])

/** 从后端用户列表动态加载 test001-006（保证 userId 与数据库一致）。 */
async function loadTestUsers() {
  try {
    const users = await api.admin.listUsers()
    const tests = (users || [])
      .filter(u => /^test\d{3}$/.test(u.username))
      .sort((a, b) => a.username.localeCompare(b.username))
      .map(u => ({
        label: `${u.username} · ${u.gender} ${u.age} · ${u.crowdType}`,
        value: u.userId
      }))
    exampleUsers.value = tests
  } catch (e: any) {
    ElMessage.error('加载 test 用户失败：' + (e?.response?.data?.message || e?.message || ''))
  }
}

/** 生成模式中文名 */
function modeLabel(m: string) {
  const found = modes.find(x => x.key === m)
  return found ? found.label : m
}

function funcLabel(k: string) {
  return funcList.find(f => f.key === k)?.label || k
}

// ==== 状态 ====
const sessionId = ref('sess-' + Math.random().toString(36).slice(2, 10))
const funcType = ref<FuncType>('article')
const mode = ref<'normal' | 'high_performance' | 'offline'>('normal')
const userId = ref<number | null>(null)

// 执行结果（流水线完成后展示）与用户详情弹窗
const finalResult = ref<PreviewApi.SnapshotEntity | null>(null)
const detailOpen = ref(false)
const detail = ref<any>(null)
const detailLoading = ref(false)

// ==== 说明 + 输入弹窗 ====
const inputModalOpen = ref(false)
const inputError = ref('')
const executing = ref(false)
const inputForm = reactive<Record<string, string>>({})

const currentForm = computed<FlowForm | null>(() => (inputModalOpen.value ? FLOW_FORMS[funcType.value] : null))

function openInputModal(k: FuncType) {
  funcType.value = k
  // 清空并重置输入表单
  Object.keys(inputForm).forEach(key => delete inputForm[key])
  inputError.value = ''
  // 预填默认值（select 有默认选项时方便演示）
  const fields = FLOW_FORMS[k].fields
  const goalDefault = fields.find(f => f.key === 'goal')?.options?.[0]
  if (goalDefault) inputForm['goal'] = goalDefault
  if (k === 'article') inputForm['audience'] = '普通人群'
  inputModalOpen.value = true
}
function closeInputModal() {
  inputModalOpen.value = false
  inputError.value = ''
}

/** 常见食材关键词表：从用户描述中提取真实食材（与后端 local_fallback / 食物库保持一致） */
const INGREDIENT_KEYWORDS = [
  '猪肉', '猪里脊', '猪排骨', '排骨', '鸡胸肉', '鸡胸', '鸡腿', '鸡蛋', '鸭蛋', '牛肉', '羊肉', '五花肉',
  '虾仁', '虾', '三文鱼', '鲈鱼', '鳕鱼', '带鱼', '鱿鱼', '龙利鱼', '鱼肉', '鳕鱼',
  '豆腐', '豆干', '豆浆', '黄豆', '腐竹',
  '西兰花', '西红柿', '番茄', '土豆', '青椒', '尖椒', '胡萝卜', '菠菜', '青菜', '白菜', '娃娃菜', '生菜', '黄瓜',
  '茄子', '冬瓜', '南瓜', '红薯', '玉米', '燕麦', '糙米', '大米', '米饭', '小米', '面条', '荞麦面', '藜麦',
  '牛奶', '酸奶', '奶酪', '蓝莓', '草莓', '苹果', '香蕉', '猕猴桃', '橙子',
  '核桃', '杏仁', '花生', '橄榄油', '食用油',
]

/** 从食谱需求描述中提取食材关键词列表；提取不到返回空数组。 */
function extractIngredients(description: string): string[] {
  const out: string[] = []
  if (!description) return out
  for (const kw of INGREDIENT_KEYWORDS) {
    if (description.includes(kw)) {
      if (!out.includes(kw)) out.push(kw)
    }
  }
  return out
}

/** 用真实输入构造该功能的 payload（骨架负责渲染字段，真实字段覆盖） */
function buildPayloadFromInput(k: FuncType): any {
  const skeleton = JSON.parse(JSON.stringify(EXAMPLE_PAYLOADS[k]))
  const set = (key: string, val: string) => { if (val && val.trim()) skeleton[key] = val.trim() }
  switch (k) {
    case 'article':
      set('topic', inputForm['topic'])
      set('audience', inputForm['audience'])
      if (inputForm['topic']) skeleton.title = inputForm['topic'] + ' · AI 生成科普指南'
      break
    case 'recipe':
      set('description', inputForm['description'])
      set('goal', inputForm['goal'])
      // 从描述中提取真实食材，作为 /food/recommend 的 ingredients 参数
      const ings = extractIngredients(inputForm['description'])
      if (ings.length) skeleton.ingredients = ings
      break
    case 'dietPlan':
      set('goal', inputForm['goal'])
      break
    case 'nutrition':
      // 无输入字段：直接用用户身份数据
      break
    case 'training':
      set('goal', inputForm['goal'])
      set('preferences', inputForm['preferences'])
      break
    case 'weeklyReport':
      // 无输入字段：直接用用户身份数据
      break
    case 'consult':
      set('question', inputForm['question'])
      set('topic', (inputForm['question'] || '').slice(0, 30))
      skeleton.summary = skeleton.summary || ((inputForm['question'] || '').slice(0, 60))
      break
    default:
      break
  }
  return skeleton
}

/** 核心动作：用真实输入启动后端流水线 */
async function handleStartExecute() {
  const k = funcType.value
  const fields = FLOW_FORMS[k].fields
  // 校验必填项
  for (const f of fields) {
    if (f.required && !(inputForm[f.key] || '').trim()) {
      inputError.value = `请填写${f.label}`
      return
    }
  }
  executing.value = true
  inputError.value = ''
  try {
    const payload = buildPayloadFromInput(k)
    finalResult.value = null
    stopPipelinePoller()
    pipelineStepOpen.value = new Set()
    traceId.value = null
    currentTrace.value = null
    currentTraceSteps.value = []

    const start = await PreviewApi.startPipeline({
      sessionId: sessionId.value,
      userId: userId.value ?? undefined,
      funcType: k,
      mode: mode.value,
      title: (payload as any)?.title || funcLabel(k) + ' · 示例',
      summary: (payload as any)?.summary || undefined,
      payload
    })
    traceId.value = start.traceId
    currentTrace.value = {
      traceId: start.traceId,
      funcType: start.funcType,
      sessionId: start.sessionId,
      mode: start.mode,
      createdAt: start.createdAt,
      totalSteps: start.totalSteps,
      done: false,
      steps: start.steps.map(s => ({ ...s }))
    }
    currentTraceSteps.value = currentTrace.value.steps
    pipelineStepOpen.value = new Set([1])
    ElMessage.info(`流水线已启动（${start.traceId}，共 ${start.totalSteps} 步）。左栏【后端实时流水线】正在推进……`)

    pollCount = 0
    pollTimer = setInterval(async () => {
      if (!traceId.value) return
      pollCount += 1
      if (pollCount > POLL_MAX_COUNT) {
        stopPipelinePoller()
        ElMessage.warning('流水线超时（已等待 180s 仍未完成），真实 AI 生成可能较慢，请稍后重试或查看后端日志。')
        return
      }
      try {
        const tr = await PreviewApi.pollPipelineTrace(traceId.value)
        currentTrace.value = tr
        currentTraceSteps.value = tr.steps || []
        const newlyDone = (tr.steps || []).filter(s => s.status === 'done' && !pipelineStepOpen.value.has(s.index)).slice(-2)
        if (newlyDone.length) {
          const next = new Set(pipelineStepOpen.value)
          newlyDone.forEach(s => next.add(s.index))
          pipelineStepOpen.value = next
        }
        if (tr.done) {
          stopPipelinePoller()
          if (tr.error) {
            ElMessage.warning('流水线失败：' + tr.error)
            return
          }
          if (tr.finalSnapshotId) {
            const sid = Number(tr.finalSnapshotId)
            try {
              const snap = await PreviewApi.getSnapshot(sid)
              finalResult.value = snap
              ElMessage.success(`流水线完成（${doneStepCount.value}/${tr.totalSteps} 步），快照 #${snap.id}。最终产出见右侧。`)
            } catch (e: any) {
              ElMessage.warning('流水线完成，但快照详情拉取失败：' + (e?.response?.data?.message || e?.message || ''))
            }
          } else {
            ElMessage.warning('流水线完成（未返回 snapshotId），请检查后端日志。')
          }
        }
      } catch (e: any) {
        if (pollCount % 10 === 0) {
          ElMessage.warning('轮询失败（已重试 ' + pollCount + ' 次）：' + (e?.response?.data?.message || e?.message || ''))
        }
      }
    }, POLL_INTERVAL_MS)
  } catch (e: any) {
    stopPipelinePoller()
    ElMessage.error('启动流水线失败：' + (e?.response?.data?.message || e?.message || ''))
  } finally {
    executing.value = false
    inputModalOpen.value = false
  }
}

// ==== 后端实时流水线状态 ====
const traceId = ref<string | null>(null)
const currentTrace = ref<PipelineTraceResult | null>(null)
const currentTraceSteps = ref<PipelineStep[]>([])
const pipelineStepOpen = ref<Set<number>>(new Set())
let pollTimer: any = null
let pollCount = 0
const POLL_INTERVAL_MS = 300
const POLL_MAX_COUNT = 600

const doneStepCount = computed(() => currentTraceSteps.value.filter(s => s.status === 'done').length)

function stepClass(status: string) {
  if (status === 'running') return 'bg-amber-50 border-amber-200 shadow-sm shadow-amber-100'
  if (status === 'done') return 'bg-white border-emerald-200'
  if (status === 'error') return 'bg-rose-50 border-rose-200'
  return 'bg-white/60 border-morandi-soft/60 opacity-60'
}
function stepDotClass(status: string) {
  if (status === 'running') return 'bg-amber-200 text-amber-800 animate-pulse'
  if (status === 'done') return 'bg-emerald-500 text-white'
  if (status === 'error') return 'bg-rose-500 text-white'
  return 'bg-morandi-soft text-morandi-lightText'
}
function toggleStepOpen(idx: number) {
  const next = new Set(pipelineStepOpen.value)
  if (next.has(idx)) next.delete(idx); else next.add(idx)
  pipelineStepOpen.value = next
}
function prettyJson(v: any): string {
  if (v == null) return '(空)'
  try {
    const s = typeof v === 'string' ? v : JSON.stringify(v, null, 2)
    return s && s.length ? s : '(空)'
  } catch {
    return String(v)
  }
}
/** 步骤 token 消耗明细：优先 step.extra（后端已写入），兼容 step.output.tokens。 */
function stepTokens(step: any): any {
  return step?.extra || step?.output?.tokens || null
}
/** 渲染输出 JSON 时剥离 tokens 字段（已单独用徽章展示，避免重复）。 */
function stripTokens(v: any): any {
  if (!v || typeof v !== 'object') return v
  if (Array.isArray(v)) return v.map(stripTokens)
  const clone: any = { ...v }
  delete clone.tokens
  return clone
}
function stopPipelinePoller() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

/** 数值格式化：保留 1 位小数；非数字原样返回。 */
function fmtNum(v: any): string {
  if (v == null || v === '') return '-'
  const n = Number(v)
  return isNaN(n) ? String(v) : n.toFixed(1)
}

/** 按份量换算食物热量（营养字段均为每 100g 值）。 */
function calcKcal(item: any): number {
  const kcal = Number(item?.calorie || 0)
  const w = Number(item?.eatWeight || 0)
  return (kcal * w) / 100
}

/** 按份量换算某项营养（protein / fat / carb / dietFiber 等）。 */
function calcNutrient(item: any, key: string): number {
  const v = Number(item?.[key] || 0)
  const w = Number(item?.eatWeight || 0)
  return (v * w) / 100
}

/** 用户详情：身份画像 + 身高体重 + 近两日饮食 + 近 5 条运动记录。 */
async function openDetail() {
  if (!userId.value) {
    ElMessage.warning('请先在③选择要查看的 test 用户')
    return
  }
  detailLoading.value = true
  try {
    const d = await api.admin.getFlowUserDetail(userId.value)
    detail.value = d
    detailOpen.value = true
  } catch (e: any) {
    ElMessage.error('加载用户详情失败：' + (e?.response?.data?.message || e?.message || ''))
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => { loadTestUsers() })
onBeforeUnmount(() => {
  stopPipelinePoller()
})
</script>

<style scoped>
.page-fade { animation: fadeIn 0.35s ease forwards; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
.fade-slide-enter-active, .fade-slide-leave-active { transition: all .25s ease; }
.fade-slide-enter-from, .fade-slide-leave-to { opacity: 0; transform: translateY(6px); }
</style>
