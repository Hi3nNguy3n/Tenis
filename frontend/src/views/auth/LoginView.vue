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
      <section class="brand-panel">
        <div class="brand-content">
          <div>
            <p class="brand-kicker">{{ $t('auth.brandKicker') }}</p>
            <h1 id="login-page-heading">Saigon Tennis</h1>
            <p class="brand-description">
              {{ $t('auth.brandDesc') }}
            </p>
          </div>

          <blockquote class="brand-quote">
            {{ $t('auth.brandQuote') }}
          </blockquote>
        </div>

        <div class="brand-ring"></div>
        <div class="brand-ball"></div>
        <div class="brand-overlay"></div>
      </section>

      <section class="form-panel">
        <div class="form-panel-inner">
          <div class="mobile-brand">Saigon Tennis</div>

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
              <span>{{ isLoggingIn ? $t('auth.loggingIn') : $t('auth.login') }}</span>
              <span class="submit-arrow">→</span>
            </button>
          </form>

          <footer class="form-footer">
            <p>
              {{ $t('auth.noAccount') }}
              <RouterLink id="go-register-link" to="/register-otp">{{ $t('auth.registerNow') }}</RouterLink>
            </p>
            <p style="margin-top: 10px;">
              <RouterLink to="/forgot-password" style="font-size: 0.9rem; color: #6e7a74;">{{ $t('auth.forgotPassword') }}</RouterLink>
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
  padding: 24px;
  background:
    radial-gradient(circle at top right, rgba(120, 216, 186, 0.12), transparent 28%),
    radial-gradient(circle at bottom left, rgba(21, 128, 61, 0.12), transparent 26%),
    linear-gradient(180deg, #f8f9f9 0%, #eef1f1 100%);
  color: #191c1c;
}

.login-shell {
  width: min(100%, 1280px);
  min-height: calc(100vh - 48px);
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(420px, 0.8fr);
  border-radius: 8px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 24px 60px rgba(25, 28, 28, 0.08);
  position: relative;
}

.login-shell::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 40px,
    rgba(226, 232, 240, 0.08) 40px,
    rgba(226, 232, 240, 0.08) 41px
  );
  pointer-events: none;
}

.brand-panel {
  position: relative;
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  padding: 56px;
  overflow: hidden;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
  color: #ffffff;
}

.brand-content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 48px;
}

.brand-kicker {
  margin-bottom: 16px;
  font-size: 0.76rem;
  font-weight: 500;
  letter-spacing: 0.26em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.78);
}

.brand-panel h1 {
  font-size: clamp(3rem, 6vw, 5rem);
  line-height: 0.95;
  letter-spacing: -0.05em;
  margin-bottom: 16px;
}

.brand-description {
  max-width: 480px;
  font-size: 1.05rem;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.82);
}

.brand-quote {
  max-width: 520px;
  font-size: clamp(1.4rem, 2vw, 2rem);
  font-weight: 300;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.94);
}

.brand-ring {
  position: absolute;
  right: -100px;
  bottom: -100px;
  width: 380px;
  height: 380px;
  border-radius: 8px;
  border: 32px solid rgba(255, 255, 255, 0.08);
}

.brand-ball {
  position: absolute;
  right: 56px;
  top: 50%;
  transform: translateY(-50%);
  width: 260px;
  height: 260px;
  border-radius: 8px;
  background:
    radial-gradient(circle at 35% 35%, rgba(255, 255, 255, 0.36), transparent 26%),
    radial-gradient(circle at 50% 50%, rgba(148, 245, 214, 0.7), rgba(120, 216, 186, 0.18));
  opacity: 0.2;
  filter: blur(2px);
}

.brand-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0)),
    radial-gradient(circle at center, rgba(255, 255, 255, 0.16), transparent 54%);
  mix-blend-mode: screen;
}

.form-panel {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.96);
}

.form-panel-inner {
  width: 100%;
  max-width: 460px;
  margin: 0 auto;
  padding: 48px;
}

.mobile-brand {
  display: none;
  margin-bottom: 28px;
  font-size: 1.9rem;
  font-weight: 500;
  letter-spacing: -0.05em;
  color: var(--primary);
}

.form-header {
  margin-bottom: 28px;
}

.form-kicker {
  margin-bottom: 10px;
  font-size: 0.74rem;
  font-weight: 500;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #6e7a74;
}

.form-header h2 {
  margin-bottom: 10px;
  font-size: 2rem;
  line-height: 1.15;
  letter-spacing: -0.03em;
}

.form-header p {
  color: #4e6073;
  line-height: 1.7;
}

.feedback {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid transparent;
  font-size: 0.95rem;
}

.feedback-error {
  background: rgba(186, 26, 26, 0.08);
  border-color: rgba(186, 26, 26, 0.16);
  color: #93000a;
}

.feedback-success {
  background: rgba(19, 132, 106, 0.1);
  border-color: rgba(19, 132, 106, 0.16);
  color: var(--primary);
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
  font-size: 0.76rem;
  font-weight: 500;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #3e4945;
}

.field-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.field-label-row a {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--primary);
}

.field-control {
  position: relative;
  display: flex;
  align-items: center;
  border-radius: 8px;
  background: #f3f4f4;
  border: 1px solid transparent;
  transition: 0.25s ease;
}

.field-control:focus-within {
  border-color: rgba(21, 128, 61, 0.22);
  box-shadow: 0 0 0 4px rgba(21, 128, 61, 0.08);
}

.field-control svg {
  width: 20px;
  height: 20px;
  fill: #6e7a74;
  flex-shrink: 0;
}

.with-icon svg {
  position: absolute;
  left: 16px;
}

.field-control input {
  width: 100%;
  min-height: 58px;
  border: none;
  outline: none;
  background: transparent;
  padding: 0 18px;
  font: inherit;
  color: #191c1c;
}

.with-icon input {
  padding-left: 48px;
}

.with-action input {
  padding-right: 70px;
}

.field-control input::placeholder {
  color: #8a9591;
}

.field-action {
  position: absolute;
  right: 14px;
  border: none;
  background: transparent;
  color: var(--primary);
  font: inherit;
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
}

.submit-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 60px;
  margin-top: 8px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
  color: #ffffff;
  font: inherit;
  font-size: 1rem;
  font-weight: 500;
  letter-spacing: 0.01em;
  cursor: pointer;
  box-shadow: 0 18px 30px rgba(21, 128, 61, 0.22);
  transition: transform 0.25s ease, box-shadow 0.25s ease, opacity 0.25s ease;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-1px) scale(1.01);
  box-shadow: 0 22px 36px rgba(21, 128, 61, 0.26);
}

.submit-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.submit-arrow {
  font-size: 1.1rem;
  transition: transform 0.25s ease;
}

.submit-button:hover:not(:disabled) .submit-arrow {
  transform: translateX(4px);
}

.form-footer {
  margin-top: 28px;
  text-align: center;
  color: #4e6073;
}

.form-footer a {
  margin-left: 6px;
  font-weight: 500;
  color: var(--primary);
}

@media (max-width: 1080px) {
  .login-shell {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    min-height: 360px;
  }
}

@media (max-width: 768px) {
  .login-page {
    padding: 16px;
  }

  .login-shell {
    min-height: calc(100vh - 32px);
    border-radius: 8px;
  }

  .brand-panel {
    display: none;
  }

  .mobile-brand {
    display: block;
  }

  .form-panel-inner {
    padding: 32px 24px;
  }
}
</style>
