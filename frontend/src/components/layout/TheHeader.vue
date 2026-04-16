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

      <nav :class="['desktop-nav', { 'mobile-open': isMobileMenuOpen }]" aria-label="Main navigation">
        <RouterLink to="/" active-class="active" @click="closeMenus">Home</RouterLink>
        <RouterLink to="/players" active-class="active" @click="closeMenus">Players</RouterLink>
        <RouterLink to="/tournaments" active-class="active" @click="closeMenus">Tournaments</RouterLink>
        <RouterLink to="/matches" active-class="active" @click="closeMenus">Matches</RouterLink>
        <RouterLink to="/rankings" active-class="active" @click="closeMenus">Ranking</RouterLink>
        <RouterLink v-if="!authStore.isAuthenticated" to="/register-otp" active-class="active" @click="closeMenus">Register OTP</RouterLink>
        <RouterLink v-if="!authStore.isAuthenticated" to="/login" active-class="active" @click="closeMenus">Login</RouterLink>
      </nav>

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
            <RouterLink v-if="authStore.isAdmin" to="/admin" class="dropdown-item" @click="closeMenus">🛠 Admin Console</RouterLink>
            <RouterLink to="/profile" class="dropdown-item" @click="closeMenus">👤 Trang cá nhân</RouterLink>
            <RouterLink to="/profile/my-tournaments" class="dropdown-item" @click="closeMenus">🎾 Giải đấu của mình</RouterLink>
            <hr />
            <button class="dropdown-item logout-action" @click="handleLogout">🚪 Đăng xuất</button>
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
  background: linear-gradient(to right, #15803d, #064e3b);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border-bottom: 2px solid #c1ff72;
}

.nav-shell {
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.brand-mark { display: inline-flex; align-items: center; }
.site-logo { height: 80px; width: auto; object-fit: contain; transition: transform 0.3s ease; }
.site-logo:hover { transform: scale(1.05); }

.desktop-nav { display: flex; align-items: center; justify-content: center; gap: 2rem; flex-wrap: wrap; }
.desktop-nav a {
  position: relative;
  padding: 1.5rem 0;
  color: #ffffff;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  opacity: 0.85;
  text-decoration: none;
}

.desktop-nav a::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 4px;
  transform: scaleX(0);
  transform-origin: left;
  background: #c1ff72;
  transition: transform 0.2s ease-out;
}

.desktop-nav a:hover, .desktop-nav a.active { color: #c1ff72; opacity: 1; }
.desktop-nav a:hover::after, .desktop-nav a.active::after { transform: scaleX(1); }

.nav-actions { display: flex; align-items: center; gap: 0.75rem; }
.mobile-toggle { display: none; }

.nav-cta {
  min-height: 44px;
  padding: 0 1.5rem;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #c1ff72;
  color: #064e3b;
  font-weight: 800;
  text-transform: uppercase;
  font-size: 0.85rem;
  letter-spacing: 0.05em;
  text-decoration: none;
  transition: all 0.2s ease;
}
.nav-cta:hover { background: #ffffff; transform: translateY(-2px); }

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
.user-name-text { font-weight: 700; color: #ffffff; font-size: 0.9rem; }
.dropdown-arrow { color: #ffffff; font-size: 0.8rem; opacity: 0.8; }

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
  font-weight: 600;
  text-align: left;
  background: transparent;
  border: none;
  cursor: pointer;
}
.dropdown-item:hover { background: rgba(21, 128, 61, 0.05); color: #15803d; }
.logout-action { color: #dc2626; }

/* Responsive Styles */
@media (max-width: 1080px) {
  .nav-shell { padding: 0.5rem 1.5rem; }
  .desktop-nav { display: none; }
  .mobile-toggle { display: flex; align-items: center; justify-content: center; background: transparent; border: none; width: 44px; height: 44px; cursor: pointer; order: 4; z-index: 3000; }
  .desktop-nav.mobile-open {
    display: flex;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(15, 23, 42, 0.98);
    backdrop-filter: blur(12px);
    flex-direction: column;
    padding: 6rem 2rem;
    gap: 2rem;
    z-index: 2000;
    animation: slideDownNav 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }
  @keyframes slideDownNav { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
  .desktop-nav.mobile-open a { font-size: 1.5rem; font-weight: 800; color: #fff; border-left: 4px solid transparent; padding-left: 1rem; text-transform: uppercase; }
  .desktop-nav.mobile-open a.active { color: #c1ff72; border-left-color: #c1ff72; }
}

@media (max-width: 768px) {
  .nav-user-button .user-name-text { display: none; }
  .mobile-toggle { display: flex; align-items: center; justify-content: center; background: transparent; border: none; width: 44px; height: 44px; cursor: pointer; order: 4; z-index: 3000; }
  .hamburger-box { width: 28px; height: 18px; position: relative; }
  .hamburger-inner, .hamburger-inner::before, .hamburger-inner::after { width: 28px; height: 2px; background-color: white; border-radius: 4px; position: absolute; transition: all 0.3s ease; }
  .hamburger-inner { top: 50%; transform: translateY(-50%); }
  .hamburger-inner::before { content: ''; top: -8px; }
  .hamburger-inner::after { content: ''; bottom: -8px; }
  .mobile-toggle.is-active .hamburger-inner { background-color: transparent; }
  .mobile-toggle.is-active .hamburger-inner::before { top: 0; transform: rotate(45deg); }
  .mobile-toggle.is-active .hamburger-inner::after { top: 0; transform: rotate(-45deg); }
}

@media (max-width: 640px) {
  .site-logo { height: 48px; }
  .nav-shell { min-height: 64px; padding: 0.5rem 1rem; }
}


</style>
