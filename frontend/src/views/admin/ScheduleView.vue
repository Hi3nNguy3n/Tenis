<script setup>
import { onMounted, ref, computed } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import { 
  Refresh, Download, Edit, Location as LocationIcon, Timer,
  Trophy, Monitor, Connection, ArrowLeft,
  CircleCheckFilled, Message, Search, Filter,
  Calendar as CalendarIcon, Operation, VideoPlay, Clock as ClockIcon
} from '@element-plus/icons-vue'
import { t } from '../../utils/locale'

const isLoading = ref(false)
const schedule = ref([])
const filterDate = ref('')

const loadMatches = async () => {
  isLoading.value = true
  try {
    const data = await apiClient.get('/api/matches/')
    schedule.value = data
  } catch (err) {
    ElMessage.error(t('admin.loadScheduleError') + err.message)
  } finally {
    isLoading.value = false
  }
}

const filteredSchedule = computed(() => {
  if (!filterDate.value) return schedule.value
  return schedule.value.filter(m => m.date === filterDate.value)
})

const getStatusType = (s) => {
  const status = s?.toLowerCase()
  if (status === 'ongoing') return 'primary'
  if (status === 'completed' || status === 'finished') return 'success'
  if (status === 'scheduled') return 'warning'
  return 'info'
}

const showEditDialog = ref(false)
const editingMatch = ref(null)
const editForm = ref({ court_id: null, start_time: '' })
const courts = ref([])

const fetchCourts = async () => {
  try {
    const data = await apiClient.get('/api/courts/')
    courts.value = data
  } catch (err) { ElMessage.error(t('admin.loadCourtsError')) }
}

const handleEdit = (row) => {
  editingMatch.value = row
  const targetCourt = courts.value.find(c => c.court_name === row.court)
  editForm.value.court_id = targetCourt ? targetCourt.id : null
  editForm.value.start_time = row.date && row.start !== '--:--' ? `${row.date}T${row.start}:00` : ''
  showEditDialog.value = true
}

const handleSchedule = async () => {
  if (!editForm.value.court_id || !editForm.value.start_time) {
    return ElMessage.warning(t('admin.chooseCourtAndTime'))
  }
  try {
    await apiClient.post(`/api/tournaments/matches/${editingMatch.value.id}/schedule`, {
      court_id: editForm.value.court_id,
      start_time: editForm.value.start_time
    })
    ElMessage.success(t('admin.updateScheduleSuccess'))
    showEditDialog.value = false
    loadMatches()
  } catch (err) {
    ElMessage.error(t('admin.updateError') + err.message)
  }
}

onMounted(() => {
  loadMatches()
  fetchCourts()
})
</script>

<template>
  <div class="saas-container" v-loading="isLoading">
    <!-- Action Bar -->
    <section class="saas-header">
      <div class="header-left">
        <div class="operation-badge-premium green">
          <el-icon class="mr-1"><Timer /></el-icon>
          <span>Schedule Management</span>
        </div>
        <div class="header-titles">
          <h2 class="saas-title">{{ $t('admin.scheduleOverview') }}</h2>
          <p class="saas-subtitle">{{ $t('admin.scheduleOverviewDesc') }}</p>
        </div>
      </div>
      
      <div class="header-right">
        <el-date-picker 
          v-model="filterDate" 
          type="date" 
          :placeholder="$t('admin.filterByDate')" 
          value-format="YYYY-MM-DD" 
          class="saas-date-picker-premium"
          @change="loadMatches"
        />
        <el-button @click="loadMatches" :icon="Refresh" class="saas-btn-refresh">Refresh</el-button>
        <el-button type="primary" :icon="Download" class="saas-btn-primary">{{ $t('admin.exportData') }}</el-button>
      </div>
    </section>

    <!-- Table Card -->
    <main class="saas-card-premium table-block">
      <div class="table-header-saas">
        <div class="th-left">
          <el-icon><CalendarIcon /></el-icon>
          <h3>{{ $t('admin.systemSchedule') }}</h3>
        </div>
        <el-badge :value="filteredSchedule.length" type="primary" class="saas-badge-count" />
      </div>

      <el-table :data="filteredSchedule" style="width: 100%" class="saas-table-premium">
        <el-table-column :label="$t('admin.tournamentCol')" min-width="280">
          <template #default="{ row }">
            <div class="tour-cell-saas">
              <div class="tc-icon"><el-icon><Trophy /></el-icon></div>
              <div class="tc-info">
                <span class="tc-name">{{ row.tournament }}</span>
                <span class="tc-sub">Saigon Tennis System</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.locationCol')" min-width="220">
          <template #default="{ row }">
            <div class="loc-cell-saas">
              <el-icon class="mr-2"><LocationIcon /></el-icon>
              <span>{{ row.court || $t('admin.unassignedCourt') }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.dateTimeCol')" width="200">
          <template #default="{ row }">
            <div class="time-cell-saas">
              <span class="tc-date">{{ row.date }}</span>
              <div class="tc-time">
                <el-icon><ClockIcon /></el-icon>
                <strong>{{ row.start }}</strong>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.statusCol')" width="160" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="dark" class="saas-status-pill">
              {{ row.status?.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.actionCol')" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <div class="saas-action-buttons">
              <el-tooltip :content="$t('admin.editMatch')" placement="top">
                <el-button circle :icon="Edit" @click="handleEdit(row)" class="btn-edit" />
              </el-tooltip>
              <el-tooltip :content="$t('admin.reschedule')" placement="top">
                <el-button circle :icon="Timer" @click="handleEdit(row)" class="btn-reschedule" />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="filteredSchedule.length === 0" :image-size="120" :description="$t('admin.noScheduleMatch')" />
    </main>

    <!-- Adjust Schedule Dialog -->
    <el-dialog 
      v-model="showEditDialog" 
      width="500px" 
      class="saas-dialog-premium"
      destroy-on-close
    >
      <template #header>
        <div class="dialog-header-saas">
          <el-icon class="mr-2"><Timer /></el-icon>
          <span>{{ $t('admin.adjustSchedule') }}</span>
        </div>
      </template>

      <div class="saas-dialog-content">
        <div v-if="editingMatch" class="saas-context-card mb-6">
          <div class="context-row">
            <span class="label">Tournament</span>
            <strong class="value">{{ editingMatch.tournament }}</strong>
          </div>
          <div class="context-row">
            <span class="label">Current Location</span>
            <strong class="value">{{ editingMatch.court || 'Unassigned' }}</strong>
          </div>
          <div class="context-row">
            <span class="label">Current Time</span>
            <strong class="value">{{ editingMatch.start || '--:--' }}</strong>
          </div>
        </div>

        <el-form label-position="top" class="saas-form-premium">
          <el-form-item :label="$t('admin.selectNewCourt')">
            <el-select v-model="editForm.court_id" :placeholder="$t('admin.clickToSelectCourt')" class="w-full saas-input-large">
              <template #prefix><el-icon><LocationIcon /></el-icon></template>
              <el-option v-for="c in courts" :key="c.id" :label="c.court_name" :value="c.id" />
            </el-select>
          </el-form-item>
          
          <el-form-item :label="$t('admin.newDateTime')">
            <el-date-picker
              v-model="editForm.start_time"
              type="datetime"
              :placeholder="$t('admin.selectSpecificTime')"
              format="DD/MM/YYYY HH:mm"
              value-format="YYYY-MM-DDTHH:mm:ss"
              class="w-full saas-input-large"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="saas-dialog-footer">
          <el-button @click="showEditDialog = false" class="saas-btn-secondary">{{ $t('admin.cancel') }}</el-button>
          <el-button type="primary" @click="handleSchedule" class="saas-btn-primary">{{ $t('admin.confirmUpdate') }}</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.saas-container { display: flex; flex-direction: column; gap: 32px; min-height: 100%; }

/* Action Bar */
.saas-header { display: flex; align-items: center; justify-content: space-between; }
.header-left { display: flex; align-items: center; }

.operation-badge-premium {
  background: #eff6ff; color: #2563eb; padding: 10px 20px; border-radius: 14px;
  font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
  display: inline-flex; align-items: center; margin-right: 24px;
}
.operation-badge-premium.green { background: #f0fdf4; color: #16a34a; }

.header-titles { display: flex; flex-direction: column; gap: 4px; }
.saas-title { font-size: 1.8rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.02em; }
.saas-subtitle { font-size: 0.95rem; color: #64748b; margin: 0; font-weight: 600; }

.header-right { display: flex; align-items: center; gap: 12px; }
.saas-date-picker-premium :deep(.el-input__wrapper) { 
  background: #fff !important; border-radius: 14px !important; height: 48px; border: 1px solid #e2e8f0 !important; box-shadow: none !important;
}
.saas-btn-refresh { height: 48px !important; border-radius: 14px !important; font-weight: 800 !important; width: 48px !important; padding: 0 !important; }
.saas-btn-primary { height: 48px !important; border-radius: 14px !important; font-weight: 900 !important; padding: 0 24px !important; background: #2563eb !important; border: none !important; }

/* Table Block */
.saas-card-premium { background: #fff; border-radius: 32px; border: 1px solid #f1f5f9; padding: 32px; box-shadow: 0 10px 40px rgba(0,0,0,0.02); }
.table-block { padding: 0; overflow: hidden; }

.table-header-saas { padding: 32px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; }
.th-left { display: flex; align-items: center; gap: 12px; }
.th-left h3 { margin: 0; font-size: 1.2rem; font-weight: 900; color: #0f172a; }
.th-left .el-icon { color: #2563eb; font-size: 20px; }
.saas-badge-count :deep(.el-badge__content) { background: #eff6ff; color: #2563eb; font-weight: 900; border: none; }

/* Table Premium */
.saas-table-premium :deep(.el-table__header) { background: #fafafa; }
.saas-table-premium :deep(.el-table__header th) { background: #fafafa; color: #94a3b8; font-weight: 800; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; padding: 20px 0; }
.saas-table-premium :deep(.el-table__row) { transition: all 0.2s; }
.saas-table-premium :deep(.el-table__row:hover) { background-color: #f8fafc !important; }

.tour-cell-saas { display: flex; align-items: center; gap: 16px; }
.tc-icon { width: 40px; height: 40px; background: #f0f7ff; color: #3b82f6; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
.tc-info { display: flex; flex-direction: column; gap: 2px; }
.tc-name { font-weight: 800; color: #1e293b; font-size: 0.95rem; }
.tc-sub { font-size: 0.75rem; color: #94a3b8; font-weight: 700; }

.loc-cell-saas { display: flex; align-items: center; color: #475569; font-weight: 700; font-size: 0.9rem; }
.loc-cell-saas .el-icon { color: #2563eb; font-size: 18px; }

.time-cell-saas { display: flex; flex-direction: column; gap: 4px; }
.tc-date { font-size: 0.8rem; color: #94a3b8; font-weight: 700; }
.tc-time { display: flex; align-items: center; gap: 6px; color: #0f172a; }
.tc-time strong { font-size: 1rem; font-weight: 900; }
.tc-time .el-icon { color: #f59e0b; }

.saas-status-pill { border-radius: 10px; font-weight: 900; font-size: 0.7rem; padding: 0 16px; height: 32px; border: none; letter-spacing: 0.05em; }

.saas-action-buttons { display: flex; gap: 10px; justify-content: center; }
.saas-action-buttons .el-button { border: 1px solid #f1f5f9; background: #fff; transition: all 0.2s; color: #64748b; }
.saas-action-buttons .btn-edit:hover { background: #eff6ff; color: #2563eb; border-color: #2563eb; }
.saas-action-buttons .btn-reschedule:hover { background: #f0fdf4; color: #10b981; border-color: #10b981; }

/* Dialog Premium */
:deep(.saas-dialog-premium) { border-radius: 32px !important; overflow: hidden; }
:deep(.el-dialog__header) { padding: 0 !important; margin: 0 !important; }

.dialog-header-saas { padding: 24px 32px; background: #fafafa; border-bottom: 1px solid #f1f5f9; display: flex; align-items: center; font-weight: 900; color: #0f172a; font-size: 1.1rem; }
.saas-dialog-content { padding: 32px; }

.saas-context-card { background: #f8fafc; border-radius: 20px; padding: 24px; border: 1px solid #f1f5f9; display: flex; flex-direction: column; gap: 12px; }
.context-row { display: flex; justify-content: space-between; align-items: center; }
.context-row .label { font-size: 0.75rem; color: #94a3b8; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; }
.context-row .value { font-size: 0.95rem; color: #1e293b; font-weight: 800; }

.saas-form-premium { display: flex; flex-direction: column; gap: 20px; }
.saas-input-large :deep(.el-input__wrapper) { background: #f8fafc !important; border-radius: 14px !important; height: 50px; box-shadow: none !important; border: 1px solid #e2e8f0 !important; }

.saas-dialog-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 0 32px 32px; }
.saas-btn-secondary { height: 48px; border-radius: 12px; font-weight: 700; padding: 0 24px; border-color: #e2e8f0; }
.saas-btn-primary { height: 48px; border-radius: 12px; font-weight: 900; padding: 0 32px; background: #2563eb; border: none; }

.mb-6 { margin-bottom: 24px; }
.mr-1 { margin-right: 4px; }
.mr-2 { margin-right: 8px; }
.w-full { width: 100%; }
</style>
