<script setup>
import { computed, onMounted, ref } from 'vue'
import { Search, Right, VideoPlay, Medal } from '@element-plus/icons-vue'
import apiClient from '../../services/apiClient'
import { newsService } from '../../services/newsService'
import { useAuthStore } from '../../stores/auth'
import { t } from '../../utils/locale'

const loading = ref(true)
const players = ref([])
const recentWinners = ref([])
const latestNews = ref([])
const searchQuery = ref('')

const isVideo = (url) => {
  if (!url) return false
  return url.match(/\.(mp4|webm|ogg|mov)(\?.*)?$/i) !== null
}

const visiblePlayers = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) return players.value
  return players.value.filter(p => p.full_name?.toLowerCase().includes(keyword))
})

const loadPlayers = async () => {
  try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/players/rankings`)
    const rankings = await res.json()
    const normalized = Array.isArray(rankings) ? rankings : []
    
    // THÊM DÒNG NÀY: Lọc bỏ những tài khoản có chữ 'admin'
    const nonAdminPlayers = normalized.filter(p => !p.full_name?.toLowerCase().includes('admin'))

    // Thay biến normalized thành nonAdminPlayers ở dòng map
    const enriched = await Promise.all(nonAdminPlayers.map(async (p) => {
      return {
        ...p,
        avatar_url: p.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(p.full_name)}&background=random`
      }
    }))
    players.value = enriched
    recentWinners.value = players.value.slice(0, 8)
  } catch (err) { console.error(err) }
}
const loadLatestNews = async () => {
  try {
    const data = await newsService.getAllPosts({ limit: 3 })
    latestNews.value = Array.isArray(data)
      ? data.map((post) => ({
          id: post.id,
          title: post.title,
          slug: post.slug,
          summary: post.summary || post.excerpt || '',
          thumbnail_url: post.thumbnail_url,
          media_url: post.media_url,
          created_at: post.publish_at || post.created_at,
        }))
      : []
  } catch {
    latestNews.value = []
  }
}

onMounted(async () => {
  await loadPlayers()
  await loadLatestNews()
  loading.value = false
})
</script>

<template>
  <div class="clean-portfolio-app">
    
    <div class="container main-wrapper" v-loading="loading">
      
      <header class="portfolio-hero">
        <h1 class="hero-title">
          {{ t('players.list') }} <span class="highlight-text">{{ t('players.players') }}</span>
        </h1>
        <p class="hero-subtitle">
          {{ t('players.systemData') }}
        </p>

      </header>

      <section class="featured-section" v-if="recentWinners.length">
        <div class="section-heading">
          <el-icon><Medal /></el-icon>
          <h2>{{ t('players.featuredPlayers') }}</h2>
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
            <p class="featured-pts">{{ p.elo_points }} {{ t('players.points') }}</p>
          </RouterLink>
        </div>
      </section>

      <div class="content-layout">
        
        <main class="grid-column">
          <div class="talent-grid">
            <div v-for="p in visiblePlayers" :key="p.id" class="talent-card group">
              
              <div class="talent-image-box">
                <img :src="p.avatar_url" alt="" class="talent-img" referrerpolicy="no-referrer" />
              </div>
              
              <div class="talent-info">
                <div class="talent-header">
                  <h3 class="talent-name">{{ p.full_name }}</h3>
                  <span class="talent-badge">{{ t('players.rank') }} #{{ p.rank || '--' }}</span>
                </div>
                
                <div class="talent-metrics">
                  <div class="metric">
                    <span class="m-label">{{ t('players.elo') }}</span>
                    <span class="m-value">{{ p.elo_points }}</span>
                  </div>
                  <div class="metric-divider"></div>
                  <div class="metric">
                    <span class="m-label">{{ t('players.winRate') }}</span>
                    <span class="m-value">{{ p.win_rate || 0 }}%</span>
                  </div>
                  <div class="metric-divider"></div>
                  <div class="metric">
                    <span class="m-label">{{ t('players.matchesCount') }}</span>
                    <span class="m-value">{{ (p.wins || 0) + (p.losses || 0) }}</span>
                  </div>
                </div>

                <RouterLink :to="`/players/${p.player_id || p.id}`" class="view-profile-link">
                  <button class="view-profile-btn">
                    {{ t('players.viewProfile') }} <el-icon><Right /></el-icon>
                  </button>
                </RouterLink>
              </div>
            </div>

            <div v-if="!visiblePlayers.length" class="empty-state-card">
              <p>{{ t('players.noMatch') }} "{{ searchQuery }}".</p>
            </div>
          </div>
        </main>

        <aside class="widgets-column">
          
          <div class="clean-widget">
            <div class="widget-top">
              <h3>{{ t('players.latestNews') }}</h3>
              <RouterLink to="/news" class="widget-link">{{ t('players.viewAll') }} <el-icon><Right /></el-icon></RouterLink>
            </div>
            
            <div class="widget-feed" v-if="latestNews.length">
              <RouterLink 
                v-for="news in latestNews" 
                :key="news.id" 
                :to="news.slug ? `/news/${news.slug}` : '/news'"
                class="feed-item"
              >
                <div class="feed-visual">
                  <video 
                    v-if="isVideo(news.media_url || news.thumbnail_url)" 
                    :src="news.media_url || news.thumbnail_url" 
                    autoplay muted loop playsinline>
                  </video>
                  <img 
                    v-else 
                    :src="news.thumbnail_url || news.media_url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop'" 
                    referrerpolicy="no-referrer"
                  />
                  <div class="feed-play" v-if="isVideo(news.media_url || news.thumbnail_url)">
                    <el-icon><VideoPlay /></el-icon>
                  </div>
                </div>
                <div class="feed-text">
                  <h4 class="line-clamp-2">{{ news.title }}</h4>
                  <time>{{ new Date(news.created_at).toLocaleDateString('vi-VN') }}</time>
                </div>
              </RouterLink>
            </div>
            <div v-else class="empty-feed">{{ t('players.updatingPosts') }}</div>
          </div>

          <div class="clean-widget promo-card">
            <div class="promo-content">
              <h4>{{ t('players.upcomingTournament') }}</h4>
              <p>{{ t('players.tournamentDesc') }}</p>
              <RouterLink to="/tournaments" class="btn-primary">{{ t('players.viewSchedule') }}</RouterLink>
            </div>
          </div>

        </aside>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* =========================================================
   CLEAN AGENCY THEME VARIABLES (BLUE-GREY & WHITE)
========================================================= */
.clean-portfolio-app {
  /* Tông màu Xanh Xám (Slate) */
  --bg-base: #f1f5f9;       /* Slate 100 - Nền tổng thể */
  --card-bg: #ffffff;       /* Trắng - Nền các thẻ Card */
  --border-light: #e2e8f0;  /* Slate 200 - Viền xám nhạt */
  --border-hover: #cbd5e1;  /* Slate 300 - Viền khi hover */
  
  --text-main: #0f172a;     /* Slate 900 - Chữ tiêu đề */
  --text-body: #334155;     /* Slate 700 - Chữ đoạn văn */
  --text-muted: #64748b;    /* Slate 500 - Chữ phụ */
  
  --accent-primary: #475569; /* Slate 600 - Xanh xám chủ đạo */
  --accent-light: #f8fafc;   /* Slate 50 - Nền highlight nhẹ */
  
  --shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.05);
  --shadow-md: 0 4px 15px rgba(15, 23, 42, 0.05);
  --shadow-hover: 0 10px 25px rgba(15, 23, 42, 0.08);

  background-color: var(--bg-base);
  color: var(--text-body);
  min-height: 100vh;
  font-family: 'Inter', -apple-system, sans-serif;
  padding-bottom: 5rem;
}

.container {
  max-width: 1360px;
  margin: 0 auto;
  padding: 0 2rem;
}

/* =========================================================
   HERO HEADER
========================================================= */
.portfolio-hero {
  padding: 5rem 0 3.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.hero-title {
  font-size: clamp(2.5rem, 6vw, 4rem);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
  margin: 0 0 1rem;
  color: var(--text-main);
}

.highlight-text {
  color: var(--accent-primary);
}

.hero-subtitle {
  color: var(--text-muted);
  font-size: 1.1rem;
  max-width: 600px;
  line-height: 1.6;
  margin-bottom: 2.5rem;
}

/* Thanh tìm kiếm trung tâm */
.clean-search-bar {
  display: flex;
  align-items: center;
  background: var(--card-bg);
  border: 1px solid var(--border-light);
  border-radius: 99px;
  padding: 0.75rem 1.5rem;
  width: 100%;
  max-width: 550px;
  box-shadow: var(--shadow-md);
  transition: all 0.3s ease;
}

.clean-search-bar:focus-within {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 4px rgba(71, 85, 105, 0.1);
}

.search-icon {
  font-size: 1.2rem;
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
}
.search-input::placeholder { color: #94a3b8; }

/* =========================================================
   FEATURED PLAYERS (DẠNG STORY)
========================================================= */
.featured-section {
  margin-bottom: 3rem;
}

.section-heading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  color: var(--accent-primary);
}
.section-heading h2 {
  font-size: 0.9rem;
  font-weight: 800;
  letter-spacing: 0.05em;
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
  min-width: 100px;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  transition: transform 0.2s;
}
.featured-card:hover { transform: translateY(-5px); }

.featured-avatar {
  position: relative;
  width: 90px; height: 90px;
  border-radius: 24px;
  background: var(--card-bg);
  padding: 4px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  margin-bottom: 0.8rem;
}

.featured-avatar img {
  width: 100%; height: 100%;
  object-fit: cover;
  border-radius: 20px;
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
  background: var(--accent-primary);
  color: white; font-size: 0.7rem; font-weight: 800;
  width: 26px; height: 26px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}

.featured-name { font-size: 0.9rem; font-weight: 700; margin: 0 0 4px; color: var(--text-main); text-align: center;}
.featured-pts { font-size: 0.75rem; color: var(--text-muted); margin: 0; font-weight: 500;}

/* =========================================================
   BỐ CỤC CHÍNH (GRID + SIDEBAR)
========================================================= */
.content-layout {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 2.5rem;
}

/* =========================================================
   BENTO GRID CARDS (DANH SÁCH VĐV)
========================================================= */
.talent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.talent-card {
  background: var(--card-bg);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.talent-card:hover {
  border-color: var(--border-hover);
  transform: translateY(-4px);
  box-shadow: var(--shadow-hover);
}

.talent-image-box {
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 12px;
  overflow: hidden;
  background: var(--bg-base);
}

.talent-img {
  width: 100%; height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.talent-card:hover .talent-img {
  transform: scale(1.03);
}

.talent-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.talent-header {
  display: flex; justify-content: space-between; align-items: flex-start;
}

.talent-name {
  font-size: 1.15rem; font-weight: 800; margin: 0; color: var(--text-main);
  line-height: 1.3;
}

.talent-badge {
  background: var(--accent-light);
  color: var(--accent-primary);
  border: 1px solid var(--border-light);
  font-size: 0.7rem; font-weight: 700;
  padding: 4px 8px; border-radius: 6px;
  letter-spacing: 0.05em;
}

.talent-metrics {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--accent-light);
  border: 1px solid var(--border-light);
  padding: 0.8rem 1rem;
  border-radius: 10px;
}

.metric { display: flex; flex-direction: column; gap: 4px; }
.m-label { font-size: 0.65rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;}
.m-value { font-size: 1rem; color: var(--text-main); font-weight: 800;}
.metric-divider { width: 1px; height: 24px; background: var(--border-light); }

/* Nút bấm tĩnh - Luôn hiển thị */
.view-profile-btn {
  width: 100%;
  padding: 0.75rem;
  background: transparent;
  color: var(--text-body);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
}

.talent-card:hover .view-profile-btn {
  background: var(--text-main);
  color: #fff;
  border-color: var(--text-main);
}

.empty-state-card {
  grid-column: 1 / -1;
  background: var(--card-bg);
  border: 1px dashed var(--border-hover);
  padding: 4rem 2rem;
  text-align: center;
  border-radius: 16px;
  color: var(--text-muted);
}


/* =========================================================
   RIGHT SIDEBAR WIDGETS (TIN TỨC)
========================================================= */
.widgets-column {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.clean-widget {
  background: var(--card-bg);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
}

.widget-top {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 1.25rem;
}

.widget-top h3 {
  font-size: 0.85rem; font-weight: 800; color: var(--text-main);
  margin: 0; letter-spacing: 0.05em;
}

.widget-link {
  color: var(--accent-primary); font-size: 0.8rem; font-weight: 600;
  text-decoration: none; display: flex; align-items: center; gap: 4px;
}
.widget-link:hover { text-decoration: underline; }

.widget-feed {
  display: flex; flex-direction: column; gap: 1.2rem;
}

.feed-item {
  display: flex; gap: 1rem; text-decoration: none; align-items: center;
  transition: opacity 0.2s;
}
.feed-item:hover { opacity: 0.7; }

.feed-visual {
  width: 75px; height: 75px; border-radius: 10px; overflow: hidden; position: relative;
  background: var(--bg-base); flex-shrink: 0;
}
.feed-visual img, .feed-visual video { width: 100%; height: 100%; object-fit: cover;}

.feed-play {
  position: absolute; inset: 0; background: rgba(15, 23, 42, 0.3);
  display: flex; align-items: center; justify-content: center; color: white;
}

.feed-text { flex: 1; display: flex; flex-direction: column; gap: 6px;}
.line-clamp-2 {
  font-size: 0.9rem; font-weight: 700; color: var(--text-main); margin: 0;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  line-height: 1.4;
}
.feed-text time { font-size: 0.75rem; color: var(--text-muted); font-weight: 500;}

/* Promo Widget */
.promo-card {
  background: linear-gradient(135deg, var(--accent-primary), var(--text-main));
  color: white;
  border: none;
}

.promo-content h4 { font-size: 1.1rem; font-weight: 800; margin: 0 0 0.5rem 0;}
.promo-content p { font-size: 0.9rem; color: rgba(255,255,255,0.8); line-height: 1.5; margin-bottom: 1.5rem;}

.btn-primary {
  display: inline-block; width: 100%; text-align: center;
  background: white; color: var(--text-main);
  padding: 0.8rem; border-radius: 8px; font-weight: 800; font-size: 0.85rem;
  text-decoration: none; transition: 0.3s; box-shadow: var(--shadow-sm);
}
.btn-primary:hover {
  background: var(--bg-base);
  transform: translateY(-2px);
}

/* =========================================================
   RESPONSIVE
========================================================= */
@media (max-width: 1024px) {
  .content-layout { grid-template-columns: 1fr; }
  .widgets-column { flex-direction: row; }
  .clean-widget { flex: 1; }
}

@media (max-width: 768px) {
  .portfolio-hero { padding: 3rem 0; }
  .hero-title { font-size: 2rem; }
  .widgets-column { flex-direction: column; }
  .talent-grid { grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); }
}

@media (max-width: 480px) {
  .container { padding: 0 1rem; }
  .talent-grid { grid-template-columns: 1fr; }
}
</style>
