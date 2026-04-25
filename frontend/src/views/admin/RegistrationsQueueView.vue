<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Check, Close } from '@element-plus/icons-vue'
import { registrationService } from '../../services/registrationService'
import { apiClient } from '../../services/apiClient'
import { t } from '../../utils/locale'

const search = ref('')
const statusFilter = ref('')
const registrations = ref([])
const isLoading = ref(false)

const loadRegistrations = async () => {
  isLoading.value = true
  try {
    const data = await registrationService.getAll()
    registrations.value = Array.isArray(data) ? data : (data.items || [])
  } catch (err) {
    ElMessage.error(t('admin.loadRegistrationsError') + ': ' + err.message)
  } finally {
    isLoading.value = false
  }
}

const handleConfirm = (id) => {
  ElMessageBox.confirm(
    t('admin.confirmRegTitle'),
    t('admin.approveReg'),
    { 
      confirmButtonText: t('admin.approveNow'),
      cancelButtonText: t('admin.cancel'),
      type: 'success' 
    }
  ).then(async () => {
    try {
      await apiClient.post(`/api/registrations/${id}/confirm`)
      ElMessage.success(t('admin.approveSuccess'))
      loadRegistrations() 
    } catch (err) {
      ElMessage.error(t('admin.updateError') + ': ' + (err.response?.data?.detail || err.message))
    }
  })
}

const handleCancel = (id) => {
  ElMessageBox.confirm(t('admin.cancelRegConfirm'), t('admin.action'), { 
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

onMounted(loadRegistrations)

const getStatusType = (status) => {
  const s = status?.toLowerCase()
  if (s === 'confirmed' || s === 'paid' || s === 'checked_in') return 'success'
  if (s === 'cancelled' || s === 'rejected') return 'danger'
  if (s === 'expired') return 'info'
  return 'warning'
}

const filteredRows = computed(() => {
  let result = [...registrations.value]
  if (search.value) {
    const s = search.value.toLowerCase().trim()
    result = result.filter(r => 
      (r.player_name || '').toLowerCase().includes(s) || 
      (r.tournament_name || '').toLowerCase().includes(s)
    )
  }
  if (statusFilter.value) {
    result = result.filter(r => r.status === statusFilter.value)
  }
  return result
})

const dynamicStatusOptions = computed(() => {
  const statuses = Array.from(new Set(registrations.value.map(r => r.status)))
  return statuses.filter(Boolean).map(s => ({
    label: s.toUpperCase(),
    value: s
  }))
})

const resetFilters = () => {
  search.value = ''
  statusFilter.value = ''
  currentPage.value = 1
}

const currentPage = ref(1)
const pageSize = ref(10)

const paginatedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredRows.value.slice(start, end)
})

const handlePageChange = (val) => {
  currentPage.value = val
}
</script>

<template>
  <div class="module-shell">
    <section class="action-bar-glass shadow-sm">
      <div class="action-info">
        <div class="kicker-wrap">
          <span class="section-kicker">Registration Flow</span>
          <div class="live-indicator">
            <span class="dot"></span>
            LIVE
          </div>
        </div>
        <p>{{ $t('admin.registrationFlow') }}</p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" plain round @click="loadRegistrations" :icon="Refresh">{{ $t('admin.refreshData') }}</el-button>
      </div>
    </section>

    <section class="filter-card">
      <div class="filter-row">
        <el-input 
          v-model="search" 
          :placeholder="$t('admin.searchRegistrationsPlaceholder')" 
          clearable 
          class="search-input"
          :prefix-icon="Search"
          @input="currentPage = 1"
        />
        
        <el-select 
          v-model="statusFilter" 
          :placeholder="$t('admin.filterByStatus')" 
          clearable 
          class="status-select"
          @change="currentPage = 1"
        >
          <el-option 
            v-for="opt in dynamicStatusOptions" 
            :key="opt.value" 
            :label="opt.label" 
            :value="opt.value" 
          />
        </el-select>

        <el-button @click="resetFilters" plain>{{ $t('admin.refresh') }}</el-button>
      </div>
    </section>

    <section class="table-card shadow-sm">
      <el-table :data="paginatedRows" stripe v-loading="isLoading" table-layout="fixed">
        <el-table-column :label="$t('admin.player')" min-width="200">
           <template #default="{ row }">
             <div class="player-cell">
               <span class="player-name">{{ row.player_name || 'N/A' }}</span>
               <span class="player-sub">{{ row.registrant_type?.toUpperCase() }} / {{ row.player_skill || 'N/A' }}</span>
             </div>
           </template>
        </el-table-column>
        
        <el-table-column :label="$t('admin.tournament')" min-width="220">
           <template #default="{ row }">
             <div class="tournament-cell">
               <span class="tour-name">{{ row.tournament_name }}</span>
               <span class="tour-cat">{{ row.category_type }}</span>
             </div>
           </template>
        </el-table-column>

        <el-table-column :label="$t('admin.status')" width="140" align="center">
           <template #default="{ row }">
             <el-tag :type="getStatusType(row.status)" effect="light" class="status-tag">
               {{ row.status?.toUpperCase() }}
             </el-tag>
           </template>
        </el-table-column>

        <el-table-column :label="$t('admin.payment')" width="140">
           <template #default="{ row }">
             <div class="payment-cell">
                <el-tag :type="row.payment_status === 'paid' ? 'success' : 'info'" effect="dark">
                  {{ row.payment_status?.toUpperCase() }}
                </el-tag>
                <small v-if="row.entry_fee">{{ row.entry_fee.toLocaleString() }}đ</small>
             </div>
           </template>
        </el-table-column>

        <el-table-column :label="$t('admin.action')" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <div class="table-actions">
              <el-tooltip v-if="row.status === 'pending' || row.payment_status !== 'paid'" :content="$t('admin.approveReg')" placement="top">
                <el-button 
                  circle 
                  size="small" 
                  type="success" 
                  plain 
                  :icon="Check" 
                  @click.stop="handleConfirm(row.id)"
                />
              </el-tooltip>

              <el-tooltip v-if="row.status !== 'cancelled'" :content="$t('admin.cancel')" placement="top">
                <el-button 
                  circle 
                  size="small" 
                  type="danger" 
                  plain 
                  :icon="Close" 
                  @click.stop="handleCancel(row.id)"
                />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="filteredRows.length"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
          size="small"
        />
      </div>
    </section>
  </div>
</template>

<style scoped>
.module-shell { display: grid; gap: 16px; padding: 0 10px; }

.action-bar-glass {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  padding: 16px 20px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.02);
}

.kicker-wrap { display: flex; align-items: center; gap: 10px; margin-bottom: 2px; }
.section-kicker { font-size: 0.7rem; font-weight: 800; color: #15803d; text-transform: uppercase; letter-spacing: 0.08em; }

.live-indicator {
  display: flex; align-items: center; gap: 4px;
  background: #f0fdf4; color: #15803d; font-size: 0.6rem; font-weight: 800;
  padding: 1px 6px; border-radius: 99px;
}
.dot { width: 5px; height: 5px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite; }

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 5px rgba(34, 197, 94, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}

.action-info p { color: #64748b; font-size: 0.85rem; margin: 0; }

.filter-card {
  background: white; padding: 12px 20px; border-radius: 16px;
  border: 1px solid #f1f5f9; box-shadow: 0 2px 4px rgba(0,0,0,0.01);
}

.filter-row { display: flex; gap: 12px; }
.search-input { width: 320px; }
.status-select { width: 220px; }

.table-card {
  background: white; padding: 4px; border-radius: 16px;
  border: 1px solid #f1f5f9; box-shadow: 0 8px 24px rgba(0,0,0,0.02);
  overflow: hidden;
}

.pagination-container {
  padding: 10px 16px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #f8fafc;
}

:deep(.el-table) { border-radius: 10px; }
:deep(.el-table .cell) { padding: 8px 12px; }

.player-cell, .tournament-cell, .payment-cell { display: flex; flex-direction: column; gap: 1px; }
.player-name, .tour-name { font-weight: 700; color: #0f172a; font-size: 0.9rem; }
.player-sub, .tour-cat { font-size: 0.7rem; color: #94a3b8; font-family: 'Arial', sans-serif; }

.status-tag { 
  font-weight: 800; border-radius: 99px; padding: 0 12px; font-size: 0.65rem; height: 24px; line-height: 24px;
  border: none !important;
}

.payment-cell { align-items: flex-start; }
.payment-cell small { font-weight: 700; color: #1e293b; margin-top: 1px; font-size: 0.75rem; }

.table-actions { display: flex; gap: 8px; justify-content: center; }

.shadow-sm { box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
</style>
