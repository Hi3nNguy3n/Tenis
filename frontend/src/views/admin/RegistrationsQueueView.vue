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

const parseDate = (val) => {
  if (!val) return null
  const d = new Date(val)
  if (!isNaN(d.getTime())) return d
  if (typeof val === 'string' && val.includes('/')) {
    const p = val.split(/[\/\s:]/)
    if (p.length >= 3) {
      const d2 = new Date(p[2], p[1]-1, p[0])
      if (!isNaN(d2.getTime())) return d2
    }
  }
  return null
}

const formatDate = (val) => {
  const d = parseDate(val)
  return d ? d.toLocaleDateString('vi-VN') : '---'
}

const formatTime = (val) => {
  const d = parseDate(val)
  return d ? d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : '---'
}
</script>

<template>
  <div class="saas-container">
    <div class="saas-stats-grid compact">
      <div class="saas-stat-card">
        <div class="stat-icon p-blue small"><el-icon><Tickets /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">TỔNG ĐƠN</span>
          <h3 class="stat-value small">{{ stats.total }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-orange small"><el-icon><Clock /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">CHỜ XỬ LÝ</span>
          <h3 class="stat-value small">{{ stats.pending }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-green small"><el-icon><CircleCheckFilled /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">XÁC NHẬN</span>
          <h3 class="stat-value small">{{ stats.confirmed }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-red small"><el-icon><CircleCloseFilled /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">HỦY/TỪ CHỐI</span>
          <h3 class="stat-value small">{{ stats.cancelled }}</h3>
        </div>
      </div>
    </div>

    <!-- Header & Action Bar -->
    <div class="saas-header compact">
      <div class="header-left">
        <el-input 
          v-model="search" 
          :placeholder="$t('admin.searchTournamentPlaceholder')" 
          clearable 
          size="small"
          class="saas-search"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        
        <el-select v-model="statusFilter" placeholder="TRẠNG THÁI" clearable size="small" class="saas-filter">
          <template #prefix><el-icon><Filter /></el-icon></template>
          <el-option v-for="opt in statusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>
        
        <el-button circle @click="loadRegistrations" size="small" class="saas-icon-btn">
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
        <el-table-column label="VẬN ĐỘNG VIÊN" min-width="200">
          <template #default="{ row }">
            <div class="saas-premium-cell">
              <div class="icon-box-premium p-blue"><el-icon><User /></el-icon></div>
              <div class="cell-meta">
                <span class="cell-title">{{ row.player_name }}</span>
                <span v-if="row.partner_name" class="cell-title" style="color: var(--blue-accent); font-size: 0.8rem;">
                  + {{ row.partner_name }}
                </span>
                <span class="cell-subtitle">ID: #{{ row.player_id || '---' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="GIẢI ĐẤU" min-width="200">
          <template #default="{ row }">
            <div class="saas-premium-cell">
              <div class="icon-box-premium p-orange"><el-icon><Trophy /></el-icon></div>
              <div class="cell-meta">
                <span class="cell-title">{{ row.tournament_name }}</span>
                <span class="cell-subtitle">{{ row.category_name || row.category_type || 'N/A' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="THỜI GIAN" width="140" align="right">
          <template #default="{ row }">
            <div class="time-premium compact">
              <div class="time-row">
                <el-icon size="12"><CalendarIcon /></el-icon>
                <span>{{ formatDate(row.registration_date || row.registered_at || row.created_at) }}</span>
              </div>
              <div class="time-row sub">
                <el-icon size="12"><Timer /></el-icon>
                <span>{{ formatTime(row.registration_date || row.registered_at || row.created_at) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="TRẠNG THÁI" width="140" align="center">
          <template #default="{ row }">
            <div class="status-indicator" :class="[`is-${getStatusType(row.status)}`, { 'is-waiting-payment': row.status === 'confirmed' && row.payment_status === 'pending' }]">
              <span class="dot"></span>
              <span>{{ translateStatus(row.status, row) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="THAO TÁC" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <div class="saas-row-actions-compact" v-if="['pending', 'waiting', 'confirmed'].includes((row.status || '').toLowerCase()) && (row.payment_status || '').toLowerCase() !== 'paid'">
              <el-button 
                type="success" 
                size="small"
                circle
                @click="confirmRegistration(row.id)" 
                class="compact-btn confirm"
                title="Xác nhận"
              >
                <el-icon><Check /></el-icon>
              </el-button>
              
              <el-button 
                type="danger" 
                size="small"
                circle
                plain 
                @click="cancelRegistration(row.id)" 
                class="compact-btn cancel"
                title="Hủy"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <div v-else class="done-label compact">
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
  gap: 20px;
  min-height: 100%;
}

.saas-stats-grid.compact { 
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px; 
}
.saas-stat-card { 
  background: #fff; 
  border: 1px solid #f1f5f9; 
  border-radius: 16px; 
  padding: 20px; 
  display: flex; 
  flex-direction: column;
  align-items: center; 
  justify-content: center;
  gap: 12px; 
  transition: all 0.3s ease; 
  box-shadow: 0 4px 12px rgba(0,0,0,0.02); 
  text-align: center;
}
.saas-stat-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.06); }
.stat-icon.small { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.stat-content { display: flex; flex-direction: column; align-items: center; }
.p-blue { background: #eff6ff; color: #3b82f6; }
.p-green { background: #ecfdf5; color: #10b981; }
.p-orange { background: #fff7ed; color: #f97316; }
.p-red { background: #fef2f2; color: #ef4444; }
.stat-value.small { margin: 4px 0 0; font-size: 1.4rem; font-weight: 800; color: #0f172a; }
.stat-label { font-size: 0.65rem; color: #64748b; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; }

/* Header & Action Bar */
.saas-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.header-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.saas-search { width: 240px; }
.saas-filter { width: 180px; }

:deep(.el-input__wrapper), :deep(.el-select__wrapper) {
  background-color: #f8fafc !important;
  box-shadow: none !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 8px !important;
  padding: 4px 10px !important;
}

.saas-icon-btn { width: 36px; height: 36px; border-radius: 8px !important; }

/* Table Section */
.saas-content { background: #fff; border-radius: 16px; border: 1px solid #f1f5f9; padding: 4px; box-shadow: 0 4px 20px rgba(0,0,0,0.02); overflow-x: auto; }
.saas-table { background: transparent !important; --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; font-size: 0.85rem; }
:deep(.el-table .cell) { padding: 8px 12px !important; }

.saas-premium-cell { display: flex; align-items: center; gap: 10px; }
.icon-box-premium { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 16px; border: 1px solid #e2e8f0; }
.cell-meta { display: flex; flex-direction: column; gap: 2px; }
.cell-title { font-weight: 800; color: #0f172a; font-size: 0.85rem; }
.cell-subtitle { font-size: 0.75rem; color: #64748b; font-weight: 600; }

.status-indicator { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 99px; font-size: 0.7rem; font-weight: 800; }
.is-success { background: #ecfdf5; color: #059669; }
.is-warning, .is-waiting-payment { background: #fffbeb; color: #d97706; }
.is-danger { background: #fef2f2; color: #dc2626; }
.is-info { background: #f1f5f9; color: #475569; }
.status-indicator .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.saas-row-actions-compact { display: flex; gap: 8px; justify-content: center; }
.compact-btn { width: 32px; height: 32px; padding: 0 !important; }
.done-label.compact { font-size: 20px; display: flex; justify-content: center; opacity: 0.8; }

.time-premium.compact { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.time-row { display: flex; align-items: center; gap: 4px; font-size: 0.75rem; color: #1e293b; font-weight: 700; }
.time-row.sub { font-size: 0.7rem; color: #64748b; font-weight: 600; }

.saas-pagination { margin-top: 16px; padding: 8px; display: flex; justify-content: center; }

@media (max-width: 1024px) {
  .saas-stats-grid.compact { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .saas-stats-grid.compact { grid-template-columns: 1fr; }
  .saas-header { flex-direction: column; align-items: stretch; }
  .saas-search, .saas-filter { width: 100%; }
}
</style>
