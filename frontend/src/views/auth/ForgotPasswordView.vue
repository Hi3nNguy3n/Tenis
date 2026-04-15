<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../../services/apiClient'

const router = useRouter()
const email = ref('')
const otp = ref('')
const newPassword = ref('')
const step = ref(1) // 1: Send Email, 2: Reset Password
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const handleSendOtp = async () => {
  if (!email.value) return
  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await apiClient.post('/api/auth/forgot-password', { email: email.value })
    step.value = 2
    successMessage.value = 'Mã xác thực đã được gửi về email của bạn.'
  } catch (err) {
    errorMessage.value = err.message || 'Lỗi khi gửi yêu cầu. Email có thể không tồn tại.'
  } finally {
    isLoading.value = false
  }
}

const handleResetPassword = async () => {
  if (!otp.value || !newPassword.value) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    await apiClient.post(`/api/auth/reset-password?email=${email.value}&otp=${otp.value}&new_password=${newPassword.value}`)
    successMessage.value = 'Đổi mật khẩu thành công! Chuyển hướng về trang đăng nhập...'
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (err) {
    errorMessage.value = err.message || 'Mã OTP không đúng hoặc đã hết hạn.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="forgot-password-page">
    <div class="blur-blob"></div>
    <div class="blur-blob secondary"></div>
    
    <main class="auth-shell">
      <section class="auth-card">
        <header class="auth-header">
          <div class="brand-logotype">Saigon Tennis</div>
          <h1>{{ step === 1 ? 'Khôi phục mật khẩu' : 'Đặt lại mật khẩu' }}</h1>
          <p v-if="step === 1">Nhập email liên kết với tài khoản của bạn để nhận mã OTP khôi phục.</p>
          <p v-else>Kiểm tra email và nhập mã xác thực 6 chữ số cùng mật khẩu mới của bạn.</p>
        </header>

        <div v-if="errorMessage" class="feedback error">{{ errorMessage }}</div>
        <div v-if="successMessage" class="feedback success">{{ successMessage }}</div>

        <div class="form-body">
          <div v-if="step === 1" class="step-container">
            <div class="field-group">
              <label>Địa chỉ Email</label>
              <div class="input-wrapper">
                <input v-model="email" type="email" placeholder="email@example.com" @keyup.enter="handleSendOtp" />
              </div>
            </div>
            
            <button class="submit-btn" :disabled="isLoading" @click="handleSendOtp">
              {{ isLoading ? 'Đang gửi mã...' : 'Gửi mã xác thực' }}
              <span class="btn-arrow">→</span>
            </button>
          </div>

          <div v-if="step === 2" class="step-container">
            <div class="field-group">
              <label>Mã xác thực (OTP)</label>
              <div class="input-wrapper">
                <input v-model="otp" type="text" placeholder="6 chữ số" maxlength="6" />
              </div>
            </div>

            <div class="field-group">
              <label>Mật khẩu mới</label>
              <div class="input-wrapper">
                <input v-model="newPassword" type="password" placeholder="Tối thiểu 6 ký tự" @keyup.enter="handleResetPassword" />
              </div>
            </div>
            
            <button class="submit-btn" :disabled="isLoading" @click="handleResetPassword">
              {{ isLoading ? 'Đang xử lý...' : 'Cập nhật mật khẩu' }}
              <span class="btn-arrow">→</span>
            </button>
            <button class="back-link-btn" @click="step = 1">Gửi lại mã khác</button>
          </div>
        </div>

        <footer class="auth-footer">
          <router-link to="/login">Quay lại trang đăng nhập</router-link>
        </footer>
      </section>
    </main>
  </div>
</template>

<style scoped>
.forgot-password-page {
  min-height: 100vh;
  background: #f8f9f9;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.blur-blob {
  position: absolute;
  top: -10%; right: -5%;
  width: 40vw; height: 40vw;
  background: radial-gradient(circle, rgba(0, 105, 83, 0.08) 0%, transparent 70%);
  z-index: 1;
}

.blur-blob.secondary {
  bottom: -10%; left: -5%;
  background: radial-gradient(circle, rgba(215, 241, 113, 0.12) 0%, transparent 70%);
}

.auth-shell {
  position: relative;
  z-index: 2;
  width: min(100%, 480px);
  padding: 24px;
}

.auth-card {
  background: white;
  padding: 3.5rem;
  border-radius: 32px;
  box-shadow: 0 40px 100px rgba(0,0,0,0.06);
  border: 1px solid rgba(0,0,0,0.02);
}

.brand-logotype {
  font-size: 1.5rem;
  font-weight: 800;
  color: #006953;
  margin-bottom: 2rem;
  letter-spacing: -0.05em;
}

.auth-header h1 {
  font-size: 2rem;
  color: #123f34;
  margin-bottom: 0.8rem;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.auth-header p {
  color: #6e7a74;
  line-height: 1.6;
  margin-bottom: 2.5rem;
}

.feedback {
  padding: 1rem 1.2rem;
  border-radius: 12px;
  font-size: 0.9rem;
  margin-bottom: 2rem;
  font-weight: 600;
}

.feedback.error { background: #fee2e2; color: #991b1b; }
.feedback.success { background: #dcfce7; color: #166534; }

.form-body { margin-bottom: 2.5rem; }

.field-group { margin-bottom: 1.5rem; }
.field-group label {
  display: block; font-size: 0.75rem; font-weight: 800;
  text-transform: uppercase; letter-spacing: 0.1em;
  color: #4e6073; margin-bottom: 0.6rem; margin-left: 0.2rem;
}

.input-wrapper input {
  width: 100%; padding: 1.1rem 1.2rem; border-radius: 16px;
  border: 2px solid #f0f2f2; background: #f8f9f9;
  font: inherit; transition: 0.2s;
}

.input-wrapper input:focus {
  border-color: #006953; background: white; outline: none;
}

.submit-btn {
  width: 100%; padding: 1.2rem; border-radius: 16px; border: none;
  background: #006953; color: white; font-weight: 800; font-size: 1.05rem;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  gap: 12px; box-shadow: 0 15px 30px rgba(0, 105, 83, 0.15); transition: 0.2s;
}

.submit-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 20px 40px rgba(0, 105, 83, 0.2); }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-arrow { transition: 0.2s; }
.submit-btn:hover .btn-arrow { transform: translateX(4px); }

.back-link-btn {
  width: 100%; background: none; border: none; padding: 1rem;
  color: #006953; font-weight: 700; cursor: pointer; font-size: 0.9rem;
}

.auth-footer { text-align: center; border-top: 1px solid #f0f2f2; padding-top: 2rem; }
.auth-footer a { color: #4e6073; text-decoration: none; font-weight: 700; font-size: 0.95rem; }
.auth-footer a:hover { color: #006953; }

@media (max-width: 480px) {
  .auth-card { padding: 2.5rem 1.5rem; }
}
</style>

