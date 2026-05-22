<script setup>
import { onMounted, ref, computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { currentLocale, t } from '../../utils/locale'
import { ElMessage } from 'element-plus'
import {
  Trophy,
  Location,
  ArrowLeft,
  Star,
  DataLine,
  Medal,
  Right,
  VideoPlay
} from '@element-plus/icons-vue'
import { apiClient } from '../../services/apiClient'
import { newsService } from '../../services/newsService'

const route = useRoute()
const router = useRouter()
const playerId = route.params.id

const playerData = ref(null)
const matchHistory = ref([])
const tournaments = ref([])
const rawNewsPosts = ref([])
const isLoading = ref(true)
const activeTab = ref('overview')

const profile = computed(() => playerData.value?.player_profile || {})
const user = computed(() => playerData.value?.user || {})

const stats = computed(() => {
  const p = profile.value
  const total = (p.wins || 0) + (p.losses || 0)
  const winRate = total > 0 ? Math.round((p.wins / total) * 100) : 0
  return { total, winRate }
})

const isVideo = (url) => {
  if (!url) return false
  return /\.(mp4|webm|ogg)$/i.test(url)
}

const newsItems = computed(() => {
  return rawNewsPosts.value.map(post => ({
    id: post.id,
    slug: post.slug || post.id,
    title: post.title,
    date: new Date(post.publish_at || post.created_at).toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US'),
    category: t('players.tennisNews'),
    excerpt: post.summary,
    image: post.media_url || post.thumbnail_url || 'https://images.unsplash.com/photo-1595435934249-5df7ed86e1f4?auto=format&fit=crop&q=80&w=800'
  }))
})

const featuredNews = computed(() => newsItems.value[0])
const sideNews = computed(() => newsItems.value.slice(1, 4))

onMounted(async () => {
  try {
    const [profileRes, historyRes, tourRes, newsRes] = await Promise.all([
      apiClient.get(`/api/players/${playerId}`),
      apiClient.get(`/api/players/${playerId}/history`),
      apiClient.get(`/api/players/${playerId}/tournaments`),
      newsService.getAllPosts({ limit: 6 }).catch(() => [])
    ])

    playerData.value = profileRes
    matchHistory.value = historyRes || []
    tournaments.value = tourRes || []
    rawNewsPosts.value = (newsRes || []).sort((a, b) => new Date(b.publish_at || b.created_at) - new Date(a.publish_at || a.created_at))
  } catch (err) {
    console.error(err)
    ElMessage.error(t('common.errorLoading'))
    router.push('/players')
  } finally {
    isLoading.value = false
  }
})

const formatGender = (gender) => {
  if (!gender) return t('profile.notSpecified') || 'N/A'
  const g = gender.toLowerCase()
  if (g === 'male' || g === 'nam') return t('profile.male')
  if (g === 'female' || g === 'nu') return t('profile.female')
  return gender
}

const formatPlayHand = (hand) => {
  if (hand === 'right') return t('profile.right')
  if (hand === 'left') return t('profile.left')
  if (hand === 'both') return t('profile.both')
  return t('profile.notUpdated')
}

const getResultType = (status) => {
  if (status === 'THẮNG' || status === 'THáº®NG') return 'win'
  if (status === 'THUA') return 'loss'
  return 'pending'
}

const getResultLabel = (status) => {
  const type = getResultType(status)
  if (type === 'win') return t('players.resultWin')
  if (type === 'loss') return t('players.resultLoss')
  return t('players.resultTbd')
}

const tabs = [
  { key: 'overview', labelKey: 'players.profileOverview' },
  { key: 'bio', labelKey: 'players.profileBio' },
  { key: 'activity', labelKey: 'players.profileActivity' },
  { key: 'stats', labelKey: 'players.profileStats' },
  { key: 'ranking', labelKey: 'players.profileRanking' }
]
</script>

<template>
  <div class="player-profile-page" v-loading="isLoading">
    <section class="profile-hero" v-if="playerData">
      <div class="hero-court"></div>
      <div class="container hero-inner">
        <button class="back-btn" @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>
          {{ t('common.back') }}
        </button>

        <div class="hero-layout">
          <div class="hero-copy">
            <div class="eyebrow">{{ t('players.playerEyebrow') }}</div>
            <h1>{{ user.full_name }}</h1>
            <div class="player-meta">
              <span><el-icon><Location /></el-icon>{{ user.province || t('players.defaultLocation') }}</span>
              <span><el-icon><Trophy /></el-icon>{{ profile.skill_level || t('players.unranked') }}</span>
              <span><el-icon><Medal /></el-icon>{{ profile.preferred_category || t('players.singles') }}</span>
            </div>
          </div>

          <div class="player-portrait">
            <img :src="user.avatar_url || 'https://ui-avatars.com/api/?background=05205c&color=fff&name=' + encodeURIComponent(user.full_name)" alt="Avatar" />
          </div>
        </div>

        <div class="score-panel">
          <div class="mode-tabs">
            <button class="mode-tab active">{{ t('players.singles') }}</button>
            <button class="mode-tab">{{ t('players.doubles') }}</button>
          </div>
          <div class="score-grid">
            <div class="score-label">{{ t('players.ytd') }}</div>
            <div class="score-stat"><b>#{{ profile.rank || '--' }}</b><span>{{ t('players.rank') }}</span></div>
            <div class="score-stat"><b>{{ profile.wins || 0 }} - {{ profile.losses || 0 }}</b><span>{{ t('players.winLoss') }}</span></div>
            <div class="score-stat"><b>{{ stats.winRate }}%</b><span>{{ t('players.winRate') }}</span></div>
            <div class="score-stat"><b>{{ profile.elo_points || 1000 }}</b><span>ELO</span></div>
          </div>
          <div class="score-grid career">
            <div class="score-label">{{ t('players.career') }}</div>
            <div class="score-stat"><b>{{ profile.matches_played || stats.total }}</b><span>{{ t('players.matchesCount') }}</span></div>
            <div class="score-stat"><b>{{ tournaments.length }}</b><span>{{ t('players.tournaments') }}</span></div>
            <div class="score-stat"><b>{{ profile.wins || 0 }}</b><span>{{ t('players.wins') }}</span></div>
            <div class="score-stat"><b>{{ profile.losses || 0 }}</b><span>{{ t('players.losses') }}</span></div>
          </div>
        </div>
      </div>
    </section>

    <div class="tab-shell" v-if="playerData">
      <div class="container">
        <nav class="profile-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ t(tab.labelKey) }}
          </button>
        </nav>
      </div>
    </div>

    <div class="container content-grid" v-if="playerData">
      <main class="main-column">
        <section v-if="activeTab === 'overview'" class="content-card">
          <div class="section-head">
            <h2>{{ t('players.personalDetails') }}</h2>
            <span></span>
          </div>
          <div class="detail-grid">
            <div class="detail-item"><label>{{ t('profile.gender') }}</label><p>{{ formatGender(profile.gender) }}</p></div>
            <div class="detail-item"><label>{{ t('profile.province') }}</label><p>{{ user.province || t('profile.notUpdated') }}</p></div>
            <div class="detail-item"><label>{{ t('profile.playHand') }}</label><p>{{ formatPlayHand(profile.play_hand) }}</p></div>
            <div class="detail-item"><label>{{ t('profile.phone') }}</label><p>{{ user.phone || t('profile.notUpdated') }}</p></div>
            <div class="detail-item"><label>{{ t('profile.height') }}</label><p>{{ profile.height_cm ? `${profile.height_cm} cm` : t('profile.notUpdated') }}</p></div>
            <div class="detail-item"><label>{{ t('profile.weight') }}</label><p>{{ profile.weight_kg ? `${profile.weight_kg} kg` : t('profile.notUpdated') }}</p></div>
          </div>
        </section>

        <section v-else-if="activeTab === 'bio'" class="content-card">
          <div class="section-head">
            <h2>{{ t('players.biography') }}</h2>
            <span></span>
          </div>
          <p class="bio-text">{{ profile.bio || t('players.emptyBio') }}</p>
        </section>

        <section v-else-if="activeTab === 'activity'" class="content-card">
          <div class="section-head">
            <h2>{{ t('players.playerActivity') }}</h2>
            <span></span>
          </div>
          <div class="match-list">
            <div v-for="match in matchHistory" :key="match.id" class="match-item" :class="getResultType(match.result_status)">
              <div class="result-pill">{{ getResultLabel(match.result_status) }}</div>
              <div class="match-detail">
                <strong>{{ match.tournament_name }}</strong>
                <div class="teams-line">{{ match.my_team?.name }} <span>{{ t('players.versus') }}</span> {{ match.opponent_team?.name }}</div>
                <small>{{ match.round }} · {{ match.time }}</small>
              </div>
              <div class="score-pill">{{ match.score }}</div>
            </div>
            <el-empty v-if="!matchHistory.length" :description="t('profile.noMatchData')" />
          </div>
        </section>

        <section v-else-if="activeTab === 'stats'" class="content-card">
          <div class="section-head">
            <h2>{{ t('players.profileStats') }}</h2>
            <span></span>
          </div>
          <div class="stats-board">
            <div><el-icon><DataLine /></el-icon><b>{{ stats.total }}</b><span>{{ t('players.matchesCount') }}</span></div>
            <div><el-icon><Trophy /></el-icon><b>{{ profile.wins || 0 }}</b><span>{{ t('players.wins') }}</span></div>
            <div><el-icon><Star /></el-icon><b>{{ stats.winRate }}%</b><span>{{ t('players.winRate') }}</span></div>
          </div>
        </section>

        <section v-else class="content-card">
          <div class="section-head">
            <h2>{{ t('players.profileRanking') }}</h2>
            <span></span>
          </div>
          <div class="ranking-panel">
            <strong>#{{ profile.rank || '--' }}</strong>
            <p>{{ t('players.rankingDescription') }}</p>
            <div>{{ profile.elo_points || 1000 }} {{ t('players.eloPoints') }}</div>
          </div>
        </section>
      </main>

      <aside class="side-column">
        <section class="content-card compact news-panel">
          <div class="side-heading">
            <h3>{{ t('players.relatedNews') }}</h3>
            <RouterLink to="/news" class="view-all-link">{{ t('players.viewAll') }} <el-icon><Right /></el-icon></RouterLink>
          </div>

          <RouterLink v-if="featuredNews" :to="`/news/${featuredNews.slug}`" class="featured-news">
            <video v-if="isVideo(featuredNews.image)" :src="featuredNews.image" autoplay muted loop playsinline></video>
            <img v-else :src="featuredNews.image" alt="" referrerpolicy="no-referrer" />
            <span v-if="isVideo(featuredNews.image)" class="play-icon"><el-icon><VideoPlay /></el-icon></span>
            <div>
              <span>{{ featuredNews.category }}</span>
              <h4>{{ featuredNews.title }}</h4>
              <small>{{ featuredNews.date }}</small>
            </div>
          </RouterLink>

          <div class="news-mini-list">
            <RouterLink v-for="news in sideNews" :key="news.id" :to="`/news/${news.slug}`" class="news-mini-row">
              <img :src="news.image" alt="" referrerpolicy="no-referrer" />
              <div>
                <p>{{ news.title }}</p>
                <small>{{ news.date }}</small>
              </div>
            </RouterLink>
            <el-empty v-if="!newsItems.length" :description="t('players.updatingPosts')" />
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.player-profile-page {
  --navy: #12355b;
  --navy-2: #28537a;
  --cyan: #2f80a7;
  --lime: #c6ff4a;
  --ink: #05052f;
  --muted: #64748b;
  --line: #d8e0ee;
  --surface: #f7f9fc;
  min-height: 100vh;
  background: var(--surface);
  color: var(--ink);
}

.container {
  max-width: 1180px;
  margin: 0 auto;
  padding: 0 24px;
}

.profile-hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(90deg, #12355b 0%, #244f76 56%, #74b8cf 100%);
  color: #fff;
  padding: 30px 0 0;
}

.hero-court {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(18, 53, 91, 0.88), rgba(32, 75, 112, 0.66) 55%, rgba(116, 184, 207, 0.16)),
    url('/src/assets/hero_bg.png') center/cover;
  opacity: 0.82;
}

.hero-inner {
  position: relative;
  z-index: 1;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(255,255,255,0.24);
  background: rgba(255,255,255,0.08);
  color: #fff;
  border-radius: 4px;
  padding: 9px 14px;
  cursor: pointer;
  font-weight: 700;
}

.hero-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  align-items: end;
  gap: 48px;
  min-height: 260px;
}

.eyebrow {
  color: var(--lime);
  font-size: 0.75rem;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.hero-copy h1 {
  margin: 0 0 18px;
  color: #fff;
  font-size: clamp(2.2rem, 6vw, 4.7rem);
  line-height: 0.95;
  font-weight: 900;
  text-transform: uppercase;
}

.player-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 18px;
  color: rgba(255,255,255,0.86);
  font-weight: 700;
}

.player-meta span {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.player-portrait {
  height: 300px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.player-portrait img {
  width: 260px;
  height: 260px;
  object-fit: cover;
  border-radius: 50%;
  border: 8px solid rgba(255,255,255,0.2);
  box-shadow: 0 22px 60px rgba(0,0,0,0.34);
}

.score-panel {
  width: min(100%, 820px);
  border: 1px solid rgba(90, 177, 210, 0.42);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 34px;
  background: rgba(18, 53, 91, 0.56);
  backdrop-filter: blur(8px);
}

.mode-tabs {
  display: flex;
}

.mode-tab {
  min-width: 132px;
  border: 0;
  border-right: 1px solid rgba(255,255,255,0.18);
  background: #cbd5e1;
  color: var(--navy);
  padding: 13px 22px;
  font-weight: 900;
  cursor: pointer;
}

.mode-tab.active {
  background: var(--navy);
  color: #fff;
}

.score-grid {
  display: grid;
  grid-template-columns: 120px repeat(4, 1fr);
  border-top: 1px solid rgba(90, 177, 210, 0.36);
}

.score-label,
.score-stat {
  min-height: 76px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 12px 18px;
  border-right: 1px solid rgba(90, 177, 210, 0.36);
}

.score-label {
  font-size: 1.1rem;
  font-weight: 900;
  text-transform: uppercase;
}

.score-stat {
  align-items: center;
  text-align: center;
}

.score-stat b {
  font-size: 1.55rem;
  line-height: 1;
}

.score-stat span {
  margin-top: 6px;
  color: rgba(255,255,255,0.78);
  font-size: 0.82rem;
}

.tab-shell {
  background: #fff;
  border-bottom: 1px solid var(--line);
}

.profile-tabs {
  display: flex;
  overflow-x: auto;
}

.profile-tabs button {
  border: 0;
  background: #2f80a7;
  color: #fff;
  min-width: 112px;
  padding: 17px 22px;
  font-weight: 900;
  cursor: pointer;
}

.profile-tabs button.active {
  background: #fff;
  color: #2f6f92;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 28px;
  padding-top: 32px;
  padding-bottom: 56px;
}

.content-card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 28px;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.05);
}

.content-card.compact {
  padding: 22px;
  margin-bottom: 22px;
}

.side-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 18px;
}

.content-card h3 {
  margin: 0 0 18px;
  color: var(--navy);
  text-transform: uppercase;
}

.side-heading h3 {
  margin: 0;
}

.view-all-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #2f6f92;
  font-size: 0.82rem;
  font-weight: 800;
  text-decoration: none;
  white-space: nowrap;
}

.section-head h2 {
  margin: 0;
  color: var(--navy);
  font-size: 1.7rem;
}

.section-head span {
  display: block;
  width: 70px;
  height: 3px;
  background: #2f80a7;
  margin: 12px 0 26px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 28px;
}

.detail-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  background: #f3f6f9;
  padding: 15px 18px;
  border-radius: 4px;
}

.detail-item label {
  color: var(--navy);
  font-weight: 800;
}

.detail-item p {
  margin: 0;
  font-weight: 700;
  text-align: right;
}

.bio-text {
  white-space: pre-line;
  color: #334155;
  font-size: 1rem;
  line-height: 1.85;
  margin: 0;
}

.match-list,
.mini-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.match-item {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) auto;
  align-items: center;
  gap: 18px;
  border: 1px solid #e6edf5;
  border-radius: 8px;
  padding: 16px;
  background: #fbfdff;
}

.result-pill {
  border-radius: 4px;
  padding: 6px 9px;
  text-align: center;
  font-size: 0.72rem;
  font-weight: 900;
  background: #e2e8f0;
  color: #334155;
}

.match-item.win .result-pill { background: #dcfce7; color: #166534; }
.match-item.loss .result-pill { background: #fee2e2; color: #991b1b; }

.match-detail strong {
  display: block;
  color: var(--navy);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.teams-line {
  font-weight: 700;
  color: #1e293b;
}

.teams-line span {
  color: #94a3b8;
  margin: 0 7px;
  text-transform: uppercase;
  font-size: 0.75rem;
}

.match-detail small {
  display: block;
  margin-top: 6px;
  color: var(--muted);
}

.score-pill {
  background: var(--navy);
  color: #fff;
  border-radius: 999px;
  padding: 8px 14px;
  font-weight: 900;
}

.stats-board {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stats-board div,
.ranking-panel {
  border: 1px solid var(--line);
  background: #f8fafc;
  border-radius: 8px;
  padding: 22px;
}

.stats-board div {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.stats-board .el-icon {
  color: #2f80a7;
  font-size: 1.4rem;
}

.stats-board b,
.ranking-panel strong {
  color: var(--navy);
  font-size: 2rem;
}

.stats-board span,
.ranking-panel p {
  color: var(--muted);
  margin: 0;
}

.featured-news {
  display: block;
  color: inherit;
  text-decoration: none;
  border: 1px solid #edf2f7;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
  background: #fff;
}

.featured-news img,
.featured-news video {
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
  display: block;
  background: #e2e8f0;
}

.featured-news > div {
  padding: 14px;
}

.featured-news span,
.news-mini-row small {
  color: #2f80a7;
  font-size: 0.72rem;
  font-weight: 900;
  text-transform: uppercase;
}

.featured-news h4 {
  color: var(--navy);
  font-size: 1rem;
  line-height: 1.35;
  margin: 7px 0 8px;
}

.featured-news small {
  color: var(--muted);
  font-weight: 700;
}

.news-panel {
  position: relative;
}

.play-icon {
  position: absolute;
  top: 42%;
  left: 50%;
  width: 42px;
  height: 42px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: rgba(18, 53, 91, 0.72);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
}

.news-mini-list {
  display: flex;
  flex-direction: column;
  gap: 13px;
}

.news-mini-row {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 12px;
  text-decoration: none;
  color: inherit;
  padding-bottom: 13px;
  border-bottom: 1px solid #edf2f7;
}

.news-mini-row:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.news-mini-row img {
  width: 88px;
  height: 66px;
  object-fit: cover;
  border-radius: 6px;
  background: #e2e8f0;
}

.news-mini-row p {
  margin: 0 0 7px;
  color: var(--ink);
  font-weight: 800;
  font-size: 0.88rem;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-mini-row small {
  color: var(--muted);
  text-transform: none;
  font-weight: 700;
}

.tour-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

@media (max-width: 960px) {
  .hero-layout,
  .content-grid {
    grid-template-columns: 1fr;
  }

  .player-portrait {
    height: auto;
    justify-content: flex-start;
    padding-bottom: 22px;
  }

  .score-grid {
    grid-template-columns: 100px repeat(2, 1fr);
  }

  .score-stat {
    border-top: 1px solid rgba(0, 166, 224, 0.45);
  }
}

@media (max-width: 640px) {
  .container {
    padding: 0 16px;
  }

  .profile-hero {
    padding-top: 20px;
  }

  .player-portrait img {
    width: 180px;
    height: 180px;
  }

  .score-grid,
  .detail-grid,
  .stats-board,
  .match-item {
    grid-template-columns: 1fr;
  }

  .score-label,
  .score-stat,
  .match-item {
    text-align: left;
    align-items: flex-start;
  }

  .mode-tab {
    flex: 1;
    min-width: 0;
  }
}
</style>
