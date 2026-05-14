<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { tournamentService } from '../../services/tournamentService'
import apiClient from '../../services/apiClient'
import { saveAs } from 'file-saver';
import { getStoredAccessToken } from '../../utils/authStorage';
import { 
  Message, Plus, Search, Refresh, Delete, 
  Edit, Trophy, DataAnalysis, Calendar as CalendarIcon, 
  User, Filter, EditPen, View, Download,
  Share, Location as LocationIcon
} from '@element-plus/icons-vue'
import { t, currentLocale } from '../../utils/locale'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const categoryOptions = ['Open', 'Intermediate', 'Advanced', 'Elite']
const formatOptions = ['Singles', 'Doubles']
const drawSizeOptions = [2, 4, 8, 16, 32, 64]
const surfaceOptions = ['Hard', 'Clay', 'Grass', 'Carpet']
const statusOptions = computed(() => [
  { label: t('admin.draft'), value: 'draft' },
  { label: t('admin.openReg'), value: 'open' },
  { label: t('admin.ongoing'), value: 'ongoing' },
  { label: t('admin.finished'), value: 'finished' },
])

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
const isDetailDrawerOpen = ref(false)
const isExporting = ref(false)
const isSendingMail = ref(false)

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

const formatCurrency = (value) => {
  const locale = currentLocale.value === 'vi' ? 'vi-VN' : 'en-US'
  const currency = currentLocale.value === 'vi' ? 'VND' : 'USD'
  return new Intl.NumberFormat(locale, { style: 'currency', currency }).format(value)
}

const loadStats = async () => {
  try {
    const data = await tournamentService.getStats()
    stats.value = data
  } catch (err) {
    console.error('Stats Load Error:', err)
  }
}

const loadTournaments = async () => {
  isLoading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      search: search.value.trim() || undefined,
      status: statusFilter.value || undefined,
      format: formatFilter.value || undefined,
      draw_size: drawSizeFilter.value || undefined
    }
    const data = await tournamentService.getAll(params)
    tournaments.value = Array.isArray(data) ? data : (data.items || [])
    total.value = data.total || tournaments.value.length
  } catch (err) {
    ElMessage.error(t('admin.loadTournamentsError') + ': ' + err.message)
  } finally {
    isLoading.value = false
  }
}

// Debounced Watcher for all filters
let filterTimeout = null
watch([search, statusFilter, formatFilter, drawSizeFilter], () => {
  if (filterTimeout) clearTimeout(filterTimeout)
  filterTimeout = setTimeout(() => {
    loadTournaments()
  }, 300)
})

// Force refresh when navigating back
watch(() => route.path, (newPath) => {
  if (newPath === '/admin/tournaments') {
    loadTournaments()
    loadStats()
  }
})

const resetFilters = () => {
  search.value = ''
  statusFilter.value = ''
  formatFilter.value = ''
  drawSizeFilter.value = ''
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
    registration_open_at: row.registration_open_at ? new Date(row.registration_open_at).toISOString().slice(0, 19) : '',
    registration_close_at: row.registration_close_at ? new Date(row.registration_close_at).toISOString().slice(0, 19) : '',
    start_date: row.start_date || '',
    end_date: row.end_date || '',
  }
  isDialogOpen.value = true
}

const selectTournament = (row) => {
  selectedTournament.value = row
  isDetailDrawerOpen.value = true
}

const validateTournamentForm = () => {
  const f = form.value
  
  if (!f.name) return t('admin.tournamentNameLabel')
  if (!f.location) return t('admin.location')
  if (!f.draw_size) return t('admin.drawSize')

  const regOpen = f.registration_open_at ? new Date(f.registration_open_at) : null
  const regClose = f.registration_close_at ? new Date(f.registration_close_at) : null
  const startDate = f.start_date ? new Date(f.start_date + 'T00:00:00') : null
  const endDate = f.end_date ? new Date(f.end_date + 'T23:59:59') : null

  if (regOpen && regClose && regClose <= regOpen) {
    return "Hạn chót đăng ký phải sau thời gian bắt đầu đăng ký"
  }
  
  if (startDate && endDate && endDate < startDate) {
    return "Ngày kết thúc giải phải sau hoặc bằng ngày khai mạc"
  }
  
  if (regClose && startDate && startDate < regClose) {
    return "Ngày khai mạc giải không được trước hạn chót đăng ký"
  }

  return null
}

const saveTournament = async () => {
  const errorMsg = validateTournamentForm()
  if (errorMsg) return ElMessage.warning(errorMsg)
  isSaving.value = true
  try {
    const payload = { ...form.value }
    const finalData = {
      name: payload.name,
      slug: payload.slug || payload.name.toLowerCase().replace(/ /g, '-'),
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
      ElMessage.success(t('admin.updateSuccess'))
    } else {
      await tournamentService.create(finalData)
      ElMessage.success(t('admin.createSuccess'))
    }
    isDialogOpen.value = false
    loadTournaments()
    loadStats()
  } catch (err) {
    ElMessage.error(t('admin.updateError') + ': ' + err.message)
  } finally {
    isSaving.value = false
  }
}

const deleteTournament = (id) => {
  ElMessageBox.confirm(t('admin.confirmDeleteTournament'), t('admin.action'), {
    type: 'warning', confirmButtonText: t('admin.confirm'), cancelButtonText: t('admin.cancel'),
  }).then(async () => {
    try {
      await tournamentService.delete(id)
      ElMessage.success(t('admin.deleteSuccess'))
      loadTournaments()
      loadStats()
    } catch (err) {
      ElMessage.error(t('admin.updateError') + ': ' + err.message)
    }
  })
}

const downloadExcelReport = async (tournament) => {
  isExporting.value = true;
  try {
    const token = getStoredAccessToken();
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
    const response = await fetch(`${baseUrl}/api/tournaments/${tournament.id}/export-excel`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Export failed');
    const blob = await response.blob();
    saveAs(blob, `Report_${tournament.name.replace(/ /g, '_')}.xlsx`);
    ElMessage.success(t('admin.exportSuccess'));
  } catch (err) {
    ElMessage.error(t('admin.exportError'));
  } finally {
    isExporting.value = false;
  }
};

const goToMailCampaign = (tournamentId) => {
  router.push({ path: '/admin/mail-campaign', query: { tournamentId } })
}

const createDefaultForm = () => ({
  id: null, name: '', slug: '', status: 'draft', format_type: 'Singles',
  draw_size: 32, category_type: 'Open', gender_division: 'Mixed',
  location: '', surface_type: 'Hard', registration_open_at: '',
  registration_close_at: '', start_date: '', end_date: '',
  entry_fee: 100, entry_fee_team: 200,
})
const form = ref(createDefaultForm())

onMounted(() => {
  loadTournaments()
  loadStats()
})
</script>

<template>
  <div class="saas-container">
    <!-- Stats Section -->
    <div class="saas-stats-grid">
      <div class="saas-stat-card">
        <div class="stat-icon p-blue"><el-icon><Trophy /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.totalTournaments') }}</span>
          <h3 class="stat-value">{{ stats.total_tournaments }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-green"><el-icon><DataAnalysis /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.ongoing') }}</span>
          <h3 class="stat-value">{{ stats.active_tournaments }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-orange"><el-icon><CalendarIcon /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.newRegistration') }}</span>
          <h3 class="stat-value">{{ stats.pending_approvals }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-purple"><el-icon><User /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.totalRegistrations') }}</span>
          <h3 class="stat-value">{{ stats.total_registrations }}</h3>
        </div>
      </div>
    </div>

    <!-- Action Bar & Filters -->
    <div class="saas-header">
      <div class="header-left">
        <el-input v-model="search" :placeholder="$t('admin.searchTournamentPlaceholder')" clearable class="saas-search">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        
        <el-select v-model="statusFilter" :placeholder="$t('admin.status')" clearable class="saas-filter">
          <template #prefix><el-icon><Filter /></el-icon></template>
          <el-option v-for="opt in statusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>

        <el-select v-model="formatFilter" :placeholder="$t('admin.tournamentFormat')" clearable class="saas-filter">
          <el-option v-for="f in ['Singles', 'Doubles']" :key="f" :label="f" :value="f" />
        </el-select>

        <el-button plain @click="resetFilters" class="saas-btn-reset">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>

      <div class="header-right">
        <el-button type="primary" @click="openCreateDialog" class="saas-btn-create">
          <el-icon><Plus /></el-icon> {{ $t('admin.createNewTournament') }}
        </el-button>
      </div>
    </div>

    <!-- Data Table -->
    <div class="saas-content">
      <el-table 
        :data="tournaments" 
        v-loading="isLoading" 
        class="saas-table"
        @row-click="selectTournament"
        :header-cell-style="{ background: 'transparent', color: '#1e293b', fontWeight: '800', borderBottom: '2px solid #e2e8f0' }"
        :cell-style="{ background: 'transparent' }"
      >
        <el-table-column :label="$t('admin.tournamentName')" min-width="250">
          <template #default="{ row }">
            <div class="saas-tournament-cell">
              <div class="tournament-icon"><el-icon><Trophy /></el-icon></div>
              <div class="tournament-info">
                <span class="tournament-name">{{ row.name }}</span>
                <span class="tournament-meta">{{ row.location || 'N/A' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.status')" width="140">
          <template #default="{ row }">
            <div class="status-indicator" :class="`is-${row.status}`">
              <span class="dot"></span>
              <span>{{ row.status.toUpperCase() }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="category_type" :label="$t('admin.category')" width="140" />
        
        <el-table-column :label="$t('admin.drawSize')" width="100" align="center">
          <template #default="{ row }">
            <span class="elo-badge">{{ row.draw_size }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="start_date" :label="$t('admin.startDate')" width="140" />

        <el-table-column :label="$t('admin.action')" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <div class="saas-row-actions" @click.stop>
              <el-tooltip :content="$t('admin.edit')">
                <el-button size="small" circle @click="openEditDialog(row)" class="saas-icon-btn"><el-icon><EditPen /></el-icon></el-button>
              </el-tooltip>
              <el-tooltip :content="$t('admin.delete')">
                <el-button size="small" circle type="danger" plain @click="deleteTournament(row.id)" class="saas-icon-btn is-delete"><el-icon><Delete /></el-icon></el-button>
              </el-tooltip>
              <el-tooltip :content="$t('admin.details')">
                <el-button size="small" circle @click="selectTournament(row)" class="saas-icon-btn is-view"><el-icon><View /></el-icon></el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="saas-pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- Drawer: Tournament Details -->
    <el-drawer
      v-model="isDetailDrawerOpen"
      :title="$t('admin.tournamentProfile')"
      size="500px"
      class="saas-drawer"
    >
      <div v-if="selectedTournament" class="saas-drawer-content">
        <div class="drawer-hero">
          <div class="hero-icon"><el-icon><Trophy /></el-icon></div>
          <div class="hero-text">
            <h2>{{ selectedTournament.name }}</h2>
            <div class="hero-badges">
              <el-tag :type="selectedTournament.status === 'open' ? 'success' : 'info'" effect="dark">{{ selectedTournament.status.toUpperCase() }}</el-tag>
              <el-tag type="warning" effect="light">{{ selectedTournament.category_type }}</el-tag>
            </div>
          </div>
        </div>

        <div class="drawer-actions-grid">
          <el-button type="primary" @click="goToMailCampaign(selectedTournament.id)" :icon="Message" class="saas-action-btn">
            {{ $t('admin.sendNotification') }}
          </el-button>
          <el-button type="success" plain :loading="isExporting" @click="downloadExcelReport(selectedTournament)" :icon="Download" class="saas-action-btn">
            {{ $t('admin.exportExcel') }}
          </el-button>
        </div>

        <div class="drawer-info-sections">
          <div class="info-section">
            <h4>{{ $t('admin.competitionInfo') }}</h4>
            <div class="info-grid">
              <div class="info-item"><span>{{ $t('admin.tournamentFormat') }}</span><strong>{{ selectedTournament.format_type }}</strong></div>
              <div class="info-item"><span>{{ $t('admin.drawSize') }}</span><strong>{{ selectedTournament.draw_size }}</strong></div>
              <div class="info-item"><span>{{ $t('admin.surface') }}</span><strong>{{ selectedTournament.surface_type }}</strong></div>
              <div class="info-item"><span>{{ $t('admin.location') }}</span><strong>{{ selectedTournament.location || 'N/A' }}</strong></div>
            </div>
          </div>

          <div class="info-section">
            <h4>{{ $t('admin.financialTime') }}</h4>
            <div class="info-grid">
              <div class="info-item"><span>{{ $t('admin.entryFeePerPerson') }}</span><strong class="text-green">{{ formatCurrency(selectedTournament.entry_fee || 0) }}</strong></div>
              <div class="info-item"><span>{{ $t('admin.startDate') }}</span><strong>{{ selectedTournament.start_date }}</strong></div>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- Dialog: Create/Edit -->
    <el-dialog
      v-model="isDialogOpen"
      :title="isEditMode ? $t('admin.editTournament') : $t('admin.createNewTournament')"
      width="800px"
      class="saas-dialog"
      top="5vh"
    >
      <el-form label-position="top" class="saas-form">
        <!-- Section: General Info -->
        <div class="form-section">
          <div class="section-header">
            <el-icon><Trophy /></el-icon>
            <span>{{ $t('admin.competitionInfo') }}</span>
          </div>
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item :label="$t('admin.tournamentNameLabel')" required>
                <el-input v-model="form.name" placeholder="Ví dụ: Saigon Open 2026 - Series A" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('admin.status')">
                <el-select v-model="form.status" style="width: 100%">
                  <el-option v-for="opt in statusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('admin.tournamentFormat')">
                <el-select v-model="form.format_type" style="width: 100%">
                  <el-option label="Singles" value="Singles" />
                  <el-option label="Doubles" value="Doubles" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- Section: Competition Config -->
        <div class="form-section">
          <div class="section-header">
            <el-icon><EditPen /></el-icon>
            <span>{{ $t('admin.tournamentFormat') }}</span>
          </div>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item :label="$t('admin.category')">
                <el-select v-model="form.category_type" style="width: 100%">
                  <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item :label="$t('admin.genderDivision')">
                <el-select v-model="form.gender_division" style="width: 100%">
                  <el-option label="Men" value="Men" />
                  <el-option label="Women" value="Women" />
                  <el-option label="Mixed" value="Mixed" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item :label="$t('admin.drawSize')" required>
                <el-select v-model="form.draw_size" style="width: 100%">
                  <el-option v-for="s in drawSizeOptions" :key="s" :label="s" :value="s" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- Section: Location & Fees -->
        <div class="form-section">
          <div class="section-header">
            <el-icon><LocationIcon /></el-icon>
            <span>{{ $t('admin.location') }} & {{ $t('admin.entryFeePerPerson') }}</span>
          </div>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="$t('admin.location')" required>
                <el-input v-model="form.location" placeholder="Tên cụm sân thi đấu..." />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('admin.surface')">
                <el-select v-model="form.surface_type" style="width: 100%">
                  <el-option v-for="s in surfaceOptions" :key="s" :label="s" :value="s" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('admin.entryFeePerPerson')">
                <el-input-number v-model="form.entry_fee" :min="0" :step="50000" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('admin.entryFeeTeam')">
                <el-input-number v-model="form.entry_fee_team" :min="0" :step="50000" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- Section: Registration & Schedule -->
        <div class="form-section">
          <div class="section-header">
            <el-icon><CalendarIcon /></el-icon>
            <span>{{ $t('admin.competitionTime') }} & {{ $t('admin.regStart') }}</span>
          </div>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="$t('admin.regStart')">
                <el-date-picker v-model="form.registration_open_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('admin.regEnd')">
                <el-date-picker v-model="form.registration_close_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('admin.startDate')">
                <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('admin.endDate')">
                <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </el-form>
      <template #footer>
        <div class="saas-dialog-footer">
          <el-button @click="isDialogOpen = false" class="saas-btn-secondary">{{ $t('admin.cancel') }}</el-button>
          <el-button type="primary" :loading="isSaving" @click="saveTournament" class="saas-btn-primary">
            {{ isEditMode ? $t('admin.save') : $t('admin.confirm') }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.saas-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
  min-height: 100%;
}

/* Stats Grid */
.saas-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

.saas-stat-card {
  background: #fff;
  border: 1px solid #f1f5f9;
  border-radius: 20px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
}

.saas-stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.05);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.p-blue { background: #eff6ff; color: #3b82f6; }
.p-green { background: #ecfdf5; color: #10b981; }
.p-orange { background: #fff7ed; color: #f97316; }
.p-purple { background: #faf5ff; color: #a855f7; }

.stat-label { font-size: 0.85rem; color: #334155; font-weight: 600; }
.stat-value { margin: 4px 0 0; font-size: 1.8rem; font-weight: 800; color: #0f172a; }

/* Header & Filters */
.saas-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.saas-search { width: 320px; }
.saas-filter { width: 160px; }

:deep(.el-input__wrapper), :deep(.el-select__wrapper) {
  background-color: #f8fafc !important;
  box-shadow: none !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 12px !important;
  padding: 8px 12px !important;
}

.saas-btn-create {
  background-color: #059669 !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 22px 28px !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2) !important;
}

.saas-btn-reset {
  border-radius: 12px !important;
  padding: 20px !important;
  background: #f8fafc !important;
  border-color: #e2e8f0 !important;
}

/* Table */
.saas-content { flex: 1; display: flex; flex-direction: column; gap: 24px; }

.saas-table {
  background: transparent !important;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: transparent;
}

.saas-tournament-cell {
  display: flex;
  align-items: center;
  gap: 16px;
}

.tournament-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 18px;
}

.tournament-name { display: block; font-weight: 800; color: #0f172a; font-size: 0.95rem; }
.tournament-meta { display: block; font-size: 0.8rem; color: #475569; font-weight: 500; }

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 4px 12px;
  background: #f1f5f9;
  border-radius: 20px;
  width: fit-content;
}

.status-indicator.is-open { color: #10b981; background: #ecfdf5; }
.status-indicator.is-ongoing { color: #3b82f6; background: #eff6ff; }
.status-indicator.is-finished { color: #334155; background: #f1f5f9; }
.status-indicator.is-draft { color: #f59e0b; background: #fffbeb; }

.status-indicator .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.elo-badge {
  font-weight: 800;
  color: #334155;
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
}

.saas-row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.saas-icon-btn {
  border: 1px solid #e2e8f0 !important;
  background: #fff !important;
  color: #64748b !important;
  transition: all 0.2s !important;
}

.saas-icon-btn:hover {
  background: #059669 !important;
  color: #fff !important;
  border-color: #059669 !important;
}

.saas-icon-btn.is-delete:hover { background: #ef4444 !important; border-color: #ef4444 !important; }
.saas-icon-btn.is-view:hover { background: #3b82f6 !important; border-color: #3b82f6 !important; }

/* Drawer */
.saas-drawer-content { display: flex; flex-direction: column; gap: 32px; padding: 0 8px; }

.drawer-hero {
  background: #f8fafc;
  padding: 32px;
  border-radius: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 16px;
}

.hero-icon { font-size: 48px; color: #f59e0b; }
.hero-text h2 { margin: 0; font-size: 1.5rem; color: #1e293b; letter-spacing: -0.02em; }
.hero-badges { display: flex; gap: 8px; margin-top: 12px; justify-content: center; }

.drawer-actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.saas-action-btn {
  height: 48px !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
}

.drawer-info-sections { display: flex; flex-direction: column; gap: 24px; }
.info-section h4 { font-size: 0.75rem; text-transform: uppercase; color: #475569; letter-spacing: 0.1em; margin-bottom: 16px; font-weight: 800; }
.info-grid { background: #f8fafc; border-radius: 20px; padding: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; border: 1px solid #f1f5f9; }
.info-item span { display: block; font-size: 0.75rem; color: #475569; margin-bottom: 4px; font-weight: 600; }
.info-item strong { font-size: 1rem; color: #0f172a; }
.text-green { color: #059669 !important; }

/* Dialog & Form Redesign */
.saas-dialog { 
  border-radius: 24px !important; 
  overflow: hidden; 
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;
}

.saas-form {
  padding: 8px 4px;
}

.form-section {
  margin-bottom: 32px;
  background: #f8fafc;
  padding: 24px;
  border-radius: 20px;
  border: 1px solid #f1f5f9;
}

.form-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  color: #064e3b;
}

.section-header .el-icon {
  font-size: 20px;
  color: #059669;
}

.section-header span {
  font-weight: 800;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.saas-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px 24px;
}

.saas-btn-primary { 
  background: #059669 !important; 
  border: none !important;
  border-radius: 14px !important; 
  padding: 24px 32px !important; 
  font-weight: 700 !important;
  box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2) !important;
}

.saas-btn-secondary { 
  border-radius: 14px !important; 
  padding: 24px 32px !important; 
  font-weight: 700 !important;
  background: #fff !important;
  border: 1px solid #e2e8f0 !important;
  color: #64748b !important;
}

:deep(.el-dialog__header) {
  padding: 24px 32px 12px !important;
  margin-right: 0 !important;
}

:deep(.el-dialog__title) { 
  font-weight: 800 !important; 
  font-size: 1.5rem !important; 
  color: #1e293b !important; 
  letter-spacing: -0.02em !important;
}

:deep(.el-form-item__label) { 
  font-weight: 800 !important; 
  color: #0f172a !important; 
  margin-bottom: 8px !important;
  font-size: 0.85rem !important;
}

:deep(.el-input-number .el-input__wrapper) {
  padding-left: 12px !important;
  padding-right: 12px !important;
}

.saas-pagination { display: flex; justify-content: flex-end; margin-top: 16px; }

@media (max-width: 768px) {
  .saas-stats-grid { grid-template-columns: 1fr 1fr; }
  .saas-search { width: 100%; }
}
</style>
