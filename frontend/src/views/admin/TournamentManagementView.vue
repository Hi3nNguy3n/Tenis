<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { tournamentService } from '../../services/tournamentService'
import apiClient from '../../services/apiClient'
import { saveAs } from 'file-saver';
import { getStoredAccessToken } from '../../utils/authStorage';
import { Message, Plus, Search, Refresh, Delete, Edit, Trophy, DataAnalysis, Calendar, User } from '@element-plus/icons-vue'

import { useRouter } from 'vue-router'
const router = useRouter()

const categoryOptions = ['Open', 'Intermediate', 'Advanced', 'Elite']
const formatOptions = ['Singles', 'Doubles']
const drawSizeOptions = [2, 4, 8, 16, 32, 64]
const surfaceOptions = ['Hard', 'Clay', 'Grass', 'Carpet']
const statusOptions = [
  { label: 'Bản nháp', value: 'draft' },
  { label: 'Mở đăng ký', value: 'open' },
  { label: 'Đang diễn ra', value: 'ongoing' },
  { label: 'Đã kết thúc', value: 'finished' },
]

const search = ref('')
const statusFilter = ref('')
const formatFilter = ref('')
const drawSizeFilter = ref('')
const tournaments = ref([])
const isLoading = ref(false)
const isSaving = ref(false)
const isDialogOpen = ref(false)
const isEditMode = ref(false)
const selectedTournament = ref(null)
const errorMessage = ref('')
const isDetailDrawerOpen = ref(false)
const isExporting = ref(false)

const downloadExcelReport = async (tournament) => {
  if (!tournament || !tournament.id) return;
  isExporting.value = true;

  try {
    // 1. Lấy token chuẩn từ tiện ích của dự án
    const token = getStoredAccessToken() || localStorage.getItem('access_token');
    
    // 2. Sử dụng đúng tên biến môi trường (Có fallback về localhost y hệt apiClient.js)
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '';

    // 3. Dùng fetch thuần để giữ nguyên vẹn dữ liệu nhị phân (Blob)
    const response = await fetch(`${baseUrl}/api/tournaments/${tournament.id}/export-excel`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Lỗi server: ${errorText}`);
    }

    // 4. Lấy dữ liệu dưới dạng Blob và lưu
    const blob = await response.blob();
    const safeName = tournament.name
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-zA-Z0-9]/g, '_');

    saveAs(blob, `BaoCao_${safeName}.xlsx`);

    ElMessage.success('Tải báo cáo thành công!');
  } catch (error) {
    console.error("Lỗi xuất Excel:", error);
    ElMessage.error('Không thể xuất báo cáo. Vui lòng kiểm tra lại quyền truy cập.');
  } finally {
    isExporting.value = false;
  }
};

// --- THÊM BIẾN VÀ HÀM GỬI EMAIL ---
const isSendingMail = ref(false)

const sendMassEmail = async (tournament) => {
  if (!tournament || !tournament.id) return;

  try {
    // 1. Xác nhận trước khi gửi để tránh bấm nhầm
    await ElMessageBox.confirm(
      `Hệ thống sẽ gửi email thông báo đến toàn bộ VĐV của giải "${tournament.name}". Bạn có chắc chắn muốn thực hiện?`,
      'Xác nhận gửi thông báo hàng loạt',
      {
        confirmButtonText: 'Xác nhận gửi',
        cancelButtonText: 'Hủy',
        type: 'warning',
      }
    )

    isSendingMail.value = true
    const token = getStoredAccessToken() || localStorage.getItem('access_token')
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''

    // 2. Gọi API POST để kích hoạt gửi mail hàng loạt
    const response = await fetch(`${baseUrl}/api/tournaments/${tournament.id}/send-notifications`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Lỗi khi gửi thông báo')
    }

    // 3. Thông báo cho Admin biết hệ thống đang xử lý ngầm
    ElMessage({
      message: data.message,
      type: 'success',
      duration: 5000,
      showClose: true
    })

  } catch (error) {
    if (error !== 'cancel') {
      console.error("Lỗi gửi mail:", error)
      ElMessage.error(error.message || 'Không thể gửi thông báo lúc này.')
    }
  } finally {
    isSendingMail.value = false
  }
}

// Pagination
const currentPage = ref(1)
const pageSize = ref(100)
const total = ref(0)

const stats = ref({
  total_tournaments: 0,
  active_tournaments: 0,
  pending_approvals: 0,
  total_registrations: 0
})

const goToMailCampaign = (tournamentId) => {
  // Thay 'name' bằng 'path' để tránh lỗi không khớp tên route
  router.push({ 
    path: '/admin/mail-campaign', 
    query: { tournamentId: tournamentId } 
  })
}

const summaryCards = computed(() => [
  { label: 'TỔNG GIẢI ĐẤU', value: stats.value.total_tournaments, tone: 'primary' },
  { label: 'ĐANG DIỄN RA', value: stats.value.active_tournaments, tone: 'success' },
  { label: 'ĐĂNG KÝ MỚI', value: stats.value.pending_approvals, tone: 'warning' },
  { label: 'VĐV ĐĂNG KÝ', value: stats.value.total_registrations, tone: 'accent' },
])

const createDefaultForm = () => ({
  id: null,
  name: '',
  slug: '',
  status: 'draft',
  format_type: 'Singles',
  draw_size: 32,
  category_type: 'Open',
  gender_division: 'Mixed',
  location: '',
  surface_type: 'Hard',
  registration_open_at: '',
  registration_close_at: '',
  start_date: '',
  end_date: '',
  entry_fee: 100,
  entry_fee_team: 200,
})

const form = ref(createDefaultForm())

// --- LOGIC CHẶN NGÀY THÁNG QUÁ KHỨ ---
// 1. Chặn các ngày trước ngày hôm nay
const disabledPastDates = (time) => {
  return time.getTime() < Date.now() - 8.64e7 // Trừ 1 ngày để cho phép chọn hôm nay
}

// 2. Ngày kết thúc Đăng ký phải sau ngày Mở đăng ký
const disabledCloseRegDate = (time) => {
  if (!form.value.registration_open_at) return disabledPastDates(time)
  return time.getTime() < new Date(form.value.registration_open_at).getTime()
}

// 3. Ngày Kết thúc giải đấu phải sau Ngày khai mạc
const disabledEndDate = (time) => {
  if (!form.value.start_date) return disabledPastDates(time)
  return time.getTime() < new Date(form.value.start_date).getTime()
}
// --------------------------------------

const loadStats = async () => {
  try {
    const data = await tournamentService.getStats()
    stats.value = data
  } catch (err) {
    console.error('Lỗi tải thống kê:', err)
  }
}

const loadTournaments = async () => {
  isLoading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      status: statusFilter.value || undefined
    }
    const data = await tournamentService.getAll(params)
    tournaments.value = Array.isArray(data) ? data : (data.items || [])
    total.value = data.total || tournaments.value.length
    if (tournaments.value.length > 0 && !selectedTournament.value) {
      selectedTournament.value = tournaments.value[0]
    }
  } catch (err) {
    errorMessage.value = 'Lỗi tải danh sách: ' + err.message
  } finally {
    isLoading.value = false
  }
}

const resetFilters = () => {
  search.value = ''
  statusFilter.value = ''
  formatFilter.value = ''
  drawSizeFilter.value = ''
  loadTournaments()
}

const handlePageChange = (val) => {
  currentPage.value = val
  loadTournaments()
}

const openCreateDialog = () => {
  isEditMode.value = false
  form.value = createDefaultForm()
  isDialogOpen.value = true
}

const openEditDialog = (row) => {
  isEditMode.value = true
  form.value = { 
    ...row,
    // Format lại ngày giờ cho Component Element Plus
    registration_open_at: row.registration_open_at ? new Date(row.registration_open_at).toISOString().slice(0, 19) : '',
    registration_close_at: row.registration_close_at ? new Date(row.registration_close_at).toISOString().slice(0, 19) : '',
    start_date: row.start_date || '',
    end_date: row.end_date || '',
  }
  isDialogOpen.value = true
}

const closeDialog = () => {
  isDialogOpen.value = false
}

const selectTournament = (row) => {
  selectedTournament.value = row
  isDetailDrawerOpen.value = true
}

const generateSlug = (name) => {
  return name.toLowerCase().trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

const saveTournament = async () => {
  if (!form.value.name) return ElMessage.warning('Vui lòng nhập tên giải')
  
  isSaving.value = true
  try {
    const payload = { ...form.value }
    if (!payload.slug) payload.slug = generateSlug(payload.name)
    
    // Convert empty dates to null for backend
    if (!payload.registration_open_at) delete payload.registration_open_at
    if (!payload.registration_close_at) delete payload.registration_close_at
    if (!payload.end_date) delete payload.end_date

    const finalData = {
      name: payload.name,
      slug: payload.slug,
      category_type: payload.category_type,
      gender_division: payload.gender_division,
      format_type: payload.format_type,
      draw_size: payload.draw_size,
      registration_open_at: payload.registration_open_at || null,
      registration_close_at: payload.registration_close_at || null,
      start_date: payload.start_date,
      end_date: payload.end_date || null,
      status: payload.status,
      location: payload.location,
      surface_type: payload.surface_type,
      entry_fee: payload.entry_fee,
      entry_fee_team: payload.entry_fee_team,
    }

    if (isEditMode.value) {
      await tournamentService.update(form.value.id, finalData)
      ElMessage.success('Cập nhật thành công')
    } else {
      await tournamentService.create(finalData)
      ElMessage.success('Tạo giải thành công')
    }
    isDialogOpen.value = false
    loadTournaments()
    loadStats()
  } catch (err) {
    const detail = err.response?.data?.detail
    const msg = Array.isArray(detail) ? detail.map(d => `${d.loc[d.loc.length-1]}: ${d.msg}`).join(', ') : (detail || err.message)
    ElMessage.error('Lỗi khi lưu: ' + msg)
  } finally {
    isSaving.value = false
  }
}

const deleteTournament = (id) => {
  ElMessageBox.confirm('Bạn có chắc chắn muốn xóa giải đấu này?', 'Cảnh báo', {
    type: 'warning'
  }).then(async () => {
    try {
      await tournamentService.delete(id)
      ElMessage.success('Đã xóa giải đấu')
      loadTournaments()
      loadStats()
    } catch (err) {
      ElMessage.error('Lỗi khi xóa: ' + err.message)
    }
  })
}

const filteredRows = computed(() => {
  let result = [...tournaments.value]

  // 1. Lọc theo tên (Search) - Client-side
  if (search.value) {
    const s = search.value.toLowerCase().trim()
    result = result.filter(t => t.name.toLowerCase().includes(s))
  }

  // 2. Lọc theo Loại hình (Format) - Client-side
  if (formatFilter.value) {
    result = result.filter(t => t.format_type === formatFilter.value)
  }

  // 3. Lọc theo Draw size - Client-side
  if (drawSizeFilter.value) {
    result = result.filter(t => t.draw_size === drawSizeFilter.value)
  }

  return result
})

onMounted(() => {
  loadTournaments()
  loadStats()
})
</script>

<template>
  <div class="module-shell">
    <!-- Redundant header removed - handled by AdminLayout -->

    <section class="admin-action-bar">
      <div class="action-left">
        <el-button type="primary" size="large" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>&nbsp;Tạo giải mới
        </el-button>
        <el-button plain size="large" @click="loadTournaments">Tải lại</el-button>
      </div>
    </section>


    <section class="summary-grid">
      <article class="stat-card-glass p-blue-glass">
        <div class="stat-icon-container">
          <el-icon><Trophy /></el-icon>
        </div>
        <div class="stat-info-v2">
          <span class="stat-kicker">Tổng giải đấu</span>
          <strong class="stat-number">{{ stats.total_tournaments }}</strong>
        </div>
      </article>

      <article class="stat-card-glass p-green-glass">
        <div class="stat-icon-container">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div class="stat-info-v2">
          <span class="stat-kicker">Đang diễn ra</span>
          <strong class="stat-number">{{ stats.active_tournaments }}</strong>
        </div>
      </article>

      <article class="stat-card-glass p-orange-glass">
        <div class="stat-icon-container">
          <el-icon><Calendar /></el-icon>
        </div>
        <div class="stat-info-v2">
          <span class="stat-kicker">Đăng ký mới</span>
          <strong class="stat-number">{{ stats.pending_approvals }}</strong>
        </div>
      </article>

      <article class="stat-card-glass p-purple-glass">
        <div class="stat-icon-container">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-info-v2">
          <span class="stat-kicker">VĐV đăng ký</span>
          <strong class="stat-number">{{ stats.total_registrations }}</strong>
        </div>
      </article>
    </section>

    <!-- Dynamic Filter Options from Data -->
    <section class="filter-card">
      <div class="search-box">
        <el-input 
          v-model="search" 
          placeholder="Tìm theo tên giải..." 
          clearable 
          style="width: 320px"
          :prefix-icon="Search"
        />
      </div>

      <div class="filter-group">
        <!-- Lọc trạng thái (Server-side trigger) -->
        <el-select v-model="statusFilter" placeholder="Trạng thái" clearable @change="loadTournaments" style="width: 140px">
          <el-option 
            v-for="opt in statusOptions" 
            :key="opt.value" 
            :label="opt.label" 
            :value="opt.value" 
          />
        </el-select>

        <!-- Lọc Loại hình (Client-side reactive) -->
        <el-select v-model="formatFilter" placeholder="Loại hình" clearable style="width: 140px">
          <el-option 
            v-for="format in Array.from(new Set(tournaments.map(t => t.format_type)))" 
            :key="format" 
            :label="format" 
            :value="format" 
          />
        </el-select>

        <!-- Lọc Draw size (Client-side reactive) -->
        <el-select v-model="drawSizeFilter" placeholder="Draw size" clearable style="width: 110px">
          <el-option 
            v-for="size in Array.from(new Set(tournaments.map(t => t.draw_size))).sort((a,b) => a-b)" 
            :key="size" 
            :label="`${size}`" 
            :value="size" 
          />
        </el-select>

        <el-button plain @click="resetFilters">
          <el-icon><Refresh /></el-icon>&nbsp;Làm mới bộ lọc
        </el-button>
      </div>
    </section>

    <section class="content-grid">
      <article class="table-card">
        <div class="card-heading">
          <div>
            <h3>Danh sách giải đấu</h3>
            <p>{{ total }} giải đấu được ghi nhận.</p>
          </div>
        </div>

        <el-table :data="filteredRows" stripe v-loading="isLoading" @row-click="selectTournament" highlight-current-row>
          <el-table-column prop="name" label="Tên giải" min-width="200" />
          <el-table-column prop="status" label="Trạng thái" width="120">
            <template #default="{ row }">
              <el-tag :type="row.status === 'open' ? 'success' : 'info'">{{ row.status.toUpperCase() }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="category_type" label="Hạng" width="140" />
          <el-table-column prop="draw_size" label="Draw" width="80" />
          <el-table-column label="Điều khiển" width="120" fixed="right" align="center">
            <template #default="{ row }">
              <div class="table-actions">
                <el-tooltip content="Chỉnh sửa" placement="top">
                  <el-button 
                    circle 
                    size="small" 
                    type="primary" 
                    plain 
                    :icon="Edit" 
                    @click.stop="openEditDialog(row)"
                  />
                </el-tooltip>
                <el-tooltip content="Xóa" placement="top">
                  <el-button 
                    circle 
                    size="small" 
                    type="danger" 
                    plain 
                    :icon="Delete" 
                    @click.stop="deleteTournament(row.id)"
                  />
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container" style="margin-top: 20px; display: flex; justify-content: flex-end;">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>
      </article>
    </section>

    <!-- Drawer cho chi tiết giải đấu -->
    <el-drawer
      v-model="isDetailDrawerOpen"
      title="Hồ sơ Giải đấu"
      size="480px"
      destroy-on-close
    >
      <div v-if="selectedTournament" class="detail-stack">
        <div class="detail-hero">
          <div class="hero-top">
            <div>
              <el-tag :type="selectedTournament.status === 'open' ? 'success' : 'info'" size="small" effect="dark" style="margin-bottom: 8px">
                {{ selectedTournament.status.toUpperCase() }}
              </el-tag>
              <h4 style="margin: 0; font-size: 1.4rem">{{ selectedTournament.name }}</h4>
            </div>
            <el-button type="primary" plain circle :icon="Edit" @click="openEditDialog(selectedTournament)" />
          </div>
          
          <div class="action-buttons-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 20px;">
            <el-button 
              type="primary" 
              @click="goToMailCampaign(selectedTournament.id)" 
              :icon="Message"
              style="width: 100%"
            >
              Gửi thông báo
            </el-button>

            <el-button 
              type="success" 
              :loading="isExporting" 
              @click="downloadExcelReport(selectedTournament)"
              style="width: 100%"
            >
              Xuất Excel
            </el-button>
          </div>
        </div>

        <div class="detail-sections" style="display: grid; gap: 20px; margin-top: 30px;">
          <div class="info-group">
            <h5 style="color: #64748b; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.05em">Thông tin thi đấu</h5>
            <div class="detail-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; background: #f8fafc; padding: 16px; border-radius: 12px;">
              <div class="detail-item">
                <span style="display: block; font-size: 0.75rem; color: #94a3b8">Loại hình</span>
                <strong style="font-size: 0.95rem">{{ selectedTournament.format_type }}</strong>
              </div>
              <div class="detail-item">
                <span style="display: block; font-size: 0.75rem; color: #94a3b8">Hạng đấu</span>
                <strong style="font-size: 0.95rem">{{ selectedTournament.category_type }}</strong>
              </div>
              <div class="detail-item">
                <span style="display: block; font-size: 0.75rem; color: #94a3b8">Draw size</span>
                <strong style="font-size: 0.95rem">{{ selectedTournament.draw_size }}</strong>
              </div>
              <div class="detail-item">
                <span style="display: block; font-size: 0.75rem; color: #94a3b8">Mặt sân</span>
                <strong style="font-size: 0.95rem">{{ selectedTournament.surface_type }}</strong>
              </div>
            </div>
          </div>

          <div class="info-group">
            <h5 style="color: #64748b; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.05em">Chi phí & Địa điểm</h5>
            <div class="detail-grid" style="display: grid; gap: 16px; background: #f8fafc; padding: 16px; border-radius: 12px;">
              <div class="detail-item">
                <span style="display: block; font-size: 0.75rem; color: #94a3b8">Lệ phí cá nhân</span>
                <strong style="font-size: 1.1rem; color: #15803d">{{ new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(selectedTournament.entry_fee || 0) }}</strong>
              </div>
              <div class="detail-item">
                <span style="display: block; font-size: 0.75rem; color: #94a3b8">Địa điểm</span>
                <strong style="font-size: 0.95rem">{{ selectedTournament.location || 'Chưa cập nhật' }}</strong>
              </div>
            </div>
          </div>

          <div class="info-group">
            <h5 style="color: #64748b; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.05em">Thời gian giải đấu</h5>
            <div class="detail-grid" style="display: grid; gap: 16px; background: #f8fafc; padding: 16px; border-radius: 12px;">
              <div class="detail-item">
                <span style="display: block; font-size: 0.75rem; color: #94a3b8">Ngày thi đấu</span>
                <strong style="font-size: 0.95rem">{{ selectedTournament.start_date }}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>

  <el-dialog
    v-model="isDialogOpen"
    :title="isEditMode ? 'Chỉnh sửa giải đấu' : 'Tạo giải đấu mới'"
    width="720px"
    destroy-on-close
  >
    <el-form label-position="top" class="tournament-form">
      <el-form-item label="Tên giải đấu" required>
        <el-input v-model="form.name" placeholder="Ví dụ: Saigon Open 2026" />
      </el-form-item>

      <div class="form-grid two-columns">
        <el-form-item label="Trạng thái">
          <el-select v-model="form.status" style="width: 100%">
            <el-option v-for="option in statusOptions" :key="option.value" :label="option.label" :value="option.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="Loại hình thi đấu">
          <el-select v-model="form.format_type" style="width: 100%">
            <el-option v-for="option in formatOptions" :key="option" :label="option" :value="option" />
          </el-select>
        </el-form-item>
      </div>

      <div class="form-grid three-columns">
        <el-form-item label="Hạng cân">
          <el-select v-model="form.category_type" style="width: 100%">
            <el-option v-for="option in categoryOptions" :key="option" :label="option" :value="option" />
          </el-select>
        </el-form-item>

        <el-form-item label="Phân nhóm phái">
          <el-select v-model="form.gender_division" style="width: 100%">
            <el-option label="Men" value="Men" />
            <el-option label="Women" value="Women" />
            <el-option label="Mixed" value="Mixed" />
          </el-select>
        </el-form-item>

        <el-form-item label="Draw size">
          <el-select v-model="form.draw_size" style="width: 100%">
            <el-option v-for="size in drawSizeOptions" :key="size" :label="`${size}`" :value="size" />
          </el-select>
        </el-form-item>
      </div>

      <div class="form-grid two-columns">
        <el-form-item label="Địa điểm thi đấu">
          <el-input v-model="form.location" placeholder="Nhập địa điểm hoặc cụm sân" />
        </el-form-item>

        <el-form-item label="Mặt sân">
          <el-select v-model="form.surface_type" style="width: 100%">
            <el-option v-for="surface in surfaceOptions" :key="surface" :label="surface" :value="surface" />
          </el-select>
        </el-form-item>
      </div>

      <div class="form-grid two-columns">
        <el-form-item label="Lệ phí cá nhân (VNĐ)">
          <el-input-number v-model="form.entry_fee" :min="0" :step="50000" style="width: 100%" />
        </el-form-item>

        <el-form-item label="Lệ phí đội (VNĐ)">
          <el-input-number v-model="form.entry_fee_team" :min="0" :step="50000" style="width: 100%" />
        </el-form-item>
      </div>

      <div class="form-grid two-columns">
        <el-form-item label="Bắt đầu đăng ký">
          <el-date-picker
            v-model="form.registration_open_at"
            type="datetime"
            placeholder="Chọn ngày và giờ"
            value-format="YYYY-MM-DDTHH:mm:ss"
            :disabled-date="disabledPastDates"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="Kết thúc đăng ký">
          <el-date-picker
            v-model="form.registration_close_at"
            type="datetime"
            placeholder="Chọn ngày và giờ"
            value-format="YYYY-MM-DDTHH:mm:ss"
            :disabled-date="disabledCloseRegDate"
            style="width: 100%"
          />
        </el-form-item>
      </div>

      <div class="form-grid two-columns">
        <el-form-item label="Ngày khai mạc">
          <el-date-picker
            v-model="form.start_date"
            type="date"
            placeholder="Chọn ngày bắt đầu"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledPastDates"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="Ngày kết thúc">
          <el-date-picker
            v-model="form.end_date"
            type="date"
            placeholder="Chọn ngày kết thúc"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledEndDate"
            style="width: 100%"
          />
        </el-form-item>
      </div>
    </el-form>

    <template #footer>
      <el-button @click="closeDialog">Hủy</el-button>
      <el-button type="primary" :loading="isSaving" @click="saveTournament">
        {{ isEditMode ? 'Lưu cập nhật' : 'Tạo giải đấu' }}
      </el-button>
    </template>
  </el-dialog>

</template>

<style scoped>
.module-shell { display: grid; gap: 24px; }

@media (max-width: 960px) {
  .module-shell {
    gap: 16px;
  }

  .summary-grid {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px;
  }

  .filter-card {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    flex-wrap: wrap;
  }

  .content-grid,
  .detail-grid,
  .two-columns,
  .three-columns {
    grid-template-columns: 1fr;
  }

  .table-card {
    padding: 16px;
  }
}

@media (max-width: 640px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .admin-action-bar,
  .action-left,
  .filter-group {
    width: 100%;
  }

  .admin-action-bar {
    flex-direction: column;
    gap: 12px;
  }

  .action-left,
  .filter-group {
    flex-wrap: wrap;
  }

  .filter-card,
  .table-card {
    padding: 12px;
    border-radius: 16px;
  }

  :deep(.el-dialog) {
    width: calc(100vw - 24px) !important;
    max-width: calc(100vw - 24px);
  }
}

.admin-action-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: -8px; }

/* Thẻ thống kê Glassmorphism */
.summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; }

.stat-card-glass {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  padding: 24px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  position: relative;
  overflow: hidden;
}

.stat-card-glass:hover {
  transform: translateY(-8px) scale(1.02);
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 15px 45px rgba(0,0,0,0.1);
}

.stat-icon-container {
  width: 60px;
  height: 60px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  transition: all 0.4s ease;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.4);
}

.stat-card-glass:hover .stat-icon-container {
  transform: rotate(10deg);
}

/* Colors with Gradients */
.p-blue-glass .stat-icon-container { background: linear-gradient(135deg, #60a5fa, #3b82f6); color: white; }
.p-green-glass .stat-icon-container { background: linear-gradient(135deg, #34d399, #10b981); color: white; }
.p-orange-glass .stat-icon-container { background: linear-gradient(135deg, #fb923c, #f59e0b); color: white; }
.p-purple-glass .stat-icon-container { background: linear-gradient(135deg, #a78bfa, #8b5cf6); color: white; }

.stat-info-v2 { display: flex; flex-direction: column; gap: 2px; }
.stat-kicker { font-size: 0.7rem; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; }
.stat-number { font-size: 2.2rem; font-weight: 900; color: #0f172a; line-height: 1; letter-spacing: -0.02em; }

/* Filters */
.filter-card { 
  display: flex; justify-content: space-between; gap: 12px; padding: 16px 24px; 
  background: white; border-radius: 20px; border: 1px solid #f1f5f9;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
}
.filter-group { display: flex; gap: 12px; }

.content-grid { display: grid; grid-template-columns: 1fr; gap: 24px; margin-top: 8px; }

.table-card { 
  background: white; padding: 24px; border-radius: 16px; border: 1px solid #f0f2f2;
}

.card-heading { margin-bottom: 20px; }
.card-heading h3 { font-size: 1.1rem; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.card-heading p { font-size: 0.85rem; color: #64748b; margin: 0; }

.detail-stack { display: grid; gap: 20px; }
.detail-hero { 
  padding: 20px; border-radius: 16px; background: #f8fafc; 
  border: 1px solid #f1f5f9; display: flex; flex-direction: column; gap: 16px; 
}
.hero-top { display: flex; justify-content: space-between; align-items: flex-start; }
.detail-eyebrow { font-size: 0.65rem; font-weight: 800; color: #10b981; text-transform: uppercase; background: #ecfdf5; padding: 4px 10px; border-radius: 99px; }
.detail-hero h4 { margin: 8px 0 0; font-size: 1.3rem; color: #1e293b; }

.table-actions { display: flex; gap: 10px; justify-content: center; }

.action-buttons { display: flex; flex-wrap: wrap; gap: 8px; }

.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.detail-item { display: flex; flex-direction: column; gap: 4px; }
.detail-item span { font-size: 0.7rem; font-weight: 700; color: #64748b; text-transform: uppercase; }
.detail-item strong { color: #1e293b; font-size: 0.95rem; }

.form-grid { display: grid; gap: 16px; }
.two-columns { grid-template-columns: 1fr 1fr; }
.three-columns { grid-template-columns: 1fr 1fr 1fr; }

:deep(.el-table) { border-radius: 12px; overflow: hidden; }
</style>
