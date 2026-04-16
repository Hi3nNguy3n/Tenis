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

const currentUserName = computed(() => authStore.profile?.full_name || 'Nguyen Cuu Minh Phu')

// --- Logic gom nhóm trận đấu ---
const groupedMatches = computed(() => {
  const groups = {}
  matches.value.forEach(m => {
    if (!groups[m.round_code]) groups[m.round_code] = []
    groups[m.round_code].push(m)
  })
  const order = ['FINAL', 'SF', 'QF', 'R16', 'R32']
  return Object.keys(groups).sort((a, b) => order.indexOf(a) - order.indexOf(b)).map(key => ({
    label: key,
    items: groups[key]
  }))
})

// --- API Functions ---
const fetchTournaments = async () => {
  try {
    const data = await apiClient.get('/api/tournaments')
    tournaments.value = data
  } catch (err) { ElMessage.error('Lỗi tải danh sách giải') }
}

const fetchCourts = async () => {
  try {
    const data = await apiClient.get('/api/courts')
    courts.value = data
  } catch (err) { ElMessage.error('Lỗi tải danh sách sân') }
}

const fetchMatches = async () => {
  if (!selectedTournamentId.value) return
  isLoading.value = true
  try {
    const data = await apiClient.get(`/api/tournaments/${selectedTournamentId.value}/matches`)
    matches.value = data
  } catch (err) { ElMessage.error('Lỗi tải trận đấu') } finally { isLoading.value = false }
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
  // Reset form về mặc định 1 set
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

  // Chuyển mảng sets thành chuỗi "6-4, 6-2" để gửi lên Backend
  const formattedScore = scoreForm.value.sets
    .map(s => `${s.side_a}-${s.side_b}`)
    .join(', ')

  try {
    await apiClient.post(`/api/tournaments/matches/${scoringMatch.value.id}/score`, {
      score: formattedScore,
      winner_side: scoreForm.value.winner_side
    })
    ElMessage.success('Cập nhật tỷ số và thăng hạng thành công!')
    showScoreDialog.value = false
    fetchMatches()
  } catch (err) { ElMessage.error('Lỗi cập nhật tỷ số') }
}

// Khóa ngày lịch
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
    <header class="ops-header">
      <div class="title-area">
        <span class="badge-live">Live Control</span>
        <h1>Điều hành Trận đấu</h1>
        <p>Quản lý luồng thi đấu và cập nhật kết quả thời gian thực.</p>
      </div>
      <div class="filter-area">
        <el-select v-model="selectedTournamentId" placeholder="Chọn giải đấu vận hành" size="large" @change="fetchMatches">
          <el-option v-for="t in tournaments" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
      </div>
    </header>

    <main class="ops-content" v-loading="isLoading">
      <div v-if="!selectedTournamentId" class="empty-state">
        <el-icon :size="60"><Trophy /></el-icon>
        <p>Chọn một giải đấu để bắt đầu điều phối các trận đấu.</p>
      </div>

      <div v-else class="rounds-container">
        <div v-for="round in groupedMatches" :key="round.label" class="round-section">
          <h3 class="round-name">{{ round.label }}</h3>
          <div class="match-grid">
            <div v-for="m in round.items" :key="m.id" class="match-card-v2" :class="{ 'is-completed': m.status === 'completed' }">
              <div class="card-top">
                <span class="match-no">Trận #{{ m.match_no }}</span>
                <el-tag :type="m.status === 'completed' ? 'success' : 'warning'" effect="dark" round size="small">
                  {{ m.status.toUpperCase() }}
                </el-tag>
              </div>

              <div class="players-area">
                <div class="p-row" :class="{ 'winner': m.winner_side === 'side_a', 'is-me': m.p1_name === currentUserName }">
                  <span class="p-name text-truncate">{{ m.p1_name }}</span>
                  <el-icon v-if="m.winner_side === 'side_a'"><Check /></el-icon>
                </div>
                <div class="vs-divider">VS</div>
                <div class="p-row" :class="{ 'winner': m.winner_side === 'side_b', 'is-me': m.p2_name === currentUserName }">
                  <span class="p-name text-truncate">{{ m.p2_name }}</span>
                  <el-icon v-if="m.winner_side === 'side_b'"><Check /></el-icon>
                </div>
              </div>

              <div class="match-info">
                <div class="info-item"><el-icon><Calendar /></el-icon>
                  <span>{{ m.start_time ? new Date(m.start_time).toLocaleString('vi-VN') : 'Chưa xếp lịch' }}</span>
                </div>
                <div class="info-item"><el-icon><Location /></el-icon>
                  <span>{{ courts.find(c => c.id === m.court_id)?.court_name || 'Chưa gán sân' }}</span>
                </div>
              </div>

              <div class="card-actions">
                <el-button @click="openScheduleDialog(m)" plain size="small" :icon="Calendar">Xếp lịch</el-button>
                <el-button @click="openScoreDialog(m)" type="success" size="small" :icon="Edit"
                  :disabled="m.status === 'completed' || m.p1_name === 'Chưa xác định' || m.p2_name === 'Chưa xác định'">
                  Tỷ số
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <el-dialog v-model="showScheduleDialog" title="Xếp lịch thi đấu" width="400px">
       <el-form label-position="top" v-if="schedulingMatch">
         <el-form-item label="Chọn sân thi đấu">
           <el-select v-model="scheduleForm.court_id" style="width: 100%">
             <el-option v-for="c in courts" :key="c.id" :label="c.court_name" :value="c.id" />
           </el-select>
         </el-form-item>
         <el-form-item label="Giờ thi đấu dự kiến">
           <el-date-picker v-model="scheduleForm.start_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" :disabled-date="disabledScheduleDate" style="width: 100%" />
         </el-form-item>
       </el-form>
       <template #footer>
         <el-button @click="showScheduleDialog = false">Hủy</el-button>
         <el-button type="primary" @click="handleSchedule">Xác nhận</el-button>
       </template>
    </el-dialog>

    <el-dialog v-model="showScoreDialog" title="Cập nhật kết quả trận đấu" width="500px" custom-class="score-dialog">
       <div v-if="scoringMatch" class="score-container">
          <div class="winner-selector">
             <p class="label">Ai là người chiến thắng?</p>
             <el-radio-group v-model="scoreForm.winner_side" class="winner-radios">
                <el-radio value="side_a" border><strong>{{ scoringMatch.p1_name }}</strong> (VĐV 1)</el-radio>
                <el-radio value="side_b" border><strong>{{ scoringMatch.p2_name }}</strong> (VĐV 2)</el-radio>
             </el-radio-group>
          </div>

          <el-divider>Tỷ số các Set</el-divider>

          <div class="sets-list">
             <div v-for="(set, index) in scoreForm.sets" :key="index" class="set-row">
                <div class="set-label">Set {{ index + 1 }}</div>
                <div class="set-inputs">
                   <el-input-number v-model="set.side_a" :min="0" :max="30" controls-position="right" size="large" />
                   <span class="vs-text">-</span>
                   <el-input-number v-model="set.side_b" :min="0" :max="30" controls-position="right" size="large" />
                </div>
                <el-button v-if="scoreForm.sets.length > 1" type="danger" :icon="Delete" circle plain @click="removeSet(index)" />
             </div>
          </div>

          <el-button type="primary" :icon="Plus" plain class="add-set-btn" @click="addSet">Thêm Set thi đấu</el-button>
       </div>

       <template #footer>
         <el-button @click="showScoreDialog = false">Hủy</el-button>
         <el-button type="success" size="large" @click="handleUpdateScore">Chốt Kết Quả & Thăng Hạng</el-button>
       </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.operation-shell { padding: 20px; background: #f9fbfd; min-height: 100vh; }
.ops-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.title-area h1 { font-size: 2rem; color: #1a3353; margin: 8px 0; }
.badge-live { background: #fee2e2; color: #dc2626; padding: 4px 12px; border-radius: 8px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; }

.round-section { margin-bottom: 40px; }
.round-name { font-size: 1.2rem; color: var(--primary); border-left: 5px solid var(--primary); padding-left: 15px; margin-bottom: 20px; font-weight: 800; }

.match-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.match-card-v2 { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #edf2f7; transition: all 0.3s; }
.match-card-v2:hover { transform: translateY(-5px); }
.is-completed { background: #f8fafc; opacity: 0.8; }

.players-area { background: #f1f5f9; border-radius: 10px; padding: 12px; margin-bottom: 15px; }
.p-row { display: flex; justify-content: space-between; align-items: center; padding: 8px; border-radius: 6px; font-weight: 600; }
.vs-divider { text-align: center; font-size: 0.7rem; color: #94a3b8; margin: 4px 0; font-weight: 900; }
.winner { background: #dcfce7; color: #166534; }
.is-me { border: 2px solid #f97316; }

.match-info { font-size: 0.85rem; color: #475569; margin-bottom: 15px; }
.info-item { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }

/* Score Dialog Styles */
.score-container { display: flex; flex-direction: column; gap: 16px; }
.winner-selector .label { font-weight: 700; margin-bottom: 12px; color: #1a3353; }
.winner-radios { display: flex; flex-direction: column; gap: 10px; width: 100%; }
.winner-radios .el-radio { margin-right: 0; width: 100%; height: 50px; }

.sets-list { display: flex; flex-direction: column; gap: 12px; }
.set-row { display: flex; align-items: center; gap: 15px; padding: 10px; background: #f8fafc; border-radius: 8px; }
.set-label { font-weight: 800; color: #64748b; width: 50px; }
.set-inputs { display: flex; align-items: center; gap: 10px; flex-grow: 1; justify-content: center; }
.vs-text { font-weight: 900; color: #cbd5e1; }
.add-set-btn { width: 100%; border-style: dashed; margin-top: 10px; }

.empty-state { text-align: center; padding: 100px 0; color: #94a3b8; }
.text-truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 180px; }
</style>