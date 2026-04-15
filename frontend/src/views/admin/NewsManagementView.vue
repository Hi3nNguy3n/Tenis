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
    <section class="hero-card">
      <div class="hero-content">
        <span class="section-kicker">Content Management</span>
        <h2>Quản lý Tin tức & Blog</h2>
        <p>Cập nhật thông báo, hình ảnh và diễn biến giải đấu đến các vận động viên.</p>
      </div>
      <el-button type="primary" size="large" :icon="DocumentAdd" @click="openCreateDialog">
        Viết bài mới
      </el-button>
    </section>

    <section class="filter-card">
      <el-input v-model="search" placeholder="Tìm kiếm tiêu đề bài viết..." clearable @input="fetchPosts" style="width: 300px" />
      <el-select v-model="categoryFilter" placeholder="Lọc theo Danh mục" clearable @change="fetchPosts" style="width: 200px">
        <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
      </el-select>
    </section>

    <el-card shadow="never" class="table-card" v-loading="isLoading">
      <el-table :data="posts" stripe style="width: 100%">
        <el-table-column label="Tiêu đề" min-width="300">
          <template #default="{ row }">
            <div class="post-title-cell">
              <strong>{{ row.title }}</strong>
              <span class="post-date">{{ row.created_at || 'Hôm nay' }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="category" label="Danh mục" width="150">
          <template #default="{ row }">
            <el-tag effect="plain" type="info">{{ row.category }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="Trạng thái" width="150">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'warning'">
              {{ row.status === 'published' ? 'Đã xuất bản' : 'Bản nháp' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="Lượt xem" width="120" align="center">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; justify-content: center; gap: 5px;">
              <el-icon><View /></el-icon> {{ row.views || 0 }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="Hành động" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" :icon="Edit" circle @click="openEditDialog(row)" />
            <el-button type="danger" plain size="small" :icon="Delete" circle @click="deletePost(row.id)" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

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
.news-container { display: flex; flex-direction: column; gap: 20px; }

.hero-card {
  padding: 24px 30px; border-radius: 20px; background: white;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
}
.section-kicker { display: inline-flex; margin-bottom: 8px; padding: 6px 12px; border-radius: 999px; background: rgba(20, 98, 80, 0.08); color: #0f5c4d; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; }
.hero-content h2 { margin: 0; font-size: 1.8rem; color: #132722; }
.hero-content p { margin: 5px 0 0 0; color: #64748b; font-size: 0.9rem; }

.filter-card { display: flex; gap: 15px; padding: 15px 20px; background: white; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); }
.table-card { border-radius: 20px; border: none; box-shadow: 0 10px 30px rgba(0,0,0,0.02); }

.post-title-cell { display: flex; flex-direction: column; gap: 4px; }
.post-title-cell strong { font-size: 1rem; color: #1e293b; display: -webkit-box; -webkit-line-clamp: 1; line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
.post-date { font-size: 0.75rem; color: #94a3b8; }

/* Upload Thumbnail UI */
.thumbnail-uploader {
  width: 100%; height: 160px; border: 2px dashed #cbd5e1; border-radius: 12px;
  position: relative; overflow: hidden; cursor: pointer; background: #f8fafc; transition: 0.2s;
}
.thumbnail-uploader:hover { border-color: #006953; background: #f0fdf4; }
.upload-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #94a3b8; gap: 10px; }
.upload-placeholder .el-icon { font-size: 2rem; }
.thumbnail-preview { width: 100%; height: 100%; object-fit: cover; }
.hidden-input { position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
</style>