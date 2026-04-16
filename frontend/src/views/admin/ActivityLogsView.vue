<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '../../services/apiClient'
import { Document, Search, Timer } from '@element-plus/icons-vue'

const logs = ref([])
const isLoading = ref(true)
const filterModule = ref('')

// Danh sách các module để filter
const modules = [
  { label: 'Tất cả', value: '' },
  { label: 'Giải đấu (Tournament)', value: 'TOURNAMENT' },
  { label: 'Vận động viên (Player)', value: 'PLAYER' },
  { label: 'Trận đấu (Match)', value: 'MATCH' },
  { label: 'Hệ thống (System)', value: 'SYSTEM' }
]

const fetchLogs = async () => {
  isLoading.value = true
  try {
    const params = filterModule.value ? { module: filterModule.value } : {}
    const data = await apiClient.get('/api/logs/activity', { params })
    logs.value = data
  } catch (error) {
    console.error('Lỗi khi tải lịch sử:', error)
  } finally {
    isLoading.value = false
  }
}

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
</script>

<template>
  <div class="logs-page">
    <div class="page-header">
      <div>
        <h1>Lịch sử hoạt động (Audit Logs)</h1>
        <p>Theo dõi mọi thao tác thay đổi dữ liệu trên hệ thống Saigon Tennis.</p>
      </div>
      
      <div class="filter-actions">
        <el-select 
          v-model="filterModule" 
          placeholder="Lọc theo Module" 
          style="width: 250px"
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
        <el-button type="primary" @click="fetchLogs" :icon="Timer">Làm mới</el-button>
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table :data="logs" v-loading="isLoading" style="width: 100%" row-key="id">
        
        <el-table-column type="expand">
          <template #default="props">
            <div class="expand-detail">
              <div class="detail-grid">
                <div class="data-block">
                  <h4>Dữ liệu cũ (Old Data)</h4>
                  <pre v-if="props.row.old_data">{{ JSON.stringify(parseJson(props.row.old_data), null, 2) }}</pre>
                  <span v-else class="text-muted">Không có dữ liệu</span>
                </div>
                
                <div class="data-block">
                  <h4>Dữ liệu mới (New Data)</h4>
                  <pre v-if="props.row.new_data">{{ JSON.stringify(parseJson(props.row.new_data), null, 2) }}</pre>
                  <span v-else class="text-muted">Không có dữ liệu</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="Thời gian" width="180">
          <template #default="scope">
            <span class="time-text">{{ formatDateTime(scope.row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="Người thực hiện" prop="user_name" width="200">
          <template #default="scope">
            <strong>{{ scope.row.user_name }}</strong>
            <div class="ip-text">{{ scope.row.ip_address || 'IP: N/A' }}</div>
          </template>
        </el-table-column>

        <el-table-column label="Module" prop="module_name" width="150" />

        <el-table-column label="Hành động" width="120">
          <template #default="scope">
            <el-tag :type="getActionTagType(scope.row.action_type)" effect="dark" size="small">
              {{ scope.row.action_type }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="Mô tả chi tiết (Event)" prop="event_name" />

      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.logs-page { padding: 10px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 25px; }
.page-header h1 { font-size: 1.8rem; color: var(--text-dark); margin: 0 0 5px 0; }
.page-header p { color: #6e7a74; margin: 0; }
.filter-actions { display: flex; gap: 15px; }

.table-card { border-radius: 16px; border: 1px solid #f0f2f2; }
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