<script setup>
import { computed, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, Refresh, Plus, Edit, Delete,
  Location as LocationIcon, OfficeBuilding, Monitor, 
  Suitcase, Compass, Connection,
  Check, Close
} from '@element-plus/icons-vue'
import { courtService } from '../../services/courtService'
import { t } from '../../utils/locale'

const search = ref('')
const statusFilter = ref('')
const courts = ref([])
const isLoading = ref(false)
const isSaving = ref(false)
const isDialogOpen = ref(false)
const isEditMode = ref(false)

const surfaceOptions = ['HARD', 'CLAY', 'GRASS', 'CARPET']
const statusOptions = computed(() => [
  { label: t('admin.statusAvailable'), value: 'AVAILABLE' },
  { label: t('admin.statusUnavailable'), value: 'UNAVAILABLE' }
])

const stats = computed(() => {
  return {
    total: courts.value.length,
    active: courts.value.filter(c => c.is_active).length,
    hard: courts.value.filter(c => c.surface_type === 'HARD').length,
    clay: courts.value.filter(c => c.surface_type === 'CLAY').length
  }
})

const createDefaultForm = () => ({
  id: null,
  court_name: '',
  location_name: '',
  surface_type: 'HARD',
  is_active: true
})

const form = ref(createDefaultForm())

const loadCourts = async () => {
  isLoading.value = true
  try {
    const data = await courtService.getAll()
    courts.value = Array.isArray(data) ? data : (data.items || [])
  } catch (err) {
    ElMessage.error(t('admin.loadCourtsError') + ' ' + err.message)
  } finally {
    isLoading.value = false
  }
}

// BỘ LỌC PHẢN HỒI TỨC THÌ (REACTIVE)
const filteredCourts = computed(() => {
  let result = [...courts.value]
  
  if (search.value) {
    const s = search.value.toLowerCase().trim()
    result = result.filter(c => 
      (c.court_name || '').toLowerCase().includes(s) || 
      (c.location_name || '').toLowerCase().includes(s)
    )
  }
  
  if (statusFilter.value) {
    const isActive = statusFilter.value === 'AVAILABLE'
    result = result.filter(c => c.is_active === isActive)
  }
  
  return result
})

const openCreateDialog = () => {
  isEditMode.value = false
  form.value = createDefaultForm()
  isDialogOpen.value = true
}

const openEditDialog = (row) => {
  isEditMode.value = true
  form.value = { ...row }
  isDialogOpen.value = true
}

const saveCourt = async () => {
  form.value.court_name = form.value.court_name?.trim() || ''
  form.value.location_name = form.value.location_name?.trim() || ''

  if (!form.value.court_name || !form.value.location_name) {
    return ElMessage.warning(t('admin.saveWarning'))
  }
  
  isSaving.value = true
  try {
    if (isEditMode.value) {
      await courtService.update(form.value.id, form.value)
      ElMessage.success(t('admin.updateSuccess'))
    } else {
      await courtService.create(form.value)
      ElMessage.success(t('admin.createSuccess'))
    }
    isDialogOpen.value = false
    loadCourts()
  } catch (err) {
    const errorMsg = err.response?.data?.detail || err.message || t('admin.saveError')
    ElMessage.error(errorMsg)
  } finally {
    isSaving.value = false
  }
}

const deleteCourt = (id) => {
  ElMessageBox.confirm(t('admin.deleteConfirm'), t('admin.deleteWarningTitle'), { type: 'warning' }).then(async () => {
    try {
      await courtService.delete(id)
      ElMessage.success(t('admin.deleteSuccess'))
      loadCourts()
    } catch (err) {
      ElMessage.error(t('admin.deleteError') + ' ' + err.message)
    }
  })
}

const resetFilters = () => {
  search.value = ''
  statusFilter.value = ''
}

onMounted(loadCourts)
</script>

<template>
  <div class="saas-container">
    <!-- Stats Row -->
    <div class="saas-stats-grid">
      <div class="saas-stat-card">
        <div class="stat-icon p-blue"><el-icon><OfficeBuilding /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.totalCourts') }}</span>
          <h3 class="stat-value">{{ stats.total }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-green"><el-icon><Monitor /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.activeCourts') }}</span>
          <h3 class="stat-value">{{ stats.active }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-orange"><el-icon><Connection /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.hardCourts') }}</span>
          <h3 class="stat-value">{{ stats.hard }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-purple"><el-icon><Compass /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.clayCourts') }}</span>
          <h3 class="stat-value">{{ stats.clay }}</h3>
        </div>
      </div>
    </div>

    <!-- Header & Action Bar -->
    <div class="saas-header">
      <div class="header-left">
        <el-input 
          v-model="search" 
          :placeholder="$t('admin.searchPlaceholder')" 
          clearable 
          class="saas-search"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        
        <el-select 
          v-model="statusFilter" 
          :placeholder="$t('admin.statusFilterPlaceholder')" 
          clearable 
          class="saas-filter"
        >
          <template #prefix><el-icon><Connection /></el-icon></template>
          <el-option v-for="st in statusOptions" :key="st.value" :label="st.label" :value="st.value" />
        </el-select>

        <el-button @click="resetFilters" class="saas-btn-reset">
          <el-icon class="mr-1"><Refresh /></el-icon> {{ $t('admin.resetFilterBtn') }}
        </el-button>
      </div>

      <div class="header-right">
        <el-button type="primary" @click="openCreateDialog" class="saas-btn-create">
          <el-icon class="mr-1"><Plus /></el-icon> {{ $t('admin.addCourtBtn') }}
        </el-button>
      </div>
    </div>

    <!-- Data Table -->
    <div class="saas-content">
      <el-table 
        :data="filteredCourts" 
        v-loading="isLoading" 
        class="saas-table"
        :header-cell-style="{ background: 'transparent', color: '#1e293b', fontWeight: '800', borderBottom: '2px solid #e2e8f0' }"
      >
        <el-table-column :label="$t('admin.courtInfoCol')" min-width="320">
          <template #default="{ row }">
            <div class="saas-court-cell">
              <div class="court-icon-premium">
                <el-icon><OfficeBuilding /></el-icon>
              </div>
              <div class="saas-court-meta">
                <span class="court-name">{{ row.court_name }}</span>
                <span class="location-name">
                  <el-icon class="mr-1"><LocationIcon /></el-icon>
                  {{ row.location_name }}
                </span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="surface_type" :label="$t('admin.surfaceCol')" width="180" align="center">
          <template #default="{ row }">
            <div class="surface-badge-premium" :class="row.surface_type.toLowerCase()">
              {{ row.surface_type }}
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.statusCol')" width="180" align="center">
          <template #default="{ row }">
            <div class="status-indicator" :class="row.is_active ? 'is-active' : 'is-inactive'">
              <span class="dot"></span>
              <span>{{ row.is_active ? $t('admin.statusAvailable') : $t('admin.statusUnavailable') }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.actionsCol')" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <div class="saas-row-actions">
              <el-tooltip :content="$t('admin.editTooltip')">
                <el-button size="small" circle @click="openEditDialog(row)" class="saas-icon-btn">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip :content="$t('admin.deleteTooltip')">
                <el-button size="small" circle @click="deleteCourt(row.id)" class="saas-icon-btn is-delete">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="filteredCourts.length === 0 && !isLoading" :description="$t('admin.noCourtsFound')" />
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog 
      v-model="isDialogOpen" 
      :title="isEditMode ? $t('admin.editCourtTitle') : $t('admin.addCourtTitle')" 
      width="550px"
      class="saas-dialog"
      destroy-on-close
    >
      <el-form label-position="top" class="saas-form">
        <el-form-item :label="$t('admin.courtNameLabel')" required>
          <el-input v-model="form.court_name" :placeholder="$t('admin.courtNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('admin.locationLabel')" required>
          <el-input v-model="form.location_name" :placeholder="$t('admin.locationPlaceholder')">
            <template #prefix><el-icon><LocationIcon /></el-icon></template>
          </el-input>
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('admin.surfaceLabel')">
              <el-select v-model="form.surface_type" style="width: 100%">
                <el-option v-for="opt in surfaceOptions" :key="opt" :label="opt" :value="opt" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('admin.statusLabel')">
              <div class="switch-wrap">
                <el-switch 
                  v-model="form.is_active" 
                  :active-text="$t('admin.statusAvailable')" 
                  :inactive-text="$t('admin.statusUnavailable')" 
                />
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <div class="saas-dialog-footer">
          <el-button @click="isDialogOpen = false" class="saas-btn-secondary">{{ $t('admin.cancelBtn') }}</el-button>
          <el-button type="primary" :loading="isSaving" @click="saveCourt" class="saas-btn-primary">
            {{ $t('admin.saveBtn') }}
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
  border-radius: 24px;
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
.p-purple { background: #f5f3ff; color: #8b5cf6; }

.stat-label { font-size: 0.75rem; color: #64748b; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; }
.stat-value { margin: 4px 0 0; font-size: 1.8rem; font-weight: 800; color: #0f172a; }

/* Header & Action Bar */
.saas-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.saas-search { width: 320px; }
.saas-filter { width: 200px; }

:deep(.el-input__wrapper), :deep(.el-select__wrapper) {
  background-color: #f8fafc !important;
  box-shadow: none !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 12px !important;
  padding: 8px 12px !important;
}

.saas-btn-reset {
  border-radius: 12px !important;
  padding: 20px !important;
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  color: #1e293b !important;
  font-weight: 700;
  transition: all 0.2s;
}

.saas-btn-reset:hover {
  background: #f1f5f9 !important;
  border-color: #cbd5e1 !important;
}

.saas-btn-create {
  border-radius: 12px !important;
  padding: 20px 24px !important;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* Table Styling */
.saas-content {
  background: #fff;
  border-radius: 24px;
  border: 1px solid #f1f5f9;
  padding: 8px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.03);
}

.saas-table {
  background: transparent !important;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
}

.saas-court-cell {
  display: flex;
  align-items: center;
  gap: 16px;
}

.court-icon-premium {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 20px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.03);
}

.saas-court-meta { display: flex; flex-direction: column; gap: 2px; }
.court-name { display: block; font-weight: 800; color: #0f172a; font-size: 1rem; }
.location-name { display: flex; align-items: center; font-size: 0.8rem; color: #64748b; font-weight: 600; }

.surface-badge-premium {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.hard { background: #eff6ff; color: #1d4ed8; }
.clay { background: #fff7ed; color: #c2410c; }
.grass { background: #f0fdf4; color: #15803d; }
.carpet { background: #f5f3ff; color: #6d28d9; }

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 700;
}

.is-active { background: #ecfdf5; color: #059669; }
.is-inactive { background: #fef2f2; color: #dc2626; }

.is-active .dot { background: #10b981; animation: pulse 2s infinite; }
.is-inactive .dot { background: #ef4444; }

.dot { width: 8px; height: 8px; border-radius: 50%; }

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.saas-row-actions { display: flex; gap: 8px; justify-content: center; }

.saas-icon-btn {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  color: #64748b !important;
  transition: all 0.2s;
}

.saas-icon-btn:hover {
  background: #eff6ff !important;
  border-color: #3b82f6 !important;
  color: #3b82f6 !important;
}

.saas-icon-btn.is-delete:hover {
  background: #fef2f2 !important;
  border-color: #ef4444 !important;
  color: #ef4444 !important;
}

/* Dialog & Form */
:deep(.saas-dialog) { border-radius: 24px !important; overflow: hidden; }

:deep(.el-dialog__header) {
  margin: 0; padding: 24px 32px; border-bottom: 1px solid #f1f5f9;
}

:deep(.el-dialog__title) { font-weight: 800; color: #0f172a; }

.saas-form { padding: 8px 12px; }

:deep(.el-form-item__label) {
  font-weight: 700; color: #1e293b; margin-bottom: 8px !important;
}

.switch-wrap {
  padding: 8px 16px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;
}

.saas-dialog-footer {
  display: flex; gap: 12px; justify-content: flex-end; padding: 0 12px 12px;
}

.saas-btn-secondary { border-radius: 12px !important; padding: 20px 24px !important; font-weight: 600; }
.saas-btn-primary { border-radius: 12px !important; padding: 20px 32px !important; font-weight: 700; }

.mr-1 { margin-right: 4px; }
</style>
