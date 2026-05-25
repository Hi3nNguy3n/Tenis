<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Calendar,
  Delete,
  Edit,
  Link,
  Medal,
  Picture,
  Plus,
  Refresh,
  UploadFilled,
} from '@element-plus/icons-vue'
import { apiClient } from '../../services/apiClient'

const activeTab = ref('banners')
const loading = ref(false)
const saving = ref(false)
const uploadLoading = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('create')
const editingId = ref(null)
const banners = ref([])
const sponsors = ref([])
const bannerPlacementFilter = ref('')
const sponsorTierFilter = ref('')

const bannerPlacements = [
  { label: 'Trang chủ - Banner chính', value: 'home_top' },
  { label: 'Trang chủ - Quảng cáo ngang', value: 'home_ad' },
  { label: 'Giải đấu - Banner', value: 'tournaments_top' },
  { label: 'Bảng xếp hạng - Banner', value: 'rankings_top' },
  { label: 'Thách đấu - Banner', value: 'challenges_top' },
]

const sponsorTiers = [
  { label: 'Premier', value: 'premier' },
  { label: 'Gold', value: 'gold' },
  { label: 'Silver', value: 'silver' },
  { label: 'Partner', value: 'partner' },
]

const emptyBannerForm = () => ({
  title: '',
  subtitle: '',
  image_url: '',
  link_url: '',
  placement: 'home_top',
  display_order: 0,
  is_active: true,
  open_in_new_tab: true,
  start_at: null,
  end_at: null,
})

const emptySponsorForm = () => ({
  name: '',
  logo_url: '',
  website_url: '',
  tier: 'partner',
  description: '',
  display_order: 0,
  is_active: true,
  start_at: null,
  end_at: null,
})

const form = reactive({
  banner: emptyBannerForm(),
  sponsor: emptySponsorForm(),
})

const dashboardStats = computed(() => ({
  banners: banners.value.length,
  sponsors: sponsors.value.length,
  activeBanners: banners.value.filter(item => item.is_active).length,
  activeSponsors: sponsors.value.filter(item => item.is_active).length,
}))

const dialogTitle = computed(() => {
  const subject = activeTab.value === 'banners' ? 'banner' : 'nhà tài trợ'
  return dialogMode.value === 'create' ? `Thêm ${subject}` : `Cập nhật ${subject}`
})

const activeForm = computed(() => activeTab.value === 'banners' ? form.banner : form.sponsor)
const activePreviewUrl = computed(() => activeTab.value === 'banners' ? form.banner.image_url : form.sponsor.logo_url)

const placementLabel = (value) => bannerPlacements.find(item => item.value === value)?.label || value
const tierLabel = (value) => sponsorTiers.find(item => item.value === value)?.label || value

const formatDateTime = (value) => {
  if (!value) return 'Không giới hạn'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const normalizeDatePayload = (value) => {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toISOString()
}

const fetchBanners = async () => {
  const params = {}
  if (bannerPlacementFilter.value) params.placement = bannerPlacementFilter.value
  banners.value = await apiClient.get('/api/marketing/admin/banners', { params })
}

const fetchSponsors = async () => {
  const params = {}
  if (sponsorTierFilter.value) params.tier = sponsorTierFilter.value
  sponsors.value = await apiClient.get('/api/marketing/admin/sponsors', { params })
}

const fetchAll = async () => {
  loading.value = true
  try {
    await Promise.all([fetchBanners(), fetchSponsors()])
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || err.message || 'Không tải được dữ liệu marketing')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  Object.assign(form.banner, emptyBannerForm())
  Object.assign(form.sponsor, emptySponsorForm())
  editingId.value = null
}

const openCreateDialog = () => {
  resetForm()
  dialogMode.value = 'create'
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  resetForm()
  dialogMode.value = 'edit'
  editingId.value = row.id

  if (activeTab.value === 'banners') {
    Object.assign(form.banner, {
      title: row.title || '',
      subtitle: row.subtitle || '',
      image_url: row.image_url || '',
      link_url: row.link_url || '',
      placement: row.placement || 'home_top',
      display_order: row.display_order || 0,
      is_active: Boolean(row.is_active),
      open_in_new_tab: Boolean(row.open_in_new_tab),
      start_at: row.start_at || null,
      end_at: row.end_at || null,
    })
  } else {
    Object.assign(form.sponsor, {
      name: row.name || '',
      logo_url: row.logo_url || '',
      website_url: row.website_url || '',
      tier: row.tier || 'partner',
      description: row.description || '',
      display_order: row.display_order || 0,
      is_active: Boolean(row.is_active),
      start_at: row.start_at || null,
      end_at: row.end_at || null,
    })
  }

  dialogVisible.value = true
}

const buildPayload = () => {
  if (activeTab.value === 'banners') {
    return {
      ...form.banner,
      start_at: normalizeDatePayload(form.banner.start_at),
      end_at: normalizeDatePayload(form.banner.end_at),
      subtitle: form.banner.subtitle || null,
      link_url: form.banner.link_url || null,
    }
  }

  return {
    ...form.sponsor,
    start_at: normalizeDatePayload(form.sponsor.start_at),
    end_at: normalizeDatePayload(form.sponsor.end_at),
    website_url: form.sponsor.website_url || null,
    description: form.sponsor.description || null,
  }
}

const validateForm = () => {
  if (activeTab.value === 'banners') {
    if (!form.banner.title.trim()) return 'Vui lòng nhập tiêu đề banner'
    if (!form.banner.image_url.trim()) return 'Vui lòng upload hoặc nhập URL ảnh banner'
  } else {
    if (!form.sponsor.name.trim()) return 'Vui lòng nhập tên nhà tài trợ'
    if (!form.sponsor.logo_url.trim()) return 'Vui lòng upload hoặc nhập URL logo'
  }
  return ''
}

const saveItem = async () => {
  const validationMessage = validateForm()
  if (validationMessage) {
    ElMessage.warning(validationMessage)
    return
  }

  saving.value = true
  try {
    const payload = buildPayload()
    if (activeTab.value === 'banners') {
      if (dialogMode.value === 'create') {
        await apiClient.post('/api/marketing/admin/banners', payload)
      } else {
        await apiClient.put(`/api/marketing/admin/banners/${editingId.value}`, payload)
      }
      await fetchBanners()
    } else {
      if (dialogMode.value === 'create') {
        await apiClient.post('/api/marketing/admin/sponsors', payload)
      } else {
        await apiClient.put(`/api/marketing/admin/sponsors/${editingId.value}`, payload)
      }
      await fetchSponsors()
    }
    ElMessage.success('Đã lưu dữ liệu')
    dialogVisible.value = false
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || err.message || 'Lưu dữ liệu thất bại')
  } finally {
    saving.value = false
  }
}

const deleteItem = async (row) => {
  const label = activeTab.value === 'banners' ? row.title : row.name
  await ElMessageBox.confirm(`Xóa "${label}"?`, 'Xác nhận xóa', {
    confirmButtonText: 'Xóa',
    cancelButtonText: 'Hủy',
    type: 'warning',
  })

  if (activeTab.value === 'banners') {
    await apiClient.delete(`/api/marketing/admin/banners/${row.id}`)
    await fetchBanners()
  } else {
    await apiClient.delete(`/api/marketing/admin/sponsors/${row.id}`)
    await fetchSponsors()
  }
  ElMessage.success('Đã xóa')
}

const toggleActive = async (row) => {
  try {
    const payload = { is_active: !row.is_active }
    if (activeTab.value === 'banners') {
      await apiClient.put(`/api/marketing/admin/banners/${row.id}`, payload)
      await fetchBanners()
    } else {
      await apiClient.put(`/api/marketing/admin/sponsors/${row.id}`, payload)
      await fetchSponsors()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || err.message || 'Không cập nhật được trạng thái')
  }
}

const uploadAsset = async (file) => {
  uploadLoading.value = true
  try {
    const body = new FormData()
    body.append('file', file)
    const res = await apiClient.post('/api/upload/image', body)
    if (activeTab.value === 'banners') form.banner.image_url = res.url
    else form.sponsor.logo_url = res.url
    ElMessage.success('Upload thành công')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || err.message || 'Upload thất bại')
  } finally {
    uploadLoading.value = false
  }
  return false
}

onMounted(fetchAll)
</script>

<template>
  <div class="marketing-page" v-loading="loading">
    <div class="metric-grid">
      <div class="metric-card">
        <div class="metric-icon is-blue"><el-icon><Picture /></el-icon></div>
        <div>
          <span>Tổng banner</span>
          <strong>{{ dashboardStats.banners }}</strong>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-icon is-green"><el-icon><Picture /></el-icon></div>
        <div>
          <span>Banner đang bật</span>
          <strong>{{ dashboardStats.activeBanners }}</strong>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-icon is-purple"><el-icon><Medal /></el-icon></div>
        <div>
          <span>Nhà tài trợ</span>
          <strong>{{ dashboardStats.sponsors }}</strong>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-icon is-orange"><el-icon><Medal /></el-icon></div>
        <div>
          <span>Đang hiển thị</span>
          <strong>{{ dashboardStats.activeSponsors }}</strong>
        </div>
      </div>
    </div>

    <div class="marketing-shell">
      <div class="toolbar">
        <div>
          <span class="eyebrow">Marketing</span>
          <h2>Banner & Nhà tài trợ</h2>
          <p>Quản lý nội dung quảng bá, đối tác và hình ảnh hiển thị trên website người dùng.</p>
        </div>
        <div class="toolbar-actions">
          <el-button :icon="Refresh" @click="fetchAll">Làm mới</el-button>
          <el-button type="primary" :icon="Plus" class="primary-action" @click="openCreateDialog">
            Thêm mới
          </el-button>
        </div>
      </div>

      <el-tabs v-model="activeTab" class="marketing-tabs">
        <el-tab-pane label="Banner" name="banners">
          <div class="filter-row">
            <el-select v-model="bannerPlacementFilter" placeholder="Tất cả vị trí" clearable @change="fetchBanners">
              <el-option v-for="item in bannerPlacements" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </div>

          <el-table
            :data="banners"
            class="marketing-table"
            :header-cell-style="{ background: 'transparent', color: '#64748b', fontWeight: '800', borderBottom: '2px solid #eef2f7' }"
            :cell-style="{ background: 'transparent' }"
          >
            <el-table-column label="Ảnh" width="190">
              <template #default="{ row }">
                <img :src="row.image_url" :alt="row.title" class="asset-preview banner-preview" />
              </template>
            </el-table-column>
            <el-table-column label="Thông tin" min-width="280">
              <template #default="{ row }">
                <strong class="item-title">{{ row.title }}</strong>
                <span class="item-subtitle">{{ row.subtitle || 'Không có mô tả phụ' }}</span>
                <a v-if="row.link_url" :href="row.link_url" target="_blank" class="item-link">
                  <el-icon><Link /></el-icon>{{ row.link_url }}
                </a>
              </template>
            </el-table-column>
            <el-table-column label="Vị trí" width="190">
              <template #default="{ row }">
                <el-tag effect="plain" class="soft-tag">{{ placementLabel(row.placement) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Thứ tự" width="90" prop="display_order" align="center" />
            <el-table-column label="Lịch hiển thị" width="230">
              <template #default="{ row }">
                <div class="date-stack">
                  <span><el-icon><Calendar /></el-icon>Từ: {{ formatDateTime(row.start_at) }}</span>
                  <span><el-icon><Calendar /></el-icon>Đến: {{ formatDateTime(row.end_at) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="Trạng thái" width="120" align="center">
              <template #default="{ row }">
                <el-switch :model-value="row.is_active" @change="toggleActive(row)" />
              </template>
            </el-table-column>
            <el-table-column label="Thao tác" width="145" fixed="right" align="center">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button circle :icon="Edit" @click="openEditDialog(row)" />
                  <el-button circle type="danger" :icon="Delete" @click="deleteItem(row)" />
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="Nhà tài trợ" name="sponsors">
          <div class="filter-row">
            <el-select v-model="sponsorTierFilter" placeholder="Tất cả hạng tài trợ" clearable @change="fetchSponsors">
              <el-option v-for="item in sponsorTiers" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </div>

          <el-table
            :data="sponsors"
            class="marketing-table"
            :header-cell-style="{ background: 'transparent', color: '#64748b', fontWeight: '800', borderBottom: '2px solid #eef2f7' }"
            :cell-style="{ background: 'transparent' }"
          >
            <el-table-column label="Logo" width="170">
              <template #default="{ row }">
                <img :src="row.logo_url" :alt="row.name" class="asset-preview sponsor-preview" />
              </template>
            </el-table-column>
            <el-table-column label="Thông tin" min-width="280">
              <template #default="{ row }">
                <strong class="item-title">{{ row.name }}</strong>
                <span class="item-subtitle">{{ row.description || 'Không có mô tả' }}</span>
                <a v-if="row.website_url" :href="row.website_url" target="_blank" class="item-link">
                  <el-icon><Link /></el-icon>{{ row.website_url }}
                </a>
              </template>
            </el-table-column>
            <el-table-column label="Hạng" width="130">
              <template #default="{ row }">
                <el-tag effect="plain" class="soft-tag">{{ tierLabel(row.tier) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Thứ tự" width="90" prop="display_order" align="center" />
            <el-table-column label="Lịch hiển thị" width="230">
              <template #default="{ row }">
                <div class="date-stack">
                  <span><el-icon><Calendar /></el-icon>Từ: {{ formatDateTime(row.start_at) }}</span>
                  <span><el-icon><Calendar /></el-icon>Đến: {{ formatDateTime(row.end_at) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="Trạng thái" width="120" align="center">
              <template #default="{ row }">
                <el-switch :model-value="row.is_active" @change="toggleActive(row)" />
              </template>
            </el-table-column>
            <el-table-column label="Thao tác" width="145" fixed="right" align="center">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button circle :icon="Edit" @click="openEditDialog(row)" />
                  <el-button circle type="danger" :icon="Delete" @click="deleteItem(row)" />
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="980px" destroy-on-close class="marketing-dialog">
      <div class="editor-layout">
        <aside class="preview-panel">
          <div class="preview-topline">
            <span>{{ activeTab === 'banners' ? 'Preview banner' : 'Preview logo' }}</span>
            <el-tag :type="activeForm.is_active ? 'success' : 'info'" effect="light">
              {{ activeForm.is_active ? 'Đang bật' : 'Đang tắt' }}
            </el-tag>
          </div>

          <div class="preview-frame" :class="{ 'is-sponsor': activeTab === 'sponsors' }">
            <img v-if="activePreviewUrl" :src="activePreviewUrl" alt="" />
            <div v-else class="preview-empty">
              <el-icon><UploadFilled /></el-icon>
              <span>Chưa có hình ảnh</span>
            </div>
          </div>

          <div class="preview-copy">
            <strong>{{ activeTab === 'banners' ? (form.banner.title || 'Tiêu đề banner') : (form.sponsor.name || 'Tên nhà tài trợ') }}</strong>
            <p>{{ activeTab === 'banners' ? (form.banner.subtitle || 'Mô tả phụ sẽ hiển thị ở đây.') : (form.sponsor.description || 'Mô tả nhà tài trợ sẽ hiển thị ở đây.') }}</p>
          </div>
        </aside>

        <el-form label-position="top" class="marketing-form">
          <template v-if="activeTab === 'banners'">
            <div class="form-section">
              <div class="section-title">
                <h3>Nội dung banner</h3>
                <p>Thiết lập tiêu đề, mô tả và vị trí hiển thị.</p>
              </div>
              <el-form-item label="Tiêu đề">
                <el-input v-model="form.banner.title" placeholder="VD: Giải đấu nổi bật tháng này" />
              </el-form-item>
              <el-form-item label="Mô tả phụ">
                <el-input v-model="form.banner.subtitle" placeholder="Thông điệp ngắn hiển thị kèm banner" />
              </el-form-item>
              <div class="form-grid">
                <el-form-item label="Vị trí">
                  <el-select v-model="form.banner.placement">
                    <el-option v-for="item in bannerPlacements" :key="item.value" :label="item.label" :value="item.value" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Thứ tự">
                  <el-input-number v-model="form.banner.display_order" :min="0" class="full-input" />
                </el-form-item>
              </div>
            </div>

            <div class="form-section">
              <div class="section-title">
                <h3>Hình ảnh & điều hướng</h3>
                <p>Upload file hoặc dán URL ảnh đã có sẵn.</p>
              </div>
              <el-form-item label="Ảnh banner">
                <div class="upload-row">
                  <el-upload :show-file-list="false" :before-upload="uploadAsset" accept="image/*,.svg">
                    <el-button :icon="UploadFilled" :loading="uploadLoading">Upload ảnh</el-button>
                  </el-upload>
                  <el-input v-model="form.banner.image_url" placeholder="Hoặc dán URL ảnh" />
                </div>
              </el-form-item>
              <el-form-item label="Link khi click">
                <el-input v-model="form.banner.link_url" placeholder="https://..." />
              </el-form-item>
            </div>

            <div class="form-section">
              <div class="section-title">
                <h3>Lịch hiển thị</h3>
                <p>Bỏ trống nếu muốn hiển thị không giới hạn thời gian.</p>
              </div>
              <div class="form-grid">
                <el-form-item label="Bắt đầu">
                  <el-date-picker v-model="form.banner.start_at" type="datetime" placeholder="Không giới hạn" class="full-input" />
                </el-form-item>
                <el-form-item label="Kết thúc">
                  <el-date-picker v-model="form.banner.end_at" type="datetime" placeholder="Không giới hạn" class="full-input" />
                </el-form-item>
              </div>
              <div class="switch-row">
                <el-switch v-model="form.banner.is_active" active-text="Đang bật" inactive-text="Tắt" />
                <el-switch v-model="form.banner.open_in_new_tab" active-text="Mở tab mới" inactive-text="Cùng tab" />
              </div>
            </div>
          </template>

          <template v-else>
            <div class="form-section">
              <div class="section-title">
                <h3>Thông tin nhà tài trợ</h3>
                <p>Thiết lập tên, hạng tài trợ và mô tả ngắn.</p>
              </div>
              <el-form-item label="Tên nhà tài trợ">
                <el-input v-model="form.sponsor.name" placeholder="VD: Emirates" />
              </el-form-item>
              <div class="form-grid">
                <el-form-item label="Hạng tài trợ">
                  <el-select v-model="form.sponsor.tier">
                    <el-option v-for="item in sponsorTiers" :key="item.value" :label="item.label" :value="item.value" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Thứ tự">
                  <el-input-number v-model="form.sponsor.display_order" :min="0" class="full-input" />
                </el-form-item>
              </div>
              <el-form-item label="Mô tả">
                <el-input v-model="form.sponsor.description" type="textarea" :rows="3" placeholder="Thông tin mô tả ngắn về đối tác" />
              </el-form-item>
            </div>

            <div class="form-section">
              <div class="section-title">
                <h3>Logo & website</h3>
                <p>Logo nên dùng nền trong suốt hoặc ảnh có tỷ lệ ngang.</p>
              </div>
              <el-form-item label="Logo">
                <div class="upload-row">
                  <el-upload :show-file-list="false" :before-upload="uploadAsset" accept="image/*,.svg">
                    <el-button :icon="UploadFilled" :loading="uploadLoading">Upload logo</el-button>
                  </el-upload>
                  <el-input v-model="form.sponsor.logo_url" placeholder="Hoặc dán URL logo" />
                </div>
              </el-form-item>
              <el-form-item label="Website">
                <el-input v-model="form.sponsor.website_url" placeholder="https://..." />
              </el-form-item>
            </div>

            <div class="form-section">
              <div class="section-title">
                <h3>Lịch hiển thị</h3>
                <p>Bỏ trống nếu muốn hiển thị không giới hạn thời gian.</p>
              </div>
              <div class="form-grid">
                <el-form-item label="Bắt đầu">
                  <el-date-picker v-model="form.sponsor.start_at" type="datetime" placeholder="Không giới hạn" class="full-input" />
                </el-form-item>
                <el-form-item label="Kết thúc">
                  <el-date-picker v-model="form.sponsor.end_at" type="datetime" placeholder="Không giới hạn" class="full-input" />
                </el-form-item>
              </div>
              <div class="switch-row">
                <el-switch v-model="form.sponsor.is_active" active-text="Đang bật" inactive-text="Tắt" />
              </div>
            </div>
          </template>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="dialogVisible = false">Hủy</el-button>
        <el-button type="primary" :loading="saving" @click="saveItem">Lưu thay đổi</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.marketing-page {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  min-height: 108px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.04);
}

.metric-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  font-size: 1.35rem;
}

.metric-icon.is-blue { background: #eff6ff; color: #2563eb; }
.metric-icon.is-green { background: #ecfdf5; color: #059669; }
.metric-icon.is-purple { background: #f5f3ff; color: #7c3aed; }
.metric-icon.is-orange { background: #fff7ed; color: #ea580c; }

.metric-card span {
  display: block;
  color: #64748b;
  font-size: 0.82rem;
  font-weight: 800;
}

.metric-card strong {
  display: block;
  margin-top: 5px;
  color: #0f172a;
  font-size: 1.65rem;
  line-height: 1;
  font-weight: 900;
}

.marketing-shell {
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 20px 42px rgba(15, 23, 42, 0.05);
  overflow: hidden;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 24px;
  border-bottom: 1px solid #eef2f7;
}

.eyebrow {
  color: #059669;
  font-size: 0.75rem;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.toolbar h2 {
  margin: 6px 0 6px;
  color: #0f172a;
  font-size: 1.5rem;
  font-weight: 900;
}

.toolbar p {
  margin: 0;
  color: #64748b;
  font-size: 0.92rem;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.primary-action {
  background: #059669 !important;
  border-color: #059669 !important;
  font-weight: 800 !important;
}

.marketing-tabs {
  padding: 0 24px 24px;
}

.marketing-tabs :deep(.el-tabs__header) {
  margin-bottom: 18px;
}

.marketing-tabs :deep(.el-tabs__item) {
  height: 52px;
  font-weight: 900;
}

.filter-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 14px;
}

.filter-row .el-select {
  width: 280px;
}

.marketing-table {
  width: 100%;
  --el-table-border-color: #eef2f7;
  --el-table-row-hover-bg-color: #f8fafc;
}

.marketing-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.asset-preview {
  display: block;
  width: 100%;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  object-fit: contain;
}

.banner-preview {
  height: 82px;
}

.sponsor-preview {
  height: 70px;
  padding: 10px;
}

.item-title,
.item-subtitle,
.item-link {
  display: block;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-title {
  color: #0f172a;
  font-weight: 900;
}

.item-subtitle {
  color: #64748b;
  font-size: 0.85rem;
  margin-top: 5px;
}

.item-link {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #2563eb;
  font-size: 0.82rem;
  margin-top: 5px;
  text-decoration: none;
}

.soft-tag {
  border-radius: 999px;
  font-weight: 800;
}

.date-stack {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #475569;
  font-size: 0.8rem;
}

.date-stack span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.marketing-dialog :deep(.el-dialog) {
  border-radius: 20px;
}

.marketing-dialog :deep(.el-dialog__body) {
  padding-top: 4px;
}

.editor-layout {
  display: grid;
  grid-template-columns: 330px minmax(0, 1fr);
  gap: 24px;
}

.preview-panel {
  position: sticky;
  top: 0;
  align-self: start;
  padding: 18px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
}

.preview-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 14px;
  color: #64748b;
  font-size: 0.78rem;
  font-weight: 900;
  text-transform: uppercase;
}

.preview-frame {
  min-height: 190px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 14px;
  background: #0f172a;
  border: 1px solid #dbeafe;
}

.preview-frame.is-sponsor {
  min-height: 150px;
  background: #ffffff;
}

.preview-frame img {
  width: 100%;
  height: 100%;
  max-height: 240px;
  object-fit: contain;
}

.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #94a3b8;
  font-weight: 800;
}

.preview-empty .el-icon {
  font-size: 2rem;
}

.preview-copy {
  margin-top: 16px;
}

.preview-copy strong {
  display: block;
  color: #0f172a;
  font-size: 1rem;
  font-weight: 900;
  line-height: 1.35;
}

.preview-copy p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 0.88rem;
  line-height: 1.5;
}

.marketing-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-section {
  padding: 18px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: #ffffff;
}

.section-title {
  margin-bottom: 16px;
}

.section-title h3 {
  margin: 0;
  color: #0f172a;
  font-size: 1rem;
  font-weight: 900;
}

.section-title p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 0.83rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.full-input {
  width: 100%;
}

.upload-row {
  width: 100%;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 10px;
}

.switch-row {
  display: flex;
  align-items: center;
  gap: 22px;
  flex-wrap: wrap;
}

@media (max-width: 1100px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .editor-layout {
    grid-template-columns: 1fr;
  }

  .preview-panel {
    position: static;
  }
}

@media (max-width: 768px) {
  .metric-grid,
  .form-grid,
  .upload-row {
    grid-template-columns: 1fr;
  }

  .toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .toolbar-actions,
  .filter-row,
  .filter-row .el-select {
    width: 100%;
  }
}
</style>
