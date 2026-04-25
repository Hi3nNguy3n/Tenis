<script setup>
import { ref, onMounted } from 'vue'
import { Refresh, CreditCard, Search, Document, Trophy, User } from '@element-plus/icons-vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import { t } from '../../utils/locale'

const payments = ref([])
const tournaments = ref([])
const loading = ref(false)

// Biến cho bộ lọc
const searchQuery = ref('')
const filterTournament = ref(null)

const fetchTournaments = async () => {
  try {
    tournaments.value = await apiClient.get('/api/tournaments?limit=100')
  } catch (err) {}
}

const fetchPayments = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterTournament.value !== null && filterTournament.value !== '') params.tournament_id = filterTournament.value
    if (searchQuery.value) params.search = searchQuery.value
    
    payments.value = await apiClient.get('/api/payments/list', { params })
  } catch (err) {
    ElMessage.error(t('admin.loadPaymentsError') + err.message)
  } finally {
    loading.value = false
  }
}

const getStatusType = (status) => {
  const s = status?.toLowerCase()
  if (s === 'completed' || s === 'success') return 'success'
  if (s === 'failed' || s === 'error') return 'danger'
  return 'warning'
}

const isExporting = ref(false)
const handleExport = () => {
  if (payments.value.length === 0) return ElMessage.warning(t('admin.noDataToExport'))
  isExporting.value = true
  
  try {
    const headers = ['ID', 'Mã Giao Dịch', 'Người Nộp', 'Nội Dung', 'Mã Đơn', 'Số Tiền', 'Phương Thức', 'Trạng Thái', 'Ngày Thanh Toán']
    const rows = payments.value.map(p => [
      p.id,
      p.transaction_ref,
      `"${p.payer_name}"`, // Bọc ngoặc kép để tránh lỗi dấu phẩy trong tên
      `"${p.tournament_name}"`,
      p.registration_id,
      p.amount,
      p.payment_method,
      p.status,
      p.paid_at ? new Date(p.paid_at).toLocaleString('vi-VN') : 'N/A'
    ])

    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `BaoCao_ThanhToan_${new Date().toLocaleDateString('vi-VN').replace(/\//g, '-')}.csv`
    link.click()
    ElMessage.success(t('admin.exportSuccess'))
  } catch (err) {
    ElMessage.error(t('admin.exportError') + err.message)
  } finally {
    isExporting.value = false
  }
}

onMounted(() => {
  fetchTournaments()
  fetchPayments()
})
</script>

<template>
  <div class="module-shell">
    <section class="action-bar-glass shadow-sm">
      <div class="action-info">
        <div class="kicker-wrap">
          <span class="section-kicker">{{ $t('admin.financialOversight') }}</span>
          <div class="live-indicator"><span class="dot"></span>LIVE</div>
        </div>
        <p>{{ $t('admin.financialOversightDesc') }}</p>
      </div>
      
      <div class="filter-area">
        <el-input 
          v-model="searchQuery" 
          :placeholder="$t('admin.searchPaymentPlaceholder')" 
          clearable 
          :prefix-icon="Search"
          @clear="fetchPayments"
          @keyup.enter="fetchPayments"
          style="width: 280px"
        />
        <el-select v-model="filterTournament" :placeholder="$t('admin.allTournaments')" clearable @change="fetchPayments" style="width: 250px">
          <el-option :label="$t('admin.friendlyFee')" :value="0" />
          <el-option v-for="t in tournaments" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        
        <el-button :icon="Refresh" circle @click="fetchPayments" />
        <el-button type="primary" round :loading="isExporting" @click="handleExport" class="btn-export">
          {{ $t('admin.exportCsvBtn') }}
        </el-button>
      </div>
    </section>

    <section class="table-card-premium shadow-sm">
      <el-table :data="payments" stripe v-loading="loading" class="modern-finance-table">
        
        <el-table-column :label="$t('admin.transactionCol')" width="180">
          <template #default="{ row }">
            <div class="tx-cell">
              <span class="tx-ref">{{ row.transaction_ref }}</span>
              <span class="reg-id">Order #{{ row.registration_id }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.payerCol')" min-width="180">
          <template #default="{ row }">
            <div class="info-cell">
              <el-icon class="info-icon"><User /></el-icon>
              <span class="payer-name">{{ row.payer_name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.contentCol')" min-width="220">
          <template #default="{ row }">
            <div class="info-cell">
              <el-icon class="info-icon"><Trophy /></el-icon>
              <span class="tour-name">{{ row.tournament_name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.amountCol')" width="150" align="right">
           <template #default="{ row }">
             <div class="amount-cell">
               {{ new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(row.amount) }}
             </div>
           </template>
        </el-table-column>

        <el-table-column :label="$t('admin.statusCol')" width="130" align="center">
           <template #default="{ row }">
             <el-tag :type="getStatusType(row.status)" effect="light" class="status-pill">
               {{ row.status?.toUpperCase() }}
             </el-tag>
           </template>
        </el-table-column>

        <el-table-column :label="$t('admin.timeCol')" min-width="140" align="right">
           <template #default="{ row }">
             <div class="time-vertical" v-if="row.paid_at">
               <span class="d-val">{{ new Date(row.paid_at).toLocaleDateString('vi-VN') }}</span>
               <span class="t-val">{{ new Date(row.paid_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) }}</span>
             </div>
             <span v-else>N/A</span>
           </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="payments.length === 0" :description="$t('admin.noPaymentData')" />
    </section>
  </div>
</template>

<style scoped>
.module-shell { display: grid; gap: 16px; padding: 10px; }

.action-bar-glass {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  padding: 16px 24px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 10px 30px rgba(0,0,0,0.03);
}

.kicker-wrap { display: flex; align-items: center; gap: 12px; margin-bottom: 2px; }
.section-kicker { font-size: 0.7rem; font-weight: 800; color: #1e293b; text-transform: uppercase; letter-spacing: 0.05em; }

.live-indicator {
  display: flex; align-items: center; gap: 6px;
  background: #f0fdf4; color: #15803d; font-size: 0.65rem; font-weight: 800;
  padding: 2px 8px; border-radius: 99px;
}
.dot { width: 6px; height: 6px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite; }

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}

.action-info p { color: #64748b; font-size: 0.9rem; margin: 0; }

.filter-area { display: flex; align-items: center; gap: 12px; }
.btn-export {
  background: linear-gradient(135deg, #10b981, #059669);
  border: none;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
}

.table-card-premium {
  background: white; padding: 8px; border-radius: 20px;
  border: 1px solid #f1f5f9; box-shadow: 0 10px 30px rgba(0,0,0,0.03);
  overflow: hidden;
}

.tx-cell { display: flex; flex-direction: column; gap: 2px; }
.tx-ref { font-weight: 700; color: #0f172a; font-size: 0.85rem; font-family: monospace; }
.reg-id { font-size: 0.75rem; color: #94a3b8; font-weight: 600; }

.info-cell { display: flex; align-items: center; gap: 8px; }
.info-icon { color: #3b82f6; font-size: 1.1rem; }
.payer-name { font-weight: 700; color: #1e293b; font-size: 0.9rem; }
.tour-name { font-weight: 600; color: #475569; font-size: 0.85rem; }

.amount-cell { font-weight: 900; color: #10b981; font-size: 1rem; }

.status-pill { font-weight: 800; border-radius: 99px; padding: 0 16px; font-size: 0.65rem; border: none !important; }

.time-vertical { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.d-val { font-size: 0.85rem; color: #64748b; font-weight: 600; }
.t-val { font-size: 0.8rem; color: #94a3b8; font-weight: 700; }

:deep(.el-table) { border-radius: 12px; }
:deep(.el-table .cell) { padding: 12px 16px; }

.shadow-sm { box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
</style>