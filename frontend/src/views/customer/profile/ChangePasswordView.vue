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
/* --- PHẦN STYLE ĐÃ ĐƯỢC TỐI ƯU TOÀN DIỆN --- */

.profile-page-wrapper {
  --profile-primary: #15803d;
  --profile-primary-dark: #166534;
  --profile-secondary: #bef264;
  --profile-soft-bg: #f1f5f9;
  --profile-border: #dbe4ee;
  --profile-text: #0f172a;
  --profile-muted: #64748b;
  --profile-shadow-sm: 0 8px 24px rgba(15, 23, 42, 0.05);
  font-family: Arial, sans-serif !important;
  background: var(--profile-soft-bg);
  min-height: 100vh;
  padding-bottom: 2rem;
}

/* Hero Banner */
.profile-hero-banner { 
  position: relative; 
  min-height: 310px; 
  background: linear-gradient(135deg, #064e3b 0%, #047857 100%); 
  display: flex;
  align-items: center;
  overflow: hidden;
}

.banner-bg { position: absolute; inset: 0; background-image: url('https://images.unsplash.com/photo-1595435063098-95843b0d2358?q=80&w=2070&auto=format&fit=crop'); background-size: cover; background-position: center; opacity: 0.2; }
.banner-overlay { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(2, 44, 34, 0.9) 0%, rgba(4, 78, 59, 0.78) 50%, rgba(6, 95, 70, 0.7) 100%); }

.hero-content-shell { position: relative; z-index: 2; width: 100%; max-width: 1200px; margin: 0 auto; }
.hero-flex { 
  display: flex; 
  align-items: center; 
  gap: 2rem; 
  padding: 2rem 1rem;
}

.avatar-frame { 
  position: relative; 
  width: 150px; 
  height: 150px; 
  background: #fff; 
  border-radius: 50%; /* Chuyển sang dạng tròn cho hiện đại */
  padding: 5px; 
  box-shadow: 0 12px 35px rgba(0,0,0,0.25);
  flex-shrink: 0;
  border: 4px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
}
.avatar-frame img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }
.avatar-placeholder { font-size: 3.5rem; }
.avatar-upload-overlay { position: absolute; right: 5px; bottom: 5px; width: 38px; height: 38px; background: var(--profile-primary); color: #fff; display: flex; align-items: center; justify-content: center; border-radius: 50%; cursor: pointer; border: 3px solid #fff; box-shadow: 0 4px 10px rgba(0,0,0,0.2); transition: 0.2s; }
.avatar-upload-overlay:hover { transform: scale(1.1); background: var(--profile-primary-dark); }

.hero-text-block { color: #fff; flex: 1; min-width: 0; }
.user-role-badge { padding: 0.4rem 0.9rem; border-radius: 999px; background: var(--profile-secondary); color: #14532d; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.75rem; display: inline-block; }
.hero-text-block h1 { margin: 0 0 1rem; font-size: clamp(1.8rem, 4vw, 2.8rem); font-weight: 500; text-transform: uppercase; color: #fff; }

/* Stats Box - Glassmorphism */
.hero-quick-stats { 
  display: inline-flex; 
  gap: 1rem; 
  padding: 0.8rem 1.2rem; 
  border-radius: 16px; 
  background: rgba(255, 255, 255, 0.1); 
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
}
.stat-item { min-width: 60px; text-align: center; }
.stat-val { display: block; color: var(--profile-secondary); font-size: 1.4rem; font-weight: 700; }
.stat-lbl { display: block; color: rgba(255, 255, 255, 0.8); font-size: 0.65rem; text-transform: uppercase; font-weight: 600; }
.stat-sep { width: 1px; background: rgba(255, 255, 255, 0.2); }

/* Layout Grid */
.main-layout-container { max-width: 1200px; margin: 0 auto; padding: 0 1rem; }
.layout-grid { display: grid; grid-template-columns: 260px 1fr; gap: 2rem; margin-top: -2.5rem; position: relative; z-index: 5; }

.sidebar-nav { position: sticky; top: 100px; display: flex; flex-direction: column; gap: 0.75rem; }
.nav-btn { display: flex; align-items: center; padding: 1rem 1.5rem; border-radius: 12px; background: #fff; color: var(--profile-muted); font-size: 0.85rem; font-weight: 700; text-transform: uppercase; transition: 0.3s; text-decoration: none; border: 1px solid var(--profile-border); box-shadow: var(--profile-shadow-sm); width: 100%; cursor: pointer; }
.nav-btn.active { background: var(--profile-primary); color: #fff; border-color: var(--profile-primary); }

.atp-card { background: #fff; border: 1px solid var(--profile-border); border-radius: 20px; padding: 2rem; box-shadow: var(--profile-shadow-sm); max-width: 800px; }
.atp-section-title { font-size: 1.4rem; font-weight: 600; color: var(--profile-text); text-transform: uppercase; margin-bottom: 0.5rem; }
.section-hint { color: var(--profile-muted); font-size: 0.85rem; font-weight: 600; margin-bottom: 2rem; }

.form-stack { display: flex; flex-direction: column; gap: 1.25rem; max-width: 400px; }
.atp-form-group { display: flex; flex-direction: column; gap: 0.5rem; }
.atp-form-group label { font-size: 0.7rem; font-weight: 600; color: var(--profile-muted); text-transform: uppercase; }
.atp-input { padding: 1rem 1.25rem; border-radius: 10px; border: 2px solid #f1f5f9; background: #f8fafc; font-family: inherit; font-weight: 500; transition: 0.2s; outline: none; }
.atp-input:focus { border-color: var(--profile-primary); background: #fff; }

.form-actions-row { margin-top: 2rem; }
.btn-atp-solid { background: var(--profile-primary); color: #fff; border: none; padding: 12px 28px; border-radius: 10px; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; cursor: pointer; transition: 0.2s; }

/* Responsive Queries */
@media (max-width: 1024px) {
  .layout-grid { grid-template-columns: 1fr; margin-top: 1.5rem; }
  .sidebar-nav { flex-direction: row; overflow-x: auto; position: sticky; top: 0; z-index: 50; background: var(--profile-soft-bg); padding: 1rem 0; margin: 0 -1rem; padding-left: 1rem; padding-right: 1rem; }
  .nav-btn { width: auto; white-space: nowrap; padding: 0.8rem 1.2rem; }
}

@media (max-width: 768px) {
  .hero-flex { flex-direction: column; text-align: center; padding: 3rem 1rem; gap: 1.5rem; }
  .avatar-frame { width: 120px; height: 120px; margin: 0 auto; }
  .hero-text-block h1 { font-size: 2rem; }
  .hero-quick-stats { width: 100%; justify-content: space-between; }
  .atp-card { padding: 1.5rem; }
  .form-stack { max-width: 100%; }
}

@media (max-width: 480px) {
  .hero-quick-stats { flex-wrap: wrap; justify-content: center; }
  .stat-item { flex: 1; min-width: 80px; }
  .stat-sep { display: none; }
}
</style>
