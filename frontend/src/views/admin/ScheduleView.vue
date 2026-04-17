<script setup>
import { onMounted, ref, computed } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import { Refresh, Download, Edit, Location, Timer } from '@element-plus/icons-vue'

const isLoading = ref(false)
const schedule = ref([])
const filterDate = ref('')

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

const filteredSchedule = computed(() => {
  if (!filterDate.value) return schedule.value
  return schedule.value.filter(m => m.date === filterDate.value)
})

const getStatusType = (s) => {
  const status = s?.toLowerCase()
  if (status === 'ongoing') return 'primary'
  if (status === 'completed' || status === 'finished') return 'success'
  return 'info'
}

const showEditDialog = ref(false)
const editingMatch = ref(null)
const editForm = ref({ court_id: null, start_time: '' })
const courts = ref([])

const fetchCourts = async () => {
  try {
    const data = await apiClient.get('/api/courts/')
    courts.value = data
  } catch (err) { ElMessage.error('Lỗi tải danh sách sân') }
}

const handleEdit = (row) => {
  editingMatch.value = row
  const targetCourt = courts.value.find(c => c.court_name === row.court)
  editForm.value.court_id = targetCourt ? targetCourt.id : null
  editForm.value.start_time = row.date && row.start !== '--:--' ? `${row.date}T${row.start}:00` : ''
  showEditDialog.value = true
}

const handleSchedule = async () => {
  if (!editForm.value.court_id || !editForm.value.start_time) {
    return ElMessage.warning('Vui lòng chọn sân và giờ thi đấu')
  }
  try {
    // Phải gán lại đúng format cho API
    await apiClient.post(`/api/tournaments/matches/${editingMatch.value.id}/schedule`, {
      court_id: editForm.value.court_id,
      start_time: editForm.value.start_time
    })
    ElMessage.success('Cập nhật lịch thi đấu thành công')
    showEditDialog.value = false
    loadMatches()
  } catch (err) {
    ElMessage.error('Lỗi cập nhật: ' + err.message)
  }
}

onMounted(() => {
  loadMatches()
  fetchCourts()
})
</script>

<template>
  <div class="schedule-container">
    <!-- HEADER PREMIUM -->
    <section class="action-bar-glass shadow-sm">
      <div class="action-info">
        <div class="kicker-wrap">
          <span class="section-kicker">Schedule Overview</span>
          <div class="live-indicator">
            <span class="dot"></span>
            ACTIVE
          </div>
        </div>
        <p>Theo dõi và tổng hợp lịch thi đấu của tất cả các giải đấu trên hệ thống.</p>
      </div>

      <div class="hero-actions-v2">
        <el-date-picker 
          v-model="filterDate" 
          type="date" 
          placeholder="Lọc theo ngày" 
          value-format="YYYY-MM-DD" 
          style="width: 180px" 
          round
          @change="loadMatches"
        />
        <el-button :icon="Refresh" circle @click="loadMatches" />
        <el-button :icon="Download" type="primary" round class="btn-excel">Xuất dữ liệu</el-button>
      </div>
    </section>

    <main class="table-card-premium shadow-sm" v-loading="isLoading">
      <div class="table-meta">
        <h3>Lịch trình thi đấu hệ thống</h3>
        <span class="count-chip">{{ filteredSchedule.length }} Trận đấu</span>
      </div>

      <el-table :data="filteredSchedule" style="width: 100%" stripe class="modern-table">
        <el-table-column label="Giải đấu" min-width="240">
          <template #default="{ row }">
            <div class="tour-cell">
              <span class="tour-name">{{ row.tournament }}</span>
              <span class="tour-sub">Hệ thống giải Saigon Tennis</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="Địa điểm & Sân" min-width="200">
          <template #default="{ row }">
            <div class="location-cell">
              <el-icon class="loc-icon"><Location /></el-icon>
              <span>{{ row.court || 'Chưa gán sân' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="Ngày & Giờ" width="200">
          <template #default="{ row }">
            <div class="schedule-cell">
              <span class="d-val">{{ row.date }}</span>
              <div class="t-val">
                <el-icon><Timer /></el-icon>
                <span>{{ row.start }}</span>
              </div>
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

        <el-table-column label="Hành động" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-cell">
              <el-tooltip content="Sửa trận đấu" placement="top">
                <el-button circle size="small" type="primary" plain :icon="Edit" @click="handleEdit(row)" />
              </el-tooltip>
              <el-tooltip content="Dời lịch" placement="top">
                <el-button circle size="small" type="success" plain :icon="Timer" @click="handleEdit(row)" />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="filteredSchedule.length === 0" description="Không có lịch thi đấu phù hợp" />
    </main>

    <el-dialog v-model="showEditDialog" title="Điều chỉnh lịch thi đấu" width="460px" destroy-on-close class="premium-dialog">
      <div v-if="editingMatch" class="edit-context shadow-inner">
        <div class="context-item">
          <span class="label">Giải đấu:</span>
          <span class="val">{{ editingMatch.tournament }}</span>
        </div>
        <div class="context-item">
          <span class="label">Hiện tại:</span>
          <span class="val">{{ editingMatch.court || 'Chưa gán sân' }} | {{ editingMatch.start || '--:--' }}</span>
        </div>
      </div>

      <el-form label-position="top" class="mt-4">
        <el-form-item label="Chọn sân thi đấu mới" required>
          <el-select v-model="editForm.court_id" style="width: 100%" placeholder="Nhấn để chọn sân...">
            <el-option v-for="c in courts" :key="c.id" :label="c.court_name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Ngày & Giờ thi đấu mới" required>
          <el-date-picker
            v-model="editForm.start_time"
            type="datetime"
            placeholder="Chọn ngày và giờ cụ thể"
            format="DD/MM/YYYY HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditDialog = false" plain>Hủy bỏ</el-button>
          <el-button type="primary" @click="handleSchedule" class="px-6">Xác nhận cập nhật</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.schedule-container { display: grid; gap: 16px; padding: 10px; }

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
.btn-excel {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border: none;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
}

.table-card-premium {
  background: white; padding: 8px; border-radius: 20px;
  border: 1px solid #f1f5f9; box-shadow: 0 10px 30px rgba(0,0,0,0.03);
  overflow: hidden;
}

.table-meta { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; }
.table-meta h3 { margin: 0; color: #1e293b; font-size: 1.1rem; font-weight: 700; }
.count-chip { background: #f1f5f9; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 800; color: #64748b; }

.tour-cell { display: flex; flex-direction: column; gap: 2px; }
.tour-name { font-weight: 700; color: #0f172a; font-size: 0.95rem; }
.tour-sub { font-size: 0.75rem; color: #94a3b8; }

.location-cell { display: flex; align-items: center; gap: 8px; color: #475569; font-weight: 600; font-size: 0.9rem; }
.loc-icon { color: #3b82f6; font-size: 1rem; }

.schedule-cell { display: flex; flex-direction: column; gap: 4px; }
.d-val { font-size: 0.85rem; color: #64748b; font-weight: 600; }
.t-val { font-size: 0.95rem; font-weight: 900; color: #0f172a; display: flex; align-items: center; gap: 6px; }

.status-pill { font-weight: 800; border-radius: 99px; padding: 0 16px; font-size: 0.65rem; border: none !important; }

.action-cell { display: flex; gap: 12px; justify-content: center; }

:deep(.el-table) { border-radius: 12px; }
:deep(.el-table .cell) { padding: 12px 16px; }

.shadow-sm { box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.edit-context { background: #f8fafc; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0; display: flex; flex-direction: column; gap: 8px; }
.context-item { display: flex; justify-content: space-between; font-size: 0.85rem; }
.label { color: #64748b; font-weight: 600; }
.val { color: #0f172a; font-weight: 800; }
</style>
