<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { registrationService } from '../../services/registrationService'

const search = ref('')
const statusFilter = ref('')
const registrations = ref([])
const isLoading = ref(false)

const loadRegistrations = async () => {
  isLoading.value = true
  try {
    const data = await registrationService.getAll({ 
      search: search.value, 
      status: statusFilter.value 
    })
    registrations.value = Array.isArray(data) ? data : (data.items || [])
  } catch (err) {
    ElMessage.error('Lỗi tải danh sách đăng ký: ' + err.message)
  } finally {
    isLoading.value = false
  }
}

const handleConfirm = (id) => {
  ElMessageBox.confirm('Xác nhận đã thanh toán cho đơn này?', 'Xác nhận', { type: 'success' }).then(async () => {
    try {
      await registrationService.confirm(id)
      ElMessage.success('Đã xác nhận thanh toán')
      loadRegistrations()
    } catch (err) {
      ElMessage.error('Lỗi: ' + err.message)
    }
  })
}

const handleCancel = (id) => {
  ElMessageBox.confirm('Bạn có chắc muốn hủy đơn đăng ký này?', 'Cảnh báo', { type: 'warning' }).then(async () => {
    try {
      await registrationService.cancel(id)
      ElMessage.success('Đã hủy đơn')
      loadRegistrations()
    } catch (err) {
      ElMessage.error('Lỗi: ' + err.message)
    }
  })
}

onMounted(loadRegistrations)

const getStatusType = (status) => {
  const s = status?.toLowerCase()
  if (s === 'confirmed' || s === 'paid') return 'success'
  if (s === 'cancelled' || s === 'rejected') return 'danger'
  if (s === 'expired') return 'info'
  return 'warning'
}

const filteredRows = computed(() => registrations.value)
</script>

<template>
  <div class="module-shell">
    <section class="hero-card">
      <div>
        <span class="section-kicker">Registration Flow</span>
        <h2>Danh sách đăng ký</h2>
        <p>Phê duyệt đơn đăng ký, kiểm tra trạng thái thanh toán và quản lý danh sách vận động viên tham gia giải.</p>
      </div>
      <div class="hero-actions">
        <el-button plain size="large" @click="loadRegistrations">Tải lại</el-button>
      </div>
    </section>

    <section class="filter-card">
      <el-input v-model="search" placeholder="Tìm tên VĐV..." clearable @change="loadRegistrations" />
      <el-select v-model="statusFilter" placeholder="Trạng thái" clearable @change="loadRegistrations">
        <el-option label="PENDING" value="pending" />
        <el-option label="CONFIRMED" value="confirmed" />
        <el-option label="CANCELLED" value="cancelled" />
        <el-option label="EXPIRED" value="expired" />
      </el-select>
    </section>

    <section class="table-card">
      <el-table :data="filteredRows" stripe v-loading="isLoading">
        <el-table-column label="Vận động viên" min-width="180">
           <template #default="{ row }">
             <div class="player-cell">
               <strong>{{ row.player_name || 'N/A' }}</strong>
               <small>{{ row.registrant_type?.toUpperCase() }}</small>
             </div>
           </template>
        </el-table-column>
        <el-table-column prop="tournament_name" label="Giải đấu" min-width="200" />
        <el-table-column prop="category_type" label="Hạng mục" width="120" />
        <el-table-column label="Trạng thái" width="140">
           <template #default="{ row }">
             <el-tag :type="getStatusType(row.status)">{{ row.status?.toUpperCase() }}</el-tag>
           </template>
        </el-table-column>
        <el-table-column label="Thanh toán" width="140">
           <template #default="{ row }">
             <el-tag :type="row.payment_status === 'paid' ? 'success' : 'info'" effect="dark">
               {{ row.payment_status?.toUpperCase() }}
             </el-tag>
           </template>
        </el-table-column>
        <el-table-column label="Actions" width="180" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button v-if="row.status !== 'confirmed'" size="small" type="success" plain @click="handleConfirm(row.id)">Duyệt</el-button>
              <el-button v-if="row.status !== 'cancelled'" size="small" type="danger" plain @click="handleCancel(row.id)">Hủy</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<style scoped>
.module-shell { display: grid; gap: 24px; }
.hero-card, .filter-card, .table-card {
  background: white; padding: 24px; border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.03);
}
.hero-card { display: flex; justify-content: space-between; align-items: flex-end; }
.section-kicker { font-size: 0.75rem; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 0.1em; display: block; margin-bottom: 8px; }
.hero-card h2 { font-size: 2.22rem; color: var(--text-dark); margin: 0; }
.hero-card p { color: #6e7a74; margin-top: 8px; }
.filter-card { display: flex; gap: 15px; }
.player-cell { display: flex; flex-direction: column; }
.player-cell small { font-size: 0.7rem; color: #9e9e9e; font-weight: 700; }
</style>
