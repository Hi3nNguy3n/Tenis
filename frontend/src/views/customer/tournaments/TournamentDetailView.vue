<script setup>
import { onMounted, computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTournamentStore } from '../../../stores/tournament'
import { useAuthStore } from '../../../stores/auth'
import { apiClient } from '../../../services/apiClient'
import { 
  Trophy, 
  Calendar as CalendarIcon, 
  Location, 
  Check,
  User, 
  ArrowRight, 
  InfoFilled, 
  Ticket 
} from '@element-plus/icons-vue'
import { currentLocale, t } from '../../../utils/locale'

const route = useRoute()
const router = useRouter()
const tournamentStore = useTournamentStore()
const authStore = useAuthStore()

const tournamentId = route.params.id

const activeTab = ref('info')
const publicMatches = ref([])
const loadingBracket = ref(false)
const standingsData = ref([])
const loadingStandings = ref(false)
const isAlreadyRegistered = ref(false)

const fetchStandings = async () => {
  loadingStandings.value = true
  try {
    const data = await apiClient.get(`/api/tournaments/${tournamentId}/standings`)
    standingsData.value = data
  } catch (err) {
    console.error("Lỗi tải bảng xếp hạng:", err)
  } finally {
    loadingStandings.value = false
  }
}

const isRegistrationOpen = computed(() => {
  if (!tournament.value) return false;
  if (tournament.value.status !== 'open') return false;
  
  if (tournament.value.registration_close_at) {
    const closeDate = new Date(tournament.value.registration_close_at);
    const now = new Date();
    if (now > closeDate) return false;
  }
  
  return true;
});

const isPastDeadline = computed(() => {
  if (!tournament.value?.registration_close_at) return false;
  return new Date() >= new Date(tournament.value.registration_close_at);
});

onMounted(async () => {
  tournamentStore.fetchTournamentById(tournamentId)
  fetchBracket()
  fetchStandings()

  if (authStore.isAuthenticated) {
    try {
      const myRegs = await apiClient.get('/api/registrations/my-registrations')
      const exists = myRegs.find(r => r.tournament_id === parseInt(tournamentId) && r.status !== 'cancelled' && r.status !== 'rejected')
      if (exists) {
        isAlreadyRegistered.value = true
      }
    } catch (err) {
      console.error("Lỗi kiểm tra đăng ký:", err)
    }
  }
})

const fetchBracket = async () => {
  loadingBracket.value = true
  try {
    const data = await apiClient.get(`/api/tournaments/${tournamentId}/public-bracket`)
    publicMatches.value = data
  } catch (err) {
    console.error("Không tải được sơ đồ nhánh đấu:", err)
  } finally {
    loadingBracket.value = false
  }
}

const groupedMatches = computed(() => {
  const groups = {}
  publicMatches.value.forEach(m => {
    if (!groups[m.round_code]) groups[m.round_code] = []
    groups[m.round_code].push(m)
  })
  const order = ['FINAL', 'SF', 'QF', 'R16', 'R32', 'R64']
  return Object.keys(groups)
    .sort((a, b) => order.indexOf(a) - order.indexOf(b))
    .map(key => ({
      label: key,
      items: groups[key].sort((a, b) => a.match_no - b.match_no)
    }))
})

const tournament = computed(() => tournamentStore.currentTournament)

const goToRegister = () => {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  router.push({ name: 'tournament-register', params: { id: tournamentId } })
}

const formatDate = (dateStr) => {
  if (!dateStr) return t('tournaments.notUpdated')
  return new Date(dateStr).toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}
</script>

<template>
  <div v-if="tournament" class="neo-tournament-page">
    
    <div class="neo-hero">
      <div class="hero-glow glow-1"></div>
      <div class="hero-glow glow-2"></div>
      
      <div class="container hero-inner">
        <div class="hero-meta-top">
          <span class="neo-badge" :class="tournament.status">
            <span class="badge-dot"></span>
            {{ tournament.status.toUpperCase() }}
          </span>
          <span class="tour-type">{{ tournament.category_type }}</span>
        </div>
        
        <h1 class="hero-title">{{ tournament.name }}</h1>
        
        <div class="hero-details">
          <div class="hd-item">
            <el-icon><CalendarIcon /></el-icon>
            <div>
              <span class="hd-lbl">{{ t('tournaments.startDate') }}</span>
              <span class="hd-val">{{ formatDate(tournament.start_date) }} - {{ formatDate(tournament.end_date) }}</span>
            </div>
          </div>
          <div class="hd-divider"></div>
          <div class="hd-item">
            <el-icon><Location /></el-icon>
            <div>
              <span class="hd-lbl">{{ t('tournaments.location') }}</span>
              <span class="hd-val">{{ tournament.location || t('tournaments.notUpdated') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="container main-overlap">
      <div class="neo-grid">
        
        <div class="neo-col-main">
          
          <div class="neo-tabs-container">
            <el-tabs v-model="activeTab" class="neo-tabs">
              
              <el-tab-pane :label="t('tournaments.overview')" name="info">
                <div class="bento-layout">
                  <div class="bento-box box-sm">
                    <el-icon class="bento-icon"><User /></el-icon>
                    <span class="bento-lbl">{{ t('tournaments.category') }}</span>
                    <strong class="bento-val">{{ tournament.gender_division }}</strong>
                  </div>
                  <div class="bento-box box-sm">
                    <el-icon class="bento-icon"><Trophy /></el-icon>
                    <span class="bento-lbl">{{ t('tournaments.format') }}</span>
                    <strong class="bento-val">{{ tournament.format_type }}</strong>
                  </div>
                  
                  <div class="bento-box box-sm">
                    <el-icon class="bento-icon"><Ticket /></el-icon>
                    <span class="bento-lbl">{{ t('tournaments.drawSize') }}</span>
                    <strong class="bento-val">{{ tournament.draw_size }} {{ t('tournaments.playersCount') }}</strong>
                  </div>
                  <div class="bento-box box-sm">
                    <el-icon class="bento-icon"><Location /></el-icon>
                    <span class="bento-lbl">{{ t('tournaments.surface') }}</span>
                    <strong class="bento-val">{{ tournament.surface_type || 'Hard Court' }}</strong>
                  </div>

                  <div class="bento-box box-lg">
                    <h3>{{ t('tournaments.aboutTournament') }}</h3>
                    <p>
                      {{ tournament.name }} {{ t('tournaments.tournamentDesc') }}
                    </p>
                    <div class="bento-highlight">
                      <strong>{{ t('tournaments.registrationDeadline') }}</strong> 
                      <span>{{ t('tournaments.from') }} {{ formatDate(tournament.registration_open_at) }} {{ t('tournaments.to') }} {{ formatDate(tournament.registration_close_at) }}</span>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane :label="t('tournaments.bracket')" name="bracket">
                <div v-loading="loadingBracket" class="neo-bracket-box">
                  <div v-if="publicMatches.length === 0" class="empty-state">
                    <div class="es-icon">🎾</div>
                    <p>{{ t('tournaments.bracketNotDrawn') }}</p>
                  </div>
                  
                  <div v-else class="neo-bracket-scroll">
                    <div v-for="round in groupedMatches" :key="round.label" class="bracket-col" :class="{ 'is-group': round.label.includes('G') }">
                      <h4 class="round-header">{{ round.label }}</h4>
                      <div class="match-nodes">
                        
                        <div v-for="m in round.items" :key="m.id" class="match-node">
                          <div class="node-player" :class="{ 'is-win': m.winner_side === 'side_a' }">
                            <span class="n-name">{{ m.p1_name }}</span>
                            <span class="n-score" v-if="m.score">{{ m.score.split('-')[0] || '' }}</span>
                            <el-icon class="n-check" v-if="m.winner_side === 'side_a'"><Check /></el-icon>
                          </div>
                          <div class="node-divider"></div>
                          <div class="node-player" :class="{ 'is-win': m.winner_side === 'side_b' }">
                            <span class="n-name">{{ m.p2_name }}</span>
                            <span class="n-score" v-if="m.score">{{ m.score.split('-')[1] || '' }}</span>
                            <el-icon class="n-check" v-if="m.winner_side === 'side_b'"><Check /></el-icon>
                          </div>
                          <div class="node-status" v-if="!m.score && m.status !== 'completed'">{{ m.status === 'ongoing' ? t('tournaments.live') : t('tournaments.upcoming') }}</div>
                        </div>

                      </div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane :label="t('tournaments.standings')" name="standings">
                <div v-loading="loadingStandings" class="neo-standings-box">
                  <div v-if="standingsData.length === 0" class="empty-state">
                    <div class="es-icon">📊</div>
                    <p>{{ t('tournaments.noGroupData') }}</p>
                  </div>
                  
                  <div v-else>
                    <div v-for="group in standingsData" :key="group.group_name" class="standings-group">
                      <h3 class="sg-title">{{ group.group_name }}</h3>
                      
                      <div class="neo-table-wrapper">
                        <table class="neo-table">
                          <thead>
                            <tr>
                              <th class="text-center">#</th>
                              <th>{{ t('tournaments.athlete') }}</th>
                              <th class="text-center">{{ t('tournaments.matches') }}</th>
                              <th class="text-center">{{ t('tournaments.winLoss') }}</th>
                              <th class="text-center">{{ t('tournaments.setDiff') }}</th>
                              <th class="text-center">{{ t('tournaments.gameDiff') }}</th>
                              <th class="text-center">{{ t('tournaments.points') }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="(row, idx) in group.rankings" :key="row.player_name">
                              <td class="text-center rank-col">{{ idx + 1 }}</td>
                              <td class="name-col"><strong>{{ row.player_name }}</strong></td>
                              <td class="text-center">{{ row.played }}</td>
                              <td class="text-center">{{ row.won }} - {{ row.lost }}</td>
                              <td class="text-center" :class="{'text-green': row.set_diff > 0, 'text-red': row.set_diff < 0}">
                                {{ row.set_diff > 0 ? '+' + row.set_diff : row.set_diff }}
                              </td>
                              <td class="text-center" :class="{'text-green': row.game_diff > 0, 'text-red': row.game_diff < 0}">
                                {{ row.game_diff > 0 ? '+' + row.game_diff : row.game_diff }}
                              </td>
                              <td class="text-center pts-col">{{ row.points }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </div>

        <aside class="neo-col-sidebar">
          <div class="neo-action-card sticky">
            
            <div class="ac-header">
              <h2>{{ t('tournaments.entryTicket') }}</h2>
              <div class="price-tag">
                {{ tournament.entry_fee ? new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(tournament.entry_fee) : t('tournaments.free') }}
              </div>
            </div>

            <div class="ac-progress-section">
              <div class="prog-labels">
                <span class="pl-title">{{ t('tournaments.registeredCount') }}</span>
                <strong class="pl-count">{{ tournament.current_participants }} / {{ tournament.max_participants || tournament.draw_size }}</strong>
              </div>
              <div class="prog-track">
                <div class="prog-fill" :style="{ width: Math.min(100, (tournament.current_participants / (tournament.max_participants || tournament.draw_size)) * 100) + '%' }"></div>
              </div>
              <p class="prog-hint" v-if="tournament.status === 'open'">{{ t('tournaments.registrationCloseAt') }} {{ formatDate(tournament.registration_close_at) }}</p>
            </div>

            <div class="ac-actions">
              <template v-if="isRegistrationOpen">
                <button 
                  class="neo-btn-primary" 
                  @click="goToRegister" 
                  :disabled="isAlreadyRegistered || tournament.current_participants >= (tournament.max_participants || tournament.draw_size)"
                  :class="{ 'is-disabled': isAlreadyRegistered || tournament.current_participants >= (tournament.max_participants || tournament.draw_size) }"
                >
                  <span v-if="isAlreadyRegistered"><el-icon><Check /></el-icon> {{ t('tournaments.alreadyRegistered') }}</span>
                  <span v-else-if="tournament.current_participants >= (tournament.max_participants || tournament.draw_size)">{{ t('tournaments.fullyBooked') }}</span>
                  <span v-else>{{ t('tournaments.registerNow') }} <el-icon><ArrowRight /></el-icon></span>
                </button>
              </template>
              
              <template v-else>
                <div class="ac-status-msg">
                  <el-icon><InfoFilled /></el-icon>
                  <span v-if="isPastDeadline">{{ t('tournaments.registrationExpired') }}</span>
                  <span v-else-if="tournament.status === 'draft'">{{ t('tournaments.registrationNotOpen') }}</span>
                  <span v-else-if="tournament.status === 'ongoing'">{{ t('tournaments.tournamentOngoing') }}</span>
                  <span v-else>{{ t('tournaments.tournamentClosed') }}</span>
                </div>
              </template>
            </div>

          </div>
        </aside>

      </div>
    </div>
  </div>
  
  <div v-else-if="tournamentStore.loading" class="neo-loading">
    <div class="spinner-ring"></div>
    <p>{{ t('tournaments.loadingData') }}</p>
  </div>
</template>

<style scoped>
/* Giữ nguyên toàn bộ cấu trúc CSS gốc */
.neo-tournament-page { --bg-body: #f1f5f9; --bg-surface: #ffffff; --hero-bg: #0f172a; --hero-glow-1: #3b82f6; --hero-glow-2: #10b981; --text-primary: #0f172a; --text-secondary: #475569; --text-muted: #94a3b8; --border-light: #e2e8f0; --accent: #2563eb; --accent-hover: #1d4ed8; --radius-xl: 24px; --radius-lg: 16px; --radius-md: 12px; background: var(--bg-body); min-height: 100vh; font-family: 'Inter', -apple-system, sans-serif; color: var(--text-primary); padding-bottom: 5rem; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }
.text-center { text-align: center; }
.text-right { text-align: right; }
.text-green { color: #16a34a !important; font-weight: 700;}
.text-red { color: #dc2626 !important; font-weight: 700;}
.neo-hero { position: relative; background: var(--hero-bg); padding: 6rem 0 7rem; overflow: hidden; color: white; z-index: 1; }
.hero-glow { position: absolute; width: 400px; height: 400px; border-radius: 50%; filter: blur(100px); opacity: 0.3; z-index: -1; pointer-events: none; }
.glow-1 { top: -10%; right: 10%; background: var(--hero-glow-1); }
.glow-2 { bottom: -20%; left: 5%; background: var(--hero-glow-2); }
.hero-inner { position: relative; z-index: 2; }
.hero-meta-top { display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem; }
.neo-badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 99px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); backdrop-filter: blur(4px); }
.badge-dot { width: 6px; height: 6px; border-radius: 50%; background: #94a3b8; }
.neo-badge.open .badge-dot { background: #34d399; box-shadow: 0 0 8px #34d399;}
.neo-badge.ongoing .badge-dot { background: #38bdf8; box-shadow: 0 0 8px #38bdf8;}
.tour-type { font-size: 0.85rem; font-weight: 600; color: #cbd5e1; text-transform: uppercase; letter-spacing: 1px;}
.hero-title { font-size: clamp(2.5rem, 5vw, 4rem); font-weight: 800; line-height: 1.1; margin: 0 0 2rem; letter-spacing: -0.02em; }
.hero-details { display: inline-flex; align-items: center; gap: 2rem; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 1rem 1.5rem; border-radius: var(--radius-lg); backdrop-filter: blur(10px); }
.hd-item { display: flex; align-items: center; gap: 12px; }
.hd-item .el-icon { font-size: 1.5rem; color: #94a3b8; }
.hd-item div { display: flex; flex-direction: column; gap: 2px; }
.hd-lbl { font-size: 0.7rem; text-transform: uppercase; color: #94a3b8; font-weight: 600; letter-spacing: 0.05em;}
.hd-val { font-size: 0.95rem; font-weight: 600; color: white; }
.hd-divider { width: 1px; height: 30px; background: rgba(255,255,255,0.2); }
.main-overlap { position: relative; z-index: 10; margin-top: -4rem; }
.neo-grid { display: grid; grid-template-columns: 1fr 360px; gap: 2rem; align-items: start; }
.neo-tabs-container { background: var(--bg-surface); border-radius: var(--radius-xl); padding: 2rem; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); min-height: 500px; }
:deep(.neo-tabs .el-tabs__nav-wrap::after) { display: none; }
:deep(.neo-tabs .el-tabs__nav) { background: var(--bg-body); padding: 4px; border-radius: 12px; }
:deep(.neo-tabs .el-tabs__item) { font-size: 0.85rem; font-weight: 700; color: var(--text-secondary); height: 40px; line-height: 40px; padding: 0 20px !important; border-radius: 8px; transition: 0.3s; }
:deep(.neo-tabs .el-tabs__item.is-active) { background: white; color: var(--text-primary); box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
:deep(.neo-tabs .el-tabs__active-bar) { display: none; }
.bento-layout { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1.5rem; }
.bento-box { background: var(--bg-body); border-radius: var(--radius-lg); padding: 1.5rem; border: 1px solid var(--border-light); }
.box-sm { display: flex; flex-direction: column; gap: 8px; }
.box-lg { grid-column: span 2; display: flex; flex-direction: column; gap: 1rem;}
.bento-icon { font-size: 1.5rem; color: var(--accent); margin-bottom: 4px;}
.bento-lbl { font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase;}
.bento-val { font-size: 1.25rem; font-weight: 800; color: var(--text-primary); }
.box-lg h3 { margin: 0; font-size: 1.2rem; font-weight: 800; color: var(--text-primary);}
.box-lg p { margin: 0; font-size: 0.95rem; line-height: 1.6; color: var(--text-secondary);}
.bento-highlight { background: white; padding: 1rem; border-radius: var(--radius-md); border: 1px solid var(--border-light); display: flex; flex-direction: column; gap: 4px; }
.bento-highlight strong { font-size: 0.85rem; color: var(--text-primary);}
.bento-highlight span { font-size: 0.9rem; color: var(--accent); font-weight: 600;}
.neo-bracket-box { margin-top: 1.5rem; }
.empty-state { text-align: center; padding: 4rem 0; color: var(--text-muted); }
.es-icon { font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;}
.neo-bracket-scroll { display: flex; gap: 30px; overflow-x: auto; padding: 10px 10px 20px; scrollbar-width: thin; }
.bracket-col { min-width: 260px; display: flex; flex-direction: column; position: relative; }
.round-header { text-align: center; font-size: 0.85rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; margin-bottom: 1.5rem; letter-spacing: 1px; }
.match-nodes { display: flex; flex-direction: column; justify-content: space-around; flex-grow: 1; gap: 24px; }
.match-node { background: white; border: 1px solid var(--border-light); border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); position: relative; z-index: 2; transition: 0.2s; }
.match-node:hover { border-color: var(--accent); box-shadow: 0 8px 20px rgba(37, 99, 235, 0.1); transform: translateY(-2px);}
.node-player { display: flex; align-items: center; padding: 10px 14px; gap: 8px; }
.node-player.is-win { background: #f8fafc; }
.node-player.is-win .n-name { font-weight: 800; color: var(--text-primary); }
.node-player.is-win .n-score { font-weight: 800; color: var(--accent); }
.n-name { flex: 1; font-size: 0.9rem; font-weight: 600; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.n-score { font-size: 0.95rem; font-weight: 600; color: var(--text-muted); }
.n-check { color: #10b981; font-weight: bold; font-size: 1rem;}
.node-divider { height: 1px; background: var(--border-light); margin: 0 10px;}
.node-status { text-align: center; font-size: 0.7rem; font-weight: 700; color: white; background: var(--text-muted); padding: 4px; border-radius: 0 0 10px 10px; }
.bracket-col:not(:last-child):not(.is-group) .match-node::after { content: ''; position: absolute; right: -30px; top: 50%; width: 30px; border-top: 2px solid var(--border-light); z-index: 1; }
.bracket-col:not(:first-child):not(.is-group) .match-node::before { content: ''; position: absolute; left: -30px; top: 50%; width: 30px; border-top: 2px solid var(--border-light); z-index: 1; }
.neo-standings-box { margin-top: 1.5rem; }
.standings-group { margin-bottom: 2.5rem; }
.sg-title { font-size: 1.1rem; font-weight: 800; color: var(--text-primary); margin-bottom: 1rem;}
.neo-table-wrapper { background: white; border: 1px solid var(--border-light); border-radius: var(--radius-md); overflow: hidden; }
.neo-table { width: 100%; border-collapse: collapse; }
.neo-table th { background: var(--bg-body); padding: 12px 16px; font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; border-bottom: 1px solid var(--border-light); text-align: left; }
.neo-table td { padding: 12px 16px; font-size: 0.9rem; color: var(--text-secondary); border-bottom: 1px solid var(--border-light); }
.neo-table tr:last-child td { border-bottom: none; }
.name-col { color: var(--text-primary); }
.rank-col { font-weight: 800; color: var(--text-muted); }
.pts-col { font-weight: 800; font-size: 1.05rem; color: var(--accent); }
.neo-col-sidebar { position: relative; }
.sticky { position: sticky; top: 24px; }
.neo-action-card { background: var(--bg-surface); border-radius: var(--radius-xl); padding: 2rem; box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.1); border: 1px solid var(--border-light); }
.ac-header { margin-bottom: 2rem; }
.ac-header h2 { font-size: 1.4rem; font-weight: 800; margin: 0 0 8px; color: var(--text-primary);}
.price-tag { font-size: 2rem; font-weight: 800; color: var(--accent); letter-spacing: -0.02em;}
.ac-progress-section { margin-bottom: 2rem; }
.prog-labels { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 8px;}
.pl-title { font-size: 0.85rem; font-weight: 600; color: var(--text-muted);}
.pl-count { font-size: 1.1rem; font-weight: 800; color: var(--text-primary);}
.prog-track { height: 10px; background: var(--bg-body); border-radius: 99px; overflow: hidden; }
.prog-fill { height: 100%; background: linear-gradient(90deg, var(--hero-glow-1), var(--hero-glow-2)); border-radius: 99px; transition: width 0.8s ease;}
.prog-hint { font-size: 0.8rem; color: #dc2626; font-weight: 600; margin: 8px 0 0; text-align: center;}
.neo-btn-primary { width: 100%; padding: 1.25rem; border-radius: var(--radius-md); border: none; background: var(--text-primary); color: white; font-size: 1rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.2s; }
.neo-btn-primary:hover:not(.is-disabled) { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(15,23,42,0.2); }
.neo-btn-primary.is-disabled { background: var(--bg-body); color: var(--text-muted); cursor: not-allowed; border: 1px solid var(--border-light);}
.ac-status-msg { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 1rem; background: var(--bg-body); border-radius: var(--radius-md); color: var(--text-muted); font-size: 0.85rem; font-weight: 600; }
.neo-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 60vh; }
.spinner-ring { width: 48px; height: 48px; border: 4px solid var(--border-light); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 1024px) { .neo-grid { grid-template-columns: 1fr; } .neo-col-sidebar { order: -1; } .neo-action-card { box-shadow: 0 10px 30px rgba(0,0,0,0.05); } }
@media (max-width: 768px) { .hero-title { font-size: 2rem; } .hero-details { flex-direction: column; align-items: flex-start; gap: 1rem; width: 100%;} .hd-divider { display: none; } .bento-layout { grid-template-columns: 1fr; } .box-lg { grid-column: auto; } }
</style>