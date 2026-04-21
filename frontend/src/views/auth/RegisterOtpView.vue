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
  // Xóa khoảng trắng thừa 2 đầu
  form.value.full_name = form.value.full_name?.trim() || ''
  form.value.phone = form.value.phone?.trim() || ''

  // 1. Kiểm tra rỗng
  if (!form.value.full_name) return ElMessage.warning('Họ và tên không được để trống.')
  if (!form.value.email) return ElMessage.warning('Email không được để trống.')
  if (!form.value.phone) return ElMessage.warning('Số điện thoại không được để trống.')
  if (!form.value.password) return ElMessage.warning('Mật khẩu không được để trống.')

  // 2. Kiểm tra định dạng Email
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(form.value.email)) return ElMessage.warning('Email không đúng định dạng.')

  // 3. Kiểm tra định dạng Số điện thoại (Chỉ cho nhập 10 số, bắt đầu bằng 0)
  const phoneRegex = /^0\d{9}$/
  if (!phoneRegex.test(form.value.phone)) {
    return ElMessage.warning('Số điện thoại không hợp lệ! Vui lòng nhập 10 chữ số và bắt đầu bằng số 0.')
  }

  // 4. Kiểm tra độ dài mật khẩu
  if (form.value.password.length < 6) return ElMessage.warning('Mật khẩu quá ngắn, vui lòng nhập ít nhất 6 ký tự.')

  // 5. Kiểm tra tay thuận
  if (!form.value.play_hand) return ElMessage.warning('Vui lòng chọn tay thuận để hệ thống phân loại trình độ.')

  loading.value = true
  let isSuccess = false // Cờ đánh dấu API gọi thành công

  try {
    sessionStorage.setItem('pending_registration', JSON.stringify({ ...form.value }))
    await authService.sendOtp(form.value.email)
    isSuccess = true // Đánh dấu là đã gửi mail và DB nhận ok
  } catch (error) {
    // Chỗ này giờ CHỈ bắt lỗi thực sự từ Backend (ví dụ: Trùng email)
    ElMessage.error(error.response?.data?.detail || 'Lỗi từ máy chủ khi gửi OTP.')
  } finally {
    loading.value = false
  }

  // Nếu gửi mail thành công thì mới hiển thị màu xanh và chuyển trang
  if (isSuccess) {
    ElMessage.success(`Mã OTP đã được gửi đến ${form.value.email}`)
    
    // Gọi đúng tên 'register-otp-verify' đã khai báo trong index.js
    router.push({ name: 'register-otp-verify' }).catch(err => {
        console.error("Lỗi chuyển trang:", err)
    })
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
