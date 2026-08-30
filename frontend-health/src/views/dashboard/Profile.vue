<template>
  <div class="user-page">
    <!-- ===== 深壳星轨带（四颗数据星球上下浮动） ===== -->
    <div class="db-band" ref="bandRef">
      <div class="db-glow db-glow--1" aria-hidden="true"></div>
      <div class="db-glow db-glow--2" aria-hidden="true"></div>

      <div class="db-top">
        <div class="star-crumbs">
          <span class="crumb-wrap">
            <button class="crumb-node" @click="goHome">
              <span class="nd"><LayoutGrid :size="12" /></span>首页
            </button>
          </span>
          <span class="crumb-wrap">
            <span class="crumb-link"></span>
            <button class="crumb-node" @click="goHub"><span class="nd"><UsersRound :size="12" /></span>用户中心</button>
          </span>
          <span class="crumb-wrap">
            <span class="crumb-link"></span>
            <span class="crumb-node hot"><span class="nd"><UserRound :size="13" /></span>个人资料</span>
          </span>
        </div>
        <div class="db-top-right">
          <span class="db-date"><Camera :size="12" />保存即写入今日快照</span>
        </div>
      </div>

      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 104" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 52 C 300 8, 440 8, 560 52 S 830 96, 960 52 S 1130 8, 1200 52" />
        </svg>

        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><Orbit :size="19" /></span>
            <span class="tt"><b>星核星环</b><span>PROFILE HALO</span></span>
          </div>
        </div>

        <!-- 四颗身体数据星球：点击弹出对应详情气泡 -->
        <div
          v-for="(b, i) in balls" :key="b.key"
          class="db-station-wrap"
          :style="{ left: stationLeft(i) + '%' }"
        >
          <div class="db-station-float" :style="floatStyle(i)">
            <button
              class="db-station"
              :class="{ now: bubbleKey === b.key }"
              :aria-label="details[b.key].name"
              @click="showBubble(b.key)"
            >
              <component :is="b.icon" :size="15" />
              <span class="nm">{{ stationVal(b.key) }}</span>
              <span class="ds">{{ details[b.key].name }} · 点击查看详情</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区（星核星环 + AI 模式） ===== -->
    <div class="db-paper" ref="paperRef">
      <div class="db-head" data-anim>
        <div class="sec-t">星核星环 · 一环读尽身体数据</div>
        <div class="db-pills">
          <span class="pill">人群 <b>{{ form.crowdType || '—' }}</b></span>
          <span class="pill">当前身份 <b>{{ operateAsLabel }}</b></span>
        </div>
      </div>

      <div v-if="toastMsg" class="db-toast" data-anim>{{ toastMsg }}</div>

      <div class="db-blocks">
        <!-- 左：星核星环 -->
        <div class="db-block main" data-anim>
          <div class="halo-stage" :class="{ paused: !!bubbleKey }">
            <!-- 金色虚线轨道 + 四颗数据球（公转 46s · 球体反向自转保持文字朝上） -->
            <div class="halo-orbit">
              <svg viewBox="0 0 272 272" aria-hidden="true">
                <circle cx="136" cy="136" r="126" />
              </svg>
              <div
                v-for="(b, i) in balls" :key="b.key"
                class="halo-pos"
                :style="{ transform: `rotate(${i * 90}deg) translate(126px) rotate(${-i * 90}deg)` }"
              >
                <div class="halo-ball-spin">
                  <button
                    class="halo-ball"
                    :class="{ sel: bubbleKey === b.key }"
                    :aria-label="details[b.key].name"
                    @click="showBubble(b.key)"
                  >
                    <component :is="b.icon" :size="15" />
                    <span class="bv">{{ ballVal(b.key) }}</span>
                    <span class="bu">{{ units[b.key] }}</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- 中心：本我恒星（点头像更换） -->
            <div class="halo-core" @click="pickAvatar" title="点击更换头像">
              <div class="ava">
                <img v-if="currentAvatar" :src="resolveAvatarUrl(currentAvatar)" alt="头像" />
                <template v-else>{{ usernameInitial }}</template>
              </div>
              <span class="nm">{{ usernameText || '未登录' }}<i>USER #{{ userInfo.userId || '—' }}</i></span>
            </div>

            <!-- 详情气泡：头像正中弹出 · 无箭头方框 · 无灰遮罩 -->
            <Transition name="halo-bubble">
              <div v-if="bubbleKey" class="halo-bubble" @click.stop>
                <div class="hb-head">
                  <component :is="details[bubbleKey].icon" :size="13" />
                  {{ details[bubbleKey].name }}
                  <span class="hb-tag">{{ details[bubbleKey].editable ? '点击可修改' : '自动计算' }}</span>
                  <button class="hb-close" aria-label="关闭" @click="hideBubble">×</button>
                </div>
                <div class="hb-main">
                  <b>{{ bubbleKey ? ballVal(bubbleKey) : '' }}</b>
                  <span>{{ details[bubbleKey].unit }}</span>
                  <span class="hb-trend" :class="trendClass(bubbleKey)">{{ trendText(bubbleKey) }}</span>
                </div>
                <!-- 正常范围带（体重 / BMI） -->
                <div v-if="details[bubbleKey].range" class="hb-range">
                  <div class="bar"><i :style="{ left: rangePin(bubbleKey) + '%' }"></i></div>
                  <div class="cap">
                    <span>{{ details[bubbleKey].range.min }}</span>
                    <span>正常范围带</span>
                    <span>{{ details[bubbleKey].range.max }}</span>
                  </div>
                </div>
                <!-- 球内编辑 -->
                <div v-if="details[bubbleKey].editable" class="hb-edit">
                  <input
                    ref="bubbleInputRef"
                    v-model="editVal"
                    type="number"
                    :step="details[bubbleKey].step"
                    :min="details[bubbleKey].min"
                    :max="details[bubbleKey].max"
                    @keyup.enter="saveBubble"
                  />
                  <span class="un">{{ details[bubbleKey].unit }}</span>
                  <button class="hb-save" :disabled="saving" @click="saveBubble">
                    <Check :size="12" />更新
                  </button>
                </div>
                <div class="hb-note">{{ details[bubbleKey].note }}</div>
              </div>
            </Transition>

            <span class="halo-hint">悬停暂停公转 · 点击星球查看并修改数据</span>
          </div>
        </div>

        <!-- 右：AI 处理模式 + 基础属性 -->
        <div class="db-block side" data-anim>
          <div class="db-side-head"><b>AI 处理模式</b></div>
          <div class="u-ai">
            <div class="txt">
              <b>{{ userStore.highPerformance ? '高性能模式' : '普通模式' }}</b>
              <p>
                {{ userStore.highPerformance
                  ? '云端直连大模型，识别更快更准，但消耗云端额度'
                  : '优先本地大模型生成、云端兜底，质量更稳且省额度' }}
              </p>
            </div>
            <button
              class="mode-switch"
              :class="{ 'is-on': userStore.highPerformance }"
              role="switch"
              :aria-checked="userStore.highPerformance"
              @click="toggleAiMode"
            >
              <span class="mode-knob"></span>
            </button>
          </div>

          <div class="meta-divider"></div>
          <div class="db-side-head"><b>基础属性</b></div>
          <div class="meta-grid">
            <label class="meta-field">
              <span>性别</span>
              <select v-model="form.gender">
                <option value="男">男</option>
                <option value="女">女</option>
              </select>
            </label>
            <label class="meta-field">
              <span>人群类型</span>
              <select v-model="form.crowdType">
                <option v-for="c in crowdOptions" :key="c.value" :value="c.value">{{ c.label }}</option>
              </select>
            </label>
          </div>
          <button class="btn-gold meta-save" :disabled="savingMeta" @click="saveMeta">
            <Check :size="13" />{{ savingMeta ? '保存中...' : '保存属性' }}
          </button>

          <div class="hb-note" style="margin-top:14px;padding-top:12px;border-top:1px dashed rgba(184,134,59,.25)">
            提示：点击左侧任意数据星球，即可在气泡内直接查看详情并修改数值，更新后自动写入今日快照。
          </div>
        </div>
      </div>
    </div>

    <!-- 裁剪弹窗 -->
    <Teleport to="body">
      <Transition name="dlg-overlay">
        <div v-if="cropperVisible" class="cropper-mask" @click.self="closeCropper">
          <Transition name="dlg-content" appear>
            <div v-if="cropperVisible" class="cropper-dialog">
              <div class="cropper-header">
                <div class="flex items-center gap-2">
                  <span class="w-7 h-7 rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-white text-sm font-bold">剪</span>
                  <h4 class="text-base font-semibold text-slate-800">裁剪头像</h4>
                </div>
                <button class="cropper-close-btn" @click="closeCropper" title="关闭">×</button>
              </div>

              <div class="cropper-body">
                <div v-if="!originImg" class="cropper-empty">
                  <div class="cropper-empty-icon"></div>
                  <div class="text-sm text-slate-500">正在加载图片...</div>
                </div>
                <VueCropper
                  v-show="!!originImg"
                  ref="cropperRef"
                  :img="originImg"
                  output-size="1"
                  :auto-crop="true"
                  :fixed="true"
                  :fixed-number="[1, 1]"
                  :fixed-box="false"
                  :can-scale="true"
                  :can-move="true"
                  :can-move-box="true"
                  :original="false"
                  :center-box="false"
                  :high="true"
                  mode="contain"
                  background-color="#fff"
                />
              </div>

              <div class="cropper-tips">
                <span> 提示：可拖动裁剪框位置（上下左右均可）、滚轮缩放图片，裁剪框已锁定 1:1 正方形</span>
              </div>

              <div class="cropper-footer">
                <button class="cropper-btn cropper-btn-ghost" @click="closeCropper" :disabled="uploading">取消</button>
                <button class="cropper-btn cropper-btn-primary" @click="confirmCropAndUpload" :disabled="uploading">
                  <span v-if="uploading" class="cropper-spinner"></span>
                  <span>{{ uploading ? '上传中...' : '确认并上传' }}</span>
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import {
  LayoutGrid, UsersRound, UserRound, Camera, Orbit,
  Cake, Ruler, Weight, Gauge, Check
} from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'
import { ElMessage } from 'element-plus'
import 'element-plus/es/components/message/style/css'
import { VueCropper } from 'vue-cropper'
import 'vue-cropper/dist/index.css'
import { CROWD_OPTIONS } from '../../constants'

// ====== 类型定义 ======
type CropperRef = InstanceType<typeof VueCropper> | null

const userStore = useUserStore()
const router = useRouter()
const crowdOptions = [...CROWD_OPTIONS]

function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'user' } }) }

// ====== 身体数据状态（星核星环） ======
const userInfo = ref<any>({})
const form = ref<any>({
  gender: '男',
  age: 18,
  height: 165,
  weight: 65,
  crowdType: '普通人'
})
const saving = ref(false)
const savingMeta = ref(false)
const toastMsg = ref('')

const usernameText = computed(() => userInfo.value.username || userStore.user?.username || '')
const usernameInitial = computed(() => (usernameText.value ? usernameText.value.slice(0, 1).toUpperCase() : 'U'))
const currentAvatar = computed(() => userInfo.value.avatar || userStore.avatar || '')
const operateAsLabel = computed(() => {
  if (userStore.actAsUserId != null) {
    return `代 #${userStore.actAsUserId} 操作`
  }
  return '本人'
})

const balls = [
  { key: 'age', icon: Cake },
  { key: 'height', icon: Ruler },
  { key: 'weight', icon: Weight },
  { key: 'bmi', icon: Gauge }
] as const
type BallKey = typeof balls[number]['key']

const units: Record<BallKey, string> = {
  age: '岁 · 年龄',
  height: 'cm · 身高',
  weight: 'kg · 体重',
  bmi: 'BMI'
}

const details: Record<BallKey, any> = {
  age: {
    icon: Cake, name: '年龄', unit: '岁', editable: true, step: 1, min: 1, max: 120,
    note: '年龄参与 BMR（基础代谢）计算，是营养推荐的核心参数之一。'
  },
  height: {
    icon: Ruler, name: '身高', unit: 'cm', editable: true, step: 1, min: 80, max: 250,
    note: '参与 BMI 与 BMR 计算。成年人身高通常稳定，显著波动建议咨询医生。'
  },
  weight: {
    icon: Weight, name: '体重', unit: 'kg', editable: true, step: 0.1, min: 20, max: 300,
    note: '每次保存都会写入今日快照，可在「健康档案 → 身体指标」查看趋势线与周变化。',
    range: { min: 50, max: 80 }
  },
  bmi: {
    icon: Gauge, name: 'BMI 体脂指数', unit: '', editable: false,
    note: '由身高体重实时计算：BMI = 体重(kg) ÷ 身高²(m²)。偏瘦 <18.5 · 正常 18.5~24 · 超重 24~28 · 肥胖 ≥28。',
    range: { min: 14, max: 36 }
  }
}

const bmiVal = computed(() => {
  const h = Number(form.value.height) / 100
  const w = Number(form.value.weight)
  if (!h || !w) return 0
  return w / (h * h)
})

function ballVal(key: BallKey): string | number {
  if (key === 'bmi') return bmiVal.value ? bmiVal.value.toFixed(1) : '—'
  return form.value[key]
}

function stationVal(key: BallKey): string {
  if (key === 'age') return `${form.value.age} 岁`
  if (key === 'height') return `${form.value.height} cm`
  if (key === 'weight') return `${form.value.weight} kg`
  return bmiVal.value ? bmiVal.value.toFixed(1) : '—'
}

function bmiCategory(): string {
  const v = bmiVal.value
  if (!v) return '—'
  if (v < 18.5) return '偏瘦'
  if (v < 24) return '正常范围'
  if (v < 28) return '超重'
  return '肥胖'
}

function trendText(key: BallKey): string {
  if (key === 'age') return '按年 +1'
  if (key === 'height') return '稳定 ±0.0'
  if (key === 'weight') return '↓ 0.4 较上次快照'
  return bmiCategory()
}

function trendClass(key: BallKey): string {
  if (key === 'bmi') {
    const c = bmiCategory()
    if (c === '正常范围') return 'down'
    if (c === '—') return 'flat'
    return 'up'
  }
  if (key === 'weight') return 'down'
  return 'flat'
}

function rangePin(key: BallKey): number {
  const d = details[key].range
  if (!d) return 0
  const pin = key === 'bmi' ? bmiVal.value : Number(form.value.weight)
  return Math.max(2, Math.min(96, ((pin - d.min) / (d.max - d.min)) * 100))
}

// ====== 详情气泡（头像正中弹出 · 无箭头） ======
const bubbleKey = ref<BallKey | null>(null)
const editVal = ref<string>('')
const bubbleInputRef = ref<HTMLInputElement | null>(null)

function showBubble(key: BallKey) {
  bubbleKey.value = key
  editVal.value = String(form.value[key] ?? '')
  nextTick(() => {
    bubbleInputRef.value?.focus()
    bubbleInputRef.value?.select()
  })
}

function hideBubble() {
  bubbleKey.value = null
}

async function saveBubble() {
  const key = bubbleKey.value
  if (!key || saving.value) return
  const d = details[key]
  const v = parseFloat(editVal.value)
  if (!Number.isFinite(v) || v < d.min || v > d.max) {
    showToast(`请输入 ${d.min} ~ ${d.max} 之间的数值`)
    return
  }
  saving.value = true
  try {
    form.value[key] = Math.round(v * 10) / 10
    await api.profile.update({
      gender: form.value.gender,
      age: Number(form.value.age) || null,
      height: Number(form.value.height) || null,
      weight: Number(form.value.weight) || null,
      crowdType: form.value.crowdType
    })
    showToast(`已更新${d.name} · 并写入今日身体指标快照`)
    await userStore.loadUserProfile?.()
  } catch (e: any) {
    showToast(e?.message || '保存失败，请重试')
  } finally {
    saving.value = false
  }
}

async function saveMeta() {
  if (savingMeta.value) return
  savingMeta.value = true
  try {
    await api.profile.update({
      gender: form.value.gender,
      age: Number(form.value.age) || null,
      height: Number(form.value.height) || null,
      weight: Number(form.value.weight) || null,
      crowdType: form.value.crowdType
    })
    showToast('基础属性已保存 · 并写入今日身体指标快照')
    await userStore.loadUserProfile?.()
  } catch (e: any) {
    showToast(e?.message || '保存失败，请重试')
  } finally {
    savingMeta.value = false
  }
}

function showToast(msg: string) {
  toastMsg.value = msg
  setTimeout(() => { toastMsg.value = '' }, 3200)
}

// ====== 加载资料 ======
function toNumber(v: any, fallback: number): number {
  const n = Number(v)
  return Number.isFinite(n) ? n : fallback
}

async function loadInfo() {
  try {
    const info: any = await api.profile.getInfo()
    if (info) {
      userInfo.value = info
      form.value.gender = info.gender || '男'
      form.value.age = toNumber(info.age, 18)
      form.value.height = toNumber(info.height, 165)
      form.value.weight = toNumber(info.weight, 65)
      form.value.crowdType = info.crowdType || info.crowd_type || '普通人'
    }
  } catch (e: any) {
    showToast(e?.message || '资料加载失败')
  }
}

// ====== AI 处理模式 ======
function toggleAiMode() {
  userStore.setHighPerformance(!userStore.highPerformance)
  showToast(userStore.highPerformance ? '已切换为高性能模式（云端直连）' : '已切换为普通模式')
}

// ====== 头像上传 & 裁剪（点击头像恒星触发） ======
const cropperVisible = ref(false)
const originImg = ref<string>('')
const cropperRef = ref<CropperRef>(null)
const uploading = ref(false)

// 上传文件大小上限：5MB
const MAX_SIZE_MB = 5
const MAX_SIZE = MAX_SIZE_MB * 1024 * 1024
const ALLOWED_EXT = ['jpg', 'jpeg', 'png', 'webp']

function pickAvatar() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = () => {
    const file = input.files?.[0]
    if (!file) return
    const fileName = file.name || ''
    const ext = fileName.includes('.') ? fileName.split('.').pop()!.toLowerCase() : ''
    if (!ALLOWED_EXT.includes(ext)) {
      ElMessage.error(`仅支持 ${ALLOWED_EXT.join('/').toUpperCase()} 格式`)
      return
    }
    if (file.size > MAX_SIZE) {
      ElMessage.error(`图片不能超过 ${MAX_SIZE_MB}MB`)
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      originImg.value = reader.result as string
      cropperVisible.value = true
    }
    reader.onerror = () => ElMessage.error('图片读取失败，请重试')
    reader.readAsDataURL(file)
  }
  input.click()
}

function closeCropper() {
  if (uploading.value) return
  cropperVisible.value = false
  originImg.value = ''
}

function confirmCropAndUpload() {
  if (uploading.value || !cropperRef.value) return
  uploading.value = true
  try {
    cropperRef.value.getCropBlob(async (blob: Blob | null) => {
      try {
        if (!blob) {
          ElMessage.error('裁剪结果为空')
          uploading.value = false
          return
        }
        const compressed = await compressImage(blob, 512, 0.82)
        await uploadAvatarBlob(compressed)
      } catch (e: any) {
        console.error(e)
        const msg = e?.message || '上传失败，请稍后重试'
        ElMessage.error(/network|Network|timeout/i.test(msg) ? '网络异常，请检查连接后重试' : msg)
      } finally {
        uploading.value = false
      }
    })
  } catch (e: any) {
    console.error(e)
    uploading.value = false
    ElMessage.error('裁剪失败，请重试')
  }
}

function compressImage(srcBlob: Blob, maxSide: number, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      try {
        let { width, height } = img
        if (width > maxSide || height > maxSide) {
          if (width >= height) {
            height = Math.round(height * (maxSide / width))
            width = maxSide
          } else {
            width = Math.round(width * (maxSide / height))
            height = maxSide
          }
        }
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')
        if (!ctx) return reject(new Error('当前环境不支持 Canvas'))
        ctx.fillStyle = '#ffffff'
        ctx.fillRect(0, 0, width, height)
        ctx.drawImage(img, 0, 0, width, height)
        canvas.toBlob(
          (b) => {
            if (b) resolve(b)
            else reject(new Error('图片压缩结果为空'))
          },
          'image/jpeg',
          quality
        )
      } catch (e) {
        reject(e)
      }
    }
    img.onerror = () => reject(new Error('图片解码失败'))
    img.src = URL.createObjectURL(srcBlob)
  })
}

async function uploadAvatarBlob(blob: Blob) {
  const uid = userStore.user?.user_id || userStore.user?.userId || userStore.user?.id
  if (!uid) {
    ElMessage.error('登录状态异常，请重新登录')
    return
  }
  const fd = new FormData()
  fd.append('avatar', blob, 'avatar.jpg')
  fd.append('userId', String(uid))
  const avatarUrl: any = await api.file.uploadAvatar(fd)
  if (avatarUrl) {
    userInfo.value.avatar = avatarUrl
    userStore.updateAvatar(avatarUrl)
    ElMessage.success('头像上传成功')
    closeCropper()
  } else {
    ElMessage.error('上传失败，未收到返回的头像地址')
  }
}

function resolveAvatarUrl(url: string): string {
  if (!url) return ''
  if (/^(https?:|data:)/i.test(url)) return url
  return url
}

// ====== 星轨站点分布 & 漂浮节奏 ======
function stationLeft(i: number): number {
  return 34 + i * (60 / 3)
}
function floatStyle(i: number): Record<string, string> {
  return {
    animationDuration: (4.6 + (i % 4) * 0.45) + 's',
    animationDelay: -(i * 0.9) + 's'
  }
}

// ====== 入场动效（面包屑点亮 → 星球弹出 → 浅芯浮起） ======
const bandRef = ref<HTMLElement | null>(null)
const paperRef = ref<HTMLElement | null>(null)

function animateEntrance() {
  const band = bandRef.value
  const paper = paperRef.value
  if (band) {
    gsap.fromTo(band.querySelectorAll('.crumb-node'),
      { opacity: 0, y: 12, scale: 0.6 },
      { opacity: 1, y: 0, scale: 1, duration: 0.45, stagger: 0.15, ease: 'back.out(2)' })
    gsap.fromTo(band.querySelectorAll('.db-top-right, .db-core-wrap'),
      { opacity: 0, y: 14 },
      { opacity: 1, y: 0, duration: 0.6, delay: 0.15, ease: 'power3.out' })
    gsap.fromTo(band.querySelectorAll('.db-station-wrap'),
      { scale: 0, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.5, stagger: 0.08, delay: 0.35, ease: 'back.out(1.7)', clearProps: 'opacity,transform' })
  }
  if (paper) {
    gsap.fromTo(paper.querySelectorAll('[data-anim]'),
      { opacity: 0, y: 24 },
      { opacity: 1, y: 0, duration: 0.7, stagger: 0.1, delay: 0.35, ease: 'power3.out' })
    gsap.fromTo(paper.querySelectorAll('.halo-ball'),
      { scale: 0, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.5, stagger: 0.07, delay: 0.55, ease: 'back.out(1.7)', clearProps: 'opacity,transform' })
  }
}

onMounted(async () => {
  animateEntrance()
  await loadInfo()
})
</script>

<style scoped>
.user-page {
  position: relative;
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
}

/* ========== 深壳星轨带 ========== */
.db-band {
  position: relative;
  padding: 14px 24px 10px;
  border-radius: 20px;
  overflow: hidden;
  isolation: isolate;
  background:
    radial-gradient(circle at 12% 24%, rgba(232, 185, 115, 0.1) 0%, transparent 44%),
    radial-gradient(circle at 88% 88%, rgba(179, 107, 42, 0.08) 0%, transparent 46%),
    linear-gradient(180deg, #14110C 0%, #0E0C0A 100%);
  border: 1px solid rgba(232, 185, 115, 0.14);
  color: #F6EAD6;
}
.db-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(50px);
  pointer-events: none;
  z-index: 0;
}
.db-glow--1 {
  width: 200px; height: 200px;
  right: -60px; top: -110px;
  background: rgba(232, 185, 115, 0.12);
  animation: dbGlowFloat 9s ease-in-out infinite alternate;
}
.db-glow--2 {
  width: 170px; height: 170px;
  left: -70px; bottom: -100px;
  background: rgba(179, 107, 42, 0.1);
  animation: dbGlowFloat 11s ease-in-out infinite alternate-reverse;
}
@keyframes dbGlowFloat {
  from { transform: translate3d(0, 0, 0) scale(1); }
  to   { transform: translate3d(16px, 10px, 0) scale(1.12); }
}

/* ---- 顶行 ---- */
.db-top {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 10px;
}
.star-crumbs { display: flex; align-items: center; }
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
.db-top-right { margin-left: auto; display: flex; align-items: center; gap: 12px; }
.db-date {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px; color: #B9A78A;
  border: 1px solid rgba(217, 162, 74, 0.3);
  background: rgba(217, 162, 74, 0.08);
  border-radius: 999px; padding: 3px 10px;
}
.db-date svg { color: #E8B973; flex-shrink: 0; }

/* ---- 星轨带 ---- */
.db-const {
  position: relative;
  z-index: 1;
  height: 104px;
  margin-top: 6px;
}
.db-line {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  overflow: visible;
}
.db-line path {
  fill: none;
  stroke: rgba(217, 162, 74, 0.35);
  stroke-width: 1.2;
  stroke-dasharray: 5 6;
  vector-effect: non-scaling-stroke;
}

/* ---- 核心恒星 ---- */
.db-core-wrap {
  position: absolute; left: 4px; top: 50%;
  margin-top: -23px; z-index: 2;
}
.db-core {
  display: flex; align-items: center; gap: 10px;
  animation: dbFloat 6.4s ease-in-out infinite alternate;
  animation-delay: -0.6s;
}
.db-core .star {
  width: 46px; height: 46px; border-radius: 50%;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(232, 185, 115, 0.55);
  display: flex; align-items: center; justify-content: center;
  color: #E8B973;
  box-shadow: 0 0 22px rgba(217, 162, 74, 0.32);
  animation: dbBreath 3.2s ease-in-out infinite;
}
@keyframes dbBreath {
  0%, 100% { box-shadow: 0 0 18px rgba(217, 162, 74, 0.3); }
  50% { box-shadow: 0 0 34px rgba(217, 162, 74, 0.52); }
}
.db-core .tt b {
  display: block; font-size: 12.5px; color: #F6EAD6;
  font-weight: 700; letter-spacing: 0.08em;
}
.db-core .tt span {
  display: block; margin-top: 2px; font-size: 9.5px;
  color: #9A8A6C; letter-spacing: 0.12em;
}

/* ---- 数据星球（星轨带） ---- */
.db-station-wrap {
  position: absolute; top: 50%;
  width: 44px; height: 44px;
  margin: -22px 0 0 -22px;
  z-index: 3;
}
.db-station-float {
  width: 100%; height: 100%;
  animation: dbFloat 4.6s ease-in-out infinite alternate;
}
@keyframes dbFloat {
  from { transform: translateY(4px); }
  to   { transform: translateY(-8px); }
}
.db-station {
  position: relative;
  width: 44px; height: 44px;
  border-radius: 50%;
  cursor: pointer;
  background: rgba(24, 19, 12, 0.95);
  border: 1px solid rgba(217, 162, 74, 0.45);
  color: #E8B973;
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.5, 0.5, 1), border-color 0.3s ease, box-shadow 0.3s ease;
}
.db-station .nm {
  position: absolute; top: -26px; left: 50%;
  transform: translateX(-50%);
  font-size: 10px; color: #F0E2C4;
  white-space: nowrap; letter-spacing: 0.06em;
  opacity: 0.72; transition: opacity 0.3s ease, color 0.3s ease;
}
.db-station .ds {
  position: absolute; top: calc(100% + 10px); left: 50%;
  transform: translateX(-50%) translateY(4px);
  white-space: nowrap;
  font-size: 9.5px; color: #F6EAD6;
  background: rgba(24, 19, 12, 0.95);
  border: 1px solid rgba(217, 162, 74, 0.4);
  padding: 2px 9px; border-radius: 999px;
  opacity: 0; transition: opacity 0.28s ease, transform 0.28s ease;
  pointer-events: none;
}
.db-station:hover {
  transform: scale(1.14);
  border-color: #E8B973;
  box-shadow: 0 0 0 5px rgba(217, 162, 74, 0.14), 0 10px 26px rgba(217, 162, 74, 0.32);
}
.db-station:hover .ds { opacity: 1; transform: translateX(-50%) translateY(0); }
.db-station:hover .nm { opacity: 1; color: #E8B973; }
.db-station.now {
  border-color: #E8B973;
  box-shadow: 0 0 0 6px rgba(217, 162, 74, 0.14), 0 0 22px rgba(217, 162, 74, 0.4);
}
.db-station.now .nm { opacity: 1; color: #E8B973; font-weight: 700; }

/* ========== 浅芯工作区 ========== */
.db-paper {
  position: relative;
  background:
    radial-gradient(circle at 18% 0%, rgba(184, 134, 59, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 86% 100%, rgba(201, 143, 62, 0.06) 0%, transparent 44%),
    linear-gradient(180deg, #F8F4EA 0%, #F2EBDC 100%);
  border: 1px solid rgba(232, 185, 115, 0.24);
  border-radius: 20px;
  padding: 18px 22px 22px;
  box-shadow: 0 30px 60px -34px rgba(90, 70, 40, 0.28);
}
.db-head {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.sec-t {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 700; color: #2A2620;
  letter-spacing: 0.02em;
}
.sec-t::before {
  content: ''; width: 3px; height: 14px; border-radius: 99px;
  background: linear-gradient(180deg, #E8B973, #B8863B);
}
.db-pills { margin-left: auto; display: flex; gap: 8px; flex-wrap: wrap; }
.pill {
  font-size: 11px; color: #6E6350;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(184, 134, 59, 0.2);
  padding: 4px 12px; border-radius: 999px;
  display: inline-flex; align-items: center; gap: 5px;
}
.pill b { color: #B8863B; font-weight: 700; }

.db-toast {
  margin-top: 12px;
  display: inline-flex; align-items: center;
  background: rgba(127, 174, 142, 0.12);
  border: 1px solid rgba(127, 174, 142, 0.35);
  border-radius: 999px; padding: 8px 16px;
  font-size: 12px; color: #2F7D5B; font-weight: 600;
  animation: toastPop 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes toastPop {
  from { transform: scale(0.85) translateY(-8px); opacity: 0; }
  to   { transform: scale(1) translateY(0); opacity: 1; }
}

.db-blocks {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 12px;
  margin-top: 14px;
}
.db-block {
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(184, 134, 59, 0.16);
  border-radius: 16px;
  padding: 16px 18px;
}
.db-side-head {
  display: flex; align-items: baseline; gap: 8px;
}
.db-side-head b { font-size: 13px; color: #2A2620; font-weight: 700; }

/* ===== 星核星环 ===== */
.halo-stage {
  position: relative;
  height: 378px;
  display: flex; align-items: center; justify-content: center;
  user-select: none;
}
.halo-orbit {
  position: absolute; left: 50%; top: 50%;
  width: 272px; height: 272px;
  margin: -136px 0 0 -136px;
  animation: haloSpin 46s linear infinite;
  pointer-events: none;
  z-index: 4;
}
.halo-stage:hover .halo-orbit,
.halo-stage:hover .halo-ball-spin,
.halo-stage.paused .halo-orbit,
.halo-stage.paused .halo-ball-spin {
  animation-play-state: paused;
}
@keyframes haloSpin { to { transform: rotate(360deg); } }
.halo-orbit svg {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  overflow: visible;
}
.halo-orbit circle {
  fill: none;
  stroke: rgba(184, 134, 59, 0.4);
  stroke-width: 1.2;
  stroke-dasharray: 4 7;
}
.halo-pos {
  position: absolute; left: 50%; top: 50%;
  width: 0; height: 0;
}
/* 内层反向自转：抵消公转，球上文字始终朝上 */
.halo-ball-spin {
  animation: haloSpin 46s linear infinite reverse;
}
.halo-ball {
  position: absolute; left: -31px; top: -31px;
  width: 62px; height: 62px;
  border-radius: 50%;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.9);
  border: 1.5px solid rgba(184, 134, 59, 0.4);
  box-shadow: 0 6px 16px -6px rgba(90, 70, 40, 0.35);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px;
  transition: transform 0.3s cubic-bezier(0.34, 1.5, 0.5, 1), border-color 0.3s, box-shadow 0.3s;
  pointer-events: auto;
  font-family: inherit;
}
.halo-ball svg { width: 15px; height: 15px; color: #B8863B; }
.halo-ball .bv {
  font-size: 10.5px; font-weight: 800; color: #2A2620;
  font-family: 'Noto Serif SC', serif;
}
.halo-ball .bu {
  font-size: 8px; color: rgba(42, 38, 32, 0.4);
  letter-spacing: 0.04em; margin-top: -2px;
}
.halo-ball:hover {
  transform: scale(1.13);
  border-color: #E8B973;
  box-shadow: 0 0 0 5px rgba(217, 162, 74, 0.15), 0 10px 24px rgba(184, 134, 59, 0.35);
}
.halo-ball.sel {
  border-color: #E8B973;
  box-shadow: 0 0 0 5px rgba(217, 162, 74, 0.18), 0 0 22px rgba(217, 162, 74, 0.45);
}

/* 中心：本我恒星 */
.halo-core {
  position: relative; z-index: 6;
  width: 120px; text-align: center;
  cursor: pointer;
}
.halo-core .ava {
  width: 96px; height: 96px; margin: 0 auto;
  border-radius: 50%;
  overflow: hidden;
  background: radial-gradient(circle at 34% 28%, #F6E3B4, #E0B268 52%, #B8863B 88%);
  color: #fff;
  font-size: 36px; font-weight: 900;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 0 6px rgba(255, 255, 255, 0.8), 0 0 30px rgba(217, 162, 74, 0.5);
  animation: coreBreath 3.4s ease-in-out infinite;
}
.halo-core .ava img {
  width: 100%; height: 100%;
  object-fit: cover;
}
@keyframes coreBreath {
  0%, 100% { box-shadow: 0 0 0 6px rgba(255, 255, 255, 0.8), 0 0 24px rgba(217, 162, 74, 0.45); }
  50% { box-shadow: 0 0 0 6px rgba(255, 255, 255, 0.8), 0 0 56px rgba(217, 162, 74, 0.72); }
}
.halo-core .nm {
  margin-top: 8px;
  font-size: 12.5px; font-weight: 700; color: #2A2620;
}
.halo-core .nm i {
  font-style: normal; display: block;
  font-size: 9px; font-weight: 500; color: rgba(42, 38, 32, 0.4);
  letter-spacing: 0.1em; margin-top: 1px;
}
.halo-core:hover .ava { filter: brightness(1.06); }
.halo-hint {
  position: absolute; bottom: -2px; left: 50%;
  transform: translateX(-50%);
  font-size: 9.5px; color: rgba(42, 38, 32, 0.35);
  letter-spacing: 0.06em; white-space: nowrap;
}

/* 详情气泡：头像正中弹出 · 无箭头方框 · 无灰遮罩 */
.halo-bubble {
  position: absolute; z-index: 20;
  left: 50%; top: 50%;
  transform: translate(-50%, -50%);
  width: 238px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(184, 134, 59, 0.45);
  border-radius: 16px;
  padding: 14px 16px 13px;
  box-shadow: 0 24px 54px -18px rgba(90, 70, 40, 0.5);
}
.halo-bubble-enter-active { animation: bubblePop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.halo-bubble-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.halo-bubble-leave-to {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.85);
}
@keyframes bubblePop {
  from { transform: translate(-50%, -50%) scale(0.72); opacity: 0; }
  to   { transform: translate(-50%, -50%) scale(1); opacity: 1; }
}
.hb-head {
  display: flex; align-items: center; gap: 7px;
  font-size: 11.5px; font-weight: 700; color: #8A6428;
}
.hb-head svg { width: 13px; height: 13px; }
.hb-close {
  margin-left: auto;
  width: 20px; height: 20px; border-radius: 50%;
  border: none; background: rgba(184, 134, 59, 0.12);
  color: #8C7A5E; font-size: 13px; line-height: 1;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.hb-close:hover { background: rgba(184, 134, 59, 0.28); color: #B8863B; }
.hb-tag {
  font-size: 9px; font-weight: 600; color: #8C7A5E;
  background: rgba(184, 134, 59, 0.1);
  border-radius: 999px; padding: 2px 7px;
}
.hb-edit {
  display: flex; align-items: center; gap: 8px; margin-top: 10px;
}
.hb-edit input {
  flex: 1; min-width: 0;
  padding: 7px 10px; border-radius: 9px;
  border: 1px solid rgba(184, 134, 59, 0.35);
  font-size: 13px; font-weight: 700; color: #2A2620;
  outline: none; background: #fff;
}
.hb-edit input:focus { border-color: #B8863B; }
.hb-edit .un { font-size: 10.5px; color: rgba(42, 38, 32, 0.45); }
.hb-save {
  border: none; cursor: pointer;
  padding: 7px 12px; border-radius: 9px;
  font-size: 11.5px; font-weight: 700; color: #fff;
  background: linear-gradient(135deg, #E8B973, #B8863B);
  display: flex; align-items: center; gap: 4px;
  transition: filter 0.2s;
  font-family: inherit;
}
.hb-save:hover { filter: brightness(1.07); }
.hb-save:disabled { opacity: 0.5; cursor: not-allowed; }
.hb-main {
  display: flex; align-items: baseline; gap: 6px; margin-top: 8px;
}
.hb-main b {
  font-family: 'Noto Serif SC', serif;
  font-size: 26px; font-weight: 900; color: #2A2620; line-height: 1;
}
.hb-main span { font-size: 10.5px; color: rgba(42, 38, 32, 0.45); }
.hb-trend {
  margin-left: auto;
  font-size: 10.5px; font-weight: 700;
  padding: 2px 9px; border-radius: 999px;
}
.hb-trend.up { background: rgba(201, 110, 80, 0.12); color: #C0522F; }
.hb-trend.down { background: rgba(127, 174, 142, 0.14); color: #2F7D5B; }
.hb-trend.flat { background: rgba(42, 38, 32, 0.07); color: rgba(42, 38, 32, 0.5); }
.hb-range { margin-top: 10px; }
.hb-range .bar {
  height: 6px; border-radius: 99px; position: relative;
  background: linear-gradient(90deg, #7FAE8E 0%, #7FAE8E 34%, #D9A24A 34%, #D9A24A 62%, #C98F6F 62%, #C98F6F 78%, #C0522F 78%);
}
.hb-range .bar i {
  position: absolute; top: -4px;
  width: 2.5px; height: 14px; border-radius: 2px;
  background: #2A2620;
  transition: left 0.45s cubic-bezier(0.34, 1.3, 0.64, 1);
}
.hb-range .cap {
  display: flex; justify-content: space-between;
  font-size: 9px; color: rgba(42, 38, 32, 0.4); margin-top: 4px;
}
.hb-note {
  margin-top: 9px;
  font-size: 10.5px; color: rgba(42, 38, 32, 0.5); line-height: 1.7;
}

/* ---- 右：AI 模式 + 基础属性 ---- */
.u-ai {
  display: flex; align-items: center; gap: 14px; margin-top: 16px;
}
.u-ai .txt b { font-size: 12.5px; color: #2A2620; }
.u-ai .txt p {
  font-size: 10.5px; color: rgba(42, 38, 32, 0.5);
  line-height: 1.7; margin-top: 3px;
}
.mode-switch {
  position: relative; flex-shrink: 0;
  width: 52px; height: 28px;
  border-radius: 999px; border: none;
  background: #D8CBB2; cursor: pointer;
  transition: background 0.25s; margin-left: auto; padding: 0;
}
.mode-switch.is-on { background: linear-gradient(135deg, #E8B973, #B8863B); }
.mode-knob {
  position: absolute; top: 3px; left: 3px;
  width: 22px; height: 22px; border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.3);
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.mode-switch.is-on .mode-knob { transform: translateX(24px); }
.meta-divider {
  margin: 16px 0 12px;
  border-top: 1px dashed rgba(184, 134, 59, 0.25);
}
.meta-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 10px; margin-top: 10px;
}
.meta-field span {
  display: block;
  font-size: 10px; color: rgba(42, 38, 32, 0.45); margin-bottom: 4px;
}
.meta-field select {
  width: 100%;
  padding: 7px 9px; border-radius: 9px;
  border: 1px solid rgba(184, 134, 59, 0.3);
  background: #fff; font-size: 12px; color: #2A2620;
  outline: none; font-family: inherit;
}
.meta-field select:focus { border-color: #B8863B; }
.meta-save {
  margin-top: 12px; width: 100%; justify-content: center;
}
.btn-gold {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 9px 20px; border-radius: 10px; border: none; cursor: pointer;
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; font-size: 12.5px; font-weight: 600; letter-spacing: 0.04em;
  transition: 0.25s; font-family: inherit;
}
.btn-gold:hover { opacity: 0.9; transform: translateY(-1px); }
.btn-gold:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }

/* ===================== 裁剪弹窗样式 ===================== */
.cropper-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.cropper-dialog {
  width: 100%;
  max-width: 480px;
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 20px 50px rgba(47, 93, 74, 0.2), 0 10px 24px rgba(15, 23, 42, 0.12);
  border: 1px solid rgba(184, 134, 59, 0.2);
  overflow: hidden;
}
.cropper-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px 12px;
}
.cropper-close-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  background: #f3f4f6;
  color: #6b7280;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  transition: all 0.2s;
}
.cropper-close-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}
.cropper-body {
  height: 320px;
  background: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.cropper-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
}
.cropper-empty-icon { font-size: 40px; }
.cropper-tips {
  padding: 10px 18px;
  background: #fdf9f0;
  font-size: 12px;
  color: #4b5563;
  line-height: 1.6;
}
.cropper-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 18px;
}
.cropper-btn {
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 13px;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}
.cropper-btn-ghost {
  background: #f3f4f6;
  color: #4b5563;
}
.cropper-btn-ghost:hover:not(:disabled) {
  background: #e5e7eb;
}
.cropper-btn-primary {
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff;
}
.cropper-btn-primary:hover:not(:disabled) { filter: brightness(1.07); }
.cropper-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.cropper-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: cropper-rotate 0.8s linear infinite;
  margin-right: 6px;
  vertical-align: middle;
}
@keyframes cropper-rotate {
  to { transform: rotate(360deg); }
}
.dlg-overlay-enter-active, .dlg-overlay-leave-active {
  transition: opacity 0.2s ease;
}
.dlg-overlay-enter-from, .dlg-overlay-leave-to {
  opacity: 0;
}
.dlg-content-enter-active {
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.dlg-content-leave-active {
  transition: all 0.2s ease;
}
.dlg-content-enter-from, .dlg-content-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(12px);
}

/* ---- 响应式 ---- */
@media (max-width: 1000px) {
  .db-blocks { grid-template-columns: 1fr; }
  .halo-stage { height: 360px; }
}
</style>
