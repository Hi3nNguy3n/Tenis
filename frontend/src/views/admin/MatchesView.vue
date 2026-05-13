<script setup>
import { onMounted, ref, computed } from 'vue'
import { apiClient } from '../../services/apiClient'
import { useAuthStore } from '../../stores/auth'
import { ElMessage } from 'element-plus'
import { 
  Calendar, Location, Trophy, Check, Edit, Plus, Delete,
  Timer, Monitor, SuccessFilled, VideoPlay, PieChart,
  Refresh, Search, ArrowRight, User
} from '@element-plus/icons-vue'
import { t } from '../../utils/locale'

const authStore = useAuthStore()
const tournaments = ref([])
const selectedTournamentId = ref(null)
const matches = ref([])
const isLoading = ref(false)
const courts = ref([])

const showScheduleDialog = ref(false)
const showScoreDialog = ref(false)

const schedulingMatch = ref(null)
const scheduleForm = ref({ court_id: null, start_time: '' })

const scoringMatch = ref(null)
const scoreForm = ref({ 
  winner_side: '',
  sets: [{ side_a: 0, side_b: 0 }] 
})

const stats = computed(() => {
  const total = matches.value.length
  const ongoing = matches.value.filter(m => m.status?.toLowerCase() === 'ongoing').length
  const scheduled = matches.value.filter(m => m.status?.toLowerCase() === 'scheduled').length
  const completed = matches.value.filter(m => m.status?.toLowerCase() === 'completed').length
  
  return {
    total,
    ongoing,
    scheduled,
    completed
  }
})

const groupedMatches = computed(() => {
  const groups = {}
  matches.value.forEach(m => {
    const label = m.round_code || t('admin.others')
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

const fetchTournaments = async () => {
  try {
    const data = await apiClient.get('/api/tournaments?limit=100')
    tournaments.value = data
  } catch (err) { ElMessage.error(t('admin.loadTournamentsError')) }
}

const fetchCourts = async () => {
  try {
    const data = await apiClient.get('/api/courts/')
    courts.value = data
  } catch (err) { ElMessage.error(t('admin.loadCourtsError') || 'Error loading courts') }
}

const fetchMatches = async () => {
  if (selectedTournamentId.value === null || selectedTournamentId.value === '') return
  
  isLoading.value = true
  try {
    const data = await apiClient.get('/api/matches/', {
      params: { tournament_id: selectedTournamentId.value }
    })
    matches.value = data
  } catch (err) { 
    ElMessage.error(t('admin.loadMatchesError')) 
  } finally { 
    isLoading.value = false 
  }
}

const openScheduleDialog = (match) => {
  schedulingMatch.value = match
  scheduleForm.value.court_id = match.court_id
  scheduleForm.value.start_time = match.start_time || ''
  showScheduleDialog.value = true
}

const handleSchedule = async () => {
  try {
    await apiClient.post(`/api/tournaments/matches/${schedulingMatch.value.id}/schedule`, scheduleForm.value)
    ElMessage.success(t('admin.scheduleUpdateSuccess'))
    showScheduleDialog.value = false
    fetchMatches()
  } catch (err) { 
    const errorMsg = err.response?.data?.detail || err.message
    ElMessage.error(t('admin.scheduleError') + ': ' + errorMsg)
  }
}

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
    ElMessage.warning(t('admin.selectWinnerWarning'))
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
    ElMessage.success(t('admin.scoreUpdateSuccess'))
    showScoreDialog.value = false
    fetchMatches()
  } catch (err) { ElMessage.error(t('admin.scoreUpdateError')) }
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
  <div class="saas-container">
    <!-- Stats Grid (Only if tournament selected) -->
    <div v-if="selectedTournamentId !== null && selectedTournamentId !== ''" class="saas-stats-grid">
      <div class="saas-stat-card">
        <div class="stat-icon p-blue"><el-icon><Monitor /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.totalMatches') }}</span>
          <h3 class="stat-value">{{ stats.total }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-orange"><el-icon><VideoPlay /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.ongoingMatches') }}</span>
          <h3 class="stat-value">{{ stats.ongoing }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-purple"><el-icon><Calendar /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.scheduledMatches') }}</span>
          <h3 class="stat-value">{{ stats.scheduled }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-green"><el-icon><SuccessFilled /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.completedMatches') }}</span>
          <h3 class="stat-value">{{ stats.completed }}</h3>
        </div>
      </div>
    </div>

    <!-- Header & Action Bar -->
    <div class="saas-header">
      <div class="header-left">
        <div class="operation-badge">
          <el-icon class="mr-1"><Monitor /></el-icon>
          <span>Match Control</span>
        </div>
        <el-select 
          v-model="selectedTournamentId" 
          :placeholder="$t('admin.selectTournamentOpsPlaceholder')" 
          size="large" 
          @change="fetchMatches" 
          filterable 
          class="saas-tournament-selector"
        >
          <template #prefix><el-icon><Trophy /></el-icon></template>
          <el-option :label="$t('admin.friendlyMatchesLabel')" :value="0" />
          <el-option v-for="t in tournaments" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button :icon="Refresh" circle @click="fetchMatches" class="saas-icon-btn" />
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="saas-content-area" v-loading="isLoading">
      <!-- Empty State -->
      <div v-if="selectedTournamentId === null || selectedTournamentId === ''" class="saas-empty-state">
        <div class="empty-visual">
          <div class="blob-anim"></div>
          <el-icon class="main-icon"><Trophy /></el-icon>
        </div>
        <h3>{{ $t('admin.startMatchControlTitle') }}</h3>
        <p>{{ $t('admin.startMatchControlDesc') }}</p>
      </div>

      <!-- Match Rounds -->
      <div v-else class="rounds-wrapper">
        <div v-for="round in groupedMatches" :key="round.label" class="round-block">
          <div class="round-header-premium">
            <div class="round-title-wrap">
              <span class="round-accent"></span>
              <h3 class="round-name">{{ round.label }}</h3>
            </div>
            <span class="round-stats">{{ round.items.length }} {{ $t('admin.matchCountLabel') }}</span>
          </div>
          
          <div class="match-cards-grid">
            <div v-for="m in round.items" :key="m.id" class="match-card-saas" :class="{ 'is-finished': m.status === 'completed' }">
              <div class="match-card-header">
                <span class="match-id">#{{ m.match_no || m.id }}</span>
                <div class="status-indicator" :class="`is-${getStatusType(m.status)}`">
                  <span class="dot"></span>
                  <span>{{ m.status.toUpperCase() }}</span>
                </div>
              </div>

              <div class="match-card-body">
                <div class="side-item" :class="{ 'is-winner': m.winner_side === 'side_a' }">
                  <div class="player-box">
                    <div class="avatar-mini"><el-icon><User /></el-icon></div>
                    <span class="player-name">{{ m.p1_name || '...' }}</span>
                  </div>
                  <el-icon v-if="m.winner_side === 'side_a'" class="win-check"><SuccessFilled /></el-icon>
                </div>

                <div class="vs-divider">
                  <div class="line"></div>
                  <span class="vs-text">VS</span>
                  <div class="line"></div>
                </div>

                <div class="side-item" :class="{ 'is-winner': m.winner_side === 'side_b' }">
                  <div class="player-box">
                    <div class="avatar-mini"><el-icon><User /></el-icon></div>
                    <span class="player-name">{{ m.p2_name || '...' }}</span>
                  </div>
                  <el-icon v-if="m.winner_side === 'side_b'" class="win-check"><SuccessFilled /></el-icon>
                </div>
              </div>

              <div class="match-card-info">
                <div class="info-row">
                  <el-icon><Calendar /></el-icon>
                  <span>{{ m.start_time ? new Date(m.start_time).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' }) : $t('admin.notScheduled') }}</span>
                </div>
                <div class="info-row">
                  <el-icon><Location /></el-icon>
                  <span>{{ courts.find(c => c.id === m.court_id)?.court_name || $t('admin.notAssignedCourt') }}</span>
                </div>
              </div>

              <div class="match-card-footer">
                <el-button-group class="full-width-group">
                  <el-button @click="openScheduleDialog(m)" class="footer-btn">
                    <el-icon class="mr-1"><Calendar /></el-icon> {{ $t('admin.scheduleMatch') }}
                  </el-button>
                  <el-button 
                    @click="openScoreDialog(m)" 
                    type="primary" 
                    class="footer-btn primary-action"
                    :disabled="m.status === 'completed' || !m.p1_name || !m.p2_name"
                  >
                    <el-icon class="mr-1"><Edit /></el-icon> {{ $t('admin.updateScore') }}
                  </el-button>
                </el-button-group>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dialogs -->
    <el-dialog v-model="showScheduleDialog" :title="$t('admin.scheduleMatch')" width="440px" class="saas-dialog">
       <el-form label-position="top" v-if="schedulingMatch" class="saas-form">
         <el-form-item :label="$t('admin.selectCourt')">
           <el-select v-model="scheduleForm.court_id" style="width: 100%" class="saas-select-premium">
             <el-option v-for="c in courts" :key="c.id" :label="c.court_name" :value="c.id" />
           </el-select>
         </el-form-item>
         <el-form-item :label="$t('admin.expectedStartTime')">
           <el-date-picker 
            v-model="scheduleForm.start_time" 
            type="datetime" 
            value-format="YYYY-MM-DD HH:mm:ss" 
            :disabled-date="disabledScheduleDate" 
            style="width: 100%" 
            class="saas-picker-premium"
           />
         </el-form-item>
       </el-form>
       <template #footer>
         <div class="saas-dialog-footer">
           <el-button @click="showScheduleDialog = false" class="saas-btn-secondary">{{ $t('admin.cancel') }}</el-button>
           <el-button type="primary" @click="handleSchedule" class="saas-btn-primary">{{ $t('admin.confirm') }}</el-button>
         </div>
       </template>
    </el-dialog>

    <el-dialog v-model="showScoreDialog" :title="$t('admin.updateScore')" width="520px" class="saas-dialog">
       <div v-if="scoringMatch" class="scoring-box">
          <div class="winner-selection-premium">
             <p class="section-label">{{ $t('admin.whoIsWinner') }}</p>
             <el-radio-group v-model="scoreForm.winner_side" class="winner-grid-selector">
                <el-radio value="side_a" border class="winner-radio-premium">
                  <div class="radio-content">
                    <el-icon><User /></el-icon>
                    <strong>{{ scoringMatch.p1_name }}</strong>
                  </div>
                </el-radio>
                <el-radio value="side_b" border class="winner-radio-premium">
                  <div class="radio-content">
                    <el-icon><User /></el-icon>
                    <strong>{{ scoringMatch.p2_name }}</strong>
                  </div>
                </el-radio>
             </el-radio-group>
          </div>

          <div class="sets-management">
             <div class="sets-header">
               <span class="section-label">{{ $t('admin.setScoreTitle') }}</span>
               <el-button type="primary" :icon="Plus" link @click="addSet">{{ $t('admin.addSet') }}</el-button>
             </div>
             
             <div class="sets-rows">
                <div v-for="(set, index) in scoreForm.sets" :key="index" class="set-row-premium">
                   <span class="set-index">Set {{ index + 1 }}</span>
                   <div class="set-inputs-wrap">
                      <el-input-number v-model="set.side_a" :min="0" :max="30" controls-position="right" class="saas-number-input" />
                      <span class="vs-dash">-</span>
                      <el-input-number v-model="set.side_b" :min="0" :max="30" controls-position="right" class="saas-number-input" />
                   </div>
                   <el-button v-if="scoreForm.sets.length > 1" type="danger" :icon="Delete" circle plain link @click="removeSet(index)" />
                </div>
             </div>
          </div>
       </div>
       <template #footer>
         <div class="saas-dialog-footer">
           <el-button @click="showScoreDialog = false" class="saas-btn-secondary">{{ $t('admin.cancel') }}</el-button>
           <el-button type="success" @click="handleUpdateScore" class="saas-btn-primary is-success">{{ $t('admin.confirmResult') }}</el-button>
         </div>
       </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.saas-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
  min-height: 100%;
}

/* Stats Grid */
.saas-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

.saas-stat-card {
  background: #fff;
  border: 1px solid #f1f5f9;
  border-radius: 24px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
}

.saas-stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.05);
}

.stat-icon {
  width: 56px; height: 56px; border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px;
}

.p-blue { background: #eff6ff; color: #3b82f6; }
.p-green { background: #ecfdf5; color: #10b981; }
.p-orange { background: #fff7ed; color: #f97316; }
.p-purple { background: #f5f3ff; color: #8b5cf6; }

.stat-label { font-size: 0.75rem; color: #64748b; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; }
.stat-value { margin: 4px 0 0; font-size: 1.8rem; font-weight: 800; color: #0f172a; }

/* Header & Action Bar */
.saas-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.header-left { display: flex; align-items: center; gap: 12px; }

.operation-badge {
  background: #fef2f2; color: #dc2626; padding: 8px 16px; border-radius: 12px;
  font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;
  display: flex; align-items: center;
}

.saas-tournament-selector { width: 380px; }

:deep(.el-input__wrapper), :deep(.el-select__wrapper) {
  background-color: #f8fafc !important;
  box-shadow: none !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 12px !important;
  padding: 8px 12px !important;
}

.saas-icon-btn {
  width: 44px; height: 44px; border-radius: 12px !important;
  background: #f8fafc !important; border: 1px solid #e2e8f0 !important;
}

/* Empty State */
.saas-empty-state {
  text-align: center; padding: 100px 40px; background: #fff; border-radius: 32px;
  border: 1px dashed #cbd5e1; display: flex; flex-direction: column; align-items: center;
}

.empty-visual { position: relative; width: 120px; height: 120px; margin-bottom: 24px; }
.main-icon { font-size: 80px; color: #94a3b8; position: relative; z-index: 2; }
.blob-anim {
  position: absolute; inset: 0; background: #f1f5f9; border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%;
  animation: blobby 10s infinite linear; opacity: 0.5;
}

@keyframes blobby {
  0% { border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%; transform: rotate(0deg); }
  50% { border-radius: 60% 40% 30% 70% / 50% 60% 40% 60%; }
  100% { border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%; transform: rotate(360deg); }
}

.saas-empty-state h3 { font-size: 1.5rem; font-weight: 800; color: #1e293b; margin-bottom: 12px; }
.saas-empty-state p { color: #64748b; font-size: 1rem; }

/* Rounds Layout */
.rounds-wrapper { display: flex; flex-direction: column; gap: 48px; }

.round-header-premium {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 24px; padding-bottom: 12px; border-bottom: 2px solid #f1f5f9;
}

.round-title-wrap { display: flex; align-items: center; gap: 12px; }
.round-accent { width: 4px; height: 24px; background: #3b82f6; border-radius: 4px; }
.round-name { font-size: 1.5rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.02em; }
.round-stats { font-size: 0.85rem; font-weight: 700; color: #64748b; background: #f8fafc; padding: 4px 12px; border-radius: 99px; }

.match-cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 24px; }

/* Match Card SaaS */
.match-card-saas {
  background: #fff; border-radius: 24px; border: 1px solid #f1f5f9;
  padding: 24px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(0,0,0,0.02); display: flex; flex-direction: column; gap: 20px;
}

.match-card-saas:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
  border-color: #e2e8f0;
}

.is-finished { opacity: 0.85; background: #fafafa; }

.match-card-header { display: flex; justify-content: space-between; align-items: center; }
.match-id { font-family: 'JetBrains Mono', monospace; font-weight: 800; color: #94a3b8; font-size: 0.85rem; }

.status-indicator {
  display: inline-flex; align-items: center; gap: 8px; padding: 4px 12px; border-radius: 99px;
  font-size: 0.7rem; font-weight: 800; letter-spacing: 0.05em;
}
.is-primary { background: #eff6ff; color: #3b82f6; }
.is-warning { background: #fff7ed; color: #f97316; }
.is-success { background: #ecfdf5; color: #10b981; }

.status-indicator .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.is-primary .dot { animation: pulse-blue 2s infinite; }
@keyframes pulse-blue { 0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); } 70% { box-shadow: 0 0 0 6px rgba(59, 130, 246, 0); } 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); } }

/* Match Card Body */
.match-card-body {
  background: #f8fafc; border-radius: 16px; padding: 16px;
  display: flex; flex-direction: column; gap: 8px; position: relative;
}

.side-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border-radius: 12px; background: #fff; border: 1px solid #f1f5f9;
  transition: all 0.2s;
}

.side-item.is-winner { background: #f0fdf4; border-color: #10b981; }

.player-box { display: flex; align-items: center; gap: 12px; }
.avatar-mini {
  width: 28px; height: 28px; border-radius: 50%; background: #f1f5f9;
  display: flex; align-items: center; justify-content: center; font-size: 14px; color: #94a3b8;
}
.player-name { font-weight: 800; color: #1e293b; font-size: 0.95rem; }
.win-check { color: #10b981; font-size: 18px; }

.vs-divider {
  display: flex; align-items: center; gap: 12px; padding: 4px 0;
}
.vs-divider .line { flex: 1; height: 1px; background: #e2e8f0; }
.vs-text { font-size: 0.65rem; font-weight: 900; color: #cbd5e1; letter-spacing: 0.1em; }

/* Meta Info */
.match-card-info { display: flex; flex-direction: column; gap: 8px; }
.info-row { display: flex; align-items: center; gap: 10px; color: #64748b; font-size: 0.8rem; font-weight: 700; }
.info-row .el-icon { font-size: 16px; }

/* Card Footer */
.match-card-footer { margin-top: 4px; }
.full-width-group { width: 100%; display: flex; }
.footer-btn { flex: 1; border-radius: 12px !important; height: 44px; font-weight: 700; }
.primary-action { background: #0f172a !important; border: none !important; color: #fff !important; }
.primary-action:hover { background: #1e293b !important; }

/* Dialog Styles */
:deep(.saas-dialog) { border-radius: 24px !important; overflow: hidden; }
:deep(.el-dialog__header) { margin: 0; padding: 24px 32px; border-bottom: 1px solid #f1f5f9; }
:deep(.el-dialog__title) { font-weight: 900; color: #0f172a; }

.saas-form { padding: 12px 0; }
:deep(.el-form-item__label) { font-weight: 700; color: #1e293b; margin-bottom: 8px !important; }

.saas-dialog-footer { display: flex; gap: 12px; justify-content: flex-end; }
.saas-btn-secondary { border-radius: 12px !important; padding: 20px 24px !important; font-weight: 600; }
.saas-btn-primary { border-radius: 12px !important; padding: 20px 32px !important; font-weight: 800; }
.saas-btn-primary.is-success { background: #10b981 !important; border: none !important; }

/* Scoring Box */
.scoring-box { display: flex; flex-direction: column; gap: 32px; padding: 10px 0; }
.section-label { font-size: 0.85rem; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 16px; display: block; }

.winner-grid-selector { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; width: 100%; }
.winner-radio-premium {
  height: auto !important; padding: 16px !important; border-radius: 16px !important;
  margin: 0 !important; width: 100%; display: flex; align-items: center; justify-content: center;
}
.radio-content { display: flex; flex-direction: column; align-items: center; gap: 10px; }
.radio-content .el-icon { font-size: 24px; color: #94a3b8; }
:deep(.el-radio.is-bordered.is-checked) { background: #f0fdf4; border-color: #10b981; }
:deep(.el-radio.is-bordered.is-checked) .radio-content .el-icon { color: #10b981; }

.sets-header { display: flex; justify-content: space-between; align-items: center; }
.sets-rows { display: flex; flex-direction: column; gap: 12px; }
.set-row-premium {
  display: flex; align-items: center; gap: 20px; padding: 16px;
  background: #f8fafc; border-radius: 16px; border: 1px solid #e2e8f0;
}
.set-index { font-weight: 800; color: #475569; min-width: 50px; }
.set-inputs-wrap { display: flex; align-items: center; gap: 12px; flex: 1; justify-content: center; }
.vs-dash { font-weight: 900; color: #cbd5e1; }

.mr-1 { margin-right: 4px; }

@media (max-width: 768px) {
  .saas-stats-grid { grid-template-columns: 1fr 1fr; }
  .saas-header { flex-direction: column; align-items: stretch; }
  .saas-tournament-selector { width: 100%; }
  .match-cards-grid { grid-template-columns: 1fr; }
  .winner-grid-selector { grid-template-columns: 1fr; }
}
</style>