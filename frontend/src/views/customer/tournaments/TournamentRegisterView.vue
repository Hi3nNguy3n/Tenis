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
    // --- THÊM CHỐT CHẶN NGÀY GIỜ VÀ TRẠNG THÁI ---
    if (tournament.value) {
      const closeDate = new Date(tournament.value.registration_close_at);
      if (tournament.value.status !== 'open' || new Date() > closeDate) {
        ElMessage.error('Giải đấu này đã đóng đăng ký hoặc đã kết thúc!');
        router.push(`/tournaments/${tournamentId}`);
        return; // Dừng việc thực thi tiếp
      }
    }
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
  <div class="neo-registration-page">
    
    <!-- IMMERSIVE HERO HEADER -->
    <header class="neo-hero">
      <div class="hero-glow"></div>
      <div class="container hero-inner">
        <div class="hero-text">
          <span class="tour-badge"><el-icon><Ticket /></el-icon> OFFICIAL REGISTRATION</span>
          <h1 class="tour-title">{{ tournament?.name || 'Đang tải thông tin...' }}</h1>
        </div>
        
        <!-- MODERN STEPPER -->
        <div class="neo-stepper" v-if="!isAlreadyRegistered">
          <div class="step" :class="{ 'active': step >= 1, 'completed': step > 1 }">
            <div class="step-icon"><el-icon v-if="step > 1"><Check /></el-icon><span v-else>1</span></div>
            <span class="step-text">Thông tin</span>
          </div>
          <div class="step-line" :class="{ 'active': step >= 2 }"></div>
          
          <div class="step" :class="{ 'active': step >= 2, 'completed': step > 2 }">
            <div class="step-icon"><el-icon v-if="step > 2"><Check /></el-icon><span v-else>2</span></div>
            <span class="step-text">Xác thực</span>
          </div>
          <div class="step-line" :class="{ 'active': step === 3 }"></div>
          
          <div class="step" :class="{ 'active': step === 3 }">
            <div class="step-icon">3</div>
            <span class="step-text">Hoàn tất</span>
          </div>
        </div>
      </div>
    </header>

    <!-- BỐ CỤC CHÍNH (GRID) -->
    <div class="container neo-grid">
      
      <!-- CỘT TRÁI (FORM NỘI DUNG) -->
      <main class="main-column">
        
        <!-- TRẠNG THÁI: ĐÃ ĐĂNG KÝ -->
        <div v-if="isAlreadyRegistered" class="neo-card alert-card fade-in">
          <div class="card-icon warning"><el-icon><WarningFilled /></el-icon></div>
          <h2>Bạn đã ghi danh giải đấu này!</h2>
          <p>Hệ thống đã ghi nhận hồ sơ của bạn. Vui lòng kiểm tra mã QR Check-in hoặc xem lại thông tin chi tiết tại trang quản lý cá nhân.</p>
          <button class="neo-btn-primary mt-4" @click="router.push('/profile/my-tournaments')">
            Đến trang Hồ sơ <el-icon class="ml-2"><ArrowRight /></el-icon>
          </button>
        </div>

        <template v-else>
          <!-- BƯỚC 1: ĐIỀN THÔNG TIN -->
          <div v-if="step === 1" class="neo-card fade-in">
            <div class="card-header">
              <div class="ch-title">
                <el-icon class="ch-icon"><UserFilled /></el-icon>
                <h3>Thông tin vận động viên</h3>
              </div>
              <p class="ch-desc">Vui lòng điền đầy đủ và chính xác thông tin để BTC sắp xếp lịch thi đấu.</p>
            </div>
            
            <div class="card-body">
              <!-- Nhập thông tin đồng đội (Đôi) -->
              <div v-if="tournament?.format_type === 'Doubles'" class="partner-box">
                <div class="pb-header">Thông tin đồng đội (Đánh đôi)</div>
                <div class="neo-form-grid">
                  <div class="neo-form-item">
                    <label>Họ và tên đồng đội <span class="required">*</span></label>
                    <el-input v-model="partners[0].name" placeholder="Nhập họ và tên..." />
                  </div>
                  <div class="neo-form-item">
                    <label>Số điện thoại liên hệ <span class="required">*</span></label>
                    <el-input v-model="partners[0].phone" placeholder="Ví dụ: 0901234567..." />
                  </div>
                </div>
              </div>

              <div class="neo-form-item mt-4">
                <label>Ghi chú gửi Ban Tổ Chức (Tùy chọn)</label>
                <el-input v-model="form.notes" type="textarea" :rows="4" placeholder="Nhập size áo đấu, hoặc các yêu cầu đặc biệt khác..." />
              </div>
            </div>

            <div class="card-footer">
              <button class="neo-btn-ghost" @click="router.back()">Trở về</button>
              <button class="neo-btn-primary" @click="goToOTP" :disabled="isSubmitting">
                {{ isSubmitting ? 'Đang xử lý...' : 'Tiếp tục nhận mã OTP' }}
              </button>
            </div>
          </div>

          <!-- BƯỚC 2: XÁC THỰC OTP -->
          <div v-else-if="step === 2" class="neo-card fade-in">
            <div class="card-header text-center">
              <div class="ch-icon mx-auto"><el-icon><Message /></el-icon></div>
              <h3>Xác thực danh tính</h3>
              <p class="ch-desc">Để bảo mật, vui lòng nhập mã xác thực OTP gồm 6 chữ số vừa được gửi đến hòm thư của bạn.</p>
            </div>
            
            <div class="card-body text-center">
              <div class="email-badge">{{ userEmail }}</div>
              
              <div class="otp-container">
                <el-input v-model="otpCode" maxlength="6" placeholder="• • • • • •" class="neo-otp-input" />
              </div>
              
              <div class="resend-block">
                <span>Chưa nhận được mã?</span>
                <a href="#" @click.prevent="goToOTP" :class="{'disabled': isSubmitting}">Gửi lại OTP</a>
              </div>
            </div>
            
            <div class="card-footer space-between">
              <button class="neo-btn-ghost" @click="step = 1">Quay lại sửa</button>
              <button class="neo-btn-primary" @click="submitRegistration" :disabled="isSubmitting || otpCode.length < 6">
                <el-icon class="mr-2" v-if="isSubmitting"><Loading /></el-icon>
                {{ isSubmitting ? 'Đang xác thực...' : 'Xác nhận Đăng ký' }}
              </button>
            </div>
          </div>

          <!-- BƯỚC 3: THÀNH CÔNG -->
          <div v-else-if="step === 3" class="neo-card success-card scale-up">
            <div class="card-icon success"><el-icon><Check /></el-icon></div>
            <h2>Ghi danh thành công!</h2>
            <p>Tuyệt vời! Hồ sơ tham dự giải đấu của bạn đã được lưu vào hệ thống.<br>Vui lòng đến bàn Check-in tại sân để hoàn tất thanh toán lệ phí (nếu có).</p>
            
            <div class="success-actions">
              <button class="neo-btn-primary" @click="router.push('/profile/my-tournaments')">
                Xem Vé điện tử (QR Code)
              </button>
            </div>
          </div>
        </template>
      </main>

      <!-- CỘT PHẢI (TICKET SUMMARY) -->
      <aside class="sidebar-column">
        <div class="ticket-widget sticky">
          
          <!-- Phần trên của vé -->
          <div class="ticket-top">
            <div class="ticket-brand">SAIGON TENNIS TOUR</div>
            <h3 class="ticket-tour-name">{{ tournament?.name || 'Đang tải...' }}</h3>
            <div class="ticket-info-grid">
              <div class="t-info-item">
                <span>Ngày khởi tranh</span>
                <strong>{{ tournament?.start_date ? new Date(tournament.start_date).toLocaleDateString('vi-VN') : 'TBA' }}</strong>
              </div>
              <div class="t-info-item text-right">
                <span>Địa điểm</span>
                <strong>{{ tournament?.location || 'Saigon Center' }}</strong>
              </div>
            </div>
          </div>
          
          <!-- Rãnh xé vé -->
          <div class="ticket-divider">
            <div class="notch left"></div>
            <div class="line"></div>
            <div class="notch right"></div>
          </div>
          
          <!-- Phần dưới của vé -->
          <div class="ticket-bottom">
            <div class="t-summary-row">
              <div class="ts-lbl"><el-icon><Trophy /></el-icon> Thể thức thi đấu</div>
              <div class="ts-val">{{ formatCategoryLabel(tournament?.format_type) }}</div>
            </div>
            <div class="t-summary-row">
              <div class="ts-lbl"><el-icon><Ticket /></el-icon> Lệ phí giải</div>
              <div class="ts-val price">
                {{ tournament?.entry_fee ? new Intl.NumberFormat('vi-VN').format(tournament.entry_fee) + 'đ' : 'Miễn phí' }}
              </div>
            </div>
          </div>
          
        </div>
      </aside>

    </div>
  </div>
</template>

<style scoped>
/* =========================================================
   NEO-MODERN VARIABLES
========================================================= */
.neo-registration-page {
  --navy: #002855;
  --navy-light: #004080;
  --blue-accent: #0066cc;
  --bg-main: #f1f5f9;
  --surface: #ffffff;
  --border-color: #e2e8f0;
  --text-dark: #0f172a;
  --text-body: #334155;
  --text-muted: #64748b;
  --success: #16a34a;
  --warning: #ca8a04;

  background-color: var(--bg-main);
  min-height: 100vh;
  padding-bottom: 5rem;
  font-family: 'Inter', -apple-system, sans-serif;
  color: var(--text-body);
}

.container { max-width: 1100px; margin: 0 auto; padding: 0 1.5rem; }
.text-center { text-align: center; }
.mx-auto { margin-left: auto; margin-right: auto; }
.mt-4 { margin-top: 1.5rem; }
.ml-2 { margin-left: 8px; }
.mr-2 { margin-right: 8px; }

/* Force font for Element Plus inputs */
:deep(.el-input__inner), :deep(.el-textarea__inner) { font-family: 'Inter', sans-serif !important; }

/* =========================================================
   HERO HEADER & STEPPER
========================================================= */
.neo-hero {
  background: var(--navy);
  color: white;
  padding: 4rem 0 7rem;
  position: relative;
  overflow: hidden;
  margin-bottom: -5rem; /* Kéo Main đè lên */
}

.hero-glow {
  position: absolute; top: -50%; right: 10%;
  width: 500px; height: 500px; background: #0066cc;
  border-radius: 50%; filter: blur(120px); opacity: 0.4;
  pointer-events: none;
}

.hero-inner {
  display: flex; justify-content: space-between; align-items: center;
  position: relative; z-index: 2; flex-wrap: wrap; gap: 2rem;
}

.tour-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.2);
  padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;
  letter-spacing: 0.05em; margin-bottom: 1rem; backdrop-filter: blur(4px);
}
.tour-title { font-size: 2.2rem; font-weight: 800; margin: 0; line-height: 1.2; letter-spacing: -0.02em;}

/* Stepper */
.neo-stepper { display: flex; align-items: center; gap: 12px; }
.step { display: flex; flex-direction: column; align-items: center; gap: 8px; opacity: 0.5; transition: 0.3s; }
.step.active, .step.completed { opacity: 1; }

.step-icon {
  width: 32px; height: 32px; border-radius: 50%;
  background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.9rem; font-weight: 700; transition: 0.3s;
}
.step.active .step-icon { background: var(--blue-accent); border-color: var(--blue-accent); color: white;}
.step.completed .step-icon { background: #34d399; border-color: #34d399; color: var(--navy);}

.step-text { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;}

.step-line { width: 40px; height: 2px; background: rgba(255,255,255,0.2); margin-top: -24px;}
.step-line.active { background: var(--blue-accent); }

@media (max-width: 900px) {
  .hero-inner { flex-direction: column; align-items: flex-start; }
  .neo-stepper { width: 100%; justify-content: space-between; }
  .step-line { flex: 1; margin-top: -20px;}
  .step-text { display: none; } /* Ẩn text bước ở mobile */
}

/* =========================================================
   GRID LAYOUT
========================================================= */
.neo-grid {
  display: grid; grid-template-columns: 1fr 340px; gap: 2rem; position: relative; z-index: 10;
}
@media (max-width: 900px) {
  .neo-grid { grid-template-columns: 1fr; }
  .sidebar-column { order: -1; }
  .neo-hero { padding-bottom: 5rem; margin-bottom: -3rem;}
}

/* =========================================================
   CARDS (MAIN FORMS)
========================================================= */
.neo-card {
  background: var(--surface); border-radius: 16px; border: 1px solid var(--border-color);
  box-shadow: 0 10px 40px rgba(0,0,0,0.04); overflow: hidden;
}

.card-header { padding: 1.5rem 2rem; border-bottom: 1px solid var(--border-color); }
.ch-title { display: flex; align-items: center; gap: 10px; margin-bottom: 6px;}
.ch-icon { font-size: 1.4rem; color: var(--blue-accent); }
.ch-title h3 { margin: 0; font-size: 1.2rem; font-weight: 800; color: var(--text-dark);}
.ch-desc { margin: 0; font-size: 0.85rem; color: var(--text-muted); line-height: 1.5;}

.card-body { padding: 2rem; }

.card-footer {
  padding: 1.25rem 2rem; background: #f8fafc; border-top: 1px solid var(--border-color);
  display: flex; justify-content: flex-end; gap: 12px;
}
.card-footer.space-between { justify-content: space-between; }


/* =========================================================
   FORM INPUTS
========================================================= */
.neo-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
@media (max-width: 600px) { .neo-form-grid { grid-template-columns: 1fr; gap: 1rem;} }

.neo-form-item label {
  display: block; font-size: 0.85rem; font-weight: 700; color: var(--text-dark); margin-bottom: 6px;
}
.required { color: #ef4444; margin-left: 2px;}

/* Ghi đè input Element */
:deep(.el-input__wrapper), :deep(.el-textarea__wrapper) {
  background: #f8fafc !important; box-shadow: 0 0 0 1px var(--border-color) inset !important; border-radius: 8px; padding: 8px 12px;
}
:deep(.el-input__wrapper.is-focus), :deep(.el-textarea__wrapper.is-focus) {
  background: white !important; box-shadow: 0 0 0 2px var(--blue-accent) inset !important;
}

.partner-box {
  background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;
}
.pb-header { font-size: 0.9rem; font-weight: 800; color: var(--navy); margin-bottom: 1rem; text-transform: uppercase;}

/* =========================================================
   OTP SECTION
========================================================= */
.email-badge {
  display: inline-block; background: #e0f2fe; color: #0369a1; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 0.9rem; margin-bottom: 2rem;
}
.otp-container { max-width: 320px; margin: 0 auto; }
:deep(.neo-otp-input .el-input__inner) {
  text-align: center; font-size: 2.2rem; letter-spacing: 0.4em; font-weight: 800; color: var(--navy); height: 70px;
}
.resend-block { margin-top: 1.5rem; font-size: 0.9rem; color: var(--text-muted); }
.resend-block a { color: var(--blue-accent); font-weight: 700; text-decoration: none; margin-left: 6px; transition: 0.2s;}
.resend-block a:hover { color: var(--navy); text-decoration: underline;}
.resend-block a.disabled { color: var(--border-color); pointer-events: none;}

/* =========================================================
   BUTTONS
========================================================= */
.neo-btn-primary {
  background: var(--blue-accent); color: white; border: none;
  padding: 0.8rem 1.5rem; border-radius: 8px; font-size: 0.9rem; font-weight: 700; cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center; transition: 0.2s;
}
.neo-btn-primary:hover:not(:disabled) { background: #0055a4; transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0, 102, 204, 0.2);}
.neo-btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.neo-btn-ghost {
  background: transparent; border: 1px solid var(--border-color); color: var(--text-body);
  padding: 0.8rem 1.5rem; border-radius: 8px; font-size: 0.9rem; font-weight: 700; cursor: pointer; transition: 0.2s;
}
.neo-btn-ghost:hover { background: #f8fafc; color: var(--text-dark); border-color: var(--text-dark);}

/* =========================================================
   STATUS CARDS (Thành công / Cảnh báo)
========================================================= */
.alert-card, .success-card { padding: 4rem 2rem; text-align: center; display: flex; flex-direction: column; align-items: center;}
.card-icon {
  width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 2.5rem; margin-bottom: 1.5rem;
}
.card-icon.warning { background: #fef9c3; color: var(--warning); }
.card-icon.success { background: #dcfce7; color: var(--success); }
.alert-card h2, .success-card h2 { margin: 0 0 1rem; color: var(--text-dark); font-weight: 800;}
.alert-card p, .success-card p { margin: 0; color: var(--text-muted); line-height: 1.6;}
.success-actions { margin-top: 2rem; }

/* =========================================================
   SIDEBAR (TICKET WIDGET)
========================================================= */
.sticky { position: sticky; top: 24px; }
.ticket-widget {
  background: var(--surface); border-radius: 16px; border: 1px solid var(--border-color);
  box-shadow: 0 20px 40px rgba(0,0,0,0.06); overflow: hidden;
}

.ticket-top { padding: 1.5rem; background: var(--navy); color: white;}
.ticket-brand { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em; color: #cbd5e1; margin-bottom: 1rem; text-transform: uppercase;}
.ticket-tour-name { font-size: 1.25rem; font-weight: 800; margin: 0 0 1.5rem; line-height: 1.3;}
.ticket-info-grid { display: flex; justify-content: space-between; }
.t-info-item { display: flex; flex-direction: column; gap: 4px; }
.t-info-item span { font-size: 0.65rem; color: #94a3b8; text-transform: uppercase; font-weight: 600;}
.t-info-item strong { font-size: 0.9rem; color: white; font-weight: 700;}

/* Rãnh xé vé */
.ticket-divider {
  height: 24px; position: relative; background: var(--surface); display: flex; align-items: center;
}
.notch {
  width: 24px; height: 24px; background: var(--bg-main); border-radius: 50%;
  position: absolute; border: 1px solid var(--border-color);
}
.notch.left { left: -13px; border-right-color: transparent; border-top-color: transparent; transform: rotate(45deg);}
.notch.right { right: -13px; border-left-color: transparent; border-bottom-color: transparent; transform: rotate(45deg);}
.ticket-divider .line {
  flex: 1; height: 1px; border-top: 2px dashed var(--border-color); margin: 0 20px;
}

.ticket-bottom { padding: 1.5rem; background: var(--surface);}
.t-summary-row {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;
}
.t-summary-row:last-child { margin-bottom: 0; }
.ts-lbl { font-size: 0.85rem; color: var(--text-muted); font-weight: 600; display: flex; align-items: center; gap: 8px;}
.ts-lbl .el-icon { color: var(--navy); }
.ts-val { font-size: 0.95rem; font-weight: 700; color: var(--text-dark);}
.ts-val.price { font-size: 1.2rem; color: var(--blue-accent); font-weight: 800;}

/* Animations */
.fade-in { animation: fadeIn 0.4s ease forwards; }
.scale-up { animation: scaleUp 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes scaleUp { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
</style>