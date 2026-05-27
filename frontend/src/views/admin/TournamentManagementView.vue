<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { tournamentService } from '../../services/tournamentService'
import apiClient from '../../services/apiClient'
import { getApiBaseUrl } from '../../utils/apiUrls'
import { saveAs } from 'file-saver';
import { getStoredAccessToken } from '../../utils/authStorage';
import { 
  Message, Plus, Search, Refresh, Delete, 
  Edit, Trophy, DataAnalysis, Calendar as CalendarIcon, 
  User, Filter, EditPen, View, Download,
  Share, Location as LocationIcon, List, Picture
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

const hasHtmlContent = (value) => /<\/?[a-z][\s\S]*>/i.test(value || '')

const normalizeTournamentDescription = (value) => {
  if (!value) return ''
  const trimmed = value.trim()
  if (!trimmed) return ''
  if (hasHtmlContent(trimmed)) return trimmed
  return trimmed.replace(/\r\n/g, '\n').replace(/\n/g, '<br>')
}

const renderTournamentDescription = (value) => {
  if (!value) return ''
  if (hasHtmlContent(value)) return value
  return value.replace(/\r\n/g, '\n').replace(/\n/g, '<br>')
}

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
const isAddPlayerDialogOpen = ref(false)
const isAddingPlayer = ref(false)
const playerSearchLoading = ref(false)
const partnerSearchLoading = ref(false)
const adminRegistrationTournament = ref(null)
const selectedPlayer = ref(null)
const selectedPartner = ref(null)
const adminPlayerSearchText = ref('')
const adminPartnerSearchText = ref('')
const adminRegistrationForm = ref({
  category_id: null,
  player_id: null,
  partner_player_id: null,
  notes: '',
  mark_paid: false,
  check_in: false
})

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
  deletedCategoryIds.value = []
  
  // Sanitize categories on load
  const sanitizedCategories = (row.categories || []).map(cat => {
    const mapping = {
      'mens_singles': 'Đơn Nam',
      'mens_doubles': 'Đôi Nam',
      'mixed_doubles': 'Đôi Nam Nữ',
      'womens_doubles': 'Đôi Nữ'
    }
    // If name is empty or looks like a slug, fix it
    if (!cat.name || cat.name.includes('_doubles') || cat.name.includes('_singles')) {
      cat.name = mapping[cat.category_type] || cat.name || 'Nội dung mới'
    }
    return cat
  })

  form.value = { 
    ...row,
    registration_open_at: row.registration_open_at ? new Date(row.registration_open_at).toISOString().slice(0, 19) : '',
    registration_close_at: row.registration_close_at ? new Date(row.registration_close_at).toISOString().slice(0, 19) : '',
    start_date: row.start_date || '',
    end_date: row.end_date || '',
    description: row.description || '',
    banner_url: row.banner_url || '',
    categories: sanitizedCategories
  }
  isDialogOpen.value = true
}

const selectTournament = (row) => {
  selectedTournament.value = row
  isDetailDrawerOpen.value = true
}

const adminSelectedCategory = computed(() => {
  if (!adminRegistrationTournament.value?.categories || !adminRegistrationForm.value.category_id) return null
  return adminRegistrationTournament.value.categories.find(c => c.id === adminRegistrationForm.value.category_id) || null
})

const adminRegistrationIsDoubles = computed(() => {
  return adminSelectedCategory.value?.category_type?.includes('doubles')
})

const formatPlayerOption = (player) => {
  const meta = [player.phone, player.level].filter(Boolean).join(' · ')
  return meta ? `${player.full_name} - ${meta}` : player.full_name
}

const querySearchPlayers = async (queryString, cb) => {
  if (!queryString || queryString.length < 2) return cb([])
  playerSearchLoading.value = true
  try {
    const data = await apiClient.get(`/api/players/search?keyword=${encodeURIComponent(queryString)}`)
    cb((data || []).map(p => ({ ...p, value: formatPlayerOption(p) })))
  } catch (err) {
    cb([])
  } finally {
    playerSearchLoading.value = false
  }
}

const querySearchPartners = async (queryString, cb) => {
  if (!queryString || queryString.length < 2) return cb([])
  partnerSearchLoading.value = true
  try {
    const data = await apiClient.get(`/api/players/search?keyword=${encodeURIComponent(queryString)}`)
    cb((data || []).filter(p => p.player_id !== adminRegistrationForm.value.player_id).map(p => ({ ...p, value: formatPlayerOption(p) })))
  } catch (err) {
    cb([])
  } finally {
    partnerSearchLoading.value = false
  }
}

const openAddPlayerDialog = (row) => {
  adminRegistrationTournament.value = row
  selectedPlayer.value = null
  selectedPartner.value = null
  adminPlayerSearchText.value = ''
  adminPartnerSearchText.value = ''
  adminRegistrationForm.value = {
    category_id: row.categories?.[0]?.id || null,
    player_id: null,
    partner_player_id: null,
    notes: '',
    mark_paid: false,
    check_in: false
  }
  isAddPlayerDialogOpen.value = true
}

const handleSelectAdminPlayer = (player) => {
  selectedPlayer.value = player
  adminPlayerSearchText.value = player.value
  adminRegistrationForm.value.player_id = player.player_id
  if (adminRegistrationForm.value.partner_player_id === player.player_id) {
    selectedPartner.value = null
    adminPartnerSearchText.value = ''
    adminRegistrationForm.value.partner_player_id = null
  }
}

const handleSelectAdminPartner = (player) => {
  selectedPartner.value = player
  adminPartnerSearchText.value = player.value
  adminRegistrationForm.value.partner_player_id = player.player_id
}

const resetAdminPartner = () => {
  selectedPartner.value = null
  adminPartnerSearchText.value = ''
  adminRegistrationForm.value.partner_player_id = null
}

watch(() => adminRegistrationForm.value.category_id, () => {
  if (!adminRegistrationIsDoubles.value) resetAdminPartner()
})

const submitAdminAddPlayer = async () => {
  if (!adminRegistrationTournament.value) return
  if (!adminRegistrationForm.value.category_id) return ElMessage.warning('Vui lòng chọn nội dung thi đấu.')
  if (!adminRegistrationForm.value.player_id) return ElMessage.warning('Vui lòng chọn vận động viên.')
  if (adminRegistrationIsDoubles.value && !adminRegistrationForm.value.partner_player_id) {
    return ElMessage.warning('Nội dung đôi cần chọn đồng đội.')
  }

  isAddingPlayer.value = true
  try {
    await apiClient.post(`/api/registrations/admin/tournaments/${adminRegistrationTournament.value.id}/add-player`, adminRegistrationForm.value)
    ElMessage.success('Đã thêm vận động viên vào giải đấu.')
    isAddPlayerDialogOpen.value = false
    await loadTournaments()
    await loadStats()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || err.message || 'Không thể thêm vận động viên.')
  } finally {
    isAddingPlayer.value = false
  }
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
    
    // Sync top-level metadata with the first category for consistency
    if (payload.categories && payload.categories.length > 0) {
      payload.category_type = payload.categories[0].category_type
      // Guess gender division from category_type
      if (payload.category_type.includes('mens')) payload.gender_division = 'Men'
      else if (payload.category_type.includes('womens')) payload.gender_division = 'Women'
      else if (payload.category_type.includes('mixed')) payload.gender_division = 'Mixed'
    }

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
      description: normalizeTournamentDescription(payload.description),
      banner_url: payload.banner_url || null,
    }

    let tourId = form.value.id
    if (isEditMode.value) {
      await tournamentService.update(form.value.id, finalData)
      ElMessage.success(t('admin.updateSuccess'))
    } else {
      const data = await tournamentService.create(finalData)
      tourId = data.id
      ElMessage.success(t('admin.createSuccess'))
    }

    // Sync Categories for both Create and Edit mode (MOVED OUTSIDE)
    if (tourId && form.value.categories) {
      // Handle deletions
      for (const catId of deletedCategoryIds.value) {
        try { await apiClient.delete(`/api/tournaments/categories/${catId}`) } catch(e) { console.error(e) }
      }
      deletedCategoryIds.value = []

      // Handle Add/Update
      for (const cat of form.value.categories) {
        if (cat.id) {
          // Update existing
          await apiClient.put(`/api/tournaments/categories/${cat.id}`, cat)
        } else {
          // Add new
          await apiClient.post(`/api/tournaments/${tourId}/categories`, cat)
        }
      }
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
    const baseUrl = getApiBaseUrl();
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
  id: null, name: '', slug: '', status: 'open', format_type: 'Singles',
  draw_size: 32, category_type: 'mens_singles', gender_division: 'Men',
  location: '', surface_type: 'Hard', registration_open_at: '',
  registration_close_at: '', start_date: '', end_date: '',
  entry_fee: 100000, entry_fee_team: 200000, description: '',
  banner_url: '',
  categories: [
    { name: 'Đơn Nam', category_type: 'mens_singles', max_points: 1200, max_participants: 32 }
  ]
})
const form = ref(createDefaultForm())

const bannerUploadLoading = ref(false)
const handleBannerUpload = async (file) => {
  const isImage = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(file.type)
  if (!isImage) {
    ElMessage.error('Chỉ hỗ trợ tải lên tệp hình ảnh.')
    return false
  }

  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isLt5M) {
    ElMessage.error('Kích thước ảnh không được vượt quá 5MB.')
    return false
  }

  bannerUploadLoading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await apiClient.post('/api/tournaments/upload-banner', formData)
    form.value.banner_url = res.banner_url
    ElMessage.success('Tải ảnh banner lên thành công!')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || err.message || 'Tải ảnh banner lên thất bại.')
  } finally {
    bannerUploadLoading.value = false
  }
  return false
}

const deletedCategoryIds = ref([])

const removeCategoryFromForm = (index) => {
  const cat = form.value.categories[index]
  if (cat.id) {
    deletedCategoryIds.value.push(cat.id)
  }
  form.value.categories.splice(index, 1)
}

// Auto-fill category name based on type if empty
watch(() => form.value.categories, (newCats) => {
  if (!newCats) return
  newCats.forEach(cat => {
    if (!cat.name && cat.category_type) {
      const mapping = {
        'mens_singles': 'Đơn Nam',
        'mens_doubles': 'Đôi Nam',
        'mixed_doubles': 'Đôi Nam Nữ',
        'womens_doubles': 'Đôi Nữ'
      }
      if (mapping[cat.category_type]) {
        cat.name = mapping[cat.category_type]
      }
    }
  })
}, { deep: true })

// Merged into Main Dialog

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
              <div class="tournament-icon">
                <img v-if="row.banner_url" :src="row.banner_url" style="width: 100%; height: 100%; object-fit: cover; border-radius: 10px;" />
                <el-icon v-else><Trophy /></el-icon>
              </div>
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

        <!-- REMOVED REDUNDANT CATEGORY TYPE COLUMN -->
        
        <el-table-column :label="$t('admin.drawSize')" width="100" align="center">
          <template #default="{ row }">
            <span class="elo-badge">{{ row.draw_size }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="start_date" :label="$t('admin.startDate')" width="140" />

        <el-table-column :label="$t('admin.action')" width="190" fixed="right" align="center">
          <template #default="{ row }">
            <div class="saas-row-actions" @click.stop>
              <el-tooltip content="Thêm VĐV">
                <el-button size="small" circle @click="openAddPlayerDialog(row)" class="saas-icon-btn is-add-player"><el-icon><Plus /></el-icon></el-button>
              </el-tooltip>
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
        <div class="drawer-hero" :style="selectedTournament.banner_url ? `background-image: linear-gradient(rgba(15, 23, 42, 0.65), rgba(15, 23, 42, 0.75)), url(${selectedTournament.banner_url}); background-size: cover; background-position: center; color: #ffffff;` : ''">
          <div class="hero-icon" :style="selectedTournament.banner_url ? 'color: #f59e0b;' : ''"><el-icon><Trophy /></el-icon></div>
          <div class="hero-text">
            <h2 :style="selectedTournament.banner_url ? 'color: #ffffff;' : ''">{{ selectedTournament.name }}</h2>
            <div class="hero-badges">
              <el-tag :type="selectedTournament.status === 'open' ? 'success' : 'info'" effect="dark">{{ selectedTournament.status.toUpperCase() }}</el-tag>
              <!-- REMOVED REDUNDANT CATEGORY TYPE TAG -->
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

          <div v-if="selectedTournament.description" class="info-section">
            <h4>Nội dung giải đấu</h4>
            <div class="info-richtext" v-html="renderTournamentDescription(selectedTournament.description)"></div>
          </div>
        </div>
      </div>
    </el-drawer>

    <el-dialog
      v-model="isAddPlayerDialogOpen"
      title="Thêm vận động viên vào giải đấu"
      width="620px"
      class="saas-dialog"
      destroy-on-close
    >
      <div v-if="adminRegistrationTournament" class="admin-registration-panel">
        <div class="admin-registration-hero">
          <div class="tournament-icon"><el-icon><Trophy /></el-icon></div>
          <div>
            <h3>{{ adminRegistrationTournament.name }}</h3>
            <p>{{ adminRegistrationTournament.location || 'N/A' }}</p>
          </div>
        </div>

        <el-form label-position="top" class="saas-form">
          <el-form-item label="Nội dung thi đấu" required>
            <el-select v-model="adminRegistrationForm.category_id" style="width: 100%">
              <el-option
                v-for="cat in adminRegistrationTournament.categories || []"
                :key="cat.id"
                :label="cat.name"
                :value="cat.id"
              >
                <div class="category-option-row">
                  <span>{{ cat.name }}</span>
                  <small>{{ cat.category_type }}</small>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item label="Vận động viên" required>
            <el-autocomplete
              v-model="adminPlayerSearchText"
              :fetch-suggestions="querySearchPlayers"
              :trigger-on-focus="false"
              placeholder="Nhập tên vận động viên..."
              clearable
              class="w-full"
              @select="handleSelectAdminPlayer"
              @clear="selectedPlayer = null; adminPlayerSearchText = ''; adminRegistrationForm.player_id = null"
            >
              <template #suffix>
                <el-icon v-if="playerSearchLoading"><Search /></el-icon>
              </template>
              <template #default="{ item }">
                <div class="player-suggest-row">
                  <div class="suggest-avatar">{{ item.full_name?.charAt(0) }}</div>
                  <div>
                    <strong>{{ item.full_name }}</strong>
                    <span>{{ [item.phone, item.level].filter(Boolean).join(' · ') || 'Chưa có thông tin' }}</span>
                  </div>
                </div>
              </template>
            </el-autocomplete>
          </el-form-item>

          <el-form-item v-if="adminRegistrationIsDoubles" label="Đồng đội" required>
            <el-autocomplete
              v-model="adminPartnerSearchText"
              :fetch-suggestions="querySearchPartners"
              :trigger-on-focus="false"
              placeholder="Nhập tên đồng đội..."
              clearable
              class="w-full"
              @select="handleSelectAdminPartner"
              @clear="resetAdminPartner"
            >
              <template #suffix>
                <el-icon v-if="partnerSearchLoading"><Search /></el-icon>
              </template>
              <template #default="{ item }">
                <div class="player-suggest-row">
                  <div class="suggest-avatar">{{ item.full_name?.charAt(0) }}</div>
                  <div>
                    <strong>{{ item.full_name }}</strong>
                    <span>{{ [item.phone, item.level].filter(Boolean).join(' · ') || 'Chưa có thông tin' }}</span>
                  </div>
                </div>
              </template>
            </el-autocomplete>
          </el-form-item>

          <el-form-item label="Ghi chú">
            <el-input
              v-model="adminRegistrationForm.notes"
              type="textarea"
              :rows="3"
              placeholder="Ví dụ: Admin thêm trực tiếp, đã xác nhận qua điện thoại..."
            />
          </el-form-item>

          <div class="admin-registration-options">
            <el-checkbox v-model="adminRegistrationForm.mark_paid">Đánh dấu đã thanh toán</el-checkbox>
            <el-checkbox v-model="adminRegistrationForm.check_in">Thanh toán và check-in luôn</el-checkbox>
          </div>
        </el-form>
      </div>

      <template #footer>
        <div class="saas-dialog-footer">
          <el-button @click="isAddPlayerDialogOpen = false" class="saas-btn-secondary">{{ $t('admin.cancel') }}</el-button>
          <el-button type="primary" :loading="isAddingPlayer" @click="submitAdminAddPlayer" class="saas-btn-primary">
            Thêm vào giải
          </el-button>
        </div>
      </template>
    </el-dialog>

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
        
        <!-- Section: Tournament Banner -->
        <div class="form-section">
          <div class="section-header">
            <el-icon><Picture /></el-icon>
            <span>Ảnh Banner giải đấu</span>
          </div>
          <el-form-item label="Tải lên Banner">
            <div style="display: flex; align-items: center; gap: 16px; width: 100%;">
              <el-upload
                class="banner-uploader"
                action=""
                :show-file-list="false"
                :before-upload="handleBannerUpload"
                :disabled="bannerUploadLoading"
              >
                <el-button type="primary" plain :loading="bannerUploadLoading" :icon="Plus">
                  Chọn hình ảnh
                </el-button>
              </el-upload>
              <el-input v-model="form.banner_url" placeholder="Hoặc nhập URL ảnh banner..." clearable style="flex: 1;" />
            </div>
            <p class="form-help-text" style="margin-top: 8px; color: #64748b; font-size: 0.85rem;">
              Kích thước khuyến nghị: 1200x400px (tỷ lệ 3:1). Hỗ trợ JPG, PNG, WEBP tối đa 5MB.
            </p>
            <div v-if="form.banner_url" class="banner-preview-wrapper" style="margin-top: 12px;">
              <img :src="form.banner_url" class="banner-preview-img" />
              <el-button type="danger" size="small" circle :icon="Delete" class="banner-delete-btn" @click="form.banner_url = ''" />
            </div>
          </el-form-item>
        </div>

        <!-- Section: Competition Config -->
        <div class="form-section">
          <div class="section-header">
            <el-icon><EditPen /></el-icon>
            <span>{{ $t('admin.tournamentFormat') }}</span>
          </div>
            <el-col :span="12">
              <el-form-item :label="$t('admin.drawSize')" required>
                <el-select v-model="form.draw_size" style="width: 100%">
                  <el-option v-for="s in drawSizeOptions" :key="s" :label="s" :value="s" />
                </el-select>
              </el-form-item>
            </el-col>
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

        <div class="form-section">
          <div class="section-header">
            <el-icon><Edit /></el-icon>
            <span>Nội dung hiển thị cho trang giải đấu</span>
          </div>
          <el-form-item label="Thông tin / điều lệ / mô tả giải đấu">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="8"
              resize="vertical"
              placeholder="Nhập thông tin giới thiệu, điều lệ, lưu ý thi đấu, cơ cấu nội dung hoặc các hướng dẫn dành cho vận động viên..."
            />
          </el-form-item>
          <p class="form-help-text">
            Có thể nhập nội dung thường nhiều dòng. Hệ thống sẽ tự hiển thị xuống dòng ở trang chi tiết giải đấu.
          </p>
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

        <!-- Section: Categories (New) -->
        <div class="form-section">
          <div class="section-header">
            <el-icon><List /></el-icon>
            <span>Các nội dung thi đấu (Nam Nam, Nữ Nữ, Nam Nữ...)</span>
          </div>
          <div class="categories-inline-list">
            <el-table :data="form.categories" size="small" border>
              <el-table-column label="Tên nội dung">
                <template #default="{ row }">
                  <el-input v-model="row.name" size="small" placeholder="Ví dụ: Đôi Nam 1200" />
                </template>
              </el-table-column>
              <el-table-column label="Loại hình" width="140">
                <template #default="{ row }">
                  <el-select v-model="row.category_type" size="small">
                    <el-option label="Đơn Nam" value="mens_singles" />
                    <el-option label="Đôi Nam" value="mens_doubles" />
                    <el-option label="Đôi Nam Nữ" value="mixed_doubles" />
                    <el-option label="Đôi Nữ" value="womens_doubles" />
                    <!-- Fallback for legacy values -->
                    <el-option v-if="row.category_type && !['mens_singles', 'mens_doubles', 'mixed_doubles', 'womens_doubles'].includes(row.category_type)" 
                               :label="row.category_type" :value="row.category_type" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="Điểm/Số người" width="180">
                <template #default="{ row }">
                  <div class="flex gap-1">
                    <el-input-number v-model="row.max_points" :step="25" size="small" controls-position="right" placeholder="Pts" />
                    <el-input-number v-model="row.max_participants" :step="2" size="small" controls-position="right" />
                  </div>
                </template>
              </el-table-column>
              <el-table-column width="60" align="center">
                <template #default="{ $index }">
                  <el-button type="danger" link :icon="Delete" @click="removeCategoryFromForm($index)" :disabled="form.categories.length <= 1" />
                </template>
              </el-table-column>
            </el-table>
            <el-button type="info" plain class="w-full mt-3" @click="form.categories.push({ name: '', category_type: 'mens_doubles', max_points: 1250, max_participants: 32 })">
              <el-icon class="mr-1"><Plus /></el-icon> Thêm nội dung khác (Ví dụ: Đôi Nam 1300)
            </el-button>
          </div>
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
.saas-icon-btn.is-add-player:hover { background: #10b981 !important; border-color: #10b981 !important; }

.admin-registration-panel {
  display: grid;
  gap: 22px;
}

.admin-registration-hero {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
}

.admin-registration-hero h3 {
  margin: 0;
  color: #0f172a;
  font-size: 1rem;
  font-weight: 900;
}

.admin-registration-hero p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 0.86rem;
}

.category-option-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
}

.category-option-row small {
  color: #94a3b8;
}

.player-suggest-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
}

.suggest-avatar {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: #ecfdf5;
  color: #059669;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
}

.player-suggest-row strong,
.player-suggest-row span {
  display: block;
}

.player-suggest-row span {
  color: #64748b;
  font-size: 0.78rem;
}

.admin-registration-options {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  padding: 12px 14px;
  background: #f8fafc;
  border-radius: 12px;
}

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
.info-richtext {
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  border-radius: 20px;
  padding: 20px;
  color: #334155;
  line-height: 1.7;
}
.info-richtext :deep(p:first-child) { margin-top: 0; }
.info-richtext :deep(p:last-child) { margin-bottom: 0; }

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

.form-help-text {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 0.9rem;
  line-height: 1.5;
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
.banner-uploader {
  display: inline-block;
}
.banner-preview-wrapper {
  position: relative;
  width: 100%;
  max-height: 200px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px dashed #cbd5e1;
  background: #f8fafc;
  display: flex;
  justify-content: center;
  align-items: center;
}
.banner-preview-img {
  width: 100%;
  height: 200px;
  object-fit: cover;
}
.banner-delete-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>
