<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { tournamentService } from '../../services/tournamentService'

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

// Pagination
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const stats = ref({
  total_tournaments: 0,
  active_tournaments: 0,
  pending_approvals: 0,
  total_registrations: 0
})

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

const filteredRows = computed(() => tournaments.value)

onMounted(() => {
  loadTournaments()
  loadStats()
})
</script>

<template>
  <div class="module-shell">
    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
      @close="errorMessage = ''"
    />

    <section class="hero-card">
      <div>
        <span class="section-kicker">Tournament operations</span>
        <h2>Quản lý giải đấu</h2>
        <p>
          Danh sách giải đấu, bộ lọc, tạo mới và chỉnh sửa thông tin giải. Dữ liệu được đồng bộ trực tiếp từ hệ thống.
        </p>
      </div>

      <div class="hero-actions">
        <el-button type="primary" size="large" @click="openCreateDialog">Tạo giải mới</el-button>
        <el-button plain size="large" @click="loadTournaments">Tải lại</el-button>
      </div>
    </section>

    <section class="summary-grid">
      <article v-for="card in summaryCards" :key="card.label" class="summary-card" :data-tone="card.tone">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
      </article>
    </section>

    <section class="filter-card">
      <el-input v-model="search" placeholder="Tìm theo tên giải..." clearable @change="loadTournaments" />
      <el-select v-model="statusFilter" placeholder="Trạng thái" clearable @change="loadTournaments">
        <el-option v-for="option in statusOptions" :key="option.value" :label="option.label" :value="option.value" />
      </el-select>
      <el-select v-model="formatFilter" placeholder="Loại hình" clearable>
        <el-option v-for="option in formatOptions" :key="option" :label="option" :value="option" />
      </el-select>
      <el-select v-model="drawSizeFilter" placeholder="Draw size" clearable>
        <el-option v-for="size in drawSizeOptions" :key="size" :label="`${size}`" :value="size" />
      </el-select>
      <el-button plain @click="resetFilters">Reset filter</el-button>
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
          <el-table-column prop="category_type" label="Hạng" width="100" />
          <el-table-column prop="draw_size" label="Draw" width="80" />
          <el-table-column label="Actions" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" plain @click.stop="openEditDialog(row)">
                Sửa
              </el-button>
              <el-button size="small" type="danger" plain @click.stop="deleteTournament(row.id)">
                Xóa
              </el-button>
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

      <aside class="detail-card">
        <div class="card-heading">
          <div>
            <h3>Chi tiết giải đấu</h3>
            <p>Chọn một giải đấu trong bảng để xem nhanh cấu hình.</p>
          </div>
        </div>

        <div v-if="selectedTournament" class="detail-stack">
          <div class="detail-hero">
            <div>
              <span class="detail-eyebrow">{{ selectedTournament.status }}</span>
              <h4>{{ selectedTournament.name }}</h4>
            </div>
            <el-button type="primary" plain @click="openEditDialog(selectedTournament)">Chỉnh sửa</el-button>
          </div>

          <div class="detail-grid">
            <div>
              <span>Loại hình</span>
              <strong>{{ selectedTournament.format_type }}</strong>
            </div>
            <div>
              <span>Hạng đấu</span>
              <strong>{{ selectedTournament.category_type }}</strong>
            </div>
            <div>
              <span>Draw size</span>
              <strong>{{ selectedTournament.draw_size }}</strong>
            </div>
            <div>
              <span>Mặt sân</span>
              <strong>{{ selectedTournament.surface_type }}</strong>
            </div>
            <div>
              <span>Lệ phí cá nhân</span>
              <strong>{{ new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(selectedTournament.entry_fee || 0) }}</strong>
            </div>
            <div>
              <span>Ngày thi đấu</span>
              <strong>{{ selectedTournament.start_date }}</strong>
            </div>
            <div style="grid-column: span 2">
              <span>Địa điểm</span>
              <strong>{{ selectedTournament.location || 'Chưa cập nhật' }}</strong>
            </div>
          </div>
        </div>

        <el-empty v-else description="Chưa chọn giải" />
      </aside>
    </section>
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
.module-shell { display: grid; gap: 18px; }
.hero-card, .summary-card, .filter-card, .table-card, .detail-card {
  border-radius: 28px; background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 18px 40px rgba(18, 30, 27, 0.07);
}
.hero-card { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; padding: 28px; }
.section-kicker { display: inline-flex; margin-bottom: 12px; padding: 8px 12px; border-radius: 999px; background: rgba(20, 98, 80, 0.08); color: #0f5c4d; font-size: 0.74rem; font-weight: 800; letter-spacing: 0.16em; text-transform: uppercase; }
.hero-card h2 { margin-bottom: 10px; font-size: 2.5rem; color: #132722; }
.hero-card p { max-width: 760px; color: #59706a; }
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.summary-card { padding: 20px; display: grid; gap: 8px; }
.summary-card span { color: #647873; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.1em; }
.summary-card strong { font-size: 1.8rem; color: #152a24; }
.filter-card { display: flex; gap: 12px; padding: 18px; align-items: center; }
.content-grid { display: grid; grid-template-columns: 1.6fr 0.9fr; gap: 18px; }
.table-card, .detail-card { padding: 20px; }
.detail-stack { display: grid; gap: 18px; }
.detail-hero { display: flex; align-items: center; justify-content: space-between; padding: 18px; border-radius: 20px; background: #f0f7f5; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.detail-grid span { font-size: 0.7rem; font-weight: 800; color: #71837d; text-transform: uppercase; }
.detail-grid strong { display: block; color: #152a24; }
.form-grid { display: grid; gap: 15px; }
.two-columns { grid-template-columns: 1fr 1fr; }
.three-columns { grid-template-columns: 1fr 1fr 1fr; }
</style>