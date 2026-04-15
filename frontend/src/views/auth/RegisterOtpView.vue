<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const SEND_OTP_ENDPOINT = `${API_BASE_URL}/api/auth/send-otp`
const PENDING_REGISTER_STORAGE_KEY = 'saigon_tennis_pending_register'

const router = useRouter()

const isSendingOtp = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const showPassword = ref(false)

// Danh sách 34 Tỉnh/Thành phố Việt Nam (Cập nhật mới nhất sau sáp nhập)
const vietnamProvinces = [
  "An Giang", "Bắc Ninh", "Cà Mau", "Cao Bằng", "Đắk Lắk", 
  "Điện Biên", "Đồng Nai", "Đồng Tháp", "Gia Lai", "Hà Tĩnh", 
  "Hưng Yên", "Khánh Hòa", "Lai Châu", "Lâm Đồng", "Lạng Sơn", 
  "Lào Cai", "Nghệ An", "Ninh Bình", "Phú Thọ", "Quảng Ngãi", 
  "Quảng Ninh", "Quảng Trị", "Sơn La", "Tây Ninh", "Thái Nguyên", 
  "Thanh Hóa", "TP Cần Thơ", "TP Đà Nẵng", "TP Hà Nội", "TP Hải Phòng", 
  "TP Hồ Chí Minh", "TP Huế", "Tuyên Quang", "Vĩnh Long"
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

const passwordStrengthLabel = () => {
  if (form.value.password.length >= 10) {
    return 'Độ mạnh mật khẩu: Tốt'
  }

  if (form.value.password.length >= 6) {
    return 'Độ mạnh mật khẩu: Trung bình'
  }

  return 'Độ mạnh mật khẩu: Yếu'
}

const startRegistration = async () => {
  clearMessages()

  if (!validateForm()) {
    return
  }

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
        'Không thể gửi mã OTP. Vui lòng kiểm tra email và thử lại.'
      )
      return
    }

    persistPendingRegistration()
    successMessage.value = 'Mã OTP đã được gửi. Đang chuyển sang bước xác thực...'
    router.push({ name: 'register-otp-verify' })
  } catch {
    errorMessage.value = 'Không kết nối được tới backend. Hãy kiểm tra API server và thử lại.'
  } finally {
    isSendingOtp.value = false
  }
}
</script>

<template>
  <div class="register-page">
    <div class="ghost-lines"></div>

    <header class="register-header">
      <div class="brand-mark">Saigon Tennis</div>
    </header>

    <main class="register-main">
      <section class="register-card">
        <div class="court-decor" aria-hidden="true">
          <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="10" width="80" height="80" fill="none" stroke="currentColor" stroke-width="2" />
            <line x1="10" y1="50" x2="90" y2="50" stroke="currentColor" stroke-width="2" />
            <line x1="50" y1="10" x2="50" y2="90" stroke="currentColor" stroke-width="2" />
          </svg>
        </div>

        <header class="register-copy">
          <p class="copy-kicker">Member Onboarding</p>
          <h1 id="register-otp-heading">Tạo tài khoản</h1>
          <p>
            Gia nhập cộng đồng Saigon Tennis. Chỉ cần nhập thông tin đăng ký, hệ thống sẽ gửi OTP
            qua email để xác thực ở bước tiếp theo.
          </p>
        </header>

        <div v-if="errorMessage" class="feedback feedback-error" role="alert">
          {{ errorMessage }}
        </div>

        <div v-if="successMessage" class="feedback feedback-success" role="status">
          {{ successMessage }}
        </div>

        <form class="register-form" @submit.prevent="startRegistration">
          <div class="form-grid">
            <label class="field-group" for="register-full-name">
              <span>Họ và tên</span>
              <input
                id="register-full-name"
                v-model="form.full_name"
                type="text"
                placeholder="Nguyễn Văn A"
                autocomplete="name"
                required
              />
            </label>

            <label class="field-group" for="register-phone">
              <span>Số điện thoại</span>
              <input
                id="register-phone"
                v-model="form.phone"
                type="tel"
                placeholder="09xx..."
                required
              />
            </label>
          </div>

          <label class="field-group" for="register-email">
            <span>Email</span>
            <div class="input-shell">
              <input
                id="register-email"
                v-model="form.email"
                type="email"
                placeholder="name@example.com"
                autocomplete="email"
                required
              />
            </div>
          </label>

          <div class="form-grid">
            <label class="field-group" for="register-province">
              <span>Tỉnh / Thành</span>
              <el-select 
                id="register-province"
                v-model="form.province" 
                placeholder="Chọn Tỉnh / Thành" 
                filterable 
                style="width: 100%; border-radius: 12px;"
                size="large"
              >
                <el-option 
                  v-for="province in vietnamProvinces" 
                  :key="province" 
                  :label="province" 
                  :value="province" 
                />
              </el-select>
            </label>
            <label class="field-group" for="register-dob">
              <span>Ngày sinh</span>
              <input
                id="register-dob"
                v-model="form.date_of_birth"
                type="date"
              />
            </label>
          </div>

          <div class="form-grid">
            <label class="field-group" for="register-gender">
              <span>Giới tính</span>
              <select id="register-gender" v-model="form.gender" class="custom-select">
                <option value="male">Nam</option>
                <option value="female">Nữ</option>
                <option value="other">Khác</option>
              </select>
            </label>
            
            <div class="field-group empty-slot" aria-hidden="true"></div>
          </div>

          <label class="field-group" for="register-password">
            <span>Mật khẩu</span>
            <div class="input-shell with-action">
              <input
                id="register-password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                autocomplete="new-password"
                minlength="6"
                required
              />
              <button
                id="toggle-register-password"
                class="toggle-password-btn"
                type="button"
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? 'Ẩn' : 'Hiện' }}
              </button>
            </div>
            <p class="password-note">{{ passwordStrengthLabel() }}</p>
          </label>

          <button
            id="register-submit-button"
            class="submit-button"
            type="submit"
            :disabled="isSendingOtp"
          >
            {{ isSendingOtp ? 'Đang gửi OTP...' : 'Đăng ký' }}
          </button>

          <div class="register-footer">
            <p>
              Đã có tài khoản?
              <RouterLink id="go-login-link" to="/login">Đăng nhập</RouterLink>
            </p>
          </div>
        </form>
      </section>
    </main>

    <div class="floating-image floating-image-left" aria-hidden="true"></div>
    <div class="floating-image floating-image-right" aria-hidden="true"></div>

    <footer class="register-footer-bar">
      <span>© 2026 SAIGON TENNIS CLUB</span>
      <div>
        <span>Privacy</span>
        <span>Terms</span>
        <span>Support</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.register-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(120, 216, 186, 0.14), transparent 26%),
    linear-gradient(180deg, #f8f9f9 0%, #eef1f1 100%);
  color: #191c1c;
}

.ghost-lines {
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(45deg, transparent 48%, rgba(189, 201, 195, 0.12) 49%, rgba(189, 201, 195, 0.12) 51%, transparent 52%),
    linear-gradient(-45deg, transparent 48%, rgba(189, 201, 195, 0.12) 49%, rgba(189, 201, 195, 0.12) 51%, transparent 52%);
  background-size: 60px 60px;
  pointer-events: none;
}

.register-header,
.register-main,
.register-footer-bar {
  position: relative;
  z-index: 2;
}

.register-header {
  padding: 32px 32px 0;
}

.brand-mark {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: #006953;
}

.register-main {
  min-height: calc(100vh - 164px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.register-card {
  position: relative;
  width: min(100%, 500px);
  padding: 40px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 24px 60px rgba(25, 28, 28, 0.08);
  overflow: hidden;
}

.court-decor {
  position: absolute;
  top: 0;
  right: 0;
  width: 132px;
  height: 132px;
  color: rgba(0, 105, 83, 0.12);
}

.register-copy {
  position: relative;
  z-index: 1;
  margin-bottom: 28px;
}

.copy-kicker {
  margin-bottom: 10px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #6e7a74;
}

.register-copy h1 {
  margin-bottom: 12px;
  font-size: 2.5rem;
  line-height: 1.08;
  letter-spacing: -0.04em;
}

.register-copy p {
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
  border-color: rgba(186, 26, 26, 0.14);
  color: #93000a;
}

.feedback-success {
  background: rgba(19, 132, 106, 0.1);
  border-color: rgba(19, 132, 106, 0.16);
  color: #006953;
}

.register-form {
  display: grid;
  gap: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.custom-select {
  width: 100%;
  min-height: 58px;
  border: none;
  outline: none;
  border-radius: 18px;
  background: #f3f4f4;
  padding: 0 14px;
  font: inherit;
  color: #191c1c;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236e7a74' d='M10.293 3.293 6 7.586 1.707 3.293A1 1 0 0 0 .293 4.707l5 5a1 1 0 0 0 1.414 0l5-5a1 1 0 1 0-1.414-1.414z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 18px center;
}

.field-group {
  display: grid;
  gap: 8px;
}

.field-group > span {
  margin-left: 4px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #3e4945;
}

.field-group input {
  width: 100%;
  min-height: 58px;
  border: none;
  outline: none;
  border-radius: 18px;
  background: #f3f4f4;
  padding: 0 18px;
  font: inherit;
  color: #191c1c;
}

.field-group input::placeholder {
  color: #8a9591;
}

.input-shell {
  position: relative;
}

.input-shell input {
  padding-right: 52px;
  border: 1px solid transparent;
  transition: 0.25s ease;
}

.input-shell input:focus,
.input-shell.with-action:focus-within input {
  border-color: rgba(0, 105, 83, 0.24);
  box-shadow: 0 0 0 4px rgba(0, 105, 83, 0.08);
}

.input-shell-error input {
  border-color: rgba(186, 26, 26, 0.24);
}

.input-status {
  position: absolute;
  top: 50%;
  right: 18px;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: rgba(186, 26, 26, 0.12);
  color: #ba1a1a;
  font-size: 0.8rem;
  font-weight: 800;
}

.with-action input {
  padding-right: 78px;
}

.toggle-password-btn {
  position: absolute;
  top: 50%;
  right: 14px;
  transform: translateY(-50%);
  border: none;
  background: transparent;
  color: #6e7a74;
  font: inherit;
  font-size: 0.86rem;
  font-weight: 700;
  cursor: pointer;
}

.password-strength {
  display: flex;
  gap: 6px;
  padding: 0 4px;
}

.password-strength span {
  height: 4px;
  flex: 1;
  border-radius: 999px;
  background: rgba(110, 122, 116, 0.18);
  transition: 0.25s ease;
}

.password-strength span.active {
  background: #13846a;
}

.password-note {
  padding: 0 4px;
  font-size: 0.78rem;
  color: #4e6073;
}

.submit-button {
  min-height: 62px;
  margin-top: 6px;
  border: none;
  border-radius: 20px;
  background: linear-gradient(135deg, #006953 0%, #13846a 100%);
  color: #ffffff;
  font: inherit;
  font-weight: 800;
  font-size: 1rem;
  cursor: pointer;
  box-shadow: 0 18px 32px rgba(0, 105, 83, 0.18);
  transition: transform 0.25s ease, box-shadow 0.25s ease, opacity 0.25s ease;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-1px) scale(1.01);
  box-shadow: 0 22px 38px rgba(0, 105, 83, 0.24);
}

.submit-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.register-footer {
  padding-top: 6px;
  text-align: center;
  color: #4e6073;
}

.register-footer a {
  margin-left: 6px;
  color: #006953;
  font-weight: 800;
}

.floating-image {
  position: fixed;
  z-index: 1;
  overflow: hidden;
  pointer-events: none;
  box-shadow: 0 28px 60px rgba(25, 28, 28, 0.08);
}

.floating-image::before {
  content: '';
  position: absolute;
  inset: 0;
}

.floating-image-left {
  left: 80px;
  bottom: 100px;
  width: 280px;
  height: 380px;
  border-radius: 26px;
  transform: rotate(-3deg);
}

.floating-image-left::before {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0)),
    linear-gradient(135deg, rgba(0, 105, 83, 0.28), rgba(19, 132, 106, 0.06)),
    radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.22), transparent 20%),
    linear-gradient(180deg, #5e706c 0%, #2d403b 100%);
  opacity: 0.34;
  filter: grayscale(1);
}

.floating-image-right {
  top: 168px;
  right: 48px;
  width: 220px;
  height: 220px;
  border-radius: 999px;
  border: 10px solid rgba(255, 255, 255, 0.8);
}

.floating-image-right::before {
  background:
    radial-gradient(circle at 36% 34%, rgba(255, 255, 255, 0.34), transparent 14%),
    radial-gradient(circle at center, #dff77b 0%, #abd64f 58%, #7ea220 100%);
}

.register-footer-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 0 32px 24px;
  color: rgba(110, 122, 116, 0.9);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.register-footer-bar div {
  display: flex;
  gap: 24px;
}

@media (max-width: 1200px) {
  .floating-image {
    display: none;
  }
}

@media (max-width: 640px) {
  .register-header {
    padding: 24px 20px 0;
  }

  .register-main {
    min-height: auto;
    padding: 20px;
  }

  .register-card {
    padding: 28px 20px;
    border-radius: 24px;
  }

  .register-copy h1 {
    font-size: 2rem;
  }

  .register-footer-bar {
    flex-direction: column;
    padding: 0 20px 20px;
    letter-spacing: 0.12em;
  }

  .register-footer-bar div {
    gap: 14px;
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
