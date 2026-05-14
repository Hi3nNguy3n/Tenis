<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { newsService } from '../../../services/newsService'
import { playerService } from '../../../services/playerService' 
import { Calendar, User, ArrowLeft, Share, ChatLineRound, VideoPlay } from '@element-plus/icons-vue'
import { currentLocale, t } from '../../../utils/locale'
import 'quill/dist/quill.snow.css'

const route = useRoute()
const router = useRouter()
const post = ref(null)
const loading = ref(true)
const scrollPercent = ref(0)

const relatedNews = ref([])
const topPlayers = ref([])

const isVideo = (url) => {
  if (!url) return false
  return url.match(/\.(mp4|webm|ogg)$/i) !== null
}

const fetchData = async () => {
  loading.value = true
  try {
    const postData = await newsService.getPost(route.params.slug)
    post.value = postData
    window.scrollTo(0, 0)

    Promise.all([
      newsService.getAllPosts({ limit: 6, category: postData.category }), 
      playerService.getRankings().catch(() => [])
    ]).then(([newsData, rankingsData]) => {
      
      relatedNews.value = (newsData || [])
        .filter(item => item.id !== postData.id && item.status === 'published')
        .slice(0, 4) 

      topPlayers.value = (rankingsData || []).slice(0, 5) 
    })

  } catch (err) {
    console.error('Lỗi tải bài viết:', err)
    router.push('/news') 
  } finally {
    loading.value = false
  }
}

watch(() => route.params.slug, () => {
  fetchData()
})

const handleScroll = () => {
  const winScroll = document.documentElement.scrollTop
  const height = document.documentElement.scrollHeight - document.documentElement.clientHeight
  scrollPercent.value = (winScroll / height) * 100
}

onMounted(() => {
  fetchData()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { 
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' 
  })
}

// Bỏ các chuỗi cứng dự phòng
const getCategoryLabel = (val) => {
  const map = {
    'announcement': t('news.typeAnnouncement'),
    'highlight': t('news.highlight'),
    'analysis': t('news.analysis'),
    'interview': t('news.interview')
  }
  return map[val] || t('news.news')
}
</script>

<template>
  <div class="atp-article-page" v-loading="loading">
    
    <div class="reading-progress">
      <div class="progress-fill" :style="{ width: scrollPercent + '%' }"></div>
    </div>

    <div v-if="post">
      
      <div v-if="isVideo(post.thumbnail_url || post.media_url)" class="video-theater-mode">
        <div class="container">
          <div class="video-player-wrapper">
            <video 
              :src="post.thumbnail_url || post.media_url" 
              controls 
              autoplay 
              playsinline
              class="main-video">
            </video>
          </div>
        </div>
      </div>

      <figure v-else class="article-hero-cinematic">
        <img 
          :src="post.thumbnail_url || 'https://images.unsplash.com/photo-1595435934249-5df7ed86e1f4?auto=format&fit=crop&q=80&w=1600'" 
          :alt="post.title" 
        />
        <div class="hero-overlay"></div>
      </figure>

      <div class="container main-container" :class="{ 'is-video-layout': isVideo(post.thumbnail_url || post.media_url) }">
        
        <header class="article-header-modern">
          <div class="article-cat">
            <span class="category-badge">{{ getCategoryLabel(post.category) }}</span>
          </div>
          <h1>{{ post.title }}</h1>
          
          <div class="article-meta-modern">
             <div class="author-block">
               <div class="avatar-pseudo"><el-icon><User /></el-icon></div>
               <div class="author-info">
                 <strong>{{ t('news.admin') }}</strong>
                 <span>{{ t('news.editorial') }}</span>
               </div>
             </div>
             <div class="date-block">
               <el-icon><Calendar /></el-icon>
               {{ formatDate(post.publish_at || post.created_at) }}
             </div>
          </div>
        </header>

        <div class="article-layout">
          
          <aside class="article-social">
            <div class="social-sticky">
              <el-button circle :icon="Share" size="large" plain :title="t('news.share')" />
              <el-button circle :icon="ChatLineRound" size="large" plain style="margin-top: 15px;" :title="t('news.comment')" />
              <div class="scroll-label">{{ t('news.scroll') }}</div>
            </div>
          </aside>

          <main class="article-main">
            <p v-if="post.summary" class="article-lead">{{ post.summary }}</p>

            <div class="article-content-rich ql-editor" v-html="post.content"></div>

            <footer class="article-footer-tags">
              <div class="tags-container">
                <el-tag v-for="tag in (post.tags || ['Tennis', 'SaigonTennis', 'ATP'])" :key="tag" class="news-tag" size="large" effect="plain">
                  #{{ tag }}
                </el-tag>
              </div>
              <div class="action-footer">
                <el-button type="primary" size="large" class="back-btn" @click="router.push('/news')">
                  <el-icon><ArrowLeft /></el-icon> {{ t('news.backToNews') }}
                </el-button>
              </div>
            </footer>
          </main>

          <aside class="article-sidebar">
            
            <div class="atp-widget related-widget" v-if="relatedNews.length > 0">
              <div class="widget-header">
                <h3>{{ t('news.relatedNews') }}</h3>
              </div>
              <div class="widget-body">
                <article 
                  v-for="rel in relatedNews" 
                  :key="rel.id" 
                  class="related-item"
                  @click="router.push('/news/' + rel.slug)"
                >
                  <div class="rel-thumb">
                    <video v-if="isVideo(rel.thumbnail_url)" :src="rel.thumbnail_url" autoplay loop muted playsinline></video>
                    <img v-else :src="rel.thumbnail_url || 'https://images.unsplash.com/photo-1592709823125-a191f07a2a5e?auto=format&fit=crop&q=80&w=200'" />
                  </div>
                  <div class="rel-info">
                    <span class="rel-cat">{{ getCategoryLabel(rel.category) }}</span>
                    <h4>{{ rel.title }}</h4>
                  </div>
                </article>
              </div>
            </div>

            <div class="atp-widget rankings-widget" v-if="topPlayers.length > 0">
              <div class="widget-header">
                <h3><span class="pif-logo">PIF</span> {{ t('news.atpRankings') }}</h3>
              </div>
              <div class="widget-body ranking-list">
                <div v-for="(player, index) in topPlayers" :key="player.player_id" class="ranking-row">
                  <div class="rank-pos">{{ index + 1 }}</div>
                  <div class="rank-name"><span class="flag">🇻🇳</span> {{ player.full_name }}</div>
                  <div class="rank-pts">{{ player.elo_points }}</div>
                </div>
              </div>
              <div class="widget-footer">
                 <router-link to="/rankings" class="view-all">{{ t('news.viewFullRankings') }}</router-link>
              </div>
            </div>

          </aside>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* CSS GIỮ NGUYÊN HOÀN TOÀN TỪ BẢN GỐC */
.atp-article-page { background: #f1f5f9; min-height: 100vh; position: relative; font-family: 'Inter', Arial, sans-serif; padding-bottom: 5rem; }
.reading-progress { position: fixed; top: 0; left: 0; width: 100%; height: 4px; background: transparent; z-index: 2000; }
.progress-fill { height: 100%; background: #c1ff72; transition: width 0.1s linear; }
.video-theater-mode { background: #000000; padding: 3rem 0 4rem; width: 100%; }
.video-player-wrapper { max-width: 1000px; margin: 0 auto; aspect-ratio: 16 / 9; background: #0f172a; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.1); }
.main-video { width: 100%; height: 100%; object-fit: contain; display: block; }
.article-hero-cinematic { position: relative; width: 100%; height: 60vh; min-height: 400px; max-height: 600px; margin: 0; background: #000; overflow: hidden; }
.article-hero-cinematic img { width: 100%; height: 100%; object-fit: cover; opacity: 0.9; }
.hero-overlay { position: absolute; bottom: 0; left: 0; width: 100%; height: 60%; background: linear-gradient(to top, #f1f5f9 0%, rgba(241, 245, 249, 0) 100%); }
.main-container { max-width: 1280px; margin: -100px auto 0; position: relative; z-index: 10; padding: 0 1.5rem; }
.main-container.is-video-layout { margin-top: 2rem; }
.article-header-modern { max-width: 900px; margin: 0 auto 3rem; background: white; padding: 3rem; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
.category-badge { display: inline-block; background: #002855; color: white; font-size: 0.85rem; font-weight: 700; padding: 0.4rem 1rem; text-transform: uppercase; border-radius: 4px; margin-bottom: 1.5rem; }
.article-header-modern h1 { font-size: 2.8rem; font-weight: 800; color: #0f172a; line-height: 1.2; margin: 0 0 2rem 0; letter-spacing: -0.02em; }
.article-meta-modern { display: flex; justify-content: space-between; align-items: center; padding-top: 2rem; border-top: 1px solid #e2e8f0; }
.author-block { display: flex; align-items: center; gap: 1rem; }
.avatar-pseudo { width: 48px; height: 48px; border-radius: 50%; background: #f1f5f9; display: flex; align-items: center; justify-content: center; color: #002855; font-size: 1.4rem; }
.author-info strong { display: block; color: #0f172a; font-size: 1.05rem; }
.author-info span { font-size: 0.85rem; color: #64748b; }
.date-block { color: #64748b; font-weight: 600; font-size: 0.95rem; display: flex; align-items: center; gap: 8px; text-transform: uppercase;}
.article-layout { display: grid; grid-template-columns: 80px 1fr 350px; gap: 3rem; }
.social-sticky { position: sticky; top: 120px; display: flex; flex-direction: column; align-items: center; }
.social-sticky .el-button { margin: 0 0 15px 0; border-color: #cbd5e1; color: #475569; }
.social-sticky .el-button:hover { color: #002855; border-color: #002855; background: #f8fafc; }
.scroll-label { margin-top: 30px; font-size: 11px; font-weight: 700; letter-spacing: 3px; writing-mode: vertical-rl; color: #94a3b8; }
.article-main { background: white; padding: 3rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #e2e8f0; }
.article-lead { font-size: 1.4rem; line-height: 1.6; font-weight: 600; color: #1e293b; margin-bottom: 2.5rem; font-style: italic; padding-bottom: 2rem; border-bottom: 2px solid #002855; }
.article-content-rich { font-size: 1.2rem; line-height: 1.8; color: #334155; }
.article-content-rich :deep(p) { margin-bottom: 1.5rem; }
.article-content-rich :deep(h2) { font-size: 1.8rem; font-weight: 700; color: #0f172a; margin: 3rem 0 1.5rem; }
.article-content-rich :deep(h3) { font-size: 1.5rem; font-weight: 700; color: #0f172a; margin: 2rem 0 1rem; }
.article-content-rich :deep(img), .article-content-rich :deep(video) { width: 100%; border-radius: 8px; margin: 2.5rem 0; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
.article-content-rich :deep(blockquote) { border-left: 6px solid #c1ff72; background: #f8fafc; padding: 2rem; margin: 3rem 0; font-style: italic; font-size: 1.3rem; color: #1e293b; border-radius: 0 8px 8px 0; }
.article-content-rich :deep(.ql-bg-black) { background-color: #000; color: #fff; }
.article-content-rich :deep(.ql-bg-red) { background-color: #e60000; color: #fff; }
.article-content-rich :deep(.ql-bg-orange) { background-color: #f50; color: #fff; }
.article-content-rich :deep(.ql-bg-yellow) { background-color: #ff0; color: #000; }
.article-content-rich :deep(.ql-bg-green) { background-color: #008a00; color: #fff; }
.article-content-rich :deep(.ql-bg-blue) { background-color: #06c; color: #fff; }
.article-content-rich :deep(.ql-bg-purple) { background-color: #d85d00; color: #fff; }
.article-footer-tags { margin-top: 4rem; padding-top: 2rem; border-top: 1px solid #e2e8f0; }
.tags-container { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 3rem; }
.news-tag { border: none !important; background: #f1f5f9 !important; color: #475569 !important; font-weight: 600 !important; font-size: 0.9rem;}
.action-footer { display: flex; justify-content: center; }
.back-btn { background: #002855; border: none; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 1.5rem 3rem; border-radius: 30px;}
.back-btn:hover { background: #003b7a; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,40,85,0.2);}
.article-sidebar { display: flex; flex-direction: column; gap: 2rem; }
.atp-widget { background: white; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.03); }
.widget-header { padding: 1.2rem 1.5rem; border-bottom: 2px solid #002855; background: #f8fafc; }
.widget-header h3 { font-size: 1rem; font-weight: 800; color: #002855; margin: 0; display: flex; align-items: center; gap: 8px; text-transform: uppercase; }
.related-item { display: flex; gap: 1rem; padding: 1rem 1.2rem; border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: background 0.2s; }
.related-item:last-child { border-bottom: none; }
.related-item:hover { background: #f8fafc; }
.rel-thumb { width: 90px; height: 60px; border-radius: 4px; overflow: hidden; background: #000; flex-shrink: 0;}
.rel-thumb img, .rel-thumb video { width: 100%; height: 100%; object-fit: cover; }
.rel-info { display: flex; flex-direction: column; justify-content: center;}
.rel-cat { font-size: 0.65rem; font-weight: 800; color: #002855; text-transform: uppercase; margin-bottom: 0.3rem;}
.rel-info h4 { font-size: 0.9rem; font-weight: 700; color: #0f172a; line-height: 1.3; margin: 0;}
.ranking-list { padding: 0; }
.ranking-row { display: flex; align-items: center; padding: 0.8rem 1.25rem; border-bottom: 1px solid #f1f5f9; }
.rank-pos { width: 30px; font-weight: 700; color: #64748b; font-size: 0.9rem;}
.rank-name { flex: 1; display: flex; align-items: center; gap: 0.5rem; font-weight: 600; font-size: 0.9rem; color: #0f172a;}
.rank-pts { font-weight: 800; color: #002855; font-size: 0.9rem; }
.pif-logo { background: #000; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-style: normal;}
.widget-footer { padding: 1rem; text-align: center; border-top: 1px solid #f1f5f9; background: #f8fafc;}
.view-all { font-size: 0.8rem; font-weight: 700; color: #002855; text-decoration: none; text-transform: uppercase;}
.view-all:hover { color: #dc2626; }
@media (max-width: 1200px) { .article-layout { grid-template-columns: 60px 1fr; } .article-sidebar { display: none; } }
@media (max-width: 900px) { .article-layout { grid-template-columns: 1fr; } .article-social { display: none; } .article-header-modern { padding: 2rem; margin: -50px auto 2rem; } .main-container.is-video-layout .article-header-modern { margin-top: 0; } .article-header-modern h1 { font-size: 2.2rem; } .article-main { padding: 2rem; } .video-theater-mode { padding: 1.5rem 0; } }
@media (max-width: 600px) { .article-hero-cinematic { height: 40vh; min-height: 300px; } .article-header-modern { padding: 1.5rem; margin-top: -30px; border-radius: 8px;} .article-header-modern h1 { font-size: 1.8rem; margin-bottom: 1.5rem; } .article-meta-modern { flex-direction: column; align-items: flex-start; gap: 1rem; } .article-main { padding: 1.5rem; border-radius: 8px;} .article-lead { font-size: 1.15rem; } .article-content-rich { font-size: 1.1rem; } .article-content-rich :deep(blockquote) { padding: 1.5rem; font-size: 1.1rem; } }
</style>