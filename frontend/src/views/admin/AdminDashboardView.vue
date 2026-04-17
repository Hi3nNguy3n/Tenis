<script setup>
import { onMounted, ref } from 'vue'
import { apiClient } from '../../services/apiClient'
import { Money, Trophy, UserFilled, Loading, DataLine } from '@element-plus/icons-vue'

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

// Hàm format tiền tệ VNĐ
const formatVND = (value) => {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value)
}
</script>

<template>
  <div class="dashboard-page" v-loading="isLoading">
    <!-- Headers are centrally managed in AdminLayout to prevent duplication -->
    
    <template v-if="stats">
      <div class="stats-grid">
        <!-- Revenue Card with Special Decoration -->
        <div class="stat-card premium-finance-card">
          <div class="card-bg-decoration"></div>
          <div class="stat-content">
            <div class="stat-text">
              <span class="stat-label">Tổng Doanh Thu</span>
              <strong class="stat-value">{{ formatVND(stats.revenue) }}</strong>
            </div>
            <div class="stat-icon-wrap finance-icon">
              <el-icon><Money /></el-icon>
            </div>
          </div>
        </div>

        <!-- Glass Style Cards -->
        <div class="stat-card glass-stat-card">
          <div class="stat-content">
            <div class="stat-text">
              <span class="stat-label">Giải Đang Diễn Ra</span>
              <strong class="stat-value">{{ stats.active_tournaments }} <span class="val-sep">/</span> <small>{{ stats.total_tournaments }}</small></strong>
            </div>
            <div class="stat-icon-wrap tournament-icon">
              <el-icon><Trophy /></el-icon>
            </div>
          </div>
        </div>

        <div class="stat-card glass-stat-card">
          <div class="stat-content">
            <div class="stat-text">
              <span class="stat-label">Đơn Chờ Phê Duyệt</span>
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
              <span class="stat-label">Lượt Đăng Ký Tham Gia</span>
              <strong class="stat-value">{{ stats.total_registrations }}</strong>
            </div>
            <div class="stat-icon-wrap user-icon">
              <el-icon><UserFilled /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <div class="overview-details-grid">
        <!-- Performance / Progress Card -->
        <div class="premium-glass-card performance-section">
          <div class="card-header-row">
            <h3><el-icon><DataLine /></el-icon> Hiệu suất Hệ thống</h3>
            <span class="live-tag">● Cập nhật thời gian thực</span>
          </div>
          
          <div class="performance-body">
            <div class="chart-container">
              <el-progress 
                type="dashboard" 
                :percentage="stats.completion_rate" 
                :color="'#b9d84d'" 
                :stroke-width="12" 
                :width="180"
              >
                <template #default="{ percentage }">
                  <div class="percentage-wrap">
                    <span class="percentage-value">{{ percentage }}%</span>
                    <span class="percentage-label">Hoàn thành</span>
                  </div>
                </template>
              </el-progress>
            </div>

            <div class="performance-stats">
              <div class="p-stat-item">
                <span class="p-dot bg-primary"></span>
                <div class="p-info">
                  <span class="p-label">Trận đấu đã xong</span>
                  <strong class="p-val">{{ stats.completed_matches }} trận</strong>
                </div>
              </div>
              <div class="p-stat-item">
                <span class="p-dot bg-neutral"></span>
                <div class="p-info">
                  <span class="p-label">Tổng số trận dự kiến</span>
                  <strong class="p-val">{{ stats.total_matches }} trận</strong>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Summary Actions -->
        <div class="quick-summary-card">
           <h4>Thông báo nhanh</h4>
           <div class="summary-list">
             <div class="summary-item">
               <el-icon class="icon-success"><Trophy /></el-icon>
               <p>Hiện có <strong>{{ stats.active_tournaments }}</strong> giải đấu đang mở.</p>
             </div>
             <div class="summary-item">
               <el-icon class="icon-warning"><Loading /></el-icon>
               <p>Cần xử lý <strong>{{ stats.pending_approvals }}</strong> đơn đăng ký mới.</p>
             </div>
             <div class="summary-item">
               <el-icon class="icon-info"><UserFilled /></el-icon>
               <p>Tổng cộng <strong>{{ stats.total_registrations }}</strong> người chơi tham gia.</p>
             </div>
           </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard-page { padding: 0; }

/* Grid Thẻ Thống kê */
.stats-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); 
  gap: 20px; 
  margin-bottom: 32px; 
}

.stat-card { 
  background: white; 
  border-radius: 20px; 
  padding: 24px; 
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(226, 232, 240, 0.8);
  position: relative;
  overflow: hidden;
}

.stat-card:hover { 
  transform: translateY(-4px); 
  box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
}

/* Premium Card (Revenue) */
.premium-finance-card {
  background: linear-gradient(135deg, #13211d 0%, #1e3a34 100%);
  border: none;
}
.premium-finance-card .stat-label { color: rgba(255,255,255,0.6); }
.premium-finance-card .stat-value { color: #d7f171; }
.card-bg-decoration {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 100px;
  height: 100px;
  background: radial-gradient(circle, rgba(215, 241, 113, 0.1) 0%, transparent 70%);
  border-radius: 50%;
}

.stat-content { display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 1; }
.stat-text { display: flex; flex-direction: column; gap: 6px; }
.stat-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; font-weight: 700; }
.stat-value { font-size: 1.8rem; font-weight: 800; letter-spacing: -0.02em; }
.stat-value small { font-size: 1rem; color: #94a3b8; font-weight: 500; }
.val-sep { margin: 0 4px; color: #cbd5e1; }
.warning-text { color: #f59e0b; }

.stat-icon-wrap { 
  width: 52px; 
  height: 52px; 
  border-radius: 14px; 
  display: flex; 
  justify-content: center; 
  align-items: center; 
  font-size: 24px; 
}

.finance-icon { background: rgba(215, 241, 113, 0.15); color: #d7f171; }
.tournament-icon { background: #f0fdf4; color: #166534; }
.pending-icon { background: #fffbeb; color: #b45309; }
.user-icon { background: #eff6ff; color: #1d4ed8; }

/* Dashboard Detail Sections */
.overview-details-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.premium-glass-card {
  background: white;
  border-radius: 24px;
  padding: 32px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}
.card-header-row h3 { font-size: 1.25rem; font-weight: 700; color: #1e293b; margin: 0; display: flex; align-items: center; gap: 10px; }
.live-tag { font-size: 0.7rem; color: #10b981; font-weight: 700; background: #ecfdf5; padding: 4px 12px; border-radius: 99px; text-transform: uppercase; }

.performance-body { display: flex; align-items: center; gap: 48px; }

.percentage-wrap { display: flex; flex-direction: column; align-items: center; }
.percentage-value { font-size: 2rem; font-weight: 800; color: #1e293b; }
.percentage-label { font-size: 0.8rem; color: #64748b; font-weight: 600; text-transform: uppercase; }

.performance-stats { display: flex; flex-direction: column; gap: 16px; flex: 1; }
.p-stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: #f8fafc;
  border-radius: 16px;
  transition: background 0.2s;
}
.p-dot { width: 10px; height: 10px; border-radius: 50%; }
.bg-primary { background: #b9d84d; }
.bg-neutral { background: #cbd5e1; }
.p-info { display: flex; flex-direction: column; }
.p-label { font-size: 0.75rem; color: #64748b; font-weight: 600; }
.p-val { font-size: 1.1rem; color: #1e293b; font-weight: 700; }

/* Quick Summary Card */
.quick-summary-card {
  background: #f8fafc;
  border-radius: 24px;
  padding: 32px;
  border: 1px solid #e2e8f0;
}
.quick-summary-card h4 { font-size: 1.1rem; font-weight: 700; color: #1e293b; margin-top: 0; margin-bottom: 24px; }

.summary-list { display: flex; flex-direction: column; gap: 20px; }
.summary-item { display: flex; align-items: flex-start; gap: 12px; }
.summary-item p { margin: 0; font-size: 0.9rem; color: #475569; line-height: 1.5; }
.summary-item strong { color: #1e293b; }

/* Icons in summary */
.icon-success { color: #10b981; }
.icon-warning { color: #f59e0b; }
.icon-info { color: #3b82f6; }

@media (max-width: 1200px) {
  .overview-details-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .performance-body { flex-direction: column; gap: 32px; text-align: center; }
}
</style>