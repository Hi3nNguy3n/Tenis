<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '../../../services/apiClient'
import { Calendar, Timer, ArrowRight, Search, Collection } from '@element-plus/icons-vue'

const newsList = ref([])
const loading = ref(true)
const searchQuery = ref('')
const selectedCategory = ref('Tất cả')

const categories = ['Tất cả', 'Thông báo', 'Highlight', 'Phân tích', 'Phỏng vấn']

const fetchNews = async () => {
  loading.value = true
  try {
    const data = await apiClient.get('/api/news/')
    newsList.value = data.filter(item => item.status === 'published')
  } catch (err) {
    console.error('Lỗi tải tin tức:', err)
  } finally {
    loading.value = false
  }
}

// Lọc tin tức theo search và category
const filteredNews = computed(() => {
  return newsList.value.filter(post => {
    const titleMatch = post.title.toLowerCase().includes(searchQuery.value.toLowerCase())
    const catMatch = selectedCategory.value === 'Tất cả' || post.category === selectedCategory.value
    return titleMatch && catMatch
  })
})

const featuredPost = computed(() => filteredNews.value[0])
const remainingNews = computed(() => filteredNews.value.slice(1))

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

onMounted(fetchNews)
</script>

<template>
  <div class="news-portal" v-loading="loading">
    <header class="magazine-header">
      <div class="container">
        <div class="header-content">
          <div>
            <span class="kicker">Saigon Tennis Tours</span>
            <h1>Tạp chí Tennis</h1>
            <p>Cập nhật nhịp đập, highlight và phân tích chuyên sâu</p>
          </div>
          <div class="search-wrapper">
            <el-input v-model="searchQuery" placeholder="Tìm bài viết..." :prefix-icon="Search" class="search-input" />
          </div>
        </div>
      </div>
    </header>

    <div class="container main-layout">
      <div class="main-column">
        <div v-if="featuredPost" class="featured-box" @click="$router.push('/news/' + featuredPost.slug)">
          <div class="featured-img-container">
            <img :src="featuredPost.thumbnail_url" alt="featured" />
            <div class="featured-info">
              <el-tag effect="dark" type="danger">MỚI NHẤT</el-tag>
              <h2>{{ featuredPost.title }}</h2>
              <p>{{ featuredPost.summary }}</p>
              <div class="meta-info">
                <el-icon><Calendar /></el-icon> {{ formatDate(featuredPost.created_at) }}
              </div>
            </div>
          </div>
        </div>

        <div class="news-grid">
          <div v-for="post in remainingNews" :key="post.id" class="post-card" @click="$router.push('/news/' + post.slug)">
            <div class="post-thumb">
              <img :src="post.thumbnail_url" />
              <span class="cat-pill">{{ post.category }}</span>
            </div>
            <div class="post-content">
              <div class="post-date"><el-icon><Timer /></el-icon> {{ formatDate(post.created_at) }}</div>
              <h3>{{ post.title }}</h3>
              <p>{{ post.summary }}</p>
              <div class="read-more">Xem chi tiết <el-icon><ArrowRight /></el-icon></div>
            </div>
          </div>
        </div>
        
        <el-empty v-if="filteredNews.length === 0 && !loading" description="Không tìm thấy bài viết nào" />
      </div>

      <aside class="magazine-sidebar">
        <div class="widget">
          <h3 class="widget-title"><el-icon><Collection /></el-icon> Chuyên mục</h3>
          <div class="cat-menu">
            <div 
              v-for="cat in categories" :key="cat" 
              class="cat-link" 
              :class="{ active: selectedCategory === cat }"
              @click="selectedCategory = cat"
            >
              {{ cat }}
            </div>
          </div>
        </div>

        <div class="widget promo-widget">
          <div class="promo-card">
            <h4>Gia nhập Cộng đồng</h4>
            <p>Đăng ký thi đấu ngay hôm nay để tích điểm ELO!</p>
            <el-button type="warning" round block @click="$router.push('/tournaments')">Xem giải đấu</el-button>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.news-portal { background: #f4f7f6; min-height: 100vh; padding-bottom: 60px; }
.container { max-width: 1240px; margin: 0 auto; padding: 0 20px; }

/* Header */
.magazine-header { background: white; padding: 50px 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 40px; }
.header-content { display: flex; justify-content: space-between; align-items: center; }
.kicker { color: var(--primary); font-weight: 800; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px; }
.magazine-header h1 { font-size: 2.8rem; font-weight: 900; color: #1e293b; margin: 10px 0; }
.search-wrapper { width: 320px; }

/* Layout */
.main-layout { display: grid; grid-template-columns: 1fr 340px; gap: 40px; }

/* Featured */
.featured-box { border-radius: 8px; overflow: hidden; height: 480px; cursor: pointer; margin-bottom: 40px; box-shadow: 0 20px 40px rgba(0,0,0,0.08); position: relative; }
.featured-img-container { width: 100%; height: 100%; }
.featured-img-container img { width: 100%; height: 100%; object-fit: cover; transition: 0.6s; }
.featured-box:hover img { transform: scale(1.05); }
.featured-info { position: absolute; bottom: 0; left: 0; right: 0; padding: 60px 40px; background: linear-gradient(to top, rgba(0,0,0,0.9), transparent); color: white; }
.featured-info h2 { font-size: 2.2rem; margin: 15px 0; line-height: 1.2; }
.featured-info p { opacity: 0.85; font-size: 1.1rem; margin-bottom: 20px; }

/* Grid */
.news-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
.post-card { background: white; border-radius: 8px; overflow: hidden; cursor: pointer; transition: 0.3s; border: 1px solid #edf2f7; }
.post-card:hover { transform: translateY(-10px); box-shadow: 0 15px 30px rgba(0,0,0,0.05); }
.post-thumb { height: 220px; position: relative; }
.post-thumb img { width: 100%; height: 100%; object-fit: cover; }
.cat-pill { position: absolute; top: 15px; left: 15px; background: rgba(21, 128, 61, 0.9); color: white; padding: 5px 14px; border-radius: 10px; font-size: 0.75rem; font-weight: bold; }
.post-content { padding: 25px; }
.post-content h3 { font-size: 1.3rem; margin: 0 0 12px 0; color: #1e293b; line-height: 1.4; font-weight: 800; }
.post-content p { font-size: 0.95rem; color: #64748b; line-height: 1.6; margin-bottom: 20px; }
.read-more { color: var(--primary); font-weight: 800; font-size: 0.9rem; display: flex; align-items: center; gap: 6px; }

/* Sidebar */
.widget { background: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #edf2f7; }
.widget-title { margin: 0 0 20px 0; font-size: 1.2rem; font-weight: 800; color: #1e293b; display: flex; align-items: center; gap: 10px; }
.cat-link { padding: 12px 18px; border-radius: 12px; cursor: pointer; transition: 0.2s; margin-bottom: 8px; color: #475569; font-weight: 600; }
.cat-link:hover, .cat-link.active { background: #f0fdf4; color: var(--primary); padding-left: 25px; }
.promo-card { background: #1e293b; color: white; padding: 30px; border-radius: 8px; text-align: center; }
.promo-card h4 { font-size: 1.4rem; margin-bottom: 10px; color: #fbbf24; }

@media (max-width: 1024px) {
  .main-layout { grid-template-columns: 1fr; }
  .news-grid { grid-template-columns: 1fr; }
}
</style>