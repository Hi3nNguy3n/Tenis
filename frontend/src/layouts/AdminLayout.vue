<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import {
  Calendar,
  Compass,
  Connection,
  DataAnalysis,
  DataBoard,
  Histogram,
  Location,
  Memo,
  Tickets,
  Trophy,
  User,
  UserFilled,
  UserFilled as UsersIcon,
  ArrowRight,
  Monitor,
  Message,
  Setting,
  Files
} from '@element-plus/icons-vue'
import { adminModules } from '../constants/adminNavigation'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const iconMap = {
  'Bảng điều khiển': DataBoard,
  'Hồ sơ Admin': User,
  'Vận động viên': UsersIcon,
  'Giải đấu': Trophy,
  'Danh sách Đăng ký': Tickets,
  'Bốc thăm & Nhánh': Compass,
  'Quản lý Sân': Location,
  'Trận đấu': Histogram,
  'Lịch trình': Calendar,
  'BXH & Điểm số': DataAnalysis,
  'Điểm danh QR': Monitor,
  'Thanh toán': Tickets,
  'Nhật ký hệ thống': Setting,
  'Lịch thi đấu ngày': Memo,
  'Lịch tổng quan': Calendar,
  'Tin tức': Files,
  'Gửi mail hàng loạt': Message,
}

const activeGroups = ref(['Tổng quan', 'Giải đấu'])

const toggleGroup = (label) => {
  const index = activeGroups.value.indexOf(label)
  if (index > -1) {
    activeGroups.value.splice(index, 1)
  } else {
    activeGroups.value.push(label)
  }
}

const isGroupActive = (label) => activeGroups.value.includes(label)

const groupedNavigation = computed(() => {
  const groups = new Map()

  adminModules.forEach((item) => {
    if (!groups.has(item.section)) {
      groups.set(item.section, [])
    }

    groups.get(item.section).push({
      ...item,
      to: item.path ? `/admin/${item.path}` : '/admin',
      icon: iconMap[item.label] || Memo,
    })
  })

  return Array.from(groups.entries()).map(([label, items]) => ({
    label,
    items,
  }))
})

const pageTitle = computed(() => route.meta.adminTitle || 'Tổng quan Quản trị')
const pageDescription = computed(
  () =>
    route.meta.adminDescription ||
    'Hệ thống quản lý giải đấu Saigon Tennis - Admin Dashboard.',
)
const currentUserName = computed(() => authStore.user?.full_name || authStore.user?.email || 'Quản trị viên')

onMounted(() => {
  document.body.classList.add('admin-body')
})

onUnmounted(() => {
  document.body.classList.remove('admin-body')
})

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="admin-layout">
    <div class="bg-orb orb-1"></div>
    <div class="bg-orb orb-2"></div>
    <div class="bg-orb orb-3"></div>

    <aside class="admin-sidebar">
      <div class="sidebar-glow"></div>

      <div class="brand-block">
        <RouterLink to="/admin" class="brand-link">
          <span class="brand-mark"></span>
          <span>Saigon Tennis</span>
        </RouterLink>
        <p>Trung tâm Điều hành</p>
      </div>

      <div class="nav-groups">
        <section v-for="group in groupedNavigation" :key="group.label" class="nav-group">
          <div
            class="group-header"
            :class="{ 'is-expanded': isGroupActive(group.label) }"
            @click="toggleGroup(group.label)"
          >
            <p class="group-label">{{ group.label }}</p>
            <el-icon class="arrow-icon"><ArrowRight /></el-icon>
          </div>

          <transition name="collapse">
            <div v-show="isGroupActive(group.label)" class="group-body">
              <nav class="admin-nav">
                <RouterLink
                  v-for="item in group.items"
                  :key="item.to"
                  :to="item.to"
                  class="nav-item"
                  active-class="nav-item-active"
                >
                  <div class="nav-leading">
                    <span class="nav-icon-shell">
                      <el-icon><component :is="item.icon" /></el-icon>
                    </span>
                    <span class="nav-label">{{ item.label }}</span>
                  </div>
                  <span class="nav-badge" v-if="item.badge">{{ item.badge }}</span>
                </RouterLink>
              </nav>
            </div>
          </transition>
        </section>
      </div>

      <div class="sidebar-footer">
        <div class="admin-user-chip">
          <span class="user-label">Đang đăng nhập</span>
          <strong>{{ currentUserName }}</strong>
        </div>
        <el-button class="logout-button" text @click="handleLogout">Đăng xuất</el-button>
      </div>
    </aside>

    <section class="admin-shell">
      <header class="admin-topbar">
        <div class="topbar-panel">
          <div class="topbar-copy">
            <p class="page-kicker">Không gian Quản trị</p>
            <h1>{{ pageTitle }}</h1>
            <p>{{ pageDescription }}</p>
          </div>

          <div class="topbar-status">
            <span class="status-dot"></span>
            <span>Hệ thống đang hoạt động</span>
          </div>
        </div>
      </header>

      <main class="admin-main">
        <div class="admin-content-panel">
          <RouterView />
        </div>
      </main>
    </section>
  </div>
</template>

<style scoped>
:global(body.admin-body) {
  margin: 0;
  background: #f3f7f4 !important;
  color: #0f172a;
}

.admin-layout {
  position: relative;
  min-height: 100vh;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  overflow: hidden;
  background:
    radial-gradient(circle at 14% 18%, rgba(34, 197, 94, 0.12), transparent 24%),
    radial-gradient(circle at 85% 10%, rgba(20, 98, 80, 0.1), transparent 26%),
    radial-gradient(circle at 62% 80%, rgba(34, 197, 94, 0.08), transparent 28%),
    linear-gradient(135deg, #083a31 0%, #0f5c4d 35%, #146250 60%, #0f5c4d 82%, #083a31 100%);
  color: #e2e8f0;
}

.bg-orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(90px);
  pointer-events: none;
  z-index: 0;
}

.orb-1 {
  top: -80px;
  right: 12%;
  width: 260px;
  height: 260px;
  background: rgba(34, 197, 94, 0.18);
}

.orb-2 {
  bottom: 8%;
  left: 18%;
  width: 300px;
  height: 300px;
  background: rgba(20, 98, 80, 0.18);
}

.orb-3 {
  top: 34%;
  right: -50px;
  width: 220px;
  height: 220px;
  background: rgba(220, 252, 231, 0.12);
}

.admin-sidebar {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 22px 14px 18px;
  background: linear-gradient(180deg, #083a31 0%, #0f5c4d 55%, #146250 100%);
  border-right: 1px solid rgba(220, 252, 231, 0.12);
  box-shadow: 20px 0 60px rgba(6, 78, 59, 0.28);
}

.sidebar-glow {
  position: absolute;
  inset: 0 auto 0 0;
  width: 100%;
  background:
    radial-gradient(circle at top left, rgba(220, 252, 231, 0.14), transparent 26%),
    radial-gradient(circle at bottom left, rgba(20, 98, 80, 0.18), transparent 28%);
  pointer-events: none;
}

.brand-block {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 8px;
  padding: 10px 12px 14px;
  margin-bottom: 6px;
}

.brand-link {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: 1.34rem;
  font-weight: 700;
  letter-spacing: -0.04em;
  text-decoration: none;
  color: #0f172a;
}

.brand-mark {
  width: 14px;
  height: 14px;
  border-radius: 5px;
  background: linear-gradient(135deg, #d9f43b 0%, #146250 100%);
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.32);
}

.brand-block p {
  margin: 0;
  color: #475569;
  font-size: 0.82rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.nav-groups {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 10px;
  overflow-y: auto;
  padding-right: 4px;
}

.nav-group {
  border-radius: 18px;
  padding: 4px;
  background: rgba(220, 252, 231, 0.95);
  border: 1px solid rgba(220, 252, 231, 0.1);
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px;
  cursor: pointer;
  border-radius: 14px;
  transition: background 0.25s ease, transform 0.25s ease;
}

.group-header:hover {
  background: rgba(255, 255, 255, 0.12);
}

.group-label {
  margin: 0;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #0f172a;
}

.arrow-icon {
  font-size: 12px;
  color: #64748b;
  transition: transform 0.28s ease, color 0.28s ease;
}

.is-expanded .arrow-icon {
  transform: rotate(90deg);
  color: #0f172a;
}

.is-expanded .group-label {
  color: #0f172a;
}

.group-body {
  padding-top: 2px;
}

.admin-nav {
  display: grid;
  gap: 6px;
  padding: 2px 8px 8px 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 44px;
  padding: 0 10px 0 8px;
  border-radius: 14px;
  color: #0f172a;
  transition: all 0.24s ease;
  text-decoration: none;
  font-size: 0.92rem;
  border: 1px solid transparent;
}

.nav-item:hover {
  color: #0f172a;
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(220, 252, 231, 0.24);
  transform: translateX(4px);
}

.nav-leading {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.nav-icon-shell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.88);
  color: #0f172a;
  flex-shrink: 0;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-item-active {
  background: linear-gradient(135deg, rgba(220, 252, 231, 0.98), rgba(255, 255, 255, 0.96));
  border-color: rgba(34, 197, 94, 0.28);
  color: #0f5c4d !important;
  font-weight: 700;
  box-shadow: 
    0 8px 20px rgba(0, 0, 0, 0.2),
    inset 0 0 15px rgba(217, 244, 59, 0.1);
}

.nav-item-active .nav-icon-shell {
  background: #d9f43b;
  color: #0f5c4d;
}

.nav-badge {
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(220, 252, 231, 0.2);
  border: 1px solid rgba(220, 252, 231, 0.35);
  color: #0f172a;
  font-size: 0.63rem;
  font-weight: 700;
  text-transform: uppercase;
  flex-shrink: 0;
}

.nav-item-active .nav-badge {
  background: #ffffff;
  color: #0f5c4d;
  border-color: #0f172a;
}

.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.28s ease;
  max-height: 800px;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-4px);
}

.sidebar-footer {
  position: relative;
  z-index: 1;
  margin-top: auto;
  display: grid;
  gap: 10px;
  width: 100%;
  box-sizing: border-box;
  padding: 12px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(220, 252, 231, 0.12);
  backdrop-filter: blur(14px);
}

.admin-user-chip {
  display: grid;
  gap: 4px;
}

.admin-user-chip strong {
  color: #0f172a;
  font-size: 0.92rem;
  line-height: 1.35;
}

.user-label {
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #0f172a;
}

.logout-button {
  justify-self: start;
  color: #0f172a;
  padding: 0;
  font-weight: 700;
  font-size: 0.9rem;
}

.logout-button:hover {
  text-decoration: underline;
}

.admin-shell {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.admin-topbar {
  padding: 24px 28px 12px;
}

.topbar-panel {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 22px 24px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(240, 253, 244, 0.95));
  border: 1px solid rgba(16, 185, 129, 0.14);
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(20px);
}

.topbar-copy {
  min-width: 0;
}

.page-kicker {
  margin: 0 0 10px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #0f172a;
}

.admin-topbar h1 {
  margin: 0 0 8px;
  font-size: clamp(2rem, 3.6vw, 2.8rem);
  line-height: 1.02;
  letter-spacing: -0.05em;
  color: #0f172a;
}

.admin-topbar p {
  margin: 0;
  max-width: 780px;
  color: #475569;
  line-height: 1.6;
}

.topbar-status {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(220, 252, 231, 0.95);
  border: 1px solid rgba(220, 252, 231, 0.35);
  color: #0f172a;
  font-size: 0.88rem;
  white-space: nowrap;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #d9f43b;
  box-shadow: 0 0 16px #d9f43b;
}

.admin-main {
  padding: 8px 28px 28px;
}

.admin-content-panel {
  min-height: calc(100vh - 160px);
  border-radius: 28px;
}

.nav-groups::-webkit-scrollbar {
  width: 5px;
}

.nav-groups::-webkit-scrollbar-thumb {
  background: rgba(217, 244, 59, 0.2);
  border-radius: 999px;
}

.nav-groups::-webkit-scrollbar-track {
  background: transparent;
}

@media (max-width: 1200px) {
  .admin-layout {
    grid-template-columns: 248px minmax(0, 1fr);
  }

  .admin-topbar,
  .admin-main {
    padding-left: 20px;
    padding-right: 20px;
  }
}

@media (max-width: 960px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }

  .admin-sidebar {
    min-height: auto;
    border-right: none;
    border-bottom: 1px solid rgba(173, 216, 255, 0.15);
  }

  .topbar-panel {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .admin-sidebar {
    padding: 18px 10px 14px;
  }

  .admin-topbar,
  .admin-main {
    padding-left: 14px;
    padding-right: 14px;
  }

  
  .admin-topbar h1 {
    font-size: 1.8rem;
  }
}
</style>
