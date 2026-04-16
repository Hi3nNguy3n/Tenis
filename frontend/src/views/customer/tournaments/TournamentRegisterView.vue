<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTournamentStore } from '../../../stores/tournament'
import { apiClient } from '../../../services/apiClient'

const route = useRoute()
const router = useRouter()
const tournamentStore = useTournamentStore()
const tournamentId = route.params.id

const registrationId = ref(null)
const step = ref(1)
const paymentMethod = ref('qr') // 'qr' only now
const teamSize = ref(2)
const partners = ref([
  { name: '', phone: '', email: '', account_code: '' }
])

const updateTeamSize = () => {
  // User is the first member, so we need size - 1 partners
  const count = Math.max(1, teamSize.value - 1)
  if (partners.value.length < count) {
    for (let i = partners.value.length; i < count; i++) {
      partners.value.push({ name: '', phone: '', email: '', account_code: '' })
    }
  } else {
    partners.value = partners.value.slice(0, count)
  }
}

const form = ref({
  registrant_type: 'player', 
  notes: ''
})

const timeLeft = ref(600) // 10 minutes = 600 seconds
let timerInterval = null

const formattedTime = computed(() => {
  const m = Math.floor(timeLeft.value / 60)
  const s = timeLeft.value % 60
  return `${m}:${s.toString().padStart(2, '0')}`
})

const startTimer = () => {
  if (timerInterval) clearInterval(timerInterval)
  timeLeft.value = 600
  timerInterval = setInterval(() => {
    if (timeLeft.value % 5 === 0) {
      // Mỗi 5 giây kiểm tra trạng thái thanh toán 1 lần (Polling)
      checkPaymentStatus()
    }

    if (timeLeft.value > 0) {
      timeLeft.value--
    } else {
      clearInterval(timerInterval)
      alert("Hết thời gian giữ chỗ! Đơn của bạn đã bị hủy.")
      router.push({ name: 'tournaments' })
    }
  }, 1000)
}

const checkPaymentStatus = async () => {
  if (!registrationId.value || step.value !== 2) return
  try {
    // Gọi API lấy danh sách đơn của mình để check status
    const data = await tournamentStore.fetchMyRegistrations()
    const myRegs = Array.isArray(data) ? data : (data?.items || [])
    
    if (myRegs.length === 0) return

    const currentReg = myRegs.find(r => r.id === registrationId.value)
    
    if (currentReg && currentReg.payment_status === 'paid') {
      if (timerInterval) clearInterval(timerInterval)
      step.value = 3 // Tự động nhảy sang bước thành công
    }
  } catch (err) {
     console.error("Polling error:", err)
  }
}


onMounted(() => {
  tournamentStore.fetchTournamentById(tournamentId)
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})

const t = computed(() => tournamentStore.currentTournament)

const submitRegistration = async () => {
  try {
    const extractId = (val) => {
      if (!val) return null
      const match = val.toString().match(/\d+/)
      return match ? parseInt(match[0]) : null
    }

    const result = await tournamentStore.registerForTournament(tournamentId, {
      registrant_type: form.value.registrant_type,
      notes: form.value.notes,
      partner_name: partners.value[0]?.name || '',
      partner_phone: partners.value[0]?.phone || '',
      partner_email: partners.value[0]?.email || '',
      partner_user_id: extractId(partners.value[0]?.account_code),
      team_members_data: partners.value.map(p => ({
        ...p,
        account_code: extractId(p.account_code)?.toString()
      }))
    })
    registrationId.value = result.id
    
    // Sync time with BE
    if (result.hold_expires_at) {
       const expiry = new Date(result.hold_expires_at).getTime()
       const now = new Date().getTime()
       timeLeft.value = Math.floor((expiry - now) / 1000)
    }

    step.value = 2
    startTimer()
  } catch (err) {
    alert('Lỗi đăng ký: ' + err.message)
  }
}

const goToPayment = async () => {
  if (!registrationId.value) return
  try {
    const data = await apiClient.post(`/api/payments/${registrationId.value}/create-url`)
    if (data.payment_url) {
      // Trong thực tế sẽ là window.location.href = data.payment_url
      // Ở đây ta giả lập bằng cách chuyển tới trang Success sau vài giây
      window.open(data.payment_url, '_blank')
      alert("Đang chuyển hướng tới cổng thanh toán... (Giả lập: Hãy quay lại đây và bấm xác nhận khi xong)")
    }
  } catch (err) {
    alert('Lỗi thanh toán: ' + err.message)
  }
}

const confirmPayment = async () => {
  if (!registrationId.value) return
  try {
    await tournamentStore.confirmRegistrationPayment(registrationId.value)
    if (timerInterval) clearInterval(timerInterval)
    step.value = 3
  } catch (err) {
    alert('Lỗi xác nhận: ' + err.message)
  }
}

const simulatePaymentSuccess = async () => {
  if (!registrationId.value) return
  try {
    // Call the callback endpoint directly to simulate success
    await apiClient.get(`/api/payments/vnpay-callback?regId=${registrationId.value}&status=success`)
    alert("Thanh toán giả lập thành công!")
    checkPaymentStatus()
  } catch (err) {
    alert("Lỗi giả lập thanh toán: " + err.message)
  }
}


const getVietQR = computed(() => {
  if (!t.value || !registrationId.value) return ''
  const amount = (form.value.registrant_type === 'team' ? t.value.entry_fee_team : t.value.entry_fee) || 0
  const info = `Thanh toan STT ${registrationId.value}`
  return `https://img.vietqr.io/image/MB-1111111111-compact.png?amount=${amount}&addInfo=${info}&accountName=SAIGON TENNIS`
})

const finish = () => {
  router.push({ name: 'my-tournaments' })
}

</script>

<template>
  <div class="register-page container">
    <div v-if="t" class="register-container">
      <div class="steps-indicator">
        <div class="step" :class="{ active: step >= 1, completed: step > 1 }">1. Thông tin</div>
        <div class="step-line"></div>
        <div class="step" :class="{ active: step >= 2, completed: step > 2 }">2. Thanh toán</div>
        <div class="step-line"></div>
        <div class="step" :class="{ active: step >= 3 }">3. Hoàn tất</div>
      </div>

      <!-- Step 1: Form -->
      <div v-if="step === 1" class="step-content">
        <h2>Đăng ký tham gia {{ t.name }}</h2>
        <p class="subtitle">Vui lòng chọn hình thức thi đấu của bạn.</p>

        <form @submit.prevent="submitRegistration" class="registration-form">
          <div class="form-group">
            <label>Hình thức thi đấu</label>
            <div class="radio-cards">
              <label class="radio-card" :class="{ selected: form.registrant_type === 'player' }">
                <input type="radio" v-model="form.registrant_type" value="player" />
                <div class="card-body">
                  <span class="icon">👤</span>
                  <span class="title">Cá nhân (Single)</span>
                  <span class="desc">Bạn tự đăng ký thi đấu độc lập.</span>
                </div>
              </label>
              
              <label class="radio-card" :class="{ selected: form.registrant_type === 'team' }">

                <input type="radio" v-model="form.registrant_type" value="team" />
                <div class="card-body">
                  <span class="icon">👥</span>
                  <span class="title">Đồng đội (Team)</span>
                  <span class="desc">Đăng ký theo đội hoặc cặp thi đấu.</span>
                </div>
              </label>
            </div>
          </div>
          
          <!-- Trường hợp đăng ký Đôi / Đội -->
          <div v-if="form.registrant_type === 'team'" class="team-partner-info animated slideInDown">
            <div class="team-header-row" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
              <h3 class="section-title" style="margin: 0; border: none;">Thông tin thành viên đội</h3>
              <div class="team-size-selector" style="display: flex; align-items: center; gap: 10px;">
                <label style="font-size: 0.9rem; font-weight: 600; margin: 0;">Số lượng:</label>
                <select v-model="teamSize" @change="updateTeamSize" style="padding: 5px 10px; border-radius: 8px; border: 1px solid #ddd;">
                   <option :value="2">2 (Đôi)</option>
                   <option :value="3">3</option>
                   <option :value="4">4</option>
                   <option :value="5">5</option>
                </select>
              </div>
            </div>

            <div v-for="(partner, index) in partners" :key="index" class="partner-form-block" style="border-top: 1px dashed #eee; padding-top: 1.5rem; margin-top: 1rem;">
              <h4 style="font-size: 0.9rem; color: var(--primary); margin-bottom: 1rem;">Thành viên #{{ index + 2 }}</h4>
              <div class="form-grid two-columns">
                <div class="form-group">
                  <label>Họ và tên</label>
                  <input type="text" v-model="partner.name" placeholder="Nhập họ tên" required />
                </div>
                <div class="form-group">
                  <label>Số điện thoại</label>
                  <input type="tel" v-model="partner.phone" placeholder="Nhập số điện thoại" required />
                </div>
              </div>
              <div class="form-grid two-columns">
                <div class="form-group">
                  <label>Email (nếu có)</label>
                  <input type="email" v-model="partner.email" placeholder="Nhập địa chỉ email" />
                </div>
                <div class="form-group">
                  <label>Mã tài khoản (nếu có)</label>
                  <input type="text" v-model="partner.account_code" placeholder="ID người chơi trên hệ thống" />
                </div>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label for="notes">Ghi chú thêm</label>
            <textarea id="notes" v-model="form.notes" placeholder="VD: Muốn ghép cặp, yêu cầu đặc biệt..."></textarea>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-back" @click="$router.back()">Quay lại</button>
            <button type="submit" class="btn-next">Tiếp tục thanh toán</button>
          </div>
        </form>
      </div>

      <!-- Step 2: Payment Mockup -->
      <div v-if="step === 2" class="step-content">
        <div class="header-with-timer">
          <h2>Thanh toán lệ phí</h2>
          <div class="countdown-timer">
            <span class="timer-label">Thời gian giữ chỗ:</span>
            <span class="timer-value">{{ formattedTime }}</span>
          </div>
        </div>

        <div class="payment-method-selectors">
           <button 
             class="method-btn active" 
           >
             <span class="icon">🏦</span>
             Chuyển khoản / QR (VietQR)
           </button>
        </div>

        <div class="payment-card">
          <div class="qr-payment-view">
            <div class="payment-info">
              <div class="info-row">
                <span class="label">Số tiền:</span>
                <span class="valueHighlight">{{ new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format((form.registrant_type === 'team' ? t.entry_fee_team : t.entry_fee) || 0) }}</span>
              </div>
              <p v-if="form.registrant_type === 'team'" style="font-size: 0.75rem; color: #ef6c00; font-weight: bold; margin-bottom: 0.5rem;">
                * Lệ phí áp dụng cho hình thức thi đấu Đội.
              </p>
              <p class="small-text" style="margin-top: 1rem;">
                Bạn có thể bấm nút bên dưới để thanh toán qua cổng VNPay/Momo hoặc quét mã chuyển khoản nhanh VietQR.
              </p>
            </div>
            <div class="payment-actions-box">
               <button class="btn-primary-payment" @click="goToPayment">
                 💳 Thanh toán Online
               </button>
               <div class="qr-display" style="margin-top: 15px; border: 1px solid #eee; padding: 10px; border-radius: 12px; background: white; text-align: center;">
                  <img :src="getVietQR" alt="VietQR" style="width: 250px; height: auto; border-radius: 8px;" />
                  <span style="font-size: 0.7rem; color: #6e7a74; display: block; margin-top: 5px;">Quét mã để thanh toán nhanh qua App Ngân hàng</span>
               </div>
            </div>
          </div>
        </div>


        <div class="payment-warning">
          <p>⚠️ Chú ý: Nếu quá 10 phút bạn không hoàn tất thanh toán, hệ thống sẽ tự động nhả slot cho người khác.</p>
          <button 
            style="margin-top: 10px; font-size: 0.8rem; background: #eee; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; color: #666;"
            @click="simulatePaymentSuccess"
          >
            🛠️ Giả lập thanh toán thành công (Dành cho Test)
          </button>
        </div>

        <div class="form-actions">
          <button type="button" class="btn-back" @click="step = 1">Quay lại</button>
          <button type="button" class="btn-next" :disabled="tournamentStore.loading" @click="confirmPayment">
            {{ tournamentStore.loading ? 'Đang kiểm tra...' : 'Xác nhận sau khi thanh toán' }}
          </button>
        </div>
      </div>


      <!-- Step 3: Success -->
      <div v-if="step === 3" class="step-content success-view">
        <div class="success-icon">✅</div>
        <h2>Đăng ký thành công!</h2>
        <p>Hồ sơ đăng ký của bạn đang được ban tổ chức xét duyệt. Bạn sẽ nhận được thông báo ngay khi trạng thái thay đổi.</p>
        
        <div class="next-steps">
          <p>Mã QR tham gia giải đã được tạo trong mục "Giải đấu của tôi".</p>
        </div>

        <button class="btn-next" @click="finish">Xem giải đấu của tôi</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-page {
  padding-top: 8rem;
  padding-bottom: 6rem;
}

.register-container {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  padding: 3rem;
  border-radius: 32px;
  box-shadow: 0 40px 80px rgba(0,0,0,0.06);
}

.steps-indicator {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4rem;
}

.step {
  font-size: 0.9rem;
  font-weight: 700;
  color: #bdc9c3;
  position: relative;
}

.step.active { color: var(--primary); }
.step.completed { color: #4caf50; }

.step-line {
  flex: 1;
  height: 2px;
  background: #eee;
  margin: 0 1.5rem;
}

.step-content h2 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  color: var(--text-dark);
}

.subtitle {
  color: #6e7a74;
  margin-bottom: 2.5rem;
}

.registration-form {
  padding: 1rem 0;
}

.section-title {
  font-size: 1.2rem;
  color: var(--text-dark);
  margin: 2rem 0 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #f0f4f2;
}

.team-partner-info {
  background: #f8fbfa;
  padding: 2rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  border: 1px solid #eef2f1;
}

.form-grid {
  display: grid;
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.form-grid.two-columns {
  grid-template-columns: 1fr 1fr;
}

@media (max-width: 600px) {
  .form-grid.two-columns {
    grid-template-columns: 1fr;
  }
}

.form-group label {
  display: block;
  font-weight: 700;
  margin-bottom: 1rem;
  color: var(--text-dark);
}

.radio-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.radio-card {
  border: 2px solid #f3f4f4;
  border-radius: 8px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.radio-card input {
  position: absolute;
  opacity: 0;
}

.radio-card.selected {
  border-color: var(--primary);
  background: rgba(21, 128, 61, 0.02);
}

.card-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.card-body .icon { font-size: 2rem; margin-bottom: 1rem; }
.card-body .title { font-weight: 800; font-size: 1.1rem; margin-bottom: 0.5rem; }
.card-body .desc { font-size: 0.85rem; color: #6e7a74; }

input[type="text"],
input[type="tel"],
input[type="email"],
textarea {
  width: 100%;
  padding: 1rem 1.2rem;
  border: 2px solid #f0f4f2;
  border-radius: 12px;
  font-family: inherit;
  font-size: 1rem;
  transition: all 0.2s;
  background: white;
}

input:focus,
textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(21, 128, 61, 0.05);
}

textarea {
  min-height: 120px;
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
}

.btn-next {
  padding: 1rem 2rem;
  border-radius: 12px;
  border: none;
  background: var(--primary);
  color: white;
  font-weight: 700;
  cursor: pointer;
}

.btn-back {
  padding: 1rem 2rem;
  border-radius: 12px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
}

.payment-card {
  display: flex;
  gap: 2rem;
  background: #f8f9f9;
  padding: 2rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.payment-info { flex: 1; display: grid; gap: 1rem; }
.info-row { display: flex; justify-content: space-between; border-bottom: 1px dashed #ddd; padding-bottom: 0.5rem; }
.valueHighlight { color: #ba1a1a; font-weight: 800; font-size: 1.2rem; }

.qr-mockup {
  width: 200px;
  text-align: center;
}

.qr-placeholder {
  width: 180px;
  height: 180px;
  background: #eee;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  font-size: 0.7rem;
  font-weight: 800;
  border: 4px solid white;
}

.payment-warning {
  padding: 1rem;
  background: #fff8e1;
  border-radius: 12px;
  color: #f57f17;
  font-weight: 600;
  margin-bottom: 2rem;
}

.success-view {
  text-align: center;
  padding: 2rem 0;
}

.success-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
}

.next-steps {
  margin: 2rem 0;
  padding: 1.5rem;
  background: #f0f7f4;
  border-radius: 12px;
  color: var(--text-dark);
}

.header-with-timer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.payment-method-selectors {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.method-btn {
  flex: 1;
  padding: 1rem;
  border: 2px solid #f3f4f4;
  border-radius: 16px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-weight: 700;
  color: #6e7a74;
  transition: all 0.2s;
}

.method-btn.active {
  border-color: var(--primary);
  color: var(--primary);
  background: #f0f7f4;
}

.qr-payment-view {
  display: flex;
  width: 100%;
  gap: 2rem;
}

@media (max-width: 600px) {
  .qr-payment-view { flex-direction: column; }
  .payment-method-selectors { flex-direction: column; }
}

.countdown-timer {
  background: #fff0f0;
  padding: 0.8rem 1.2rem;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  border: 1px solid #ffcccc;
}

.timer-label {
  font-size: 0.75rem;
  color: #ba1a1a;
  text-transform: uppercase;
  font-weight: 700;
}

.timer-value {
  font-size: 1.5rem;
  font-weight: 900;
  color: #ba1a1a;
  font-family: monospace;
}

.payment-actions-box {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: white;
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: 0 10px 20px rgba(0,0,0,0.05);
}

.btn-primary-payment {
  background: var(--primary);
  color: white;
  border: none;
  padding: 1.2rem 1.5rem;
  border-radius: 14px;
  font-size: 1.1rem;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.2s;
  width: 100%;
}

.btn-primary-payment:hover {
  transform: scale(1.02);
  background: #005a47;
}

.small-text {
  font-size: 0.8rem;
  color: #6e7a74;
  margin-top: 0.8rem;
}

@media (max-width: 600px) {
  .header-with-timer { flex-direction: column; align-items: flex-start; gap: 1rem; }
  .radio-cards { grid-template-columns: 1fr; }
  .payment-card { flex-direction: column; }
  .steps-indicator { display: none; }
}
</style>
