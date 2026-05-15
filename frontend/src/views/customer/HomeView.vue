<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import apiClient from '../../services/apiClient'
import { newsService } from '../../services/newsService'
import { playerService } from '../../services/playerService'
import { useAuthStore } from '../../stores/auth'
import { currentLocale, t } from '../../utils/locale'
import { Message, Check, Right, VideoPlay, Location } from '@element-plus/icons-vue'

const authStore = useAuthStore()

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
const topPlayers = ref([])
const recentMatches = ref([])
const featuredTournaments = ref([])
const h2hData = ref(null) 

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

onMounted(async () => {
  authStore.hydrate()
  
  Promise.all([
    newsService.getAllPosts(),
    playerService.getRankings().catch(() => []),
    apiClient.get('/api/tournaments/matches/all').catch(() => []),
    apiClient.get('/api/tournaments').catch(() => [])
  ]).then(async ([newsData, rankingsData, matchesData, toursData]) => {
    
    // 1. Xử lý Tin tức
    if (newsData) {
      rawNewsPosts.value = newsData.sort((a, b) => new Date(b.publish_at || b.created_at) - new Date(a.publish_at || a.created_at))
    }
    
    // 2. Xử lý Rankings
    const filteredRankings = (rankingsData || []).filter(p => !p.full_name?.toLowerCase().includes('admin'))
    topPlayers.value = filteredRankings.slice(0, 10).map((p, index) => ({
      ...p,
      displayRank: index + 1
    }))

    // 3. Xử lý Matches
    const filteredMatches = (Array.isArray(matchesData) ? matchesData : []).filter(m => {
      const isP1Admin = m.p1_name?.toLowerCase().includes('admin')
      const isP2Admin = m.p2_name?.toLowerCase().includes('admin')
      return !isP1Admin && !isP2Admin
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
      h2hData.value = {
        player1: p1,
        player2: p2,
        score1: Math.floor(Math.random() * 6),
        score2: Math.floor(Math.random() * 6)
      }
    }

  }).catch(err => console.error("Lỗi tải dữ liệu Home:", err))
})
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
          <span>{{ t('home.schedule') }}</span>
        </div>
        <div class="widget-body match-list">
          <div v-for="match in recentMatches" :key="match.id" class="match-item">
            <div class="match-meta">
              <span class="round">{{ match.round_code || t('home.round') }}</span>
              <span class="status" :class="{ 'live-text': match.status === 'ongoing' }">
                {{ match.status === 'completed' ? t('home.finished') : (match.status === 'ongoing' ? t('home.live') : match.start) }}
              </span>
            </div>
            <div class="player-row" :class="{ 'is-winner': match.winner_side === 'side_a' }">
              <div class="p-name"><span class="flag"></span> {{ match.p1_name || t('home.tba') }}</div>
              <div class="p-score">
                <span v-if="match.winner_side === 'side_a'" class="check-icon"><el-icon><Check /></el-icon></span>
                <strong>{{ match.score ? match.score.split(',')[0].split('-')[0] : '-' }}</strong>
              </div>
            </div>
            <div class="player-row" :class="{ 'is-winner': match.winner_side === 'side_b' }">
              <div class="p-name"><span class="flag"></span> {{ match.p2_name || t('home.tba') }}</div>
              <div class="p-score">
                <span v-if="match.winner_side === 'side_b'" class="check-icon"><el-icon><Check /></el-icon></span>
                <strong>{{ match.score ? match.score.split(',')[0].split('-')[1] : '-' }}</strong>
              </div>
            </div>
          </div>
          <div v-if="recentMatches.length === 0" class="empty-state">{{ t('home.noMatches') }}</div>
        </div>
      </div>
    </section>

    <section class="container ad-banner-section">
      <div class="ad-banner-wrapper">
        <img src="https://tpc.googlesyndication.com/simgad/9470293650305402252" alt="Sponsor Banner" class="ad-banner-img" referrerpolicy="no-referrer" />
      </div>
    </section>

    <section class="container atp-middle-section">
      
      <div class="rankings-widget">
        <div class="widget-header">
          <h3><span class="pif-logo">PIF</span> {{ t('home.rankings') }}</h3>
          <RouterLink to="/rankings" class="view-all">{{ t('home.viewAll') }} <el-icon><Right /></el-icon></RouterLink>
        </div>
        <div class="widget-tabs">
          <span class="active">{{ t('home.singles') }}</span>
          <span>{{ t('home.doubles') }}</span>
        </div>
        <div class="widget-body ranking-list">
          <div v-for="(player, index) in topPlayers" :key="player.player_id" class="ranking-row">
            <div class="rank-pos">{{ index + 1 }}</div>
            <div class="rank-name"><span class="flag"></span> {{ player.full_name }}</div>
            <div class="rank-pts">{{ player.elo_points }}</div>
          </div>
          <div v-if="topPlayers.length === 0" class="empty-state">{{ t('home.noRanking') }}</div>
        </div>
      </div>

      <div class="h2h-widget" v-if="h2hData">
        <div class="h2h-header">
          <h3>LEXUS <span class="h2h-logo">{{ t('home.h2h') }}</span></h3>
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

          <button class="h2h-btn">{{ t('home.showH2h') }} <el-icon><Right /></el-icon></button>
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
        <div class="sponsor-tiers">
          
          <div class="tier">
            <h5>{{ t('home.premierPartner') }}</h5>
            <div class="logos">
              <img src="../../../public/emirates.svg" alt="Emirates" class="sponsor-img premier-img">
            </div>
          </div>
          
          <div class="tier">
            <h5>{{ t('home.platinumPartner') }}</h5>
            <div class="logos">
              <img src="../../../public/pif.svg" alt="PIF" class="sponsor-img">
              <img src="../../../public/lexus.svg" alt="Lexus" class="sponsor-img">
            </div>
          </div>
          
          <div class="tier">
            <h5>{{ t('home.goldPartner') }}</h5>
            <div class="logos">
              <img src="https://upload.wikimedia.org/wikipedia/commons/9/95/Infosys_logo.svg" alt="Infosys" class="sponsor-img">
              <img src="../../../public/nitto.svg" alt="Nitto" class="sponsor-img">
              <img src="../../../public/haier.jpg" alt="Haier" class="sponsor-img">
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
.match-meta { display: flex; justify-content: space-between; font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem; font-weight: 600; }
.live-text { color: #dc2626; }
.player-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; font-size: 0.95rem; color: var(--atp-dark); }
.is-winner { font-weight: 700; color: var(--atp-blue); }
.check-icon { color: #16a34a; font-size: 0.9rem; display: inline-flex; align-items: center; }

/* =========================================================
   AD BANNER SECTION
========================================================= */
.ad-banner-section {
  margin-bottom: 3rem;
  text-align: center;
}

.ad-banner-wrapper {
  display: inline-block;
  width: 100%;
  max-width: 970px; 
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  background: #f8fafc;
}

.ad-banner-img {
  width: 100%;
  height: auto;
  display: block;
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
}
.h2h-header h3 { font-size: 1.1rem; font-style: italic; font-weight: 800; margin: 0; color: #cbd5e1;}
.h2h-logo { color: white; font-size: 1.2rem;}

.h2h-body { padding: 1.5rem; display: flex; flex-direction: column; align-items: center;}
.h2h-players {
  display: flex; align-items: center; justify-content: space-between; width: 100%; margin-bottom: 2rem;
}
.h2h-player { display: flex; flex-direction: column; align-items: center; width: 90px; text-align: center;}
.h2h-avatar {
  width: 70px; height: 70px; border-radius: 50%; overflow: hidden; border: 2px solid #c1ff72; margin-bottom: 0.8rem;
}
.h2h-avatar img { width: 100%; height: 100%; object-fit: cover; }
.h2h-name { font-size: 0.85rem; font-weight: 700; margin: 0 0 4px 0; line-height: 1.2;}
.h2h-loc { font-size: 0.7rem; color: #94a3b8;}

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
  background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white;
  padding: 0.6rem 1.5rem; border-radius: 20px; font-weight: 700; font-size: 0.8rem; cursor: pointer; transition: 0.2s;
}
.h2h-btn:hover { background: white; color: #002855; }


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
  background: white;
  border-top: 1px solid #e2e8f0;
  padding: 4rem 0;
  text-align: center;
}

.sponsor-tiers { display: flex; flex-direction: column; gap: 3.5rem; }

.tier h5 {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: #94a3b8;
  letter-spacing: 1px;
  margin-bottom: 1.5rem;
}

.logos {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4rem;
  flex-wrap: wrap;
}

.sponsor-img {
  height: 50px; 
  width: auto;
  object-fit: contain;
  transition: transform 0.3s ease;
}

.sponsor-img:hover {
  transform: translateY(-3px);
}

.premier-img {
  height: 85px; 
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
  .logos { gap: 2rem; }
  .sponsor-img { height: 40px; } 
  .premier-img { height: 65px; }
  .atp-tournaments-section h2 { font-size: 1.2rem; }
}

@media (max-width: 480px) {
  .news-cards-row { grid-template-columns: 1fr; }
  .main-hero-news { min-height: 350px; }
  .h2h-players { gap: 1rem; }
  .score-number { font-size: 2rem; }
  .tournament-grid { grid-template-columns: 1fr; }
}
</style>