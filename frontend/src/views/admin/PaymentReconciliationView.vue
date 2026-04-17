<script setup>
import { Refresh, CreditCard } from '@element-plus/icons-vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'

const payments = ref([])
const loading = ref(false)

const fetchPayments = async () => {
  loading.value = true
  try {
    const data = await apiClient.get('/api/payments/list')
    payments.value = data
  } catch (err) {
    ElMessage.error('Lỗi tải danh sách thanh toán: ' + err.message)
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
  if (payments.value.length === 0) return ElMessage.warning('Không có dữ liệu để xuất')
  isExporting.value = true
  
  try {
    const headers = ['ID', 'Ma Giao Dich', 'Ma Don', 'So Tien', 'Phuong Thuc', 'Trang Thai', 'Ngay Thanh Toan']
    const rows = payments.value.map(p => [
      p.id,
      p.transaction_ref,
      p.registration_id,
      p.amount,
      p.payment_method,
      p.status,
      p.paid_at ? new Date(p.paid_at).toLocaleString('vi-VN') : 'N/A'
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map(r => r.join(','))
    ].join('\n')

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `BaoCao_ThanhToan_${new Date().toLocaleDateString('vi-VN').replace(/\//g, '-')}.csv`
    link.click()
    ElMessage.success('Đã xuất báo cáo CSV thành công')
  } catch (err) {
    ElMessage.error('Lỗi khi xuất báo cáo: ' + err.message)
  } finally {
    isExporting.value = false
  }
}

onMounted(fetchPayments)
</script>

<template>
  <div class="module-shell">
    <!-- HEADER PREMIUM -->
    <section class="action-bar-glass shadow-sm">
      <div class="action-info">
        <div class="kicker-wrap">
          <span class="section-kicker">Financial Oversight</span>
          <div class="live-indicator">
            <span class="dot"></span>
            LIVE
          </div>
        </div>
        <p>Theo dõi các giao dịch từ cổng thanh toán và quản lý doanh thu thời gian thực.</p>
      </div>
      <div class="hero-actions-v2">
        <el-button :icon="Refresh" circle @click="fetchPayments" />
        <el-button type="primary" round :loading="isExporting" @click="handleExport" class="btn-export">
          Xuất báo cáo Excel
        </el-button>
      </div>
    </section>

    <section class="table-card-premium shadow-sm">
      <el-table :data="payments" stripe v-loading="loading" class="modern-finance-table">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        
        <el-table-column label="Giao dịch / Đơn hàng" min-width="220">
          <template #default="{ row }">
            <div class="tx-cell">
              <span class="tx-ref">{{ row.transaction_ref }}</span>
              <span class="reg-id">Order #{{ row.registration_id }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="Số tiền" width="160" align="right">
           <template #default="{ row }">
             <div class="amount-cell">
               {{ new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(row.amount) }}
             </div>
           </template>
        </el-table-column>

        <el-table-column label="Phương thức" width="180">
          <template #default="{ row }">
            <div class="method-cell">
              <el-icon class="m-icon"><CreditCard /></el-icon>
              <span>{{ row.payment_method }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="Trạng thái" width="140" align="center">
           <template #default="{ row }">
             <el-tag :type="getStatusType(row.status)" effect="light" class="status-pill">
               {{ row.status?.toUpperCase() }}
             </el-tag>
           </template>
        </el-table-column>

        <el-table-column label="Ngày thanh toán" min-width="180" align="right">
           <template #default="{ row }">
             <div class="time-vertical" v-if="row.paid_at">
               <span class="d-val">{{ new Date(row.paid_at).toLocaleDateString('vi-VN') }}</span>
               <span class="t-val">{{ new Date(row.paid_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) }}</span>
             </div>
             <span v-else>N/A</span>
           </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="payments.length === 0" description="Chưa có giao dịch thanh toán nào" />
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

.hero-actions-v2 { display: flex; align-items: center; gap: 12px; }
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
.tx-ref { font-weight: 700; color: #0f172a; font-size: 0.9rem; font-family: monospace; }
.reg-id { font-size: 0.75rem; color: #94a3b8; font-weight: 600; }

.amount-cell { font-weight: 900; color: #10b981; font-size: 1.05rem; }

.method-cell { display: flex; align-items: center; gap: 8px; color: #475569; font-weight: 600; font-size: 0.9rem; }
.m-icon { color: #64748b; font-size: 1.1rem; }

.status-pill { font-weight: 800; border-radius: 99px; padding: 0 16px; font-size: 0.65rem; border: none !important; }

.time-vertical { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.d-val { font-size: 0.85rem; color: #64748b; font-weight: 600; }
.t-val { font-size: 0.8rem; color: #94a3b8; font-weight: 700; }

:deep(.el-table) { border-radius: 12px; }
:deep(.el-table .cell) { padding: 12px 16px; }

.shadow-sm { box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
</style>
