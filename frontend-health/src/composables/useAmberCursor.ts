/* ============================================================================
 * useAmberCursor · Direction C 赤金 Amber Editorial 自定义光标 composable
 * ----------------------------------------------------------------------------
 * 用法：
 *   <script setup>
 *   import { useAmberCursor } from '../composables/useAmberCursor'
 *   const { cursorDot, cursorHalo } = useAmberCursor()
 *   </script>
 *
 *   <template>
 *     <div class="hc-layer">
 *       <div class="hc-halo" ref="cursorHalo"></div>
 *       <div class="hc-dot" ref="cursorDot"></div>
 *     </div>
 *   </template>
 *
 * 规格（与首页"离开 Hero 区"状态一致）：
 *   · B 柔光光斑 · 锁亮度 0.95 / 0.98 hover（无脉冲闪光）
 *   · 尺寸呼吸 108↔122 idle / 156↔170 hover（2.0s sine 缓动）
 *   · 针尖 6→8px · 紧追 lerp 0.26 · hover 变白
 *   · 拖尾 lerp 0.16
 *   · mix-blend-mode: screen 暖光扫纸面
 *   · 移动端（pointer:coarse）自动隐藏
 * ============================================================================ */

import { onMounted, onBeforeUnmount, ref } from 'vue'

// 唯一 injected style 标签 ID，避免多个 composable 实例重复注入
const AMBER_CURSOR_STYLE_ID = 'amber-cursor-style'

function ensureStyleInjected() {
  if (document.getElementById(AMBER_CURSOR_STYLE_ID)) return
  const style = document.createElement('style')
  style.id = AMBER_CURSOR_STYLE_ID
  style.textContent = `
/* === amber-cursor · Direction C B 柔光光斑（锁亮度 0.95 + 尺寸呼吸）===
   仅在 html.hc-on 作用域内生效，避免影响 Dashboard / 其他页面 */
html.hc-on, html.hc-on *:not(.hc-layer):not(.hc-layer *) {
  cursor: none !important;
}

.hc-layer {
  position: fixed; inset: 0;
  pointer-events: none;
  z-index: 99999;
}

/* B · 针尖：6→8px，紧追 lerp 0.26 */
.hc-dot {
  position: absolute; left: 0; top: 0;
  width: 6px; height: 6px; border-radius: 50%;
  background: #F1CF92;
  box-shadow:
    0 0 12px rgba(217,162,74,0.75),
    0 0 2px rgba(255,255,255,0.75),
    0 0 0 1px rgba(0,0,0,0.35);
  transform: translate(-50%, -50%);
  will-change: transform;
  transition:
    width 0.28s cubic-bezier(0.22,1,0.36,1),
    height 0.28s cubic-bezier(0.22,1,0.36,1),
    background-color 0.28s ease,
    box-shadow 0.28s ease;
}
.hc-dot.is-hover {
  width: 8px; height: 8px;
  background: #ffffff;
  box-shadow:
    0 0 16px rgba(255,255,255,0.7),
    0 0 10px rgba(217,162,74,0.85),
    0 0 0 1px rgba(0,0,0,0.45);
}

/* B · 柔光：径向暖色模糊光斑 + mix-blend-mode: screen
   尺寸呼吸（108↔122 idle / 156↔170 hover，2.0s sine），亮度锁死 0.95 / 0.98 静态 */
.hc-halo {
  position: absolute; left: 0; top: 0;
  width: 114px; height: 114px; border-radius: 50%;
  transform: translate(-50%, -50%);
  filter: blur(10px);
  mix-blend-mode: screen;
  will-change: transform, opacity;
  animation: hc-halo-size-idle 2.0s cubic-bezier(0.25,0.1,0.25,1) infinite;
  opacity: 0.95;
  background: radial-gradient(circle,
    rgba(228,180,108,0.35) 0%,
    rgba(215,163,90,0.185) 40%,
    rgba(205,151,82,0.055) 70%,
    rgba(205,151,82,0)    92%);
}
@keyframes hc-halo-size-idle {
  0%, 100% { width: 108px; height: 108px; }
  50%      { width: 122px; height: 122px; }
}

.hc-halo.is-hover {
  animation-name: hc-halo-size-hover;
  animation-duration: 2.0s;
  animation-timing-function: cubic-bezier(0.25,0.1,0.25,1);
  animation-iteration-count: infinite;
  opacity: 0.98;
  filter: blur(10.5px);
  background: radial-gradient(circle,
    rgba(242,202,134,0.46) 0%,
    rgba(228,180,108,0.24) 40%,
    rgba(220,170,98,0.075) 70%,
    rgba(220,170,98,0)    93%);
}
@keyframes hc-halo-size-hover {
  0%, 100% { width: 156px; height: 156px; }
  50%      { width: 170px; height: 170px; }
}

/* 移动端（触控）：隐藏自定义光标层 */
@media (hover: none) and (pointer: coarse) {
  .hc-layer { display: none !important; }
}
`
  document.head.appendChild(style)
}

function removeStyleIfNoConsumers() {
  // 没有其他组件挂载 amber-cursor 时移除样式
  // 简单实现：用全局计数器
  // 这里我们采用更保守的策略——样式只在 first-mount 时注入，
  // 不在 unmount 时移除（因为页面切换可能瞬时无消费者但马上又有）
  // 真正的清理留给了 onBeforeUnmount 移除 html.hc-on
}

export function useAmberCursor() {
  const cursorDot  = ref<HTMLElement | null>(null)
  const cursorHalo = ref<HTMLElement | null>(null)

  // 全局坐标
  let tx = 0, ty = 0
  // lerp 累积坐标
  const pDot  = { x: 0, y: 0 }
  const pHalo = { x: 0, y: 0 }

  let rafId = 0
  let hovered = false

  const INTERACTIVE_SEL =
    'a, button, input, textarea, select, label, summary, ' +
    '[role="button"], [tabindex], ' +
    '.c-cta, .c-brand, .amber-cta, .amber-card, .amber-pill, .amber-tab, ' +
    '.amber-input, .amber-toggle, .amber-step'

  function isInteractive(el: EventTarget | null): boolean {
    if (!el || !(el instanceof Element)) return false
    return el.matches(INTERACTIVE_SEL) || !!el.closest(INTERACTIVE_SEL)
  }

  function tick() {
    rafId = 0
    if (cursorDot.value) {
      pDot.x += (tx - pDot.x) * 0.26
      pDot.y += (ty - pDot.y) * 0.26
      cursorDot.value.style.transform = `translate3d(${pDot.x}px,${pDot.y}px,0) translate(-50%,-50%)`
    }
    if (cursorHalo.value) {
      pHalo.x += (tx - pHalo.x) * 0.16
      pHalo.y += (ty - pHalo.y) * 0.16
      cursorHalo.value.style.transform = `translate3d(${pHalo.x}px,${pHalo.y}px,0) translate(-50%,-50%)`
    }
    rafId = requestAnimationFrame(tick)
  }

  function setHover(on: boolean) {
    if (hovered === on) return
    hovered = on
    cursorDot.value?.classList.toggle('is-hover', on)
    cursorHalo.value?.classList.toggle('is-hover', on)
  }

  function onMove(e: PointerEvent) {
    tx = e.clientX
    ty = e.clientY
    if (pDot.x === 0 && pDot.y === 0) {
      pDot.x = pHalo.x = tx
      pDot.y = pHalo.y = ty
    }
    setHover(isInteractive(e.target))
  }

  function onDown(_e: PointerEvent) {
    if (!cursorDot.value || !cursorHalo.value) return
    cursorDot.value.animate(
      [
        { width: hovered ? '8px' : '6px', height: hovered ? '8px' : '6px' },
        { width: '16px', height: '16px', offset: 0.45 },
        { width: hovered ? '8px' : '6px', height: hovered ? '8px' : '6px' }
      ],
      { duration: 280, easing: 'cubic-bezier(0.22,1,0.36,1)' }
    )
    cursorHalo.value.animate(
      [
        { opacity: 0.95, filter: 'blur(10px)' },
        { opacity: 1, filter: 'blur(12px)', offset: 0.5 },
        { opacity: 0.95, filter: 'blur(10px)' }
      ],
      { duration: 360, easing: 'cubic-bezier(0.22,1,0.36,1)' }
    )
  }

  onMounted(() => {
    ensureStyleInjected()
    document.documentElement.classList.add('hc-on')
    window.addEventListener('pointermove', onMove, { passive: true })
    window.addEventListener('pointerdown', onDown)
    rafId = requestAnimationFrame(tick)
  })

  onBeforeUnmount(() => {
    document.documentElement.classList.remove('hc-on')
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerdown', onDown)
    if (rafId) { cancelAnimationFrame(rafId); rafId = 0 }
  })

  return { cursorDot, cursorHalo }
}
