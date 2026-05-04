<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { newsService } from '../../../services/newsService'
import { playerService } from '../../../services/playerService' 
import { Search, VideoPlay, ArrowDown } from '@element-plus/icons-vue' // Thêm ArrowDown
import { currentLocale, t } from '../../../utils/locale'

const router = useRouter()
const newsList = ref([])
const topPlayers = ref([]) 
const loading = ref(true)
const searchQuery = ref('')
const selectedCategory = ref('all') 

// LOGIC MỚI: Dùng object để map chính xác label (hiển thị) và value (gửi API)
const categories = computed(() => [
  { label: t('news.all') || 'Tất cả', value: 'all' },
  { label: t('news.typeAnnouncement') || 'Thông báo', value: 'announcement' },
  { label: t('news.highlight') || 'Highlight', value: 'highlight' },
  { label: t('news.analysis') || 'Phân tích', value: 'analysis' },
  { label: t('news.interview') || 'Phỏng vấn', value: 'interview' }
])

const isVideo = (url) => {
  if (!url) return false
  return url.match(/\.(mp4|webm|ogg)$/i) !== null
}

const fetchNewsAndRankings = async () => {
  loading.value = true
  try {
    const params = { limit: 100 }
    
    // Gửi đúng value tiếng Anh xuống Backend
    if (selectedCategory.value !== 'all') {
      params.category = selectedCategory.value
    }
    if (searchQuery.value) {
      params.search = searchQuery.value
    }

    const [newsData, rankingsData] = await Promise.all([
      newsService.getAllPosts(params),
      playerService.getRankings().catch(() => [])
    ])

    let results = (newsData || [])
      .filter(item => item.status === 'published')
      .sort((a, b) => new Date(b.publish_at || b.created_at) - new Date(a.publish_at || a.created_at))
    newsList.value = results

    topPlayers.value = (rankingsData || []).slice(0, 5)

  } catch (err) {
    console.error('Lỗi tải dữ liệu:', err)
  } finally {
    loading.value = false
  }
}

watch(selectedCategory, () => fetchNewsAndRankings())

let searchTimeout = null
watch(searchQuery, () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => fetchNewsAndRankings(), 500)
})

const featuredPost = computed(() => newsList.value[0])
const remainingPosts = computed(() => newsList.value.slice(1))

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { day: '2-digit', month: 'short', year: 'numeric' })
}

const getCategoryLabel = (val) => {
  const cat = categories.value.find(c => c.value === val)
  return cat ? cat.label : (t('nav.news') || 'TIN TỨC')
}

onMounted(fetchNewsAndRankings)
</script>

<template>
  <div class="atp-news-page" v-loading="loading">
    <div class="container">
      
      <!-- MENU BỘ LỌC CŨ (GỌN GÀNG, KHÔNG BỊ ĐÈ LAYOUT) -->
      <nav class="news-inner-nav">
        <div class="nav-brand">
          <span class="l-label">{{ t('news.latest') || 'LATEST' }}</span>
          <span class="separator">|</span>
          <el-dropdown trigger="click">
            <span class="el-dropdown-link">
              {{ selectedCategory === 'all' ? (t('nav.news') || 'NEWS') : getCategoryLabel(selectedCategory) }} 
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item 
                  v-for="cat in categories" 
                  :key="cat.value" 
                  @click="selectedCategory = cat.value"
                >
                  {{ cat.label }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        
        <div class="nav-search">
           <el-input 
             v-model="searchQuery" 
             :placeholder="t('news.searchPlaceholder') || 'Tìm kiếm tin tức...'" 
             :prefix-icon="Search" 
             clearable 
             class="minimal-search" 
           />
        </div>
      </nav>

      <!-- BỐ CỤC NỘI DUNG MỚI (TRÁI: TIN TỨC | PHẢI: BXH) -->
      <div class="magazine-layout">
        
        <!-- CỘT CHÍNH: HIỂN THỊ TOÀN BỘ TIN TỨC -->
        <main class="news-main-feed">
          
          <!-- Bài nổi bật (Hero) -->
          <div v-if="featuredPost" class="featured-card" @click="$router.push('/news/' + featuredPost.slug)">
            <figure class="featured-visual">
              <video 
                v-if="isVideo(featuredPost.thumbnail_url || featuredPost.media_url)" 
                :src="featuredPost.thumbnail_url || featuredPost.media_url" 
                autoplay loop muted playsinline>
              </video>
              <img 
                v-else 
                :src="featuredPost.thumbnail_url || 'https://images.unsplash.com/photo-1595435934249-5df7ed86e1f4?auto=format&fit=crop&q=80&w=1200'" 
                :alt="featuredPost.title" 
              />
              <span class="play-icon-large" v-if="isVideo(featuredPost.thumbnail_url || featuredPost.media_url)">
                <el-icon><VideoPlay /></el-icon>
              </span>
            </figure>

            <div class="featured-content">
              <span class="category-badge">{{ getCategoryLabel(featuredPost.category) }}</span>
              <h1 class="featured-title">{{ featuredPost.title }}</h1>
              <p class="featured-excerpt">{{ featuredPost.summary }}</p>
              <span class="post-date">{{ formatDate(featuredPost.publish_at || featuredPost.created_at) }}</span>
            </div>
          </div>
          
          <!-- Grid các bài còn lại -->
          <div v-if="remainingPosts.length > 0" class="news-grid">
            <article 
              v-for="post in remainingPosts" 
              :key="post.id" 
              class="grid-news-card" 
              @click="$router.push('/news/' + post.slug)"
            >
              <div class="grid-thumb">
                <video 
                  v-if="isVideo(post.thumbnail_url || post.media_url)" 
                  :src="post.thumbnail_url || post.media_url" 
                  autoplay loop muted playsinline>
                </video>
                <img 
                  v-else 
                  :src="post.thumbnail_url || 'https://images.unsplash.com/photo-1592709823125-a191f07a2a5e?auto=format&fit=crop&q=80&w=600'" 
                />
                <span class="play-icon-small" v-if="isVideo(post.thumbnail_url || post.media_url)">▶</span>
                <span class="grid-cat-badge">{{ getCategoryLabel(post.category) }}</span>
              </div>
              <div class="grid-content">
                <h4 class="grid-title">{{ post.title }}</h4>
                <span class="grid-date">{{ formatDate(post.publish_at || post.created_at) }}</span>
              </div>
            </article>
          </div>

          <div v-if="!featuredPost" class="empty-placeholder">
            <el-empty :description="t('news.noNews') || 'Không có tin tức nào phù hợp'" />
          </div>
        </main>

        <!-- CỘT PHỤ: RANKINGS & WIDGETS -->
        <aside class="sidebar-widgets">
          
          <!-- Widget BXH -->
          <div class="atp-widget rankings-widget">
            <div class="widget-header">
              <h3><span class="pif-logo">PIF</span> ATP RANKINGS</h3>
              <router-link to="/rankings" class="view-all">View All ➔</router-link>
            </div>
            
            <div class="widget-body ranking-list">
              <div v-for="(player, index) in topPlayers" :key="player.player_id" class="ranking-row">
                <div class="rank-pos">{{ index + 1 }}</div>
                <div class="rank-name"><span class="flag"></span> {{ player.full_name }}</div>
                <div class="rank-pts">{{ player.elo_points }}</div>
              </div>
              <div v-if="topPlayers.length === 0" class="empty-state">Đang cập nhật...</div>
            </div>
          </div>

          <!-- Widget Newsletter -->
          <div class="atp-widget newsletter-widget">
            <h3>NEWSLETTERS</h3>
            <p>Đăng ký để nhận thông tin mới nhất về giải đấu, tin tức và các ưu đãi đặc quyền từ Saigon Tennis Tour.</p>
            <div class="input-group">
              <input type="email" placeholder="Nhập email của bạn..." />
              <button>ĐĂNG KÝ ✉</button>
            </div>
          </div>

        </aside>

      </div>
    </div>
  </div>
</template>

<style scoped>
/* TỔNG QUAN THEME */
.atp-news-page {
  background: #f1f5f9; 
  min-height: 100vh;
  padding-bottom: 5rem;
  padding-top: 1.5rem; /* Cách xa header tổng ở trên */
  font-family: 'Inter', Arial, sans-serif;
  color: #0f172a;
}

.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* MENU BỘ LỌC CŨ (SẠCH SẼ, TRẮNG) */
.news-inner-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 0;
  border-bottom: 2px solid #e2e8f0;
  margin-bottom: 2.5rem;
}

.nav-brand {
  display: flex;
  align-items: center;
  font-weight: 800;
  font-size: 1.4rem;
  text-transform: uppercase;
}

.l-label { color: #002855; }
.separator { margin: 0 12px; color: #cbd5e1; }
.el-dropdown-link {
  cursor: pointer;
  color: #0f172a;
  display: flex;
  align-items: center;
  font-size: 1.4rem;
  font-weight: 800;
  outline: none;
}

.minimal-search { width: 300px; }
:deep(.minimal-search .el-input__wrapper) {
  box-shadow: none;
  border-bottom: 2px solid #cbd5e1;
  border-radius: 0;
  padding: 0;
  background: transparent;
}
:deep(.minimal-search .el-input__wrapper.is-focus) {
  border-bottom-color: #002855;
}

/* BỐ CỤC CHÍNH 2 CỘT */
.magazine-layout {
  display: grid;
  grid-template-columns: 2fr 1fr; /* Tỉ lệ 2/3 - 1/3 */
  gap: 2.5rem;
}

/* CỘT TRÁI: TIN TỨC CHÍNH */
.news-main-feed {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Featured Post */
.featured-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(0,0,0,0.03);
  transition: transform 0.3s, box-shadow 0.3s;
}
.featured-card:hover { 
  transform: translateY(-4px); 
  box-shadow: 0 10px 25px rgba(0,0,0,0.08);
  border-color: #002855; 
}

.featured-visual {
  position: relative;
  width: 100%;
  height: 420px;
  margin: 0;
  background: #000;
}
.featured-visual img, .featured-visual video {
  width: 100%; height: 100%; object-fit: cover;
}
.play-icon-large {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  font-size: 4rem; color: white; background: rgba(0,0,0,0.5);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
}

.featured-content { padding: 2rem; }
.category-badge {
  display: inline-block; background: #c1ff72; color: #002855;
  font-size: 0.75rem; font-weight: 800; padding: 0.3rem 0.8rem;
  text-transform: uppercase; margin-bottom: 1rem;
}
.featured-title {
  font-size: 2.2rem; line-height: 1.2; font-weight: 800;
  color: #0f172a; margin-bottom: 1rem; letter-spacing: -0.02em;
}
.featured-excerpt {
  font-size: 1.1rem; line-height: 1.6; color: #475569; margin-bottom: 1.5rem;
}
.post-date, .grid-date {
  font-size: 0.8rem; font-weight: 600; color: #94a3b8; text-transform: uppercase;
}

/* Lưới Tin Tức Bên Dưới */
.news-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.grid-news-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s, box-shadow 0.3s;
}
.grid-news-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.05);
  border-color: #002855;
}

.grid-thumb {
  position: relative;
  height: 200px;
  background: #000;
}
.grid-thumb img, .grid-thumb video { width: 100%; height: 100%; object-fit: cover; }
.grid-cat-badge {
  position: absolute; top: 12px; left: 12px;
  background: #002855; color: white;
  font-size: 0.65rem; font-weight: 700;
  padding: 0.25rem 0.6rem; border-radius: 4px; text-transform: uppercase;
}
.play-icon-small {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 40px; height: 40px; background: rgba(0,0,0,0.6);
  color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 1rem; padding-left: 3px;
}

.grid-content { padding: 1.5rem; display: flex; flex-direction: column; flex: 1;}
.grid-title {
  font-size: 1.15rem; font-weight: 700; line-height: 1.4;
  color: #0f172a; margin-bottom: 1rem; flex: 1;
}

/* CỘT PHẢI: WIDGETS */
.sidebar-widgets {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.atp-widget {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.02);
}

.widget-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1.2rem 1.5rem; border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}
.widget-header h3 {
  font-size: 1.1rem; font-style: italic; font-weight: 800;
  color: #002855; margin: 0; display: flex; align-items: center; gap: 6px;
}
.pif-logo { background: #000; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-style: normal;}
.view-all { font-size: 0.8rem; color: #002855; text-decoration: none; font-weight: 600; }

.ranking-list { padding: 0; }
.ranking-row {
  display: flex; align-items: center; padding: 0.8rem 1.25rem; border-bottom: 1px solid #f1f5f9;
}
.ranking-row:last-child { border-bottom: none; }
.rank-pos { width: 30px; font-weight: 700; color: #64748b; }
.rank-name { flex: 1; display: flex; align-items: center; gap: 0.5rem; font-weight: 600; font-size: 0.95rem; color: #0f172a;}
.rank-pts { font-weight: 800; color: #002855; font-size: 0.95rem; }
.empty-state { padding: 2rem; text-align: center; color: #94a3b8; font-size: 0.9rem; }

.newsletter-widget {
  background: #002855; color: white; padding: 2rem 1.5rem; text-align: center;
}
.newsletter-widget h3 { font-size: 1.2rem; font-weight: 800; margin-bottom: 1rem; }
.newsletter-widget p { font-size: 0.85rem; line-height: 1.5; margin-bottom: 1.5rem; color: #cbd5e1; }
.input-group { display: flex; flex-direction: column; gap: 0.5rem; }
.input-group input { padding: 0.8rem; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2); background: transparent; color: white; }
.input-group input::placeholder { color: rgba(255,255,255,0.6); }
.input-group button { padding: 0.8rem; border-radius: 4px; border: none; background: #c1ff72; color: #002855; font-weight: 800; cursor: pointer; transition: 0.2s; }
.input-group button:hover { background: white; }

/* RESPONSIVE */
@media (max-width: 1024px) {
  .magazine-layout { grid-template-columns: 1fr; }
  .featured-visual { height: 350px; }
}

@media (max-width: 768px) {
  .news-inner-nav { flex-direction: column; align-items: flex-start; gap: 1rem; }
  .minimal-search { width: 100%; }
  .news-grid { grid-template-columns: 1fr; }
  .featured-visual { height: 250px; }
  .featured-title { font-size: 1.6rem; }
  .featured-excerpt { display: none; } 
  .featured-content { padding: 1.5rem; }
}
</style>