<script setup>
import { computed, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isMenuOpen = ref(false)

const isAuthLayout = computed(() => Boolean(route.meta.authLayout))
const isAdminLayout = computed(() => Boolean(route.meta.adminLayout))
const shouldShowPublicChrome = computed(() => !isAuthLayout.value && !isAdminLayout.value)

const toggleUserMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}

const handleLogout = () => {
  authStore.logout()
  isMenuOpen.value = false
  router.push({ name: 'login' })
}
</script>

<template>
  <header v-if="shouldShowPublicChrome" class="site-navbar">
    <div class="container nav-shell">
      <RouterLink id="global-logo-link" to="/" class="brand-mark">Saigon Tennis</RouterLink>

      <nav class="desktop-nav" aria-label="Main navigation">
        <RouterLink to="/" active-class="active">Home</RouterLink>
        <RouterLink to="/players" active-class="active">Players</RouterLink>
        <RouterLink to="/tournaments" active-class="active">Tournaments</RouterLink>
        <RouterLink to="/matches" active-class="active">Matches</RouterLink>
        <RouterLink to="/rankings" active-class="active">Ranking</RouterLink>
        <RouterLink v-if="!authStore.isAuthenticated" to="/register-otp" active-class="active">Register OTP</RouterLink>
        <RouterLink v-if="!authStore.isAuthenticated" to="/login" active-class="active">Login</RouterLink>
      </nav>

      <div class="nav-actions">
        <button id="global-notify-button" class="icon-button" type="button" aria-label="Notifications">
          <span>◌</span>
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
            <RouterLink v-if="authStore.isAdmin" to="/admin" class="dropdown-item" @click="isMenuOpen = false">🛠 Admin Console</RouterLink>
            <RouterLink to="/profile" class="dropdown-item" @click="isMenuOpen = false">👤 Trang cá nhân</RouterLink>
            <RouterLink to="/profile/my-tournaments" class="dropdown-item" @click="isMenuOpen = false">🎾 Giải đấu của mình</RouterLink>
            <hr />
            <button class="dropdown-item logout-action" @click="handleLogout">🚪 Đăng xuất</button>

          </div>
        </div>

        <RouterLink v-else id="open-login-nav" to="/login" class="nav-cta">Đăng nhập</RouterLink>
      </div>
    </div>
  </header>

  <main
    :class="{
      'main-default': shouldShowPublicChrome,
      'main-auth': isAuthLayout,
      'main-admin': isAdminLayout,
    }"
  >
    <RouterView v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </RouterView>
  </main>

  <footer v-if="shouldShowPublicChrome" class="site-footer">
    <div class="container footer-shell">
      <div class="footer-branding">
        <h2>Saigon Tennis.</h2>
        <p>
          Không gian tennis hiện đại dành cho thi đấu, huấn luyện, kết nối cộng đồng và vận hành
          giải đấu theo tiêu chuẩn premium.
        </p>
      </div>

      <div class="footer-links-grid">
        <div>
          <h4>Club</h4>
          <ul>
            <li><RouterLink to="/">Home</RouterLink></li>
            <li><RouterLink to="/players">Players</RouterLink></li>
            <li><RouterLink to="/tournaments">Tournaments</RouterLink></li>
          </ul>
        </div>
        <div>
          <h4>Experience</h4>
          <ul>
            <li><RouterLink to="/matches">Live Matches</RouterLink></li>
            <li><RouterLink to="/register-otp">Register OTP</RouterLink></li>
            <li><RouterLink to="/login">Login</RouterLink></li>
          </ul>
        </div>
        <div>
          <h4>Follow</h4>
          <div class="social-links">
            <span>Share</span>
            <span>Global</span>
            <span>Contact</span>
          </div>
        </div>
      </div>
    </div>

    <div class="container footer-bottom-bar">
      © 2026 Saigon Tennis Club. All rights reserved. Professionalism in every swing.
    </div>
  </footer>
</template>

<style scoped>
.site-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(18px);
  box-shadow: 0 20px 40px rgba(25, 28, 28, 0.06);
  border-bottom: 1px solid rgba(189, 201, 195, 0.2);
}

.nav-shell {
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.brand-mark {
  font-size: 1.95rem;
  font-weight: 800;
  letter-spacing: -0.06em;
  color: #123f34;
  white-space: nowrap;
}

.desktop-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.75rem;
  flex-wrap: wrap;
}

.desktop-nav a {
  position: relative;
  padding: 0.25rem 0;
  color: #5d6b66;
  font-size: 0.94rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.desktop-nav a::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -0.45rem;
  width: 100%;
  height: 2px;
  transform: scaleX(0);
  transform-origin: left;
  background: #006953;
  transition: transform 0.25s ease;
}

.desktop-nav a:hover,
.desktop-nav a.active {
  color: #123f34;
}

.desktop-nav a:hover::after,
.desktop-nav a.active::after {
  transform: scaleX(1);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.icon-button {
  width: 42px;
  height: 42px;
  border: none;
  border-radius: 999px;
  background: rgba(0, 105, 83, 0.08);
  color: #006953;
  font: inherit;
  font-size: 1rem;
  cursor: pointer;
  transition: transform 0.25s ease, background 0.25s ease;
}

.icon-button:hover {
  transform: scale(1.05);
  background: rgba(0, 105, 83, 0.12);
}

.nav-cta {
  min-height: 46px;
  padding: 0 1.4rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #006953 0%, #13846a 100%);
  color: #ffffff;
  font-weight: 700;
  box-shadow: 0 16px 28px rgba(0, 105, 83, 0.18);
}

.main-default {
  padding-top: 80px;
  min-height: calc(100vh - 220px);
}

.main-auth,
.main-admin {
  min-height: 100vh;
}

.site-footer {
  padding: 5rem 0 2rem;
  background: #ffffff;
  border-top: 1px solid rgba(189, 201, 195, 0.28);
}

.footer-shell {
  display: flex;
  justify-content: space-between;
  gap: 3rem;
}

.footer-branding {
  max-width: 420px;
}

.footer-branding h2 {
  margin-bottom: 1rem;
  font-size: 3rem;
  line-height: 1;
  letter-spacing: -0.05em;
  color: #123f34;
}

.footer-branding p {
  color: #4e6073;
  line-height: 1.8;
}

.footer-links-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(120px, 1fr));
  gap: 2.5rem;
}

.footer-links-grid h4 {
  margin-bottom: 1rem;
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #006953;
}

.footer-links-grid ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.9rem;
}

.footer-links-grid li,
.social-links span {
  color: #4e6073;
}

.social-links {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.footer-bottom-bar {
  margin-top: 4rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(189, 201, 195, 0.3);
  color: rgba(78, 96, 115, 0.8);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.page-enter-active,
.page-leave-active {
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 1080px) {
  .nav-shell {
    flex-wrap: wrap;
    padding-top: 0.75rem;
    padding-bottom: 0.75rem;
  }

  .desktop-nav {
    order: 3;
    width: 100%;
    justify-content: flex-start;
  }

  .main-default {
    padding-top: 132px;
  }

  .footer-shell {
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  .desktop-nav {
    gap: 1rem;
  }

  .nav-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .footer-links-grid {
    grid-template-columns: 1fr;
  }
}
/* User Profile & Dropdown Styles */
.user-profile-wrapper {
  position: relative;
}

.nav-user-button {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  border: 1px solid rgba(0, 105, 83, 0.1);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: all 0.25s ease;
}

.nav-user-button:hover {
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 105, 83, 0.2);
}

.user-avatar-mini {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  background: #f0f7f4;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #ddd;
}

.user-avatar-mini img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-avatar {
  font-size: 1.2rem;
}

.user-name-text {
  font-weight: 700;
  color: #123f34;
  font-size: 0.94rem;
}

.dropdown-arrow {
  color: #006953;
  font-size: 0.8rem;
  opacity: 0.6;
}

.user-dropdown-menu {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 240px;
  background: white;
  border-radius: 18px;
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

.dropdown-header {
  padding: 0.75rem 1rem;
}

.user-email {
  font-size: 0.85rem;
  color: #6e7a74;
  word-break: break-all;
}

hr {
  margin: 0.5rem 0;
  border: none;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  text-decoration: none;
  color: #4e6073;
  font-size: 0.94rem;
  font-weight: 600;
  text-align: left;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dropdown-item:hover {
  background: rgba(0, 105, 83, 0.05);
  color: #006953;
}

.logout-action {
  color: #ba1a1a;
}

.logout-action:hover {
  background: rgba(186, 26, 26, 0.05);
  color: #ba1a1a;
}
</style>
