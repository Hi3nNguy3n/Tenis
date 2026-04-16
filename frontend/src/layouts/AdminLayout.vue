<script setup>
import { ref, computed } from 'vue'
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
  Setting,
  Files
} from '@element-plus/icons-vue'
import { adminModules } from '../constants/adminNavigation'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// Icon mapping cho các item con
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
  'Tin tức': Files
}

// Logic quản lý các nhóm đang mở (Mặc định mở nhóm đầu tiên)
const activeGroups = ref(['Tổng quan', 'Giải đấu'])

const toggleGroup = (label) => {
  const index = activeGroups.value.indexOf(label)
  if (index > -1) {
    activeGroups.value.splice(index, 1) // Đóng
  } else {
    activeGroups.value.push(label) // Mở
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

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="brand-block">
        <RouterLink to="/admin" class="brand-link">Saigon Tennis</RouterLink>
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
            <div v-show="isGroupActive(group.label)">
              <nav class="admin-nav">
                <RouterLink
                  v-for="item in group.items"
                  :key="item.to"
                  :to="item.to"
                  class="nav-item"
                  active-class="nav-item-active"
                >
                  <div class="nav-leading">
                    <el-icon><component :is="item.icon" /></el-icon>
                    <span>{{ item.label }}</span>
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
        <div>
          <p class="page-kicker">Không gian Quản trị</p>
          <h1>{{ pageTitle }}</h1>
          <p>{{ pageDescription }}</p>
        </div>
      </header>

      <main class="admin-main">
        <RouterView />
      </main>
    </section>
  </div>
</template>

<style scoped>
/* GIỮ NGUYÊN LAYOUT CHUNG */
.admin-layout {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  background:
    radial-gradient(circle at top left, rgba(27, 153, 139, 0.12), transparent 24%),
    linear-gradient(180deg, #f5f7f7 0%, #eef2f1 100%);
  color: #182320;
}

.admin-sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 28px 16px;
  background: linear-gradient(180deg, #14332e 0%, #0f2622 100%);
  color: #f7fbf9;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.brand-block {
  display: grid;
  gap: 8px;
  padding: 8px 10px;
  margin-bottom: 10px;
}

.brand-link {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.04em;
  text-decoration: none;
  color: white;
}

/* CUSTOM MENU XỔ XUỐNG */
.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  cursor: pointer;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.group-header:hover {
  background: rgba(255, 255, 255, 0.05);
}

.group-label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(247, 251, 249, 0.46);
  margin: 0;
}

.arrow-icon {
  font-size: 12px;
  color: rgba(247, 251, 249, 0.3);
  transition: transform 0.3s ease;
}

.is-expanded .arrow-icon {
  transform: rotate(90deg);
  color: #d7f171;
}

.is-expanded .group-label {
  color: rgba(247, 251, 249, 0.8);
}

.admin-nav {
  display: grid;
  gap: 4px;
  padding-left: 10px; /* Thụt lề menu con */
  margin-top: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 44px;
  padding: 0 14px;
  border-radius: 14px;
  color: rgba(247, 251, 249, 0.6);
  transition: 0.2s ease;
  text-decoration: none;
  font-size: 0.95rem;
}

.nav-item:hover {
  background: rgba(247, 251, 249, 0.08);
  color: #ffffff;
}

.nav-item-active {
  background: linear-gradient(135deg, #d7f171 0%, #b9d84d 100%);
  color: #13211d !important;
  font-weight: 700;
}

/* Badge style */
.nav-badge {
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
}

.nav-item-active .nav-badge {
  background: rgba(19, 33, 29, 0.15);
}

/* Animation collapse */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease-in-out;
  max-height: 800px;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
}

/* CÁC PHẦN CÒN LẠI GIỮ NGUYÊN */
.nav-groups {
  display: grid;
  gap: 10px;
  overflow-y: auto;
  padding-right: 4px;
}

.sidebar-footer {
  margin-top: auto;
  display: grid;
  gap: 14px;
  padding: 18px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.05);
}

.admin-user-chip {
  display: grid;
  gap: 4px;
}

.user-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: rgba(247, 251, 249, 0.62);
}

.logout-button {
  justify-self: start;
  color: #d7f171;
  padding: 0;
}

.admin-shell {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.admin-topbar {
  padding: 28px 32px 12px;
}

.page-kicker {
  margin-bottom: 8px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #3f7f74;
}

.admin-topbar h1 {
  margin-bottom: 10px;
  font-size: clamp(2rem, 4vw, 2.8rem);
  line-height: 1.05;
  letter-spacing: -0.04em;
}

.admin-topbar p {
  max-width: 720px;
  color: #5e716b;
}

.admin-main {
  padding: 20px 32px 32px;
}

/* Scrollbar cho Sidebar */
.nav-groups::-webkit-scrollbar {
  width: 4px;
}
.nav-groups::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.1);
  border-radius: 10px;
}
</style>