<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isMenuOpen = ref(false)
const isMobileMenuOpen = ref(false)

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const toggleUserMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}

const handleLogout = () => {
  authStore.logout()
  isMenuOpen.value = false
  isMobileMenuOpen.value = false
  router.push({ name: 'login' })
}

const closeMenus = () => {
  isMenuOpen.value = false
  isMobileMenuOpen.value = false
}
</script>

<template>
  <header class="site-navbar">
    <div class="container nav-shell">
      <RouterLink id="global-logo-link" to="/" class="brand-mark" @click="closeMenus">
        <img src="https://res.cloudinary.com/dfs9o3bny/image/upload/v1776309753/z7730353029258_1dbe77285e553a1aa2ae1ab543a985c8-removebg-preview_nj3utv.png" alt="Saigon Tennis" class="site-logo" />
      </RouterLink>

      <nav class="desktop-nav" aria-label="Main navigation">
        <RouterLink to="/" active-class="active">Trang chủ</RouterLink>
        <RouterLink to="/news" active-class="active">Tin tức</RouterLink>
        <RouterLink to="/players" active-class="active">Vận động viên</RouterLink>
        <RouterLink to="/tournaments" active-class="active">Giải đấu</RouterLink>
        <RouterLink to="/matches" active-class="active">Lịch thi đấu</RouterLink>
        <RouterLink to="/rankings" active-class="active">Bảng xếp hạng</RouterLink>
      </nav>

      <!-- Mobile Overlay Menu -->
      <transition name="mobile-nav">
        <div v-if="isMobileMenuOpen" class="mobile-menu-overlay">
          <button class="mobile-close-btn" @click="closeMenus">✕</button>
          <div class="mobile-links">
            <RouterLink to="/" active-class="active" @click="closeMenus">Home</RouterLink>
            <RouterLink to="/news" active-class="active" @click="closeMenus">News</RouterLink>
            <RouterLink to="/players" active-class="active" @click="closeMenus">Players</RouterLink>
            <RouterLink to="/tournaments" active-class="active" @click="closeMenus">Tournaments</RouterLink>
            <RouterLink to="/matches" active-class="active" @click="closeMenus">Matches</RouterLink>
            <RouterLink to="/rankings" active-class="active" @click="closeMenus">Ranking</RouterLink>
          </div>
        </div>
      </transition>
      <div class="nav-actions">
        <!-- Hamburger Menu Button (Mobile Only) -->
        <button :class="['mobile-toggle', { 'is-active': isMobileMenuOpen }]" @click="toggleMobileMenu" aria-label="Toggle menu">
          <div class="hamburger-box">
            <span class="hamburger-inner"></span>
          </div>
        </button>

        <div v-if="authStore.isAuthenticated" class="user-profile-wrapper">
          <button class="nav-user-button" @click="toggleUserMenu">
            <div class="user-avatar-mini">
              <img v-if="authStore.user?.avatar_url" :src="authStore.user.avatar_url" alt="Avatar" />
              <span v-else>👤</span>
            </div>
            <span class="user-name-text">{{ authStore.user?.full_name || 'User' }}</span>
            <span class="dropdown-arrow">▾</span>
          </button>
          
          <div v-if="isMenuOpen" class="user-dropdown-menu">
            <div class="dropdown-header">
              <p class="user-email">{{ authStore.user?.email }}</p>
            </div>
            <hr />
            <RouterLink v-if="authStore.isAdmin" to="/admin" class="dropdown-item" @click="closeMenus">Admin Console</RouterLink>
            <RouterLink to="/profile" class="dropdown-item" @click="closeMenus">Trang cá nhân</RouterLink>
            <RouterLink to="/profile/my-tournaments" class="dropdown-item" @click="closeMenus">Giải đấu của mình</RouterLink>
            <hr />
            <button class="dropdown-item logout-action" @click="handleLogout">Đăng xuất</button>
          </div>
        </div>

        <RouterLink v-else id="open-login-nav" to="/login" class="nav-cta">Đăng nhập</RouterLink>
      </div>
    </div>
  </header>
</template>

<style scoped>
.site-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: rgba(248, 250, 252, 0.92); /* Modern Tech Slate nhạt */
  backdrop-filter: blur(15px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border-bottom: 1px solid rgba(148, 163, 184, 0.15);
}

.nav-shell {
  min-height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.brand-mark { display: inline-flex; align-items: center; }
.site-logo { 
  height: 60px; 
  width: auto; 
  filter: brightness(0) saturate(100%) invert(32%) sepia(95%) saturate(415%) hue-rotate(94deg) brightness(92%) contrast(92%); /* Giữ màu xanh cho logo trên nền sáng */
  object-fit: contain; 
  transition: transform 0.3s ease; 
}
.site-logo:hover { transform: scale(1.05); }

.desktop-nav { display: flex; align-items: center; justify-content: center; gap: 2rem; flex-wrap: wrap; }
.desktop-nav a {
  position: relative;
  padding: 1.25rem 0;
  color: #475569; /* Slate 600 */
  font-size: 0.85rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  text-decoration: none;
}

.desktop-nav a::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 3px;
  transform: scaleX(0);
  transform-origin: left;
  background: #15803d;
  transition: transform 0.2s ease-out;
}

.desktop-nav a:hover, .desktop-nav a.active { color: #15803d; }
.desktop-nav a:hover::after, .desktop-nav a.active::after { transform: scaleX(1); }

.nav-actions { display: flex; align-items: center; gap: 0.75rem; }
.mobile-toggle { display: none; }

.nav-cta {
  min-height: 40px;
  padding: 0 1.25rem;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #15803d;
  color: #ffffff;
  font-weight: 500;
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 0.05em;
  text-decoration: none;
  transition: all 0.2s ease;
}
.nav-cta:hover { background: #166534; transform: translateY(-1px); }

/* User Profile & Dropdown */
.user-profile-wrapper { position: relative; }
.nav-user-button {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}
.nav-user-button:hover { background: rgba(255, 255, 255, 0.1); }
.user-avatar-mini {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-avatar-mini img { width: 100%; height: 100%; object-fit: cover; }
.user-name-text { font-weight: 500; color: #1e293b; font-size: 0.9rem; } /* Chuyển sang màu tối slate-800 */
.dropdown-arrow { color: #64748b; font-size: 0.8rem; }

.user-dropdown-menu {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 240px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(0, 0, 0, 0.05);
  padding: 0.75rem;
  z-index: 1001;
  animation: dropdownFade 0.3s ease;
}
@keyframes dropdownFade {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
.dropdown-header { padding: 0.75rem 1rem; }
.user-email { font-size: 0.85rem; color: #6e7a74; word-break: break-all; }
hr { margin: 0.5rem 0; border: none; border-top: 1px solid rgba(0, 0, 0, 0.05); }
.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  text-decoration: none;
  color: #4e6073;
  font-size: 0.94rem;
  font-weight: 500;
  text-align: left;
  background: transparent;
  border: none;
  cursor: pointer;
}
.dropdown-item:hover { background: rgba(21, 128, 61, 0.05); color: #15803d; }
.logout-action { color: #dc2626; }

/* Responsive Styles */
/* Mobile Overlay Styles */
.mobile-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh;
  background: #0d1930;
  z-index: 5000;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 2rem;
}

.mobile-close-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  background: transparent;
  border: none;
  color: white;
  font-size: 2rem;
  cursor: pointer;
}

.mobile-links {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  width: 100%;
  text-align: center;
}

.mobile-links a {
  font-size: 1.8rem;
  font-weight: 500;
  color: white;
  text-decoration: none;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  transition: color 0.2s;
}

.mobile-links a.active {
  color: #c1ff72;
}

/* Transitions */
.mobile-nav-enter-active, .mobile-nav-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.mobile-nav-enter-from, .mobile-nav-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}


@media (max-width: 1080px) {
  .nav-shell { padding: 0.5rem 1.5rem; }
  .desktop-nav { display: none; }
  .mobile-toggle { display: flex; align-items: center; justify-content: center; background: transparent; border: none; width: 44px; height: 44px; cursor: pointer; order: 4; z-index: 3000; }
}

@media (max-width: 768px) {
  .nav-user-button .user-name-text { display: none; }
  .mobile-toggle { display: flex; align-items: center; justify-content: center; background: transparent; border: none; width: 44px; height: 44px; cursor: pointer; order: 4; z-index: 3000; }
  .hamburger-box { width: 28px; height: 18px; position: relative; }
  .hamburger-inner, .hamburger-inner::before, .hamburger-inner::after { width: 28px; height: 2px; background-color: #475569; border-radius: 4px; position: absolute; transition: all 0.3s ease; }
  .hamburger-inner { top: 50%; transform: translateY(-50%); }
  .hamburger-inner::before { content: ''; top: -8px; }
  .hamburger-inner::after { content: ''; bottom: -8px; }
  .mobile-toggle.is-active .hamburger-inner { background-color: transparent; }
  .mobile-toggle.is-active .hamburger-inner::before { top: 0; transform: rotate(45deg); }
  .mobile-toggle.is-active .hamburger-inner::after { top: 0; transform: rotate(-45deg); }
  .user-avatar-mini { border: 1px solid #e2e8f0; }
  .dropdown-arrow { color: #475569; }
}

@media (max-width: 640px) {
  .site-logo { height: 42px; }
  .nav-shell { min-height: 56px; padding: 0.5rem 1rem; }
  .nav-cta { min-height: 38px; padding: 0 1rem; font-size: 0.75rem; }
}

@media (max-width: 480px) {
  .site-logo { height: 36px; }
  .nav-shell { min-height: 50px; }
}


</style>
