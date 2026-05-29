<script setup>
import { onMounted, ref, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { playerService } from '../../services/playerService'
import apiClient from '../../services/apiClient' 
import { Plus, Camera, User, Search, Filter, EditPen, Delete } from '@element-plus/icons-vue' 
import { t } from '../../utils/locale'
import { useRoute } from 'vue-router'

const route = useRoute()

const players = ref([])
const loading = ref(false)
const isSaving = ref(false)
const search = ref('')
const skillFilter = ref('')
const statusFilter = ref('')

const createErrors = ref({
  email: '',
  phone: ''
})

const editErrors = ref({
  phone: ''
})

const playerStatDefaults = {
  aces: 0,
  double_faults: 0,
  first_serve_pct: 0,
  first_serve_points_won_pct: 0,
  second_serve_points_won_pct: 0,
  break_points_faced: 0,
  break_points_saved_pct: 0,
  service_games_played: 0,
  service_games_won_pct: 0,
  total_service_points_won_pct: 0,
  first_serve_return_points_won_pct: 0,
  second_serve_return_points_won_pct: 0,
  break_points_opportunities: 0,
  break_points_converted_pct: 0,
  return_games_played: 0,
  return_games_won_pct: 0,
  return_points_won_pct: 0,
  total_points_won_pct: 0
}

const playerStatGroups = [
  {
    title: 'Giao bóng',
    subtitle: 'Serve',
    description: 'Các chỉ số khi vận động viên cầm giao bóng.',
    fields: [
      ['aces', 'Giao bóng ăn điểm trực tiếp', 'Aces', 'count'],
      ['double_faults', 'Lỗi giao bóng kép', 'Double Faults', 'count'],
      ['first_serve_pct', 'Tỷ lệ giao bóng 1 vào sân', '1st Serve', 'percent'],
      ['first_serve_points_won_pct', 'Điểm thắng khi giao bóng 1', '1st Serve Points Won', 'percent'],
      ['second_serve_points_won_pct', 'Điểm thắng khi giao bóng 2', '2nd Serve Points Won', 'percent'],
      ['break_points_faced', 'Số break point phải đối mặt', 'Break Points Faced', 'count'],
      ['break_points_saved_pct', 'Tỷ lệ cứu break point', 'Break Points Saved', 'percent'],
      ['service_games_played', 'Số game giao bóng đã chơi', 'Service Games Played', 'count'],
      ['service_games_won_pct', 'Tỷ lệ thắng game giao bóng', 'Service Games Won', 'percent'],
      ['total_service_points_won_pct', 'Tổng điểm thắng khi giao bóng', 'Total Service Points Won', 'percent']
    ]
  },
  {
    title: 'Trả giao bóng',
    subtitle: 'Return',
    description: 'Các chỉ số khi vận động viên đỡ/trả giao bóng.',
    fields: [
      ['first_serve_return_points_won_pct', 'Điểm thắng khi trả giao bóng 1', '1st Serve Return Points Won', 'percent'],
      ['second_serve_return_points_won_pct', 'Điểm thắng khi trả giao bóng 2', '2nd Serve Return Points Won', 'percent'],
      ['break_points_opportunities', 'Cơ hội bẻ game', 'Break Points Opportunities', 'count'],
      ['break_points_converted_pct', 'Tỷ lệ tận dụng break point', 'Break Points Converted', 'percent'],
      ['return_games_played', 'Số game trả giao bóng đã chơi', 'Return Games Played', 'count'],
      ['return_games_won_pct', 'Tỷ lệ thắng game trả giao bóng', 'Return Games Won', 'percent'],
      ['return_points_won_pct', 'Tỷ lệ thắng điểm trả giao bóng', 'Return Points Won', 'percent'],
      ['total_points_won_pct', 'Tổng tỷ lệ điểm thắng', 'Total Points Won', 'percent']
    ]
  }
]

const validateEmail = (email) => {
  if (!email) return 'Email không được để trống'
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) return 'Vui lòng nhập đúng định dạng email '
  return ''
}

const validatePhone = (phone) => {
  if (!phone) return 'Số điện thoại không được để trống'
  const cleaned = phone.replace(/[\s\-\(\)]/g, '')
  if (!cleaned.startsWith('0')) return 'Số điện thoại phải bắt đầu bằng số 0'
  if (cleaned.length !== 10) return 'Số điện thoại phải nhập đủ 10 chữ số'
  const phoneRegex = /^0[35789][0-9]{8}$/
  if (!phoneRegex.test(cleaned)) return 'Số điện thoại không hợp lệ'
  return ''
}

const removeVietnameseTones = (str) => {
  if (!str) return ''
  return str
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLowerCase()
}

const filteredPlayers = computed(() => {
  if (!search.value.trim()) {
    return players.value
  }
  const searchNormalized = removeVietnameseTones(search.value.trim())
  return players.value.filter(player => {
    const fullNameNormalized = removeVietnameseTones(player.user?.full_name || '')
    const emailNormalized = removeVietnameseTones(player.user?.email || '')
    const phoneNormalized = removeVietnameseTones(player.user?.phone || '')
    return fullNameNormalized.includes(searchNormalized) || 
           emailNormalized.includes(searchNormalized) || 
           phoneNormalized.includes(searchNormalized)
  })
})

const disabledDate = (time) => {
  return time.getTime() > Date.now()
}

const isEditDialogVisible = ref(false)
const editForm = ref({
  id: null,
  full_name: '',
  phone: '',
  gender: 'male',
  play_hand: 'right',
  skill_level: 'Beginner',
  preferred_category: 'Singles',
  province: '',
  date_of_birth: null, 
  elo_points: 1000,
  height_cm: null,
  weight_kg: null,
  avatar_url: '',
  is_active: true,
  admin_notes: '',
  ...playerStatDefaults
})

const isCreateDialogVisible = ref(false)
const isCreating = ref(false)
const createForm = ref({
  full_name: '', email: '', password: '', phone: '', 
  gender: 'male', play_hand: 'right', account_type: 'user', 
  otp_code: 'bypass_otp',
  avatar_url: '', 
  skill_level: 'Beginner',
  preferred_category: 'Singles',
  province: '',
  date_of_birth: null, 
  elo_points: 1000,
  height_cm: null,
  weight_kg: null,
  admin_notes: '',
  ...playerStatDefaults
})

const isUploading = ref(false)

const handleImageUpload = async (event, formType) => {
  const file = event.target.files[0]
  if (!file) return
  
  if (file.size > 2 * 1024 * 1024) {
    return ElMessage.error('Kích thước ảnh không được vượt quá 2MB')
  }

  const formData = new FormData()
  formData.append('file', file)

  isUploading.value = true
  try {
    const response = await apiClient.post('/api/players/upload-avatar', formData)
    const uploadedUrl = response.data?.avatar_url || response.avatar_url || response.data?.url || response.url
    
    if (formType === 'create') {
      createForm.value.avatar_url = uploadedUrl
    } else {
      editForm.value.avatar_url = uploadedUrl
    }
    ElMessage.success('Tải ảnh lên thành công!')
  } catch (err) {
    ElMessage.error('Lỗi khi tải ảnh: ' + (err.response?.data?.detail || err.message))
  } finally {
    isUploading.value = false
  }
}

const fetchPlayers = async () => {
  loading.value = true
  try {
    const params = {
      skill: skillFilter.value || undefined,
      status: statusFilter.value || undefined
    }
    const data = await playerService.getAll(params)
    players.value = Array.isArray(data) ? data : (data.items || [])
  } catch (err) {
    ElMessage.error(t('admin.loadPlayersError') + ': ' + err.message)
  } finally {
    loading.value = false
  }
}

// Debounced search watcher for all filters
let filterTimeout = null
watch([skillFilter, statusFilter], () => {
  if (filterTimeout) clearTimeout(filterTimeout)
  filterTimeout = setTimeout(() => {
    fetchPlayers()
  }, 300)
})

// Force data refresh when navigating back to this page
watch(() => route.path, (newPath) => {
  if (newPath === '/admin/players') {
    fetchPlayers()
  }
})

const openEditDialog = (player) => {
  editErrors.value = { phone: '' }
  editForm.value = {
    id: player.id,
    full_name: player.user.full_name,
    phone: player.user.phone || '',
    gender: player.player_profile?.gender || 'male',
    play_hand: player.player_profile?.play_hand || 'right',
    skill_level: player.player_profile?.skill_level || 'Beginner',
    preferred_category: player.player_profile?.preferred_category || 'Singles',
    province: player.player_profile?.province || '',
    date_of_birth: player.player_profile?.date_of_birth || null,
    elo_points: player.player_profile?.elo_points || 1000,
    height_cm: player.player_profile?.height_cm || null,
    weight_kg: player.player_profile?.weight_kg || null,
    avatar_url: player.user.avatar_url || '',
    is_active: player.user.is_active,
    admin_notes: player.player_profile?.admin_notes || '',
    ...Object.fromEntries(
      Object.keys(playerStatDefaults).map(key => [key, player.player_profile?.[key] ?? 0])
    )
  }
  isEditDialogVisible.value = true
}

const openCreateDialog = () => {
  createErrors.value = { email: '', phone: '' }
  createForm.value = { 
    full_name: '', email: '', password: '', phone: '', 
    gender: 'male', play_hand: 'right', account_type: 'user', 
    otp_code: 'bypass_otp',
    avatar_url: '', skill_level: 'Beginner', preferred_category: 'Singles',
    province: '', date_of_birth: null, elo_points: 1000,
    height_cm: null, weight_kg: null,
    ...playerStatDefaults
  }
  isCreateDialogVisible.value = true
}

const handleCreatePlayer = async () => {
  createErrors.value.email = validateEmail(createForm.value.email)
  createErrors.value.phone = validatePhone(createForm.value.phone)

  if (!createForm.value.full_name || !createForm.value.password) {
    ElMessage.warning('Vui lòng điền đủ Họ tên và Mật khẩu!')
    return
  }

  if (createErrors.value.email || createErrors.value.phone) {
    ElMessage.error('Vui lòng sửa các lỗi trong form trước khi lưu!')
    return
  }

  isCreating.value = true
  try {
    const payload = { ...createForm.value }
    payload.phone = payload.phone.replace(/[\s\-\(\)]/g, '')
    if (!payload.date_of_birth) payload.date_of_birth = null

    await apiClient.post('/api/players/admin-create', payload)
    ElMessage.success('Đã tạo tài khoản VĐV thành công!')
    isCreateDialogVisible.value = false
    fetchPlayers() 
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || 'Lỗi khi tạo tài khoản')
  } finally {
    isCreating.value = false
  }
}

const handleUpdatePlayer = async () => {
  editErrors.value.phone = validatePhone(editForm.value.phone)

  if (editErrors.value.phone) {
    ElMessage.error('Vui lòng sửa các lỗi trong form trước khi lưu!')
    return
  }

  isSaving.value = true
  try {
    const payload = { ...editForm.value }
    payload.phone = payload.phone.replace(/[\s\-\(\)]/g, '')
    if (!payload.date_of_birth) payload.date_of_birth = null

    await playerService.update(payload.id, payload)
    ElMessage.success(t('admin.updateSuccess'))
    isEditDialogVisible.value = false
    fetchPlayers()
  } catch (err) {
    ElMessage.error(t('admin.updateError') + ': ' + err.message)
  } finally {
    isSaving.value = false
  }
}

const deletePlayer = async (row) => {
  try {
    await ElMessageBox.confirm(
      `Bạn có chắc chắn muốn xóa vận động viên ${row.user?.full_name}? Việc này sẽ không xóa các dữ liệu thi đấu lịch sử nhưng tài khoản của vận động viên sẽ bị vô hiệu hóa.`,
      'Xác nhận xóa',
      {
        confirmButtonText: 'Đồng ý',
        cancelButtonText: 'Hủy',
        type: 'warning',
      }
    )
    await playerService.delete(row.user.id)
    ElMessage.success('Đã xóa vận động viên thành công!')
    fetchPlayers()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || 'Lỗi khi xóa vận động viên')
    }
  }
}

const formatSkillLevel = (val) => {
  const map = { 
    'Beginner': t('admin.beginner'), 
    'Intermediate': t('admin.intermediate'), 
    'Advanced': t('admin.advanced'), 
    'Professional': t('admin.professional') 
  }
  return map[val] || val || 'N/A'
}

const formatPhone = (val) => {
  if (!val) return 'N/A'
  // Remove all non-numeric characters
  const cleaned = ('' + val).replace(/\D/g, '')
  // Match groups for XXX XXX XXXX
  const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/)
  if (match) {
    return `${match[1]} ${match[2]} ${match[3]}`
  }
  // Fallback for other lengths
  if (cleaned.length === 10) {
    return cleaned.slice(0, 3) + ' ' + cleaned.slice(3, 6) + ' ' + cleaned.slice(6)
  }
  return val
}

const formatElo = (val) => {
  if (val === null || val === undefined) return '0'
  return val.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

const formatPlayerStatValue = (value, type) => {
  const numericValue = Number(value ?? 0)
  if (type === 'percent') {
    return `${numericValue.toFixed(2).replace(/\.00$/, '')}%`
  }
  return formatElo(Number.isNaN(numericValue) ? 0 : numericValue)
}

const getPlayerStatProgress = (value, type) => {
  if (type !== 'percent') return null
  const numericValue = Number(value ?? 0)
  if (Number.isNaN(numericValue)) return 0
  return Math.min(Math.max(numericValue, 0), 100)
}

const formatPlayHand = (hand) => {
  if (hand === 'right') return 'Tay phải'
  if (hand === 'left') return 'Tay trái'
  if (hand === 'both') return 'Cả hai tay'
  return 'Chưa cập nhật'
}

const getBirthYear = (dob) => {
  if (!dob) return 'Chưa cập nhật'
  try {
    return new Date(dob).getFullYear()
  } catch (e) {
    return '---'
  }
}

onMounted(fetchPlayers)

const getSkillType = (skill) => {
  if (skill === 'Professional') return 'danger'
  if (skill === 'Advanced') return 'warning'
  if (skill === 'Intermediate') return 'success'
  return 'info'
}

// --- PLAYER DETAILS LOGIC ---
const isDetailDialogVisible = ref(false)
const selectedPlayer = ref(null)
const matchHistory = ref([])
const tournamentList = ref([])
const detailsLoading = ref(false)

const selectedPlayerStatGroups = computed(() => {
  const profile = selectedPlayer.value?.player_profile || {}
  return playerStatGroups.map(group => ({
    ...group,
    fields: group.fields.map(([key, label, englishLabel, type]) => ({
      key,
      label,
      englishLabel,
      type,
      value: profile[key] ?? 0,
      progress: getPlayerStatProgress(profile[key], type)
    }))
  }))
})

const openDetailDialog = async (player) => {
  selectedPlayer.value = player
  isDetailDialogVisible.value = true
  detailsLoading.value = true
  
  try {
    const [history, tournaments] = await Promise.all([
      playerService.getMatchHistoryAdmin(player.id),
      playerService.getTournamentsAdmin(player.id)
    ])
    matchHistory.value = history
    tournamentList.value = tournaments
  } catch (err) {
    ElMessage.error('Lỗi khi tải thông tin chi tiết: ' + err.message)
  } finally {
    detailsLoading.value = false
  }
}

const getResultTagType = (status) => {
  if (status === 'THẮNG') return 'success'
  if (status === 'THUA') return 'danger'
  return 'info'
}

const getRegStatusType = (status) => {
  if (status === 'confirmed' || status === 'checked_in') return 'success'
  if (status === 'pending') return 'warning'
  return 'info'
}
</script>

<template>
  <div class="saas-container">
    <!-- Action Header -->
    <div class="saas-header">
      <div class="header-left">
        <el-input 
          v-model="search" 
          :placeholder="$t('admin.searchPlayersPlaceholder')" 
          clearable 
          class="saas-search"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select v-model="skillFilter" :placeholder="$t('admin.skillLevel')" clearable class="saas-filter">
          <template #prefix>
            <el-icon><Filter /></el-icon>
          </template>
          <el-option v-for="s in ['Beginner', 'Intermediate', 'Advanced', 'Professional']" :key="s" :label="formatSkillLevel(s)" :value="s" />
        </el-select>

        <el-select v-model="statusFilter" :placeholder="$t('admin.status')" clearable class="saas-filter">
          <el-option :label="$t('admin.active')" value="active" />
          <el-option :label="$t('admin.locked')" value="inactive" />
        </el-select>
      </div>

      <div class="header-right">
        <el-button type="primary" @click="openCreateDialog" class="saas-btn-create">
          <el-icon><Plus /></el-icon> {{ $t('admin.createPlayer') }}
        </el-button>
      </div>
    </div>

    <!-- Data Table Section -->
    <div class="saas-content">
      <el-table 
        :data="filteredPlayers" 
        v-loading="loading" 
        class="saas-table"
        :header-cell-style="{ background: 'transparent', color: '#64748b', fontWeight: '700', borderBottom: '2px solid #f1f5f9' }"
        :cell-style="{ background: 'transparent' }"
      >
        <el-table-column :label="$t('admin.player')" min-width="250">
          <template #default="{ row }">
            <div class="saas-user-cell clickable" @click="openDetailDialog(row)">
              <div class="saas-avatar">
                <img 
                  :src="row.user.avatar_url || `https://ui-avatars.com/api/?name=${row.user.full_name}&background=f1f5f9&color=64748b`" 
                  @error="$event.target.src = `https://ui-avatars.com/api/?name=${row.user.full_name}&background=f1f5f9&color=64748b`"
                  referrerpolicy="no-referrer"
                />
              </div>
              <div class="saas-user-meta">
                <span class="user-name">{{ row.user.full_name }}</span>
                <span class="user-email">{{ row.user.email }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.phone')" width="140">
          <template #default="{ row }">
            {{ formatPhone(row.user.phone) }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.skillLevel')" width="160">
          <template #default="{ row }">
            <el-tag 
              :type="getSkillType(row.player_profile?.skill_level)" 
              effect="light" 
              class="saas-tag"
            >
              {{ formatSkillLevel(row.player_profile?.skill_level) }}
            </el-tag>
          </template>
        </el-table-column>

         <el-table-column :label="$t('admin.elo')" width="100" align="center">
            <template #default="{ row }">
              <span class="elo-badge">{{ formatElo(row.player_profile?.elo_points || 1000) }}</span>
            </template>
         </el-table-column>

        <el-table-column :label="$t('admin.accountStatus')" width="140">
           <template #default="{ row }">
             <div class="status-indicator" :class="{ 'is-active': row.user.is_active }">
               <span class="dot"></span>
               <span>{{ row.user.is_active ? $t('admin.active') : $t('admin.locked') }}</span>
             </div>
           </template>
        </el-table-column>

        <el-table-column :label="$t('admin.action')" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button 
                size="small" 
                circle
                type="info" 
                @click="openDetailDialog(row)"
                title="Xem chi tiết"
              >
                <el-icon><User /></el-icon>
              </el-button>
              <el-button 
                size="small" 
                type="primary" 
                @click="openEditDialog(row)"
                class="saas-edit-btn"
              >
                <el-icon><EditPen /></el-icon>
                <span>{{ $t('admin.edit') }}</span>
              </el-button>
              <el-button 
                size="small" 
                type="danger" 
                circle
                @click="deletePlayer(row)"
                title="Xóa vận động viên"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Dialogs -->
    <el-dialog v-model="isCreateDialogVisible" :title="$t('admin.createNewPlayer')" width="980px" class="saas-dialog player-editor-dialog">
      <el-form label-position="top">
        <el-tabs class="player-editor-tabs">
          <el-tab-pane label="Thông tin cơ bản">
            <div class="editor-intro">
              <div>
                <strong>Hồ sơ vận động viên</strong>
                <p>Thông tin nhận diện, trình độ và trạng thái xếp hạng ban đầu.</p>
              </div>
            </div>

        <div class="saas-upload-zone compact-upload">
          <div class="avatar-preview-box">
            <img v-if="createForm.avatar_url" :src="createForm.avatar_url" />
            <el-icon v-else><User /></el-icon>
            <label class="hover-overlay">
              <input type="file" hidden @change="e => handleImageUpload(e, 'create')" accept="image/*" />
              <el-icon><Camera /></el-icon>
            </label>
          </div>
          <span class="upload-hint">{{ $t('admin.clickToUpload') }}</span>
        </div>

        <el-row :gutter="24">
          <el-col :span="12"><el-form-item :label="$t('admin.fullName')"><el-input v-model="createForm.full_name" placeholder="Ví dụ: Nguyễn Văn A" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="$t('admin.email')" :error="createErrors.email"><el-input v-model="createForm.email" placeholder="email@example.com" @input="createErrors.email = ''" @blur="createErrors.email = validateEmail(createForm.email)" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="$t('admin.password')"><el-input v-model="createForm.password" type="password" show-password /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="$t('admin.phone')" :error="createErrors.phone"><el-input v-model="createForm.phone" placeholder="Ví dụ: 0987654321" @input="createErrors.phone = ''" @blur="createErrors.phone = validatePhone(createForm.phone)" /></el-form-item></el-col>
          <el-col :span="8">
            <el-form-item :label="$t('admin.skillLevel')">
              <el-select v-model="createForm.skill_level" style="width: 100%">
                <el-option v-for="s in ['Beginner', 'Intermediate', 'Advanced', 'Professional']" :key="s" :label="formatSkillLevel(s)" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item :label="$t('admin.preferredCategory')">
              <el-select v-model="createForm.preferred_category" style="width: 100%">
                <el-option :label="$t('admin.singles')" value="Singles" />
                <el-option :label="$t('admin.doubles')" value="Doubles" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8"><el-form-item :label="$t('admin.elo')"><el-input-number v-model="createForm.elo_points" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="$t('admin.province')"><el-input v-model="createForm.province" /></el-form-item></el-col>
          <el-col :span="12">
            <el-form-item :label="$t('admin.dob')">
              <el-date-picker v-model="createForm.date_of_birth" type="date" format="DD/MM/YYYY" value-format="YYYY-MM-DD" style="width: 100%" :disabled-date="disabledDate" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Tay thuận">
              <el-select v-model="createForm.play_hand" style="width: 100%">
                <el-option label="Tay phải" value="right" />
                <el-option label="Tay trái" value="left" />
                <el-option label="Cả hai tay" value="both" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Chiều cao (cm)">
              <el-input-number v-model="createForm.height_cm" :min="80" :max="250" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Cân nặng (kg)">
              <el-input-number v-model="createForm.weight_kg" :min="25" :max="250" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="Đánh giá / Ghi chú của Ban quản trị">
              <el-input type="textarea" v-model="createForm.admin_notes" :rows="3" placeholder="Nhập đánh giá, ghi chú hoặc thông tin từ ban quản trị..." />
            </el-form-item>
          </el-col>
        </el-row>

          </el-tab-pane>

          <el-tab-pane label="Chỉ số ATP">
            <div class="editor-intro">
              <div>
                <strong>Bảng thống kê thi đấu</strong>
                <p>Nhập chỉ số đếm hoặc tỷ lệ %. Có thể để 0 nếu chưa có dữ liệu chính thức.</p>
              </div>
            </div>

        <div class="stats-editor">
          <section v-for="group in playerStatGroups" :key="group.title" class="stats-group">
            <div class="stats-group-head">
              <div>
                <h4>{{ group.title }}</h4>
                <span>{{ group.subtitle }}</span>
              </div>
              <p>{{ group.description }}</p>
            </div>
            <div class="stat-field-grid">
              <el-form-item v-for="[key, viLabel, enLabel, type] in group.fields" :key="key">
                <template #label>
                  <span class="field-label">
                    <strong>{{ viLabel }}</strong>
                    <small>{{ enLabel }}</small>
                  </span>
                </template>
                  <el-input-number
                    v-model="createForm[key]"
                    :min="0"
                    :max="type === 'percent' ? 100 : undefined"
                    :precision="type === 'percent' ? 2 : 0"
                    :step="type === 'percent' ? 0.1 : 1"
                    :controls-position="'right'"
                    style="width: 100%"
                  />
                  <span class="field-unit">{{ type === 'percent' ? '%' : 'lần' }}</span>
              </el-form-item>
            </div>
          </section>
        </div>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      <template #footer>
        <el-button @click="isCreateDialogVisible = false" class="saas-btn-secondary">{{ $t('admin.cancel') }}</el-button>
        <el-button type="primary" :loading="isCreating" @click="handleCreatePlayer" class="saas-btn-primary">{{ $t('admin.confirmCreate') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="isEditDialogVisible" :title="$t('admin.editPlayerProfile')" width="980px" class="saas-dialog player-editor-dialog">
      <el-form label-position="top">
        <el-tabs class="player-editor-tabs">
          <el-tab-pane label="Thông tin cơ bản">
            <div class="editor-intro">
              <div>
                <strong>Hồ sơ vận động viên</strong>
                <p>Cập nhật thông tin cá nhân, trình độ và trạng thái tài khoản.</p>
              </div>
            </div>

        <div class="saas-upload-zone compact-upload">
          <div class="avatar-preview-box">
            <img v-if="editForm.avatar_url" :src="editForm.avatar_url" />
            <el-icon v-else><User /></el-icon>
            <label class="hover-overlay">
              <input type="file" hidden @change="e => handleImageUpload(e, 'edit')" accept="image/*" />
              <el-icon><Camera /></el-icon>
            </label>
          </div>
          <span class="upload-hint">{{ $t('admin.clickToChange') }}</span>
        </div>

        <el-row :gutter="24">
          <el-col :span="12"><el-form-item :label="$t('admin.fullName')"><el-input v-model="editForm.full_name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="$t('admin.phone')" :error="editErrors.phone"><el-input v-model="editForm.phone" @input="editErrors.phone = ''" @blur="editErrors.phone = validatePhone(editForm.phone)" /></el-form-item></el-col>
          <el-col :span="8">
            <el-form-item :label="$t('admin.skillLevel')">
              <el-select v-model="editForm.skill_level" style="width: 100%">
                <el-option v-for="s in ['Beginner', 'Intermediate', 'Advanced', 'Professional']" :key="s" :label="formatSkillLevel(s)" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item :label="$t('admin.preferredCategory')">
              <el-select v-model="editForm.preferred_category" style="width: 100%">
                <el-option :label="$t('admin.singles')" value="Singles" />
                <el-option :label="$t('admin.doubles')" value="Doubles" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8"><el-form-item :label="$t('admin.elo')"><el-input-number v-model="editForm.elo_points" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="$t('admin.province')"><el-input v-model="editForm.province" /></el-form-item></el-col>
          <el-col :span="12">
            <el-form-item :label="$t('admin.dob')">
              <el-date-picker v-model="editForm.date_of_birth" type="date" format="DD/MM/YYYY" value-format="YYYY-MM-DD" style="width: 100%" :disabled-date="disabledDate" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Tay thuận">
              <el-select v-model="editForm.play_hand" style="width: 100%">
                <el-option label="Tay phải" value="right" />
                <el-option label="Tay trái" value="left" />
                <el-option label="Cả hai tay" value="both" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Chiều cao (cm)">
              <el-input-number v-model="editForm.height_cm" :min="80" :max="250" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Cân nặng (kg)">
              <el-input-number v-model="editForm.weight_kg" :min="25" :max="250" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('admin.gender')">
              <el-radio-group v-model="editForm.gender">
                <el-radio value="male">{{ $t('admin.male') }}</el-radio>
                <el-radio value="female">{{ $t('admin.female') }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('admin.accountStatus')">
              <el-switch v-model="editForm.is_active" inline-prompt :active-text="$t('admin.active')" :inactive-text="$t('admin.locked')" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="Đánh giá / Ghi chú của Ban quản trị">
              <el-input type="textarea" v-model="editForm.admin_notes" :rows="3" placeholder="Nhập đánh giá, ghi chú hoặc thông tin từ ban quản trị..." />
            </el-form-item>
          </el-col>
        </el-row>

          </el-tab-pane>

          <el-tab-pane label="Chỉ số ATP">
            <div class="editor-intro">
              <div>
                <strong>Bảng thống kê thi đấu</strong>
                <p>Các chỉ số này sẽ hiển thị ở tab Stats của hồ sơ vận động viên.</p>
              </div>
            </div>

        <div class="stats-editor">
          <section v-for="group in playerStatGroups" :key="group.title" class="stats-group">
            <div class="stats-group-head">
              <div>
                <h4>{{ group.title }}</h4>
                <span>{{ group.subtitle }}</span>
              </div>
              <p>{{ group.description }}</p>
            </div>
            <div class="stat-field-grid">
              <el-form-item v-for="[key, viLabel, enLabel, type] in group.fields" :key="key">
                <template #label>
                  <span class="field-label">
                    <strong>{{ viLabel }}</strong>
                    <small>{{ enLabel }}</small>
                  </span>
                </template>
                  <el-input-number
                    v-model="editForm[key]"
                    :min="0"
                    :max="type === 'percent' ? 100 : undefined"
                    :precision="type === 'percent' ? 2 : 0"
                    :step="type === 'percent' ? 0.1 : 1"
                    :controls-position="'right'"
                    style="width: 100%"
                  />
                  <span class="field-unit">{{ type === 'percent' ? '%' : 'lần' }}</span>
              </el-form-item>
            </div>
          </section>
        </div>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      <template #footer>
        <el-button @click="isEditDialogVisible = false" class="saas-btn-secondary">{{ $t('admin.cancel') }}</el-button>
        <el-button type="primary" :loading="isSaving" @click="handleUpdatePlayer" class="saas-btn-primary">{{ $t('admin.saveChanges') }}</el-button>
      </template>
    </el-dialog>

    <!-- PLAYER DETAILS DIALOG -->
    <el-dialog v-model="isDetailDialogVisible" width="980px" class="saas-dialog detail-dialog" destroy-on-close>
      <template #header>
        <div class="detail-header">
          <div class="player-info-brief" v-if="selectedPlayer">
            <div class="saas-avatar large">
              <img 
                :src="selectedPlayer.user.avatar_url || `https://ui-avatars.com/api/?name=${selectedPlayer.user.full_name}&background=f1f5f9&color=64748b`" 
                referrerpolicy="no-referrer"
              />
            </div>
            <div class="meta">
              <h3>{{ selectedPlayer.user.full_name }}</h3>
              <div class="badges">
                <el-tag size="small" :type="getSkillType(selectedPlayer.player_profile?.skill_level)">{{ formatSkillLevel(selectedPlayer.player_profile?.skill_level) }}</el-tag>
                <span class="elo-val">ELO: {{ formatElo(selectedPlayer.player_profile?.elo_points) }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <el-tabs type="border-card" class="detail-tabs" v-loading="detailsLoading">
        <el-tab-pane label="Thông tin cá nhân & Ghi chú">
          <el-descriptions :column="2" border size="small" v-if="selectedPlayer">
            <el-descriptions-item label="Họ và tên">{{ selectedPlayer.user.full_name }}</el-descriptions-item>
            <el-descriptions-item label="Số điện thoại">{{ formatPhone(selectedPlayer.user.phone) }}</el-descriptions-item>
            <el-descriptions-item label="Email">{{ selectedPlayer.user.email }}</el-descriptions-item>
            <el-descriptions-item label="Năm sinh">{{ getBirthYear(selectedPlayer.player_profile?.date_of_birth || selectedPlayer.user.date_of_birth) }}</el-descriptions-item>
            <el-descriptions-item label="Câu lạc bộ hoạt động">{{ selectedPlayer.user.province || 'Chưa cập nhật' }}</el-descriptions-item>
            <el-descriptions-item label="Tay thuận">{{ formatPlayHand(selectedPlayer.player_profile?.play_hand) }}</el-descriptions-item>
            <el-descriptions-item label="Trình độ">{{ formatSkillLevel(selectedPlayer.player_profile?.skill_level) }}</el-descriptions-item>
            <el-descriptions-item label="Sở trường">{{ selectedPlayer.player_profile?.preferred_category === 'Singles' ? 'Đơn' : (selectedPlayer.player_profile?.preferred_category === 'Doubles' ? 'Đôi' : 'Chưa cập nhật') }}</el-descriptions-item>
            <el-descriptions-item label="Chiều cao">{{ selectedPlayer.player_profile?.height_cm ? selectedPlayer.player_profile.height_cm + ' cm' : 'Chưa cập nhật' }}</el-descriptions-item>
            <el-descriptions-item label="Cân nặng">{{ selectedPlayer.player_profile?.weight_kg ? selectedPlayer.player_profile.weight_kg + ' kg' : 'Chưa cập nhật' }}</el-descriptions-item>
            <el-descriptions-item label="Ghi chú của Ban quản trị" :span="2">
              <div style="white-space: pre-line; min-height: 50px; font-style: italic;">{{ selectedPlayer.player_profile?.admin_notes || 'Không có ghi chú' }}</div>
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
        <el-tab-pane label="Lịch sử thi đấu">
          <el-table :data="matchHistory" stripe style="width: 100%" size="small" empty-text="Chưa có dữ liệu thi đấu">
            <el-table-column property="time" label="Thời gian" width="150" />
            <el-table-column property="tournament_name" label="Giải đấu" min-width="180" show-overflow-tooltip />
            <el-table-column property="opponent" label="Đối thủ" min-width="150" />
            <el-table-column label="Kết quả" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getResultTagType(row.result_status)" size="small" effect="dark">
                  {{ row.result_status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column property="score" label="Tỷ số" width="100" align="center" />
            <el-table-column type="expand">
              <template #default="{ row }">
                <div class="match-detail-expand">
                  <h4>Chi tiết trận đấu #{{ row.id }}</h4>
                  <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="Sân thi đấu">{{ row.court }}</el-descriptions-item>
                    <el-descriptions-item label="Vòng đấu">{{ row.round }}</el-descriptions-item>
                    <el-descriptions-item label="Đối thủ">{{ row.opponent }}</el-descriptions-item>
                    <el-descriptions-item label="Tỷ số chung cuộc">{{ row.score }}</el-descriptions-item>
                    <el-descriptions-item label="Trạng thái">{{ row.status === 'completed' ? 'Hoàn thành' : 'Đang chờ' }}</el-descriptions-item>
                    <el-descriptions-item label="Người thắng">{{ row.winner_side === 'side_a' ? 'Bản thân' : (row.winner_side === 'side_b' ? row.opponent : 'N/A') }}</el-descriptions-item>
                    <el-descriptions-item label="Tỷ số các hiệp" :span="2">
                      <div class="sets-summary">
                        <template v-for="(val, key) in row.sets" :key="key">
                          <el-tag v-if="val.a !== null || val.b !== null" size="small" effect="plain" class="set-tag">
                            {{ key.replace('set', 'Set ') }}: <strong>{{ val.a }} - {{ val.b }}</strong>
                          </el-tag>
                        </template>
                      </div>
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
        <el-tab-pane label="Giải đấu tham gia">
          <el-table :data="tournamentList" stripe style="width: 100%" size="small" empty-text="Chưa tham gia giải đấu nào">
            <el-table-column property="registered_at" label="Ngày đăng ký" width="150" />
            <el-table-column property="tournament_name" label="Tên giải đấu" min-width="200" />
            <el-table-column label="Trạng thái" width="120">
              <template #default="{ row }">
                <el-tag :type="getRegStatusType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column property="payment_status" label="Thanh toán" width="120" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="Chỉ số thi đấu">
          <div class="detail-stats-panel">
            <section v-for="group in selectedPlayerStatGroups" :key="group.title" class="detail-stats-group">
              <div class="detail-stats-group-head">
                <div>
                  <h4>{{ group.title }}</h4>
                  <span>{{ group.subtitle }}</span>
                </div>
                <p>{{ group.description }}</p>
              </div>

              <div class="detail-stat-grid">
                <article v-for="field in group.fields" :key="field.key" class="detail-stat-card">
                  <div class="detail-stat-label">
                    <strong>{{ field.label }}</strong>
                    <small>{{ field.englishLabel }}</small>
                  </div>
                  <div class="detail-stat-value">{{ formatPlayerStatValue(field.value, field.type) }}</div>
                  <el-progress
                    v-if="field.type === 'percent'"
                    :percentage="field.progress"
                    :show-text="false"
                    :stroke-width="7"
                    class="detail-stat-progress"
                  />
                </article>
              </div>
            </section>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<style scoped>
.saas-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100%; /* Ensure it takes full space */
}

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

.saas-search { width: 300px; }
.saas-filter { width: 160px; }

:deep(.el-input__wrapper), :deep(.el-select__wrapper) {
  background-color: #f8fafc !important;
  box-shadow: none !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 10px !important;
  padding: 8px 12px !important;
}

:deep(.el-input__wrapper.is-focus), :deep(.el-select__wrapper.is-focused) {
  border-color: #059669 !important;
  background-color: #fff !important;
}

.saas-btn-create {
  background-color: #059669 !important;
  border: none !important;
  border-radius: 10px !important;
  padding: 20px 24px !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2) !important;
}

/* Table Styling - REMOVED SECOND WHITE PANEL */
.saas-content {
  background: transparent;
  flex: 1;
}

.saas-table {
  background: transparent !important;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-border-color: #f1f5f9;
}

:deep(.el-table__inner-wrapper::before) { display: none; }
:deep(.el-table__border-left-patch) { display: none; }
:deep(.el-table--border .el-table__inner-wrapper::after) { display: none; }

.saas-user-cell {
  display: flex;
  align-items: center;
  gap: 14px;
}

.saas-avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  overflow: hidden;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
}

.saas-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.saas-user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-weight: 700;
  color: #1e293b;
  font-size: 0.95rem;
}

.user-email {
  font-size: 0.8rem;
  color: #64748b;
}

.saas-tag {
  border-radius: 6px !important;
  font-weight: 700 !important;
  padding: 4px 10px !important;
  border: none !important;
}

.elo-badge {
  font-weight: 800;
  color: #059669;
  background: #ecfdf5;
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #ef4444;
}

.status-indicator.is-active {
  color: #10b981;
}

.status-indicator .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

/* Enhanced Edit Button */
.saas-edit-btn {
  background: #f1f5f9 !important;
  border: 1px solid #e2e8f0 !important;
  color: #475569 !important;
  border-radius: 8px !important;
  font-weight: 700 !important;
  padding: 8px 16px !important;
  transition: all 0.2s !important;
  display: flex !important;
  align-items: center !important;
  gap: 6px !important;
}

.saas-edit-btn:hover {
  background: #059669 !important;
  color: #fff !important;
  border-color: #059669 !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2);
}

/* Dialog & Upload */
.saas-upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32px;
}

.avatar-preview-box {
  position: relative;
  width: 110px;
  height: 110px;
  border-radius: 20px;
  background: #f8fafc;
  border: 2px dashed #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: all 0.3s;
}

.avatar-preview-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-preview-box .el-icon {
  font-size: 36px;
  color: #94a3b8;
}

.hover-overlay {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: 0.3s;
  cursor: pointer;
}

.avatar-preview-box:hover .hover-overlay {
  opacity: 1;
}

.hover-overlay .el-icon {
  color: #fff;
  font-size: 28px;
}

.upload-hint {
  margin-top: 12px;
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 500;
}

.saas-btn-primary {
  background-color: #059669 !important;
  border: none !important;
  border-radius: 10px !important;
  padding: 12px 24px !important;
  font-weight: 700 !important;
}

.saas-btn-secondary {
  border-radius: 10px !important;
  padding: 12px 24px !important;
  font-weight: 700 !important;
}

:deep(.el-dialog.saas-dialog) {
  border-radius: 24px !important;
  padding: 16px !important;
}

:deep(.el-dialog__header) {
  margin-bottom: 24px !important;
}

:deep(.el-dialog__title) {
  font-weight: 700 !important;
  color: #1e293b !important;
}

.clickable { cursor: pointer; }
.clickable:hover .user-name { color: #059669; text-decoration: underline; }

.action-btns { display: flex; align-items: center; gap: 8px; justify-content: center; }

.detail-header { padding-bottom: 10px; }
.player-info-brief { display: flex; align-items: center; gap: 20px; }
.saas-avatar.large { width: 64px; height: 64px; border-radius: 16px; }
.player-info-brief h3 { margin: 0; font-size: 1.25rem; color: #1e293b; }
.player-info-brief .badges { display: flex; align-items: center; gap: 12px; margin-top: 6px; }
.elo-val { font-size: 0.85rem; font-weight: 700; color: #059669; background: #ecfdf5; padding: 2px 8px; border-radius: 4px; }

.detail-tabs { border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0 !important; box-shadow: none !important; }
:deep(.el-tabs--border-card) { background: #fff; }
:deep(.el-tabs__header) { background: #f8fafc !important; border-bottom: 1px solid #e2e8f0 !important; }

.match-detail-expand { padding: 15px 25px; background: #f8fafc; border-radius: 8px; margin: 5px; }
.match-detail-expand h4 { margin-top: 0; margin-bottom: 15px; font-size: 0.9rem; color: #475569; border-left: 3px solid #059669; padding-left: 10px; }
.match-detail-expand {
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 8px;
}

.match-detail-expand h4 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 14px;
  color: #1e293b;
}

.sets-summary {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.set-tag {
  border-radius: 6px !important;
  font-family: 'Inter', sans-serif !important;
}

.set-tag strong {
  color: #059669;
  margin-left: 4px;
}

.detail-stats-panel {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.detail-stats-group {
  min-width: 0;
  padding: 18px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.detail-stats-group-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid #e2e8f0;
}

.detail-stats-group-head h4 {
  margin: 0;
  color: #002855;
  font-size: 1rem;
  font-weight: 900;
}

.detail-stats-group-head span {
  display: inline-block;
  margin-top: 4px;
  color: #059669;
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.detail-stats-group-head p {
  max-width: 240px;
  margin: 0;
  color: #64748b;
  font-size: 0.78rem;
  line-height: 1.45;
  text-align: right;
}

.detail-stat-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-stat-card {
  min-width: 0;
  padding: 14px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #ffffff;
}

.detail-stat-label {
  min-height: 42px;
}

.detail-stat-label strong {
  display: block;
  color: #0f172a;
  font-size: 0.84rem;
  line-height: 1.25;
}

.detail-stat-label small {
  display: block;
  margin-top: 3px;
  color: #64748b;
  font-size: 0.72rem;
  line-height: 1.25;
}

.detail-stat-value {
  margin-top: 12px;
  color: #002855;
  font-size: 1.25rem;
  font-weight: 900;
}

.detail-stat-progress {
  margin-top: 10px;
}

.detail-stat-progress :deep(.el-progress-bar__outer) {
  background-color: #e2e8f0;
}

.detail-stat-progress :deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #0ea5e9 0%, #059669 100%);
}

.player-editor-dialog :deep(.el-dialog__body) {
  padding-top: 0;
}

.player-editor-tabs :deep(.el-tabs__header) {
  margin-bottom: 22px;
}

.player-editor-tabs :deep(.el-tabs__item) {
  height: 44px;
  padding: 0 22px;
  color: #64748b;
  font-weight: 800;
}

.player-editor-tabs :deep(.el-tabs__item.is-active) {
  color: #059669;
}

.editor-intro {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
  padding: 16px 18px;
  border: 1px solid #dbeafe;
  border-radius: 14px;
  background: linear-gradient(135deg, #f8fafc 0%, #eef7ff 100%);
}

.editor-intro strong {
  display: block;
  color: #0f2f57;
  font-size: 1rem;
  font-weight: 900;
}

.editor-intro p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 0.88rem;
  line-height: 1.45;
}

.compact-upload {
  margin-bottom: 22px;
}

.stats-editor {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.stats-group {
  min-width: 0;
  padding: 18px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
}

.stats-group-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid #eef2f7;
}

.stats-group h4 {
  margin: 0;
  color: #002855;
  font-size: 1.05rem;
  font-weight: 900;
}

.stats-group-head span {
  display: inline-block;
  margin-top: 4px;
  color: #059669;
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.stats-group-head p {
  max-width: 220px;
  margin: 0;
  color: #64748b;
  font-size: 0.78rem;
  line-height: 1.45;
  text-align: right;
}

.stat-field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 16px;
}

.stat-field-grid :deep(.el-form-item) {
  position: relative;
  margin-bottom: 0;
  padding: 12px;
  border: 1px solid #eef2f7;
  border-radius: 12px;
  background: #f8fafc;
}

.field-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-height: 38px;
}

.field-label strong {
  color: #1e293b;
  font-size: 0.84rem;
  line-height: 1.25;
}

.field-label small {
  color: #64748b;
  font-size: 0.72rem;
  line-height: 1.25;
}

.field-unit {
  position: absolute;
  right: 18px;
  bottom: 18px;
  color: #94a3b8;
  font-size: 0.72rem;
  font-weight: 800;
  pointer-events: none;
}

@media (max-width: 960px) {
  .detail-stats-panel,
  .stats-editor,
  .stat-field-grid {
    grid-template-columns: 1fr;
  }

  .detail-stats-group-head,
  .stats-group-head {
    flex-direction: column;
  }

  .detail-stats-group-head p,
  .stats-group-head p {
    max-width: none;
    text-align: left;
  }
}
</style>
