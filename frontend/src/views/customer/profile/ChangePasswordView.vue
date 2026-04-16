<script setup>
import { ref } from 'vue'
import { apiClient } from '../../../services/apiClient'
import { useAuthStore } from '../../../stores/auth'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const loading = ref(false)
const error = ref('')
const success = ref('')

const form = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
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
    await apiClient.post('/api/auth/change-password', {
      old_password: form.value.old_password,
      new_password: form.value.new_password
    })
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
      <div class="container hero-content-shell">
        <div class="hero-flex">
          <div class="avatar-container">
            <div class="avatar-frame">
              <img v-if="authStore.user?.avatar_url" :src="authStore.user.avatar_url" alt="Avatar" />
              <div v-else class="avatar-placeholder">👤</div>
            </div>
          </div>
          
          <div class="hero-text-block">
            <span class="user-role-badge">bảo mật tài khoản</span>
            <h1>{{ authStore.user?.full_name }}</h1>
            
            <div class="hero-quick-stats">
              <div class="stat-item">
                <span class="stat-val">••••••</span>
                <span class="stat-lbl">Mật khẩu</span>
              </div>
              <div class="stat-sep"></div>
              <div class="stat-item">
                <span class="stat-val">🔒</span>
                <span class="stat-lbl">Trạng thái</span>
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
              <span class="icon">👤</span> hồ sơ
            </RouterLink>
            <RouterLink to="/profile/my-tournaments" class="nav-btn">
              <span class="icon">🎾</span> giải đấu
            </RouterLink>
            <RouterLink to="/profile/change-password" class="nav-btn active">
              <span class="icon">🔒</span> bảo mật
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
  background: var(--bg-soft);
  min-height: 100vh;
  padding-bottom: 5rem;
}

/* Hero Section (Reused) */
.profile-hero-banner {
  position: relative;
  height: 280px;
  background: #064e3b;
  margin-bottom: 4rem;
}

.banner-bg {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1595435063098-95843b0d2358?q=80&w=2070&auto=format&fit=crop');
  background-size: cover;
  background-position: center;
}

.hero-content-shell {
  height: 100%;
  display: flex;
  align-items: flex-end;
  padding-bottom: 2rem;
}

.hero-flex {
  display: flex;
  align-items: center;
  gap: 3rem;
  width: 100%;
}

.avatar-frame {
  width: 180px;
  height: 180px;
  background: #fff;
  border-radius: 12px;
  padding: 8px;
  box-shadow: var(--shadow-lg);
  margin-bottom: -60px;
  overflow: hidden;
}

.avatar-frame img { width: 100%; height: 100%; object-fit: cover; border-radius: 6px; }
.avatar-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 3rem; background: #f1f5f9; }

.hero-text-block { color: #fff; flex: 1; }
.user-role-badge { background: var(--secondary); color: #064e3b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; padding: 4px 12px; border-radius: 4px; margin-bottom: 0.5rem; display: inline-block; }
.hero-text-block h1 { font-size: 3rem; font-weight: 600; margin: 0 0 1rem; text-transform: uppercase; letter-spacing: -0.02em; }

.hero-quick-stats {
  display: flex;
  align-items: center;
  gap: 2rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 1rem 2rem;
  border-radius: 8px;
  width: fit-content;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.stat-item { text-align: center; }
.stat-val { display: block; font-size: 1.5rem; font-weight: 600; color: var(--secondary); }
.stat-lbl { font-size: 0.7rem; font-weight: 500; text-transform: uppercase; opacity: 0.7; }
.stat-sep { width: 1px; height: 30px; background: rgba(255, 255, 255, 0.2); }

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
