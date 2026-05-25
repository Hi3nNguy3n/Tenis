<script setup>
import { onMounted, ref, computed, watch, onBeforeUnmount } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, Download, Edit, Location as LocationIcon, Timer,
  Trophy, Monitor, Connection, ArrowLeft, ArrowRight,
  CircleCheckFilled, Message, Search, Filter,
  Calendar as CalendarIcon, Operation, VideoPlay, Clock as ClockIcon,
  Right, Calendar, InfoFilled, Promotion
} from '@element-plus/icons-vue'
import { t } from '../../utils/locale'

// --- GLOBAL STATE ---
const viewMode = ref('grid') // calendar, grid, timeline
const pendingTab = ref('today') // today, overdue

const isLoading = ref(false)
const isSaving = ref(false)
const selectedDate = ref(new Date().toISOString().split('T')[0])
const allMatches = ref([])
const courts = ref([])
const showEditDialog = ref(false)
const editingMatch = ref(null)

const form = ref({
  court_id: null,
  start_time: '08:00'
})

// --- COMPUTED ---
const groupedSchedule = computed(() => {
  const groups = {}
  allMatches.value.forEach(m => {
    // Lọc nghiêm ngặt: Trận đấu phải có thời gian và bắt đầu bằng ngày đang chọn
    if (m.start_time && m.start_time.startsWith(selectedDate.value)) {
      if (!groups[m.tournament]) groups[m.tournament] = []
      groups[m.tournament].push({
        ...m,
        start: m.start_time.split('T')[1].substring(0, 5)
      })
    }
  })
  return groups
})

const filteredPending = computed(() => {
  return allMatches.value.filter(m => {
    const isPending = !m.court_id && m.status === 'pending'
    if (!isPending) return false
    
    const tourEndDate = m.tournament_end_date ? m.tournament_end_date.split('T')[0] : null
    const matchDate = m.start_time ? m.start_time.split('T')[0] : null
    
    // Một trận bị Tồn đọng (Overdue) nếu:
    // 1. Giải đấu đã kết thúc so với ngày đang xem (selectedDate)
    // 2. Hoặc ngày dự kiến của trận đấu nhỏ hơn ngày đang xem
    const isOverdue = (tourEndDate && tourEndDate < selectedDate.value) || (matchDate && matchDate < selectedDate.value)
    
    if (pendingTab.value === 'today') {
      // Hiện trận KHÔNG tồn đọng và (chưa có ngày HOẶC đúng ngày đang chọn)
      return !isOverdue && (!matchDate || matchDate === selectedDate.value)
    } else {
      return isOverdue
    }
  })
})

const groupedPending = computed(() => {
  const groups = {}
  filteredPending.value.forEach(m => {
    if (!groups[m.tournament]) groups[m.tournament] = []
    groups[m.tournament].push(m)
  })
  return groups
})

// --- DATA LOADING ---
const fetchData = async () => {
  isLoading.value = true
  try {
    // We fetch all matches to support calendar view and daily views
    const [matchesData, courtsData] = await Promise.all([
      apiClient.get('/api/matches/'),
      apiClient.get('/api/courts/', { params: { status: 'AVAILABLE' } })
    ])
    allMatches.value = matchesData
    courts.value = courtsData
  } catch (err) {
    ElMessage.error(t('admin.loadError') || 'Lỗi tải dữ liệu: ' + err.message)
  } finally {
    isLoading.value = false
  }
}

// --- DATE NAVIGATION ---
const changeDate = (days) => {
  const date = new Date(`${selectedDate.value}T12:00:00`)
  date.setDate(date.getDate() + days)
  selectedDate.value = date.toISOString().split('T')[0]
}

const goToToday = () => {
  selectedDate.value = new Date().toISOString().split('T')[0]
}

// --- CALENDAR LOGIC ---
const normalizeDateKey = (value) => {
  if (!value || typeof value !== 'string') return ''
  const match = value.match(/^(\d{4}-\d{2}-\d{2})/)
  return match ? match[1] : value
}

const getMatchesByDate = (dateStr) => {
  const dayKey = normalizeDateKey(dateStr)
  return allMatches.value.filter(m => normalizeDateKey(m.date || m.start_time) === dayKey)
}

const handleCalendarDateClick = (dateStr) => {
  selectedDate.value = dateStr
  viewMode.value = 'grid' // Switch to grid view on click
}

// --- GRID (ORDER OF PLAY) LOGIC ---
const timeSlots = Array.from({ length: 18 }, (_, i) => i + 6) // 6:00 to 23:00

const gridMatches = computed(() => {
  return allMatches.value.filter(m => 
    m.start_time && 
    m.start_time.startsWith(selectedDate.value) && 
    m.court_id && 
    m.start !== '--:--'
  )
})

const getMatchesForCourt = (courtId) => {
  return gridMatches.value.filter(m => m.court_id === courtId)
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

// --- EDIT/SCHEDULE DIALOG ---
const handleEdit = (match) => {
  editingMatch.value = match
  
  let startTime = match.start_time
  if (!startTime || startTime === '--:--') {
    // Nếu giải đấu đã kết thúc, gợi ý ngày cuối cùng của giải
    const tourEndDate = match.tournament_end_date ? match.tournament_end_date.split('T')[0] : null
    if (tourEndDate && tourEndDate < selectedDate.value) {
      startTime = `${tourEndDate}T08:00:00`
    } else {
      startTime = `${selectedDate.value}T08:00:00`
    }
  }
  
  form.value = {
    court_id: match.court_id || null,
    start_time: startTime
  }
  showEditDialog.value = true
}

onBeforeUnmount(() => {
  showEditDialog.value = false
})

const disabledMatchDate = (time) => {
  if (!editingMatch.value) return false
  
  const start = editingMatch.value.tournament_start_date ? new Date(editingMatch.value.tournament_start_date) : null
  const end = editingMatch.value.tournament_end_date ? new Date(editingMatch.value.tournament_end_date) : null
  
  if (start) {
    start.setHours(0, 0, 0, 0)
    if (time.getTime() < start.getTime()) return true
  }
  if (end) {
    end.setHours(23, 59, 59, 999)
    if (time.getTime() > end.getTime()) return true
  }
  return false
}

const handleSave = async () => {
  if (!form.value.court_id || !form.value.start_time) {
    ElMessage.warning('Vui lòng chọn đầy đủ sân và giờ')
    return
  }

  try {
    isSaving.value = true
    // start_time từ el-date-picker đã là format ISO YYYY-MM-DDTHH:mm:ss
    const payload = {
      court_id: form.value.court_id,
      start_time: form.value.start_time
    }
    
    await apiClient.post(`/api/tournaments/matches/${editingMatch.value.id}/schedule`, payload)
    
    ElMessage.success('Xếp lịch thành công')
    showEditDialog.value = false
    await fetchData()
  } catch (error) {
    console.error('Lỗi xếp lịch:', error)
    const detail = error.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : 'Không thể cập nhật lịch thi đấu')
  } finally {
    isSaving.value = false
  }
}

const getStatusType = (s) => {
  const status = s?.toLowerCase()
  if (status === 'ongoing') return 'primary'
  if (status === 'completed' || status === 'finished') return 'success'
  if (status === 'scheduled') return 'warning'
  if (status === 'canceled') return 'danger'
  return 'info'
}

const handleCancel = (match) => {
  ElMessageBox.confirm(
    'Bạn có chắc chắn muốn hủy trận đấu này không? Trận đấu sẽ được đánh dấu là Canceled và gỡ khỏi hàng chờ.',
    'Xác nhận hủy trận',
    {
      confirmButtonText: 'Xác nhận hủy',
      cancelButtonText: 'Quay lại',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    }
  ).then(async () => {
    try {
      await apiClient.delete(`/api/matches/${match.id}`)
      ElMessage.success('Đã hủy trận đấu thành công')
      await fetchData()
    } catch (error) {
      console.error('Lỗi khi hủy trận:', error)
      ElMessage.error('Không thể hủy trận đấu')
    }
  }).catch(() => {})
}

onMounted(fetchData)
</script>

<template>
  <div class="saas-container" v-loading="isLoading">
    <!-- Action Bar -->
    <section class="saas-header-compact">
      <div class="header-left-compact">
        <!-- View Switcher Cố định -->
        <el-radio-group v-model="viewMode" size="large" class="saas-view-switcher-premium">
          <el-radio-button value="calendar">
            <el-icon><CalendarIcon /></el-icon> Lịch tháng
          </el-radio-button>
          <el-radio-button value="grid">
            <el-icon><Operation /></el-icon> Sơ đồ sân
          </el-radio-button>
          <el-radio-button value="timeline">
            <el-icon><Timer /></el-icon> Danh sách
          </el-radio-button>
        </el-radio-group>
      </div>
      
      <div class="header-right-compact">

        <!-- Global Date Controls -->
        <div v-if="viewMode !== 'calendar'" class="saas-date-navigator mr-4">
          <el-button @click="changeDate(-1)" class="nav-btn"><el-icon><ArrowLeft /></el-icon></el-button>
          <el-date-picker 
            v-model="selectedDate" 
            type="date" 
            value-format="YYYY-MM-DD" 
            :clearable="false"
            class="saas-date-picker-mini"
          />
          <el-button @click="changeDate(1)" class="nav-btn"><el-icon><ArrowRight /></el-icon></el-button>
        </div>

        <el-button v-if="viewMode !== 'calendar'" @click="goToToday" class="saas-btn-today mr-2">Hôm nay</el-button>
        <el-button @click="fetchData" :icon="Refresh" class="saas-btn-refresh" circle></el-button>
        <el-button type="primary" :icon="Download" class="saas-btn-primary ml-2">{{ $t('admin.exportData') }}</el-button>
      </div>
    </section>

    <!-- CONTENT AREA -->
    <transition name="fade-slide" mode="out-in">
      <!-- 1. CALENDAR VIEW -->
      <div v-if="viewMode === 'calendar'" key="calendar" class="calendar-viewport saas-card-premium">
        <el-calendar class="saas-calendar-premium">
          <template #date-cell="{ data }">
            <div class="saas-date-cell" @click="handleCalendarDateClick(data.day)">
              <div class="cell-head">
                <span class="cell-num">{{ data.day.split('-').pop() }}</span>
                <el-badge v-if="getMatchesByDate(data.day).length > 0" :value="getMatchesByDate(data.day).length" class="cell-badge" />
              </div>
              <div class="cell-content">
                <div v-for="m in getMatchesByDate(data.day).slice(0, 2)" :key="m.id" class="saas-match-chip" :class="m.status">
                  <div class="chip-dot"></div>
                  <span class="chip-text">{{ m.tournament }}</span>
                </div>
                <div v-if="getMatchesByDate(data.day).length > 2" class="saas-more-tag">+{{ getMatchesByDate(data.day).length - 2 }} matches</div>
              </div>
            </div>
          </template>
        </el-calendar>
      </div>

      <!-- 2. GRID (ORDER OF PLAY) VIEW -->
      <div v-else-if="viewMode === 'grid'" key="grid" class="schedule-layout-saas">
        <main class="saas-card-premium grid-main-block">
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
              <div class="time-track">
                <div v-for="hour in timeSlots" :key="hour" class="hour-marker">
                  <span>{{ hour.toString().padStart(2, '0') }}:00</span>
                </div>
              </div>
              <div class="lanes-wrapper">
                <div v-for="court in courts" :key="court.id" class="court-lane-saas">
                  <div v-for="hour in timeSlots" :key="'g'+hour" class="lane-grid-cell"></div>
                  <!-- Match Cards in Grid -->
                  <div v-for="match in getMatchesForCourt(court.id)" :key="match.id" class="saas-match-card-visual" :class="match.status" :style="getMatchStyle(match.start)" @click="handleEdit(match)">
                    <div class="mc-accent"></div>
                    <div class="mc-content">
                      <div class="mc-time"><el-icon class="mr-1"><ClockIcon /></el-icon>{{ match.start }}</div>
                      <div class="mc-tour truncate">{{ match.tournament }}</div>
                      <div class="mc-versus">
                        <span class="p-name">{{ (match.p1_name || match.side_a_name)?.split(' ').pop() || 'TBD' }}</span>
                        <span class="vs-tag">VS</span>
                        <span class="p-name">{{ (match.p2_name || match.side_b_name)?.split(' ').pop() || 'TBD' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
        <!-- Sidebar Pending -->
        <aside class="saas-sidebar-premium pending-block">
          <div class="saas-card-premium mini sidebar-header-saas">
            <div class="sh-left">
              <el-icon class="icon-pulse"><InfoFilled /></el-icon>
              <h4>Hàng chờ xếp lịch</h4>
            </div>
            <el-badge :value="filteredPending.length" :type="pendingTab === 'overdue' ? 'danger' : 'primary'" />
          </div>

          <!-- Pending Tabs -->
          <div class="pending-tabs-container">
            <el-radio-group v-model="pendingTab" size="small" class="saas-tabs-mini">
              <el-radio-button value="today">Hôm nay</el-radio-button>
              <el-radio-button value="overdue">Tồn đọng</el-radio-button>
            </el-radio-group>
          </div>

          <div class="pending-scroll-stack">
            <div v-if="filteredPending.length > 0">
              <div v-for="(matches, tourName) in groupedPending" :key="tourName" class="pending-tour-group">
                <div class="tour-group-label">{{ tourName }}</div>
                <div v-for="pm in matches" :key="pm.id" class="saas-pending-card" :class="{ 'is-overdue': pendingTab === 'overdue' }" @click="handleEdit(pm)">
                  <div class="pc-head">
                    <span class="pc-round">{{ pm.round_code || pm.round }}</span>
                    <span v-if="pm.start_time" class="pc-date-tag">{{ pm.start_time.split('T')[0] }}</span>
                  </div>
                  <div class="pc-pair">
                    <div class="pc-p">{{ pm.p1_name || pm.side_a_name || 'Chưa xác định' }}</div>
                    <div class="pc-vs">VS</div>
                    <div class="pc-p">{{ pm.p2_name || pm.side_b_name || 'Chưa xác định' }}</div>
                  </div>
                  <div class="pc-footer">
                    <div class="pc-footer-left">
                      <el-icon class="mr-1"><Promotion /></el-icon>
                      <span>{{ pendingTab === 'overdue' ? 'Dời lịch' : 'Click để xếp lịch' }}</span>
                    </div>
                    <el-button 
                      v-if="pendingTab === 'overdue'" 
                      link 
                      type="danger" 
                      size="small" 
                      @click.stop="handleCancel(pm)"
                      class="pc-cancel-btn"
                    >
                      Hủy trận
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
            <el-empty v-else :description="pendingTab === 'today' ? 'Không có trận chờ hôm nay' : 'Không có trận tồn đọng'" />
          </div>
        </aside>
      </div>

      <!-- 3. TIMELINE (LIST) VIEW -->
      <div v-else-if="viewMode === 'timeline'" key="timeline" class="timeline-list-viewport">
        <div v-if="Object.keys(groupedSchedule).length === 0" class="empty-state">
          <el-empty :description="$t('admin.noScheduleMatch')" />
        </div>
        <div v-for="(matches, tournament) in groupedSchedule" :key="tournament" class="tournament-group">
          <div class="tournament-header">
            <div class="th-title">
              <div class="th-icon"><el-icon><Trophy /></el-icon></div>
              <h3>{{ tournament }}</h3>
            </div>
            <el-tag size="small" effect="plain" type="info">{{ matches.length }} Trận đấu</el-tag>
          </div>
          <div class="match-grid">
            <div v-for="match in matches" :key="match.id" class="match-card-premium">
              <div class="mc-time-side">
                <span class="mc-time">{{ match.start }}</span>
                <div class="mc-timeline-dot"></div>
              </div>
              <div class="mc-main-content">
                <div class="mc-top">
                  <div class="mc-court"><el-icon><LocationIcon /></el-icon><span>{{ match.court || 'Chưa gán sân' }}</span></div>
                  <el-tag :type="getStatusType(match.status)" size="small" class="mc-status">{{ match.status?.toUpperCase() }}</el-tag>
                </div>
                <div class="mc-players">
                  <div class="player-item">
                    <div class="p-avatar">{{ (match.p1_name || match.side_a_name)?.charAt(0) || 'A' }}</div>
                    <span class="p-name">{{ match.p1_name || match.side_a_name || 'Đang đợi...' }}</span>
                  </div>
                  <div class="vs-divider">VS</div>
                  <div class="player-item">
                    <div class="p-avatar">{{ (match.p2_name || match.side_b_name)?.charAt(0) || 'B' }}</div>
                    <span class="p-name">{{ match.p2_name || match.side_b_name || 'Đang đợi...' }}</span>
                  </div>
                </div>
                <div class="mc-footer">
                  <div class="mc-info-items"><span v-if="match.round_code || match.round" class="mc-info-tag">{{ $t('admin.round') }}: {{ match.round_code || match.round }}</span></div>
                  <div class="mc-actions">
                    <el-button link type="primary" :icon="Edit" @click="handleEdit(match)">{{ $t('admin.update') }}</el-button>
                    <el-button link type="warning" :icon="Timer" @click="handleEdit(match)">{{ $t('admin.reschedule') }}</el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Unified Schedule Dialog -->
    <el-dialog v-model="showEditDialog" width="500px" class="saas-dialog-premium" destroy-on-close>
      <template #header>
        <div class="dialog-header-saas">
          <el-icon class="mr-2"><Timer /></el-icon>
          <span>{{ editingMatch?.court_id ? $t('admin.updateSchedule') : $t('admin.allocateMatch') }}</span>
        </div>
      </template>
      <div class="saas-dialog-content">
        <div v-if="editingMatch" class="saas-context-card mb-6">
          <div class="context-row"><span class="label">Tournament</span><strong class="value">{{ editingMatch.tournament }}</strong></div>
          <div class="context-row"><span class="label">Match</span><strong class="value">{{ editingMatch.p1_name || editingMatch.side_a_name }} vs {{ editingMatch.p2_name || editingMatch.side_b_name }}</strong></div>
          <div class="context-row"><span class="label">Current</span><strong class="value">{{ editingMatch.court || 'Unassigned' }} @ {{ editingMatch.start || '--:--' }}</strong></div>
        </div>
        <el-form label-position="top" class="saas-form-premium">
          <el-form-item :label="$t('admin.assignCourt')">
            <el-select v-model="form.court_id" :placeholder="$t('admin.selectCourt')" class="w-full saas-input-large">
              <template #prefix><el-icon><LocationIcon /></el-icon></template>
              <el-option v-for="c in courts" :key="c.id" :label="c.court_name" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item :label="$t('admin.matchTime')">
            <el-date-picker 
              v-model="form.start_time" 
              type="datetime" 
              format="DD/MM/YYYY HH:mm" 
              value-format="YYYY-MM-DDTHH:mm:ss" 
              :disabled-date="disabledMatchDate"
              class="w-full saas-input-large" 
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="saas-dialog-footer">
          <el-button @click="showEditDialog = false" class="saas-btn-secondary">{{ $t('admin.cancel') }}</el-button>
          <el-button type="primary" :loading="isSaving" @click="handleSave" class="saas-btn-primary">{{ $t('admin.confirm') }}</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.saas-container { display: flex; flex-direction: column; gap: 24px; height: calc(100vh - 100px); }

/* Header Styles Cải tiến */
.saas-header-compact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: #ffffff;
  border-bottom: 1px solid #f1f5f9;
  border-radius: 16px 16px 0 0;
  min-height: 80px;
  flex-shrink: 0;
}
.header-left-compact {
  flex-shrink: 0;
}
.header-right-compact {
  display: flex;
  align-items: center;
  gap: 12px;
}
.saas-view-switcher-premium {
  background: #f1f5f9;
  padding: 4px;
  border-radius: 12px;
}
.saas-view-switcher-premium :deep(.el-radio-button__inner) {
  border: none !important;
  background: transparent !important;
  color: #64748b;
  border-radius: 8px !important;
  padding: 10px 20px;
  font-weight: 600;
  transition: all 0.2s ease;
  height: 44px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.saas-view-switcher-premium :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #ffffff !important;
  color: #2563eb !important;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1) !important;
}

/* Date Navigator */
.saas-date-navigator { display: flex; align-items: center; gap: 4px; background: #fff; border: 1px solid #f1f5f9; padding: 4px; border-radius: 12px; }
.nav-btn { border: none !important; background: #f8fafc !important; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 8px !important; color: #64748b; }
.saas-date-picker-mini :deep(.el-input__wrapper) { background: transparent !important; box-shadow: none !important; width: 130px; font-weight: 800; }

.saas-btn-today { height: 44px; border-radius: 12px; font-weight: 800; border-color: #e2e8f0; padding: 0 20px; }
.saas-btn-refresh { height: 44px; width: 44px; border-color: #e2e8f0; color: #64748b; border-radius: 12px; }
.saas-btn-primary { height: 44px; border-radius: 12px; font-weight: 900; padding: 0 20px; background: #2563eb; border: none; }

/* Main Content Area */
.saas-card-premium { background: #fff; border-radius: 24px; border: 1px solid #f1f5f9; box-shadow: 0 4px 20px rgba(0,0,0,0.02); overflow: hidden; }

/* Calendar Style */
.saas-calendar-premium :deep(.el-calendar-day) { height: 110px !important; padding: 8px !important; }
.saas-date-cell { height: 100%; display: flex; flex-direction: column; gap: 4px; }
.cell-head { display: flex; justify-content: space-between; align-items: center; }
.cell-num { font-size: 1rem; font-weight: 900; color: #1e293b; }
.saas-match-chip { padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: 800; display: flex; align-items: center; gap: 4px; margin-bottom: 2px; }
.chip-dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
.saas-match-chip.completed { background: #f0fdf4; color: #166534; }
.saas-match-chip.ongoing { background: #eff6ff; color: #1e40af; }
.saas-match-chip.scheduled { background: #fffbeb; color: #92400e; }

/* Sidebar Pending Tabs */
.pending-tabs-container {
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.5);
  border-bottom: 1px solid #eee;
}
.saas-tabs-mini {
  width: 100%;
}
.saas-tabs-mini :deep(.el-radio-button__inner) {
  min-width: 100px;
  border-radius: 8px !important;
  font-size: 13px;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  white-space: nowrap;
  transition: all 0.3s;
}
.pending-tabs-container {
  padding: 16px;
  background: #fdfdfd;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: center;
}

/* Pending Tour Grouping */
.pending-tour-group {
  margin-bottom: 16px;
}
.tour-group-label {
  padding: 8px 16px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: #909399;
  letter-spacing: 0.5px;
  background: #f8f9fa;
  border-left: 3px solid #409eff;
  margin-bottom: 8px;
}
.pending-tour-group .saas-pending-card {
  margin-left: 8px;
  margin-right: 8px;
}

.saas-pending-card.is-overdue {
  border-left-color: #f56c6c;
  background: #fffafa;
}
.pc-date-tag {
  font-size: 10px;
  background: #eee;
  padding: 2px 6px;
  border-radius: 4px;
  color: #666;
}
.is-overdue .pc-date-tag {
  background: #ffecec;
  color: #f56c6c;
}

/* Status Colors */
.status-indicator.pending { background: #909399; }
.status-indicator.scheduled { background: #409eff; }
.status-indicator.playing { background: #67c23a; box-shadow: 0 0 8px rgba(103,194,58,0.5); }
.status-indicator.finished { background: #e6a23c; }

@media (max-width: 1200px) {
  .schedule-layout-saas {
    flex-direction: column;
  }
  .pending-block {
    width: 100%;
    height: 300px;
  }
}

/* Grid View Layout */
.schedule-layout-saas { display: grid; grid-template-columns: 1fr 320px; gap: 20px; height: 100%; overflow: hidden; }
.grid-main-block { display: flex; flex-direction: column; }
.timeline-viewport { flex: 1; overflow: auto; position: relative; }

.courts-row-sticky { display: flex; position: sticky; top: 0; z-index: 50; background: #fff; border-bottom: 2px solid #f1f5f9; }
.time-corner { width: 60px; min-width: 60px; height: 60px; background: #fafafa; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 0.65rem; color: #94a3b8; border-right: 1px solid #f1f5f9; }
.court-header-saas { flex: 1; min-width: 180px; height: 60px; display: flex; flex-direction: column; align-items: center; justify-content: center; border-right: 1px solid #f1f5f9; }
.court-header-saas .c-name { font-weight: 900; color: #0f172a; font-size: 0.9rem; }
.court-header-saas .c-loc { font-size: 0.65rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; }

.timeline-body { display: flex; position: relative; }
.time-track { width: 60px; min-width: 60px; background: #fafafa; border-right: 1px solid #f1f5f9; }
.hour-marker { height: 108px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: center; padding-top: 8px; }
.hour-marker span { font-size: 0.7rem; color: #94a3b8; font-weight: 800; }

.lanes-wrapper { display: flex; flex: 1; position: relative; }
.court-lane-saas { flex: 1; min-width: 180px; border-right: 1px solid #f1f5f9; position: relative; background-image: linear-gradient(#f1f5f9 1px, transparent 1px); background-size: 100% 108px; }
.lane-grid-cell { height: 108px; }

.saas-match-card-visual { position: absolute; left: 6px; right: 6px; border-radius: 12px; background: #fff; border: 1px solid #f1f5f9; box-shadow: 0 4px 12px rgba(0,0,0,0.05); display: flex; cursor: pointer; transition: all 0.2s; overflow: hidden; }
.saas-match-card-visual:hover { transform: scale(1.02); z-index: 10; border-color: #2563eb; }
.mc-accent { width: 4px; background: #cbd5e1; }
.saas-match-card-visual.completed .mc-accent { background: #10b981; }
.saas-match-card-visual.ongoing .mc-accent { background: #3b82f6; }
.saas-match-card-visual.scheduled .mc-accent { background: #f59e0b; }
.mc-content { flex: 1; padding: 8px; display: flex; flex-direction: column; gap: 2px; }
.mc-time { font-size: 0.7rem; font-weight: 900; color: #0f172a; }
.mc-tour { font-size: 0.7rem; font-weight: 800; color: #2563eb; }
.mc-versus { display: flex; align-items: center; justify-content: space-between; background: #f8fafc; padding: 4px 6px; border-radius: 8px; }

/* Pending Sidebar */
.pending-block { display: flex; flex-direction: column; gap: 12px; overflow: hidden; padding: 0 !important; }
.sidebar-header-saas { padding: 16px !important; display: flex; justify-content: space-between; align-items: center; border-radius: 0 !important; border: none !important; border-bottom: 1px solid #f1f5f9 !important; }
.sidebar-header-saas h4 { margin: 0; font-size: 0.9rem; font-weight: 900; color: #0f172a; }
.pending-scroll-stack { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.saas-pending-card { background: #fff; border-radius: 16px; padding: 14px; border: 1px solid #f1f5f9; cursor: pointer; transition: all 0.2s; }
.saas-pending-card:hover { border-color: #2563eb; transform: translateX(-4px); }
.pc-pair { display: flex; align-items: center; justify-content: space-between; background: #f8fafc; padding: 8px; border-radius: 10px; margin: 8px 0; }
.pc-p { font-size: 0.75rem; font-weight: 800; }
.pc-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
}
.pc-footer-left {
  display: flex;
  align-items: center;
}
.pc-cancel-btn {
  font-weight: 700 !important;
  font-size: 11px !important;
  padding: 0 !important;
}

/* Timeline List View */
.timeline-list-viewport { flex: 1; overflow-y: auto; }
.tournament-group { margin-bottom: 32px; }
.tournament-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.th-title { display: flex; align-items: center; gap: 10px; }
.th-icon { width: 32px; height: 32px; background: #fffbeb; color: #d97706; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.match-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 16px; }
.match-card-premium { background: #fff; border-radius: 20px; padding: 16px; border: 1px solid #f1f5f9; display: flex; gap: 16px; }
.mc-time-side { display: flex; flex-direction: column; align-items: center; width: 50px; }
.mc-time { font-weight: 900; font-size: 0.9rem; }
.mc-timeline-dot { width: 10px; height: 10px; border: 2px solid #e2e8f0; border-radius: 50%; position: relative; margin-top: 8px; }
.mc-timeline-dot::after { content: ''; position: absolute; top: 10px; left: 50%; transform: translateX(-50%); width: 2px; height: 100px; background: #f1f5f9; }

.mc-players { display: flex; align-items: center; justify-content: space-between; background: #f8fafc; padding: 12px; border-radius: 12px; }
.p-avatar { width: 32px; height: 32px; background: #fff; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; color: #2563eb; }

/* Transitions */
.fade-slide-enter-active, .fade-slide-leave-active { transition: all 0.3s ease; }
.fade-slide-enter-from { opacity: 0; transform: translateY(10px); }
.fade-slide-leave-to { opacity: 0; transform: translateY(-10px); }

/* Dialog Styles */
.saas-context-card { background: #f8fafc; border-radius: 16px; padding: 16px; margin-bottom: 20px; }
.context-row { display: flex; justify-content: space-between; margin-bottom: 8px; }
.context-row .label { font-size: 0.7rem; color: #94a3b8; font-weight: 800; text-transform: uppercase; }
.context-row .value { font-weight: 800; font-size: 0.9rem; }

.ml-2 { margin-left: 8px; }
.mr-4 { margin-right: 16px; }
.truncate { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.icon-pulse { animation: pulse 2s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
</style>
