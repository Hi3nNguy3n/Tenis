<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiClient from '../../services/apiClient'
import { 
  Search, Refresh, Check, Close, 
  User, Trophy, Tickets, Timer, 
  CircleCheckFilled, CircleCloseFilled, Filter,
  Clock, DataAnalysis, Calendar as CalendarIcon,
  Lock, Unlock, Checked, MoreFilled,
  Delete, Edit, Loading
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
    const res = await apiClient.get('/api/registrations/')
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
  { label: 'TẤT CẢ TRẠNG THÁI', value: '' },
  { label: 'CHỜ DUYỆT', value: 'pending' },
  { label: 'CHƯA THANH TOÁN', value: 'unpaid' },
  { label: 'ĐÃ THANH TOÁN', value: 'paid' },
  { label: 'ĐÃ CHECK-IN', value: 'checked_in' },
  { label: 'ĐÃ HỦY / TỪ CHỐI', value: 'cancelled_rejected' }
]

const translateStatus = (status, row = {}) => {
  if (row.is_locked) return 'ĐÃ KHÓA'
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
  ElMessageBox.confirm(t('admin.cancelRegConfirm'), t('admin.action') || 'Xác nhận', {
    type: 'warning',
    confirmButtonText: t('admin.confirm'),
    cancelButtonText: t('admin.cancel'),
  }).then(async () => {
    try {
      await apiClient.delete(`/api/registrations/${id}`) 
      ElMessage.success(t('admin.cancelSuccess'))
      loadRegistrations()
    } catch (err) {
      ElMessage.error(t('admin.updateError') + ': ' + (err.response?.data?.detail || err.message))
    }
  })
}

const lockRegistration = async (id) => {
  try {
    await apiClient.post(`/api/registrations/${id}/lock`)
    ElMessage.success('Khóa vận động viên thành công!')
    loadRegistrations()
  } catch (err) {
    ElMessage.error('Lỗi khi khóa: ' + (err.response?.data?.detail || err.message))
  }
}

const unlockRegistration = async (id) => {
  try {
    await apiClient.post(`/api/registrations/${id}/unlock`)
    ElMessage.success('Mở khóa vận động viên thành công!')
    loadRegistrations()
  } catch (err) {
    ElMessage.error('Lỗi khi mở khóa: ' + (err.response?.data?.detail || err.message))
  }
}

const checkInRegistration = async (row) => {
  const isPaid = (row.payment_status || '').toLowerCase() === 'paid'
  
  if (isPaid) {
    ElMessageBox.confirm(t('admin.confirmCheckInPaid'), t('admin.checkInDirectTitle') || 'Xác nhận Check-in', {
      type: 'success',
      confirmButtonText: t('admin.confirm') || 'Đồng ý',
      cancelButtonText: t('admin.cancel') || 'Hủy',
    }).then(async () => {
      try {
        await apiClient.post(`/api/registrations/${row.id}/check-in`)
        ElMessage.success(t('admin.checkInSuccess') || 'Check-in thành công!')
        loadRegistrations()
      } catch (err) {
        ElMessage.error(t('admin.updateError') + ': ' + (err.response?.data?.detail || err.message))
      }
    })
  } else {
    ElMessageBox.prompt(
      t('admin.confirmCheckInUnpaid'),
      t('admin.checkInDirectTitle') || 'Xác nhận Check-in',
      {
        confirmButtonText: t('admin.confirm') || 'Đồng ý',
        cancelButtonText: t('admin.cancel') || 'Hủy',
        inputPlaceholder: 'Nhập ghi chú thanh toán (không bắt buộc)...',
      }
    ).then(async ({ value }) => {
      try {
        const notesParam = value ? value.trim() : ''
        await apiClient.post(`/api/registrations/${row.id}/pay-and-check-in`, null, {
          params: { notes: notesParam }
        })
        ElMessage.success(t('admin.payAndCheckInSuccess') || 'Thu tiền và Check-in thành công!')
        loadRegistrations()
      } catch (err) {
        ElMessage.error(t('admin.updateError') + ': ' + (err.response?.data?.detail || err.message))
      }
    })
  }
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
    const filter = statusFilter.value.toLowerCase()
    if (filter === 'pending') {
      result = result.filter(r => r.status?.toLowerCase() === 'pending')
    } else if (filter === 'unpaid') {
      // Chưa thanh toán: status không phải cancelled/rejected/expired và payment_status !== 'paid'
      result = result.filter(r => 
        !['cancelled', 'rejected', 'expired'].includes(r.status?.toLowerCase()) && 
        (r.payment_status || '').toLowerCase() !== 'paid'
      )
    } else if (filter === 'paid') {
      // Đã thanh toán: payment_status === 'paid' hoặc status === 'paid' (trừ khi checked_in)
      result = result.filter(r => (r.payment_status || '').toLowerCase() === 'paid' || r.status?.toLowerCase() === 'paid')
    } else if (filter === 'checked_in') {
      result = result.filter(r => r.status?.toLowerCase() === 'checked_in')
    } else if (filter === 'cancelled_rejected') {
      result = result.filter(r => ['cancelled', 'rejected', 'expired'].includes(r.status?.toLowerCase()))
    } else {
      result = result.filter(r => r.status?.toLowerCase() === filter)
    }
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

const getStatusType = (status, row = {}) => {
  if (row.is_locked) return 'info'
  const s = status?.toLowerCase()
  if (s === 'confirmed' || s === 'paid' || s === 'checked_in') return 'success'
  if (s === 'cancelled' || s === 'rejected') return 'danger'
  if (s === 'expired') return 'info'
  return 'warning'
}

const parseDate = (val) => {
  if (!val) return null
  
  let dateStr = val
  if (typeof val === 'string') {
    // Nếu là chuỗi thời gian chưa kèm timezone, tự động append 'Z' (giờ UTC)
    // giúp trình duyệt ở Việt Nam (UTC+7) hiển thị đúng giờ Việt Nam (cộng thêm 7 tiếng).
    if (!val.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(val) && !/[+-]\d{4}$/.test(val)) {
      if (val.includes('T')) {
        dateStr = val + 'Z'
      } else if (/^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}/.test(val)) {
        dateStr = val.replace(' ', 'T') + 'Z'
      }
    }
  }
  
  const d = new Date(dateStr)
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
// Delete registration
const deleteRegistration = (id) => {
  ElMessageBox.confirm('Bạn có chắc chắn muốn xóa đăng ký này khỏi danh sách? Hành động này sẽ không thể khôi phục.', 'Xác nhận xóa', {
    type: 'warning',
    confirmButtonText: 'Xóa',
    cancelButtonText: 'Hủy',
  }).then(async () => {
    try {
      await apiClient.delete(`/api/registrations/${id}/delete`)
      ElMessage.success('Xóa đăng ký khỏi danh sách thành công!')
      loadRegistrations()
    } catch (err) {
      ElMessage.error('Lỗi khi xóa đăng ký: ' + (err.response?.data?.detail || err.message))
    }
  })
}

// Edit category logic
const editDialogVisible = ref(false)
const isSavingEdit = ref(false)
const currentEditRow = ref(null)
const tournamentCategories = ref([])
const editForm = ref({
  category_id: null,
  partner_player_id: null,
  partner_name: ''
})
const selectedPartner = ref(null)
const partnerSearchLoading = ref(false)

const editIsDoubles = computed(() => {
  if (!editForm.value.category_id || !tournamentCategories.value.length) return false
  const cat = tournamentCategories.value.find(c => c.id === editForm.value.category_id)
  return cat?.category_type?.toLowerCase()?.includes('doubles') || false
})

const openEditDialog = async (row) => {
  currentEditRow.value = row
  editDialogVisible.value = true
  tournamentCategories.value = []
  
  editForm.value = {
    category_id: row.category_id,
    partner_player_id: row.partner_player_id || null,
    partner_name: row.partner_name || ''
  }
  selectedPartner.value = row.partner_name ? { player_id: row.partner_player_id, full_name: row.partner_name } : null
  
  try {
    const res = await apiClient.get(`/api/tournaments/${row.tournament_id}`)
    tournamentCategories.value = res.categories || []
  } catch (err) {
    ElMessage.error('Không thể tải danh sách nội dung thi đấu: ' + err.message)
    editDialogVisible.value = false
  }
}

const querySearchPartner = async (queryString, cb) => {
  if (!queryString || queryString.length < 2) return cb([])
  partnerSearchLoading.value = true
  try {
    const res = await apiClient.get(`/api/players/search?keyword=${queryString}`)
    const filtered = res.filter(p => p.player_id !== currentEditRow.value.player_id)
    const results = filtered.map(p => ({
      value: p.full_name,
      player_id: p.player_id,
      full_name: p.full_name,
      phone: p.phone,
      avatar_url: p.avatar_url,
      level: p.level,
      gender: p.gender
    }))
    cb(results)
  } catch (err) {
    console.error(err)
    cb([])
  } finally {
    partnerSearchLoading.value = false
  }
}

const handleSelectPartner = (item) => {
  editForm.value.partner_player_id = item.player_id
  editForm.value.partner_name = item.full_name
  selectedPartner.value = item
}

const handlePartnerNameInput = () => {
  if (editForm.value.partner_player_id) {
    editForm.value.partner_player_id = null
    selectedPartner.value = null
  }
}

const submitEditCategory = async () => {
  if (!editForm.value.category_id) {
    return ElMessage.warning('Vui lòng chọn nội dung thi đấu.')
  }
  
  if (editIsDoubles.value && !editForm.value.partner_player_id) {
    return ElMessage.warning('Vui lòng chọn đồng đội cho nội dung đánh đôi.')
  }
  
  isSavingEdit.value = true
  try {
    const payload = {
      category_id: editForm.value.category_id,
      partner_player_id: editIsDoubles.value ? editForm.value.partner_player_id : null
    }
    await apiClient.put(`/api/registrations/${currentEditRow.value.id}/change-category`, payload)
    ElMessage.success('Đã cập nhật nội dung thi đấu thành công!')
    editDialogVisible.value = false
    loadRegistrations()
  } catch (err) {
    ElMessage.error('Lỗi khi cập nhật nội dung thi đấu: ' + (err.response?.data?.detail || err.message))
  } finally {
    isSavingEdit.value = false
  }
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
            <div class="status-indicator" :class="[`is-${getStatusType(row.status, row)}`, { 'is-waiting-payment': row.status === 'confirmed' && row.payment_status === 'pending' && !row.is_locked }]">
              <span class="dot"></span>
              <span>{{ translateStatus(row.status, row) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="THAO TÁC" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-dropdown trigger="click">
              <el-button size="small" circle class="more-actions-btn">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu class="saas-dropdown-menu">
                  <!-- Duyệt (Xác nhận) -->
                  <el-dropdown-item 
                    v-if="['pending', 'waiting', 'confirmed', 'rejected'].includes((row.status || '').toLowerCase()) && (row.payment_status || '').toLowerCase() !== 'paid' && !row.is_locked"
                    @click="confirmRegistration(row.id)"
                  >
                    <el-icon color="#10b981"><Check /></el-icon>
                    <span>Duyệt đăng ký</span>
                  </el-dropdown-item>
                  
                  <!-- Hủy (Từ chối) -->
                  <el-dropdown-item 
                    v-if="['pending', 'waiting', 'confirmed'].includes((row.status || '').toLowerCase()) && (row.payment_status || '').toLowerCase() !== 'paid' && !row.is_locked"
                    @click="cancelRegistration(row.id)"
                  >
                    <el-icon color="#ef4444"><Close /></el-icon>
                    <span>Từ chối / Hủy</span>
                  </el-dropdown-item>

                  <!-- Check-in trực tiếp -->
                  <el-dropdown-item 
                    v-if="!['checked_in', 'cancelled', 'expired'].includes((row.status || '').toLowerCase()) && !row.is_locked"
                    @click="checkInRegistration(row)"
                  >
                    <el-icon color="#3b82f6"><Checked /></el-icon>
                    <span>Check-in / Thu tiền</span>
                  </el-dropdown-item>

                  <!-- Chỉnh sửa nội dung -->
                  <el-dropdown-item 
                    v-if="!row.is_locked"
                    @click="openEditDialog(row)"
                  >
                    <el-icon color="#3b82f6"><Edit /></el-icon>
                    <span>Đổi nội dung thi đấu</span>
                  </el-dropdown-item>

                  <!-- Khóa / Mở khóa -->
                  <template v-if="!['cancelled', 'rejected', 'expired'].includes((row.status || '').toLowerCase())">
                    <el-dropdown-item
                      v-if="!row.is_locked"
                      @click="lockRegistration(row.id)"
                    >
                      <el-icon color="#f59e0b"><Lock /></el-icon>
                      <span>Khóa VĐV</span>
                    </el-dropdown-item>
                    <el-dropdown-item
                      v-else
                      @click="unlockRegistration(row.id)"
                    >
                      <el-icon color="#6b7280"><Unlock /></el-icon>
                      <span>Mở khóa VĐV</span>
                    </el-dropdown-item>
                  </template>

                  <!-- Xóa đăng ký -->
                  <el-dropdown-item 
                    divided
                    class="danger-item"
                    @click="deleteRegistration(row.id)"
                  >
                    <el-icon color="#ef4444"><Delete /></el-icon>
                    <span>Xóa khỏi danh sách</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
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

    <!-- Dialog chỉnh sửa nội dung thi đấu -->
    <el-dialog
      v-model="editDialogVisible"
      title="Chỉnh sửa nội dung thi đấu"
      width="500px"
      destroy-on-close
      append-to-body
    >
      <el-form label-position="top">
        <el-form-item label="Nội dung thi đấu" required>
          <el-select v-model="editForm.category_id" style="width: 100%" placeholder="Chọn nội dung">
            <el-option
              v-for="cat in tournamentCategories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>

        <!-- Nếu là đánh đôi, hiện chọn đồng đội -->
        <el-form-item v-if="editIsDoubles" label="Đồng đội" required>
          <div v-if="selectedPartner" class="partner-selected-box">
            <el-avatar :size="32" :src="selectedPartner.avatar_url || '/default-avatar.png'" style="margin-right: 8px;" />
            <div class="partner-info">
              <div class="partner-name">{{ selectedPartner.full_name }}</div>
              <div class="partner-meta">SĐT: {{ selectedPartner.phone || 'N/A' }} | Trình độ: {{ selectedPartner.level || 'N/A' }}</div>
            </div>
            <el-button type="danger" size="small" circle icon="Close" @click="handlePartnerNameInput" />
          </div>
          <el-autocomplete
            v-else
            v-model="editForm.partner_name"
            :fetch-suggestions="querySearchPartner"
            placeholder="Nhập tên hoặc SĐT tìm đồng đội..."
            @select="handleSelectPartner"
            style="width: 100%"
          >
            <template #suffix>
              <el-icon v-if="partnerSearchLoading"><Loading /></el-icon>
              <el-icon v-else><Search /></el-icon>
            </template>
            <template #default="{ item }">
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-avatar :size="24" :src="item.avatar_url || '/default-avatar.png'" />
                <div>
                  <div style="font-weight: bold; font-size: 0.85rem;">{{ item.full_name }}</div>
                  <div style="font-size: 0.75rem; color: #64748b;">{{ item.phone }} ({{ item.level || 'N/A' }} pts)</div>
                </div>
              </div>
            </template>
          </el-autocomplete>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">Hủy</el-button>
          <el-button type="primary" :loading="isSavingEdit" @click="submitEditCategory">Lưu thay đổi</el-button>
        </span>
      </template>
    </el-dialog>
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

.more-actions-btn {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  color: #64748b !important;
  transition: all 0.2s ease;
}
.more-actions-btn:hover {
  background: #f1f5f9 !important;
  color: #0f172a !important;
  border-color: #cbd5e1 !important;
}

:deep(.saas-dropdown-menu) {
  padding: 6px !important;
  border-radius: 12px !important;
  border: 1px solid #f1f5f9 !important;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05) !important;
}

:deep(.el-dropdown-menu__item) {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  padding: 8px 16px !important;
  font-size: 0.8rem !important;
  font-weight: 700 !important;
  color: #475569 !important;
  border-radius: 8px !important;
  margin: 2px 0 !important;
  transition: all 0.15s ease !important;
}

:deep(.el-dropdown-menu__item:hover) {
  background-color: #f1f5f9 !important;
  color: #0f172a !important;
}

:deep(.el-dropdown-menu__item.danger-item) {
  color: #ef4444 !important;
}

:deep(.el-dropdown-menu__item.danger-item:hover) {
  background-color: #fef2f2 !important;
  color: #dc2626 !important;
}
.partner-selected-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  padding: 10px 14px;
  border-radius: 8px;
  width: 100%;
}
.partner-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.partner-name {
  font-weight: bold;
  font-size: 0.85rem;
  color: #0f172a;
}
.partner-meta {
  font-size: 0.75rem;
  color: #64748b;
}
</style>
