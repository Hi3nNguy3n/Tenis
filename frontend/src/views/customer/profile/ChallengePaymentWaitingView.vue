<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '../../../services/apiClient'
import { useAuthStore } from '../../../stores/auth'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const challengeId = route.params.id

const timeLeft = ref(600) 
const challenge = ref(null)
const timer = ref(null)
const polling = ref(null)

const formattedTime = computed(() => {
  const minutes = Math.floor(timeLeft.value / 60)
  const seconds = timeLeft.value % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})

const fetchStatus = async () => {
  try {
    const data = await apiClient.get(`/api/challenges/my-challenges`)
    const current = data.find(c => c.id === parseInt(challengeId))
    if (current) {
      challenge.value = current
      
      if (current.status === 'paid') {
        router.push({ name: 'profile' }) // Hoặc trang thành công
      } else if (current.status === 'rejected') {
        router.push({ name: 'payment-failure' })
      }
    }
  } catch (err) {
    console.error('Lỗi khi kiểm tra trạng thái kèo:', err)
  }
}

const startCountdown = () => {
  timer.value = setInterval(() => {
    if (timeLeft.value > 0) timeLeft.value--
    else {
      clearInterval(timer.value)
      router.push({ name: 'payment-failure' })
    }
  }, 1000)
}

const simulatePaymentSuccess = async () => {
  try {
    // Gọi API callback với challengeId thay vì regId
    await apiClient.get(`/api/payments/vnpay-callback`, {
      params: { challengeId: challengeId, status: 'success' }
    })
    alert("Thanh toán kèo thách đấu giả lập thành công!")
    fetchStatus()
  } catch (err) {
    alert("Lỗi giả lập: " + err.message)
  }
}

onMounted(async () => {
  // 1. Nạp lại thông tin đăng nhập từ bộ nhớ
  await authStore.hydrate() 
  
  // 2. Nếu không thấy Token, đuổi ra trang login (Tránh lỗi 401 liên tục)
  if (!authStore.accessToken) {
    ElMessage.error('Phiên làm việc hết hạn, vui lòng đăng nhập lại.')
    return router.push('/login')
  }
  
  // 3. Đã có Token thì mới bắt đầu chạy
  fetchStatus()
  startCountdown()
  polling.value = setInterval(fetchStatus, 5000)
})

onUnmounted(() => {
  clearInterval(timer.value)
  clearInterval(polling.value)
})
</script>

<template>
  <div class="payment-waiting container">
    <div class="waiting-card">
      <div class="icon-section">
        <div class="pulse-ring"></div>
        <div class="icon">🎾</div>
      </div>

      <h1>Xác nhận kèo thách đấu</h1>
      <p class="description">
        Kèo thách đấu của bạn đã được chấp nhận. Vui lòng thanh toán phí sân để hệ thống chuyển thông tin cho Ban quản trị gán lịch thi đấu.
      </p>

      <div class="countdown-timer">
        <span class="label">Thời gian thanh toán còn lại:</span>
        <span class="time">{{ formattedTime }}</span>
      </div>

      <div class="action-section">
        <button class="btn-check" @click="fetchStatus">Tôi đã thanh toán, kiểm tra ngay</button>
        <button class="simulate-btn" @click="simulatePaymentSuccess">🛠️ Giả lập thanh toán kèo (Test)</button>
        <button class="btn-secondary" @click="router.push('/profile')">Quay lại hồ sơ</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Thay thế dòng @import bằng toàn bộ nội dung CSS ở Cách 1 vào đây */
.payment-waiting {
  padding: 8rem 0;
  display: flex;
  justify-content: center;
  background: #f8fafc;
}
/* payment-style-shared.css */
.payment-waiting {
  padding: 8rem 0;
  display: flex;
  justify-content: center;
  background: #f8fafc;
  min-height: 100vh;
}

.waiting-card {
  max-width: 500px;
  width: 100%;
  background: white;
  padding: 3rem;
  border-radius: 30px;
  text-align: center;
  box-shadow: 0 20px 50px rgba(0,0,0,0.05);
}

.icon-section {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto 2rem;
}

.pulse-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #15803d;
  opacity: 0.2;
  animation: pulse 2s infinite;
}

.icon {
  position: relative;
  font-size: 3rem;
  line-height: 100px;
}

h1 { color: #1e293b; font-size: 1.8rem; margin-bottom: 1rem; }
.description { color: #64748b; margin-bottom: 2rem; line-height: 1.6; }

.countdown-timer {
  background: #f1f5f9;
  padding: 1.5rem;
  border-radius: 16px;
  margin-bottom: 2rem;
}

.time {
  display: block;
  font-size: 3rem;
  font-weight: 800;
  color: #15803d;
  font-family: monospace;
}

.action-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-check, .simulate-btn, .btn-secondary {
  padding: 1rem;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  border: none;
  transition: 0.2s;
}

.btn-check { background: #15803d; color: white; }
.simulate-btn { background: #f59e0b; color: white; }
.btn-secondary { background: #e2e8f0; color: #475569; }

@keyframes pulse {
  0% { transform: scale(1); opacity: 0.4; }
  100% { transform: scale(1.5); opacity: 0; }
}
</style>