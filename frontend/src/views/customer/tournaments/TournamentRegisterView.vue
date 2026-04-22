<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTournamentStore } from '../../../stores/tournament'
import { useAuthStore } from '../../../stores/auth'
import { apiClient } from '../../../services/apiClient'
import { authService } from '../../../services/authService'
import { ElMessage } from 'element-plus'
import { Check, Trophy, UserFilled, Message, WarningFilled, Calendar, Ticket, ArrowRight } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const tournamentStore = useTournamentStore()
const authStore = useAuthStore()
const tournamentId = route.params.id

const step = ref(1) // 1: Info, 2: OTP, 3: Success
const isSubmitting = ref(false)
const isAlreadyRegistered = ref(false) // Biến khóa trang
const otpCode = ref('')

const partners = ref([{ name: '', phone: '', email: '', account_code: '' }])
const form = ref({ notes: '' })

const tournament = computed(() => tournamentStore.currentTournament)
const userEmail = computed(() => authStore.user?.email || '')

const formatCategoryLabel = (type) => type === 'Singles' ? 'Đơn (Singles)' : 'Đôi (Doubles)'

onMounted(async () => {
  if (tournamentId) {
    await tournamentStore.fetchTournamentById(tournamentId)
    if (tournament.value?.format_type === 'Doubles') {
      partners.value = [{ name: '', phone: '', email: '', account_code: '' }]
    }

    // KIỂM TRA ĐĂNG KÝ TRÙNG LẶP Ở ĐÂY
    try {
      const myRegs = await apiClient.get('/api/registrations/my-registrations')
      const exists = myRegs.find(r => r.tournament_id === parseInt(tournamentId) && r.status !== 'cancelled' && r.status !== 'rejected')
      if (exists) {
        isAlreadyRegistered.value = true // Khóa màn hình lại
      }
    } catch (err) {
      console.error(err)
    }
  }
})

const goToOTP = async () => {
  if (tournament.value?.format_type === 'Doubles') {
    for (const p of partners.value) {
      if (!p.name || !p.phone) return ElMessage.warning('Vui lòng nhập đủ thông tin đồng đội.')
    }
  }

  isSubmitting.value = true
  try {
    await authService.sendOtp(userEmail.value)
    ElMessage.success(`Mã OTP đã được gửi đến ${userEmail.value}`)
    step.value = 2
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || 'Lỗi gửi OTP.')
  } finally {
    isSubmitting.value = false
  }
}

const submitRegistration = async () => {
  if (otpCode.value.length < 6) return ElMessage.warning('Vui lòng nhập đủ 6 số OTP.')

  isSubmitting.value = true
  try {
    const payload = {
      notes: form.value.notes,
      partners: tournament.value?.format_type === 'Doubles' ? partners.value : [],
      otp: otpCode.value
    }
    await apiClient.post(`/api/tournaments/${tournamentId}/register`, payload)
    step.value = 3
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || 'Mã OTP không đúng hoặc giải đấu đã hết chỗ.')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="registration-page">
    <div class="page-header">
      <div class="container header-content">
        <div class="header-text">
          <span class="tagline">Ghi danh giải đấu</span>
          <h1>{{ tournament?.name || 'Đang tải thông tin...' }}</h1>
        </div>
        
        <div class="stepper" v-if="!isAlreadyRegistered">
          <div :class="['step-item', { active: step >= 1, completed: step > 1 }]">
            <div class="step-circle">1</div>
            <span class="step-label">Thông tin</span>
          </div>
          <div class="step-divider"></div>
          <div :class="['step-item', { active: step >= 2, completed: step > 2 }]">
            <div class="step-circle">2</div>
            <span class="step-label">Xác thực OTP</span>
          </div>
          <div class="step-divider"></div>
          <div :class="['step-item', { active: step === 3 }]">
            <div class="step-circle">3</div>
            <span class="step-label">Hoàn tất</span>
          </div>
        </div>
      </div>
    </div>

    <div class="container content-grid">
      
      <div class="main-column">
        <div v-if="isAlreadyRegistered" class="status-card alert-card fade-in">
          <div class="icon-wrapper warning">
            <el-icon><WarningFilled /></el-icon>
          </div>
          <h2>Bạn đã đăng ký giải đấu này!</h2>
          <p>Hồ sơ của bạn đã được hệ thống ghi nhận. Vui lòng theo dõi trạng thái tại trang cá nhân.</p>
          <button class="btn-primary mt-4" @click="router.push('/profile/my-tournaments')">
            Về trang Hồ sơ <el-icon class="ml-2"><ArrowRight /></el-icon>
          </button>
        </div>

        <template v-else>
          <div v-if="step === 1" class="data-card fade-in">
            <div class="card-header">
              <el-icon class="header-icon"><UserFilled /></el-icon>
              <h3>Thông tin vận động viên</h3>
            </div>
            
            <div class="card-body">
              <div v-if="tournament?.format_type === 'Doubles'" class="partner-section">
                <div class="section-title">Thông tin đồng đội</div>
                <div class="form-grid">
                  <div class="form-item">
                    <label>Họ và tên đồng đội <span class="required">*</span></label>
                    <el-input v-model="partners[0].name" placeholder="Nhập họ và tên" />
                  </div>
                  <div class="form-item">
                    <label>Số điện thoại <span class="required">*</span></label>
                    <el-input v-model="partners[0].phone" placeholder="Nhập số điện thoại" />
                  </div>
                </div>
              </div>

              <div class="form-item mt-4">
                <label>Ghi chú cho Ban tổ chức (Tùy chọn)</label>
                <el-input v-model="form.notes" type="textarea" :rows="4" placeholder="Nhập size áo, yêu cầu đặc biệt..." />
              </div>
            </div>

            <div class="card-footer">
              <button class="btn-text" @click="router.back()">Hủy bỏ</button>
              <button class="btn-primary" @click="goToOTP" :disabled="isSubmitting">
                {{ isSubmitting ? 'Đang xử lý...' : 'Tiếp tục nhận OTP' }}
              </button>
            </div>
          </div>

          <div v-else-if="step === 2" class="data-card fade-in">
            <div class="card-header">
              <el-icon class="header-icon"><Message /></el-icon>
              <h3>Xác thực danh tính</h3>
            </div>
            <div class="card-body otp-body">
              <div class="otp-instruction">
                Mã bảo mật gồm 6 chữ số đã được gửi đến email:<br>
                <strong>{{ userEmail }}</strong>
              </div>
              <el-input v-model="otpCode" maxlength="6" placeholder="• • • • • •" class="otp-input" />
              <div class="resend-text">Không nhận được mã? <a href="#" @click.prevent="goToOTP">Gửi lại</a></div>
            </div>
            <div class="card-footer">
              <button class="btn-text" @click="step = 1">Quay lại</button>
              <button class="btn-primary" @click="submitRegistration" :disabled="isSubmitting || otpCode.length < 6">
                {{ isSubmitting ? 'Đang xử lý...' : 'Xác nhận đăng ký' }}
              </button>
            </div>
          </div>

          <div v-else-if="step === 3" class="status-card success-card scale-up">
            <div class="icon-wrapper success">
              <el-icon><Check /></el-icon>
            </div>
            <h2>Ghi danh thành công!</h2>
            <p>Hồ sơ của bạn đã được hệ thống <strong>Xác nhận</strong>.<br>Vui lòng thanh toán lệ phí trực tiếp cho Ban Tổ Chức tại sân vào ngày thi đấu.</p>
            <button class="btn-primary mt-4" @click="router.push('/profile/my-tournaments')">
              Xem mã QR Check-in
            </button>
          </div>
        </template>
      </div>

      <div class="sidebar-column">
        <div class="summary-card sticky">
          <div class="summary-hero">
            <div class="hero-pattern"></div>
            <div class="hero-content">
              <div class="category-badge">{{ formatCategoryLabel(tournament?.format_type) }}</div>
              <h3 class="tour-name-side">{{ tournament?.name || 'Đang tải...' }}</h3>
            </div>
          </div>
          
          <div class="summary-details">
            <div class="detail-row">
              <el-icon class="detail-icon"><Trophy /></el-icon>
              <div>
                <div class="detail-label">Thể thức thi đấu</div>
                <div class="detail-value">{{ formatCategoryLabel(tournament?.format_type) }}</div>
              </div>
            </div>
            <div class="detail-row">
              <el-icon class="detail-icon"><Ticket /></el-icon>
              <div>
                <div class="detail-label">Lệ phí tham dự</div>
                <div class="detail-value price">
                  {{ tournament?.entry_fee ? new Intl.NumberFormat('vi-VN').format(tournament.entry_fee) + ' VNĐ' : 'Miễn phí' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* Reset & Base Variables cho trang này */
.registration-page {
  --primary-color: #15803d;
  --primary-hover: #166534;
  --bg-color: #f8fafc;
  --card-bg: #ffffff;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --border-color: #e2e8f0;
  
  background-color: var(--bg-color);
  min-height: 100vh;
  padding-bottom: 4rem;
  font-family: 'Inter', Arial, sans-serif;
}

/* Ép font cho Element Plus cục bộ trang này để không bị lỗi font */
:deep(.el-input__inner),
:deep(.el-textarea__inner),
:deep(.el-button) {
  font-family: 'Inter', Arial, sans-serif !important;
}

/* Typography Utilities */
h1, h2, h3 { margin: 0; color: var(--text-main); font-weight: 700; }
.mt-4 { margin-top: 1.5rem; }
.ml-2 { margin-left: 0.5rem; }

/* -------------------------------------
   Header Banner
-------------------------------------- */
.page-header {
  background: linear-gradient(135deg, #001242 0%, #04246b 100%);
  color: white;
  padding: 3rem 0;
  margin-bottom: -4rem; /* Kéo nội dung main lên trên một chút */
  position: relative;
}
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}
.tagline {
  color: #c1ff72;
  font-size: 0.875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
  display: block;
}
.header-text h1 {
  color: white;
  font-size: 2rem;
  line-height: 1.2;
}

/* -------------------------------------
   Stepper (Quy trình)
-------------------------------------- */
.stepper {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 1rem 1.5rem;
  border-radius: 50px;
  backdrop-filter: blur(10px);
}
.step-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  opacity: 0.5;
  transition: 0.3s;
}
.step-item.active, .step-item.completed { opacity: 1; }
.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: grid;
  place-items: center;
  font-size: 0.875rem;
  font-weight: 700;
}
.step-item.active .step-circle { background: #c1ff72; color: #001242; }
.step-item.completed .step-circle { background: #15803d; color: white; }
.step-label { font-size: 0.875rem; font-weight: 600; display: none; }
.step-item.active .step-label { display: block; }
.step-divider { width: 30px; height: 2px; background: rgba(255, 255, 255, 0.2); }

@media (min-width: 768px) {
  .step-label { display: block; }
}

/* -------------------------------------
   Grid Layout
-------------------------------------- */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 2rem;
  position: relative;
  z-index: 10;
}
@media (max-width: 992px) {
  .content-grid { grid-template-columns: 1fr; }
  .sidebar-column { order: -1; } /* Đưa sidebar lên trên ở mobile */
  .page-header { margin-bottom: 2rem; padding: 2rem 0; }
}

/* -------------------------------------
   Cards (Thẻ chứa nội dung chính)
-------------------------------------- */
.data-card {
  background: var(--card-bg);
  border-radius: 16px;
  box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
  border: 1px solid var(--border-color);
  overflow: hidden;
  margin-top: 2rem;
}

.card-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.header-icon { font-size: 1.5rem; color: var(--primary-color); }
.card-body { padding: 2rem; }
.card-footer {
  padding: 1.5rem 2rem;
  background: #f8fafc;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

/* -------------------------------------
   Forms & Inputs
-------------------------------------- */
.form-item label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 0.5rem;
}
.required { color: #ef4444; }

.partner-section {
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  padding: 1.5rem;
}
.section-title {
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 1rem;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}
@media (max-width: 640px) {
  .form-grid { grid-template-columns: 1fr; }
}

:deep(.el-input__wrapper), :deep(.el-textarea__wrapper) {
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
  border-radius: 8px;
  padding: 8px 12px;
}
:deep(.el-input__wrapper.is-focus), :deep(.el-textarea__wrapper.is-focus) {
  box-shadow: 0 0 0 2px var(--primary-color) inset !important;
}

/* -------------------------------------
   OTP Section
-------------------------------------- */
.otp-body { text-align: center; }
.otp-instruction { font-size: 0.95rem; color: var(--text-muted); margin-bottom: 2rem; }
.otp-instruction strong { color: var(--text-main); }
.otp-input { max-width: 300px; margin: 0 auto; }
:deep(.otp-input .el-input__inner) {
  text-align: center;
  font-size: 2rem;
  letter-spacing: 0.5em;
  font-weight: 800;
  color: var(--primary-color);
  height: 60px;
}
.resend-text { margin-top: 1.5rem; font-size: 0.875rem; color: var(--text-muted); }
.resend-text a { color: var(--primary-color); font-weight: 600; text-decoration: none; }

/* -------------------------------------
   Buttons
-------------------------------------- */
.btn-primary, .btn-text {
  font-family: 'Inter', Arial, sans-serif;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.btn-primary {
  background: var(--primary-color);
  color: white;
  border: none;
}
.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(21, 128, 61, 0.25);
}
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-text {
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
}
.btn-text:hover { background: #f1f5f9; color: var(--text-main); }

/* -------------------------------------
   Status Cards (Alert & Success)
-------------------------------------- */
.status-card {
  background: var(--card-bg);
  border-radius: 16px;
  padding: 4rem 2rem;
  text-align: center;
  border: 1px solid var(--border-color);
  box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
  margin-top: 2rem;
}
.icon-wrapper {
  width: 80px; height: 80px;
  border-radius: 50%;
  display: grid; place-items: center;
  font-size: 2.5rem;
  margin: 0 auto 1.5rem;
}
.icon-wrapper.success { background: #dcfce7; color: #16a34a; }
.icon-wrapper.warning { background: #fef9c3; color: #ca8a04; }
.status-card h2 { margin-bottom: 1rem; }
.status-card p { color: var(--text-muted); line-height: 1.6; }

/* -------------------------------------
   Sidebar Summary (No Image Design)
-------------------------------------- */
.sticky { position: sticky; top: 100px; }
.summary-card {
  background: var(--card-bg);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
  overflow: hidden;
  margin-top: 2rem;
}
.summary-hero {
  background: linear-gradient(135deg, #15803d 0%, #166534 100%);
  position: relative;
  padding: 2.5rem 1.5rem;
  color: white;
  overflow: hidden;
}
.hero-pattern {
  position: absolute;
  top: -50px; right: -50px;
  width: 150px; height: 150px;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 10%, transparent 10%),
              radial-gradient(circle, rgba(255,255,255,0.1) 10%, transparent 10%);
  background-size: 20px 20px;
  background-position: 0 0, 10px 10px;
  opacity: 0.5;
  border-radius: 50%;
}
.hero-content { position: relative; z-index: 1; }
.category-badge {
  display: inline-block;
  background: #c1ff72;
  color: #001242;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  margin-bottom: 1rem;
}
.tour-name-side { font-size: 1.25rem; line-height: 1.4; color: white; }

.summary-details { padding: 1.5rem; }
.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: 1px solid var(--border-color);
}
.detail-row:last-child { border-bottom: none; padding-bottom: 0; }
.detail-icon {
  font-size: 1.5rem;
  color: var(--primary-color);
  background: #dcfce7;
  padding: 8px;
  border-radius: 8px;
}
.detail-label { font-size: 0.75rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-bottom: 0.25rem; }
.detail-value { font-weight: 600; color: var(--text-main); }
.detail-value.price { font-size: 1.25rem; color: var(--primary-color); }

/* Animations */
.fade-in { animation: fadeIn 0.4s ease forwards; }
.scale-up { animation: scaleUp 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes scaleUp { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
</style>