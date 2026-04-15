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
    <header class="dashboard-header">
      <h1>Tổng quan Hệ thống</h1>
      <p>Trung tâm kiểm soát Saigon Tennis. Cập nhật dữ liệu thời gian thực.</p>
    </header>

    <template v-if="stats">
      <div class="stats-grid">
        <div class="stat-card premium-card">
          <div class="stat-content">
            <div class="stat-text">
              <span class="stat-label">Tổng Doanh Thu</span>
              <strong class="stat-value text-gold">{{ formatVND(stats.revenue) }}</strong>
            </div>
            <div class="stat-icon-wrap bg-gold">
              <el-icon><Money /></el-icon>
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-content">
            <div class="stat-text">
              <span class="stat-label">Giải Đang Diễn Ra</span>
              <strong class="stat-value text-green">{{ stats.active_tournaments }} <small>/ {{ stats.total_tournaments }}</small></strong>
            </div>
            <div class="stat-icon-wrap bg-green">
              <el-icon><Trophy /></el-icon>
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-content">
            <div class="stat-text">
              <span class="stat-label">Đơn Chờ Phê Duyệt</span>
              <strong class="stat-value text-orange">{{ stats.pending_approvals }}</strong>
            </div>
            <div class="stat-icon-wrap bg-orange">
              <el-icon><Loading /></el-icon>
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-content">
            <div class="stat-text">
              <span class="stat-label">Lượt Đăng Ký Tham Gia</span>
              <strong class="stat-value text-blue">{{ stats.total_registrations }}</strong>
            </div>
            <div class="stat-icon-wrap bg-blue">
              <el-icon><UserFilled /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <div class="progress-section">
        <div class="progress-card">
          <div class="card-header">
            <h3><el-icon><DataLine /></el-icon> Tiến độ Giải đấu (Toàn hệ thống)</h3>
          </div>
          <div class="progress-body">
            
            <div class="chart-container">
              <el-progress type="dashboard" :percentage="stats.completion_rate" :color="'#006953'" :stroke-width="15" :width="200">
                <template #default="{ percentage }">
                  <div class="percentage-wrap">
                    <span class="percentage-value">{{ percentage }}%</span>
                    <span class="percentage-label">Hoàn thành</span>
                  </div>
                </template>
              </el-progress>
            </div>

            <div class="progress-details">
              <div class="detail-item">
                <div class="dot bg-green"></div>
                <div class="d-text">
                  <span>Trận đã đánh xong</span>
                  <strong>{{ stats.completed_matches }} trận</strong>
                </div>
              </div>
              <div class="detail-item">
                <div class="dot bg-gray"></div>
                <div class="d-text">
                  <span>Tổng số trận hệ thống</span>
                  <strong>{{ stats.total_matches }} trận</strong>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard-page { padding: 10px; }
.dashboard-header { margin-bottom: 30px; }
.dashboard-header h1 { font-size: 2rem; color: #123f34; margin-bottom: 5px; }
.dashboard-header p { color: #6e7a74; }

/* Grid Thẻ Thống kê */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 30px; }
.stat-card { background: white; border-radius: 20px; padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.03); transition: transform 0.2s; border: 1px solid #f0f2f2; }
.stat-card:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.06); }
.premium-card { background: linear-gradient(135deg, #123f34 0%, #006953 100%); border: none; }
.premium-card .stat-label, .premium-card .stat-value small { color: rgba(255,255,255,0.8); }

.stat-content { display: flex; justify-content: space-between; align-items: center; }
.stat-text { display: flex; flex-direction: column; gap: 8px; }
.stat-label { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; color: #6e7a74; font-weight: 700; }
.stat-value { font-size: 1.8rem; font-weight: 900; }
.stat-value small { font-size: 1rem; color: #94a3b8; }

.text-gold { color: #fef08a; }
.text-green { color: #006953; }
.text-orange { color: #ea580c; }
.text-blue { color: #2563eb; }

/* Icons */
.stat-icon-wrap { width: 56px; height: 56px; border-radius: 16px; display: flex; justify-content: center; align-items: center; font-size: 24px; }
.bg-gold { background: rgba(254, 240, 138, 0.2); color: #fef08a; }
.bg-green { background: #e6f0ee; color: #006953; }
.bg-orange { background: #ffedd5; color: #ea580c; }
.bg-blue { background: #dbeafe; color: #2563eb; }

/* Progress Section */
.progress-card { background: white; border-radius: 20px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.03); border: 1px solid #f0f2f2; }
.card-header h3 { display: flex; align-items: center; gap: 10px; color: #123f34; margin-bottom: 30px; font-size: 1.3rem; }
.progress-body { display: flex; align-items: center; gap: 60px; }

.percentage-wrap { display: flex; flex-direction: column; align-items: center; }
.percentage-value { font-size: 2.5rem; font-weight: 900; color: #123f34; }
.percentage-label { font-size: 0.9rem; color: #6e7a74; font-weight: 600; text-transform: uppercase; }

.progress-details { display: flex; flex-direction: column; gap: 20px; }
.detail-item { display: flex; align-items: center; gap: 15px; background: #f8f9f9; padding: 15px 25px; border-radius: 16px; min-width: 250px;}
.dot { width: 12px; height: 12px; border-radius: 50%; }
.dot.bg-gray { background: #cbd5e1; }
.d-text { display: flex; flex-direction: column; gap: 5px; }
.d-text span { font-size: 0.85rem; color: #6e7a74; font-weight: 600; }
.d-text strong { font-size: 1.2rem; color: #123f34; font-weight: 800; }

@media (max-width: 768px) {
  .progress-body { flex-direction: column; gap: 30px; text-align: center; }
  .detail-item { justify-content: center; }
}
</style>