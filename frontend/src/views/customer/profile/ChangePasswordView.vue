<script setup>
import { ref } from 'vue'
import { apiClient } from '../../../services/apiClient'
import { useAuthStore } from '../../../stores/auth'

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
    form.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch (err) {
    error.value = err.message || 'Lỗi khi đổi mật khẩu.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="change-password-page container">
    <div class="profile-grid">
      <aside class="profile-sidebar">
        <nav class="side-nav">
          <RouterLink to="/profile" class="nav-item">
            <span class="icon">👤</span>
            Thông tin cá nhân
          </RouterLink>
          <RouterLink to="/profile/my-tournaments" class="nav-item">
            <span class="icon">🏆</span>
            Giải đấu & Trận đấu
          </RouterLink>
          <RouterLink to="/profile/change-password" class="nav-item">
            <span class="icon">🔒</span>
            Đổi mật khẩu
          </RouterLink>
          <button class="nav-item logout" @click="authStore.logout()">
            <span class="icon">🚪</span>
            Đăng xuất
          </button>
        </nav>
      </aside>

      <main class="profile-main">
        <div class="card">
          <h3>Đổi mật khẩu</h3>
          <p class="subtitle">Vui lòng nhập mật khẩu hiện tại và mật khẩu mới để cập nhật.</p>

          <form @submit.prevent="handleChangePassword" class="password-form">
            <div v-if="success" class="alert alert-success">{{ success }}</div>
            <div v-if="error" class="alert alert-error">{{ error }}</div>

            <div class="form-group">
              <label>Mật khẩu hiện tại</label>
              <input v-model="form.old_password" type="password" required placeholder="••••••••" />
            </div>

            <div class="form-group">
              <label>Mật khẩu mới</label>
              <input v-model="form.new_password" type="password" required placeholder="••••••••" />
            </div>

            <div class="form-group">
              <label>Xác nhận mật khẩu mới</label>
              <input v-model="form.confirm_password" type="password" required placeholder="••••••••" />
            </div>

            <div class="form-actions">
              <button type="submit" class="btn-submit" :disabled="loading">
                {{ loading ? 'Đang thực hiện...' : 'Cập nhật mật khẩu' }}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.change-password-page { padding-top: 8rem; padding-bottom: 6rem; }

.profile-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 3rem;
  align-items: start;
}

.side-nav {
  display: flex; flex-direction: column; gap: 0.5rem;
  background: white; padding: 1.5rem; border-radius: 28px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.03);
}

.nav-item {
  display: flex; align-items: center; gap: 1rem; padding: 1rem 1.5rem;
  border-radius: 16px; text-decoration: none; color: #4e6073;
  font-weight: 700; transition: all 0.2s; background: transparent;
  border: none; cursor: pointer; font-family: inherit; font-size: 0.95rem;
}

.nav-item:hover { background: rgba(0, 105, 83, 0.05); color: #006953; }
.nav-item.router-link-active { background: #006953; color: white; box-shadow: 0 10px 20px rgba(0, 105, 83, 0.15); }

.card {
  background: white; padding: 3rem; border-radius: 32px;
  box-shadow: 0 4px 25px rgba(0,0,0,0.02);
}

.card h3 { margin-bottom: 1rem; color: #123f34; font-size: 1.5rem; border-left: 6px solid #006953; padding-left: 1.5rem; }
.subtitle { color: #6e7a74; margin-bottom: 2.5rem; margin-left: 2rem; }

.password-form { display: flex; flex-direction: column; gap: 1.5rem; max-width: 500px; }

.form-group { display: flex; flex-direction: column; gap: 0.8rem; }
.form-group label { font-weight: 700; color: #4e6073; font-size: 0.9rem; margin-left: 0.4rem; }
.form-group input {
  padding: 1.2rem; border-radius: 16px; border: 2px solid #f0f2f2;
  background: #f8f9f9; font: inherit; transition: 0.2s;
}
.form-group input:focus { border-color: #006953; outline: none; background: white; }

.btn-submit {
  margin-top: 1rem; padding: 1.2rem 3rem; border-radius: 18px; border: none;
  background: #006953; color: white; font-weight: 800; font-size: 1.1rem;
  cursor: pointer; box-shadow: 0 15px 30px rgba(0, 105, 83, 0.2); transition: 0.2s;
}
.btn-submit:hover { transform: translateY(-3px); box-shadow: 0 20px 40px rgba(0, 105, 83, 0.3); }

.alert { padding: 1rem 1.5rem; border-radius: 14px; font-weight: 600; margin-bottom: 1rem; }
.alert-success { background: #e8f5e9; color: #2e7d32; }
.alert-error { background: #ffebee; color: #c62828; }

@media (max-width: 800px) {
  .profile-grid { grid-template-columns: 1fr; }
}
</style>
