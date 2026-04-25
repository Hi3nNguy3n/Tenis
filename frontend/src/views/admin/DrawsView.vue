<script setup>
import { onMounted, ref, computed } from 'vue'
import { tournamentService } from '../../services/tournamentService' 
import { useAuthStore } from '../../stores/auth' 
import { ElMessage } from 'element-plus'
import apiClient from '../../services/apiClient'
import { t } from '../../utils/locale'

const authStore = useAuthStore()
const tournaments = ref([])
const selectedTournamentId = ref(null)
const matches = ref([])
const isLoading = ref(false)
const generating = ref(false)
const lastDrawSummary = ref(null)

// --- BIẾN CHO BỐC THĂM BAN ĐẦU ---
const isDrawDialogOpen = ref(false)
const drawForm = ref({
  format_type: 'knockout',
  num_groups: 1
})

// --- BIẾN CHO VÒNG PLAYOFF ---
const isPlayoffDialogOpen = ref(false)
const generatingPlayoff = ref(false)
const playoffForm = ref({
  advancers_per_group: 2
})

const openDrawDialog = () => isDrawDialogOpen.value = true
const openPlayoffDialog = () => isPlayoffDialogOpen.value = true

const currentUserName = computed(() => {
  return authStore.profile?.full_name || authStore.user?.full_name || 'Admin'
})

const hasGroupStage = computed(() => {
  if (!matches.value) return false
  return matches.value.some(m => m.round_code && m.round_code.includes('G'))
})

const currentTournament = computed(() => {
  return tournaments.value.find(t => t.id === selectedTournamentId.value) || null
})

const canDraw = computed(() => {
  if (!currentTournament.value) return false
  return ['draft', 'open'].includes(currentTournament.value.status)
})

const fetchTournaments = async () => {
  try {
    const data = await tournamentService.getAll({ limit: 100 })
    tournaments.value = data
  } catch (err) {
    ElMessage.error(t('admin.loadTournamentsError') + ': ' + err.message)
  }
}

const fetchMatches = async () => {
  if (!selectedTournamentId.value) return
  isLoading.value = true
  try {
    const data = await tournamentService.getMatches(selectedTournamentId.value)
    matches.value = data
  } catch (err) {
    ElMessage.error(t('admin.loadMatchesError') || 'Error loading brackets: ' + err.message)
    matches.value = []
  } finally {
    isLoading.value = false
  }
}

const confirmGenerateDraw = async () => {
  if (!selectedTournamentId.value) return
  isDrawDialogOpen.value = false
  generating.value = true
  
  try {
    const response = await apiClient.post(`/api/tournaments/${selectedTournamentId.value}/generate-draw`, drawForm.value)
    lastDrawSummary.value = { message: response.message } 
    ElMessage.success(response.message || t('admin.drawSuccess'))
    await fetchMatches()
  } catch (err) {
    const errorMsg = err.response?.data?.detail || err.message
    ElMessage.error(t('admin.drawError') + ': ' + errorMsg)
  } finally {
    generating.value = false
  }
}

const confirmGeneratePlayoff = async () => {
  if (!selectedTournamentId.value) return
  isPlayoffDialogOpen.value = false
  generatingPlayoff.value = true
  
  try {
    const response = await apiClient.post(`/api/tournaments/${selectedTournamentId.value}/generate-playoffs`, playoffForm.value)
    ElMessage.success(response.message || t('admin.playoffSuccess'))
    await fetchMatches() 
  } catch (err) {
    const errorMsg = err.response?.data?.detail || err.message
    ElMessage.error(t('admin.playoffError') + ': ' + errorMsg)
  } finally {
    generatingPlayoff.value = false
  }
}

const roundOrder = (roundCode) => {
  const normalized = String(roundCode || '').toUpperCase()
  if (normalized.includes('G')) return 0
  const orderMap = { R128: 1, R64: 2, R32: 3, R16: 4, R8: 5, QF: 6, SF: 7, F: 8, FINAL: 8 }
  return orderMap[normalized] ?? 99
}

const groupedMatches = computed(() => {
  const roundsMap = {}
  matches.value.forEach(m => {
    if (!roundsMap[m.round_code]) roundsMap[m.round_code] = []
    roundsMap[m.round_code].push(m)
  })
  return Object.entries(roundsMap)
    .map(([roundCode, items]) => ({
      roundCode,
      items: items.slice().sort((a, b) => (a.match_no || 0) - (b.match_no || 0)),
    }))
    .sort((a, b) => roundOrder(a.roundCode) - roundOrder(b.roundCode))
})

const groupRounds = computed(() => groupedMatches.value.filter(r => r.roundCode.includes('G')))
const knockoutRounds = computed(() => groupedMatches.value.filter(r => !r.roundCode.includes('G')))

onMounted(fetchTournaments)
</script>

<template>
  <div class="module-shell">
    <section class="action-bar-glass shadow-sm">
      <div class="action-info">
        <div class="kicker-wrap">
          <span class="section-kicker">Drawing Matrix</span>
          <div class="live-indicator"><span class="dot"></span>ACTIVE</div>
        </div>
        <p>{{ $t('admin.drawingMatrix') }}</p>
        <p v-if="lastDrawSummary" class="draw-summary">System: {{ lastDrawSummary.message }}</p>
      </div>
      <div class="hero-actions">
        <div class="control-group-v2">
          <el-select v-model="selectedTournamentId" :placeholder="$t('admin.selectTournamentPlaceholder')" style="width: 240px" @change="fetchMatches" filterable round>
            <el-option v-for="t in tournaments" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
          
          <el-button v-if="hasGroupStage" type="danger" :disabled="!selectedTournamentId" :loading="generatingPlayoff" @click="openPlayoffDialog" round>
            {{ $t('admin.finalizeGroups') }}
          </el-button>

          <el-button type="primary" :disabled="!canDraw" :loading="generating" @click="openDrawDialog" class="btn-generate-premium" round>
            {{ $t('admin.startNewDraw') }}
          </el-button>
        </div>
      </div>
    </section>

    <section class="draw-container" v-loading="isLoading">
      <div v-if="!selectedTournamentId" class="empty-state">
        <p>{{ $t('admin.emptyDrawState') }}</p>
      </div>
      <div v-else-if="matches.length === 0" class="empty-state">
        <p>{{ $t('admin.noMatchesState') }}</p>
      </div>
      
      <div v-else class="stages-wrapper">
        
        <div v-if="groupRounds.length > 0" class="stage-section">
          <div class="stage-header">
            <h3>{{ $t('admin.stage1Title') }}</h3>
            <p>{{ $t('admin.stage1Desc') }}</p>
          </div>
          <div class="group-board">
            <div v-for="round in groupRounds" :key="round.roundCode" class="group-column">
              <div class="round-tag-wrapper"><span class="round-tag">{{ round.roundCode }}</span></div>
              <div class="matches-list">
                <div v-for="m in round.items" :key="m.id" class="match-card-premium">
                  <div class="match-top">
                    <span class="m-no">{{ $t('admin.matchNo') }} #{{ m.match_no }}</span>
                    <span class="m-status" :class="m.status">{{ m.status?.toUpperCase() }}</span>
                  </div>
                  <div class="match-players">
                    <div class="p-row" :class="{ 'is-winner': m.winner_side === 'side_a', 'is-me': m.p1_name === currentUserName }">
                      <span class="p-name">{{ m.p1_name || '...' }}</span>
                      <span v-if="m.score && m.winner_side" class="m-score-inline">{{ m.winner_side === 'side_a' ? 'WIN' : '' }}</span>
                    </div>
                    <div class="p-row" :class="{ 'is-winner': m.winner_side === 'side_b', 'is-me': m.p2_name === currentUserName }">
                      <span class="p-name">{{ m.p2_name || '...' }}</span>
                      <span v-if="m.score && m.winner_side" class="m-score-inline">{{ m.winner_side === 'side_b' ? 'WIN' : '' }}</span>
                    </div>
                  </div>
                  <div class="match-footer" v-if="m.result_note || m.score_summary">
                    {{ $t('admin.score') }}: <strong>{{ m.result_note || m.score_summary }}</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="groupRounds.length > 0 && knockoutRounds.length > 0" class="stage-divider"></div>

        <div v-if="knockoutRounds.length > 0" class="stage-section">
          <div class="stage-header playoff-header">
            <h3>{{ $t('admin.stage2Title') }}</h3>
            <p>{{ $t('admin.stage2Desc') }}</p>
          </div>
          
          <div class="bracket-board">
            <div v-for="(round, index) in knockoutRounds" :key="round.roundCode" class="bracket-column">
              <div class="round-tag-wrapper"><span class="round-tag knockout-tag">{{ round.roundCode }}</span></div>
              
              <div class="bracket-matches">
                <div v-for="m in round.items" :key="m.id" class="match-wrapper">
                  <div class="bracket-line-left" v-if="index > 0"></div>

                  <div class="match-card-premium knockout-card">
                    <div class="match-top">
                      <span class="m-no">#{{ m.match_no }}</span>
                      <span class="m-status" :class="m.status">{{ m.status?.toUpperCase() }}</span>
                    </div>
                    <div class="match-players">
                      <div class="p-row" :class="{ 'is-winner': m.winner_side === 'side_a' }">
                        <span class="p-name">{{ m.p1_name || '...' }}</span>
                      </div>
                      <div class="p-row" :class="{ 'is-winner': m.winner_side === 'side_b' }">
                        <span class="p-name">{{ m.p2_name || '...' }}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="bracket-line-right" v-if="index < knockoutRounds.length - 1"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  </div>

  <el-dialog v-model="isDrawDialogOpen" :title="$t('admin.drawOptionsTitle')" width="450px" destroy-on-close>
    <el-form :model="drawForm" label-position="top">
      <el-form-item :label="$t('admin.formatType')">
        <el-radio-group v-model="drawForm.format_type">
          <el-radio value="knockout">{{ $t('admin.knockout') }}</el-radio>
          <el-radio value="round_robin">{{ $t('admin.roundRobin') }}</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item v-if="drawForm.format_type === 'round_robin'" :label="$t('admin.numGroups')">
        <el-input-number v-model="drawForm.num_groups" :min="1" :max="16" />
        <div style="font-size: 12px; color: #64748b; margin-top: 5px;">{{ $t('admin.numGroupsDesc') }}</div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="isDrawDialogOpen = false">{{ $t('admin.cancel') }}</el-button>
      <el-button type="primary" @click="confirmGenerateDraw">{{ $t('admin.confirm') }}</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="isPlayoffDialogOpen" :title="$t('admin.finalizePlayoffTitle')" width="450px" destroy-on-close>
    <el-form :model="playoffForm" label-position="top">
      <div style="margin-bottom: 20px; color: #b91c1c; font-size: 0.9rem; background: #fef2f2; padding: 12px; border-radius: 8px;">
        {{ $t('admin.finalizePlayoffNote') }}
      </div>
      <el-form-item :label="$t('admin.advancersPerGroup')">
        <el-input-number v-model="playoffForm.advancers_per_group" :min="1" :max="4" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="isPlayoffDialogOpen = false">{{ $t('admin.cancel') }}</el-button>
      <el-button type="danger" @click="confirmGeneratePlayoff">{{ $t('admin.generatePlayoffBtn') }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
/* GENERAL LAYOUT */
.module-shell { display: grid; gap: 24px; padding: 10px; }
.action-bar-glass { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); padding: 20px 24px; border-radius: 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.03); }
.kicker-wrap { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
.section-kicker { font-size: 0.75rem; font-weight: 800; color: #1e293b; text-transform: uppercase; letter-spacing: 0.05em; }
.live-indicator { display: flex; align-items: center; gap: 6px; background: #f0fdf4; color: #15803d; font-size: 0.65rem; font-weight: 800; padding: 2px 8px; border-radius: 99px; }
.dot { width: 6px; height: 6px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34,197,94,0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(34,197,94,0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34,197,94,0); } }
.action-info p { color: #64748b; font-size: 0.9rem; margin: 0; }
.control-group-v2 { display: flex; gap: 12px; align-items: center; }
.empty-state { text-align: center; color: #94a3b8; font-style: italic; padding: 80px 0; }
.draw-container { background: transparent; min-height: 600px; }
.stages-wrapper { display: grid; gap: 40px; }

/* STAGE HEADERS */
.stage-section { background: white; padding: 30px; border-radius: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.02); border: 1px solid #f1f5f9; overflow-x: auto; }
.stage-header { margin-bottom: 30px; padding-bottom: 15px; border-bottom: 2px solid #f1f5f9; }
.stage-header h3 { margin: 0 0 8px; font-size: 1.4rem; font-weight: 800; color: #0f172a; letter-spacing: -0.02em;}
.stage-header p { margin: 0; color: #64748b; font-size: 0.95rem; }
.playoff-header h3 { color: #b91c1c; } /* Nhấn mạnh Playoff màu đỏ đô */

.stage-divider { height: 4px; background: repeating-linear-gradient(90deg, #e2e8f0, #e2e8f0 10px, transparent 10px, transparent 20px); border-radius: 2px; margin: -10px 20px; opacity: 0.6;}

/* CARDS COMMON */
.match-card-premium { background: white; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); overflow: hidden; transition: all 0.3s ease; position: relative; z-index: 2;}
.match-card-premium:hover { transform: translateY(-3px); border-color: #3b82f6; box-shadow: 0 12px 20px -5px rgba(0,0,0,0.08); }
.match-top { background: #f8fafc; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; }
.m-no { font-size: 0.65rem; font-weight: 800; color: #64748b; text-transform: uppercase;}
.m-status { font-size: 0.6rem; font-weight: 800; padding: 3px 8px; border-radius: 6px; }
.m-status.pending { background: #fff7ed; color: #c2410c; }
.m-status.completed { background: #f0fdf4; color: #15803d; }
.m-status.scheduled { background: #eff6ff; color: #1d4ed8; }
.match-players { padding: 4px; display: grid; gap: 2px; }
.p-row { padding: 12px 14px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
.p-name { font-size: 0.9rem; font-weight: 600; color: #334155; }
.is-winner { background: #f0fdf4; }
.is-winner .p-name { color: #15803d; font-weight: 800; }
.m-score-inline { font-size: 0.7rem; font-weight: 900; color: #15803d; background: #dcfce7; padding: 2px 6px; border-radius: 4px;}
.match-footer { background: #f8fafc; padding: 8px 12px; font-size: 0.8rem; color: #475569; border-top: 1px dashed #e2e8f0; text-align: center;}

/* GROUP STAGE SPECIFIC */
.group-board { display: flex; gap: 24px; }
.group-column { min-width: 280px; display: flex; flex-direction: column; gap: 20px; }
.matches-list { display: grid; gap: 16px; }

/* PLAYOFF BRACKET SPECIFIC (TREE DESIGN) */
.bracket-board { display: flex; gap: 60px; padding: 10px 0; }
.bracket-column { display: flex; flex-direction: column; justify-content: space-around; flex: 1; min-width: 260px; position: relative; }
.bracket-matches { display: flex; flex-direction: column; justify-content: space-around; flex-grow: 1; gap: 30px;}
.match-wrapper { position: relative; width: 100%; display: flex; align-items: center;}
.knockout-card { width: 100%; border: 2px solid #e2e8f0; }

/* CSS TREE CONNECTORS */
.bracket-line-right { position: absolute; right: -30px; top: 50%; width: 30px; height: 2px; background: #cbd5e1; z-index: 1; }
.bracket-line-left { position: absolute; left: -30px; top: 50%; width: 30px; height: 2px; background: #cbd5e1; z-index: 1; }

.round-tag-wrapper { text-align: center; margin-bottom: 24px; }
.round-tag { background: #f1f5f9; color: #475569; padding: 6px 20px; border-radius: 99px; font-weight: 800; font-size: 0.75rem; text-transform: uppercase; border: 1px solid #e2e8f0; }
.knockout-tag { background: #fef2f2; color: #b91c1c; border-color: #fecaca; }
</style>