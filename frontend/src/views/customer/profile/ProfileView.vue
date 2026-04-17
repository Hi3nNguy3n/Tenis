<script setup>
import { onMounted, ref } from 'vue'
import { useAuthStore } from '../../../stores/auth'
import { ElMessage } from 'element-plus'
import { CameraFilled } from '@element-plus/icons-vue'

import { playerService } from '../../../services/playerService'

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


onMounted(async () => {
  try {
    // Luôn fetch profile mới nhất để có đủ thông tin (wins, losses, etc.)
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
            <RouterLink to="/profile" class="nav-btn" active-class="active" exact-active-class="active">
              <span>Hồ sơ</span>
            </RouterLink>

            <RouterLink to="/profile/my-tournaments" class="nav-btn" active-class="active" exact-active-class="active">
              <span>Giải đấu</span>
            </RouterLink>

            <RouterLink to="/profile/change-password" class="nav-btn" active-class="active" exact-active-class="active">
              <span>Bảo mật</span>
            </RouterLink>
          </nav>
        </aside>

        <main class="content-primary">
          <article class="atp-card">
            <div class="card-header-flex">
              <div class="section-title-wrap">
                <h2 class="atp-section-title">Thông tin cá nhân</h2>
                <div class="section-line"></div>
              </div>

              <button
                v-if="!isEditing"
                type="button"
                class="btn-atp-outline"
                @click="startEdit"
              >
                Chỉnh sửa
              </button>
            </div>

            <div v-if="!isEditing" class="data-display-grid">
              <div class="display-item">
                <label>Họ và tên</label>
                <p>{{ authStore.user?.full_name || '---' }}</p>
              </div>

              <div class="display-item">
                <label>Email liên hệ</label>
                <p class="text-break email-value">{{ authStore.user?.email || '---' }}</p>
              </div>

              <div class="display-item">
                <label>Số điện thoại</label>
                <p>{{ authStore.user?.phone || 'Chưa cập nhật' }}</p>
              </div>

              <div class="display-item">
                <label>Giới tính</label>
                <p>
                  {{
                    authStore.user?.gender === 'male'
                      ? 'Nam'
                      : authStore.user?.gender === 'female'
                      ? 'Nữ'
                      : 'Khác'
                  }}
                </p>
              </div>
            </div>

            <el-form v-else :model="editForm" label-position="top" class="atp-form-modern">
              <div class="form-grid">
                <el-form-item label="Họ và tên">
                  <el-input v-model="editForm.full_name" />
                </el-form-item>

                <el-form-item label="Số điện thoại">
                  <el-input v-model="editForm.phone" />
                </el-form-item>

                <el-form-item label="Giới tính">
                  <el-select v-model="editForm.gender" style="width: 100%">
                    <el-option label="Nam" value="male" />
                    <el-option label="Nữ" value="female" />
                    <el-option label="Khác" value="other" />
                  </el-select>
                </el-form-item>
              </div>

              <div class="form-actions-row">
                <button
                  type="button"
                  class="btn-atp-text"
                  @click="isEditing = false"
                >
                  Hủy bỏ
                </button>

                <button
                  type="button"
                  class="btn-atp-solid"
                  :disabled="isLoading"
                  @click="handleUpdate"
                >
                  {{ isLoading ? 'Đang lưu...' : 'Lưu thay đổi' }}
                </button>
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
                      <span :class="['result-tag', scope.row.status === 'THẮNG' ? 'win' : 'lose']">
                        {{ scope.row.status }}
                      </span>
                   </template>
                </el-table-column>
              </el-table>
            </div>
          </article>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
  background: var(--bg-soft, var(--profile-soft-bg));
  min-height: 100vh;
  padding-bottom: 4rem;
  overflow-x: hidden;
  color: var(--profile-text);
}

.profile-page-wrapper,
.profile-page-wrapper * {
  box-sizing: border-box;
  font-family: Arial, sans-serif !important;
}

.profile-page-wrapper button,
.profile-page-wrapper input,
.profile-page-wrapper select,
.profile-page-wrapper textarea,
.profile-page-wrapper a,
.profile-page-wrapper span,
.profile-page-wrapper p,
.profile-page-wrapper h1,
.profile-page-wrapper h2,
.profile-page-wrapper h3,
.profile-page-wrapper h4,
.profile-page-wrapper h5,
.profile-page-wrapper h6,
.profile-page-wrapper label,
.profile-page-wrapper th,
.profile-page-wrapper td {
  font-family: Arial, sans-serif !important;
}

/* HERO */
.profile-hero-banner {
  position: relative;
  min-height: 310px;
  margin-bottom: 2.25rem;
  overflow: hidden;
  background: linear-gradient(135deg, #064e3b 0%, #065f46 48%, #047857 100%);
}

.banner-bg {
  position: absolute;
  inset: 0;
  background-image: url('https://images.unsplash.com/photo-1595435063098-95843b0d2358?q=80&w=2070&auto=format&fit=crop');
  background-size: cover;
  background-position: center;
  opacity: 0.2;
}

.banner-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(2, 44, 34, 0.9) 0%, rgba(4, 78, 59, 0.78) 50%, rgba(6, 95, 70, 0.7) 100%);
}

.hero-content-shell {
  position: relative;
  z-index: 2;
  min-height: 310px;
  display: flex;
  align-items: center;
  padding-top: 1.5rem;
  padding-bottom: 1.5rem;
}

.hero-flex {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 1.75rem;
}

.avatar-container {
  flex-shrink: 0;
}

.avatar-frame {
  position: relative;
  width: 138px;
  height: 138px;
  background: #ffffff;
  border-radius: 20px;
  padding: 6px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 14px;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 14px;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.8rem;
  color: #94a3b8;
}

.avatar-upload-overlay {
  position: absolute;
  right: 6px;
  bottom: 6px;
  width: 32px;
  height: 32px;
  background: var(--profile-primary);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  border-radius: 10px; /* Bo góc nhẹ cho hợp với khung avatar */
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid #ffffff;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  z-index: 5;
}

.avatar-upload-overlay:hover {
  background: var(--profile-primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}





.hero-text-block {
  color: #fff;
  min-width: 0;
  flex: 1;
}

.user-role-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.45rem 0.9rem;
  border-radius: 999px;
  background: var(--profile-secondary);
  color: #14532d;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 0.8rem;
}

.hero-text-block h1 {
  margin: 0 0 1rem;
  font-size: clamp(2.1rem, 3vw, 3rem);
  line-height: 1.02;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: -0.03em;
  color: #ffffff;
  text-shadow: 0 6px 24px rgba(0, 0, 0, 0.18);
}

.hero-quick-stats {
  display: inline-flex;
  align-items: stretch;
  gap: 1rem;
  padding: 1rem 1.2rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(12px);
  box-shadow: 0 16px 34px rgba(0, 0, 0, 0.1);
}

.stat-item {
  min-width: 72px;
  text-align: center;
}

.stat-val {
  display: block;
  color: var(--profile-secondary);
  font-size: 1.6rem;
  line-height: 1;
  font-weight: 600;
  margin-bottom: 0.35rem;
}

.stat-lbl {
  display: block;
  color: rgba(255, 255, 255, 0.86);
  font-size: 0.72rem;
  font-weight: 500;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.stat-sep {
  width: 1px;
  background: rgba(255, 255, 255, 0.18);
}

/* LAYOUT */
.main-layout-container {
  position: relative;
  z-index: 3;
}

.layout-grid {
  display: grid;
  grid-template-columns: 230px minmax(0, 1fr);
  gap: 1.5rem;
  align-items: start;
}

.compact-sidebar {
  min-width: 0;
}

.sidebar-nav {
  position: sticky;
  top: 96px;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  min-height: 56px;
  padding: 0.95rem 1rem;
  border-radius: 14px;
  text-decoration: none;
  background: #fff;
  color: var(--profile-muted);
  border: 1px solid var(--profile-border);
  font-size: 0.86rem;
  font-weight: 500;
  text-transform: uppercase;
  transition: all 0.22s ease;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
}

.nav-btn .icon {
  flex-shrink: 0;
  font-size: 1rem;
  line-height: 1;
}

.nav-btn:hover {
  color: var(--profile-primary);
  border-color: rgba(21, 128, 61, 0.2);
  transform: translateY(-1px);
}

.nav-btn.active,
.nav-btn.router-link-active {
  background: var(--profile-primary);
  color: #fff;
  border-color: var(--profile-primary);
  box-shadow: var(--profile-shadow-md);
}

.content-primary {
  min-width: 0;
}

/* CARD */
.atp-card {
  width: 100%;
  background: var(--profile-card-bg);
  border: 1px solid var(--profile-border);
  border-radius: 22px;
  padding: 1.75rem;
  box-shadow: var(--profile-shadow-sm);
}

.mt-3 {
  margin-top: 1.5rem;
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.section-title-wrap {
  min-width: 0;
}

.atp-section-title {
  margin: 0;
  color: var(--profile-text);
  font-size: clamp(1.2rem, 2vw, 1.8rem);
  line-height: 1.1;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: -0.03em;
}

.section-line {
  width: 220px;
  max-width: 100%;
  height: 2px;
  margin-top: 0.9rem;
  background: linear-gradient(90deg, rgba(21, 128, 61, 0.14) 0%, rgba(21, 128, 61, 0.32) 50%, transparent 100%);
  border-radius: 999px;
}

.table-head {
  margin-bottom: 1.25rem;
}

/* DISPLAY GRID */
.data-display-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.4rem 2rem;
}

.display-item {
  min-width: 0;
}

.display-item label {
  display: block;
  margin-bottom: 0.55rem;
  color: var(--profile-muted);
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.display-item p {
  margin: 0;
  color: var(--profile-text);
  font-size: 1.05rem;
  line-height: 1.4;
  font-weight: 500;
  text-transform: uppercase;
  word-break: break-word;
}

.email-value {
  font-size: 0.98rem;
  line-height: 1.5;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.text-break {
  overflow-wrap: anywhere;
  word-break: break-word;
}

/* FORM */
.atp-form-modern {
  width: 100%;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.2rem 1.5rem;
}

.form-actions-row {
  display: flex;
  justify-content: flex-end;
  gap: 0.85rem;
  flex-wrap: wrap;
  margin-top: 1.4rem;
}

.btn-atp-outline,
.btn-atp-solid,
.btn-atp-text {
  font-family: Arial, sans-serif !important;
  transition: all 0.2s ease;
}

.result-tag {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 4px;
}
.result-tag.win { background: #dcfce7; color: #166534; }
.result-tag.lose { background: #fef2f2; color: #991b1b; }


.btn-atp-outline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 46px;
  padding: 0.78rem 1.2rem;
  border-radius: 14px;
  border: 1.6px solid var(--profile-primary);
  background: #fff;
  color: var(--profile-primary);
  font-size: 0.82rem;
  font-weight: 600;
  text-transform: uppercase;
  cursor: pointer;
  white-space: nowrap;
}

.btn-atp-outline:hover {
  background: rgba(21, 128, 61, 0.05);
}

.btn-atp-solid {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  padding: 0.85rem 1.25rem;
  border: none;
  border-radius: 14px;
  background: var(--profile-primary);
  color: #fff;
  font-size: 0.84rem;
  font-weight: 600;
  text-transform: uppercase;
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(21, 128, 61, 0.18);
}

.btn-atp-solid:hover:not(:disabled) {
  background: var(--profile-primary-dark);
}

.btn-atp-solid:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-atp-text {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  padding: 0.85rem 1rem;
  background: transparent;
  border: none;
  color: var(--profile-muted);
  font-size: 0.82rem;
  font-weight: 500;
  text-transform: uppercase;
  cursor: pointer;
}

/* TABLE */
.atp-table-wrapper {
  width: 100%;
  overflow-x: auto;
  border-radius: 16px;
  border: 1px solid #eef2f7;
}

:deep(.el-table) {
  font-family: Arial, sans-serif !important;
  color: var(--profile-text);
}

:deep(.el-table th.el-table__cell) {
  font-family: Arial, sans-serif !important;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--profile-muted);
  background: #fbfdff;
}

:deep(.el-table td.el-table__cell) {
  font-family: Arial, sans-serif !important;
  font-size: 0.9rem;
}

:deep(.el-table__empty-text) {
  font-family: Arial, sans-serif !important;
  color: var(--profile-muted);
}

:deep(.el-form-item__label) {
  font-family: Arial, sans-serif !important;
  font-weight: 500;
  color: var(--profile-text);
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  min-height: 48px;
  border-radius: 14px;
  font-family: Arial, sans-serif !important;
}

:deep(.el-input__inner),
:deep(.el-select__selected-item),
:deep(.el-textarea__inner) {
  font-family: Arial, sans-serif !important;
}

/* RESPONSIVE */
@media (max-width: 1024px) {
  .profile-hero-banner {
    min-height: 360px;
    margin-bottom: 1.75rem;
  }

  .hero-content-shell {
    min-height: 360px;
    padding-top: 1.75rem;
    padding-bottom: 1.75rem;
  }

  .hero-flex {
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.25rem;
    text-align: center;
  }

  .hero-text-block {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .hero-quick-stats {
    justify-content: center;
  }

  .layout-grid {
    grid-template-columns: 1fr;
    gap: 1.25rem;
  }

  .sidebar-nav {
    position: sticky;
    top: 70px;
    flex-direction: row;
    align-items: stretch;
    gap: 0.7rem;
    overflow-x: auto;
    padding-bottom: 0.2rem;
    background: var(--bg-soft, var(--profile-soft-bg));
    scrollbar-width: none;
  }

  .sidebar-nav::-webkit-scrollbar {
    display: none;
  }

  .nav-btn {
    flex: 0 0 auto;
    min-width: max-content;
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .profile-page-wrapper {
    padding-bottom: 2.5rem;
  }

  .profile-hero-banner {
    min-height: 390px;
  }

  .hero-content-shell {
    min-height: 390px;
    padding-top: 1.4rem;
    padding-bottom: 1.4rem;
  }

  .avatar-frame {
    width: 122px;
    height: 122px;
    border-radius: 16px;
  }

  .hero-text-block h1 {
    font-size: 1.95rem;
  }

  .hero-quick-stats {
    width: 100%;
    max-width: 340px;
    justify-content: space-between;
    gap: 0.5rem;
    padding: 0.9rem;
  }

  .stat-item {
    flex: 1;
    min-width: 0;
  }

  .stat-sep {
    display: none;
  }

  .atp-card {
    border-radius: 18px;
    padding: 1.2rem;
  }

  .card-header-flex {
    align-items: stretch;
    margin-bottom: 1.25rem;
  }

  .btn-atp-outline {
    width: 100%;
  }

  .data-display-grid,
  .form-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .display-item p {
    font-size: 0.98rem;
  }

  .email-value {
    font-size: 0.92rem;
  }

  .form-actions-row {
    flex-direction: column-reverse;
    align-items: stretch;
  }

  .btn-atp-solid,
  .btn-atp-text {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .profile-hero-banner {
    min-height: 410px;
  }

  .hero-content-shell {
    min-height: 410px;
    padding-top: 1.15rem;
    padding-bottom: 1.15rem;
  }

  .hero-flex {
    gap: 0.95rem;
  }

  .avatar-frame {
    width: 108px;
    height: 108px;
    padding: 6px;
  }

  .user-role-badge {
    font-size: 0.66rem;
    padding: 0.38rem 0.75rem;
  }

  .hero-text-block h1 {
    font-size: 1.6rem;
    line-height: 1.04;
    margin-bottom: 0.85rem;
  }

  .hero-quick-stats {
    border-radius: 14px;
    padding: 0.8rem 0.7rem;
  }

  .stat-val {
    font-size: 1.35rem;
  }

  .stat-lbl {
    font-size: 0.67rem;
  }

  .sidebar-nav {
    gap: 0.55rem;
  }

  .nav-btn {
    min-height: 48px;
    padding: 0.78rem 0.95rem;
    border-radius: 12px;
    font-size: 0.76rem;
    gap: 0.55rem;
  }

  .atp-card {
    padding: 1rem;
    border-radius: 16px;
  }

  .atp-section-title {
    font-size: 1.02rem;
  }

  .section-line {
    margin-top: 0.7rem;
  }

  .display-item label {
    font-size: 0.67rem;
  }

  .display-item p {
    font-size: 0.94rem;
  }
}
</style>