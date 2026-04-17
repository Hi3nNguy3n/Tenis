<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '../../../services/apiClient'
import { useAuthStore } from '../../../stores/auth'
import { ElMessage } from 'element-plus'
import { CameraFilled } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const loading = ref(false)
const error = ref('')
const success = ref('')

const form = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

onMounted(async () => {
  try {
    await authStore.fetchCurrentProfile()
  } catch (err) {
    console.error('Lỗi tải hồ sơ:', err)
  }
})

const handleChangePassword = async () => {
  if (form.value.new_password !== form.value.confirm_password) {
    error.value = 'Mật khẩu xác nhận không khớp.'
    ElMessage.error(error.value)
    return
  }

  loading.value = true
  error.value = ''
  success.value = ''

  try {
    // Backend yêu cầu old_password và new_password dưới dạng Query Parameters
    const url = `/api/auth/change-password?old_password=${encodeURIComponent(form.value.old_password)}&new_password=${encodeURIComponent(form.value.new_password)}`
    await apiClient.post(url)
    
    success.value = 'Đổi mật khẩu thành công!'
    ElMessage.success(success.value)
    form.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch (err) {
    error.value = err.message || 'Lỗi khi đổi mật khẩu.'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="profile-page-wrapper">
    <!-- Hero Header (Synced with Profile/Tournaments) -->
    <section class="profile-hero-banner">
      <div class="banner-bg"></div>
      <div class="banner-overlay"></div>
      
      <div class="container hero-content-shell">
        <div class="hero-flex">
          <div class="avatar-container">
            <div class="avatar-frame">
              <img v-if="authStore.user?.avatar_url" :src="authStore.user.avatar_url" alt="Avatar" />
              <div v-else class="avatar-placeholder">👤</div>
              
              <RouterLink to="/profile" class="avatar-upload-overlay">
                <el-icon><CameraFilled /></el-icon>
              </RouterLink>
            </div>
          </div>
          
          <div class="hero-text-block">
            <span class="user-role-badge">bảo mật tài khoản</span>
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

    <!-- Main Navigation & Content -->
    <div class="container main-layout-container">
      <div class="layout-grid">
        <!-- Sticky Sidebar -->
        <aside class="compact-sidebar">
          <nav class="sidebar-nav">
            <RouterLink to="/profile" class="nav-btn">
              hồ sơ
            </RouterLink>
            <RouterLink to="/profile/my-tournaments" class="nav-btn">
              giải đấu
            </RouterLink>
            <RouterLink to="/profile/change-password" class="nav-btn active">
              bảo mật
            </RouterLink>
          </nav>
        </aside>

        <!-- Dynamic Content Area -->
        <main class="content-primary">
          <article class="atp-card">
            <h2 class="atp-section-title">Đổi mật khẩu</h2>
            <p class="section-hint">Để đảm bảo an toàn, vui lòng không chia sẻ mật khẩu của bạn với người khác.</p>

            <form @submit.prevent="handleChangePassword" class="atp-form-modern">
              <div class="form-stack">
                <div class="atp-form-group">
                  <label>Mật khẩu hiện tại</label>
                  <input v-model="form.old_password" type="password" required placeholder="Nhập mật khẩu hiện tại" class="atp-input" />
                </div>

                <div class="atp-form-group">
                  <label>Mật khẩu mới</label>
                  <input v-model="form.new_password" type="password" required placeholder="Nhập mật khẩu mới" class="atp-input" />
                </div>

                <div class="atp-form-group">
                  <label>Xác nhận mật khẩu mới</label>
                  <input v-model="form.confirm_password" type="password" required placeholder="Xác nhận lại mật khẩu mới" class="atp-input" />
                </div>
              </div>

              <div class="form-actions-row">
                <button type="submit" class="btn-atp-solid" :disabled="loading">
                  {{ loading ? 'Đang xử lý...' : 'Cập nhật mật khẩu' }}
                </button>
              </div>
            </form>
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
  background: var(--bg-soft, var(--profile-soft-bg));
  min-height: 100vh;
  padding-bottom: 5rem;
  font-family: Arial, sans-serif !important;
}

/* Hero Section (Reused) */
.profile-hero-banner {
  position: relative;
  min-height: 310px;
  background: linear-gradient(135deg, #064e3b 0%, #065f46 48%, #047857 100%);
  margin-bottom: 2.25rem;
  overflow: hidden;
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
  background: linear-gradient(90deg, rgba(2, 44, 34, 0.9) 0%, rgba(4, 78, 59, 0.78) 50%, rgba(6, 95, 70, 0.7) 100%);
}

.hero-content-shell {
  position: relative;
  z-index: 2;
  height: 100%;
  padding-top: 1.5rem;
  padding-bottom: 2.5rem;
  display: flex;
  align-items: center;
}

.hero-flex {
  display: flex;
  align-items: center;
  gap: 1.75rem;
  width: 100%;
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

.avatar-frame img { width: 100%; height: 100%; object-fit: cover; border-radius: 14px; }
.avatar-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 2.75rem; background: #f1f5f9; border-radius: 14px; }

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
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
  border: 2px solid #ffffff;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.hero-text-block { color: #fff; flex: 1; min-width: 0; }
.user-role-badge { 
  display: inline-flex;
  padding: 0.45rem 0.9rem;
  border-radius: 999px;
  background: var(--profile-secondary);
  color: #14532d;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 0.8rem;
}
.hero-text-block h1 { 
  font-size: clamp(2.1rem, 3vw, 3rem);
  font-weight: 600;
  margin: 0 0 1rem;
  text-transform: uppercase;
  letter-spacing: -0.03em;
  text-shadow: 0 6px 24px rgba(0, 0, 0, 0.18);
}

.hero-quick-stats {
  display: inline-flex;
  align-items: stretch;
  gap: 1rem;
  padding: 1rem 1.2rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.14);
}

.stat-item { text-align: center; min-width: 72px; }
.stat-val { display: block; font-size: 1.6rem; font-weight: 600; color: var(--profile-secondary); }
.stat-lbl { font-size: 0.72rem; font-weight: 500; text-transform: uppercase; color: rgba(255,255,255,0.86); }
.stat-sep { width: 1px; background: rgba(255, 255, 255, 0.18); }

/* Layout Grid */
.layout-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 2.5rem;
}

.sidebar-nav {
  position: sticky;
  top: 100px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: #fff;
  border-radius: 8px;
  color: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  font-size: 0.85rem;
  transition: var(--transition);
  border: 1px solid transparent;
  text-decoration: none;
}

.nav-btn.active { background: var(--primary); color: #fff; box-shadow: var(--shadow-md); }

/* Card Content */
.atp-card {
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 3rem;
  box-shadow: var(--shadow-sm);
  max-width: 800px;
}

.atp-section-title { font-size: 1.5rem; font-weight: 600; color: var(--text-dark); text-transform: uppercase; margin-bottom: 0.5rem; }
.section-hint { color: var(--text-muted); font-size: 0.9rem; font-weight: 700; margin-bottom: 2.5rem; }

.form-stack { display: flex; flex-direction: column; gap: 1.5rem; max-width: 500px; }
.atp-form-group { display: flex; flex-direction: column; gap: 0.6rem; }
.atp-form-group label { font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; }
.atp-input {
  padding: 1rem 1.25rem;
  border-radius: 8px;
  border: 2px solid var(--bg-soft);
  background: var(--bg-soft);
  font-family: inherit;
  font-weight: 700;
  transition: var(--transition);
  outline: none;
}
.atp-input:focus { border-color: var(--primary); background: #fff; box-shadow: 0 0 0 4px rgba(21, 128, 61, 0.1); }

.form-actions-row { margin-top: 2.5rem; }

.btn-atp-solid {
  background: var(--primary);
  color: #fff;
  border: none;
  padding: 14px 34px;
  border-radius: 6px;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.9rem;
  cursor: pointer;
  transition: var(--transition);
}
.btn-atp-solid:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(21, 128, 61, 0.2); }

/* RESPONSIVE */
@media (max-width: 1024px) {
  .layout-grid { grid-template-columns: 1fr; }
  .sidebar-nav {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 1rem;
    position: sticky;
    top: 80px;
    z-index: 100;
    background: var(--bg-soft);
  }
  .nav-btn { min-width: max-content; }
  .hero-flex { flex-direction: column; text-align: center; gap: 2rem; }
  .avatar-frame { margin-bottom: 0; }
  .hero-quick-stats { margin: 0 auto; }
}

@media (max-width: 768px) {
  .profile-hero-banner { height: 220px; }
  .avatar-frame { width: 150px; height: 150px; }
  .hero-text-block h1 { font-size: 2.2rem; }
  .atp-card { padding: 1.5rem; }
  .form-stack { max-width: 100%; }
}

@media (max-width: 480px) {
  .hero-quick-stats { flex-direction: column; width: 100%; gap: 1rem; }
  .stat-sep { display: none; }
}
</style>
