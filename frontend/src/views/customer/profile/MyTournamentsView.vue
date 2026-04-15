<script setup>
import { onMounted } from 'vue'
import { useTournamentStore } from '../../../stores/tournament'
import { useAuthStore } from '../../../stores/auth'

const tournamentStore = useTournamentStore()
const authStore = useAuthStore()


onMounted(() => {
  tournamentStore.fetchMyRegistrations()
})

// Trigger HMR for cancellation feature

const getStatusClass = (status) => {
  const classes = {
    pending: 'status-holding',
    confirmed: 'status-approved',
    rejected: 'status-rejected',
    cancelled: 'status-expired'
  }
  return classes[status] || ''
}

const getStatusText = (status) => {
  const texts = {
    pending: 'Đang giữ chỗ (Chờ thanh toán)',
    confirmed: 'Đã xác nhận',
    rejected: 'Bị từ chối',
    cancelled: 'Đã hết hạn/Hủy'
  }
  return texts[status] || status
}


const handleCancel = async (regId) => {
  if (confirm('Bạn có chắc chắn muốn hủy đăng ký này không?')) {
    try {
      await tournamentStore.cancelRegistration(regId)
      alert('Hủy đăng ký thành công.')
    } catch (err) {
      alert('Không thể hủy: ' + (err.message || 'Lỗi hệ thống'))
    }
  }
}


</script>

<template>
  <div class="my-tournaments container">
    <!-- Header Section (Same as Profile) -->
    <section v-if="authStore.user" class="profile-header">
      <div class="avatar-section">
        <div class="avatar-box">
          <img v-if="authStore.user.avatar_url" :src="authStore.user.avatar_url" alt="Avatar" />
          <div v-else class="avatar-placeholder">👤</div>
        </div>
      </div>

      <div class="header-info">
        <div class="name-row">
          <h1>{{ authStore.user.full_name }}</h1>
        </div>
        <p class="role-badge">Hạng thành viên: Pro Player</p>
      </div>
    </section>

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
          <button class="nav-item logout" @click="authStore.logout()">
            <span class="icon">🚪</span>
            Đăng xuất
          </button>
        </nav>
      </aside>

      <main class="profile-main">
        <div class="header-section">
          <h1>Giải đấu của tôi</h1>
          <p>Danh sách các giải đấu bạn đã đăng ký tham gia.</p>
        </div>

        <div v-if="tournamentStore.loading" class="loading-state">
          <div class="spinner"></div>
          <p>Đang tải danh sách đăng ký...</p>
        </div>

        <div v-else-if="tournamentStore.myRegistrations.length > 0" class="registrations-grid">
          <div v-for="reg in tournamentStore.myRegistrations" :key="reg.id" class="reg-card">
            <div class="reg-header">
              <span class="status-badge" :class="getStatusClass(reg.status)">
                {{ getStatusText(reg.status) }}
              </span>
              <span class="reg-date">{{ new Date(reg.registered_at).toLocaleDateString('vi-VN') }}</span>
            </div>

            <div class="reg-body">
              <div class="tournament-info">
                <h3>{{ reg.tournament_name || 'Giải đấu #' + reg.tournament_id }}</h3>
                <p>Hạng mục: {{ reg.registrant_type === 'single' ? 'Đơn' : 'Đôi/Đồng đội' }}</p>
              </div>

              <!-- QR Section only if confirmed -->
              <div v-if="reg.status === 'confirmed'" class="qr-section">
                <div class="qr-box">
                  <img v-if="reg.qr_code_url" :src="reg.qr_code_url" alt="QR Check-in" />
                  <div v-else class="qr-placeholder">QR CODE</div>
                </div>
                <!-- Hiển thị mã ID thủ công để dễ test trên máy tính -->
                <div style="margin-bottom: 5px;">
                  <code style="background: #f0f3f2; padding: 2px 6px; border-radius: 4px; font-weight: 800; color: #006953; font-size: 0.8rem;">
                    STT_REG_{{ reg.id }}
                  </code>
                </div>
                <p class="qr-tip">Mã check-in tại sân</p>
              </div>
            </div>

            <div class="reg-footer">
              <button class="btn-detail" @click="$router.push({ name: 'tournament-detail', params: { id: reg.tournament_id } })">
                Xem thông tin giải
              </button>
              <button v-if="reg.status === 'pending'" 
                      class="btn-cancel" 
                      @click="handleCancel(reg.id)">
                Hủy đăng ký
              </button>
              <p v-else-if="reg.status === 'confirmed'" class="cancellation-note">
                Vui lòng liên hệ CLB/Sân để hỗ trợ hủy & hoàn phí.
              </p>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <div class="empty-icon">🎾</div>
          <h3>Bạn chưa đăng ký giải đấu nào</h3>
          <p>Hãy tham gia ngay các giải đấu hấp dẫn đang mở đăng ký.</p>
          <button class="btn-primary" @click="$router.push({ name: 'tournaments' })">Khám phá giải đấu</button>
        </div>
      </main>
    </div>

  </div>
</template>

<style scoped>
.my-tournaments {
  padding-top: 8rem;
  padding-bottom: 6rem;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 3rem;
  margin-bottom: 2rem;
  background: white;
  padding: 2.5rem;
  border-radius: 32px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.03);
}

.avatar-section { display: flex; flex-direction: column; align-items: center; gap: 1rem; }
.avatar-box {
  width: 100px; height: 100px;
  border-radius: 30px; overflow: hidden;
  background: #f0f7f4; border: 3px solid white;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}
.avatar-box img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; }

.header-info { flex: 1; }
.header-info h1 { font-size: 2.22rem; color: #123f34; margin: 0; }
.role-badge { color: #6e7a74; margin-top: 0.5rem; font-weight: 600; font-size: 1rem; }

.profile-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 3rem;
  align-items: start;
}

.profile-sidebar {
  position: sticky;
  top: 100px;
}

.side-nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: white;
  padding: 1.5rem;
  border-radius: 28px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.03);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-radius: 16px;
  text-decoration: none;
  color: #4e6073;
  font-weight: 700;
  transition: all 0.2s;
  background: transparent;
  border: none;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.95rem;
  text-align: left;
}

.nav-item .icon { font-size: 1.2rem; }

.nav-item:hover {
  background: rgba(0, 105, 83, 0.05);
  color: #006953;
}

.nav-item.router-link-active {
  background: #006953;
  color: white;
  box-shadow: 0 10px 20px rgba(0, 105, 83, 0.15);
}

.nav-item.logout {
  margin-top: 1rem;
  color: #ba1a1a;
  border-top: 1px solid #f0f0f0;
  border-radius: 0;
  padding-top: 1.5rem;
}
.nav-item.logout:hover {
  background: rgba(186, 26, 26, 0.05);
}

.profile-main {
  flex: 1;
}

.header-section {
  margin-bottom: 2.5rem;
}
.header-section h1 { font-size: 2rem; color: #123f34; margin-bottom: 0.5rem; }
.header-section p { color: #6e7a74; }



.registrations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 2rem;
}

.reg-card {
  background: white;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
}

.reg-header {
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fbfcfb;
  border-bottom: 1px solid #f0f0f0;
}

.status-badge {
  padding: 0.4rem 0.8rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-holding { background: #fff3e0; color: #ef6c00; border: 1px solid #ffe0b2; }
.status-approved { background: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
.status-rejected { background: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }
.status-expired { background: #f5f5f5; color: #757575; border: 1px solid #e0e0e0; }

.reg-date {
  font-size: 0.85rem;
  color: #9e9e9e;
}

.reg-body {
  padding: 2rem;
  flex: 1;
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
}

.tournament-info h3 {
  font-size: 1.4rem;
  color: #123f34;
  margin-bottom: 0.5rem;
}

.tournament-info p {
  color: #6e7a74;
}

.qr-section {
  text-align: center;
  width: 120px;
}

.qr-box {
  width: 100px;
  height: 100px;
  background: white;
  border: 1px solid #eee;
  padding: 5px;
  margin: 0 auto 0.5rem;
}

.qr-box img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.qr-placeholder {
  width: 100%;
  height: 100%;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.6rem;
  font-weight: 800;
}

.qr-tip {
  font-size: 0.7rem;
  color: #6e7a74;
  font-weight: 600;
}

.status-placeholder {
  width: 150px;
  font-size: 0.8rem;
  color: #9e9e9e;
  text-align: right;
  font-style: italic;
}

.reg-footer {
  padding: 1rem 2rem;
  background: #fbfcfb;
  border-top: 1px solid #f0f0f0;
}

.btn-detail {
  width: 100%;
  padding: 0.75rem;
  background: none;
  border: 1px solid #ddd;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  color: #4e6073;
  margin-bottom: 0.5rem;
}


.btn-cancel {
  width: 100%;
  padding: 0.75rem;
  background: #fff;
  border: 1px solid #ff5252;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  color: #ff5252;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #ff5252;
  color: white;
}


.btn-detail:hover {
  border-color: #006953;
  color: #006953;
}

.cancellation-note {
  font-size: 0.75rem;
  color: #6e7a74;
  text-align: center;
  margin-top: 0.5rem;
  font-style: italic;
}

.empty-state {
  text-align: center;
  padding: 5rem 0;
  background: white;
  border-radius: 32px;
}

.empty-icon { font-size: 4rem; margin-bottom: 1.5rem; }
.empty-state h3 { font-size: 1.8rem; margin-bottom: 1rem; color: #123f34; }
.empty-state p { margin-bottom: 2rem; color: #6e7a74; }

.btn-primary {
  padding: 1rem 2.5rem;
  background: #006953;
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
}

.loading-state { text-align: center; padding: 4rem; }
.spinner {
  width: 40px; height: 40px; border: 4px solid rgba(0,105,83,0.1);
  border-top-color: #006953; border-radius: 50%; animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 500px) {
  .registrations-grid { grid-template-columns: 1fr; }
  .reg-body { flex-direction: column; align-items: center; text-align: center; }
  .status-placeholder { text-align: center; width: 100%; }
}
</style>
