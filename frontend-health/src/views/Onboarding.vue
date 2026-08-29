<template>
  <div class="amber-auth min-h-screen relative">
    <!-- 顶部刊头 -->
    <header class="amber-top-nav">
      <router-link to="/" class="amber-brand">
        <span class="amber-brand-name amber-brand-name--video">
          <span class="amber-brand-video-mask">
            <span class="amber-brand-fallback" aria-hidden="true">NutriPro</span>
            <video class="amber-brand-video" autoplay muted loop playsinline preload="auto">
              <source src="https://videos.pexels.com/video-files/5866263/5866263-hd_1280_720_25fps.mp4" type="video/mp4" />
            </video>
          </span>
        </span>
        <span class="amber-brand-sub">档案 · Journal of Health</span>
      </router-link>
      <span class="amber-nav-meta">Step {{ currentStep + 1 }} / {{ steps.length }}</span>
    </header>

    <!-- 主体：双栏（左卷首语 · 右居中卡片） -->
    <main class="amber-stage">
      <div class="amber-grid">
        <!-- 左栏：小卷首语 -->
        <aside class="amber-aside">
          <p class="amber-eyebrow">
            <span class="amber-eyebrow-bar"></span>
            Editor's Note · 卷首语
          </p>
          <p class="amber-issue">Issue № 06 · 入门号</p>
          <p class="amber-pull">
            "每一次启程，都值得被郑重书写。回答几个问题，让你的健康档案从此与众不同。"
          </p>
          <p class="amber-aside-meta">
            基础信息 · 人群类型 · 健康习惯——三步建立你的专属档案，随后开启健康之旅。
          </p>

          <!-- 步骤进度 -->
          <ol class="amber-progress">
            <li
              v-for="(step, index) in steps"
              :key="index"
              class="amber-progress-item"
              :class="{
                'amber-progress-item--active': currentStep === index,
                'amber-progress-item--done': currentStep > index
              }"
            >
              <span class="amber-progress-no">{{ String(index + 1).padStart(2, '0') }}</span>
              <span class="amber-progress-name">{{ step }}</span>
            </li>
          </ol>
        </aside>

        <!-- 右栏：居中卡片 -->
        <div class="amber-card-wrap">
          <div class="amber-card">
            <div class="amber-badge">健</div>
            <p class="amber-card-eyebrow">Onboarding · {{ String(currentStep + 1).padStart(2, '0') }}</p>
            <h1 class="amber-card-title">{{ steps[currentStep] }}</h1>

            <transition name="amber-step" mode="out-in">
              <!-- Step 1：基本信息 -->
              <div v-if="currentStep === 0" key="step1" class="amber-form">
                <p class="amber-card-sub">设置你的性别、身高、体重与年龄。</p>
                <div class="amber-field">
                  <label class="amber-label">性别</label>
                  <div class="amber-chips">
                    <button
                      v-for="g in ['男', '女']"
                      :key="g"
                      type="button"
                      @click="form.gender = g"
                      class="amber-chip"
                      :class="{ 'amber-chip--active': form.gender === g }"
                    >{{ g }}</button>
                  </div>
                </div>
                <div class="amber-row amber-row-3">
                  <div class="amber-field amber-grow">
                    <label class="amber-label">身高 / cm</label>
                    <input v-model.number="form.height" type="number" min="50" max="250" class="amber-input" placeholder="170" />
                  </div>
                  <div class="amber-field amber-grow">
                    <label class="amber-label">体重 / kg</label>
                    <input v-model.number="form.weight" type="number" min="20" max="300" class="amber-input" placeholder="65" />
                  </div>
                  <div class="amber-field amber-grow">
                    <label class="amber-label">年龄</label>
                    <input v-model.number="form.age" type="number" min="1" max="150" class="amber-input" placeholder="25" />
                  </div>
                </div>
                <button @click="nextStep" :disabled="!isStep1Valid" class="amber-submit amber-submit--row">
                  <span>下一步</span><span class="amber-arrow">→</span>
                </button>
              </div>

              <!-- Step 2：人群类型 -->
              <div v-else-if="currentStep === 1" key="step2" class="amber-form">
                <p class="amber-card-sub">选择最适合你的人群类型。</p>
                <div class="amber-tiles">
                  <button
                    v-for="type in crowdTypes"
                    :key="type.value"
                    type="button"
                    @click="form.crowdType = type.value"
                    class="amber-tile"
                    :class="{ 'amber-tile--active': form.crowdType === type.value }"
                  >
                    <component :is="type.icon" class="amber-tile-icon" />
                    <span class="amber-tile-label">{{ type.label }}</span>
                  </button>
                </div>
                <div class="amber-row amber-row-btns">
                  <button @click="prevStep" class="amber-ghost">返回</button>
                  <button @click="nextStep" :disabled="!form.crowdType" class="amber-submit amber-submit--grow amber-submit--row">
                    <span>下一步</span><span class="amber-arrow">→</span>
                  </button>
                </div>
              </div>

              <!-- Step 3：健康产品 -->
              <div v-else-if="currentStep === 2" key="step3" class="amber-form">
                <p class="amber-card-sub">你使用过以下哪些健康类产品？</p>
                <div class="amber-product-list">
                  <button
                    v-for="product in healthProducts"
                    :key="product"
                    type="button"
                    @click="toggleProduct(product)"
                    class="amber-product"
                    :class="{ 'amber-product--active': selectedProducts.includes(product) }"
                  >
                    <span class="amber-product-name">{{ product }}</span>
                    <span class="amber-product-check">
                      <component v-if="selectedProducts.includes(product)" :is="Check" class="amber-check-icon" />
                    </span>
                  </button>
                </div>
                <div class="amber-row amber-row-btns">
                  <button @click="prevStep" class="amber-ghost">返回</button>
                  <button @click="nextStep" class="amber-submit amber-submit--grow amber-submit--row">
                    <span>下一步</span><span class="amber-arrow">→</span>
                  </button>
                </div>
              </div>

              <!-- Step 4：完成 -->
              <div v-else-if="currentStep === 3" key="step4" class="amber-form amber-form--center">
                <div class="amber-finish-mark">
                  <component :is="PartyPopper" class="amber-finish-icon" />
                </div>
                <h2 class="amber-finish-title">欢迎加入！</h2>
                <p class="amber-finish-sub">恭喜你完成了所有设置，现在开始你的健康之旅吧。</p>
                <div class="amber-summary">
                  <div class="amber-summary-grid">
                    <div><p class="amber-summary-k">性别</p><p class="amber-summary-v">{{ form.gender }}</p></div>
                    <div><p class="amber-summary-k">年龄</p><p class="amber-summary-v">{{ form.age }} 岁</p></div>
                    <div><p class="amber-summary-k">身高</p><p class="amber-summary-v">{{ form.height }} cm</p></div>
                    <div><p class="amber-summary-k">体重</p><p class="amber-summary-v">{{ form.weight }} kg</p></div>
                  </div>
                  <div class="amber-summary-foot">
                    <p class="amber-summary-k">人群类型</p>
                    <p class="amber-summary-v">{{ getCrowdTypeLabel(form.crowdType) }}</p>
                  </div>
                </div>
                <button @click="completeOnboarding" :disabled="loading" class="amber-submit amber-submit--row">
                  <span>{{ loading ? '正在进入...' : '开始我的健康之旅' }}</span><span class="amber-arrow">→</span>
                </button>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </main>

    <!-- 自定义光标（useAmberCursor composable） -->
    <div class="hc-layer" aria-hidden="true">
      <div class="hc-halo" ref="cursorHalo"></div>
      <div class="hc-dot" ref="cursorDot"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { api } from '../api'
import { useAmberCursor } from '../composables/useAmberCursor'
import { User, Heart, Baby, GraduationCap, Droplet, Dumbbell, Check, PartyPopper } from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()
const { cursorDot, cursorHalo } = useAmberCursor()

const currentStep = ref(0)
const loading = ref(false)
const steps = ['基本信息', '人群类型', '健康产品', '完成']

const form = reactive({
  gender: '',
  height: null as number | null,
  weight: null as number | null,
  age: null as number | null,
  crowdType: '',
  usedProducts: [] as string[]
})
const selectedProducts = ref<string[]>([])

const crowdTypes = [
  { value: '普通人', label: '普通人', icon: User as Component },
  { value: '健身', label: '健身爱好者', icon: Dumbbell as Component },
  { value: '老年', label: '老年人', icon: Heart as Component },
  { value: '孕妇', label: '孕妇', icon: Baby as Component },
  { value: '青少年', label: '青少年', icon: GraduationCap as Component },
  { value: '糖尿病', label: '糖尿病患者', icon: Droplet as Component }
]

const healthProducts = ['小荷AI医生', '咕咚', '薄荷健康', 'Keep', '其他']

const isStep1Valid = computed(() => {
  return form.gender && form.height && form.weight && form.age
})

const toggleProduct = (product: string) => {
  const index = selectedProducts.value.indexOf(product)
  if (index === -1) selectedProducts.value.push(product)
  else selectedProducts.value.splice(index, 1)
}

const getCrowdTypeLabel = (value: string) => {
  const type = crowdTypes.find(t => t.value === value)
  return type ? type.label : value
}

const nextStep = () => {
  if (currentStep.value < steps.length - 1) currentStep.value++
}
const prevStep = () => {
  if (currentStep.value > 0) currentStep.value--
}

const completeOnboarding = async () => {
  loading.value = true
  userStore.setFirstLogin(0)
  userStore.updateProfile({
    gender: form.gender,
    height: form.height ?? undefined,
    weight: form.weight ?? undefined,
    age: form.age ?? undefined,
    crowdType: form.crowdType
  })
  try {
    await api.profile.update({
      gender: form.gender,
      height: form.height ?? undefined,
      weight: form.weight ?? undefined,
      age: form.age ?? undefined,
      crowdType: form.crowdType
    })
    router.push('/dashboard/profile')
  } catch (e: any) {
    console.error('保存资料到后端失败（引导已完成，可在个人中心重新修改）', e)
    router.push('/dashboard/profile')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* =============== Direction C 赤金 Amber Editorial · 全局画布 =============== */
.amber-auth {
  background: #0E0C0A;
  color: #F6EAD6;
  font-family: "PingFang SC","Hiragino Sans GB","Microsoft YaHei","HarmonyOS Sans SC",system-ui,sans-serif;
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
}
.amber-auth::before {
  content: ""; position: absolute; inset: 0;
  z-index: 0; pointer-events: none;
  background:
    radial-gradient(circle at 18% 22%, rgba(232,185,115,0.20) 0%, rgba(232,185,115,0.03) 40%, transparent 68%),
    radial-gradient(circle at 86% 78%, rgba(179,107,42,0.16) 0%, transparent 55%),
    linear-gradient(180deg, #14110C 0%, #0E0C0A 55%, #110E09 100%);
}
.amber-auth::after {
  content: ""; position: absolute; inset: 0;
  z-index: 0; pointer-events: none;
  background-image:
    repeating-linear-gradient(90deg, rgba(217,162,74,0.042) 0 1px, transparent 1px 86px),
    repeating-linear-gradient(0deg,  rgba(217,162,74,0.026) 0 1px, transparent 1px 86px);
  mix-blend-mode: overlay;
}

/* =============== 顶部刊头 =============== */
.amber-top-nav {
  position: relative; z-index: 3;
  max-width: 1240px; margin: 0 auto;
  padding: 24px 32px 18px;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px dashed rgba(217,162,74,0.28);
}
.amber-brand {
  display: flex; align-items: center; gap: 12px;
  color: #F6EAD6; font-weight: 800; font-size: 14px;
  letter-spacing: 0.04em;
  text-decoration: none;
}
.amber-brand-name--video {
  display: inline-flex; align-items: center; height: 28px;
  position: relative;
}
.amber-brand-video-mask {
  display: block; width: 130px; height: 100%;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='130' height='28' viewBox='0 0 130 28'%3E%3Ctext x='0' y='23' font-size='23' font-weight='900' font-family='serif' fill='black'%3ENutriPro%3C/text%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='130' height='28' viewBox='0 0 130 28'%3E%3Ctext x='0' y='23' font-size='23' font-weight='900' font-family='serif' fill='black'%3ENutriPro%3C/text%3E%3C/svg%3E");
  -webkit-mask-size: 100% 100%; mask-size: 100% 100%;
  -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
  -webkit-mask-position: center; mask-position: center;
  position: relative;
}
.amber-brand-fallback {
  position: absolute; inset: 0;
  display: flex; align-items: center;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-weight: 900; font-size: 21px;
  color: #F6EAD6;
  white-space: nowrap;
}
.amber-brand-video {
  width: 100%; height: 100%;
  object-fit: cover; display: block; pointer-events: none;
}
.amber-brand-sub { color: #B9A78A; font-weight: 500; font-size: 12px; letter-spacing: 0.18em; }
.amber-nav-meta {
  font-size: 11px; letter-spacing: 0.28em; color: #D9A24A;
  text-transform: uppercase; font-weight: 700;
  padding: 6px 12px;
  border: 1px solid rgba(217,162,74,0.4); border-radius: 999px;
}

/* =============== 主体舞台 =============== */
.amber-stage {
  position: relative; z-index: 2;
  max-width: 1240px; margin: 0 auto;
  padding: 48px 32px 80px;
}
.amber-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 64px;
  align-items: center;
}

/* —— 左栏：小卷首语 —— */
.amber-aside {
  max-width: 460px;
  justify-self: end;
  padding-right: 28px;
  border-right: 1px dashed rgba(217,162,74,0.22);
}
.amber-eyebrow {
  display: flex; align-items: center; gap: 12px;
  font-size: 11px; letter-spacing: 0.28em; color: #D9A24A;
  text-transform: uppercase; font-weight: 700;
  margin: 0 0 10px;
}
.amber-eyebrow-bar {
  width: 28px; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(217,162,74,0.85), transparent);
}
.amber-issue {
  font-size: 10.5px; letter-spacing: 0.22em; color: #8C7A5E;
  text-transform: uppercase; font-weight: 600;
  margin: 0 0 22px;
}
.amber-pull {
  font-family: "Songti SC","Noto Serif SC","Times New Roman",serif;
  font-style: italic; font-weight: 700;
  font-size: 19px; line-height: 1.7;
  color: #F1CF92;
  margin: 0 0 20px;
  letter-spacing: 0.01em;
}
.amber-aside-meta {
  font-size: 12px; line-height: 1.7;
  color: #B9A78A;
  margin: 0 0 28px;
  letter-spacing: 0.04em;
}

/* —— 步骤进度 —— */
.amber-progress {
  list-style: none; margin: 0; padding: 0;
  display: flex; flex-direction: column; gap: 14px;
}
.amber-progress-item {
  display: flex; align-items: center; gap: 14px;
  padding: 8px 0;
  border-left: 1px solid rgba(217,162,74,0.18);
  padding-left: 16px;
  transition: border-color 0.4s ease, opacity 0.4s ease;
  opacity: 0.5;
}
.amber-progress-item--active {
  opacity: 1;
  border-left-color: rgba(232,185,115,0.85);
}
.amber-progress-item--done {
  opacity: 0.8;
  border-left-color: rgba(217,162,74,0.5);
}
.amber-progress-no {
  font-size: 11px; letter-spacing: 0.18em; color: #8C7A5E;
  font-weight: 700; min-width: 24px;
}
.amber-progress-item--active .amber-progress-no { color: #F1CF92; }
.amber-progress-name {
  font-size: 13px; color: #B9A78A; letter-spacing: 0.04em;
}
.amber-progress-item--active .amber-progress-name {
  color: #F6EAD6; font-weight: 600;
}

/* =============== 右栏：居中卡片 =============== */
.amber-card-wrap { width: 100%; display: flex; justify-content: flex-start; }
.amber-card {
  position: relative;
  width: 100%; max-width: 420px;
  padding: 30px 30px 26px;
  border: 1px solid rgba(217,162,74,0.28);
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(28,22,16,0.7), rgba(20,16,11,0.6));
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow:
    0 40px 80px -28px rgba(0,0,0,0.85),
    0 12px 40px -6px rgba(217,162,74,0.18),
    inset 0 0 0 1px rgba(232,185,115,0.08);
  text-align: center;
}
.amber-card::before {
  content: ""; position: absolute; inset: -1px;
  border-radius: 17px;
  background: linear-gradient(135deg, rgba(232,185,115,0.35), transparent 50%, rgba(179,107,42,0.2));
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
          mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
          mask-composite: exclude;
  padding: 1px; pointer-events: none;
}

.amber-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 56px; height: 56px; border-radius: 14px;
  background: linear-gradient(135deg,#E8B973 0%, #D9A24A 60%, #B36B2A 100%);
  color: #1F170E; font-weight: 900; font-size: 22px;
  box-shadow: 0 12px 30px rgba(217,162,74,0.3), inset 0 1px 0 rgba(255,255,255,0.3);
  margin-bottom: 14px;
}
.amber-card-eyebrow {
  font-size: 11px; letter-spacing: 0.32em; color: #D9A24A;
  text-transform: uppercase; font-weight: 700; margin: 0 0 8px;
}
.amber-card-title {
  font-size: 26px; font-weight: 900; color: #F6EAD6;
  letter-spacing: -0.02em; margin: 0 0 18px;
}

/* =============== 表单 =============== */
.amber-form { text-align: left; }
.amber-form--center { text-align: center; }
.amber-card-sub {
  font-size: 12.5px; color: #B9A78A; margin: 0 0 18px;
  line-height: 1.6;
}
.amber-field { margin-bottom: 14px; }
.amber-label {
  display: block; font-size: 10.5px; letter-spacing: 0.22em;
  color: #B9A78A; text-transform: uppercase;
  font-weight: 600; margin-bottom: 8px;
}
.amber-row {
  display: flex; gap: 12px; align-items: flex-start;
}
.amber-row-3 .amber-field { margin-bottom: 0; }
.amber-grow { flex: 1 1 0; min-width: 0; }

.amber-input {
  width: 100%; padding: 11px 14px;
  background: rgba(14,12,10,0.5);
  border: 1px solid rgba(246,234,214,0.12);
  border-radius: 8px;
  color: #F6EAD6;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.35s cubic-bezier(0.22,1,0.36,1),
              box-shadow 0.35s cubic-bezier(0.22,1,0.36,1),
              background 0.35s ease;
  outline: none;
}
.amber-input::placeholder { color: rgba(246,234,214,0.32); }
.amber-input:focus {
  border-color: rgba(232,185,115,0.65);
  background: rgba(20,17,12,0.7);
  box-shadow: 0 0 0 3px rgba(217,162,74,0.12), 0 0 24px rgba(217,162,74,0.18);
}

/* —— Chips（性别） —— */
.amber-chips {
  display: flex; flex-wrap: wrap; gap: 8px;
}
.amber-chip {
  padding: 9px 18px;
  border: 1px solid rgba(246,234,214,0.14);
  border-radius: 999px;
  background: rgba(14,12,10,0.4);
  color: #B9A78A;
  font-size: 13px; font-family: inherit;
  letter-spacing: 0.04em;
  cursor: none;
  transition: all 0.35s cubic-bezier(0.22,1,0.36,1);
}
.amber-chip:hover {
  border-color: rgba(217,162,74,0.4);
  color: #F1CF92;
}
.amber-chip--active {
  border-color: rgba(232,185,115,0.85);
  background: linear-gradient(135deg, rgba(232,185,115,0.18), rgba(179,107,42,0.1));
  color: #F6EAD6;
  box-shadow: 0 0 0 1px rgba(232,185,115,0.35), 0 6px 18px rgba(217,162,74,0.18);
}

/* —— Tiles（人群类型） —— */
.amber-tiles {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
  margin-bottom: 16px;
}
.amber-tile {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 16px 10px;
  border: 1px solid rgba(246,234,214,0.12);
  border-radius: 12px;
  background: rgba(14,12,10,0.4);
  color: #B9A78A;
  font-family: inherit;
  cursor: none;
  transition: all 0.35s cubic-bezier(0.22,1,0.36,1);
}
.amber-tile:hover {
  border-color: rgba(217,162,74,0.4);
  color: #F1CF92;
  transform: translateY(-2px);
}
.amber-tile--active {
  border-color: rgba(232,185,115,0.85);
  background: linear-gradient(135deg, rgba(232,185,115,0.16), rgba(179,107,42,0.08));
  color: #F6EAD6;
  box-shadow: 0 0 0 1px rgba(232,185,115,0.35), 0 8px 22px rgba(217,162,74,0.2);
}
.amber-tile-icon {
  width: 26px; height: 26px;
  color: #D9A24A;
  transition: color 0.35s ease;
}
.amber-tile--active .amber-tile-icon { color: #F1CF92; }
.amber-tile-label {
  font-size: 12px; letter-spacing: 0.04em; font-weight: 600;
}

/* —— 产品列表 —— */
.amber-product-list {
  display: flex; flex-direction: column; gap: 8px;
  margin-bottom: 16px;
}
.amber-product {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px;
  border: 1px solid rgba(246,234,214,0.12);
  border-radius: 10px;
  background: rgba(14,12,10,0.4);
  color: #B9A78A;
  font-family: inherit;
  cursor: none;
  transition: all 0.35s cubic-bezier(0.22,1,0.36,1);
}
.amber-product:hover {
  border-color: rgba(217,162,74,0.4);
  color: #F1CF92;
}
.amber-product--active {
  border-color: rgba(232,185,115,0.7);
  background: linear-gradient(135deg, rgba(232,185,115,0.1), rgba(179,107,42,0.04));
  color: #F6EAD6;
}
.amber-product-name {
  font-size: 13px; letter-spacing: 0.04em; font-weight: 500;
}
.amber-product-check {
  width: 20px; height: 20px;
  border: 1.5px solid rgba(246,234,214,0.2);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.35s ease;
}
.amber-product--active .amber-product-check {
  border-color: transparent;
  background: linear-gradient(135deg,#E8B973 0%, #D9A24A 60%, #B36B2A 100%);
}
.amber-check-icon {
  width: 12px; height: 12px; color: #1F170E;
}

/* —— 按钮行 —— */
.amber-row-btns {
  align-items: stretch;
  margin-top: 4px;
}
.amber-ghost {
  flex: 0 0 auto;
  padding: 12px 22px;
  border: 1px solid rgba(246,234,214,0.14);
  border-radius: 999px;
  background: transparent;
  color: #B9A78A;
  font-size: 12px; font-family: inherit;
  letter-spacing: 0.18em; text-transform: uppercase; font-weight: 700;
  cursor: none;
  transition: all 0.35s cubic-bezier(0.22,1,0.36,1);
}
.amber-ghost:hover {
  border-color: rgba(217,162,74,0.4);
  color: #F1CF92;
}
.amber-submit--grow { flex: 1 1 0; }

.amber-submit {
  width: 100%; padding: 12px 18px;
  border: 0; border-radius: 999px;
  background: linear-gradient(135deg,#E8B973 0%, #D9A24A 60%, #B36B2A 100%);
  color: #1F170E;
  font-weight: 800; font-size: 12.5px; letter-spacing: 0.22em;
  text-transform: uppercase;
  cursor: none;
  font-family: inherit;
  transition: transform 0.45s cubic-bezier(0.22,1,0.36,1),
              box-shadow 0.45s ease,
              opacity 0.3s ease;
  box-shadow: 0 10px 30px rgba(217,162,74,0.28), inset 0 1px 0 rgba(255,255,255,0.3);
  margin-top: 12px;
  display: inline-flex; align-items: center; justify-content: center; gap: 10px;
}
.amber-submit--row {
  width: auto;
}
.amber-submit:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 40px rgba(217,162,74,0.4), inset 0 1px 0 rgba(255,255,255,0.4);
}
.amber-submit:disabled {
  opacity: 0.5; cursor: not-allowed; transform: none;
}
.amber-arrow {
  font-size: 14px; transition: transform 0.4s cubic-bezier(0.22,1,0.36,1);
}
.amber-submit:hover .amber-arrow { transform: translateX(4px); }

/* —— 完成页 —— */
.amber-finish-mark {
  display: inline-flex; align-items: center; justify-content: center;
  width: 72px; height: 72px; border-radius: 50%;
  background: linear-gradient(135deg, rgba(232,185,115,0.18), rgba(179,107,42,0.08));
  border: 1px solid rgba(217,162,74,0.35);
  margin-bottom: 16px;
}
.amber-finish-icon {
  width: 32px; height: 32px; color: #F1CF92;
}
.amber-finish-title {
  font-family: "Songti SC","Noto Serif SC",serif;
  font-size: 26px; font-weight: 900; color: #F6EAD6;
  margin: 0 0 8px;
}
.amber-finish-sub {
  font-size: 12.5px; color: #B9A78A; line-height: 1.7;
  margin: 0 0 22px;
}

.amber-summary {
  border: 1px solid rgba(217,162,74,0.22);
  border-radius: 12px;
  padding: 16px;
  background: rgba(14,12,10,0.4);
  margin-bottom: 8px;
  text-align: left;
}
.amber-summary-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
}
.amber-summary-k {
  font-size: 10px; letter-spacing: 0.22em; color: #8C7A5E;
  text-transform: uppercase; font-weight: 600;
  margin: 0 0 4px;
}
.amber-summary-v {
  font-size: 14px; color: #F6EAD6; font-weight: 600;
  margin: 0;
}
.amber-summary-foot {
  margin-top: 14px; padding-top: 14px;
  border-top: 1px dashed rgba(217,162,74,0.22);
}

/* =============== 步骤切换动画 =============== */
.amber-step-enter-active {
  transition: opacity 0.35s cubic-bezier(0.22,1,0.36,1), transform 0.35s cubic-bezier(0.22,1,0.36,1);
}
.amber-step-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.amber-step-enter-from {
  opacity: 0; transform: translateX(18px);
}
.amber-step-leave-to {
  opacity: 0; transform: translateX(-18px);
}

/* =============== 入场动画 =============== */
.amber-card {
  animation: amber-fade-up 0.7s cubic-bezier(0.22,1,0.36,1) both;
}
.amber-aside {
  animation: amber-fade-left 0.8s cubic-bezier(0.22,1,0.36,1) 0.1s both;
}
@keyframes amber-fade-up {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes amber-fade-left {
  from { opacity: 0; transform: translateX(-18px); }
  to   { opacity: 1; transform: translateX(0); }
}

/* =============== 响应式 =============== */
@media (max-width: 900px) {
  .amber-grid {
    grid-template-columns: 1fr;
    gap: 36px;
  }
  .amber-aside {
    justify-self: start;
    max-width: 100%;
    padding-right: 0;
    padding-bottom: 28px;
    border-right: 0;
    border-bottom: 1px dashed rgba(217,162,74,0.22);
  }
  .amber-pull { font-size: 17px; }
}
@media (max-width: 640px) {
  .amber-top-nav { padding: 18px 20px 14px; }
  .amber-stage { padding: 32px 20px 56px; }
  .amber-card { padding: 24px 20px 22px; }
  .amber-card-title { font-size: 22px; }
  .amber-pull { font-size: 16px; }
  .amber-tiles { grid-template-columns: 1fr 1fr; }
  .amber-row-3 { flex-direction: column; gap: 14px; }
  .amber-row-btns { flex-direction: column-reverse; gap: 10px; }
  .amber-ghost { width: 100%; }
  .amber-submit--grow { width: 100%; }
}
</style>
