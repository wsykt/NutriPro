<template>
  <div class="page-fade">
    <h2 class="text-2xl font-bold mb-2 text-morandi-text">个人中心</h2>
    <p class="text-morandi-lightText mb-6 text-sm">查看和更新你的个人信息。保存后，系统会自动在"身体指标历史"里保留一份今日快照。</p>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- 头像卡片 -->
      <div class="glass rounded-2xl p-6 text-center">
        <!-- 头像容器：纯展示，点击下方按钮更换 -->
        <div class="relative w-24 h-24 mx-auto mb-3">
          <div class="w-full h-full rounded-full bg-morandi-accent flex items-center justify-center text-white font-bold text-3xl overflow-hidden ring-4 ring-white shadow-lg shadow-emerald-100/60">
            <template v-if="currentAvatar">
              <img :src="resolveAvatarUrl(currentAvatar)" class="w-full h-full object-cover" alt="头像" />
            </template>
            <template v-else>
              {{ usernameInitial }}
            </template>
          </div>
          <!-- 隐藏的文件输入框，点击下方按钮触发 -->
          <input ref="fileInputRef" type="file" accept="image/*" class="hidden" @change="onFileSelected" />
        </div>

        <h3 class="font-bold text-lg">{{ usernameText }}</h3>
        <p class="text-morandi-lightText text-sm mt-1">用户 ID：#{{ userInfo.userId || '—' }}</p>
        <p class="text-xs text-morandi-accent mt-1 capitalize">{{ userInfo.role || 'user' }}</p>
        <p class="text-xs text-morandi-lightText mt-3">当前身份：{{ operateAsLabel }}</p>

        <!-- 更换头像按钮：点击后触发隐藏的文件输入框 -->
        <button
          class="change-avatar-btn mt-4"
          :disabled="uploading"
          @click="pickAvatar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4">
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
            <circle cx="12" cy="13" r="4"></circle>
          </svg>
          <span>{{ uploading ? '上传中...' : '更换头像' }}</span>
        </button>
      </div>

      <!-- 基本信息卡片 -->
      <div class="glass rounded-2xl p-6 md:col-span-2">
        <h3 class="font-semibold mb-4">基本信息</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">性别</label>
            <select v-model="form.gender" class="w-full px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm">
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">年龄</label>
            <input v-model.number="form.age" type="number" class="w-full px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm" />
          </div>
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">身高 (cm)</label>
            <input v-model.number="form.height" type="number" class="w-full px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm" />
          </div>
          <div>
            <label class="block text-xs text-morandi-lightText mb-1">体重 (kg)</label>
            <input v-model.number="form.weight" type="number" class="w-full px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm" />
          </div>
          <div class="sm:col-span-2">
            <label class="block text-xs text-morandi-lightText mb-1">人群类型</label>
            <select v-model="form.crowdType" class="w-full px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm">
              <option v-for="c in crowdOptions" :key="c.value" :value="c.value">{{ c.label }}</option>
            </select>
          </div>
          <div class="sm:col-span-2">
            <label class="block text-xs text-morandi-lightText mb-1">BMI 指数（自动计算）</label>
            <div class="w-full px-3 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm font-semibold text-morandi-accent">{{ bmiText }}</div>
          </div>
        </div>

        <div class="flex items-center gap-3 mt-5">
          <button @click="handleSave" :disabled="saving" class="px-5 py-2 rounded-lg bg-morandi-accent text-white text-sm hover:opacity-90 transition-opacity disabled:opacity-50">
            {{ saving ? '保存中...' : '保存信息' }}
          </button>
          <span v-if="saveMsg" class="text-xs text-morandi-accent">{{ saveMsg }}</span>
        </div>
        <p class="mt-3 text-xs text-morandi-lightText leading-relaxed">
          保存信息 = 更新资料 + 写入一条今日身体指标快照，方便在趋势线上查看变化。
        </p>
      </div>
    </div>

    <!-- AI 处理模式开关 -->
    <div class="glass rounded-2xl p-6 mt-6">
      <div class="flex items-center justify-between gap-4">
        <div>
          <h3 class="font-semibold">AI 处理模式</h3>
          <p class="text-xs text-morandi-lightText mt-1 leading-relaxed">
            <template v-if="userStore.highPerformance">
              高性能模式：AI 云端直连，响应快、回答更丰富，但消耗云端额度。
            </template>
            <template v-else>
              普通模式：优先本地大模型生成、云端兜底，质量更稳且省额度。
            </template>
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
      <p class="mt-3 text-xs text-morandi-lightText">
        当前：<span class="font-semibold text-morandi-accent">{{ userStore.highPerformance ? '高性能模式' : '普通模式' }}</span>
        ，已同步应用到健康咨询与周报/月报 AI 分析。
      </p>
    </div>

    <!-- 裁剪弹窗 -->
    <Teleport to="body">
      <Transition name="dlg-overlay">
        <div v-if="cropperVisible" class="cropper-mask" @click.self="closeCropper">
          <Transition name="dlg-content" appear>
            <div v-if="cropperVisible" class="cropper-dialog">
              <div class="cropper-header">
                <div class="flex items-center gap-2">
                  <span class="w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-400 to-green-600 flex items-center justify-center text-white text-sm font-bold">剪</span>
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
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'
import { ElMessage } from 'element-plus'
import 'element-plus/es/components/message/style/css'
import { VueCropper } from 'vue-cropper'
import 'vue-cropper/dist/index.css'
import { CROWD_OPTIONS } from '../../constants'

// ====== 类型定义 ======
type CropperRef = InstanceType<typeof VueCropper> | null

const crowdOptions = [...CROWD_OPTIONS]

// 上传文件大小上限：5MB
const MAX_SIZE_MB = 5
const MAX_SIZE = MAX_SIZE_MB * 1024 * 1024
const ALLOWED_EXT = ['jpg', 'jpeg', 'png', 'webp']

const userStore = useUserStore()
const userInfo = ref<any>({})
const usernameText = computed(() => userInfo.value.username || userStore.user?.username || '')
const usernameInitial = computed(() => (usernameText.value ? usernameText.value.slice(0, 1).toUpperCase() : 'U'))
const currentAvatar = computed(() => userInfo.value.avatar || userStore.avatar || '')
const operateAsLabel = computed(() => {
  if (userStore.actAsUserId != null) {
    return `代 #${userStore.actAsUserId} 操作`
  }
  return '本人'
})

// ====== 文件选择 & 裁剪 ======
const fileInputRef = ref<HTMLInputElement | null>(null)
const cropperVisible = ref(false)
const originImg = ref<string>('')
const cropperRef = ref<CropperRef>(null)
const uploading = ref(false)

function pickAvatar() {
  fileInputRef.value?.click()
}

function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
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

const form = ref<any>({
  gender: '男',
  age: 18,
  height: 165,
  weight: 65,
  crowdType: '普通人'
})
const saving = ref(false)
const saveMsg = ref('')

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
    saveMsg.value = e?.message || '加载失败'
  }
}

function toNumber(v: any, fallback: number): number {
  const n = Number(v)
  return Number.isFinite(n) ? n : fallback
}

const bmiText = computed(() => {
  const h = Number(form.value.height) / 100
  const w = Number(form.value.weight)
  if (!h || !w) return '—'
  const bmi = w / (h * h)
  let category = ''
  if (bmi < 18.5) category = '（偏瘦）'
  else if (bmi < 24) category = '（正常）'
  else if (bmi < 28) category = '（超重）'
  else category = '（肥胖）'
  return `${bmi.toFixed(2)} ${category}`
})

async function handleSave() {
  saving.value = true
  saveMsg.value = ''
  try {
    await api.profile.update({
      gender: form.value.gender,
      age: Number(form.value.age) || null,
      height: Number(form.value.height) || null,
      weight: Number(form.value.weight) || null,
      crowdType: form.value.crowdType
    })
    saveMsg.value = '已保存，并写入今日身体指标快照'
    await userStore.loadUserProfile?.()
  } catch (e: any) {
    saveMsg.value = e?.message || '保存失败'
  } finally {
    saving.value = false
  }
}

// ====== AI 处理模式 ======
function toggleAiMode() {
  userStore.setHighPerformance(!userStore.highPerformance)
  ElMessage.success(userStore.highPerformance ? '已切换为高性能模式（云端直连）' : '已切换为普通模式')
}

onMounted(async () => {
  await loadInfo()
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.9);
}
.page-fade {
  animation: fadeIn 0.3s ease forwards;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 更换头像按钮 */
.change-avatar-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 10px;
  border: 1px solid rgba(47, 93, 74, 0.3);
  background: rgba(47, 93, 74, 0.06);
  color: #2F5D4A;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s;
}
.change-avatar-btn:hover:not(:disabled) {
  background: #2F5D4A;
  color: #fff;
}
.change-avatar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===================== AI 模式开关 ===================== */
.mode-switch {
  position: relative;
  flex-shrink: 0;
  width: 52px;
  height: 28px;
  border-radius: 999px;
  border: none;
  background: #cbd5e1;
  cursor: pointer;
  transition: background 0.25s;
  padding: 0;
}
.mode-switch.is-on {
  background: #2F5D4A;
}
.mode-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.3);
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.mode-switch.is-on .mode-knob {
  transform: translateX(24px);
}

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
  border: 1px solid rgba(47, 93, 74, 0.15);
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
.cropper-empty-icon {
  font-size: 40px;
}
.cropper-tips {
  padding: 10px 18px;
  background: #f0fdf4;
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
  background: #2F5D4A;
  color: #fff;
}
.cropper-btn-primary:hover:not(:disabled) {
  background: #274d3d;
}
.cropper-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.cropper-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: cropper-rotate 0.8s linear infinite;
  margin-right: 6px;
  vertical-align: middle;
}
@keyframes cropper-rotate {
  to { transform: rotate(360deg); }
}
/* 过渡动画 */
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
</style>