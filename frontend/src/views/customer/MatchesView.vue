<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay, PieChart, ArrowRight, ArrowDown, Search, Calendar, Check, Trophy } from '@element-plus/icons-vue'
import { currentLocale, t } from '../../utils/locale'
import { apiClient } from '../../services/apiClient'
import { newsService } from '../../services/newsService'
import { playerService } from '../../services/playerService'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const isVideo = (url) => {
  if (!url) return false
  return url.match(/\.(mp4|webm|ogg)$/i) !== null
}
const loading = ref(false)
const tournamentsWithMatches = ref([])
const latestNews = ref([])
const topPlayers = ref([])
const matchDays = ref(new Set())

// ── Date strip state ─────────────────────────────────────────────
const today = new Date()
const todayKey = formatDateKey(today)
const activeDate = ref(todayKey)
const stripRef = ref(null)

// ── Helpers ──────────────────────────────────────────────────────
function formatDateKey(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function normalizeDateKey(value) {
  if (!value || typeof value !== 'string') return ''
  const m = value.match(/^(\d{4}-\d{2}-\d{2})/)
  return m ? m[1] : value
}

function addDays(date, days) {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}

// ── Generate 90-day strip: 30 days past → today → 60 days future ─
const dateStrip = computed(() => {
  const days = []
  for (let i = -30; i <= 60; i++) {
    const d = addDays(today, i)
    const key = formatDateKey(d)
    days.push({ key, d })
  }
  return days
})

const groupedStrip = computed(() => {
  const groups = []
  let currentMonth = null
  dateStrip.value.forEach(item => {
    const monthKey = item.key.slice(0, 7)
    if (monthKey !== currentMonth) {
      currentMonth = monthKey
      const label = new Date(item.key + 'T12:00:00').toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { month: 'long', year: 'numeric' })
      groups.push({ monthKey, label, days: [] })
    }
    groups[groups.length - 1].days.push(item)
  })
  return groups
})

function scrollToActive() {
  nextTick(() => {
    if (!stripRef.value) return
    const el = stripRef.value.querySelector('.date-item.active')
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
  })
}

function selectDate(key) {
  activeDate.value = key
  scrollToActive()
}

// ── Data fetching ─────────────────────────────────────────────────
const fetchAllMatchesData = async (silent = false) => {
  if (!silent) loading.value = true
  try {
    const raw = await apiClient.get('/api/tournaments/matches/all')
    const normalizedMatches = Array.isArray(raw) ? raw : []

    const buckets = {}
    const days = new Set()

    normalizedMatches.forEach(matchItem => {
      const dateKey = normalizeDateKey(matchItem.date || matchItem.start_time || '')
      if (dateKey) days.add(dateKey)

      const tournamentId = matchItem.tournament_id || matchItem.tournament_name || 'unknown'
      const bucketKey = `${tournamentId}::${dateKey}`

      if (!buckets[bucketKey]) {
        buckets[bucketKey] = {
          id: tournamentId,
          name: matchItem.tournament || matchItem.tournament_name || t('nav.tournaments'),
          location: matchItem.location || 'Vietnam',
          matches: [],
          isOpen: true // Trạng thái đóng/mở group
        }
      }

      buckets[bucketKey].matches.push({
        id: matchItem.id,
        matchDate: dateKey,
        round: matchItem.round_code || matchItem.round || 'TBA',
        time: matchItem.start
          ? matchItem.start
          : matchItem.start_time
            ? new Date(matchItem.start_time).toLocaleTimeString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { hour: '2-digit', minute: '2-digit' })
            : '--:--',
        status: matchItem.status === 'completed'
          ? 'Finished'
          : matchItem.status === 'ongoing' ? 'Live' : 'Scheduled',
        players: [
          {
            name: matchItem.p1_name || matchItem.player_a || matchItem.player1 || t('matches.undetermined'),
            winner: matchItem.winner_side === 'side_a',
            sets: matchItem.score ? matchItem.score.split(',').map(s => s.trim().split('-')[0]) : [],
          },
          {
            name: matchItem.p2_name || matchItem.player_b || matchItem.player2 || t('matches.undetermined'),
            winner: matchItem.winner_side === 'side_b',
            sets: matchItem.score ? matchItem.score.split(',').map(s => s.trim().split('-')[1]) : [],
          },
        ],
      })
    })

    matchDays.value = days
    tournamentsWithMatches.value = Object.values(buckets).filter(t => t.matches.length > 0)

    if (days.size > 0) {
      const sorted = [...days].sort()
      const countOnActive = Object.values(buckets).reduce(
        (sum, t) => sum + t.matches.filter(m => m.matchDate === activeDate.value).length, 0
      )
      if (countOnActive === 0) {
        if (days.has(todayKey)) {
          activeDate.value = todayKey
        } else {
          const future = sorted.find(d => d >= todayKey)
          const past   = [...sorted].reverse().find(d => d < todayKey)
          activeDate.value = future || past || sorted[0]
        }
      }
    }

    scrollToActive()

    const [news, rankings] = await Promise.all([
      newsService.getAllPosts({ limit: 3 }),
      playerService.getRankings(),
    ])
    latestNews.value = news || []
    topPlayers.value = (rankings || []).slice(0, 5)

  } catch (err) {
    console.error('Lỗi khi tải dữ liệu trận đấu:', err)
    if (!silent) ElMessage.error(t('common.errorLoading'))
  } finally {
    if (!silent) loading.value = false
  }
}

const filteredTournaments = computed(() =>
  tournamentsWithMatches.value
    .map(t => ({ ...t, matches: t.matches.filter(m => m.matchDate === activeDate.value) }))
    .filter(t => t.matches.length > 0)
)

const activeDateLabel = computed(() => {
  if (!activeDate.value) return ''
  const d = new Date(`${activeDate.value}T12:00:00`)
  return d.toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { month: 'long', year: 'numeric' })
})

function weekdayLabel(date) {
  const d = new Date(date + 'T12:00:00')
  return d.toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { weekday: 'short' }).replace('.', '').toUpperCase()
}

const toggleGroup = (tId) => {
  const group = tournamentsWithMatches.value.find(t => t.id === tId)
  if (group) group.isOpen = !group.isOpen
}

const openTournamentDetail = (id) => router.push(`/tournaments/${id}`)
const openReplay = (tId, match) => {
  if (match.status === 'Scheduled') { ElMessage.info(t('matches.noReplayYet')); return }
  router.push(`/tournaments/${tId}`)
}
const openStats = () => router.push('/rankings')
const openNewsDetail = (slug) => { if (slug) router.push(`/news/${slug}`) }

let pollingTimer = null

onMounted(async () => {
  authStore.hydrate()
  await fetchAllMatchesData()

  pollingTimer = setInterval(async () => {
    await fetchAllMatchesData(true)
  }, 30_000)
})

onUnmounted(() => {
  if (pollingTimer) clearInterval(pollingTimer)
})
</script>

<template>
  <div class="modern-matches-page">
    
    <div class="neo-date-nav">
      <div class="container nav-inner">
        <button class="neo-btn-today" @click="selectDate(todayKey)">
          <el-icon><Calendar /></el-icon> {{ t('matches.today') }}
        </button>
        <div class="date-strip-wrapper" ref="stripRef">
          <div class="date-strip-track">
            <template v-for="group in groupedStrip" :key="group.monthKey">
              <div class="month-divider">
                <span class="month-label">{{ group.label }}</span>
              </div>
              <button
                v-for="item in group.days"
                :key="item.key"
                :class="[
                  'date-item',
                  { 'is-today': item.key === todayKey },
                  { 'has-data': matchDays.has(item.key) },
                  { 'active': item.key === activeDate },
                ]"
                @click="selectDate(item.key)"
              >
                <span class="d-week">{{ weekdayLabel(item.key) }}</span>
                <span class="d-num">{{ item.d.getDate() }}</span>
                <span class="d-dot" v-if="matchDays.has(item.key)"></span>
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <div class="container neo-layout">
      
      <main class="main-column" v-loading="loading">
        
        <div class="list-header-controls">
          <div class="neo-search-box">
            <el-icon><Search /></el-icon>
            <input type="text" :placeholder="t('matches.searchMatches')" />
          </div>
        </div>

        <div class="group-heading-row">
          <h2 class="active-month-title">
            {{ activeDateLabel }} 
            <span class="badge-count">{{ filteredTournaments.reduce((s, t) => s + t.matches.length, 0) }} {{ t('matches.matchesCount') }}</span>
          </h2>
        </div>

        <div class="tournaments-wrapper">
          
          <div v-for="tournament in filteredTournaments" :key="tournament.id" class="neo-tournament-card">
            
            <div class="tour-banner" @click="toggleGroup(tournament.id)">
              <div class="tb-left">
                <div class="tour-icon-box">
                  <el-icon><Trophy /></el-icon>
                </div>
                <div class="tour-name-info">
                  <h3>{{ tournament.name }}</h3>
                  <span class="tour-loc">{{ tournament.location }} &bull; {{ new Date(activeDate).toLocaleDateString('en-GB') }}</span>
                </div>
              </div>
              <div class="tb-right">
                <el-icon :class="{'rotated': !tournament.isOpen}"><ArrowDown /></el-icon>
              </div>
            </div>

            <div v-show="tournament.isOpen" class="match-list">
              
              <div v-for="match in tournament.matches" :key="match.id" class="neo-match-row">
                
                <div class="col-meta">
                  <span class="m-round">{{ match.round }}</span>
                  <div class="m-status-badge" :class="match.status.toLowerCase()">
                    <span v-if="match.status === 'Live'" class="live-pulse"></span>
                    {{ match.status === 'Live' ? 'LIVE' : match.status === 'Finished' ? 'FT' : match.time }}
                  </div>
                </div>

                <div class="col-players">
                  <div class="p-line" :class="{ 'is-winner': match.players[0].winner }">
                    <div class="p-identity">
                      <span class="flag-mini">🇻🇳</span>
                      <span class="p-name">{{ match.players[0].name }}</span>
                      <el-icon v-if="match.players[0].winner" class="winner-tick"><Check /></el-icon>
                    </div>
                    <div class="p-score-wrap">
                      <span v-for="(s, i) in match.players[0].sets" :key="i" class="p-score">{{ s }}</span>
                    </div>
                  </div>
                  
                  <div class="p-line" :class="{ 'is-winner': match.players[1].winner }">
                    <div class="p-identity">
                      <span class="flag-mini">🇻🇳</span>
                      <span class="p-name">{{ match.players[1].name }}</span>
                      <el-icon v-if="match.players[1].winner" class="winner-tick"><Check /></el-icon>
                    </div>
                    <div class="p-score-wrap">
                      <span v-for="(s, i) in match.players[1].sets" :key="i" class="p-score">{{ s }}</span>
                    </div>
                  </div>
                </div>

                <div class="col-actions">
                  <button class="btn-neo-ghost" @click="openStats">
                     {{ t('matches.statsBtn') }}
                  </button>
                  <button class="btn-neo-solid" @click="openReplay(tournament.id, match)">
                    <el-icon><VideoPlay /></el-icon> {{ t('matches.video') }}
                  </button>
                </div>
              </div>

            </div>
          </div>

          <div v-if="!loading && filteredTournaments.length === 0" class="neo-empty-state">
            <el-empty :description="t('matches.noMatches')" />
          </div>

        </div>
      </main>

      <aside class="sidebar-column">
        
        <div class="neo-widget">
          <div class="w-header">
            <h3>{{ t('matches.news') }}</h3>
            <a href="/news" class="w-link">{{ t('matches.viewAll') }} <el-icon><ArrowRight /></el-icon></a>
          </div>
          <div class="w-body p-0">
            <div class="news-featured" v-if="latestNews.length > 0" @click="openNewsDetail(latestNews[0].slug)">
              <div class="nf-img">
                <img :src="latestNews[0].thumbnail_url || latestNews[0].media_url || '/poster-1.jpg'" />
              </div>
              <div class="nf-content">
                <h4 class="nf-title">{{ latestNews[0].title }}</h4>
              </div>
            </div>
            <div class="news-list">
              <div v-for="post in latestNews.slice(1)" :key="post.id" class="news-list-item" @click="openNewsDetail(post.slug)">
                <div class="nl-thumb">
                  <img :src="post.thumbnail_url || post.media_url || '/poster-1.jpg'" />
                </div>
                <p class="nl-title">{{ post.title }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="neo-widget">
          <div class="w-header">
            <h3>{{ t('matches.sgtStats') }}</h3>
            <a href="/rankings" class="w-link">{{ t('matches.seeAll') }} <el-icon><ArrowRight /></el-icon></a>
          </div>
          <div class="w-subtabs">
            <span class="active">{{ t('matches.points') }}</span>
            <span>{{ t('matches.winRate') }}</span>
          </div>
          <div class="w-body p-0">
            <table class="neo-stats-table">
              <tr v-for="(player, i) in topPlayers" :key="player.player_id">
                <td class="st-rank">#{{ i + 1 }}</td>
                <td class="st-name">{{ player.full_name }}</td>
                <td class="st-val">{{ player.elo_points }}</td>
              </tr>
            </table>
          </div>
        </div>

      </aside>
    </div>
  </div>
</template>

<style scoped>
/* =========================================================
   MODERN CLEAN THEME VARIABLES
========================================================= */
.modern-matches-page {
  --bg-page: #f8fafc;        /* Nền trang sáng, sạch */
  --bg-surface: #ffffff;     /* Nền card trắng tinh */
  --text-main: #0f172a;      /* Chữ đậm */
  --text-muted: #64748b;     /* Chữ nhạt */
  --border-light: #e2e8f0;   /* Viền mềm */
  
  --primary-color: #2563eb;  /* Xanh dương hiện đại */
  --primary-hover: #1d4ed8;
  --live-color: #ef4444;     /* Đỏ tươi cho LIVE */
  
  --shadow-sm: 0 2px 8px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 10px 25px rgba(15, 23, 42, 0.05);

  background: var(--bg-page);
  min-height: 100vh;
  font-family: 'Inter', -apple-system, sans-serif;
  color: var(--text-main);
}

.container {
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* =========================================================
   DATE NAV (NỔI & MƯỢT MÀ)
========================================================= */
.neo-date-nav {
  position: sticky;
  top: 70px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-light);
  box-shadow: 0 4px 20px rgba(0,0,0,0.02);
  margin-bottom: 2rem;
}

.nav-inner {
  display: flex;
  align-items: center;
  height: 80px;
  gap: 1.5rem;
}

.neo-btn-today {
  flex-shrink: 0;
  display: flex; align-items: center; gap: 6px;
  padding: 0.6rem 1.2rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: 99px;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-main);
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: 0.2s;
}
.neo-btn-today:hover { border-color: var(--primary-color); color: var(--primary-color); }

.date-strip-wrapper {
  flex: 1;
  overflow-x: auto;
  scrollbar-width: none;
}
.date-strip-wrapper::-webkit-scrollbar { display: none; }

.date-strip-track {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 1rem;
}

.month-divider {
  display: flex; align-items: center; padding-left: 1rem; margin-right: 0.5rem;
  border-left: 1px solid var(--border-light); height: 40px;
}
.date-strip-track > .month-divider:first-child { border-left: none; padding-left: 0; }

.month-label {
  font-size: 0.75rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase;
}

.date-item {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  width: 54px; height: 60px;
  border: 1px solid transparent; border-radius: 12px;
  background: transparent; color: var(--text-muted);
  cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}
.date-item:hover { background: #f1f5f9; }

.d-week { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; margin-bottom: 2px;}
.d-num { font-size: 1.2rem; font-weight: 800; }
.d-dot { width: 5px; height: 5px; border-radius: 50%; background: #cbd5e1; margin-top: 4px; transition: 0.3s; }

.date-item.has-data .d-num { color: var(--text-main); }
.date-item.has-data .d-dot { background: var(--primary-color); }

.date-item.active { background: var(--primary-color); color: white !important; box-shadow: 0 8px 16px rgba(37,99,235,0.25); transform: translateY(-2px);}
.date-item.active .d-num, .date-item.active .d-week { color: white; }
.date-item.active .d-dot { background: white; }


/* =========================================================
   MAIN LAYOUT
========================================================= */
.neo-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 2.5rem;
  padding-bottom: 4rem;
}

/* ── CỘT TRÁI: DANH SÁCH ────────────────────────────────────────── */
.list-header-controls {
  display: flex; justify-content: flex-end; align-items: center; margin-bottom: 1.5rem;
}

.neo-search-box {
  display: flex; align-items: center; gap: 10px;
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  padding: 10px 18px; border-radius: 99px;
  width: 280px; box-shadow: var(--shadow-sm);
  transition: 0.3s;
}
.neo-search-box:focus-within { border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
.neo-search-box input { border: none; outline: none; width: 100%; font-size: 0.9rem; color: var(--text-main); background: transparent;}
.neo-search-box .el-icon { color: var(--text-muted); font-size: 1.1rem;}

.group-heading-row { margin-bottom: 1.5rem; }
.active-month-title { font-size: 1.4rem; font-weight: 800; margin: 0; display: flex; align-items: center; gap: 12px;}
.badge-count { 
  font-size: 0.75rem; font-weight: 700; color: var(--primary-color); 
  background: #eff6ff; padding: 4px 10px; border-radius: 99px;
}

/* TOURNAMENT CARD (Hiện đại, bo tròn) */
.neo-tournament-card {
  background: var(--bg-surface);
  border-radius: 16px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  margin-bottom: 1.5rem;
  overflow: hidden;
  transition: box-shadow 0.3s;
}
.neo-tournament-card:hover { box-shadow: var(--shadow-md); }

.tour-banner {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1rem 1.5rem; cursor: pointer; background: var(--bg-surface);
  border-bottom: 1px solid var(--border-light);
}
.tb-left { display: flex; align-items: center; gap: 1rem; }
.tour-icon-box {
  width: 44px; height: 44px; background: #f1f5f9; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: var(--primary-color); font-size: 1.4rem;
}
.tour-name-info h3 { margin: 0 0 4px; font-size: 1.1rem; font-weight: 800; color: var(--text-main); }
.tour-loc { font-size: 0.8rem; font-weight: 500; color: var(--text-muted); }
.rotated { transform: rotate(-90deg); }

/* MATCH ROW (Phân vùng rõ ràng) */
.match-list { background: #fdfdfd; }
.neo-match-row {
  display: flex; align-items: stretch; padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #f1f5f9; transition: background 0.2s;
}
.neo-match-row:last-child { border-bottom: none; }
.neo-match-row:hover { background: #f8fafc; }

/* Cột 1: Meta */
.col-meta { 
  width: 130px; display: flex; flex-direction: column; justify-content: center; gap: 8px;
  border-right: 1px solid #f1f5f9; padding-right: 1.5rem;
}
.m-round { font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;}
.m-status-badge {
  display: inline-flex; align-items: center; gap: 6px; align-self: flex-start;
  padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 800;
  background: #f1f5f9; color: var(--text-main);
}
.m-status-badge.live { background: #fee2e2; color: var(--live-color); }
.live-pulse {
  width: 6px; height: 6px; background: var(--live-color); border-radius: 50%;
  animation: pulse 1.5s infinite;
}
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); } 70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }

/* Cột 2: Players */
.col-players { flex: 1; padding: 0 2rem; display: flex; flex-direction: column; justify-content: center; gap: 12px; }
.p-line { display: flex; justify-content: space-between; align-items: center; }
.p-identity { display: flex; align-items: center; gap: 10px; }
.flag-mini { font-size: 1rem; }
.p-name { font-size: 1rem; font-weight: 600; color: var(--text-muted); }
.is-winner .p-name { color: var(--text-main); font-weight: 800; }
.winner-tick { color: #10b981; font-weight: bold; font-size: 1.1rem;}

.p-score-wrap { display: flex; align-items: center; gap: 8px; }
.p-score { 
  font-size: 1rem; font-weight: 600; color: var(--text-muted); 
  width: 24px; text-align: center; background: #f8fafc; border-radius: 4px; padding: 2px 0;
}
.is-winner .p-score { color: var(--text-main); font-weight: 800; background: #eff6ff;}

/* Cột 3: Actions */
.col-actions { 
  width: 140px; display: flex; flex-direction: column; justify-content: center; gap: 10px; 
  border-left: 1px solid #f1f5f9; padding-left: 1.5rem;
}
.btn-neo-ghost {
  background: transparent; border: 1px solid var(--border-light); color: var(--text-muted);
  padding: 8px 0; border-radius: 8px; font-size: 0.8rem; font-weight: 700; cursor: pointer; transition: 0.2s;
}
.btn-neo-ghost:hover { background: var(--bg-page); color: var(--text-main); border-color: var(--text-muted);}

.btn-neo-solid {
  background: #f1f5f9; border: none; color: var(--text-main);
  padding: 8px 0; border-radius: 8px; font-size: 0.8rem; font-weight: 700; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 6px; transition: 0.2s;
}
.btn-neo-solid:hover { background: var(--primary-color); color: white; }


/* ── CỘT PHẢI: WIDGETS ─────────────────────────────────────────── */
.neo-widget {
  background: var(--bg-surface); border-radius: 16px;
  border: 1px solid var(--border-light); box-shadow: var(--shadow-sm); margin-bottom: 2rem; overflow: hidden;
}
.w-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border-light);
}
.w-header h3 { margin: 0; font-size: 1.05rem; font-weight: 800; color: var(--text-main); }
.w-link { font-size: 0.8rem; color: var(--primary-color); font-weight: 700; text-decoration: none; display: flex; align-items: center; gap: 4px;}
.w-link:hover { text-decoration: underline; }

.w-subtabs { display: flex; border-bottom: 1px solid var(--border-light); background: #f8fafc;}
.w-subtabs span {
  flex: 1; text-align: center; padding: 12px 0; font-size: 0.8rem; font-weight: 700; color: var(--text-muted); cursor: pointer; transition: 0.2s;
}
.w-subtabs span.active { color: var(--primary-color); background: var(--bg-surface); border-bottom: 2px solid var(--primary-color); }

/* News Layout */
.news-featured { cursor: pointer; display: flex; flex-direction: column; position: relative;}
.nf-img { width: 100%; height: 200px; }
.nf-img img { width: 100%; height: 100%; object-fit: cover;}
.nf-content { padding: 1.25rem 1.5rem; background: var(--bg-surface); border-bottom: 1px solid var(--border-light);}
.nf-title { margin: 0; font-size: 1.05rem; font-weight: 800; color: var(--text-main); line-height: 1.4;}

.news-list-item {
  display: flex; gap: 16px; padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-light); cursor: pointer; transition: background 0.2s;
}
.news-list-item:hover { background: #f8fafc; }
.news-list-item:last-child { border-bottom: none; }
.nl-thumb { width: 70px; height: 70px; border-radius: 8px; overflow: hidden; flex-shrink: 0; }
.nl-thumb img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s;}
.news-list-item:hover .nl-thumb img { transform: scale(1.05); }
.nl-title { margin: 0; font-size: 0.9rem; font-weight: 600; color: var(--text-main); line-height: 1.4;}

/* Stats Table */
.neo-stats-table { width: 100%; border-collapse: collapse; }
.neo-stats-table td { padding: 1rem 1.5rem; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem; }
.neo-stats-table tr:last-child td { border-bottom: none; }
.st-rank { width: 40px; font-weight: 800; color: var(--text-muted); font-size: 0.8rem;}
.st-name { font-weight: 700; color: var(--text-main); }
.st-val { text-align: right; font-weight: 800; color: var(--primary-color); }


/* ── RESPONSIVE ────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .neo-layout { grid-template-columns: 1fr; }
  .sidebar-column { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
}

@media (max-width: 768px) {
  .sidebar-column { grid-template-columns: 1fr; }
  .list-header-controls { justify-content: flex-start; }
  .neo-search-box { width: 100%; }
  
  .neo-match-row { flex-direction: column; align-items: stretch; gap: 1rem; padding: 1rem;}
  .col-meta { width: 100%; border-right: none; border-bottom: 1px solid var(--border-light); padding-right: 0; padding-bottom: 12px; flex-direction: row; justify-content: space-between; align-items: center;}
  .col-players { padding: 0; }
  .col-actions { width: 100%; border-left: none; border-top: 1px solid var(--border-light); padding-left: 0; padding-top: 12px; flex-direction: row; gap: 12px;}
  .btn-neo-ghost, .btn-neo-solid { flex: 1; padding: 10px 0;}
}
</style>