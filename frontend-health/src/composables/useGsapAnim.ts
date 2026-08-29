import { onBeforeUnmount } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

/**
 * GSAP 动画工具（方案 B：赭金壳 + 浅色舞台）
 * 封装侧栏展开、菜单 stagger、顶栏入场、数字 counter、ScrollTrigger 滚动揭示。
 * 所有动画通过 gsap.context 纳管，组件卸载时统一 revert，避免内存泄漏。
 */
export function useGsapAnim() {
  const contexts: gsap.Context[] = []

  function track(fn: () => void, scope?: Element | string) {
    const ctx = gsap.context(fn as any, scope as any)
    contexts.push(ctx as gsap.Context)
    return ctx as gsap.Context
  }

  /** 侧栏展开 / 折叠（替代 CSS width transition，交给 GSAP timeline） */
  function sidebarToggle(root: HTMLElement, expanded: boolean) {
    const labels = root.querySelectorAll<HTMLElement>('.menu-label-wrap')
    if (expanded) {
      const tl = gsap.timeline()
      tl.to(root, { width: 220, duration: 0.45, ease: 'power3.out' }, 0)
        .to(labels, {
          maxWidth: 160, opacity: 1, marginLeft: 10,
          duration: 0.4, ease: 'power3.out', stagger: 0.025
        }, 0.05)
    } else {
      const tl = gsap.timeline()
      tl.to(labels, {
        maxWidth: 0, opacity: 0, marginLeft: 0,
        duration: 0.3, ease: 'power3.in'
      }, 0)
        .to(root, { width: 60, duration: 0.45, ease: 'power3.out' }, 0.05)
    }
  }

  /** 菜单项 stagger 浮入（从左侧滑入） */
  function menuEnter(items: Element[] | NodeListOf<Element>) {
    gsap.from(items, {
      x: -14, opacity: 0, duration: 0.55, stagger: 0.05,
      ease: 'back.out(1.4)'
    })
  }

  /** 顶栏元素 stagger 下落 */
  function topbarEnter(items: Element[] | NodeListOf<Element>) {
    gsap.from(items, {
      y: -12, opacity: 0, duration: 0.5, stagger: 0.08,
      ease: 'power3.out'
    })
  }

  /** 数字 counter 滚动（用于健康指标卡片） */
  function counter(el: Element | HTMLElement, to: number, duration = 1.5) {
    const obj = { v: 0 }
    return gsap.to(obj, {
      v: to, duration, ease: 'power2.out',
      onUpdate: () => {
        if (el.textContent !== null) {
          el.textContent = Math.round(obj.v).toLocaleString()
        }
      }
    })
  }

  /**
   * ScrollTrigger 滚动揭示（用于子页面卡片）
   * 在指定作用域内，对匹配 selector 的元素做"进入视口时上浮淡入"。
   * 调用时机：子页面 onMounted（DOM 渲染完成后）。
   */
  function reveal(
    scope: HTMLElement | string,
    selector: string,
    opts?: gsap.TweenVars & { start?: string }
  ) {
    const start = opts?.start || 'top 85%'
    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>(selector).forEach((el) => {
        gsap.from(el, {
          y: 36, opacity: 0, duration: 0.75, ease: 'power2.out',
          scrollTrigger: {
            trigger: el, start,
            toggleActions: 'play none none none'
          },
          ...(opts || {})
        } as gsap.TweenVars)
      })
    }, scope as any)
    contexts.push(ctx)
    return ctx
  }

  onBeforeUnmount(() => {
    contexts.forEach(c => c.revert())
  })

  return { sidebarToggle, menuEnter, topbarEnter, counter, reveal, track, gsap, ScrollTrigger }
}
