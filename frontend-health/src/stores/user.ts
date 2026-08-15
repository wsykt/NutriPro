import { defineStore } from 'pinia'
import {
  getToken, setToken, clearSession,
  getCurrentUserId, setCurrentUserId,
  getActAsUserId, setActAsUserId,
} from '@/utils/storage'

export interface User {
  username: string
  avatar?: string
  token: string
  role?: string
  crowd_type?: string
  crowdType?: string
  user_id?: number
  userId?: number
  id?: number
  height?: number
  weight?: number
  age?: number
  gender?: string
  [key: string]: any
}

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null as User | null,
    // 我监护的亲属列表（用于操作身份切换）
    wards: [] as Array<{ wardId: number; wardUsername: string; status?: string }>,
    // 当前替谁操作：null 表示操作自己；否则是被监护人 userId
    actAsUserId: getActAsUserId()
  }),
  actions: {
    async login(username: string, password: string) {
      const { api } = await import('../api')
      try {
        const response: any = await api.auth.login({ username, password })
        if (response?.access_token || response?.token) {
          const token = response.access_token || response.token
          const uid = response.user_id || response.userId
          const user: User = {
            username: response.username || username,
            token,
            avatar: response.avatar || '',
            role: response.role || 'user',
            crowd_type: response.crowd_type || response.crowdType || '普通人',
            user_id: uid,
            height: response.height,
            weight: response.weight,
            age: response.age,
            gender: response.gender
          }
          this.user = user
          setToken(token) // 单一事实源，不再双写 user_token + token
          if (uid != null) setCurrentUserId(uid)
          this.setActAs(null)
          try { await this.loadWards() } catch {}
          return { success: true }
        }
        return { success: false, message: (response as any)?.message || '登录失败，请稍后重试' }
      } catch (e: any) {
        const message = e?.response?.data?.message || e?.response?.data?.error || e?.message || '登录失败，请稍后重试'
        return { success: false, message }
      }
    },
    async register(data: any) {
      const { api } = await import('../api')
      try {
        const response: any = await api.auth.register(data)
        if (response?.user_id || response?.access_token) {
          return { success: true }
        }
        return { success: false, message: (response as any)?.message || '注册失败，请稍后重试' }
      } catch (e: any) {
        const message = e?.response?.data?.message || e?.response?.data?.error || e?.message || '注册失败，请稍后重试'
        return { success: false, message }
      }
    },
    async init() {
      if (this.user?.token) return
      const token = getToken()
      if (!token) return
      try {
        const { api } = await import('../api')
        // init 阶段只查自己的资料，不做亲属切换
        const backup = getActAsUserId()
        setActAsUserId(null)
        const info: any = await api.profile.getInfo()
        if (info) {
          const uid = info.id || info.user_id || info.userId || info.user?.id
          this.user = {
            username: info.username || info.user?.username || '',
            avatar: info.avatar || info.user?.avatar || '',
            token,
            role: info.role || info.user?.role || 'user',
            crowd_type: info.crowd_type || info.crowdType || info.user?.crowd_type || '普通人',
            user_id: uid,
            height: info.height || info.user?.height,
            weight: info.weight || info.user?.weight,
            age: info.age || info.user?.age,
            gender: info.gender || info.user?.gender
          }
          if (uid != null) setCurrentUserId(uid)
          // init 完成后，恢复之前的 actAsUserId（如监护人希望直接打开替亲属操作的页面）
          if (backup != null) {
            this.actAsUserId = backup
            setActAsUserId(backup)
          }
          try { await this.loadWards() } catch {}
        }
      } catch {
        // 开发模式：后端未启动时，使用默认模拟用户，避免页面空白
        if (token === 'dev-mock-token' || localStorage.getItem('dev_mode') === 'true') {
          this.user = {
            username: '开发者',
            avatar: '',
            token,
            role: 'user',
            crowd_type: '普通人',
            user_id: 1,
            height: 170,
            weight: 65,
            age: 30,
            gender: '男'
          }
          setCurrentUserId(1)
        } else {
          this.user = null
          clearSession()
        }
      }
    },
    logout() {
      this.user = null
      this.wards = []
      this.actAsUserId = null
      clearSession()
    },
    // 载入我监护的亲属列表
    async loadWards() {
      const { api } = await import('../api')
      const list: any = await api.relation.myWards()
      const arr: Array<{ wardId: number; wardUsername: string; status?: string }> =
        (Array.isArray(list) ? list : []).map((r: any) => ({
          wardId: r.wardId ?? r.ward_id,
          wardUsername: r.wardUsername ?? r.ward_username
        }))
      this.wards = arr
    },
    async loadUserProfile() {
      const { api } = await import('../api')
      try {
        const info: any = await api.profile.getInfo()
        if (info) {
          this.user = {
            username: info.username || this.user?.username || '',
            avatar: info.avatar || info.user?.avatar || '',
            token: this.user?.token || '',
            role: info.role || 'user',
            crowd_type: info.crowdType || info.crowd_type || '普通人',
            user_id: info.userId || info.user_id || info.id || this.user?.user_id,
            height: info.height,
            weight: info.weight,
            age: info.age,
            gender: info.gender
          }
        }
      } catch (e) {
        console.warn('刷新资料失败', e)
      }
    },
    // 切换当前操作身份：传 null 代表操作自己
    setActAs(userId: number | null) {
      this.actAsUserId = userId
      setActAsUserId(userId)
    }
  },
  getters: {
    isLogin: (state) => !!state.user,
    isLoggedIn: (state) => !!state.user,
    isAdmin: (state) => !!state.user && state.user.role === 'admin',
    avatar: (state): string => state.user?.avatar || '',
    // 当前操作对象的 userId
    activeUserId: (state): number | null => {
      if (!state.user) return null
      if (state.actAsUserId != null) return state.actAsUserId
      const id = state.user.user_id || state.user.userId || state.user.id
      return typeof id === 'number' ? id : id != null ? parseInt(String(id), 10) : null
    },
    // 当前操作对象的显示名
    activeUserLabel: (state): string => {
      if (!state.user) return '未登录'
      if (state.actAsUserId != null) {
        const w = state.wards.find(x => x.wardId === state.actAsUserId)
        if (w) return `替 ${w.wardUsername} 操作`
        return `替 #${state.actAsUserId} 操作`
      }
      return state.user.username || '自己'
    }
  }
})
