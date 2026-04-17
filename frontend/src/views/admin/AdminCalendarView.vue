<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '../../services/apiClient'
import { Calendar as CalendarIcon, Timer, Location, Trophy, Clock } from '@element-plus/icons-vue'

const matches = ref([])
const isLoading = ref(false)
const currentDate = ref(new Date())

// --- BIẾN CHO DIALOG CHI TIẾT NGÀY ---
const dialogVisible = ref(false)
const selectedDateStr = ref('')
const selectedDayMatches = ref([])

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
  return matches.value.filter(m => m.date === dateStr)
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
  <div class="calendar-module">
    <!-- HEADER PREMIUM - MERGED TITLES -->
    <section class="action-bar-glass shadow-sm">
      <div class="action-info">
        <div class="kicker-wrap">
          <span class="section-kicker">Operational Planning</span>
          <div class="live-indicator">
            <span class="dot"></span>
            LIVE
          </div>
        </div>
      </div>
    </section>

    <main class="calendar-card-premium shadow-sm" v-loading="isLoading">
      <el-calendar v-model="currentDate" class="modern-admin-calendar">
        <template #date-cell="{ data }">
          <div class="calendar-cell" @click="openDayDetail(data.day, getMatchesByDate(data.day))">
            <div class="day-header">
              <span class="day-num">{{ data.day.split('-').slice(2).join('') }}</span>
              <span v-if="getMatchesByDate(data.day).length > 0" class="m-count">{{ getMatchesByDate(data.day).length }}</span>
            </div>
            <div class="match-mini-chips">
              <div 
                v-for="m in getMatchesByDate(data.day).slice(0, 3)" 
                :key="m.id" 
                class="chip-item"
                :class="m.status"
              >
                {{ m.tournament }}
              </div>
              <div v-if="getMatchesByDate(data.day).length > 3" class="more-indicator">+ {{ getMatchesByDate(data.day).length - 3 }} trận nữa</div>
            </div>
          </div>
        </template>
      </el-calendar>
    </main>

    <el-dialog 
      v-model="dialogVisible" 
      :title="'Lịch thi đấu ngày ' + formatDate(selectedDateStr)" 
      width="550px" 
      class="day-dialog" 
      destroy-on-close
    >
      <div v-if="selectedDayMatches.length > 0" class="day-matches-list">
        
        <div v-for="match in selectedDayMatches" :key="match.id" class="day-match-card" :class="match.status">
          <div class="match-header">
            <h3>Trận #{{ match.id }}</h3>
            <el-tag effect="dark" :type="getStatusType(match.status)" class="status-tag">
              {{ getStatusName(match.status).toUpperCase() }}
            </el-tag>
          </div>

          <div class="info-grid">
            <div class="info-item">
              <el-icon><Trophy /></el-icon>
              <div class="info-text">
                <span>Giải đấu</span>
                <strong>{{ match.tournament }}</strong>
              </div>
            </div>

            <div class="info-item">
              <el-icon><Location /></el-icon>
              <div class="info-text">
                <span>Sân thi đấu</span>
                <strong>{{ match.court }}</strong>
              </div>
            </div>

            <div class="info-item" style="grid-column: span 2;">
              <el-icon><Clock /></el-icon>
              <div class="info-text">
                <span>Giờ thi đấu</span>
                <strong>{{ match.start !== '--:--' ? match.start : 'Chưa xếp giờ' }}</strong>
              </div>
            </div>
          </div>
        </div>

      </div>
      <el-empty v-else description="Không có trận đấu nào được xếp trong ngày này." />
      
      <template #footer>
        <el-button type="primary" @click="dialogVisible = false">Đóng lại</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.calendar-module { display: grid; gap: 16px; padding: 10px; }

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

.action-bar-glass h2 { margin: 0; font-size: 1.25rem; color: #0f172a; font-weight: 700; }
.action-bar-glass p { margin: 2px 0 0 0; color: #64748b; font-size: 0.85rem; }

.hero-actions-v2 { display: flex; align-items: center; gap: 12px; }

.calendar-card-premium {
  background: white; border-radius: 20px; border: 1px solid #f1f5f9;
  box-shadow: 0 10px 30px rgba(0,0,0,0.03); overflow: hidden;
}

.calendar-cell { height: 100%; display: flex; flex-direction: column; gap: 4px; }
.day-header { display: flex; justify-content: space-between; align-items: center; }
.day-num { font-weight: 900; font-size: 1.1rem; color: #1e293b; }
.m-count { font-size: 0.65rem; background: #eff6ff; color: #3b82f6; width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; }

.match-mini-chips { display: flex; flex-direction: column; gap: 3px; }
.chip-item { 
  font-size: 0.6rem; padding: 2px 6px; border-radius: 4px; font-weight: 700;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  background: #f1f5f9; border-left: 2px solid #94a3b8; color: #475569;
}
.chip-item.completed { background: #f0fdf4; border-left-color: #10b981; color: #166534; }
.chip-item.ongoing { background: #eff6ff; border-left-color: #3b82f6; color: #1e40af; }
.chip-item.scheduled { background: #fffbeb; border-left-color: #f59e0b; color: #854d0e; }
.more-indicator { font-size: 0.55rem; color: #94a3b8; font-weight: 700; margin-top: 2px; }

:deep(.modern-admin-calendar) { border: none !important; }
:deep(.modern-admin-calendar .el-calendar-day) { height: 110px !important; padding: 12px !important; transition: all 0.2s ease; }
:deep(.modern-admin-calendar .el-calendar-day:hover) { background: #f8fafc; }
:deep(.modern-admin-calendar .is-today .day-num) { color: #3b82f6; text-decoration: underline; }

/* Dialog detail */
.day-matches-list { display: grid; gap: 12px; padding: 4px; }
.day-match-card {
  background: white; border: 1px solid #f1f5f9; border-left: 4px solid #94a3b8;
  border-radius: 16px; padding: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);
}
.day-match-card.completed { border-left-color: #10b981; }
.day-match-card.ongoing { border-left-color: #3b82f6; }
.day-match-card.scheduled { border-left-color: #f59e0b; }

.match-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.match-header h3 { margin: 0; font-size: 1rem; color: #0f172a; font-weight: 800; }
.status-tag { font-weight: 800; border-radius: 99px; padding: 0 12px; font-size: 0.6rem; border: none !important; }

.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.info-item { display: flex; gap: 12px; align-items: flex-start; }
.info-item .el-icon { color: #3b82f6; font-size: 1.1rem; }
.info-text { display: flex; flex-direction: column; }
.info-text span { font-size: 0.65rem; color: #94a3b8; text-transform: uppercase; font-weight: 800; margin-bottom: 2px; }
.info-text strong { font-size: 0.85rem; color: #1e293b; font-weight: 700; }

.shadow-sm { box-shadow: 0 1px 3px rgba(0,0,0,0.05); }</style>