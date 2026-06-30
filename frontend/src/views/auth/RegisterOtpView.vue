<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authService } from '../../services/authService'
import { Trophy, Right, InfoFilled, Loading } from '@element-plus/icons-vue'
import { t, currentLocale } from '../../utils/locale'

const router = useRouter()
const loading = ref(false)
const showPassword = ref(false)
const currentStep = ref(1) // 1: Nhập email, 2: Điền thông tin cá nhân

const form = ref({
  full_name: '',
  email: '',
  phone: '',
  password: '',
  province: '',
  date_of_birth: '',
  gender: 'male',
  play_hand: 'right', // Set default to right
  account_type: 'user',
})

const handleSendOtp = async () => {
  form.value.email = form.value.email?.trim() || ''

  // 1. Kiểm tra rỗng
  if (!form.value.email) return ElMessage.warning(t('auth.valEmailRequired'))

  // 2. Kiểm tra định dạng Email chuẩn xác
  const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/
  if (!emailRegex.test(form.value.email)) {
    return ElMessage.warning(t('auth.valEmailInvalid'))
  }

  loading.value = true
  let isSuccess = false // Cờ đánh dấu API gọi thành công

  try {
    await authService.sendOtp(form.value.email)
    isSuccess = true
  } catch (err) {
    const errorMsg = err.response?.data?.detail || err.message || t('auth.loginErrorConnection')
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }

  // Chỉ chuyển bước KHI VÀ CHỈ KHI API gửi OTP thành công
  if (isSuccess) {
    ElMessage.success(t('auth.otpSent', { email: form.value.email }))
    currentStep.value = 2
  }
}

const handleNext = async () => {
  if (currentStep.value === 1) {
    await handleSendOtp()
    return
  }

  // Xóa khoảng trắng thừa 2 đầu
  form.value.full_name = form.value.full_name?.trim() || ''
  form.value.phone = form.value.phone?.trim() || ''
  form.value.email = form.value.email?.trim() || ''

  // 1. Kiểm tra rỗng các trường bắt buộc ở bước 2
  if (!form.value.full_name) return ElMessage.warning(t('auth.valNameRequired'))
  if (!form.value.phone) return ElMessage.warning(t('auth.valPhoneRequired'))
  if (!form.value.password) return ElMessage.warning(t('auth.valPasswordRequired'))

  // 2. Kiểm tra số điện thoại (chỉ chứa số, độ dài 10-11 số)
  const phoneRegex = /^[0-9]{10,11}$/
  if (!phoneRegex.test(form.value.phone)) {
    return ElMessage.warning(t('auth.valPhoneInvalid'))
  }

  // 3. Kiểm tra độ dài mật khẩu (ít nhất 6 ký tự)
  if (form.value.password.length < 6) {
    return ElMessage.warning(t('auth.valPasswordLength'))
  }

  // Lưu tạm form xuống sessionStorage theo chuẩn cũ hệ thống đang dùng
  sessionStorage.setItem('pending_registration', JSON.stringify({ ...form.value }))
  
  // Chuyển trang đến màn verify nhập OTP
  router.push({ name: 'register-otp-verify' }).catch(err => {
    console.error("Lỗi chuyển trang:", err)
  })
}
</script>

<template>
  <div class="register-layout">
    <div class="background-wrapper">
      <div class="bg-image"></div>
      <div class="bg-overlay"></div>
    </div>

    <div class="register-container">
      <div class="register-card">
        
        <div class="card-brand">
          <div class="brand-content">
             <img src="https://res.cloudinary.com/dfs9o3bny/image/upload/v1776309753/z7730353029258_1dbe77285e553a1aa2ae1ab543a985c8-removebg-preview_nj3utv.png" alt="Saigontennistours Logo" class="brand-logo" />
            
            <h1 class="brand-title">Saigontennistours</h1>
            <p class="brand-subtitle">{{ $t('auth.brandDesc') }}</p>
            
            <div class="feature-list">
              <div class="feature-item">
                <el-icon><Trophy /></el-icon>
                <span>{{ $t('challenges.winTitle') }}</span>
              </div>
              <div class="feature-item">
                <el-icon><InfoFilled /></el-icon>
                <span>{{ $t('chat.newsSubtitle') }}</span>
              </div>
            </div>
          </div>
          <div class="brand-footer">
            <p>&copy; 2026 Saigontennistours</p>
          </div>
        </div>

        <div class="card-form">
          <!-- Form Header Step 1 -->
          <div v-if="currentStep === 1" class="form-header">
            <h2>{{ $t('auth.registerTitle') }}</h2>
            <p>Nhập email của bạn để nhận mã xác thực OTP tạo tài khoản</p>
          </div>
          <!-- Form Header Step 2 -->
          <div v-else class="form-header">
            <h2>Hoàn thiện thông tin</h2>
            <p>Vui lòng điền thông tin tài khoản và kiểm tra hòm thư của bạn</p>
          </div>

          <div class="form-body">
            <!-- BƯỚC 1: CHỈ NHẬP EMAIL -->
            <div v-if="currentStep === 1" class="form-row">
              <div class="form-group">
                <label>{{ $t('auth.email') }} <span class="required">*</span></label>
                <el-input 
                  v-model="form.email" 
                  type="email" 
                  placeholder="tennis@gmail.com" 
                  class="modern-input"
                  size="large"
                  @keyup.enter="handleNext"
                />
                <small style="color: var(--text-muted); margin-top: 4px; font-size: 0.82rem; line-height: 1.4;">
                  * Vui lòng nhập email hợp lệ. Ví dụ: tennis@gmail.com
                </small>
              </div>
            </div>

            <!-- BƯỚC 2: NHẬP THÔNG TIN CÁ NHÂN -->
            <template v-else>
              <div class="form-row">
                <div class="form-group">
                  <label>{{ $t('auth.fullName') }} <span class="required">*</span></label>
                  <el-input 
                    v-model="form.full_name" 
                    placeholder="VD: Nguyễn Văn A" 
                    class="modern-input"
                    size="large"
                  />
                </div>
              </div>

              <div class="form-row two-col">
                <div class="form-group">
                  <label>{{ $t('auth.email') }}</label>
                  <el-input 
                    v-model="form.email" 
                    type="email" 
                    class="modern-input"
                    size="large"
                    disabled
                  />
                </div>
                <div class="form-group">
                  <label>{{ $t('auth.phone') }} <span class="required">*</span></label>
                  <el-input 
                    v-model="form.phone" 
                    type="tel" 
                    placeholder="09xx xxx xxx" 
                    class="modern-input"
                    size="large"
                  />
                </div>
              </div>

              <div class="form-row two-col">
                <div class="form-group">
                  <label>{{ $t('auth.province') }}</label>
                   <el-input 
                    v-model="form.province" 
                    placeholder="VD: TP. Hồ Chí Minh" 
                    class="modern-input"
                    size="large"
                  />
                </div>
                 <div class="form-group">
                  <label>{{ $t('auth.dob') }}</label>
                  <el-input 
                    type="date" 
                    v-model="form.date_of_birth" 
                    class="modern-input"
                    size="large"
                  />
                </div>
              </div>

              <div class="form-row two-col">
                 <div class="form-group">
                  <label>{{ $t('auth.gender') }}</label>
                  <el-select v-model="form.gender" class="modern-select" size="large">
                    <el-option :label="$t('auth.male')" value="male" />
                    <el-option :label="$t('auth.female')" value="female" />
                  </el-select>
                </div>
                 <div class="form-group">
                  <label>{{ $t('auth.playHand') }}</label>
                  <el-select v-model="form.play_hand" class="modern-select" size="large">
                    <el-option :label="$t('auth.right')" value="right" />
                    <el-option :label="$t('auth.left')" value="left" />
                    <el-option :label="$t('auth.both')" value="both" />
                  </el-select>
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>{{ $t('auth.password') }} <span class="required">*</span></label>
                  <el-input 
                    v-model="form.password" 
                    :type="showPassword ? 'text' : 'password'" 
                    :placeholder="$t('auth.passwordHint')" 
                    class="modern-input"
                    size="large"
                    @keyup.enter="handleNext"
                  >
                    <template #suffix>
                      <span 
                        class="password-toggle" 
                        @click="showPassword = !showPassword"
                      >
                        {{ showPassword ? $t('auth.hide') : $t('auth.show') }}
                      </span>
                    </template>
                  </el-input>
                </div>
              </div>
            </template>
          </div>

          <div class="form-actions">
            <el-button 
              type="primary" 
              class="submit-btn" 
              :loading="loading" 
              @click="handleNext"
              size="large"
            >
              <span v-if="!loading">{{ currentStep === 1 ? 'Nhận mã xác thực OTP' : 'Tiếp tục xác thực OTP' }}</span>
              <el-icon v-if="!loading" class="el-icon--right"><Right /></el-icon>
            </el-button>
            
            <button 
              v-if="currentStep === 2" 
              class="resend-btn"
              style="border: none; background: transparent; cursor: pointer; color: var(--text-muted); font-weight: 600; text-align: center; margin-top: -10px; font-size: 0.92rem;"
              @click="currentStep = 1"
            >
              Quay lại nhập email
            </button>
            
            <p class="login-prompt">
              {{ $t('auth.hasAccount') }} 
              <router-link to="/login" class="login-link">{{ $t('auth.loginHere') }}</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Reset & Typography */
* {
  box-sizing: border-box;
}

.register-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background-color: #f8fafc;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  padding: 20px;
}

/* Background Effects */
.background-wrapper {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  overflow: hidden;
  z-index: 0;
}

.bg-image {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: url('https://images.unsplash.com/photo-1595435934249-5df7ed86e1f4?q=80&w=2070&auto=format&fit=crop');
  background-size: cover;
  background-position: center;
  filter: blur(8px);
  transform: scale(1.05); /* Tránh viền trắng khi blur */
}

.bg-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(135deg, rgba(0, 18, 66, 0.85) 0%, rgba(16, 185, 129, 0.75) 100%);
}

/* Main Container & Card */
.register-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1100px;
}

.register-card {
  display: flex;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  min-height: 520px;
  height: auto;
  transition: all 0.3s ease;
}

/* Left Side: Branding */
.card-brand {
  flex: 0 0 40%;
  background: #001242; /* Màu xanh đậm thương hiệu */
  color: white;
  padding: 48px 40px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  overflow: hidden;
}

/* Hiệu ứng trang trí góc */
.card-brand::before {
  content: '';
  position: absolute;
  top: -50px;
  left: -50px;
  width: 250px;
  height: 250px;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 50%;
  z-index: 0;
}

.card-brand::after {
  content: '';
  position: absolute;
  bottom: -100px;
  right: -50px;
  width: 300px;
  height: 300px;
  background: rgba(16, 185, 129, 0.15);
  border-radius: 50%;
  z-index: 0;
}

.brand-content, .brand-footer {
  position: relative;
  z-index: 1;
}

.brand-logo {
  height: 80px;
  width: auto;
  margin-bottom: 24px;
  filter: drop-shadow(0 4px 6px rgba(0,0,0,0.2));
}

.brand-title {
  font-size: 2.2rem;
  font-weight: 800;
  margin: 0 0 16px 0;
  line-height: 1.2;
  background: linear-gradient(to right, #ffffff, #10b981);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.brand-subtitle {
  font-size: 1rem;
  line-height: 1.6;
  color: #cbd5e1;
  margin: 0 0 40px 0;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 0.95rem;
  color: #f8fafc;
}

.feature-item .el-icon {
  font-size: 1.5rem;
  color: #10b981;
  background: rgba(16, 185, 129, 0.15);
  padding: 8px;
  border-radius: 12px;
}

.brand-footer {
  font-size: 0.85rem;
  color: #64748b;
}

/* Right Side: Form */
.card-form {
  flex: 1;
  padding: 48px 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: #ffffff;
}

.form-header {
  margin-bottom: 32px;
}

.form-header h2 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.form-header p {
  font-size: 0.95rem;
  color: #64748b;
  margin: 0;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 32px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row.two-col {
  flex-direction: row;
}

.form-row.two-col .form-group {
  flex: 1;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #334155;
}

.required {
  color: #ef4444;
}

/* Element Plus Overrides for Modern Look */
:deep(.modern-input .el-input__wrapper),
:deep(.modern-select .el-select__wrapper) {
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  background-color: #f8fafc;
  transition: all 0.2s ease;
  padding-left: 12px;
  padding-right: 12px;
}

:deep(.modern-input .el-input__wrapper:hover),
:deep(.modern-select .el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #cbd5e1 inset;
}

:deep(.modern-input .el-input__wrapper.is-focus),
:deep(.modern-select .el-select__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2) inset !important;
  background-color: #ffffff;
}

:deep(.modern-input .el-input__inner) {
  font-family: inherit;
  color: #0f172a;
}

.password-toggle {
  cursor: pointer;
  color: #10b981;
  font-size: 0.85rem;
  font-weight: 600;
  user-select: none;
}

.password-toggle:hover {
  color: #059669;
}

/* Actions */
.form-actions {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.submit-btn {
  width: 100%;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  letter-spacing: 0.5px;
  background-color: #10b981;
  border-color: #10b981;
  height: 52px;
  transition: all 0.3s ease;
}

.submit-btn:hover {
  background-color: #059669;
  border-color: #059669;
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
}

.login-prompt {
  text-align: center;
  font-size: 0.95rem;
  color: #64748b;
  margin: 0;
}

.login-link {
  color: #001242;
  font-weight: 700;
  text-decoration: none;
  margin-left: 4px;
  transition: color 0.2s;
}

.login-link:hover {
  color: #10b981;
  text-decoration: underline;
}

/* Responsive Design */
@media (max-width: 992px) {
  .register-card {
    flex-direction: column;
    min-height: auto;
  }
  
  .card-brand {
    padding: 40px 32px;
  }
  
  .brand-logo {
    height: 60px;
  }
  
  .card-brand::before, .card-brand::after {
    display: none;
  }
}

@media (max-width: 768px) {
  .register-layout {
    padding: 16px;
  }
  
  .register-card {
    flex-direction: column;
    min-height: auto;
  }
  
  .card-brand {
    flex: none;
    padding: 24px 20px;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    gap: 16px;
  }
  
  .brand-logo {
    height: 48px;
    margin-bottom: 0;
  }
  
  .brand-title {
    font-size: 1.5rem;
    margin: 0;
  }
  
  .brand-subtitle, .feature-list, .brand-footer {
    display: none !important;
  }
  
  .card-form {
    padding: 32px 24px;
  }
  
  .form-row.two-col {
    flex-direction: column;
    gap: 20px;
  }
}

@media (max-width: 480px) {
  .register-layout {
    padding: 0;
  }
  
  .register-card {
    border-radius: 0;
    box-shadow: none;
  }
  
  .card-brand {
    padding: 20px 16px;
    gap: 12px;
  }
  
  .brand-logo {
    height: 40px;
  }

  .brand-title {
    font-size: 1.3rem;
  }
  
  .card-form {
    padding: 24px 16px;
  }
}
</style>