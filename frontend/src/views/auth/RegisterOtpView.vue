<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authService } from '../../services/authService'

const router = useRouter()
const loading = ref(false)
const showPassword = ref(false)

const form = ref({
  full_name: '',
  email: '',
  phone: '',
  password: '',
  province: '',
  date_of_birth: '',
  gender: 'male',
  play_hand: '',
  account_type: 'user',
})

const handleNext = async () => {
  if (!form.value.email || !form.value.full_name || !form.value.password) {
    ElMessage.warning('Vui lòng điền đầy đủ họ tên, email và mật khẩu.')
    return
  }
  if (!form.value.play_hand) {
    ElMessage.warning('Thiếu phần tay thuận.')
    return
  }

  loading.value = true
  try {
    sessionStorage.setItem('pending_registration', JSON.stringify({ ...form.value }))
    await authService.sendOtp(form.value.email)
    ElMessage.success(`Mã OTP đã được gửi đến ${form.value.email}`)
    router.push({ name: 'verify-register-otp' })
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Không thể gửi OTP.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-page">
    <div class="register-card">
      <div class="card-side">
        <h2>Saigon Tennis</h2>
        <p>Đăng ký tài khoản và xác thực OTP.</p>
      </div>
      <div class="card-main">
        <h1>Đăng ký thành viên</h1>

        <div class="field">
          <label>Họ và tên</label>
          <input v-model="form.full_name" placeholder="Nguyễn Văn A" />
        </div>

        <div class="field">
          <label>Email</label>
          <input v-model="form.email" type="email" placeholder="example@email.com" />
        </div>

        <div class="field">
          <label>Số điện thoại</label>
          <input v-model="form.phone" placeholder="090..." />
        </div>

        <div class="field">
          <label>Tỉnh / thành phố</label>
          <input v-model="form.province" placeholder="TP. Hồ Chí Minh" />
        </div>

        <div class="field">
          <label>Ngày sinh</label>
          <input v-model="form.date_of_birth" type="date" />
        </div>

        <div class="field">
          <label>Giới tính</label>
          <div class="radio-row">
            <label><input type="radio" v-model="form.gender" value="male" /> Nam</label>
            <label><input type="radio" v-model="form.gender" value="female" /> Nữ</label>
          </div>
        </div>

        <div class="field">
          <label>Tay thuận</label>
          <div class="radio-row">
            <label><input type="radio" v-model="form.play_hand" value="right" /> Phải</label>
            <label><input type="radio" v-model="form.play_hand" value="left" /> Trái</label>
            <label><input type="radio" v-model="form.play_hand" value="both" /> Cả hai</label>
          </div>
        </div>

        <div class="field">
          <label>Mật khẩu</label>
          <div class="password-row">
            <input v-model="form.password" :type="showPassword ? 'text' : 'password'" placeholder="••••••••" />
            <button type="button" @click="showPassword = !showPassword">{{ showPassword ? 'Ẩn' : 'Hiện' }}</button>
          </div>
        </div>

        <button class="submit-btn" :disabled="loading" @click="handleNext">
          {{ loading ? 'Đang gửi...' : 'Khởi tạo tài khoản' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-page { min-height: 100vh; display: grid; place-items: center; background: #f1f5f9; padding: 20px; }
.register-card { width: min(100%, 980px); display: grid; grid-template-columns: 320px 1fr; background: #fff; border-radius: 20px; overflow: hidden; }
.card-side { padding: 32px; background: linear-gradient(180deg, #146250, #0f4d3f); color: #fff; }
.card-main { padding: 32px; display: grid; gap: 14px; }
.field { display: grid; gap: 6px; }
.field input { padding: 12px 14px; border: 1px solid #dbe4ea; border-radius: 10px; }
.radio-row { display: flex; gap: 16px; flex-wrap: wrap; }
.password-row { display: flex; gap: 10px; }
.password-row input { flex: 1; }
.submit-btn { padding: 14px; border: 0; border-radius: 12px; background: #146250; color: #fff; font-weight: 700; }
@media (max-width: 900px) { .register-card { grid-template-columns: 1fr; } }
</style>
