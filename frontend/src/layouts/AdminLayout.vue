<script setup>
import { computed } from 'vue'
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
} from '@element-plus/icons-vue'
import { adminModules } from '../constants/adminNavigation'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const iconMap = {
  Dashboard: DataBoard,
  Profile: User,
  Users: UsersIcon,
  Players: UserFilled,
  Teams: Connection,
  Tournaments: Trophy,
  Registrations: Tickets,
  Draws: Compass,
  Courts: Location,
  Matches: Histogram,
  Schedule: Calendar,
  Rankings: DataAnalysis,
}

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

const pageTitle = computed(() => route.meta.adminTitle || 'Admin Overview')
const pageDescription = computed(
  () =>
    route.meta.adminDescription ||
    'Lớp nền tảng cho Admin dashboard: layout, guard, API client và bộ component chuẩn.',
)
const currentUserName = computed(() => authStore.user?.full_name || authStore.user?.email || 'Admin')

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
        <p>Admin Control Center</p>
      </div>

      <div class="nav-groups">
        <section v-for="group in groupedNavigation" :key="group.label" class="nav-group">
          <p class="group-label">{{ group.label }}</p>
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
              <span class="nav-badge">{{ item.badge }}</span>
            </RouterLink>
          </nav>
        </section>
      </div>

      <div class="sidebar-footer">
        <div class="admin-user-chip">
          <span class="user-label">Signed in</span>
          <strong>{{ currentUserName }}</strong>
        </div>
        <el-button class="logout-button" text @click="handleLogout">Đăng xuất</el-button>
      </div>
    </aside>

    <section class="admin-shell">
      <header class="admin-topbar">
        <div>
          <p class="page-kicker">Admin Workspace</p>
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
  gap: 26px;
  padding: 28px 20px;
  background: linear-gradient(180deg, #14332e 0%, #0f2622 100%);
  color: #f7fbf9;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.brand-block {
  display: grid;
  gap: 8px;
  padding: 8px 10px;
}

.brand-link {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.brand-block p {
  color: rgba(247, 251, 249, 0.68);
  font-size: 0.92rem;
}

.nav-groups {
  display: grid;
  gap: 18px;
  min-height: 0;
  padding-right: 4px;
  overflow-y: auto;
}

.nav-group {
  display: grid;
  gap: 8px;
}

.group-label {
  padding: 0 12px;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(247, 251, 249, 0.46);
}

.admin-nav {
  display: grid;
  gap: 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 48px;
  padding: 0 14px;
  border-radius: 16px;
  color: rgba(247, 251, 249, 0.78);
  transition: 0.25s ease;
}

.nav-leading {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.nav-item:hover {
  background: rgba(247, 251, 249, 0.08);
  color: #ffffff;
}

.nav-item-active {
  background: linear-gradient(135deg, #d7f171 0%, #b9d84d 100%);
  color: #13211d;
  font-weight: 700;
}

.nav-badge {
  min-width: 50px;
  padding: 4px 10px;
  border-radius: 999px;
  text-align: center;
  background: rgba(255, 255, 255, 0.08);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.nav-item-active .nav-badge {
  background: rgba(19, 33, 29, 0.12);
}

.sidebar-footer {
  margin-top: auto;
  display: grid;
  gap: 14px;
  padding: 18px 14px;
  border-radius: 20px;
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
  font-weight: 800;
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

@media (max-width: 1180px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }

  .admin-sidebar {
    position: sticky;
    top: 0;
    z-index: 10;
    gap: 18px;
  }

  .nav-groups {
    max-height: none;
  }

  .admin-nav {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }
}

@media (max-width: 640px) {
  .admin-topbar,
  .admin-main {
    padding-left: 20px;
    padding-right: 20px;
  }
}
</style>
