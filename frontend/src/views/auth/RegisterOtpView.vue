<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { User, Lock, Phone, Location, Calendar, Check, Loading, View, Hide } from '@element-plus/icons-vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const SEND_OTP_ENDPOINT = `${API_BASE_URL}/api/auth/send-otp`
const PENDING_REGISTER_STORAGE_KEY = 'saigon_tennis_pending_register'

const router = useRouter()

const isSendingOtp = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const showPassword = ref(false)

const vietnamProvinces = [
  'An Giang', 'Bắc Ninh', 'Cà Mau', 'Cao Bằng', 'Đắk Lắk',
  'Điện Biên', 'Đồng Nai', 'Đồng Tháp', 'Gia Lai', 'Hà Tĩnh',
  'Hưng Yên', 'Khánh Hòa', 'Lai Châu', 'Lâm Đồng', 'Lạng Sơn',
  'Lào Cai', 'Nghệ An', 'Ninh Bình', 'Phú Thọ', 'Quảng Ngãi',
  'Quảng Ninh', 'Quảng Trị', 'Sơn La', 'Tây Ninh', 'Thái Nguyên',
  'Thanh Hóa', 'TP Cần Thơ', 'TP Đà Nẵng', 'TP Hà Nội', 'TP Hải Phòng',
  'TP Hồ Chí Minh', 'TP Huế', 'Tuyên Quang', 'Vĩnh Long',
]

const form = ref({
  email: '',
  full_name: '',
  password: '',
  phone: '',
  province: '',
  date_of_birth: '',
  gender: 'male',
  account_type: 'user',
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

const validateForm = () => {
  const normalizedEmail = form.value.email.trim()
  const normalizedFullName = form.value.full_name.trim()

  if (!normalizedEmail) {
    errorMessage.value = 'Vui lòng nhập email để nhận mã OTP.'
    return false
  }

  if (!normalizedFullName) {
    errorMessage.value = 'Vui lòng nhập họ và tên.'
    return false
  }

  if (!form.value.phone) {
    errorMessage.value = 'Vui lòng nhập số điện thoại.'
    return false
  }

  if (form.value.password.length < 6) {
    errorMessage.value = 'Mật khẩu phải có ít nhất 6 ký tự.'
    return false
  }

  return true
}

const persistPendingRegistration = () => {
  window.sessionStorage.setItem(
    PENDING_REGISTER_STORAGE_KEY,
    JSON.stringify({
      email: form.value.email.trim(),
      full_name: form.value.full_name.trim(),
      password: form.value.password,
      phone: form.value.phone.trim(),
      province: form.value.province,
      date_of_birth: form.value.date_of_birth,
      gender: form.value.gender,
      account_type: form.value.account_type,
    })
  )
}

const startRegistration = async () => {
  clearMessages()
  if (!validateForm()) return

  isSendingOtp.value = true

  try {
    const response = await fetch(SEND_OTP_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: form.value.email.trim() }),
    })

    if (!response.ok) {
      errorMessage.value = await handleApiError(response, 'Không thể gửi mã OTP. Vui lòng kiểm tra lại.')
      return
    }

    persistPendingRegistration()
    successMessage.value = 'Mã OTP đã được gửi. Đang chuyển hướng...'
    setTimeout(() => {
      router.push({ name: 'register-otp-verify' })
    }, 1200)
  } catch {
    errorMessage.value = 'Không kết nối được tới server.'
  } finally {
    isSendingOtp.value = false
  }
}
</script>

<template>
  <div class="veridian-register-layout">
    <div class="visual-panel">
      <div class="grid-overlay"></div>
      <div class="brand-content">
        <div class="hero-text">
          <h2 class="text-top">CÔNG NGHỆ</h2>
          <h2 class="text-bottom">VƯỢT TRỘI</h2>
        </div>
        <div class="kicker-line">
          <span class="lime-bar"></span>
          <p>QUẢN LÝ GIẢI ĐẤU CHUYÊN NGHIỆP</p>
        </div>
      </div>

      <div class="status-box">
        <div class="status-inner">
          <div class="status-label-group">
            <span class="status-title">TRẠNG THÁI HỆ THỐNG</span>
            <span class="status-desc">Xác thực Truy cập Sân</span>
          </div>
          <div class="status-badge">LIVE</div>
        </div>
      </div>
    </div>

    <div class="form-panel">
      <div class="scroll-container">
        <div class="onboarding-box">
          <header class="veridian-header">
            <h1>Đăng ký Thành viên</h1>
            <p class="intro-p">Tạo tài khoản chính thức để đăng ký giải đấu và truy cập hệ thống quản lý.</p>
          </header>

          <transition name="fade">
            <div v-if="errorMessage" class="alert-box error">{{ errorMessage }}</div>
            <div v-else-if="successMessage" class="alert-box success">{{ successMessage }}</div>
          </transition>

          <form @submit.prevent="startRegistration" class="onboarding-form">
            <div class="form-row">
              <div class="field">
                <label>HỌ VÀ TÊN</label>
                <div class="input-wrap">
                  <el-icon class="icon"><User /></el-icon>
                  <input v-model="form.full_name" type="text" placeholder="Nhập họ và tên" required />
                </div>
              </div>
              <div class="field">
                <label>SỐ ĐIỆN THOẠI</label>
                <div class="input-wrap">
                  <el-icon class="icon"><Phone /></el-icon>
                  <input v-model="form.phone" type="tel" placeholder="09xxxxxx" required />
                </div>
              </div>
            </div>

            <div class="field">
              <label>EMAIL ĐỊNH DANH (NHẬN OTP)</label>
              <div class="input-wrap">
                <el-icon class="icon"><User /></el-icon>
                <input v-model="form.email" type="email" placeholder="email@vi-du.com" required />
              </div>
            </div>

            <div class="form-row">
              <div class="field">
                <label>KHU VỰC / TỈNH THÀNH</label>
                <div class="input-wrap">
                  <el-icon class="icon"><Location /></el-icon>
                  <select v-model="form.province" class="custom-native-select">
                    <option value="" disabled selected>Chọn Tỉnh / Thành</option>
                    <option v-for="p in vietnamProvinces" :key="p" :value="p">{{ p }}</option>
                  </select>
                </div>
              </div>
              <div class="field">
                <label>NGÀY SINH</label>
                <div class="input-wrap">
                  <el-icon class="icon"><Calendar /></el-icon>
                  <input v-model="form.date_of_birth" type="date" />
                </div>
              </div>
            </div>

            <div class="form-row">
              <div class="field">
                <label>GIỚI TÍNH</label>
                <div class="gender-radio-group">
                  <label class="radio-item" :class="{ active: form.gender === 'male' }">
                    <input type="radio" v-model="form.gender" value="male">
                    <span>NAM</span>
                  </label>
                  <label class="radio-item" :class="{ active: form.gender === 'female' }">
                    <input type="radio" v-model="form.gender" value="female">
                    <span>NỮ</span>
                  </label>
                </div>
              </div>
              <div class="field">
                <label>MẬT KHẨU TRUY CẬP</label>
                <div class="input-wrap">
                  <el-icon class="icon"><Lock /></el-icon>
                  <input
                    v-model="form.password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="••••••••"
                    required
                  />
                  <el-button link class="eye-btn" @click="showPassword = !showPassword">
                    <el-icon v-if="!showPassword"><View /></el-icon>
                    <el-icon v-else><Hide /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>

            <div class="form-options">
              <label class="remember-check">
                <input type="checkbox"> <span>Ghi nhớ phiên đăng nhập</span>
              </label>
              <router-link to="/login" class="login-redirect">Đã có tài khoản?</router-link>
            </div>

            <button type="submit" :disabled="isSendingOtp" class="btn-initialize-session">
              <span v-if="!isSendingOtp">KHỞI TẠO TÀI KHOẢN <el-icon><Check /></el-icon></span>
              <el-icon v-else class="is-loading"><Loading /></el-icon>
            </button>
          </form>

          <footer class="veridian-footer">
            <p class="system-version">HỆ THỐNG SAIGON TENNIS V4.2</p>
            <div class="footer-nav">
              <a href="#">HỖ TRỢ</a>
              <a href="#">TRẠNG THÁI MẠNG</a>
            </div>
          </footer>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.veridian-register-layout { display: flex; min-height: 100vh; background: #f7f9fa; color: #1a1c1e; font-family: Arial, sans-serif; overflow: hidden; }
.visual-panel { flex: 1.1; position: relative; background: linear-gradient(135deg, #abb1ab 0%, #878c87 100%); display: flex; align-items: center; justify-content: center; border-right: 1px solid rgba(0,0,0,0.05); }
.visual-panel::before { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent 49%, rgba(0,0,0,0.02) 50%, transparent 51%), linear-gradient(90deg, transparent 24%, rgba(0,0,0,0.02) 25%, transparent 26%); background-size: 200px 100%; }
.brand-content { position: relative; z-index: 10; width: 70%; }
.hero-text h2 { font-size: clamp(4rem, 7vw, 7.5rem); font-weight: 500; line-height: 0.85; font-style: italic; margin: 0; letter-spacing: -0.04em; }
.text-top { color: #fff; } .text-bottom { color: rgba(255,255,255,0.4); }
.kicker-line { display: flex; align-items: center; gap: 15px; margin-top: 2rem; }
.lime-bar { width: 50px; height: 3px; background: #c1ff72; }
.kicker-line p { font-size: 0.8rem; font-weight: 500; letter-spacing: 0.15em; color: #fff; }
.status-box { position: absolute; bottom: 60px; left: 60px; background: #fff; padding: 16px 24px; border-radius: 6px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
.status-inner { display: flex; align-items: center; gap: 30px; } .status-label-group { display: flex; flex-direction: column; }
.status-title { font-size: 0.6rem; font-weight: 500; color: #888; } .status-desc { font-size: 0.95rem; font-weight: 500; }
.status-badge { background: #4a6300; color: #c1ff72; padding: 4px 12px; border-radius: 4px; font-size: 0.75rem; font-weight: 500; }
.form-panel { flex: 1; background: #f7fbff; display: flex; }
.scroll-container { flex: 1; overflow-y: auto; display: flex; align-items: center; justify-content: center; padding: 60px 40px; }
.onboarding-box { width: 100%; max-width: 480px; }
.veridian-header { margin-bottom: 2.5rem; }
.pre-title { font-size: 0.75rem; font-weight: 500; letter-spacing: 0.12em; color: #839100; margin-bottom: 1rem; }
.veridian-header h1 { font-size: 2.8rem; font-weight: 500; letter-spacing: -0.03em; margin-bottom: 1rem; }
.intro-p { color: #6c7278; font-size: 0.95rem; line-height: 1.6; }
.onboarding-form { display: flex; flex-direction: column; gap: 1.5rem; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.field label { display: block; font-size: 0.65rem; font-weight: 500; color: #90a4ae; margin-bottom: 0.6rem; letter-spacing: 0.05em; }
.input-wrap { position: relative; display: flex; align-items: center; }
.input-wrap .icon { position: absolute; left: 14px; color: #b0bec5; font-size: 1.1rem; }
.input-wrap input, .custom-native-select { width: 100%; padding: 1.1rem 1rem 1.1rem 3.5rem; background: #e9eff2; border: none; border-radius: 4px; font-size: 0.95rem; color: #263238; outline: none; transition: all 0.2s; font-family: Arial, sans-serif; }
.input-wrap input:focus { background: #fff; box-shadow: 0 0 0 2px #c1ff72; }
.gender-radio-group { display: flex; gap: 10px; }
.radio-item { flex: 1; background: #e9eff2; padding: 1.1rem; border-radius: 4px; text-align: center; font-size: 0.8rem; font-weight: 500; color: #90a4ae; cursor: pointer; transition: all 0.2s; }
.radio-item input { display: none; }
.radio-item.active { background: #fff; color: #839100; box-shadow: inset 0 0 0 2px #c1ff72; }
.form-options { display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; }
.remember-check { display: flex; align-items: center; gap: 8px; color: #90a4ae; }
.login-redirect { color: #839100; text-decoration: none; font-weight: 500; }
.btn-initialize-session { margin-top: 1rem; padding: 1.2rem; border: none; border-radius: 4px; background: linear-gradient(90deg, #4a6300 0%, #a4d100 100%); color: #fff; font-size: 1rem; font-weight: 500; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 12px; transition: all 0.3s; font-family: Arial, sans-serif; }
.btn-initialize-session:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(74, 99, 0, 0.2); }
.veridian-footer { margin-top: 4rem; padding-top: 2rem; border-top: 1px solid #e0e6ed; text-align: center; }
.system-version { font-size: 0.6rem; font-weight: 500; color: #cfd8dc; letter-spacing: 0.1em; margin-bottom: 2rem; }
.footer-nav { display: flex; justify-content: center; gap: 40px; }
.footer-nav a { font-size: 0.75rem; font-weight: 400; color: #90a4ae; text-decoration: none; letter-spacing: 0.03em; }
.alert-box { padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem; font-size: 0.85rem; font-weight: 600; }
.alert-box.error { background: #ffebee; color: #c62828; }
.alert-box.success { background: #e8f5e9; color: #2e7d32; }
@media (max-width: 1024px) { .visual-panel { display: none; } }
@media (max-width: 640px) { .form-row { grid-template-columns: 1fr; } }
</style>
