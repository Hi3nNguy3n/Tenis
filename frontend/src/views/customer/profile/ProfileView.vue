<script setup>
import { onMounted, ref } from 'vue'
import { useAuthStore } from '../../../stores/auth'
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
  Timer
} from '@element-plus/icons-vue'

import { playerService } from '../../../services/playerService'
import { apiClient } from '../../../services/apiClient' // Đảm bảo import apiClient

const authStore = useAuthStore()
const isEditing = ref(false)
const isLoading = ref(false)
const matchHistory = ref([])
const avatarFile = ref(null)

const editForm = ref({
  full_name: '',
  email: '',
  phone: '',
  gender: '',
  birth_date: ''
})

// --- LOGIC THÁCH ĐẤU ---
const challenges = ref([])
const activeTab = ref('info') // info hoặc challenges
const isProcessing = ref(false)

// Load danh sách kèo thách đấu
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

// Xử lý Phản hồi (Chấp nhận/Từ chối)
const handleRespond = async (challengeId, status) => {
  try {
    const actionText = status === 'accepted' ? 'chấp nhận' : 'từ chối';
    await ElMessageBox.confirm(`Bạn chắc chắn muốn ${actionText} lời mời này?`, 'Xác nhận');
    
    await apiClient.patch(`/api/challenges/${challengeId}/respond`, { status })
    ElMessage.success(status === 'accepted' ? 'Đã chấp nhận lời mời!' : 'Đã từ chối lời mời.')
    loadMyChallenges() 
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('Không thể thực hiện thao tác.')
  }
}

// Xử lý Thanh toán
const handlePay = async (challengeId) => {
  try {
    const res = await apiClient.post(`/api/payments/challenge/${challengeId}/create-url`)
    if (res.payment_url) {
      window.location.href = res.payment_url 
    }
  } catch (err) {
    ElMessage.error('Lỗi khởi tạo thanh toán.')
  }
}

// Helper hiển thị trạng thái
const getChallengeStatus = (status) => {
  const map = {
    'pending': { label: 'Đang chờ', type: 'warning' },
    'waiting_payment': { label: 'Chờ thanh toán', type: 'danger' },
    'paid': { label: 'Đã thanh toán', type: 'success' },
    'scheduled': { label: 'Đã lên lịch', type: 'primary' },
    'rejected': { label: 'Đã từ chối', type: 'info' }
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
        birth_date: profileData?.player_profile?.date_of_birth || authStore.user.date_of_birth
      }
    }

    const history = await playerService.getMatchHistory()
    matchHistory.value = history || []
    
    loadMyChallenges() // Tải kèo thách đấu ngay khi vào trang
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
    ElMessage.success('Cập nhật ảnh đại diện thành công!')
  } catch (err) {
    ElMessage.error(err.message || 'Lỗi khi upload ảnh.')
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
    ElMessage.success('Cập nhật hồ sơ thành công!')
  } catch (error) {
    ElMessage.error(error.message || 'Có lỗi xảy ra khi cập nhật.')
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="profile-page-wrapper">
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
              {{ authStore.isAdmin ? 'Ban quản trị' : 'Vận động viên' }}
            </span>

            <h1>{{ authStore.user?.full_name || 'Người dùng' }}</h1>

            <div class="hero-quick-stats">
              <div class="stat-item">
                <span class="stat-val">#{{ authStore.profile?.player_profile?.rank || '---' }}</span>
                <span class="stat-lbl">Hạng</span>
              </div>
              <div class="stat-sep"></div>
              <div class="stat-item">
                <span class="stat-val">{{ authStore.profile?.player_profile?.wins || 0 }}</span>
                <span class="stat-lbl">Thắng</span>
              </div>
              <div class="stat-sep"></div>
              <div class="stat-item">
                <span class="stat-val">{{ authStore.profile?.player_profile?.losses || 0 }}</span>
                <span class="stat-lbl">Bại</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div class="container main-layout-container">
      <div class="layout-grid">
        <aside class="compact-sidebar">
          <nav class="sidebar-nav">
            <button class="nav-btn" :class="{ active: activeTab === 'info' }" @click="activeTab = 'info'">
              <span>Hồ sơ & Lịch sử</span>
            </button>

            <button class="nav-btn btn-challenge-nav" :class="{ active: activeTab === 'challenges' }" @click="activeTab = 'challenges'">
              <el-icon class="mr-2"><Trophy /></el-icon>
              <span>Kèo thách đấu</span>
              <el-badge v-if="challenges.filter(c => c.status === 'pending' && c.challenged_id === authStore.profile?.player_profile?.id).length > 0" 
                        :value="challenges.filter(c => c.status === 'pending' && c.challenged_id === authStore.profile?.player_profile?.id).length" 
                        class="ml-2" />
            </button>

            <RouterLink to="/profile/my-tournaments" class="nav-btn">
              <span>Giải đấu của tôi</span>
            </RouterLink>

            <RouterLink to="/profile/change-password" class="nav-btn">
              <span>Bảo mật</span>
            </RouterLink>
          </nav>
        </aside>

        <main class="content-primary">
          
          <div v-if="activeTab === 'info'" class="tab-fade-in">
            <article class="atp-card">
              <div class="card-header-flex">
                <div class="section-title-wrap">
                  <h2 class="atp-section-title">Thông tin cá nhân</h2>
                  <div class="section-line"></div>
                </div>
                <button v-if="!isEditing" type="button" class="btn-atp-outline" @click="startEdit">Chỉnh sửa</button>
              </div>

              <div v-if="!isEditing" class="data-display-grid">
                <div class="display-item"><label>Họ và tên</label><p>{{ authStore.user?.full_name || '---' }}</p></div>
                <div class="display-item"><label>Email liên hệ</label><p class="text-break email-value">{{ authStore.user?.email || '---' }}</p></div>
                <div class="display-item"><label>Số điện thoại</label><p>{{ authStore.user?.phone || 'Chưa cập nhật' }}</p></div>
                <div class="display-item"><label>Giới tính</label><p>{{ authStore.user?.gender === 'male' ? 'Nam' : authStore.user?.gender === 'female' ? 'Nữ' : 'Khác' }}</p></div>
              </div>

              <el-form v-else :model="editForm" label-position="top" class="atp-form-modern">
                <div class="form-grid">
                  <el-form-item label="Họ và tên"><el-input v-model="editForm.full_name" /></el-form-item>
                  <el-form-item label="Số điện thoại"><el-input v-model="editForm.phone" /></el-form-item>
                  <el-form-item label="Giới tính">
                    <el-select v-model="editForm.gender" style="width: 100%">
                      <el-option label="Nam" value="male" /><el-option label="Nữ" value="female" /><el-option label="Khác" value="other" />
                    </el-select>
                  </el-form-item>
                </div>
                <div class="form-actions-row">
                  <button type="button" class="btn-atp-text" @click="isEditing = false">Hủy bỏ</button>
                  <button type="button" class="btn-atp-solid" :disabled="isLoading" @click="handleUpdate">{{ isLoading ? 'Đang lưu...' : 'Lưu thay đổi' }}</button>
                </div>
              </el-form>
            </article>

            <article class="atp-card mt-3">
              <div class="section-title-wrap table-head">
                <h2 class="atp-section-title">Lịch sử thi đấu gần đây</h2>
                <div class="section-line"></div>
              </div>
              <div class="atp-table-wrapper">
                <el-table :data="matchHistory" empty-text="Chưa có dữ liệu thi đấu" style="width: 100%">
                  <el-table-column prop="time" label="Thời gian" width="160" />
                  <el-table-column prop="tournament_name" label="Giải đấu" />
                  <el-table-column prop="opponent" label="Đối thủ" />
                  <el-table-column prop="round" label="Vòng" width="100" />
                  <el-table-column prop="status" label="Kết quả" width="100">
                     <template #default="scope">
                        <span :class="['result-tag', scope.row.status === 'THẮNG' ? 'win' : 'lose']">{{ scope.row.status }}</span>
                     </template>
                  </el-table-column>
                </el-table>
              </div>
            </article>
          </div>

          <div v-else-if="activeTab === 'challenges'" class="tab-fade-in">
            <article class="atp-card">
              <div class="card-header-flex">
                <div class="section-title-wrap">
                  <h2 class="atp-section-title">Kèo thách đấu 1vs1</h2>
                  <div class="section-line"></div>
                </div>
                <el-button :icon="Refresh" circle @click="loadMyChallenges" :loading="isProcessing" />
              </div>

              <div class="atp-table-wrapper" v-loading="isProcessing">
                <el-table :data="challenges" stripe style="width: 100%">
                  <el-table-column label="Đối thủ & Liên hệ" min-width="220">
                    <template #default="{ row }">
                      <div class="opponent-cell">
                        <el-avatar :size="40" :src="row.opponent_avatar" class="mr-3" />
                        <div class="opp-info">
                          <span class="role-hint">{{ row.challenger_id === authStore.profile?.player_profile?.id ? 'Bạn thách đấu:' : 'Thách đấu bạn:' }}</span>
                          <b class="opp-name">{{ row.opponent_name }}</b>
                          <div class="opp-contact">
                            <el-icon><Iphone /></el-icon> {{ row.opponent_phone || 'Chưa có SĐT' }}
                          </div>
                        </div>
                      </div>
                    </template>
                  </el-table-column>

                  <el-table-column label="Ngày dự kiến" width="140">
                    <template #default="{ row }">
                      <div class="date-cell">
                        <el-icon class="mr-1"><CalendarIcon /></el-icon>
                        <span>{{ new Date(row.proposed_date).toLocaleDateString('vi-VN') }}</span>
                      </div>
                    </template>
                  </el-table-column>

                  <el-table-column label="Trạng thái" width="140">
                    <template #default="{ row }">
                      <el-tag :type="getChallengeStatus(row.status).type" effect="dark" size="small" round>
                        {{ getChallengeStatus(row.status).label.toUpperCase() }}
                      </el-tag>
                    </template>
                  </el-table-column>

                  <el-table-column label="Thao tác" width="220" align="right">
                    <template #default="{ row }">
                      <div v-if="row.status === 'pending' && row.challenged_id === authStore.profile?.player_profile?.id" class="action-flex">
                        <el-button type="success" size="small" :icon="Check" circle @click="handleRespond(row.id, 'accepted')" />
                        <el-button type="danger" size="small" :icon="Close" circle @click="handleRespond(row.id, 'rejected')" />
                      </div>

                      <div v-if="row.status === 'waiting_payment'" class="action-flex">
                        <el-button type="primary" size="small" :icon="CreditCard" @click="handlePay(row.id)">Thanh toán phí</el-button>
                      </div>

                      <span v-if="row.status === 'paid'" class="status-hint">Admin đang xếp sân...</span>
                      <span v-if="row.status === 'pending' && row.challenger_id === authStore.profile?.player_profile?.id" class="status-hint">Đang chờ phản hồi...</span>
                    </template>
                  </el-table-column>
                </el-table>
                <el-empty v-if="challenges.length === 0" description="Bạn chưa có kèo thách đấu nào." />
              </div>
            </article>
          </div>

        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* GIỮ NGUYÊN CÁC STYLE CŨ CỦA ÔNG VÀ THÊM CÁC STYLE MỚI DƯỚI ĐÂY */

.profile-page-wrapper {
  --profile-primary: #15803d;
  --profile-primary-dark: #166534;
  --profile-secondary: #bef264;
  --profile-soft-bg: #f1f5f9;
  --profile-card-bg: #ffffff;
  --profile-border: #dbe4ee;
  --profile-text: #0f172a;
  --profile-muted: #64748b;
  --profile-shadow-sm: 0 8px 24px rgba(15, 23, 42, 0.05);
  --profile-shadow-md: 0 14px 34px rgba(21, 128, 61, 0.14);
  font-family: Arial, sans-serif !important;
  background: var(--profile-soft-bg);
  min-height: 100vh;
  padding-bottom: 4rem;
}

/* Tab Animation */
.tab-fade-in {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Sidebar Update */
.nav-btn {
  width: 100%;
  cursor: pointer;
  border: 1.5px solid var(--profile-border);
  margin-bottom: 0.5rem;
}
.btn-challenge-nav.active {
  background: #dc2626 !important; /* Màu đỏ nổi bật cho tab thách đấu */
  border-color: #dc2626 !important;
}

/* Challenge Table Styles */
.opponent-cell { display: flex; align-items: center; }
.opp-info { display: flex; flex-direction: column; line-height: 1.2; }
.role-hint { font-size: 0.65rem; color: var(--profile-muted); text-transform: uppercase; }
.opp-name { font-size: 0.9rem; color: var(--profile-text); }
.date-cell { display: flex; align-items: center; color: #475569; font-size: 0.85rem; font-weight: 600; }
.action-flex { display: flex; gap: 8px; justify-content: flex-end; }
.status-hint { font-size: 0.75rem; color: #94a3b8; font-style: italic; }

.mr-2 { margin-right: 0.5rem; }
.ml-2 { margin-left: 0.5rem; }
.mr-1 { margin-right: 0.25rem; }

/* REUSE OLD STYLES */
.profile-hero-banner { position: relative; min-height: 310px; margin-bottom: 2.25rem; overflow: hidden; background: linear-gradient(135deg, #064e3b 0%, #065f46 48%, #047857 100%); }
.banner-bg { position: absolute; inset: 0; background-image: url('https://images.unsplash.com/photo-1595435063098-95843b0d2358?q=80&w=2070&auto=format&fit=crop'); background-size: cover; background-position: center; opacity: 0.2; }
.banner-overlay { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(2, 44, 34, 0.9) 0%, rgba(4, 78, 59, 0.78) 50%, rgba(6, 95, 70, 0.7) 100%); }
.hero-content-shell { position: relative; z-index: 2; min-height: 310px; display: flex; align-items: center; }
.hero-flex { width: 100%; display: flex; align-items: center; gap: 1.75rem; }
.avatar-frame { position: relative; width: 138px; height: 138px; background: #fff; border-radius: 20px; padding: 6px; display: flex; align-items: center; justify-content: center; }
.avatar-frame img { width: 100%; height: 100%; object-fit: cover; border-radius: 14px; }
.avatar-upload-overlay { position: absolute; right: 6px; bottom: 6px; width: 32px; height: 32px; background: var(--profile-primary); color: #fff; display: flex; align-items: center; justify-content: center; border-radius: 10px; cursor: pointer; border: 2px solid #fff; }
.hero-text-block { color: #fff; flex: 1; }
.user-role-badge { padding: 0.45rem 0.9rem; border-radius: 999px; background: var(--profile-secondary); color: #14532d; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.8rem; display: inline-block; }
.hero-text-block h1 { margin: 0 0 1rem; font-size: 2.5rem; font-weight: 600; text-transform: uppercase; color: #fff; }
.hero-quick-stats { display: inline-flex; gap: 1rem; padding: 1rem; border-radius: 16px; background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(12px); }
.stat-item { min-width: 72px; text-align: center; }
.stat-val { display: block; color: var(--profile-secondary); font-size: 1.6rem; font-weight: 600; }
.stat-lbl { display: block; color: rgba(255, 255, 255, 0.8); font-size: 0.7rem; text-transform: uppercase; }
.stat-sep { width: 1px; background: rgba(255, 255, 255, 0.2); }
.main-layout-container { position: relative; z-index: 3; }
.layout-grid { display: grid; grid-template-columns: 230px 1fr; gap: 1.5rem; }
.sidebar-nav { position: sticky; top: 96px; display: flex; flex-direction: column; gap: 0.5rem; }
.nav-btn { display: flex; align-items: center; padding: 1rem; border-radius: 14px; background: #fff; color: var(--profile-muted); font-size: 0.85rem; font-weight: 600; text-transform: uppercase; transition: 0.2s; text-decoration: none; border: 1px solid var(--profile-border); }
.nav-btn.active { background: var(--profile-primary); color: #fff; border-color: var(--profile-primary); }
.atp-card { background: #fff; border: 1px solid var(--profile-border); border-radius: 22px; padding: 1.75rem; box-shadow: var(--profile-shadow-sm); }
.atp-section-title { margin: 0; font-size: 1.5rem; font-weight: 600; text-transform: uppercase; }
.section-line { width: 100px; height: 3px; background: var(--profile-primary); margin-top: 0.5rem; border-radius: 99px; }
.data-display-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 1.5rem; }
.display-item label { font-size: 0.7rem; color: var(--profile-muted); text-transform: uppercase; font-weight: 700; }
.display-item p { font-size: 1rem; font-weight: 600; color: var(--profile-text); margin-top: 0.25rem; }
.atp-table-wrapper { margin-top: 1rem; border-radius: 12px; overflow: hidden; border: 1px solid #f1f5f9; }
.result-tag { font-size: 0.7rem; font-weight: 800; padding: 4px 8px; border-radius: 6px; }
.result-tag.win { background: #dcfce7; color: #166534; }
.result-tag.lose { background: #fee2e2; color: #991b1b; }
.mt-3 { margin-top: 1.5rem; }

@media (max-width: 1024px) {
  .layout-grid { grid-template-columns: 1fr; }
  .sidebar-nav { flex-direction: row; overflow-x: auto; position: static; }
  .nav-btn { white-space: nowrap; }
}
</style>