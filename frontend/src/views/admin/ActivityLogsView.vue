<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '../../services/apiClient'
import { 
  Document, Search, Timer, Monitor, 
  Connection, User, Calendar, InfoFilled,
  VideoPlay, ArrowRight, View, Histogram,
  SuccessFilled as SuccessIcon
} from '@element-plus/icons-vue'
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

const showRawJson = ref({})

const attributeMap = {
  // Common fields
  id: 'ID',
  user_id: 'ID Người thực hiện / VĐV',
  full_name: 'Họ và tên',
  email: 'Email',
  phone: 'Số điện thoại',
  avatar_url: 'Ảnh đại diện',
  province: 'Khu vực/Tỉnh thành',
  date_of_birth: 'Ngày sinh',
  gender: 'Giới tính',
  is_active: 'Trạng thái hoạt động',
  is_verified: 'Đã xác minh',
  role_id: 'ID Vai trò',
  message: 'Thông báo / Kết quả',
  
  // Player specific fields
  play_hand: 'Tay thuận',
  skill_level: 'Trình độ',
  preferred_category: 'Sở trường',
  elo_points: 'Điểm ELO',
  wins: 'Số trận thắng',
  losses: 'Số trận thua',
  matches_played: 'Tổng số trận',
  bio: 'Tiểu sử',
  admin_notes: 'Ghi chú quản trị',
  height_cm: 'Chiều cao (cm)',
  weight_kg: 'Cân nặng (kg)',
  
  // news / tournament / court fields
  title: 'Tiêu đề bài viết',
  summary: 'Tóm tắt bài viết',
  content: 'Nội dung chi tiết',
  status: 'Trạng thái',
  name: 'Tên',
  location: 'Địa điểm',
  court_name: 'Tên sân',
  location_name: 'Vị trí sân',
  surface_type: 'Loại mặt sân',
  entry_fee: 'Lệ phí giải đấu',
  draw_size: 'Quy mô giải đấu',
  start_date: 'Ngày bắt đầu',
  end_date: 'Ngày kết thúc'
}

const formatLogData = (dataStr) => {
  if (!dataStr) return []
  try {
    const dataObj = typeof dataStr === 'object' ? dataStr : JSON.parse(dataStr)
    if (!dataObj || typeof dataObj !== 'object') return []
    
    return Object.entries(dataObj)
      .filter(([key]) => key !== '_sa_instance_state' && key !== 'password_hash')
      .map(([key, val]) => {
        let displayVal = val
        if (val === null || val === undefined) {
          displayVal = 'N/A'
        } else if (typeof val === 'boolean') {
          displayVal = val ? 'Có / Kích hoạt' : 'Không / Khóa'
        } else if (key === 'gender') {
          displayVal = val === 'male' ? 'Nam' : (val === 'female' ? 'Nữ' : val)
        } else if (key === 'play_hand') {
          const hands = { 'right': 'Tay phải', 'left': 'Tay trái', 'both': 'Cả hai tay' }
          displayVal = hands[val] || val
        } else if (key === 'preferred_category') {
          displayVal = val === 'Singles' ? 'Đơn' : (val === 'Doubles' ? 'Đôi' : val)
        } else if (key === 'skill_level') {
          const skills = { 'Beginner': 'Người mới chơi', 'Intermediate': 'Trung bình', 'Advanced': 'Khá/Tốt', 'Professional': 'Chuyên nghiệp' }
          displayVal = skills[val] || val
        }
        
        return {
          key,
          label: attributeMap[key] || key,
          val: displayVal
        }
      })
  } catch (e) {
    return [{ key: 'raw', label: 'Dữ liệu thô', val: dataStr }]
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

// Stats for header
const totalLogs = computed(() => logs.value.length)
const createCount = computed(() => logs.value.filter(l => l.action_type === 'CREATE').length)
const updateCount = computed(() => logs.value.filter(l => l.action_type === 'UPDATE').length)
</script>

<template>
  <div class="saas-container" v-loading="isLoading">
    <!-- Action Bar -->
    <section class="saas-header">
      <div class="header-left">
        <div class="operation-badge-premium purple">
          <el-icon class="mr-1"><Monitor /></el-icon>
          <span>Audit Engine</span>
        </div>
        <div class="header-titles">
          <h2 class="saas-title">{{ $t('admin.auditTrails') }}</h2>
          <p class="saas-subtitle">{{ $t('admin.auditTrailsDesc') }}</p>
        </div>
      </div>
      <div class="header-right">
        <div class="saas-filter-cluster">
          <el-select 
            v-model="filterModule" 
            :placeholder="$t('admin.filterModulePlaceholder')" 
            class="saas-module-filter"
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
          <el-button type="primary" :icon="Timer" @click="fetchLogs" class="saas-btn-action">
            {{ $t('admin.refreshBtn') }}
          </el-button>
        </div>
      </div>
    </section>

    <!-- Mini Stats Grid -->
    <div class="saas-stats-grid-mini">
      <div class="saas-stat-card-mini">
        <div class="mini-icon p-blue"><el-icon><Histogram /></el-icon></div>
        <div class="mini-content">
          <span class="mini-label">Tổng số bản ghi</span>
          <h4 class="mini-value">{{ totalLogs }}</h4>
        </div>
      </div>
      <div class="saas-stat-card-mini">
        <div class="mini-icon p-green"><el-icon><SuccessIcon /></el-icon></div>
        <div class="mini-content">
          <span class="mini-label">Khởi tạo (CREATE)</span>
          <h4 class="mini-value">{{ createCount }}</h4>
        </div>
      </div>
      <div class="saas-stat-card-mini">
        <div class="mini-icon p-orange"><el-icon><VideoPlay /></el-icon></div>
        <div class="mini-content">
          <span class="mini-label">Cập nhật (UPDATE)</span>
          <h4 class="mini-value">{{ updateCount }}</h4>
        </div>
      </div>
    </div>

    <!-- Table Content Area -->
    <main class="saas-content-area">
      <el-table :data="displayLogs" class="saas-table-premium" row-key="id" stripe>
        <!-- JSON Details Expanded -->
        <el-table-column type="expand">
          <template #default="props">
            <div class="audit-expand-viewport">
              <div class="expand-header-saas">
                <div class="header-title-flex">
                  <el-icon class="mr-2"><View /></el-icon>
                  <span>Dữ liệu chi tiết sự thay đổi</span>
                </div>
                <div class="header-toggle-flex">
                  <span class="toggle-label mr-2">Xem JSON gốc:</span>
                  <el-switch
                    v-model="showRawJson[props.row.id]"
                    inline-prompt
                    active-text="Bật"
                    inactive-text="Tắt"
                  />
                </div>
              </div>

              <!-- View Mode: Table (Default) -->
              <div v-if="!showRawJson[props.row.id]" class="audit-details-table-wrap">
                <table class="details-table-premium">
                  <thead>
                    <tr>
                      <th class="col-field">Trường thông tin</th>
                      <th class="col-value">Nội dung ghi nhận</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in formatLogData(props.row.new_data)" :key="item.key">
                      <td class="details-field-label">{{ item.label }}</td>
                      <td class="details-field-value">
                        <!-- Hiển thị ảnh nếu thuộc tính là avatar_url -->
                        <div v-if="item.key === 'avatar_url' && item.val !== 'N/A'" class="avatar-preview-inline">
                          <img :src="item.val" class="inline-avatar-img" />
                          <span class="avatar-link">{{ item.val }}</span>
                        </div>
                        <span v-else>{{ item.val }}</span>
                      </td>
                    </tr>
                    <tr v-if="formatLogData(props.row.new_data).length === 0">
                      <td colspan="2" class="empty-table-details">Không có dữ liệu chi tiết ghi nhận</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- View Mode: Raw JSON -->
              <div v-else class="audit-grid-saas">
                <div class="audit-block-saas">
                  <div class="block-label">Dữ liệu cũ (Old Data)</div>
                  <div class="code-container">
                    <pre v-if="props.row.old_data">{{ JSON.stringify(parseJson(props.row.old_data), null, 2) }}</pre>
                    <div v-else class="empty-code">Không có dữ liệu cũ</div>
                  </div>
                </div>
                
                <div class="audit-block-saas">
                  <div class="block-label highlight">Dữ liệu mới (New Data)</div>
                  <div class="code-container">
                    <pre v-if="props.row.new_data">{{ JSON.stringify(parseJson(props.row.new_data), null, 2) }}</pre>
                    <div v-else class="empty-code">Không có dữ liệu mới</div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- Time Column -->
        <el-table-column :label="$t('admin.timeCol')" width="200">
          <template #default="scope">
            <div class="audit-time-box">
              <el-icon class="mr-1 text-slate-300"><Calendar /></el-icon>
              <span>{{ formatDateTime(scope.row.created_at) }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- User Column -->
        <el-table-column :label="$t('admin.userCol')" width="240">
          <template #default="scope">
            <div class="audit-user-box">
              <el-avatar :size="32" class="saas-avatar-mini">{{ scope.row.user_name?.charAt(0) }}</el-avatar>
              <div class="user-meta">
                <span class="u-name">{{ scope.row.user_name }}</span>
                <span class="u-ip">IP: {{ scope.row.ip_address || 'N/A' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- Module Column -->
        <el-table-column :label="$t('admin.moduleCol')" width="180">
          <template #default="scope">
            <el-tag size="small" effect="plain" class="saas-module-tag">{{ scope.row.module_name }}</el-tag>
          </template>
        </el-table-column>

        <!-- Action Column -->
        <el-table-column :label="$t('admin.actionCol')" width="140">
          <template #default="scope">
            <el-tag :type="getActionTagType(scope.row.action_type)" effect="dark" class="saas-action-badge">
              {{ scope.row.action_type }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- Event Description Column -->
        <el-table-column :label="$t('admin.eventDescCol')" min-width="250">
          <template #default="scope">
            <span class="event-desc-text">{{ translateEvent(scope.row.event_name) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="saas-pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next"
          :total="logs.length"
          background
        />
      </div>
    </main>
  </div>
</template>

<style scoped>
.saas-container { display: flex; flex-direction: column; gap: 32px; min-height: 100%; }

/* Action Bar */
.saas-header { display: flex; align-items: center; justify-content: space-between; gap: 24px; flex-wrap: wrap; }
.header-left { display: flex; align-items: center; }

.operation-badge-premium {
  background: #eff6ff; color: #2563eb; padding: 10px 20px; border-radius: 14px;
  font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
  display: inline-flex; align-items: center; margin-right: 24px;
}
.operation-badge-premium.purple { background: #f5f3ff; color: #7c3aed; }

.header-titles { display: flex; flex-direction: column; gap: 4px; }
.saas-title { font-size: 1.8rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.02em; }
.saas-subtitle { font-size: 0.95rem; color: #64748b; margin: 0; }

.saas-filter-cluster { display: flex; gap: 12px; }
.saas-module-filter { width: 220px; }

:deep(.el-input__wrapper), :deep(.el-select__wrapper) {
  background: #f8fafc !important; border: 1px solid #e2e8f0 !important; border-radius: 12px !important; padding: 10px 16px !important; box-shadow: none !important;
}

.saas-btn-action { height: 48px !important; border-radius: 12px !important; font-weight: 800 !important; padding: 0 20px !important; }

/* Stats Mini */
.saas-stats-grid-mini { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; }
.saas-stat-card-mini {
  background: #fff; border-radius: 20px; padding: 20px; display: flex; align-items: center; gap: 16px;
  border: 1px solid #f1f5f9; transition: all 0.3s;
}
.saas-stat-card-mini:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.03); border-color: #e2e8f0; }

.mini-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.mini-icon.p-blue { background: #eff6ff; color: #3b82f6; }
.mini-icon.p-green { background: #f0fdf4; color: #10b981; }
.mini-icon.p-orange { background: #fff7ed; color: #f97316; }

.mini-label { font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.mini-value { font-size: 1.25rem; font-weight: 900; color: #1e293b; margin: 2px 0 0; }

/* Table Section */
.saas-content-area { background: #fff; border-radius: 32px; border: 1px solid #f1f5f9; box-shadow: 0 10px 40px rgba(0,0,0,0.02); overflow: hidden; padding: 10px; }

:deep(.saas-table-premium) { --el-table-border-color: #f1f5f9; border-radius: 24px; overflow: hidden; }
:deep(.saas-table-premium .el-table__header) { background: #fafafa !important; }
:deep(.saas-table-premium th.el-table__cell) { background: #fafafa !important; font-weight: 800; color: #64748b; font-size: 0.75rem; text-transform: uppercase; padding: 20px 0; border-bottom: 2px solid #f1f5f9; }
:deep(.saas-table-premium td.el-table__cell) { padding: 16px 0; }

.audit-time-box { font-size: 0.9rem; font-weight: 600; color: #475569; display: flex; align-items: center; }

.audit-user-box { display: flex; align-items: center; gap: 12px; }
.saas-avatar-mini { background: #f1f5f9; color: #64748b; font-weight: 800; border: 2px solid #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
.user-meta { display: flex; flex-direction: column; gap: 2px; }
.u-name { font-weight: 800; color: #1e293b; font-size: 0.95rem; }
.u-ip { font-size: 0.75rem; color: #94a3b8; font-family: monospace; }

.saas-module-tag { border-radius: 8px; font-weight: 800; font-size: 0.7rem; letter-spacing: 0.02em; padding: 4px 10px; background: #f8fafc; border: 1px solid #e2e8f0; color: #64748b; }
.saas-action-badge { border-radius: 8px; font-weight: 900; font-size: 0.7rem; letter-spacing: 0.05em; padding: 4px 12px; min-width: 80px; text-align: center; }

.event-desc-text { font-weight: 600; color: #334155; font-size: 0.9rem; }

/* Expanded Audit Details */
.audit-expand-viewport { padding: 32px; background: #fafafa; border-radius: 24px; margin: 10px; border: 1px solid #f1f5f9; }
.expand-header-saas {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 900;
  color: #1e293b;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  width: 100%;
}

.header-title-flex {
  display: flex;
  align-items: center;
}

.header-toggle-flex {
  display: flex;
  align-items: center;
}

.toggle-label {
  font-size: 0.8rem;
  color: #64748b;
  text-transform: none;
  font-weight: 700;
}

.audit-details-table-wrap {
  background: #ffffff;
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
  overflow: hidden;
  padding: 8px;
}

.details-table-premium {
  width: 100%;
  border-collapse: collapse;
}

.details-table-premium th {
  background: #f8fafc;
  color: #475569;
  font-weight: 800;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-align: left;
  padding: 12px 20px;
  border-bottom: 2px solid #e2e8f0;
}

.details-table-premium td {
  padding: 14px 20px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  font-size: 0.9rem;
}

.details-table-premium tr:last-child td {
  border-bottom: none;
}

.details-field-label {
  font-weight: 700;
  color: #0f172a;
  width: 30%;
}

.details-field-value {
  font-weight: 500;
  color: #475569;
  word-break: break-all;
}

.empty-table-details {
  text-align: center;
  color: #94a3b8;
  font-style: italic;
  padding: 24px 0 !important;
}

.avatar-preview-inline {
  display: flex;
  align-items: center;
  gap: 12px;
}

.inline-avatar-img {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  object-fit: cover;
  border: 1px solid #e2e8f0;
}

.avatar-link {
  font-size: 0.8rem;
  color: #94a3b8;
  font-family: monospace;
}

.audit-grid-saas { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
.audit-block-saas { display: flex; flex-direction: column; gap: 12px; }

.block-label { font-size: 0.75rem; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; display: flex; align-items: center; gap: 8px; }
.block-label.highlight { color: #2563eb; }

.code-container { background: #0f172a; border-radius: 20px; padding: 24px; border: 1px solid #1e293b; box-shadow: inset 0 2px 10px rgba(0,0,0,0.2); }
.code-container pre { margin: 0; color: #38bdf8; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 0.85rem; line-height: 1.6; white-space: pre-wrap; word-break: break-all; max-height: 400px; overflow-y: auto; }
.empty-code { color: #475569; font-style: italic; font-size: 0.9rem; text-align: center; padding: 20px 0; }

.saas-pagination-wrap { padding: 32px; display: flex; justify-content: center; background: #fff; border-top: 1px solid #f1f5f9; }

/* Utility */
.mr-1 { margin-right: 4px; }
.mr-2 { margin-right: 8px; }
.text-slate-300 { color: #cbd5e1; }
</style>