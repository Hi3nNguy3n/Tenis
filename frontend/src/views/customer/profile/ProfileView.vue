<script setup>
import { onMounted, ref, computed } from 'vue'
import { currentLocale, t } from '../../../utils/locale'
import { useAuthStore } from '../../../stores/auth'
import { useTournamentStore } from '../../../stores/tournament'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  CameraFilled, 
  Trophy, 
  Refresh, 
  CreditCard, 
  Check, 
  Close,
  User,
  Iphone,
  Calendar as CalendarIcon,
  Timer,
  Menu,
  ArrowDown,
  Setting
} from '@element-plus/icons-vue'

import { playerService } from '../../../services/playerService'
import { apiClient } from '../../../services/apiClient'

const authStore = useAuthStore()
const tournamentStore = useTournamentStore()
const isEditing = ref(false)
const isLoading = ref(false)
const matchHistory = ref([])
const avatarFile = ref(null)

const editForm = ref({
  full_name: '',
  email: '',
  phone: '',
  gender: '',
  date_of_birth: '',
  province: '',
  play_hand: ''
})

// --- LOGIC THÁCH ĐẤU ---
const challenges = ref([])
const activeTab = ref('info') // info, challenges, tournaments, security
const isProcessing = ref(false)

const loadMyChallenges = async () => {
  isProcessing.value = true
  try {
    const data = await apiClient.get('/api/challenges/my-challenges')
    challenges.value = data
  } catch (err) {
    console.error('Lỗi tải kèo thách đấu:', err)
  } finally {
    isProcessing.value = false
  }
}

const handleRespond = async (challengeId, status) => {
  try {
    const actionText = status === 'accepted' ? t('profile.accept') : t('profile.reject');
    await ElMessageBox.confirm(t('profile.respondConfirm', { action: actionText }), t('common.confirm'));
    
    await apiClient.patch(`/api/challenges/${challengeId}/respond`, { status })
    ElMessage.success(status === 'accepted' ? t('profile.acceptSuccess') : t('profile.rejectSuccess'))
    loadMyChallenges() 
  } catch (err) {
    if (err !== 'cancel') ElMessage.error(t('common.errorLoading'))
  }
}

const handlePay = async (challengeId) => {
  try {
    const res = await apiClient.post(`/api/payments/challenge/${challengeId}/create-url`)
    if (res.payment_url) {
      window.location.href = res.payment_url 
    }
  } catch (err) {
    ElMessage.error(t('profile.paymentError'))
  }
}

const getChallengeStatus = (status) => {
  const map = {
    'pending': { label: t('challenges.pending') || 'Chờ duyệt', type: 'warning' },
    'waiting_payment': { label: t('challenges.waiting_payment') || 'Chờ thanh toán', type: 'danger' },
    'paid': { label: t('challenges.paid') || 'Đã thanh toán', type: 'success' },
    'scheduled': { label: t('challenges.scheduled') || 'Đã lên lịch', type: 'primary' },
    'rejected': { label: t('challenges.rejected') || 'Đã từ chối', type: 'info' }
  }
  return map[status] || { label: status, type: 'info' }
}

onMounted(async () => {
  try {
    const profileData = await authStore.fetchCurrentProfile()
    
    if (authStore.user) {
      editForm.value = { 
        full_name: authStore.user.full_name,
        phone: authStore.user.phone,
        gender: profileData?.player_profile?.gender || authStore.user.gender,
        date_of_birth: profileData?.player_profile?.date_of_birth || authStore.user.date_of_birth,
        province: authStore.user.province || '',
        play_hand: profileData?.player_profile?.play_hand || ''
      }
    }

    const history = await playerService.getMatchHistory()
    matchHistory.value = history || []
    
  loadMyChallenges() 
    await tournamentStore.fetchMyRegistrations() 
    
    // Handle tab from query param
    const urlParams = new URLSearchParams(window.location.search)
    const tab = urlParams.get('tab')
    if (tab && ['info', 'challenges', 'tournaments', 'security'].includes(tab)) {
      activeTab.value = tab
    }
  } catch (error) {
    console.error('Lỗi khi tải dữ liệu hồ sơ:', error)
  }
})

const startEdit = () => {
  editForm.value = { ...authStore.user }
  isEditing.value = true
}

const handleAvatarUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  isLoading.value = true
  try {
    const data = await playerService.uploadAvatar(file)
    authStore.user.avatar_url = data.avatar_url
    ElMessage.success(t('profile.avatarSuccess'))
  } catch (err) {
    ElMessage.error(err.message || t('common.error'))
  } finally {
    isLoading.value = false
  }
}

const handleUpdate = async () => {
  isLoading.value = true
  try {
    const data = await playerService.updateMe(editForm.value)
    authStore.user = { ...authStore.user, ...editForm.value }
    isEditing.value = false
    ElMessage.success(t('profile.updateSuccess'))
  } catch (error) {
    ElMessage.error(error.message || t('common.error'))
  } finally {
    isLoading.value = false
  }
}

// --- LOGIC ĐỔI MẬT KHẨU ---
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const handlePasswordChange = async () => {
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    ElMessage.error(t('profile.passwordMismatch'))
    return
  }
  isLoading.value = true
  try {
    const url = `/api/auth/change-password?old_password=${encodeURIComponent(passwordForm.value.old_password)}&new_password=${encodeURIComponent(passwordForm.value.new_password)}`
    await apiClient.post(url)
    ElMessage.success(t('profile.changeSuccess'))
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch (err) {
    ElMessage.error(err.message || t('common.error'))
  } finally {
    isLoading.value = false
  }
}

// --- MOBILE MENU LOGIC ---
const showMobileMenu = ref(false)
const selectTab = (tab) => {
  activeTab.value = tab
  showMobileMenu.value = false
}
</script>

<template>
  <div class="profile-page-wrapper">
    <!-- KHU VỰC HERO BANNER -->
    <section class="profile-hero-banner">
      <div class="banner-bg"></div>
      <div class="banner-overlay"></div>

      <div class="container hero-content-shell">
        <div class="hero-flex">
          <div class="avatar-container">
            <div class="avatar-frame">
              <img v-if="authStore.user?.avatar_url" :src="authStore.user.avatar_url" alt="Avatar" />
              <div v-else class="avatar-placeholder">👤</div>
              
              <label class="avatar-upload-overlay" for="avatar-input">
                <el-icon><CameraFilled /></el-icon>
              </label>
              <input 
                id="avatar-input" 
                type="file" 
                accept="image/*" 
                style="display: none;" 
                @change="handleAvatarUpload" 
              />
            </div>
          </div>

          <div class="hero-text-block">
            <span class="user-role-badge">
              {{ authStore.isAdmin ? t('profile.roleAdmin') : t('profile.roleAthlete') }}
            </span>

            <h1>{{ authStore.user?.full_name || t('chat.user') }}</h1>

            <div class="hero-quick-stats">
              <div class="stat-item">
                <span class="stat-val">#{{ authStore.profile?.player_profile?.rank || '---' }}</span>
                <span class="stat-lbl">{{ t('profile.rank') }}</span>
              </div>
              <div class="stat-sep"></div>
              <div class="stat-item">
                <span class="stat-val">{{ authStore.profile?.player_profile?.wins || 0 }}</span>
                <span class="stat-lbl">{{ t('profile.win') }}</span>
              </div>
              <div class="stat-sep"></div>
              <div class="stat-item">
                <span class="stat-val">{{ authStore.profile?.player_profile?.losses || 0 }}</span>
                <span class="stat-lbl">{{ t('profile.loss') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- KHU VỰC MAIN LAYOUT CÓ SIDEBAR -->
    <div class="container main-layout-container">
      <div class="layout-grid">
        
        <!-- SIDEBAR ĐIỀU HƯỚNG BÊN TRÁI -->
        <aside class="compact-sidebar">
          
          <button :class="['mobile-menu-toggle', { 'is-active': showMobileMenu }]" @click="showMobileMenu = !showMobileMenu">
            <div class="hamburger-box">
              <span class="hamburger-inner"></span>
            </div>
            <span class="toggle-text">{{ t('profile.categoryProfile') || 'Danh mục' }}</span>
            <el-icon class="arrow-icon" :class="{ rotate: showMobileMenu }"><ArrowDown /></el-icon>
          </button>

          <nav class="sidebar-nav" :class="{ 'mobile-open': showMobileMenu }">
            <button class="nav-btn" :class="{ active: activeTab === 'info' }" @click="selectTab('info')">
              <el-icon class="nav-icon"><User /></el-icon>
              <span>{{ t('profile.sections.info') || 'Thông tin chung' }}</span>
            </button>

            <button class="nav-btn btn-challenge-nav" :class="{ active: activeTab === 'challenges' }" @click="selectTab('challenges')">
              <el-icon class="nav-icon"><Trophy /></el-icon>
              <span>{{ t('profile.sections.challenges') || 'Thách đấu' }}</span>
              <el-badge v-if="challenges.filter(c => c.status === 'pending' && c.challenged_id === authStore.profile?.player_profile?.id).length > 0" 
                        :value="challenges.filter(c => c.status === 'pending' && c.challenged_id === authStore.profile?.player_profile?.id).length" 
                        class="nav-badge" />
            </button>

            <button class="nav-btn" :class="{ active: activeTab === 'tournaments' }" @click="selectTab('tournaments')">
              <el-icon class="nav-icon"><CalendarIcon /></el-icon>
              <span>{{ t('profile.sections.tournaments') || 'Giải đấu' }}</span>
            </button>

            <button class="nav-btn" :class="{ active: activeTab === 'security' }" @click="selectTab('security')">
              <el-icon class="nav-icon"><Setting /></el-icon>
              <span>{{ t('profile.sections.security') || 'Bảo mật' }}</span>
            </button>
          </nav>
        </aside>

        <!-- NỘI DUNG CHÍNH BÊN PHẢI -->
        <main class="content-primary">
          
          <!-- TAB 1: THÔNG TIN CÁ NHÂN -->
          <div v-if="activeTab === 'info'" class="tab-fade-in">
            <article class="atp-card">
              <div class="card-header-flex">
                <div class="section-title-wrap">
                  <h2 class="atp-section-title">{{ t('profile.personalInfo') }}</h2>
                  <div class="section-line"></div>
                </div>
                <button v-if="!isEditing" type="button" class="btn-atp-outline" @click="startEdit">{{ t('profile.edit') }}</button>
              </div>

              <!-- View Mode -->
              <div v-if="!isEditing" class="data-display-grid">
                <div class="display-item"><label>{{ t('profile.fullName') }}</label><p>{{ authStore.user?.full_name || '---' }}</p></div>
                <div class="display-item"><label>{{ t('profile.email') }}</label><p class="text-break email-value">{{ authStore.user?.email || '---' }}</p></div>
                <div class="display-item"><label>{{ t('profile.phone') }}</label><p>{{ authStore.user?.phone || t('profile.notUpdated') }}</p></div>
                <div class="display-item"><label>{{ t('profile.gender') }}</label><p>{{ authStore.user?.gender === 'male' ? t('profile.male') : authStore.user?.gender === 'female' ? t('profile.female') : t('profile.other') }}</p></div>
                
                <div class="display-item"><label>{{ t('profile.dob') }}</label><p>{{ authStore.profile?.player_profile?.date_of_birth || authStore.user?.date_of_birth ? new Date(authStore.profile?.player_profile?.date_of_birth || authStore.user?.date_of_birth).toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US') : t('profile.notUpdated') }}</p></div>
                <div class="display-item"><label>{{ t('profile.province') }}</label><p>{{ authStore.user?.province || t('profile.notUpdated') }}</p></div>
                <div class="display-item"><label>{{ t('profile.playHand') }}</label><p>{{ authStore.profile?.player_profile?.play_hand === 'right' ? t('profile.right') : authStore.profile?.player_profile?.play_hand === 'left' ? t('profile.left') : authStore.profile?.player_profile?.play_hand === 'both' ? t('profile.both') : t('profile.notUpdated') }}</p></div>
              </div>

              <!-- Edit Mode -->
              <el-form v-else :model="editForm" label-position="top" class="atp-form-modern">
                <div class="form-grid">
                  <el-form-item :label="t('profile.fullName')"><el-input v-model="editForm.full_name" /></el-form-item>
                  <el-form-item :label="t('profile.phone')"><el-input v-model="editForm.phone" /></el-form-item>
                  <el-form-item :label="t('profile.gender')">
                    <el-select v-model="editForm.gender" style="width: 100%">
                      <el-option :label="t('profile.male')" value="male" />
                      <el-option :label="t('profile.female')" value="female" />
                      <el-option :label="t('profile.other')" value="other" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item :label="t('profile.dob')">
                    <el-input type="date" v-model="editForm.date_of_birth" />
                  </el-form-item>
                  <el-form-item :label="t('profile.province')">
                    <el-input v-model="editForm.province" :placeholder="t('profile.provincePlaceholder')" />
                  </el-form-item>
                  <el-form-item :label="t('profile.playHand')">
                    <el-select v-model="editForm.play_hand" style="width: 100%">
                      <el-option :label="t('profile.right')" value="right" />
                      <el-option :label="t('profile.left')" value="left" />
                      <el-option :label="t('profile.both')" value="both" />
                    </el-select>
                  </el-form-item>
                </div>
                
                <div class="form-actions-row">
                  <button type="button" class="btn-atp-text" @click="isEditing = false">{{ t('profile.cancel') }}</button>
                  <button type="button" class="btn-atp-solid" :disabled="isLoading" @click="handleUpdate">{{ isLoading ? t('profile.saving') : t('profile.save') }}</button>
                </div>
              </el-form>
            </article>

            <!-- LỊCH SỬ THI ĐẤU (Nằm trong Tab Info) -->
            <article class="atp-card mt-3">
              <div class="section-title-wrap table-head">
                <h2 class="atp-section-title">{{ t('profile.matchHistory') }}</h2>
                <div class="section-line"></div>
              </div>
              
              <!-- Desktop Table -->
              <div class="atp-table-wrapper hide-mobile">
                <el-table :data="matchHistory" :empty-text="t('profile.noMatchData')" style="width: 100%">
                  <el-table-column prop="time" label="Thời gian" width="160" />
                  <el-table-column prop="tournament_name" label="Giải đấu" />
                  <el-table-column prop="opponent" label="Đối thủ" />
                  <el-table-column prop="round" label="Vòng" width="100" />
                  <el-table-column prop="status" label="Kết quả" width="100">
                      <template #default="scope">
                        <span :class="['result-tag', scope.row.status === 'THẮNG' ? 'win' : 'lose']">{{ scope.row.status === 'THẮNG' ? t('profile.winTag') : t('profile.loseTag') }}</span>
                      </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- Mobile List -->
              <div class="mobile-history-list hide-desktop">
                <div v-for="(match, idx) in matchHistory" :key="idx" class="mobile-match-item">
                  <div class="m-match-header">
                    <span :class="['result-tag', match.status === 'THẮNG' ? 'win' : 'lose']">{{ match.status === 'THẮNG' ? t('profile.winTag') : t('profile.loseTag') }}</span>
                    <span class="m-match-time">{{ match.time }}</span>
                  </div>
                  <div class="m-match-body">
                    <div class="m-match-row"><b>Giải đấu:</b> <span>{{ match.tournament_name }}</span></div>
                    <div class="m-match-row"><b>Đối thủ:</b> <span>{{ match.opponent }}</span></div>
                    <div class="m-match-row"><b>Vòng:</b> <span>{{ match.round }}</span></div>
                  </div>
                </div>
                <el-empty v-if="matchHistory.length === 0" :description="t('profile.noMatchData')" />
              </div>
            </article>
          </div>

          <!-- TAB 2: DANH SÁCH THÁCH ĐẤU -->
          <div v-else-if="activeTab === 'challenges'" class="tab-fade-in">
            <article class="atp-card">
              <div class="card-header-flex">
                <div class="section-title-wrap">
                  <h2 class="atp-section-title">{{ t('profile.challenge1v1') }}</h2>
                  <div class="section-line"></div>
                </div>
                <el-button :icon="Refresh" circle @click="loadMyChallenges" :loading="isProcessing" />
              </div>

              <!-- Desktop Table -->
              <div class="atp-table-wrapper hide-mobile" v-loading="isProcessing">
                <el-table :data="challenges" stripe style="width: 100%">
                  <el-table-column :label="t('profile.opponentContact')" min-width="220">
                    <template #default="{ row }">
                      <div class="opponent-cell">
                        <el-avatar :size="40" :src="row.opponent_avatar" class="mr-3" />
                        <div class="opp-info">
                          <span class="role-hint">{{ row.challenger_id === authStore.profile?.player_profile?.id ? 'Bạn thách đấu:' : 'Thách đấu bạn:' }}</span>
                          <b class="opp-name">{{ row.opponent_name }}</b>
                          <div class="opp-contact">
                            <el-icon><Iphone /></el-icon> {{ row.opponent_phone || t('profile.noPhone') }}
                          </div>
                        </div>
                      </div>
                    </template>
                  </el-table-column>

                  <el-table-column :label="t('profile.proposedDate')" width="140">
                    <template #default="{ row }">
                      <div class="date-cell">
                        <el-icon class="mr-1"><CalendarIcon /></el-icon>
                        <span>{{ new Date(row.proposed_date).toLocaleDateString('vi-VN') }}</span>
                      </div>
                    </template>
                  </el-table-column>

                  <el-table-column :label="t('profile.status')" width="140">
                    <template #default="{ row }">
                      <el-tag :type="getChallengeStatus(row.status).type" effect="dark" size="small" round>
                        {{ getChallengeStatus(row.status).label.toUpperCase() }}
                      </el-tag>
                    </template>
                  </el-table-column>

                  <el-table-column :label="t('profile.actions')" width="220" align="right">
                    <template #default="{ row }">
                      <!-- Trạng thái: Mình được mời và chờ phản hồi -->
                      <div v-if="row.status === 'pending' && row.challenged_id === authStore.profile?.player_profile?.id" class="action-flex">
                        <el-button type="success" size="small" :icon="Check" circle @click="handleRespond(row.id, 'accepted')" title="Chấp nhận" />
                        <el-button type="danger" size="small" :icon="Close" circle @click="handleRespond(row.id, 'rejected')" title="Từ chối" />
                      </div>

                      <!-- Trạng thái: Chờ thanh toán lệ phí -->
                      <div v-if="row.status === 'waiting_payment'" class="action-flex">
                        <el-button type="primary" size="small" :icon="CreditCard" @click="handlePay(row.id)">{{ t('profile.payFee') || 'Thanh toán ngay' }}</el-button>
                      </div>

                      <span v-if="row.status === 'paid'" class="status-hint">{{ t('profile.adminScheduling') || 'Chờ BTC xếp lịch' }}</span>
                      <span v-if="row.status === 'pending' && row.challenger_id === authStore.profile?.player_profile?.id" class="status-hint">{{ t('profile.waitingOpponent') || 'Chờ đối thủ phản hồi' }}</span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- Mobile Challenge List -->
              <div class="mobile-challenge-list hide-desktop" v-loading="isProcessing">
                <div v-for="row in challenges" :key="row.id" class="mobile-challenge-card">
                  <div class="m-ch-header">
                    <el-avatar :size="36" :src="row.opponent_avatar" />
                    <div class="m-ch-names">
                      <span class="role-hint">{{ row.challenger_id === authStore.profile?.player_profile?.id ? 'Bạn thách đấu' : 'Thách đấu bạn' }}</span>
                      <b class="m-opp-name">{{ row.opponent_name }}</b>
                    </div>
                    <el-tag :type="getChallengeStatus(row.status).type" size="small" effect="dark" round>
                      {{ getChallengeStatus(row.status).label }}
                    </el-tag>
                  </div>
                  <div class="m-ch-info">
                    <div class="m-info-line"><el-icon><Iphone /></el-icon> {{ row.opponent_phone || t('profile.notUpdated') }}</div>
                    <div class="m-info-line"><el-icon><CalendarIcon /></el-icon> {{ new Date(row.proposed_date).toLocaleDateString('vi-VN') }}</div>
                  </div>
                  <div class="m-ch-actions">
                    <div v-if="row.status === 'pending' && row.challenged_id === authStore.profile?.player_profile?.id" class="m-action-flex">
                      <el-button type="success" size="default" block @click="handleRespond(row.id, 'accepted')">{{ t('profile.acceptBtn') || 'Đồng ý' }}</el-button>
                      <el-button type="danger" size="default" block @click="handleRespond(row.id, 'rejected')">{{ t('profile.rejectBtn') || 'Từ chối' }}</el-button>
                    </div>
                    <el-button v-if="row.status === 'waiting_payment'" type="primary" block :icon="CreditCard" @click="handlePay(row.id)">{{ t('profile.payFee') }}</el-button>
                    <span v-if="row.status === 'paid'" class="m-status-hint">{{ t('profile.adminScheduling') }}</span>
                    <span v-if="row.status === 'pending' && row.challenger_id === authStore.profile?.player_profile?.id" class="m-status-hint">{{ t('profile.waitingOpponent') }}</span>
                  </div>
                </div>
                <el-empty v-if="challenges.length === 0" :description="t('profile.noChallenges')" />
              </div>
            </article>
          </div>

          <!-- TAB 3: GIẢI ĐẤU ĐÃ ĐĂNG KÝ -->
          <div v-else-if="activeTab === 'tournaments'" class="tab-fade-in">
            <div v-if="tournamentStore.myRegistrations?.length" class="tournaments-stack">
              <article v-for="reg in tournamentStore.myRegistrations" :key="reg.id" class="atp-tour-card">
                <div class="tour-main-info">
                  <div class="tour-header-row">
                    <span class="tour-category">Saigontennistours</span>
                    <span :class="['atp-status-pill', reg.payment_status]">
                      {{ reg.payment_status === 'confirmed' ? 'Đã xác nhận' : 'Đang xử lý' }}
                    </span>
                  </div>
                  <h2 class="atp-tour-name">{{ reg.tournament_name }}</h2>
                  <div class="tour-meta-grid">
                    <div class="m-item"><span class="m-label">Hạng đấu</span><span class="m-val">{{ reg.category_type || 'Chuyên nghiệp' }}</span></div>
                    <div class="m-item"><span class="m-label">Ngày thi đấu</span><span class="m-val">{{ reg.tournament_date ? new Date(reg.tournament_date).toLocaleDateString() : 'TBD' }}</span></div>
                    <div class="m-item"><span class="m-label">Địa điểm</span><span class="m-val">{{ reg.location || 'Saigon Tennis Center' }}</span></div>
                  </div>
                </div>
                <div class="atp-ticket-stub">
                  <div class="stub-qr-box">
                    <img :src="reg.qr_code_url || `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=STT_REG_${reg.id}`" alt="QR Code" />
                  </div>
                  <span class="stub-label">Mã đăng ký</span>
                  <code>#{{ reg.id.toString().slice(-8).toUpperCase() }}</code>
                </div>
              </article>
            </div>
            <div v-else class="atp-empty-state-card">
              <div class="empty-visual">🎾</div>
              <h3>{{ t('profile.noTournaments') || 'Bạn chưa đăng ký giải đấu nào' }}</h3>
              <p>{{ t('profile.exploreTournaments') || 'Hãy tham gia các giải đấu hấp dẫn đang diễn ra' }}</p>
              <RouterLink to="/tournaments" class="btn-atp-solid">{{ t('profile.findTournamentBtn') || 'Tìm Giải Đấu' }}</RouterLink>
            </div>
          </div>

          <!-- TAB 4: BẢO MẬT & ĐỔI MẬT KHẨU -->
          <div v-else-if="activeTab === 'security'" class="tab-fade-in">
            <article class="atp-card">
              <div class="section-title-wrap">
                <h2 class="atp-section-title">{{ t('profile.changePassword') }}</h2>
                <div class="section-line"></div>
              </div>
              <p class="section-hint mb-4" style="color: #64748b;">{{ t('profile.securityHint') || 'Để bảo mật tài khoản, vui lòng không chia sẻ mật khẩu cho bất kỳ ai.' }}</p>

              <form @submit.prevent="handlePasswordChange" class="atp-form-modern">
                <div class="form-stack-full">
                  <div class="atp-form-group">
                    <label>{{ t('profile.currentPassword') }}</label>
                    <el-input v-model="passwordForm.old_password" type="password" show-password :placeholder="t('profile.currentPasswordPlaceholder')" />
                  </div>
                  <div class="atp-form-group mt-3">
                    <label>{{ t('profile.newPassword') }}</label>
                    <el-input v-model="passwordForm.new_password" type="password" show-password :placeholder="t('profile.newPasswordPlaceholder')" />
                  </div>
                  <div class="atp-form-group mt-3">
                    <label>{{ t('profile.confirmPassword') }}</label>
                    <el-input v-model="passwordForm.confirm_password" type="password" show-password :placeholder="t('profile.confirmPasswordPlaceholder')" />
                  </div>
                </div>
                <div class="form-actions-row mt-4">
                  <button type="submit" class="btn-atp-solid" :disabled="isLoading">
                    {{ isLoading ? t('profile.saving') : t('profile.updatePasswordBtn') || 'Cập nhật Mật khẩu' }}
                  </button>
                </div>
              </form>
            </article>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* =======================================================
   BASE THEME
   ======================================================= */
.profile-page-wrapper {
  --profile-primary: #002855; /* Navy Blue ATP */
  --profile-primary-dark: #001f44;
  --profile-secondary: #c1ff72; /* Dạ quang */
  --profile-soft-bg: #f8fafc;
  --profile-border: #e2e8f0;
  --profile-text: #0f172a;
  --profile-muted: #64748b;
  --profile-shadow: 0 4px 15px rgba(0,0,0,0.03);
  
  font-family: 'Inter', Arial, sans-serif !important;
  background: var(--profile-soft-bg);
  min-height: 100vh;
  padding-bottom: 3rem;
}

/* =======================================================
   HERO BANNER
   ======================================================= */
.profile-hero-banner { 
  position: relative; 
  min-height: 280px; 
  background: var(--profile-primary); 
  display: flex;
  align-items: center;
  overflow: hidden;
}

.banner-bg { 
  position: absolute; inset: 0; 
  background-image: url('/src/assets/hero_bg.png'); 
  background-size: cover; background-position: center; opacity: 0.15; 
}
.banner-overlay { 
  position: absolute; inset: 0; 
  background: linear-gradient(90deg, rgba(0, 40, 85, 0.95) 0%, rgba(0, 40, 85, 0.7) 100%); 
}

.hero-content-shell { position: relative; z-index: 2; width: 100%; max-width: 1280px; margin: 0 auto; }
.hero-flex { 
  display: flex; align-items: center; gap: 2.5rem; padding: 2.5rem 1.5rem;
}

/* Avatar Frame */
.avatar-frame { 
  position: relative; 
  width: 140px; height: 140px; 
  background: #fff; border-radius: 50%; 
  padding: 4px; box-shadow: 0 10px 25px rgba(0,0,0,0.3);
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.avatar-frame img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }
.avatar-placeholder { font-size: 3.5rem; }

.avatar-upload-overlay { 
  position: absolute; right: 0px; bottom: 5px; 
  width: 36px; height: 36px; 
  background: var(--profile-secondary); color: var(--profile-primary); 
  display: flex; align-items: center; justify-content: center; 
  border-radius: 50%; cursor: pointer; border: 3px solid #fff; 
  transition: 0.2s; font-size: 1.1rem;
}
.avatar-upload-overlay:hover { transform: scale(1.1); }

/* Text Block */
.hero-text-block { color: #fff; flex: 1; min-width: 0; }
.user-role-badge { 
  padding: 0.3rem 0.8rem; border-radius: 4px; 
  background: var(--profile-secondary); color: var(--profile-primary); 
  font-size: 0.7rem; font-weight: 800; text-transform: uppercase; 
  margin-bottom: 0.75rem; display: inline-block; 
}
.hero-text-block h1 { margin: 0 0 1rem; font-size: 2.5rem; font-weight: 800; letter-spacing: -0.02em; color: #fff; }

.hero-quick-stats { 
  display: inline-flex; gap: 1.5rem; padding: 0.8rem 1.5rem; 
  border-radius: 8px; background: rgba(255, 255, 255, 0.1); 
  backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.15);
}
.stat-item { text-align: center; }
.stat-val { display: block; color: var(--profile-secondary); font-size: 1.4rem; font-weight: 800; }
.stat-lbl { display: block; color: #e2e8f0; font-size: 0.65rem; text-transform: uppercase; font-weight: 600; letter-spacing: 1px;}
.stat-sep { width: 1px; background: rgba(255, 255, 255, 0.2); }

/* =======================================================
   MAIN LAYOUT & SIDEBAR
   ======================================================= */
.main-layout-container { max-width: 1280px; margin: 0 auto; padding: 0 1.5rem; }
.layout-grid { display: grid; grid-template-columns: 240px 1fr; gap: 2.5rem; margin-top: -2.5rem; position: relative; z-index: 5; }

.sidebar-nav { position: sticky; top: 100px; display: flex; flex-direction: column; gap: 0.5rem; }

.nav-btn { 
  display: flex; align-items: center; padding: 1rem 1.25rem; 
  border-radius: 8px; background: #fff; color: var(--profile-muted); 
  font-size: 0.85rem; font-weight: 700; text-transform: uppercase; 
  transition: 0.2s; border: 1px solid var(--profile-border); 
  box-shadow: var(--profile-shadow); cursor: pointer;
  letter-spacing: 0.05em;
}
.nav-icon { margin-right: 12px; font-size: 1.2rem; }
.nav-btn.active { background: var(--profile-primary); color: #fff; border-color: var(--profile-primary); }
.nav-btn:hover:not(.active) { border-color: var(--profile-primary); color: var(--profile-primary); }

.nav-badge { margin-left: auto; }

/* =======================================================
   CARDS & FORMS
   ======================================================= */
.atp-card { 
  background: #fff; border: 1px solid var(--profile-border); 
  border-radius: 12px; padding: 2rem 2.5rem; 
  box-shadow: var(--profile-shadow); margin-bottom: 2rem;
  max-width: 1000px;
}
.card-header-flex { 
  display: flex; 
  justify-content: flex-start; 
  align-items: flex-end; 
  gap: 2rem;
  margin-bottom: 2rem; 
}
.card-header-flex .btn-atp-outline {
  margin-left: auto;
}
.atp-section-title { margin: 0; font-size: 1.4rem; font-weight: 800; text-transform: uppercase; color: var(--profile-primary); }
.section-line { width: 40px; height: 3px; background: var(--profile-secondary); margin-top: 0.8rem; }

.data-display-grid { 
  display: grid; 
  grid-template-columns: repeat(2, minmax(200px, 350px)); 
  gap: 2rem 3rem; 
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem 2rem;
}
.display-item label { font-size: 0.7rem; color: var(--profile-muted); text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 0.5rem; letter-spacing: 0.05em;}
.display-item p { font-size: 1rem; font-weight: 600; color: var(--profile-text); margin: 0; word-break: break-all; }

/* Nút Bấm */
.btn-atp-outline {
  background: transparent; border: 2px solid var(--profile-primary);
  color: var(--profile-primary); padding: 0.5rem 1.5rem;
  border-radius: 4px; font-weight: 700; text-transform: uppercase;
  font-size: 0.8rem; cursor: pointer; transition: 0.2s;
}
.btn-atp-outline:hover { background: var(--profile-primary); color: #fff; }

.btn-atp-solid {
  background: var(--profile-primary); border: none;
  color: #fff; padding: 0.6rem 2rem; border-radius: 4px; 
  font-weight: 700; text-transform: uppercase; font-size: 0.85rem; 
  cursor: pointer; transition: 0.2s;
}
.btn-atp-solid:hover { background: var(--profile-primary-dark); }
.btn-atp-text { background: none; border: none; color: var(--profile-muted); font-weight: 600; cursor: pointer;}

.form-actions-row { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 2rem;}

/* Table (Lịch sử, Thách đấu) */
.atp-table-wrapper { border: 1px solid var(--profile-border); border-radius: 8px; overflow: hidden; }
:deep(.el-table th) { background: #f8fafc !important; color: var(--profile-primary); font-weight: 800; text-transform: uppercase; font-size: 0.75rem;}
.result-tag { font-size: 0.7rem; font-weight: 700; padding: 4px 10px; border-radius: 4px; text-transform: uppercase;}
.result-tag.win { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0;}
.result-tag.lose { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca;}

.opponent-cell { display: flex; align-items: center; }
.opp-info { display: flex; flex-direction: column; line-height: 1.4; margin-left: 12px;}
.role-hint { font-size: 0.65rem; color: var(--profile-muted); text-transform: uppercase; font-weight: 600;}
.opp-name { font-size: 0.95rem; font-weight: 700; color: var(--profile-text); }
.opp-contact { font-size: 0.8rem; color: var(--profile-muted); display: flex; align-items: center; gap: 4px; }
.status-hint { font-size: 0.8rem; color: var(--profile-muted); font-style: italic; display: block; text-align: right;}

/* =======================================================
   GIẢI ĐẤU CARDS
   ======================================================= */
.tournaments-stack { display: flex; flex-direction: column; gap: 1.5rem; }
.atp-tour-card { 
  display: flex; background: #fff; border: 1px solid var(--profile-border); 
  border-radius: 12px; overflow: hidden; box-shadow: var(--profile-shadow); 
  transition: transform 0.2s; 
}
.atp-tour-card:hover { transform: translateY(-3px); border-color: var(--profile-primary);}

.tour-main-info { flex: 1; padding: 2rem; }
.tour-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.tour-category { font-size: 0.7rem; font-weight: 800; color: var(--profile-primary); text-transform: uppercase; letter-spacing: 0.1em; }
.atp-status-pill { padding: 4px 12px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
.confirmed { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0;}
.pending { background: #fef9c3; color: #854d0e; border: 1px solid #fef08a;}

.atp-tour-name { font-size: 1.5rem; font-weight: 800; color: var(--profile-text); margin: 0 0 1.5rem; text-transform: uppercase; line-height: 1.2; }
.tour-meta-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
.m-label { display: block; font-size: 0.65rem; font-weight: 700; color: var(--profile-muted); text-transform: uppercase; margin-bottom: 4px; }
.m-val { font-size: 0.95rem; font-weight: 600; color: var(--profile-text); }

.atp-ticket-stub { 
  width: 200px; background: #f8fafc; border-left: 2px dashed #cbd5e1; 
  display: flex; flex-direction: column; align-items: center; justify-content: center; 
  padding: 1.5rem; text-align: center; 
}
.stub-qr-box { width: 100px; height: 100px; background: #fff; padding: 6px; border-radius: 8px; margin-bottom: 1rem; border: 1px solid var(--profile-border); }
.stub-qr-box img { width: 100%; height: 100%; }
.stub-label { font-size: 0.65rem; font-weight: 700; color: var(--profile-muted); text-transform: uppercase; margin-bottom: 6px; }
.atp-ticket-stub code { background: #0f172a; color: #fff; padding: 6px 12px; border-radius: 4px; font-weight: 700; font-size: 0.9rem; letter-spacing: 1px;}

.atp-empty-state-card { background: #fff; border-radius: 12px; padding: 4rem 2rem; text-align: center; border: 1px solid var(--profile-border); }
.empty-visual { font-size: 4rem; margin-bottom: 1rem; }
.atp-empty-state-card h3 { font-size: 1.2rem; color: var(--profile-text); margin-bottom: 0.5rem;}
.atp-empty-state-card p { color: var(--profile-muted); margin-bottom: 2rem;}

/* =======================================================
   RESPONSIVE MOBILE
   ======================================================= */
.hide-mobile { display: block; }
.hide-desktop { display: none; }

@media (max-width: 1024px) {
  .layout-grid { grid-template-columns: 1fr; margin-top: 1.5rem; }
  
  .mobile-menu-toggle {
    display: flex; align-items: center; width: 100%; padding: 1rem 1.25rem;
    background: #fff; color: #0f172a; border: 1px solid var(--profile-border);
    border-radius: 8px; font-weight: 700; font-size: 0.9rem; cursor: pointer;
    margin-bottom: 1.5rem; box-shadow: var(--profile-shadow); position: sticky; top: 70px; z-index: 100;
  }
  .hamburger-box { width: 24px; height: 14px; position: relative; margin-right: 12px; }
  .hamburger-inner, .hamburger-inner::before, .hamburger-inner::after { width: 24px; height: 2px; background-color: var(--profile-primary); border-radius: 4px; position: absolute; transition: 0.3s; }
  .hamburger-inner { top: 50%; transform: translateY(-50%); }
  .hamburger-inner::before { content: ''; top: -6px; left: 0; }
  .hamburger-inner::after { content: ''; bottom: -6px; left: 0; }
  .mobile-menu-toggle.is-active .hamburger-inner { background-color: transparent; }
  .mobile-menu-toggle.is-active .hamburger-inner::before { top: 0; transform: rotate(45deg); }
  .mobile-menu-toggle.is-active .hamburger-inner::after { top: 0; transform: rotate(-45deg); }
  .toggle-text { flex: 1; text-align: left; text-transform: uppercase; letter-spacing: 0.05em; }
  .arrow-icon { font-size: 1rem; color: var(--profile-muted); transition: 0.3s; }
  .arrow-icon.rotate { transform: rotate(180deg); }

  .sidebar-nav { 
    display: none; flex-direction: column; gap: 0.4rem; background: #fff;
    border: 1px solid var(--profile-border); border-radius: 8px; padding: 0.5rem; margin-bottom: 1.5rem;
  }
  .sidebar-nav.mobile-open { display: flex; animation: fadeIn 0.3s ease; }
  .nav-btn { width: 100%; border: none; box-shadow: none; border-radius: 6px; padding: 0.8rem 1rem; justify-content: flex-start; }

  .hide-mobile { display: none !important; }
  .hide-desktop { display: flex !important; }

  /* Mobile Card Lists (Match History & Challenges) */
  .mobile-history-list, .mobile-challenge-list { display: flex; flex-direction: column; gap: 1rem; }
  .mobile-match-item, .mobile-challenge-card { background: #fff; border: 1px solid var(--profile-border); border-radius: 8px; padding: 1.2rem; }
  .m-match-header, .m-ch-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding-bottom: 0.8rem; border-bottom: 1px solid #f1f5f9; }
  .m-match-time { font-size: 0.85rem; color: var(--profile-muted); font-weight: 500;}
  .m-match-row { font-size: 0.9rem; margin-bottom: 0.6rem; display: flex; justify-content: space-between; }
  .m-match-row b { color: var(--profile-muted); font-weight: 600; }

  .m-ch-names { flex: 1; margin-left: 12px; display: flex; flex-direction: column; }
  .m-opp-name { font-size: 1.05rem; color: var(--profile-text); }
  .m-info-line { display: flex; align-items: center; gap: 8px; font-size: 0.9rem; color: var(--profile-muted); margin-bottom: 0.5rem; font-weight: 500;}
  .m-ch-actions { margin-top: 1rem; padding-top: 1rem; border-top: 1px dashed var(--profile-border); }
  .m-action-flex { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  
  .atp-card { padding: 1.5rem; }
  .data-display-grid { grid-template-columns: 1fr; gap: 1.5rem; }
  
  /* Tournament Mobile Fix */
  .atp-tour-card { flex-direction: column; }
  .tour-main-info { padding: 1.5rem; }
  .atp-tour-name { font-size: 1.3rem; margin-bottom: 1.2rem; }
  .tour-meta-grid { grid-template-columns: 1fr; gap: 1rem; }
  .atp-ticket-stub { width: 100%; border-left: none; border-top: 2px dashed var(--profile-border); padding: 1.5rem; flex-direction: row; gap: 1.5rem; text-align: left; }
  .stub-qr-box { margin-bottom: 0; width: 80px; height: 80px; flex-shrink: 0;}
}

@media (max-width: 768px) {
  .hero-flex { flex-direction: column; text-align: center; padding: 2rem 1rem; gap: 1.5rem; }
  .avatar-frame { width: 120px; height: 120px; margin: 0 auto; }
  .hero-text-block h1 { font-size: 2rem; margin-bottom: 1rem; }
  .hero-quick-stats { width: 100%; justify-content: space-between; padding: 1rem; }
  .stat-val { font-size: 1.2rem; }
}

@media (max-width: 480px) {
  .hero-quick-stats { flex-wrap: wrap; justify-content: center; gap: 1rem; }
  .stat-item { flex: 1; min-width: 80px; }
  .stat-sep { display: none; }
  .atp-ticket-stub { flex-direction: column; text-align: center; gap: 1rem; }
  .stub-qr-box { margin: 0 auto; }
}

@media (min-width: 1025px) {
  .mobile-menu-toggle { display: none; }
}
</style>