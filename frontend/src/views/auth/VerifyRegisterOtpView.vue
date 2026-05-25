<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authService } from '../../services/authService'
import { t } from '../../utils/locale'

const router = useRouter()
const loading = ref(false)
const resending = ref(false)
const countdown = ref(60)
const emailDisplay = ref('')
const otp = ref(['', '', '', '', '', ''])
const form = ref({})
const otpInputs = ref([])

let timer = null

const startCountdown = () => {
  countdown.value = 60
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    if (countdown.value > 0) {
      countdown.value--
    } else {
      clearInterval(timer)
    }
  }, 1000)
}

onMounted(() => {
  const pending = JSON.parse(sessionStorage.getItem('pending_registration') || 'null')
  if (!pending) {
    ElMessage.error(t('auth.sessionNotFound'))
    router.push({ name: 'register-otp' })
    return
  }
  form.value = pending
  emailDisplay.value = pending.email || ''
  startCountdown()
})

const handleInput = (index, event) => {
  const value = event.target.value
  // Keep only the last character entered
  otp.value[index] = value.slice(-1)
  
  if (otp.value[index] && index < otpInputs.value.length - 1) {
    otpInputs.value[index + 1]?.focus()
  }

  // Auto-submit if all digits are filled
  const otpCode = otp.value.join('')
  if (otpCode.length === 6) {
    registerAccount()
  }
}

const handleKeyDown = (index, event) => {
  if (event.key === 'Backspace') {
    if (!otp.value[index] && index > 0) {
      otp.value[index - 1] = ''
      otpInputs.value[index - 1]?.focus()
    } else {
      otp.value[index] = ''
    }
    event.preventDefault()
  }
}

const handlePaste = (event) => {
  event.preventDefault()
  const pasteData = event.clipboardData.getData('text').trim()
  if (/^\d{6}$/.test(pasteData)) {
    for (let i = 0; i < 6; i++) {
      otp.value[i] = pasteData[i]
    }
    otpInputs.value[5]?.focus()
    registerAccount()
  } else {
    ElMessage.warning('Vui lòng dán mã OTP gồm 6 chữ số')
  }
}

const resendOtpCode = async () => {
  if (countdown.value > 0 || resending.value) return
  resending.value = true
  try {
    await authService.sendOtp(emailDisplay.value)
    ElMessage.success('Đã gửi lại mã OTP thành công!')
    startCountdown()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Không thể gửi lại mã OTP. Vui lòng thử lại.')
  } finally {
    resending.value = false
  }
}

const registerAccount = async () => {
  const otpCode = otp.value.join('').trim()
  if (otpCode.length !== 6) {
    ElMessage.warning(t('auth.valOtpRequired'))
    return
  }

  loading.value = true
  try {
    await authService.register({
      email: form.value.email,
      password: form.value.password,
      full_name: form.value.full_name,
      phone: form.value.phone || null,
      province: form.value.province || null,
      date_of_birth: form.value.date_of_birth || null,
      gender: form.value.gender || null,
      account_type: form.value.account_type || 'user',
      play_hand: form.value.play_hand || null,
      otp_code: otpCode,
    })

    ElMessage.success(t('auth.registerSuccess'))
    sessionStorage.removeItem('pending_registration')
    router.push({ name: 'login' })
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('auth.verifyFailed'))
    // Clear OTP inputs on error to let user retry
    otp.value = ['', '', '', '', '', '']
    otpInputs.value[0]?.focus()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="verify-page">
    <div class="background-decorations">
      <div class="bubble bubble-1"></div>
      <div class="bubble bubble-2"></div>
    </div>
    
    <div class="verify-card">
      <div class="logo-area">
        <div class="logo-shield">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="tennis-icon">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M6 12A6 6 0 0 1 18 12"></path>
            <path d="M12 6A6 6 0 0 1 12 18"></path>
          </svg>
        </div>
      </div>

      <div class="header-section">
        <h1>{{ $t('auth.verifyTitle') }}</h1>
        <p class="subtitle">{{ $t('auth.otpSentTo') }}</p>
        <p class="email-highlight">{{ emailDisplay }}</p>
      </div>

      <div class="otp-container">
        <div class="otp-row">
          <input
            v-for="(_, index) in otp"
            :key="index"
            :ref="el => (otpInputs[index] = el)"
            v-model="otp[index]"
            maxlength="1"
            inputmode="numeric"
            type="text"
            pattern="[0-9]*"
            class="otp-input"
            @input="handleInput(index, $event)"
            @keydown="handleKeyDown(index, $event)"
            @paste="handlePaste"
            :disabled="loading"
          />
        </div>
      </div>

      <div class="action-section">
        <button class="submit-btn" :disabled="loading" @click="registerAccount">
          <span v-if="loading" class="spinner"></span>
          <span>{{ loading ? $t('auth.verifying') : $t('auth.verifyAndRegister') }}</span>
        </button>

        <div class="resend-wrapper">
          <span class="resend-text">Không nhận được mã?</span>
          <button 
            class="resend-btn" 
            :disabled="countdown > 0 || resending" 
            @click="resendOtpCode"
            :class="{ disabled: countdown > 0 }"
          >
            {{ countdown > 0 ? `Gửi lại mã sau (${countdown}s)` : 'Gửi lại mã ngay' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.verify-page {
  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #021f18 0%, #053b2f 50%, #0a4f40 100%);
  padding: 20px;
  overflow: hidden;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* Glassmorphism card and decorative bubbles */
.background-decorations {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
}

.bubble {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0) 70%);
  filter: blur(40px);
  animation: float-slow 12s infinite alternate ease-in-out;
}

.bubble-1 {
  width: 500px;
  height: 500px;
  top: -100px;
  right: -100px;
}

.bubble-2 {
  width: 600px;
  height: 600px;
  bottom: -200px;
  left: -200px;
  animation-delay: -4s;
}

@keyframes float-slow {
  0% { transform: translateY(0) scale(1); }
  100% { transform: translateY(30px) scale(1.1); }
}

.verify-card {
  position: relative;
  z-index: 2;
  width: min(100%, 460px);
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 28px;
  padding: 40px 32px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 28px;
  animation: card-appear 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes card-appear {
  0% { opacity: 0; transform: translateY(20px); }
  100% { opacity: 1; transform: translateY(0); }
}

/* Logo shield */
.logo-area {
  display: flex;
  justify-content: center;
}

.logo-shield {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.4) 100%);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 20px;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.tennis-icon {
  width: 36px;
  height: 36px;
  animation: spin-slow 20s linear infinite;
}

@keyframes spin-slow {
  100% { transform: rotate(360deg); }
}

/* Header typography */
.header-section h1 {
  font-size: 1.85rem;
  font-weight: 800;
  color: #ffffff;
  margin: 0 0 10px 0;
  letter-spacing: -0.5px;
}

.subtitle {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  line-height: 1.5;
}

.email-highlight {
  font-size: 1rem;
  font-weight: 600;
  color: #10b981;
  margin: 4px 0 0 0;
  word-break: break-all;
}

/* OTP Digits styling */
.otp-container {
  margin: 8px 0;
}

.otp-row {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.otp-input {
  width: 52px;
  height: 60px;
  text-align: center;
  font-size: 1.6rem;
  font-weight: 700;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.05);
  border: 1.5px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}

.otp-input:focus {
  background: rgba(255, 255, 255, 0.08);
  border-color: #10b981;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.2);
  transform: translateY(-2px);
}

.otp-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Submit button & actions */
.action-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.submit-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 16px;
  border: 0;
  border-radius: 16px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  font-size: 1.05rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 10px 25px rgba(5, 150, 105, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 14px 30px rgba(5, 150, 105, 0.4);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s infinite linear;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Resend mechanism */
.resend-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.resend-text {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.resend-btn {
  background: none;
  border: none;
  font-size: 0.9rem;
  font-weight: 600;
  color: #10b981;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: all 0.2s;
  outline: none;
}

.resend-btn:hover:not(.disabled) {
  color: #34d399;
  background: rgba(16, 185, 129, 0.08);
}

.resend-btn.disabled {
  color: rgba(255, 255, 255, 0.35);
  cursor: not-allowed;
}

/* Responsive adjustment */
@media (max-width: 480px) {
  .verify-card {
    padding: 30px 20px;
    gap: 24px;
  }
  
  .otp-input {
    width: 44px;
    height: 52px;
    font-size: 1.4rem;
  }
  
  .header-section h1 {
    font-size: 1.6rem;
  }
}
</style>
