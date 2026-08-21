import type { Directive, DirectiveBinding } from 'vue'

interface RippleElement extends HTMLElement {
  __rippleCleanup?: () => void
}

interface RippleOptions {
  color?: string
  duration?: number
}

function createRipple(e: PointerEvent, el: RippleElement, binding: DirectiveBinding<RippleOptions | string | undefined>) {
  const opts: RippleOptions = typeof binding.value === 'object' ? binding.value : {}
  const color = opts.color || (typeof binding.value === 'string' ? binding.value : 'rgba(255, 255, 255, 0.5)')
  const duration = opts.duration || 600

  // Ensure positioning context
  const computed = window.getComputedStyle(el)
  if (computed.position === 'static') {
    el.style.position = 'relative'
  }
  if (computed.overflow !== 'hidden') {
    el.style.overflow = 'hidden'
  }

  const rect = el.getBoundingClientRect()
  const size = Math.max(rect.width, rect.height)
  const x = e.clientX - rect.left - size / 2
  const y = e.clientY - rect.top - size / 2

  const span = document.createElement('span')
  span.style.cssText = `
    position: absolute;
    border-radius: 50%;
    width: ${size}px;
    height: ${size}px;
    left: ${x}px;
    top: ${y}px;
    background: ${color};
    transform: scale(0);
    opacity: 0.6;
    pointer-events: none;
    transition: transform ${duration}ms cubic-bezier(0.4, 0, 0.2, 1), opacity ${duration}ms ease-out;
    z-index: 0;
  `
  el.appendChild(span)

  // Trigger animation
  requestAnimationFrame(() => {
    span.style.transform = 'scale(2.5)'
    span.style.opacity = '0'
  })

  const cleanup = () => {
    if (span.parentNode) {
      span.parentNode.removeChild(span)
    }
    el.removeEventListener('pointerup', cleanup)
    el.removeEventListener('pointerleave', cleanup)
  }

  el.addEventListener('pointerup', cleanup)
  el.addEventListener('pointerleave', cleanup)
  el.__rippleCleanup = cleanup
}

const ripple: Directive<RippleElement, RippleOptions | string | undefined> = {
  mounted(el, binding) {
    el.style.position = el.style.position === 'static' ? 'relative' : el.style.position
    el.style.overflow = 'hidden'
    el.addEventListener('pointerdown', (e: PointerEvent) => createRipple(e, el, binding))
  },
  unmounted(el) {
    if (el.__rippleCleanup) el.__rippleCleanup()
  }
}

export default ripple
