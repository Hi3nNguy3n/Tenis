<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Trophy, Calendar, Location, User, Pointer, Check,
  ArrowLeft, Monitor, VideoPlay, Timer, Connection,
  UserFilled, CircleCheckFilled, InfoFilled
} from '@element-plus/icons-vue'
import apiClient from '../../services/apiClient'
import { t } from '../../utils/locale'

const router = useRouter()

// Dữ liệu nguồn
const tournamentsList = ref([])
const playersList = ref([])
const courtsList = ref([])
const paidChallenges = ref([]) // Danh sách kèo đã nộp tiền

const loadingData = ref(true)
const submitting = ref(false)
const activeTab = ref('manual') // manual hoặc approve

// Dữ liệu Form
const form = ref({
  tournament_id: null,
  match_name: '',
  side_a_id: null,
  side_b_id: null,
  side_a2_id: null,
  side_b2_id: null,
  match_type: 'singles', // 'singles' or 'doubles'
  court_id: null,
  match_date: '',
  start_time: '',
  challenge_id: null // Lưu ID nếu đây là duyệt kèo thách đấu
})

const fetchInitialData = async () => {
  loadingData.value = true
  try {
    const [tourRes, playerResRaw, courtRes, challengeRes] = await Promise.all([
      apiClient.get('/api/tournaments/', { params: { limit: 100 } }),
      apiClient.get('/api/players/rankings'),
      apiClient.get('/api/courts/').catch(() => []),
      apiClient.get('/api/challenges/admin/pending-approvals').catch(() => [])
    ])
    
    tournamentsList.value = Array.isArray(tourRes) ? tourRes : []
    courtsList.value = Array.isArray(courtRes) ? courtRes : []
    paidChallenges.value = challengeRes

    const rawPlayers = Array.isArray(playerResRaw) ? playerResRaw : (playerResRaw?.items || [])
    playersList.value = rawPlayers.map(p => ({
      id: p.id || p.player_id, 
      full_name: p.full_name || p.user?.full_name || 'Vô danh',
      elo_points: p.elo_points || 1200
    }))
  } catch (error) {
    ElMessage.error(t('admin.loadInitDataError'))
  } finally {
    loadingData.value = false
  }
}

// Khi Admin chọn 1 kèo từ danh sách nộp tiền
const selectChallenge = (c) => {
  form.value.side_a_id = c.side_a_id
  form.value.side_b_id = c.side_b_id
  form.value.side_a2_id = c.side_a2_id || null
  form.value.side_b2_id = c.side_b2_id || null
  form.value.match_type = c.match_type || 'singles'
  form.value.match_date = c.proposed_date
  form.value.match_name = c.match_name
  form.value.challenge_id = c.id
  form.value.tournament_id = null
  activeTab.value = 'manual' // Nhảy về tab form để gán sân
  ElMessage.success(`${t('admin.assignScheduleNow')} #${c.id}.`)
}

const submitMatch = async () => {
  if (!form.value.side_a_id || !form.value.side_b_id || !form.value.court_id || !form.value.start_time) {
    return ElMessage.warning(t('admin.fillAllFields'))
  }

  if (form.value.match_type === 'doubles') {
    if (!form.value.side_a2_id || !form.value.side_b2_id) {
      return ElMessage.warning('Vui lòng chọn đầy đủ đồng đội cho cả 2 bên khi tạo trận đấu đôi!')
    }
  }

  submitting.value = true
  try {
    // 1. Tạo trận đấu chính thức
    await apiClient.post('/api/matches/', form.value)
    
    // 2. Nếu đi từ Kèo thách đấu, gọi API cập nhật trạng thái kèo thành 'scheduled'
    if (form.value.challenge_id) {
       await apiClient.patch(`/api/challenges/${form.value.challenge_id}/respond`, { status: 'scheduled' })
    }

    ElMessage.success(t('admin.scheduleSuccess'))
    router.push({ path: '/admin/matches' })
  } catch (error) {
    ElMessage.error('Lỗi: ' + (error.response?.data?.detail || error.message))
  } finally {
    submitting.value = false
  }
}

const playerA = computed(() => playersList.value.find(p => p.id === form.value.side_a_id))
const playerB = computed(() => playersList.value.find(p => p.id === form.value.side_b_id))
const playerA2 = computed(() => playersList.value.find(p => p.id === form.value.side_a2_id))
const playerB2 = computed(() => playersList.value.find(p => p.id === form.value.side_b2_id))

const getAvailablePlayers = (excludeIds) => {
  return playersList.value.filter(p => !excludeIds.includes(p.id))
}

const sideAOptions = computed(() => getAvailablePlayers([form.value.side_b_id, form.value.side_a2_id, form.value.side_b2_id].filter(Boolean)))
const sideBOptions = computed(() => getAvailablePlayers([form.value.side_a_id, form.value.side_a2_id, form.value.side_b2_id].filter(Boolean)))
const sideA2Options = computed(() => getAvailablePlayers([form.value.side_a_id, form.value.side_b_id, form.value.side_b2_id].filter(Boolean)))
const sideB2Options = computed(() => getAvailablePlayers([form.value.side_a_id, form.value.side_b_id, form.value.side_a2_id].filter(Boolean)))

onMounted(fetchInitialData)
</script>

<template>
  <div class="saas-container" v-loading="loadingData">
    <!-- Action Bar -->
    <section class="saas-header">
      <div class="header-left">
        <el-button @click="router.back()" circle :icon="ArrowLeft" class="saas-icon-btn mr-4" />
        <div class="operation-badge-premium">
          <el-icon class="mr-1"><Connection /></el-icon>
          <span>Match Organizer</span>
        </div>
        <div class="header-titles">
          <h2 class="saas-title">{{ $t('admin.createMatch') }}</h2>
          <p class="saas-subtitle">{{ $t('admin.createMatchSub') }}</p>
        </div>
      </div>
    </section>

    <!-- Main Content -->
    <main class="saas-content-area">
      <el-tabs v-model="activeTab" class="saas-tabs-premium">
        <!-- Tab 1: Approve Challenges -->
        <el-tab-pane name="approve">
          <template #label>
            <div class="tab-label-custom">
              <el-icon><Pointer /></el-icon>
              <span>{{ $t('admin.paidChallengesTab') }}</span>
              <el-badge v-if="paidChallenges.length" :value="paidChallenges.length" class="tab-badge-saas" />
            </div>
          </template>

          <div class="challenges-grid-premium">
            <div v-for="c in paidChallenges" :key="c.id" class="challenge-premium-card">
              <div class="cp-card-left">
                <div class="cp-icon-box"><el-icon><VideoPlay /></el-icon></div>
                <div class="cp-info">
                  <div class="cp-pairing">
                    <span class="player-name">{{ c.challenger_name }}</span>
                    <span class="vs-tag">VS</span>
                    <span class="player-name">{{ c.challenged_name }}</span>
                  </div>
                  <div class="cp-meta">
                    <span class="meta-item"><el-icon><Calendar /></el-icon> {{ c.proposed_date }}</span>
                    <span v-if="c.notes" class="meta-note">"{{ c.notes }}"</span>
                  </div>
                </div>
              </div>
              <el-button type="primary" :icon="Check" round @click="selectChallenge(c)" class="saas-btn-primary mini">
                {{ $t('admin.assignScheduleNow') }}
              </el-button>
            </div>
            
            <div v-if="!paidChallenges.length" class="saas-empty-state-mini">
              <div class="empty-blob"></div>
              <el-icon class="empty-icon"><InfoFilled /></el-icon>
              <p>{{ $t('admin.noPendingChallenges') }}</p>
            </div>
          </div>
        </el-tab-pane>

        <!-- Tab 2: Manual Setup -->
        <el-tab-pane name="manual">
          <template #label>
            <div class="tab-label-custom">
              <el-icon><Trophy /></el-icon>
              <span>{{ $t('admin.matchSetupTab') }}</span>
            </div>
          </template>

          <div class="saas-form-layout">
            <el-form label-position="top" class="saas-form-premium">
              
              <!-- Section 1: Event & Participants -->
              <div class="form-section-premium">
                <div class="section-header-saas">
                  <span class="accent-line p-blue"></span>
                  <div class="sh-text">
                    <h3>{{ $t('admin.eventInfo') }}</h3>
                    <p>Cấu hình thông tin cơ bản cho trận đấu</p>
                  </div>
                </div>

                <div class="saas-form-grid triple" style="grid-template-columns: 1fr 1fr 1fr; margin-bottom: 20px;">
                  <el-form-item :label="$t('admin.tournamentLabel')">
                    <el-select v-model="form.tournament_id" placeholder="Chọn giải đấu (không bắt buộc)" class="w-full" clearable filterable>
                      <template #prefix><el-icon><Trophy /></el-icon></template>
                      <el-option v-for="t in tournamentsList" :key="t.id" :label="t.name" :value="t.id" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item :label="$t('admin.matchNameLabel')">
                    <el-input v-model="form.match_name" :placeholder="$t('admin.matchNamePlaceholder')" />
                  </el-form-item>

                  <el-form-item label="Thể thức trận đấu">
                    <el-radio-group v-model="form.match_type" size="default" style="width: 100%; display: flex;">
                      <el-radio-button value="singles" style="flex: 1; text-align: center;">Đơn (1vs1)</el-radio-button>
                      <el-radio-button value="doubles" style="flex: 1; text-align: center;">Đôi (2vs2)</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                </div>

                <!-- Pairing Arena -->
                <div class="saas-pairing-arena">
                  <div class="arena-column">
                    <span class="column-label">SIDE A</span>
                    <el-select v-model="form.side_a_id" placeholder="Chọn VĐV A" filterable class="w-full arena-select" style="margin-bottom: 12px;">
                      <template #prefix><el-icon><User /></el-icon></template>
                      <el-option v-for="p in sideAOptions" :key="p.id" :label="p.full_name" :value="p.id">
                        <div class="p-opt-saas">
                          <span>{{ p.full_name }}</span>
                          <el-tag size="small" type="info">ELO: {{ p.elo_points }}</el-tag>
                        </div>
                      </el-option>
                    </el-select>

                    <div v-if="form.match_type === 'doubles'">
                      <el-select v-model="form.side_a2_id" placeholder="Chọn Đồng đội VĐV A" filterable class="w-full arena-select" style="margin-bottom: 12px;">
                        <template #prefix><el-icon><User /></el-icon></template>
                        <el-option v-for="p in sideA2Options" :key="p.id" :label="p.full_name" :value="p.id">
                          <div class="p-opt-saas">
                            <span>{{ p.full_name }}</span>
                            <el-tag size="small" type="info">ELO: {{ p.elo_points }}</el-tag>
                          </div>
                        </el-option>
                      </el-select>
                    </div>

                    <div class="player-indicators-group" style="display: flex; flex-direction: column; gap: 8px;">
                      <div class="player-indicator" v-if="playerA">
                        <el-avatar :size="48" class="saas-avatar-premium">{{ playerA.full_name.charAt(0) }}</el-avatar>
                        <div class="pi-info">
                          <strong>{{ playerA.full_name }}</strong>
                          <span>{{ playerA.elo_points }} ELO (A1)</span>
                        </div>
                      </div>
                      <div class="player-indicator" v-if="form.match_type === 'doubles' && playerA2">
                        <el-avatar :size="48" class="saas-avatar-premium" style="background: #ecf5ff; color: #409eff;">{{ playerA2.full_name.charAt(0) }}</el-avatar>
                        <div class="pi-info">
                          <strong>{{ playerA2.full_name }}</strong>
                          <span>{{ playerA2.elo_points }} ELO (A2)</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="vs-divider-premium">
                    <div class="vs-circle-glow">VS</div>
                  </div>

                  <div class="arena-column">
                    <span class="column-label">SIDE B</span>
                    <el-select v-model="form.side_b_id" placeholder="Chọn VĐV B" filterable class="w-full arena-select" style="margin-bottom: 12px;">
                      <template #prefix><el-icon><User /></el-icon></template>
                      <el-option v-for="p in sideBOptions" :key="p.id" :label="p.full_name" :value="p.id">
                        <div class="p-opt-saas">
                          <span>{{ p.full_name }}</span>
                          <el-tag size="small" type="info">ELO: {{ p.elo_points }}</el-tag>
                        </div>
                      </el-option>
                    </el-select>

                    <div v-if="form.match_type === 'doubles'">
                      <el-select v-model="form.side_b2_id" placeholder="Chọn Đồng đội VĐV B" filterable class="w-full arena-select" style="margin-bottom: 12px;">
                        <template #prefix><el-icon><User /></el-icon></template>
                        <el-option v-for="p in sideB2Options" :key="p.id" :label="p.full_name" :value="p.id">
                          <div class="p-opt-saas">
                            <span>{{ p.full_name }}</span>
                            <el-tag size="small" type="info">ELO: {{ p.elo_points }}</el-tag>
                          </div>
                        </el-option>
                      </el-select>
                    </div>

                    <div class="player-indicators-group" style="display: flex; flex-direction: column; gap: 8px;">
                      <div class="player-indicator reverse" v-if="playerB">
                        <div class="pi-info">
                          <strong>{{ playerB.full_name }}</strong>
                          <span>{{ playerB.elo_points }} ELO (B1)</span>
                        </div>
                        <el-avatar :size="48" class="saas-avatar-premium">{{ playerB.full_name.charAt(0) }}</el-avatar>
                      </div>
                      <div class="player-indicator reverse" v-if="form.match_type === 'doubles' && playerB2">
                        <div class="pi-info">
                          <strong>{{ playerB2.full_name }}</strong>
                          <span>{{ playerB2.elo_points }} ELO (B2)</span>
                        </div>
                        <el-avatar :size="48" class="saas-avatar-premium" style="background: #fdf2f2; color: #f56c6c;">{{ playerB2.full_name.charAt(0) }}</el-avatar>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Section 2: Court & Time -->
              <div class="form-section-premium">
                <div class="section-header-saas">
                  <span class="accent-line p-orange"></span>
                  <div class="sh-text">
                    <h3>{{ $t('admin.courtAndTime') }}</h3>
                    <p>Sắp xếp thời gian và địa điểm diễn ra</p>
                  </div>
                </div>

                <div class="saas-form-grid triple">
                  <el-form-item :label="$t('admin.courtLabel')" required>
                    <el-select v-model="form.court_id" placeholder="Chọn sân thi đấu" class="w-full">
                      <template #prefix><el-icon><Location /></el-icon></template>
                      <el-option v-for="c in courtsList" :key="c.id" :label="c.court_name" :value="c.id" />
                    </el-select>
                  </el-form-item>

                  <el-form-item :label="$t('admin.dateLabel')" required>
                    <el-date-picker v-model="form.match_date" type="date" value-format="YYYY-MM-DD" placeholder="Ngày thi đấu" class="w-full" />
                  </el-form-item>

                  <el-form-item :label="$t('admin.timeLabel')" required>
                    <el-time-picker v-model="form.start_time" format="HH:mm" value-format="HH:mm:ss" placeholder="Giờ thi đấu" class="w-full" />
                  </el-form-item>
                </div>
              </div>

              <div class="form-actions-saas">
                <el-button type="primary" size="large" :loading="submitting" @click="submitMatch" class="saas-btn-primary is-full">
                  {{ $t('admin.confirmAndSchedule') }}
                </el-button>
              </div>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </main>
  </div>
</template>

<style scoped>
.saas-container { display: flex; flex-direction: column; gap: 32px; min-height: 100%; }

/* Action Bar */
.saas-header { display: flex; align-items: center; justify-content: space-between; }
.header-left { display: flex; align-items: center; }
.saas-icon-btn { width: 44px; height: 44px; border-radius: 12px !important; border: 1px solid #e2e8f0 !important; background: #fff !important; }

.operation-badge-premium {
  background: #eff6ff; color: #2563eb; padding: 10px 20px; border-radius: 14px;
  font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
  display: inline-flex; align-items: center; margin-right: 24px;
}

.header-titles { display: flex; flex-direction: column; gap: 4px; }
.saas-title { font-size: 1.8rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.02em; }
.saas-subtitle { font-size: 0.95rem; color: #64748b; margin: 0; }

/* Tabs & Content */
.saas-content-area { background: #fff; border-radius: 32px; border: 1px solid #f1f5f9; box-shadow: 0 10px 40px rgba(0,0,0,0.02); overflow: hidden; }

:deep(.saas-tabs-premium) { border: none !important; }
:deep(.saas-tabs-premium .el-tabs__header) { margin: 0; padding: 0 32px; background: #fafafa; border-bottom: 1px solid #f1f5f9; }
:deep(.saas-tabs-premium .el-tabs__nav-wrap::after) { display: none; }
:deep(.saas-tabs-premium .el-tabs__item) { height: 72px; font-weight: 800; font-size: 0.95rem; color: #94a3b8; transition: all 0.3s; }
:deep(.saas-tabs-premium .el-tabs__item.is-active) { color: #2563eb; }
:deep(.saas-tabs-premium .el-tabs__active-bar) { height: 4px; border-radius: 4px; }

.tab-label-custom { display: flex; align-items: center; gap: 10px; position: relative; }
.tab-badge-saas { position: absolute; top: -10px; right: -25px; }

/* Challenges Grid */
.challenges-grid-premium { padding: 32px; display: grid; gap: 16px; }
.challenge-premium-card {
  background: #fff; border: 1px solid #f1f5f9; border-radius: 20px; padding: 24px;
  display: flex; justify-content: space-between; align-items: center;
  transition: all 0.3s ease; box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.challenge-premium-card:hover { transform: translateX(8px); border-color: #3b82f6; box-shadow: 0 12px 24px rgba(15, 23, 42, 0.05); }

.cp-card-left { display: flex; align-items: center; gap: 20px; }
.cp-icon-box { width: 48px; height: 48px; border-radius: 14px; background: #eff6ff; color: #3b82f6; display: flex; align-items: center; justify-content: center; font-size: 20px; }

.cp-pairing { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.player-name { font-weight: 800; color: #1e293b; font-size: 1.1rem; }
.vs-tag { font-weight: 900; font-style: italic; color: #ef4444; font-size: 0.75rem; background: #fef2f2; padding: 4px 10px; border-radius: 8px; }

.cp-meta { display: flex; align-items: center; gap: 16px; font-size: 0.85rem; color: #64748b; }
.meta-item { display: flex; align-items: center; gap: 6px; font-weight: 600; }
.meta-note { color: #94a3b8; font-style: italic; border-left: 2px solid #e2e8f0; padding-left: 12px; }

/* Form Layout */
.saas-form-layout { padding: 40px; max-width: 900px; margin: 0 auto; }
.form-section-premium { margin-bottom: 48px; }

.section-header-saas { display: flex; gap: 16px; margin-bottom: 32px; }
.accent-line { width: 4px; height: 44px; border-radius: 4px; }
.p-blue { background: #3b82f6; }
.p-orange { background: #f97316; }

.sh-text h3 { font-size: 1.25rem; font-weight: 900; color: #0f172a; margin: 0; }
.sh-text p { font-size: 0.85rem; color: #64748b; margin-top: 4px; font-weight: 600; }

.saas-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.saas-form-grid.triple { grid-template-columns: 1fr 1fr 1fr; }

:deep(.el-form-item__label) { font-weight: 800; color: #475569; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }
:deep(.el-input__wrapper), :deep(.el-select__wrapper) { background: #f8fafc !important; border: 1px solid #e2e8f0 !important; border-radius: 12px !important; padding: 10px 16px !important; box-shadow: none !important; }

/* Pairing Arena */
.saas-pairing-arena {
  margin-top: 40px; background: #fafafa; border: 2px dashed #e2e8f0; border-radius: 28px;
  padding: 40px; display: flex; align-items: center; gap: 32px; position: relative;
}

.arena-column { flex: 1; display: flex; flex-direction: column; gap: 16px; }
.column-label { font-size: 0.75rem; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.2em; text-align: center; }

.vs-divider-premium { width: 80px; display: flex; justify-content: center; position: relative; }
.vs-circle-glow {
  width: 60px; height: 60px; background: #ef4444; color: #fff; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 1.2rem;
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.4); border: 4px solid #fff; z-index: 5;
}

.player-indicator { display: flex; align-items: center; gap: 16px; background: #fff; padding: 16px; border-radius: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
.player-indicator.reverse { justify-content: flex-end; }
.pi-info { display: flex; flex-direction: column; gap: 2px; }
.pi-info strong { font-size: 1rem; color: #0f172a; font-weight: 800; }
.pi-info span { font-size: 0.75rem; color: #10b981; font-weight: 900; }

.saas-avatar-premium { border: 2px solid #eff6ff; background: #eff6ff; color: #3b82f6; font-weight: 800; }

.p-opt-saas { display: flex; justify-content: space-between; align-items: center; width: 100%; }

/* Form Footer */
.form-actions-saas { margin-top: 48px; border-top: 1px solid #f1f5f9; padding-top: 32px; }
.saas-btn-primary { 
  height: 56px !important; border-radius: 16px !important; font-weight: 900 !important; 
  font-size: 1.05rem !important; border: none !important;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2) !important;
}
.saas-btn-primary.mini { height: 44px !important; font-size: 0.9rem !important; }
.is-full { width: 100%; }

/* Empty State Mini */
.saas-empty-state-mini { text-align: center; padding: 60px 0; position: relative; }
.empty-icon { font-size: 48px; color: #cbd5e1; position: relative; z-index: 2; margin-bottom: 12px; }
.empty-blob { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 100px; height: 100px; background: #f8fafc; border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%; animation: blob-anim 10s infinite alternate; }

@keyframes blob-anim {
  0% { border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%; }
  100% { border-radius: 70% 30% 30% 70% / 70% 70% 30% 30%; }
}

.mr-4 { margin-right: 16px; }
.w-full { width: 100%; }
</style>
