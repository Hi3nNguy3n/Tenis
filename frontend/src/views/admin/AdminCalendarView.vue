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
    <section class="hero-card">
      <div>
        <span class="section-kicker">Operational Planning</span>
        <h2>Lịch thi đấu (Calendar View)</h2>
        <p>Theo dõi mật độ trận đấu trên toàn hệ thống. Click vào bất kỳ ngày nào để xem danh sách trận.</p>
      </div>
      <el-button type="primary" plain :icon="Timer" @click="fetchMatches">Làm mới dữ liệu</el-button>
    </section>

    <el-card shadow="never" class="calendar-wrapper" v-loading="isLoading">
      <el-calendar v-model="currentDate">
        <template #date-cell="{ data }">
          <div class="calendar-cell" @click="openDayDetail(data.day, getMatchesByDate(data.day))">
            <span class="day-label">{{ data.day.split('-').slice(2).join('') }}</span>
            <div class="match-list">
              <div 
                v-for="m in getMatchesByDate(data.day)" 
                :key="m.id" 
                class="match-item"
                :class="m.status"
              >
                <span class="match-time">{{ m.start !== '--:--' ? m.start : 'N/A' }}</span>
                <span class="match-name">{{ m.tournament }}</span>
              </div>
            </div>
          </div>
        </template>
      </el-calendar>
    </el-card>

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
.calendar-module { display: flex; flex-direction: column; gap: 20px; }
.hero-card { border-radius: 8px; background: white; padding: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center; }
.section-kicker { display: inline-flex; margin-bottom: 12px; padding: 8px 12px; border-radius: 8px; background: rgba(20, 98, 80, 0.08); color: #0f5c4d; font-size: 0.74rem; font-weight: 800; text-transform: uppercase; }
h2 { margin: 0 0 5px 0; font-size: 2.2rem; color: #132722; }

.calendar-wrapper { border-radius: 8px; border: none; padding: 10px; }

/* Tùy chỉnh ô lịch */
.calendar-cell { height: 100%; display: flex; flex-direction: column; cursor: pointer; }
.day-label { font-weight: 900; font-size: 1.2rem; color: #1e293b; margin-bottom: 5px; }

.match-list { display: flex; flex-direction: column; gap: 4px; overflow-y: auto; max-height: 80px; }
.match-item { 
  font-size: 0.65rem; padding: 4px 6px; border-radius: 6px; display: flex; gap: 5px; 
  background: #f1f5f9; border-left: 3px solid #94a3b8;
}
.match-item.completed { background: #dcfce7; color: #166534; border-left-color: #166534; }
.match-item.ongoing { background: #dbeafe; color: #1e40af; border-left-color: #1e40af; }
.match-item.scheduled { background: #fef9c3; color: #854d0e; border-left-color: #eab308; }

.match-time { font-weight: bold; min-width: 35px; }
.match-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

:deep(.el-calendar-table .el-calendar-day) { height: 120px; padding: 10px; transition: 0.2s; }
:deep(.el-calendar-table .el-calendar-day:hover) { background-color: #f0f7f5; }

/* CSS CHO DIALOG DANH SÁCH NGÀY */
.day-matches-list { display: flex; flex-direction: column; gap: 15px; max-height: 60vh; overflow-y: auto; padding-right: 5px; }
.day-match-card { background: #f8fafc; border: 1px solid #e2e8f0; border-left: 5px solid #94a3b8; border-radius: 12px; padding: 16px; }
.day-match-card.completed { border-left-color: #166534; }
.day-match-card.ongoing { border-left-color: #1e40af; }
.day-match-card.scheduled { border-left-color: #eab308; }

.match-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px dashed #cbd5e1; }
.match-header h3 { margin: 0; font-size: 1.2rem; color: #0f172a; }

.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
.info-item { display: flex; gap: 10px; align-items: flex-start; }
.info-item .el-icon { font-size: 1.3rem; color: #0f5c4d; margin-top: 2px; }
.info-text { display: flex; flex-direction: column; gap: 2px; }
.info-text span { font-size: 0.7rem; color: #64748b; text-transform: uppercase; font-weight: 800; }
.info-text strong { font-size: 0.95rem; color: #1e293b; }
</style>