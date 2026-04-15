<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const LOGIN_ENDPOINT = `${API_BASE_URL}/api/auth/login`

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isLoggingIn = ref(false)
const errorMessage = ref('')
const showPassword = ref(false)

const form = ref({
  email: '',
  password: '',
})

onMounted(() => {
  // Nếu đã là admin rồi thì vào thẳng dashboard
  if (authStore.isAuthenticated && authStore.isAdmin) {
    router.push('/admin')
  }
})

const login = async () => {
  errorMessage.value = ''
  if (!form.value.email || !form.value.password) {
    errorMessage.value = 'Vui lòng nhập đầy đủ thông tin.'
    return
  }

  isLoggingIn.value = true

  try {
    const response = await fetch(LOGIN_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })

    if (!response.ok) {
      errorMessage.value = 'Đăng nhập thất bại. Tài khoản không tồn tại hoặc sai mật khẩu.'
      return
    }

    const data = await response.json()
    
    if (data.account_type !== 'admin') {
      errorMessage.value = 'Lỗi: Tài khoản này không có quyền truy cập khu vực Quản trị.'
      return
    }

    authStore.setSession({
      accessToken: data.access_token,
      tokenType: data.token_type,
      user: {
        email: form.value.email,
        full_name: data.full_name,
        user_id: data.user_id,
        role_id: data.role_id,
        account_type: data.account_type
      }
    })

    router.push('/admin')
  } catch (err) {
    errorMessage.value = 'Không thể kết nối tới máy chủ.'
  } finally {
    isLoggingIn.value = false
  }
}
</script>

<template>
  <div class="admin-login-page">
    <div class="login-card">
      <div class="admin-icon">🛡️</div>
      <h1>Admin Portal</h1>
      <p>Khu vực dành riêng cho người quản trị Saigon Tennis</p>

      <div v-if="errorMessage" class="error-box">{{ errorMessage }}</div>

      <form @submit.prevent="login" class="login-form">
        <div class="field">
          <label>Admin Email</label>
          <input v-model="form.email" type="email" placeholder="admin@example.com" required />
        </div>
        
        <div class="field">
          <label>Password</label>
          <input v-model="form.password" :type="showPassword ? 'text' : 'password'" placeholder="••••••••" required />
        </div>

        <button type="submit" :disabled="isLoggingIn" class="btn-login">
          {{ isLoggingIn ? 'Đang xác thực...' : 'Đăng nhập hệ thống' }}
        </button>
      </form>
      
      <div class="footer-links">
        <router-link to="/">Quay về trang chủ</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #091d2e; /* Dark theme for admin */
  color: white;
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: #123f34;
  padding: 3rem;
  border-radius: 32px;
  text-align: center;
  box-shadow: 0 40px 100px rgba(0,0,0,0.5);
}

.admin-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

h1 {
  font-size: 2.2rem;
  margin-bottom: 0.5rem;
}

p {
  color: #bdc9c3;
  margin-bottom: 2.5rem;
}

.error-box {
  background: rgba(186, 26, 26, 0.2);
  color: #ffb4ab;
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  font-size: 0.9rem;
}

.login-form {
  display: grid;
  gap: 1.5rem;
  text-align: left;
}

.field label {
  display: block;
  font-size: 0.75rem;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
  color: #8da49c;
}

.field input {
  width: 100%;
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05);
  color: white;
  font-size: 1rem;
}

.btn-login {
  width: 100%;
  padding: 1.2rem;
  border-radius: 16px;
  border: none;
  background: #13846a;
  color: white;
  font-weight: 800;
  font-size: 1.1rem;
  cursor: pointer;
  margin-top: 1rem;
}

.footer-links {
  margin-top: 2rem;
}

.footer-links a {
  color: #13846a;
  text-decoration: none;
  font-weight: 600;
}
</style>
