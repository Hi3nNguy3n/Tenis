<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '../../../stores/auth'
import { useTournamentStore } from '../../../stores/tournament'
import { RouterLink } from 'vue-router'
import { CameraFilled } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const tournamentStore = useTournamentStore()

onMounted(async () => {
  try {
    // Luôn fetch profile mới nhất để có đủ thông tin
    await authStore.fetchCurrentProfile()
    
    // Gọi đúng action từ tournamentStore để lấy các giải đã tham gia
    await tournamentStore.fetchMyRegistrations()
  } catch (error) {
    console.error('Lỗi tải dữ liệu giải đấu:', error)
  }
})
</script>

<template>
  <div class="profile-page-wrapper">
    <!-- Optimized Hero Header (Synced with Profile) -->
    <section class="profile-hero-banner">
      <div class="banner-bg"></div>
      <div class="banner-overlay"></div>
      
      <div class="container hero-content-shell">
        <div class="hero-flex">
          <div class="avatar-container">
            <div class="avatar-frame">
              <img v-if="authStore.user?.avatar_url" :src="authStore.user.avatar_url" alt="Avatar" />
              <div v-else class="avatar-placeholder">👤</div>
              
              <!-- Consistency: Camera icon placeholder/trigger -->
              <RouterLink to="/profile" class="avatar-upload-overlay">
                <el-icon><CameraFilled /></el-icon>
              </RouterLink>
            </div>
          </div>
          
          <div class="hero-text-block">
            <span class="user-role-badge">giải đấu của tôi</span>
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
            <RouterLink to="/profile/my-tournaments" class="nav-btn active">
              giải đấu
            </RouterLink>
            <RouterLink to="/profile/change-password" class="nav-btn">
              bảo mật
            </RouterLink>
          </nav>
        </aside>

        <!-- Dynamic Content Area -->
        <main class="content-primary">
          <div v-if="tournamentStore.myRegistrations?.length" class="tournaments-stack">
            <article 
              v-for="reg in tournamentStore.myRegistrations" 
              :key="reg.id" 
              class="atp-tour-card"
            >
              <div class="tour-main-info">
                <div class="tour-header-row">
                  <span class="tour-category">saigon tennis tour</span>
                  <span :class="['atp-status-pill', reg.payment_status]">
                    {{ reg.payment_status === 'confirmed' ? 'Đã xác nhận' : 'Đang xử lý' }}
                  </span>
                </div>
                
                <h2 class="atp-tour-name">{{ reg.tournament_name }}</h2>
                
                <div class="tour-meta-grid">
                  <div class="m-item">
                    <span class="m-label">Hạng đấu</span>
                    <span class="m-val">{{ reg.category_type || 'Chuyên nghiệp' }}</span>
                  </div>
                  <div class="m-item">
                    <span class="m-label">Ngày thi đấu</span>
                    <span class="m-val">{{ reg.tournament_date ? new Date(reg.tournament_date).toLocaleDateString() : 'TBD' }}</span>
                  </div>
                  <div class="m-item">
                    <span class="m-label">Địa điểm</span>
                    <span class="m-val">{{ reg.location || 'Saigon Tennis Center' }}</span>
                  </div>
                </div>
              </div>

              <!-- Ticket Stub Section -->
              <div class="atp-ticket-stub">
                <div class="stub-qr-box">
                  <!-- Simplified QR placeholder for UI design -->
                   <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=SAIGONTENNIS" alt="QR" />
                </div>
                <span class="stub-label">Mã đăng ký</span>
                <code>#{{ reg.id.toString().slice(-8).toUpperCase() }}</code>
                <p class="stub-hint">Trình mã này khi check-in tại sân</p>
              </div>
            </article>
          </div>

          <!-- Empty State -->
          <div v-else class="atp-empty-state-card">
            <div class="empty-visual">🎾</div>
            <h3>Bạn chưa tham gia giải nào</h3>
            <p>Khám phá các giải đấu mới nhất và đăng ký ngay hôm nay để nhận thứ hạng!</p>
            <RouterLink to="/tournaments" class="btn-atp-solid">Tìm giải đấu ngay</RouterLink>
          </div>
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

/* Hero Section (Synced from Profile) */
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
}

.nav-btn.active { background: var(--primary); color: #fff; box-shadow: var(--shadow-md); }

/* Tournament Cards */
.tournaments-stack { display: flex; flex-direction: column; gap: 1.5rem; }

.atp-tour-card {
  display: flex;
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
}

.atp-tour-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-md); }

.tour-main-info {
  flex: 1;
  padding: 2.5rem;
}

.tour-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.tour-category { font-size: 0.7rem; font-weight: 600; color: var(--primary); text-transform: uppercase; letter-spacing: 0.1em; }

.atp-status-pill { padding: 4px 12px; border-radius: 4px; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; }
.confirmed { background: #dcfce7; color: #166534; }
.pending { background: #fef9c3; color: #854d0e; }

.atp-tour-name { font-size: 1.8rem; font-weight: 600; color: var(--text-dark); margin: 0 0 2rem; text-transform: uppercase; line-height: 1.1; }

.tour-meta-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; }
.m-label { display: block; font-size: 0.65rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px; }
.m-val { font-size: 1rem; font-weight: 500; color: var(--text-dark); text-transform: uppercase; }

/* Ticket Stub */
.atp-ticket-stub {
  width: 200px;
  background: #f8fafc;
  border-left: 2px dashed var(--border-light);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
}

.stub-qr-box { width: 100px; height: 100px; background: #fff; padding: 6px; border-radius: 4px; margin-bottom: 1rem; border: 1px solid var(--border-light); }
.stub-qr-box img { width: 100%; height: 100%; }
.stub-label { font-size: 0.6rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px; }
.atp-ticket-stub code { background: #0f172a; color: #fff; padding: 4px 10px; border-radius: 4px; font-weight: 600; font-size: 0.85rem; margin-bottom: 0.5rem; }
.stub-hint { font-size: 0.6rem; font-weight: 700; color: var(--text-muted); margin: 0; }

/* Empty State */
.atp-empty-state-card { background: #fff; border-radius: 12px; padding: 5rem 2rem; text-align: center; border: 1px solid var(--border-light); }
.empty-visual { font-size: 4rem; margin-bottom: 1.5rem; opacity: 0.15; }
.atp-empty-state-card h3 { font-size: 1.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 1rem; }
.atp-empty-state-card p { color: var(--text-muted); font-weight: 700; margin-bottom: 2rem; }

.btn-atp-solid {
  background: var(--primary);
  color: #fff;
  border: none;
  padding: 14px 30px;
  border-radius: 6px;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.9rem;
  text-decoration: none;
  display: inline-block;
  transition: var(--transition);
}
.btn-atp-solid:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }

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
  .atp-tour-card { flex-direction: column; }
  .atp-ticket-stub { width: 100%; border-left: none; border-top: 2px dashed var(--border-light); padding: 2.5rem; }
}

@media (max-width: 768px) {
  .profile-hero-banner { height: 220px; }
  .avatar-frame { width: 150px; height: 150px; }
  .hero-text-block h1 { font-size: 2.2rem; }
  .tour-main-info { padding: 1.5rem; }
  .atp-tour-name { font-size: 1.4rem; }
  .tour-meta-grid { grid-template-columns: 1fr; gap: 1.5rem; }
}

@media (max-width: 480px) {
  .hero-quick-stats { flex-direction: column; width: 100%; gap: 1rem; }
  .stat-sep { display: none; }
}
</style>