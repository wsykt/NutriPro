import type { App } from 'vue'
import ripple from './ripple'
import tilt from './tilt'

export function registerDirectives(app: App) {
  app.directive('ripple', ripple)
  app.directive('tilt', tilt)
}

export { ripple, tilt }
