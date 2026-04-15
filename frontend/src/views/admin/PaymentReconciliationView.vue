<script setup>
import { onMounted, ref } from 'vue'
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

onMounted(fetchPayments)
</script>

<template>
  <div class="module-shell">
    <section class="hero-card">
      <div>
        <span class="section-kicker">Financial Oversight</span>
        <h2>Đối soát thanh toán</h2>
        <p>Theo dõi các giao dịch từ cổng thanh toán, đối soát lệ phí giải đấu và quản lý doanh thu thực tế.</p>
      </div>
      <div class="hero-actions">
        <el-button plain size="large" @click="fetchPayments">Làm mới</el-button>
        <el-button type="primary" size="large">Xuất báo cáo</el-button>
      </div>
    </section>

    <section class="table-card">
      <el-table :data="payments" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="transaction_ref" label="Mã giao dịch" min-width="180" />
        <el-table-column prop="registration_id" label="Mã đơn" width="100" />
        <el-table-column label="Số tiền" width="150">
           <template #default="{ row }">
             <strong>{{ new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(row.amount) }}</strong>
           </template>
        </el-table-column>
        <el-table-column prop="payment_method" label="Phương thức" width="130" />
        <el-table-column label="Trạng thái" width="140">
           <template #default="{ row }">
             <el-tag :type="getStatusType(row.status)">{{ row.status?.toUpperCase() }}</el-tag>
           </template>
        </el-table-column>
        <el-table-column label="Ngày thanh toán" min-width="160">
           <template #default="{ row }">
             {{ row.paid_at ? new Date(row.paid_at).toLocaleString('vi-VN') : 'N/A' }}
           </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="payments.length === 0" description="Chưa có giao dịch thanh toán nào" />
    </section>
  </div>
</template>

<style scoped>
.module-shell { display: grid; gap: 24px; }
.hero-card, .table-card {
  background: white; padding: 24px; border-radius: 28px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.03);
}
.hero-card { display: flex; justify-content: space-between; align-items: flex-end; }
.section-kicker { font-size: 0.75rem; font-weight: 800; color: #006953; text-transform: uppercase; letter-spacing: 0.1em; display: block; margin-bottom: 8px; }
.hero-card h2 { font-size: 2.22rem; color: #123f34; margin: 0; }
.hero-card p { color: #6e7a74; margin-top: 8px; }
</style>
