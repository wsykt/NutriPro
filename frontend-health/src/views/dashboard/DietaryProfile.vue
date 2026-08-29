<template>
  <div class="user-page">
    <!-- ===== 深壳星轨带（六项禁忌星球 · 点击点亮/熄灭） ===== -->
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
            <span class="crumb-node hot"><span class="nd"><Salad :size="13" /></span>饮食偏好</span>
          </span>
        </div>
        <div class="db-top-right">
          <span class="db-date"><Sparkles :size="12" />已选 <b>{{ selectedRestrictions.length }}</b> 项禁忌</span>
        </div>
      </div>

      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 104" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 52 C 300 8, 440 8, 560 52 S 830 96, 960 52 S 1130 8, 1200 52" />
        </svg>

        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><Salad :size="19" /></span>
            <span class="tt"><b>味域星图</b><span>TASTE MAP</span></span>
          </div>
        </div>

        <!-- 六项禁忌星球 -->
        <div
          v-for="(it, i) in restrictionOptions" :key="it.value"
          class="db-station-wrap"
          :style="{ left: stationLeft(i, restrictionOptions.length) + '%' }"
        >
          <div class="db-station-float" :style="floatStyle(i)">
            <button
              class="db-station"
              :class="{ now: selectedRestrictions.includes(it.value) }"
              :aria-label="it.label"
              @click="toggleRestriction(it.value)"
            >
              <component :is="it.icon" :size="15" />
              <span class="nm">{{ it.value }}</span>
              <span class="ds">点击{{ selectedRestrictions.includes(it.value) ? '熄灭' : '点亮' }}此项禁忌</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区（过敏禁星环 + 口味星环） ===== -->
    <div class="db-paper" ref="paperRef">
      <div class="db-head" data-anim>
        <div class="sec-t">偏好星图 · 菜谱将自动避开你的禁忌</div>
        <div class="db-pills">
          <span class="pill"><ShieldAlert :size="11" />过敏原 <b>{{ allergicTags.length }}</b> 项</span>
          <span class="pill">口味 <b>{{ form.tastePreference }}</b></span>
        </div>
      </div>

      <div v-if="toastMsg" class="db-toast" data-anim>{{ toastMsg }}</div>

      <div class="db-blocks">
        <!-- 左：过敏食材 + 禁忌 + 保存 -->
        <div class="db-block main" data-anim>
          <div class="db-block-head"><b>过敏食材</b></div>

          <div class="tag-row">
            <span v-for="t in allergicTags" :key="t" class="tag">
              {{ t }}
              <button aria-label="移除" @click="removeTag(t)">×</button>
            </span>
            <input
              v-model="tagInput"
              class="tag-input"
              placeholder="输入食材后回车，如：花生、海鲜、牛奶"
              @keydown.enter.prevent="addTag"
            />
          </div>

          <div class="sec-label">饮食禁忌（与星轨星球同步）</div>
          <div class="chips">
            <button
              v-for="it in restrictionOptions" :key="it.value"
              class="chip"
              :class="{ on: selectedRestrictions.includes(it.value) }"
              @click="toggleRestriction(it.value)"
            >
              <component :is="selectedRestrictions.includes(it.value) ? Check : Plus" :size="12" />
              {{ it.value }}
            </button>
          </div>

          <div class="save-row">
            <button class="btn-gold" :disabled="saving" @click="saveProfile">
              <Save :size="13" />{{ saving ? '保存中...' : '保存饮食档案' }}
            </button>
            <span class="save-note">保存后立即生效于菜谱库与营养分析</span>
          </div>
        </div>

        <!-- 右：口味星环（热度光点右侧的专属火焰 · 仅已选点亮） -->
        <div class="db-block side" data-anim>
          <div class="db-side-head"><b>口味星环</b></div>
          <div class="taste-list">
            <div
              v-for="t in tasteOptions" :key="t.value"
              class="taste"
              :class="{ on: form.tastePreference === t.value }"
              @click="form.tastePreference = t.value"
            >
              <b>{{ t.value }}</b>
              <span class="heat">
                <i v-for="n in 5" :key="n" :class="n <= t.lv ? 'f' + t.lv : ''"></i>
              </span>
              <!-- 火焰特效：位于热度光点右侧，仅已选口味点亮 -->
              <span class="fx" :data-lv="t.lv">
                <template v-if="t.lv === 1">
                  <span class="spark s1"></span><span class="spark s2"></span><span class="spark s3"></span>
                </template>
                <template v-else>
                  <span class="flame"><i></i></span>
                  <template v-if="t.lv === 5">
                    <span class="spark s1"></span><span class="spark s3"></span>
                  </template>
                </template>
              </span>
              <span class="st">{{ form.tastePreference === t.value ? '已选' : '点击选择' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import {
  LayoutGrid, UsersRound, Salad, Sparkles, ShieldAlert,
  Droplet, Droplets, Candy, Activity, Flame, Leaf,
  Check, Plus, Save
} from 'lucide-vue-next'
import type { Component } from 'vue'
import { api } from '@/api'

const router = useRouter()

function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'user' } }) }

// ====== 表单状态 ======
const form = ref({
  allergicFoods: '',
  dietaryRestrictions: '',
  tastePreference: '清淡'
})

const selectedRestrictions = ref<string[]>([])
const allergicTags = ref<string[]>([])
const tagInput = ref('')
const saving = ref(false)
const toastMsg = ref('')

interface RestrictionItem { value: string; label: string; icon: Component }

const restrictionOptions: RestrictionItem[] = [
  { value: '低脂', label: '低脂饮食', icon: Droplet },
  { value: '低盐', label: '低盐饮食', icon: Droplets },
  { value: '低糖', label: '低糖饮食', icon: Candy },
  { value: '糖尿病', label: '糖尿病饮食', icon: Activity },
  { value: '无辣椒', label: '无辣椒', icon: Flame },
  { value: '素食', label: '素食', icon: Leaf }
]

// 口味 5 档：lv 对应火焰等级（1 火星 / 2~4 小火苗→渐旺 / 5 烈焰四溅）
const tasteOptions = [
  { value: '清淡', lv: 1 },
  { value: '适中', lv: 2 },
  { value: '重口味', lv: 3 },
  { value: '微辣', lv: 4 },
  { value: '辣', lv: 5 }
]

// ====== 禁忌同步（星球 ⇋ chips） ======
function toggleRestriction(v: string) {
  const i = selectedRestrictions.value.indexOf(v)
  if (i >= 0) selectedRestrictions.value.splice(i, 1)
  else selectedRestrictions.value.push(v)
}

watch(selectedRestrictions, (val) => {
  form.value.dietaryRestrictions = val.join(',')
}, { deep: true })

// ====== 过敏食材标签 ======
function addTag() {
  const v = tagInput.value.trim().replace(/，/g, ',')
  if (!v) return
  v.split(',').map(s => s.trim()).filter(Boolean).forEach(t => {
    if (!allergicTags.value.includes(t)) allergicTags.value.push(t)
  })
  tagInput.value = ''
  showToast(`「${v}」已加入禁星环`)
}

function removeTag(t: string) {
  allergicTags.value = allergicTags.value.filter(x => x !== t)
}

watch(allergicTags, (val) => {
  form.value.allergicFoods = val.join(',')
}, { deep: true })

// ====== 加载 & 保存 ======
onMounted(async () => {
  try {
    const data: any = await api.profile.getInfo()
    form.value.allergicFoods = data.allergicFoods || ''
    form.value.dietaryRestrictions = data.dietaryRestrictions || ''
    form.value.tastePreference = data.tastePreference || '清淡'

    if (form.value.dietaryRestrictions) {
      selectedRestrictions.value = form.value.dietaryRestrictions.split(',').map((s: string) => s.trim()).filter(Boolean)
    }
    if (form.value.allergicFoods) {
      allergicTags.value = form.value.allergicFoods.split(',').map((s: string) => s.trim()).filter(Boolean)
    }
  } catch (e) {
    console.error('加载用户信息失败', e)
  }
})

async function saveProfile() {
  if (saving.value) return
  saving.value = true
  try {
    await api.profile.updateDietary({
      allergicFoods: form.value.allergicFoods,
      dietaryRestrictions: form.value.dietaryRestrictions,
      tastePreference: form.value.tastePreference
    })
    showToast('饮食档案已保存 · 菜谱推荐将避开所选禁忌')
  } catch (e) {
    console.error('保存饮食档案失败', e)
    showToast('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

function showToast(msg: string) {
  toastMsg.value = msg
  setTimeout(() => { toastMsg.value = '' }, 3200)
}

// ====== 星轨站点分布 & 漂浮节奏 ======
function stationLeft(i: number, total: number): number {
  if (total <= 1) return 64
  if (total <= 5) return 34 + i * (60 / (total - 1))
  return 30 + i * (66 / (total - 1))
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
    gsap.fromTo(paper.querySelectorAll('.taste'),
      { opacity: 0, x: 18 },
      { opacity: 1, x: 0, duration: 0.5, stagger: 0.07, delay: 0.55, ease: 'power2.out', clearProps: 'opacity,transform' })
  }
}

onMounted(() => {
  animateEntrance()
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
.db-date b { color: #F0E2C4; }

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

/* ---- 禁忌星球 ---- */
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
.pill svg { color: #B8863B; }
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
.db-block-head b { font-size: 13px; color: #2A2620; font-weight: 700; }
.db-side-head {
  display: flex; align-items: baseline; gap: 8px;
}
.db-side-head b { font-size: 13px; color: #2A2620; font-weight: 700; }

/* ---- 左：过敏食材标签 ---- */
.tag-row {
  display: flex; flex-wrap: wrap; gap: 7px;
  margin-top: 12px; min-height: 30px;
  align-items: center;
}
.tag {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11.5px; font-weight: 600; color: #C0522F;
  background: rgba(201, 110, 80, 0.1);
  border: 1px solid rgba(201, 110, 80, 0.35);
  border-radius: 999px; padding: 4px 11px;
  animation: tagPop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tag button {
  border: none; background: none; cursor: pointer;
  color: #C0522F; font-size: 13px; line-height: 1;
  padding: 0; display: flex;
}
@keyframes tagPop {
  from { transform: scale(0.6); opacity: 0; }
  to   { transform: scale(1); opacity: 1; }
}
.tag-input {
  flex: 1; min-width: 150px;
  border: none; outline: none; background: none;
  font-size: 12.5px; color: #2A2620;
  font-family: inherit;
}
.tag-input::placeholder { color: rgba(42, 38, 32, 0.3); }

.sec-label {
  margin-top: 16px;
  font-size: 10.5px; color: #B8863B;
  letter-spacing: 0.08em; font-weight: 600;
  display: flex; align-items: center; gap: 10px;
}
.sec-label::before, .sec-label::after {
  content: ''; flex: 1; height: 0;
  border-top: 1px dashed rgba(184, 134, 59, 0.3);
}

.chips {
  display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px;
}
.chip {
  font-size: 11.5px; color: #6E6350;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(184, 134, 59, 0.25);
  padding: 5px 13px; border-radius: 999px;
  cursor: pointer; transition: 0.25s;
  display: inline-flex; align-items: center; gap: 6px;
  font-family: inherit;
}
.chip svg { color: #B9A78A; transition: 0.25s; }
.chip:hover { border-color: #B8863B; color: #B8863B; }
.chip.on {
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; border-color: transparent; font-weight: 600;
  box-shadow: 0 4px 14px rgba(184, 134, 59, 0.35);
}
.chip.on svg { color: #F6EAD6; }

.save-row {
  display: flex; gap: 10px; margin-top: 16px; align-items: center;
}
.save-note { font-size: 10.5px; color: rgba(42, 38, 32, 0.4); }
.btn-gold {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 9px 20px; border-radius: 10px; border: none; cursor: pointer;
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; font-size: 12.5px; font-weight: 600; letter-spacing: 0.04em;
  transition: 0.25s; font-family: inherit;
}
.btn-gold:hover { opacity: 0.9; transform: translateY(-1px); }
.btn-gold:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }

/* ---- 右：口味星环 ---- */
.taste-list {
  display: flex; flex-direction: column; gap: 8px; margin-top: 12px;
}
.taste {
  display: flex; align-items: center; gap: 10px;
  border: 1px solid rgba(184, 134, 59, 0.2);
  background: rgba(255, 255, 255, 0.65);
  border-radius: 12px; padding: 9px 13px;
  cursor: pointer; transition: 0.25s;
}
.taste b {
  font-size: 12.5px; color: #2A2620; width: 52px;
}
.heat { display: flex; gap: 3px; }
.heat i {
  width: 7px; height: 7px; border-radius: 50%;
  background: rgba(184, 134, 59, 0.18); transition: 0.25s;
}
.heat i.f1 { background: #7FAE8E; }
.heat i.f2 { background: #9FBF8F; }
.heat i.f3 { background: #D9A24A; }
.heat i.f4 { background: #C98F6F; }
.heat i.f5 { background: #C0522F; }
.taste .st {
  margin-left: auto;
  font-size: 10px; color: rgba(42, 38, 32, 0.35);
}
.taste:hover { border-color: rgba(184, 134, 59, 0.45); }
.taste.on {
  border-color: #B8863B;
  background: linear-gradient(135deg, rgba(232, 185, 115, 0.16), rgba(184, 134, 59, 0.08));
  box-shadow: 0 4px 14px rgba(184, 134, 59, 0.2);
}
.taste.on .st { color: #B8863B; font-weight: 700; }

/* ---- 辣度火焰（热度光点右侧 · 只在已选口味点亮） ---- */
.taste .fx {
  position: relative;
  width: 46px; height: 36px; flex-shrink: 0;
  opacity: 0; transition: opacity 0.35s;
}
.taste.on .fx { opacity: 1; }
.fx .spark {
  position: absolute; bottom: 8px;
  width: 3.5px; height: 3.5px; border-radius: 50%;
  background: #D9A24A;
  animation: sparkTw 1.25s ease-in-out infinite;
}
.fx .spark.s1 { left: 30%; }
.fx .spark.s2 { left: 52%; bottom: 15px; animation-delay: 0.42s; background: #E8B45C; }
.fx .spark.s3 { left: 70%; animation-delay: 0.85s; }
@keyframes sparkTw {
  0%, 100% { opacity: 0.12; transform: translateY(0) scale(0.75); }
  50% { opacity: 1; transform: translateY(-4px) scale(1.3); }
}
.fx .flame {
  position: absolute; bottom: 3px; left: 50%;
  margin-left: -8px; width: 16px;
}
.fx .flame i {
  display: block; width: 100%;
  height: calc(30px * var(--h, 0.6));
  border-radius: 50% 50% 32% 32% / 64% 64% 36% 36%;
  background: radial-gradient(ellipse at 50% 80%, #FFF6DE 0%, var(--c1) 34%, var(--c2) 66%, rgba(201, 58, 31, 0) 76%);
  filter: blur(0.6px);
  transform-origin: 50% 100%;
  animation: flick var(--spd, 1s) ease-in-out infinite alternate;
  box-shadow: 0 0 10px -2px var(--c2);
}
/* 渐进等级：适中(2) 小火苗 → 重口味(3) → 微辣(4) → 辣(5) 烈焰 */
.fx[data-lv="2"] { --h: 0.5;  --c1: #E8CE96; --c2: #D9A24A; --spd: 1.3s; }
.fx[data-lv="3"] { --h: 0.75; --c1: #F0C46B; --c2: #E0863C; --spd: 0.95s; }
.fx[data-lv="4"] { --h: 1.05; --c1: #F2A54C; --c2: #D95F2B; --spd: 0.7s; }
.fx[data-lv="5"] { --h: 1.35; --c1: #FF8A4C; --c2: #C93A1F; --spd: 0.45s; }
.fx[data-lv="5"] .flame i { box-shadow: 0 0 16px 1px rgba(201, 58, 31, 0.5); }
.fx[data-lv="5"] .spark { opacity: 0.9; }
@keyframes flick {
  0%   { transform: scaleX(1.06) scaleY(0.94) rotate(-2.5deg); }
  45%  { transform: scaleX(0.94) scaleY(1.1) rotate(1.5deg); }
  100% { transform: scaleX(1.04) scaleY(0.9) rotate(2.5deg); }
}

/* ---- 响应式 ---- */
@media (max-width: 1000px) {
  .db-blocks { grid-template-columns: 1fr; }
}
</style>
