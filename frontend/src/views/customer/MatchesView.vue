<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay, PieChart, ArrowLeft as ArrowLeftIcon, ArrowRight as ArrowRightIcon } from '@element-plus/icons-vue'
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
const stripRef = ref(null)   // ref to the scrollable strip element

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

// Group strip days by month for headers
const groupedStrip = computed(() => {
  const groups = []
  let currentMonth = null
  dateStrip.value.forEach(item => {
    const monthKey = item.key.slice(0, 7) // "YYYY-MM"
    if (monthKey !== currentMonth) {
      currentMonth = monthKey
      const label = new Date(item.key + 'T12:00:00').toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { month: 'long', year: 'numeric' })
      groups.push({ monthKey, label, days: [] })
    }
    groups[groups.length - 1].days.push(item)
  })
  return groups
})

// Scroll the active date button into view
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
// silent=true: chạy ngầm (auto-refresh) - không làm giật UI, không show lỗi
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

    // Chọn ngày thông minh: luôn nhảy đến ngày có trận
    if (days.size > 0) {
      const sorted = [...days].sort()
      // Đếm số trận thực tế trên ngày đang active
      const countOnActive = Object.values(buckets).reduce(
        (sum, t) => sum + t.matches.filter(m => m.matchDate === activeDate.value).length, 0
      )
      if (countOnActive === 0) {
        // Ngày hiện tại không có trận → nhảy đến ngày phù hợp nhất
        // 1. Ưu tiên ngày hôm nay nếu có trận
        if (days.has(todayKey)) {
          activeDate.value = todayKey
        } else {
          // 2. Tìm ngày gần nhất trong tương lai có trận
          const future = sorted.find(d => d >= todayKey)
          // 3. Nếu không có tương lai thì lấy ngày gần nhất trong quá khứ
          const past   = [...sorted].reverse().find(d => d < todayKey)
          activeDate.value = future || past || sorted[0]
        }
      }
    }

    scrollToActive()


    const [news, rankings] = await Promise.all([
      newsService.getAllPosts({ limit: 2 }),
      playerService.getRankings(),
    ])
    latestNews.value = news || []
    topPlayers.value = (rankings || []).slice(0, 3)

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
  if (activeDate.value === todayKey)
    return t('matches.today') + ' — ' + d.toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' })
  return d.toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' })
})

const matchCountForDay = (key) =>
  tournamentsWithMatches.value.reduce((sum, t) => sum + t.matches.filter(m => m.matchDate === key).length, 0)

// Weekday abbrev (T2…CN)
function weekdayLabel(date) {
  const d = new Date(date + 'T12:00:00')
  return d.toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { weekday: 'short' }).replace('.', '').toUpperCase()
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

  // Tự động cập nhật mỗi 30 giây — khi admin thêm trận, bên khách hiện liền
  pollingTimer = setInterval(async () => {
    await fetchAllMatchesData(true)
  }, 30_000)
})

onUnmounted(() => {
  if (pollingTimer) clearInterval(pollingTimer)
})
</script>

<template>
  <div class="matches-page">

    <!-- ── Sticky date nav bar ───────────────────────────────── -->
    <div class="date-nav-bar">
      <div class="date-nav-inner">

        <!-- Today button -->
        <button class="today-pill" @click="selectDate(todayKey)">{{ t('matches.today') }}</button>

        <!-- Scrollable strip grouped by month -->
        <div class="strip-scroll-wrap" ref="stripRef">
          <div class="strip-track">
            <template v-for="group in groupedStrip" :key="group.monthKey">
              <!-- Month divider -->
              <span class="month-divider">{{ group.label }}</span>
              <!-- Day buttons -->
              <button
                v-for="item in group.days"
                :key="item.key"
                :id="'dbtn-' + item.key"
                :class="[
                  'date-btn',
                  { 'is-today': item.key === todayKey },
                  { 'has-matches': matchDays.has(item.key) },
                  { 'is-active': item.key === activeDate },
                ]"
                @click="selectDate(item.key)"
              >
                <span class="btn-wd">{{ weekdayLabel(item.key) }}</span>
                <span class="btn-day">{{ item.d.getDate() }}</span>
                <span v-if="matchDays.has(item.key)" class="btn-dot"></span>
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Page content ──────────────────────────────────────── -->
    <div class="container main-layout">

      <!-- LEFT: Matches col -->
      <main class="main-col">

        <!-- Date label + count -->
        <div class="date-heading">
          <h2>{{ activeDateLabel }}</h2>
          <span v-if="filteredTournaments.length > 0" class="match-count-badge">
            {{ filteredTournaments.reduce((s, t) => s + t.matches.length, 0) }} {{ t('matches.match') }}
          </span>
        </div>

        <!-- Match list for active date -->
        <div v-loading="loading">
          <div v-for="tournament in filteredTournaments" :key="tournament.id" class="tournament-group">
            <header class="tournament-header">
              <div class="t-title">
                <span class="location">{{ tournament.location }}</span>
                <h3>{{ tournament.name }}</h3>
              </div>
              <el-button link @click="openTournamentDetail(tournament.id)">{{ t('common.details') }} →</el-button>
            </header>

            <div class="match-list">
              <article v-for="match in tournament.matches" :key="match.id" class="match-card">
                <div class="match-info-strip">
                  <span class="round-badge">{{ match.round }}</span>
                  <span :class="['match-status', match.status.toLowerCase()]">
                    <span v-if="match.status === 'Live'" class="pulse"></span>
                    {{ match.status === 'Live' ? t('common.live') : match.status === 'Finished' ? t('matches.final') : match.time }}
                  </span>
                </div>

                <div class="match-players">
                  <div
                    v-for="player in match.players"
                    :key="player.name"
                    class="player-row"
                    :class="{ winner: player.winner }"
                  >
                    <div class="player-identity">
                      <span class="winner-icon" v-if="player.winner">🏆</span>
                      <span class="player-name">{{ player.name }}</span>
                    </div>
                    <div class="player-scores">
                      <span
                        v-for="(set, idx) in player.sets"
                        :key="idx"
                        class="set-score"
                        :class="{ active: idx === player.sets.length - 1 && match.status === 'Live' }"
                      >{{ set }}</span>
                    </div>
                  </div>
                </div>

                <div class="match-actions">
                  <button class="m-btn highlight" @click="openReplay(tournament.id, match)">
                    <el-icon><VideoPlay /></el-icon> {{ t('matches.replay') }}
                  </button>
                  <button class="m-btn" @click="openStats">
                    <el-icon><PieChart /></el-icon> {{ t('matches.stats') }}
                  </button>
                </div>
              </article>
            </div>
          </div>

          <!-- Empty state -->
          <div v-if="!loading && filteredTournaments.length === 0" class="empty-state">
            <div class="empty-icon">📅</div>
            <p class="empty-title">{{ t('matches.noMatches') }}</p>
            <p class="empty-sub">
              {{ matchDays.size === 0
                  ? t('matches.noScheduleYet')
                  : t('matches.selectDayHint') }}
            </p>
            <div v-if="matchDays.size > 0" class="quick-days">
              <p>{{ t('matches.nearestDays') }}:</p>
              <button
                v-for="day in [...matchDays].sort().slice(0, 6)"
                :key="day"
                class="quick-day-btn"
                @click="selectDate(day)"
              >
                {{ new Date(day + 'T12:00:00').toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { day: '2-digit', month: '2-digit' }) }}
              </button>
            </div>
          </div>
        </div>
      </main>

      <!-- RIGHT: Sidebar -->
      <aside class="sidebar-col">
        <!-- Tin tức -->
        <div class="widget">
          <div class="widget-header"><h4>{{ t('matches.tournamentNews') }}</h4></div>
          <div class="widget-body">
            <div
              v-for="post in latestNews"
              :key="post.id"
              class="news-item-mini"
              @click="openNewsDetail(post.slug)"
            >
              <video 
                v-if="isVideo(post.media_url || post.thumbnail_url)" 
                :src="post.media_url || post.thumbnail_url" 
                autoplay muted loop playsinline
              ></video>
              <img 
                v-else 
                :src="post.thumbnail_url || post.media_url || 'https://images.unsplash.com/photo-1595435064214-079678c18789?auto=format&fit=crop&q=80&w=150'" 
              />
              <p>{{ post.title }}</p>
            </div>
            <p v-if="latestNews.length === 0" class="empty-widget">{{ t('common.noNews') }}</p>
          </div>
        </div>

        <!-- Xếp hạng -->
        <div class="widget">
          <div class="widget-header"><h4>{{ t('matches.eloRankings') }}</h4></div>
          <div class="widget-body">
            <div v-for="(player, i) in topPlayers" :key="player.player_id" class="rank-row">
              <span class="rank-no" :class="`rank-${i+1}`">{{ i + 1 }}</span>
              <span class="rank-name">{{ player.full_name }}</span>
              <strong class="rank-elo">{{ player.elo_points }}</strong>
            </div>
            <p v-if="topPlayers.length === 0" class="empty-widget">{{ t('common.noData') }}</p>
          </div>
        </div>

        <!-- Các ngày có trận -->
        <div class="widget" v-if="matchDays.size > 0">
          <div class="widget-header"><h4>{{ t('matches.matchDays') }}</h4></div>
          <div class="widget-body all-match-days">
            <button
              v-for="day in [...matchDays].sort()"
              :key="day"
              :class="['match-day-pill', { active: day === activeDate }]"
              @click="selectDate(day)"
            >
              {{ new Date(day + 'T12:00:00').toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { day: '2-digit', month: '2-digit', year: 'numeric' }) }}
              <span class="pill-count">{{ matchCountForDay(day) }}</span>
            </button>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
/* ── Base ──────────────────────────────────────────────────────── */
.matches-page {
  background: #f4f6f9;
  min-height: 100vh;
}

/* ── Layout ─────────────────────────────────────────────────────── */
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 2rem;
}
.main-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 2.5rem;
  padding-top: 2.5rem;
  padding-bottom: 6rem;
}

/* ═══════════════════════════════════════════════════════════════
   DATE NAV BAR  (sticky, spans full width, dark like ATP/ESPN)
   ═══════════════════════════════════════════════════════════════ */
.date-nav-bar {
  position: sticky;
  top: 80px;          /* below site header */
  z-index: 200;
  background: #0f172a;
  border-bottom: 3px solid #c1ff72;
  box-shadow: 0 4px 18px rgba(0,0,0,.35);
}

.date-nav-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1.5rem;
  display: flex;
  align-items: stretch;
  gap: 1rem;
  height: 76px;
}

/* "Hôm nay" button on left */
.today-pill {
  flex-shrink: 0;
  align-self: center;
  padding: 0.4rem 1.1rem;
  border: 2px solid #c1ff72;
  border-radius: 20px;
  background: transparent;
  color: #c1ff72;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}
.today-pill:hover { background: #c1ff72; color: #0f172a; }

/* Scrollable strip container */
.strip-scroll-wrap {
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;   /* Firefox */
}
.strip-scroll-wrap::-webkit-scrollbar { display: none; }

/* Inner track – flex row, no wrapping */
.strip-track {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 100%;
  padding: 0 0.25rem;
  white-space: nowrap;
}

/* Month separator label */
.month-divider {
  flex-shrink: 0;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: rgba(255,255,255,.35);
  padding: 0 0.75rem 0 1rem;
  border-left: 1px solid rgba(255,255,255,.12);
  margin: 0 0.25rem;
}
.strip-track > .month-divider:first-child { border-left: none; padding-left: 0; }

/* Individual day button */
.date-btn {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  width: 54px;
  height: 56px;
  border: none;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  color: rgba(255,255,255,.55);
  transition: background 0.15s, color 0.15s;
  position: relative;
}
.date-btn:hover {
  background: rgba(255,255,255,.08);
  color: #fff;
}

.btn-wd {
  font-size: 0.6rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  line-height: 1;
}
.btn-day {
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1;
}
.btn-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #c1ff72;
  margin-top: 1px;
}

/* Today */
.date-btn.is-today .btn-day {
  background: rgba(193,255,114,.15);
  border-radius: 4px;
  padding: 2px 6px;
  color: #c1ff72;
}
.date-btn.is-today .btn-wd { color: #c1ff72; }

/* Has matches */
.date-btn.has-matches .btn-day { color: rgba(255,255,255,.9); }

/* Active / selected */
.date-btn.is-active {
  background: #c1ff72 !important;
  border-radius: 8px;
}
.date-btn.is-active .btn-wd,
.date-btn.is-active .btn-day { color: #0f172a !important; font-weight: 700; }
.date-btn.is-active .btn-dot { background: #0f172a; }

/* ── Date heading ───────────────────────────────────────────────── */
.date-heading {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.date-heading h2 {
  font-size: 1.2rem;
  font-weight: 700;
  color: #0f172a;
  text-transform: capitalize;
}
.match-count-badge {
  background: #146250;
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.2rem 0.7rem;
  border-radius: 20px;
}

/* ── Tournament group ───────────────────────────────────────────── */
.tournament-group {
  margin-bottom: 3rem;
}
.tournament-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 1rem 1.25rem;
  background: #fff;
  border-radius: 10px 10px 0 0;
  border-bottom: 3px solid #146250;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.t-title .location {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #94a3b8;
  letter-spacing: 1px;
  display: block;
}
.t-title h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0.2rem 0 0;
}

/* ── Match list ─────────────────────────────────────────────────── */
.match-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 1rem;
  padding: 1rem 0;
}
.match-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
  box-shadow: 0 1px 4px rgba(0,0,0,.04);
}
.match-card:hover {
  border-color: #146250;
  box-shadow: 0 4px 16px rgba(20,98,80,.12);
  transform: translateY(-2px);
}

.match-info-strip {
  background: #f8fafc;
  padding: 0.6rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f1f5f9;
}
.round-badge {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #475569;
  letter-spacing: 1px;
  background: #e2e8f0;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
}
.match-status {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
}
.match-status.live { color: #dc2626; display: flex; align-items: center; gap: 0.4rem; }
.match-status.finished { color: #146250; }
.pulse {
  width: 8px; height: 8px;
  background: #dc2626;
  border-radius: 50%;
  animation: pulse-anim 1.5s infinite;
}
@keyframes pulse-anim {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(2.5); opacity: 0; }
}

.match-players { padding: 1.25rem 1rem; display: flex; flex-direction: column; gap: 0.85rem; flex: 1; }
.player-row { display: flex; justify-content: space-between; align-items: center; }
.player-identity { display: flex; align-items: center; gap: 0.5rem; }
.winner-icon { font-size: 0.85rem; }
.player-name { font-size: 1rem; font-weight: 500; color: #334155; }
.player-row.winner .player-name { color: #146250; font-weight: 700; }

.player-scores { display: flex; gap: 0.4rem; }
.set-score {
  width: 30px; height: 30px;
  background: #f1f5f9;
  display: flex; align-items: center; justify-content: center;
  font-weight: 600; font-size: 0.85rem;
  color: #475569; border-radius: 4px;
}
.set-score.active { background: #0f172a; color: #c1ff72; }
.player-row.winner .set-score { background: #dcfce7; color: #166534; }

.match-actions { display: flex; border-top: 1px solid #f1f5f9; }
.m-btn {
  flex: 1; padding: 0.85rem;
  background: none; border: none;
  border-right: 1px solid #f1f5f9;
  font-size: 0.72rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.5px;
  color: #475569; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 0.4rem;
  transition: background 0.18s, color 0.18s;
}
.m-btn:last-child { border-right: none; }
.m-btn:hover { background: #f8fafc; color: #146250; }
.m-btn.highlight { color: #dc2626; }
.m-btn.highlight:hover { background: #fff5f5; }

/* ── Empty state ────────────────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.empty-icon { font-size: 3rem; margin-bottom: 1rem; }
.empty-title { font-size: 1.2rem; font-weight: 700; color: #334155; margin: 0 0 0.5rem; }
.empty-sub { font-size: 0.9rem; color: #94a3b8; margin: 0 0 1.5rem; }
.quick-days { margin-top: 1rem; }
.quick-days p { font-size: 0.8rem; color: #64748b; margin-bottom: 0.75rem; }
.quick-day-btn {
  display: inline-block; margin: 0.25rem;
  padding: 0.4rem 1rem; border: 2px solid #146250;
  border-radius: 20px; background: transparent;
  color: #146250; font-weight: 600; font-size: 0.82rem;
  cursor: pointer; transition: all 0.2s;
}
.quick-day-btn:hover { background: #146250; color: #fff; }

/* ── Media Queries ────────────────────────────────────────────── */
@media (max-width: 1080px) {
  .main-layout { grid-template-columns: 1fr; gap: 2rem; padding: 1.5rem 1rem; }
  .sidebar-col { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
  .widget { margin-bottom: 0; }
}

@media (max-width: 768px) {
  .date-nav-bar { top: 56px; } /* Phù hợp với header mobile nhỏ hơn */
  .date-nav-inner { padding: 0 0.75rem; height: 68px; gap: 0.5rem; }
  .today-pill { padding: 0.3rem 0.8rem; font-size: 0.72rem; border-width: 1.5px; }
  
  .date-heading h2 { font-size: 1rem; }
  .match-count-badge { font-size: 0.65rem; padding: 0.1rem 0.5rem; }

  .tournament-header { flex-direction: column; align-items: flex-start; gap: 0.75rem; padding: 1rem; }
  .tournament-header .el-button { padding: 0; }

  .match-list { grid-template-columns: 1fr; }
  .match-card { border-radius: 12px; }
  .match-players { padding: 1rem; gap: 0.75rem; }
  .player-name { font-size: 0.9rem; }
  .set-score { width: 26px; height: 26px; font-size: 0.75rem; }
  
  .m-btn { padding: 0.75rem; font-size: 0.68rem; }
}

@media (max-width: 480px) {
  .date-nav-inner { gap: 0.25rem; }
  .today-pill { display: none; } /* Ẩn nút hôm nay trên màn hình quá nhỏ để dành chỗ cho lịch */
  
  .sidebar-col { grid-template-columns: 1fr; }
  .t-title h3 { font-size: 1rem; }
  .match-info-strip { padding: 0.5rem 0.75rem; }
  .round-badge { font-size: 0.6rem; padding: 0.15rem 0.4rem; }
}

/* ── Sidebar widgets ────────────────────────────────────────────── */
.widget {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 6px rgba(0,0,0,.06);
  margin-bottom: 1.5rem;
  overflow: hidden;
}
.widget-header {
  padding: 1rem 1.25rem;
  background: #f8fafc;
  border-bottom: 2px solid #146250;
}
.widget-header h4 {
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #0f172a;
  margin: 0;
}
.widget-body { padding: 0.75rem 0; }

.news-item-mini {
  display: flex; gap: 0.75rem;
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer; transition: background 0.15s;
}
.news-item-mini:last-child { border-bottom: none; }
.news-item-mini:hover { background: #f8fafc; }
.news-item-mini img,
.news-item-mini video { 
  width: 80px !important; 
  height: 80px !important; 
  border-radius: 8px; 
  object-fit: cover; 
  flex-shrink: 0; 
  display: block;
  background: #000;
}
.news-item-mini p { font-size: 0.82rem; font-weight: 500; color: #334155; line-height: 1.4; margin: 0; }

.rank-row {
  display: flex; align-items: center;
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid #f8fafc;
  gap: 0.75rem;
}
.rank-row:last-child { border-bottom: none; }
.rank-no {
  width: 24px; height: 24px; border-radius: 50%;
  background: #e2e8f0; color: #475569;
  font-size: 0.75rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.rank-1 { background: #fef9c3; color: #854d0e; }
.rank-2 { background: #f1f5f9; color: #475569; }
.rank-3 { background: #ffedd5; color: #9a3412; }
.rank-name { flex: 1; font-size: 0.85rem; font-weight: 600; color: #1e293b; }
.rank-elo { font-size: 0.85rem; color: #146250; font-weight: 800; }

.all-match-days { padding: 0.5rem 1rem 1rem; }
.match-day-pill {
  display: flex; justify-content: space-between; align-items: center;
  width: 100%; padding: 0.6rem 1rem; margin-bottom: 0.4rem;
  border: 1px solid #f1f5f9; border-radius: 8px;
  background: #fff; font-size: 0.8rem; font-weight: 600;
  color: #475569; cursor: pointer; transition: all 0.2s;
}
.match-day-pill:hover, .match-day-pill.active {
  background: #146250; color: #fff; border-color: #146250;
}
.pill-count {
  font-size: 0.7rem; background: #e2e8f0; color: #475569;
  padding: 2px 6px; border-radius: 10px;
}
.match-day-pill.active .pill-count { background: #c1ff72; color: #0f172a; }
</style>
