<script setup>
import { onMounted, ref } from 'vue'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const isLoading = ref(false)
const errorMessage = ref('')

const loadProfile = async () => {
  errorMessage.value = ''
  isLoading.value = true
  try {
    await authStore.fetchCurrentProfile()
  } catch {
    errorMessage.value = 'Không thể tải hồ sơ từ API /api/players/me.'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<template>
  <div class="profile-grid">
    <section class="profile-card">
      <header>
        <h2>Admin Account</h2>
        <p>Thông tin tài khoản hiện tại dựa trên API `/api/players/me`.</p>
      </header>

      <el-skeleton :loading="isLoading" animated>
        <template #template>
          <el-skeleton-item variant="h1" style="width: 60%" />
          <el-skeleton-item variant="text" style="width: 80%" />
          <el-skeleton-item variant="text" style="width: 50%" />
        </template>
        <template #default>
          <div v-if="errorMessage" class="error-banner">{{ errorMessage }}</div>
          <div v-else class="profile-detail">
            <div>
              <span>Email</span>
              <strong>{{ authStore.profile?.user_info?.email || authStore.user?.email || 'N/A' }}</strong>
            </div>
            <div>
              <span>Họ và tên</span>
              <strong>{{ authStore.profile?.user_info?.full_name || authStore.user?.full_name || 'N/A' }}</strong>
            </div>
            <div>
              <span>User ID</span>
              <strong>{{ authStore.profile?.user_info?.id || 'N/A' }}</strong>
            </div>
            <div>
              <span>Role ID</span>
              <strong>{{ authStore.profile?.user_info?.role_id || authStore.roleId || 'N/A' }}</strong>
            </div>
          </div>
        </template>
      </el-skeleton>
    </section>
  </div>
</template>

<style scoped>
.profile-grid {
  display: grid;
  gap: 18px;
}

.profile-card {
  padding: 24px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 18px 34px rgba(18, 30, 27, 0.06);
}

.profile-card header {
  margin-bottom: 18px;
}

.profile-card h2 {
  margin-bottom: 6px;
  font-size: 1.6rem;
  letter-spacing: -0.03em;
  color: #172320;
}

.profile-card p {
  color: #556a65;
}

.profile-detail {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.profile-detail span {
  display: block;
  font-size: 0.78rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6c7c77;
}

.profile-detail strong {
  font-size: 1.05rem;
  color: #172320;
}

.error-banner {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(186, 26, 26, 0.08);
  color: #9a1414;
  border: 1px solid rgba(186, 26, 26, 0.2);
}

@media (max-width: 720px) {
  .profile-detail {
    grid-template-columns: 1fr;
  }
}
</style>
