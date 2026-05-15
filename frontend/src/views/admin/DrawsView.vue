<script setup>
import { onMounted, ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { tournamentService } from '../../services/tournamentService' 
import { useAuthStore } from '../../stores/auth' 
import { ElMessage } from 'element-plus'
import apiClient from '../../services/apiClient'
import { t } from '../../utils/locale'
import { 
  Trophy, Finished, EditPen, Menu,
  CircleCheckFilled, CircleCloseFilled,
  Search, Refresh, Edit, Delete
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const tournaments = ref([])
const selectedTournamentId = ref(null)
const matches = ref([])
const isLoading = ref(false)
const generating = ref(false)
const lastDrawSummary = ref(null)

const selectedCategoryId = ref(null)

// --- BIẾN CHO BỐC THĂM BAN ĐẦU ---
const isDrawDialogOpen = ref(false)
const drawForm = ref({
  category_id: null,
  format_type: 'knockout',
  num_groups: 1
})

// --- BIẾN CHO VÒNG PLAYOFF ---
const isPlayoffDialogOpen = ref(false)
const generatingPlayoff = ref(false)
const playoffForm = ref({
  category_id: null,
  advancers_per_group: 2
})

const openDrawDialog = () => {
  drawForm.value.category_id = selectedCategoryId.value
  isDrawDialogOpen.value = true
}
const openPlayoffDialog = () => {
  playoffForm.value.category_id = selectedCategoryId.value
  isPlayoffDialogOpen.value = true
}

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

const selectedCategory = computed(() => {
  if (!selectedCategoryId.value || !currentTournament.value?.categories) return null
  return currentTournament.value.categories.find(c => c.id === selectedCategoryId.value)
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

// Các hàm fetchMatches và handleTournamentChange đã được dời xuống dưới để gộp vào luồng khởi tạo chính.

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

// Tải dữ liệu các trận đấu
const fetchMatches = async () => {
  if (!selectedTournamentId.value) {
    matches.value = []
    return
  }
  isLoading.value = true
  try {
    // API support category filtering
    const url = `/api/tournaments/${selectedTournamentId.value}/matches` + 
                (selectedCategoryId.value ? `?category_id=${selectedCategoryId.value}` : '')
    const data = await apiClient.get(url)
    matches.value = data
  } catch (err) {
    ElMessage.error(t('admin.loadMatchesError') || 'Error loading brackets: ' + err.message)
    matches.value = []
  } finally {
    isLoading.value = false
  }
}

// Xử lý khi chọn giải đấu khác từ dropdown
const handleTournamentChange = (id) => {
  selectedCategoryId.value = null // Reset category when tournament changes
  router.push({ query: { ...route.query, tournamentId: id, categoryId: undefined } })
}

const handleCategoryChange = (catId) => {
  router.push({ query: { ...route.query, categoryId: catId } })
}

// Chỉ theo dõi ID để cập nhật dữ liệu trận đấu
watch(() => [route.query.tournamentId, route.query.categoryId], async ([newId, newCatId]) => {
  if (newId) {
    selectedTournamentId.value = parseInt(newId)
    
    // Auto-select first category if not specified
    if (!newCatId && currentTournament.value?.categories?.length) {
      selectedCategoryId.value = currentTournament.value.categories[0].id
      handleCategoryChange(selectedCategoryId.value)
      return
    }
    
    selectedCategoryId.value = newCatId ? parseInt(newCatId) : null
    await fetchMatches()
  } else {
    selectedTournamentId.value = null
    selectedCategoryId.value = null
    matches.value = []
  }
}, { immediate: true })

onMounted(async () => {
  isLoading.value = true
  try {
    await fetchTournaments()
    // Không tự động fill ID từ query để tránh gây bối rối cho người dùng, 
    // buộc người dùng phải chọn giải đấu từ dropdown.
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="saas-container">
    <section class="saas-action-bar">
      <div class="bar-left">
        <div class="page-title-wrap">
          <div class="title-icon"><el-icon><Trophy /></el-icon></div>
          <div>
            <h2 class="page-title">{{ $t('admin.drawingMatrix') }}</h2>
            <p class="page-subtitle">{{ $t('admin.drawingMatrixDesc') || 'Quản lý bốc thăm và sơ đồ nhánh đấu' }}</p>
          </div>
        </div>
      </div>

      <div class="bar-right">
        <div class="control-cluster">
          <el-select v-model="selectedTournamentId" :placeholder="$t('admin.selectTournamentPlaceholder')" class="tournament-selector" @change="handleTournamentChange" filterable>
            <el-option v-for="t in tournaments" :key="t.id" :label="t.name" :value="t.id">
              <div class="t-opt">
                <span class="t-name">{{ t.name }}</span>
                <el-tag size="small" :type="t.status === 'open' ? 'success' : 'info'" effect="plain">{{ t.status.toUpperCase() }}</el-tag>
              </div>
            </el-option>
          </el-select>

          <!-- Category selector removed and moved to tabs below -->

          <el-button v-if="hasGroupStage" type="danger" :disabled="!selectedTournamentId || !selectedCategoryId" :loading="generatingPlayoff" @click="openPlayoffDialog" class="saas-btn-action is-danger">
            <el-icon class="mr-1"><Finished /></el-icon> {{ $t('admin.finalizeGroups') }}
          </el-button>
          
          <el-button type="primary" :disabled="!canDraw || !selectedCategoryId" :loading="generating" @click="openDrawDialog" class="saas-btn-action is-primary">
            <el-icon class="mr-1"><EditPen /></el-icon> {{ $t('admin.startNewDraw') }}
          </el-button>
        </div>
      </div>
    </section>

    <!-- Tab chọn thể thức thi đấu -->
    <section class="category-tabs-section" v-if="selectedTournamentId && currentTournament?.categories?.length">
      <el-tabs v-model="selectedCategoryId" @tab-change="handleCategoryChange" class="draws-tabs-premium">
        <el-tab-pane 
          v-for="cat in currentTournament.categories" 
          :key="cat.id" 
          :label="cat.name.toUpperCase()" 
          :name="cat.id"
        />
      </el-tabs>
    </section>

    <section class="saas-draw-viewport" v-loading="isLoading">
      <div v-if="!selectedTournamentId" class="saas-empty-state-hero">
        <div class="hero-content">
          <div class="hero-visual">
            <div class="visual-blob"></div>
            <el-icon class="visual-icon"><Trophy /></el-icon>
          </div>
          <h2 class="hero-title">{{ t('admin.selectTournamentToStart') || 'CHỌN GIẢI ĐẤU ĐỂ BẮT ĐẦU' }}</h2>
          <p class="hero-desc">Hệ thống đang sẵn sàng. Vui lòng chọn một giải đấu từ menu phía trên để thực hiện bóc thăm, quản lý sơ đồ nhánh đấu và lịch thi đấu.</p>
          <div class="hero-hint">
            <el-icon><Search /></el-icon>
            <span>Sử dụng bộ chọn giải đấu ở thanh công cụ</span>
          </div>
        </div>
      </div>
      <div v-else-if="matches.length === 0" class="saas-empty-state">
        <el-empty :description="$t('admin.noMatchesState')">
          <el-button type="primary" plain round @click="openDrawDialog" :disabled="!canDraw">
            {{ $t('admin.startNewDraw') }}
          </el-button>
        </el-empty>
      </div>
      
      <div v-else class="saas-stages-grid">
        
        <!-- Vòng Bảng -->
        <div v-if="groupRounds.length > 0" class="saas-stage-block group-stage">
          <div class="stage-header-modern">
            <div class="header-icon"><el-icon><Menu /></el-icon></div>
            <div class="header-text">
              <h3>{{ $t('admin.stage1Title') }}</h3>
              <span>{{ $t('admin.stage1Desc') }}</span>
            </div>
          </div>

          <div class="group-board-horizontal">
            <div v-for="round in groupRounds" :key="round.roundCode" class="group-lane">
              <div class="lane-header"><span class="lane-tag">{{ round.roundCode }}</span></div>
              <div class="lane-content">
                <div v-for="m in round.items" :key="m.id" class="saas-match-card">
                  <div class="m-card-header">
                    <span class="m-id">#{{ m.match_no }}</span>
                    <el-tag size="small" :type="m.status === 'completed' ? 'success' : 'warning'" effect="dark" class="m-status-tag">
                      {{ m.status?.toUpperCase() }}
                    </el-tag>
                  </div>
                  <div class="m-card-body">
                    <div class="team-row" :class="{ 'is-winner': m.winner_side === 'side_a' }">
                      <div class="team-meta-stack">
                        <span class="team-name">{{ m.p1_name || '---' }}</span>
                        <span v-if="m.p1_partner_name" class="partner-subtext">& {{ m.p1_partner_name }}</span>
                      </div>
                      <el-icon v-if="m.winner_side === 'side_a'" class="win-icon"><CircleCheckFilled /></el-icon>
                    </div>
                    <div class="team-row" :class="{ 'is-winner': m.winner_side === 'side_b' }">
                      <div class="team-meta-stack">
                        <span class="team-name">{{ m.p2_name || '---' }}</span>
                        <span v-if="m.p2_partner_name" class="partner-subtext">& {{ m.p2_partner_name }}</span>
                      </div>
                      <el-icon v-if="m.winner_side === 'side_b'" class="win-icon"><CircleCheckFilled /></el-icon>
                    </div>
                  </div>
                  <div class="m-card-footer" v-if="m.result_note || m.score_summary">
                    <span class="score-label">{{ $t('admin.score') }}</span>
                    <span class="score-value">{{ m.result_note || m.score_summary }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Vòng Loại Trực Tiếp -->
        <div v-if="knockoutRounds.length > 0" class="saas-stage-block knockout-stage">
          <div class="stage-header-modern">
            <div class="header-icon knockout"><el-icon><Finished /></el-icon></div>
            <div class="header-text">
              <h3>{{ $t('admin.stage2Title') }}</h3>
              <span>{{ $t('admin.stage2Desc') }}</span>
            </div>
          </div>
          
          <div class="bracket-viewport-wrapper">
            <div class="bracket-flex-board">
              <div v-for="(round, index) in knockoutRounds" :key="round.roundCode" class="bracket-column-lane">
                <div class="lane-header"><span class="lane-tag knockout">{{ round.roundCode }}</span></div>
                
                <div class="bracket-matches-stack">
                  <div v-for="m in round.items" :key="m.id" class="bracket-match-node">
                    <div class="connector-line-in" v-if="index > 0"></div>

                    <div class="saas-match-card bracket-card">
                      <div class="m-card-header compact">
                        <span class="m-id">#{{ m.match_no }}</span>
                        <span class="m-status-dot" :class="m.status"></span>
                      </div>
                      <div class="m-card-body">
                        <div class="team-row compact" :class="{ 'is-winner': m.winner_side === 'side_a' }">
                          <div class="team-meta-stack">
                            <span class="team-name">{{ m.p1_name || '---' }}</span>
                            <span v-if="m.p1_partner_name" class="partner-subtext mini">& {{ m.p1_partner_name }}</span>
                          </div>
                        </div>
                        <div class="team-row compact" :class="{ 'is-winner': m.winner_side === 'side_b' }">
                          <div class="team-meta-stack">
                            <span class="team-name">{{ m.p2_name || '---' }}</span>
                            <span v-if="m.p2_partner_name" class="partner-subtext mini">& {{ m.p2_partner_name }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div class="connector-line-out" v-if="index < knockoutRounds.length - 1"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>

  <el-dialog v-model="isDrawDialogOpen" :title="$t('admin.drawOptionsTitle')" width="450px" destroy-on-close>
    <el-form :model="drawForm" label-position="top">
      <el-form-item :label="$t('admin.category')">
        <el-select v-model="drawForm.category_id" style="width: 100%" placeholder="Chọn nội dung để bốc thăm">
          <el-option 
            v-for="cat in currentTournament?.categories" 
            :key="cat.id" 
            :label="cat.name" 
            :value="cat.id" 
          />
        </el-select>
      </el-form-item>
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
      <el-form-item :label="$t('admin.category')">
        <el-select v-model="playoffForm.category_id" style="width: 100%" placeholder="Chọn nội dung chốt bảng">
          <el-option 
            v-for="cat in currentTournament?.categories" 
            :key="cat.id" 
            :label="cat.name" 
            :value="cat.id" 
          />
        </el-select>
      </el-form-item>
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
</div>
</template>

<style scoped>
/* MODER SAAS LAYOUT */
.saas-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 10px;
}

.saas-action-bar {
  background: white;
  padding: 24px 32px;
  border-radius: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.03);
  border: 1px solid #f1f5f9;
}

.page-title-wrap {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-icon {
  width: 48px;
  height: 48px;
  background: #eff6ff;
  color: #2563eb;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.page-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 800;
  color: #1e293b;
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: 4px 0 0;
  font-size: 0.9rem;
  color: #64748b;
}

.control-cluster {
  display: flex;
  gap: 12px;
  align-items: center;
}

.tournament-selector {
  width: 250px;
}

.category-selector {
  width: 200px;
}

.saas-btn-action {
  height: 45px;
  padding: 0 24px;
  font-weight: 800 !important;
  border-radius: 12px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.saas-btn-action.is-primary {
  background: #2563eb !important;
  border: none !important;
}

.saas-btn-action.is-danger {
  background: #dc2626 !important;
  border: none !important;
}

.saas-btn-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 15px rgba(0,0,0,0.1);
}

.saas-empty-state-hero {
  background: white;
  min-height: 500px;
  border-radius: 32px;
  border: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.02);
}

.hero-content { text-align: center; max-width: 500px; padding: 40px; }
.hero-visual { position: relative; width: 140px; height: 140px; margin: 0 auto 32px; display: flex; align-items: center; justify-content: center; }
.visual-blob { position: absolute; inset: 0; background: #eff6ff; border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%; animation: blobMorph 8s infinite alternate; opacity: 0.6; }
.visual-icon { font-size: 80px; color: #3b82f6; position: relative; z-index: 2; }
.hero-title { font-size: 1.8rem; font-weight: 900; color: #0f172a; margin-bottom: 16px; letter-spacing: -0.02em; }
.hero-desc { color: #64748b; font-size: 1.1rem; line-height: 1.6; margin-bottom: 32px; }
.hero-hint { display: inline-flex; align-items: center; gap: 10px; padding: 12px 24px; background: #f8fafc; border-radius: 99px; color: #3b82f6; font-weight: 700; font-size: 0.9rem; border: 1px solid #e2e8f0; }

@keyframes blobMorph {
  0% { border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%; transform: scale(1); }
  100% { border-radius: 70% 30% 30% 70% / 70% 70% 30% 30%; transform: scale(1.1); }
}

/* STAGE BLOCKS */
.saas-stage-block {
  background: white;
  padding: 32px;
  border-radius: 24px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 4px 20px rgba(0,0,0,0.02);
  margin-bottom: 32px;
}

.stage-header-modern {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 2px solid #f8fafc;
}

.header-icon {
  width: 40px;
  height: 40px;
  background: #f0fdf4;
  color: #16a34a;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.header-icon.knockout {
  background: #fef2f2;
  color: #dc2626;
}

.header-text h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 800;
  color: #1e293b;
}

.header-text span {
  font-size: 0.85rem;
  color: #94a3b8;
}

/* MATCH CARDS */
.saas-match-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.saas-match-card:hover {
  border-color: #2563eb;
  box-shadow: 0 8px 16px rgba(0,0,0,0.04);
}

.m-card-header {
  background: #f8fafc;
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f1f5f9;
}

.m-id {
  font-size: 0.75rem;
  font-weight: 800;
  color: #64748b;
}

.m-card-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.team-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fcfcfc;
  border: 1px solid transparent;
}

.team-row.is-winner {
  background: #f0fdf4;
  border-color: #dcfce7;
}

.team-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1e293b;
}

.is-winner .team-name {
  color: #16a34a;
}

.win-icon {
  color: #16a34a;
  font-size: 18px;
}

.m-card-footer {
  padding: 10px 16px;
  background: #f8fafc;
  border-top: 1px dashed #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.score-label {
  color: #94a3b8;
  font-weight: 600;
}

.score-value {
  color: #1e293b;
  font-weight: 800;
}

/* HORIZONTAL SCROLL FOR GROUPS */
.group-board-horizontal {
  display: flex;
  gap: 24px;
  overflow-x: auto;
  padding-bottom: 12px;
}

.group-lane {
  min-width: 300px;
  flex: 0 0 300px;
}

.lane-header {
  margin-bottom: 16px;
  text-align: center;
}

.lane-tag {
  background: #f1f5f9;
  color: #475569;
  padding: 6px 20px;
  border-radius: 99px;
  font-weight: 800;
  font-size: 0.75rem;
  text-transform: uppercase;
  border: 1px solid #e2e8f0;
}

.lane-tag.knockout {
  background: #fef2f2;
  color: #dc2626;
  border-color: #fecaca;
}

.lane-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* BRACKET LAYOUT */
.bracket-viewport-wrapper {
  overflow-x: auto;
  padding: 20px 0;
}

.bracket-flex-board {
  display: flex;
  gap: 80px;
  min-width: max-content;
}

.bracket-column-lane {
  display: flex;
  flex-direction: column;
  min-width: 280px;
}

.bracket-matches-stack {
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  flex-grow: 1;
  gap: 40px;
}

.bracket-match-node {
  position: relative;
  display: flex;
  align-items: center;
}

.bracket-card {
  width: 100%;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}

.m-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e2e8f0;
}

.m-status-dot.completed { background: #16a34a; }
.m-status-dot.scheduled { background: #2563eb; }
.m-status-dot.pending { background: #f59e0b; }

/* CONNECTORS */
.connector-line-in {
  position: absolute;
  left: -40px;
  width: 40px;
  height: 2px;
  background: #e2e8f0;
}

.connector-line-out {
  position: absolute;
  right: -40px;
  width: 40px;
  height: 2px;
  background: #e2e8f0;
}

@media (max-width: 1024px) {
  .saas-action-bar {
    flex-direction: column;
    gap: 20px;
    align-items: flex-start;
  }
  .control-cluster {
    width: 100%;
    flex-wrap: wrap;
  }
}

.saas-tournament-selector { width: 380px; }

.category-tabs-section {
  background: white;
  padding: 0 32px;
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.03);
  border: 1px solid #f1f5f9;
}

:deep(.draws-tabs-premium) {
  --el-tabs-header-height: 60px;
}
:deep(.draws-tabs-premium .el-tabs__nav-wrap::after) {
  display: none;
}
:deep(.draws-tabs-premium .el-tabs__item) {
  font-weight: 800;
  font-size: 0.85rem;
  color: #94a3b8;
  letter-spacing: 0.05em;
  padding: 0 32px;
  transition: all 0.3s;
}
:deep(.draws-tabs-premium .el-tabs__item.is-active) {
  color: #2563eb;
  font-size: 0.9rem;
}
:deep(.draws-tabs-premium .el-tabs__active-bar) {
  background-color: #2563eb;
  height: 4px;
  border-radius: 4px;
}

.team-meta-stack {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.partner-subtext {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
}
.partner-subtext.mini {
  font-size: 0.7rem;
}
</style>