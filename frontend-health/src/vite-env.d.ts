/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// vue-cropper 1.x 未内置类型声明，补充最小类型
declare module 'vue-cropper' {
  import type { DefineComponent } from 'vue'
  export const VueCropper: DefineComponent<any, any, any>
  const _default: DefineComponent<any, any, any>
  export default _default
}
