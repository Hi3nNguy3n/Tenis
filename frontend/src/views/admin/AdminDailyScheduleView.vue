<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import { Calendar, Location, Timer, ArrowLeft, ArrowRight, Plus, Refresh, Promotion } from '@element-plus/icons-vue'

const courts = ref([])
const matches = ref([])
const pendingMatches = ref([]) 
const isLoading = ref(false)
const selectedDate = ref(new Date().toISOString().split('T')[0])

const normalizeDateKey = (value) => {
  if (!value || typeof value !== 'string') return ''
  const match = value.match(/^(\d{4}-\d{2}-\d{2})/)
  return match ? match[1] : value
}

// --- STATE CHO DIALOG ĐIỀU PHỐI ---
const isDialogOpen = ref(false)
const isSaving = ref(false)
const isEditing = ref(false)
const form = ref({
  match_id: null,
  court_id: null,
  start_time: ''
})

// Khung giờ hiển thị: từ 6h sáng đến 23h đêm
const timeSlots = Array.from({ length: 18 }, (_, i) => i + 6)

const fetchData = async () => {
  isLoading.value = true
  try {
    const courtsData = await apiClient.get('/api/courts/', { params: { status: 'AVAILABLE' } })
    courts.value = courtsData

    // ĐÃ SỬA API: Dùng /api/matches/ để lấy cả đấu Giải + Giao hữu
    const matchesData = await apiClient.get('/api/matches/')
    
    matches.value = matchesData.filter(m => normalizeDateKey(m.date || m.start_time) === selectedDate.value && m.court_id && m.start !== '--:--')
    
    // Gom tất cả các trận chưa có sân hoặc chưa có giờ vào Hàng Chờ
    pendingMatches.value = matchesData.filter(m => m.status === 'pending' || m.status === 'scheduled' && (!m.court_id || m.start === '--:--'))
  } catch (err) {
    ElMessage.error('Lỗi tải lịch trình: ' + err.message)
  } finally {
    isLoading.value = false
  }
}

const changeDate = (days) => {
  const date = new Date(`${selectedDate.value}T12:00:00`)
  date.setDate(date.getDate() + days)
  selectedDate.value = date.toISOString().split('T')[0]
  fetchData()
}

// Bấm vào 1 trận đang ở Hàng Chờ để xếp lịch cho nó
const scheduleFromPending = (match) => {
  isEditing.value = false
  form.value = {
    match_id: match.id,
    court_id: null,
    start_time: `${selectedDate.value}T08:00:00` // Mặc định gợi ý 8h sáng của ngày đang chọn
  }
  isDialogOpen.value = true
}

const openEditSchedule = (match) => {
  isEditing.value = true
  form.value = {
    match_id: match.id,
    court_id: match.court_id,
    start_time: match.date && match.start !== '--:--' ? `${match.date}T${match.start}:00` : ''
  }
  isDialogOpen.value = true
}

const saveSchedule = async () => {
  if (!form.value.match_id || !form.value.court_id || !form.value.start_time) {
    return ElMessage.warning('Vui lòng điền đủ Trận đấu, Sân và Giờ')
  }

  isSaving.value = true
  try {
    await apiClient.post(`/api/tournaments/matches/${form.value.match_id}/schedule`, {
      court_id: form.value.court_id,
      start_time: form.value.start_time
    })
    ElMessage.success('Điều phối thành công!')
    isDialogOpen.value = false
    fetchData() 
  } catch (err) {
    ElMessage.error('Lỗi xếp lịch: ' + (err.response?.data?.detail || err.message))
  } finally {
    isSaving.value = false
  }
}

const getMatchStyle = (startTimeStr) => {
  if (!startTimeStr || startTimeStr === '--:--') return { display: 'none' }
  const [hours, minutes] = startTimeStr.split(':').map(Number)
  const startFromSix = (hours - 6) * 60 + minutes
  return {
    top: `${startFromSix * 1.5}px`, 
    height: '110px', 
    zIndex: 10
  }
}

const getMatchesForCourt = (courtId) => {
  return matches.value.filter(m => m.court_id === courtId)
}

onMounted(fetchData)
</script>

<template>
  <div class="schedule-container">
    <section class="action-bar shadow-sm">
      <div class="action-info">
        <span class="section-kicker">Order of Play</span>
        <p>Điều phối Sân & Giờ thi đấu trực quan theo từng ngày.</p>
      </div>

      <div class="header-actions">
        <div class="date-controls">
          <el-button :icon="ArrowLeft" plain circle @click="changeDate(-1)" />
          <div class="current-date-display">
            <el-icon><Calendar /></el-icon>
            <span>{{ selectedDate }}</span>
          </div>
          <el-button :icon="ArrowRight" plain circle @click="changeDate(1)" />
        </div>
        <el-button plain :icon="Refresh" @click="fetchData">Tải lại</el-button>
      </div>
    </section>

    <div class="layout-split">
      
      <div class="schedule-wrapper" v-loading="isLoading">
        <div class="schedule-scroll-container">
          <div class="schedule-header-row">
            <div class="corner-header">GIỜ / SÂN</div>
            <div class="court-header" v-for="court in courts" :key="court.id">
              <strong>{{ court.court_name }}</strong>
              <span>{{ court.location_name || 'Saigon Tennis' }}</span>
            </div>
          </div>

          <div class="schedule-body-row">
            <div class="time-column">
              <div class="time-slot" v-for="hour in timeSlots" :key="hour">
                <span>{{ hour.toString().padStart(2, '0') }}:00</span>
              </div>
            </div>

            <div class="court-lane" v-for="court in courts" :key="court.id">
              <div class="grid-cell" v-for="hour in timeSlots" :key="'g'+hour"></div>

              <div 
                v-for="match in getMatchesForCourt(court.id)" 
                :key="match.id"
                class="match-card"
                :class="match.status"
                :style="getMatchStyle(match.start)"
                @click="openEditSchedule(match)"
              >
                <div class="match-time-tag"><el-icon><Timer /></el-icon> {{ match.start }}</div>
                <div class="match-tour">{{ match.tournament }}</div>
                <div class="match-players">
                  {{ match.p1_name }} <br/><span style="color:red; font-size:0.7rem">VS</span><br/> {{ match.p2_name }}
                </div>
                <div class="match-footer">
                  <span class="match-id">#{{ match.id }}</span>
                  <span class="status-dot" :class="match.status"></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <aside class="pending-sidebar">
        <div class="pending-header">
          <h3>Trận chưa xếp lịch</h3>
          <el-tag type="danger" round>{{ pendingMatches.length }} trận</el-tag>
        </div>
        <div class="pending-list">
          <div v-for="pm in pendingMatches" :key="pm.id" class="pending-card" @click="scheduleFromPending(pm)">
            <div class="pm-head">
              <span class="pm-tour">{{ pm.tournament }}</span>
              <span class="pm-round">{{ pm.round_code }}</span>
            </div>
            <div class="pm-players">
              {{ pm.p1_name || 'Chưa xác định' }} <span>vs</span> {{ pm.p2_name || 'Chưa xác định' }}
            </div>
            <div class="pm-action">
              <el-icon><Promotion /></el-icon> Nhấn để xếp lịch
            </div>
          </div>
          <el-empty v-if="pendingMatches.length === 0" description="Tuyệt vời! Không có trận nào tồn đọng." :image-size="80" />
        </div>
      </aside>

    </div>

    <el-dialog 
      v-model="isDialogOpen" 
      :title="isEditing ? 'Đổi lịch trận đấu' : 'Phân bổ trận vào sân'" 
      width="480px"
      class="clean-dialog"
      destroy-on-close
    >
      <el-form label-position="top" size="large" class="schedule-form">
        
        <el-form-item label="Trận đấu" required>
          <el-select v-model="form.match_id" style="width: 100%" disabled>
            <el-option :label="`Trận #${form.match_id}`" :value="form.match_id" />
          </el-select>
        </el-form-item>

        <div class="form-row-2">
          <el-form-item label="Chỉ định Sân" required style="flex: 1;">
            <el-select v-model="form.court_id" style="width: 100%" placeholder="--- Chọn sân ---">
              <el-option v-for="c in courts" :key="c.id" :label="`${c.court_name}`" :value="c.id" />
            </el-select>
          </el-form-item>

          <el-form-item label="Giờ bắt đầu" required style="flex: 1;">
            <el-date-picker
              v-model="form.start_time"
              type="datetime"
              format="DD/MM/YYYY HH:mm"
              value-format="YYYY-MM-DDTHH:mm:ss"
              style="width: 100%"
              :clearable="false"
            />
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="isDialogOpen = false" size="large">Hủy bỏ</el-button>
          <el-button type="primary" :loading="isSaving" @click="saveSchedule" size="large">
            {{ isEditing ? 'Cập nhật lịch' : 'Xác nhận xếp lịch' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.schedule-container { display: flex; flex-direction: column; gap: 20px; height: calc(100vh - 100px); padding: 20px; background: #f8fafc; }

.action-bar {
  background: white; padding: 16px 24px; border-radius: 12px;
  display: flex; justify-content: space-between; align-items: center;
  border-left: 5px solid var(--primary); border: 1px solid #eef2f6;
  flex-shrink: 0;
}
.action-info p { color: #888; font-size: 0.9rem; margin: 2px 0 0 0; }
.section-kicker { font-size: 0.7rem; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 2px; }

.header-actions { display: flex; align-items: center; gap: 15px; }
.date-controls { display: flex; align-items: center; gap: 12px; background: #f1f5f9; padding: 6px 16px; border-radius: 10px; border: 1px solid #e2e8f0; }
.current-date-display { display: flex; align-items: center; gap: 8px; font-weight: 800; color: #1e293b; min-width: 140px; justify-content: center; font-size: 1rem; }

/* BỐ CỤC 2 CỘT */
.layout-split {
  display: flex;
  gap: 20px;
  flex: 1;
  overflow: hidden;
}

/* LƯỚI SÂN BÃI */
.schedule-wrapper { 
  flex: 1; border: 1px solid #e2e8f0; border-radius: 12px; 
  background: white; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.02);
}
.schedule-scroll-container { height: 100%; overflow: auto; position: relative; }

.schedule-header-row { display: flex; position: sticky; top: 0; z-index: 40; background: white; border-bottom: 2px solid #cbd5e1; }
.corner-header { width: 80px; min-width: 80px; height: 70px; position: sticky; left: 0; z-index: 50; background: #f8fafc; display: flex; align-items: center; justify-content: center; font-weight: 900; color: #64748b; font-size: 0.7rem; border-right: 1px solid #e2e8f0; }
.court-header { flex: 1; min-width: 200px; height: 70px; display: flex; flex-direction: column; align-items: center; justify-content: center; border-right: 1px solid #e2e8f0; background: white; }
.court-header strong { color: #0f5c4d; font-size: 1rem; }
.court-header span { font-size: 0.75rem; color: #94a3b8; margin-top: 3px; }

.schedule-body-row { display: flex; position: relative; }
.time-column { width: 80px; min-width: 80px; position: sticky; left: 0; z-index: 30; background: #f8fafc; border-right: 1px solid #e2e8f0; }
.time-slot { height: 90px; box-sizing: border-box; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: center; padding-top: 8px; }
.time-slot span { font-size: 0.8rem; color: #64748b; font-weight: 700; }

.court-lane { flex: 1; min-width: 200px; position: relative; border-right: 1px solid #e2e8f0; background: #fafcff; }
.grid-cell { height: 90px; box-sizing: border-box; border-bottom: 1px dashed #cbd5e1; }

.match-card {
  position: absolute; left: 8px; right: 8px; padding: 8px 10px; 
  box-sizing: border-box; border-radius: 8px; border-left: 4px solid; 
  background: white; box-shadow: 0 4px 10px rgba(0,0,0,0.06); 
  display: flex; flex-direction: column; cursor: pointer; transition: 0.2s;
  overflow: hidden;
}
.match-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.1); filter: brightness(0.98); z-index: 20; }
.match-card.ongoing { border-left-color: #3b82f6; background: #eff6ff; }
.match-card.completed { border-left-color: #22c55e; background: #f0fdf4; opacity: 0.85; }
.match-card.scheduled { border-left-color: #eab308; background: #fefce8; }

.match-time-tag { font-size: 0.7rem; font-weight: 900; color: #1e293b; margin-bottom: 3px; display: flex; align-items: center; gap: 4px; }
.match-tour { font-size: 0.75rem; font-weight: 700; color: #334155; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.match-players { font-size: 0.7rem; color: #64748b; margin-top: 4px; line-height: 1.2; text-align: center; }
.match-footer { display: flex; justify-content: space-between; align-items: center; margin-top: auto; }
.match-id { font-size: 0.65rem; color: #94a3b8; font-weight: bold; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.status-dot.ongoing { background: #3b82f6; }
.status-dot.completed { background: #22c55e; }
.status-dot.scheduled { background: #eab308; }

/* CỘT HÀNG CHỜ BÊN PHẢI */
.pending-sidebar {
  width: 320px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0,0,0,0.02);
}
.pending-header {
  padding: 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.pending-header h3 { margin: 0; font-size: 1rem; color: #0f172a; }
.pending-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #f1f5f9;
}
.pending-card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.pending-card:hover {
  border-color: var(--primary);
  transform: translateX(-4px);
  box-shadow: -4px 4px 12px rgba(0,0,0,0.05);
}
.pm-head { display: flex; justify-content: space-between; margin-bottom: 8px; }
.pm-tour { font-size: 0.75rem; font-weight: 700; color: #3b82f6; max-width: 70%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pm-round { font-size: 0.7rem; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; color: #64748b; font-weight: bold; }
.pm-players { font-size: 0.85rem; font-weight: 600; color: #1e293b; text-align: center; margin-bottom: 8px; }
.pm-players span { font-size: 0.7rem; color: #ef4444; margin: 0 4px; }
.pm-action { font-size: 0.75rem; color: var(--primary); font-weight: bold; display: flex; justify-content: center; align-items: center; gap: 4px; background: #f0fdf4; padding: 6px; border-radius: 6px;}

.form-row-2 { display: flex; gap: 20px; }
:deep(.el-form-item__label) { font-weight: 700; color: #334155; padding-bottom: 5px; }
.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; padding-top: 15px; border-top: 1px solid #f1f5f9; }

@media (max-width: 1200px) {
  .layout-split { flex-direction: column; }
  .pending-sidebar { width: 100%; max-height: 250px; }
}
</style>