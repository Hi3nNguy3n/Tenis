<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DocumentAdd, Edit, Delete, Picture, View } from '@element-plus/icons-vue'

const posts = ref([])
const isLoading = ref(false)
const search = ref('')
const categoryFilter = ref('')

// State cho Dialog
const isDialogOpen = ref(false)
const isSaving = ref(false)
const isEditMode = ref(false)

const form = ref({
  id: null,
  title: '',
  content: '',
  category: 'Thông báo',
  status: 'published',
  thumbnail_url: ''
})

const categories = ['Thông báo', 'Highlight', 'Phân tích', 'Phỏng vấn', 'Khác']

const fetchPosts = async () => {
  isLoading.value = true
  try {
    // Giả định Backend đã có API này. Nếu chưa, hệ thống sẽ báo lỗi 404 để bạn biết đường code thêm Backend
    const data = await apiClient.get('/api/news/', {
      params: { search: search.value, category: categoryFilter.value }
    })
    posts.value = data
  } catch (err) {
    console.error('Lỗi tải tin tức:', err)
    // Nếu chưa có API, tạo dữ liệu ảo để test UI
    if (err.message.includes('404')) {
      posts.value = [
        { id: 1, title: 'Khai mạc Saigon Open 2026', category: 'Thông báo', status: 'published', views: 120, created_at: '2026-04-15' },
        { id: 2, title: 'Highlight: Nguyễn Văn A vs Trần B', category: 'Highlight', status: 'draft', views: 0, created_at: '2026-04-16' }
      ]
      ElMessage.warning('Đang dùng dữ liệu ảo vì chưa có API Backend /api/news')
    }
  } finally {
    isLoading.value = false
  }
}

const openCreateDialog = () => {
  isEditMode.value = false
  form.value = { id: null, title: '', content: '', category: 'Thông báo', status: 'published', thumbnail_url: '' }
  isDialogOpen.value = true
}

const openEditDialog = (row) => {
  isEditMode.value = true
  form.value = { ...row }
  isDialogOpen.value = true
}

// Xử lý upload ảnh bìa (Thumbnail)
const handleThumbnailUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // Đồng bộ cách đóng gói dữ liệu với Profile
  const formData = new FormData()
  formData.append('file', file)

  isSaving.value = true // Hiện loading để user không bấm lung tung
  try {
    // Gọi đến cổng upload tập trung vừa tạo ở Bước 1
    const res = await apiClient.request('/api/upload/image', {
      method: 'POST',
      body: formData,
      includeJson: false // Quan trọng: Để apiClient không tự ép kiểu JSON khi gửi file
    })
    
    // Gán URL trả về từ server vào form
    form.value.thumbnail_url = res.url 
    ElMessage.success('Tải ảnh bìa thành công!')
  } catch (err) {
    ElMessage.error('Lỗi upload ảnh: ' + (err.message || 'Server không phản hồi'))
  } finally {
    isSaving.value = false
  }
}

const savePost = async () => {
  if (!form.value.title || !form.value.content) {
    return ElMessage.warning('Vui lòng nhập đủ Tiêu đề và Nội dung')
  }

  isSaving.value = true
  try {
    if (isEditMode.value) {
      await apiClient.put(`/api/news/${form.value.id}`, form.value)
      ElMessage.success('Cập nhật bài viết thành công')
    } else {
      await apiClient.post('/api/news', form.value)
      ElMessage.success('Tạo bài viết mới thành công')
    }
    isDialogOpen.value = false
    fetchPosts()
  } catch (err) {
    ElMessage.error('Lỗi khi lưu: ' + err.message)
  } finally {
    isSaving.value = false
  }
}

const deletePost = (id) => {
  ElMessageBox.confirm('Bạn có chắc muốn xóa bài viết này không?', 'Cảnh báo', { type: 'warning' })
    .then(async () => {
      try {
        await apiClient.delete(`/api/news/${id}`)
        ElMessage.success('Đã xóa bài viết')
        fetchPosts()
      } catch (err) {
        ElMessage.error('Lỗi xóa bài: ' + err.message)
      }
    })
}

onMounted(fetchPosts)
</script>

<template>
  <div class="news-container">
    <!-- HEADER PREMIUM -->
    <section class="action-bar-glass shadow-sm">
      <div class="action-info">
        <div class="kicker-wrap">
          <span class="section-kicker">Content Management</span>
          <div class="live-indicator">
            <span class="dot"></span>
            LIVE
          </div>
        </div>
        <h2>Quản lý Tin tức & Blog</h2>
        <p>Viết bài, tải ảnh và điều phối luồng thông tin giải đấu đến vận động viên.</p>
      </div>
      <div class="hero-actions-v2">
        <el-button :icon="DocumentAdd" type="primary" round @click="openCreateDialog">
          Viết bài mới
        </el-button>
      </div>
    </section>

    <section class="filter-card">
      <el-input v-model="search" placeholder="Tìm kiếm tiêu đề bài viết..." clearable @input="fetchPosts" style="width: 300px" />
      <el-select v-model="categoryFilter" placeholder="Lọc theo Danh mục" clearable @change="fetchPosts" style="width: 200px">
        <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
      </el-select>
    </section>

    <section class="table-card-premium shadow-sm" v-loading="isLoading">
      <el-table :data="posts" stripe style="width: 100%" class="modern-news-table">
        <el-table-column label="Bài viết" min-width="350">
          <template #default="{ row }">
            <div class="post-info-cell">
              <span class="post-title">{{ row.title }}</span>
              <span class="post-meta">{{ row.created_at ? new Date(row.created_at).toLocaleDateString('vi-VN') : 'Hôm nay' }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="Danh mục" width="180">
          <template #default="{ row }">
            <el-tag effect="light" type="info" class="category-pill">
              {{ row.category || 'Chung' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="Trạng thái" width="160" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'warning'" class="status-pill">
              {{ row.status === 'published' ? 'Đã xuất bản' : 'Bản nháp' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="Điều hành" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-tooltip content="Chỉnh sửa bài viết" placement="top">
                <el-button type="primary" plain circle :icon="Edit" @click="openEditDialog(row)" />
              </el-tooltip>
              <el-tooltip content="Xóa bài viết" placement="top">
                <el-button type="danger" plain circle :icon="Delete" @click="deletePost(row.id)" />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="isDialogOpen" :title="isEditMode ? 'Chỉnh sửa bài viết' : 'Soạn bài viết mới'" width="800px" destroy-on-close top="5vh">
      <el-form label-position="top" class="news-form">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-form-item label="Tiêu đề bài viết" required>
              <el-input v-model="form.title" placeholder="Nhập tiêu đề hấp dẫn..." size="large" />
            </el-form-item>

            <el-form-item label="Nội dung" required>
              <el-input 
                v-model="form.content" 
                type="textarea" 
                :rows="12" 
                placeholder="Nội dung bài viết... (Có thể nhập mã HTML nếu cần)" 
              />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="Trạng thái">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="Đã xuất bản (Công khai)" value="published" />
                <el-option label="Lưu bản nháp (Ẩn)" value="draft" />
              </el-select>
            </el-form-item>

            <el-form-item label="Danh mục">
              <el-select v-model="form.category" style="width: 100%">
                <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
              </el-select>
            </el-form-item>

            <el-form-item label="Ảnh bìa (Thumbnail)">
              <div class="thumbnail-uploader">
                <img v-if="form.thumbnail_url" :src="form.thumbnail_url" class="thumbnail-preview" />
                <div v-else class="upload-placeholder">
                  <el-icon><Picture /></el-icon>
                  <span>Nhấp để tải ảnh</span>
                </div>
                <input type="file" class="hidden-input" accept="image/*" @change="handleThumbnailUpload" />
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <el-button @click="isDialogOpen = false">Hủy bỏ</el-button>
        <el-button type="primary" :loading="isSaving" @click="savePost">
          {{ isEditMode ? 'Cập nhật' : 'Đăng bài' }}
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