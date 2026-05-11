<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTournamentStore } from '../../../stores/tournament'
import { newsService } from '../../../services/newsService'
import { playerService } from '../../../services/playerService'
import { Search, Location, Clock, Trophy } from '@element-plus/icons-vue'
import { currentLocale, t } from '../../../utils/locale'

const router = useRouter()
const isVideo = (url) => {
  if (!url) return false
  return url.match(/\.(mp4|webm|ogg|mov)(\?.*)?$/i) !== null
}

const tournamentStore = useTournamentStore()
const searchQuery = ref('')
const activeFilter = ref('upcoming') // 'ongoing', 'upcoming', 'completed', 'my_tours'

const latestNews = ref([])
const topPlayers = ref([])

const fetchTournaments = () => {
  tournamentStore.fetchTournaments({ search: searchQuery.value })
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

// === LOGIC NGÀY THÁNG & TRẠNG THÁI (GIỮ NGUYÊN) ===
const getDay = (dateStr) => {
  if (!dateStr) return '?'
  return new Date(dateStr).getDate().toString().padStart(2, '0')
}

const getMonth = (dateStr) => {
  if (!dateStr) return '?'
  return (new Date(dateStr).getMonth() + 1).toString().padStart(2, '0')
}

const getMonthYearLabel = (dateStr) => {
  if (!dateStr) return 'Khác'
  const date = new Date(dateStr)
  return `Tháng ${date.getMonth() + 1}/${date.getFullYear()}`
}

const getStatusLabel = (status) => {
  const map = {
    'ongoing': 'Đang diễn ra',
    'pending': 'Sắp diễn ra',
    'open': 'Sắp diễn ra',
    'finished': 'Hoàn thành'
  }
  return map[status] || 'Sắp diễn ra'
}

// === LOGIC HÌNH ẢNH LINH ĐỘNG TỪ FOLDER PUBLIC ===
const fallbackPosters = [
  '/poster-1.jpg',
  '/poster-2.jpg',
  '/poster-3.jpg'
]

const getTournamentImage = (tour) => {
  // Nếu có ảnh thật từ Database (Cloudinary/AWS) thì dùng ảnh thật
  if (tour.media_url) return tour.media_url;
  
  // Nếu không, lấy ngẫu nhiên xoay vòng từ public folder dựa trên ID để không bị giật đổi ảnh liên tục
  const index = (tour.id || 0) % fallbackPosters.length;
  return fallbackPosters[index];
}

// Lọc và Nhóm giải đấu theo tháng
const groupedTournaments = computed(() => {
  let filtered = tournamentStore.tournaments || []

  // Áp dụng bộ lọc Tabs
  if (activeFilter.value === 'ongoing') {
    filtered = filtered.filter(t => t.status === 'ongoing')
  } else if (activeFilter.value === 'upcoming') {
    filtered = filtered.filter(t => ['pending', 'open'].includes(t.status))
  } else if (activeFilter.value === 'completed') {
    filtered = filtered.filter(t => t.status === 'finished')
  }

  const groups = {}
  filtered.forEach(tour => {
    const monthYear = getMonthYearLabel(tour.start_date)
    if (!groups[monthYear]) groups[monthYear] = []
    groups[monthYear].push(tour)
  })
  return groups
})

const viewDetail = (id) => {
  router.push({ name: 'tournament-detail', params: { id } })
}
</script>

<template>
  <div class="baseline-tournaments-page">
    
    <div class="container main-layout">
      
      <!-- CỘT TRÁI (WIDGETS QUẢNG CÁO / ĐỐI TÁC TRONG FOLDER PUBLIC) -->
      <aside class="left-sidebar">
        <div class="ad-banner">
          <!-- Gọi ảnh từ public/ad-main.jpg -->
          <img src="/ad-main.jpg" alt="Sponsor Ad" onerror="this.src='https://images.unsplash.com/photo-1622279457486-62dcc4a431d6?auto=format&fit=crop&q=80&w=400'" />
          <div class="ad-content">
            <h4>Ứng dụng số hoá Tennis</h4>
            <p>Trải nghiệm hệ thống Saigontennistours ngay hôm nay!</p>
          </div>
        </div>

        <div class="partners-widget">
          <h4 class="widget-title">Đối tác</h4>
          <div class="partner-list">
            <!-- Gọi ảnh từ public/partner-1.png -->
            <img src="/partner-1.png" alt="Partner 1" class="partner-img" onerror="this.style.display='none'"/>
            <img src="/partner-2.png" alt="Partner 2" class="partner-img" onerror="this.style.display='none'"/>
          </div>
        </div>
      </aside>

      <!-- CỘT GIỮA (DANH SÁCH GIẢI ĐẤU) -->
      <main class="center-content">
        
        <!-- HEADER & TABS -->
        <div class="baseline-header-controls">
          <div class="baseline-tabs">
            <button :class="{ active: activeFilter === 'ongoing' }" @click="activeFilter = 'ongoing'">Đang diễn ra</button>
            <button :class="{ active: activeFilter === 'upcoming' }" @click="activeFilter = 'upcoming'">Sắp diễn ra</button>
            <button :class="{ active: activeFilter === 'completed' }" @click="activeFilter = 'completed'">Hoàn thành</button>
            <button :class="{ active: activeFilter === 'my_tours' }" @click="activeFilter = 'my_tours'">Giải của tôi</button>
          </div>
          <div class="baseline-search">
            <el-input 
              v-model="searchQuery" 
              placeholder="Tìm kiếm giải đấu..." 
              :prefix-icon="Search"
              clearable
              @input="fetchTournaments"
            />
          </div>
        </div>

        <!-- TRẠNG THÁI LOADING -->
        <div v-if="tournamentStore.loading" class="loading-state">
          <div class="spinner"></div>
          <p>{{ t('common.loading') }}...</p>
        </div>

        <!-- DANH SÁCH THEO THÁNG -->
        <div v-else class="tournament-feed">
          <div v-for="(tournaments, month) in groupedTournaments" :key="month" class="month-block">
            <h3 class="month-title">{{ month }}</h3>

            <div class="baseline-cards-wrapper">
              <article 
                v-for="tour in tournaments" 
                :key="tour.id" 
                class="baseline-card"
                @click="viewDetail(tour.id)"
              >
                <!-- 1. Phần hình ảnh Banner -->
                <div class="card-hero-image">
                  <!-- Lấy ảnh linh động từ hàm vừa tạo -->
                  <img :src="getTournamentImage(tour)" alt="Tournament Banner" />
                  
                  <div class="badge-status">
                    <el-icon><Clock /></el-icon> {{ getStatusLabel(tour.status) }}
                  </div>
                  
                  <div class="badge-location">
                    <el-icon><Location /></el-icon> {{ tour.location || 'Hồ Chí Minh' }}
                  </div>
                </div>

                <!-- 2. Phần thông tin (Dates & Title) -->
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
                      <span class="org-name">{{ tour.category_type || 'Hệ thống SGT' }} - {{ tour.format_type === 'Singles' ? 'Đơn' : 'Đôi' }}</span>
                    </div>
                    <h2 class="tournament-title">{{ tour.name }}</h2>
                  </div>
                </div>
              </article>
            </div>
          </div>

          <div v-if="Object.keys(groupedTournaments).length === 0" class="empty-state">
            <el-empty description="Không tìm thấy giải đấu nào phù hợp" />
          </div>
        </div>
      </main>

      <!-- CỘT PHẢI (WIDGETS TIN TỨC VÀ RANKING) -->
      <aside class="right-sidebar">
        <!-- Gọi ảnh từ public/ad-mini.jpg -->
        <div class="ad-banner mini">
          <img src="/ad-mini.jpg" alt="Sponsor Ad" onerror="this.src='https://images.unsplash.com/photo-1599586120429-48281b6f0ece?auto=format&fit=crop&q=80&w=300'" />
        </div>

        <div class="widget">
          <div class="widget-header">
            <h4>Tin tức nổi bật</h4>
          </div>
          <div class="widget-body news-list">
            <div v-for="post in latestNews.slice(0, 3)" :key="post.id" class="news-item" @click="$router.push('/news/' + post.slug)">
              <img :src="post.thumbnail_url || '/poster-1.jpg'" onerror="this.src='https://images.unsplash.com/photo-1595435064214-079678c18789?auto=format&fit=crop&q=80&w=150'" />
              <p>{{ post.title }}</p>
            </div>
          </div>
        </div>
      </aside>

    </div>
  </div>
</template>

<style scoped>
/* CSS ĐƯỢC GIỮ NGUYÊN HOÀN TOÀN TỪ BẢN TRƯỚC */
.baseline-tournaments-page { background: #f4f6f8; min-height: 100vh; padding-bottom: 4rem; }
.main-layout { display: grid; grid-template-columns: 280px 1fr 280px; gap: 24px; padding-top: 2rem; align-items: start; }
.baseline-header-controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; gap: 16px; }
.baseline-tabs { display: flex; background: #ffffff; padding: 4px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); overflow-x: auto; }
.baseline-tabs button { border: none; background: transparent; padding: 10px 20px; font-size: 0.9rem; font-weight: 600; color: #475569; border-radius: 6px; cursor: pointer; white-space: nowrap; transition: all 0.2s; }
.baseline-tabs button:hover { background: #f1f5f9; }
.baseline-tabs button.active { background: #002855; color: #ffffff; }
.baseline-search { width: 250px; }
:deep(.baseline-search .el-input__wrapper) { border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.month-block { background: #ffffff; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.03); }
.month-title { background: #f8fafc; padding: 12px 20px; border-radius: 8px; font-size: 1.1rem; font-weight: 700; color: #1e293b; margin-top: 0; margin-bottom: 20px; }
.baseline-cards-wrapper { display: flex; flex-direction: column; gap: 24px; }
.baseline-card { border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; cursor: pointer; transition: transform 0.2s ease, box-shadow 0.2s ease; background: #fff; }
.baseline-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.08); }
.card-hero-image { position: relative; width: 100%; height: 280px; background: #1e293b; }
.card-hero-image img { width: 100%; height: 100%; object-fit: cover; }
.badge-status { position: absolute; top: 16px; left: 16px; background: rgba(15, 23, 42, 0.85); color: #ffffff; padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: flex; align-items: center; gap: 6px; backdrop-filter: blur(4px); }
.badge-location { position: absolute; bottom: 16px; left: 16px; background: #ffffff; color: #0f172a; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; display: flex; align-items: center; gap: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.card-info-section { display: flex; padding: 20px; gap: 24px; align-items: center; }
.date-block { display: flex; flex-direction: column; align-items: center; min-width: 80px; border-right: 1px solid #e2e8f0; padding-right: 24px; }
.days-row { display: flex; align-items: baseline; gap: 6px; }
.days-row .day { font-size: 2rem; font-weight: 800; color: #0f172a; line-height: 1; }
.days-row .dot { font-size: 1.5rem; font-weight: 800; color: #94a3b8; transform: translateY(-4px); }
.months-row { display: flex; gap: 22px; margin-top: 4px; }
.months-row .month { font-size: 0.9rem; font-weight: 600; color: #64748b; }
.text-block { flex: 1; }
.organizer-info { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.org-icon { background: #002855; color: #fff; padding: 4px; border-radius: 50%; font-size: 0.8rem; }
.org-name { font-size: 0.85rem; font-weight: 600; color: #475569; }
.tournament-title { font-size: 1.25rem; font-weight: 700; color: #0f172a; margin: 0; line-height: 1.4; }
.ad-banner { background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.03); margin-bottom: 24px; }
.ad-banner img { width: 100%; height: 200px; object-fit: cover; display: block; }
.ad-banner.mini img { height: 350px; }
.ad-content { padding: 16px; background: #c1ff72; color: #002855; }
.ad-content h4 { margin: 0 0 8px; font-weight: 800; font-size: 1.1rem; }
.ad-content p { margin: 0; font-size: 0.85rem; font-weight: 500; }
.widget-title { font-size: 1rem; color: #64748b; text-transform: uppercase; margin-bottom: 12px; }
.partner-img { width: 100%; height: 120px; object-fit: contain; background: #fff; border-radius: 12px; margin-bottom: 16px; border: 1px solid #f1f5f9; }
.widget { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.03); overflow: hidden; }
.widget-header { padding: 16px; border-bottom: 1px solid #f1f5f9; }
.widget-header h4 { margin: 0; font-size: 1rem; font-weight: 700; }
.news-list { padding: 16px; display: flex; flex-direction: column; gap: 16px; }
.news-item { display: flex; gap: 12px; cursor: pointer; }
.news-item img { width: 70px; height: 70px; border-radius: 8px; object-fit: cover; }
.news-item p { margin: 0; font-size: 0.9rem; font-weight: 600; line-height: 1.4; color: #1e293b; }
@media (max-width: 1200px) { .main-layout { grid-template-columns: 250px 1fr; } .right-sidebar { display: none; } }
@media (max-width: 900px) { .main-layout { grid-template-columns: 1fr; } .left-sidebar { display: none; } .baseline-header-controls { flex-direction: column; align-items: stretch; } .baseline-tabs { overflow-x: auto; white-space: nowrap; padding-bottom: 4px;} .baseline-search { width: 100%; } }
@media (max-width: 600px) { .card-info-section { flex-direction: column; align-items: flex-start; gap: 16px; } .date-block { border-right: none; border-bottom: 1px solid #e2e8f0; padding-right: 0; padding-bottom: 16px; width: 100%; flex-direction: row; align-items: center; gap: 16px;} .months-row { margin-top: 0; } .days-row .day { font-size: 1.5rem; } .card-hero-image { height: 200px; } }
.loading-state { text-align: center; padding: 4rem; }
.spinner { width: 40px; height: 40px; border: 4px solid rgba(0,0,0,0.05); border-top-color: #002855; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>