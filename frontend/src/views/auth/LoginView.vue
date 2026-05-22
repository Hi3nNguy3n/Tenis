<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { User, Lock, View, Hide, Warning } from '@element-plus/icons-vue'
import { t } from '../../utils/locale'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const LOGIN_ENDPOINT = `${API_BASE_URL}/api/auth/login`

const router = useRouter()
const authStore = useAuthStore()

const isLoggingIn = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const showPassword = ref(false)

const form = ref({
  email: '',
  password: '',
})

const clearMessages = () => {
  errorMessage.value = ''
  successMessage.value = ''
}

const handleApiError = async (response, fallbackMessage) => {
  try {
    const data = await response.json()
    return data.detail || data.message || fallbackMessage
  } catch {
    return fallbackMessage
  }
}

onMounted(() => {
  if (authStore.isAuthenticated && authStore.isAdmin) {
    router.push('/admin')
  }
})

const login = async () => {
  clearMessages()

  if (!form.value.email.trim()) {
    errorMessage.value = t('auth.loginErrorEmail')
    return
  }

  if (!form.value.password) {
    errorMessage.value = t('auth.loginErrorPassword')
    return
  }

  isLoggingIn.value = true

  try {
    const response = await fetch(LOGIN_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: form.value.email.trim(),
        password: form.value.password,
      }),
    })

    if (!response.ok) {
      errorMessage.value = await handleApiError(
        response,
        t('auth.loginErrorGeneric')
      )
      return
    }

    const data = await response.json()

    authStore.setSession({
      accessToken: data.access_token,
      tokenType: data.token_type,
      user: {
        email: form.value.email.trim(),
        full_name: data.full_name || form.value.email.trim().split('@')[0],
        user_id: data.user_id,
        role_id: data.role_id,
        account_type: data.account_type,
      },
    })

    successMessage.value = t('auth.loginSuccessWelcome')

    if (data.account_type === 'admin') {
      router.push('/admin')
    } else {
      router.push({ name: 'home' }).catch(() => {
        router.push('/')
      })
    }
  } catch {
    errorMessage.value = t('auth.loginErrorConnection')
  } finally {
    isLoggingIn.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="brand-panel" aria-labelledby="login-page-heading">
        <div class="brand-media"></div>
        <div class="brand-shade"></div>

        <div class="brand-content">
          <RouterLink to="/" class="brand-logo-link" aria-label="Saigontennistours">
            <img
              class="brand-logo"
              src="https://res.cloudinary.com/dfs9o3bny/image/upload/v1776309753/z7730353029258_1dbe77285e553a1aa2ae1ab543a985c8-removebg-preview_nj3utv.png"
              alt="Saigontennistours"
            />
          </RouterLink>

          <div class="brand-copy">
            <p class="brand-kicker">{{ $t('auth.brandKicker') }}</p>
            <h1 id="login-page-heading">Saigontennistours</h1>
            <p class="brand-description">
              {{ $t('auth.brandDesc') }}
            </p>
          </div>

          <blockquote class="brand-quote">
            {{ $t('auth.brandQuote') }}
          </blockquote>
        </div>
      </section>

      <section class="form-panel">
        <div class="form-panel-inner">
          <RouterLink to="/" class="mobile-brand" aria-label="Saigontennistours">
            <img
              src="https://res.cloudinary.com/dfs9o3bny/image/upload/v1776309753/z7730353029258_1dbe77285e553a1aa2ae1ab543a985c8-removebg-preview_nj3utv.png"
              alt=""
            />
            <span>Saigontennistours</span>
          </RouterLink>

          <header class="form-header">
            <p class="form-kicker">{{ $t('auth.loginHeaderKicker') }}</p>
            <h2>{{ $t('auth.loginHeaderTitle') }}</h2>
            <p>
              {{ $t('auth.loginHeaderSubtitle') }}
            </p>
          </header>

          <div v-if="errorMessage" class="feedback feedback-error" role="alert">
            {{ errorMessage }}
          </div>

          <div v-if="successMessage" class="feedback feedback-success" role="status">
            {{ successMessage }}
          </div>

          <form class="auth-form" @submit.prevent="login">
            <label class="field-group" for="login-email">
              <span>{{ $t('auth.email') }}</span>
              <div class="field-control with-icon">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    d="M4 6.75h16A1.25 1.25 0 0 1 21.25 8v8A1.25 1.25 0 0 1 20 17.25H4A1.25 1.25 0 0 1 2.75 16V8A1.25 1.25 0 0 1 4 6.75Zm0 1.5a.25.25 0 0 0-.25.25v.18l8.25 5.77 8.25-5.77V8.5a.25.25 0 0 0-.25-.25H4Zm16.25 2.26-7.53 5.27a1.25 1.25 0 0 1-1.44 0l-7.53-5.27V16c0 .14.11.25.25.25h16c.14 0 .25-.11.25-.25v-5.49Z"
                  />
                </svg>
                <input
                  id="login-email"
                  v-model="form.email"
                  type="email"
                  placeholder="name@example.com"
                  autocomplete="email"
                  required
                />
              </div>
            </label>

            <label class="field-group" for="login-password">
              <div class="field-label-row">
                <span>{{ $t('auth.password') }}</span>
                <RouterLink id="forgot-password-link" to="/forgot-password">{{ $t('auth.forgotPassword') }}</RouterLink>
              </div>
              <div class="field-control with-icon with-action">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    d="M12 1.75A4.75 4.75 0 0 0 7.25 6.5v2H6A2.25 2.25 0 0 0 3.75 10.75v8.5A2.25 2.25 0 0 0 6 21.5h12a2.25 2.25 0 0 0 2.25-2.25v-8.5A2.25 2.25 0 0 0 18 8.5h-1.25v-2A4.75 4.75 0 0 0 12 1.75Zm3.25 6.75h-6.5v-2a3.25 3.25 0 0 1 6.5 0v2Zm-3.25 3a1.75 1.75 0 0 1 .75 3.33v1.42a.75.75 0 0 1-1.5 0v-1.42A1.75 1.75 0 0 1 12 11.5Z"
                  />
                </svg>
                <input
                  id="login-password"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="••••••••"
                  autocomplete="current-password"
                  required
                />
                <button
                  id="toggle-login-password"
                  class="field-action"
                  type="button"
                  @click="showPassword = !showPassword"
                >
                  {{ showPassword ? $t('auth.hide') : $t('auth.show') }}
                </button>
              </div>
            </label>

            <button id="login-submit-button" class="submit-button" type="submit" :disabled="isLoggingIn">
              <span v-if="isLoggingIn" class="button-spinner" aria-hidden="true"></span>
              <span>{{ isLoggingIn ? $t('auth.loggingIn') : $t('auth.login') }}</span>
              <span v-if="!isLoggingIn" class="submit-arrow" aria-hidden="true">&rarr;</span>
            </button>
          </form>

          <footer class="form-footer">
            <p>
              {{ $t('auth.noAccount') }}
              <RouterLink id="go-register-link" to="/register-otp">{{ $t('auth.registerNow') }}</RouterLink>
            </p>
          </footer>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  padding: 32px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #eef7f0 48%, #f4f8f4 100%);
  color: #0f172a;
  font-family: 'Inter', 'Segoe UI', sans-serif;
}

.login-shell {
  width: min(100%, 1160px);
  min-height: calc(100vh - 64px);
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(420px, 0.95fr);
  border: 1px solid rgba(21, 128, 61, 0.14);
  border-radius: 8px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.12);
}

.brand-panel {
  position: relative;
  display: flex;
  align-items: flex-end;
  min-height: 100%;
  padding: 48px;
  overflow: hidden;
  background: #14532d;
  color: #ffffff;
  isolation: isolate;
}

.brand-media,
.brand-shade {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.brand-media {
  z-index: -3;
  background:
    linear-gradient(90deg, rgba(10, 60, 35, 0.88) 0%, rgba(10, 60, 35, 0.62) 54%, rgba(10, 60, 35, 0.26) 100%),
    url('/src/assets/hero_bg.png') center/cover;
}

.brand-shade {
  z-index: -2;
  background:
    linear-gradient(180deg, rgba(20, 83, 45, 0.05), rgba(5, 46, 22, 0.72)),
    linear-gradient(135deg, rgba(193, 255, 114, 0.2), transparent 34%);
}

.brand-content {
  width: 100%;
  max-width: 520px;
  display: flex;
  flex-direction: column;
  gap: 34px;
}

.brand-logo-link {
  width: 86px;
  height: 86px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.56);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
}

.brand-logo {
  width: 70px;
  height: 70px;
  object-fit: contain;
}

.brand-copy {
  display: grid;
  gap: 14px;
}

.brand-kicker {
  margin: 0;
  color: #c1ff72;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.brand-panel h1 {
  margin: 0;
  font-size: clamp(2.65rem, 6vw, 5.2rem);
  line-height: 0.94;
  letter-spacing: 0;
  text-transform: uppercase;
}

.brand-description {
  max-width: 500px;
  margin: 0;
  color: rgba(255, 255, 255, 0.86);
  font-size: 1.05rem;
  line-height: 1.75;
}

.brand-quote {
  margin: 0;
  padding: 22px 24px;
  border-left: 4px solid #c1ff72;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16);
  color: #ffffff;
  line-height: 1.7;
  backdrop-filter: blur(12px);
}

.form-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
}

.form-panel-inner {
  width: min(430px, 100%);
  padding: 52px 48px;
}

.mobile-brand {
  display: none;
  align-items: center;
  gap: 10px;
  width: max-content;
  margin-bottom: 22px;
  color: #14532d;
  font-weight: 900;
  letter-spacing: 0.04em;
  text-decoration: none;
  text-transform: uppercase;
}

.mobile-brand img {
  width: 38px;
  height: 38px;
  object-fit: contain;
}

.form-header {
  margin-bottom: 28px;
}

.form-kicker {
  margin: 0 0 10px;
  color: #15803d;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.form-header h2 {
  margin: 0;
  color: #0f172a;
  font-size: clamp(2rem, 4vw, 2.65rem);
  line-height: 1.08;
  letter-spacing: 0;
}

.form-header p:not(.form-kicker) {
  margin: 14px 0 0;
  color: #64748b;
  line-height: 1.7;
}

.feedback {
  margin-bottom: 16px;
  padding: 14px 16px;
  border: 1px solid transparent;
  border-radius: 8px;
  font-size: 0.95rem;
  line-height: 1.55;
}

.feedback-error {
  background: #fef2f2;
  border-color: #fecaca;
  color: #991b1b;
}

.feedback-success {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #166534;
}

.auth-form {
  display: grid;
  gap: 18px;
}

.field-group {
  display: grid;
  gap: 8px;
}

.field-group > span,
.field-label-row span {
  color: #334155;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.field-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.field-label-row a,
.form-footer a {
  color: #15803d;
  font-weight: 800;
  text-decoration: none;
}

.field-control {
  position: relative;
  display: flex;
  align-items: center;
  border: 1px solid #dce7df;
  border-radius: 8px;
  background: #f8fafc;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.field-control:focus-within {
  border-color: #22c55e;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.13);
}

.field-control svg {
  width: 20px;
  height: 20px;
  fill: #64748b;
  flex-shrink: 0;
}

.with-icon svg {
  position: absolute;
  left: 16px;
}

.field-control input {
  width: 100%;
  min-height: 58px;
  border: 0;
  outline: 0;
  background: transparent;
  padding: 0 18px;
  color: #0f172a;
  font: inherit;
}

.with-icon input {
  padding-left: 48px;
}

.with-action input {
  padding-right: 76px;
}

.field-control input::placeholder {
  color: #94a3b8;
}

.field-action {
  position: absolute;
  right: 14px;
  border: 0;
  background: transparent;
  color: #15803d;
  cursor: pointer;
  font: inherit;
  font-size: 0.88rem;
  font-weight: 800;
}

.submit-button {
  min-height: 60px;
  margin-top: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border: 0;
  border-radius: 8px;
  background: linear-gradient(135deg, #15803d, #16a34a);
  color: #ffffff;
  box-shadow: 0 16px 34px rgba(21, 128, 61, 0.24);
  cursor: pointer;
  font: inherit;
  font-size: 1rem;
  font-weight: 900;
  transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 22px 42px rgba(21, 128, 61, 0.3);
}

.submit-button:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.submit-arrow {
  font-size: 1.1rem;
  transition: transform 0.2s ease;
}

.submit-button:hover:not(:disabled) .submit-arrow {
  transform: translateX(4px);
}

.button-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.42);
  border-top-color: #ffffff;
  border-radius: 999px;
  animation: spin 0.8s linear infinite;
}

.form-footer {
  margin-top: 24px;
  color: #64748b;
  text-align: center;
  font-weight: 600;
}

.form-footer p {
  margin: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 980px) {
  .login-shell {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    min-height: 420px;
  }
}

@media (max-width: 768px) {
  .login-page {
    padding: 12px;
  }

  .login-shell {
    min-height: calc(100vh - 24px);
  }

  .brand-panel {
    display: none;
  }

  .form-panel {
    align-items: stretch;
  }

  .form-panel-inner {
    width: 100%;
    padding: 36px 24px;
  }

  .mobile-brand {
    display: inline-flex;
  }
}

@media (max-width: 520px) {
  .form-panel-inner {
    padding: 32px 20px;
  }

  .field-label-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }
}
</style>
