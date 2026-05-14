<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import { 
  Calendar as CalendarIcon, Location as LocationIcon, Timer, ArrowLeft, ArrowRight, 
  Plus, Refresh, Promotion, Trophy, Monitor,
  Connection, CircleCheckFilled, InfoFilled, Search,
  Filter, VideoPlay, Clock as ClockIcon
} from '@element-plus/icons-vue'

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

    const matchesData = await apiClient.get('/api/matches/')
    
    matches.value = matchesData.filter(m => normalizeDateKey(m.date || m.start_time) === selectedDate.value && m.court_id && m.start !== '--:--')
    
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

const scheduleFromPending = (match) => {
  isEditing.value = false
  form.value = {
    match_id: match.id,
    court_id: null,
    start_time: `${selectedDate.value}T08:00:00`
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
    top: `${startFromSix * 1.8}px`, 
    height: '100px', 
    zIndex: 10
  }
}

const getMatchesForCourt = (courtId) => {
  return matches.value.filter(m => m.court_id === courtId)
}

onMounted(fetchData)
</script>

<template>
  <div class="saas-container" v-loading="isLoading">
    <!-- Action Bar -->
    <section class="saas-header">
      <div class="header-left">
        <div class="operation-badge-premium indigo">
          <el-icon class="mr-1"><CalendarIcon /></el-icon>
          <span>Order of Play</span>
        </div>
        <div class="header-titles">
          <h2 class="saas-title">Điều phối Sân & Giờ</h2>
          <p class="saas-subtitle">Quản lý lịch trình thi đấu trực quan theo từng ngày</p>
        </div>
      </div>
      
      <div class="header-right">
        <div class="saas-date-navigator">
          <el-button @click="changeDate(-1)" class="nav-btn"><el-icon><ArrowLeft /></el-icon></el-button>
          <div class="date-display-box">
            <el-icon class="mr-2"><CalendarIcon /></el-icon>
            <span>{{ selectedDate }}</span>
          </div>
          <el-button @click="changeDate(1)" class="nav-btn"><el-icon><ArrowRight /></el-icon></el-button>
        </div>
        <el-button @click="fetchData" :icon="Refresh" class="saas-btn-refresh">Refresh</el-button>
      </div>
    </section>

    <!-- Content Layout -->
    <div class="schedule-layout-saas">
      <!-- Main Visual Schedule -->
      <main class="saas-card-premium schedule-main-block">
        <div class="timeline-viewport">
          <!-- Court Headers -->
          <div class="courts-row-sticky">
            <div class="time-corner">TIME</div>
            <div v-for="court in courts" :key="court.id" class="court-header-saas">
              <span class="c-name">{{ court.court_name }}</span>
              <span class="c-loc">{{ court.location_name || 'Main Arena' }}</span>
            </div>
          </div>

          <!-- Timeline Body -->
          <div class="timeline-body">
            <!-- Time Markers -->
            <div class="time-track">
              <div v-for="hour in timeSlots" :key="hour" class="hour-marker">
                <span>{{ hour.toString().padStart(2, '0') }}:00</span>
              </div>
            </div>

            <!-- Court Lanes -->
            <div class="lanes-wrapper">
              <div v-for="court in courts" :key="court.id" class="court-lane-saas">
                <!-- Grid lines -->
                <div v-for="hour in timeSlots" :key="'g'+hour" class="lane-grid-cell"></div>

                <!-- Match Cards -->
                <div 
                  v-for="match in getMatchesForCourt(court.id)" 
                  :key="match.id"
                  class="saas-match-card-visual"
                  :class="match.status"
                  :style="getMatchStyle(match.start)"
                  @click="openEditSchedule(match)"
                >
                  <div class="mc-accent"></div>
                  <div class="mc-content">
                    <div class="mc-time">
                      <el-icon class="mr-1"><ClockIcon /></el-icon>
                      {{ match.start }}
                    </div>
                    <div class="mc-tour truncate">{{ match.tournament }}</div>
                    <div class="mc-versus">
                      <span class="p-name">{{ match.p1_name?.split(' ').pop() || 'TBD' }}</span>
                      <span class="vs-tag">VS</span>
                      <span class="p-name">{{ match.p2_name?.split(' ').pop() || 'TBD' }}</span>
                    </div>
                    <div class="mc-footer">
                      <span class="mc-id">#{{ match.id }}</span>
                      <div class="status-indicator" :class="match.status"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <!-- Sidebar: Pending Matches -->
      <aside class="saas-sidebar-premium pending-block">
        <div class="saas-card-premium mini sidebar-header-saas">
          <div class="sh-left">
            <el-icon class="icon-pulse"><InfoFilled /></el-icon>
            <h4>Hàng chờ xếp lịch</h4>
          </div>
          <el-badge :value="pendingMatches.length" type="danger" />
        </div>

        <div class="pending-scroll-stack">
          <div v-if="pendingMatches.length" class="pending-list-saas">
            <div v-for="pm in pendingMatches" :key="pm.id" class="saas-pending-card" @click="scheduleFromPending(pm)">
              <div class="pc-head">
                <span class="pc-tour truncate">{{ pm.tournament }}</span>
                <span class="pc-round">{{ pm.round_code }}</span>
              </div>
              <div class="pc-body">
                <div class="pc-pair">
                  <div class="pc-p">{{ pm.p1_name || 'Chưa xác định' }}</div>
                  <div class="pc-vs">VS</div>
                  <div class="pc-p">{{ pm.p2_name || 'Chưa xác định' }}</div>
                </div>
              </div>
              <div class="pc-footer">
                <el-icon class="mr-1"><Promotion /></el-icon>
                <span>Click to schedule</span>
              </div>
            </div>
          </div>
          <el-empty v-else :image-size="80" description="No pending matches" />
        </div>
      </aside>
    </div>

    <!-- Schedule Dialog -->
    <el-dialog 
      v-model="isDialogOpen" 
      width="500px" 
      class="saas-dialog-premium"
      destroy-on-close
    >
      <template #header>
        <div class="dialog-header-saas">
          <el-icon class="mr-2"><Timer /></el-icon>
          <span>{{ isEditing ? 'Cập nhật lịch thi đấu' : 'Phân bổ trận đấu' }}</span>
        </div>
      </template>

      <div class="saas-dialog-content">
        <el-form label-position="top" class="saas-form-premium">
          <el-form-item label="Trận đấu đang chọn">
            <div class="saas-read-only-box">
              <el-icon class="mr-2"><VideoPlay /></el-icon>
              <strong>Trận #{{ form.match_id }}</strong>
            </div>
          </el-form-item>

          <div class="saas-form-grid">
            <el-form-item label="Chỉ định Sân" class="span-2">
              <el-select v-model="form.court_id" placeholder="Chọn sân thi đấu" class="w-full saas-input-large">
                <template #prefix><el-icon><LocationIcon /></el-icon></template>
                <el-option v-for="c in courts" :key="c.id" :label="c.court_name" :value="c.id" />
              </el-select>
            </el-form-item>

            <el-form-item label="Thời gian bắt đầu" class="span-2">
              <el-date-picker
                v-model="form.start_time"
                type="datetime"
                format="DD/MM/YYYY HH:mm"
                value-format="YYYY-MM-DDTHH:mm:ss"
                class="w-full saas-input-large"
              />
            </el-form-item>
          </div>
        </el-form>
      </div>

      <template #footer>
        <div class="saas-dialog-footer">
          <el-button @click="isDialogOpen = false" class="saas-btn-secondary">Hủy</el-button>
          <el-button type="primary" :loading="isSaving" @click="saveSchedule" class="saas-btn-primary">
            {{ isEditing ? 'Cập nhật' : 'Xác nhận xếp lịch' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.saas-container { display: flex; flex-direction: column; gap: 24px; height: calc(100vh - 40px); }

/* Action Bar */
.saas-header { display: flex; align-items: center; justify-content: space-between; }
.header-left { display: flex; align-items: center; }

.operation-badge-premium {
  background: #eff6ff; color: #2563eb; padding: 10px 20px; border-radius: 14px;
  font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
  display: inline-flex; align-items: center; margin-right: 24px;
}
.operation-badge-premium.indigo { background: #e0e7ff; color: #4f46e5; }

.header-titles { display: flex; flex-direction: column; gap: 4px; }
.saas-title { font-size: 1.6rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.02em; }
.saas-subtitle { font-size: 0.9rem; color: #64748b; margin: 0; font-weight: 600; }

.saas-date-navigator { display: flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #f1f5f9; padding: 6px; border-radius: 16px; margin-right: 16px; }
.nav-btn { border: none !important; background: #f8fafc !important; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 10px !important; color: #64748b; }
.nav-btn:hover { background: #eff6ff !important; color: #2563eb; }
.date-display-box { padding: 0 16px; font-weight: 800; color: #0f172a; font-size: 0.95rem; display: flex; align-items: center; }
.saas-btn-refresh { height: 48px !important; border-radius: 14px !important; font-weight: 800 !important; }

/* Layout Split */
.schedule-layout-saas { display: grid; grid-template-columns: 1fr 340px; gap: 24px; flex: 1; overflow: hidden; }

/* Timeline Main Area */
.schedule-main-block { padding: 0 !important; overflow: hidden; display: flex; flex-direction: column; }
.timeline-viewport { flex: 1; overflow: auto; display: flex; flex-direction: column; position: relative; }

.courts-row-sticky { display: flex; position: sticky; top: 0; z-index: 100; background: #fff; border-bottom: 2px solid #f1f5f9; }
.time-corner { width: 80px; min-width: 80px; height: 70px; background: #fafafa; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 0.7rem; color: #94a3b8; border-right: 1px solid #f1f5f9; }
.court-header-saas { flex: 1; min-width: 220px; height: 70px; display: flex; flex-direction: column; align-items: center; justify-content: center; border-right: 1px solid #f1f5f9; }
.court-header-saas .c-name { font-weight: 900; color: #0f172a; font-size: 1rem; }
.court-header-saas .c-loc { font-size: 0.7rem; color: #94a3b8; font-weight: 800; text-transform: uppercase; margin-top: 2px; }

.timeline-body { display: flex; flex: 1; position: relative; }
.time-track { width: 80px; min-width: 80px; background: #fafafa; border-right: 1px solid #f1f5f9; }
.hour-marker { height: 108px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: center; padding-top: 10px; }
.hour-marker span { font-size: 0.75rem; color: #94a3b8; font-weight: 800; }

.lanes-wrapper { display: flex; flex: 1; position: relative; }
.court-lane-saas { flex: 1; min-width: 220px; border-right: 1px solid #f1f5f9; position: relative; background-image: linear-gradient(#f1f5f9 1px, transparent 1px); background-size: 100% 108px; }
.lane-grid-cell { height: 108px; }

/* Visual Match Cards */
.saas-match-card-visual {
  position: absolute; left: 10px; right: 10px; border-radius: 16px;
  background: #fff; border: 1px solid #f1f5f9; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  display: flex; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
.saas-match-card-visual:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 12px 30px rgba(0,0,0,0.08); z-index: 50; }

.mc-accent { width: 6px; background: #cbd5e1; }
.saas-match-card-visual.completed .mc-accent { background: #10b981; }
.saas-match-card-visual.ongoing .mc-accent { background: #3b82f6; }
.saas-match-card-visual.scheduled .mc-accent { background: #f59e0b; }

.mc-content { flex: 1; padding: 12px; display: flex; flex-direction: column; gap: 4px; }
.mc-time { font-size: 0.75rem; font-weight: 900; color: #0f172a; display: flex; align-items: center; }
.mc-tour { font-size: 0.8rem; font-weight: 800; color: #2563eb; margin-bottom: 4px; }
.mc-versus { display: flex; align-items: center; justify-content: space-between; background: #f8fafc; padding: 6px 10px; border-radius: 10px; }
.p-name { font-size: 0.75rem; font-weight: 800; color: #1e293b; }
.vs-tag { font-size: 0.6rem; font-weight: 900; color: #ef4444; }
.mc-footer { display: flex; justify-content: space-between; align-items: center; margin-top: auto; padding-top: 8px; }
.mc-id { font-size: 0.65rem; color: #94a3b8; font-weight: 800; }
.status-indicator { width: 8px; height: 8px; border-radius: 50%; }
.status-indicator.completed { background: #10b981; box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1); }
.status-indicator.ongoing { background: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
.status-indicator.scheduled { background: #f59e0b; box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1); }

/* Sidebar Pending */
.pending-block { display: flex; flex-direction: column; gap: 16px; overflow: hidden; }
.sidebar-header-saas { padding: 20px !important; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
.sidebar-header-saas h4 { margin: 0; font-size: 1rem; font-weight: 900; color: #0f172a; }
.sh-left { display: flex; align-items: center; gap: 12px; }
.sh-left .el-icon { color: #ef4444; font-size: 20px; }

.pending-scroll-stack { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; padding-right: 4px; }
.saas-pending-card { 
  background: #fff; border-radius: 20px; padding: 18px; border: 1px solid #f1f5f9; 
  cursor: pointer; transition: all 0.3s;
}
.saas-pending-card:hover { transform: translateX(-6px); border-color: #2563eb; box-shadow: 0 8px 25px rgba(0,0,0,0.04); }

.pc-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.pc-tour { font-size: 0.8rem; font-weight: 900; color: #2563eb; }
.pc-round { font-size: 0.65rem; background: #eff6ff; color: #1e40af; padding: 4px 10px; border-radius: 8px; font-weight: 800; }
.pc-pair { display: flex; align-items: center; justify-content: space-between; background: #f8fafc; padding: 12px; border-radius: 14px; }
.pc-p { font-size: 0.85rem; font-weight: 800; color: #1e293b; max-width: 90px; text-align: center; }
.pc-vs { font-size: 0.7rem; font-weight: 900; color: #ef4444; }
.pc-footer { margin-top: 12px; display: flex; align-items: center; justify-content: center; color: #10b981; font-size: 0.75rem; font-weight: 800; background: #f0fdf4; padding: 8px; border-radius: 10px; }

/* Dialog Premium */
:deep(.saas-dialog-premium) { border-radius: 32px !important; overflow: hidden; }
:deep(.el-dialog__header) { padding: 0 !important; margin: 0 !important; }

.dialog-header-saas { padding: 24px 32px; background: #fafafa; border-bottom: 1px solid #f1f5f9; display: flex; align-items: center; font-weight: 900; color: #0f172a; font-size: 1.1rem; }
.saas-dialog-content { padding: 32px; }

.saas-read-only-box { 
  background: #f8fafc; padding: 16px; border-radius: 16px; border: 1px solid #f1f5f9; 
  display: flex; align-items: center; color: #1e293b; font-size: 1.1rem;
}

.saas-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.span-2 { grid-column: span 2; }
.saas-input-large :deep(.el-input__wrapper) { background: #f8fafc !important; border-radius: 14px !important; height: 50px; box-shadow: none !important; border: 1px solid #e2e8f0 !important; }

.saas-dialog-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 0 32px 32px; }
.saas-btn-secondary { height: 48px; border-radius: 12px; font-weight: 700; padding: 0 24px; border-color: #e2e8f0; }
.saas-btn-primary { height: 48px; border-radius: 12px; font-weight: 900; padding: 0 32px; background: #2563eb; border: none; }

.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mr-1 { margin-right: 4px; }
.mr-2 { margin-right: 8px; }
.w-full { width: 100%; }

.icon-pulse { animation: pulse-red 2s infinite; }
@keyframes pulse-red {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.7; }
  100% { transform: scale(1); opacity: 1; }
}
</style>