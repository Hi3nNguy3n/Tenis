<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import apiClient from '../../services/apiClient'
import { newsService } from '../../services/newsService'
import { playerService } from '../../services/playerService'
import { useAuthStore } from '../../stores/auth'
import { currentLocale, t } from '../../utils/locale'
import { Message, Check, Right, VideoPlay, Location } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const router = useRouter()

const isVideo = (url) => {
  if (!url) return false
  return url.match(/\.(mp4|webm|ogg)$/i) !== null
}

const rawNewsPosts = ref([])
const newsItems = computed(() => {
  return rawNewsPosts.value.map(post => ({
    id: post.id,
    slug: post.slug,
    title: post.title,
    date: new Date(post.publish_at || post.created_at).toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US'),
    category: t('home.tennisNews'),
    excerpt: post.summary,
    image: post.media_url || post.thumbnail_url || 'https://images.unsplash.com/photo-1595435934249-5df7ed86e1f4?auto=format&fit=crop&q=80&w=800'
  }))
})

// === STATE ===
const activeRankingTab = ref('singles')
const rawRankings = ref([])
const recentMatches = ref([])
const featuredTournaments = ref([])

const topPlayers = computed(() => {
  return rawRankings.value.slice(0, 10).map((p, index) => ({
    ...p,
    displayRank: index + 1
  }))
})

const doublesRankings = computed(() => {
  const sorted = [...rawRankings.value].sort((a, b) => (a.rank || 0) - (b.rank || 0))
  const pairs = []
  for (let index = 0; index < sorted.length; index += 2) {
    const first = sorted[index]
    const second = sorted[index + 1]
    if (!first || !second) continue
    pairs.push({
      rank: pairs.length + 1,
      player_id: `pair-${first.player_id}-${second.player_id}`,
      full_name: `${first.full_name} / ${second.full_name}`,
      p1_name: first.full_name,
      p2_name: second.full_name,
      p1_user_id: first.player_id,
      p2_user_id: second.player_id,
      elo_points: (first.elo_points || 0) + (second.elo_points || 0),
      isDoublesPair: true
    })
  }
  return pairs.slice(0, 10)
})

const displayedRankings = computed(() => {
  if (activeRankingTab.value === 'doubles') return doublesRankings.value
  return topPlayers.value
})
const h2hData = ref(null) 
const h2hPairIndex = ref(0)
const h2hLoading = ref(false)
const h2hSelectedLeft = ref(null)
const h2hSelectedRight = ref(null)
const h2hShowSelectLeft = ref(false)
const h2hShowSelectRight = ref(false)
const homeTopBanners = ref([])
const homeAdBanners = ref([])
const marketingSponsors = ref([])

const fallbackHomeBanner = {
  title: 'Saigontennistours',
  subtitle: 'Cập nhật giải đấu, lịch thi đấu và cộng đồng tennis mỗi ngày.',
  image_url: 'https://tpc.googlesyndication.com/simgad/9470293650305402252',
  link_url: '/tournaments',
  open_in_new_tab: false,
}

const fallbackSponsors = [
  { id: 'fallback-emirates', name: 'Emirates', logo_url: '/emirates.svg', tier: 'premier', website_url: '' },
  { id: 'fallback-pif', name: 'PIF', logo_url: '/pif.svg', tier: 'gold', website_url: '' },
  { id: 'fallback-lexus', name: 'Lexus', logo_url: '/lexus.svg', tier: 'gold', website_url: '' },
  { id: 'fallback-infosys', name: 'Infosys', logo_url: 'https://upload.wikimedia.org/wikipedia/commons/9/95/Infosys_logo.svg', tier: 'partner', website_url: '' },
  { id: 'fallback-nitto', name: 'Nitto', logo_url: '/nitto.svg', tier: 'partner', website_url: '' },
  { id: 'fallback-haier', name: 'Haier', logo_url: '/haier.jpg', tier: 'partner', website_url: '' },
]

const homeTopBanner = computed(() => homeTopBanners.value[0] || null)
const homeAdBanner = computed(() => homeAdBanners.value[0] || null)
const homeBannerItems = computed(() => {
  const seen = new Set()
  return homeTopBanners.value
    .filter((banner) => {
      if (!banner?.id || seen.has(banner.id)) return false
      seen.add(banner.id)
      return Boolean(banner.image_url)
    })
    .slice(0, 3)
})
const homeAdItems = computed(() => {
  const seen = new Set()
  return homeAdBanners.value
    .filter((banner) => {
      if (!banner?.id || seen.has(banner.id)) return false
      seen.add(banner.id)
      return Boolean(banner.image_url)
    })
    .slice(0, 3)
})

const sponsorTierLabels = {
  premier: t('home.premierPartner') || 'Đối tác chính',
  gold: t('home.platinumPartner') || 'Đối tác vàng',
  silver: 'Đối tác bạc',
  partner: t('home.goldPartner') || 'Đối tác đồng hành',
}

const sponsorTierOrder = ['premier', 'gold', 'silver', 'partner']

const sponsorGroups = computed(() => {
  const source = marketingSponsors.value.length ? marketingSponsors.value : fallbackSponsors
  const groups = new Map()
  source.forEach((sponsor) => {
    const tier = sponsor.tier || 'partner'
    if (!groups.has(tier)) {
      groups.set(tier, {
        tier,
        label: sponsorTierLabels[tier] || tier,
        items: []
      })
    }
    groups.get(tier).items.push(sponsor)
  })

  return [...groups.values()].sort((a, b) => {
    const orderA = sponsorTierOrder.indexOf(a.tier)
    const orderB = sponsorTierOrder.indexOf(b.tier)
    return (orderA === -1 ? 99 : orderA) - (orderB === -1 ? 99 : orderB)
  })
})

const getTournamentStatusLabel = (status) => {
  const map = {
    'ongoing': t('tournaments.ongoing'),
    'open': t('tournaments.upcoming'),
    'finished': t('tournaments.completed'),
    'pending': t('tournaments.upcoming')
  }
  return map[status] || t('tournaments.upcoming')
}

const getTournamentImage = (tour) => {
  if (tour.media_url) return tour.media_url
  const posters = ['/poster-1.jpg', '/poster-2.jpg', '/poster-3.jpg', '/poster-4.jpg']
  const index = (tour.id || 0) % posters.length
  return posters[index]
}

const hasHomeBanners = computed(() => homeBannerItems.value.length > 0)
const hasHomeAds = computed(() => homeAdItems.value.length > 0)

const getScorePart = (score, sideIndex) => {
  if (!score) return '-'
  const firstSet = String(score).split(',')[0] || ''
  const parts = firstSet.split('-')
  return parts[sideIndex]?.trim() || '-'
}

const hasRealPlayerName = (name) => {
  const normalized = String(name || '').trim().toLowerCase()
  if (!normalized) return false
  return ![
    'dang cap nhat',
    'đang cập nhật',
    'chua xac dinh',
    'chưa xác định',
    'tba'
  ].includes(normalized)
}

const hasScoreData = (match) => {
  const score = String(match?.score || match?.score_summary || match?.result_note || '').trim()
  return Boolean(score && !['-', '--', '--:--', 'n/a'].includes(score.toLowerCase()))
}

const hasDisplayableMatchData = (match) => {
  if (hasScoreData(match)) return true
  return hasRealPlayerName(match?.p1_name) && hasRealPlayerName(match?.p2_name)
}

const getMatchContext = (match) => {
  const tournament = match.tournament || 'Giao hữu tự do'
  const round = match.round_code || t('home.round')
  return `${tournament} · ${round}`
}

onMounted(async () => {
  authStore.hydrate()
  
  Promise.all([
    newsService.getAllPosts({ limit: 5 }),
    playerService.getRankings({ limit: 10 }).catch(() => []),
    apiClient.get('/api/tournaments/matches/all', { params: { show_on_homepage: true, limit: 5 } }).catch(() => []),
    apiClient.get('/api/tournaments', { params: { limit: 4 } }).catch(() => []),
    apiClient.get('/api/marketing/banners', { params: { placement: 'home_top', limit: 3 } }).catch(() => []),
    apiClient.get('/api/marketing/banners', { params: { placement: 'home_ad', limit: 3 } }).catch(() => []),
    apiClient.get('/api/marketing/sponsors', { params: { limit: 100 } }).catch(() => [])
  ]).then(async ([newsData, rankingsData, matchesData, toursData, homeTopData, homeAdData, sponsorsData]) => {
    
    // 1. Xử lý Tin tức
    if (newsData) {
      rawNewsPosts.value = newsData.sort((a, b) => new Date(b.publish_at || b.created_at) - new Date(a.publish_at || a.created_at))
    }
    
    // 2. Xử lý Rankings
    const filteredRankings = (rankingsData || []).filter(p => !p.full_name?.toLowerCase().includes('admin'))
    rawRankings.value = filteredRankings.map((p, index) => ({
      ...p,
      rank: index + 1
    }))

    // 3. Xử lý Matches
    const filteredMatches = (Array.isArray(matchesData) ? matchesData : []).filter(m => {
      const isP1Admin = m.p1_name?.toLowerCase().includes('admin')
      const isP2Admin = m.p2_name?.toLowerCase().includes('admin')
      return !isP1Admin && !isP2Admin && hasDisplayableMatchData(m) && m.show_on_homepage === true
    })
    recentMatches.value = filteredMatches.slice(0, 5)

    // 2.5 Xử lý Tournaments
    if (toursData && Array.isArray(toursData)) {
      // Ưu tiên ONGOING -> OPEN -> FINISHED
      const statusOrder = { 'ongoing': 0, 'open': 1, 'pending': 2, 'finished': 3 }
      featuredTournaments.value = [...toursData]
        .sort((a, b) => (statusOrder[a.status] ?? 99) - (statusOrder[b.status] ?? 99))
        .slice(0, 4)
    }

    homeTopBanners.value = Array.isArray(homeTopData) ? homeTopData : []
    homeAdBanners.value = Array.isArray(homeAdData) ? homeAdData : []
    marketingSponsors.value = Array.isArray(sponsorsData) ? sponsorsData : []

    // 4. LOGIC H2H
    let p1 = null;
    let p2 = null;

    if (recentMatches.value.length > 0) {
      const highlightMatch = recentMatches.value[0]; 
      p1 = topPlayers.value.find(p => p.full_name === highlightMatch.p1_name);
      p2 = topPlayers.value.find(p => p.full_name === highlightMatch.p2_name);
    }

    if (!p1 || !p2) {
      if (topPlayers.value.length >= 2) {
        p1 = topPlayers.value[0];
        p2 = topPlayers.value[1];
      }
    }

    if (p1 && p2) {
      h2hSelectedLeft.value = p1.player_id
      h2hSelectedRight.value = p2.player_id
      loadH2HForPair(p1, p2)
    }

  }).catch(err => console.error("Lỗi tải dữ liệu Home:", err))
})

const goToMatch = (match) => {
  if (match.tournament_id) {
    router.push({
      path: `/tournaments/${match.tournament_id}`,
      query: { matchId: match.id }
    })
  }
}

const shuffleH2H = (direction = 1) => {
  const players = topPlayers.value
  if (players.length < 2 || h2hLoading.value) return

  const allPairs = []
  for (let i = 0; i < players.length; i++) {
    for (let j = i + 1; j < players.length; j++) {
      allPairs.push([players[i], players[j]])
    }
  }
  if (allPairs.length === 0) return

  h2hPairIndex.value = (h2hPairIndex.value + direction + allPairs.length) % allPairs.length
  const [p1, p2] = allPairs[h2hPairIndex.value]
  h2hSelectedLeft.value = p1.player_id
  h2hSelectedRight.value = p2.player_id
  loadH2HForPair(p1, p2)
}

const loadH2HForPair = (p1, p2) => {
  if (!p1 || !p2 || p1.player_id === p2.player_id) return
  h2hLoading.value = true
  h2hData.value = {
    player1: p1,
    player2: p2,
    score1: 0,
    score2: 0
  }
  apiClient.get(`/api/players/h2h/compare/${p1.player_id}/${p2.player_id}`)
    .then(res => {
      if (res) {
        h2hData.value.score1 = res.wins_a || 0
        h2hData.value.score2 = res.wins_b || 0
      }
    })
    .catch(err => console.error('L\u1ed7i l\u1ea5y l\u1ecbch s\u1eed \u0111\u1ed1i \u0111\u1ea7u:', err))
    .finally(() => { h2hLoading.value = false })
}

const selectH2HPlayer = (side, player) => {
  if (side === 'left') {
    h2hSelectedLeft.value = player.player_id
    h2hShowSelectLeft.value = false
    const rightPlayer = topPlayers.value.find(p => p.player_id === h2hSelectedRight.value)
    if (rightPlayer && player.player_id !== rightPlayer.player_id) {
      loadH2HForPair(player, rightPlayer)
    }
  } else {
    h2hSelectedRight.value = player.player_id
    h2hShowSelectRight.value = false
    const leftPlayer = topPlayers.value.find(p => p.player_id === h2hSelectedLeft.value)
    if (leftPlayer && leftPlayer.player_id !== player.player_id) {
      loadH2HForPair(leftPlayer, player)
    }
  }
}
</script>

<template>
  <div class="home-page atp-theme">
    
    <section class="container atp-top-section">
      <div class="main-hero-news" v-if="newsItems.length > 0" @click="$router.push('/news/' + newsItems[0].slug)">
        <video 
          v-if="isVideo(newsItems[0].image)" 
          :src="newsItems[0].image" 
          class="hero-media" 
          autoplay muted loop playsinline
        ></video>
        <img v-else :src="newsItems[0].image" class="hero-media" referrerpolicy="no-referrer" />
        
        <div class="hero-overlay">
          <span class="category-badge">{{ newsItems[0].category }}</span>
          <h1>{{ newsItems[0].title }}</h1>
        </div>
      </div>

      <div class="scores-widget">
        <div class="widget-header">
          <h3>{{ t('home.scores') }}</h3>
          <RouterLink to="/matches" class="view-all">{{ t('home.seeAllMatches') }} <el-icon><Right /></el-icon></RouterLink>
        </div>
        <div class="widget-tabs">
          <span class="active">{{ t('home.liveCompleted') }}</span>
          <span @click="$router.push('/tournaments')" style="cursor: pointer;">{{ t('home.schedule') }}</span>
        </div>
        <div class="widget-body match-list">
          <div v-for="match in recentMatches" :key="match.id" class="match-item" @click="goToMatch(match)" style="cursor: pointer;">
            <div class="match-context" :title="getMatchContext(match)">
              {{ getMatchContext(match) }}
            </div>
            <div class="match-meta">
              <span class="round">#{{ match.id }}</span>
              <span class="status" :class="{ 'live-text': match.status === 'ongoing' }">
                {{ match.status === 'completed' ? t('home.finished') : (match.status === 'ongoing' ? t('home.live') : match.start) }}
              </span>
            </div>
            <div class="player-row" :class="{ 'is-winner': match.winner_side === 'side_a' }">
              <div class="p-name"><span class="flag"></span> {{ match.p1_name || t('home.tba') }}</div>
              <div class="p-score">
                <span v-if="match.winner_side === 'side_a'" class="check-icon"><el-icon><Check /></el-icon></span>
                <strong>{{ getScorePart(match.score, 0) }}</strong>
              </div>
            </div>
            <div class="player-row" :class="{ 'is-winner': match.winner_side === 'side_b' }">
              <div class="p-name"><span class="flag"></span> {{ match.p2_name || t('home.tba') }}</div>
              <div class="p-score">
                <span v-if="match.winner_side === 'side_b'" class="check-icon"><el-icon><Check /></el-icon></span>
                <strong>{{ getScorePart(match.score, 1) }}</strong>
              </div>
            </div>
          </div>
          <div v-if="recentMatches.length === 0" class="empty-state">{{ t('home.noMatches') }}</div>
        </div>
      </div>
    </section>

    <section class="container marketing-showcase" v-if="hasHomeBanners">
      <div class="marketing-heading">
        <span>Promotions</span>
        <h2>Banner nổi bật</h2>
      </div>
      <div class="marketing-banner-grid">
        <a
          v-for="(banner, index) in homeBannerItems"
          :key="banner.id"
          class="marketing-banner-card"
          :class="{ 'marketing-banner-card--primary': index === 0 && homeBannerItems.length > 1 }"
          :href="banner.link_url || '#'"
          :target="banner.open_in_new_tab ? '_blank' : '_self'"
          rel="noopener"
          @click="!banner.link_url && $event.preventDefault()"
        >
          <img :src="banner.image_url" :alt="banner.title" class="marketing-banner-img" referrerpolicy="no-referrer" />
          <div class="marketing-banner-content">
            <span>Banner chính</span>
            <strong>{{ banner.title }}</strong>
            <p v-if="banner.subtitle">{{ banner.subtitle }}</p>
          </div>
        </a>
      </div>
    </section>

    <section class="container home-ads-section" v-if="hasHomeAds">
      <div class="home-ads-heading">
        <span>Ads</span>
        <h2>Quảng cáo</h2>
      </div>
      <div class="home-ads-grid">
        <a
          v-for="banner in homeAdItems"
          :key="banner.id"
          class="home-ad-card"
          :href="banner.link_url || '#'"
          :target="banner.open_in_new_tab ? '_blank' : '_self'"
          rel="noopener"
          @click="!banner.link_url && $event.preventDefault()"
        >
          <img :src="banner.image_url" :alt="banner.title" referrerpolicy="no-referrer" />
          <div class="home-ad-content">
            <span>Quảng cáo</span>
            <strong>{{ banner.title }}</strong>
            <p v-if="banner.subtitle">{{ banner.subtitle }}</p>
          </div>
        </a>
      </div>
    </section>

    <section class="container atp-middle-section">
      
      <div class="rankings-widget">
        <div class="widget-header">
          <h3><span class="pif-logo">PIF</span> {{ t('home.rankings') }}</h3>
          <RouterLink to="/rankings" class="view-all">{{ t('home.viewAll') }} <el-icon><Right /></el-icon></RouterLink>
        </div>
        <div class="widget-tabs">
          <span :class="{ active: activeRankingTab === 'singles' }" @click="activeRankingTab = 'singles'" style="cursor: pointer;">{{ t('home.singles') }}</span>
          <span :class="{ active: activeRankingTab === 'doubles' }" @click="activeRankingTab = 'doubles'" style="cursor: pointer;">{{ t('home.doubles') }}</span>
        </div>
        <div class="widget-body ranking-list">
          <div v-for="(player, index) in displayedRankings" :key="player.player_id" class="ranking-row">
            <div class="rank-pos">{{ index + 1 }}</div>
            <div class="rank-name">
              <span class="flag"></span>
              <template v-if="player.isDoublesPair">
                <RouterLink :to="'/players/' + player.p1_user_id" class="player-link" style="color: inherit; text-decoration: none;">{{ player.p1_name }}</RouterLink>
                <span> / </span>
                <RouterLink :to="'/players/' + player.p2_user_id" class="player-link" style="color: inherit; text-decoration: none;">{{ player.p2_name }}</RouterLink>
              </template>
              <template v-else>
                <RouterLink :to="'/players/' + player.player_id" class="player-link" style="color: inherit; text-decoration: none;">{{ player.full_name }}</RouterLink>
              </template>
            </div>
            <div class="rank-pts">{{ player.elo_points }}</div>
          </div>
          <div v-if="displayedRankings.length === 0" class="empty-state">{{ t('home.noRanking') }}</div>
        </div>
      </div>

      <div class="h2h-widget" v-if="h2hData">
        <div class="h2h-header">
          <button class="h2h-nav-btn" @click="shuffleH2H(-1)" :disabled="h2hLoading" title="C\u1eb7p tr\u01b0\u1edbc">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
          <h3>LEXUS <span class="h2h-logo">{{ t('home.h2h') }}</span></h3>
          <button class="h2h-nav-btn" @click="shuffleH2H(1)" :disabled="h2hLoading" title="C\u1eb7p ti\u1ebfp">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        </div>
        <div class="h2h-body">
          <div class="h2h-players">
            
            <div class="h2h-player">
              <div class="h2h-avatar" @click="h2hShowSelectLeft = !h2hShowSelectLeft" style="cursor: pointer;" title="Ch\u1ecdn v\u1eadn \u0111\u1ed9ng vi\u00ean">
                <img :src="h2hData.player1.avatar_url || `https://ui-avatars.com/api/?name=${h2hData.player1.full_name}&background=random`" referrerpolicy="no-referrer" />
                <div class="h2h-avatar-edit">\u270E</div>
              </div>
              <h4 class="h2h-name">{{ h2hData.player1.full_name }}</h4>
              <span class="h2h-loc"> VIE</span>
              <div class="h2h-player-select" v-if="h2hShowSelectLeft">
                <div class="h2h-select-list">
                  <div
                    v-for="p in topPlayers.filter(x => x.player_id !== h2hSelectedRight)"
                    :key="p.player_id"
                    class="h2h-select-item"
                    :class="{ active: p.player_id === h2hSelectedLeft }"
                    @click="selectH2HPlayer('left', p)"
                  >
                    <img :src="p.avatar_url || `https://ui-avatars.com/api/?name=${p.full_name}&background=random&size=28`" referrerpolicy="no-referrer" />
                    <span>{{ p.full_name }}</span>
                    <small>{{ p.elo_points }} pts</small>
                  </div>
                </div>
              </div>
            </div>

            <div class="h2h-score-board">
              <div class="score-number">{{ h2hData.score1 }}</div>
              <div class="vs-circle">VS</div>
              <div class="score-number">{{ h2hData.score2 }}</div>
            </div>

            <div class="h2h-player">
              <div class="h2h-avatar" @click="h2hShowSelectRight = !h2hShowSelectRight" style="cursor: pointer;" title="Ch\u1ecdn v\u1eadn \u0111\u1ed9ng vi\u00ean">
                <img :src="h2hData.player2.avatar_url || `https://ui-avatars.com/api/?name=${h2hData.player2.full_name}&background=random`" referrerpolicy="no-referrer" />
                <div class="h2h-avatar-edit">\u270E</div>
              </div>
              <h4 class="h2h-name">{{ h2hData.player2.full_name }}</h4>
              <span class="h2h-loc"> VIE</span>
              <div class="h2h-player-select" v-if="h2hShowSelectRight">
                <div class="h2h-select-list">
                  <div
                    v-for="p in topPlayers.filter(x => x.player_id !== h2hSelectedLeft)"
                    :key="p.player_id"
                    class="h2h-select-item"
                    :class="{ active: p.player_id === h2hSelectedRight }"
                    @click="selectH2HPlayer('right', p)"
                  >
                    <img :src="p.avatar_url || `https://ui-avatars.com/api/?name=${p.full_name}&background=random&size=28`" referrerpolicy="no-referrer" />
                    <span>{{ p.full_name }}</span>
                    <small>{{ p.elo_points }} pts</small>
                  </div>
                </div>
              </div>
            </div>

          </div>

          <div class="h2h-stats">
            <div class="stat-row">
              <span class="stat-left">{{ h2hData.player1.elo_points || '-' }}</span>
              <span class="stat-label">{{ t('home.eloPoints') }}</span>
              <span class="stat-right">{{ h2hData.player2.elo_points || '-' }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-left">{{ h2hData.player1.wins || 0 }}</span>
              <span class="stat-label">{{ t('home.totalWins') }}</span>
              <span class="stat-right">{{ h2hData.player2.wins || 0 }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-left">{{ h2hData.player1.win_rate || 0 }}%</span>
              <span class="stat-label">{{ t('home.winRate') }}</span>
              <span class="stat-right">{{ h2hData.player2.win_rate || 0 }}%</span>
            </div>
          </div>

          <RouterLink to="/challenges" class="h2h-btn">
            \u26A1 Th\u00e1ch \u0111\u1ea5u ngay <el-icon><Right /></el-icon>
          </RouterLink>
        </div>
      </div>

      <div class="right-widgets">
        <div class="newsletter-widget">
          <h3>{{ t('home.newsletter') }}</h3>
          <p>{{ t('home.newsletterDesc') }}</p>
          <div class="input-group">
            <input type="email" :placeholder="t('home.emailPlaceholder')" />
            <button>{{ t('home.subscribe') }} <el-icon><Message /></el-icon></button>
          </div>
        </div>

        <RouterLink to="/tournaments" class="promo-card shop-card">
          <div class="shop-content">
            <h4>{{ t('home.sgtStore') }}</h4>
            <span class="promo-btn">{{ t('home.shopNow') }} <el-icon><Right /></el-icon></span>
          </div>
        </RouterLink>
      </div>
    </section>

    <section class="container atp-tournaments-section" v-if="featuredTournaments.length > 0">
      <div class="section-header">
        <h2>{{ t('home.featuredTournaments') || 'GIẢI ĐẤU TIÊU BIỂU' }}</h2>
        <RouterLink to="/tournaments" class="view-all-link">{{ t('home.viewAllTournaments') || 'Xem tất cả giải đấu' }} <el-icon><Right /></el-icon></RouterLink>
      </div>
      <div class="tournament-grid">
        <div 
          v-for="tour in featuredTournaments" 
          :key="tour.id" 
          class="tour-card"
          @click="$router.push(`/tournaments/${tour.id}`)"
        >
          <div class="tour-media">
            <img :src="getTournamentImage(tour)" alt="Tournament" referrerpolicy="no-referrer" />
            <div class="tour-status-badge" :class="tour.status">
              <span v-if="tour.status === 'ongoing'" class="pulse-dot"></span>
              {{ getTournamentStatusLabel(tour.status) }}
            </div>
            <div class="tour-location-badge">
              <el-icon><Location /></el-icon> {{ tour.location || 'Hồ Chí Minh' }}
            </div>
          </div>
          <div class="tour-info">
            <h3 class="tour-name">{{ tour.name }}</h3>
            <div class="tour-meta">
              <span class="tour-date">{{ new Date(tour.start_date).toLocaleDateString(currentLocale === 'vi' ? 'vi-VN' : 'en-US') }}</span>
              <span class="tour-type">{{ tour.category_type }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="container atp-news-grid">
      <div class="section-title">
        <h2>{{ t('home.topNews') }}</h2>
      </div>
      
      <div class="news-cards-row">
        <article v-for="news in newsItems.slice(1, 5)" :key="news.id" class="news-card" @click="$router.push('/news/' + news.slug)">
          <div class="card-media">
            <video v-if="isVideo(news.image)" :src="news.image" autoplay muted loop playsinline></video>
            <img v-else :src="news.image" referrerpolicy="no-referrer" />
            <span class="play-icon" v-if="isVideo(news.image)"><el-icon><VideoPlay /></el-icon></span>
          </div>
          <div class="card-body">
            <h3>{{ news.title }}</h3>
          </div>
        </article>
      </div>
    </section>

    <section class="atp-sponsors">
      <div class="container">
        <div class="sponsors-heading">
          <span>Partners</span>
          <h2>Nhà tài trợ & Đối tác</h2>
        </div>
        <div class="sponsor-tiers">
          <div v-for="group in sponsorGroups" :key="group.tier" class="tier">
            <h5>{{ group.label }}</h5>
            <div class="logos">
              <a
                v-for="sponsor in group.items"
                :key="sponsor.id"
                class="sponsor-link"
                :href="sponsor.website_url || '#'"
                :target="sponsor.website_url ? '_blank' : '_self'"
                rel="noopener"
                @click="!sponsor.website_url && $event.preventDefault()"
              >
                <img :src="sponsor.logo_url" :alt="sponsor.name" class="sponsor-img" :class="{ 'premier-img': group.tier === 'premier' }" referrerpolicy="no-referrer">
                <span class="sponsor-name">{{ sponsor.name }}</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<style scoped>
/* =========================================================
   ATP THEME - GLOBAL VARIABLES
========================================================= */
.atp-theme {
  --atp-blue: #002855;
  --atp-blue-light: #003b7a;
  --atp-dark: #0f172a;
  --atp-gray: #f1f5f9;
  --atp-text: #334155;
  background-color: #ffffff;
  color: var(--atp-dark);
  padding-bottom: 0;
  overflow-x: hidden;
}

.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* =========================================================
   TICKER MARQUEE ANIMATION
========================================================= */
.news-ticker {
  background: var(--atp-blue);
  color: white;
  padding: 0.5rem 0;
  overflow: hidden;
  white-space: nowrap;
  border-bottom: 3px solid #c1ff72;
}

.ticker-content {
  display: inline-block;
  animation: ticker-slide 25s linear infinite;
}

.ticker-item {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.ticker-dot {
  color: #c1ff72;
  margin: 0 2rem;
  font-size: 0.8rem;
}

@keyframes ticker-slide {
  0% { transform: translateX(100vw); }
  100% { transform: translateX(-100%); }
}

/* =========================================================
   SECTION 1: HERO & SCORES
========================================================= */
.atp-top-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
  margin-top: 2rem;
  margin-bottom: 3rem;
}

.main-hero-news {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  min-height: 450px;
  display: block;
  color: inherit;
  text-decoration: none;
}

.main-hero-news .hero-media {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  top: 0; left: 0;
  transition: transform 0.5s ease;
}

.main-hero-news:hover .hero-media { transform: scale(1.03); }

.hero-overlay {
  position: absolute; bottom: 0; left: 0; width: 100%;
  padding: 3rem 2rem 2rem;
  background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 100%);
  color: white;
}

.category-badge {
  display: inline-block; background: #c1ff72; color: var(--atp-dark);
  font-size: 0.75rem; font-weight: 700; padding: 0.3rem 0.8rem;
  text-transform: uppercase; margin-bottom: 1rem;
}

.hero-overlay h1 {
  font-size: 2.5rem; font-weight: 700; line-height: 1.2;
  margin: 0; text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

.hero-subtitle {
  max-width: 720px;
  margin: 0.85rem 0 0;
  color: rgba(255,255,255,0.88);
  font-size: 1rem;
  line-height: 1.55;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0,0,0,0.35);
}

.scores-widget, .rankings-widget {
  background: white; border: 1px solid #e2e8f0; border-radius: 8px;
  overflow: hidden; display: flex; flex-direction: column;
}

.widget-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1rem 1.25rem; border-bottom: 1px solid #e2e8f0;
}
.widget-header h3 { font-size: 1.1rem; font-style: italic; font-weight: 800; color: var(--atp-blue); margin: 0; }
.view-all { display: inline-flex; align-items: center; gap: 4px; font-size: 0.8rem; color: var(--atp-blue); text-decoration: none; font-weight: 600; }

.widget-tabs { display: flex; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
.widget-tabs span { flex: 1; text-align: center; padding: 0.75rem 0; font-size: 0.85rem; color: var(--atp-text); font-weight: 600; cursor: pointer; }
.widget-tabs span.active { background: white; color: var(--atp-blue); border-bottom: 2px solid var(--atp-blue); }

.match-list { padding: 0; max-height: 380px; overflow-y: auto; }
.match-item { padding: 1rem 1.25rem; border-bottom: 1px solid #f1f5f9; }
.match-item:last-child { border-bottom: none; }
.match-context {
  margin-bottom: 0.45rem;
  color: var(--atp-blue);
  font-size: 0.78rem;
  font-weight: 800;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.match-meta { display: flex; justify-content: space-between; font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem; font-weight: 600; }
.live-text { color: #dc2626; }
.player-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; font-size: 0.95rem; color: var(--atp-dark); }
.is-winner { font-weight: 700; color: var(--atp-blue); }
.check-icon { color: #16a34a; font-size: 0.9rem; display: inline-flex; align-items: center; }

/* =========================================================
   AD BANNER SECTION
========================================================= */
.marketing-showcase {
  margin-bottom: 3rem;
}

.marketing-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.marketing-heading span {
  color: #16a34a;
  font-size: 0.74rem;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.marketing-heading h2 {
  margin: 0;
  color: var(--atp-dark);
  font-size: 1.35rem;
  font-weight: 900;
}

.marketing-banner-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  grid-auto-flow: dense;
}

.marketing-banner-card {
  position: relative;
  display: block;
  width: 100%;
  min-height: 260px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid #dbe6f3;
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.08);
  background: #0f172a;
  text-decoration: none;
  isolation: isolate;
}

.marketing-banner-card--primary {
  grid-column: span 2;
  min-height: 330px;
}

.marketing-banner-img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  position: absolute;
  inset: 0;
  opacity: 0.86;
  transition: transform 0.35s ease, opacity 0.35s ease;
}
.marketing-banner-card:hover .marketing-banner-img {
  transform: scale(1.03);
  opacity: 0.74;
}
.marketing-banner-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.08), rgba(15, 23, 42, 0.78)),
    linear-gradient(90deg, rgba(15, 23, 42, 0.72), rgba(15, 23, 42, 0.16));
  z-index: 1;
}
.marketing-banner-content {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  max-width: 520px;
  padding: 24px 28px;
  color: #ffffff;
}
.marketing-banner-content span {
  width: fit-content;
  margin-bottom: 10px;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(193, 255, 114, 0.18);
  color: #d9ff8f;
  font-size: 0.72rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.marketing-banner-content strong {
  font-size: clamp(1.35rem, 2.4vw, 2.25rem);
  line-height: 1.12;
  font-weight: 900;
}
.marketing-banner-content p {
  margin: 10px 0 0;
  color: #dbeafe;
  font-size: 0.95rem;
  line-height: 1.55;
}

.home-ads-section {
  margin-bottom: 3rem;
}

.home-ads-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.home-ads-heading span {
  color: #2563eb;
  font-size: 0.74rem;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.home-ads-heading h2 {
  margin: 0;
  color: var(--atp-dark);
  font-size: 1.35rem;
  font-weight: 900;
}

.home-ads-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
}

.home-ad-card {
  position: relative;
  min-height: 170px;
  display: block;
  overflow: hidden;
  border-radius: 12px;
  background: #0f172a;
  color: #ffffff;
  text-decoration: none;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.08);
  isolation: isolate;
}

.home-ad-card img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.home-ad-card:hover img {
  transform: scale(1.04);
  opacity: 0.8;
}

.home-ad-card::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.04), rgba(15, 23, 42, 0.82));
}

.home-ad-content {
  position: absolute;
  inset: auto 0 0 0;
  z-index: 2;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.home-ad-content span {
  width: fit-content;
  padding: 4px 9px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.28);
  color: #bfdbfe;
  font-size: 0.7rem;
  font-weight: 900;
  text-transform: uppercase;
}

.home-ad-content strong {
  font-size: 1.2rem;
  line-height: 1.2;
  font-weight: 900;
}

.home-ad-content p {
  margin: 0;
  color: #dbeafe;
  font-size: 0.88rem;
  line-height: 1.4;
}

/* =========================================================
   SECTION 2: RANKINGS, H2H & NEWSLETTER
========================================================= */
.atp-middle-section {
  display: grid;
  grid-template-columns: 3fr 4fr 3fr;
  gap: 1.5rem;
  margin-bottom: 3rem;
}

/* RANKINGS */
.ranking-row { display: flex; align-items: center; padding: 0.8rem 1.25rem; border-bottom: 1px solid #f1f5f9; }
.rank-pos { width: 30px; font-weight: 700; color: #64748b; }
.rank-name { flex: 1; display: flex; align-items: center; gap: 0.5rem; font-weight: 600; font-size: 0.9rem;}
.rank-pts { font-weight: 700; color: var(--atp-blue); font-size: 0.9rem; }
.pif-logo { background: #000; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; margin-right: 5px; }

/* HEAD-TO-HEAD WIDGET */
.h2h-widget {
  background: #002855;
  border-radius: 8px;
  overflow: hidden;
  color: white;
  display: flex;
  flex-direction: column;
}
.h2h-header {
  padding: 1rem 1.25rem; border-bottom: 1px solid rgba(255,255,255,0.1); text-align: center;
  display: flex; align-items: center; justify-content: space-between;
}
.h2h-header h3 { font-size: 1.1rem; font-style: italic; font-weight: 800; margin: 0; color: #cbd5e1; flex: 1;}
.h2h-logo { color: white; font-size: 1.2rem;}

.h2h-nav-btn {
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); color: #cbd5e1;
  width: 32px; height: 32px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s ease; flex-shrink: 0;
}
.h2h-nav-btn:hover:not(:disabled) { background: rgba(193,255,114,0.2); color: #c1ff72; border-color: #c1ff72; }
.h2h-nav-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.h2h-spinner {
  display: inline-block; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #c1ff72; border-radius: 50%; animation: h2h-spin 0.6s linear infinite;
}
@keyframes h2h-spin { to { transform: rotate(360deg); } }

.h2h-body { padding: 1.5rem; display: flex; flex-direction: column; align-items: center;}
.h2h-players {
  display: flex; align-items: center; justify-content: space-between; width: 100%; margin-bottom: 2rem;
}
.h2h-player { display: flex; flex-direction: column; align-items: center; width: 90px; text-align: center; position: relative;}
.h2h-avatar {
  width: 70px; height: 70px; border-radius: 50%; overflow: hidden; border: 2px solid #c1ff72; margin-bottom: 0.8rem;
  position: relative;
}
.h2h-avatar img { width: 100%; height: 100%; object-fit: cover; }
.h2h-avatar-edit {
  position: absolute; bottom: 0; right: 0;
  width: 22px; height: 22px; border-radius: 50%;
  background: #c1ff72; color: #002855;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
  opacity: 0; transition: opacity 0.2s ease;
  pointer-events: none;
}
.h2h-avatar:hover .h2h-avatar-edit { opacity: 1; }
.h2h-name { font-size: 0.85rem; font-weight: 700; margin: 0 0 4px 0; line-height: 1.2;}
.h2h-loc { font-size: 0.7rem; color: #94a3b8;}

/* H2H PLAYER SELECTOR DROPDOWN */
.h2h-player-select {
  position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
  z-index: 20; margin-top: 6px;
  min-width: 200px;
}
.h2h-select-list {
  background: #0f172a; border: 1px solid rgba(193,255,114,0.25);
  border-radius: 10px; box-shadow: 0 12px 32px rgba(0,0,0,0.5);
  max-height: 260px; overflow-y: auto;
  padding: 6px 0;
}
.h2h-select-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; cursor: pointer;
  transition: background 0.15s ease;
  font-size: 0.82rem; color: #e2e8f0;
}
.h2h-select-item:hover { background: rgba(193,255,114,0.1); }
.h2h-select-item.active { background: rgba(193,255,114,0.18); color: #c1ff72; }
.h2h-select-item img {
  width: 28px; height: 28px; border-radius: 50%; object-fit: cover;
  border: 1px solid rgba(255,255,255,0.15); flex-shrink: 0;
}
.h2h-select-item span { flex: 1; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.h2h-select-item small { color: #94a3b8; font-size: 0.72rem; font-weight: 700; flex-shrink: 0; }

.h2h-score-board { display: flex; align-items: center; gap: 1rem; }
.score-number { font-size: 2.5rem; font-weight: 800; color: #c1ff72; }
.vs-circle {
  width: 32px; height: 32px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.3);
  display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; color: #cbd5e1;
}

.h2h-stats { width: 100%; display: flex; flex-direction: column; gap: 0.8rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 1.5rem; margin-bottom: 1.5rem;}
.stat-row { display: flex; justify-content: space-between; font-size: 0.85rem; }
.stat-label { color: #94a3b8; font-weight: 600; text-transform: uppercase; font-size: 0.75rem;}
.stat-left, .stat-right { font-weight: 700; width: 40px; text-align: center;}

.h2h-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(193,255,114,0.15); border: 1px solid rgba(193,255,114,0.3); color: #c1ff72;
  padding: 0.6rem 1.5rem; border-radius: 20px; font-weight: 700; font-size: 0.8rem; cursor: pointer; transition: 0.2s;
  text-decoration: none;
}
.h2h-btn:hover { background: #c1ff72; color: #002855; }


/* NEWSLETTER & SHOP */
.right-widgets { display: flex; flex-direction: column; gap: 1.5rem; }
.newsletter-widget { background: var(--atp-blue); color: white; padding: 2rem 1.5rem; border-radius: 8px; text-align: center; }
.newsletter-widget h3 { font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem; }
.newsletter-widget p { font-size: 0.85rem; line-height: 1.5; margin-bottom: 1.5rem; opacity: 0.9; }
.input-group { display: flex; flex-direction: column; gap: 0.5rem; }
.input-group input { padding: 0.8rem; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2); background: transparent; color: white; }
.input-group button { display: inline-flex; justify-content: center; align-items: center; gap: 6px; padding: 0.8rem; border-radius: 4px; border: none; background: rgba(255,255,255,0.15); color: white; font-weight: 700; cursor: pointer; transition: 0.2s; }
.input-group button:hover { background: white; color: var(--atp-blue); }

.shop-card { background: url('/src/assets/hero_bg.png') center/cover; border-radius: 8px; color: white; padding: 2rem; position: relative; min-height: 150px; text-decoration: none; display: flex; flex-direction: column; justify-content: center;}
.shop-content h4 { font-size: 1.4rem; font-style: italic; font-weight: 800; margin-bottom: 1rem; }
.promo-btn { display: inline-flex; align-items: center; gap: 4px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; background: rgba(255,255,255,0.2); padding: 0.4rem 1rem; border-radius: 20px; }


/* =========================================================
   SECTION 3: NEWS GRID
========================================================= */
.atp-news-grid { margin-bottom: 4rem; }
.section-title h2 { font-size: 1.5rem; font-weight: 700; color: var(--atp-dark); margin-bottom: 1.5rem; border-bottom: 2px solid var(--atp-blue); padding-bottom: 0.5rem; display: inline-block;}

.news-cards-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; }
.news-card { cursor: pointer; }
.card-media { position: relative; height: 180px; border-radius: 8px; overflow: hidden; margin-bottom: 1rem; }
.card-media img, .card-media video { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s; }
.news-card:hover .card-media img, .news-card:hover .card-media video { transform: scale(1.05); }
.play-icon { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 40px; height: 40px; background: rgba(0,0,0,0.6); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }
.card-body h3 { font-size: 1rem; font-weight: 600; line-height: 1.4; color: var(--atp-dark); }

/* =========================================================
   SECTION 4: SPONSORS (HÌNH ẢNH LOGO) - ĐÃ BỎ HIỆU ỨNG MỜ
========================================================= */
.atp-sponsors {
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-top: 1px solid #e2e8f0;
  padding: 4rem 0;
  text-align: center;
}

.sponsors-heading { margin-bottom: 2.5rem; }
.sponsors-heading span {
  display: inline-block;
  margin-bottom: 8px;
  color: var(--atp-blue);
  font-size: 0.78rem;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.sponsors-heading h2 {
  margin: 0;
  color: var(--atp-dark);
  font-size: clamp(1.4rem, 3vw, 2rem);
  font-weight: 900;
}

.sponsor-tiers { display: flex; flex-direction: column; gap: 2.6rem; }

.tier h5 {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: #94a3b8;
  letter-spacing: 1px;
  margin-bottom: 1.5rem;
}

.logos {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  justify-content: center;
  align-items: center;
  gap: 16px;
}

.sponsor-link {
  min-height: 98px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 18px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #ffffff;
  color: var(--atp-dark);
  text-decoration: none;
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.04);
  transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}
.sponsor-link:hover {
  transform: translateY(-4px);
  border-color: #bfdbfe;
  box-shadow: 0 18px 34px rgba(37, 99, 235, 0.12);
}

.sponsor-img {
  max-height: 54px; 
  max-width: 150px;
  width: 100%;
  object-fit: contain;
}

.premier-img {
  max-height: 78px; 
  max-width: 210px;
}

.sponsor-name {
  max-width: 100%;
  color: #334155;
  font-size: 0.78rem;
  font-weight: 800;
  line-height: 1.25;
  text-align: center;
  overflow-wrap: anywhere;
}

/* =========================================================
   TOURNAMENTS SECTION
========================================================= */
.atp-tournaments-section { margin-bottom: 4rem; }
.atp-tournaments-section .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 2px solid var(--atp-blue); padding-bottom: 0.5rem; }
.atp-tournaments-section h2 { font-size: 1.5rem; font-weight: 700; color: var(--atp-dark); margin: 0; }
.view-all-link { display: flex; align-items: center; gap: 6px; font-size: 0.9rem; color: var(--atp-blue); text-decoration: none; font-weight: 700; transition: 0.2s; }
.view-all-link:hover { color: #c1ff72; }
.tournament-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; }
.tour-card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); cursor: pointer; transition: transform 0.3s ease, box-shadow 0.3s ease; border: 1px solid #e2e8f0; }
.tour-card:hover { transform: translateY(-5px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
.tour-media { position: relative; height: 180px; background: #1e293b; }
.tour-media img { width: 100%; height: 100%; object-fit: cover; }
.tour-status-badge { position: absolute; top: 12px; left: 12px; padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: white; display: flex; align-items: center; gap: 6px; backdrop-filter: blur(4px); }
.tour-status-badge.ongoing { background: rgba(220, 38, 38, 0.9); }
.tour-status-badge.open { background: rgba(22, 163, 74, 0.9); }
.tour-status-badge.finished { background: rgba(100, 116, 139, 0.9); }
.tour-status-badge.pending { background: rgba(37, 99, 235, 0.9); }
.pulse-dot { width: 8px; height: 8px; background: #fff; border-radius: 50%; box-shadow: 0 0 0 rgba(255, 255, 255, 0.4); animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(255, 255, 255, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); } }
.tour-location-badge { position: absolute; bottom: 12px; left: 12px; background: rgba(255,255,255,0.9); color: #0f172a; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; display: flex; align-items: center; gap: 4px; }
.tour-info { padding: 1rem; }
.tour-name { font-size: 1rem; font-weight: 700; color: #1e293b; margin: 0 0 0.5rem 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 2.8rem; line-height: 1.4; }
.tour-meta { display: flex; justify-content: space-between; font-size: 0.75rem; color: #64748b; font-weight: 600; }

/* =========================================================
   RESPONSIVE
========================================================= */
@media (max-width: 1024px) {
  .atp-top-section { grid-template-columns: 1fr; }
  .marketing-banner-card--primary { grid-column: span 1; }
  .atp-middle-section { grid-template-columns: 1fr 1fr; }
  .right-widgets { grid-column: span 2; flex-direction: row; }
  .newsletter-widget, .shop-card { flex: 1; }
  .news-cards-row { grid-template-columns: repeat(2, 1fr); }
  .tournament-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .atp-middle-section { grid-template-columns: 1fr; }
  .right-widgets { flex-direction: column; grid-column: span 1; }
  .hero-overlay h1 { font-size: 1.8rem; }
  .marketing-banner-card,
  .marketing-banner-card--primary { min-height: 230px; }
  .marketing-banner-content { padding: 22px; }
  .logos { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
  .sponsor-link { min-height: 86px; padding: 14px; }
  .sponsor-img { max-height: 40px; } 
  .premier-img { max-height: 62px; }
  .atp-tournaments-section h2 { font-size: 1.2rem; }
}

@media (max-width: 480px) {
  .news-cards-row { grid-template-columns: 1fr; }
  .main-hero-news { min-height: 350px; }
  .marketing-heading { align-items: flex-start; flex-direction: column; }
  .marketing-banner-content strong { font-size: 1.25rem; }
  .h2h-players { gap: 1rem; }
  .score-number { font-size: 2rem; }
  .tournament-grid { grid-template-columns: 1fr; }
  .logos { grid-template-columns: 1fr; }
}

.player-link:hover {
  color: #00b0f0 !important;
  text-decoration: underline !important;
}
</style>
