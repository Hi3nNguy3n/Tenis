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

/* Tournament Cards */
.tournaments-stack { display: flex; flex-direction: column; gap: 1.5rem; }
.atp-tour-card { display: flex; background: #fff; border: 1px solid var(--profile-border); border-radius: 16px; overflow: hidden; box-shadow: var(--profile-shadow-sm); transition: 0.3s; }
.atp-tour-card:hover { transform: translateY(-4px); }

.tour-main-info { flex: 1; padding: 2rem; }
.tour-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.tour-category { font-size: 0.65rem; font-weight: 700; color: var(--profile-primary); text-transform: uppercase; letter-spacing: 0.1em; }
.atp-status-pill { padding: 4px 10px; border-radius: 6px; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; }
.confirmed { background: #dcfce7; color: #166534; }
.pending { background: #fef9c3; color: #854d0e; }

.atp-tour-name { font-size: 1.5rem; font-weight: 600; color: var(--profile-text); margin: 0 0 1.5rem; text-transform: uppercase; line-height: 1.2; }
.tour-meta-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
.m-label { display: block; font-size: 0.6rem; font-weight: 600; color: var(--profile-muted); text-transform: uppercase; margin-bottom: 4px; }
.m-val { font-size: 0.9rem; font-weight: 500; color: var(--profile-text); text-transform: uppercase; }

.atp-ticket-stub { width: 180px; background: #f8fafc; border-left: 2px dashed var(--profile-border); display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 1.5rem; text-align: center; }
.stub-qr-box { width: 90px; height: 90px; background: #fff; padding: 6px; border-radius: 8px; margin-bottom: 0.75rem; border: 1px solid var(--profile-border); }
.stub-qr-box img { width: 100%; height: 100%; }
.stub-label { font-size: 0.6rem; font-weight: 700; color: var(--profile-muted); text-transform: uppercase; margin-bottom: 4px; }
.atp-ticket-stub code { background: #0f172a; color: #fff; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 0.8rem; margin-bottom: 0.5rem; }
.stub-hint { font-size: 0.6rem; color: var(--profile-muted); margin: 0; }

/* Empty State */
.atp-empty-state-card { background: #fff; border-radius: 16px; padding: 4rem 2rem; text-align: center; border: 1px solid var(--profile-border); }
.empty-visual { font-size: 3.5rem; margin-bottom: 1rem; opacity: 0.2; }
.btn-atp-solid { background: var(--profile-primary); color: #fff; border: none; padding: 12px 28px; border-radius: 10px; font-weight: 700; text-transform: uppercase; font-size: 0.85rem; cursor: pointer; text-decoration: none; display: inline-block; }

/* Responsive Queries */
@media (max-width: 1024px) {
  .layout-grid { grid-template-columns: 1fr; margin-top: 1.5rem; }
  .sidebar-nav { flex-direction: row; overflow-x: auto; position: sticky; top: 0; z-index: 50; background: var(--profile-soft-bg); padding: 1rem 0; margin: 0 -1rem; padding-left: 1rem; padding-right: 1rem; }
  .nav-btn { width: auto; white-space: nowrap; padding: 0.8rem 1.2rem; }
  .atp-tour-card { flex-direction: column; }
  .atp-ticket-stub { width: 100%; border-left: none; border-top: 2px dashed var(--profile-border); padding: 2rem; }
}

@media (max-width: 768px) {
  .hero-flex { flex-direction: column; text-align: center; padding: 3rem 1rem; gap: 1.5rem; }
  .avatar-frame { width: 120px; height: 120px; margin: 0 auto; }
  .hero-text-block h1 { font-size: 2rem; }
  .hero-quick-stats { width: 100%; justify-content: space-between; }
  .tour-meta-grid { grid-template-columns: 1fr; gap: 1rem; }
}

@media (max-width: 480px) {
  .hero-quick-stats { flex-wrap: wrap; justify-content: center; }
  .stat-item { flex: 1; min-width: 80px; }
  .stat-sep { display: none; }
}
</style>