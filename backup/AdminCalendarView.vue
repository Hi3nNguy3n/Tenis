<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '../../services/apiClient'
import { 
  Calendar as CalendarIcon, Timer, Location as LocationIcon, Trophy, Clock as ClockIcon,
  Monitor, Connection, ArrowLeft, CircleCheckFilled,
  VideoPlay, InfoFilled
} from '@element-plus/icons-vue'

const matches = ref([])
const isLoading = ref(false)
const currentDate = ref(new Date())

// --- BIẾN CHO DIALOG CHI TIẾT NGÀY ---
const dialogVisible = ref(false)
const selectedDateStr = ref('')
const selectedDayMatches = ref([])

const normalizeDateKey = (value) => {
  if (!value) return ''
  if (typeof value !== 'string') return ''
  const match = value.match(/^(\d{4}-\d{2}-\d{2})/)
  return match ? match[1] : value
}

const fetchMatches = async () => {
  isLoading.value = true
  try {
    const data = await apiClient.get('/api/tournaments/matches/all')
    matches.value = data
  } catch (err) {
    console.error('Lỗi tải lịch:', err)
  } finally {
    isLoading.value = false
  }
}

const getMatchesByDate = (dateStr) => {
  const dayKey = normalizeDateKey(dateStr)
  return matches.value.filter(m => normalizeDateKey(m.date || m.start_time) === dayKey)
}

// --- HÀM MỞ POPUP HIỂN THỊ DANH SÁCH TRẬN THEO NGÀY ---
const openDayDetail = (dateStr, dayMatches) => {
  selectedDateStr.value = dateStr
  selectedDayMatches.value = dayMatches
  dialogVisible.value = true
}

const getStatusName = (status) => {
  const map = { 'scheduled': 'Đã lên lịch', 'ongoing': 'Đang thi đấu', 'completed': 'Đã kết thúc', 'pending': 'Chờ xếp lịch' }
  return map[status] || status
}

const getStatusType = (status) => {
  const map = { 'scheduled': 'warning', 'completed': 'success', 'ongoing': 'primary', 'pending': 'info' }
  return map[status] || 'info'
}

// Format ngày từ YYYY-MM-DD sang DD/MM/YYYY cho tiêu đề đẹp hơn
const formatDate = (dateString) => {
  if(!dateString) return ''
  const parts = dateString.split('-')
  if(parts.length !== 3) return dateString
  return `${parts[2]}/${parts[1]}/${parts[0]}`
}

onMounted(fetchMatches)
</script>

<template>
  <div class="saas-container" v-loading="isLoading">
    <!-- Action Bar -->
    <section class="saas-header">
      <div class="header-left">
        <div class="operation-badge-premium blue">
          <el-icon class="mr-1"><CalendarIcon /></el-icon>
          <span>Operational Calendar</span>
        </div>
        <div class="header-titles">
          <h2 class="saas-title">{{ $t('admin.matchSchedule') || 'Lịch Thi Đấu Tổng Thể' }}</h2>
          <p class="saas-subtitle">{{ $t('admin.calendarDesc') || 'Quản lý và điều phối lịch trình các giải đấu' }}</p>
        </div>
      </div>
      <div class="header-right">
        <div class="live-status-pill">
          <span class="pulse-dot"></span>
          <span>SYSTEM LIVE</span>
        </div>
      </div>
    </section>

    <!-- Main Calendar Area -->
    <main class="saas-content-area calendar-viewport">
      <el-calendar v-model="currentDate" class="saas-calendar-premium">
        <template #date-cell="{ data }">
          <div class="saas-date-cell" @click="openDayDetail(data.day, getMatchesByDate(data.day))">
            <div class="cell-head">
              <span class="cell-num">{{ data.day.split('-').pop() }}</span>
              <el-badge v-if="getMatchesByDate(data.day).length > 0" :value="getMatchesByDate(data.day).length" class="cell-badge" />
            </div>
            
            <div class="cell-content">
              <div 
                v-for="m in getMatchesByDate(data.day).slice(0, 2)" 
                :key="m.id" 
                class="saas-match-chip"
                :class="m.status"
              >
                <div class="chip-dot"></div>
                <span class="chip-text">{{ m.tournament }}</span>
              </div>
              <div v-if="getMatchesByDate(data.day).length > 2" class="saas-more-tag">
                +{{ getMatchesByDate(data.day).length - 2 }} matches
              </div>
            </div>
          </div>
        </template>
      </el-calendar>
    </main>

    <!-- Day Detail Dialog -->
    <el-dialog 
      v-model="dialogVisible" 
      width="600px" 
      class="saas-dialog-premium"
      destroy-on-close
    >
      <template #header>
        <div class="dialog-header-saas">
          <el-icon class="mr-2"><Timer /></el-icon>
          <span>Lịch thi đấu ngày {{ formatDate(selectedDateStr) }}</span>
        </div>
      </template>

      <div class="saas-dialog-content">
        <div v-if="selectedDayMatches.length > 0" class="dialog-matches-stack">
          <div v-for="match in selectedDayMatches" :key="match.id" class="saas-match-item-card" :class="match.status">
            <div class="mi-header">
              <span class="mi-no">#{{ match.id }}</span>
              <el-tag effect="dark" :type="getStatusType(match.status)" size="small" class="saas-status-tag">
                {{ getStatusName(match.status).toUpperCase() }}
              </el-tag>
            </div>
            
            <div class="mi-body">
              <div class="mi-info-row">
                <el-icon><Trophy /></el-icon>
                <div class="mi-info">
                  <span class="label">Giải đấu</span>
                  <strong class="value">{{ match.tournament }}</strong>
                </div>
              </div>
              
              <div class="mi-info-row">
                <el-icon><LocationIcon /></el-icon>
                <div class="mi-info">
                  <span class="label">Sân thi đấu</span>
                  <strong class="value">{{ match.court }}</strong>
                </div>
              </div>

              <div class="mi-info-row">
                <el-icon><ClockIcon /></el-icon>
                <div class="mi-info">
                  <span class="label">Giờ thi đấu</span>
                  <strong class="value">{{ match.start !== '--:--' ? match.start : 'Chưa xếp giờ' }}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else :description="'Không có trận đấu nào trong ngày này'" />
      </div>

      <template #footer>
        <div class="saas-dialog-footer">
          <el-button @click="dialogVisible = false" class="saas-btn-secondary">Đóng</el-button>
          <el-button type="primary" @click="dialogVisible = false" class="saas-btn-primary">OK</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.saas-container { display: flex; flex-direction: column; gap: 32px; min-height: 100%; }

/* Action Bar */
.saas-header { display: flex; align-items: center; justify-content: space-between; }
.header-left { display: flex; align-items: center; }

.operation-badge-premium {
  background: #eff6ff; color: #2563eb; padding: 10px 20px; border-radius: 14px;
  font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
  display: inline-flex; align-items: center; margin-right: 24px;
}
.operation-badge-premium.blue { background: #eff6ff; color: #2563eb; }

.header-titles { display: flex; flex-direction: column; gap: 4px; }
.saas-title { font-size: 1.8rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.02em; }
.saas-subtitle { font-size: 0.95rem; color: #64748b; margin: 0; }

.live-status-pill {
  display: flex; align-items: center; gap: 10px; background: #f0fdf4; color: #166534;
  padding: 8px 16px; border-radius: 99px; font-weight: 800; font-size: 0.75rem;
}
.pulse-dot { width: 8px; height: 8px; background: #10b981; border-radius: 50%; animation: pulse-green 2s infinite; }

@keyframes pulse-green {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* Calendar Area */
.saas-content-area { background: #fff; border-radius: 32px; border: 1px solid #f1f5f9; box-shadow: 0 10px 40px rgba(0,0,0,0.02); overflow: hidden; padding: 0; }

:deep(.saas-calendar-premium) { border: none !important; }
:deep(.saas-calendar-premium .el-calendar__header) { padding: 32px; border-bottom: 1px solid #f1f5f9; }
:deep(.saas-calendar-premium .el-calendar__title) { font-weight: 900; color: #0f172a; font-size: 1.25rem; text-transform: capitalize; }
:deep(.saas-calendar-premium .el-calendar-day) { height: 140px !important; padding: 12px !important; transition: all 0.3s; }
:deep(.saas-calendar-premium .el-calendar-day:hover) { background: #f8fafc; }
:deep(.saas-calendar-premium .is-today) { background: #f0f7ff !important; }
:deep(.saas-calendar-premium .el-calendar-table thead th) { padding: 16px; color: #94a3b8; font-weight: 800; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; }

.saas-date-cell { height: 100%; display: flex; flex-direction: column; gap: 8px; cursor: pointer; }
.cell-head { display: flex; justify-content: space-between; align-items: center; }
.cell-num { font-size: 1.1rem; font-weight: 900; color: #1e293b; }
:deep(.cell-badge .el-badge__content) { background: #2563eb; font-weight: 900; border: none; }

.cell-content { display: flex; flex-direction: column; gap: 4px; }
.saas-match-chip {
  padding: 4px 10px; border-radius: 8px; font-size: 0.7rem; font-weight: 800;
  display: flex; align-items: center; gap: 6px; white-space: nowrap; overflow: hidden;
}
.chip-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.chip-text { text-overflow: ellipsis; overflow: hidden; }

.saas-match-chip.completed { background: #f0fdf4; color: #166534; }
.saas-match-chip.ongoing { background: #eff6ff; color: #1e40af; }
.saas-match-chip.scheduled { background: #fffbeb; color: #92400e; }
.saas-match-chip.pending { background: #f8fafc; color: #64748b; }

.saas-more-tag { font-size: 0.65rem; color: #94a3b8; font-weight: 800; margin-top: 4px; text-align: center; }

/* Dialog Premium */
:deep(.saas-dialog-premium) { border-radius: 32px !important; overflow: hidden; }
:deep(.el-dialog__header) { padding: 0 !important; margin: 0 !important; }

.dialog-header-saas { padding: 32px; background: #fafafa; border-bottom: 1px solid #f1f5f9; display: flex; align-items: center; font-weight: 900; color: #0f172a; font-size: 1.1rem; }

.saas-dialog-content { padding: 32px; }
.dialog-matches-stack { display: flex; flex-direction: column; gap: 16px; max-height: 500px; overflow-y: auto; padding-right: 10px; }

.saas-match-item-card {
  background: #fff; border: 1px solid #f1f5f9; border-left: 6px solid #e2e8f0;
  border-radius: 20px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.02);
  transition: all 0.3s;
}
.saas-match-item-card:hover { transform: translateX(8px); box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
.saas-match-item-card.completed { border-left-color: #10b981; }
.saas-match-item-card.ongoing { border-left-color: #3b82f6; }
.saas-match-item-card.scheduled { border-left-color: #f59e0b; }

.mi-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.mi-no { font-family: monospace; font-weight: 800; color: #94a3b8; font-size: 0.8rem; }
.saas-status-tag { border-radius: 8px; font-weight: 900; font-size: 0.65rem; letter-spacing: 0.05em; padding: 0 12px; border: none; }

.mi-body { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.mi-info-row { display: flex; gap: 12px; align-items: flex-start; }
.mi-info-row .el-icon { color: #3b82f6; font-size: 1.1rem; margin-top: 4px; }
.mi-info { display: flex; flex-direction: column; gap: 2px; }
.mi-info .label { font-size: 0.65rem; color: #94a3b8; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; }
.mi-info .value { font-size: 0.95rem; color: #1e293b; font-weight: 700; line-height: 1.4; }

.saas-dialog-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 0 32px 32px; }
.saas-btn-secondary { height: 48px; border-radius: 12px; font-weight: 700; padding: 0 24px; border-color: #e2e8f0; }
.saas-btn-primary { height: 48px; border-radius: 12px; font-weight: 900; padding: 0 32px; background: #2563eb; border: none; }

.mr-1 { margin-right: 4px; }
.mr-2 { margin-right: 8px; }
</style>
