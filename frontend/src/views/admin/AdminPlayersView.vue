<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { playerService } from '../../services/playerService'
import apiClient from '../../services/apiClient' // Gọi API client để gọi POST request
import { Plus } from '@element-plus/icons-vue' // Icon dấu cộng
import { t } from '../../utils/locale'

const players = ref([])
const loading = ref(false)
const isSaving = ref(false)
const search = ref('')
const skillFilter = ref('')
const statusFilter = ref('')

// --- Biến cho form Edit (Giữ nguyên) ---
const isEditDialogVisible = ref(false)
const editForm = ref({
  id: null, full_name: '', skill_level: '', play_hand: '', phone: '', is_active: true
})

// --- Biến cho form Tạo mới (Mới thêm) ---
const isCreateDialogVisible = ref(false)
const isCreating = ref(false)
const createForm = ref({
  full_name: '', email: '', password: '', phone: '', 
  gender: 'male', play_hand: 'right', account_type: 'user', 
  otp_code: 'bypass_otp' // Trick bypass OTP model validation
})

// Fetch danh sách người chơi
const fetchPlayers = async () => {
  loading.value = true
  try {
    const data = await playerService.getAll({ 
      search: search.value, skill: skillFilter.value, status: statusFilter.value 
    })
    players.value = Array.isArray(data) ? data : (data.items || [])
  } catch (err) {
    ElMessage.error(t('admin.loadPlayersError') + ': ' + err.message)
  } finally {
    loading.value = false
  }
}

// Mở form Edit
const openEditDialog = (player) => {
  editForm.value = {
    id: player.id,
    full_name: player.user.full_name,
    skill_level: player.player_profile?.skill_level || 'Beginner',
    play_hand: player.player_profile?.play_hand || 'right',
    phone: player.user.phone || '',
    is_active: player.user.is_active
  }
  isEditDialogVisible.value = true
}

// Mở form Create
const openCreateDialog = () => {
  createForm.value = { 
    full_name: '', email: '', password: '', phone: '', 
    gender: 'male', play_hand: 'right', account_type: 'user', otp_code: 'bypass_otp' 
  }
  isCreateDialogVisible.value = true
}

// Xử lý tạo mới tài khoản (Admin Create)
const handleCreatePlayer = async () => {
  if (!createForm.value.full_name || !createForm.value.email || !createForm.value.password) {
    ElMessage.warning('Vui lòng điền đủ Họ tên, Email và Mật khẩu!')
    return
  }
  
  isCreating.value = true
  try {
    // Gọi thẳng vào API admin-create vừa viết ở Backend
    await apiClient.post('/api/players/admin-create', createForm.value)
    ElMessage.success('Đã tạo tài khoản VĐV thành công!')
    isCreateDialogVisible.value = false
    fetchPlayers() // Refresh lại bảng danh sách
  } catch (err) {
    const errorMsg = err.response?.data?.detail || err.message || 'Lỗi khi tạo tài khoản'
    ElMessage.error(errorMsg)
  } finally {
    isCreating.value = false
  }
}

// Xử lý cập nhật thông tin
const handleUpdatePlayer = async () => {
  isSaving.value = true
  try {
    await playerService.update(editForm.value.id, editForm.value)
    ElMessage.success(t('admin.updateSuccess'))
    isEditDialogVisible.value = false
    fetchPlayers()
  } catch (err) {
    ElMessage.error(t('admin.updateError') + ': ' + err.message)
  } finally {
    isSaving.value = false
  }
}

onMounted(fetchPlayers)

const getSkillType = (skill) => {
  if (skill === 'Professional') return 'danger'
  if (skill === 'Advanced') return 'warning'
  if (skill === 'Intermediate') return 'success'
  return 'info'
}
</script>

<template>
  <div class="module-shell">
    <section class="filter-card">
      <el-input v-model="search" :placeholder="$t('admin.searchPlayersPlaceholder')" clearable @change="fetchPlayers" style="width: 300px" />
      <el-select v-model="skillFilter" :placeholder="$t('admin.skillLevel')" clearable @change="fetchPlayers" style="width: 150px">
        <el-option label="Beginner" value="Beginner" />
        <el-option label="Intermediate" value="Intermediate" />
        <el-option label="Advanced" value="Advanced" />
        <el-option label="Professional" value="Professional" />
      </el-select>
      <el-select v-model="statusFilter" :placeholder="$t('admin.status')" clearable @change="fetchPlayers" style="width: 150px">
        <el-option :label="$t('admin.active')" value="active" />
        <el-option :label="$t('admin.locked')" value="inactive" />
      </el-select>
      <el-button @click="() => { search=''; skillFilter=''; statusFilter=''; fetchPlayers(); }">{{ $t('admin.reset') }}</el-button>
      <el-button plain @click="fetchPlayers">{{ $t('admin.refresh') }}</el-button>
      
      <el-button type="success" @click="openCreateDialog" style="margin-left: auto;">
        <el-icon><Plus /></el-icon> Thêm VĐV
      </el-button>
    </section>

    <section class="table-card">
      <el-table :data="players" v-loading="loading" stripe>
        <el-table-column :label="$t('admin.player')" min-width="200">
          <template #default="{ row }">
            <div class="player-info">
              <el-avatar :src="row.user.avatar_url" shape="square">{{ row.user.full_name.charAt(0) }}</el-avatar>
              <div class="details">
                <span>{{ row.user.full_name }}</span>
                <span>{{ row.user.email }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column property="user.phone" :label="$t('admin.phone')" width="120" />
        <el-table-column :label="$t('admin.skillLevel')" width="130">
          <template #default="{ row }">
            <el-tag :type="getSkillType(row.player_profile?.skill_level)">
              {{ row.player_profile?.skill_level || 'N/A' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('admin.elo')" width="80" align="center">
           <template #default="{ row }">
             <span>{{ row.player_profile?.elo_points || 0 }}</span>
           </template>
        </el-table-column>
        <el-table-column :label="$t('admin.status')" width="120">
           <template #default="{ row }">
             <el-tag :type="row.user.is_active ? 'success' : 'danger'">
               {{ row.user.is_active ? $t('admin.active') : $t('admin.locked') }}
             </el-tag>
           </template>
        </el-table-column>
        <el-table-column :label="$t('admin.action')" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openEditDialog(row)">{{ $t('admin.edit') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="isCreateDialogVisible" title="Thêm Vận Động Viên Mới" width="500px">
      <el-form label-position="top">
        <el-form-item label="Họ và tên (*)">
          <el-input v-model="createForm.full_name" placeholder="VD: Nguyễn Văn A" />
        </el-form-item>
        <el-form-item label="Email đăng nhập (*)">
          <el-input v-model="createForm.email" placeholder="VD: tennis@example.com" type="email" />
        </el-form-item>
        <el-form-item label="Mật khẩu khởi tạo (*)">
          <el-input v-model="createForm.password" placeholder="Tối thiểu 6 ký tự" type="password" show-password />
        </el-form-item>
        <el-form-item label="Số điện thoại">
          <el-input v-model="createForm.phone" placeholder="VD: 0912345678" />
        </el-form-item>
        
        <div style="display: flex; gap: 15px;">
          <el-form-item label="Giới tính" style="flex: 1;">
            <el-select v-model="createForm.gender">
              <el-option label="Nam" value="male" />
              <el-option label="Nữ" value="female" />
            </el-select>
          </el-form-item>
          <el-form-item label="Tay thuận" style="flex: 1;">
            <el-select v-model="createForm.play_hand">
              <el-option label="Tay phải" value="right" />
              <el-option label="Tay trái" value="left" />
              <el-option label="Đánh hai tay" value="both" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="isCreateDialogVisible = false">{{ $t('admin.cancel') }}</el-button>
        <el-button type="success" :loading="isCreating" @click="handleCreatePlayer">Xác nhận tạo</el-button>
      </template>
    </el-dialog>

<el-dialog v-model="isEditDialogVisible" :title="$t('admin.editPlayerProfile')" width="450px">
      <el-form label-position="top">
        <el-form-item :label="$t('admin.fullName')">
          <el-input v-model="editForm.full_name" />
        </el-form-item>
        <el-form-item :label="$t('admin.phoneNumber')">
          <el-input v-model="editForm.phone" />
        </el-form-item>
        
        <el-form-item label="Tay thuận">
          <el-select v-model="editForm.play_hand" style="width: 100%">
            <el-option label="Tay phải" value="right" />
            <el-option label="Tay trái" value="left" />
            <el-option label="Đánh hai tay" value="both" />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('admin.skillLevel')">
          <el-select v-model="editForm.skill_level" style="width: 100%">
            <el-option label="Beginner" value="Beginner" />
            <el-option label="Intermediate" value="Intermediate" />
            <el-option label="Advanced" value="Advanced" />
            <el-option label="Professional" value="Professional" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('admin.accountStatus')">
           <el-switch v-model="editForm.is_active" :active-text="$t('admin.active')" :inactive-text="$t('admin.locked')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="isEditDialogVisible = false">{{ $t('admin.cancel') }}</el-button>
        <el-button type="primary" :loading="isSaving" @click="handleUpdatePlayer">{{ $t('admin.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.module-shell { display: grid; gap: 24px; }
.filter-card, .table-card {
  background: rgba(248, 250, 252, 0.97);
  padding: 24px; border-radius: 28px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(12px);
}
.filter-card { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
.player-info { display: flex; align-items: center; gap: 12px; }
.player-info .details { display: flex; flex-direction: column; }
.player-info .details span:first-child { font-weight: 500; color: #0f172a; font-size: 0.92rem; }
.player-info .details span:last-child { font-size: 0.75rem; color: #64748b; }
:deep(.el-table) { --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-header-bg-color: rgba(0, 0, 0, 0.02); border-radius: 16px; overflow: hidden; }
:deep(.el-table th.el-table__cell) { font-weight: 500; color: #64748b; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }
:deep(.el-table__row) { transition: background 0.2s; }
:deep(.el-table__row:hover > td.el-table__cell) { background-color: rgba(255, 255, 255, 0.4) !important; }
</style>