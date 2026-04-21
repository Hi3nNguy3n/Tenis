<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authService } from '../../services/authService'

const router = useRouter()
const loading = ref(false)
const emailDisplay = ref('')
const otp = ref(['', '', '', '', '', ''])
const form = ref({})
const otpInputs = ref([])

onMounted(() => {
  const pending = JSON.parse(sessionStorage.getItem('pending_registration') || 'null')
  if (!pending) {
    ElMessage.error('Không tìm thấy phiên đăng ký.')
    router.push({ name: 'register-otp' })
    return
  }
  form.value = pending
  emailDisplay.value = pending.email || ''
})

const handleInput = (index, event) => {
  if (event.target.value && index < otpInputs.value.length - 1) {
    otpInputs.value[index + 1]?.focus()
  }
}

const registerAccount = async () => {
  const otpCode = otp.value.join('')
  if (otpCode.length !== 6) {
    ElMessage.warning('Vui lòng nhập đủ 6 số OTP.')
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

    ElMessage.success('Đăng ký thành công.')
    sessionStorage.removeItem('pending_registration')
    router.push({ name: 'login' })
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Xác nhận OTP thất bại.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="verify-page">
    <div class="verify-card">
      <h1>Xác thực tài khoản</h1>
      <p>OTP đã gửi tới: <strong>{{ emailDisplay }}</strong></p>

      <div class="otp-row">
        <input
          v-for="(_, index) in otp"
          :key="index"
          :ref="el => (otpInputs[index] = el)"
          v-model="otp[index]"
          maxlength="1"
          inputmode="numeric"
          @input="handleInput(index, $event)"
        />
      </div>

      <button class="submit-btn" :disabled="loading" @click="registerAccount">
        {{ loading ? 'Đang xác nhận...' : 'Xác nhận & đăng ký' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.verify-page { min-height: 100vh; display: grid; place-items: center; background: #f1f5f9; padding: 20px; }
.verify-card { width: min(100%, 480px); background: #fff; border-radius: 20px; padding: 32px; display: grid; gap: 16px; }
.otp-row { display: flex; gap: 10px; justify-content: center; }
.otp-row input { width: 48px; height: 56px; text-align: center; font-size: 1.4rem; border: 1px solid #dbe4ea; border-radius: 10px; }
.submit-btn { padding: 14px; border: 0; border-radius: 12px; background: #146250; color: #fff; font-weight: 700; }
</style>
