<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DocumentAdd, Edit, Delete, Picture, View } from '@element-plus/icons-vue'
import { t } from '../../utils/locale'

const posts = ref([])
const isLoading = ref(false)
const search = ref('')
const categoryFilter = ref('')

const isDialogOpen = ref(false)
const isSaving = ref(false)
const isEditMode = ref(false)
const isUploading = ref(false)

const form = ref({
  id: null,
  title: '',
  content: '',
  category: 'announcement',
  status: 'published',
  thumbnail_url: ''
})

const categories = computed(() => [
  { label: t('admin.announcement'), value: 'announcement' },
  { label: t('admin.highlight'), value: 'highlight' },
  { label: t('admin.analysis'), value: 'analysis' },
  { label: t('admin.interview'), value: 'interview' },
  { label: t('admin.others'), value: 'others' }
])

const getCategoryLabel = (val) => {
  const cat = categories.value.find(c => c.value === val)
  return cat ? cat.label : val
}

const fetchPosts = async () => {
  isLoading.value = true
  try {
    const data = await apiClient.get('/api/news/', {
      params: { search: search.value, category: categoryFilter.value }
    })
    posts.value = data
  } catch (err) {
    console.error('Fetch News Error:', err)
    if (err.message.includes('404')) {
      posts.value = [
        { id: 1, title: 'Saigon Open 2026 Opening', category: 'announcement', status: 'published', views: 120, created_at: '2026-04-15' },
        { id: 2, title: 'Highlight: A vs B', category: 'highlight', status: 'draft', views: 0, created_at: '2026-04-16' }
      ]
    }
  } finally {
    isLoading.value = false
  }
}

const openCreateDialog = () => {
  isEditMode.value = false
  form.value = { id: null, title: '', content: '', category: 'announcement', status: 'published', thumbnail_url: '' }
  isDialogOpen.value = true
}

const openEditDialog = (row) => {
  isEditMode.value = true
  form.value = { ...row }
  isDialogOpen.value = true
}

const handleThumbnailUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  isUploading.value = true 
  try {
    const res = await apiClient.request('/api/upload/image', {
      method: 'POST',
      body: formData,
      includeJson: false
    })
    
    form.value.thumbnail_url = res.url 
    ElMessage.success(t('admin.uploadSuccess') || 'Upload successful!')
  } catch (err) {
    ElMessage.error(t('admin.uploadError') || 'Upload failed: ' + (err.message || 'Server error'))
  } finally {
    isUploading.value = false 
    event.target.value = '' 
  }
}

const savePost = async () => {
  if (!form.value.title || !form.value.content) {
    return ElMessage.warning(t('admin.inputRequired'))
  }

  isSaving.value = true
  try {
    if (isEditMode.value) {
      await apiClient.put(`/api/news/${form.value.id}`, form.value)
      ElMessage.success(t('admin.saveArticleSuccess'))
    } else {
      await apiClient.post('/api/news/', form.value)
      ElMessage.success(t('admin.publishSuccess'))
    }
    isDialogOpen.value = false
    fetchPosts()
  } catch (err) {
    ElMessage.error(t('admin.updateError') + ': ' + err.message)
  } finally {
    isSaving.value = false
  }
}

const deletePost = (id) => {
  ElMessageBox.confirm(t('admin.deletePostConfirm'), t('admin.action'), { 
    type: 'warning',
    confirmButtonText: t('admin.confirm'),
    cancelButtonText: t('admin.cancel'),
  })
    .then(async () => {
      try {
        await apiClient.delete(`/api/news/${id}`)
        ElMessage.success(t('admin.deletePostSuccess'))
        fetchPosts()
      } catch (err) {
        ElMessage.error(t('admin.updateError') + ': ' + err.message)
      }
    })
}

onMounted(fetchPosts)
</script>

<template>
  <div class="news-container">
    <section class="action-bar-glass shadow-sm">
      <div class="action-info">
        <div class="kicker-wrap">
          <span class="section-kicker">Content Management</span>
          <div class="live-indicator">
            <span class="dot"></span>
            LIVE
          </div>
        </div>
        <h2>{{ $t('admin.newsManagementTitle') }}</h2>
        <p>{{ $t('admin.newsManagementDesc') }}</p>
      </div>
      <div class="hero-actions-v2">
        <el-button :icon="DocumentAdd" type="primary" round @click="openCreateDialog">
          {{ $t('admin.writeNewPost') }}
        </el-button>
      </div>
    </section>

    <section class="filter-card">
      <el-input v-model="search" :placeholder="$t('admin.searchPostPlaceholder')" clearable @input="fetchPosts" style="width: 300px" />
      <el-select v-model="categoryFilter" :placeholder="$t('admin.filterByCategory')" clearable @change="fetchPosts" style="width: 200px">
        <el-option v-for="cat in categories" :key="cat.value" :label="cat.label" :value="cat.value" />
      </el-select>
    </section>

    <section class="table-card-premium shadow-sm" v-loading="isLoading">
      <el-table :data="posts" stripe style="width: 100%" class="modern-news-table">
        <el-table-column :label="$t('admin.article')" min-width="350">
          <template #default="{ row }">
            <div class="post-info-cell">
              <span class="post-title">{{ row.title }}</span>
              <span class="post-meta">{{ row.created_at ? new Date(row.created_at).toLocaleDateString() : 'Today' }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column :label="$t('admin.filterByCategory')" width="180">
          <template #default="{ row }">
            <el-tag effect="light" type="info" class="category-pill">
              {{ getCategoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.status')" width="160" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'warning'" class="status-pill">
              {{ row.status === 'published' ? $t('admin.published') : $t('admin.draft') }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.action')" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-tooltip :content="$t('admin.editPost')" placement="top">
                <el-button type="primary" plain circle :icon="Edit" @click="openEditDialog(row)" />
              </el-tooltip>
              <el-tooltip :content="$t('admin.delete')" placement="top">
                <el-button type="danger" plain circle :icon="Delete" @click="deletePost(row.id)" />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="isDialogOpen" :title="isEditMode ? $t('admin.editPost') : $t('admin.createNewPost')" width="800px" destroy-on-close top="5vh">
      <el-form label-position="top" class="news-form">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-form-item :label="$t('admin.postTitleLabel')" required>
              <el-input v-model="form.title" placeholder="..." size="large" />
            </el-form-item>

            <el-form-item :label="$t('admin.postContentLabel')" required>
              <el-input 
                v-model="form.content" 
                type="textarea" 
                :rows="12" 
                placeholder="..." 
              />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item :label="$t('admin.status')">
              <el-select v-model="form.status" style="width: 100%">
                <el-option :label="$t('admin.publishedPublic')" value="published" />
                <el-option :label="$t('admin.draftHidden')" value="draft" />
              </el-select>
            </el-form-item>

            <el-form-item :label="$t('admin.filterByCategory')">
              <el-select v-model="form.category" style="width: 100%">
                <el-option v-for="cat in categories" :key="cat.value" :label="cat.label" :value="cat.value" />
              </el-select>
            </el-form-item>

            <el-form-item :label="$t('admin.thumbnailMedia')">
              <div 
                class="thumbnail-uploader" 
                v-loading="isUploading" 
                :element-loading-text="$t('admin.uploadingWait')"
              >
                <video 
                  v-if="form.thumbnail_url && form.thumbnail_url.match(/\.(mp4|webm|ogg)$/i)" 
                  :src="form.thumbnail_url" 
                  class="thumbnail-preview" 
                  controls>
                </video>
                
                <img 
                  v-else-if="form.thumbnail_url" 
                  :src="form.thumbnail_url" 
                  class="thumbnail-preview" 
                />
                
                <div v-else class="upload-placeholder">
                  <el-icon><Picture /></el-icon>
                  <span>{{ $t('admin.uploadHint') }}</span>
                </div>
                
                <input 
                  type="file" 
                  class="hidden-input" 
                  accept="image/*,video/*" 
                  :disabled="isUploading"
                  @change="handleThumbnailUpload" 
                />
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <el-button @click="isDialogOpen = false">{{ $t('admin.cancel') }}</el-button>
        <el-button type="primary" :loading="isSaving" @click="savePost">
          {{ isEditMode ? $t('admin.update') : $t('admin.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.news-container { display: grid; gap: 16px; padding: 10px; }

.action-bar-glass {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  padding: 16px 24px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 10px 30px rgba(0,0,0,0.03);
}

.kicker-wrap { display: flex; align-items: center; gap: 12px; margin-bottom: 2px; }
.section-kicker { font-size: 0.7rem; font-weight: 800; color: #1e293b; text-transform: uppercase; letter-spacing: 0.05em; }

.live-indicator {
  display: flex; align-items: center; gap: 6px;
  background: #f0fdf4; color: #15803d; font-size: 0.65rem; font-weight: 800;
  padding: 2px 8px; border-radius: 99px;
}
.dot { width: 6px; height: 6px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite; }

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}

.action-bar-glass h2 { margin: 0; font-size: 1.25rem; color: #0f172a; font-weight: 700; }
.action-bar-glass p { margin: 2px 0 0 0; color: #64748b; font-size: 0.85rem; }

.hero-actions-v2 { display: flex; align-items: center; gap: 12px; }

.filter-card {
  display: flex; gap: 15px; padding: 16px 24px; background: white;
  border-radius: 20px; border: 1px solid #f1f5f9;
}

.table-card-premium {
  background: white; padding: 8px; border-radius: 20px;
  border: 1px solid #f1f5f9; box-shadow: 0 10px 30px rgba(0,0,0,0.03);
  overflow: hidden;
}

.post-info-cell { display: flex; flex-direction: column; gap: 2px; }
.post-title { font-weight: 700; color: #0f172a; font-size: 0.95rem; }
.post-meta { font-size: 0.75rem; color: #94a3b8; font-weight: 600; }

.category-pill { font-weight: 700; border-radius: 6px; padding: 0 10px; height: 24px; border: none; }

.status-pill { font-weight: 800; border-radius: 99px; padding: 0 16px; font-size: 0.65rem; border: none !important; }

.action-buttons { display: flex; gap: 10px; justify-content: center; }

:deep(.el-table) { border-radius: 12px; }
:deep(.el-table .cell) { padding: 12px 16px; }

.shadow-sm { box-shadow: 0 1px 3px rgba(0,0,0,0.05); }

/* Dialog Form */
.news-form { padding-top: 10px; }
.thumbnail-uploader {
  width: 100%; height: 160px; border: 2px dashed #cbd5e1; border-radius: 20px;
  position: relative; overflow: hidden; cursor: pointer; background: #f8fafc; transition: 0.3s;
}
.thumbnail-uploader:hover { border-color: #3b82f6; background: #eff6ff; }
.upload-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #94a3b8; gap: 8px; }
.thumbnail-preview { width: 100%; height: 100%; object-fit: cover; }
.hidden-input { position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
</style>