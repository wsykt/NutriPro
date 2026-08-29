<template>
  <div class="diet-page">
    <!-- ===== 深壳星轨带（与首页/记录页同构 · 亲属星球上下浮动） ===== -->
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
            <button class="crumb-node" @click="goHub"><span class="nd"><Utensils :size="12" /></span>饮食管理</button>
          </span>
          <span class="crumb-wrap">
            <span class="crumb-link"></span>
            <span class="crumb-node hot"><span class="nd"><Link2 :size="13" /></span>亲属代录</span>
          </span>
        </div>
        <div class="db-top-right">
          <span class="db-date"><UsersRound :size="12" />星链成员 <b>{{ wards.length }}</b> 位</span>
        </div>
      </div>

      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 104" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 52 C 300 8, 440 8, 560 52 S 830 96, 960 52 S 1130 8, 1200 52" />
        </svg>

        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><Link2 :size="19" /></span>
            <span class="tt"><b>代录星链</b><span>WARD LINK</span></span>
          </div>
        </div>

        <!-- 自己（核心位一侧的常驻球） -->
        <div class="db-station-wrap" :style="{ left: stationLeft(0, wards.length + 1) + '%' }">
          <div class="db-station-float" :style="floatStyle(0)">
            <button
              class="db-station st-self"
              :class="{ now: selectedWardId === null }"
              aria-label="自己"
              @click="selectWard(null)"
            >
              <UserRound :size="15" />
              <span class="nm">自己</span>
              <span class="ds">恢复为自己记录</span>
            </button>
          </div>
        </div>

        <!-- 亲属星球 -->
        <div
          v-for="(w, i) in wards" :key="w.wardId"
          class="db-station-wrap"
          :style="{ left: stationLeft(i + 1, wards.length + 1) + '%' }"
        >
          <div class="db-station-float" :style="floatStyle(i + 1)">
            <button
              class="db-station st-ward"
              :class="{ now: selectedWardId === w.wardId }"
              :aria-label="w.wardUsername"
              @click="selectWard(w.wardId)"
            >
              <span class="ward-badge">{{ (w.wardUsername || '·').slice(0, 1) }}</span>
              <span class="nm">{{ w.wardUsername }}</span>
              <span class="ds">点击为 TA 代录三餐</span>
            </button>
          </div>
        </div>

        <!-- 空态 -->
        <div v-if="wards.length === 0 && !wardsLoading" class="db-empty-star">
          还没有已确认的亲属 · 请先前往「亲属关系管理」建立星链
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区（7:5 · 代录星链） ===== -->
    <div class="db-paper" ref="paperRef">
      <div class="db-head" data-anim>
        <div class="sec-t">代录工作区 · 当前链路指向</div>
        <div class="db-pills">
          <span class="pill"><UserRound :size="11" />当前 <b>{{ selectedWardId !== null ? selectedWardName : '自己' }}</b></span>
        </div>
      </div>

      <div v-if="linkToast" class="ff-toast" data-anim>{{ linkToast }}</div>

      <div class="db-blocks">
        <!-- 左：当前对象与前往录入 -->
        <div class="db-block main" data-anim>
          <div class="db-block-head"><b>代录对象</b></div>

          <div class="ff-current">
            <span class="ff-orb" :class="{ ward: selectedWardId !== null }">
              <UserRound v-if="selectedWardId === null" :size="22" />
              <template v-else>{{ (selectedWardName || '·').slice(0, 1) }}</template>
            </span>
            <div class="ff-current-txt">
              <b>{{ selectedWardId !== null ? selectedWardName : '我自己' }}</b>
              <span v-if="selectedWardId !== null">已进入为 TA 操作的模式，页面内的饮食记录、营养分析均会保存到该亲属账号。</span>
              <span v-else>当前在自己的账号下记录，所有数据保存到自己名下。</span>
            </div>
          </div>

          <div class="ff-go">
            <button class="confirm-btn" @click="goToFoodInput">
              <ClipboardList :size="14" />前往记录三餐
            </button>
            <button
              v-if="selectedWardId !== null"
              class="ghost-add"
              @click="selectWard(null)"
            ><X :size="13" />取消代录</button>
          </div>

          <div v-if="wards.length === 0 && !wardsLoading" class="ff-empty">
            暂无可代录的亲属，请先前往
            <button class="ff-link" @click="goFamilyManage">亲属关系管理</button>
            添加亲属并等待对方确认。
          </div>
        </div>

        <!-- 右：星链指引 -->
        <div class="db-block side" data-anim>
          <div class="db-side-head"><b>星链指引</b><span>三步完成代录</span></div>
          <div class="ff-steps">
            <div class="ff-step" v-for="(s, i) in steps" :key="i">
              <span class="ff-step-no">{{ i + 1 }}</span>
              <div class="ff-step-txt">
                <b>{{ s.title }}</b>
                <span>{{ s.desc }}</span>
              </div>
            </div>
          </div>
          <div class="ff-note">
            <Info :size="13" />
            代录期间，所有页面的数据读写都会指向亲属账号，随时可以点击「自己」星球切回。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import {
  LayoutGrid, Utensils, Link2, UsersRound, UserRound,
  ClipboardList, X, Info
} from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const router = useRouter()

const selectedWardId = ref<number | null>(null)
const wardsLoading = ref(false)
const linkToast = ref('')

const wards = computed(() => userStore.wards || [])

const selectedWardName = computed(() => {
  if (selectedWardId.value === null) return ''
  const w = wards.value.find((x: any) => x.wardId === selectedWardId.value)
  return (w && w.wardUsername) || ''
})

const steps = [
  { title: '点亮亲属星球', desc: '在上方星轨点击要代录的家人，激活代录模式' },
  { title: '前往记录三餐', desc: '进入记录页后像平时一样选餐次、加食物' },
  { title: '数据自动归档', desc: '所有记录自动保存到亲属账号，无需额外操作' }
]

function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'diet' } }) }
function goToFoodInput() { router.push('/dashboard/food-input') }
function goFamilyManage() { router.push('/dashboard/family?tab=relation') }

function selectWard(wardId: number | null) {
  selectedWardId.value = wardId
  userStore.setActAs(wardId)
  linkToast.value = wardId === null
    ? '已切回自己，后续记录保存到自己账号'
    : `已进入为 ${selectedWardName.value} 代录的模式`
  setTimeout(() => { linkToast.value = '' }, 3200)
}

// ---- 星轨站点：横向分布 + 各自漂浮节奏 ----
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

// ===== 入场动效（与首页/记录页同节奏：面包屑点亮 → 星球弹出 → 浅芯浮起） =====
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
  }
}

onMounted(async () => {
  animateEntrance()
  userStore.init()
  // 同步当前代录身份
  selectedWardId.value = userStore.actAsUserId != null ? Number(userStore.actAsUserId) : null
  if (userStore.wards.length === 0) {
    wardsLoading.value = true
    try { await userStore.loadWards() } catch { /* 未登录或接口异常时保持空态 */ }
    wardsLoading.value = false
  }
})
</script>

<style scoped>
.diet-page {
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
.db-empty-star {
  position: absolute; left: 50%; top: 50%;
  transform: translate(-50%, -50%);
  font-size: 11px; color: rgba(140, 122, 94, 0.8);
  border: 1px dashed rgba(217, 162, 74, 0.3);
  border-radius: 999px; padding: 6px 16px;
  white-space: nowrap;
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

/* ---- 星球（自己 + 亲属） ---- */
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
.ward-badge {
  width: 30px; height: 30px; border-radius: 50%;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(217, 162, 74, 0.35);
  font-size: 12px; font-weight: 700; color: #F0E2C4;
  display: flex; align-items: center; justify-content: center;
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
.db-station.st-ward.now .ward-badge {
  border-color: #E8B973; color: #E8B973;
  box-shadow: 0 0 12px rgba(217, 162, 74, 0.5);
}

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

.ff-toast {
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
.db-side-head span { font-size: 10px; color: rgba(42, 38, 32, 0.4); }

/* ---- 左：当前对象 ---- */
.ff-current {
  margin-top: 14px;
  display: flex; align-items: center; gap: 14px;
  background: rgba(217, 162, 74, 0.07);
  border: 1px solid rgba(184, 134, 59, 0.18);
  border-radius: 14px; padding: 14px 16px;
}
.ff-orb {
  width: 52px; height: 52px; border-radius: 50%; flex-shrink: 0;
  background: radial-gradient(circle at 34% 30%, rgba(232, 185, 115, 0.4), rgba(184, 134, 59, 0.15) 72%);
  border: 1px solid rgba(184, 134, 59, 0.35);
  color: #B8863B; font-size: 18px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  animation: dbFloat 4.6s ease-in-out infinite alternate;
}
.ff-orb.ward { color: #8A6428; }
.ff-current-txt b { display: block; font-size: 14px; color: #2A2620; font-weight: 700; }
.ff-current-txt span {
  display: block; margin-top: 4px;
  font-size: 11.5px; color: rgba(42, 38, 32, 0.55); line-height: 1.65;
}
.ff-go {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  margin-top: 14px;
}
.ff-empty {
  margin-top: 14px;
  border: 1px dashed rgba(184, 134, 59, 0.35);
  border-radius: 12px; padding: 14px 16px;
  font-size: 12px; color: #8C7A5E; line-height: 1.7;
}
.ff-link {
  border: none; background: none; padding: 0;
  font-size: 12px; font-weight: 700; color: #B8863B;
  cursor: pointer; text-decoration: underline dotted;
  font-family: inherit;
}
.ff-link:hover { color: #8A6428; }

/* ---- 右：指引 ---- */
.ff-steps {
  margin-top: 12px;
  display: flex; flex-direction: column; gap: 12px;
}
.ff-step { display: flex; align-items: flex-start; gap: 10px; }
.ff-step-no {
  width: 22px; height: 22px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  margin-top: 1px;
}
.ff-step-txt b { display: block; font-size: 12px; color: #2A2620; font-weight: 700; }
.ff-step-txt span {
  display: block; margin-top: 2px;
  font-size: 10.5px; color: rgba(42, 38, 32, 0.5); line-height: 1.6;
}
.ff-note {
  margin-top: 14px; padding-top: 12px;
  border-top: 1px dashed rgba(184, 134, 59, 0.2);
  display: flex; gap: 7px; align-items: flex-start;
  font-size: 10.5px; color: rgba(42, 38, 32, 0.5); line-height: 1.6;
}
.ff-note svg { color: #B8863B; flex-shrink: 0; margin-top: 1px; }

/* ---- 通用 ---- */
.ghost-add {
  display: inline-flex; align-items: center; gap: 6px;
  border: 1px dashed rgba(184, 134, 59, 0.4);
  color: #B8863B; background: none; cursor: pointer;
  font-size: 12px; font-weight: 600; letter-spacing: 0.05em;
  border-radius: 10px; padding: 8px 14px; transition: 0.25s;
  font-family: inherit;
}
.ghost-add:hover { background: rgba(217, 162, 74, 0.1); border-color: #B8863B; }
.confirm-btn {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 8px 20px; border-radius: 10px; border: none; cursor: pointer;
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; font-size: 12.5px; font-weight: 600; letter-spacing: 0.04em;
  transition: 0.25s; font-family: inherit;
}
.confirm-btn:hover { opacity: 0.9; transform: translateY(-1px); }

/* ---- 响应式 ---- */
@media (max-width: 1000px) {
  .db-blocks { grid-template-columns: 1fr; }
}
</style>
