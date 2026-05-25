<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTournamentStore } from '../../../stores/tournament'
import { useAuthStore } from '../../../stores/auth'
import { apiClient } from '../../../services/apiClient'
import { authService } from '../../../services/authService'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Trophy, UserFilled, Message, WarningFilled, Calendar, Ticket, ArrowRight, Loading, Phone, Close, Search, CircleCheckFilled } from '@element-plus/icons-vue'
import { t } from '../../../utils/locale' 


const route = useRoute()
const router = useRouter()
const tournamentStore = useTournamentStore()
const authStore = useAuthStore()
const tournamentId = route.params.id

const step = ref(1) 
const isSubmitting = ref(false)
const myRegistrations = ref([])
const otpCode = ref('')

const safeFormatDate = (dateStr) => {
  if (!dateStr) return 'TBA'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return 'TBA'
  return d.toLocaleDateString('vi-VN')
}

const partners = ref([{ name: '', phone: '', email: '', player_id: null }])
const selectedCategoryId = ref(null)
const form = ref({ notes: '' })
const partnerSearchLoading = ref(false)

const tournament = computed(() => tournamentStore.currentTournament)
const userEmail = computed(() => authStore.user?.email || '')

const selectedCategory = computed(() => {
  if (!selectedCategoryId.value || !tournament.value?.categories) return null
  return tournament.value.categories.find(c => c.id === selectedCategoryId.value)
})

const isAlreadyRegistered = computed(() => {
  return myRegistrations.value.some(r => r.category_id === selectedCategoryId.value)
})

const formatCategoryLabel = (type) => type === 'Singles' ? t('tournaments.singlesFormat') : t('tournaments.doublesFormat')

onMounted(async () => {
  // Safeguard: Detect corrupted [object Object] in URL
  let tid = route.params.id
  if (!tid || String(tid).includes('[object')) {
    console.warn("Detected corrupted tournament ID in URL:", tid)
    // Try to recover from store if possible
    if (tournament.value?.id) {
      tid = tournament.value.id
      router.replace({ name: 'tournament-register', params: { id: tid } })
    } else {
      ElMessage.error("Đường dẫn không hợp lệ, đang quay lại trang giải đấu...")
      router.push('/tournaments')
      return
    }
  }

  if (tid) {
    await tournamentStore.fetchTournamentById(tid)
    if (tournament.value) {
      if (tournament.value.registration_close_at) {
        const closeDate = new Date(tournament.value.registration_close_at);
        if (!isNaN(closeDate.getTime()) && (tournament.value.status !== 'open' || new Date() > closeDate)) {
          ElMessage.error(t('tournaments.registrationClosedAlert'));
          router.push(`/tournaments/${tid}`);
          return; 
        }
      }
    }
    if (tournament.value?.categories?.length > 0) {
      selectedCategoryId.value = tournament.value.categories[0].id
    }
    
    // Kiểm tra loại hình thi đấu của category đầu tiên
    const firstCat = tournament.value?.categories?.[0]
    if (firstCat && firstCat.category_type.includes('doubles')) {
      partners.value = [{ name: '', phone: '', email: '', player_id: null }]
    }

    try {
      const myRegs = await apiClient.get('/api/registrations/my-registrations')
      myRegistrations.value = myRegs.filter(r => r.tournament_id === parseInt(tid) && r.status !== 'cancelled' && r.status !== 'rejected')
    } catch (err) {
      console.error(err)
    }
  }
})

const isDoubles = computed(() => {
  if (!selectedCategoryId.value || !tournament.value?.categories) return false
  const cat = tournament.value.categories.find(c => c.id === selectedCategoryId.value)
  return cat?.category_type?.includes('doubles')
})

const querySearchPartner = async (queryString, cb) => {
  if (!queryString || queryString.length < 2) return cb([])
  partnerSearchLoading.value = true
  try {
    const res = await apiClient.get(`/api/players/search?keyword=${queryString}`)
    // Format data cho el-autocomplete
    const results = res.map(p => ({
      value: p.full_name,
      player_id: p.player_id,
      full_name: p.full_name,
      phone: p.phone,
      avatar_url: p.avatar_url,
      level: p.level,
      gender: p.gender // Add gender here
    }))
    cb(results)
  } catch (err) {
    console.error(err)
    cb([])
  } finally {
    partnerSearchLoading.value = false
  }
}

const handleSelectPartner = (item) => {
  partners.value[0] = {
    name: item.full_name,
    phone: item.phone,
    player_id: item.player_id,
    avatar_url: item.avatar_url,
    level: item.level,
    gender: item.gender // Store gender
  }
}

const handlePartnerNameInput = () => {
  // Khi người dùng tự gõ, xóa ID để coi như nhập thủ công
  if (partners.value[0].player_id) {
    partners.value[0].player_id = null
    partners.value[0].phone = ''
  }
}

const goToOTP = async () => {
  if (!selectedCategoryId.value) return ElMessage.warning(t('tournaments.selectCategoryAlert') || 'Vui lòng chọn nội dung thi đấu')

  if (isDoubles.value) {
    for (const p of partners.value) {
      if (!p.name || !p.player_id) return ElMessage.warning(t('tournaments.enterPartnerInfoAlert'))
    }
  }

  isSubmitting.value = true
  try {
    // 1. Kiểm tra giới tính sớm (Frontend)
    if (isDoubles.value && partners.value[0]?.gender) {
      const partnerGender = partners.value[0].gender.toLowerCase()
      const catType = selectedCategory.value?.category_type || ''
      
      let isMismatch = false
      let expectedGender = ''
      
      if (catType === 'mens_doubles' && (partnerGender === 'female' || partnerGender === 'nữ')) {
        isMismatch = true
        expectedGender = 'Nam'
      } else if (catType === 'womens_doubles' && (partnerGender === 'male' || partnerGender === 'nam')) {
        isMismatch = true
        expectedGender = 'Nữ'
      }
      
      if (isMismatch) {
        try {
          await ElMessageBox.confirm(
            `Người đồng đội bạn chọn có giới tính khác với nội dung thi đấu (${expectedGender}). Bạn có chắc chắn muốn tiếp tục không?`,
            'Cảnh báo giới tính',
            {
              confirmButtonText: 'Tiếp tục',
              cancelButtonText: 'Chọn lại',
              type: 'warning'
            }
          )
        } catch (e) {
          isSubmitting.value = false
          return // User cancelled
        }
      }
    }

    // 2. Gọi API kiểm tra sớm điều kiện đăng ký
    const partnerId = isDoubles.value && partners.value[0]?.player_id ? partners.value[0].player_id : null
    const partnerName = isDoubles.value && partners.value[0]?.name ? partners.value[0].name : null
    
    // Ensure tournamentId is used correctly as a string/number, not the whole params object
    const tid = route.params.id && !String(route.params.id).includes('[object') ? route.params.id : tournament.value?.id
    await apiClient.post(`/api/tournaments/${tid}/validate-registration`, {
      category_id: selectedCategoryId.value,
      partner_player_id: partnerId,
      partner_name: partnerName
    })

    await authService.sendOtp(userEmail.value, 'tournament_registration')
    ElMessage.success(`${t('tournaments.otpSentAlert')} ${userEmail.value}`)
    step.value = 2
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || t('tournaments.otpErrorAlert'))
  } finally {
    isSubmitting.value = false
  }
}

const submitRegistration = async () => {
  if (otpCode.value.length < 6) return ElMessage.warning(t('tournaments.enterFullOtpAlert'))

  isSubmitting.value = true
  try {
    const payload = {
      category_id: selectedCategoryId.value,
      notes: form.value.notes,
      partners: isDoubles.value ? partners.value : [],
      otp: otpCode.value,
    }
    const tid = route.params.id && !String(route.params.id).includes('[object') ? route.params.id : tournament.value?.id
    await apiClient.post(`/api/tournaments/${tid}/register`, payload)
    step.value = 3
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || t('tournaments.otpInvalidAlert'))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="neo-registration-page">
    
    <header class="neo-hero">
      <div class="hero-glow"></div>
      <div class="container hero-inner">
        <div class="hero-text">
          <span class="tour-badge"><el-icon><Ticket /></el-icon> {{ t('tournaments.officialRegistration') }}</span>
          <h1 class="tour-title">{{ tournament?.name || t('tournaments.loadingInfo') }}</h1>
        </div>
        
        <div class="neo-stepper" v-if="!isAlreadyRegistered">
          <div class="step" :class="{ 'active': step >= 1, 'completed': step > 1 }">
            <div class="step-icon"><el-icon v-if="step > 1"><Check /></el-icon><span v-else>1</span></div>
            <span class="step-text">{{ t('tournaments.stepInfo') }}</span>
          </div>
          <div class="step-line" :class="{ 'active': step >= 2 }"></div>
          
          <div class="step" :class="{ 'active': step >= 2, 'completed': step > 2 }">
            <div class="step-icon"><el-icon v-if="step > 2"><Check /></el-icon><span v-else>2</span></div>
            <span class="step-text">{{ t('tournaments.stepVerify') }}</span>
          </div>
          <div class="step-line" :class="{ 'active': step === 3 }"></div>
          
          <div class="step" :class="{ 'active': step === 3 }">
            <div class="step-icon">3</div>
            <span class="step-text">{{ t('tournaments.stepComplete') }}</span>
          </div>
        </div>
      </div>
    </header>

    <div class="container neo-grid">
      
      <main class="main-column">
        <div v-if="tournament?.categories?.length > 1" class="neo-card category-switch-card fade-in">
          <div class="neo-form-item">
            <label>{{ t('tournaments.selectCategory') || 'Chọn nội dung thi đấu' }} <span class="required">*</span></label>
            <el-select v-model="selectedCategoryId" class="w-full" placeholder="Chọn nội dung">
              <el-option 
                v-for="cat in tournament?.categories" 
                :key="cat.id" 
                :label="cat.name" 
                :value="cat.id"
              >
                <div class="flex justify-between">
                  <span>{{ cat.name }}</span>
                  <span class="text-xs text-muted">{{ cat.max_points ? `${cat.max_points} pts` : '' }}</span>
                </div>
              </el-option>
            </el-select>
          </div>
        </div>
        
        <div v-if="isAlreadyRegistered" class="neo-card alert-card fade-in">
          <div class="card-icon warning"><el-icon><WarningFilled /></el-icon></div>
          <h2>{{ t('tournaments.alreadyRegisteredTitle') }}</h2>
          <p>{{ t('tournaments.alreadyRegisteredDesc') }}</p>
          <button class="neo-btn-primary mt-4" @click="router.push('/profile?tab=tournaments')">
            {{ t('tournaments.goToProfile') }} <el-icon class="ml-2"><ArrowRight /></el-icon>
          </button>
        </div>

        <template v-else>
          <div v-if="step === 1" class="neo-card fade-in">
            <div class="card-header">
              <div class="ch-title">
                <el-icon class="ch-icon"><UserFilled /></el-icon>
                <h3>{{ t('tournaments.athleteInfoTitle') }}</h3>
              </div>
              <p class="ch-desc">{{ t('tournaments.athleteInfoDesc') }}</p>
            </div>
            
            <div class="card-body">
              <!-- CHỌN NỘI DUNG THI ĐẤU -->
              <!-- Chọn nội dung thi đấu (Chỉ hiện nếu có > 1 category) -->
              <div v-if="tournament?.categories?.length === 1" class="selected-category-banner mb-6">
                <div class="scb-label">{{ t('tournaments.category') || 'Nội dung thi đấu' }}</div>
                <div class="scb-value">{{ tournament.categories[0].name }}</div>
              </div>

              <div v-if="isDoubles" class="partner-box">
                <div class="pb-header flex justify-between items-center">
                  <span>{{ t('tournaments.partnerInfoTitle') }}</span>
                  <el-tag v-if="partners[0].player_id" type="success" effect="light" size="small" round>
                    <el-icon><CircleCheckFilled /></el-icon> Đã liên kết tài khoản
                  </el-tag>
                </div>

                <div v-if="partners[0].player_id" class="partner-selected-card">
                  <div class="psc-avatar">
                    <img :src="partners[0].avatar_url || '/default-avatar.png'" alt="Partner">
                  </div>
                  <div class="psc-info">
                    <div class="psc-name">{{ partners[0].name }}</div>
                    <div class="psc-meta">
                      <span class="psc-phone"><el-icon><Phone /></el-icon> {{ partners[0].phone }}</span>
                      <span class="psc-gender">
                        <span v-if="partners[0].gender?.toLowerCase() === 'female' || partners[0].gender?.toLowerCase() === 'nữ'">♀ Nữ</span>
                        <span v-else-if="partners[0].gender?.toLowerCase() === 'male' || partners[0].gender?.toLowerCase() === 'nam'">♂ Nam</span>
                      </span>
                      <span class="psc-level"><el-icon><Trophy /></el-icon> {{ partners[0].level || 'N/A' }}</span>
                    </div>
                  </div>
                  <button class="psc-remove" @click="handlePartnerNameInput">
                    <el-icon><Close /></el-icon>
                  </button>
                </div>

                <div v-else class="neo-form-grid">
                  <div class="neo-form-item">
                    <label>{{ t('tournaments.partnerSearch') }} <span class="required">*</span></label>
                    <el-autocomplete
                      v-model="partners[0].name"
                      :fetch-suggestions="querySearchPartner"
                      :trigger-on-focus="false"
                      placeholder="Nhập tên hoặc số điện thoại..."
                      @select="handleSelectPartner"
                      @input="handlePartnerNameInput"
                      class="w-full partner-autocomplete"
                    >
                      <template #suffix>
                        <el-icon v-if="partnerSearchLoading"><Loading /></el-icon>
                        <el-icon v-else><Search /></el-icon>
                      </template>
                      <template #default="{ item }">
                        <div class="partner-suggestion-item">
                          <el-avatar :size="32" :src="item.avatar_url || '/default-avatar.png'" />
                          <div class="psi-content">
                            <div class="psi-name">{{ item.full_name }}</div>
                            <div class="psi-meta">
                              <span>{{ item.phone }}</span>
                              <span class="gender-mini">
                                <span v-if="item.gender?.toLowerCase() === 'female' || item.gender?.toLowerCase() === 'nữ'">♀</span>
                                <span v-else-if="item.gender?.toLowerCase() === 'male' || item.gender?.toLowerCase() === 'nam'">♂</span>
                              </span>
                              <el-tag size="small" type="info" plain>{{ item.level || 'N/A' }}</el-tag>
                            </div>
                          </div>
                        </div>
                      </template>
                    </el-autocomplete>
                  </div>
                  <div class="neo-form-item">
                    <label>{{ t('tournaments.phoneNumber') }}</label>
                    <el-input v-model="partners[0].phone" placeholder="Nhập SĐT đồng đội..." />
                  </div>
                </div>
              </div>

              <div class="neo-form-item mt-4">
                <label>{{ t('tournaments.notesToOrg') }}</label>
                <el-input v-model="form.notes" type="textarea" :rows="4" :placeholder="t('tournaments.notesPlaceholder')" />
              </div>
            </div>

            <div class="card-footer">
              <button class="neo-btn-ghost" @click="router.back()">{{ t('tournaments.goBack') }}</button>
              <button class="neo-btn-primary" @click="goToOTP" :disabled="isSubmitting">
                {{ isSubmitting ? t('tournaments.processing') : t('tournaments.continueToOtp') }}
              </button>
            </div>
          </div>

          <div v-else-if="step === 2" class="neo-card fade-in">
            <div class="card-header text-center">
              <div class="ch-icon mx-auto"><el-icon><Message /></el-icon></div>
              <h3>{{ t('tournaments.verifyIdentity') }}</h3>
              <p class="ch-desc">{{ t('tournaments.otpDesc') }}</p>
            </div>
            
            <div class="card-body text-center">
              <div class="email-badge">{{ userEmail }}</div>
              
              <div class="otp-container">
                <el-input v-model="otpCode" maxlength="6" placeholder="• • • • • •" class="neo-otp-input" />
              </div>
              
              <div class="resend-block">
                <span>{{ t('tournaments.notReceivedOtp') }}</span>
                <a href="#" @click.prevent="goToOTP" :class="{'disabled': isSubmitting}">{{ t('tournaments.resendOtp') }}</a>
              </div>
            </div>
            
            <div class="card-footer space-between">
              <button class="neo-btn-ghost" @click="step = 1">{{ t('tournaments.backToEdit') }}</button>
              <button class="neo-btn-primary" @click="submitRegistration" :disabled="isSubmitting || otpCode.length < 6">
                <el-icon class="mr-2" v-if="isSubmitting"><Loading /></el-icon>
                {{ isSubmitting ? t('tournaments.verifying') : t('tournaments.confirmRegistration') }}
              </button>
            </div>
          </div>

          <div v-else-if="step === 3" class="neo-card success-card scale-up">
            <div class="card-icon success"><el-icon><Check /></el-icon></div>
            <h2>{{ t('tournaments.registrationSuccessTitle') }}</h2>
            <p v-html="t('tournaments.registrationSuccessDesc')"></p>
            
            <div class="success-actions">
              <button class="neo-btn-primary" @click="router.push('/profile?tab=tournaments')">
                {{ t('tournaments.viewETicket') }}
              </button>
            </div>
          </div>
        </template>
      </main>

      <aside class="sidebar-column">
        <div class="ticket-widget sticky">
          
          <div class="ticket-top">
            <div class="ticket-brand">Saigontennistours</div>
            <h3 class="ticket-tour-name">{{ tournament?.name || t('tournaments.loadingInfo') }}</h3>
            <div class="ticket-info-grid">
              <div class="t-info-item">
                <span>{{ t('tournaments.startDateTicket') }}</span>
                <strong>{{ safeFormatDate(tournament?.start_date) }}</strong>
              </div>
              <div class="t-info-item text-right">
                <span>{{ t('tournaments.location') }}</span>
                <strong>{{ tournament?.location || 'Saigon Center' }}</strong>
              </div>
            </div>
          </div>
          
          <div class="ticket-divider">
            <div class="notch left"></div>
            <div class="line"></div>
            <div class="notch right"></div>
          </div>
          
          <div class="ticket-bottom">
            <div class="t-summary-row">
              <div class="ts-lbl"><el-icon><Trophy /></el-icon> {{ t('tournaments.matchFormat') }}</div>
              <div class="ts-val">{{ selectedCategory ? selectedCategory.name : tournament?.format_type }}</div>
            </div>
            <div class="t-summary-row">
              <div class="ts-lbl"><el-icon><Ticket /></el-icon> {{ t('tournaments.tournamentFee') }}</div>
              <div class="ts-val price">
                {{ tournament?.entry_fee ? new Intl.NumberFormat('vi-VN').format(tournament.entry_fee) + 'đ' : t('tournaments.freeFee') }}
              </div>
            </div>
          </div>
          
        </div>
      </aside>

    </div>
  </div>
</template>

<style scoped>
/* Giữ nguyên toàn bộ cấu trúc CSS gốc */
.neo-registration-page { --navy: #002855; --navy-light: #004080; --blue-accent: #0066cc; --bg-main: #f1f5f9; --surface: #ffffff; --border-color: #e2e8f0; --text-dark: #0f172a; --text-body: #334155; --text-muted: #64748b; --success: #16a34a; --warning: #ca8a04; background-color: var(--bg-main); min-height: 100vh; padding-bottom: 5rem; font-family: 'Inter', -apple-system, sans-serif; color: var(--text-body); }
.container { max-width: 1100px; margin: 0 auto; padding: 0 1.5rem; }
.text-center { text-align: center; }
.mx-auto { margin-left: auto; margin-right: auto; }
.mt-4 { margin-top: 1.5rem; }
.ml-2 { margin-left: 8px; }
.mr-2 { margin-right: 8px; }
:deep(.el-input__inner), :deep(.el-textarea__inner) { font-family: 'Inter', sans-serif !important; }
.neo-hero { background: var(--navy); color: white; padding: 4rem 0 7rem; position: relative; overflow: hidden; margin-bottom: -5rem; }
.hero-glow { position: absolute; top: -50%; right: 10%; width: 500px; height: 500px; background: #0066cc; border-radius: 50%; filter: blur(120px); opacity: 0.4; pointer-events: none; }
.hero-inner { display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 2; flex-wrap: wrap; gap: 2rem; }
.tour-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.2); padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 1rem; backdrop-filter: blur(4px); }
.tour-title { font-size: 2.2rem; font-weight: 800; margin: 0; line-height: 1.2; letter-spacing: -0.02em;}
.neo-stepper { display: flex; align-items: center; gap: 12px; }
.step { display: flex; flex-direction: column; align-items: center; gap: 8px; opacity: 0.5; transition: 0.3s; }
.step.active, .step.completed { opacity: 1; }
.step-icon { width: 32px; height: 32px; border-radius: 50%; background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); display: flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: 700; transition: 0.3s; }
.step.active .step-icon { background: var(--blue-accent); border-color: var(--blue-accent); color: white;}
.step.completed .step-icon { background: #34d399; border-color: #34d399; color: var(--navy);}
.step-text { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;}
.step-line { width: 40px; height: 2px; background: rgba(255,255,255,0.2); margin-top: -24px;}
.step-line.active { background: var(--blue-accent); }
@media (max-width: 900px) { 
  .hero-inner { flex-direction: column; align-items: flex-start; gap: 1.25rem; } 
  .neo-stepper { width: 100%; justify-content: space-between; } 
  .step-line { flex: 1; margin-top: -18px;} 
  .step-text { display: none; } 
  .tour-title { font-size: 1.6rem; word-break: break-word; }
  .neo-grid { grid-template-columns: 1fr; gap: 1.5rem; } 
  .sidebar-column { order: 2; } 
  .neo-hero { padding: 3rem 0 4.5rem; margin-bottom: -2.5rem;}
  .sticky { position: relative; top: 0; }
}

@media (max-width: 600px) {
  .container { padding: 0 1rem; }
  .neo-hero { padding: 2.5rem 0 4rem; margin-bottom: -2rem;}
  .tour-badge { font-size: 0.7rem; padding: 4px 10px; }
  .tour-title { font-size: 1.4rem; }
  .neo-form-grid { grid-template-columns: 1fr; gap: 1rem;}
  .card-header { padding: 1.25rem 1.25rem 1rem; }
  .card-body { padding: 1.25rem; }
  .card-footer { padding: 1rem 1.25rem; flex-direction: column; gap: 0.75rem; }
  .card-footer .neo-btn-primary, .card-footer .neo-btn-ghost { width: 100%; padding: 1rem; }
  .neo-otp-input :deep(.el-input__inner) { font-size: 1.5rem; height: 55px; letter-spacing: 0.2em; }
  .ticket-widget { border-radius: 12px; }
  .ticket-top, .ticket-bottom { padding: 1.25rem; }
  .notch { width: 20px; height: 20px; }
  .notch.left { left: -11px; }
  .notch.right { right: -11px; }
}
.neo-card { background: var(--surface); border-radius: 16px; border: 1px solid var(--border-color); box-shadow: 0 10px 40px rgba(0,0,0,0.04); overflow: hidden; }
.category-switch-card { padding: 1.25rem 2rem; margin-bottom: 1rem; }
.card-header { padding: 1.5rem 2rem; border-bottom: 1px solid var(--border-color); }
.ch-title { display: flex; align-items: center; gap: 10px; margin-bottom: 6px;}
.ch-icon { font-size: 1.4rem; color: var(--blue-accent); }
.ch-title h3 { margin: 0; font-size: 1.2rem; font-weight: 800; color: var(--text-dark);}
.ch-desc { margin: 0; font-size: 0.85rem; color: var(--text-muted); line-height: 1.5;}
.card-body { padding: 2rem; }
.card-footer { padding: 1.25rem 2rem; background: #f8fafc; border-top: 1px solid var(--border-color); display: flex; justify-content: flex-end; gap: 12px; }
.card-footer.space-between { justify-content: space-between; }
.neo-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
@media (max-width: 600px) { .neo-form-grid { grid-template-columns: 1fr; gap: 1rem;} }
.neo-form-item label { display: block; font-size: 0.85rem; font-weight: 700; color: var(--text-dark); margin-bottom: 6px; }
.required { color: #ef4444; margin-left: 2px;}
:deep(.el-input__wrapper), :deep(.el-textarea__wrapper) { background: #f8fafc !important; box-shadow: 0 0 0 1px var(--border-color) inset !important; border-radius: 8px; padding: 8px 12px; }
:deep(.el-input__wrapper.is-focus), :deep(.el-textarea__wrapper.is-focus) { background: white !important; box-shadow: 0 0 0 2px var(--blue-accent) inset !important; }
.partner-box { background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; }
.pb-header { font-size: 0.9rem; font-weight: 800; color: var(--navy); margin-bottom: 1rem; text-transform: uppercase;}
.email-badge { display: inline-block; background: #e0f2fe; color: #0369a1; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 0.9rem; margin-bottom: 2rem; }
.otp-container { max-width: 320px; margin: 0 auto; }
:deep(.neo-otp-input .el-input__inner) { text-align: center; font-size: 2.2rem; letter-spacing: 0.4em; font-weight: 800; color: var(--navy); height: 70px; }
.resend-block { margin-top: 1.5rem; font-size: 0.9rem; color: var(--text-muted); }
.resend-block a { color: var(--blue-accent); font-weight: 700; text-decoration: none; margin-left: 6px; transition: 0.2s;}
.resend-block a:hover { color: var(--navy); text-decoration: underline;}
.resend-block a.disabled { color: var(--border-color); pointer-events: none;}
.neo-btn-primary { background: var(--blue-accent); color: white; border: none; padding: 0.8rem 1.5rem; border-radius: 8px; font-size: 0.9rem; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; transition: 0.2s; }
.neo-btn-primary:hover:not(:disabled) { background: #0055a4; transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0, 102, 204, 0.2);}
.neo-btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.neo-btn-ghost { background: transparent; border: 1px solid var(--border-color); color: var(--text-body); padding: 0.8rem 1.5rem; border-radius: 8px; font-size: 0.9rem; font-weight: 700; cursor: pointer; transition: 0.2s; }
.neo-btn-ghost:hover { background: #f8fafc; color: var(--text-dark); border-color: var(--text-dark);}
.alert-card, .success-card { padding: 4rem 2rem; text-align: center; display: flex; flex-direction: column; align-items: center;}
.card-icon { width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; margin-bottom: 1.5rem; }
.card-icon.warning { background: #fef9c3; color: var(--warning); }
.card-icon.success { background: #dcfce7; color: var(--success); }
.alert-card h2, .success-card h2 { margin: 0 0 1rem; color: var(--text-dark); font-weight: 800;}
.alert-card p, .success-card p { margin: 0; color: var(--text-muted); line-height: 1.6;}
.success-actions { margin-top: 2rem; }
.sticky { position: sticky; top: 24px; }
.ticket-widget { background: var(--surface); border-radius: 16px; border: 1px solid var(--border-color); box-shadow: 0 20px 40px rgba(0,0,0,0.06); overflow: hidden; }
.ticket-top { padding: 1.5rem; background: var(--navy); color: white;}
.ticket-brand { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em; color: #cbd5e1; margin-bottom: 1rem; text-transform: uppercase;}
.ticket-tour-name { font-size: 1.25rem; font-weight: 800; margin: 0 0 1.5rem; line-height: 1.3;}
.ticket-info-grid { display: flex; justify-content: space-between; }
.t-info-item { display: flex; flex-direction: column; gap: 4px; }
.t-info-item span { font-size: 0.65rem; color: #94a3b8; text-transform: uppercase; font-weight: 600;}
.t-info-item strong { font-size: 0.9rem; color: white; font-weight: 700;}
.ticket-divider { height: 24px; position: relative; background: var(--surface); display: flex; align-items: center; }
.notch { width: 24px; height: 24px; background: var(--bg-main); border-radius: 50%; position: absolute; border: 1px solid var(--border-color); }
.notch.left { left: -13px; border-right-color: transparent; border-top-color: transparent; transform: rotate(45deg);}
.notch.right { right: -13px; border-left-color: transparent; border-bottom-color: transparent; transform: rotate(45deg);}
.ticket-divider .line { flex: 1; height: 1px; border-top: 2px dashed var(--border-color); margin: 0 20px; }
.ticket-bottom { padding: 1.5rem; background: var(--surface);}
.t-summary-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.t-summary-row:last-child { margin-bottom: 0; }
.ts-lbl { font-size: 0.85rem; color: var(--text-muted); font-weight: 600; display: flex; align-items: center; gap: 8px;}
.ts-lbl .el-icon { color: var(--navy); }
.ts-val { font-size: 0.95rem; font-weight: 700; color: var(--text-dark);}
.ts-val.price { font-size: 1.2rem; color: var(--blue-accent); font-weight: 800;}
.fade-in { animation: fadeIn 0.4s ease forwards; }
.scale-up { animation: scaleUp 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes scaleUp { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }

/* Partner selection styles */
.partner-selected-card { display: flex; align-items: center; gap: 1rem; background: white; border: 1px solid var(--blue-accent); padding: 1rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 102, 204, 0.08); position: relative; animation: slideIn 0.3s ease; margin-top: 0.5rem; }
.psc-avatar { width: 48px; height: 48px; border-radius: 50%; overflow: hidden; border: 2px solid #e2e8f0; flex-shrink: 0; }
.psc-avatar img { width: 100%; height: 100%; object-fit: cover; }
.psc-info { flex: 1; }
.psc-name { font-size: 1rem; font-weight: 800; color: var(--text-dark); margin-bottom: 2px; }
.psc-meta { display: flex; gap: 12px; font-size: 0.8rem; color: var(--text-muted); font-weight: 500; }
.psc-meta span { display: flex; align-items: center; gap: 4px; }
.psc-meta .el-icon { color: var(--blue-accent); }
.psc-remove { width: 28px; height: 28px; border-radius: 50%; border: none; background: #f1f5f9; color: var(--text-muted); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; }
.psc-remove:hover { background: #fee2e2; color: #ef4444; transform: rotate(90deg); }

.partner-suggestion-item { display: flex; align-items: center; gap: 10px; padding: 4px 0; }
.psi-content { flex: 1; line-height: 1.4; }
.psi-name { font-size: 0.9rem; font-weight: 700; color: var(--text-dark); }
.psi-meta { display: flex; align-items: center; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }

@keyframes slideIn { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }

/* Customize el-autocomplete dropdown */
:deep(.el-autocomplete-suggestion li) { padding: 8px 12px !important; border-bottom: 1px solid #f1f5f9; }
:deep(.el-autocomplete-suggestion li:last-child) { border-bottom: none; }
:deep(.el-autocomplete-suggestion li:hover) { background-color: #f0f7ff !important; }

.partner-autocomplete :deep(.el-input__wrapper) { padding-right: 12px; }
.selected-category-banner {
  background: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.scb-label {
  font-size: 12px;
  color: var(--el-color-primary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.scb-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}
</style>
