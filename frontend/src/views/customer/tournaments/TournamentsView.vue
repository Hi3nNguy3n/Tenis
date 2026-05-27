<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTournamentStore } from '../../../stores/tournament'
import { newsService } from '../../../services/newsService'
import { playerService } from '../../../services/playerService'
import MarketingBannerStrip from '../../../components/MarketingBannerStrip.vue'
import { Search, Location, Clock, Trophy } from '@element-plus/icons-vue'
import { currentLocale, t } from '../../../utils/locale'

const router = useRouter()
const isVideo = (url) => {
  if (!url) return false
  return url.match(/\.(mp4|webm|ogg|mov)(\?.*)?$/i) !== null
}

const tournamentStore = useTournamentStore()
const searchQuery = ref('')

const activeFilter = ref('all')
const latestNews = ref([])
const topPlayers = ref([])

// Pagination
const currentPage = ref(1)
const pageSize = ref(6)

const fetchTournaments = () => {
  tournamentStore.fetchTournaments({ 
    search: searchQuery.value,
    limit: 100 // Tăng giới hạn để lấy đủ 11 giải đấu (và nhiều hơn nữa)
  })
}

onMounted(async () => {
  fetchTournaments()
  
  try {
    const news = await newsService.getAllPosts({ limit: 4 })
    latestNews.value = (news || []).filter(n => n.status === 'published')
  } catch (err) {
    console.error('Lỗi tải tin tức:', err)
  }

  try {
    const rankings = await playerService.getRankings()
    topPlayers.value = (rankings || []).slice(0, 5)
  } catch (err) {
    console.error('Lỗi tải xếp hạng:', err)
  }
})

const normalizeDateKey = (value) => {
  if (!value || typeof value !== 'string') return ''
  const match = value.match(/^(\d{4}-\d{2}-\d{2})/)
  return match ? match[1] : value
}

const getMonthLabel = (date) => {
  return date.toLocaleString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { month: 'long', year: 'numeric' })
}

const getDay = (dateStr) => {
  if (!dateStr) return '?'
  return new Date(dateStr).getDate().toString().padStart(2, '0')
}

const getMonth = (dateStr) => {
  if (!dateStr) return '?'
  return (new Date(dateStr).getMonth() + 1).toString().padStart(2, '0')
}

const getStatusLabel = (status) => {
  const map = {
    'ongoing': t('tournaments.ongoing'),
    'pending': t('tournaments.upcoming'),
    'open': t('tournaments.upcoming'),
    'finished': t('tournaments.completed')
  }
  return map[status] || t('tournaments.upcoming')
}

const fallbackPosters = [
  '/poster-1.jpg',
  '/poster-2.jpg',
  '/poster-3.jpg',
  '/poster-4.jpg'
]

const getTournamentImage = (tour) => {
  if (tour.banner_url) return tour.banner_url;
  if (tour.media_url) return tour.media_url;
  const index = (tour.id || 0) % fallbackPosters.length;
  return fallbackPosters[index];
}

const groupedTournaments = computed(() => {
  let filtered = tournamentStore.tournaments || []

  if (activeFilter.value === 'ongoing') {
    filtered = filtered.filter(t => t.status === 'ongoing')
  } else if (activeFilter.value === 'upcoming') {
    filtered = filtered.filter(t => ['pending', 'open'].includes(t.status))
  } else if (activeFilter.value === 'completed') {
    filtered = filtered.filter(t => t.status === 'finished')
  } else if (activeFilter.value === 'my_tours') {
    filtered = filtered.filter(t => t.is_registered || t.is_mine || t.is_participant)
  }

  // Sorting: Ongoing (0) -> Open (1) -> Pending (2) -> Finished (3)
  const statusOrder = { 'ongoing': 0, 'open': 1, 'pending': 2, 'finished': 3 }
  
  return [...filtered].sort((a, b) => {
    const orderA = statusOrder[a.status] ?? 99
    const orderB = statusOrder[b.status] ?? 99
    
    if (orderA !== orderB) return orderA - orderB
    
    // Within same status, sort by date (newest first)
    return new Date(b.start_date) - new Date(a.start_date)
  })
})

const paginatedTournaments = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return groupedTournaments.value.slice(start, end)
})

const handlePageChange = (page) => {
  currentPage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const handleFilterChange = (filter) => {
  activeFilter.value = filter
  currentPage.value = 1
}

const viewDetail = (id) => {
  router.push({ name: 'tournament-detail', params: { id } })
}
</script>

<template>
  <div class="baseline-tournaments-page">
    
    <div class="container main-layout">
      
      <aside class="left-sidebar">
        <MarketingBannerStrip placement="tournaments_top" variant="sidebar" :max="2" />

        <div class="partners-widget">
          <h4 class="widget-title">{{ t('tournaments.partners') }}</h4>
          <div class="partner-list">
            <img src="/emirates.svg" alt="Partner 1" class="partner-img" onerror="this.style.display='none'"/>
            <img src="/haier.jpg" alt="Partner 2" class="partner-img" onerror="this.style.display='none'"/>
            <img src="/lexus.svg" alt="Partner 3" class="partner-img" onerror="this.style.display='none'"/>
            <img src="/nitto.svg" alt="Partner 4" class="partner-img" onerror="this.style.display='none'"/>
          </div>
        </div>
      </aside>

      <main class="center-content">
        
        <div class="baseline-header-controls">
          <div class="baseline-tabs">
            <button :class="{ active: activeFilter === 'all' }" @click="handleFilterChange('all')">{{ t('tournaments.all') }}</button>
            <button :class="{ active: activeFilter === 'ongoing' }" @click="handleFilterChange('ongoing')">{{ t('tournaments.ongoing') }}</button>
            <button :class="{ active: activeFilter === 'upcoming' }" @click="handleFilterChange('upcoming')">{{ t('tournaments.upcoming') }}</button>
            <button :class="{ active: activeFilter === 'completed' }" @click="handleFilterChange('completed')">{{ t('tournaments.completed') }}</button>
            <button :class="{ active: activeFilter === 'my_tours' }" @click="handleFilterChange('my_tours')">{{ t('tournaments.myTournaments') }}</button>
          </div>
          <div class="baseline-search">
            <el-input 
              v-model="searchQuery" 
              :placeholder="t('tournaments.searchPlaceholder')" 
              :prefix-icon="Search"
              clearable
              @input="fetchTournaments"
            />
          </div>
        </div>

        <div v-if="tournamentStore.loading" class="loading-state">
          <div class="spinner"></div>
          <p>{{ t('tournaments.loadingData') }}</p>
        </div>

        <div v-else class="tournament-feed">
          <div class="baseline-cards-wrapper">
            <article 
              v-for="tour in paginatedTournaments" 
              :key="tour.id" 
              class="baseline-card"
              :class="tour.status"
              @click="viewDetail(tour.id)"
            >
              <div class="card-hero-image">
                <img :src="getTournamentImage(tour)" alt="Tournament Banner" />
                
                <div class="badge-status" :class="tour.status">
                  <span v-if="tour.status === 'ongoing'" class="pulse-dot"></span>
                  <el-icon><Clock /></el-icon> {{ getStatusLabel(tour.status) }}
                </div>
                
                <div class="badge-location">
                  <el-icon><Location /></el-icon> {{ tour.location || t('tournaments.hcmc') }}
                </div>
              </div>

              <div class="card-info-section">
                <div class="date-block">
                  <div class="days-row">
                    <span class="day">{{ getDay(tour.start_date) }}</span>
                    <template v-if="tour.end_date && tour.end_date !== tour.start_date">
                      <span class="dot">.</span>
                      <span class="day">{{ getDay(tour.end_date) }}</span>
                    </template>
                  </div>
                  <div class="months-row">
                    <span class="month">{{ getMonth(tour.start_date) }}</span>
                    <template v-if="tour.end_date && tour.end_date !== tour.start_date">
                      <span class="space"></span>
                      <span class="month">{{ getMonth(tour.end_date) }}</span>
                    </template>
                  </div>
                </div>

                <div class="text-block">
                  <div class="organizer-info">
                    <el-icon class="org-icon"><Trophy /></el-icon>
                    <span class="org-name">{{ tour.category_type || t('tournaments.sgtSystem') }} - {{ tour.format_type === 'Singles' ? t('tournaments.singles') : t('tournaments.doubles') }}</span>
                  </div>
                  <h2 class="tournament-title">{{ tour.name }}</h2>
                </div>
              </div>
            </article>
          </div>

          <!-- Phân trang -->
          <div class="pagination-container" v-if="groupedTournaments.length > pageSize">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="groupedTournaments.length"
              layout="prev, pager, next"
              background
              @current-change="handlePageChange"
            />
          </div>

          <div v-if="groupedTournaments.length === 0" class="empty-state">
            <el-empty :description="t('tournaments.noTournamentsFound')" />
          </div>
        </div>
      </main>

      <aside class="right-sidebar">
        <div class="ad-banner mini">
          <img src="/ad-mini.jpg" alt="Sponsor Ad" />
        </div>

        <div class="widget">
          <div class="widget-header">
            <h4>{{ t('tournaments.highlightNews') }}</h4>
          </div>
          <div class="widget-body news-list">
            <div v-for="post in latestNews.slice(0, 3)" :key="post.id" class="news-item" @click="$router.push('/news/' + post.slug)">
              <img :src="post.thumbnail_url || '/poster-1.jpg'" />
              <p>{{ post.title }}</p>
            </div>
          </div>
        </div>
      </aside>

    </div>
  </div>
</template>

<style scoped>
/* Toàn bộ style được giữ nguyên hoàn toàn như cũ */
.baseline-tournaments-page { background: #f4f6f8; min-height: 100vh; padding-bottom: 4rem; width: 100%; overflow-x: hidden; }
.main-layout { display: grid; grid-template-columns: 280px minmax(0, 1fr) 280px; gap: 24px; padding-top: 2rem; align-items: start; width: 100%; max-width: 1280px; margin: 0 auto; box-sizing: border-box; }
.center-content { min-width: 0; width: 100%; }
.baseline-header-controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; gap: 16px; }
.baseline-tabs { display: flex; flex: 1; background: #ffffff; padding: 4px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); overflow-x: auto; scrollbar-width: none; }
.baseline-tabs::-webkit-scrollbar { display: none; }
.baseline-tabs button { border: none; background: transparent; padding: 8px 16px; font-size: 0.9rem; font-weight: 600; color: #475569; border-radius: 6px; cursor: pointer; white-space: nowrap; transition: all 0.2s; }
.baseline-tabs button:hover { background: #f1f5f9; }
.baseline-tabs button.active { background: #002855; color: #ffffff; }
.baseline-search { width: 185px; flex-shrink: 0; }
:deep(.baseline-search .el-input__wrapper) { border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.baseline-card { border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; cursor: pointer; transition: transform 0.2s ease, box-shadow 0.2s ease; background: #fff; }
.baseline-card.ongoing { border-color: rgba(220, 38, 38, 0.3); border-left: 4px solid #dc2626; }
.baseline-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.08); }
.card-hero-image { position: relative; width: 100%; height: 280px; background: #1e293b; }
.card-hero-image img { width: 100%; height: 100%; object-fit: cover; }
.badge-status { position: absolute; top: 16px; left: 16px; background: rgba(15, 23, 42, 0.85); color: #ffffff; padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: flex; align-items: center; gap: 6px; backdrop-filter: blur(4px); }
.badge-status.ongoing { background: rgba(220, 38, 38, 0.9); }
.badge-status.finished { background: rgba(100, 116, 139, 0.9); }

.pulse-dot { width: 8px; height: 8px; background: #fff; border-radius: 50%; box-shadow: 0 0 0 rgba(255, 255, 255, 0.4); animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(255, 255, 255, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); } }

.pagination-container { display: flex; justify-content: center; margin-top: 3rem; padding-bottom: 2rem; }
:deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) { background-color: #002855; }
.baseline-cards-wrapper { display: flex; flex-direction: column; gap: 24px; }
.baseline-card { border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; cursor: pointer; transition: transform 0.2s ease, box-shadow 0.2s ease; background: #fff; }
.baseline-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.08); }
.card-hero-image { position: relative; width: 100%; height: 280px; background: #1e293b; }
.card-hero-image img { width: 100%; height: 100%; object-fit: cover; }
.badge-status { position: absolute; top: 16px; left: 16px; background: rgba(15, 23, 42, 0.85); color: #ffffff; padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: flex; align-items: center; gap: 6px; backdrop-filter: blur(4px); }
.badge-location { position: absolute; bottom: 16px; left: 16px; background: #ffffff; color: #0f172a; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; display: flex; align-items: center; gap: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-width: 80%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.card-info-section { display: flex; padding: 20px; gap: 24px; align-items: center; }
.date-block { display: flex; flex-direction: column; align-items: center; min-width: 80px; border-right: 1px solid #e2e8f0; padding-right: 24px; }
.days-row { display: flex; align-items: baseline; gap: 6px; }
.days-row .day { font-size: 2rem; font-weight: 800; color: #0f172a; line-height: 1; }
.days-row .dot { font-size: 1.5rem; font-weight: 800; color: #94a3b8; transform: translateY(-4px); }
.months-row { display: flex; gap: 22px; margin-top: 4px; }
.months-row .month { font-size: 0.9rem; font-weight: 600; color: #64748b; }
.text-block { flex: 1; min-width: 0; }
.organizer-info { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.org-icon { background: #002855; color: #fff; padding: 4px; border-radius: 50%; font-size: 0.8rem; }
.org-name { font-size: 0.85rem; font-weight: 600; color: #475569; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.tournament-title { font-size: 1.25rem; font-weight: 700; color: #0f172a; margin: 0; line-height: 1.4; word-wrap: break-word; }
.ad-banner { background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.03); margin-bottom: 24px; }
.ad-banner img { width: 100%; height: 200px; object-fit: cover; display: block; }
.ad-banner.mini img { height: 350px; }
.ad-content { padding: 16px; background: #002855; color: #ffffff; }
.ad-content h4 { margin: 0 0 8px; font-weight: 800; font-size: 1.1rem; }
.ad-content p { margin: 0; font-size: 0.85rem; font-weight: 500; opacity: 0.9; }
.widget-title { font-size: 1rem; color: #64748b; text-transform: uppercase; margin-bottom: 12px; }
.partner-img { width: 100%; height: 120px; object-fit: contain; background: #fff; border-radius: 12px; margin-bottom: 16px; border: 1px solid #f1f5f9; padding: 10px;}
.widget { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.03); overflow: hidden; }
.widget-header { padding: 16px; border-bottom: 1px solid #f1f5f9; }
.widget-header h4 { margin: 0; font-size: 1rem; font-weight: 700; }
.news-list { padding: 16px; display: flex; flex-direction: column; gap: 16px; }
.news-item { display: flex; gap: 12px; cursor: pointer; }
.news-item img { width: 70px; height: 70px; border-radius: 8px; object-fit: cover; flex-shrink: 0;}
.news-item p { margin: 0; font-size: 0.9rem; font-weight: 600; line-height: 1.4; color: #1e293b; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;}
@media (max-width: 1200px) { .main-layout { grid-template-columns: 250px minmax(0, 1fr); } .right-sidebar { display: none; } }
@media (max-width: 992px) { .main-layout { grid-template-columns: minmax(0, 1fr); } .left-sidebar { display: none; } }
@media (max-width: 768px) { 
  .baseline-header-controls { flex-direction: column; align-items: stretch; } 
  .baseline-tabs { width: 100%; padding-bottom: 8px; } 
  .baseline-search { width: 100%; } 
  .card-info-section { flex-direction: row; align-items: center; gap: 16px; padding: 16px; } 
  .date-block { border-right: 1px solid #e2e8f0; border-bottom: none; padding-right: 24px; padding-bottom: 0; width: auto; flex-direction: column; align-items: center; gap: 4px; } 
  .months-row { margin-top: 4px; } 
  .days-row .day { font-size: 1.8rem; } 
  .card-hero-image { height: 220px; } 
  .tournament-feed { padding: 0; }
}
@media (max-width: 480px) { 
  .card-info-section { flex-direction: column; align-items: flex-start; gap: 12px; }
  .date-block { border-right: none; border-bottom: 1px solid #e2e8f0; padding-right: 0; padding-bottom: 12px; width: 100%; flex-direction: row; justify-content: flex-start; gap: 12px; }
  .tournament-title { font-size: 1.1rem; } 
  .badge-location { font-size: 0.75rem; padding: 4px 10px; } 
  .badge-status { font-size: 0.7rem; padding: 4px 10px; } 
}
.loading-state { text-align: center; padding: 4rem; }
.spinner { width: 40px; height: 40px; border: 4px solid rgba(0,0,0,0.05); border-top-color: #002855; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
