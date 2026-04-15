<script setup>
import { onMounted, ref } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'

const isLoading = ref(false)
const schedule = ref([])

const loadMatches = async () => {
  isLoading.value = true
  try {
    const data = await apiClient.get('/api/tournaments/matches/all')
    schedule.value = data
  } catch (err) {
    ElMessage.error('Lỗi tải lịch thi đấu: ' + err.message)
  } finally {
    isLoading.value = false
  }
}

const getStatusType = (s) => {
  const status = s?.toLowerCase()
  if (status === 'ongoing' || status === 'in progress') return 'primary'
  if (status === 'finished' || status === 'completed') return 'success'
  if (status === 'cancelled') return 'danger'
  return 'info'
}

onMounted(loadMatches)
</script>

<template>
  <div class="module-shell">
    <section class="hero-card">
      <div>
        <span class="section-kicker">Match Scheduling</span>
        <h2>Lịch thi đấu</h2>
        <p>Theo dõi và sắp xếp lịch thi đấu cho các giải đấu đang diễn ra. Dữ liệu được cập nhật trực tiếp từ hệ thống.</p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" size="large" @click="loadMatches">Tải lại</el-button>
        <el-button plain size="large">Xuất Excel</el-button>
      </div>
    </section>

    <section class="table-card">
      <div class="card-header" style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <h3 style="margin: 0; color: #123f34;">Lịch trình hôm nay</h3>
        <el-date-picker type="date" placeholder="Chọn ngày" style="width: 200px" />
      </div>

      <el-table :data="schedule" stripe v-loading="isLoading">
        <el-table-column prop="tournament" label="Giải đấu" min-width="180" />
        <el-table-column prop="court" label="Sân đấu" min-width="150" />
        <el-table-column prop="date" label="Ngày" width="120" />
        <el-table-column label="Thời gian" width="150">
           <template #default="{ row }">
             {{ row.start }} - {{ row.end }}
           </template>
        </el-table-column>
        <el-table-column label="Trạng thái" width="130">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="light">{{ row.status?.toUpperCase() || 'SCHEDULED' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain>Dời lịch</el-button>
            <el-button size="small" type="info" plain>Sửa</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="schedule.length === 0" description="Chưa có lịch thi đấu được xếp" />
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
