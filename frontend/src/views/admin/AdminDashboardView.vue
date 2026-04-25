<script setup>
import { onMounted, ref, computed } from 'vue'
import { apiClient } from '../../services/apiClient'
import { Money, Trophy, UserFilled, Loading, DataLine } from '@element-plus/icons-vue'
import { currentLocale, t } from '../../utils/locale'

const stats = ref(null)
const isLoading = ref(true)

const fetchStats = async () => {
  try {
    const data = await apiClient.get('/api/tournaments/summary/stats')
    stats.value = data
  } catch (error) {
    console.error('Failed to fetch admin stats:', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchStats)

// Reactive currency formatter
const formatCurrency = (value) => {
  const locale = currentLocale.value === 'vi' ? 'vi-VN' : 'en-US'
  const currency = currentLocale.value === 'vi' ? 'VND' : 'USD'
  return new Intl.NumberFormat(locale, { style: 'currency', currency }).format(value)
}
</script>

<template>
  <div class="dashboard-page" v-loading="isLoading">
    <template v-if="stats">
      <section class="hero-panel">
        <div class="hero-copy">
          <span class="eyebrow">Admin control center</span>
          <h2>{{ $t('admin.adminOpsCenter') }}</h2>
          <p>
            {{ $t('admin.adminOpsDesc') }}
          </p>
        </div>
        <div class="hero-actions">
          <div class="hero-metric">
            <span>{{ $t('admin.completed') }}</span>
            <strong>{{ stats.completion_rate }}%</strong>
          </div>
          <div class="hero-metric">
            <span>{{ $t('admin.matchesDone') }}</span>
            <strong>{{ stats.completed_matches }}</strong>
          </div>
          <div class="hero-metric accent">
            <span>{{ $t('admin.totalMatches') }}</span>
            <strong>{{ stats.total_matches }}</strong>
          </div>
        </div>
      </section>

      <div class="stats-grid">
        <div class="stat-card premium-finance-card">
          <div class="card-bg-decoration"></div>
          <div class="stat-content">
            <div class="stat-text">
              <span class="stat-label">{{ $t('admin.totalRevenue') }}</span>
              <strong class="stat-value">{{ formatCurrency(stats.revenue) }}</strong>
            </div>
            <div class="stat-icon-wrap finance-icon">
              <el-icon><Money /></el-icon>
            </div>
          </div>
        </div>

        <div class="stat-card glass-stat-card">
          <div class="stat-content">
            <div class="stat-text">
              <span class="stat-label">{{ $t('admin.activeTournaments') }}</span>
              <strong class="stat-value">
                {{ stats.active_tournaments }}
                <span class="val-sep">/</span>
                <small>{{ stats.total_tournaments }}</small>
              </strong>
            </div>
            <div class="stat-icon-wrap tournament-icon">
              <el-icon><Trophy /></el-icon>
            </div>
          </div>
        </div>

        <div class="stat-card glass-stat-card">
          <div class="stat-content">
            <div class="stat-text">
              <span class="stat-label">{{ $t('admin.pendingApprovals') }}</span>
              <strong class="stat-value warning-text">{{ stats.pending_approvals }}</strong>
            </div>
            <div class="stat-icon-wrap pending-icon">
              <el-icon><Loading /></el-icon>
            </div>
          </div>
        </div>

        <div class="stat-card glass-stat-card">
          <div class="stat-content">
            <div class="stat-text">
              <span class="stat-label">{{ $t('admin.totalRegistrations') }}</span>
              <strong class="stat-value">{{ stats.total_registrations }}</strong>
            </div>
            <div class="stat-icon-wrap user-icon">
              <el-icon><UserFilled /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <div class="overview-details-grid">
        <div class="premium-glass-card performance-section">
          <div class="card-header-row">
            <h3><el-icon><DataLine /></el-icon> {{ $t('admin.systemPerformance') }}</h3>
            <span class="live-tag">● {{ $t('admin.liveUpdate') }}</span>
          </div>

          <div class="performance-body">
            <div class="chart-container">
              <el-progress
                type="dashboard"
                :percentage="stats.completion_rate"
                :color="'#146250'"
                :stroke-width="12"
                :width="180"
              >
                <template #default="{ percentage }">
                  <div class="percentage-wrap">
                    <span class="percentage-value">{{ percentage }}%</span>
                    <span class="percentage-label">{{ $t('admin.completed') }}</span>
                  </div>
                </template>
              </el-progress>
            </div>

            <div class="performance-stats">
              <div class="p-stat-item">
                <span class="p-dot bg-primary"></span>
                <div class="p-info">
                  <span class="p-label">{{ $t('admin.matchesDone') }}</span>
                  <strong class="p-val">{{ stats.completed_matches }} {{ $t('admin.matches').toLowerCase() }}</strong>
                </div>
              </div>

              <div class="p-stat-item">
                <span class="p-dot bg-neutral"></span>
                <div class="p-info">
                  <span class="p-label">{{ $t('admin.matchesExpected') }}</span>
                  <strong class="p-val">{{ stats.total_matches }} {{ $t('admin.matches').toLowerCase() }}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="quick-summary-card">
          <h4>{{ $t('admin.quickReport') }}</h4>
          <div class="summary-list">
            <div class="summary-item">
              <el-icon class="icon-success"><Trophy /></el-icon>
              <p>{{ $t('admin.reportActiveTournaments', { count: stats.active_tournaments }) }}</p>
            </div>
            <div class="summary-item">
              <el-icon class="icon-warning"><Loading /></el-icon>
              <p>{{ $t('admin.reportPendingApprovals', { count: stats.pending_approvals }) }}</p>
            </div>
            <div class="summary-item">
              <el-icon class="icon-info"><UserFilled /></el-icon>
              <p>{{ $t('admin.reportTotalRegistrations', { count: stats.total_registrations }) }}</p>
            </div>
            <div class="summary-item">
              <el-icon class="icon-success"><DataLine /></el-icon>
              <p>{{ $t('admin.reportCompletionRate', { rate: stats.completion_rate }) }}</p>
            </div>
          </div>
        </div>
      </div>

      <section class="ops-report-grid">
        <article class="ops-report-card">
          <span class="ops-label">{{ $t('admin.totalRevenue') }}</span>
          <strong>{{ formatCurrency(stats.revenue) }}</strong>
          <p>{{ $t('admin.revenueDesc') }}</p>
        </article>
        <article class="ops-report-card">
          <span class="ops-label">{{ $t('admin.completed') }}</span>
          <strong>{{ stats.completion_rate }}%</strong>
          <p>{{ $t('admin.completionDesc') }}</p>
        </article>
        <article class="ops-report-card">
          <span class="ops-label">{{ $t('admin.activeTournaments') }}</span>
          <strong>{{ stats.active_tournaments }}</strong>
          <p>{{ $t('admin.activeTournamentsDesc') }}</p>
        </article>
        <article class="ops-report-card">
          <span class="ops-label">{{ $t('admin.pendingApprovals') }}</span>
          <strong>{{ stats.pending_approvals }}</strong>
          <p>{{ $t('admin.pendingApprovalsDesc') }}</p>
        </article>
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard-page {
  padding: 0;
  color: #0f172a;
  background:
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.08), transparent 28%),
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.hero-panel {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: stretch;
  padding: 26px 28px;
  margin-bottom: 22px;
  border-radius: 28px;
  background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
  border: 1px solid rgba(16, 185, 129, 0.15);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.hero-copy {
  max-width: 760px;
}

.eyebrow {
  display: inline-flex;
  margin-bottom: 12px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(20, 98, 80, 0.08);
  color: #146250;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.hero-copy h2 {
  margin: 0 0 10px;
  font-size: clamp(1.8rem, 3vw, 2.6rem);
  line-height: 1.05;
  letter-spacing: -0.04em;
  color: #0f172a;
}

.hero-copy p {
  margin: 0;
  max-width: 680px;
  color: #475569;
  line-height: 1.7;
  font-size: 0.96rem;
}

.hero-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  min-width: 360px;
}

.hero-metric {
  min-width: 0;
  border-radius: 20px;
  padding: 16px;
  background: #ffffff;
  border: 1px solid rgba(203, 213, 225, 0.8);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 10px;
}

.hero-metric span {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #64748b;
  font-weight: 600;
}

.hero-metric strong {
  font-size: 1.8rem;
  line-height: 1;
  color: #146250;
  font-weight: 700;
}

.hero-metric.accent {
  background: linear-gradient(135deg, #146250 0%, #1f7a61 100%);
  border-color: transparent;
}

.hero-metric.accent span,
.hero-metric.accent strong {
  color: #ffffff;
}

/* Grid Thẻ Thống kê */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  border-radius: 24px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover {
  transform: translateY(-4px);
}

/* Card doanh thu */
.premium-finance-card {
  background:
    linear-gradient(135deg, rgba(15, 118, 110, 0.98) 0%, rgba(20, 98, 80, 0.95) 48%, rgba(34, 197, 94, 0.88) 100%);
  border: 1px solid rgba(16, 185, 129, 0.18);
  box-shadow:
    0 18px 40px rgba(20, 98, 80, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
}

.premium-finance-card .stat-label {
  color: rgba(191, 219, 254, 0.74);
}

.premium-finance-card .stat-value {
  color: #f8fafc;
}

.card-bg-decoration {
  position: absolute;
  top: -32px;
  right: -28px;
  width: 140px;
  height: 140px;
  background:
    radial-gradient(circle, rgba(34, 197, 94, 0.24) 0%, rgba(20, 98, 80, 0.18) 42%, transparent 72%);
  border-radius: 50%;
}

/* Card sáng mềm - Phong cách Modern Tech Slate */
.glass-stat-card {
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(16, 185, 129, 0.14);
  box-shadow:
    0 16px 36px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
}

.glass-stat-card:hover {
  box-shadow:
    0 22px 44px rgba(15, 23, 42, 0.1),
    0 4px 12px rgba(20, 98, 80, 0.08);
}

.stat-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
  gap: 16px;
}

.stat-text {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.stat-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #64748b;
  font-weight: 500;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
  line-height: 1.1;
}

.stat-value small {
  font-size: 1rem;
  color: #64748b;
  font-weight: 500;
}

.val-sep {
  margin: 0 4px;
  color: #94a3b8;
}

.warning-text {
  color: #d97706;
}

.stat-icon-wrap {
  width: 54px;
  height: 54px;
  border-radius: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
  flex-shrink: 0;
}

.finance-icon {
  background: rgba(96, 165, 250, 0.12);
  color: #93c5fd;
}

.tournament-icon {
  background: #ecfdf5;
  color: #146250;
}

.pending-icon {
  background: #fff7ed;
  color: #c2410c;
}

.user-icon {
  background: #ecfdf5;
  color: #0f766e;
}

/* Dashboard Detail Sections */
.overview-details-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.premium-glass-card {
  background: rgba(255, 255, 255, 0.98); 
  border-radius: 28px;
  padding: 32px;
  border: 1px solid rgba(16, 185, 129, 0.14);
  box-shadow:
    0 20px 40px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  gap: 16px;
}

.card-header-row h3 {
  font-size: 1.25rem;
  font-weight: 500;
  color: #0f172a;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.live-tag {
  font-size: 0.72rem;
  color: #146250;
  font-weight: 500;
  background: rgba(220, 252, 231, 0.9);
  padding: 6px 12px;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border: 1px solid rgba(34, 197, 94, 0.18);
}

.performance-body {
  display: flex;
  align-items: center;
  gap: 48px;
}

.percentage-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.percentage-value {
  font-size: 2rem;
  font-weight: 500;
  color: #0f172a;
}

.percentage-label {
  font-size: 0.78rem;
  color: #64748b;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.performance-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.p-stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  background: rgba(248, 250, 252, 0.88);
  border-radius: 18px;
  border: 1px solid rgba(209, 250, 229, 0.8);
  transition: background 0.2s, transform 0.2s;
}

.p-stat-item:hover {
  transform: translateY(-1px);
  background: rgba(241, 245, 249, 0.96);
}

.p-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.bg-primary {
  background: #146250;
}

.bg-neutral {
  background: #94a3b8;
}

.p-info {
  display: flex;
  flex-direction: column;
}

.p-label {
  font-size: 0.78rem;
  color: #64748b;
  font-weight: 500;
}

.p-val {
  font-size: 1.08rem;
  color: #0f172a;
  font-weight: 500;
}

/* Quick Summary Card */
.quick-summary-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 28px;
  padding: 32px;
  border: 1px solid rgba(16, 185, 129, 0.14);
  box-shadow:
    0 20px 40px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
}

.quick-summary-card h4 {
  font-size: 1.1rem;
  font-weight: 500;
  color: #0f172a;
  margin-top: 0;
  margin-bottom: 24px;
}

.summary-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.summary-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.summary-item p {
  margin: 0;
  font-size: 0.94rem;
  color: #475569;
  line-height: 1.6;
}

.summary-item .summary-val {
  color: #0f172a;
  font-weight: 500;
}

.icon-success {
  color: #146250;
}

.icon-warning {
  color: #d97706;
}

.icon-info {
  color: #0f766e;
}

.ops-report-grid {
  margin-top: 24px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.ops-report-card {
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(16, 185, 129, 0.14);
  border-radius: 20px;
  padding: 18px 20px;
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.05);
}

.ops-label {
  display: inline-flex;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #64748b;
  margin-bottom: 10px;
}

.ops-report-card strong {
  display: block;
  font-size: 1.35rem;
  color: #146250;
  margin-bottom: 8px;
}

.ops-report-card p {
  margin: 0;
  color: #64748b;
  font-size: 0.86rem;
  line-height: 1.55;
}

@media (max-width: 1100px) {
  .hero-panel {
    flex-direction: column;
  }
  .hero-actions {
    width: 100%;
    min-width: 0;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .hero-actions {
    grid-template-columns: 1fr;
  }
  .hero-metric strong {
    font-size: 1.5rem;
  }
}

@media (max-width: 1200px) {
  .overview-details-grid {
    grid-template-columns: 1fr;
  }

  .ops-report-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .performance-body {
    flex-direction: column;
    gap: 32px;
    text-align: center;
  }

  .card-header-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .ops-report-grid {
    grid-template-columns: 1fr;
  }
}
</style>
