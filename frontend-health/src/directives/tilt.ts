import type { Directive, DirectiveBinding } from 'vue'

interface TiltElement extends HTMLElement {
  __tiltMove?: (e: PointerEvent) => void
  __tiltLeave?: () => void
}

interface TiltOptions {
  max?: number          // 最大倾斜角度（度）
  scale?: number        // 悬停时缩放
  speed?: number        // 过渡时长（ms）
  glare?: boolean       // 是否启用光泽效果
  glareColor?: string
  reset?: boolean
}

const defaults: Required<TiltOptions> = {
  max: 8,
  scale: 1.02,
  speed: 300,
  glare: true,
  glareColor: 'rgba(255, 255, 255, 0.25)',
  reset: true
}

function mergeOptions(binding: DirectiveBinding<TiltOptions | undefined>): Required<TiltOptions> {
  return { ...defaults, ...(binding.value || {}) }
}

const tilt: Directive<TiltElement, TiltOptions | undefined> = {
  mounted(el, binding) {
    const opts = mergeOptions(binding)

    // Ensure transform context
    const computed = window.getComputedStyle(el)
    if (computed.transformStyle !== 'preserve-3d') {
      el.style.transformStyle = 'preserve-3d'
    }
    el.style.willChange = 'transform'
    el.style.transition = `transform ${opts.speed}ms ease-out`

    // Glare layer
    let glareEl: HTMLDivElement | null = null
    if (opts.glare) {
      glareEl = document.createElement('div')
      glareEl.style.cssText = `
        position: absolute;
        inset: 0;
        border-radius: inherit;
        pointer-events: none;
        background: linear-gradient(135deg, ${opts.glareColor} 0%, transparent 60%);
        opacity: 0;
        transition: opacity ${opts.speed}ms ease-out;
        mix-blend-mode: overlay;
        z-index: 1;
      `
      const pos = window.getComputedStyle(el).position
      if (pos === 'static') el.style.position = 'relative'
      el.style.overflow = 'hidden'
      el.appendChild(glareEl)
    }

    const move = (e: PointerEvent) => {
      const rect = el.getBoundingClientRect()
      const px = (e.clientX - rect.left) / rect.width   // 0..1
      const py = (e.clientY - rect.top) / rect.height    // 0..1
      const rotateY = (px - 0.5) * 2 * opts.max
      const rotateX = -(py - 0.5) * 2 * opts.max
      el.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${opts.scale})`
      el.style.setProperty('--rotate-x', `${rotateX}deg`)
      el.style.setProperty('--rotate-y', `${rotateY}deg`)
      if (glareEl) {
        glareEl.style.opacity = '1'
        glareEl.style.background = `radial-gradient(circle at ${px * 100}% ${py * 100}%, ${opts.glareColor} 0%, transparent 60%)`
      }
    }

    const leave = () => {
      if (opts.reset) {
        el.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg) scale(1)'
      }
      if (glareEl) glareEl.style.opacity = '0'
    }

    el.__tiltMove = move
    el.__tiltLeave = leave
    el.addEventListener('pointermove', move)
    el.addEventListener('pointerleave', leave)
  },
  unmounted(el) {
    if (el.__tiltMove) el.removeEventListener('pointermove', el.__tiltMove)
    if (el.__tiltLeave) el.removeEventListener('pointerleave', el.__tiltLeave)
  }
}

export default tilt
