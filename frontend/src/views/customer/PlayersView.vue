<script setup>
import { computed, ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

// Mock Data for Top Winners
const recentWinners = [
  { id: 1, name: 'Jannik Sinner', tournament: 'ATP Masters 1000 Miami', image: 'https://images.unsplash.com/photo-1595435064214-079678c18789?auto=format&fit=crop&q=80&w=200' },
  { id: 2, name: 'Rafael Nadal', tournament: 'ATP 500 Barcelona', image: 'https://images.unsplash.com/photo-1510832198440-a52376950479?auto=format&fit=crop&q=80&w=200' },
  { id: 3, name: 'Carlos Alcaraz', tournament: 'ATP Masters 1000 Madrid', image: 'https://images.unsplash.com/photo-1592709823125-a191f07a2a5e?auto=format&fit=crop&q=80&w=200' },
  { id: 4, name: 'Novak Djokovic', tournament: 'Australian Open', image: 'https://images.unsplash.com/photo-1622279457486-62dcc4a4bd13?auto=format&fit=crop&q=80&w=200' }
]

// Mock Data for Main Player Grid
const mockupPlayers = [
  { id: 1, rank: 1, name: 'Jannik Sinner', country: 'Italy', points: 11200, avatar: '' },
  { id: 2, rank: 2, name: 'Carlos Alcaraz', country: 'Spain', points: 8900, avatar: '' },
  { id: 3, rank: 3, name: 'Alexander Zverev', country: 'Germany', points: 7500, avatar: '' },
  { id: 4, rank: 4, name: 'Novak Djokovic', country: 'Serbia', points: 7200, avatar: '' },
  { id: 5, rank: 5, name: 'Daniil Medvedev', country: 'Neutral', points: 6800, avatar: '' },
  { id: 6, rank: 6, name: 'Andrey Rublev', country: 'Neutral', points: 5400, avatar: '' },
  { id: 7, rank: 7, name: 'Casper Ruud', country: 'Norway', points: 4100, avatar: '' },
  { id: 8, rank: 8, name: 'Hubert Hurkacz', country: 'Poland', points: 3950, avatar: '' },
]

const players = ref(mockupPlayers)
const totalPoints = computed(() => players.value.reduce((sum, player) => sum + player.points, 0))

onMounted(() => {
  // Logic to fetch real players would go here
})
</script>

<template>
  <div class="players-page">
    
    <!-- RECENT WINNERS SECTION -->
    <section class="winners-hero">
      <div class="container">
        <div class="winners-header">
          <span class="section-kicker">Champions</span>
          <h2>Recent ATP Tour Winners</h2>
        </div>
        <div class="winners-grid">
          <div v-for="winner in recentWinners" :key="winner.id" class="winner-card">
            <div class="winner-avatar">
              <img :src="winner.image" alt="Winner" />
            </div>
            <div class="winner-info">
              <span class="tour-name">{{ winner.tournament }}</span>
              <h3>{{ winner.name }}</h3>
              <div class="winner-visual-strip"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- MAIN INTERFACE -->
    <section class="players-main-section">
      <div class="container main-layout">
        
        <!-- LEFT: Player Listing -->
        <div class="content-col">
          <div class="listing-filters">
            <div class="search-wrap">
              <input type="text" placeholder="Search for players..." class="player-search" />
              <button class="search-btn">🔍</button>
            </div>
            <div class="filter-group">
              <select><option>Singles</option></select>
              <select><option>Top 100</option></select>
              <select><option>All Regions</option></select>
            </div>
          </div>

          <div class="players-grid">
            <article v-for="player in players" :key="player.id" class="atp-player-card">
              <div class="player-visual">
                <div class="rank-badge">{{ player.rank }}</div>
                <div class="profile-circle">
                  <span v-if="!player.avatar">🎾</span>
                  <img v-else :src="player.avatar" />
                </div>
              </div>
              <div class="player-meta">
                <h3>{{ player.name }}</h3>
                <div class="meta-bottom">
                  <span class="country-tag">{{ player.country }}</span>
                  <span class="points-tag">{{ player.points.toLocaleString() }} PTS</span>
                </div>
              </div>
            </article>
          </div>
        </div>

        <!-- RIGHT: Sidebar Widgets -->
        <aside class="sidebar-col">
          
          <!-- SCORES WIDGET -->
          <div class="widget">
            <div class="widget-header">
              <h4>Live Scores</h4>
              <button class="view-all">View All</button>
            </div>
            <div class="widget-body scoreslist">
              <div class="score-item">
                <div class="tour-loc">Barcelona Open</div>
                <div class="match-mini">
                  <div class="player-row"><span>🇪🇸 C. Alcaraz</span> <strong>2</strong></div>
                  <div class="player-row"><span>🇬🇷 S. Tsitsipas</span> <strong>1</strong></div>
                </div>
              </div>
              <div class="score-item">
                <div class="tour-loc">BMW Open Munich</div>
                <div class="match-mini">
                  <div class="player-row"><span>🇩🇪 A. Zverev</span> <strong>2</strong></div>
                  <div class="player-row"><span>🇳🇴 C. Ruud</span> <strong>0</strong></div>
                </div>
              </div>
            </div>
          </div>

          <!-- PROFILE HIGHLIGHT WIDGET -->
          <div class="widget profile-feature">
            <div class="feature-bg"></div>
            <div class="feature-inner">
              <span class="kicker">Player Profile</span>
              <h4>CARLOS ALCARAZ</h4>
              <div class="feature-stats">
                <div class="fs-row"><span>Rank</span> <span>3</span></div>
                <div class="fs-row"><span>Age</span> <span>21</span></div>
                <div class="fs-row"><span>Win/Loss</span> <span>18 - 4</span></div>
              </div>
              <button class="full-bio">See Full Bio</button>
            </div>
          </div>

          <!-- TRENDING NEWS WIDGET -->
          <div class="widget">
            <div class="widget-header">
              <h4>Latest News</h4>
            </div>
            <div class="widget-body news-mini-list">
              <div class="news-item-mini">
                <img src="https://images.unsplash.com/photo-1595435064214-079678c18789?auto=format&fit=crop&q=80&w=150" />
                <p>Nadal advances to semi-finals in Barcelona Open</p>
              </div>
              <div class="news-item-mini">
                <img src="https://images.unsplash.com/photo-1510832198440-a52376950479?auto=format&fit=crop&q=80&w=150" />
                <p>Djokovic confirms participation in French Open</p>
              </div>
              <div class="news-item-mini">
                <img src="https://images.unsplash.com/photo-1592709823125-a191f07a2a5e?auto=format&fit=crop&q=80&w=150" />
                <p>Alcaraz's recovery looks promising for Madrid</p>
              </div>
            </div>
          </div>

        </aside>

      </div>
    </section>

  </div>
</template>

<style scoped>
.players-page {
  background: var(--bg-main);
  min-height: 100vh;
}

/* WINNERS HERO SECTION */
.winners-hero {
  background: #0f172a;
  padding: 4rem 0;
  color: #fff;
  border-bottom: 4px solid var(--primary);
}

.winners-header {
  margin-bottom: 3rem;
  text-align: center;
}

.section-kicker {
  display: block;
  color: var(--primary);
  font-weight: 500;
  text-transform: uppercase;
  font-size: 0.85rem;
  letter-spacing: 0.2rem;
  margin-bottom: 0.5rem;
}

.winners-header h2 {
  font-size: 2.5rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: -0.02em;
}

.winners-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 2rem;
}

.winner-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  transition: transform 0.3s;
  border-radius: 4px;
}

.winner-card:hover {
  transform: translateY(-10px);
  background: rgba(255, 255, 255, 0.06);
}

.winner-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  margin-bottom: 1.2rem;
  border: 4px solid var(--primary);
}

.winner-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.tour-name {
  display: block;
  font-size: 0.7rem;
  color: #94a3b8;
  text-transform: uppercase;
  font-weight: 500;
  margin-bottom: 0.4rem;
}

.winner-info h3 {
  font-size: 1.2rem;
  font-weight: 500;
  margin-bottom: 1rem;
}

.winner-visual-strip {
  width: 40px;
  height: 4px;
  background: var(--primary);
  margin-top: auto;
}

/* MAIN LAYOUT */
.players-main-section {
  padding: 3rem 0 6rem;
}

.main-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 3rem;
}

/* LISTING CONTROLS */
.listing-filters {
  background: #fff;
  padding: 1.5rem;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  gap: 1.5rem;
}

.search-wrap {
  flex: 1;
  position: relative;
}

.player-search {
  width: 100%;
  padding: 0.8rem 1rem;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  font-size: 0.95rem;
  outline: none;
}

.player-search:focus { border-color: var(--primary); }

.search-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
}

.filter-group {
  display: flex;
  gap: 1rem;
}

.filter-group select {
  padding: 0.8rem 1.2rem;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  font-weight: 500;
  font-size: 0.85rem;
  background: #fff;
  cursor: pointer;
}

/* PLAYER GRID */
.players-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.atp-player-card {
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.atp-player-card:hover {
  border-color: var(--primary);
  box-shadow: 0 10px 25px rgba(0,0,0,0.05);
}

.player-visual {
  position: relative;
  margin-bottom: 2rem;
}

.rank-badge {
  position: absolute;
  top: 0;
  left: 0;
  width: 40px;
  height: 40px;
  background: var(--primary);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  border: 3px solid #fff;
  z-index: 2;
}

.profile-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: var(--bg-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 4rem;
  border: 1px solid var(--border-light);
  overflow: hidden;
}

.profile-circle img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.atp-player-card h3 {
  font-size: 1.3rem;
  font-weight: 500;
  text-transform: uppercase;
  margin-bottom: 0.8rem;
  color: var(--text-dark);
}

.meta-bottom {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.country-tag {
  color: var(--text-muted);
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
}

.points-tag {
  color: var(--primary);
  font-size: 1.1rem;
  font-weight: 500;
}

/* SIDEBAR WIDGETS */
.sidebar-col {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.widget {
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  overflow: hidden;
}

.widget-header {
  padding: 1.2rem;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.widget-header h4 {
  font-size: 0.9rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-dark);
}

.view-all {
  background: none;
  border: none;
  color: var(--primary);
  font-weight: 500;
  font-size: 0.75rem;
  text-transform: uppercase;
  cursor: pointer;
}

.widget-body { padding: 0; }

.score-item {
  padding: 1.25rem;
  border-bottom: 1px solid var(--bg-soft);
}

.tour-loc {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  margin-bottom: 0.8rem;
}

.player-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.3rem;
  font-size: 0.95rem;
}

.player-row strong { color: var(--text-dark); }

/* FEATURE WIDGET */
.profile-feature {
  position: relative;
  background: #0f172a;
  color: #fff;
  padding: 2rem;
  border: none;
}

.feature-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 70% 30%, var(--primary) -50%, transparent 60%);
  opacity: 0.4;
}

.feature-inner { position: relative; z-index: 2; }

.feature-inner .kicker {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--primary);
  text-transform: uppercase;
  margin-bottom: 0.5rem;
  display: block;
}

.feature-inner h4 {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
}

.feature-stats {
  margin-bottom: 2rem;
}

.fs-row {
  display: flex;
  justify-content: space-between;
  padding: 0.6rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  font-size: 0.9rem;
}

.fs-row span:first-child { color: rgba(255,255,255,0.6); font-weight: 600; }
.fs-row span:last-child { font-weight: 500; }

.full-bio {
  width: 100%;
  padding: 1rem;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  text-transform: uppercase;
  cursor: pointer;
  transition: background 0.2s;
}

/* NEWS MINI LIST */
.news-item-mini {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid var(--bg-soft);
}

.news-item-mini img {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  object-fit: cover;
}

.news-item-mini p {
  font-size: 0.85rem;
  font-weight: 500;
  line-height: 1.3;
  color: var(--text-dark);
}

@media (max-width: 1080px) {
  .main-layout { grid-template-columns: 1fr; }
  .sidebar-col { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
}

@media (max-width: 768px) {
  .listing-filters { flex-direction: column; align-items: stretch; }
  .winners-grid { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 480px) {
  .winners-grid { grid-template-columns: 1fr; }
  .atp-player-card { padding: 1.5rem; }
}
</style>
