<template>
  <div class="star-orbit" aria-label="功能导航轨道">
    <div class="so-dash" aria-hidden="true"></div>

    <!-- 外层公转：整体坐标系旋转；每个节点内层反向自转，保证图标始终朝上 -->
    <div class="so-spin">
      <button
        v-for="(g, i) in groups"
        :key="g.key"
        class="so-node"
        :style="{ left: `calc(50% + ${nodePos[i].x}px)`, top: `calc(50% + ${nodePos[i].y}px)` }"
        :aria-label="g.name"
        @click="onNodeClick(g, $event)"
      >
        <span class="so-node-in">
          <component :is="g.icon" class="so-node-ic" :stroke-width="1.75" />
          <span class="so-tip">{{ g.name }}</span>
        </span>
      </button>
    </div>

    <!-- 中心热量环：数据即轨道核心 -->
    <div class="so-core">
      <svg viewBox="0 0 92 92">
        <defs>
          <linearGradient id="soGold" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#E8B973" />
            <stop offset="60%" stop-color="#D9A24A" />
            <stop offset="100%" stop-color="#B36B2A" />
          </linearGradient>
        </defs>
        <circle class="so-ring-bg" cx="46" cy="46" r="40" />
        <circle ref="ringFg" class="so-ring-fg" cx="46" cy="46" r="40" />
      </svg>
      <div class="so-core-in">
        <b ref="pctEl">0%</b>
        <span>今日热量</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import { Users, Utensils, HeartPulse, BookOpen, ChefHat } from 'lucide-vue-next'
import type { Component } from 'vue'

const props = defineProps<{ percent: number }>()

const router = useRouter()

interface OrbitGroup { key: string; name: string; icon: Component }
// 与 Dashboard.vue 侧栏 groups 保持一致的 5 个功能分组
const groups: OrbitGroup[] = [
  { key: 'user', name: '用户中心', icon: Users },
  { key: 'diet', name: '饮食管理', icon: Utensils },
  { key: 'health', name: '健康监测', icon: HeartPulse },
  { key: 'knowledge', name: '知识中心', icon: BookOpen },
  { key: 'recipe', name: '菜谱美食', icon: ChefHat },
]

// 节点角度分布（-90° 为正上方），公转半径 72px
const R = 72
const angles = [-90, -18, 54, 126, 198]
const nodePos = angles.map(a => {
  const rad = (a * Math.PI) / 180
  return { x: +(R * Math.cos(rad)).toFixed(2), y: +(R * Math.sin(rad)).toFixed(2) }
})

const ringFg = ref<SVGCircleElement | null>(null)
const pctEl = ref<HTMLElement | null>(null)
let pctTween: ReturnType<typeof gsap.to> | null = null
let navigating = false

const C = 2 * Math.PI * 40

function playRing() {
  if (!ringFg.value) return
  ringFg.value.style.strokeDasharray = String(C)
  gsap.set(ringFg.value, { strokeDashoffset: C })
  const target = Math.max(0, Math.min(100, props.percent))
  if (pctTween) pctTween.kill()
  const o = { v: 0 }
  pctTween = gsap.to(o, {
    v: target,
    duration: 1.2,
    delay: 0.35,
    ease: 'power2.out',
    onUpdate: () => {
      if (pctEl.value) pctEl.value.textContent = Math.round(o.v) + '%'
      if (ringFg.value) ringFg.value.style.strokeDashoffset = String(C * (1 - o.v / 100))
    }
  })
}

onMounted(() => {
  playRing()
  // 节点入场（clearProps 释放 transform，保证 hover 缩放由 CSS 接管）
  gsap.fromTo('.so-node',
    { scale: 0, opacity: 0 },
    { scale: 1, opacity: 1, duration: 0.5, stagger: 0.08, delay: 0.15, ease: 'back.out(1.7)', clearProps: 'opacity,transform' }
  )
})

watch(() => props.percent, () => playRing())

onBeforeUnmount(() => { if (pctTween) pctTween.kill() })

/**
 * 点击节点：金色粒子飞向侧栏对应图标 → 图标脉冲点亮，
 * 该动画完整结束后才执行页面转场
 */
function onNodeClick(g: OrbitGroup, e: MouseEvent) {
  if (navigating) return
  const nodeEl = e.currentTarget as HTMLElement
  const target = document.querySelector(`.menu-icon-wrap[data-orbit-group="${g.key}"]`) as HTMLElement | null
  // 兜底：找不到侧栏图标时直接跳转
  if (!target) {
    router.push({ path: '/dashboard/hub', query: { group: g.key } })
    return
  }
  navigating = true

  const nr = nodeEl.getBoundingClientRect()
  const tr = target.getBoundingClientRect()
  const sx = nr.left + nr.width / 2
  const sy = nr.top + nr.height / 2
  const dx = tr.left + tr.width / 2 - sx
  const dy = tr.top + tr.height / 2 - sy

  // 粒子挂在 body（fixed 层），跨组件飞向侧栏
  const fly = document.createElement('span')
  fly.className = 'so-fly-particle'
  fly.style.left = sx - 6 + 'px'
  fly.style.top = sy - 6 + 'px'
  document.body.appendChild(fly)

  gsap.to(fly, {
    x: dx,
    y: dy,
    duration: 0.72,
    ease: 'power3.inOut',
    onComplete: () => {
      fly.remove()
      // 粒子抵达：侧栏图标脉冲点亮（0.6s），动画完整结束后再转场
      target.classList.add('orbit-pulse')
      setTimeout(() => {
        target.classList.remove('orbit-pulse')
        navigating = false
        router.push({ path: '/dashboard/hub', query: { group: g.key } })
      }, 620)
    }
  })
}
</script>

<style scoped>
.star-orbit {
  position: relative;
  width: 188px;
  height: 188px;
  flex-shrink: 0;
  align-self: center;
  z-index: 1;
}
.so-dash {
  position: absolute;
  inset: 9px;
  border: 1px dashed rgba(217, 162, 74, 0.3);
  border-radius: 50%;
  pointer-events: none;
  /* 虚线环反向缓转（刻度爬行效果），与节点公转形成层次 */
  animation: soSpinRev 54s linear infinite;
}
.so-spin {
  position: absolute;
  inset: 0;
  animation: soSpin 36s linear infinite;
}
/* 节点内层反向自转：抵消公转角度，图标与提示保持正立 */
.so-node-in {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: soSpinRev 36s linear infinite;
}
/* 鼠标移入轨道：公转/自转/虚线全部暂停；移开：自动恢复旋转 */
.star-orbit:hover .so-spin,
.star-orbit:hover .so-node-in,
.star-orbit:hover .so-dash {
  animation-play-state: paused;
}
@keyframes soSpin { to { transform: rotate(360deg); } }
@keyframes soSpinRev { to { transform: rotate(-360deg); } }

.so-node {
  position: absolute;
  width: 40px;
  height: 40px;
  margin: -20px 0 0 -20px;
  border-radius: 50%;
  background: rgba(26, 21, 14, 0.92);
  border: 1px solid rgba(217, 162, 74, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #E8B973;
  transition: transform 0.3s cubic-bezier(0.34, 1.5, 0.5, 1), border-color 0.3s ease, box-shadow 0.3s ease;
}
.so-node:hover {
  transform: scale(1.16);
  border-color: #E8B973;
  box-shadow: 0 0 0 4px rgba(217, 162, 74, 0.15), 0 8px 20px rgba(217, 162, 74, 0.3);
}
.so-node-ic { width: 16px; height: 16px; }
.so-tip {
  position: absolute;
  bottom: 46px; /* 气泡显示在圆圈上方，避免与中心大圈重叠 */
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  font-size: 10px;
  color: #F0E2C4;
  background: rgba(24, 19, 12, 0.94);
  border: 1px solid rgba(217, 162, 74, 0.4);
  padding: 2px 8px;
  border-radius: 999px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.25s ease;
}
.so-node:hover .so-tip { opacity: 1; }

.so-core {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 92px;
  height: 92px;
  pointer-events: none;
}
.so-core svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.so-ring-bg { fill: none; stroke: rgba(217, 162, 74, 0.16); stroke-width: 6; }
.so-ring-fg { fill: none; stroke: url(#soGold); stroke-width: 6; stroke-linecap: round; }
.so-core-in {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.so-core-in b {
  font-family: 'Noto Serif SC', serif;
  font-size: 17px;
  color: #F6EAD6;
  line-height: 1;
}
.so-core-in span {
  font-size: 8.5px;
  color: #B9A78A;
  letter-spacing: 1px;
  margin-top: 4px;
}

/* 粒子挂载在 body 上（跨组件飞行），需全局样式 */
:global(.so-fly-particle) {
  position: fixed;
  z-index: 9999;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  pointer-events: none;
  background: radial-gradient(circle, #F1CF92, #D9A24A);
  box-shadow: 0 0 12px rgba(232, 185, 115, 0.9);
}
</style>
