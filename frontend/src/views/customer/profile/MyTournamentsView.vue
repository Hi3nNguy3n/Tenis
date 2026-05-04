<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '../../../stores/auth'
import { useTournamentStore } from '../../../stores/tournament'
import { RouterLink } from 'vue-router'
import { CameraFilled, User, Calendar, Setting } from '@element-plus/icons-vue'
import { t } from '../../../utils/locale'

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
    <!-- KHU VỰC HERO BANNER -->
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
            <span class="user-role-badge">GIẢI ĐẤU CỦA TÔI</span>
            <h1>{{ authStore.user?.full_name || 'Người dùng' }}</h1>
            
            <div class="hero-quick-stats">
              <div class="stat-item">
                <span class="stat-val">#{{ authStore.profile?.player_profile?.rank || '---' }}</span>
                <span class="stat-lbl">{{ t('profile.rank') || 'Hạng' }}</span>
              </div>
              <div class="stat-sep"></div>
              <div class="stat-item">
                <span class="stat-val">{{ authStore.profile?.player_profile?.wins || 0 }}</span>
                <span class="stat-lbl">{{ t('profile.win') || 'Thắng' }}</span>
              </div>
              <div class="stat-sep"></div>
              <div class="stat-item">
                <span class="stat-val">{{ authStore.profile?.player_profile?.losses || 0 }}</span>
                <span class="stat-lbl">{{ t('profile.loss') || 'Bại' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- LAYOUT CHÍNH (SIDEBAR + CONTENT) -->
    <div class="container main-layout-container">
      <div class="layout-grid">
        
        <!-- SIDEBAR ĐIỀU HƯỚNG BÊN TRÁI -->
        <aside class="compact-sidebar">
          <nav class="sidebar-nav">
            <RouterLink to="/profile" class="nav-btn">
              <el-icon class="nav-icon"><User /></el-icon>
              <span>{{ t('profile.sections.info') || 'Hồ sơ' }}</span>
            </RouterLink>
            <RouterLink to="/profile/my-tournaments" class="nav-btn active">
              <el-icon class="nav-icon"><Calendar /></el-icon>
              <span>{{ t('profile.sections.tournaments') || 'Giải đấu' }}</span>
            </RouterLink>
            <RouterLink to="/profile/change-password" class="nav-btn">
              <el-icon class="nav-icon"><Setting /></el-icon>
              <span>{{ t('profile.sections.security') || 'Bảo mật' }}</span>
            </RouterLink>
          </nav>
        </aside>

        <!-- NỘI DUNG CHÍNH BÊN PHẢI -->
        <main class="content-primary">
          <div v-if="tournamentStore.myRegistrations?.length" class="tournaments-stack">
            <article 
              v-for="reg in tournamentStore.myRegistrations" 
              :key="reg.id" 
              class="atp-tour-card"
            >
              <div class="tour-main-info">
                <div class="tour-header-row">
                  <span class="tour-category">SAIGON TENNIS TOUR</span>
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

              <!-- Giao diện Vé điện tử -->
              <div class="atp-ticket-stub">
                <div class="stub-qr-box">
                   <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=SAIGONTENNIS" alt="QR Code" />
                </div>
                <span class="stub-label">Mã đăng ký</span>
                <code>#{{ reg.id.toString().slice(-8).toUpperCase() }}</code>
                <p class="stub-hint">Trình mã này khi check-in tại sân</p>
              </div>
            </article>
          </div>

          <!-- Trạng thái trống (Empty State) -->
          <div v-else class="atp-empty-state-card">
            <div class="empty-visual">🎾</div>
            <h3>{{ t('profile.noTournaments') || 'Bạn chưa tham gia giải nào' }}</h3>
            <p>{{ t('profile.exploreTournaments') || 'Khám phá các giải đấu mới nhất và đăng ký ngay hôm nay để nhận thứ hạng!' }}</p>
            <RouterLink to="/tournaments" class="btn-atp-solid">{{ t('profile.findTournamentBtn') || 'Tìm giải đấu ngay' }}</RouterLink>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* =======================================================
   BASE THEME
   ======================================================= */
.profile-page-wrapper {
  --profile-primary: #002855; /* Navy Blue ATP */
  --profile-primary-dark: #001f44;
  --profile-secondary: #c1ff72; /* Dạ quang */
  --profile-soft-bg: #f8fafc;
  --profile-border: #e2e8f0;
  --profile-text: #0f172a;
  --profile-muted: #64748b;
  --profile-shadow: 0 4px 15px rgba(0,0,0,0.03);
  
  font-family: 'Inter', Arial, sans-serif !important;
  background: var(--profile-soft-bg);
  min-height: 100vh;
  padding-bottom: 3rem;
}

/* =======================================================
   HERO BANNER
   ======================================================= */
.profile-hero-banner { 
  position: relative; 
  min-height: 280px; 
  background: var(--profile-primary); 
  display: flex;
  align-items: center;
  overflow: hidden;
}

.banner-bg { 
  position: absolute; inset: 0; 
  background-image: url('/src/assets/hero_bg.png'); 
  background-size: cover; background-position: center; opacity: 0.15; 
}
.banner-overlay { 
  position: absolute; inset: 0; 
  background: linear-gradient(90deg, rgba(0, 40, 85, 0.95) 0%, rgba(0, 40, 85, 0.7) 100%); 
}

.hero-content-shell { position: relative; z-index: 2; width: 100%; max-width: 1280px; margin: 0 auto; }
.hero-flex { 
  display: flex; align-items: center; gap: 2.5rem; padding: 2.5rem 1.5rem;
}

/* Avatar Frame */
.avatar-frame { 
  position: relative; 
  width: 140px; height: 140px; 
  background: #fff; border-radius: 50%; 
  padding: 4px; box-shadow: 0 10px 25px rgba(0,0,0,0.3);
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.avatar-frame img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }
.avatar-placeholder { font-size: 3.5rem; }

.avatar-upload-overlay { 
  position: absolute; right: 0px; bottom: 5px; 
  width: 36px; height: 36px; 
  background: var(--profile-secondary); color: var(--profile-primary); 
  display: flex; align-items: center; justify-content: center; 
  border-radius: 50%; cursor: pointer; border: 3px solid #fff; 
  transition: 0.2s; font-size: 1.1rem;
}
.avatar-upload-overlay:hover { transform: scale(1.1); }

/* Text Block */
.hero-text-block { color: #fff; flex: 1; min-width: 0; }
.user-role-badge { 
  padding: 0.3rem 0.8rem; border-radius: 4px; 
  background: var(--profile-secondary); color: var(--profile-primary); 
  font-size: 0.7rem; font-weight: 800; text-transform: uppercase; 
  margin-bottom: 0.75rem; display: inline-block; 
}
.hero-text-block h1 { margin: 0 0 1rem; font-size: 2.5rem; font-weight: 800; letter-spacing: -0.02em; color: #fff; }

.hero-quick-stats { 
  display: inline-flex; gap: 1.5rem; padding: 0.8rem 1.5rem; 
  border-radius: 8px; background: rgba(255, 255, 255, 0.1); 
  backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.15);
}
.stat-item { text-align: center; }
.stat-val { display: block; color: var(--profile-secondary); font-size: 1.4rem; font-weight: 800; }
.stat-lbl { display: block; color: #e2e8f0; font-size: 0.65rem; text-transform: uppercase; font-weight: 600; letter-spacing: 1px;}
.stat-sep { width: 1px; background: rgba(255, 255, 255, 0.2); }

/* =======================================================
   MAIN LAYOUT & SIDEBAR
   ======================================================= */
.main-layout-container { max-width: 1280px; margin: 0 auto; padding: 0 1.5rem; }
.layout-grid { display: grid; grid-template-columns: 240px 1fr; gap: 2.5rem; margin-top: -2.5rem; position: relative; z-index: 5; }

.sidebar-nav { position: sticky; top: 100px; display: flex; flex-direction: column; gap: 0.5rem; }

.nav-btn { 
  display: flex; align-items: center; padding: 1rem 1.25rem; 
  border-radius: 8px; background: #fff; color: var(--profile-muted); 
  font-size: 0.85rem; font-weight: 700; text-transform: uppercase; 
  transition: 0.2s; border: 1px solid var(--profile-border); 
  box-shadow: var(--profile-shadow); cursor: pointer;
  letter-spacing: 0.05em; text-decoration: none;
}
.nav-icon { margin-right: 12px; font-size: 1.2rem; }
.nav-btn.active { background: var(--profile-primary); color: #fff; border-color: var(--profile-primary); }
.nav-btn:hover:not(.active) { border-color: var(--profile-primary); color: var(--profile-primary); }

/* =======================================================
   GIẢI ĐẤU CARDS
   ======================================================= */
.tournaments-stack { display: flex; flex-direction: column; gap: 1.5rem; }
.atp-tour-card { 
  display: flex; background: #fff; border: 1px solid var(--profile-border); 
  border-radius: 12px; overflow: hidden; box-shadow: var(--profile-shadow); 
  transition: transform 0.2s; 
}
.atp-tour-card:hover { transform: translateY(-3px); border-color: var(--profile-primary);}

.tour-main-info { flex: 1; padding: 2rem; }
.tour-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.tour-category { font-size: 0.7rem; font-weight: 800; color: var(--profile-primary); text-transform: uppercase; letter-spacing: 0.1em; }
.atp-status-pill { padding: 4px 12px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
.confirmed { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0;}
.pending { background: #fef9c3; color: #854d0e; border: 1px solid #fef08a;}

.atp-tour-name { font-size: 1.5rem; font-weight: 800; color: var(--profile-text); margin: 0 0 1.5rem; text-transform: uppercase; line-height: 1.2; }
.tour-meta-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
.m-label { display: block; font-size: 0.65rem; font-weight: 700; color: var(--profile-muted); text-transform: uppercase; margin-bottom: 4px; }
.m-val { font-size: 0.95rem; font-weight: 600; color: var(--profile-text); }

/* Giao diện Vé */
.atp-ticket-stub { 
  width: 220px; background: #f8fafc; border-left: 2px dashed #cbd5e1; 
  display: flex; flex-direction: column; align-items: center; justify-content: center; 
  padding: 1.5rem; text-align: center; 
}
.stub-qr-box { width: 100px; height: 100px; background: #fff; padding: 6px; border-radius: 8px; margin-bottom: 1rem; border: 1px solid var(--profile-border); }
.stub-qr-box img { width: 100%; height: 100%; }
.stub-label { font-size: 0.65rem; font-weight: 700; color: var(--profile-muted); text-transform: uppercase; margin-bottom: 6px; }
.atp-ticket-stub code { background: #0f172a; color: #fff; padding: 6px 12px; border-radius: 4px; font-weight: 700; font-size: 0.9rem; letter-spacing: 1px; margin-bottom: 0.8rem;}
.stub-hint { font-size: 0.65rem; color: var(--profile-muted); margin: 0; font-style: italic;}

/* Nút bấm & Trạng thái trống */
.btn-atp-solid {
  background: var(--profile-primary); border: none;
  color: #fff; padding: 0.8rem 2.5rem; border-radius: 4px; 
  font-weight: 700; text-transform: uppercase; font-size: 0.85rem; 
  cursor: pointer; transition: 0.2s; text-decoration: none;
  display: inline-block;
}
.btn-atp-solid:hover { background: var(--profile-primary-dark); }

.atp-empty-state-card { background: #fff; border-radius: 12px; padding: 4rem 2rem; text-align: center; border: 1px solid var(--profile-border); }
.empty-visual { font-size: 4rem; margin-bottom: 1rem; opacity: 0.6;}
.atp-empty-state-card h3 { font-size: 1.2rem; color: var(--profile-text); margin-bottom: 0.5rem; font-weight: 800;}
.atp-empty-state-card p { color: var(--profile-muted); margin-bottom: 2rem;}

/* =======================================================
   RESPONSIVE
   ======================================================= */
@media (max-width: 1024px) {
  .layout-grid { grid-template-columns: 1fr; margin-top: 1.5rem; }
  .sidebar-nav { flex-direction: row; overflow-x: auto; position: sticky; top: 60px; z-index: 50; background: var(--profile-soft-bg); padding: 1rem 0; margin: 0 -1.5rem; padding-left: 1.5rem; padding-right: 1.5rem; border-bottom: 1px solid var(--profile-border);}
  .nav-btn { width: auto; white-space: nowrap; padding: 0.8rem 1.2rem; border-radius: 8px;}
}

@media (max-width: 768px) {
  .hero-flex { flex-direction: column; text-align: center; padding: 2rem 1rem; gap: 1.5rem; }
  .avatar-frame { width: 120px; height: 120px; margin: 0 auto; }
  .hero-text-block h1 { font-size: 2rem; margin-bottom: 1rem; }
  .hero-quick-stats { width: 100%; justify-content: space-between; padding: 1rem; }
  
  .atp-tour-card { flex-direction: column; }
  .tour-main-info { padding: 1.5rem; }
  .atp-tour-name { font-size: 1.3rem; margin-bottom: 1.2rem; }
  .tour-meta-grid { grid-template-columns: 1fr; gap: 1rem; }
  .atp-ticket-stub { width: 100%; border-left: none; border-top: 2px dashed var(--profile-border); padding: 1.5rem; flex-direction: row; gap: 1.5rem; text-align: left; }
  .stub-qr-box { margin-bottom: 0; width: 80px; height: 80px; flex-shrink: 0;}
}

@media (max-width: 480px) {
  .hero-quick-stats { flex-wrap: wrap; justify-content: center; gap: 1rem; }
  .stat-item { flex: 1; min-width: 80px; }
  .stat-sep { display: none; }
  .atp-ticket-stub { flex-direction: column; text-align: center; gap: 1rem; }
  .stub-qr-box { margin: 0 auto; }
}
</style>