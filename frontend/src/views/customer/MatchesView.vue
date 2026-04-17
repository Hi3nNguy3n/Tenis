<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Calendar as CalendarIcon, ArrowLeft, ArrowRight, VideoPlay, PieChart } from '@element-plus/icons-vue'
import { tournamentService } from '../../services/tournamentService'
import { newsService } from '../../services/newsService'
import { playerService } from '../../services/playerService'

const router = useRouter()

const loading = ref(false)
const tournamentsWithMatches = ref([])
const latestNews = ref([])
const topPlayers = ref([])

const formatDateKey = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const addDays = (date, days) => {
  const next = new Date(date)
  next.setDate(next.getDate() + days)
  return next
}

const today = new Date()
const todayKey = formatDateKey(today)
const activeDate = ref(todayKey)
const visibleStartDate = ref(addDays(today, -3))

const dateOptions = computed(() => {
  const options = []
  for (let i = 0; i < 6; i += 1) {
    const current = addDays(visibleStartDate.value, i)
    const key = formatDateKey(current)
    options.push({
      value: key,
      label: key === todayKey
        ? 'TODAY'
        : current.toLocaleDateString('en-US', { day: '2-digit', month: 'short' }).toUpperCase(),
    })
  }
  return options
})

const shiftDateRange = (days) => {
  visibleStartDate.value = addDays(visibleStartDate.value, days)
}

const resetToToday = () => {
  activeDate.value = todayKey
  visibleStartDate.value = addDays(today, -3)
}

const openTournamentDetail = (tournamentId) => {
  router.push(`/tournaments/${tournamentId}`)
}

const openReplay = (tournamentId, match) => {
  if (match.status === 'Scheduled') {
    ElMessage.info('Tran nay chua co ket qua de xem lai.')
    return
  }
  router.push(`/tournaments/${tournamentId}`)
}

const openStats = () => {
  router.push('/rankings')
}

const openNewsDetail = (slug) => {
  if (!slug) return
  router.push(`/news/${slug}`)
}

const fetchAllMatchesData = async () => {
  loading.value = true
  try {
    const tours = await tournamentService.getAll({ limit: 20 })

    const brackets = await Promise.all(
      (tours || []).map(async (tournament) => {
        try {
          const matchesData = await tournamentService.getPublicBracket(tournament.id)
          return { tournament, matchesData: matchesData || [] }
        } catch {
          return { tournament, matchesData: [] }
        }
      })
    )

    tournamentsWithMatches.value = brackets
      .filter(({ matchesData }) => matchesData.length > 0)
      .map(({ tournament, matchesData }) => ({
        id: tournament.id,
        name: tournament.name,
        location: tournament.location || 'Vietnam',
        matches: matchesData.map((matchItem) => ({
          id: matchItem.id,
          matchDate: matchItem.start_time ? matchItem.start_time.split('T')[0] : null,
          round: matchItem.round_code,
          time: matchItem.start_time
            ? new Date(matchItem.start_time).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
            : 'TBA',
          status: matchItem.status === 'completed'
            ? 'Finished'
            : (matchItem.status === 'ongoing' ? 'Live' : 'Scheduled'),
          players: [
            {
              name: matchItem.p1_name,
              winner: matchItem.winner_side === 'side_a',
              sets: matchItem.score
                ? matchItem.score.split(',').map((setScore) => setScore.trim().split('-')[0])
                : []
            },
            {
              name: matchItem.p2_name,
              winner: matchItem.winner_side === 'side_b',
              sets: matchItem.score
                ? matchItem.score.split(',').map((setScore) => setScore.trim().split('-')[1])
                : []
            }
          ]
        }))
      }))

    const [news, rankings] = await Promise.all([
      newsService.getAllPosts({ limit: 2 }),
      playerService.getRankings()
    ])

    latestNews.value = news || []
    topPlayers.value = (rankings || []).slice(0, 3)
  } catch (err) {
    console.error('Loi khi tai du lieu tran dau:', err)
    ElMessage.error('Khong the tai du lieu tran dau.')
  } finally {
    loading.value = false
  }
}

const filteredTournaments = computed(() => {
  return tournamentsWithMatches.value
    .map((tournament) => ({
      ...tournament,
      matches: tournament.matches.filter((match) => {
        if (match.matchDate) {
          return match.matchDate === activeDate.value
        }
        return activeDate.value === todayKey
      })
    }))
    .filter((tournament) => tournament.matches.length > 0)
})

onMounted(() => {
  fetchAllMatchesData()
})
</script>

<template>
  <div class="matches-page">
    <div class="matches-subnav">
      <div class="container nav-inner">
        <button class="nav-arrow" @click="shiftDateRange(-1)"><el-icon><ArrowLeft /></el-icon></button>
        <div class="date-strip">
          <button
            v-for="date in dateOptions"
            :key="date.value"
            :class="{ active: activeDate === date.value }"
            @click="activeDate = date.value"
          >
            {{ date.label }}
          </button>
        </div>
        <button class="nav-arrow" @click="shiftDateRange(1)"><el-icon><ArrowRight /></el-icon></button>
        <button class="calendar-btn" @click="resetToToday" title="Back to today">
          <el-icon><CalendarIcon /></el-icon>
        </button>
      </div>
    </div>

    <div class="container main-layout">
      <main class="scores-col" v-loading="loading">
        <div v-for="tournament in filteredTournaments" :key="tournament.id" class="tournament-group">
          <header class="tournament-header">
            <div class="t-title">
              <span class="location">{{ tournament.location }}</span>
              <h2>{{ tournament.name }}</h2>
            </div>
            <div class="t-actions">
              <el-button link @click="openTournamentDetail(tournament.id)">Chi tiet giai</el-button>
            </div>
          </header>

          <div class="match-list">
            <article v-for="match in tournament.matches" :key="match.id" class="atp-match-card">
              <div class="match-info-strip">
                <span class="round">{{ match.round }}</span>
                <span :class="['match-status', match.status.toLowerCase()]">
                  <span v-if="match.status === 'Live'" class="pulse"></span>
                  {{ match.time === 'TBA' && match.status === 'Finished' ? 'Ket thuc' : match.time }}
                </span>
              </div>

              <div class="match-players">
                <div v-for="player in match.players" :key="player.name" class="player-row" :class="{ winner: player.winner }">
                  <div class="player-identity">
                    <span class="player-name">{{ player.name }}</span>
                  </div>
                  <div class="player-scores">
                    <span
                      v-for="(set, idx) in player.sets"
                      :key="idx"
                      class="set-score"
                      :class="{ active: idx === player.sets.length - 1 && match.status === 'Live' }"
                    >
                      {{ set }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="match-actions">
                <button class="m-btn highlight" @click="openReplay(tournament.id, match)"><el-icon><VideoPlay /></el-icon> Xem lai</button>
                <button class="m-btn" @click="openStats"><el-icon><PieChart /></el-icon> Thong ke</button>
              </div>
            </article>
          </div>
        </div>

        <div v-if="!loading && filteredTournaments.length === 0" class="empty-matches">
          <el-empty description="Khong co tran dau cho ngay da chon" />
        </div>
      </main>

      <aside class="sidebar-col">
        <div class="widget">
          <div class="widget-header">
            <h4>Tin Tuc Giai Dau</h4>
          </div>
          <div class="widget-body news-mini-list">
            <div
              v-for="post in latestNews"
              :key="post.id"
              class="news-item-mini"
              @click="openNewsDetail(post.slug)"
            >
              <img :src="post.thumbnail_url || 'https://images.unsplash.com/photo-1595435064214-079678c18789?auto=format&fit=crop&q=80&w=150'" />
              <p>{{ post.title }}</p>
            </div>
          </div>
        </div>

        <div class="widget">
          <div class="widget-header">
            <h4>Xep Hang Elo</h4>
          </div>
          <div class="widget-body">
            <div class="mini-table">
              <div v-for="player in topPlayers" :key="player.player_id" class="tr">
                <span>{{ player.rank }}. {{ player.full_name }}</span>
                <strong>{{ player.elo_points }}</strong>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.matches-page {
  background: #fff;
  min-height: 100vh;
}

.matches-subnav {
  background: #0f172a;
  color: #fff;
  padding: 1.5rem 0;
  margin-top: 80px;
  border-bottom: 2px solid #c1ff72;
}

.nav-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
}

.date-strip {
  display: flex;
  gap: 1.5rem;
}

.date-strip button {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
  font-size: 0.85rem;
  letter-spacing: 1px;
  cursor: pointer;
  padding: 0.5rem 1rem;
  transition: all 0.2s;
  border-radius: 4px;
}

.date-strip button.active {
  background: #c1ff72;
  color: #064e3b;
}

.nav-arrow {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #fff;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
}

.calendar-btn {
  margin-left: 2rem;
  font-size: 1.4rem;
  color: #c1ff72;
  cursor: pointer;
  background: transparent;
  border: none;
}

.main-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 3rem;
  padding-top: 3rem;
  padding-bottom: 6rem;
}

.tournament-group { margin-bottom: 4rem; }

.tournament-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding-bottom: 1rem;
  border-bottom: 2px solid #002855;
  margin-bottom: 1.5rem;
}

.t-title .location {
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  color: var(--text-muted);
  display: block;
}

.t-title h2 {
  font-size: 1.6rem;
  font-weight: 600;
  color: #002855;
  text-transform: uppercase;
}

.t-actions :deep(.el-button) {
  font-weight: 500;
  text-transform: uppercase;
  color: #002855;
}

.match-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1.5rem;
}

.atp-match-card {
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  transition: all 0.2s ease;
}

.atp-match-card:hover {
  border-color: var(--primary);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
}

.match-info-strip {
  background: #f8fafc;
  padding: 0.75rem 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-light);
}

.match-status.live { color: #ba1a1a; display: flex; align-items: center; gap: 0.5rem; }
.pulse { width: 8px; height: 8px; background: #ba1a1a; border-radius: 50%; animation: pulse-live 1.5s infinite; }

@keyframes pulse-live {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(2.5); opacity: 0; }
}

.match-players { padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; flex: 1; }

.player-row { display: flex; justify-content: space-between; align-items: center; }

.player-identity { display: flex; align-items: center; gap: 0.6rem; }
.player-name { font-size: 1.1rem; font-weight: 500; color: #0f172a; }
.player-row.winner .player-name { color: var(--primary); font-weight: 500; }

.player-scores { display: flex; gap: 0.5rem; }
.set-score {
  width: 32px; height: 32px;
  background: #f1f5f9;
  display: flex; align-items: center; justify-content: center;
  font-weight: 500; font-size: 0.9rem;
  color: #334155; border-radius: 4px;
}
.set-score.active { background: #002855; color: #c1ff72; }
.player-row.winner .set-score { background: #dcfce7; color: #166534; }

.match-actions {
  display: flex;
  border-top: 1px solid var(--border-light);
}

.m-btn {
  flex: 1;
  padding: 1rem;
  background: none;
  border: none;
  border-right: 1px solid var(--border-light);
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  color: #002855;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  transition: background 0.2s;
}

.m-btn:last-child { border-right: none; }
.m-btn:hover { background: #f8fafc; }
.m-btn.highlight { color: #ba1a1a; }

.widget { border: 1px solid var(--border-light); border-radius: 4px; margin-bottom: 2rem; overflow: hidden; }
.widget-header { padding: 1.25rem; background: #f8fafc; border-bottom: 1px solid var(--border-light); }
.widget-header h4 { font-size: 0.9rem; font-weight: 500; text-transform: uppercase; color: #002855; }

.news-item-mini {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
}
.news-item-mini img { width: 60px; height: 60px; border-radius: 4px; object-fit: cover; }
.news-item-mini p { font-size: 0.85rem; font-weight: 500; color: #0f172a; line-height: 1.3; }

.mini-table { padding: 0.5rem 1.25rem; }
.tr { display: flex; justify-content: space-between; padding: 0.8rem 0; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem; }
.tr span { font-weight: 600; color: #475569; }
.tr strong { color: #0f172a; }

@media (max-width: 1080px) {
  .main-layout { grid-template-columns: 1fr; }
}

@media (max-width: 480px) {
  .nav-inner { gap: 1rem; }
  .date-strip button { font-size: 0.7rem; padding: 0.4rem 0.6rem; }
  .match-list { grid-template-columns: 1fr; }
  .atp-match-card { width: 100%; }
}
</style>
