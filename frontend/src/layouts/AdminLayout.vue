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
import { currentLocale, t, toggleLocale } from '../utils/locale'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// Mapping logic for localized labels
const getLocalizedLabel = (label) => {
  const labelMap = {
    'Bảng điều khiển': t('admin.dashboard'),
    'Hồ sơ Admin': t('admin.adminProfile'),
    'Vận động viên': t('admin.players'),
    'Giải đấu': t('admin.tournaments'),
    'Danh sách Đăng ký': t('admin.registrations'),
    'Bốc thăm & Nhánh': t('admin.draws'),
    'Quản lý Sân': t('admin.courts'),
    'Trận đấu': t('admin.matches'),
    'Lịch trình': t('admin.schedule'),
    'BXH & Điểm số': t('admin.rankings'),
    'Điểm danh QR': t('admin.checkIn'),
    'Thanh toán': t('admin.payments'),
    'Nhật ký hệ thống': t('admin.logs'),
    'Lịch thi đấu ngày': t('admin.dailySchedule'),
    'Lịch tổng quan': t('admin.calendar'),
    'Tin tức': t('admin.news'),
    'Gửi mail hàng loạt': t('admin.mailCampaign'),
    'Tạo trận thủ công': t('admin.createMatch')
  }
  return labelMap[label] || label
}

const getLocalizedSection = (section) => {
  const sectionMap = {
    'Tổng quan': t('admin.overview'),
    'Vận hành': t('admin.operation'),
    'Giải đấu': t('admin.tournaments'),
    'Điều phối': t('admin.coordination'),
    'Hệ thống': t('admin.system')
  }
  return sectionMap[section] || section
}

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
  'Tạo trận thủ công': Monitor
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
    const localizedSection = getLocalizedSection(item.section)
    if (!groups.has(localizedSection)) {
      groups.set(localizedSection, {
        originalSection: item.section,
        items: []
      })
    }

    groups.get(localizedSection).items.push({
      ...item,
      localizedLabel: getLocalizedLabel(item.label),
      to: item.path ? `/admin/${item.path}` : '/admin',
      icon: iconMap[item.label] || Memo,
    })
  })

  return Array.from(groups.entries()).map(([label, data]) => ({
    label,
    originalLabel: data.originalSection,
    items: data.items,
  }))
})

const getLocalizedTitle = (title) => {
  const titleMap = {
    'Tổng quan Quản trị': t('admin.dashboard'),
    'Quản lý Vận động viên': t('admin.players'),
    'Quản lý Giải đấu': t('admin.tournaments'),
    'Danh sách Đăng ký': t('admin.registrations'),
    'Bốc thăm & Nhánh': t('admin.draws'),
    'Quản lý Sân': t('admin.courts'),
    'Điều phối Trận đấu': t('admin.matches'),
    'Lịch trình': t('admin.schedule'),
    'Bảng xếp hạng': t('admin.rankings'),
    'Điểm danh QR': t('admin.checkIn'),
    'Đối soát Thanh toán': t('admin.payments'),
    'Nhật ký hệ thống': t('admin.logs'),
    'Lịch thi đấu ngày': t('admin.dailySchedule'),
    'Lịch tổng quan': t('admin.calendar'),
    'Quản lý Tin tức': t('admin.news'),
    'Mail Campaign': t('admin.mailCampaign'),
    'Tạo trận giao hữu / 1vs1': t('admin.createMatch')
  }
  return titleMap[title] || title
}

const getLocalizedDescription = (desc) => {
  const descMap = {
    'Bảng điều khiển tổng quan cho toàn bộ hệ thống quản trị.': t('admin.dashboardDesc'),
    'Quản lý hồ sơ vận động viên, kỹ năng, khu vực và thống kê thi đấu.': t('admin.playersDesc'),
    'Danh sách giải đấu, bộ lọc, tạo mới và chỉnh sửa thông tin giải.': t('admin.tournamentsDesc'),
    'Duyệt đăng ký thi đấu, theo dõi thanh toán và trạng thái vào main draw.': t('admin.registrationsDesc'),
    'Thiết lập bracket, seed slots, bye slots và luồng nhánh thi đấu.': t('admin.drawsDesc'),
    'Quản lý danh sách sân, mặt sân, địa điểm và tình trạng khả dụng.': t('admin.courtsDesc'),
    'Điều hành trận đấu, cập nhật tỷ số, người thắng và referee assignment.': t('admin.matchesDesc'),
    'Timeline lịch thi đấu theo ngày, sân và khung giờ.': t('admin.scheduleDesc'),
    'Bảng xếp hạng và lịch sử biến động ELO theo nhiều bộ lọc.': t('admin.rankingsDesc'),
    'Quét QR của vận động viên để xác nhận tham gia thi đấu tại sân.': t('admin.checkInDesc'),
    'Đối soát các giao dịch thanh toán, kiểm tra trạng thái webhook và hoàn phí.': t('admin.paymentsDesc'),
    'Truy vết các thay đổi dữ liệu và thao tác của quản trị viên trên toàn hệ thống.': t('admin.logsDesc'),
    'Lịch trình chi tiết theo từng cụm sân và khung giờ hàng ngày.': t('admin.dailyScheduleDesc'),
    'Giao diện lịch theo tháng giúp theo dõi mật độ các trận đấu.': t('admin.calendarDesc'),
    'Viết bài, tải ảnh và đăng thông báo giải đấu.': t('admin.newsDesc'),
    'Soạn template, chọn lịch gửi, ghi log và gửi thông báo hàng loạt đến VĐV.': t('admin.mailCampaignDesc')
  }
  return descMap[desc] || desc
}

const pageTitle = computed(() => getLocalizedTitle(route.meta.adminTitle || 'Tổng quan Quản trị'))
const pageDescription = computed(() => getLocalizedDescription(route.meta.adminDescription || 'Hệ thống quản lý giải đấu Saigontennistours- Admin Dashboard.'))
const currentUserName = computed(() => authStore.user?.full_name || authStore.user?.email || t('admin.admin'))
const isSidebarOpen = ref(false)

onMounted(() => {
  document.body.classList.add('admin-body')
})

onUnmounted(() => {
  document.body.classList.remove('admin-body')
})

const handleLogout = () => {
  if (confirm(t('auth.logoutConfirm'))) {
    authStore.logout()
    router.push({ name: 'login' })
  }
}

const closeSidebar = () => {
  isSidebarOpen.value = false
}

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}
</script>

<template>
  <div class="admin-layout">
    <div class="bg-orb orb-1"></div>
    <div class="bg-orb orb-2"></div>
    <div class="bg-orb orb-3"></div>

    <div v-if="isSidebarOpen" class="sidebar-backdrop" @click="closeSidebar"></div>

    <aside class="admin-sidebar" :class="{ 'is-open': isSidebarOpen }">
      <div class="sidebar-glow"></div>

      <el-dropdown trigger="click" placement="bottom-start" class="brand-dropdown">
        <div class="brand-block">
          <div class="brand-link">
            <span class="brand-logo-wrap">
              <img
                src="https://res.cloudinary.com/dfs9o3bny/image/upload/v1776309753/z7730353029258_1dbe77285e553a1aa2ae1ab543a985c8-removebg-preview_nj3utv.png"
                alt="Saigon Tennis"
                class="brand-logo"
              />
            </span>
            <span>Saigontennistours</span>
            <el-icon style="margin-left: auto; color: rgba(225, 255, 236, 0.75);"><ArrowRight style="transform: rotate(90deg);" /></el-icon>
          </div>
          <p>{{ $t('admin.opsCenter') }}</p>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="router.push('/admin')">
              {{ $t('admin.dashboard') }}
            </el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout" style="color: #dc2626; font-weight: bold;">
              {{ $t('admin.logout') }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <div class="nav-groups">
        <section v-for="group in groupedNavigation" :key="group.label" class="nav-group">
          <div
            class="group-header"
            :class="{ 'is-expanded': isGroupActive(group.originalLabel) }"
            @click="toggleGroup(group.originalLabel)"
          >
            <p class="group-label">{{ group.label }}</p>
            <el-icon class="arrow-icon"><ArrowRight /></el-icon>
          </div>

          <transition name="collapse">
            <div v-show="isGroupActive(group.originalLabel)" class="group-body">
              <nav class="admin-nav">
                <RouterLink
                  v-for="item in group.items"
                  :key="item.to"
                  :to="item.to"
                  class="nav-item"
                  active-class="nav-item-active"
                  @click="closeSidebar"
                >
                  <div class="nav-leading">
                    <span class="nav-icon-shell">
                      <el-icon><component :is="item.icon" /></el-icon>
                    </span>
                    <span class="nav-label">{{ item.localizedLabel }}</span>
                  </div>
                  <span class="nav-badge" v-if="item.badge">{{ item.badge }}</span>
                </RouterLink>
              </nav>
            </div>
          </transition>
        </section>
      </div>
    </aside>

    <section class="admin-shell">
      <header class="admin-topbar">
        <div class="topbar-panel">
          <button class="mobile-menu-button" type="button" @click="toggleSidebar" aria-label="Mở menu">
            <span></span>
            <span></span>
            <span></span>
          </button>
          <div class="topbar-copy">
            <p class="page-kicker">{{ $t('admin.adminSpace') }}</p>
            <h1>{{ pageTitle }}</h1>
            <p>{{ pageDescription }}</p>
          </div>

          <div class="topbar-actions">
            <!-- Globe Locale Toggle -->
            <button 
              class="lang-toggle-btn-admin" 
              @click="toggleLocale" 
            >
              <span class="globe-icon">🌐</span>
              <span class="lang-text">{{ currentLocale.toUpperCase() }}</span>
            </button>

            <div class="topbar-status">
              <span class="status-dot"></span>
              <span>{{ $t('admin.systemActive') }}</span>
            </div>
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

.sidebar-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 23, 0.42);
  backdrop-filter: blur(2px);
  z-index: 20;
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

.brand-dropdown {
  width: 100%;
  display: block;
}

.brand-dropdown:focus-visible {
  outline: none;
}

.brand-block {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 8px;
  padding: 10px 12px 14px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: background 0.2s ease;
  border-radius: 8px;
}

.brand-block:hover {
  background: rgba(255, 255, 255, 0.05);
}

.brand-link {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.05em;
  text-decoration: none;
  color: #07111f;
}

.brand-logo-wrap {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(217, 244, 59, 0.18), rgba(255, 255, 255, 0.92));
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.45);
  flex-shrink: 0;
}

.brand-logo {
  width: 34px;
  height: 34px;
  object-fit: contain;
  display: block;
}

.brand-block p {
  margin: 0;
  color: rgba(225, 255, 236, 0.75);
  font-size: 0.84rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.nav-groups {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 10px;
  overflow-y: auto;
  padding-right: 4px;
  padding-bottom: 4px;
}

.nav-group {
  border-radius: 18px;
  padding: 0;
  background: transparent;
  border: 0;
  overflow: visible;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  cursor: pointer;
  border-radius: 14px;
  transition:
    background 0.28s ease,
    transform 0.28s ease,
    box-shadow 0.28s ease,
    border-color 0.28s ease;
  background: rgba(220, 252, 231, 0.95);
  border: 1px solid rgba(220, 252, 231, 0.12);
  will-change: transform;
}

.group-header:hover {
  background: rgba(220, 252, 231, 1);
  transform: translateX(2px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
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
  transition: transform 0.32s cubic-bezier(0.22, 1, 0.36, 1), color 0.28s ease;
}

.is-expanded .arrow-icon {
  transform: rotate(90deg);
  color: #0f172a;
}

.is-expanded .group-label {
  color: #0f172a;
}

.group-body {
  margin-top: 8px;
  padding: 0;
  background: transparent;
  border: 0;
}

.admin-nav {
  display: grid;
  gap: 8px;
  padding: 0;
  margin: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 44px;
  padding: 0 10px 0 8px;
  border-radius: 16px;
  color: #0f172a;
  transition:
    transform 0.24s cubic-bezier(0.22, 1, 0.36, 1),
    background 0.24s ease,
    color 0.24s ease,
    border-color 0.24s ease,
    box-shadow 0.24s ease;
  text-decoration: none;
  font-size: 0.92rem;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.92);
}

.nav-item:hover {
  color: #0f172a;
  background: rgba(255, 255, 255, 0.92);
  border-color: rgba(220, 252, 231, 0.24);

  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.06);
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
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(240, 253, 244, 0.96));
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
  background: rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(15, 23, 42, 0.08);
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
  transition:
    opacity 0.28s ease,
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    max-height 0.32s ease;
  overflow: hidden;
}

.collapse-enter-to,
.collapse-leave-from {
  max-height: 800px;
  opacity: 1;
  transform: translateY(0);
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-6px);
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
  background: rgba(255, 255, 255, 0.92);
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

.mobile-menu-button {
  display: none;
  width: 44px;
  height: 44px;
  border: 1px solid rgba(16, 185, 129, 0.16);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.94);
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex-direction: column;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
  cursor: pointer;
  flex-shrink: 0;
}

.mobile-menu-button span {
  width: 18px;
  height: 2px;
  border-radius: 99px;
  background: #0f172a;
  display: block;
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

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.lang-toggle-btn-admin {
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  border: 1px solid rgba(16, 185, 129, 0.14);
  padding: 8px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}

.lang-toggle-btn-admin:hover {
  background: #f0fdf4;
  transform: translateY(-1px);
}

.lang-toggle-btn-admin .globe-icon {
  font-size: 1.1rem;
}

.lang-toggle-btn-admin .lang-text {
  font-weight: 700;
  font-size: 0.85rem;
  color: #0f172a;
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
    grid-template-columns: 232px minmax(0, 1fr);
  }

  .admin-topbar,
  .admin-main {
    padding-left: 20px;
    padding-right: 20px;
  }

  .brand-link {
    font-size: 1.32rem;
  }

  .nav-item {
    min-height: 42px;
    font-size: 0.88rem;
  }
}

@media (max-width: 960px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }

  .admin-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 300px;
    min-height: auto;
    max-height: none;
    border-right: none;
    border-bottom: 1px solid rgba(173, 216, 255, 0.15);
    transform: translateX(-102%);
    transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1);
    z-index: 30;
  }

  .admin-sidebar.is-open {
    transform: translateX(0);
  }

  .nav-groups {
    max-height: none;
  }

  .admin-shell {
    min-width: 0;
  }

  .topbar-panel {
    flex-direction: column;
    align-items: flex-start;
  }

  .mobile-menu-button {
    display: inline-flex;
  }

  .topbar-status {
    align-self: flex-start;
  }
}

@media (max-width: 640px) {
  .admin-layout {
    grid-template-columns: 1fr;
    overflow-x: hidden;
  }

  .admin-sidebar {
    width: min(86vw, 320px);
    padding: 16px 10px 12px;
    gap: 12px;
  }

  .admin-topbar,
  .admin-main {
    padding-left: 14px;
    padding-right: 14px;
  }

  .brand-block {
    padding: 8px 8px 10px;
  }

  .brand-link {
    font-size: 1.18rem;
    gap: 10px;
  }

  .brand-logo-wrap {
    width: 36px;
    height: 36px;
  }

  .brand-logo {
    width: 28px;
    height: 28px;
  }

  .brand-block p {
    font-size: 0.72rem;
    letter-spacing: 0.1em;
  }

  .nav-groups {
    gap: 8px;
  }

  .group-header {
    padding: 10px 12px;
  }

  .nav-item {
    min-height: 40px;
    padding: 0 10px 0 8px;
  }

  .nav-icon-shell {
    width: 26px;
    height: 26px;
  }

  .sidebar-footer {
    padding: 10px;
  }

  .topbar-panel {
    padding: 18px 16px;
    border-radius: 20px;
  }

  .mobile-menu-button {
    width: 40px;
    height: 40px;
    border-radius: 12px;
  }

  .admin-topbar h1 {
    font-size: 1.8rem;
  }

  .admin-topbar p {
    font-size: 0.92rem;
  }

  .admin-content-panel {
    border-radius: 20px;
  }
}
</style>
