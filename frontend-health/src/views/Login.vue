<template>
  <div class="amber-auth min-h-screen relative">
    <!-- 顶部刊头 -->
    <header class="amber-top-nav">
      <router-link to="/" class="amber-brand">
        <span class="amber-brand-name amber-brand-name--video">
          <span class="amber-brand-video-mask">
            <span class="amber-brand-fallback" aria-hidden="true">NutriPro</span>
            <video class="amber-brand-video" autoplay muted loop playsinline preload="auto">
              <source src="https://videos.pexels.com/video-files/5866263/5866263-hd_1280_720_25fps.mp4" type="video/mp4" />
            </video>
          </span>
        </span>
      </router-link>
      <router-link to="/register" class="amber-nav-cta">
        立即注册 →
      </router-link>
    </header>

    <!-- 主体：双栏（左卷首语 · 右居中卡片） -->
    <main class="amber-stage">
      <div class="amber-grid">
        <!-- 左栏：小卷首语 -->
        <aside class="amber-aside">
          <p class="amber-pull">
            "一份属于你的身体日志。每日三餐、运动时长、睡眠节律——回到这里，继续书写。"
          </p>
          <p class="amber-aside-meta">
            每一次登录，都是一段未完待续的篇章。
          </p>
        </aside>

        <!-- 右栏：居中卡片 -->
        <div class="amber-card-wrap">
          <div class="amber-card">
            <p class="amber-card-eyebrow">Sign In · 01</p>
            <h1 class="amber-card-title">登录账号</h1>
            <p class="amber-card-sub">输入你的用户名与密码，回到你的健康档案。</p>

            <form @submit.prevent="handleLogin" class="amber-form" autocomplete="off">
              <!-- 诱饵字段：拦截浏览器自动填充，真实字段仍由用户手动输入 -->
              <div style="position:absolute;left:-9999px;top:-9999px;opacity:0;pointer-events:none" aria-hidden="true">
                <input type="text" name="username" tabindex="-1" autocomplete="username" />
                <input type="password" name="password" tabindex="-1" autocomplete="current-password" />
              </div>
              <div class="amber-field">
                <label class="amber-label">用户名</label>
                <input
                  v-model="username"
                  type="text"
                  required
                  class="amber-input"
                  placeholder="请输入用户名"
                  autocomplete="off"
                  spellcheck="false"
                />
              </div>

              <div class="amber-field">
                <div class="amber-label-row">
                  <label class="amber-label">密码</label>
                  <button
                    type="button"
                    @click="router.push('/forgot-password')"
                    class="amber-forgot"
                  >忘记密码？</button>
                </div>
                <input
                  v-model="password"
                  type="password"
                  required
                  @keydown.enter.prevent="handleLogin"
                  class="amber-input"
                  placeholder="请输入密码"
                  autocomplete="new-password"
                  spellcheck="false"
                  readonly
                  @focus="($event.target as HTMLInputElement).removeAttribute('readonly')"
                />
              </div>

              <button
                type="submit"
                :disabled="loading"
                class="amber-submit"
              >
                {{ loading ? '登录中...' : '登 录 →' }}
              </button>

              <p v-if="error" class="amber-error">{{ error }}</p>
            </form>

            <div class="amber-foot">
              还没有账号？
              <router-link to="/register" class="amber-foot-link">立即注册</router-link>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 自定义光标（useAmberCursor composable） -->
    <div class="hc-layer" aria-hidden="true">
      <div class="hc-halo" ref="cursorHalo"></div>
      <div class="hc-dot" ref="cursorDot"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useAmberCursor } from '../composables/useAmberCursor'

const router = useRouter()
const userStore = useUserStore()
const { cursorDot, cursorHalo } = useAmberCursor()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    const result: any = await userStore.login(username.value, password.value)
    if (result?.success) {
      if (userStore.isAdmin) {
        router.push('/admin')
      } else {
        // 首次登录引导：读 localStorage + 后端 first_login 字段（移植自 health1）
        await userStore.loadUserProfile?.()
        const userId = userStore.user?.user_id || userStore.user?.userId || userStore.user?.id
        const uname = userStore.user?.username

        let storedFirstLogin: string | null = null
        if (userId != null && uname) {
          const raw = localStorage.getItem(`first_login_${userId}`)
          if (raw) {
            try {
              const parsed = JSON.parse(raw)
              if (parsed && parsed.username === uname && parsed.value != null) {
                storedFirstLogin = String(parsed.value)
              }
            } catch {
              const byUser = localStorage.getItem(`first_login_user_${uname}`)
              if (byUser !== null) storedFirstLogin = byUser
            }
          }
        }
        if (storedFirstLogin === null && uname) {
          storedFirstLogin = localStorage.getItem(`first_login_user_${uname}`)
        }

        const backendFirstLogin = (userStore.user as any)?.first_login ?? (userStore.user as any)?.firstLogin

        if (storedFirstLogin === '0') {
          router.push('/dashboard')
        } else if (backendFirstLogin === 1 || storedFirstLogin === '1') {
          router.push('/onboarding')
        } else {
          userStore.setFirstLogin(0)
          router.push('/dashboard')
        }
      }
    } else {
      error.value = result?.message || '用户名或密码错误'
    }
  } catch (e: any) {
    error.value = e?.response?.data?.message || e?.message || '登录失败，请稍后再试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* =============== Direction C 赤金 Amber Editorial · 全局画布 =============== */
.amber-auth {
  background: #0E0C0A;
  color: #F6EAD6;
  font-family: "PingFang SC","Hiragino Sans GB","Microsoft YaHei","HarmonyOS Sans SC",system-ui,sans-serif;
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
}
/* 暖光扫纸面背景：琥珀柔光 + 深色基盘 + 86px 刊网纸纹 */
.amber-auth::before {
  content: ""; position: absolute; inset: 0;
  z-index: 0; pointer-events: none;
  background:
    radial-gradient(circle at 18% 22%, rgba(232,185,115,0.20) 0%, rgba(232,185,115,0.03) 40%, transparent 68%),
    radial-gradient(circle at 86% 78%, rgba(179,107,42,0.16) 0%, transparent 55%),
    linear-gradient(180deg, #14110C 0%, #0E0C0A 55%, #110E09 100%);
}
.amber-auth::after {
  content: ""; position: absolute; inset: 0;
  z-index: 0; pointer-events: none;
  background-image:
    repeating-linear-gradient(90deg, rgba(217,162,74,0.042) 0 1px, transparent 1px 86px),
    repeating-linear-gradient(0deg,  rgba(217,162,74,0.026) 0 1px, transparent 1px 86px);
  mix-blend-mode: overlay;
}

/* =============== 顶部刊头 =============== */
.amber-top-nav {
  position: relative; z-index: 3;
  max-width: 1240px; margin: 0 auto;
  padding: 24px 32px 18px;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px dashed rgba(217,162,74,0.28);
}
.amber-brand {
  display: flex; align-items: center; gap: 12px;
  color: #F6EAD6; font-weight: 800; font-size: 14px;
  letter-spacing: 0.04em;
  text-decoration: none;
}
.amber-brand-name--video {
  display: inline-flex; align-items: center; height: 28px;
  position: relative;
}
.amber-brand-video-mask {
  display: block; width: 130px; height: 100%;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='130' height='28' viewBox='0 0 130 28'%3E%3Ctext x='0' y='23' font-size='23' font-weight='900' font-family='serif' fill='black'%3ENutriPro%3C/text%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='130' height='28' viewBox='0 0 130 28'%3E%3Ctext x='0' y='23' font-size='23' font-weight='900' font-family='serif' fill='black'%3ENutriPro%3C/text%3E%3C/svg%3E");
  -webkit-mask-size: 100% 100%; mask-size: 100% 100%;
  -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
  -webkit-mask-position: center; mask-position: center;
  position: relative;
}
.amber-brand-fallback {
  position: absolute; inset: 0;
  display: flex; align-items: center;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-weight: 900; font-size: 21px;
  color: #F6EAD6;
  white-space: nowrap;
}
.amber-brand-video {
  width: 100%; height: 100%;
  object-fit: cover; display: block; pointer-events: none;
}
.amber-brand-sub { color: #B9A78A; font-weight: 500; font-size: 12px; letter-spacing: 0.18em; }
.amber-nav-cta {
  font-size: 11.5px; font-weight: 700; letter-spacing: 0.18em;
  color: #F1CF92; padding: 6px 12px;
  border: 1px solid rgba(217,162,74,0.4); border-radius: 999px;
  text-transform: uppercase; text-decoration: none;
  transition: background 0.3s ease, color 0.3s ease;
}
.amber-nav-cta:hover { background: rgba(217,162,74,0.1); color: #F6EAD6; }

/* =============== 主体舞台 =============== */
.amber-stage {
  position: relative; z-index: 2;
  max-width: 1240px; margin: 0 auto;
  padding: 120px 32px 96px;
}
.amber-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 64px;
  align-items: center;
}

/* —— 左栏：小卷首语 —— */
.amber-aside {
  max-width: 460px;
  justify-self: end;
  padding-right: 28px;
  border-right: 1px dashed rgba(217,162,74,0.22);
}
.amber-eyebrow {
  display: flex; align-items: center; gap: 12px;
  font-size: 11px; letter-spacing: 0.28em; color: #D9A24A;
  text-transform: uppercase; font-weight: 700;
  margin: 0 0 10px;
}
.amber-eyebrow-bar {
  width: 28px; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(217,162,74,0.85), transparent);
}
.amber-issue {
  font-size: 10.5px; letter-spacing: 0.22em; color: #8C7A5E;
  text-transform: uppercase; font-weight: 600;
  margin: 0 0 22px;
}
.amber-pull {
  font-family: "Songti SC","Noto Serif SC","Times New Roman",serif;
  font-style: italic; font-weight: 700;
  font-size: 19px; line-height: 1.7;
  color: #F1CF92;
  margin: 0 0 20px;
  letter-spacing: 0.01em;
}
.amber-aside-meta {
  font-size: 12px; line-height: 1.7;
  color: #B9A78A;
  margin: 0;
  letter-spacing: 0.04em;
}

/* =============== 右栏：居中卡片 =============== */
.amber-card-wrap { width: 100%; display: flex; justify-content: flex-start; }
.amber-card {
  position: relative;
  width: 100%; max-width: 380px;
  padding: 32px 30px 26px;
  border: 1px solid rgba(217,162,74,0.28);
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(28,22,16,0.7), rgba(20,16,11,0.6));
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow:
    0 40px 80px -28px rgba(0,0,0,0.85),
    0 12px 40px -6px rgba(217,162,74,0.18),
    inset 0 0 0 1px rgba(232,185,115,0.08);
  text-align: center;
}
/* AT 风格渐变描边光 ::before mask-composite */
.amber-card::before {
  content: ""; position: absolute; inset: -1px;
  border-radius: 17px;
  background: linear-gradient(135deg, rgba(232,185,115,0.35), transparent 50%, rgba(179,107,42,0.2));
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
          mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
          mask-composite: exclude;
  padding: 1px; pointer-events: none;
}

.amber-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 56px; height: 56px; border-radius: 14px;
  background: linear-gradient(135deg,#E8B973 0%, #D9A24A 60%, #B36B2A 100%);
  color: #1F170E; font-weight: 900; font-size: 22px;
  box-shadow: 0 12px 30px rgba(217,162,74,0.3), inset 0 1px 0 rgba(255,255,255,0.3);
  margin-bottom: 14px;
}
.amber-card-eyebrow {
  font-size: 11px; letter-spacing: 0.32em; color: #D9A24A;
  text-transform: uppercase; font-weight: 700; margin: 0 0 8px;
}
.amber-card-title {
  font-size: 28px; font-weight: 900; color: #F6EAD6;
  letter-spacing: -0.02em; margin: 0 0 6px;
}
.amber-card-sub {
  font-size: 12.5px; color: #B9A78A; margin: 0 0 24px;
}

/* =============== 表单 =============== */
.amber-form { text-align: left; }
.amber-field { margin-bottom: 16px; }
.amber-label {
  display: block; font-size: 10.5px; letter-spacing: 0.22em;
  color: #B9A78A; text-transform: uppercase;
  font-weight: 600; margin-bottom: 6px;
}
.amber-label-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 6px;
}
.amber-label-row .amber-label { margin: 0; }
.amber-forgot {
  background: none; border: 0; padding: 0;
  font-size: 11.5px; color: #B9A78A;
  cursor: none;
  font-family: inherit;
  transition: color 0.3s ease;
}
.amber-forgot:hover { color: #F1CF92; }
.amber-input {
  width: 100%; padding: 12px 14px;
  background: rgba(14,12,10,0.5);
  border: 1px solid rgba(246,234,214,0.12);
  border-radius: 8px;
  color: #F6EAD6;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.35s cubic-bezier(0.22,1,0.36,1),
              box-shadow 0.35s cubic-bezier(0.22,1,0.36,1),
              background 0.35s ease;
  outline: none;
}
.amber-input::placeholder { color: rgba(246,234,214,0.32); }
.amber-input:focus {
  border-color: rgba(232,185,115,0.65);
  background: rgba(20,17,12,0.7);
  box-shadow: 0 0 0 3px rgba(217,162,74,0.12), 0 0 24px rgba(217,162,74,0.18);
}

.amber-submit {
  width: 100%; padding: 13px 18px;
  border: 0; border-radius: 999px;
  background: linear-gradient(135deg,#E8B973 0%, #D9A24A 60%, #B36B2A 100%);
  color: #1F170E;
  font-weight: 800; font-size: 12.5px; letter-spacing: 0.22em;
  text-transform: uppercase;
  cursor: none;
  font-family: inherit;
  transition: transform 0.45s cubic-bezier(0.22,1,0.36,1),
              box-shadow 0.45s ease,
              opacity 0.3s ease;
  box-shadow: 0 10px 30px rgba(217,162,74,0.28), inset 0 1px 0 rgba(255,255,255,0.3);
  margin-top: 8px;
}
.amber-submit:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 40px rgba(217,162,74,0.4), inset 0 1px 0 rgba(255,255,255,0.4);
}
.amber-submit:disabled {
  opacity: 0.6; cursor: not-allowed; transform: none;
}

.amber-error {
  text-align: center;
  font-size: 12.5px;
  color: #E88060;
  margin: 12px 0 0;
}

.amber-foot {
  text-align: center; margin-top: 20px;
  font-size: 12px; color: #B9A78A;
}
.amber-foot-link {
  color: #F1CF92; text-decoration: none;
  margin-left: 4px; font-weight: 600;
  transition: color 0.3s ease;
}
.amber-foot-link:hover { text-decoration: underline; }

/* =============== 入场动画 =============== */
.amber-card {
  animation: amber-fade-up 0.7s cubic-bezier(0.22,1,0.36,1) both;
}
.amber-aside {
  animation: amber-fade-left 0.8s cubic-bezier(0.22,1,0.36,1) 0.1s both;
}
@keyframes amber-fade-up {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes amber-fade-left {
  from { opacity: 0; transform: translateX(-18px); }
  to   { opacity: 1; transform: translateX(0); }
}

/* =============== 响应式 =============== */
@media (max-width: 900px) {
  .amber-grid {
    grid-template-columns: 1fr;
    gap: 36px;
  }
  .amber-aside {
    justify-self: start;
    max-width: 100%;
    padding-right: 0;
    padding-bottom: 28px;
    border-right: 0;
    border-bottom: 1px dashed rgba(217,162,74,0.22);
  }
  .amber-pull { font-size: 17px; }
}
@media (max-width: 640px) {
  .amber-top-nav { padding: 18px 20px 14px; }
  .amber-stage { padding: 64px 20px 56px; }
  .amber-card { padding: 26px 22px 22px; }
  .amber-card-title { font-size: 24px; }
  .amber-pull { font-size: 16px; }
}
</style>
