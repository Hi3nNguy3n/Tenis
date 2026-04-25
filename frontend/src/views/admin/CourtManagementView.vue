<script setup>
import { computed, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Edit, Delete } from '@element-plus/icons-vue'
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
  // 1. Chuẩn hóa chuỗi (Xóa dấu cách dư thừa ở đầu và cuối)
  form.value.court_name = form.value.court_name?.trim() || ''
  form.value.location_name = form.value.location_name?.trim() || ''

  // 2. Validate rỗng
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
    // 3. Hiển thị thông báo lỗi từ Backend (Cực kỳ quan trọng)
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
  <div class="module-shell">
    <!-- HEADER PREMIUM -->
    <section class="action-bar-glass shadow-sm">
      <div class="action-info">
        <div class="kicker-wrap">
          <span class="section-kicker">{{ $t('admin.facilitiesManagement') }}</span>
          <div class="live-indicator">
            <span class="dot"></span>
            LIVE
          </div>
        </div>
        <p>{{ $t('admin.facilitiesDesc') }}</p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" round :icon="Plus" @click="openCreateDialog">{{ $t('admin.addCourtBtn') }}</el-button>
        <el-button plain round :icon="Refresh" @click="loadCourts">{{ $t('admin.refreshBtn') }}</el-button>
      </div>
    </section>

    <section class="filter-card">
      <div class="filter-row">
        <el-input 
          v-model="search" 
          :placeholder="$t('admin.searchPlaceholder')" 
          clearable 
          style="width: 350px"
          :prefix-icon="Search"
        />
        <el-select 
          v-model="statusFilter" 
          :placeholder="$t('admin.statusFilterPlaceholder')" 
          clearable 
          style="width: 200px"
        >
          <el-option v-for="st in statusOptions" :key="st.value" :label="st.label" :value="st.value" />
        </el-select>
        <el-button @click="resetFilters" plain>{{ $t('admin.resetFilterBtn') }}</el-button>
      </div>
    </section>

    <section class="table-card shadow-sm">
      <el-table :data="filteredCourts" stripe v-loading="isLoading" table-layout="fixed">
        <el-table-column prop="id" label="ID" min-width="60" align="center" />
        <el-table-column :label="$t('admin.courtInfoCol')" min-width="250">
           <template #default="{ row }">
             <div class="court-info">
               <span class="court-name">{{ row.court_name }}</span>
               <span class="location-name">{{ row.location_name }}</span>
             </div>
           </template>
        </el-table-column>
        <el-table-column prop="surface_type" :label="$t('admin.surfaceCol')" min-width="100" align="center">
           <template #default="{ row }">
             <el-tag effect="plain" type="info">{{ row.surface_type }}</el-tag>
           </template>
        </el-table-column>
        <el-table-column :label="$t('admin.statusCol')" min-width="200" align="center">
           <template #default="{ row }">
             <el-tag :type="row.is_active ? 'success' : 'danger'" effect="light" class="status-tag">
               {{ row.is_active ? $t('admin.statusActive') : $t('admin.statusInactive') }}
             </el-tag>
           </template>
        </el-table-column>
        <el-table-column :label="$t('admin.actionsCol')" min-width="120" fixed="right" align="center">
          <template #default="{ row }">
            <div class="table-actions">
              <el-tooltip :content="$t('admin.editTooltip')" placement="top">
                <el-button 
                  circle 
                  size="small" 
                  type="primary" 
                  plain 
                  :icon="Edit" 
                  @click="openEditDialog(row)"
                />
              </el-tooltip>

              <el-tooltip :content="$t('admin.deleteTooltip')" placement="top">
                <el-button 
                  circle 
                  size="small" 
                  type="danger" 
                  plain 
                  :icon="Delete" 
                  @click="deleteCourt(row.id)"
                />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="filteredCourts.length === 0" :description="$t('admin.noCourtsFound')" />
    </section>

    <el-dialog v-model="isDialogOpen" :title="isEditMode ? $t('admin.editCourtTitle') : $t('admin.addCourtTitle')" width="500px">
      <el-form label-position="top">
        <el-form-item :label="$t('admin.courtNameLabel')" required>
          <el-input v-model="form.court_name" :placeholder="$t('admin.courtNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('admin.locationLabel')" required>
          <el-input v-model="form.location_name" :placeholder="$t('admin.locationPlaceholder')" />
        </el-form-item>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
           <el-form-item :label="$t('admin.surfaceLabel')">
             <el-select v-model="form.surface_type" style="width: 100%">
               <el-option v-for="opt in surfaceOptions" :key="opt" :label="opt" :value="opt" />
             </el-select>
           </el-form-item>
           <el-form-item :label="$t('admin.statusLabel')">
             <el-switch v-model="form.is_active" :active-text="$t('admin.statusAvailable')" :inactive-text="$t('admin.statusUnavailable')" />
           </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="isDialogOpen = false">{{ $t('admin.cancelBtn') }}</el-button>
        <el-button type="primary" :loading="isSaving" @click="saveCourt" round>{{ $t('admin.saveBtn') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.module-shell { display: grid; gap: 16px; padding: 10px; }

@media (max-width: 960px) {
  .module-shell { padding: 0; }

  .action-bar-glass,
  .filter-card,
  .table-card {
    padding-left: 16px;
    padding-right: 16px;
  }

  .action-bar-glass {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .hero-actions,
  .filter-row,
  .table-actions {
    flex-wrap: wrap;
  }

  .filter-row {
    width: 100%;
  }

  :deep(.el-input),
  :deep(.el-select) {
    width: 100% !important;
  }
}

@media (max-width: 640px) {
  .action-bar-glass,
  .filter-card,
  .table-card {
    padding: 12px;
    border-radius: 16px;
  }

  .hero-actions,
  .filter-row {
    display: grid;
    grid-template-columns: 1fr;
  }

  :deep(.el-dialog) {
    width: calc(100vw - 24px) !important;
    max-width: calc(100vw - 24px);
  }
}

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

.action-info p { color: #64748b; font-size: 0.9rem; margin: 0; }

.filter-card {
  background: white; padding: 16px 24px; border-radius: 20px;
  border: 1px solid #f1f5f9; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
}

.filter-row { display: flex; gap: 16px; }

.table-card {
  background: white; padding: 8px; border-radius: 20px;
  border: 1px solid #f1f5f9; box-shadow: 0 10px 30px rgba(0,0,0,0.03);
  overflow: hidden;
}

:deep(.el-table) { border-radius: 12px; }

.court-info { display: flex; flex-direction: column; gap: 2px; }
.court-name { font-weight: 700; color: #0f172a; font-size: 0.95rem; }
.location-name { font-size: 0.8rem; color: #94a3b8; font-family: 'Arial', sans-serif; }

.status-tag { 
  font-weight: 600; border-radius: 99px; padding: 0 16px; font-size: 0.65rem; 
  border: none !important;
}

.table-actions { display: flex; gap: 12px; justify-content: center; }

.shadow-sm { box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
</style>
