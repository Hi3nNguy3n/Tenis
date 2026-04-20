import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { adminModules } from '../constants/adminNavigation'

import ChatTest from '../views/customer/ChatRoom.vue'

// --- CUSTOMER VIEWS ---
const HomeView = () => import('../views/customer/HomeView.vue')
const TournamentsView = () => import('../views/customer/tournaments/TournamentsView.vue')
const TournamentDetailView = () => import('../views/customer/tournaments/TournamentDetailView.vue')
const TournamentRegisterView = () => import('../views/customer/tournaments/TournamentRegisterView.vue')
const PlayersView = () => import('../views/customer/PlayersView.vue')
const MatchesView = () => import('../views/customer/MatchesView.vue')
const RankingsView = () => import('../views/customer/RankingsView.vue')
const NewsView = () => import('../views/customer/tournaments/NewsView.vue')
const NewsDetailView = () => import('../views/customer/tournaments/NewsDetailView.vue')

// --- PROFILE & ACCOUNT ---
const ProfileView = () => import('../views/customer/profile/ProfileView.vue')
const MyTournamentsView = () => import('../views/customer/profile/MyTournamentsView.vue')
const ChangePasswordView = () => import('../views/customer/profile/ChangePasswordView.vue')

// --- AUTH VIEWS ---
const LoginView = () => import('../views/auth/LoginView.vue')
const RegisterOtpView = () => import('../views/auth/RegisterOtpView.vue')
const VerifyRegisterOtpView = () => import('../views/auth/VerifyRegisterOtpView.vue')
const AdminLoginView = () => import('../views/auth/AdminLoginView.vue')
const ForgotPasswordView = () => import('../views/auth/ForgotPasswordView.vue')

const PaymentWaitingView = () => import('../views/customer/tournaments/PaymentWaitingView.vue')
const PaymentFailureView = () => import('../views/customer/tournaments/PaymentFailureView.vue')


const adminViewFactories = {
  dashboard: () => import('../views/admin/AdminDashboardView.vue'),
  profile: () => import('../views/admin/AdminProfileView.vue'),
  tournaments: () => import('../views/admin/TournamentManagementView.vue'),
  registrations: () => import('../views/admin/RegistrationsQueueView.vue'),
  courts: () => import('../views/admin/CourtManagementView.vue'),
  schedule: () => import('../views/admin/ScheduleView.vue'),
  checkin: () => import('../views/admin/CheckInView.vue'),
  players: () => import('../views/admin/AdminPlayersView.vue'),
  payments: () => import('../views/admin/PaymentReconciliationView.vue'),
  draws: () => import('../views/admin/DrawsView.vue'),
  matches: () => import('../views/admin/MatchesView.vue'),
  placeholder: () => import('../views/admin/GenericAdminModuleView.vue'),
  ActivityLogsView: () => import('../views/admin/ActivityLogsView.vue'),
  dailySchedule: () => import('../views/admin/AdminDailyScheduleView.vue'),
  calendar: () => import('../views/admin/AdminCalendarView.vue'),
  news: () => import('../views/admin/NewsManagementView.vue'),
  rankings: () => import('../views/admin/AdminRankingsView.vue'),
  mailCampaign: () => import('../views/admin/MailCampaignView.vue'),
}


const adminRoutes = adminModules.map((module) => ({
  path: module.path,
  name: module.name,
  component: adminViewFactories[module.view] || adminViewFactories.placeholder,
  meta: {
    adminLayout: true,
    requiresAuth: true,
    adminTitle: module.title,
    adminDescription: module.description,
    adminModuleLabel: module.label,
    adminModuleBadge: module.badge,
    adminModuleHighlights: module.highlights,
  },
}))

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { authLayout: true },
    },

    {
      path: '/admin/login',
      name: 'admin-login',
      component: AdminLoginView,
      meta: { authLayout: true },
    },

    {
      path: '/register-otp',
      name: 'register-otp',
      component: RegisterOtpView,
      meta: { authLayout: true },
    },
    {
      path: '/register-otp/verify',
      name: 'register-otp-verify',
      component: VerifyRegisterOtpView,
      meta: { authLayout: true },
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPasswordView,
      meta: { authLayout: true },
    },
    // --- TOURNAMENTS ---
    {
      path: '/tournaments',
      name: 'tournaments',
      component: TournamentsView,
    },
    {
      path: '/tournaments/:id',
      name: 'tournament-detail',
      component: TournamentDetailView,
    },
    {
      path: '/tournaments/:id/register',
      name: 'tournament-register',
      component: TournamentRegisterView,
      meta: { requiresAuth: true },
    },
    // --- PLAYER & PROFILE ---
    {
      path: '/players',
      name: 'players',
      component: PlayersView,
    },
    {
      path: '/rankings',
      name: 'rankings',
      component: RankingsView,
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true },
    },
    {
      path: '/profile/my-tournaments',
      name: 'my-tournaments',
      component: MyTournamentsView,
      meta: { requiresAuth: true },
    },
    {
      path: '/profile/change-password',
      name: 'change-password',
      component: ChangePasswordView,
      meta: { requiresAuth: true },
    },
    {
      path: '/tournaments/:id/waiting',
      name: 'payment-waiting',
      component: PaymentWaitingView,
      meta: { requiresAuth: true },
    },
    {
      path: '/tournaments/:id/failure',
      name: 'payment-failure',
      component: PaymentFailureView,
      meta: { requiresAuth: true },
    },
    {
      path: '/news',
      name: 'customer-news',
      component: NewsView,
    },
    {
      path: '/news/:slug',
      name: 'customer-news-detail',
      component: NewsDetailView,
    },
    // --- ADMIN ---
    {
      path: '/admin',
      component: () => import('../layouts/AdminLayout.vue'),
      meta: {
        adminLayout: true,
        requiresAuth: true,
      },
      children: adminRoutes,
    },
    {
      path: '/matches',
      name: 'matches',
      component: MatchesView,
    },
    {
      path: '/chat',
      name: 'ChatRoom',
      component: ChatTest,
      meta: { requiresAuth: true } // Nếu hệ thống của bạn có check đăng nhập
    }
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  },
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  authStore.hydrate()

  if (authStore.isAuthenticated && !authStore.profile) {
    await authStore.fetchCurrentProfile()
  }

  if (to.meta.adminLayout && !authStore.isAdmin) {
    if (authStore.isAuthenticated) {
      authStore.logout()
    }
    return {
      name: 'admin-login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }


  if (to.meta.authLayout && authStore.isAuthenticated) {
    let redirectPath = typeof to.query.redirect === 'string' ? to.query.redirect : (authStore.isAdmin ? '/admin' : '/')
    if (redirectPath.startsWith('/admin') && !authStore.isAdmin) {
      redirectPath = '/'
    }
    return redirectPath
  }

  return true
})

export default router
