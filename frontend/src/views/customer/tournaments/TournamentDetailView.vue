<script setup>
import { onMounted, computed, ref, watch } from 'vue'
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
  Ticket,
  VideoCamera,
  Picture,
  VideoPlay,
  View
} from '@element-plus/icons-vue'
import { currentLocale, t } from '../../../utils/locale'

const route = useRoute()
const router = useRouter()
const tournamentStore = useTournamentStore()
const authStore = useAuthStore()

const tournamentId = computed(() => route.params.id)
const tournament = computed(() => tournamentStore.currentTournament)

const activeTab = ref('info')
const publicMatches = ref([])
const loadingBracket = ref(false)
const standingsData = ref([])
const loadingStandings = ref(false)
const isAlreadyRegistered = ref(false)
const myRegistration = ref(null)
const registrations = ref([])
const loadingRegistrations = ref(false)
const selectedCategoryId = ref(null)

watch(tournamentId, async (newId) => {
  if (newId) {
    // Reset state
    activeTab.value = 'info'
    publicMatches.value = []
    standingsData.value = []
    registrations.value = []
    selectedCategoryId.value = null
    isAlreadyRegistered.value = false
    
    await tournamentStore.fetchTournamentById(newId)
    
    // Re-check registration
    if (authStore.isAuthenticated) {
      checkRegistration()
    }
  }
}, { immediate: true })

const checkRegistration = async () => {
  try {
    const myRegs = await apiClient.get('/api/registrations/my-registrations')
    const exists = myRegs.find(r => r.tournament_id === parseInt(tournamentId.value) && r.status !== 'cancelled' && r.status !== 'rejected')
    if (exists) {
      isAlreadyRegistered.value = true
      myRegistration.value = exists
      // AUTO-SELECT THE REGISTERED CATEGORY BY DEFAULT
      if (!selectedCategoryId.value) {
        selectedCategoryId.value = exists.category_id
      }
    }
  } catch (err) {
    console.error("Lỗi kiểm tra đăng ký:", err)
  }
}

const fetchRegistrations = async () => {
  loadingRegistrations.value = true
  try {
    const url = `/api/tournaments/${tournamentId.value}/registrations` + 
                (selectedCategoryId.value ? `?category_id=${selectedCategoryId.value}` : '')
    const data = await apiClient.get(url)
    registrations.value = data
  } catch (err) {
    console.error("Lỗi tải danh sách VĐV:", err)
  } finally {
    loadingRegistrations.value = false
  }
}


const fetchStandings = async () => {
  loadingStandings.value = true
  try {
    const url = `/api/tournaments/${tournamentId.value}/standings` + 
                (selectedCategoryId.value ? `?category_id=${selectedCategoryId.value}` : '')
    const data = await apiClient.get(url)
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

const fetchBracket = async () => {
  loadingBracket.value = true
  try {
    const url = `/api/tournaments/${tournamentId.value}/matches` + 
                (selectedCategoryId.value ? `?category_id=${selectedCategoryId.value}` : '')
    const data = await apiClient.get(url)
    publicMatches.value = data
  } catch (err) {
    console.error("Không tải được sơ đồ nhánh đấu:", err)
  } finally {
    loadingBracket.value = false
  }
}

// Watch category change to re-fetch data
watch(selectedCategoryId, (newVal) => {
  if (newVal) {
    fetchBracket()
    fetchStandings()
    fetchRegistrations()
  }
}, { immediate: true })

// Initialize first category if available from tournament data
watch(() => tournament.value?.categories, (cats) => {
  if (cats && cats.length > 0 && !selectedCategoryId.value) {
    selectedCategoryId.value = cats[0].id
  }
}, { immediate: true })

// RE-FETCH DATA ON TAB SWITCH (Fix blank list bug)
watch(activeTab, (newTab) => {
  if (!selectedCategoryId.value) return
  
  if (newTab === 'bracket' && publicMatches.value.length === 0) {
    fetchBracket()
  } else if (newTab === 'standings' && standingsData.value.length === 0) {
    fetchStandings()
  } else if (newTab === 'participants' && registrations.value.length === 0) {
    fetchRegistrations()
  }
})

const groupedMatches = computed(() => {
  const groups = {}
  publicMatches.value.forEach(m => {
    if (!groups[m.round_code]) groups[m.round_code] = []
    groups[m.round_code].push(m)
  })
  const order = ['G1', 'G2', 'G3', 'R128', 'R64', 'R32', 'R16', 'QF', 'SF', 'F', 'FINAL']
  return Object.keys(groups)
    .sort((a, b) => {
      const idxA = order.indexOf(a)
      const idxB = order.indexOf(b)
      if (idxA === -1 && idxB === -1) return a.localeCompare(b)
      if (idxA === -1) return 1
      if (idxB === -1) return -1
      return idxA - idxB
    })
    .map(key => ({
      label: key,
      items: [...groups[key]].sort((a, b) => (a.match_no || 0) - (b.match_no || 0))
    }))
})

const goToRegister = () => {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  router.push({ name: 'tournament-register', params: { id: tournamentId.value } })
}

const formatDate = (val) => {
  if (!val) return t('tournaments.notUpdated')
  const d = new Date(val)
  if (!isNaN(d.getTime())) {
    return d.toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    })
  }
  // Thử parse thủ công nếu là định dạng dd/mm/yyyy
  if (typeof val === 'string' && val.includes('/')) {
    const p = val.split(/[\/\s:]/)
    if (p.length >= 3) {
      const d2 = new Date(p[2], p[1]-1, p[0])
      if (!isNaN(d2.getTime())) {
        return d2.toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', {
          day: 'numeric',
          month: 'long',
          year: 'numeric'
        })
      }
    }
  }
  return t('tournaments.notUpdated')
}

const formatDateTime = (val) => {
  if (!val) return '---'
  const d = new Date(val)
  if (isNaN(d.getTime())) return formatDate(val)
  return d.toLocaleString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const selectedCategory = computed(() => {
  if (!selectedCategoryId.value || !tournament.value?.categories) return null
  return tournament.value.categories.find(c => c.id === selectedCategoryId.value)
})

const selectedCategoryName = computed(() => {
  if (selectedCategory.value) return selectedCategory.value.name
  if (tournament.value?.categories?.length > 0) return tournament.value.categories[0].name
  return tournament.value?.category_type || '---'
})

const allMedia = computed(() => {
  const media = []
  publicMatches.value.forEach(m => {
    if (m.video_url || m.image_url) {
      media.push({
        id: m.id,
        match_label: `Trận #${m.match_no}`,
        round_code: m.round_code,
        p1_name: m.p1_name,
        p2_name: m.p2_name,
        video_url: m.video_url,
        image_url: m.image_url
      })
    }
  })
  return media
})

const previewVisible = ref(false)
const previewData = ref({ type: 'image', url: '', title: '' })

const openPreview = (type, url, title) => {
  previewData.value = { type, url, title }
  previewVisible.value = true
}
</script>

<template>
  <div class="tournament-detail-root">
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
            <span class="tour-type">{{ selectedCategoryName }}</span>
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
                  <div v-if="isAlreadyRegistered" class="bento-box box-sm registered-highlight">
                    <el-icon class="bento-icon"><Check /></el-icon>
                    <span class="bento-lbl">Nội dung bạn tham gia</span>
                    <strong class="bento-val">{{ myRegistration?.category_name || 'Đã đăng ký' }}</strong>
                  </div>
                  <div class="bento-box box-sm" :class="{ 'viewing-highlight': !isAlreadyRegistered }">
                    <el-icon class="bento-icon"><User /></el-icon>
                    <span class="bento-lbl">Đang xem nội dung</span>
                    <strong class="bento-val">{{ selectedCategoryName }}</strong>
                  </div>
                  <div class="bento-box box-sm">
                    <el-icon class="bento-icon"><Trophy /></el-icon>
                    <span class="bento-lbl">Điểm giới hạn</span>
                    <strong class="bento-val">{{ selectedCategory?.max_points || 'Open' }} Pts</strong>
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
                    <div class="tournament-description" v-if="tournament.description" v-html="tournament.description"></div>
                    <p v-else>
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
                <div v-if="tournament.categories?.length > 1" class="category-filter-wrap">
                  <div class="filter-label">Chọn nội dung:</div>
                  <el-radio-group v-model="selectedCategoryId" size="small">
                    <el-radio-button v-for="cat in tournament.categories" :key="cat.id" :value="cat.id">
                      {{ cat.name }}
                    </el-radio-button>
                  </el-radio-group>
                </div>

                <div v-if="publicMatches.length > 0" class="bracket-scroll-hint">
                  <el-icon><InfoFilled /></el-icon>
                  <span>Vuốt ngang để xem các vòng đấu khác ↔</span>
                </div>

                <div v-loading="loadingBracket" class="bracket-viewport">
                  <div v-if="publicMatches.length === 0" class="empty-state">
                    <div class="es-icon">🎾</div>
                    <p>{{ t('tournaments.bracketNotDrawn') }}</p>
                  </div>
                  
                  <div v-else class="neo-bracket-horizontal">
                    <div v-for="(round, roundIdx) in groupedMatches" :key="round.label" class="bracket-column">
                      <div class="round-sticky-header">
                        <div class="round-title-group">
                          <span class="round-index">{{ roundIdx + 1 }}</span>
                          <h4 class="round-title">{{ round.label }}</h4>
                        </div>
                        <span class="round-count">{{ round.items.length }} {{ t('tournaments.matches') }}</span>
                      </div>
                      
                      <div class="matches-stack">
                        <div v-for="m in round.items" :key="m.id" class="match-node-wrapper">
                          <div class="connector-line-in" v-if="roundIdx > 0"></div>
                          
                          <div class="match-node-v2">
                            <div class="m-v2-header">
                              <div class="m-v2-header-left">
                                <span class="m-v2-no">#{{ m.match_no }}</span>
                                <span class="m-v2-court" v-if="m.court">
                                  <el-icon><Location /></el-icon> {{ m.court }}
                                </span>
                              </div>
                              <span v-if="m.status === 'completed'" class="m-v2-status is-done">{{ t('tournaments.completed') || 'Đã xong' }}</span>
                              <span v-else-if="m.status === 'ongoing'" class="m-v2-status is-live">{{ t('tournaments.live') }}</span>
                              <span v-else class="m-v2-status">{{ t('tournaments.upcoming') }}</span>
                            </div>
                            
                            <div class="m-v2-body">
                              <div class="m-v2-player" :class="{ 'is-win': m.winner_side === 'side_a' }">
                                <div class="player-stack-v2">
                                  <div class="p-mini-box">
                                    <el-avatar :size="20" :src="m.p1_avatar" class="p-avatar-mini">
                                      <el-icon><User /></el-icon>
                                    </el-avatar>
                                    <router-link :to="m.p1_user_id ? `/players/${m.p1_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p1_user_id}">
                                      {{ m.p1_name || '???' }}
                                    </router-link>
                                    <el-icon v-if="m.winner_side === 'side_a'" class="p-win-icon"><Check /></el-icon>
                                  </div>
                                  <div v-if="m.p1_partner_name" class="p-mini-box">
                                    <el-avatar :size="20" :src="m.p1_partner_avatar" class="p-avatar-mini">
                                      <el-icon><User /></el-icon>
                                    </el-avatar>
                                    <router-link :to="m.p1_partner_user_id ? `/players/${m.p1_partner_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p1_partner_user_id}">
                                      {{ m.p1_partner_name }}
                                    </router-link>
                                  </div>
                                </div>
                                <span class="p-score" v-if="m.score_a !== null && m.status === 'completed'">{{ m.score_a }}</span>
                              </div>
                              
                              <div class="m-v2-divider"></div>
                              
                              <div class="m-v2-player" :class="{ 'is-win': m.winner_side === 'side_b' }">
                                <div class="player-stack-v2">
                                  <div class="p-mini-box">
                                    <el-avatar :size="20" :src="m.p2_avatar" class="p-avatar-mini">
                                      <el-icon><User /></el-icon>
                                    </el-avatar>
                                    <router-link :to="m.p2_user_id ? `/players/${m.p2_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p2_user_id}">
                                      {{ m.p2_name || '???' }}
                                    </router-link>
                                    <el-icon v-if="m.winner_side === 'side_b'" class="p-win-icon"><Check /></el-icon>
                                  </div>
                                  <div v-if="m.p2_partner_name" class="p-mini-box">
                                    <el-avatar :size="20" :src="m.p2_partner_avatar" class="p-avatar-mini">
                                      <el-icon><User /></el-icon>
                                    </el-avatar>
                                    <router-link :to="m.p2_partner_user_id ? `/players/${m.p2_partner_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p2_partner_user_id}">
                                      {{ m.p2_partner_name }}
                                    </router-link>
                                  </div>
                                </div>
                                <span class="p-score" v-if="m.score_b !== null && m.status === 'completed'">{{ m.score_b }}</span>
                              </div>

                              <div v-if="m.video_url || m.image_url || m.referee_name" class="m-v2-footer">
                                <div v-if="m.referee_name" class="m-referee">
                                  <el-icon><User /></el-icon> <span>Trọng tài: {{ m.referee_name }}</span>
                                </div>
                                <div class="m-media-actions">
                                  <el-button v-if="m.video_url" link type="danger" size="small" @click="openPreview('video', m.video_url, `Highlight Trận #${m.match_no}`)">
                                    <el-icon><VideoCamera /></el-icon> Video
                                  </el-button>
                                  <el-button v-if="m.image_url" link type="primary" size="small" @click="openPreview('image', m.image_url, `Ảnh Trận #${m.match_no}`)">
                                    <el-icon><Picture /></el-icon> {{ t('tournaments.photos') || 'Ảnh' }}
                                  </el-button>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          <div class="connector-line-out" v-if="roundIdx < groupedMatches.length - 1"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane :label="t('tournaments.standings')" name="standings">
                <div v-if="tournament.categories?.length > 1" class="category-filter-wrap">
                  <div class="filter-label">Chọn nội dung:</div>
                  <el-radio-group v-model="selectedCategoryId" size="small">
                    <el-radio-button v-for="cat in tournament.categories" :key="cat.id" :value="cat.id">
                      {{ cat.name }}
                    </el-radio-button>
                  </el-radio-group>
                </div>
                
                <div v-loading="loadingStandings" class="standings-wrap">
                  <div v-if="standingsData.length === 0" class="empty-state">
                    <div class="es-icon">📊</div>
                    <p>{{ t('tournaments.noGroupData') || 'Giải đấu đang diễn ra hoặc chưa có bảng xếp hạng vòng tròn.' }}</p>
                    <p class="small-hint">Bảng xếp hạng chỉ hiển thị cho các giải đấu có giai đoạn Vòng Bảng.</p>
                  </div>
                  
                  <div v-else class="standings-list">
                    <div v-for="group in standingsData" :key="group.group_name" class="premium-group-card">
                      <div class="pg-header">
                        <div class="pg-accent"></div>
                        <h3 class="pg-title">{{ group.group_name }}</h3>
                      </div>
                      
                      <div class="pg-table-wrap">
                        <table class="pg-table">
                          <thead>
                            <tr>
                              <th class="col-rank">#</th>
                              <th>{{ t('tournaments.athlete') }}</th>
                              <th class="text-center">W-L</th>
                              <th class="text-center">+/-</th>
                              <th class="text-center">PTS</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="(row, idx) in group.rankings" :key="row.player_name" :class="{ 'is-qualified': idx < 2 }">
                              <td class="col-rank">
                                <span class="rank-badge" :class="`rank-${idx + 1}`">{{ idx + 1 }}</span>
                              </td>
                              <td class="col-player">
                                <div class="player-stack-premium">
                                  <div class="player-unit-row">
                                    <el-avatar :size="24" :src="row.player_avatar" class="unit-avatar">
                                      <el-icon><User /></el-icon>
                                    </el-avatar>
                                    <router-link :to="row.player_id ? `/players/${row.player_id}` : '#'" class="main-player">
                                      {{ row.player_name }}
                                    </router-link>
                                  </div>
                                  <div v-if="row.partner_name" class="player-unit-row">
                                    <el-avatar :size="24" :src="row.partner_avatar" class="unit-avatar">
                                      <el-icon><User /></el-icon>
                                    </el-avatar>
                                    <router-link :to="row.partner_player_id ? `/players/${row.partner_player_id}` : '#'" class="partner-name">
                                      {{ row.partner_name }}
                                    </router-link>
                                  </div>
                                </div>
                              </td>
                              <td class="text-center stat-cell">
                                <span class="stat-win">{{ row.won }}</span> - <span class="stat-loss">{{ row.lost }}</span>
                              </td>
                              <td class="text-center diff-cell">
                                <el-tooltip content="Hiệu số Game" placement="top">
                                  <span :class="row.game_diff >= 0 ? 'pos' : 'neg'">{{ row.game_diff >= 0 ? '+' : '' }}{{ row.game_diff }}</span>
                                </el-tooltip>
                              </td>
                              <td class="text-center pts-cell">
                                <strong>{{ row.points }}</strong>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane :label="t('tournaments.participants') || 'Danh sách VĐV'" name="participants">
                <div v-if="tournament.categories?.length > 1" class="category-filter-wrap">
                  <div class="filter-label">Chọn nội dung:</div>
                  <el-radio-group v-model="selectedCategoryId" size="small">
                    <el-radio-button v-for="cat in tournament.categories" :key="cat.id" :value="cat.id">
                      {{ cat.name }}
                    </el-radio-button>
                  </el-radio-group>
                </div>
                
                <div v-loading="loadingRegistrations" class="neo-participants-container">
                  <div v-if="registrations.length === 0" class="empty-state">
                    <div class="es-icon">👥</div>
                    <p>{{ t('tournaments.noParticipants') || 'Chưa có vận động viên nào đăng ký.' }}</p>
                  </div>
                  
                  <div v-else class="participants-grid">
                    <div class="pg-table-wrap shadow-sm">
                      <table class="pg-table">
                        <thead>
                          <tr>
                            <th width="60" class="text-center">#</th>
                            <th>{{ t('tournaments.athlete') }}</th>
                            <th>{{ t('tournaments.category') }}</th>
                            <th class="text-right">{{ t('tournaments.registrationTime') || 'Thời gian đăng ký' }}</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(reg, idx) in registrations" :key="reg.id">
                            <td class="text-center"><span class="idx-badge">{{ idx + 1 }}</span></td>
                            <td class="col-player">
                              <div class="teams-display-premium">
                                <div class="player-item-mini">
                                  <el-avatar :size="32" :src="reg.player_avatar" class="player-avatar">
                                    <el-icon><User /></el-icon>
                                  </el-avatar>
                                  <div class="player-meta">
                                    <router-link :to="`/players/${reg.user_id}`" class="name">{{ reg.player_name }}</router-link>
                                    <span v-if="reg.player_skill" class="skill-tag">{{ reg.player_skill }}</span>
                                  </div>
                                </div>
                                <div v-if="reg.partner_name" class="team-divider">&</div>
                                <div v-if="reg.partner_name" class="player-item-mini">
                                  <el-avatar :size="32" :src="reg.partner_avatar" class="player-avatar">
                                    <el-icon><User /></el-icon>
                                  </el-avatar>
                                  <div class="player-meta">
                                    <router-link v-if="reg.partner_user_id" :to="`/players/${reg.partner_user_id}`" class="name">{{ reg.partner_name }}</router-link>
                                    <span v-else class="name">{{ reg.partner_name }}</span>
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td>
                              <span class="category-text">{{ reg.category_name || (reg.registrant_type === 'team' ? 'Đôi' : 'Đơn') }}</span>
                            </td>
                            <td class="text-right time-cell">
                              {{ formatDateTime(reg.registered_at) }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane label="Media" name="media">
                <div v-if="allMedia.length === 0" class="empty-state">
                  <div class="es-icon">🎞️</div>
                  <p>Giải đấu chưa có hình ảnh hoặc video highlight nào.</p>
                </div>
                <div v-else class="media-gallery-grid">
                  <div v-for="item in allMedia" :key="item.id" class="media-item-card">
                    <div class="media-preview">
                      <img v-if="item.image_url" :src="item.image_url" :alt="item.match_label" />
                      <div v-else class="video-placeholder">
                        <el-icon><VideoCamera /></el-icon>
                        <span>Video Highlight</span>
                      </div>
                      <div class="media-overlay">
                        <div class="play-btn" @click="openPreview(item.video_url ? 'video' : 'image', item.video_url || item.image_url, item.match_label)">
                          <el-icon v-if="item.video_url"><VideoPlay /></el-icon>
                          <el-icon v-else><View /></el-icon>
                        </div>
                      </div>
                    </div>
                    <div class="media-info">
                      <h4 class="m-match-label">{{ item.match_label }}</h4>
                      <p class="m-round-info">{{ item.round_code }} - {{ item.p1_name }} vs {{ item.p2_name }}</p>
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

    <!-- Mobile Sticky Registration Bar -->
    <div class="mobile-sticky-action-bar" v-if="tournament">
      <div class="ms-inner">
        <div class="ms-info">
          <span class="ms-label">{{ t('tournaments.entryFee') || 'Lệ phí:' }}</span>
          <strong class="ms-price">
            {{ tournament.entry_fee ? new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(tournament.entry_fee) : t('tournaments.free') }}
          </strong>
        </div>
        <div class="ms-btn-wrap">
          <button 
            v-if="isRegistrationOpen"
            class="neo-btn-primary ms-btn" 
            @click="goToRegister" 
            :disabled="isAlreadyRegistered || tournament.current_participants >= (tournament.max_participants || tournament.draw_size)"
            :class="{ 'is-disabled': isAlreadyRegistered || tournament.current_participants >= (tournament.max_participants || tournament.draw_size) }"
          >
            <span v-if="isAlreadyRegistered">{{ t('tournaments.alreadyRegistered') || 'Đã ghi danh' }}</span>
            <span v-else-if="tournament.current_participants >= (tournament.max_participants || tournament.draw_size)">{{ t('tournaments.fullyBooked') || 'Đã hết slot' }}</span>
            <span v-else>{{ t('tournaments.registerNow') || 'Đăng ký ngay' }}</span>
          </button>
          <div v-else class="ms-status-text">
            <span v-if="isPastDeadline">{{ t('tournaments.registrationExpired') || 'Hết hạn' }}</span>
            <span v-else-if="tournament.status === 'draft'">{{ t('tournaments.registrationNotOpen') || 'Chưa mở' }}</span>
            <span v-else>{{ t('tournaments.tournamentClosed') || 'Đã đóng' }}</span>
          </div>
        </div>
      </div>
    </div>

  </div>


    <!-- Media Preview Dialog -->
    <el-dialog
      v-model="previewVisible"
      :title="previewData.title"
      width="80%"
      destroy-on-close
      class="media-preview-dialog"
    >
      <div class="preview-content">
        <div v-if="previewData.type === 'video'" class="video-container">
          <iframe 
            v-if="previewData.url.includes('youtube.com') || previewData.url.includes('youtu.be')"
            :src="previewData.url.replace('watch?v=', 'embed/')" 
            frameborder="0" 
            allowfullscreen
            class="preview-video"
          ></iframe>
          <video v-else :src="previewData.url" controls autoplay class="preview-video"></video>
        </div>
        <div v-else class="image-container">
          <el-image :src="previewData.url" fit="contain" class="preview-image" />
        </div>
      </div>
    </el-dialog>

    <div v-if="tournamentStore.loading && !tournament" class="neo-loading">
      <div class="spinner-ring"></div>
      <p>{{ t('tournaments.loadingData') }}</p>
    </div>
  </div>
</template>

<style scoped>
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
.neo-grid { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 2rem; align-items: start; }
.neo-col-main { min-width: 0; width: 100%; }
.neo-tabs-container { background: var(--bg-surface); border-radius: var(--radius-xl); padding: 2rem; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); min-height: 500px; overflow: hidden; }
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
.bracket-scroll-hint {
  display: none;
}
.bracket-viewport {
  margin-top: 10px;
  overflow-x: auto;
  padding: 20px 0;
  -webkit-overflow-scrolling: touch;
}
.bracket-viewport::-webkit-scrollbar {
  height: 6px;
}
.bracket-viewport::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 10px;
}
.bracket-viewport::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
}
.bracket-viewport::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.4);
}

.neo-bracket-horizontal {
  display: flex;
  gap: 60px;
  padding: 20px;
  min-width: max-content;
}

.bracket-column {
  display: flex;
  flex-direction: column;
  width: 280px;
  flex-shrink: 0;
}

.round-sticky-header {
  margin-bottom: 24px;
  background: #f8fafc;
  padding: 12px 20px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.round-title-group { display: flex; align-items: center; gap: 10px; }
.round-index { 
  background: var(--text-primary); 
  color: white; 
  width: 24px; 
  height: 24px; 
  border-radius: 6px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  font-size: 0.75rem; 
  font-weight: 800; 
}
.round-title { margin: 0; font-size: 0.95rem; font-weight: 800; color: var(--text-primary); text-transform: uppercase; letter-spacing: 0.05em; }
.round-count { font-size: 0.75rem; color: #64748b; font-weight: 600; }

.matches-stack {
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  flex-grow: 1;
  gap: 30px;
}

.match-node-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.match-node-v2 {
  width: 100%;
  background: white;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 2;
}

.match-node-v2:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(15, 23, 42, 0.1); border-color: var(--accent-light); }

.m-v2-header { padding: 10px 16px; background: #f8fafc; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
.m-v2-header-left { display: flex; align-items: center; gap: 12px; }
.m-v2-no { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; font-weight: 700; color: #94a3b8; }
.m-v2-court { display: flex; align-items: center; gap: 4px; font-size: 0.7rem; font-weight: 700; color: #64748b; background: #e2e8f0; padding: 2px 8px; border-radius: 4px; }
.m-v2-status { font-size: 0.65rem; font-weight: 800; text-transform: uppercase; padding: 3px 8px; border-radius: 6px; background: #f1f5f9; color: #64748b; }
.m-v2-status.is-done { background: #dcfce7; color: #16a34a; }
.m-v2-status.is-live { background: #fee2e2; color: #dc2626; animation: pulse 2s infinite; }

.m-v2-body { padding: 8px 0; }
.m-v2-player { display: flex; justify-content: space-between; align-items: center; padding: 10px 16px; transition: all 0.2s; position: relative; }
.m-v2-player.is-win { background: #f0fdf4; }
.p-info-wrapper { display: flex; align-items: center; gap: 10px; flex: 1; overflow: hidden; }
.p-avatar-mini { border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.p-info { display: flex; align-items: center; gap: 6px; overflow: hidden; }
.p-name-link { font-weight: 700; color: #1e293b; text-decoration: none; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.p-name-link.no-link { pointer-events: none; }
.p-win-icon { color: #22c55e; font-size: 0.9rem; flex-shrink: 0; }
.p-partner { font-size: 0.7rem; color: #64748b; font-style: italic; white-space: nowrap; }
.p-score { font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 800; color: #0f172a; min-width: 24px; text-align: center; }
.m-v2-divider { height: 1px; background: #f1f5f9; margin: 0 16px; }

/* Connector lines */
.connector-line-in {
  position: absolute;
  left: -40px;
  width: 40px;
  height: 1px;
  background: #cbd5e1;
}

.connector-line-out {
  position: absolute;
  right: -40px;
  width: 40px;
  height: 1px;
  background: #cbd5e1;
}

.matches-stack > .match-node-wrapper:nth-child(even) .connector-line-out {
  height: calc(50% + 15px);
  top: 50%;
  border-left: 1px solid #cbd5e1;
  border-bottom: 1px solid #cbd5e1;
  width: 40px;
  background: transparent;
}

.matches-stack > .match-node-wrapper:nth-child(odd) .connector-line-out {
  height: calc(50% + 15px);
  bottom: 50%;
  border-left: 1px solid #cbd5e1;
  border-top: 1px solid #cbd5e1;
  width: 40px;
  background: transparent;
}

.empty-state { text-align: center; padding: 4rem 0; color: var(--text-muted); }
.es-icon { font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;}
.player-stack-v2 { display: flex; flex-direction: column; gap: 6px; flex: 1; overflow: hidden; padding: 4px 0; }
.p-mini-box { display: flex; align-items: center; gap: 8px; overflow: hidden; }
.p-name-link { font-size: 0.85rem; font-weight: 700; color: var(--navy); text-decoration: none; transition: 0.2s; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px; }
.p-name-link:hover { color: var(--accent); }
.p-name-link.no-link { pointer-events: none; color: #64748b; }

.teams-display-premium { display: flex; align-items: center; gap: 16px; }
.player-item-mini { display: flex; align-items: center; gap: 10px; }
.player-meta { display: flex; flex-direction: column; line-height: 1.2; }
.player-meta .name { font-weight: 700; color: var(--navy); text-decoration: none; font-size: 0.9rem; }
.player-meta .name:hover { color: var(--accent); }
.team-divider { font-weight: 900; color: #cbd5e1; font-size: 1.2rem; margin: 0 4px; }
.m-v2-footer { margin-top: 10px; padding-top: 10px; border-top: 1px solid #f1f5f9; display: flex; flex-direction: column; gap: 8px; }
.m-referee { font-size: 0.75rem; color: #64748b; font-weight: 600; display: flex; align-items: center; gap: 4px; }
.m-media-actions { display: flex; gap: 8px; }
.media-btn { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; text-decoration: none; transition: all 0.2s; }
.media-btn.video { background: #fef2f2; color: #dc2626; border: 1px solid #fee2e2; }
.media-btn.video:hover { background: #dc2626; color: white; }
.media-btn.image { background: #eff6ff; color: #2563eb; border: 1px solid #dbeafe; }
.media-btn.image:hover { background: #2563eb; color: white; }
.neo-standings-container { margin-top: 1.5rem; }
.standings-list { display: flex; flex-direction: column; gap: 2rem; }
.premium-group-card { background: white; border-radius: 20px; border: 1px solid #f1f5f9; padding: 24px; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.02); }
.pg-header { display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem; }
.pg-accent { width: 4px; height: 20px; background: var(--hero-glow-2); border-radius: 4px; }
.pg-title { font-size: 1.1rem; font-weight: 800; color: var(--text-primary); margin: 0; text-transform: uppercase; letter-spacing: 0.05em; }
.pg-table-wrap { overflow-x: auto; border-radius: 12px; border: 1px solid #f1f5f9; -webkit-overflow-scrolling: touch; }
.pg-table { width: 100%; border-collapse: collapse; min-width: 480px; }
.pg-table th { background: #f8fafc; padding: 12px 16px; font-size: 0.7rem; font-weight: 800; color: #64748b; text-transform: uppercase; border-bottom: 2px solid #f1f5f9; text-align: left; }
.pg-table td { padding: 14px 16px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.pg-table tr:last-child td { border-bottom: none; }
.pg-table tr.is-qualified { background: #f0fdf440; }
.col-rank { width: 50px; text-align: center; }
.rank-badge { width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; font-weight: 800; font-size: 0.75rem; background: #f1f5f9; color: #64748b; }
.rank-1 { background: #fef3c7; color: #92400e; box-shadow: 0 0 0 2px #fde68a; }
.rank-2 { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
.player-stack-premium { display: flex; flex-direction: column; gap: 8px; }
.player-unit-row { display: flex; align-items: center; gap: 10px; }
.unit-avatar { border: 1.5px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }
.main-player, .partner-name { font-weight: 700; color: var(--navy); text-decoration: none; font-size: 0.9rem; }
.main-player:hover, .partner-name:hover { color: var(--accent); }
.stat-cell { font-weight: 600; color: #64748b; font-size: 0.85rem; }
.stat-win { color: #16a34a; }
.stat-loss { color: #dc2626; }
.diff-cell { font-weight: 700; font-size: 0.85rem; }
.diff-cell span.pos { color: #16a34a; }
.diff-cell span.neg { color: #dc2626; }
.pts-cell { color: var(--accent); font-size: 1.05rem; }
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
@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
  100% { transform: scale(1); opacity: 1; }
}
@media (max-width: 1024px) { 
  .neo-grid { grid-template-columns: 1fr; gap: 1.5rem; } 
  .neo-col-sidebar { order: 2; } 
  .neo-action-card { box-shadow: 0 10px 30px rgba(0,0,0,0.05); } 
  .sticky { position: relative; top: 0; }
  .main-overlap { margin-top: -2rem; }
}
@media (max-width: 768px) { 
  .container { padding: 0 1rem; }
  .neo-hero { padding: 3.5rem 0 4.5rem; }
  .hero-title { font-size: 1.8rem; margin-bottom: 1.25rem; word-break: break-word; } 
  .hero-details { 
    flex-direction: column; 
    align-items: flex-start; 
    gap: 0.75rem; 
    width: 100%;
    padding: 1rem;
    border-radius: var(--radius-md);
  } 
  .hd-divider { display: none; } 
  .bento-layout { grid-template-columns: 1fr; gap: 0.75rem; } 
  .box-lg { grid-column: auto; } 
  .neo-tabs-container { padding: 1rem; border-radius: var(--radius-lg); min-height: auto; max-width: 100vw; overflow: hidden; }
  .main-overlap { margin-top: -1.5rem; }
  .registered-highlight {
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    border: 1px solid #bbf7d0 !important;
  }
  .registered-highlight .bento-icon { color: #22c55e; }
  .registered-highlight .bento-val { color: #15803d; }
  
  .viewing-highlight {
    border: 1px solid var(--accent-light) !important;
  }
  :deep(.neo-tabs .el-tabs__header) { margin-bottom: 1rem; }
  :deep(.neo-tabs .el-tabs__nav-wrap) { overflow-x: auto !important; overflow-y: hidden !important; -webkit-overflow-scrolling: touch; scrollbar-width: none; -ms-overflow-style: none; }
  :deep(.neo-tabs .el-tabs__nav-wrap::-webkit-scrollbar) { display: none !important; }
  :deep(.neo-tabs .el-tabs__nav-wrap.is-scrollable) { padding: 0 !important; }
  :deep(.neo-tabs .el-tabs__nav-prev), :deep(.neo-tabs .el-tabs__nav-next) { display: none !important; }
  :deep(.neo-tabs .el-tabs__nav-scroll) { overflow: visible !important; }
  :deep(.neo-tabs .el-tabs__nav) { display: flex; flex-wrap: nowrap; width: max-content; }
  :deep(.neo-tabs .el-tabs__item) { flex: none !important; text-align: center; padding: 0 16px !important; min-width: max-content; font-size: 0.85rem; }
  .neo-table th, .neo-table td { padding: 8px 6px; font-size: 0.75rem; }
  .sg-title { font-size: 0.95rem; }
  .matches-vertical-grid { grid-template-columns: 1fr; gap: 1rem; }
  .round-sticky-header { padding: 10px 15px; }
  .round-title { font-size: 0.9rem; }
  .m-v2-player { padding: 8px; }
  .p-name { font-size: 0.85rem; }
  .p-score { font-size: 1rem; }
  .ac-progress-section { margin-bottom: 1.5rem; }
  
  /* Responsive Bracket draw & filter on mobile */
  .category-filter-wrap {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    padding: 10px;
    overflow: hidden;
  }
  .category-filter-wrap .filter-label {
    text-align: center;
  }
  .category-filter-wrap :deep(.el-radio-group) {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 4px;
    width: 100%;
  }
  .category-filter-wrap :deep(.el-radio-button) {
    flex-shrink: 0;
  }
  .category-filter-wrap :deep(.el-radio-group::-webkit-scrollbar) { display: none; }
  .bracket-scroll-hint {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #eff6ff;
    color: var(--accent);
    padding: 6px 12px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 700;
    margin-bottom: 12px;
    border: 1px solid #dbeafe;
    animation: pulseHint 2s infinite ease-in-out;
  }
  @keyframes pulseHint {
    0%, 100% { opacity: 0.9; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.02); }
  }
  .bracket-viewport {
    scroll-snap-type: x mandatory;
  }
  .neo-bracket-horizontal {
    gap: 30px;
    padding: 10px;
  }
  .bracket-column {
    width: 250px;
    scroll-snap-align: center;
  }
  .connector-line-in {
    left: -20px;
    width: 20px;
  }
  .connector-line-out {
    right: -20px;
    width: 20px;
  }
  .matches-stack > .match-node-wrapper:nth-child(even) .connector-line-out {
    width: 20px;
    border-left: 1px solid #cbd5e1;
    border-bottom: 1px solid #cbd5e1;
  }
  .matches-stack > .match-node-wrapper:nth-child(odd) .connector-line-out {
    width: 20px;
    border-left: 1px solid #cbd5e1;
    border-top: 1px solid #cbd5e1;
  }
}
@media (max-width: 480px) {
  .hero-title { font-size: 1.5rem; }
  .neo-hero { padding: 2.5rem 0 4rem; }
  .neo-badge { font-size: 0.65rem; padding: 3px 8px; }
  .tour-type { font-size: 0.7rem; }
  .main-overlap { margin-top: 0; }
  .neo-tabs-container { border-radius: 0; margin-left: -1rem; margin-right: -1rem; width: calc(100% + 2rem); max-width: 100vw; overflow: hidden; }
  .bento-box { padding: 0.85rem; }
  .bento-val { font-size: 1rem; }
  .bento-icon { font-size: 1.25rem; }
  .neo-action-card { padding: 1.25rem; border-radius: var(--radius-lg); }
  .price-tag { font-size: 1.25rem; }
  .ac-header h2 { font-size: 1.1rem; }
  .ac-header { margin-bottom: 1.25rem; }
  .ac-progress-section { margin-bottom: 1.5rem; }
}

/* Participants Styles */
.neo-participants-container { margin-top: 1.5rem; }
.idx-badge { width: 24px; height: 24px; background: #f1f5f9; color: #64748b; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; font-weight: 800; font-size: 0.7rem; }
.player-info-cell { display: flex; flex-direction: column; gap: 4px; }
.player-main { display: flex; align-items: center; gap: 8px; }
.player-main .name { font-weight: 700; color: var(--text-primary); text-decoration: none; font-size: 0.95rem; }
.player-main .name:hover { color: var(--accent); text-decoration: underline; }
.skill-tag { font-size: 0.65rem; background: #eff6ff; color: #3b82f6; padding: 2px 6px; border-radius: 4px; font-weight: 700; }
.player-partner { font-size: 0.8rem; color: #64748b; display: flex; gap: 4px; }
.partner-label { font-weight: 500; }
.partner-name { font-weight: 600; color: #334155; }
.type-tag { font-size: 0.7rem; font-weight: 700; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; }
.type-tag.team { background: #fff7ed; color: #f97316; }
.type-tag.player { background: #f1f5f9; color: #475569; }
.time-cell { font-size: 0.8rem; color: #64748b; font-weight: 500; font-family: monospace; }
.shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
.category-filter-wrap {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}
.filter-label {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-secondary);
}

:deep(.el-radio-button__inner) {
  background: white !important;
  color: var(--text-secondary) !important;
  border: 1px solid #e2e8f0 !important;
  font-weight: 700;
  transition: all 0.3s ease;
}

:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--accent) !important;
  color: white !important;
  border-color: var(--accent) !important;
}

.standings-wrap, .bracket-viewport {
  margin-top: 10px;
}

/* Match Node Footer */
.m-v2-footer { margin-top: 10px; padding-top: 10px; border-top: 1px solid #f1f5f9; display: flex; flex-direction: column; gap: 8px; }
.m-referee { font-size: 0.75rem; color: #64748b; font-weight: 600; display: flex; align-items: center; gap: 4px; }
.m-media-actions { display: flex; gap: 8px; }
.media-btn { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; text-decoration: none; transition: all 0.2s; }
.media-btn.video { background: #fef2f2; color: #dc2626; border: 1px solid #fee2e2; }
.media-btn.video:hover { background: #dc2626; color: white; }
.media-btn.image { background: #eff6ff; color: #2563eb; border: 1px solid #dbeafe; }
.media-btn.image:hover { background: #2563eb; color: white; }

/* Media Gallery */
.media-gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; padding: 10px 0; }
.media-item-card { background: white; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; transition: transform 0.3s; }
.media-item-card:hover { transform: translateY(-5px); }
.media-preview { position: relative; height: 180px; background: #0f172a; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.media-preview img { width: 100%; height: 100%; object-fit: cover; }
.video-placeholder { color: #94a3b8; display: flex; flex-direction: column; align-items: center; gap: 10px; }
.video-placeholder .el-icon { font-size: 2.5rem; }
.media-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s; }
.media-item-card:hover .media-overlay { opacity: 1; }
.play-btn { width: 50px; height: 50px; background: white; color: #dc2626; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; text-decoration: none; }
.media-info { padding: 15px; }
.m-match-label { margin: 0 0 5px; font-size: 1rem; font-weight: 700; color: #1e293b; }
.m-round-info { margin: 0; font-size: 0.8rem; color: #64748b; font-weight: 500; }

/* Premium Sticky Mobile Registration Bar */
.mobile-sticky-action-bar {
  display: none;
}

@media (max-width: 768px) {
  .mobile-sticky-action-bar {
    display: block;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-top: 1px solid rgba(226, 232, 240, 0.8);
    box-shadow: 0 -10px 30px rgba(15, 23, 42, 0.08);
    padding: 12px 24px;
    z-index: 999;
    padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
  }
  
  .ms-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 600px;
    margin: 0 auto;
    gap: 16px;
  }
  
  .ms-info {
    display: flex;
    flex-direction: column;
  }
  
  .ms-label {
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.05em;
  }
  
  .ms-price {
    font-size: 1.1rem;
    color: var(--accent);
    font-weight: 800;
  }
  
  .ms-btn-wrap {
    flex: 1;
    max-width: 200px;
  }
  
  .ms-btn {
    width: 100%;
    padding: 10px 16px !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    border-radius: var(--radius-md) !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
  }
  
  .ms-status-text {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-align: center;
    padding: 8px 12px;
    background: #f1f5f9;
    border-radius: var(--radius-md);
  }
  
  .neo-tournament-page {
    padding-bottom: calc(7rem + env(safe-area-inset-bottom, 0px)) !important;
  }
}
</style>