<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '../../../services/apiClient'
import { Calendar, User, ArrowLeft, Share, ChatLineRound } from '@element-plus/icons-vue'

const route = useRoute()
const post = ref(null)
const loading = ref(true)
const scrollPercent = ref(0)

const fetchDetail = async () => {
  loading.value = true
  try {
    const data = await apiClient.get(`/api/news/${route.params.slug}`)
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
  <div class="article-wrapper" v-loading="loading">
    <div class="reading-progress">
      <div class="progress-fill" :style="{ width: scrollPercent + '%' }"></div>
    </div>

    <div v-if="post" class="container">
      <div class="article-layout">
        
        <aside class="article-tools">
          <div class="tool-sticky">
            <el-button circle :icon="Share" size="large" />
            <el-button circle :icon="ChatLineRound" size="large" style="margin-top: 15px;" />
          </div>
        </aside>

        <main class="article-body">
          <el-breadcrumb separator="/" class="mb-8">
            <el-breadcrumb-item :to="{ path: '/news' }">Tin tức</el-breadcrumb-item>
            <el-breadcrumb-item>{{ post.category }}</el-breadcrumb-item>
          </el-breadcrumb>

          <header class="article-header">
            <el-tag effect="dark" type="success" round class="mb-4">{{ post.category }}</el-tag>
            <h1>{{ post.title }}</h1>
            <div class="article-meta">
              <span><el-icon><User /></el-icon> Ban Quản Trị</span>
              <span><el-icon><Calendar /></el-icon> {{ formatDate(post.created_at) }}</span>
            </div>
          </header>

          <div class="article-hero-img">
            <img :src="post.thumbnail_url" alt="cover" />
          </div>

          <div class="article-content" v-html="post.content"></div>

          <footer class="article-footer">
            <div v-if="post.tags && post.tags.length" class="tag-cloud">
              <el-tag v-for="tag in post.tags" :key="tag" class="mr-2" size="large" plain>#{{ tag }}</el-tag>
            </div>
            <div class="back-link">
              <el-button type="primary" link :icon="ArrowLeft" @click="$router.push('/news')" size="large">
                Quay lại trang tin
              </el-button>
            </div>
          </footer>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
.article-wrapper { background: white; min-height: 100vh; position: relative; }
.reading-progress { position: fixed; top: 0; left: 0; width: 100%; height: 5px; background: transparent; z-index: 1000; }
.progress-fill { height: 100%; background: var(--primary); transition: width 0.1s linear; }

.container { max-width: 1100px; margin: 0 auto; padding: 60px 20px; }
.article-layout { display: grid; grid-template-columns: 80px 1fr; gap: 50px; }

.tool-sticky { position: sticky; top: 100px; display: flex; flex-direction: column; align-items: center; }

.article-header { margin-bottom: 40px; }
.article-header h1 { font-size: 3.4rem; font-weight: 900; color: #0f172a; line-height: 1.1; margin: 20px 0; }
.article-meta { display: flex; gap: 30px; color: #94a3b8; font-weight: 600; font-size: 1rem; }
.article-meta span { display: flex; align-items: center; gap: 8px; }

.article-hero-img { border-radius: 32px; overflow: hidden; margin-bottom: 60px; box-shadow: 0 30px 60px rgba(0,0,0,0.1); }
.article-hero-img img { width: 100%; height: auto; display: block; }

/* TYPOGRAPHY CHO CONTENT */
.article-content { font-size: 1.3rem; line-height: 1.85; color: #334155; font-family: Arial, sans-serif; }
.article-content :deep(p) { margin-bottom: 30px; }
.article-content :deep(h2) { font-size: 2.2rem; color: #0f172a; margin: 50px 0 20px; font-weight: 800; }
.article-content :deep(img) { width: 100%; border-radius: 8px; margin: 40px 0; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
.article-content :deep(blockquote) { border-left: 6px solid var(--primary); background: #f0fdf4; padding: 40px; margin: 40px 0; font-style: italic; font-size: 1.5rem; color: var(--primary); border-radius: 0 20px 20px 0; }

.article-footer { margin-top: 80px; padding-top: 40px; border-top: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
.mr-2 { margin-right: 12px; }

@media (max-width: 850px) {
  .article-layout { grid-template-columns: 1fr; }
  .article-tools { display: none; }
  .article-header h1 { font-size: 2.4rem; }
}
</style>