<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { 
  Search, 
  Right, 
  VideoPlay, 
  Medal, 
  Aim, 
  Calendar, 
  CircleCheck, 
  Close, 
  Trophy, 
  InfoFilled, 
  ArrowRight, 
  User, 
  Check 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import apiClient from '../../services/apiClient'
import { useAuthStore } from '../../stores/auth'
import { t } from '../../utils/locale'

const loading = ref(true)
const tabLoading = ref(false)
const players = ref([])
const recentWinners = ref([])
const searchQuery = ref('')
const playerPage = ref(1)
const PLAYER_PAGE_SIZE = 12
const activeTab = ref('ranking') // Default to 'ranking' (Vận động viên & Xếp hạng)

// --- AUTH STORE ---
const authStore = useAuthStore()

// --- LAZY LOADING STATE ---
const matches = ref([])
const matchesLoaded = ref(false)

const loadMatches = async () => {
  try {
    const data = await apiClient.get('/api/tournaments/matches/all')
    matches.value = Array.isArray(data) ? data : []
  } catch (err) {
    console.error('Error loading matches:', err)
  }
}

// --- TAB CHANGE HANDLER (Lazy Load) ---
const handleTabChange = async (tab) => {
  activeTab.value = tab
  
  if ((tab === 'results' || tab === 'h2h') && !matchesLoaded.value) {
    tabLoading.value = true
    await loadMatches()
    matchesLoaded.value = true
    tabLoading.value = false
  }

  if (tab === 'h2h') {
    await fetchH2HCompare()
  }
}

// --- KẾT QUẢ TAB (Matches - Sorted & Limited to 15) ---
const finishedMatches = computed(() => {
  const completed = matches.value.filter(m => m.status === 'completed')
  
  // Sort by date descending (newest on top)
  const sorted = [...completed].sort((a, b) => {
    const dateA = a.match_date || a.start_time || ''
    const dateB = b.match_date || b.start_time || ''
    return dateB.localeCompare(dateA)
  })
  
  // Limit to 15 matches
  return sorted.slice(0, 15).map(m => {
    return {
      id: m.id,
      tournamentName: m.tournament || m.tournament_name || 'Giao hữu',
      round: m.round_code || m.round || 'Vòng đấu',
      date: m.match_date || (m.start_time ? m.start_time.split('T')[0] : ''),
      score: m.score || m.score_summary || m.result_note || '- / -',
      winner_side: m.winner_side,
      p1_name: m.p1_name,
      p1_avatar: m.p1_avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(m.p1_name || 'P1')}&background=random`,
      p1_partner_name: m.p1_partner_name,
      p1_partner_avatar: m.p1_partner_avatar,
      p2_name: m.p2_name,
      p2_avatar: m.p2_avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(m.p2_name || 'P2')}&background=random`,
      p2_partner_name: m.p2_partner_name,
      p2_partner_avatar: m.p2_partner_avatar,
    }
  })
})

// --- THÁCH ĐẤU MODAL CONFIG ---
const showChallengeDialog = ref(false)
const selectedOpponent = ref(null)
const challengeForm = ref({ 
  date: '', 
  notes: '',
  match_type: 'singles',
  challenger_partner_id: null,
  challenged_partner_id: null
})

const myPlayer = computed(() => {
  if (!players.value || !Array.isArray(players.value)) return null
  return players.value.find(p => p.full_name === authStore.user?.full_name)
})
const myPlayerId = computed(() => myPlayer.value?.player_id || null)

const myPartnerOptions = computed(() => {
  if (!players.value || !Array.isArray(players.value)) return []
  return players.value.filter(p => {
    const isMe = p.player_id === myPlayerId.value
    const isOpponent = p.player_id === selectedOpponent.value?.player_id
    return !isMe && !isOpponent
  })
})

const opponentPartnerOptions = computed(() => {
  if (!players.value || !Array.isArray(players.value)) return []
  return players.value.filter(p => {
    const isMe = p.player_id === myPlayerId.value
    const isOpponent = p.player_id === selectedOpponent.value?.player_id
    const isMyPartner = p.player_id === challengeForm.value.challenger_partner_id
    return !isMe && !isOpponent && !isMyPartner
  })
})

const openChallenge = (p) => {
  if (!authStore.user) {
    ElMessage.warning('Vui lòng đăng nhập để gửi lời thách đấu!')
    return
  }
  selectedOpponent.value = p
  challengeForm.value = { 
    date: '', 
    notes: '', 
    match_type: 'singles',
    challenger_partner_id: null,
    challenged_partner_id: null
  }
  showChallengeDialog.value = true
}

const sendChallengeRequest = async () => {
  if (!challengeForm.value.date) {
    return ElMessage.warning('Vui lòng chọn ngày thi đấu đề xuất!')
  }
  
  if (challengeForm.value.match_type === 'doubles') {
    if (!challengeForm.value.challenger_partner_id || !challengeForm.value.challenged_partner_id) {
      return ElMessage.warning('Vui lòng chọn đầy đủ đồng đội cho cả hai bên khi thách đấu đôi!')
    }
  }

  try {
    await apiClient.post('/api/challenges/', {
      challenged_id: selectedOpponent.value.player_id,
      proposed_date: challengeForm.value.date,
      notes: challengeForm.value.notes,
      match_type: challengeForm.value.match_type,
      challenger_partner_id: challengeForm.value.match_type === 'doubles' ? challengeForm.value.challenger_partner_id : null,
      challenged_partner_id: challengeForm.value.match_type === 'doubles' ? challengeForm.value.challenged_partner_id : null
    })
    ElMessage.success('Gửi yêu cầu thách đấu thành công!')
    showChallengeDialog.value = false
    challengeForm.value = { 
      date: '', 
      notes: '',
      match_type: 'singles',
      challenger_partner_id: null,
      challenged_partner_id: null
    }
  } catch (err) { 
    const errorMsg = err.response?.data?.detail || 'Gửi yêu cầu thách đấu thất bại.'
    ElMessage.error(errorMsg) 
  }
}

// --- ĐỐI ĐẦU TAB (H2H) ---
const h2hPlayerA = ref(null)
const h2hPlayerB = ref(null)
const h2hWinsA = ref(0)
const h2hWinsB = ref(0)
const h2hLoading = ref(false)

const playerAObject = computed(() => players.value.find(p => p.player_id === h2hPlayerA.value))
const playerBObject = computed(() => players.value.find(p => p.player_id === h2hPlayerB.value))
const h2hPlayersList = computed(() => players.value)

const fetchH2HCompare = async () => {
  if (!h2hPlayerA.value || !h2hPlayerB.value) return
  h2hLoading.value = true
  try {
    const data = await apiClient.get(`/api/players/h2h/compare/${h2hPlayerA.value}/${h2hPlayerB.value}`)
    h2hWinsA.value = data.wins_a || 0
    h2hWinsB.value = data.wins_b || 0
  } catch (err) {
    console.error('Error loading H2H Compare:', err)
    h2hWinsA.value = 0
    h2hWinsB.value = 0
  } finally {
    h2hLoading.value = false
  }
}

const totalH2HWins = computed(() => h2hWinsA.value + h2hWinsB.value)
const percentA = computed(() => {
  if (totalH2HWins.value === 0) return 50
  return Math.round((h2hWinsA.value / totalH2HWins.value) * 100)
})
const percentB = computed(() => {
  if (totalH2HWins.value === 0) return 50
  return Math.round((h2hWinsB.value / totalH2HWins.value) * 100)
})

const h2hDirectMatches = computed(() => {
  if (!h2hPlayerA.value || !h2hPlayerB.value) return []
  const nameA = playerAObject.value?.full_name?.toLowerCase()
  const nameB = playerBObject.value?.full_name?.toLowerCase()
  if (!nameA || !nameB) return []
  
  return finishedMatches.value.filter(m => {
    const p1 = m.p1_name?.toLowerCase()
    const p2 = m.p2_name?.toLowerCase()
    const p1Partner = m.p1_partner_name?.toLowerCase()
    const p2Partner = m.p2_partner_name?.toLowerCase()
    
    const isAPlayer1 = p1 === nameA || p1Partner === nameA
    const isAPlayer2 = p2 === nameA || p2Partner === nameA
    const isBPlayer1 = p1 === nameB || p1Partner === nameB
    const isBPlayer2 = p2 === nameB || p2Partner === nameB
    
    return (isAPlayer1 && isBPlayer2) || (isAPlayer2 && isBPlayer1)
  })
})

watch([h2hPlayerA, h2hPlayerB], () => {
  fetchH2HCompare()
})

// --- VẬN ĐỘNG VIÊN & XẾP HẠNG (Main player list with Search) ---
const visiblePlayers = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) return players.value
  return players.value.filter(p => p.full_name?.toLowerCase().includes(keyword))
})

const totalPlayerPages = computed(() => Math.max(1, Math.ceil(visiblePlayers.value.length / PLAYER_PAGE_SIZE)))

const paginatedPlayers = computed(() => {
  const start = (playerPage.value - 1) * PLAYER_PAGE_SIZE
  return visiblePlayers.value.slice(start, start + PLAYER_PAGE_SIZE)
})

watch(searchQuery, () => {
  playerPage.value = 1
})

watch(totalPlayerPages, (total) => {
  if (playerPage.value > total) playerPage.value = total
})

const loadPlayers = async () => {
  try {
    const rankings = await apiClient.get('/api/players/rankings')
    const normalized = Array.isArray(rankings) ? rankings : []
    
    const nonAdminPlayers = normalized.filter(p => !p.full_name?.toLowerCase().includes('admin'))

    const enriched = await Promise.all(nonAdminPlayers.map(async (p, index) => {
      return {
        ...p,
        displayRank: index + 1,
        avatar_url: p.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(p.full_name)}&background=random`
      }
    }))
    players.value = enriched
    recentWinners.value = players.value.slice(0, 8)
  } catch (err) { 
    console.error('Error loading players:', err) 
  }
}

onMounted(async () => {
  authStore.hydrate()
  await loadPlayers() // Only load players on mount (Lazy Load)
  
  if (myPlayerId.value) {
    h2hPlayerA.value = myPlayerId.value
  }
  loading.value = false
})
</script>

<template>
  <div class="clean-portfolio-app">
    <div class="container main-wrapper" v-loading="loading || tabLoading">
      
      <header class="portfolio-hero">
        <h1 class="hero-title">
          Danh sách <span class="highlight-text">Vận động viên</span>
        </h1>
        <p class="hero-subtitle">
          Hệ thống dữ liệu lưu trữ thông tin, thứ hạng và lịch sử thi đấu của các tay vợt.
        </p>
      </header>

      <!-- Tabs Navigation (Sleek Glassmorphic Style) -->
      <div class="tabs-container">
        <button 
          :class="['tab-btn', { active: activeTab === 'ranking' }]"
          @click="handleTabChange('ranking')"
        >
          Vận động viên & Xếp hạng
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'results' }]"
          @click="handleTabChange('results')"
        >
          Kết quả gần đây
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'h2h' }]"
          @click="handleTabChange('h2h')"
        >
          Phân tích Đối đầu
        </button>
      </div>

      <!-- Search Section (Only displayed on main list tab) -->
      <div class="search-section" v-if="activeTab === 'ranking'">
        <div class="clean-search-bar">
          <el-icon class="search-icon"><Search /></el-icon>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Tìm kiếm tay vợt theo tên..."
            class="search-input"
          />
        </div>
      </div>

      <!-- Featured Players (Only displayed on main list tab) -->
      <section class="featured-section" v-if="recentWinners.length && activeTab === 'ranking'">
        <div class="section-heading">
          <el-icon><Medal /></el-icon>
          <h2>TAY VỢT NỔI BẬT</h2>
        </div>
        <div class="featured-scroll">
          <RouterLink
            v-for="(p, i) in recentWinners"
            :key="'featured-'+(p.player_id || p.id)"
            :to="`/players/${p.player_id || p.id}`"
            class="featured-card"
          >
            <div class="featured-avatar">
              <img :src="p.avatar_url" alt="" referrerpolicy="no-referrer" />
              <div class="rank-ring"><span>#{{ i + 1 }}</span></div>
            </div>
            <h4 class="featured-name">{{ p.full_name }}</h4>
            <p class="featured-pts">{{ p.elo_points }} Điểm</p>
          </RouterLink>
        </div>
      </section>

      <!-- Content Area -->
      <div class="content-layout">
        <main class="grid-column">
          
          <!-- TAB 1: VẬN ĐỘNG VIÊN & XẾP HẠNG -->
          <div v-if="activeTab === 'ranking'" class="tab-content">
            <div class="talent-grid">
              <div v-for="p in paginatedPlayers" :key="p.player_id || p.id" class="talent-card group">
                <RouterLink :to="`/players/${p.player_id || p.id}`" class="talent-image-box">
                  <img :src="p.avatar_url" alt="" class="talent-img" referrerpolicy="no-referrer" />
                </RouterLink>
                
                <div class="talent-info">
                  <div class="talent-header">
                    <h3 class="talent-name">
                      <RouterLink :to="`/players/${p.player_id || p.id}`" class="talent-link-name">
                        {{ p.full_name }}
                      </RouterLink>
                    </h3>
                    <span class="talent-badge">Hạng #{{ p.displayRank || '--' }}</span>
                  </div>
                  
                  <div class="talent-metrics">
                    <div class="metric">
                      <span class="m-label">ELO</span>
                      <span class="m-value highlighted-val">{{ p.elo_points }}</span>
                    </div>
                    <div class="metric-divider"></div>
                    <div class="metric">
                      <span class="m-label">Tỷ lệ thắng</span>
                      <span class="m-value">{{ p.win_rate || 0 }}%</span>
                    </div>
                    <div class="metric-divider"></div>
                    <div class="metric">
                      <span class="m-label">Số trận</span>
                      <span class="m-value">{{ (p.wins || 0) + (p.losses || 0) }}</span>
                    </div>
                  </div>

                  <div class="action-buttons-card">
                    <RouterLink :to="`/players/${p.player_id || p.id}`" class="flex-btn-link">
                      <button class="view-profile-btn-split">
                        Hồ sơ <el-icon><Right /></el-icon>
                      </button>
                    </RouterLink>
                    <button 
                      v-if="p.full_name !== authStore.user?.full_name" 
                      class="challenge-now-btn" 
                      @click="openChallenge(p)"
                    >
                      Thách đấu <el-icon><Aim /></el-icon>
                    </button>
                  </div>
                </div>
              </div>

              <div v-if="!visiblePlayers.length" class="empty-state-card">
                <p>Không tìm thấy vận động viên phù hợp với từ khóa tìm kiếm.</p>
              </div>
            </div>
          </div>

          <!-- TAB 2: KẾT QUẢ GẦN ĐÂY -->
            <div v-if="activeTab === 'ranking' && visiblePlayers.length > PLAYER_PAGE_SIZE" class="list-pagination">
              <el-pagination
                v-model:current-page="playerPage"
                :page-size="PLAYER_PAGE_SIZE"
                :total="visiblePlayers.length"
                layout="prev, pager, next"
                background
              />
            </div>
          <div v-if="activeTab === 'results'" class="tab-content results-tab-content">
            <div class="results-list">
              <div v-for="match in finishedMatches" :key="match.id" class="result-match-card">
                <div class="match-card-header">
                  <span class="tour-badge">{{ match.tournamentName }}</span>
                  <span class="match-round">{{ match.round }}</span>
                  <span class="match-date">{{ match.date }}</span>
                </div>
                
                <div class="match-card-body">
                  <!-- Side A -->
                  <div class="side-item" :class="{ winner: match.winner_side === 'side_a' }">
                    <div class="players-stack">
                      <div class="player-unit">
                        <img :src="match.p1_avatar" class="ava-small" referrerpolicy="no-referrer" />
                        <span class="name">{{ match.p1_name }}</span>
                      </div>
                      <div class="player-unit" v-if="match.p1_partner_name">
                        <img :src="match.p1_partner_avatar || 'https://ui-avatars.com/api/?name=Partner'" class="ava-small" referrerpolicy="no-referrer" />
                        <span class="name">{{ match.p1_partner_name }}</span>
                      </div>
                    </div>
                    <div class="winner-indicator" v-if="match.winner_side === 'side_a'">
                      <el-icon><Check /></el-icon> Thắng
                    </div>
                  </div>

                  <div class="vs-divider-text">VS</div>

                  <!-- Side B -->
                  <div class="side-item" :class="{ winner: match.winner_side === 'side_b' }">
                    <div class="players-stack">
                      <div class="player-unit">
                        <img :src="match.p2_avatar" class="ava-small" referrerpolicy="no-referrer" />
                        <span class="name">{{ match.p2_name }}</span>
                      </div>
                      <div class="player-unit" v-if="match.p2_partner_name">
                        <img :src="match.p2_partner_avatar || 'https://ui-avatars.com/api/?name=Partner'" class="ava-small" referrerpolicy="no-referrer" />
                        <span class="name">{{ match.p2_partner_name }}</span>
                      </div>
                    </div>
                    <div class="winner-indicator" v-if="match.winner_side === 'side_b'">
                      <el-icon><Check /></el-icon> Thắng
                    </div>
                  </div>
                </div>

                <div class="match-card-score">
                  <div class="score-label">Tỷ số</div>
                  <div class="score-values">{{ match.score }}</div>
                </div>
              </div>

              <div v-if="!finishedMatches.length" class="empty-state-card">
                <p>Không tìm thấy lịch sử trận đấu nào đã hoàn thành.</p>
              </div>
            </div>
          </div>

          <!-- TAB 3: ĐỐI ĐẦU (H2H) -->
          <div v-if="activeTab === 'h2h'" class="tab-content h2h-tab-content">
            <div class="h2h-selectors">
              <div class="selector-box">
                <label>Tay vợt A</label>
                <el-select v-model="h2hPlayerA" placeholder="Chọn tay vợt A" filterable style="width: 100%">
                  <el-option 
                    v-for="p in h2hPlayersList" 
                    :key="p.player_id" 
                    :label="p.full_name" 
                    :value="p.player_id"
                  />
                </el-select>
              </div>
              
              <div class="h2h-vs-sign">VS</div>

              <div class="selector-box">
                <label>Tay vợt B</label>
                <el-select v-model="h2hPlayerB" placeholder="Chọn tay vợt B" filterable style="width: 100%">
                  <el-option 
                    v-for="p in h2hPlayersList" 
                    :key="p.player_id" 
                    :label="p.full_name" 
                    :value="p.player_id"
                  />
                </el-select>
              </div>
            </div>

            <!-- H2H Comparison results -->
            <div class="h2h-comparison-results" v-if="playerAObject && playerBObject" v-loading="h2hLoading">
              <div class="h2h-cards-comparison">
                <!-- Card Player A -->
                <div class="h2h-player-card card-a">
                  <img :src="playerAObject.avatar_url" class="h2h-card-avatar" referrerpolicy="no-referrer" />
                  <h3>{{ playerAObject.full_name }}</h3>
                  <div class="h2h-card-details">
                    <div class="detail-row"><span class="lbl">Hạng SGT:</span><strong>#{{ playerAObject.displayRank }}</strong></div>
                    <div class="detail-row"><span class="lbl">ELO hiện tại:</span><strong class="elo-a">{{ playerAObject.elo_points }}</strong></div>
                    <div class="detail-row"><span class="lbl">Tỷ lệ thắng:</span><strong>{{ playerAObject.win_rate }}%</strong></div>
                  </div>
                </div>

                <!-- H2H Statistics and ratio bar -->
                <div class="h2h-score-center">
                  <div class="score-text">LỊCH SỬ ĐỐI ĐẦU</div>
                  <div class="score-numbers">
                    <span class="score-a">{{ h2hWinsA }}</span>
                    <span class="score-dash">:</span>
                    <span class="score-b">{{ h2hWinsB }}</span>
                  </div>
                  
                  <!-- Match win ratio bar -->
                  <div class="h2h-ratio-track">
                    <div class="h2h-ratio-fill-a" :style="{ width: percentA + '%' }"></div>
                    <div class="h2h-ratio-fill-b" :style="{ width: percentB + '%' }"></div>
                  </div>

                  <div class="elo-diff-indicator">
                    Chênh lệch ELO: {{ Math.abs(playerAObject.elo_points - playerBObject.elo_points) }}
                  </div>
                </div>

                <!-- Card Player B -->
                <div class="h2h-player-card card-b">
                  <img :src="playerBObject.avatar_url" class="h2h-card-avatar" referrerpolicy="no-referrer" />
                  <h3>{{ playerBObject.full_name }}</h3>
                  <div class="h2h-card-details">
                    <div class="detail-row"><span class="lbl">Hạng SGT:</span><strong>#{{ playerBObject.displayRank }}</strong></div>
                    <div class="detail-row"><span class="lbl">ELO hiện tại:</span><strong class="elo-b">{{ playerBObject.elo_points }}</strong></div>
                    <div class="detail-row"><span class="lbl">Tỷ lệ thắng:</span><strong>{{ playerBObject.win_rate }}%</strong></div>
                  </div>
                </div>
              </div>

              <!-- Direct Matches History List -->
              <div class="h2h-direct-history">
                <h3>Các trận chạm trán trực tiếp</h3>
                <div class="direct-matches-list" v-if="h2hDirectMatches.length">
                  <div v-for="match in h2hDirectMatches" :key="match.id" class="direct-match-item">
                    <div class="dm-header">
                      <span>{{ match.tournamentName }} - {{ match.round }}</span>
                      <span class="dm-date">{{ match.date }}</span>
                    </div>
                    <div class="dm-body">
                      <span class="team-a" :class="{ winner: match.winner_side === 'side_a' }">{{ match.p1_name }}</span>
                      <span class="dm-score">{{ match.score }}</span>
                      <span class="team-b" :class="{ winner: match.winner_side === 'side_b' }">{{ match.p2_name }}</span>
                    </div>
                  </div>
                </div>
                <div v-else class="empty-h2h-history">
                  <el-empty description="Hai tuyển thủ chưa từng gặp nhau trong các trận đấu chính thức hoặc giao hữu." :image-size="60" />
                </div>
              </div>
            </div>

            <div v-else class="h2h-placeholder">
              <el-icon class="placeholder-icon"><User /></el-icon>
              <p>Chọn 2 vận động viên phía trên để tiến hành phân tích lịch sử đối đầu chi tiết.</p>
            </div>
          </div>

        </main>
      </div>

    </div>

    <!-- Element Plus Dialog for Challenges -->
    <el-dialog v-model="showChallengeDialog" :show-close="false" width="90%" style="max-width: 450px" class="atp-modal">
      <template #header>
        <div class="modal-custom-header">
          <h3>Đề xuất kèo thách đấu</h3>
          <button class="close-btn" @click="showChallengeDialog = false"><el-icon><Close /></el-icon></button>
        </div>
      </template>

      <div class="modal-body">
        <div class="challenge-target">
          <img :src="selectedOpponent?.avatar_url" alt="" class="target-avatar" referrerpolicy="no-referrer" />
          <div class="target-info">
            <span>Đối thủ thách đấu</span>
            <strong>{{ selectedOpponent?.full_name }}</strong>
          </div>
        </div>

        <el-form label-position="top" class="atp-form">
          <el-form-item label="Thể thức trận đấu">
            <el-radio-group v-model="challengeForm.match_type" size="default" style="width: 100%; display: flex; margin-bottom: 10px;">
              <el-radio-button value="singles" style="flex: 1; text-align: center;">Đấu đơn (1vs1)</el-radio-button>
              <el-radio-button value="doubles" style="flex: 1; text-align: center;">Đấu đôi (2vs2)</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <div v-if="challengeForm.match_type === 'doubles'" class="doubles-select-section">
            <el-form-item label="Đồng đội của bạn" required style="margin-bottom: 10px;">
              <el-select 
                v-model="challengeForm.challenger_partner_id" 
                placeholder="Chọn đồng đội ghép cặp" 
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="p in myPartnerOptions"
                  :key="p.player_id"
                  :label="p.full_name + ' (ELO: ' + (p.elo_points || 1000) + ')'"
                  :value="p.player_id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="Đồng đội của đối thủ" required style="margin-bottom: 0;">
              <el-select 
                v-model="challengeForm.challenged_partner_id" 
                placeholder="Chọn đồng đội đối thủ" 
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="p in opponentPartnerOptions"
                  :key="p.player_id"
                  :label="p.full_name + ' (ELO: ' + (p.elo_points || 1000) + ')'"
                  :value="p.player_id"
                />
              </el-select>
            </el-form-item>
          </div>

          <el-form-item label="Ngày đề xuất thi đấu">
            <el-date-picker 
              v-model="challengeForm.date" 
              type="date" 
              placeholder="Chọn ngày thi đấu"
              value-format="YYYY-MM-DD" 
              style="width: 100%" 
            />
          </el-form-item>
          <el-form-item label="Tin nhắn kèm theo">
            <el-input 
              v-model="challengeForm.notes" 
              type="textarea" 
              :rows="3"
              placeholder="Nhập ghi chú (sân đấu đề xuất, khung giờ, v.v.)..." 
            />
          </el-form-item>
        </el-form>

        <div class="atp-notice-box">
          <el-icon class="notice-icon"><InfoFilled /></el-icon>
          <p>Kèo thách đấu giao hữu sẽ tự động cập nhật ELO của các tay vợt sau khi kết thúc trận đấu và kết quả được hai bên xác nhận trên hệ thống.</p>
        </div>
      </div>

      <template #footer>
        <div class="modal-footer-flex">
          <button class="btn-cancel" @click="showChallengeDialog = false">Hủy bỏ</button>
          <button class="btn-atp-solid" @click="sendChallengeRequest">Gửi lời thách đấu</button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* =========================================================
   CLEAN AGENCY THEME VARIABLES (BLUE-GREY & WHITE)
 ========================================================= */
.clean-portfolio-app {
  --bg-base: #f8fafc;       /* Light, clean slate grey */
  --card-bg: #ffffff;       
  --border-light: #e2e8f0;  
  --border-hover: #cbd5e1;  
  
  --text-main: #0f172a;     
  --text-body: #334155;     
  --text-muted: #64748b;    
  
  --accent-primary: #1e293b; 
  --accent-light: #f1f5f9;   
  
  --shadow-sm: 0 2px 4px rgba(15, 23, 42, 0.02);
  --shadow-md: 0 8px 30px rgba(15, 23, 42, 0.04);
  --shadow-hover: 0 16px 40px rgba(15, 23, 42, 0.08);

  background-color: var(--bg-base);
  color: var(--text-body);
  min-height: 100vh;
  font-family: 'Inter', -apple-system, sans-serif;
  padding-bottom: 5rem;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

/* =========================================================
   HERO HEADER
 ========================================================= */
.portfolio-hero {
  padding: 5rem 0 3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.hero-title {
  font-size: clamp(2.5rem, 6vw, 3.5rem);
  font-weight: 850;
  line-height: 1.1;
  letter-spacing: -0.03em;
  margin: 0 0 0.8rem;
  color: var(--text-main);
}

.highlight-text {
  background: linear-gradient(135deg, #0066cc, #00b0f0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-subtitle {
  color: var(--text-muted);
  font-size: 1.15rem;
  max-width: 600px;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

/* =========================================================
   TABS NAVIGATION
 ========================================================= */
.tabs-container {
  display: flex;
  justify-content: center;
  background: rgba(15, 23, 42, 0.03);
  padding: 6px;
  border-radius: 99px;
  max-width: 580px;
  margin: 0 auto 3rem;
  border: 1px solid var(--border-light);
}

.tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-muted);
  cursor: pointer;
  padding: 10px 20px;
  border-radius: 99px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
  white-space: nowrap;
}

.tab-btn:hover {
  color: var(--text-main);
}

.tab-btn.active {
  color: #fff;
  background: var(--text-main);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
}

/* Search bar */
.search-section {
  display: flex;
  justify-content: center;
  margin-bottom: 3rem;
}

.clean-search-bar {
  display: flex;
  align-items: center;
  background: var(--card-bg);
  border: 1px solid var(--border-light);
  border-radius: 99px;
  padding: 0.85rem 1.75rem;
  width: 100%;
  max-width: 550px;
  box-shadow: var(--shadow-md);
  transition: all 0.3s ease;
}

.clean-search-bar:focus-within {
  border-color: #0066cc;
  box-shadow: 0 0 0 4px rgba(0, 102, 204, 0.1);
}

.search-icon {
  font-size: 1.3rem;
  color: var(--text-muted);
  margin-right: 0.8rem;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-main);
  font-size: 1rem;
  outline: none;
  font-weight: 500;
}
.search-input::placeholder { color: #94a3b8; }

/* =========================================================
   FEATURED PLAYERS (Stories)
 ========================================================= */
.featured-section {
  margin-bottom: 3.5rem;
}

.section-heading {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1.5rem;
  color: var(--text-main);
}
.section-heading h2 {
  font-size: 0.85rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 0;
}

.featured-scroll {
  display: flex;
  gap: 1.5rem;
  overflow-x: auto;
  padding-bottom: 1rem;
  scrollbar-width: none;
}
.featured-scroll::-webkit-scrollbar { display: none; }

.featured-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 105px;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.featured-card:hover { transform: translateY(-6px); }

.featured-avatar {
  position: relative;
  width: 94px; height: 94px;
  border-radius: 28px;
  background: var(--card-bg);
  padding: 4px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  margin-bottom: 0.8rem;
}

.featured-avatar img {
  width: 100%; height: 100%;
  object-fit: cover;
  border-radius: 24px;
}

.rank-ring {
  position: absolute;
  top: -6px; right: -6px;
  background: var(--bg-base);
  border: 1px solid var(--border-light);
  padding: 3px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.rank-ring span {
  background: #0f172a;
  color: white; font-size: 0.7rem; font-weight: 800;
  width: 26px; height: 26px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}

.featured-name { font-size: 0.9rem; font-weight: 700; margin: 0 0 4px; color: var(--text-main); text-align: center;}
.featured-pts { font-size: 0.75rem; color: var(--text-muted); margin: 0; font-weight: 600;}

/* =========================================================
   BỐ CỤC CHÍNH
 ========================================================= */
.content-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2.5rem;
}

/* =========================================================
   TALENT GRID (DANH SÁCH VĐV)
 ========================================================= */
.talent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.75rem;
}

.list-pagination {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
}

.list-pagination :deep(.el-pagination.is-background .el-pager li.is-active) {
  background: var(--text-main);
}

.talent-card {
  background: var(--card-bg);
  border: 1px solid var(--border-light);
  border-radius: 20px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.talent-card:hover {
  border-color: var(--border-hover);
  transform: translateY(-5px);
  box-shadow: var(--shadow-hover);
}

.talent-image-box {
  display: block;
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 14px;
  overflow: hidden;
  background: var(--bg-base);
}

.talent-img {
  width: 100%; height: 100%;
  object-fit: cover;
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.talent-card:hover .talent-img {
  transform: scale(1.04);
}

.talent-info {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.talent-header {
  display: flex; justify-content: space-between; align-items: flex-start;
}

.talent-name {
  font-size: 1.2rem; font-weight: 800; margin: 0; color: var(--text-main);
  line-height: 1.3;
}

.talent-link-name {
  color: inherit;
  text-decoration: none;
  transition: color 0.2s ease;
}

.talent-link-name:hover {
  color: #0066cc;
}

.talent-badge {
  background: var(--accent-light);
  color: var(--text-main);
  border: 1px solid var(--border-light);
  font-size: 0.72rem; font-weight: 700;
  padding: 4px 10px; border-radius: 8px;
  letter-spacing: 0.05em;
}

.talent-metrics {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--accent-light);
  border: 1px solid var(--border-light);
  padding: 0.9rem 1.25rem;
  border-radius: 12px;
}

.metric { display: flex; flex-direction: column; gap: 4px; }
.m-label { font-size: 0.65rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;}
.m-value { font-size: 1.05rem; color: var(--text-main); font-weight: 800;}
.highlighted-val { color: #0066cc; }
.metric-divider { width: 1px; height: 26px; background: var(--border-light); }

/* Nút phân chia */
.action-buttons-card {
  display: flex;
  gap: 10px;
}

.flex-btn-link {
  flex: 1;
  text-decoration: none;
}

.view-profile-btn-split {
  width: 100%;
  padding: 0.75rem;
  background: transparent;
  color: var(--text-body);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
}

.view-profile-btn-split:hover {
  background: var(--accent-light);
  border-color: var(--border-hover);
}

.challenge-now-btn {
  flex: 1.3;
  padding: 0.75rem;
  background: #0066cc;
  color: #fff;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
}

.challenge-now-btn:hover {
  background: #004d99;
}

/* =========================================================
   RESULTS TAB (KẾT QUẢ GẦN ĐÂY)
 ========================================================= */
.results-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 1.5rem;
  width: 100%;
}

.players-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.player-unit {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ava-small {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--border-light);
  background: var(--bg-base);
}

.result-match-card {
  background: var(--card-bg);
  border: 1px solid var(--border-light);
  border-radius: 20px;
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.match-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 10px;
  font-weight: 600;
}

.tour-badge {
  color: #0066cc;
  background: #eff6ff;
  padding: 2px 10px;
  border-radius: 6px;
}

.match-round {
  text-transform: uppercase;
  font-weight: 700;
}

.match-card-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.side-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--accent-light);
  border: 1px solid transparent;
}

.side-item.winner {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.side-item.winner .name {
  color: #16a34a;
  font-weight: 700;
}

.winner-indicator {
  font-size: 0.75rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #16a34a;
  background: #dcfce7;
  padding: 2px 8px;
  border-radius: 6px;
}

.match-card-score {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8fafc;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid var(--border-light);
}

.score-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.score-values {
  font-size: 1.15rem;
  font-weight: 850;
  color: var(--text-main);
  letter-spacing: 0.05em;
}

/* =========================================================
   H2H TAB (ĐỐI ĐẦU)
 ========================================================= */
.h2h-tab-content {
  background: var(--card-bg);
  border: 1px solid var(--border-light);
  border-radius: 24px;
  padding: 3rem;
  box-shadow: var(--shadow-sm);
  width: 100%;
  box-sizing: border-box;
}

.h2h-cards-comparison {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
  margin-bottom: 3rem;
  width: 100%;
}

.h2h-selectors {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 2rem;
  margin-bottom: 3.5rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border-light);
}

.selector-box label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

:deep(.selector-box .el-select .el-input__wrapper) {
  border-radius: 12px;
  padding: 8px 16px;
  box-shadow: 0 0 0 1px var(--border-light) inset;
}

:deep(.selector-box .el-select .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #0066cc inset !important;
}

.h2h-vs-sign {
  font-size: 1.8rem;
  font-weight: 900;
  font-style: italic;
  color: var(--border-hover);
  padding-bottom: 6px;
}

.h2h-player-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  border: 1px solid var(--border-light);
  border-radius: 16px;
  background: var(--accent-light);
  box-shadow: var(--shadow-sm);
  max-width: 320px;
  width: 100%;
  box-sizing: border-box;
}

.h2h-player-card.card-a {
  border-left: 4px solid #0066cc;
}

.h2h-player-card.card-b {
  border-left: 4px solid #e11d48;
}

.h2h-card-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #fff;
  box-shadow: var(--shadow-md);
  margin-bottom: 1.25rem;
}

.h2h-player-card h3 {
  margin: 0 0 1.25rem;
  font-size: 1.25rem;
  font-weight: 850;
  color: var(--text-main);
  text-align: center;
}

.elo-a {
  color: #0066cc;
}
.elo-b {
  color: #e11d48;
}

/* Versus Center Area */
.h2h-score-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  flex: 1;
  max-width: 300px;
}

.score-numbers {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 3.5rem;
  font-weight: 900;
  color: var(--text-main);
  line-height: 1;
}

/* Win ratio progress track */
.h2h-ratio-track {
  width: 100%;
  height: 10px;
  background: var(--border-light);
  border-radius: 99px;
  overflow: hidden;
  display: flex;
}

.h2h-ratio-fill-a {
  background: #0066cc;
  height: 100%;
  transition: width 0.5s ease;
}

.h2h-ratio-fill-b {
  background: #e11d48;
  height: 100%;
  transition: width 0.5s ease;
}

.h2h-direct-history h3 {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text-main);
  border-bottom: 2px solid var(--border-light);
  padding-bottom: 10px;
  margin: 0 0 1.5rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.direct-match-item {
  background: var(--accent-light);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 12px 18px;
  margin-bottom: 12px;
  transition: border-color 0.2s;
}
.direct-match-item:hover {
  border-color: var(--border-hover);
}

.dm-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  width: 100%;
}

.team-a {
  flex: 1;
  text-align: right;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-body);
}

.team-b {
  flex: 1;
  text-align: left;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-body);
}

.team-a.winner, .team-b.winner {
  font-weight: 800;
  color: #16a34a;
}

.dm-score {
  font-weight: 850;
  color: var(--text-main);
  background: #fff;
  border: 1px solid var(--border-light);
  padding: 4px 14px;
  border-radius: 8px;
  min-width: 75px;
  text-align: center;
}

.h2h-placeholder {
  text-align: center;
  padding: 5rem 1.5rem;
  color: var(--text-muted);
}

.placeholder-icon {
  font-size: 3.5rem;
  margin-bottom: 1rem;
  color: var(--border-hover);
}

/* =========================================================
   ELEMENT PLUS DIALOG (MODALS)
 ========================================================= */
.doubles-select-section {
  background: #f8fafc; 
  padding: 16px; 
  border-radius: 12px; 
  border: 1px dashed #cbd5e1; 
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

:deep(.atp-modal .el-dialog) { 
  border-radius: 20px; 
}

/* =========================================================
   RESPONSIVE
 ========================================================= */
@media (max-width: 768px) {
  .portfolio-hero { padding: 3.5rem 0; }
  .tabs-container {
    flex-wrap: wrap;
    gap: 0.4rem;
    border-radius: 16px;
    padding: 4px;
  }
  .tab-btn {
    font-size: 0.85rem;
    padding: 8px 12px;
  }
  .h2h-cards-comparison {
    flex-direction: column;
    gap: 2rem;
  }
}
</style>
