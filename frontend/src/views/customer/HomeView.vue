<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
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
const isHomeLoading = ref(true)
const isRankingsLoading = ref(false)
const isMarketingBannersLoading = ref(false)
const isHomeAdsLoading = ref(false)
const isSidebarBannersLoading = ref(false)
const isTournamentsLoading = ref(false)
const isSponsorsLoading = ref(false)
const didLoadRankings = ref(false)
const didLoadMarketingBanners = ref(false)
const didLoadHomeAds = ref(false)
const didLoadSidebarBanners = ref(false)
const didLoadTournaments = ref(false)
const didLoadSponsors = ref(false)
const marketingShowcaseRef = ref(null)
const homeAdsRef = ref(null)
const middleSectionRef = ref(null)
const tournamentsSectionRef = ref(null)
const sponsorsSectionRef = ref(null)
const observers = []

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
const h2hSearchKeyword = ref('')
const h2hSearchResults = ref([])
const h2hSearchLoading = ref(false)
let h2hSearchTimer = null
const homeTopBanners = ref([])
const homeAdBanners = ref([])
const homeSidebarNewsletterBanners = ref([])
const homeSidebarStoreBanners = ref([])
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
const homeSidebarNewsletterBanner = computed(() => homeSidebarNewsletterBanners.value[0] || null)
const homeSidebarStoreBanner = computed(() => homeSidebarStoreBanners.value[0] || null)
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
  if (tour.banner_url) return tour.banner_url
  if (tour.media_url) return tour.media_url
  const posters = ['/poster-1.jpg', '/poster-2.jpg', '/poster-3.jpg', '/poster-4.jpg']
  const index = (tour.id || 0) % posters.length
  return posters[index]
}

const hasHomeBanners = computed(() => homeBannerItems.value.length > 0)
const hasHomeAds = computed(() => homeAdItems.value.length > 0)

const parseMatchSets = (match) => {
  const score = String(match?.score_summary || match?.score || match?.result_note || '').trim()
  if (score) {
    const sets = score
      .split(/[,\n;]/)
      .map(part => part.trim())
      .filter(Boolean)
      .map(part => {
        const normalized = part.replace(/[()]/g, '').trim()
        const pieces = normalized.split(/\s*[-:\/]\s*/)
        return pieces.length >= 2 ? { a: pieces[0], b: pieces[1] } : null
      })
      .filter(Boolean)

    if (sets.length) return sets
  }

  const hasFallbackScore =
    match?.score_a !== null && match?.score_a !== undefined &&
    match?.score_b !== null && match?.score_b !== undefined

  return hasFallbackScore ? [{ a: match.score_a, b: match.score_b }] : []
}

const getSetScorePart = (set, sideIndex) => {
  const value = sideIndex === 0 ? set?.a : set?.b
  return value !== null && value !== undefined && String(value).trim() !== '' ? value : '-'
}

const hasRealPlayerName = (name) => {
  const normalized = String(name || '').trim().toLowerCase()
  if (!normalized) return false
  return ![
    'dang cap nhat',
    'dang cap nhat',
    'chua xac dinh',
    'chua xac dinh',
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
  return `${tournament} Â· ${round}`
}

const getMatchStatusPriority = (status) => {
  const normalized = String(status || '').toLowerCase()
  if (normalized === 'ongoing') return 0
  if (normalized === 'completed' || normalized === 'finished') return 1
  return 2
}

const getMatchSortTime = (match) => {
  return match?.start_time || match?.scheduled_at || match?.date || match?.start || ''
}

const processNewsData = (newsData) => {
  if (newsData) {
    rawNewsPosts.value = newsData.sort((a, b) => new Date(b.publish_at || b.created_at) - new Date(a.publish_at || a.created_at))
  }
}

const processRankingsData = (rankingsData) => {
  const filteredRankings = (rankingsData || []).filter(p => !p.full_name?.toLowerCase().includes('admin'))
  rawRankings.value = filteredRankings.map((p, index) => ({
    ...p,
    rank: index + 1
  }))
}

const processMatchesData = (matchesData) => {
  const filteredMatches = (Array.isArray(matchesData) ? matchesData : []).filter(m => {
    const isP1Admin = m.p1_name?.toLowerCase().includes('admin')
    const isP2Admin = m.p2_name?.toLowerCase().includes('admin')
    const status = String(m.status || '').toLowerCase()
    return !isP1Admin && !isP2Admin && hasDisplayableMatchData(m) && ['ongoing', 'completed', 'finished'].includes(status)
  })
  recentMatches.value = filteredMatches
    .sort((a, b) => {
      const priorityA = getMatchStatusPriority(a.status)
      const priorityB = getMatchStatusPriority(b.status)
      if (priorityA !== priorityB) return priorityA - priorityB
      return String(getMatchSortTime(b)).localeCompare(String(getMatchSortTime(a)))
    })
    .slice(0, 5)
}

const processTournamentsData = (toursData) => {
  if (toursData && Array.isArray(toursData)) {
    const statusOrder = { 'ongoing': 0, 'open': 1, 'pending': 2, 'finished': 3 }
    featuredTournaments.value = [...toursData]
      .sort((a, b) => (statusOrder[a.status] ?? 99) - (statusOrder[b.status] ?? 99))
      .slice(0, 4)
  }
}

const initializeH2H = () => {
  if (h2hData.value || h2hLoading.value) return

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
}

const loadTopSection = async () => {
  isHomeLoading.value = true
  Promise.all([
    newsService.getAllPosts({ limit: 5 }),
    apiClient.get('/api/tournaments/matches/all', { params: { limit: 30 } }).catch(() => [])
  ]).then(([newsData, matchesData]) => {
    processNewsData(newsData)
    processMatchesData(matchesData)
  }).catch(err => console.error("Loi tai du lieu Home:", err))
    .finally(() => { isHomeLoading.value = false })
}

const loadRankingsSection = async () => {
  if (didLoadRankings.value || isRankingsLoading.value) return
  isRankingsLoading.value = true
  playerService.getRankings({ limit: 10 }).catch(() => [])
    .then((rankingsData) => {
      processRankingsData(rankingsData)
      didLoadRankings.value = true
      initializeH2H()
    })
    .finally(() => {
      isRankingsLoading.value = false
      observeSection(tournamentsSectionRef, loadTournamentsSection)
    })
}

const loadMarketingBanners = async () => {
  if (didLoadMarketingBanners.value || isMarketingBannersLoading.value) return
  isMarketingBannersLoading.value = true
  apiClient.get('/api/marketing/banners', { params: { placement: 'home_top', limit: 3 } }).catch(() => [])
    .then((homeTopData) => {
      homeTopBanners.value = Array.isArray(homeTopData) ? homeTopData : []
      didLoadMarketingBanners.value = true
    })
    .finally(() => {
      isMarketingBannersLoading.value = false
      observeSection(homeAdsRef, loadHomeAds)
    })
}

const loadHomeAds = async () => {
  if (didLoadHomeAds.value || isHomeAdsLoading.value) return
  isHomeAdsLoading.value = true
  apiClient.get('/api/marketing/banners', { params: { placement: 'home_ad', limit: 3 } }).catch(() => [])
    .then((homeAdData) => {
      homeAdBanners.value = Array.isArray(homeAdData) ? homeAdData : []
      didLoadHomeAds.value = true
    })
    .finally(() => {
      isHomeAdsLoading.value = false
      observeSection(middleSectionRef, () => {
        loadRankingsSection()
        loadSidebarBanners()
      })
    })
}

const loadSidebarBanners = async () => {
  if (didLoadSidebarBanners.value || isSidebarBannersLoading.value) return
  isSidebarBannersLoading.value = true
  Promise.all([
    apiClient.get('/api/marketing/banners', { params: { placement: 'home_sidebar_newsletter', limit: 1 } }).catch(() => []),
    apiClient.get('/api/marketing/banners', { params: { placement: 'home_sidebar_store', limit: 1 } }).catch(() => [])
  ]).then(([sidebarNewsletterData, sidebarStoreData]) => {
    homeSidebarNewsletterBanners.value = Array.isArray(sidebarNewsletterData) ? sidebarNewsletterData : []
    homeSidebarStoreBanners.value = Array.isArray(sidebarStoreData) ? sidebarStoreData : []
    didLoadSidebarBanners.value = true
  }).finally(() => { isSidebarBannersLoading.value = false })
}

const loadTournamentsSection = async () => {
  if (didLoadTournaments.value || isTournamentsLoading.value) return
  isTournamentsLoading.value = true
  apiClient.get('/api/tournaments/', { params: { limit: 4 } }).catch(() => [])
    .then((toursData) => {
      processTournamentsData(toursData)
      didLoadTournaments.value = true
    })
    .finally(() => {
      isTournamentsLoading.value = false
      observeSection(sponsorsSectionRef, loadSponsorsSection)
    })
}

const loadSponsorsSection = async () => {
  if (didLoadSponsors.value || isSponsorsLoading.value) return
  isSponsorsLoading.value = true
  apiClient.get('/api/marketing/sponsors', { params: { limit: 100 } }).catch(() => [])
    .then((sponsorsData) => {
      marketingSponsors.value = Array.isArray(sponsorsData) ? sponsorsData : []
      didLoadSponsors.value = true
    })
    .finally(() => { isSponsorsLoading.value = false })
}

const observeSection = (targetRef, callback) => {
  if (!targetRef.value || typeof IntersectionObserver === 'undefined') {
    callback()
    return
  }

  const observer = new IntersectionObserver((entries) => {
    if (!entries.some(entry => entry.isIntersecting)) return
    callback()
    observer.disconnect()
  }, {
    rootMargin: '240px 0px',
    threshold: 0.01
  })

  observer.observe(targetRef.value)
  observers.push(observer)
}

onMounted(async () => {
  authStore.hydrate()
  loadTopSection()
  observeSection(marketingShowcaseRef, loadMarketingBanners)
})

onBeforeUnmount(() => {
  if (h2hSearchTimer) clearTimeout(h2hSearchTimer)
  observers.forEach(observer => observer.disconnect())
  observers.length = 0
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

const normalizeH2HPlayer = (item) => {
  if (item?.user && item?.player_profile) {
    const matchesPlayed = item.player_profile.matches_played || 0
    return {
      player_id: item.user.id,
      full_name: item.user.full_name,
      avatar_url: item.user.avatar_url,
      elo_points: item.player_profile.elo_points,
      wins: item.player_profile.wins || 0,
      win_rate: matchesPlayed ? Math.round(((item.player_profile.wins || 0) / matchesPlayed) * 100) : 0
    }
  }

  return {
    ...item,
    player_id: item.player_id || item.id,
    elo_points: item.elo_points || 0,
    wins: item.wins || 0,
    win_rate: item.win_rate || 0
  }
}

const openH2HSearch = (side) => {
  h2hShowSelectLeft.value = side === 'left'
  h2hShowSelectRight.value = side === 'right'
  h2hSearchKeyword.value = ''
  h2hSearchResults.value = []
}

const searchH2HPlayers = () => {
  if (h2hSearchTimer) clearTimeout(h2hSearchTimer)
  h2hSearchTimer = setTimeout(async () => {
    const keyword = h2hSearchKeyword.value.trim()
    if (!keyword) {
      h2hSearchResults.value = []
      return
    }

    h2hSearchLoading.value = true
    try {
      const data = await apiClient.get('/api/players/list', { params: { search: keyword, status: 'active' } })
      h2hSearchResults.value = (Array.isArray(data) ? data : [])
        .map(normalizeH2HPlayer)
        .filter(player => player.player_id)
    } catch (err) {
      console.error('H2H player search error:', err)
      h2hSearchResults.value = []
    } finally {
      h2hSearchLoading.value = false
    }
  }, 250)
}

const selectH2HPlayer = (side, player) => {
  const selectedPlayer = normalizeH2HPlayer(player)
  if (side === 'left') {
    h2hSelectedLeft.value = selectedPlayer.player_id
    h2hShowSelectLeft.value = false
    h2hSearchKeyword.value = ''
    h2hSearchResults.value = []
    const rightPlayer = h2hData.value?.player2 || topPlayers.value.find(p => p.player_id === h2hSelectedRight.value)
    if (rightPlayer && selectedPlayer.player_id !== rightPlayer.player_id) {
      loadH2HForPair(selectedPlayer, rightPlayer)
    }
  } else {
    h2hSelectedRight.value = selectedPlayer.player_id
    h2hShowSelectRight.value = false
    h2hSearchKeyword.value = ''
    h2hSearchResults.value = []
    const leftPlayer = h2hData.value?.player1 || topPlayers.value.find(p => p.player_id === h2hSelectedLeft.value)
    if (leftPlayer && leftPlayer.player_id !== selectedPlayer.player_id) {
      loadH2HForPair(leftPlayer, selectedPlayer)
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
      <div v-else-if="isHomeLoading" class="main-hero-news loading-card">
        <div class="loading-content">
          <span class="loading-kicker">Tin tức</span>
          <strong>Đang tải dữ liệu...</strong>
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
          <template v-if="isHomeLoading">
            <div v-for="index in 3" :key="'match-loading-' + index" class="match-item loading-row">
              <div class="loading-line loading-line--wide"></div>
              <div class="loading-line loading-line--short"></div>
              <div class="loading-line"></div>
              <div class="loading-line"></div>
            </div>
          </template>
          <div v-else v-for="match in recentMatches" :key="match.id" class="match-item" @click="goToMatch(match)" style="cursor: pointer;">
            <div class="match-context" :title="getMatchContext(match)">
              {{ getMatchContext(match) }}
            </div>
            <div class="match-meta">
              <span class="round">#{{ match.id }}</span>
              <span class="status" :class="{ 'live-text': match.status === 'ongoing' }">
                {{ ['completed', 'finished'].includes(match.status) ? t('home.finished') : (match.status === 'ongoing' ? t('home.live') : match.start) }}
              </span>
            </div>
            <div class="player-row" :class="{ 'is-winner': match.winner_side === 'side_a' }">
              <div class="p-name"><span class="flag"></span> {{ match.p1_name || t('home.tba') }}</div>
              <div class="p-score">
                <span v-if="match.winner_side === 'side_a'" class="check-icon"><el-icon><Check /></el-icon></span>
                <div class="set-score-list" v-if="parseMatchSets(match).length">
                  <strong
                    v-for="(set, setIndex) in parseMatchSets(match)"
                    :key="`a-${match.id}-${setIndex}`"
                    class="set-score"
                    :class="{ 'is-set-win': Number(getSetScorePart(set, 0)) > Number(getSetScorePart(set, 1)) }"
                  >
                    {{ getSetScorePart(set, 0) }}
                  </strong>
                </div>
                <strong v-else>-</strong>
              </div>
            </div>
            <div class="player-row" :class="{ 'is-winner': match.winner_side === 'side_b' }">
              <div class="p-name"><span class="flag"></span> {{ match.p2_name || t('home.tba') }}</div>
              <div class="p-score">
                <span v-if="match.winner_side === 'side_b'" class="check-icon"><el-icon><Check /></el-icon></span>
                <div class="set-score-list" v-if="parseMatchSets(match).length">
                  <strong
                    v-for="(set, setIndex) in parseMatchSets(match)"
                    :key="`b-${match.id}-${setIndex}`"
                    class="set-score"
                    :class="{ 'is-set-win': Number(getSetScorePart(set, 1)) > Number(getSetScorePart(set, 0)) }"
                  >
                    {{ getSetScorePart(set, 1) }}
                  </strong>
                </div>
                <strong v-else>-</strong>
              </div>
            </div>
          </div>
          <div v-if="!isHomeLoading && recentMatches.length === 0" class="empty-state">{{ t('home.noMatches') }}</div>
        </div>
      </div>
    </section>

    <div ref="marketingShowcaseRef" class="lazy-section-anchor"></div>
    <section class="container marketing-showcase" v-if="isMarketingBannersLoading || hasHomeBanners">
      <div class="marketing-heading">
        <span>Promotions</span>
        <h2>Banner nổi bật</h2>
      </div>
      <div class="marketing-banner-grid">
        <template v-if="isMarketingBannersLoading">
          <div v-for="index in 3" :key="'marketing-loading-' + index" class="marketing-banner-card loading-card"></div>
        </template>
        <a
          v-else
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
            <span>Banner chinh</span>
            <strong>{{ banner.title }}</strong>
            <p v-if="banner.subtitle">{{ banner.subtitle }}</p>
          </div>
        </a>
      </div>
    </section>

    <div ref="homeAdsRef" class="lazy-section-anchor"></div>
    <section class="container home-ads-section" v-if="isHomeAdsLoading || hasHomeAds">
      <div class="home-ads-heading">
        <span>Ads</span>
        <h2>Quảng cáo</h2>
      </div>
      <div class="home-ads-grid">
        <template v-if="isHomeAdsLoading">
          <div v-for="index in 3" :key="'home-ad-loading-' + index" class="home-ad-card loading-card"></div>
        </template>
        <a
          v-else
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

    <div ref="middleSectionRef" class="lazy-section-anchor"></div>
    <section class="container atp-middle-section" v-if="isRankingsLoading || didLoadRankings">
      
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
          <template v-if="isRankingsLoading">
            <div v-for="index in 8" :key="'ranking-loading-' + index" class="ranking-row loading-ranking-row">
              <div class="rank-pos">{{ index }}</div>
              <div class="loading-line loading-line--name"></div>
              <div class="loading-line loading-line--points"></div>
            </div>
          </template>
          <div v-else v-for="(player, index) in displayedRankings" :key="player.player_id" class="ranking-row">
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
          <div v-if="didLoadRankings && displayedRankings.length === 0" class="empty-state">{{ t('home.noRanking') }}</div>
        </div>
      </div>

      <div class="h2h-widget" v-if="h2hData">
        <div class="h2h-header">
          <button class="h2h-nav-btn" @click="shuffleH2H(-1)" :disabled="h2hLoading" title="Cặp trước">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
          <h3>LEXUS <span class="h2h-logo">{{ t('home.h2h') }}</span></h3>
          <button class="h2h-nav-btn" @click="shuffleH2H(1)" :disabled="h2hLoading" title="Cặp tiếp">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        </div>
        <div class="h2h-body">
          <div class="h2h-players">
            <div class="h2h-player">
              <div class="h2h-avatar">
                <img :src="h2hData.player1.avatar_url || `https://ui-avatars.com/api/?name=${h2hData.player1.full_name}&background=random`" referrerpolicy="no-referrer" />
              </div>
              <h4 class="h2h-name">{{ h2hData.player1.full_name }}</h4>
              <span class="h2h-loc"> VIE</span>
            </div>

            <div class="h2h-score-board">
              <div class="score-number">{{ h2hData.score1 }}</div>
              <div class="vs-circle">VS</div>
              <div class="score-number">{{ h2hData.score2 }}</div>
            </div>

            <div class="h2h-player">
              <div class="h2h-avatar">
                <img :src="h2hData.player2.avatar_url || `https://ui-avatars.com/api/?name=${h2hData.player2.full_name}&background=random`" referrerpolicy="no-referrer" />
              </div>
              <h4 class="h2h-name">{{ h2hData.player2.full_name }}</h4>
              <span class="h2h-loc"> VIE</span>
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
            Thách đấu ngay <el-icon><Right /></el-icon>
          </RouterLink>
          <div class="h2h-search-launcher">
            <button
              type="button"
              class="h2h-search-target"
              :class="{ active: h2hShowSelectLeft }"
              @click="openH2HSearch('left')"
            >
              <span>Bên trái</span>
              <strong>{{ h2hData.player1.full_name }}</strong>
            </button>
            <button
              type="button"
              class="h2h-search-main"
              @click="openH2HSearch(h2hShowSelectRight ? 'right' : 'left')"
            >
              <span class="search-icon">⌕</span>
              <span>Tìm vận động viên</span>
            </button>
            <button
              type="button"
              class="h2h-search-target"
              :class="{ active: h2hShowSelectRight }"
              @click="openH2HSearch('right')"
            >
              <span>Bên phải</span>
              <strong>{{ h2hData.player2.full_name }}</strong>
            </button>
          </div>

          <div class="h2h-select-panel" v-if="h2hShowSelectLeft || h2hShowSelectRight">
            <div class="h2h-select-panel-head">
              <span>{{ h2hShowSelectLeft ? 'Tìm vận động viên bên trái' : 'Tìm vận động viên bên phải' }}</span>
              <button type="button" @click="h2hShowSelectLeft = false; h2hShowSelectRight = false">Đóng</button>
            </div>
            <div class="h2h-search-box">
              <input
                v-model="h2hSearchKeyword"
                type="search"
                placeholder="Nhập tên vận động viên..."
                @input="searchH2HPlayers"
              />
            </div>
            <div class="h2h-select-list">
              <div
                v-for="p in h2hSearchResults.filter(x => h2hShowSelectLeft ? x.player_id !== h2hSelectedRight : x.player_id !== h2hSelectedLeft)"
                :key="p.player_id"
                class="h2h-select-item"
                :class="{ active: p.player_id === (h2hShowSelectLeft ? h2hSelectedLeft : h2hSelectedRight) }"
                @click="selectH2HPlayer(h2hShowSelectLeft ? 'left' : 'right', p)"
              >
                <img :src="p.avatar_url || `https://ui-avatars.com/api/?name=${p.full_name}&background=random&size=28`" referrerpolicy="no-referrer" />
                <span>{{ p.full_name }}</span>
                <small>{{ p.elo_points }} pts</small>
              </div>
              <div v-if="h2hSearchLoading" class="h2h-select-empty">Đang tìm kiếm...</div>
              <div v-else-if="h2hSearchKeyword && h2hSearchResults.length === 0" class="h2h-select-empty">Không tìm thấy vận động viên</div>
              <div v-else-if="!h2hSearchKeyword" class="h2h-select-empty">Nhập tên để tìm vận động viên</div>
            </div>
          </div>
        </div>
      </div>
      <div class="h2h-widget h2h-widget--loading" v-else-if="isRankingsLoading">
        <div class="h2h-header">
          <button class="h2h-nav-btn" disabled>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
          <h3>LEXUS <span class="h2h-logo">{{ t('home.h2h') }}</span></h3>
          <button class="h2h-nav-btn" disabled>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        </div>
        <div class="h2h-body">
          <div class="loading-content loading-content--dark">
            <span class="h2h-spinner"></span>
            <strong>Đang tải dữ liệu đối đầu...</strong>
          </div>
        </div>
      </div>

      <div class="right-widgets">
        <!-- Sidebar 1: Newsletter or Custom Banner -->
        <a 
          v-if="homeSidebarNewsletterBanner" 
          :href="homeSidebarNewsletterBanner.link_url || '#'" 
          :target="homeSidebarNewsletterBanner.open_in_new_tab ? '_blank' : '_self'"
          class="sidebar-banner-card"
          @click="!homeSidebarNewsletterBanner.link_url && $event.preventDefault()"
        >
          <img :src="homeSidebarNewsletterBanner.image_url" :alt="homeSidebarNewsletterBanner.title" referrerpolicy="no-referrer" />
          <div class="sidebar-banner-content" v-if="homeSidebarNewsletterBanner.title">
            <h4>{{ homeSidebarNewsletterBanner.title }}</h4>
            <p v-if="homeSidebarNewsletterBanner.subtitle">{{ homeSidebarNewsletterBanner.subtitle }}</p>
          </div>
        </a>
        <div v-else class="newsletter-widget">
          <h3>{{ t('home.newsletter') }}</h3>
          <p>{{ t('home.newsletterDesc') }}</p>
          <div class="input-group">
            <input type="email" :placeholder="t('home.emailPlaceholder')" />
            <button>{{ t('home.subscribe') }} <el-icon><Message /></el-icon></button>
          </div>
        </div>

        <!-- Sidebar 2: SGT Store or Custom Banner -->
        <a 
          v-if="homeSidebarStoreBanner" 
          :href="homeSidebarStoreBanner.link_url || '#'" 
          :target="homeSidebarStoreBanner.open_in_new_tab ? '_blank' : '_self'"
          class="sidebar-banner-card"
          @click="!homeSidebarStoreBanner.link_url && $event.preventDefault()"
        >
          <img :src="homeSidebarStoreBanner.image_url" :alt="homeSidebarStoreBanner.title" referrerpolicy="no-referrer" />
          <div class="sidebar-banner-content" v-if="homeSidebarStoreBanner.title">
            <h4>{{ homeSidebarStoreBanner.title }}</h4>
            <p v-if="homeSidebarStoreBanner.subtitle">{{ homeSidebarStoreBanner.subtitle }}</p>
          </div>
        </a>
        <RouterLink v-else to="/tournaments" class="promo-card shop-card">
          <div class="shop-content">
            <h4>{{ t('home.sgtStore') }}</h4>
            <span class="promo-btn">{{ t('home.shopNow') }} <el-icon><Right /></el-icon></span>
          </div>
        </RouterLink>
      </div>
    </section>

    <div ref="tournamentsSectionRef" class="lazy-section-anchor"></div>
    <section class="container atp-tournaments-section" v-if="isTournamentsLoading || featuredTournaments.length > 0">
      <div class="section-header">
        <h2>{{ t('home.featuredTournaments') || 'Giải đấu tiêu biểu' }}</h2>
        <RouterLink to="/tournaments" class="view-all-link">{{ t('home.viewAllTournaments') || 'Xem tất cả giải đấu' }} <el-icon><Right /></el-icon></RouterLink>
      </div>
      <div class="tournament-grid">
        <template v-if="isTournamentsLoading">
          <div v-for="index in 4" :key="'tour-loading-' + index" class="tour-card loading-tour-card">
            <div class="tour-media"></div>
            <div class="tour-info">
              <div class="loading-line loading-line--wide"></div>
              <div class="loading-line loading-line--short"></div>
            </div>
          </div>
        </template>
        <div 
          v-else
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
        <template v-if="isHomeLoading">
          <article v-for="index in 4" :key="'news-loading-' + index" class="news-card loading-news-card">
            <div class="card-media"></div>
            <div class="card-body">
              <div class="loading-line loading-line--wide"></div>
              <div class="loading-line loading-line--short"></div>
            </div>
          </article>
        </template>
        <article v-else v-for="news in newsItems.slice(1, 5)" :key="news.id" class="news-card" @click="$router.push('/news/' + news.slug)">
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

    <div ref="sponsorsSectionRef" class="lazy-section-anchor"></div>
    <section class="atp-sponsors" v-if="isSponsorsLoading || didLoadSponsors">
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

.lazy-section-anchor {
  width: 100%;
  height: 1px;
  pointer-events: none;
}

.loading-card {
  background: linear-gradient(135deg, #e2e8f0 0%, #f8fafc 45%, #e2e8f0 100%);
  cursor: default;
}

.loading-card::after,
.loading-row::after,
.loading-ranking-row::after,
.loading-tour-card .tour-media::after,
.loading-news-card .card-media::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent);
  transform: translateX(-100%);
  animation: loading-shimmer 1.4s infinite;
}

.loading-content {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 10px;
  padding: 2rem;
  color: var(--atp-blue);
  z-index: 1;
}

.loading-content--dark {
  position: static;
  align-items: center;
  justify-content: center;
  min-height: 230px;
  color: #cbd5e1;
  text-align: center;
}

.loading-kicker {
  width: fit-content;
  padding: 5px 10px;
  background: rgba(0, 40, 85, 0.1);
  color: var(--atp-blue);
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
}

.loading-line {
  height: 12px;
  border-radius: 999px;
  background: #e2e8f0;
}

.loading-line--wide { width: 82%; }
.loading-line--short { width: 48%; }
.loading-line--name { flex: 1; max-width: 180px; }
.loading-line--points { width: 52px; }

.loading-row,
.loading-ranking-row,
.loading-tour-card .tour-media,
.loading-news-card .card-media {
  position: relative;
  overflow: hidden;
}

.loading-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 116px;
}

.loading-ranking-row {
  gap: 12px;
  min-height: 48px;
}

.loading-tour-card,
.loading-news-card {
  cursor: default;
}

.loading-tour-card .tour-media,
.loading-news-card .card-media {
  background: #e2e8f0;
}

@keyframes loading-shimmer {
  100% { transform: translateX(100%); }
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
.player-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 0.75rem; margin-bottom: 0.4rem; font-size: 0.95rem; color: var(--atp-dark); }
.p-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.p-score { display: inline-flex; align-items: center; justify-content: flex-end; gap: 4px; min-width: 72px; }
.set-score-list { display: inline-flex; align-items: center; justify-content: flex-end; gap: 4px; }
.set-score {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 24px;
  border-radius: 5px;
  background: #f1f5f9;
  color: #0f172a;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82rem;
  font-weight: 900;
}
.set-score.is-set-win {
  background: #ecfdf5;
  color: #047857;
}
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
  background:
    radial-gradient(circle at 20% 0%, rgba(37, 99, 235, 0.28), transparent 34%),
    linear-gradient(160deg, #07084f 0%, #002855 54%, #14213d 100%);
  border-radius: 10px;
  color: white;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  box-shadow: 0 18px 42px rgba(0, 40, 85, 0.18);
}
.h2h-widget::before {
  content: '';
  position: absolute;
  inset: 64px 24px auto 24px;
  height: 112px;
  background: repeating-linear-gradient(135deg, rgba(59, 130, 246, 0.22) 0 2px, transparent 2px 24px);
  opacity: 0.6;
  pointer-events: none;
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

.h2h-body { padding: 1.5rem; display: flex; flex-direction: column; align-items: center; position: relative; z-index: 1;}
.h2h-players {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.h2h-player { display: flex; flex-direction: column; align-items: center; min-width: 0; text-align: center; position: relative;}
.h2h-avatar {
  width: 78px; height: 78px; border-radius: 50%; overflow: hidden; border: 2px solid #c1ff72; margin-bottom: 0.8rem;
  position: relative;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.25);
}
.h2h-avatar img { width: 100%; height: 100%; object-fit: cover; }
.h2h-name { width: 100%; min-height: 2.2em; font-size: 0.92rem; font-weight: 800; margin: 0 0 4px 0; line-height: 1.2; overflow-wrap: anywhere;}
.h2h-loc { font-size: 0.7rem; color: #94a3b8;}

.h2h-search-launcher {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(150px, 1.25fr) minmax(0, 1fr);
  gap: 8px;
  padding: 10px;
  border-radius: 999px;
  background: #172236;
  border: 2px solid #c1ff72;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
}
.h2h-search-target,
.h2h-search-main {
  min-width: 0;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.h2h-search-target {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.06);
  color: #cbd5e1;
}
.h2h-search-target span {
  font-size: 0.64rem;
  font-weight: 800;
  text-transform: uppercase;
  color: #94a3b8;
}
.h2h-search-target strong {
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.78rem;
  color: #ffffff;
}
.h2h-search-target.active {
  background: rgba(193, 255, 114, 0.16);
  box-shadow: 0 0 0 1px rgba(193, 255, 114, 0.35);
}
.h2h-search-main {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 14px;
  background: #c1ff72;
  color: #002855;
  font-size: 0.9rem;
  font-weight: 900;
}
.h2h-search-main:hover,
.h2h-search-target:hover {
  transform: translateY(-1px);
}
.search-icon {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #002855;
  color: #c1ff72;
  font-size: 1rem;
  line-height: 1;
}
.h2h-select-panel {
  width: 100%;
  margin-top: 0.9rem;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(193, 255, 114, 0.28);
  background: rgba(15, 23, 42, 0.44);
}
.h2h-select-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}
.h2h-select-panel-head span {
  color: #c1ff72;
  font-size: 0.78rem;
  font-weight: 900;
}
.h2h-select-panel-head button {
  border: none;
  background: transparent;
  color: #cbd5e1;
  font-size: 0.72rem;
  font-weight: 800;
  cursor: pointer;
}
.h2h-search-box {
  margin-bottom: 10px;
}
.h2h-search-box input {
  width: 100%;
  height: 40px;
  border-radius: 10px;
  border: 1px solid rgba(193, 255, 114, 0.35);
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
  padding: 0 12px;
  font-size: 0.86rem;
  font-weight: 700;
  outline: none;
}
.h2h-search-box input::placeholder {
  color: #94a3b8;
}
.h2h-search-box input:focus {
  border-color: #c1ff72;
  box-shadow: 0 0 0 3px rgba(193, 255, 114, 0.14);
}
.h2h-select-list {
  background: rgba(15, 23, 42, 0.96);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(193, 255, 114, 0.35);
  border-radius: 12px;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.7);
  max-height: 280px;
  overflow-y: auto;
  padding: 8px 0;
}
.h2h-select-list::-webkit-scrollbar {
  width: 6px;
}
.h2h-select-list::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}
.h2h-select-list::-webkit-scrollbar-thumb {
  background: rgba(193, 255, 114, 0.3);
  border-radius: 3px;
}
.h2h-select-list::-webkit-scrollbar-thumb:hover {
  background: rgba(193, 255, 114, 0.5);
}
.h2h-select-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.85rem;
  color: #e2e8f0;
}
.h2h-select-item:hover {
  background: rgba(193, 255, 114, 0.12);
  color: #c1ff72;
}
.h2h-select-item.active {
  background: rgba(193, 255, 114, 0.2);
  color: #c1ff72;
  font-weight: 700;
}
.h2h-select-item img {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  border: 1.5px solid rgba(193, 255, 114, 0.3);
  flex-shrink: 0;
}
.h2h-select-item span {
  flex: 1;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.h2h-select-item small {
  color: #c1ff72;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
  background: rgba(193, 255, 114, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}
.h2h-select-empty {
  padding: 14px 16px;
  color: #94a3b8;
  font-size: 0.82rem;
  font-weight: 700;
  text-align: center;
}

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
   SECTION 4: SPONSORS
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
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.sponsor-link {
  min-height: 98px;
  flex: 0 1 220px;
  max-width: 220px;
  min-width: 150px;
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
  .h2h-search-launcher {
    grid-template-columns: 1fr;
    border-radius: 18px;
  }
  .h2h-search-main {
    min-height: 42px;
  }
  .marketing-banner-card,
  .marketing-banner-card--primary { min-height: 230px; }
  .marketing-banner-content { padding: 22px; }
  .logos { gap: 12px; }
  .sponsor-link { flex-basis: calc(50% - 6px); max-width: 220px; min-width: 140px; }
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
  .h2h-players { gap: 0.75rem; }
  .h2h-avatar { width: 64px; height: 64px; }
  .h2h-name { font-size: 0.8rem; }
  .score-number { font-size: 2rem; }
  .tournament-grid { grid-template-columns: 1fr; }
  .sponsor-link { flex-basis: 100%; max-width: 280px; }
}

.player-link:hover {
  color: #00b0f0 !important;
  text-decoration: underline !important;
}

.sidebar-banner-card {
  display: block;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  background: #002855;
  height: 200px;
}
.sidebar-banner-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}
.sidebar-banner-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.sidebar-banner-content {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 60%, rgba(0,0,0,0) 100%);
  padding: 1.25rem 1rem;
  color: white;
  box-sizing: border-box;
  text-align: left;
}
.sidebar-banner-content h4 {
  margin: 0 0 4px 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: white;
}
.sidebar-banner-content p {
  margin: 0;
  font-size: 0.8rem;
  opacity: 0.9;
}
</style>
