<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay, PieChart, ArrowRight, ArrowDown, Search } from '@element-plus/icons-vue'
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
    const el = stripRef.value.querySelector('.date-btn.is-active')
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
    console.error('Loi khi tai du lieu tran dau:', err)
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
  <div class="atp-matches-page">
    
    <!-- THANH ĐIỀU HƯỚNG NGÀY (SÁNG SỦA, GỌN GÀNG) -->
    <div class="clean-date-nav">
      <div class="container nav-inner">
        <button class="btn-today" @click="selectDate(todayKey)">{{ t('matches.today') }}</button>
        <div class="date-strip-wrapper" ref="stripRef">
          <div class="date-strip-track">
            <template v-for="group in groupedStrip" :key="group.monthKey">
              <span class="month-label">{{ group.label }}</span>
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

    <!-- BỐ CỤC CHÍNH (MAIN + SIDEBAR) -->
    <div class="container atp-layout">
      
      <!-- CỘT TRÁI: DANH SÁCH LIST -->
      <main class="main-column" v-loading="loading">
        
        <!-- HEADER CỦA LIST (Như hình: Search & Title) -->
        <div class="list-header-controls">
          <div class="search-box">
            <el-icon><Search /></el-icon>
            <input type="text" placeholder="Search matches..." readonly />
          </div>
          <div class="header-actions">
            <button class="btn-action-solid">All Matches</button>
            <button class="btn-action-solid"><el-icon><Calendar style="margin-right:4px;"/></el-icon> Calendar</button>
          </div>
        </div>

        <div class="group-heading-row">
          <h2 class="active-month-title">
            {{ activeDateLabel }} <span>({{ filteredTournaments.reduce((s, t) => s + t.matches.length, 0) }} matches)</span>
          </h2>
          <el-icon class="collapse-icon"><ArrowDown /></el-icon>
        </div>

        <!-- DANH SÁCH TRẬN ĐẤU DẠNG ROW (HORIZONTAL) -->
        <div class="tournaments-wrapper">
          
          <div v-for="tournament in filteredTournaments" :key="tournament.id" class="atp-tournament-group">
            
            <!-- Tiêu đề Giải Đấu -->
            <div class="group-banner" @click="toggleGroup(tournament.id)">
              <div class="group-banner-left">
                <img src="../../../public/pif.svg" alt="Tour Logo" class="tour-logo" />
                <div class="tour-name-info">
                  <h3>{{ tournament.name }}</h3>
                  <span class="tour-loc">{{ tournament.location }} | {{ new Date(activeDate).toLocaleDateString('en-GB') }}</span>
                </div>
              </div>
              <div class="group-banner-right">
                <el-icon :class="{'rotated': !tournament.isOpen}"><ArrowDown /></el-icon>
              </div>
            </div>

            <!-- Các Dòng Trận Đấu (Rows) -->
            <div v-show="tournament.isOpen" class="match-rows-container">
              
              <div v-for="match in tournament.matches" :key="match.id" class="atp-match-row">
                
                <!-- Cột 1: Meta (Round, Time) -->
                <div class="row-col col-meta">
                  <span class="m-round">{{ match.round }}</span>
                  <span :class="['m-status', match.status.toLowerCase()]">
                    <span v-if="match.status === 'Live'" class="live-dot"></span>
                    {{ match.status === 'Live' ? 'LIVE' : match.status === 'Finished' ? 'FT' : match.time }}
                  </span>
                </div>

                <!-- Cột 2: Players & Score -->
                <div class="row-col col-players">
                  <div class="p-line" :class="{ 'is-winner': match.players[0].winner }">
                    <div class="p-identity">
                      <span class="flag-mini"></span>
                      <span class="p-name">{{ match.players[0].name }}</span>
                    </div>
                    <div class="p-score-wrap">
                      <span v-for="(s, i) in match.players[0].sets" :key="i" class="p-score">{{ s }}</span>
                      <el-icon v-if="match.players[0].winner" class="winner-tick"><Check /></el-icon>
                    </div>
                  </div>
                  <div class="p-line" :class="{ 'is-winner': match.players[1].winner }">
                    <div class="p-identity">
                      <span class="flag-mini"></span>
                      <span class="p-name">{{ match.players[1].name }}</span>
                    </div>
                    <div class="p-score-wrap">
                      <span v-for="(s, i) in match.players[1].sets" :key="i" class="p-score">{{ s }}</span>
                      <el-icon v-if="match.players[1].winner" class="winner-tick"><Check /></el-icon>
                    </div>
                  </div>
                </div>

                <!-- Cột 3: Buttons (Tickets / Results) -->
                <div class="row-col col-actions">
                  <button class="btn-atp-outline" @click="openStats">Thống kê</button>
                  <button class="btn-atp-solid" @click="openReplay(tournament.id, match)">Video <el-icon><ArrowRight /></el-icon></button>
                </div>
              </div>

            </div>
          </div>

          <!-- Trạng thái trống -->
          <div v-if="!loading && filteredTournaments.length === 0" class="empty-list-state">
            <el-empty description="Không có trận đấu nào trong ngày này." />
          </div>

        </div>
      </main>

      <!-- CỘT PHẢI: WIDGETS -->
      <aside class="sidebar-column">
        
        <!-- WIDGET NEWS (Giống ảnh) -->
        <div class="atp-widget">
          <div class="w-header">
            <h3>NEWS</h3>
            <a href="/news" class="w-link">View All <el-icon><ArrowRight /></el-icon></a>
          </div>
          <div class="w-body p-0">
            <!-- Tin lớn đầu tiên -->
            <div class="news-featured" v-if="latestNews.length > 0" @click="openNewsDetail(latestNews[0].slug)">
              <div class="nf-img">
                <img :src="latestNews[0].thumbnail_url || latestNews[0].media_url || 'https://images.unsplash.com/photo-1595435064214-079678c18789?auto=format&fit=crop&q=80&w=400'" />
              </div>
              <h4 class="nf-title">{{ latestNews[0].title }}</h4>
            </div>
            <!-- Các tin nhỏ tiếp theo -->
            <div class="news-list">
              <div v-for="post in latestNews.slice(1)" :key="post.id" class="news-list-item" @click="openNewsDetail(post.slug)">
                <div class="nl-thumb">
                  <img :src="post.thumbnail_url || post.media_url || 'https://images.unsplash.com/photo-1595435064214-079678c18789?auto=format&fit=crop&q=80&w=150'" />
                </div>
                <p class="nl-title">{{ post.title }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- WIDGET STATS (Giống ảnh) -->
        <div class="atp-widget">
          <div class="w-header">
            <h3><span class="brand-text">Infosys</span> SGT STATS</h3>
            <a href="/rankings" class="w-link">See all <el-icon><ArrowRight /></el-icon></a>
          </div>
          <div class="w-subtabs">
            <span class="active">Points</span>
            <span>Win Rate</span>
            <span>Matches</span>
          </div>
          <div class="w-body p-0">
            <table class="stats-table">
              <tr v-for="(player, i) in topPlayers" :key="player.player_id">
                <td class="st-rank">{{ i + 1 }}</td>
                <td class="st-flag"></td>
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
   ATP CALENDAR THEME VARIABLES
========================================================= */
.atp-matches-page {
  --atp-navy: #002855;
  --atp-blue: #0066cc; /* Màu xanh nước biển cho nút */
  --bg-light: #ffffff;
  --bg-gray: #f8fafc;
  --border-color: #e2e8f0;
  
  --text-dark: #0f172a;
  --text-muted: #64748b;
  --text-blue: #0055a4;

  background: var(--bg-light);
  min-height: 100vh;
  font-family: 'Inter', Arial, sans-serif;
}

.container {
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* =========================================================
   DATE NAV (SÁNG SỦA & GỌN GÀNG)
========================================================= */
.clean-date-nav {
  position: sticky;
  top: 75px;
  z-index: 100;
  background: var(--bg-light);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
}

.nav-inner {
  display: flex;
  align-items: center;
  height: 70px;
  gap: 1.5rem;
}

.btn-today {
  flex-shrink: 0;
  padding: 0.4rem 1rem;
  background: var(--bg-gray);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-dark);
  cursor: pointer;
}
.btn-today:hover { background: #e2e8f0; }

.date-strip-wrapper {
  flex: 1;
  overflow-x: auto;
  scrollbar-width: none;
}
.date-strip-wrapper::-webkit-scrollbar { display: none; }

.date-strip-track {
  display: flex;
  align-items: center;
  gap: 4px;
}

.month-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  margin: 0 0.8rem 0 0.5rem;
  padding-left: 0.8rem;
  border-left: 1px solid var(--border-color);
}
.date-strip-track > .month-label:first-child { border-left: none; padding-left: 0; }

.date-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 56px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: 0.2s;
  position: relative;
}
.date-item:hover { background: var(--bg-gray); color: var(--text-dark); }

.d-week { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; margin-bottom: 2px;}
.d-num { font-size: 1.1rem; font-weight: 800; }
.d-dot { width: 4px; height: 4px; border-radius: 50%; background: #cbd5e1; margin-top: 2px; }

.date-item.has-data .d-num { color: var(--text-dark); }
.date-item.has-data .d-dot { background: var(--atp-blue); }

.date-item.active { background: var(--atp-navy); color: white !important; }
.date-item.active .d-num, .date-item.active .d-week { color: white; }
.date-item.active .d-dot { background: white; }


/* =========================================================
   MAIN LAYOUT (2 CỘT)
========================================================= */
.atp-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 2rem;
  padding-top: 2rem;
  padding-bottom: 4rem;
}

/* ── CỘT TRÁI: ROW LIST ────────────────────────────────────────── */
.list-header-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}
.search-box {
  display: flex; align-items: center; gap: 8px;
  border: 1px solid var(--border-color);
  padding: 8px 16px; border-radius: 6px;
  width: 300px; background: var(--bg-light);
}
.search-box input { border: none; outline: none; width: 100%; font-size: 0.85rem; color: var(--text-dark); }
.search-box .el-icon { color: var(--text-muted); }

.header-actions { display: flex; gap: 8px; }
.btn-action-solid {
  background: var(--atp-blue); color: white; border: none;
  padding: 8px 16px; border-radius: 6px; font-size: 0.85rem; font-weight: 700; cursor: pointer;
  display: flex; align-items: center;
}

.group-heading-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 1rem; color: var(--atp-navy);
}
.active-month-title { font-size: 1.1rem; font-weight: 800; margin: 0; }
.active-month-title span { font-weight: 500; font-size: 0.9rem; color: var(--text-muted); }
.collapse-icon { color: var(--atp-blue); font-size: 1.2rem; font-weight: bold;}

/* Tournament Group */
.atp-tournament-group { margin-bottom: 1rem; }
.group-banner {
  display: flex; justify-content: space-between; align-items: center;
  background: var(--bg-gray); padding: 12px 16px;
  border: 1px solid var(--border-color); border-radius: 8px 8px 0 0;
  cursor: pointer;
}
.group-banner-left { display: flex; align-items: center; gap: 12px; }
.tour-logo { width: 40px; height: auto; object-fit: contain;}
.tour-name-info h3 { margin: 0; font-size: 1rem; font-weight: 800; color: var(--text-dark); }
.tour-loc { font-size: 0.75rem; color: var(--text-muted); }
.rotated { transform: rotate(-90deg); transition: 0.3s; }

/* Match Rows */
.match-rows-container {
  border: 1px solid var(--border-color);
  border-top: none;
  border-radius: 0 0 8px 8px;
  background: var(--bg-light);
}

.atp-match-row {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s;
}
.atp-match-row:last-child { border-bottom: none; }
.atp-match-row:hover { background: #f8fafc; }

.row-col { display: flex; flex-direction: column; }

/* Cột 1: Meta */
.col-meta { width: 120px; border-right: 1px solid var(--border-color); padding-right: 1rem; gap: 6px; }
.m-round { font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;}
.m-status { font-size: 0.85rem; font-weight: 700; color: var(--text-dark); }
.m-status.live { color: #dc2626; display: flex; align-items: center; gap: 6px; }
.live-dot { width: 6px; height: 6px; background: #dc2626; border-radius: 50%; }

/* Cột 2: Players */
.col-players { flex: 1; padding: 0 1.5rem; gap: 8px; }
.p-line { display: flex; justify-content: space-between; align-items: center; }
.p-identity { display: flex; align-items: center; gap: 8px; }
.flag-mini { font-size: 0.9rem; }
.p-name { font-size: 0.95rem; font-weight: 600; color: var(--text-muted); }
.is-winner .p-name { color: var(--text-dark); font-weight: 800; }

.p-score-wrap { display: flex; align-items: center; gap: 6px; min-width: 60px; justify-content: flex-end;}
.p-score { font-size: 0.95rem; font-weight: 600; color: var(--text-muted); width: 16px; text-align: center;}
.is-winner .p-score { color: var(--text-dark); font-weight: 800; }
.winner-tick { color: #16a34a; font-weight: bold; margin-left: 4px; font-size: 1.1rem;}

/* Cột 3: Actions */
.col-actions { width: 130px; gap: 8px; border-left: 1px solid var(--border-color); padding-left: 1rem;}
.btn-atp-outline {
  border: 1px solid var(--atp-blue); color: var(--atp-blue); background: transparent;
  padding: 6px 12px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; cursor: pointer; transition: 0.2s;
}
.btn-atp-outline:hover { background: var(--bg-gray); }

.btn-atp-solid {
  border: none; background: var(--atp-blue); color: white;
  padding: 6px 12px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 4px; transition: 0.2s;
}
.btn-atp-solid:hover { background: #0055a4; }


/* ── CỘT PHẢI: WIDGETS ─────────────────────────────────────────── */
.atp-widget {
  border: 1px solid var(--border-color);
  background: var(--bg-light);
  border-radius: 8px;
  margin-bottom: 2rem;
  overflow: hidden;
}
.w-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1rem; border-bottom: 1px solid var(--border-color);
}
.w-header h3 { margin: 0; font-size: 1rem; font-weight: 800; color: var(--atp-navy); }
.brand-text { font-style: italic; color: #00b0f0; }
.w-link { font-size: 0.75rem; color: var(--atp-blue); font-weight: 700; text-decoration: none; display: flex; align-items: center; gap: 2px;}

.w-subtabs {
  display: flex; border-bottom: 1px solid var(--border-color);
}
.w-subtabs span {
  flex: 1; text-align: center; padding: 10px 0; font-size: 0.8rem; font-weight: 600; color: var(--text-muted); cursor: pointer;
}
.w-subtabs span.active { color: var(--atp-blue); border-bottom: 2px solid var(--atp-blue); }

.p-0 { padding: 0 !important; }

/* News Layout */
.news-featured { cursor: pointer; border-bottom: 1px solid var(--border-color); }
.nf-img { width: 100%; height: 160px; }
.nf-img img { width: 100%; height: 100%; object-fit: cover;}
.nf-title { padding: 1rem; margin: 0; font-size: 0.95rem; font-weight: 700; color: var(--text-dark); line-height: 1.4;}

.news-list-item {
  display: flex; gap: 12px; padding: 1rem;
  border-bottom: 1px solid var(--border-color); cursor: pointer;
}
.news-list-item:last-child { border-bottom: none; }
.nl-thumb { width: 60px; height: 60px; border-radius: 4px; overflow: hidden; flex-shrink: 0; }
.nl-thumb img { width: 100%; height: 100%; object-fit: cover;}
.nl-title { margin: 0; font-size: 0.85rem; font-weight: 600; color: var(--text-body); line-height: 1.3;}

/* Stats Table */
.stats-table { width: 100%; border-collapse: collapse; }
.stats-table td { padding: 12px 1rem; border-bottom: 1px solid var(--border-color); font-size: 0.85rem; }
.st-rank { width: 30px; font-weight: 700; color: var(--text-muted); }
.st-flag { width: 30px; }
.st-name { font-weight: 600; color: var(--text-dark); }
.st-val { text-align: right; font-weight: 800; color: var(--atp-navy); }


/* ── RESPONSIVE ────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .atp-layout { grid-template-columns: 1fr; }
  .sidebar-column { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
}

@media (max-width: 768px) {
  .sidebar-column { grid-template-columns: 1fr; }
  .list-header-controls { flex-direction: column; gap: 1rem; align-items: flex-start; }
  .search-box { width: 100%; }
  
  .atp-match-row { flex-direction: column; align-items: stretch; gap: 12px;}
  .col-meta { width: 100%; border-right: none; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; flex-direction: row; justify-content: space-between;}
  .col-players { padding: 0; }
  .col-actions { width: 100%; border-left: none; border-top: 1px solid var(--border-color); padding-left: 0; padding-top: 12px; flex-direction: row; }
  .btn-atp-outline, .btn-atp-solid { flex: 1; }
}
</style>