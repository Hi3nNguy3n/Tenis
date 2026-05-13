<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiClient from '../../services/apiClient'
import { 
  Search, Refresh, Check, Close, 
  User, Trophy, Tickets, Timer, 
  CircleCheckFilled, CircleCloseFilled, Filter,
  Clock, DataAnalysis, Calendar as CalendarIcon
} from '@element-plus/icons-vue'
import { t } from '../../utils/locale'
import { useRoute } from 'vue-router'

const route = useRoute()
const registrations = ref([])
const isLoading = ref(false)
const search = ref('')
const statusFilter = ref('')

// Pagination
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const stats = computed(() => {
  return {
    total: registrations.value.length,
    pending: registrations.value.filter(r => r.status?.toLowerCase() === 'pending').length,
    confirmed: registrations.value.filter(r => ['confirmed', 'paid'].includes(r.status?.toLowerCase())).length,
    cancelled: registrations.value.filter(r => ['cancelled', 'rejected', 'expired'].includes(r.status?.toLowerCase())).length
  }
})

const loadRegistrations = async () => {
  isLoading.value = true
  try {
    const res = await apiClient.get('/api/registrations')
    const data = Array.isArray(res) ? res : (res.data || [])
    
    registrations.value = data.sort((a, b) => {
      const statusA = (a.status || '').toLowerCase()
      const statusB = (b.status || '').toLowerCase()
      const psA = (a.payment_status || '').toLowerCase()
      const psB = (b.payment_status || '').toLowerCase()
      
      const isPendingA = statusA === 'pending' || (statusA === 'confirmed' && psA === 'pending')
      const isPendingB = statusB === 'pending' || (statusB === 'confirmed' && psB === 'pending')
      
      if (isPendingA && !isPendingB) return -1
      if (!isPendingA && isPendingB) return 1
      
      const dateA = new Date(a.registered_at || a.registration_date || a.created_at || 0)
      const dateB = new Date(b.registered_at || b.registration_date || b.created_at || 0)
      return dateB - dateA
    })
    
    total.value = registrations.value.length
  } catch (err) {
    ElMessage.error(t('admin.loadRegistrationsError'))
  } finally {
    isLoading.value = false
  }
}

const handlePageChange = (val) => {
  currentPage.value = val
}

const statusOptions = [
  { label: 'CHỜ XỬ LÝ', value: 'pending' },
  { label: 'ĐÃ XÁC NHẬN', value: 'confirmed' },
  { label: 'ĐÃ THANH TOÁN', value: 'paid' },
  { label: 'ĐÃ HỦY', value: 'cancelled' },
  { label: 'TỪ CHỐI', value: 'rejected' }
]

const translateStatus = (status, row = {}) => {
  if (!status) return 'KHÔNG XÁC ĐỊNH'
  const s = status.toLowerCase()
  const ps = (row.payment_status || '').toLowerCase()
  
  if (s === 'confirmed' && ps === 'pending') return 'CHỜ XÁC NHẬN'
  
  const map = {
    'confirmed': 'ĐÃ XÁC NHẬN',
    'paid': 'ĐÃ THANH TOÁN',
    'pending': 'CHỜ DUYỆT',
    'waiting': 'ĐANG CHỜ',
    'cancelled': 'ĐÃ HỦY',
    'rejected': 'TỪ CHỐI',
    'expired': 'HẾT HẠN',
    'checked_in': 'ĐÃ CHECK-IN'
  }
  return map[s] || status.toUpperCase()
}

const confirmRegistration = async (id) => {
  try {
    await apiClient.post(`/api/registrations/${id}/confirm`)
    ElMessage.success(t('admin.confirmSuccess'))
    loadRegistrations()
  } catch (err) {
    ElMessage.error(t('admin.updateError') + ': ' + (err.response?.data?.detail || err.message))
  }
}

const cancelRegistration = (id) => {
  ElMessageBox.confirm(t('admin.confirmCancelRegistration'), t('admin.action'), {
    type: 'warning',
    confirmButtonText: t('admin.confirm'),
    cancelButtonText: t('admin.cancel'),
  }).then(async () => {
    try {
      await apiClient.post(`/api/registrations/${id}/cancel`) 
      ElMessage.success(t('admin.cancelSuccess'))
      loadRegistrations()
    } catch (err) {
      ElMessage.error(t('admin.updateError') + ': ' + (err.response?.data?.detail || err.message))
    }
  })
}

onMounted(async () => {
  await loadRegistrations()
  const queryId = route.query.tournamentId
  if (queryId) {
    statusFilter.value = ''
  }
})

watch(() => route.fullPath, async () => {
  await loadRegistrations()
})

const filteredRows = computed(() => {
  let result = [...registrations.value]
  const queryId = route.query.tournamentId
  if (queryId) {
    result = result.filter(r => String(r.tournament_id) === String(queryId))
  }

  if (search.value) {
    const s = search.value.toLowerCase().trim()
    result = result.filter(r => 
      (r.player_name || '').toLowerCase().includes(s) || 
      (r.tournament_name || '').toLowerCase().includes(s)
    )
  }
  if (statusFilter.value) {
    result = result.filter(r => r.status?.toLowerCase() === statusFilter.value.toLowerCase())
  }
  return result
})

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredRows.value.slice(start, end)
})

watch([search, statusFilter], () => {
  currentPage.value = 1
})

const getStatusType = (status) => {
  const s = status?.toLowerCase()
  if (s === 'confirmed' || s === 'paid' || s === 'checked_in') return 'success'
  if (s === 'cancelled' || s === 'rejected') return 'danger'
  if (s === 'expired') return 'info'
  return 'warning'
}

const formatDateTime = (val) => {
  if (!val) return 'N/A'
  return new Date(val).toLocaleString('vi-VN', {
    hour: '2-digit', minute: '2-digit',
    day: '2-digit', month: '2-digit', year: 'numeric'
  })
}
</script>

<template>
  <div class="saas-container">
    <!-- Stats Row -->
    <div class="saas-stats-grid">
      <div class="saas-stat-card">
        <div class="stat-icon p-blue"><el-icon><Tickets /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">TỔNG ĐƠN ĐĂNG KÝ</span>
          <h3 class="stat-value">{{ stats.total }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-orange"><el-icon><Clock /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">ĐANG CHỜ XỬ LÝ</span>
          <h3 class="stat-value">{{ stats.pending }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-green"><el-icon><CircleCheckFilled /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">ĐÃ XÁC NHẬN</span>
          <h3 class="stat-value">{{ stats.confirmed }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-red"><el-icon><CircleCloseFilled /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">ĐÃ HỦY / TỪ CHỐI</span>
          <h3 class="stat-value">{{ stats.cancelled }}</h3>
        </div>
      </div>
    </div>

    <!-- Header & Action Bar -->
    <div class="saas-header">
      <div class="header-left">
        <el-input 
          v-model="search" 
          :placeholder="$t('admin.searchTournamentPlaceholder')" 
          clearable 
          class="saas-search"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        
        <el-select v-model="statusFilter" placeholder="TẤT CẢ TRẠNG THÁI" clearable class="saas-filter">
          <template #prefix><el-icon><Filter /></el-icon></template>
          <el-option v-for="opt in statusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>

        <el-button circle @click="loadRegistrations" class="saas-icon-btn">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- Data Table Section -->
    <div class="saas-content">
      <el-table 
        :data="pagedRows" 
        v-loading="isLoading" 
        class="saas-table"
        :header-cell-style="{ background: 'transparent', color: '#1e293b', fontWeight: '800', borderBottom: '2px solid #e2e8f0' }"
      >
        <el-table-column label="VẬN ĐỘNG VIÊN" min-width="260">
          <template #default="{ row }">
            <div class="saas-premium-cell">
              <div class="icon-box-premium p-blue"><el-icon><User /></el-icon></div>
              <div class="cell-meta">
                <span class="cell-title">{{ row.player_name }}</span>
                <span class="cell-subtitle">ID: #{{ row.player_id || '---' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="GIẢI ĐẤU" min-width="260">
          <template #default="{ row }">
            <div class="saas-premium-cell">
              <div class="icon-box-premium p-orange"><el-icon><Trophy /></el-icon></div>
              <div class="cell-meta">
                <span class="cell-title">{{ row.tournament_name }}</span>
                <span class="cell-subtitle">{{ row.category_type || 'N/A' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="THỜI GIAN ĐĂNG KÝ" width="220" align="right">
          <template #default="{ row }">
            <div class="time-premium">
              <div class="time-row">
                <el-icon><CalendarIcon /></el-icon>
                <span>{{ new Date(row.registration_date || row.created_at).toLocaleDateString('vi-VN') }}</span>
              </div>
              <div class="time-row sub">
                <el-icon><Timer /></el-icon>
                <span>{{ new Date(row.registration_date || row.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="TRẠNG THÁI" width="180" align="center">
          <template #default="{ row }">
            <div class="status-indicator" :class="[`is-${getStatusType(row.status)}`, { 'is-waiting-payment': row.status === 'confirmed' && row.payment_status === 'pending' }]">
              <span class="dot"></span>
              <span>{{ translateStatus(row.status, row) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="THAO TÁC" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <div class="saas-row-actions-prominent" v-if="['pending', 'waiting', 'confirmed'].includes((row.status || '').toLowerCase()) && (row.payment_status || '').toLowerCase() !== 'paid'">
              <el-button 
                type="success" 
                @click="confirmRegistration(row.id)" 
                class="prominent-btn confirm"
              >
                <el-icon class="mr-1"><Check /></el-icon> DUYỆT
              </el-button>
              
              <el-button 
                type="danger" 
                plain 
                @click="cancelRegistration(row.id)" 
                class="prominent-btn cancel"
              >
                <el-icon class="mr-1"><Close /></el-icon> HỦY
              </el-button>
            </div>
            <div v-else class="done-label">
              <el-icon v-if="['confirmed', 'paid', 'checked_in'].includes((row.status || '').toLowerCase())" color="#059669"><CircleCheckFilled /></el-icon>
              <el-icon v-else color="#dc2626"><CircleCloseFilled /></el-icon>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="saas-pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.saas-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
  min-height: 100%;
}

/* Stats Grid */
.saas-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

.saas-stat-card {
  background: #fff;
  border: 1px solid #f1f5f9;
  border-radius: 24px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
}

.saas-stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.05);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.p-blue { background: #eff6ff; color: #3b82f6; }
.p-green { background: #ecfdf5; color: #10b981; }
.p-orange { background: #fff7ed; color: #f97316; }
.p-red { background: #fef2f2; color: #ef4444; }

.stat-label { font-size: 0.75rem; color: #64748b; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; }
.stat-value { margin: 4px 0 0; font-size: 1.8rem; font-weight: 800; color: #0f172a; }

/* Header & Action Bar */
.saas-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.saas-search { width: 320px; }
.saas-filter { width: 220px; }

:deep(.el-input__wrapper), :deep(.el-select__wrapper) {
  background-color: #f8fafc !important;
  box-shadow: none !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 12px !important;
  padding: 8px 12px !important;
}

.saas-icon-btn {
  width: 44px; height: 44px; border-radius: 12px !important;
  background: #f8fafc !important; border: 1px solid #e2e8f0 !important;
}

/* Table Section */
.saas-content {
  background: #fff;
  border-radius: 24px;
  border: 1px solid #f1f5f9;
  padding: 8px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.03);
}

.saas-table {
  background: transparent !important;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
}

.saas-premium-cell {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-box-premium {
  width: 48px; height: 48px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; border: 1px solid #e2e8f0;
}

.cell-meta { display: flex; flex-direction: column; gap: 2px; }
.cell-title { font-weight: 800; color: #0f172a; font-size: 0.95rem; }
.cell-subtitle { font-size: 0.8rem; color: #64748b; font-weight: 600; }

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 800;
}

.is-success { background: #ecfdf5; color: #059669; }
.is-warning, .is-waiting-payment { background: #fffbeb; color: #d97706; }
.is-danger { background: #fef2f2; color: #dc2626; }
.is-info { background: #f1f5f9; color: #475569; }

.status-indicator .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.is-success .dot, .is-warning .dot, .is-waiting-payment .dot { animation: pulse 2s infinite; }

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.saas-row-actions-prominent { display: flex; gap: 12px; justify-content: center; }

.prominent-btn {
  border-radius: 10px !important;
  font-weight: 800 !important;
  padding: 10px 18px !important;
  transition: all 0.2s !important;
}

.prominent-btn.confirm { box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2); }
.prominent-btn.confirm:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(5, 150, 105, 0.3); }
.prominent-btn.cancel:hover { transform: translateY(-2px); }

.done-label { font-size: 24px; display: flex; justify-content: center; opacity: 0.8; }

.time-premium { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.time-row { display: flex; align-items: center; gap: 6px; font-size: 0.85rem; color: #1e293b; font-weight: 700; }
.time-row.sub { font-size: 0.8rem; color: #64748b; font-weight: 600; }

.saas-pagination { margin-top: 24px; padding: 12px; display: flex; justify-content: center; }

.mr-1 { margin-right: 4px; }

@media (max-width: 768px) {
  .saas-stats-grid { grid-template-columns: 1fr 1fr; }
  .saas-header { flex-direction: column; align-items: stretch; }
  .saas-search { width: 100%; }
}
</style>
