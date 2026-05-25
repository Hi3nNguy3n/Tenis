<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import {
  Calendar as CalendarIcon,
  Compass,
  Connection,
  DataAnalysis,
  DataBoard,
  Histogram,
  Location as LocationIcon,
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
    'Tạo trận thủ công': t('admin.createMatch'),
    marketing: 'Banner & Nhà tài trợ'
  }
  return labelMap[label] || label
}

const getLocalizedSection = (section) => {
  const sectionMap = {
    'Tổng quan': t('admin.overview'),
    'Vận hành': t('admin.operation'),
    'Giải đấu': t('admin.tournaments'),
    'Điều phối': t('admin.coordination'),
    'Hệ thống': t('admin.system'),
    system: 'Hệ thống'
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
  'Quản lý Sân': LocationIcon,
  'Trận đấu': Histogram,
  'Lịch trình': CalendarIcon,
  'BXH & Điểm số': DataAnalysis,
  'Điểm danh QR': Monitor,
  'Thanh toán': Tickets,
  'Nhật ký hệ thống': Setting,
  'Lịch thi đấu ngày': Memo,
  'Lịch tổng quan': CalendarIcon,
  'Tin tức': Files,
  marketing: Files,
  'Gửi mail hàng loạt': Message,
  'Tạo trận thủ công': Monitor
}

const activeGroups = ref(['Tổng quan', 'Giải đấu', 'Vận hành', 'Điều phối', 'Hệ thống', 'system'])

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
    'Tạo trận giao hữu / 1vs1': t('admin.createMatch'),
    marketing: 'Quản lý Banner & Nhà tài trợ'
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
    'Soạn template, chọn lịch gửi, ghi log và gửi thông báo hàng loạt đến VĐV.': t('admin.mailCampaignDesc'),
    marketingDesc: 'Quản lý banner quảng bá, logo nhà tài trợ, vị trí hiển thị và thứ tự sắp xếp.'
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
    <!-- Sidebar Overlay for Mobile -->
    <transition name="fade">
      <div v-if="isSidebarOpen" class="sidebar-backdrop" @click="closeSidebar"></div>
    </transition>

    <!-- Admin Sidebar -->
    <aside class="admin-sidebar" :class="{ 'is-open': isSidebarOpen }">
      <div class="sidebar-header">
        <div class="brand-block" @click="router.push('/admin')">
          <div class="brand-link">
            <span class="brand-logo-wrap">
              <img
                src="https://res.cloudinary.com/dfs9o3bny/image/upload/v1776309753/z7730353029258_1dbe77285e553a1aa2ae1ab543a985c8-removebg-preview_nj3utv.png"
                alt="Saigon Tennis"
                class="brand-logo"
              />
            </span>
            <span class="brand-name">Saigontennistours</span>
          </div>
          <p class="brand-subtitle">{{ $t('admin.opsCenter') }}</p>
        </div>
      </div>

      <!-- Navigation groups with Scrollable Container -->
      <div class="nav-groups-wrapper custom-scrollbar">
        <div class="nav-groups">
          <section v-for="group in groupedNavigation" :key="group.label" class="nav-group">
            <div
              class="group-header"
              :class="{ 'is-expanded': isGroupActive(group.originalLabel) }"
              @click="toggleGroup(group.originalLabel)"
            >
              <span class="group-label">{{ group.label }}</span>
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
      </div>

      <!-- Fixed Sidebar Footer -->
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">
            <el-icon><UserFilled /></el-icon>
          </div>
          <div class="user-meta">
            <span class="user-name">{{ currentUserName }}</span>
            <span class="user-role">Administrator</span>
          </div>
        </div>
        <button class="logout-btn-sidebar" @click="handleLogout">
          <el-icon><Connection /></el-icon>
          <span>{{ $t('admin.logout') }}</span>
        </button>
      </div>
    </aside>

    <!-- Main Content Shell -->
    <section class="admin-shell">
      <header class="admin-topbar">
        <div class="topbar-inner">
          <div class="topbar-left">
            <button class="mobile-menu-button" @click="toggleSidebar" aria-label="Toggle Menu">
              <span class="line"></span>
              <span class="line"></span>
              <span class="line"></span>
            </button>
            <div class="page-info">
              <span class="page-kicker">{{ $t('admin.adminSpace') }}</span>
              <h1 class="page-title">{{ pageTitle }}</h1>
            </div>
          </div>

          <div class="topbar-right">
            <div class="topbar-actions">
              <button class="lang-btn" @click="toggleLocale">
                <span class="icon">🌐</span>
                <span class="text">{{ currentLocale.toUpperCase() }}</span>
              </button>
              
              <div class="system-status">
                <span class="status-dot pulse"></span>
                <span class="status-text">{{ $t('admin.systemActive') }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="page-description" v-if="pageDescription">
          <p>{{ pageDescription }}</p>
        </div>
      </header>

      <main class="admin-main custom-scrollbar">
        <div class="admin-view-panel">
          <RouterView v-slot="{ Component }">
            <transition name="page-fade" mode="out-in">
              <!-- ADDED KEY TO FORCE RE-RENDER ON ROUTE CHANGE -->
              <component :is="Component" :key="route.path" />
            </transition>
          </RouterView>
        </div>
      </main>
    </section>
  </div>
</template>

<style scoped>
/* Base Layout */
:global(body.admin-body) {
  margin: 0;
  background: #f8fafc !important;
  overflow: hidden;
}

.admin-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  height: 100vh;
  width: 100vw;
  background: #064e3b;
  position: relative;
  overflow: hidden;
}

/* Sidebar */
.admin-sidebar {
  display: flex;
  flex-direction: column;
  background: #064e3b;
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  padding: 24px 0; /* Padding handled by internal elements */
  z-index: 100;
  height: 100vh;
  overflow: hidden;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-header { 
  padding: 0 20px;
  margin-bottom: 24px; 
}

.brand-block {
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}
.brand-block:hover { background: rgba(255, 255, 255, 0.05); }

.brand-link { display: flex; align-items: center; gap: 12px; }

.brand-logo-wrap {
  width: 40px; height: 40px;
  background: #fff;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.brand-logo { width: 30px; height: 30px; }

.brand-name {
  font-weight: 700; font-size: 1.1rem; color: #fff;
  letter-spacing: -0.01em;
}
.brand-subtitle {
  margin: 6px 0 0; font-size: 0.65rem; color: rgba(255,255,255,0.4);
  text-transform: uppercase; letter-spacing: 0.1em;
}

/* Nav Groups - FIXED SCROLLING */
.nav-groups-wrapper {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0; /* Critical for flex scrolling */
  padding: 0 16px;
}

.nav-groups {
  display: flex; 
  flex-direction: column; 
  gap: 8px;
  padding-bottom: 20px;
}

.nav-group { display: flex; flex-direction: column; gap: 4px; }

.group-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 10px; border-radius: 8px;
  background: transparent;
  cursor: pointer; transition: all 0.2s;
}
.group-header:hover { background: rgba(255,255,255,0.03); }

/* Highlighted Parent Headers */
.group-label {
  font-size: 0.8rem; 
  font-weight: 800; 
  color: rgba(255,255,255,0.8); /* Brighter */
  text-transform: uppercase; 
  letter-spacing: 0.08em;
}
.arrow-icon { font-size: 12px; color: rgba(255,255,255,0.4); transition: transform 0.3s; }
.is-expanded .arrow-icon { transform: rotate(90deg); }

/* Tree Structure Indentation */
.admin-nav { 
  display: flex; 
  flex-direction: column; 
  gap: 4px; 
  padding-left: 20px;
  position: relative;
  margin-top: 4px;
}

.admin-nav::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 24px;
  width: 1px;
  background: rgba(255, 255, 255, 0.15);
}

.nav-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; border-radius: 8px;
  color: rgba(255,255,255,0.65); text-decoration: none;
  transition: all 0.2s;
  position: relative;
}

.nav-item::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  width: 10px;
  height: 1px;
  background: rgba(255, 255, 255, 0.15);
}

.nav-item:hover { background: rgba(255,255,255,0.06); color: #fff; }

.nav-leading { display: flex; align-items: center; gap: 10px; }
.nav-icon-shell { font-size: 18px; opacity: 0.7; display: flex; align-items: center; }
.nav-label { font-size: 0.95rem; font-weight: 500; }

/* Active Item - White Theme */
.nav-item-active {
  background: #fff !important; 
  color: #064e3b !important;
  font-weight: 700;
  box-shadow: 0 4px 15px rgba(255, 255, 255, 0.15);
}
.nav-item-active .nav-icon-shell { opacity: 1; }

.nav-badge {
  background: rgba(0,0,0,0.2); padding: 2px 6px;
  border-radius: 4px; font-size: 0.6rem; font-weight: 800;
}

/* Sidebar Footer */
.sidebar-footer {
  margin-top: auto;
  padding: 20px;
  border-top: 1px solid rgba(255,255,255,0.08);
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #064e3b;
}
.user-info { display: flex; align-items: center; gap: 12px; }
.user-avatar {
  width: 36px; height: 36px; border-radius: 10px;
  background: rgba(255,255,255,0.1);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; color: #fff;
}
.user-meta { display: flex; flex-direction: column; }
.user-name { font-size: 0.9rem; font-weight: 600; color: #fff; }
.user-role { font-size: 0.75rem; color: rgba(255,255,255,0.4); }

.logout-btn-sidebar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #fca5a5;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 700;
}
.logout-btn-sidebar:hover {
  background: #ef4444;
  color: #fff;
  border-color: transparent;
}

/* Main Content Shell */
.admin-shell {
  background: #f8fafc;
  display: flex; flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.admin-topbar { padding: 32px 48px 16px; }

.topbar-inner { display: flex; align-items: center; justify-content: space-between; gap: 32px; }

.topbar-left { display: flex; align-items: center; gap: 24px; }

.page-info { display: flex; flex-direction: column; }
.page-kicker {
  font-size: 0.8rem; font-weight: 700; color: #059669;
  text-transform: uppercase; letter-spacing: 0.12em;
}
.page-title {
  margin: 6px 0 0; font-size: 2.4rem; font-weight: 800;
  color: #0f172a; letter-spacing: -0.03em;
}

.page-description { margin-top: 12px; padding: 0 48px; }
.page-description p { margin: 0; color: #64748b; line-height: 1.6; font-size: 1rem; }

.topbar-right { display: flex; align-items: center; }
.topbar-actions { display: flex; align-items: center; gap: 20px; }

.lang-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 18px; border-radius: 12px;
  background: #fff; border: 1px solid #e2e8f0;
  cursor: pointer; transition: all 0.2s;
  font-weight: 700; color: #0f172a;
}
.lang-btn:hover { border-color: #059669; background: #f0fdf4; }

.system-status {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 18px; background: #ecfdf5;
  border-radius: 12px; border: 1px solid rgba(5, 150, 105, 0.1);
}
.status-dot { width: 8px; height: 8px; background: #10b981; border-radius: 50%; }
.status-dot.pulse { animation: pulse 2s infinite; }
.status-text { font-size: 0.85rem; font-weight: 600; color: #065f46; }

/* Main Area */
.admin-main {
  flex: 1; 
  overflow-y: auto; 
  padding: 16px 48px 48px;
  display: block; /* Allow children to flow and expand naturally */
}

.admin-view-panel {
  background: #fff; 
  border-radius: 24px;
  padding: 40px; 
  box-shadow: 0 4px 25px rgba(0,0,0,0.03);
  border: 1px solid #f1f5f9;
  min-height: calc(100vh - 180px); /* Ensure it fills space but can grow infinitely */
  width: 100%;
}

/* Mobile Controls */
.mobile-menu-button {
  display: none; flex-direction: column; gap: 5px;
  width: 48px; height: 48px; border-radius: 12px;
  border: 1px solid #e2e8f0; background: #fff;
  cursor: pointer; align-items: center; justify-content: center;
}
.mobile-menu-button .line { width: 20px; height: 2px; background: #0f172a; border-radius: 10px; }

.sidebar-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px); z-index: 90;
}

/* SCROLLBAR REFINED */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { 
  background: rgba(255, 255, 255, 0.2); 
  border-radius: 10px; 
}
.custom-scrollbar:hover::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.35); }

/* Main Content Scrollbar */
.admin-main.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.1); }
.admin-main.custom-scrollbar:hover::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.15); }

/* Animations */
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.collapse-enter-active, .collapse-leave-active {
  transition: max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s;
  overflow: hidden;
}
.collapse-enter-from, .collapse-leave-to { max-height: 0; opacity: 0; }
.collapse-enter-to, .collapse-leave-from { max-height: 2000px; opacity: 1; }

.page-fade-enter-active, .page-fade-leave-active { transition: all 0.3s ease; }
.page-fade-enter-from { opacity: 0; transform: scale(0.98); }
.page-fade-leave-to { opacity: 0; transform: scale(1.02); }

/* Responsive */
@media (max-width: 1280px) {
  .admin-layout { grid-template-columns: 260px 1fr; }
  .admin-topbar { padding: 24px 32px 12px; }
  .admin-main { padding: 0 32px 32px; }
  .page-description { padding: 0 32px; }
}

@media (max-width: 1024px) {
  .admin-layout { grid-template-columns: 1fr; }
  .admin-sidebar {
    position: fixed; left: 0; top: 0; bottom: 0;
    transform: translateX(-100%); width: 280px;
  }
  .admin-sidebar.is-open { transform: translateX(0); }
  .admin-shell { margin: 0; }
  .mobile-menu-button { display: flex; }
  .system-status { display: none; }
}

@media (max-width: 640px) {
  .admin-topbar { padding: 24px 20px 12px; }
  .admin-main { padding: 0 20px 20px; }
  .admin-view-panel { padding: 24px; border-radius: 20px; }
  .page-title { font-size: 1.6rem; }
  .page-description { display: none; }
  .topbar-right { display: none; }
}
</style>
