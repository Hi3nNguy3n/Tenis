<script setup>
import { onMounted, ref, computed } from 'vue'
import { apiClient } from '../../services/apiClient'
import { useAuthStore } from '../../stores/auth'
import { ElMessage } from 'element-plus'
import { Calendar, Location, Trophy, Check, Edit, Plus, Delete } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const tournaments = ref([])
const selectedTournamentId = ref(null)
const matches = ref([])
const isLoading = ref(false)
const courts = ref([])

// --- Quản lý Dialog ---
const showScheduleDialog = ref(false)
const showScoreDialog = ref(false)

const schedulingMatch = ref(null)
const scheduleForm = ref({ court_id: null, start_time: '' })

const scoringMatch = ref(null)
const scoreForm = ref({ 
  winner_side: '',
  sets: [{ side_a: 0, side_b: 0 }] // Danh sách các set đấu
})

const currentUserName = computed(() => authStore.profile?.full_name || '')

// --- Logic gom nhóm trận đấu ---
const groupedMatches = computed(() => {
  const groups = {}
  matches.value.forEach(m => {
    const label = m.round_code || 'Khác'
    if (!groups[label]) groups[label] = []
    groups[label].push(m)
  })
  const order = ['FINAL', 'SF', 'QF', 'R16', 'R32']
  return Object.keys(groups).sort((a, b) => {
    const idxA = order.indexOf(a)
    const idxB = order.indexOf(b)
    if (idxA === -1) return 1
    if (idxB === -1) return -1
    return idxA - idxB
  }).map(key => ({
    label: key,
    items: groups[key]
  }))
})

// --- API Functions ---
const fetchTournaments = async () => {
  try {
    const data = await apiClient.get('/api/tournaments?limit=100')
    tournaments.value = data
  } catch (err) { ElMessage.error('Lỗi tải danh sách giải') }
}

const fetchCourts = async () => {
  try {
    const data = await apiClient.get('/api/courts/')
    courts.value = data
  } catch (err) { ElMessage.error('Lỗi tải danh sách sân') }
}

const fetchMatches = async () => {
  // Sửa logic check (Cho phép số 0 đi qua)
  if (selectedTournamentId.value === null || selectedTournamentId.value === '') return
  
  isLoading.value = true
  try {
    // Sửa đường dẫn gọi API để ăn khớp với Backend mới nâng cấp
    const data = await apiClient.get('/api/matches/', {
      params: { tournament_id: selectedTournamentId.value }
    })
    matches.value = data
  } catch (err) { 
    ElMessage.error('Lỗi tải trận đấu') 
  } finally { 
    isLoading.value = false 
  }
}

// --- Xử lý Xếp lịch ---
const openScheduleDialog = (match) => {
  schedulingMatch.value = match
  scheduleForm.value.court_id = match.court_id
  scheduleForm.value.start_time = match.start_time || ''
  showScheduleDialog.value = true
}

const handleSchedule = async () => {
  try {
    await apiClient.post(`/api/tournaments/matches/${schedulingMatch.value.id}/schedule`, scheduleForm.value)
    ElMessage.success('Đã cập nhật lịch thi đấu')
    showScheduleDialog.value = false
    fetchMatches()
  } catch (err) { 
    const errorMsg = err.response?.data?.detail || err.message
    ElMessage.error('Lỗi xếp lịch: ' + errorMsg)
  }
}

// --- Xử lý Nhập tỷ số thông minh ---
const openScoreDialog = (match) => {
  scoringMatch.value = match
  scoreForm.value.sets = [{ side_a: 0, side_b: 0 }]
  scoreForm.value.winner_side = ''
  showScoreDialog.value = true
}

const addSet = () => {
  scoreForm.value.sets.push({ side_a: 0, side_b: 0 })
}

const removeSet = (index) => {
  if (scoreForm.value.sets.length > 1) {
    scoreForm.value.sets.splice(index, 1)
  }
}

const handleUpdateScore = async () => {
  if (!scoreForm.value.winner_side) {
    ElMessage.warning('Vui lòng chọn VĐV chiến thắng!')
    return
  }

  const formattedScore = scoreForm.value.sets
    .map(s => `${s.side_a}-${s.side_b}`)
    .join(', ')

  try {
    await apiClient.post(`/api/tournaments/matches/${scoringMatch.value.id}/score`, {
      score: formattedScore,
      winner_side: scoreForm.value.winner_side
    })
    ElMessage.success('Cập nhật tỷ số thành công!')
    showScoreDialog.value = false
    fetchMatches()
  } catch (err) { ElMessage.error('Lỗi cập nhật tỷ số') }
}

const getStatusType = (status) => {
  const map = { 'scheduled': 'warning', 'ongoing': 'primary', 'completed': 'success' }
  return map[status] || 'info'
}

const selectedTournamentData = computed(() => tournaments.value.find(t => t.id === selectedTournamentId.value))
const disabledScheduleDate = (time) => {
  if (!selectedTournamentData.value) return false
  const start = new Date(selectedTournamentData.value.start_date).setHours(0,0,0,0)
  const end = new Date(selectedTournamentData.value.end_date).setHours(0,0,0,0)
  const check = new Date(time).setHours(0,0,0,0)
  return check < start || check > end
}

onMounted(() => {
  fetchTournaments()
  fetchCourts()
})
</script>

<template>
  <div class="operation-shell">
    <header class="action-bar shadow-sm">
      <div class="action-info">
        <span class="badge-live">Match Control</span>
        <p>Điều hành luồng thi đấu và cập nhật kết quả thời gian thực (Live Data).</p>
      </div>
      <div class="filter-area">
        <el-select v-model="selectedTournamentId" placeholder="--- Chọn giải đấu vận hành ---" size="large" @change="fetchMatches" filterable style="width: 320px">
          <el-option v-for="t in tournaments" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>

        <el-select v-model="selectedTournamentId" placeholder="--- Chọn giải đấu vận hành ---" size="large" @change="fetchMatches" filterable style="width: 320px">
          <el-option label="🌟 Các trận Giao hữu tự do (1vs1)" :value="0" />
          
          <el-option v-for="t in tournaments" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button :icon="Plus" plain @click="fetchMatches" style="margin-left: 12px">Làm mới</el-button>
      </div>
    </header>

    <main class="ops-content" v-loading="isLoading">
      <div v-if="selectedTournamentId === null || selectedTournamentId === ''" class="empty-state-lux">
        <div class="empty-icon-wrap">
          <el-icon :size="80"><Trophy /></el-icon>
        </div>
        <h3>Bắt đầu điều hành trận đấu</h3>
        <p>Vui lòng chọn một giải đấu để hiển thị danh sách các trận đấu cần xử lý.</p>
      </div>

      <div v-else class="rounds-container">
        <div v-for="round in groupedMatches" :key="round.label" class="round-section">
          <div class="round-header">
            <h3 class="round-name">{{ round.label }}</h3>
            <span class="match-count">{{ round.items.length }} Trận</span>
          </div>
          
          <div class="match-grid">
            <div v-for="m in round.items" :key="m.id" class="match-card-premium" :class="{ 'is-completed': m.status === 'completed' }">
              <div class="card-head">
                <div class="match-tag">#{{ m.match_no || m.id }}</div>
                <el-tag :type="getStatusType(m.status)" effect="dark" round size="small" class="status-tag">
                  {{ m.status.toUpperCase() }}
                </el-tag>
              </div>

              <div class="teams-container">
                <div class="team-slot" :class="{ 'is-winner': m.winner_side === 'side_a' }">
                  <div class="player-info">
                    <span class="player-name">{{ m.p1_name || 'Chưa xác định' }}</span>
                  </div>
                  <el-icon v-if="m.winner_side === 'side_a'" class="win-icon"><Check /></el-icon>
                </div>

                <div class="vs-badge"><span>VS</span></div>

                <div class="team-slot" :class="{ 'is-winner': m.winner_side === 'side_b' }">
                  <div class="player-info">
                    <span class="player-name">{{ m.p2_name || 'Chưa xác định' }}</span>
                  </div>
                  <el-icon v-if="m.winner_side === 'side_b'" class="win-icon"><Check /></el-icon>
                </div>
              </div>

              <div class="match-meta">
                <div class="meta-item">
                  <el-icon><Calendar /></el-icon>
                  <span>{{ m.start_time ? new Date(m.start_time).toLocaleString('vi-VN', {hour:'2-digit', minute:'2-digit', day:'2-digit', month:'2-digit'}) : 'Chưa xếp lịch' }}</span>
                </div>
                <div class="meta-item">
                  <el-icon><Location /></el-icon>
                  <span>{{ courts.find(c => c.id === m.court_id)?.court_name || 'Chưa gán sân' }}</span>
                </div>
              </div>

              <div class="card-footer">
                <el-button-group class="w-full">
                  <el-button @click="openScheduleDialog(m)" plain class="action-btn" :icon="Calendar">Xếp lịch</el-button>
                  <el-button 
                    @click="openScoreDialog(m)" 
                    type="primary" 
                    class="action-btn" 
                    :icon="Edit"
                    :disabled="m.status === 'completed' || m.p1_name === 'Chưa xác định' || m.p2_name === 'Chưa xác định'"
                  >
                    Tỷ số
                  </el-button>
                </el-button-group>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Dialogs -->
    <el-dialog v-model="showScheduleDialog" title="Xếp lịch thi đấu" width="400px">
       <el-form label-position="top" v-if="schedulingMatch">
         <el-form-item label="Chọn sân thi đấu">
           <el-select v-model="scheduleForm.court_id" style="width: 100%">
             <el-option v-for="c in courts" :key="c.id" :label="c.court_name" :value="c.id" />
           </el-select>
         </el-form-item>
         <el-form-item label="Giờ thi đấu dự kiến">
           <el-date-picker 
            v-model="scheduleForm.start_time" 
            type="datetime" 
            value-format="YYYY-MM-DD HH:mm:ss" 
            :disabled-date="disabledScheduleDate" 
            style="width: 100%" 
           />
         </el-form-item>
       </el-form>
       <template #footer>
         <el-button @click="showScheduleDialog = false">Hủy</el-button>
         <el-button type="primary" @click="handleSchedule">Xác nhận</el-button>
       </template>
    </el-dialog>

    <el-dialog v-model="showScoreDialog" title="Cập nhật kết quả trận đấu" width="500px">
       <div v-if="scoringMatch" class="score-container">
          <div class="winner-selector">
             <p class="label">Ai là người chiến thắng?</p>
             <el-radio-group v-model="scoreForm.winner_side" class="winner-radios">
                <el-radio value="side_a" border><strong>{{ scoringMatch.p1_name }}</strong></el-radio>
                <el-radio value="side_b" border><strong>{{ scoringMatch.p2_name }}</strong></el-radio>
             </el-radio-group>
          </div>
          <el-divider>Tỷ số các Set</el-divider>
          <div class="sets-list">
             <div v-for="(set, index) in scoreForm.sets" :key="index" class="set-row">
                <div class="set-label">Set {{ index + 1 }}</div>
                <div class="set-inputs">
                   <el-input-number v-model="set.side_a" :min="0" :max="30" controls-position="right" />
                   <span class="vs-text">-</span>
                   <el-input-number v-model="set.side_b" :min="0" :max="30" controls-position="right" />
                </div>
                <el-button v-if="scoreForm.sets.length > 1" type="danger" :icon="Delete" circle plain @click="removeSet(index)" />
             </div>
          </div>
          <el-button type="primary" :icon="Plus" plain class="add-set-btn" @click="addSet">Thêm Set</el-button>
       </div>
       <template #footer>
         <el-button @click="showScoreDialog = false">Hủy</el-button>
         <el-button type="success" size="large" @click="handleUpdateScore">Xác nhận kết quả</el-button>
       </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.operation-shell { display: flex; flex-direction: column; gap: 24px; padding: 20px; background: #f8fafc; min-height: 100vh; }

.action-bar {
  background: white; padding: 16px 24px; border-radius: 12px;
  display: flex; justify-content: space-between; align-items: center;
  border-left: 5px solid var(--primary); border: 1px solid #eef2f6;
}
.action-info p { color: #888; font-size: 0.9rem; margin: 2px 0 0 0; }
.badge-live { background: #fee2e2; color: #dc2626; padding: 4px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; }

.empty-state-lux {
  text-align: center; padding: 80px 20px; background: white; border-radius: 16px;
  border: 1px dashed #e2e8f0; margin-top: 20px;
}
.empty-icon-wrap { color: #cbd5e1; margin-bottom: 20px; }
.empty-state-lux h3 { color: #1e293b; margin-bottom: 8px; }
.empty-state-lux p { color: #64748b; }

.round-section { margin-bottom: 40px; }
.round-header { display: flex; align-items: baseline; gap: 15px; margin-bottom: 20px; }
.round-name { font-size: 1.4rem; color: #1e293b; font-weight: 800; margin: 0; }
.match-count { font-size: 0.85rem; color: #64748b; font-weight: 600; }

.match-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 24px; }

.match-card-premium {
  background: white; border-radius: 16px; border: 1px solid #f1f5f9;
  padding: 20px; transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(0,0,0,0.03); display: flex; flex-direction: column; gap: 16px;
}
.match-card-premium:hover { transform: translateY(-4px); box-shadow: 0 12px 30px rgba(0,0,0,0.07); }
.is-completed { background: #fcfdfe; opacity: 0.8; }

.card-head { display: flex; justify-content: space-between; align-items: center; }
.match-tag { font-family: monospace; font-weight: 800; color: #94a3b8; font-size: 0.9rem; }

.teams-container { background: #f8fafc; border-radius: 12px; padding: 12px; position: relative; display: flex; flex-direction: column; gap: 8px; }
.team-slot {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; border-radius: 8px; background: white; border: 1px solid #edf2f7;
}
.team-slot.is-winner { background: #ecfdf5; border-color: #10b981; }
.player-name { font-weight: 700; color: #334155; }
.win-icon { color: #10b981; font-weight: 900; }

.vs-badge { 
  position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);
  background: white; border: 1px solid #e2e8f0; width: 30px; height: 30px;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 0.65rem; font-weight: 900; color: #cbd5e1; z-index: 2;
}

.match-meta { display: flex; gap: 15px; border-top: 1px solid #f1f5f9; padding-top: 12px; }
.meta-item { display: flex; align-items: center; gap: 6px; color: #64748b; font-size: 0.8rem; font-weight: 600; }

.card-footer { margin-top: auto; }
.action-btn { width: 50%; }
.w-full { width: 100%; }

.winner-radios { display: flex; flex-direction: column; gap: 8px; }
.set-row { display: flex; align-items: center; gap: 10px; padding: 10px; background: #f8fafc; border-radius: 8px; margin-bottom: 8px; }
.set-inputs { display: flex; align-items: center; gap: 5px; flex-grow: 1; justify-content: center; }
.shadow-sm { box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.add-set-btn { width: 100%; border-style: dashed; }
</style>