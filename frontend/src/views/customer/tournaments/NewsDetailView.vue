<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { newsService } from '../../../services/newsService'
import { Calendar, User, ArrowLeft, Share, ChatLineRound, Timer } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const post = ref(null)
const loading = ref(true)
const scrollPercent = ref(0)

const fetchDetail = async () => {
  loading.value = true
  try {
    const data = await newsService.getPost(route.params.slug)
    post.value = data
    window.scrollTo(0, 0)
  } catch (err) {
    console.error('Lỗi tải bài viết:', err)
  } finally {
    loading.value = false
  }
}

const handleScroll = () => {
  const winScroll = document.documentElement.scrollTop
  const height = document.documentElement.scrollHeight - document.documentElement.clientHeight
  scrollPercent.value = (winScroll / height) * 100
}

onMounted(() => {
  fetchDetail()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('vi-VN', { 
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' 
  })
}
</script>

<template>
  <div class="article-page" v-loading="loading">
    <div class="reading-progress">
      <div class="progress-fill" :style="{ width: scrollPercent + '%' }"></div>
    </div>

    <div v-if="post" class="container">
      <div class="article-layout">
        
        <aside class="article-social">
          <div class="social-sticky">
            <el-button circle :icon="Share" size="large" plain />
            <el-button circle :icon="ChatLineRound" size="large" plain style="margin-top: 15px;" />
            <div class="scroll-label">SCROLL</div>
          </div>
        </aside>

        <main class="article-main">
          <nav class="breadcrumb-nav">
            <span @click="router.push('/news')" class="crumb-link">Tin tức</span>
            <span class="separator">/</span>
            <span class="crumb-active">{{ post.post_type === 'news' ? 'Tin tức' : 'Thông báo' }}</span>
          </nav>

          <header class="article-header">
            <div class="article-cat">
              <span class="dot"></span>
              {{ post.post_type === 'news' ? 'Tin tức' : 'Thông báo' }}
            </div>
            <h1>{{ post.title }}</h1>
            
            <div class="article-meta-modern">
               <div class="author-block">
                 <div class="avatar-pseudo"><el-icon><User /></el-icon></div>
                 <div class="author-info">
                   <strong>Ban Quản Trị</strong>
                   <span>Saigon Tennis Editorial</span>
                 </div>
               </div>
               <div class="date-block">
                 <el-icon><Calendar /></el-icon>
                 {{ formatDate(post.publish_at || post.created_at) }}
               </div>
            </div>
          </header>

          <figure class="article-hero">
            <img :src="post.thumbnail_url || 'https://images.unsplash.com/photo-1592709823125-a191f07a2a5e?auto=format&fit=crop&q=80&w=1200'" alt="cover" />
            <figcaption v-if="post.summary">{{ post.summary }}</figcaption>
          </figure>

          <div class="article-content-rich" v-html="post.content"></div>

          <footer class="article-footer-tags">
            <!-- <div class="tag-label">Tags:</div> -->
            <div class="tags-container">
              <el-tag v-for="tag in (post.tags || ['Tennis', 'SaigonTennis'])" :key="tag" class="news-tag" size="large" effect="plain">
                #{{ tag }}
              </el-tag>
            </div>
            <div class="action-footer">
              <el-button type="success" size="large" round @click="router.push('/news')">
                <el-icon><ArrowLeft /></el-icon> Quay lại trang tin
              </el-button>
            </div>
          </footer>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
.article-page { 
  background: white; 
  min-height: 100vh; 
  position: relative; 
  font-family: Arial, sans-serif !important;
}

.reading-progress { 
  position: fixed; 
  top: 0; 
  left: 0; 
  width: 100%; 
  height: 4px; 
  background: transparent; 
  z-index: 2000; 
}

.progress-fill { 
  height: 100%; 
  background: #15803d; 
  transition: width 0.1s linear; 
}

.container { 
  max-width: 1160px; 
  margin: 0 auto; 
  padding: 80px 20px; 
}

.article-layout { 
  display: grid; 
  grid-template-columns: 100px 1fr; 
  gap: 40px; 
}

/* Social Sticky */
.social-sticky { 
  position: sticky; 
  top: 120px; 
  display: flex; 
  flex-direction: column; 
  align-items: center; 
}

.scroll-label {
  margin-top: 30px;
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 3px;
  writing-mode: vertical-rl;
  color: #cbd5e1;
}

/* Breadcrumb */
.breadcrumb-nav {
  margin-bottom: 2rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.crumb-link {
  cursor: pointer;
  color: #15803d;
  transition: opacity 0.2s;
}

.crumb-link:hover { opacity: 0.7; }
.crumb-active { color: #475569; }

/* Header */
.article-cat {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #15803d;
  font-weight: 500;
  font-size: 0.85rem;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 1.5rem;
}

.article-cat .dot { width: 8px; height: 8px; border-radius: 50%; background: #15803d; }

.article-header h1 { 
  font-size: 3.5rem; 
  font-weight: 500; 
  color: #0f172a; 
  line-height: 1.15; 
  margin: 0 0 2.5rem 0;
  letter-spacing: -0.05rem;
}

.article-meta-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 2rem;
  border-bottom: 1px solid #f1f5f9;
  margin-bottom: 3rem;
}

.author-block { display: flex; align-items: center; gap: 1rem; }
.avatar-pseudo { width: 44px; height: 44px; border-radius: 50%; background: #f1f5f9; display: flex; align-items: center; justify-content: center; color: #15803d; font-size: 1.2rem; }
.author-info strong { display: block; color: #0f172a; font-size: 1.1rem; }
.author-info span { font-size: 0.85rem; color: #64748b; }
.date-block { color: #64748b; font-weight: normal; font-size: 0.95rem; display: flex; align-items: center; gap: 8px; }

/* Hero Image */
.article-hero { margin: 0 0 4rem 0; }
.article-hero img { 
  width: 100%; 
  max-height: 600px;
  object-fit: cover;
  border-radius: 24px; 
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.2);
}
.article-hero figcaption {
  margin-top: 1.5rem;
  text-align: center;
  color: #64748b;
  font-style: italic;
  font-size: 1rem;
}

/* Content Rich Text */
.article-content-rich { 
  font-size: 1.25rem; 
  line-height: 1.8; 
  color: #334155; 
  max-width: 820px;
  margin: 0 auto;
}

.article-content-rich :deep(p) { margin-bottom: 2rem; }
.article-content-rich :deep(h2) { font-size: 2rem; font-weight: 500; color: #0f172a; margin: 3rem 0 1.5rem; }
.article-content-rich :deep(img) { width: 100%; border-radius: 16px; margin: 3rem 0; }
.article-content-rich :deep(blockquote) { 
  border-left: 5px solid #15803d; 
  background: #f0fdf4; 
  padding: 30px 40px; 
  margin: 3rem 0; 
  font-style: italic; 
  font-size: 1.4rem; 
  color: #166534; 
  border-radius: 0 16px 16px 0; 
}

/* Footer */
.article-footer-tags { 
  max-width: 820px;
  margin: 5rem auto 0;
  padding-top: 3rem; 
  border-top: 2px solid #f1f5f9; 
}

.tag-label { font-weight: 500; color: #0f172a; margin-bottom: 1rem; }
.tags-container { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 3rem; }
.news-tag { border: none !important; background: #f1f5f9 !important; color: #475569 !important; font-weight: 500 !important; }

.action-footer { display: flex; justify-content: center; }

@media (max-width: 900px) {
  .article-layout { grid-template-columns: 1fr; }
  .article-social { display: none; }
  .article-header h1 { font-size: 2.2rem; }
  .article-meta-modern { flex-direction: column; align-items: flex-start; gap: 1.5rem; }
}
</style>
