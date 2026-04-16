<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const SEND_OTP_ENDPOINT = `${API_BASE_URL}/api/auth/send-otp`
const REGISTER_ENDPOINT = `${API_BASE_URL}/api/auth/register`
const LOGIN_ENDPOINT = `${API_BASE_URL}/api/auth/login`
const RESEND_SECONDS = 60
const OTP_CODE_REGEX = /^\d{6}$/
const PENDING_REGISTER_STORAGE_KEY = 'saigon_tennis_pending_register'

import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isRegistering = ref(false)
const isSendingOtp = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const createdUserId = ref(null)
const resendCountdown = ref(0)
const countdownTimerId = ref(null)

const form = ref({
  email: '',
  full_name: '',
  password: '',
  otp_code: '',
})

const canResendOtp = computed(() => resendCountdown.value === 0 && !isSendingOtp.value)
const otpDigits = computed(() => form.value.otp_code.padEnd(6, '').slice(0, 6).split(''))
const resendProgressStyle = computed(() => ({
  width: `${((RESEND_SECONDS - resendCountdown.value) / RESEND_SECONDS) * 100}%`,
}))

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

const loadPendingRegistration = () => {
  const rawValue = window.sessionStorage.getItem(PENDING_REGISTER_STORAGE_KEY)

  if (!rawValue) {
    router.replace({ name: 'register-otp' })
    return
  }

  try {
    const pendingRegistration = JSON.parse(rawValue)
    form.value.email = pendingRegistration.email || ''
    form.value.full_name = pendingRegistration.full_name || ''
    form.value.password = pendingRegistration.password || ''
    form.value.phone = pendingRegistration.phone || ''
    form.value.province = pendingRegistration.province || ''
    form.value.date_of_birth = pendingRegistration.date_of_birth || ''
    form.value.gender = pendingRegistration.gender || 'male'
    form.value.account_type = pendingRegistration.account_type || 'user'

    if (!form.value.email || !form.value.full_name || !form.value.password) {
      window.sessionStorage.removeItem(PENDING_REGISTER_STORAGE_KEY)
      router.replace({ name: 'register-otp' })
    }
  } catch {
    window.sessionStorage.removeItem(PENDING_REGISTER_STORAGE_KEY)
    router.replace({ name: 'register-otp' })
  }
}

const clearPendingRegistration = () => {
  window.sessionStorage.removeItem(PENDING_REGISTER_STORAGE_KEY)
}

const startResendCountdown = () => {
  resendCountdown.value = RESEND_SECONDS

  if (countdownTimerId.value) {
    clearInterval(countdownTimerId.value)
  }

  countdownTimerId.value = window.setInterval(() => {
    if (resendCountdown.value <= 1) {
      resendCountdown.value = 0
      clearInterval(countdownTimerId.value)
      countdownTimerId.value = null
      return
    }

    resendCountdown.value -= 1
  }, 1000)
}

const resendOtp = async () => {
  clearMessages()
  isSendingOtp.value = true

  try {
    const response = await fetch(SEND_OTP_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: form.value.email.trim(),
      }),
    })

    if (!response.ok) {
      errorMessage.value = await handleApiError(
        response,
        'Không thể gửi lại mã OTP. Vui lòng thử lại.'
      )
      return
    }

    successMessage.value = 'Mã OTP đã được gửi lại thành công.'
    startResendCountdown()
  } catch {
    errorMessage.value = 'Không kết nối được tới backend. Hãy kiểm tra API server và thử lại.'
  } finally {
    isSendingOtp.value = false
  }
}

const persistSession = (tokenData) => {
  authStore.setSession({
    accessToken: tokenData.access_token,
    tokenType: tokenData.token_type || 'bearer',
    user: {
      email: form.value.email.trim(),
      full_name: tokenData.full_name || form.value.full_name.trim(),
      user_id: tokenData.user_id || createdUserId.value,
      role_id: tokenData.role_id,
      account_type: tokenData.account_type
    }
  })
}

const loginAfterRegister = async () => {
  const response = await fetch(LOGIN_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: form.value.email.trim(),
      password: form.value.password,
    }),
  })

  if (!response.ok) {
    throw new Error(await handleApiError(response, 'Không thể tự động đăng nhập sau khi đăng ký.'))
  }

  const data = await response.json()
  persistSession(data)
  clearPendingRegistration()
  successMessage.value = 'Đăng ký và đăng nhập thành công. Đang chuyển vào hệ thống...'

  router.push({ name: 'home' }).catch(() => {
    router.push('/')
  })
}

const registerAccount = async () => {
  clearMessages()

  const normalizedOtpCode = form.value.otp_code.trim()

  if (!OTP_CODE_REGEX.test(normalizedOtpCode)) {
    errorMessage.value = 'Mã OTP phải gồm đúng 6 chữ số.'
    return
  }

  isRegistering.value = true

  try {
    const response = await fetch(REGISTER_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: form.value.email.trim(),
        full_name: form.value.full_name.trim(),
        password: form.value.password,
        otp_code: normalizedOtpCode,
        phone: form.value.phone || null,
        province: form.value.province || null,
        date_of_birth: form.value.date_of_birth || null,
        gender: form.value.gender || null,
        account_type: form.value.account_type || 'user'
      }),
    })

    if (!response.ok) {
      errorMessage.value = await handleApiError(
        response,
        'Đăng ký thất bại. Vui lòng kiểm tra lại mã OTP.'
      )
      return
    }

    const data = await response.json()
    createdUserId.value = data.user_id ?? null

    try {
      await loginAfterRegister()
    } catch (loginError) {
      successMessage.value = `${data.message || 'Đăng ký thành công.'} Tài khoản đã được tạo nhưng chưa tự động đăng nhập được.`
      errorMessage.value = loginError.message
    }
  } catch {
    errorMessage.value = 'Không thể hoàn tất đăng ký vì backend không phản hồi.'
  } finally {
    isRegistering.value = false
  }
}

const backToRegister = () => {
  router.push({ name: 'register-otp' })
}

const handleOtpInput = (event) => {
  const normalizedValue = event.target.value.replace(/\D/g, '').slice(0, 6)
  form.value.otp_code = normalizedValue
}

loadPendingRegistration()
startResendCountdown()

onBeforeUnmount(() => {
  if (countdownTimerId.value) {
    clearInterval(countdownTimerId.value)
  }

})
</script>

<template>
  <div class="otp-page">
    <header class="otp-header">
      <div class="otp-brand">Saigon Tennis</div>
      <button id="back-register-button" class="header-action" type="button" @click="backToRegister">
        Quay lại
      </button>
    </header>

    <main class="otp-main">
      <div class="court-line court-line-top"></div>
      <div class="court-line court-line-middle"></div>
      <div class="court-line court-line-bottom"></div>

      <section class="otp-shell">
        <div class="otp-glow"></div>

        <article class="otp-card">
          <header class="otp-copy">
            <p class="copy-kicker">Xác thực tài khoản</p>
            <h1>Nhập mã OTP</h1>
            <p>
              Mã xác thực đã được gửi tới <strong>{{ form.email }}</strong>. Nhập 6 chữ số để hoàn tất
              quá trình đăng ký.
            </p>
          </header>

          <div v-if="errorMessage" class="feedback feedback-error" role="alert">
            {{ errorMessage }}
          </div>

          <div v-if="successMessage" class="feedback feedback-success" role="status">
            {{ successMessage }}
          </div>

          <form class="otp-form" @submit.prevent="registerAccount">
            <label class="otp-field" for="register-otp-code">
              <span>Mã OTP</span>
              <input
                id="register-otp-code"
                :value="form.otp_code"
                type="text"
                inputmode="numeric"
                placeholder="Nhập 6 số OTP"
                maxlength="6"
                autocomplete="one-time-code"
                required
                @input="handleOtpInput"
              />
            </label>

            <div class="otp-preview" aria-hidden="true">
              <span v-for="(digit, index) in otpDigits" :key="index">{{ digit || '•' }}</span>
            </div>

            <div class="resend-block">
              <div class="resend-row">
                <span>
                  {{ resendCountdown > 0 ? `Gửi lại OTP sau ${resendCountdown}s` : 'Bạn có thể gửi lại OTP ngay bây giờ' }}
                </span>
                <button
                  id="resend-otp-button"
                  class="resend-link"
                  type="button"
                  :disabled="!canResendOtp"
                  @click="resendOtp"
                >
                  {{ isSendingOtp ? 'Đang gửi...' : 'Gửi lại OTP' }}
                </button>
              </div>
              <div class="progress-bar">
                <div class="progress-bar-fill" :style="resendProgressStyle"></div>
              </div>
            </div>

            <div class="action-grid">
              <button class="secondary-button" type="button" @click="backToRegister">Sửa thông tin</button>
              <button
                id="verify-otp-submit-button"
                class="primary-button"
                type="submit"
                :disabled="isRegistering"
              >
                {{ isRegistering ? 'Đang tạo tài khoản...' : 'Xác thực' }}
              </button>
            </div>

            <div class="success-hint">
              <span class="hint-icon">✓</span>
              <span>Sẵn sàng vào sân. Xác thực xong là bạn có thể sử dụng hệ thống ngay.</span>
            </div>
          </form>
        </article>

        <aside class="support-card">
          <div>
            <span class="support-kicker">Support</span>
            <p>
              Nếu bạn chưa nhận được mã, hãy kiểm tra thư mục spam hoặc liên hệ đội hỗ trợ qua
              support@saigontennis.com.
            </p>
          </div>
          <div class="support-ball"></div>
        </aside>
      </section>
    </main>

    <footer class="otp-footer">© 2026 SAIGON TENNIS CLUB • OTP VERIFICATION</footer>
  </div>
</template>

<style scoped>
.otp-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #f8f9f9 0%, #edf0f0 100%);
  color: #191c1c;
}

.otp-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 80px;
  padding: 0 32px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(18px);
  box-shadow: 0 18px 32px rgba(25, 28, 28, 0.04);
}

.otp-brand {
  font-size: 1.9rem;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: var(--text-dark);
}

.header-action {
  border: none;
  border-radius: 8px;
  background: rgba(21, 128, 61, 0.08);
  color: var(--primary);
  min-height: 42px;
  padding: 0 18px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.otp-main {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
  overflow: hidden;
}

.court-line {
  position: absolute;
  left: -20%;
  width: 140%;
  height: 1px;
  background: rgba(21, 128, 61, 0.06);
  transform: rotate(-45deg);
}

.court-line-top {
  top: 8%;
}

.court-line-middle {
  top: 34%;
}

.court-line-bottom {
  top: 60%;
}

.otp-shell {
  position: relative;
  width: min(100%, 760px);
}

.otp-glow {
  position: absolute;
  top: -36px;
  left: -36px;
  width: 160px;
  height: 160px;
  border-radius: 8px;
  background: rgba(148, 245, 214, 0.34);
  filter: blur(48px);
}

.otp-card {
  position: relative;
  z-index: 2;
  padding: 40px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 24px 60px rgba(25, 28, 28, 0.06);
}

.otp-copy {
  margin-bottom: 24px;
}

.copy-kicker {
  margin-bottom: 10px;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #6e7a74;
}

.otp-copy h1 {
  margin-bottom: 10px;
  font-size: clamp(2.25rem, 5vw, 3.4rem);
  line-height: 1.05;
  letter-spacing: -0.04em;
}

.otp-copy p {
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

.otp-form {
  display: grid;
  gap: 18px;
}

.otp-field {
  display: grid;
  gap: 8px;
}

.otp-field > span {
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #3e4945;
}

.otp-field input {
  width: 100%;
  min-height: 60px;
  border: 1px solid transparent;
  outline: none;
  border-radius: 8px;
  background: #f3f4f4;
  padding: 0 18px;
  font: inherit;
  font-size: 1rem;
  color: #191c1c;
  transition: 0.25s ease;
}

.otp-field input:focus {
  border-color: rgba(21, 128, 61, 0.24);
  box-shadow: 0 0 0 4px rgba(21, 128, 61, 0.08);
}

.otp-preview {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.otp-preview span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1;
  border-radius: 8px;
  background: #f3f4f4;
  font-size: 1.7rem;
  font-weight: 800;
  color: var(--text-dark);
}

.resend-block {
  display: grid;
  gap: 10px;
}

.resend-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  font-size: 0.94rem;
  color: #4e6073;
}

.resend-link {
  border: none;
  background: transparent;
  color: var(--primary);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.resend-link:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.progress-bar {
  height: 6px;
  width: 100%;
  overflow: hidden;
  border-radius: 8px;
  background: #e7e8e8;
}

.progress-bar-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
  transition: width 1s linear;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.primary-button,
.secondary-button {
  min-height: 58px;
  border-radius: 8px;
  font: inherit;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease, opacity 0.25s ease;
}

.primary-button {
  border: none;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
  color: #ffffff;
  box-shadow: 0 18px 32px rgba(21, 128, 61, 0.18);
}

.secondary-button {
  border: 1px solid rgba(21, 128, 61, 0.14);
  background: rgba(21, 128, 61, 0.04);
  color: var(--primary);
}

.primary-button:hover:not(:disabled),
.secondary-button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.primary-button:disabled,
.secondary-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.success-hint {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(148, 245, 214, 0.18);
  border: 1px solid rgba(148, 245, 214, 0.26);
  color: #005140;
  font-size: 0.92rem;
}

.hint-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 8px;
  background: rgba(21, 128, 61, 0.12);
  color: var(--primary);
  font-weight: 800;
}

.support-card {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 16px 0;
}

.support-kicker {
  display: inline-block;
  margin-bottom: 6px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #6e7a74;
}

.support-card p {
  max-width: 520px;
  color: #4e6073;
  font-size: 0.9rem;
  line-height: 1.6;
}

.support-ball {
  width: 72px;
  height: 72px;
  border-radius: 8px;
  flex-shrink: 0;
  background:
    radial-gradient(circle at 36% 34%, rgba(255, 255, 255, 0.34), transparent 14%),
    radial-gradient(circle at center, #dff77b 0%, #abd64f 58%, #7ea220 100%);
  box-shadow: 0 18px 24px rgba(25, 28, 28, 0.08);
}

.otp-footer {
  padding: 24px;
  text-align: center;
  color: #6e7a74;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

@media (max-width: 720px) {
  .otp-header {
    padding: 0 20px;
  }

  .otp-main {
    padding: 20px 16px;
  }

  .otp-card {
    padding: 28px 20px;
    border-radius: 8px;
  }

  .otp-preview {
    gap: 8px;
  }

  .otp-preview span {
    border-radius: 14px;
    font-size: 1.3rem;
  }

  .resend-row,
  .action-grid,
  .support-card {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }

  .action-grid {
    display: grid;
  }

  .support-ball {
    width: 56px;
    height: 56px;
    align-self: flex-start;
  }
}
</style>
