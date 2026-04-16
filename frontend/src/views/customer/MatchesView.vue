<script setup>
import { ref } from 'vue'
import { Search, Calendar as CalendarIcon, ArrowLeft, ArrowRight, VideoPlay, PieChart } from '@element-plus/icons-vue'

// Mock Data for Matches
const mockTournamentMatches = [
  {
    id: 't1',
    name: 'Barcelona Open Banc Sabadell',
    location: 'Barcelona, Spain',
    matches: [
      {
        id: 1,
        round: 'Round of 16',
        players: [
          { name: 'C. Alcaraz', seed: '1', flag: '🇪🇸', sets: [6, 7, 2], winner: true },
          { name: 'S. Tsitsipas', seed: '5', flag: '🇬🇷', sets: [4, 6, 1], winner: false }
        ],
        status: 'Finished',
        time: 'Final'
      },
      {
        id: 2,
        round: 'Round of 16',
        players: [
          { name: 'A. De Minaur', seed: '11', flag: '🇦🇺', sets: [3, 4], winner: false },
          { name: 'R. Nadal', flag: '🇪🇸', sets: [6, 6], winner: true }
        ],
        status: 'Finished',
        time: 'Final'
      }
    ]
  },
  {
    id: 't2',
    name: 'BMW Open by Ibipanda',
    location: 'Munich, Germany',
    matches: [
      {
        id: 3,
        round: 'Quarter-Finals',
        players: [
          { name: 'A. Zverev', seed: '1', flag: '🇩🇪', sets: [4, 1], winner: false, serve: true },
          { name: 'H. Rune', seed: '2', flag: '🇩🇰', sets: [6, 2], winner: false }
        ],
        status: 'Live',
        time: 'Set 2 - Game 4'
      }
    ]
  }
]

const matches = ref(mockTournamentMatches)
const dates = ['14 APR', '15 APR', '16 APR', 'TODAY', '18 APR', '19 APR']
const activeDate = ref('TODAY')

</script>

<template>
  <div class="matches-page">
    
    <!-- SUBNAV: DATE SELECTION -->
    <div class="matches-subnav">
      <div class="container nav-inner">
        <button class="nav-arrow"><el-icon><ArrowLeft /></el-icon></button>
        <div class="date-strip">
          <button 
            v-for="date in dates" 
            :key="date" 
            :class="{ active: activeDate === date }"
            @click="activeDate = date"
          >
            {{ date }}
          </button>
        </div>
        <button class="nav-arrow"><el-icon><ArrowRight /></el-icon></button>
        <div class="calendar-btn">
          <el-icon><CalendarIcon /></el-icon>
        </div>
      </div>
    </div>

    <div class="container main-layout">
      
      <!-- MAIN SCORES AREA -->
      <main class="scores-col">
          <div v-for="tournament in matches" :key="tournament.id" class="tournament-group">
            <header class="tournament-header">
              <div class="t-title">
                <span class="location">{{ tournament.location }}</span>
                <h2>{{ tournament.name }}</h2>
              </div>
              <div class="t-actions">
                <el-button link>Order of Play</el-button>
                <el-button link>Draws</el-button>
              </div>
            </header>

            <div class="match-list">
              <article v-for="match in tournament.matches" :key="match.id" class="atp-match-card">
                <div class="match-info-strip">
                  <span class="round">{{ match.round }}</span>
                  <span :class="['match-status', match.status.toLowerCase()]">
                    <span v-if="match.status === 'Live'" class="pulse"></span>
                    {{ match.time }}
                  </span>
                </div>

                <div class="match-players">
                  <div v-for="player in match.players" :key="player.name" class="player-row" :class="{ winner: player.winner }">
                    <div class="player-identity">
                      <span class="player-flag">{{ player.flag }}</span>
                      <span v-if="player.seed" class="player-seed">({{ player.seed }})</span>
                      <span class="player-name">{{ player.name }}</span>
                      <span v-if="player.serve" class="serve-dots">🎾</span>
                    </div>
                    <div class="player-scores">
                      <span v-for="(set, idx) in player.sets" :key="idx" class="set-score" :class="{ active: idx === player.sets.length - 1 && match.status === 'Live' }">
                        {{ set }}
                      </span>
                    </div>
                  </div>
                </div>

                <div class="match-actions">
                  <button class="m-btn highlight"><el-icon><VideoPlay /></el-icon> Highlights</button>
                  <button class="m-btn"><el-icon><PieChart /></el-icon> Stats</button>
                </div>
              </article>
            </div>
          </div>
      </main>

      <!-- SIDEBAR WIDGETS (Consistent with other pages) -->
      <aside class="sidebar-col">
        <div class="widget">
          <div class="widget-header">
            <h4>Tournament News</h4>
          </div>
          <div class="widget-body news-mini-list">
             <div class="news-item-mini">
                <img src="https://images.unsplash.com/photo-1595435064214-079678c18789?auto=format&fit=crop&q=80&w=150" />
                <p>Nadal wins thriller in Barcelona comeback</p>
              </div>
              <div class="news-item-mini">
                <img src="https://images.unsplash.com/photo-1510832198440-a52376950479?auto=format&fit=crop&q=80&w=150" />
                <p>Alcaraz sets up Sinner semi-final in Madrid</p>
              </div>
          </div>
        </div>

        <div class="widget">
           <div class="widget-header">
            <h4>Live Standings</h4>
          </div>
          <div class="widget-body">
             <div class="mini-table">
                <div class="tr"><span>1. J. Sinner</span> <strong>11,200</strong></div>
                <div class="tr"><span>2. N. Djokovic</span> <strong>9,800</strong></div>
                <div class="tr"><span>3. C. Alcaraz</span> <strong>8,950</strong></div>
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

/* SUBNAV DATE STRIP */
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
  color: rgba(255,255,255,0.6);
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
  background: rgba(255,255,255,0.1);
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
}

/* MAIN LAYOUT */
.main-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 3rem;
  padding-top: 3rem;
  padding-bottom: 6rem;
}

/* TOURNAMENT GROUPS */
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

/* MATCH CARDS */
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
  box-shadow: 0 10px 30px rgba(0,0,0,0.05);
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
.player-seed { font-size: 0.8rem; color: var(--text-muted); font-weight: 600; }
.player-row.winner .player-name { color: var(--primary); font-weight: 600; }

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

/* SIDEBAR WIDGETS */
.widget { border: 1px solid var(--border-light); border-radius: 4px; margin-bottom: 2rem; overflow: hidden; }
.widget-header { padding: 1.25rem; background: #f8fafc; border-bottom: 1px solid var(--border-light); }
.widget-header h4 { font-size: 0.9rem; font-weight: 500; text-transform: uppercase; color: #002855; }

.news-item-mini { display: flex; gap: 1rem; padding: 1rem; border-bottom: 1px solid #f1f5f9; }
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
