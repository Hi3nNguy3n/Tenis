<script setup>
import { onMounted, ref } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { 
  User, Message, Lock, Postcard, 
  Monitor, Connection, ArrowLeft,
  CircleCheckFilled, Setting, Key
} from '@element-plus/icons-vue'
import { t } from '../../utils/locale'

const authStore = useAuthStore()
const isLoading = ref(false)
const errorMessage = ref('')

const loadProfile = async () => {
  errorMessage.value = ''
  isLoading.value = true
  try {
    await authStore.fetchCurrentProfile()
  } catch {
    errorMessage.value = t('admin.loadProfileError')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<template>
  <div class="saas-container" v-loading="isLoading">
    <!-- Action Bar -->
    <section class="saas-header">
      <div class="header-left">
        <div class="operation-badge-premium orange">
          <el-icon class="mr-1"><Lock /></el-icon>
          <span>Security & Identity</span>
        </div>
        <div class="header-titles">
          <h2 class="saas-title">{{ $t('admin.adminAccount') }}</h2>
          <p class="saas-subtitle">{{ $t('admin.adminProfileDesc') }}</p>
        </div>
      </div>
    </section>

    <!-- Profile Grid -->
    <div class="profile-grid-saas">
      <!-- Left Column: Identity -->
      <div class="identity-card-premium">
        <div class="ic-banner"></div>
        <div class="ic-content">
          <div class="ic-avatar-wrapper">
            <el-avatar :size="120" class="ic-avatar">{{ authStore.profile?.user_info?.full_name?.charAt(0) || 'A' }}</el-avatar>
            <div class="ic-status-dot"></div>
          </div>
          <h3 class="ic-name">{{ authStore.profile?.user_info?.full_name || authStore.user?.full_name || 'Admin' }}</h3>
          <p class="ic-role">{{ authStore.roleId === 1 ? 'Root Administrator' : 'System Manager' }}</p>
          
          <div class="ic-badges">
            <el-tag effect="dark" type="success" class="saas-badge"><el-icon class="mr-1"><CircleCheckFilled /></el-icon> Verified</el-tag>
            <el-tag effect="dark" type="primary" class="saas-badge"><el-icon class="mr-1"><Key /></el-icon> Root Access</el-tag>
          </div>
        </div>
      </div>

      <!-- Right Column: Details -->
      <div class="details-stack-saas">
        <div v-if="errorMessage" class="saas-alert error mb-4">{{ errorMessage }}</div>
        
        <div class="saas-card-premium">
          <div class="card-header-saas">
            <el-icon class="mr-2"><Postcard /></el-icon>
            <span>Thông tin định danh</span>
          </div>
          
          <div class="info-grid-saas">
            <div class="info-item-saas">
              <span class="info-label">Email Address</span>
              <div class="info-value-box">
                <el-icon><Message /></el-icon>
                <strong>{{ authStore.profile?.user_info?.email || authStore.user?.email || 'N/A' }}</strong>
              </div>
            </div>
            
            <div class="info-item-saas">
              <span class="info-label">Full Name</span>
              <div class="info-value-box">
                <el-icon><User /></el-icon>
                <strong>{{ authStore.profile?.user_info?.full_name || authStore.user?.full_name || 'N/A' }}</strong>
              </div>
            </div>

            <div class="info-item-saas">
              <span class="info-label">Access Level</span>
              <div class="info-value-box">
                <el-icon><Lock /></el-icon>
                <strong>{{ authStore.profile?.user_info?.role_id || authStore.roleId || 'N/A' }} (Administrator)</strong>
              </div>
            </div>

            <div class="info-item-saas">
              <span class="info-label">System User ID</span>
              <div class="info-value-box">
                <el-icon><Setting /></el-icon>
                <code class="saas-code">ID: {{ authStore.profile?.user_info?.id || 'N/A' }}</code>
              </div>
            </div>
          </div>
        </div>

        <div class="saas-card-premium mt-4">
          <div class="card-header-saas">
            <el-icon class="mr-2"><Monitor /></el-icon>
            <span>Bảo mật & Phiên làm việc</span>
          </div>
          <div class="security-info-saas">
            <div class="si-row">
              <div class="si-left">
                <el-icon class="si-icon"><Connection /></el-icon>
                <div class="si-text">
                  <strong>Trạng thái kết nối</strong>
                  <span>Hệ thống đang hoạt động ổn định qua SSL</span>
                </div>
              </div>
              <el-tag type="success" effect="plain">ACTIVE</el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.saas-container { display: flex; flex-direction: column; gap: 32px; min-height: 100%; }

/* Action Bar */
.saas-header { display: flex; align-items: center; justify-content: space-between; }
.header-left { display: flex; align-items: center; }

.operation-badge-premium {
  background: #eff6ff; color: #2563eb; padding: 10px 20px; border-radius: 14px;
  font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
  display: inline-flex; align-items: center; margin-right: 24px;
}
.operation-badge-premium.orange { background: #fff7ed; color: #f97316; }

.header-titles { display: flex; flex-direction: column; gap: 4px; }
.saas-title { font-size: 1.8rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.02em; }
.saas-subtitle { font-size: 0.95rem; color: #64748b; margin: 0; }

/* Profile Grid */
.profile-grid-saas { display: grid; grid-template-columns: 350px 1fr; gap: 32px; }

/* Identity Card */
.identity-card-premium { background: #fff; border-radius: 32px; border: 1px solid #f1f5f9; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.02); }
.ic-banner { height: 120px; background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); position: relative; }
.ic-content { padding: 0 32px 40px; display: flex; flex-direction: column; align-items: center; margin-top: -60px; }

.ic-avatar-wrapper { position: relative; margin-bottom: 20px; }
.ic-avatar { border: 6px solid #fff; background: #f8fafc; color: #f97316; font-size: 40px; font-weight: 900; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
.ic-status-dot { position: absolute; bottom: 8px; right: 8px; width: 18px; height: 18px; background: #10b981; border: 3px solid #fff; border-radius: 50%; }

.ic-name { font-size: 1.5rem; font-weight: 900; color: #0f172a; margin: 0; }
.ic-role { font-size: 0.9rem; color: #64748b; font-weight: 700; margin: 4px 0 20px; }

.ic-badges { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
.saas-badge { border-radius: 10px; font-weight: 800; font-size: 0.75rem; padding: 6px 12px; }

/* Details Stack */
.details-stack-saas { display: flex; flex-direction: column; gap: 24px; }
.saas-card-premium { background: #fff; border-radius: 28px; border: 1px solid #f1f5f9; padding: 32px; box-shadow: 0 4px 20px rgba(0,0,0,0.01); }

.card-header-saas { margin-bottom: 24px; display: flex; align-items: center; font-weight: 900; color: #1e293b; font-size: 1rem; text-transform: uppercase; letter-spacing: 0.05em; }

.info-grid-saas { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.info-item-saas { display: flex; flex-direction: column; gap: 8px; }
.info-label { font-size: 0.75rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }

.info-value-box { display: flex; align-items: center; gap: 12px; background: #f8fafc; padding: 16px; border-radius: 16px; border: 1px solid #f1f5f9; }
.info-value-box strong { font-size: 1rem; color: #1e293b; font-weight: 700; }
.info-value-box .el-icon { color: #f97316; font-size: 18px; }

.saas-code { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #64748b; font-weight: 800; }

.security-info-saas { background: #f8fafc; border-radius: 16px; padding: 20px; }
.si-row { display: flex; justify-content: space-between; align-items: center; }
.si-left { display: flex; align-items: center; gap: 16px; }
.si-icon { width: 40px; height: 40px; background: #fff; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #10b981; font-size: 20px; border: 1px solid #f1f5f9; }
.si-text { display: flex; flex-direction: column; gap: 2px; }
.si-text strong { font-size: 0.95rem; color: #1e293b; }
.si-text span { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }

.saas-alert { padding: 16px 20px; border-radius: 16px; font-weight: 700; font-size: 0.9rem; border: 1px solid transparent; }
.saas-alert.error { background: #fef2f2; border-color: #fee2e2; color: #ef4444; }

@media (max-width: 1100px) {
  .profile-grid-saas { grid-template-columns: 1fr; }
  .info-grid-saas { grid-template-columns: 1fr; }
}

.mr-1 { margin-right: 4px; }
.mr-2 { margin-right: 8px; }
.mb-4 { margin-bottom: 16px; }
.mt-4 { margin-top: 16px; }
</style>
