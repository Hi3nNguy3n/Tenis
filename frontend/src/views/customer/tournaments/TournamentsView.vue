
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTournamentStore } from '../../../stores/tournament'
import { Ticket, Search, Filter, Calendar as CalendarIcon, Location, Trophy } from '@element-plus/icons-vue'

const router = useRouter()
const tournamentStore = useTournamentStore()
const activeTab = ref('Tournaments')

onMounted(() => {
  tournamentStore.fetchTournaments()
})

// Group tournaments by month for the layout
const groupedTournaments = computed(() => {
  const groups = {}
  tournamentStore.tournaments.forEach(t => {
    const date = new Date(t.start_date)
    const monthYear = date.toLocaleString('en-US', { month: 'long', year: 'numeric' })
    if (!groups[monthYear]) groups[monthYear] = []
    groups[monthYear].push(t)
  })
  return groups
})

const viewDetail = (id) => {
  router.push({ name: 'tournament-detail', params: { id } })
}
</script>

<template>
  <div class="tournaments-page">
    
    <!-- SUB-NAV / CATEGORIES -->
    <div class="tour-subnav">
      <div class="container shell">
        <div class="category-tabs">
          <button class="active">ATP Tour</button>
          <button>Challenger</button>
          <button>ITF</button>
        </div>
      </div>
    </div>

    <div class="container main-layout">
      
      <!-- MAIN CALENDAR AREA -->
      <main class="calendar-col">
        
        <!-- HEADER & SEARCH -->
        <header class="calendar-header">
          <div class="title-row">
            <h1>TOURNAMENTS | <span>Calendar</span></h1>
          </div>
          
          <div class="calendar-controls">
            <div class="search-wrap">
              <el-input 
                placeholder="Search tournaments..." 
                class="atp-search-input"
              >
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </div>
            <div class="btn-group">
              <el-button type="primary" class="atp-btn-solid">Open All</el-button>
              <el-button plain class="atp-btn-outline">2026 Calendar PDF</el-button>
            </div>
          </div>
        </header>

        <!-- LOADING STATE -->
        <div v-if="tournamentStore.loading" class="loading-state">
          <div class="spinner"></div>
          <p>Tải lịch thi đấu...</p>
        </div>

        <!-- CALENDAR LIST -->
        <div v-else class="calendar-list">
          <div v-for="(tournaments, month) in groupedTournaments" :key="month" class="month-group">
            <div class="month-header">
              <span>{{ month }}</span>
              <span class="count">({{ tournaments.length }} events)</span>
            </div>

            <div class="tournament-rows">
              <article 
                v-for="t in tournaments" 
                :key="t.id" 
                class="tour-row-card"
                @click="viewDetail(t.id)"
              >
                <!-- Category Badge -->
                <div class="tour-badge">
                  <div class="badge-inner">
                    <span class="type">{{ t.category_type }}</span>
                    <span class="points">250</span>
                  </div>
                </div>

                <!-- Main Info -->
                <div class="tour-main-info">
                  <div class="location-flag">
                    <span class="flag-icon">📍</span>
                    <h3 class="location-text">{{ t.location || 'Saigon, Vietnam' }}</h3>
                  </div>
                  <h4 class="tour-name-text">{{ t.name }} | {{ new Date(t.start_date).toLocaleDateString('vi-VN') }}</h4>
                </div>

                <!-- Technical Specs -->
                <div class="tour-specs">
                  <div class="spec">
                    <span class="label">SGL 28</span>
                    <span class="label">DBL 16</span>
                  </div>
                  <div class="spec">
                    <span class="value">{{ t.surface_type || 'Hard' }}</span>
                    <span class="sub">Outdoor</span>
                  </div>
                </div>

                <!-- Actions -->
                <div class="tour-row-actions">
                  <el-button type="primary" class="btn-tickets" @click.stop="viewDetail(t.id)">
                    Tickets <el-icon class="el-icon--right"><Ticket /></el-icon>
                  </el-button>
                </div>
              </article>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="Object.keys(groupedTournaments).length === 0" class="empty-state">
            <el-empty description="Không có giải đấu nào trong thời gian này" />
          </div>
        </div>
      </main>

      <!-- SIDEBAR WIDGETS -->
      <aside class="sidebar-col">
        
        <!-- WIDGET: TOP NEWS (Mockup similar to screenshot) -->
        <div class="widget">
          <div class="widget-header">
            <h4>Latest News</h4>
            <a href="#" class="view-all">View All</a>
          </div>
          <div class="widget-body news-mini">
            <div class="news-main-feature">
              <img src="https://images.unsplash.com/photo-1595435064214-079678c18789?auto=format&fit=crop&q=80&w=300" />
              <p>Mutua Madrid Open 2026: Draws, Dates, History & All You Need To Know</p>
            </div>
            <div class="news-sub-list">
              <div class="news-item">
                <img src="https://images.unsplash.com/photo-1622279457486-62dcc4a4bd13?auto=format&fit=crop&q=80&w=100" />
                <p>Nadal: 'I hope you'll see me back on court very soon'</p>
              </div>
              <div class="news-item">
                <img src="https://images.unsplash.com/photo-1592709823125-a191f07a2a5e?auto=format&fit=crop&q=80&w=100" />
                <p>Sinner guaranteed to remain World No.1 next week</p>
              </div>
            </div>
          </div>
        </div>

        <!-- WIDGET: ATP STATS -->
        <div class="widget stats-widget">
          <div class="widget-header">
            <h4>Player Stats</h4>
          </div>
          <div class="widget-body">
            <div class="stats-tabs">
              <span class="active">Serve</span>
              <span>Return</span>
              <span>Pressure</span>
            </div>
            <ul class="stats-list">
              <li><span>1. Jannik Sinner</span> <strong>299.4</strong></li>
              <li><span>2. Reilly Opelka</span> <strong>298.0</strong></li>
              <li><span>3. Taylor Fritz</span> <strong>297.6</strong></li>
            </ul>
          </div>
        </div>

      </aside>

    </div>
  </div>
</template>

<style scoped>
.tournaments-page {
  background: #fff;
  min-height: 100vh;
}

/* SUB NAVIGATION */
.tour-subnav {
  background: #f8fafc;
  border-bottom: 1px solid var(--border-light);
  padding: 1rem 0;
  margin-top: 80px;
}

.category-tabs {
  display: flex;
  gap: 2rem;
}

.category-tabs button {
  background: none;
  border: none;
  font-size: 0.85rem;
  font-weight: 500;
  text-transform: uppercase;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.5rem 0;
  position: relative;
}

.category-tabs button.active { color: var(--primary); }
.category-tabs button.active::after {
  content: '';
  position: absolute;
  bottom: -1rem;
  left: 0;
  width: 100%;
  height: 3px;
  background: var(--primary);
}

/* MAIN LAYOUT */
.main-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 3rem;
  padding-top: 2.5rem;
  padding-bottom: 6rem;
}

/* CALENDAR COLUMN */
.calendar-header { margin-bottom: 3rem; }

.title-row h1 {
  font-size: 1.8rem;
  font-weight: 500;
  text-transform: uppercase;
  color: #0f172a;
}

.title-row h1 span { color: var(--primary); font-weight: 400; }

.calendar-controls {
  margin-top: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
}

.search-wrap { flex: 1; max-width: 400px; }

.btn-group { display: flex; gap: 0.8rem; }

.atp-btn-solid { background: #002855; border: none; font-weight: 500; text-transform: uppercase; }
.atp-btn-outline { font-weight: 500; text-transform: uppercase; color: #002855; border-color: #002855; }

/* MONTH GROUPS */
.month-group { margin-bottom: 3rem; }

.month-header {
  padding: 1rem 0;
  border-bottom: 2px solid #002855;
  display: flex;
  align-items: baseline;
  gap: 0.8rem;
  margin-bottom: 1rem;
}

.month-header span:first-child {
  font-size: 1.1rem;
  font-weight: 500;
  color: #002855;
  text-transform: uppercase;
}

.month-header .count {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 500;
}

/* TOURNAMENT ROWS */
.tournament-rows { display: flex; flex-direction: column; gap: 0.8rem; }

.tour-row-card {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  padding: 1.2rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tour-row-card:hover {
  border-color: var(--primary);
  box-shadow: 0 10px 25px rgba(0,0,0,0.05);
}

.tour-badge {
  width: 100px;
  border-right: 1px solid var(--border-light);
  padding-right: 1rem;
  margin-right: 1.5rem;
}

.badge-inner { text-align: left; }
.badge-inner .type {
  display: block;
  font-size: 1.1rem;
  font-weight: 500;
  color: #002855;
  font-style: italic;
  line-height: 1;
}

.tour-main-info { flex: 1; }

.location-flag { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem; }
.location-text { font-size: 1.1rem; font-weight: 500; color: #0f172a; margin: 0; }

.tour-name-text { font-size: 0.85rem; color: var(--text-muted); font-weight: 500; margin: 0; }

.tour-specs {
  display: flex;
  gap: 2rem;
  padding: 0 2rem;
  border-right: 1px solid var(--border-light);
  margin-right: 1.5rem;
}

.spec { display: flex; flex-direction: column; text-align: left; }
.spec .label { font-size: 0.65rem; font-weight: 500; color: #64748b; text-transform: uppercase; }
.spec .value { font-size: 0.95rem; font-weight: 500; color: #0f172a; }
.spec .sub { font-size: 0.65rem; color: #64748b; font-weight: 500; }

.btn-tickets {
  background: #002855;
  border: none;
  font-weight: 500;
  text-transform: uppercase;
  padding: 0.8rem 1.5rem;
  height: auto;
}

/* SIDEBAR WIDGETS */
.widget {
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 2rem;
}

.widget-header {
  padding: 1.25rem;
  background: #f8fafc;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.widget-header h4 {
  font-size: 0.9rem;
  font-weight: 500;
  text-transform: uppercase;
  color: #002855;
  margin: 0;
}

.view-all { font-size: 0.75rem; font-weight: 500; color: var(--primary); text-transform: uppercase; }

.news-main-feature { padding: 1.25rem; border-bottom: 1px solid var(--border-light); }
.news-main-feature img { width: 100%; border-radius: 4px; margin-bottom: 1rem; }
.news-main-feature p { font-weight: 500; color: #0f172a; font-size: 1rem; line-height: 1.3; }

.news-sub-list { padding: 1.25rem; display: flex; flex-direction: column; gap: 1rem; }
.news-item { display: flex; gap: 0.8rem; align-items: flex-start; }
.news-item img { width: 60px; border-radius: 4px; }
.news-item p { font-size: 0.85rem; font-weight: 500; color: #0f172a; line-height: 1.3; }

.stats-tabs { display: flex; padding: 1rem; border-bottom: 1px solid var(--border-light); gap: 1rem; }
.stats-tabs span { font-size: 0.8rem; font-weight: 500; color: var(--text-muted); cursor: pointer; text-transform: uppercase; }
.stats-tabs span.active { color: var(--primary); }

.stats-list { list-style: none; padding: 1rem; margin: 0; }
.stats-list li { display: flex; justify-content: space-between; padding: 0.8rem 0; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem; }
.stats-list li span { font-weight: 500; color: #334155; }
.stats-list li strong { color: #0f172a; font-weight: 500; }

@media (max-width: 1080px) {
  .main-layout { grid-template-columns: 1fr; }
  .sidebar-col { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
}

@media (max-width: 768px) {
  .calendar-controls { flex-direction: column; align-items: stretch; }
  .tour-row-card { flex-direction: column; align-items: stretch; gap: 1rem; text-align: center; }
  .tour-badge { width: 100%; border: none; border-bottom: 1px solid var(--border-light); padding: 0 0 1rem; margin: 0; }
  .tour-specs { padding: 1rem 0; border: none; border-bottom: 1px solid var(--border-light); margin: 0; justify-content: center; }
  .btn-tickets { width: 100%; }
}

.loading-state { text-align: center; padding: 4rem; }
.spinner {
  width: 40px; height: 40px; border: 4px solid rgba(0,0,0,0.05);
  border-top-color: var(--primary); border-radius: 50%; animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
