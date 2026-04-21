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
        <RouterLink to="/players" active-class="active">Kênh trò chuyện</RouterLink>
        <RouterLink to="/challenges" active-class="active">Vận động viên</RouterLink>
        <RouterLink to="/tournaments" active-class="active">Giải đấu</RouterLink>
        <RouterLink to="/matches" active-class="active">Lịch thi đấu</RouterLink>
        <RouterLink to="/rankings" active-class="active">Bảng xếp hạng</RouterLink>
      </nav>

      <!-- Mobile Sidebar Menu -->
      <div v-if="isMobileMenuOpen" class="mobile-menu-backdrop" @click="closeMenus"></div>
      
      <transition name="slide-right">
        <div v-if="isMobileMenuOpen" class="mobile-sidebar">
          <div class="sidebar-header">
            <button class="sidebar-close-btn" @click="closeMenus">✕</button>
            <img src="https://res.cloudinary.com/dfs9o3bny/image/upload/v1776309753/z7730353029258_1dbe77285e553a1aa2ae1ab543a985c8-removebg-preview_nj3utv.png" alt="Logo" class="sidebar-logo" />
          </div>
          
          <nav class="sidebar-links">
            <RouterLink to="/" active-class="active" @click="closeMenus">Trang chủ</RouterLink>
            <RouterLink to="/news" active-class="active" @click="closeMenus">Tin tức</RouterLink>
            <RouterLink to="/players" active-class="active" @click="closeMenus">Kênh trò chuyện</RouterLink>
            <RouterLink to="/challenges" active-class="active" @click="closeMenus">Vận động viên</RouterLink>
            <RouterLink to="/tournaments" active-class="active" @click="closeMenus">Giải đấu</RouterLink>
            <RouterLink to="/matches" active-class="active" @click="closeMenus">Lịch thi đấu</RouterLink>
            <RouterLink to="/rankings" active-class="active" @click="closeMenus">Bảng xếp hạng</RouterLink>
          </nav>

          <div class="sidebar-footer" v-if="!authStore.isAuthenticated">
             <RouterLink to="/login" class="sidebar-login-btn" @click="closeMenus">Đăng nhập</RouterLink>
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
  object-fit: contain; 
  transition: transform 0.3s ease; 
}
.site-logo:hover { transform: scale(1.05); }

.desktop-nav { 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  gap: 1.2rem; 
  flex-wrap: nowrap; 
}
.desktop-nav a {
  position: relative;
  padding: 1.25rem 0;
  color: #475569;
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.02em;
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
.user-name-text { font-weight: 500; color: #1e293b; font-size: 0.9rem; }
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

/* Sidebar Mobile Styles */
.mobile-menu-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  z-index: 4999;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.mobile-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 280px;
  max-width: 85vw;
  height: 100vh;
  background: white;
  z-index: 5000;
  display: flex;
  flex-direction: column;
  box-shadow: -10px 0 30px rgba(0,0,0,0.1);
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-logo { height: 40px; width: auto; object-fit: contain; }
.sidebar-close-btn { background: none; border: none; font-size: 1.5rem; color: #64748b; cursor: pointer; }

.sidebar-links {
  flex: 1;
  padding: 2rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.sidebar-links a {
  font-size: 0.95rem;
  font-weight: 600;
  color: #334155;
  text-decoration: none;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: all 0.2s;
  display: flex;
  align-items: center;
}

.sidebar-links a.active { color: #15803d; }
.sidebar-links a:hover { padding-left: 5px; color: #15803d; }

.sidebar-footer { padding: 1.5rem; border-top: 1px solid #f1f5f9; }
.sidebar-login-btn {
  display: block;
  width: 100%;
  padding: 0.8rem;
  background: #15803d;
  color: white;
  text-align: center;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.85rem;
}

/* Transitions */
.slide-right-enter-active, .slide-right-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-right-enter-from, .slide-right-leave-to {
  transform: translateX(100%);
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
