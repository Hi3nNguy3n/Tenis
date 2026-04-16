<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import { Calendar, Location, Timer, ArrowLeft, ArrowRight, Plus } from '@element-plus/icons-vue'

const courts = ref([])
const matches = ref([])
const pendingMatches = ref([]) 
const isLoading = ref(false)
const selectedDate = ref(new Date().toISOString().split('T')[0])

// --- STATE CHO DIALOG ĐIỀU PHỐI ---
const isDialogOpen = ref(false)
const isSaving = ref(false)
const isEditing = ref(false)
const form = ref({
  match_id: null,
  court_id: null,
  start_time: ''
})

// Khung giờ hiển thị: từ 6h sáng đến 23h đêm (Tăng thêm 1 tiếng để có không gian cho trận cuối ngày)
const timeSlots = Array.from({ length: 18 }, (_, i) => i + 6)

const fetchData = async () => {
  isLoading.value = true
  try {
    const courtsData = await apiClient.get('/api/courts/', { params: { status: 'AVAILABLE' } })
    courts.value = courtsData

    const matchesData = await apiClient.get('/api/tournaments/matches/all')
    
    matches.value = matchesData.filter(m => m.date === selectedDate.value && m.court && m.start !== '--:--')
    pendingMatches.value = matchesData.filter(m => m.status === 'pending' || !m.court || m.start === '--:--')
  } catch (err) {
    ElMessage.error('Lỗi tải lịch trình: ' + err.message)
  } finally {
    isLoading.value = false
  }
}

const changeDate = (days) => {
  const date = new Date(selectedDate.value)
  date.setDate(date.getDate() + days)
  selectedDate.value = date.toISOString().split('T')[0]
  fetchData()
}

const openCreateSchedule = () => {
  isEditing.value = false
  form.value = {
    match_id: null,
    court_id: null,
    start_time: `${selectedDate.value}T08:00:00` 
  }
  isDialogOpen.value = true
}

const openEditSchedule = (match) => {
  isEditing.value = true
  const targetCourt = courts.value.find(c => c.court_name === match.court)
  form.value = {
    match_id: match.id,
    court_id: targetCourt ? targetCourt.id : null,
    start_time: `${match.date}T${match.start}:00`
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
    ElMessage.error('Lỗi xếp lịch: ' + err.message)
  } finally {
    isSaving.value = false
  }
}

// Lõi tính toán: 1 phút = 1.5px. Khối 1 giờ = 90px
const getMatchStyle = (startTimeStr) => {
  if (!startTimeStr || startTimeStr === '--:--') return { display: 'none' }
  const [hours, minutes] = startTimeStr.split(':').map(Number)
  const startFromSix = (hours - 6) * 60 + minutes
  return {
    top: `${startFromSix * 1.5}px`, 
    height: '110px', // Thu nhỏ một chút để hở viền bên dưới
    zIndex: 10
  }
}

const getMatchesForCourt = (courtName) => {
  return matches.value.filter(m => m.court === courtName)
}

const getStatusType = (status) => {
  const map = { 'scheduled': 'warning', 'ongoing': 'primary', 'completed': 'success' }
  return map[status] || 'info'
}

onMounted(fetchData)
</script>

<template>
  <div class="schedule-container">
    <section class="hero-card">
      <div class="hero-content">
        <span class="section-kicker">Order of Play</span>
        <h2>Điều phối Sân & Giờ</h2>
        <p>Lịch trình theo cụm sân. Click vào trận để đổi giờ, hoặc bấm xếp lịch trận mới.</p>
      </div>

      <div class="header-actions">
        <el-button type="primary" size="large" :icon="Plus" @click="openCreateSchedule" class="action-btn">
          Xếp lịch trận đấu
        </el-button>

        <div class="date-controls">
          <el-button :icon="ArrowLeft" circle @click="changeDate(-1)" />
          <div class="current-date-display">
            <el-icon><Calendar /></el-icon>
            <span>{{ selectedDate }}</span>
          </div>
          <el-button :icon="ArrowRight" circle @click="changeDate(1)" />
        </div>
      </div>
    </section>

    <div class="schedule-wrapper" v-loading="isLoading">
      <div class="schedule-scroll-container">
        
        <div class="schedule-header-row">
          <div class="corner-header">GIỜ / SÂN</div>
          <div class="court-header" v-for="court in courts" :key="court.id">
            <strong>{{ court.court_name }}</strong>
            <span>{{ court.location_name }}</span>
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
              v-for="match in getMatchesForCourt(court.court_name)" 
              :key="match.id"
              class="match-card"
              :class="match.status"
              :style="getMatchStyle(match.start)"
              @click="openEditSchedule(match)"
            >
              <div class="match-time-tag"><el-icon><Timer /></el-icon> {{ match.start }}</div>
              <div class="match-tour">{{ match.tournament }}</div>
              <div class="match-footer">
                <span class="match-id">#{{ match.id }}</span>
                <span class="status-dot" :class="match.status"></span>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>

    <el-dialog 
      v-model="isDialogOpen" 
      :title="isEditing ? 'Đổi lịch trận đấu' : 'Phân bổ trận chưa xếp lịch'" 
      width="480px"
      class="clean-dialog"
      destroy-on-close
    >
      <el-form label-position="top" size="large" class="schedule-form">
        
        <el-form-item label="Chọn Trận đấu" required>
          <el-select 
            v-model="form.match_id" 
            style="width: 100%" 
            placeholder="--- Nhấp để chọn trận đấu ---"
            :disabled="isEditing"
          >
            <el-option v-if="isEditing" :label="`Trận #${form.match_id}`" :value="form.match_id" />
            <el-option 
              v-for="m in pendingMatches" 
              :key="m.id" 
              :label="`Trận #${m.id} - ${m.tournament}`" 
              :value="m.id" 
            />
          </el-select>
        </el-form-item>

        <div class="form-row-2">
          <el-form-item label="Chọn Sân" required style="flex: 1;">
            <el-select v-model="form.court_id" style="width: 100%" placeholder="--- Chọn sân ---">
              <el-option 
                v-for="c in courts" 
                :key="c.id" 
                :label="`${c.court_name}`" 
                :value="c.id" 
              />
            </el-select>
          </el-form-item>

          <el-form-item label="Giờ bắt đầu" required style="flex: 1;">
            <el-date-picker
              v-model="form.start_time"
              type="datetime"
              placeholder="Chọn ngày giờ"
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
            {{ isEditing ? 'Cập nhật lịch' : 'Lưu điều phối' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.schedule-container { display: flex; flex-direction: column; gap: 20px; height: calc(100vh - 100px); }

/* HERO CARD */
.hero-card {
  padding: 24px 30px; border-radius: 8px; background: white;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03); flex-shrink: 0;
}
.section-kicker { display: inline-flex; margin-bottom: 8px; padding: 6px 12px; border-radius: 8px; background: rgba(20, 98, 80, 0.08); color: #0f5c4d; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; }
.hero-content h2 { margin: 0; font-size: 1.8rem; color: #132722; }
.hero-content p { margin: 5px 0 0 0; color: #64748b; font-size: 0.9rem; }

.header-actions { display: flex; align-items: center; gap: 15px; }
.action-btn { font-weight: bold; border-radius: 12px; }
.date-controls { display: flex; align-items: center; gap: 15px; background: #f1f5f9; padding: 6px 12px; border-radius: 8px; }
.current-date-display { display: flex; align-items: center; gap: 8px; font-weight: 800; color: #0f172a; min-width: 130px; justify-content: center; font-size: 1.05rem; }

/* BẢNG GRID MỚI */
.schedule-wrapper { 
  flex: 1; border: 1px solid #e2e8f0; border-radius: 8px; 
  background: white; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.02);
}
.schedule-scroll-container { 
  height: 100%; overflow: auto; position: relative; 
}

/* Header Grid */
.schedule-header-row { 
  display: flex; position: sticky; top: 0; z-index: 40; 
  background: white; border-bottom: 2px solid #cbd5e1; box-shadow: 0 2px 10px rgba(0,0,0,0.02);
}
.corner-header { 
  width: 80px; min-width: 80px; height: 70px; 
  position: sticky; left: 0; z-index: 50; background: #f8fafc; 
  display: flex; align-items: center; justify-content: center; 
  font-weight: 900; color: #64748b; font-size: 0.7rem; border-right: 1px solid #e2e8f0;
}
.court-header { 
  flex: 1; min-width: 240px; height: 70px; 
  display: flex; flex-direction: column; align-items: center; justify-content: center; 
  border-right: 1px solid #e2e8f0; background: white;
}
.court-header strong { color: #0f5c4d; font-size: 1rem; }
.court-header span { font-size: 0.75rem; color: #94a3b8; margin-top: 3px; }

/* Body Grid */
.schedule-body-row { display: flex; position: relative; }

.time-column { 
  width: 80px; min-width: 80px; position: sticky; left: 0; 
  z-index: 30; background: #f8fafc; border-right: 1px solid #e2e8f0; 
}
.time-slot { 
  height: 90px; box-sizing: border-box; border-bottom: 1px solid #e2e8f0; 
  display: flex; justify-content: center; padding-top: 8px;
}
.time-slot span { font-size: 0.8rem; color: #64748b; font-weight: 700; }

.court-lane { 
  flex: 1; min-width: 240px; position: relative; 
  border-right: 1px solid #e2e8f0; background: #fafcff; 
}
.grid-cell { 
  height: 90px; box-sizing: border-box; border-bottom: 1px dashed #cbd5e1; 
}

/* Match Cards */
.match-card {
  position: absolute; left: 8px; right: 8px; padding: 12px; 
  box-sizing: border-box; border-radius: 12px; border-left: 5px solid; 
  background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.06); 
  display: flex; flex-direction: column; cursor: pointer; transition: 0.2s;
}
.match-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); filter: brightness(0.98); z-index: 20; }
.match-card.ongoing { border-left-color: #3b82f6; background: #eff6ff; }
.match-card.completed { border-left-color: #22c55e; background: #f0fdf4; opacity: 0.85; }
.match-card.scheduled { border-left-color: #eab308; background: #fefce8; }

.match-time-tag { font-size: 0.8rem; font-weight: 900; color: #1e293b; margin-bottom: 5px; display: flex; align-items: center; gap: 4px; }
.match-tour { 
  font-size: 0.85rem; font-weight: 700; color: #334155; line-height: 1.3; 
  flex: 1; display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; 
}
.match-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 5px; }
.match-id { font-size: 0.7rem; color: #94a3b8; font-weight: bold; }
.status-dot { width: 10px; height: 10px; border-radius: 50%; }
.status-dot.ongoing { background: #3b82f6; }
.status-dot.completed { background: #22c55e; }
.status-dot.scheduled { background: #eab308; }

/* FORM ĐIỀU PHỐI */
.schedule-form { margin-top: 10px; }
.form-row-2 { display: flex; gap: 20px; }
:deep(.el-form-item__label) { font-weight: 700; color: #334155; padding-bottom: 5px; }
.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; padding-top: 15px; border-top: 1px solid #f1f5f9; }
</style>