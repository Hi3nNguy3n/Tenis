<script setup>
import { onMounted, ref, computed } from 'vue'
import { apiClient, MAIN_API_URL } from '../../services/apiClient'
import { useAuthStore } from '../../stores/auth'
import { ElMessage } from 'element-plus'
import { 
  Calendar, Location, Trophy, Check, Edit, Plus, Delete,
  Timer, Monitor, SuccessFilled, VideoPlay, PieChart,
  Refresh, Search, ArrowRight, User, VideoCamera, Picture
} from '@element-plus/icons-vue'
import { t } from '../../utils/locale'

const authStore = useAuthStore()
const tournaments = ref([])
const selectedTournamentId = ref(null)
const matches = ref([])
const isLoading = ref(false)
const courts = ref([])
const referees = ref([])
const isUploading = ref(false)
const selectedCategoryId = ref('all')

const showScheduleDialog = ref(false)
const showScoreDialog = ref(false)

const schedulingMatch = ref(null)
const scheduleForm = ref({ court_id: null, start_time: '', referee_name: '', referee_phone: '' })

const scoringMatch = ref(null)
const scoreForm = ref({ 
  winner_side: '',
  sets: [{ side_a: 0, side_b: 0 }],
  video_url: '',
  image_url: '',
  referee_name: '',
  referee_phone: ''
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

const currentTournament = computed(() => {
  return tournaments.value.find(t => t.id === selectedTournamentId.value) || null
})

const categories = computed(() => {
  if (!currentTournament.value) return []
  return currentTournament.value.categories || []
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
    const params = { tournament_id: selectedTournamentId.value }
    if (selectedCategoryId.value !== 'all') {
      params.category_id = selectedCategoryId.value
    }
    
    const data = await apiClient.get('/api/matches/', { params })
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
  scheduleForm.value.referee_name = match.referee_name || ''
  scheduleForm.value.referee_phone = match.referee_phone || ''
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
  scoreForm.value.winner_side = match.winner_side || ''
  scoreForm.value.video_url = match.video_url || ''
  scoreForm.value.image_url = match.image_url || ''
  scoreForm.value.referee_name = match.referee_name || ''
  scoreForm.value.referee_phone = match.referee_phone || ''
  showScoreDialog.value = true
}

const handleVideoSuccess = (res) => {
  scoreForm.value.video_url = res.url
  ElMessage.success("Tải video lên thành công!")
}

const handleImageSuccess = (res) => {
  scoreForm.value.image_url = res.url
  ElMessage.success("Tải ảnh lên thành công!")
}

const beforeUpload = (file) => {
  isUploading.value = true
  return true
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
      winner_side: scoreForm.value.winner_side,
      video_url: scoreForm.value.video_url,
      image_url: scoreForm.value.image_url,
      referee_name: scoreForm.value.referee_name,
      referee_phone: scoreForm.value.referee_phone
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

      <div class="header-tabs-wrap" v-if="selectedTournamentId && categories.length > 0">
        <el-tabs v-model="selectedCategoryId" @tab-change="fetchMatches" class="category-tabs-premium">
          <el-tab-pane label="TẤT CẢ NỘI DUNG" name="all" />
          <el-tab-pane 
            v-for="cat in categories" 
            :key="cat.id" 
            :label="cat.name.toUpperCase()" 
            :name="cat.id" 
          />
        </el-tabs>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="saas-content-area" v-loading="isLoading">
      <!-- Empty State -->
      <div v-if="selectedTournamentId === null || selectedTournamentId === ''" class="saas-empty-state">
        <div class="empty-hero">
          <div class="hero-blob"></div>
          <el-icon class="hero-icon"><Monitor /></el-icon>
        </div>
        <h3>ĐIỀU HÀNH TRẬN ĐẤU</h3>
        <p class="empty-tip">Vui lòng chọn một giải đấu để bắt đầu cập nhật lịch thi đấu, tỉ số và quản lý diễn biến các trận đấu.</p>
        <div class="empty-action-hint">
          <el-icon><Search /></el-icon>
          <span>Sử dụng bộ chọn giải đấu ở thanh công cụ phía trên</span>
        </div>
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
                <div class="header-meta-info">
                  <span class="match-id">#{{ m.match_no || m.id }}</span>
                  <el-tag v-if="m.category_name" size="small" effect="light" class="category-indicator-tag">
                    {{ m.category_name }}
                  </el-tag>
                </div>
                <div class="status-indicator" :class="`is-${getStatusType(m.status)}`">
                  <span class="dot"></span>
                  <span>{{ m.status.toUpperCase() }}</span>
                </div>
              </div>

              <div class="match-card-body">
                <div class="side-item" :class="{ 'is-winner': m.winner_side === 'side_a' }">
                  <div class="team-meta-container">
                    <div class="player-unit">
                      <el-avatar :size="24" :src="m.p1_avatar" class="avatar-mini">
                        <el-icon><User /></el-icon>
                      </el-avatar>
                      <span class="player-name">{{ m.p1_name || '...' }}</span>
                    </div>
                    <div v-if="m.p1_partner_name" class="player-unit">
                      <el-avatar :size="24" :src="m.p1_partner_avatar" class="avatar-mini">
                        <el-icon><User /></el-icon>
                      </el-avatar>
                      <span class="player-name">{{ m.p1_partner_name }}</span>
                    </div>
                  </div>
                  <el-icon v-if="m.winner_side === 'side_a'" class="win-check"><SuccessFilled /></el-icon>
                </div>

                <div class="vs-divider">
                  <div class="line"></div>
                  <span class="vs-text">VS</span>
                  <div class="line"></div>
                </div>

                <div class="side-item" :class="{ 'is-winner': m.winner_side === 'side_b' }">
                  <div class="team-meta-container">
                    <div class="player-unit">
                      <el-avatar :size="24" :src="m.p2_avatar" class="avatar-mini">
                        <el-icon><User /></el-icon>
                      </el-avatar>
                      <span class="player-name">{{ m.p2_name || '...' }}</span>
                    </div>
                    <div v-if="m.p2_partner_name" class="player-unit">
                      <el-avatar :size="24" :src="m.p2_partner_avatar" class="avatar-mini">
                        <el-icon><User /></el-icon>
                      </el-avatar>
                      <span class="player-name">{{ m.p2_partner_name }}</span>
                    </div>
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
         <div class="referee-info-grid">
           <el-form-item label="Tên trọng tài">
             <el-input v-model="scheduleForm.referee_name" placeholder="Nhập tên trọng tài" />
           </el-form-item>
           <el-form-item label="SĐT trọng tài">
             <el-input v-model="scheduleForm.referee_phone" placeholder="Nhập số điện thoại" />
           </el-form-item>
         </div>
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
                    <div class="team-meta-container">
                      <div class="player-unit">
                        <el-avatar :size="20" :src="scoringMatch.p1_avatar"><el-icon><User /></el-icon></el-avatar>
                        <strong>{{ scoringMatch.p1_name }}</strong>
                      </div>
                      <div v-if="scoringMatch.p1_partner_name" class="player-unit">
                        <el-avatar :size="20" :src="scoringMatch.p1_partner_avatar"><el-icon><User /></el-icon></el-avatar>
                        <strong>{{ scoringMatch.p1_partner_name }}</strong>
                      </div>
                    </div>
                  </div>
                </el-radio>
                <el-radio value="side_b" border class="winner-radio-premium">
                  <div class="radio-content">
                    <div class="team-meta-container">
                      <div class="player-unit">
                        <el-avatar :size="20" :src="scoringMatch.p2_avatar"><el-icon><User /></el-icon></el-avatar>
                        <strong>{{ scoringMatch.p2_name }}</strong>
                      </div>
                      <div v-if="scoringMatch.p2_partner_name" class="player-unit">
                        <el-avatar :size="20" :src="scoringMatch.p2_partner_avatar"><el-icon><User /></el-icon></el-avatar>
                        <strong>{{ scoringMatch.p2_partner_name }}</strong>
                      </div>
                    </div>
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
          <div class="media-management">
             <span class="section-label">Thông tin bổ sung</span>
             <div class="media-inputs">
                <el-form label-position="top">
                   <div class="referee-info-grid" style="margin-bottom: 10px;">
                      <el-form-item label="Tên trọng tài">
                        <el-input v-model="scoreForm.referee_name" placeholder="Tên trọng tài chính" />
                      </el-form-item>
                      <el-form-item label="SĐT trọng tài">
                        <el-input v-model="scoreForm.referee_phone" placeholder="Số điện thoại" />
                      </el-form-item>
                   </div>

                   <div class="upload-grid">
                      <el-form-item label="Video trận đấu (Highlight)">
                        <el-upload
                          class="saas-upload"
                          :action="`${MAIN_API_URL}/api/upload/image`"
                          :headers="{ Authorization: `Bearer ${authStore.accessToken}` }"
                          :on-success="handleVideoSuccess"
                          :before-upload="beforeUpload"
                          :show-file-list="false"
                        >
                          <el-button v-if="!scoreForm.video_url" type="primary" plain :icon="VideoCamera">Tải Video lên</el-button>
                          <div v-else class="upload-result success">
                             <el-icon><Check /></el-icon> <span>Đã có Video</span>
                             <el-button link type="primary" @click.stop="scoreForm.video_url = ''">Thay đổi</el-button>
                          </div>
                        </el-upload>
                        <el-input v-model="scoreForm.video_url" size="small" placeholder="Hoặc dán URL Youtube/Cloudinary" style="margin-top: 8px;" />
                      </el-form-item>

                      <el-form-item label="Ảnh kết quả / Trao giải">
                        <el-upload
                          class="saas-upload"
                          :action="`${MAIN_API_URL}/api/upload/image`"
                          :headers="{ Authorization: `Bearer ${authStore.accessToken}` }"
                          :on-success="handleImageSuccess"
                          :before-upload="beforeUpload"
                          :show-file-list="false"
                        >
                          <el-button v-if="!scoreForm.image_url" type="success" plain :icon="Picture">Tải Ảnh lên</el-button>
                          <div v-else class="upload-result success">
                             <el-icon><Check /></el-icon> <span>Đã có Ảnh</span>
                             <el-button link type="primary" @click.stop="scoreForm.image_url = ''">Thay đổi</el-button>
                          </div>
                        </el-upload>
                      </el-form-item>
                   </div>
                </el-form>
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

.header-tabs-wrap {
  margin-top: 10px;
  width: 100%;
}

:deep(.category-tabs-premium) {
  --el-tabs-header-height: 50px;
}
:deep(.category-tabs-premium .el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #f1f5f9;
}
:deep(.category-tabs-premium .el-tabs__item) {
  font-weight: 800;
  font-size: 0.75rem;
  color: #94a3b8;
  letter-spacing: 0.05em;
  padding: 0 24px;
}
:deep(.category-tabs-premium .el-tabs__item.is-active) {
  color: #2563eb;
}
:deep(.category-tabs-premium .el-tabs__active-bar) {
  background-color: #2563eb;
  height: 3px;
  border-radius: 3px;
}

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
  background: white;
  padding: 100px 20px;
  border-radius: 32px;
  border: 1px dashed #cbd5e1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-hero {
  position: relative;
  width: 120px;
  height: 120px;
  margin-bottom: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-blob {
  position: absolute;
  inset: 0;
  background: #fef2f2;
  border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%;
  animation: blobMorph 8s infinite alternate;
  opacity: 0.6;
}

@keyframes blobMorph {
  0% { border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%; transform: scale(1); }
  100% { border-radius: 70% 30% 30% 70% / 70% 70% 30% 30%; transform: scale(1.1); }
}

.hero-icon {
  font-size: 64px;
  color: #dc2626;
  position: relative;
  z-index: 2;
}

.saas-empty-state h3 {
  font-size: 1.6rem;
  font-weight: 900;
  color: #1e293b;
  margin: 0 0 12px;
  letter-spacing: -0.02em;
}

.empty-tip {
  color: #64748b;
  font-size: 1.1rem;
  max-width: 450px;
  margin: 0 auto 24px;
  line-height: 1.6;
}

.empty-action-hint {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  background: #fff1f2;
  border-radius: 99px;
  color: #e11d48;
  font-weight: 700;
  font-size: 0.9rem;
  border: 1px solid #fecaca;
}

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

.header-meta-info { display: flex; align-items: center; gap: 8px; }
.category-indicator-tag { 
  background-color: #f5f3ff !important; 
  border-color: #ddd6fe !important; 
  color: #7c3aed !important; 
  font-weight: 800;
  font-size: 0.65rem;
  border-radius: 6px;
}

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
.team-meta-container { display: flex; flex-direction: column; gap: 8px; flex-grow: 1; overflow: hidden; }
.player-unit { display: flex; align-items: center; gap: 10px; overflow: hidden; }
.player-name { font-weight: 800; color: #1e293b; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.avatar-mini { border: 1.5px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }
.win-check { color: #10b981; font-size: 18px; flex-shrink: 0; }

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
.winner-selection-premium, .sets-management, .media-management { display: flex; flex-direction: column; gap: 8px; }
.section-label { font-size: 0.85rem; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; display: block; }
.media-inputs { background: #f8fafc; padding: 16px; border-radius: 16px; border: 1px solid #e2e8f0; }

.winner-grid-selector { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; width: 100%; }
.winner-radio-premium {
  height: auto !important; padding: 20px 16px !important; border-radius: 20px !important;
  margin: 0 !important; width: 100%; display: flex; align-items: flex-start;
}
.radio-content { display: flex; width: 100%; }
:deep(.el-radio.is-bordered.is-checked) { background: #f0fdf4 !important; border-color: #10b981 !important; border-width: 2px; }
:deep(.el-radio__label) { width: 100%; padding-left: 0; }

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

.upload-grid, .referee-info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px; border-top: 1px dashed #e2e8f0; padding-top: 15px; }
.referee-info-grid { border-top: none; padding-top: 0; margin-top: 0; }
.upload-result { display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 0.85rem; }
.upload-result.success { color: #059669; }
.saas-upload { display: block; }

@media (max-width: 768px) {
  .saas-stats-grid { grid-template-columns: 1fr 1fr; }
  .saas-header { flex-direction: column; align-items: stretch; }
  .saas-tournament-selector { width: 100%; }
  .match-cards-grid { grid-template-columns: 1fr; }
  .winner-grid-selector { grid-template-columns: 1fr; }
}
</style>