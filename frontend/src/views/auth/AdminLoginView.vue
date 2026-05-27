<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { User, Lock, View, Hide, Warning } from '@element-plus/icons-vue'
import { getApiBaseUrl } from '../../utils/apiUrls'

const API_BASE_URL = getApiBaseUrl()
const LOGIN_ENDPOINT = `${API_BASE_URL}/api/auth/login`

const router = useRouter()
const authStore = useAuthStore()

const isLoggingIn = ref(false)
const errorMessage = ref('')
const showPassword = ref(false)

const form = ref({
  email: '',
  password: '',
})

onMounted(() => {
  if (authStore.isAuthenticated && authStore.isAdmin) {
    router.push('/admin')
  }
})

const login = async () => {
  errorMessage.value = ''
  if (!form.value.email.trim() || !form.value.password) {
    errorMessage.value = 'Vui lòng nhập đầy đủ thông tin.'
    return
  }

  isLoggingIn.value = true

  try {
    const response = await fetch(LOGIN_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })

    if (!response.ok) {
      const errorData = await response.json()
      errorMessage.value = errorData.detail || 'Đăng nhập thất bại. Sai tài khoản hoặc mật khẩu.'
      return
    }

    const data = await response.json()

    if (data.account_type !== 'admin') {
      errorMessage.value = 'Lỗi: Bạn không có quyền Quản trị.'
      return
    }

    authStore.setSession({
      accessToken: data.access_token,
      tokenType: data.token_type,
      user: {
        email: form.value.email.trim(),
        full_name: data.full_name,
        user_id: data.user_id,
        role_id: data.role_id,
        account_type: data.account_type,
      },
    })

    router.push('/admin')
  } catch {
    errorMessage.value = 'Không thể kết nối tới máy chủ.'
  } finally {
    isLoggingIn.value = false
  }
}
</script>

<template>
  <div class="admin-login-layout">
    <div class="visual-panel">
      <div class="background-overlay"></div>
      <div class="brand-assets">
        <div class="typography-hero">
          <h2 class="text-court">ĐIỀU HÀNH</h2>
          <h2 class="text-director">HỆ THỐNG</h2>
        </div>
        <div class="motto-box">
          <span class="accent-line"></span>
          <p class="motto-text">QUẢN TRỊ TẬP TRUNG</p>
        </div>
      </div>
      <div class="court-image"></div>
    </div>

    <div class="form-panel">
      <div class="form-scroll">
        <div class="login-core">
          <header class="form-intro">
            <h1>Truy cập Hệ thống</h1>
            <p>Bảng điều khiển dành cho Quản trị viên</p>
          </header>

          <transition name="shake">
            <div v-if="errorMessage" class="error-strip">
              <el-icon><Warning /></el-icon>
              <span>{{ errorMessage }}</span>
            </div>
          </transition>

          <form @submit.prevent="login" class="terminal-auth-form">
            <div class="form-field">
              <label>ĐỊNH DANH QUẢN TRỊ (EMAIL)</label>
              <div class="input-container">
                <el-icon class="field-icon"><User /></el-icon>
                <input v-model="form.email" type="email" placeholder="Email đăng nhập" required />
              </div>
            </div>

            <div class="form-field">
              <label>MẬT MÃ BẢO MẬT</label>
              <div class="input-container">
                <el-icon class="field-icon"><Lock /></el-icon>
                <input
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="••••••••"
                  required
                />
                <div class="eye-toggle" @click="showPassword = !showPassword">
                  <el-icon v-if="!showPassword"><View /></el-icon>
                  <el-icon v-else><Hide /></el-icon>
                </div>
              </div>
            </div>

            <div class="form-utilities">
              <label class="check-station">
                <input type="checkbox" />
                <span>Ghi nhớ phiên làm việc</span>
              </label>
              <a href="#" class="key-reset">Quên mật mã?</a>
            </div>

            <button type="submit" :disabled="isLoggingIn" class="btn-init">
              <span v-if="!isLoggingIn">KHỞI TẠO PHIÊN LÀM VIỆC</span>
              <span v-else class="loading-spinner"></span>
            </button>
          </form>

          <footer class="form-bottom">
            <div class="encryption-notice">
              <el-icon><Lock /></el-icon>
              <span>DỮ LIỆU ĐƯỢC MÃ HÓA ĐẦU CUỐI - Saigontennistours</span>
            </div>
            <router-link to="/" class="public-exit-btn">Quay lại trang chủ</router-link>
          </footer>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-login-layout {
  display: flex;
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
  font-family: Arial, sans-serif;
  overflow: hidden;
}
.visual-panel {
  flex: 1.3;
  position: relative;
  overflow: hidden;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.court-image {
  position: absolute;
  inset: 0;
  background-image: url('https://images.unsplash.com/photo-1595435064219-510ccbdb4975?q=80&w=2000');
  background-size: cover;
  background-position: center;
  opacity: 0.35;
  filter: grayscale(100%);
  z-index: 1;
}
.background-overlay { position: absolute; inset: 0; background: radial-gradient(circle at center, transparent 20%, #0a0a0a 90%); z-index: 2; }
.brand-assets { position: relative; z-index: 3; width: 80%; }
.typography-hero h2 { font-family: Arial, sans-serif; font-size: clamp(4rem, 8vw, 9rem); font-weight: 500; line-height: 0.82; font-style: italic; margin: 0; letter-spacing: normal; }
.text-court { color: #d1d5db; }
.text-director { color: #16a34a; }
.motto-box { display: flex; align-items: center; gap: 20px; margin-top: 3rem; }
.accent-line { width: 44px; height: 2px; background: #16a34a; }
.motto-text { font-size: clamp(0.7rem, 1.2vw, 1rem); letter-spacing: 0.5em; font-weight: 500; color: rgba(255, 255, 255, 0.7); margin: 0; }
.form-panel { flex: 1; background: #111; display: flex; flex-direction: column; }
.form-scroll { flex: 1; overflow-y: auto; display: flex; align-items: center; justify-content: center; padding: 60px 40px; }
.login-core { width: 100%; max-width: 420px; }
.form-intro { margin-bottom: 3.5rem; }
.form-intro h1 { font-size: 2.4rem; font-weight: 500; letter-spacing: -0.02em; margin-bottom: 0.5rem; color: #fff; }
.form-intro p { color: rgba(255, 255, 255, 0.4); font-size: 0.95rem; }
.terminal-auth-form { display: flex; flex-direction: column; gap: 1.75rem; }
.form-field label { display: block; font-size: 0.7rem; font-weight: 500; color: rgba(255, 255, 255, 0.3); margin-bottom: 0.75rem; letter-spacing: 0.12em; }
.input-container { position: relative; display: flex; align-items: center; background: #1a1a1a; border: 1px solid #262626; border-radius: 6px; transition: all 0.2s ease; }
.input-container:focus-within { border-color: #16a34a; box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.15); }
.input-container input { width: 100%; padding: 1.1rem 1rem 1.1rem 3.5rem; background: transparent; border: none; color: #fff; font-size: 1rem; outline: none; }
.field-icon { position: absolute; left: 18px; font-size: 1.2rem; color: #404040; }
.eye-toggle { position: absolute; right: 18px; color: #404040; cursor: pointer; transition: color 0.2s; }
.eye-toggle:hover { color: #16a34a; }
.form-utilities { display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; margin-top: 0.25rem; }
.check-station { display: flex; align-items: center; gap: 10px; color: rgba(255, 255, 255, 0.5); cursor: pointer; }
.check-station input { width: 16px; height: 16px; }
.key-reset { color: #16a34a; text-decoration: none; font-weight: 500; }
.btn-init { margin-top: 1.5rem; padding: 1.25rem; background: #16a34a; color: #fff; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; letter-spacing: 0.08em; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); font-size: 0.95rem; }
.btn-init:hover:not(:disabled) { background: #15803d; transform: translateY(-2px); box-shadow: 0 10px 20px rgba(22, 163, 74, 0.2); }
.btn-init:disabled { opacity: 0.5; cursor: not-allowed; }
.error-strip { background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 14px 18px; color: #fca5a5; font-size: 0.9rem; display: flex; align-items: center; gap: 12px; margin-bottom: 2rem; border-radius: 4px; }
.form-bottom { margin-top: 5rem; text-align: center; }
.encryption-notice { font-size: 0.65rem; color: #404040; display: flex; align-items: center; justify-content: center; gap: 10px; letter-spacing: 0.1em; margin-bottom: 2rem; text-transform: uppercase; }
.public-exit-btn { font-size: 0.85rem; color: #525252; text-decoration: none; transition: color 0.2s; }
.public-exit-btn:hover { color: #fff; }
.loading-spinner { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.3); border-bottom-color: #fff; border-radius: 50%; display: inline-block; animation: rotate 0.8s linear infinite; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-5px); } 75% { transform: translateX(5px); } }
.shake-enter-active { animation: shake 0.3s; }
@media (max-width: 1080px) { .visual-panel { display: none; } }
</style>
