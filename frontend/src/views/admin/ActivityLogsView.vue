<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '../../services/apiClient'
import { Document, Search, Timer } from '@element-plus/icons-vue'
import { t } from '../../utils/locale'

const logs = ref([])
const isLoading = ref(true)
const filterModule = ref('')

// Danh sách các module để filter
const modules = computed(() => [
  { label: t('admin.moduleAll'), value: '' },
  { label: t('admin.moduleTournament'), value: 'TOURNAMENT' },
  { label: t('admin.modulePlayer'), value: 'PLAYER' },
  { label: t('admin.moduleMatch'), value: 'MATCH' },
  { label: t('admin.moduleCourt'), value: 'COURT' },
  { label: t('admin.moduleNews'), value: 'NEWS' },
  { label: t('admin.moduleSystem'), value: 'SYSTEM' }
])

const currentPage = ref(1)
const pageSize = ref(15)

const fetchLogs = async () => {
  isLoading.value = true
  try {
    const params = filterModule.value ? { module: filterModule.value } : {}
    const data = await apiClient.get('/api/logs/activity', { params })
    logs.value = data
    currentPage.value = 1 // Reset về trang 1 khi lọc
  } catch (error) {
    console.error(t('admin.loadLogsError'), error)
  } finally {
    isLoading.value = false
  }
}

const displayLogs = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return logs.value.slice(start, end)
})

onMounted(fetchLogs)

// Hàm parse JSON an toàn để hiển thị
const parseJson = (jsonStr) => {
  if (!jsonStr) return null
  try {
    return JSON.parse(jsonStr)
  } catch (e) {
    return jsonStr // Trả về text gốc nếu không parse được
  }
}

// Format ngày giờ
const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('vi-VN', { 
    hour: '2-digit', minute: '2-digit', second: '2-digit', 
    day: '2-digit', month: '2-digit', year: 'numeric' 
  })
}

// Cấp màu cho các loại hành động
const getActionTagType = (action) => {
  const map = {
    'CREATE': 'success',
    'UPDATE': 'warning',
    'DELETE': 'danger',
    'LOGIN': 'info'
  }
  return map[action?.toUpperCase()] || 'info'
}

// Dịch Event Name từ DB
const translateEvent = (eventName) => {
  if (!eventName) return ''
  const map = {
    'Khởi tạo giải đấu mới': 'admin.eventCreateTournament',
    'Đăng bài viết mới': 'admin.eventCreateNews',
    'Tạo sân thi đấu mới': 'admin.eventCreateCourt',
    'Cập nhật giải đấu': 'admin.eventUpdateTournament',
    'Cập nhật bài viết': 'admin.eventUpdateNews',
    'Cập nhật sân thi đấu': 'admin.eventUpdateCourt',
    'Xóa giải đấu': 'admin.eventDeleteTournament',
    'Xóa bài viết': 'admin.eventDeleteNews',
    'Xóa sân thi đấu': 'admin.eventDeleteCourt'
  }
  return map[eventName] ? t(map[eventName]) : eventName
}
</script>

<template>
  <div class="logs-page">
    <section class="action-bar shadow-sm">
      <div class="action-info">
        <span class="section-kicker">{{ $t('admin.auditTrails') }}</span>
        <p>{{ $t('admin.auditTrailsDesc') }}</p>
      </div>
      
      <div class="hero-actions">
        <el-select 
          v-model="filterModule" 
          :placeholder="$t('admin.filterModulePlaceholder')" 
          style="width: 220px"
          @change="fetchLogs"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
          <el-option 
            v-for="item in modules" 
            :key="item.value" 
            :label="item.label" 
            :value="item.value" 
          />
        </el-select>
        <el-button type="primary" @click="fetchLogs" :icon="Timer">{{ $t('admin.refreshBtn') }}</el-button>
      </div>
    </section>

    <el-card shadow="never" class="table-card">
      <el-table :data="displayLogs" v-loading="isLoading" style="width: 100%" row-key="id">
        <!-- ... (columns remain same) ... -->
        <el-table-column type="expand">
          <template #default="props">
            <div class="expand-detail">
              <div class="detail-grid">
                <div class="data-block">
                  <h4>{{ $t('admin.oldDataTitle') }}</h4>
                  <pre v-if="props.row.old_data">{{ JSON.stringify(parseJson(props.row.old_data), null, 2) }}</pre>
                  <span v-else class="text-muted">{{ $t('admin.noData') }}</span>
                </div>
                
                <div class="data-block">
                  <h4>{{ $t('admin.newDataTitle') }}</h4>
                  <pre v-if="props.row.new_data">{{ JSON.stringify(parseJson(props.row.new_data), null, 2) }}</pre>
                  <span v-else class="text-muted">{{ $t('admin.noData') }}</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.timeCol')" width="180">
          <template #default="scope">
            <span class="time-text">{{ formatDateTime(scope.row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.userCol')" prop="user_name" width="200">
          <template #default="scope">
            <strong>{{ scope.row.user_name }}</strong>
            <div class="ip-text">{{ scope.row.ip_address || 'IP: N/A' }}</div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.moduleCol')" prop="module_name" width="150" />

        <el-table-column :label="$t('admin.actionCol')" width="120">
          <template #default="scope">
            <el-tag :type="getActionTagType(scope.row.action_type)" effect="dark" size="small">
              {{ scope.row.action_type }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.eventDescCol')" min-width="200">
          <template #default="scope">
            {{ translateEvent(scope.row.event_name) }}
          </template>
        </el-table-column>

      </el-table>

      <div class="pagination-footer">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[15, 30, 50]"
          layout="total, sizes, prev, pager, next"
          :total="logs.length"
          background
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.logs-page { display: grid; gap: 24px; padding: 10px; }
.action-bar {
  background: white; padding: 16px 24px; border-radius: 12px;
  display: flex; justify-content: space-between; align-items: center;
  border-left: 5px solid #6366f1; border: 1px solid #eef2f6;
}
.action-info p { color: #64748b; font-size: 0.9rem; margin: 4px 0 0 0; }
.hero-actions { display: flex; gap: 12px; }
.section-kicker { font-size: 0.72rem; font-weight: 800; color: #6366f1; text-transform: uppercase; letter-spacing: 0.05em; }
.shadow-sm { box-shadow: 0 1px 3px rgba(0,0,0,0.05); }

.table-card { border-radius: 16px; border: 1px solid #f0f2f2; }
.pagination-footer { margin-top: 25px; display: flex; justify-content: center; }
.time-text { color: #4e6073; font-size: 0.9rem; }
.ip-text { font-size: 0.75rem; color: #94a3b8; margin-top: 4px; }

/* Khu vực Expand chi tiết JSON */
.expand-detail { padding: 20px 40px; background: #f8fafc; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
.data-block h4 { margin: 0 0 10px 0; color: var(--text-dark); font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.5px; }
.data-block pre { 
  background: #1e293b; color: #a5b4fc; padding: 15px; border-radius: 8px; 
  font-family: 'Consolas', monospace; font-size: 0.85rem; 
  white-space: pre-wrap; word-wrap: break-word; max-height: 300px; overflow-y: auto;
}
.text-muted { color: #94a3b8; font-style: italic; }
</style>