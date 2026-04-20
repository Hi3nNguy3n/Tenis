<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { newsService } from '../../../services/newsService'
import { Calendar, Timer, ArrowRight, Search, Collection, ArrowDown } from '@element-plus/icons-vue'

const newsList = ref([])
const loading = ref(true)
const searchQuery = ref('')
const selectedCategory = ref('Tất cả')
const activeTab = ref('related')

const categories = ['Tất cả', 'Thông báo', 'Highlight', 'Phân tích', 'Phỏng vấn']

const fetchNews = async () => {
  loading.value = true
  try {
    const params = {
      limit: 100
    }
    
    // Chỉ truyền category nếu khác 'Tất cả'
    if (selectedCategory.value !== 'Tất cả') {
      params.category = selectedCategory.value
    }
    
    // Chỉ truyền search nếu có nội dung
    if (searchQuery.value) {
      params.search = searchQuery.value
    }

    const data = await newsService.getAllPosts(params)
    let results = (data || []).filter(item => item.status === 'published')
    
    // FE Fallback Filter: Đảm bảo lọc đúng category ở FE nếu BE trả về dư thừa
    if (selectedCategory.value !== 'Tất cả') {
      results = results.filter(post => {
        // Kiểm tra field category (nếu có) hoặc post_type hoặc nội dung tiêu đề để "đoán"
        const catValue = (post.category || '').toLowerCase()
        const selectedValue = selectedCategory.value.toLowerCase()
        return catValue === selectedValue || post.post_type === selectedValue
      })
    }

    newsList.value = results
  } catch (err) {
    console.error('Lỗi tải tin tức:', err)
  } finally {
    loading.value = false
  }
}

// Watchers để tự động gọi API khi người dùng thay đổi bộ lọc
watch(selectedCategory, () => {
  fetchNews()
})

// Sử dụng debounce cho ô tìm kiếm
let searchTimeout = null
watch(searchQuery, () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchNews()
  }, 500)
})

const featuredPost = computed(() => newsList.value[0])

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

onMounted(fetchNews)
</script>

<template>
  <div class="atp-news-portal" v-loading="loading">
    <div class="container">
      
      <!-- TOP NAVIGATION BAR (LATEST | NEWS) -->
      <nav class="news-inner-nav">
        <div class="nav-brand">
          <span class="l-label">LATEST</span>
          <span class="separator">|</span>
          <el-dropdown trigger="click">
            <span class="el-dropdown-link">
              {{ selectedCategory === 'Tất cả' ? 'News' : selectedCategory }} <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="cat in categories" :key="cat" @click="selectedCategory = cat">{{ cat }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <div class="nav-search">
           <el-input v-model="searchQuery" placeholder="Search news..." :prefix-icon="Search" clearable class="minimal-search" />
        </div>
      </nav>

      <div class="magazine-layout">
        <!-- MAIN COLUMN: FEATURED CONTENT -->
        <main class="main-content-area">
          <div v-if="featuredPost" class="featured-grand-entry" @click="$router.push('/news/' + featuredPost.slug)">
            <div class="entry-meta">
              <el-tag size="small" effect="plain" class="cat-tag">{{ featuredPost.post_type === 'news' ? 'SGTN NEWS' : 'OFFICIAL' }}</el-tag>
            </div>
            <h1 class="entry-title">{{ featuredPost.title }}</h1>
            <p class="entry-excerpt">{{ featuredPost.summary }}</p>
            <div class="entry-author-date">
              <span class="date">{{ formatDate(featuredPost.publish_at || featuredPost.created_at) }}</span>
            </div>
            <figure class="entry-visual">
              <img :src="featuredPost.thumbnail_url || 'https://images.unsplash.com/photo-1592709823125-a191f07a2a5e?auto=format&fit=crop&q=80&w=1200'" alt="hero" />
            </figure>
          </div>
          
          <div v-else class="empty-placeholder">
            <el-empty description="Không có tin tức nào được tìm thấy" />
          </div>

          <!-- Bottom Grid for remaining news on mobile/tablet -->
          <div class="mobile-news-list">
             <div v-for="post in newsList.slice(1, 5)" :key="post.id" class="mobile-item" @click="$router.push('/news/' + post.slug)">
                <img :src="post.thumbnail_url" alt="thumb" />
                <div class="mi-text">
                  <h3>{{ post.title }}</h3>
                  <span>{{ formatDate(post.publish_at) }}</span>
                </div>
             </div>
          </div>
        </main>

        <!-- SIDEBAR: NEWS LIST -->
        <aside class="news-sidebar-modern">
          <div class="sidebar-box">
            <div class="sb-header">
              <h2>NEWS</h2>
            </div>
            
            <el-tabs v-model="activeTab" class="sidebar-tabs">
              <el-tab-pane label="Related" name="related">
                <div class="sidebar-news-list">
                  <div v-for="post in newsList.slice(1, 6)" :key="post.id" class="sb-news-item" @click="$router.push('/news/' + post.slug)">
                    <div class="sb-item-thumb">
                      <img :src="post.thumbnail_url || 'https://images.unsplash.com/photo-1592709823125-a191f07a2a5e?auto=format&fit=crop&q=80&w=200'" />
                    </div>
                    <div class="sb-item-info">
                      <h3>{{ post.title }}</h3>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
              <el-tab-pane label="Most Recent" name="recent">
                <div class="sidebar-news-list">
                   <div v-for="post in newsList.slice(0, 5)" :key="post.id" class="sb-news-item" @click="$router.push('/news/' + post.slug)">
                    <div class="sb-item-thumb">
                      <img :src="post.thumbnail_url" />
                    </div>
                    <div class="sb-item-info">
                      <h3>{{ post.title }}</h3>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<style scoped>
.atp-news-portal {
  background: #ffffff;
  min-height: 100vh;
  padding-bottom: 100px;
  font-family: Arial, sans-serif !important;
  color: #001242;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* INNER NAV */
.news-inner-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem 0;
  border-bottom: 2px solid #eee;
  margin-bottom: 2.5rem;
}

.nav-brand {
  display: flex;
  align-items: center;
  font-weight: 500;
  font-size: 1.4rem;
  letter-spacing: -0.02em;
}

.l-label { color: #001242; }
.separator { margin: 0 10px; color: #ccc; }
.el-dropdown-link {
  cursor: pointer;
  color: #001242;
  display: flex;
  align-items: center;
  font-size: 1.4rem;
  font-weight: 500;
}

.minimal-search { width: 300px; }
:deep(.minimal-search .el-input__wrapper) {
  box-shadow: none;
  border-bottom: 2px solid #eee;
  border-radius: 0;
  padding: 0;
}
:deep(.minimal-search .el-input__wrapper.is-focus) {
  border-bottom-color: #001242;
}

/* MAGAZINE LAYOUT */
.magazine-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 4rem;
}

/* MAIN CONTENT */
.featured-grand-entry {
  cursor: pointer;
  margin-bottom: 4rem;
}

.cat-tag {
  border-radius: 0;
  border: 1px solid #eee;
  color: #666;
  font-weight: 500;
  letter-spacing: 0.05em;
  margin-bottom: 1.5rem;
}

.entry-title {
  font-size: 3.2rem;
  line-height: 1.1;
  font-weight: 500;
  margin-bottom: 1.5rem;
  letter-spacing: -0.04em;
  color: #001242;
}

.entry-excerpt {
  font-size: 1.25rem;
  line-height: 1.6;
  color: #444;
  margin-bottom: 1.5rem;
  max-width: 90%;
}

.entry-author-date {
  font-size: 0.9rem;
  font-weight: 500;
  color: #888;
  margin-bottom: 2rem;
  text-transform: uppercase;
}

.entry-visual {
  margin: 0;
  width: 100%;
  border-radius: 4px;
  overflow: hidden;
}

.entry-visual img {
  width: 100%;
  height: auto;
  display: block;
}

/* SIDEBAR */
.sidebar-box {
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 1.5rem;
}

.sb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.sb-header h2 {
  font-size: 1rem;
  font-weight: 500;
  color: #001242;
}

.view-all-link {
  font-size: 0.75rem;
  font-weight: 500;
  color: #001242;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* TABS */
:deep(.el-tabs__header) { margin-bottom: 2rem; }
:deep(.el-tabs__nav-wrap::after) { height: 1px; background-color: #eee; }
:deep(.el-tabs__item) {
  font-weight: 500;
  color: #888;
  font-size: 0.95rem;
}
:deep(.el-tabs__item.is-active) { color: #001242; }
:deep(.el-tabs__active-bar) { background-color: #001242; height: 3px; }

.sb-news-item {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  cursor: pointer;
  transition: opacity 0.2s;
}

.sb-news-item:hover { opacity: 0.7; }

.sb-item-thumb {
  width: 80px;
  height: 80px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
}

.sb-item-thumb img { width: 100%; height: 100%; object-fit: cover; }

.sb-item-info h3 {
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1.4;
  color: #001242;
  margin: 0;
}

.mobile-news-list { display: none; }

@media (max-width: 1024px) {
  .magazine-layout { grid-template-columns: 1fr; gap: 2rem; }
  .entry-title { font-size: 2.2rem; }
}

@media (max-width: 768px) {
  .news-inner-nav { flex-direction: column; align-items: stretch; gap: 0.5rem; padding: 0.5rem 0; }
  .nav-brand { justify-content: space-between; font-size: 1rem; }
  .el-dropdown-link { font-size: 1rem; }
  .minimal-search { width: 100%; }
  .container { padding: 0 12px; }
}

@media (max-width: 480px) {
  .atp-news-portal { padding-top: 50px; }
  .entry-title { font-size: 1.4rem; margin-bottom: 0.75rem; line-height: 1.2; word-break: break-word; }
  .entry-excerpt { font-size: 0.9rem; margin-bottom: 1rem; }
  .featured-grand-entry { margin-bottom: 1.5rem; }
}
</style>


