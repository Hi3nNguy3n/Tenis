<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '../../../services/apiClient'

const route = useRoute()
const router = useRouter()
const registrationId = route.params.id

const timeLeft = ref(600) // 10 minutes in seconds
const registration = ref(null)
const timer = ref(null)
const polling = ref(null)

const formattedTime = computed(() => {
  const minutes = Math.floor(timeLeft.value / 60)
  const seconds = timeLeft.value % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})

const fetchStatus = async () => {
  try {
    const data = await apiClient.get(`/api/registrations/my-registrations`)
    const current = data.find(r => r.id === parseInt(registrationId))
    if (current) {
      registration.value = current
      
      // Calculate remaining time from BE
      if (current.hold_expires_at) {
        const expiry = new Date(current.hold_expires_at).getTime()
        const now = new Date().getTime()
        const diff = Math.floor((expiry - now) / 1000)
        timeLeft.value = diff > 0 ? diff : 0
      }

      if (current.payment_status === 'paid') {
        router.push({ name: 'payment-success', params: { id: registrationId } })
      } else if (current.payment_status === 'expired' || current.status === 'cancelled') {
        router.push({ name: 'payment-failure', params: { id: registrationId } })
      }
    }
  } catch (err) {
    console.error('Lỗi khi kiểm tra trạng thái:', err)
  }
}

const startCountdown = () => {
  timer.value = setInterval(() => {
    if (timeLeft.value > 0) {
      timeLeft.value--
    } else {
      clearInterval(timer.value)
      router.push({ name: 'payment-failure', params: { id: registrationId } })
    }
  }, 1000)
}

onMounted(() => {
  fetchStatus()
  startCountdown()
  // Polling every 5 seconds to check if payment is confirmed
  polling.value = setInterval(fetchStatus, 5000)
})

onUnmounted(() => {
  clearInterval(timer.value)
  clearInterval(polling.value)
})

const handleManualConfirm = () => {
  fetchStatus()
}

const simulatePaymentSuccess = async () => {
  try {
    await apiClient.get(`/api/payments/vnpay-callback?regId=${registrationId}&status=success`)
    alert("Thanh toán giả lập thành công!")
    fetchStatus()
  } catch (err) {
    alert("Lỗi giả lập: " + err.message)
  }
}
</script>

<template>
  <div class="payment-waiting container">
    <div class="waiting-card">
      <div class="icon-section">
        <div class="pulse-ring"></div>
        <div class="icon">⏳</div>
      </div>

      <h1>Đang chờ thanh toán</h1>
      <p class="description">
        Hệ thống đang giữ chỗ cho bạn. Vui lòng hoàn tất thanh toán trong thời gian quy định để xác nhận đăng ký.
      </p>

      <div class="countdown-timer">
        <span class="label">Thời gian giữ chỗ còn lại:</span>
        <span class="time">{{ formattedTime }}</span>
      </div>

      <div class="action-section">
        <button class="btn-check" @click="handleManualConfirm">Tôi đã thanh toán, kiểm tra ngay</button>
        <button class="simulate-btn" @click="simulatePaymentSuccess">🛠️ Giả lập thanh toán thành công (Test)</button>
        <button class="btn-secondary" @click="router.push('/profile/my-tournaments')">Xem danh sách đăng ký</button>
      </div>

      <div class="info-note">
        <p>Lưu ý: Nếu quá 10 phút bạn chưa hoàn tất thanh toán, yêu cầu đăng ký sẽ tự động bị hủy và slot sẽ được giải phóng cho người khác.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.payment-waiting {
  padding-top: 10rem;
  padding-bottom: 6rem;
  display: flex;
  justify-content: center;
}

.waiting-card {
  max-width: 600px;
  width: 100%;
  background: white;
  padding: 4rem;
  border-radius: 40px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0,0,0,0.05);
}

.icon-section {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon {
  font-size: 3.5rem;
  z-index: 2;
}

.pulse-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 4px solid var(--primary);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.8); opacity: 0.8; }
  100% { transform: scale(1.5); opacity: 0; }
}

h1 { color: var(--text-dark); font-size: 2.2rem; margin-bottom: 1.5rem; }
.description { color: #6e7a74; font-size: 1.1rem; line-height: 1.6; margin-bottom: 3rem; }

.countdown-timer {
  background: #f0f7f4;
  padding: 2rem;
  border-radius: 8px;
  margin-bottom: 3rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.countdown-timer .label { color: var(--primary); font-weight: 500; font-size: 0.9rem; text-transform: uppercase; }
.countdown-timer .time { color: var(--primary); font-size: 3.5rem; font-weight: 500; font-variant-numeric: tabular-nums; }

.action-section { display: flex; flex-direction: column; gap: 1rem; }

.btn-check {
  padding: 1.2rem; border: none; border-radius: 8px;
  background: var(--primary); color: white; font-weight: 500; font-size: 1.1rem;
  cursor: pointer; box-shadow: 0 15px 30px rgba(0,105,83,0.2); transition: 0.2s;
}
.btn-check:hover { transform: translateY(-3px); box-shadow: 0 20px 40px rgba(0,105,83,0.3); }

.btn-secondary {
  padding: 1.2rem; background: transparent; border: 2px solid #eef1f1;
  border-radius: 8px; color: #4e6073; font-weight: 500; cursor: pointer; transition: 0.2s;
}
.btn-secondary:hover { background: #f8f9f9; }

.simulate-btn {
  background: #eee; border: none; padding: 10px; border-radius: 12px;
  color: #666; cursor: pointer; font-size: 0.85rem;
}
.simulate-btn:hover { background: #e0e0e0; }

.info-note { margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #f0f0f0; }
.info-note p { font-size: 0.9rem; color: #9e9e9e; font-style: italic; }
</style>
