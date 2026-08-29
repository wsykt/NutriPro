<template>
  <div class="diet-page">
    <!-- ===== 深壳星轨带（与首页/代录星链同构 · 亲缘星球上下浮动） ===== -->
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
            <span class="crumb-node hot"><span class="nd"><Link2 :size="13" /></span>成员关系</span>
          </span>
        </div>
        <div class="db-top-right">
          <span class="db-date"><UsersRound :size="12" />监护 <b>{{ wards.length }}</b> · 被监护 <b>{{ guardians.length }}</b></span>
        </div>
      </div>

      <div class="db-const">
        <svg class="db-line" viewBox="0 0 1200 104" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 150 52 C 300 8, 440 8, 560 52 S 830 96, 960 52 S 1130 8, 1200 52" />
        </svg>

        <div class="db-core-wrap">
          <div class="db-core">
            <span class="star"><Link2 :size="19" /></span>
            <span class="tt"><b>亲缘星链</b><span>KIN LINK</span></span>
          </div>
        </div>

        <!-- 星球：待确认邀请（红点脉冲）→ 我监护的亲属（金边）→ 我的监护人（银边） -->
        <div
          v-for="(s, i) in stations" :key="s.key"
          class="db-station-wrap"
          :style="{ left: stationLeft(i, stations.length) + '%' }"
        >
          <div class="db-station-float" :style="floatStyle(i)">
            <button
              class="db-station"
              :class="s.cls"
              :aria-label="s.nm"
              @click="s.kind === 'ward' ? goActAs(s.raw) : undefined"
            >
              <Bell v-if="s.kind === 'pending'" :size="15" />
              <span v-else class="ward-badge" :class="{ silver: s.kind === 'guardian' }">{{ s.nm.slice(0, 1) }}</span>
              <span class="nm">{{ s.nm }}</span>
              <span class="ds">{{ s.ds }}</span>
            </button>
          </div>
        </div>

        <!-- 空态 -->
        <div v-if="stations.length === 0 && !loading" class="db-empty-star">
          星链还是空的 · 在下方发起第一份邀请吧
        </div>
      </div>
    </div>

    <!-- ===== 浅芯工作区（星链管理） ===== -->
    <div class="db-paper" ref="paperRef">
      <div class="db-head" data-anim>
        <div class="sec-t">星链管理 · 邀请与监护的生命周期</div>
      </div>

      <div v-if="toastMsg" class="kr-toast" :class="{ err: toastErr }" data-anim>{{ toastMsg }}</div>

      <div class="db-blocks">
        <!-- 左：发起邀请 + 待确认邀请 -->
        <div class="db-block main" data-anim>
          <div class="bl-head"><b>发起邀请</b><span>输入对方注册用户名</span></div>

          <div class="inv-row">
            <input v-model="wardUsername" placeholder="被监护人用户名（登录账号）" @keyup.enter="handleAdd" />
            <button class="btn-gold" :disabled="submitting" @click="handleAdd">
              <Send :size="13" />{{ submitting ? '发送中…' : '发送邀请' }}
            </button>
          </div>

          <div class="sec-label">待确认的邀请</div>

          <div v-if="pendingList.length === 0" class="kr-empty">
            暂无待确认的邀请 · 发出后对方确认即建立星链
          </div>
          <div
            v-for="item in pendingList" :key="item.relationId"
            class="inv-card"
          >
            <span class="inv-orb"><Bell :size="14" /></span>
            <div class="ki-txt">
              <b>来自：{{ item.guardianUsername }}</b>
              <span>邀请您作为被监护人 · {{ formatDate(item.createdAt) }}</span>
            </div>
            <div class="op">
              <button class="btn-mini gold" @click="handleConfirm(item.relationId)">接受</button>
              <button class="btn-mini red" @click="handleReject(item.relationId)">拒绝</button>
            </div>
          </div>

          <div class="kr-note">解除关系前会弹出气泡二次确认，避免误触。</div>
        </div>

        <!-- 右：我监护的亲属 + 我的监护人 -->
        <div class="db-block side" data-anim>
          <div class="bl-head"><b>我监护的亲属</b><span>可直接去代录</span></div>

          <div v-if="wards.length === 0" class="kr-empty">暂无监护中的亲属</div>
          <div v-for="w in wards" :key="w.relationId" class="kin-item">
            <span class="kin-orb">{{ (w.wardUsername || '·').slice(0, 1) }}</span>
            <div class="ki-txt">
              <b>{{ w.wardUsername }}</b>
              <span>ID #{{ w.wardId }} · 可代录 / 查看报告</span>
            </div>
            <div class="op">
              <button class="btn-mini gold" @click="goActAs(w)">去代录</button>
              <button class="btn-mini red" @click="askRemove(w.relationId, w.wardUsername)">解除</button>
            </div>
          </div>

          <div class="sec-label">我的监护人</div>

          <div v-if="guardians.length === 0" class="kr-empty">暂无监护人</div>
          <div v-for="g in guardians" :key="g.relationId" class="kin-item">
            <span class="kin-orb silver">{{ (g.guardianUsername || '·').slice(0, 1) }}</span>
            <div class="ki-txt">
              <b>{{ g.guardianUsername }}</b>
              <span>可替您录入饮食 / 查看报告 / 修改资料</span>
            </div>
            <span class="guard-chip">监护中</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 解除关系 · 气泡二次确认（无遮罩） -->
    <div v-if="removeTarget" class="kr-bubble">
      <b>解除监护关系？</b>
      <span>确认后将解除与「{{ removeTarget.name }}」的星链连接，双方都不再能代录与查看报告。</span>
      <div class="kr-bubble-op">
        <button class="btn-mini red" @click="confirmRemove">确认解除</button>
        <button class="btn-mini plain" @click="removeTarget = null">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import {
  LayoutGrid, UsersRound, Link2, Bell, Send
} from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'

const userStore = useUserStore()
const router = useRouter()

const wardUsername = ref('')
const submitting = ref(false)
const loading = ref(false)
const toastMsg = ref('')
const toastErr = ref(false)
const removeTarget = ref<{ relationId: number; name: string } | null>(null)

const wards = ref<Array<{ relationId: number; wardId: number; wardUsername: string }>>([])
const guardians = ref<Array<{ relationId: number; guardianId: number; guardianUsername: string }>>([])
const pendingList = ref<Array<{ relationId: number; guardianId?: number; guardianUsername: string; createdAt?: any }>>([])

// ---- 星轨星球：待确认（红点脉冲）→ 我监护（金边）→ 监护我（银边） ----
const stations = computed(() => {
  const list: Array<{
    key: string; kind: 'pending' | 'ward' | 'guardian'
    nm: string; ds: string; cls: string; raw: any
  }> = []
  pendingList.value.forEach(p => list.push({
    key: 'pending-' + p.relationId, kind: 'pending',
    nm: '邀请·' + p.guardianUsername, ds: '待对方确认 · 红点脉冲',
    cls: 'pulse-inv', raw: p
  }))
  wards.value.forEach(w => list.push({
    key: 'ward-' + w.wardId, kind: 'ward',
    nm: w.wardUsername, ds: '我监护 · 点击去代录',
    cls: 'lit', raw: w
  }))
  guardians.value.forEach(g => list.push({
    key: 'guardian-' + g.guardianId, kind: 'guardian',
    nm: g.guardianUsername, ds: '监护我 · 可代录/改资料',
    cls: '', raw: g
  }))
  return list
})

function popToast(msg: string, isErr = false) {
  toastMsg.value = msg
  toastErr.value = isErr
  setTimeout(() => { if (toastMsg.value === msg) toastMsg.value = '' }, 3200)
}

function errMsg(e: any) {
  return e?.response?.data?.message || e?.message || '操作失败'
}

function goHome() { router.push('/dashboard/home') }
function goHub() { router.push({ path: '/dashboard/hub', query: { group: 'user' } }) }

// ---- 去代录：切换 actAs 身份并前往记录三餐 ----
function goActAs(w: { wardId: number; wardUsername: string }) {
  userStore.setActAs(w.wardId)
  popToast(`已切换为替 ${w.wardUsername} 记录 · 前往记录三餐`)
  setTimeout(() => { router.push('/dashboard/food-input') }, 650)
}

// ---- 发起邀请 ----
async function handleAdd() {
  const name = wardUsername.value.trim()
  if (!name) { popToast('请输入对方用户名', true); return }
  submitting.value = true
  try {
    await api.relation.add(name)
    wardUsername.value = ''
    popToast('邀请已发送 · 星轨上出现红点脉冲星球，等待对方确认')
    await loadAll()
  } catch (e: any) {
    popToast(errMsg(e), true)
  } finally {
    submitting.value = false
  }
}

// ---- 接受邀请：星球从星轨弹出并常驻浮动 ----
async function handleConfirm(relationId: number) {
  const before = new Set(stations.value.map(s => s.key))
  try {
    await api.relation.confirm(relationId)
    popToast('已接受邀请 · 对方星球已加入你的监护轨道')
    await loadAll()
    await nextTick()
    const newKey = stations.value.find(s => !before.has(s.key))?.key
    if (newKey && bandRef.value) {
      const wraps = bandRef.value.querySelectorAll('.db-station-wrap')
      const idx = stations.value.findIndex(s => s.key === newKey)
      if (idx >= 0 && wraps[idx]) {
        gsap.fromTo(wraps[idx],
          { scale: 0, opacity: 0 },
          { scale: 1, opacity: 1, duration: 0.5, ease: 'back.out(1.7)', clearProps: 'opacity,transform' })
      }
    }
  } catch (e: any) {
    popToast(errMsg(e), true)
  }
}

async function handleReject(relationId: number) {
  try {
    await api.relation.reject(relationId)
    popToast('已拒绝邀请 · 星球从轨道淡出')
    await loadAll()
  } catch (e: any) {
    popToast(errMsg(e), true)
  }
}

// ---- 解除关系：气泡二次确认（无遮罩） ----
function askRemove(relationId: number, name: string) {
  removeTarget.value = { relationId, name }
}

async function confirmRemove() {
  if (!removeTarget.value) return
  const { relationId, name } = removeTarget.value
  removeTarget.value = null
  try {
    await api.relation.remove(relationId)
    popToast(`已解除与 ${name} 的星链 · 星球已从轨道移除`)
    await loadAll()
  } catch (e: any) {
    popToast(errMsg(e), true)
  }
}

// ---- 数据加载（兼容 camelCase / snake_case 字段） ----
async function loadAll() {
  loading.value = true
  try {
    const myWards: any = await api.relation.myWards()
    wards.value = (Array.isArray(myWards) ? myWards : []).map((r: any) => ({
      relationId: r.relationId ?? r.relation_id,
      wardId: r.wardId ?? r.ward_id,
      wardUsername: r.wardUsername ?? r.ward_username
    }))
  } catch {}
  try {
    const myGuardians: any = await api.relation.myGuardians()
    guardians.value = (Array.isArray(myGuardians) ? myGuardians : []).map((r: any) => ({
      relationId: r.relationId ?? r.relation_id,
      guardianId: r.guardianId ?? r.guardian_id,
      guardianUsername: r.guardianUsername ?? r.guardian_username
    }))
  } catch {}
  try {
    const pending: any = await api.relation.pendingInvitations()
    pendingList.value = (Array.isArray(pending) ? pending : []).map((r: any) => ({
      relationId: r.relationId ?? r.relation_id,
      guardianId: r.guardianId ?? r.guardian_id,
      guardianUsername: r.guardianUsername ?? r.guardian_username,
      createdAt: r.createdAt ?? r.created_at
    }))
  } catch {}
  loading.value = false
}

function formatDate(v: any) {
  if (!v) return '刚刚'
  try {
    const d = new Date(v)
    if (Number.isNaN(d.getTime())) return String(v)
    return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch { return String(v) }
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

// ===== 入场动效（与首页/代录星链同节奏：面包屑点亮 → 星球弹出 → 浅芯浮起） =====
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
  userStore.init().then(() => loadAll()).catch(() => loadAll())
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

/* ---- 亲缘星球（待确认红点 / 金边 / 银边） ---- */
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
  font-family: inherit;
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
.db-station.lit {
  border-color: #E8B973;
  box-shadow: 0 0 0 5px rgba(217, 162, 74, 0.16), 0 0 20px rgba(217, 162, 74, 0.4);
}
.ward-badge {
  width: 30px; height: 30px; border-radius: 50%;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(217, 162, 74, 0.35);
  font-size: 12px; font-weight: 700; color: #F0E2C4;
  display: flex; align-items: center; justify-content: center;
}
.ward-badge.silver {
  border-color: rgba(108, 143, 190, 0.6);
  color: #9DB9DE;
}
/* 待确认邀请 · 红点脉冲 */
.db-station.pulse-inv::before {
  content: '';
  position: absolute; top: -4px; right: -4px;
  width: 10px; height: 10px; border-radius: 50%;
  background: #E0655A;
  box-shadow: 0 0 8px rgba(224, 101, 90, 0.8);
  animation: invPulse 1.6s ease-in-out infinite;
}
@keyframes invPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.35); opacity: 0.65; }
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

/* ---- 气泡提示（无遮罩） ---- */
.kr-toast {
  margin-top: 12px;
  display: inline-flex; align-items: center;
  background: rgba(127, 174, 142, 0.12);
  border: 1px solid rgba(127, 174, 142, 0.35);
  border-radius: 999px; padding: 8px 16px;
  font-size: 12px; color: #2F7D5B; font-weight: 600;
  animation: toastPop 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.kr-toast.err {
  background: rgba(201, 110, 80, 0.12);
  border-color: rgba(201, 110, 80, 0.4);
  color: #C0522F;
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
.bl-head {
  display: flex; align-items: baseline; gap: 8px;
}
.bl-head b { font-size: 13px; color: #2A2620; font-weight: 700; }
.bl-head span { font-size: 10px; color: rgba(42, 38, 32, 0.4); }

/* ---- 左：发起邀请 + 待确认 ---- */
.inv-row {
  display: flex; gap: 10px; margin-top: 12px;
}
.inv-row input {
  flex: 1; min-width: 0;
  padding: 9px 12px; border-radius: 10px;
  border: 1px solid rgba(184, 134, 59, 0.25);
  background: #fff; font-size: 12.5px; color: #2A2620;
  outline: none; font-family: inherit;
  transition: border-color 0.25s ease;
}
.inv-row input:focus { border-color: #B8863B; }
.sec-label {
  margin-top: 16px; margin-bottom: 4px;
  font-size: 10.5px; color: #B8863B;
  letter-spacing: 0.08em; font-weight: 600;
  display: flex; align-items: center; gap: 10px;
}
.sec-label::before, .sec-label::after {
  content: ''; flex: 1; height: 0;
  border-top: 1px dashed rgba(184, 134, 59, 0.3);
}
.inv-card {
  margin-top: 10px;
  border: 1px solid rgba(217, 162, 74, 0.4);
  background: linear-gradient(135deg, rgba(232, 185, 115, 0.14), rgba(184, 134, 59, 0.06));
  border-radius: 14px; padding: 12px 14px;
  display: flex; align-items: center; gap: 11px;
  animation: tagPop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes tagPop {
  from { transform: scale(0.92) translateY(6px); opacity: 0; }
  to   { transform: scale(1) translateY(0); opacity: 1; }
}
.inv-orb {
  width: 34px; height: 34px; flex-shrink: 0; border-radius: 50%;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(217, 162, 74, 0.45);
  color: #E8B973;
  display: flex; align-items: center; justify-content: center;
  position: relative;
}
.inv-orb::before {
  content: '';
  position: absolute; top: -3px; right: -3px;
  width: 8px; height: 8px; border-radius: 50%;
  background: #E0655A;
  box-shadow: 0 0 8px rgba(224, 101, 90, 0.8);
  animation: invPulse 1.6s ease-in-out infinite;
}
.ki-txt { min-width: 0; }
.ki-txt b {
  display: block; font-size: 12.5px; color: #2A2620;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.inv-card .ki-txt span { font-size: 10.5px; color: #8A6428; }
.kr-note {
  margin-top: 14px;
  font-size: 10.5px; color: rgba(42, 38, 32, 0.4); line-height: 1.8;
}

/* ---- 右：监护列表 ---- */
.kin-item {
  display: flex; align-items: center; gap: 11px;
  padding: 10px 12px; border-radius: 12px;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(184, 134, 59, 0.16);
  transition: 0.25s;
}
.kin-item + .kin-item { margin-top: 8px; }
.kin-item:hover {
  border-color: rgba(184, 134, 59, 0.35);
  transform: translateY(-1px);
}
.kin-item .ki-txt { flex: 1; }
.kin-item .ki-txt span { font-size: 10.5px; color: rgba(42, 38, 32, 0.45); }
.kin-orb {
  width: 34px; height: 34px; flex-shrink: 0; border-radius: 50%;
  background: radial-gradient(circle at 34% 30%, #3A2E1B, #1A140C 72%);
  border: 1px solid rgba(217, 162, 74, 0.35);
  font-size: 12px; font-weight: 700; color: #F0E2C4;
  display: flex; align-items: center; justify-content: center;
}
.kin-orb.silver {
  border-color: rgba(108, 143, 190, 0.6);
  color: #9DB9DE;
}
.kin-item .op { margin-left: auto; display: flex; gap: 6px; flex-shrink: 0; }
.guard-chip {
  margin-left: auto; flex-shrink: 0;
  font-size: 10px; color: #8A6428;
  background: rgba(217, 162, 74, 0.1);
  border: 1px dashed rgba(184, 134, 59, 0.35);
  border-radius: 999px; padding: 2px 9px;
}
.kr-empty {
  margin-top: 10px;
  border: 1px dashed rgba(184, 134, 59, 0.3);
  border-radius: 12px; padding: 12px 14px;
  font-size: 11.5px; color: #8C7A5E; line-height: 1.7;
}

/* ---- 通用按钮 ---- */
.btn-gold {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 9px 20px; border-radius: 10px; border: none; cursor: pointer;
  background: linear-gradient(135deg, #E8B973, #B8863B);
  color: #fff; font-size: 12.5px; font-weight: 600; letter-spacing: 0.04em;
  transition: 0.25s; font-family: inherit;
}
.btn-gold:hover { opacity: 0.9; transform: translateY(-1px); }
.btn-gold:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
.btn-mini {
  padding: 5px 13px; border-radius: 8px;
  font-size: 11px; font-weight: 600; cursor: pointer;
  border: none; transition: 0.2s; font-family: inherit;
}
.btn-mini.gold { background: linear-gradient(135deg, #E8B973, #B8863B); color: #fff; }
.btn-mini.red { background: rgba(201, 110, 80, 0.12); color: #C0522F; border: 1px solid rgba(201, 110, 80, 0.4); }
.btn-mini.plain { background: none; color: #6E6350; border: 1px solid rgba(184, 134, 59, 0.3); }
.btn-mini:hover { opacity: 0.85; }

/* ---- 解除关系气泡（居中弹出 · 无遮罩 · 无箭头） ---- */
.kr-bubble {
  position: fixed; z-index: 60;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 290px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(184, 134, 59, 0.45);
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 24px 54px -18px rgba(90, 70, 40, 0.5);
  animation: bubblePop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes bubblePop {
  from { transform: translate(-50%, -50%) scale(0.7); opacity: 0; }
  to   { transform: translate(-50%, -50%) scale(1); opacity: 1; }
}
.kr-bubble b {
  display: block; font-size: 13px; color: #2A2620; font-weight: 700;
}
.kr-bubble > span {
  display: block; margin-top: 6px;
  font-size: 11.5px; color: rgba(42, 38, 32, 0.6); line-height: 1.7;
}
.kr-bubble-op {
  display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px;
}

/* ---- 响应式 ---- */
@media (max-width: 1000px) {
  .db-blocks { grid-template-columns: 1fr; }
}
</style>
