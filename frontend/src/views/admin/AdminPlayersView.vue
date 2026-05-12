<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { playerService } from '../../services/playerService'
import apiClient from '../../services/apiClient' 
import { Plus, Camera, User } from '@element-plus/icons-vue' 
import { t } from '../../utils/locale'

const players = ref([])
const loading = ref(false)
const isSaving = ref(false)
const search = ref('')
const skillFilter = ref('')
const statusFilter = ref('')

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
  avatar_url: '',
  is_active: true
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
  elo_points: 1000
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

const openEditDialog = (player) => {
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
    avatar_url: player.user.avatar_url || '',
    is_active: player.user.is_active
  }
  isEditDialogVisible.value = true
}

const openCreateDialog = () => {
  createForm.value = { 
    full_name: '', email: '', password: '', phone: '', 
    gender: 'male', play_hand: 'right', account_type: 'user', 
    otp_code: 'bypass_otp',
    avatar_url: '', skill_level: 'Beginner', preferred_category: 'Singles',
    province: '', date_of_birth: null, elo_points: 1000
  }
  isCreateDialogVisible.value = true
}

const handleCreatePlayer = async () => {
  if (!createForm.value.full_name || !createForm.value.email || !createForm.value.password) {
    ElMessage.warning('Vui lòng điền đủ Họ tên, Email và Mật khẩu!')
    return
  }
  isCreating.value = true
  try {
    const payload = { ...createForm.value }
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
  isSaving.value = true
  try {
    const payload = { ...editForm.value }
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

// Đã cập nhật hàm map ngôn ngữ động cho trình độ VĐV
const formatSkillLevel = (val) => {
  const map = { 
    'Beginner': t('admin.beginner'), 
    'Intermediate': t('admin.intermediate'), 
    'Advanced': t('admin.advanced'), 
    'Professional': t('admin.professional') 
  }
  return map[val] || val || 'N/A'
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
        <el-option v-for="s in ['Beginner', 'Intermediate', 'Advanced', 'Professional']" :key="s" :label="formatSkillLevel(s)" :value="s" />
      </el-select>
      <el-select v-model="statusFilter" :placeholder="$t('admin.status')" clearable @change="fetchPlayers" style="width: 150px">
        <el-option :label="$t('admin.active')" value="active" />
        <el-option :label="$t('admin.locked')" value="inactive" />
      </el-select>
      <el-button type="success" @click="openCreateDialog" style="margin-left: auto;">
        <el-icon><Plus /></el-icon> {{ $t('admin.createPlayer') }}
      </el-button>
    </section>

    <section class="table-card">
      <el-table :data="players" v-loading="loading" stripe>
        <el-table-column :label="$t('admin.player').toUpperCase()" min-width="200">
          <template #default="{ row }">
            <div class="player-info">
              <img 
                :src="row.user.avatar_url || `https://ui-avatars.com/api/?name=${row.user.full_name}&background=f1f5f9&color=002855`" 
                referrerpolicy="no-referrer"
                class="custom-table-ava"
                @error="$event.target.src = `https://ui-avatars.com/api/?name=${row.user.full_name}&background=f1f5f9&color=002855`"
              />
              <div class="details">
                <span>{{ row.user.full_name }}</span>
                <span>{{ row.user.email }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column property="user.phone" :label="$t('admin.phone').toUpperCase()" width="120" />
        <el-table-column :label="$t('admin.skillLevel').toUpperCase()" width="130">
          <template #default="{ row }">
            <el-tag :type="getSkillType(row.player_profile?.skill_level)">
              {{ formatSkillLevel(row.player_profile?.skill_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('admin.elo').toUpperCase()" width="80" align="center">
           <template #default="{ row }">
             <span>{{ row.player_profile?.elo_points || 0 }}</span>
           </template>
        </el-table-column>
        <el-table-column :label="$t('admin.accountStatus').toUpperCase()" width="120">
           <template #default="{ row }">
             <el-tag :type="row.user.is_active ? 'success' : 'danger'">
               {{ row.user.is_active ? $t('admin.active') : $t('admin.locked') }}
             </el-tag>
           </template>
        </el-table-column>
        <el-table-column :label="$t('admin.action').toUpperCase()" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openEditDialog(row)">{{ $t('admin.edit') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="isCreateDialogVisible" :title="$t('admin.createNewPlayer')" width="650px">
      <el-form label-position="top">
        <div class="avatar-upload-section">
          <div class="avatar-preview">
            <img v-if="createForm.avatar_url" :src="createForm.avatar_url" />
            <el-icon v-else><User /></el-icon>
            <label class="upload-overlay">
              <input type="file" hidden @change="e => handleImageUpload(e, 'create')" accept="image/*" />
              <el-icon><Camera /></el-icon>
            </label>
          </div>
          <p class="upload-tip">{{ $t('admin.clickToUpload') }}</p>
        </div>

        <el-row :gutter="20">
          <el-col :span="12"><el-form-item :label="$t('admin.fullName') + ' (*)'"><el-input v-model="createForm.full_name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="$t('admin.email') + ' (*)'"><el-input v-model="createForm.email" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="$t('admin.password') + ' (*)'"><el-input v-model="createForm.password" type="password" show-password /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="$t('admin.phone')"><el-input v-model="createForm.phone" /></el-form-item></el-col>
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
              <el-date-picker 
                v-model="createForm.date_of_birth" 
                type="date" 
                format="DD/MM/YYYY" 
                value-format="YYYY-MM-DD" 
                :placeholder="$t('admin.dobPlaceholder')" 
                style="width: 100%" 
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="isCreateDialogVisible = false">{{ $t('admin.cancel') }}</el-button>
        <el-button type="success" :loading="isCreating" @click="handleCreatePlayer">{{ $t('admin.confirmCreate') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="isEditDialogVisible" :title="$t('admin.editPlayerProfile')" width="650px">
      <el-form label-position="top">
        <div class="avatar-upload-section">
          <div class="avatar-preview">
            <img v-if="editForm.avatar_url" :src="editForm.avatar_url" />
            <el-icon v-else><User /></el-icon>
            <label class="upload-overlay">
              <input type="file" hidden @change="e => handleImageUpload(e, 'edit')" accept="image/*" />
              <el-icon><Camera /></el-icon>
            </label>
          </div>
          <p class="upload-tip">{{ $t('admin.clickToChange') }}</p>
        </div>

        <el-row :gutter="20">
          <el-col :span="12"><el-form-item :label="$t('admin.fullName')"><el-input v-model="editForm.full_name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="$t('admin.phone')"><el-input v-model="editForm.phone" /></el-form-item></el-col>
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
              <el-date-picker 
                v-model="editForm.date_of_birth" 
                type="date" 
                format="DD/MM/YYYY" 
                value-format="YYYY-MM-DD" 
                :placeholder="$t('admin.dobPlaceholder')" 
                style="width: 100%" 
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('admin.gender')">
              <el-radio-group v-model="editForm.gender">
                <el-radio label="male">{{ $t('admin.male') }}</el-radio>
                <el-radio label="female">{{ $t('admin.female') }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('admin.accountStatus')">
              <el-switch v-model="editForm.is_active" :active-text="$t('admin.active')" :inactive-text="$t('admin.locked')" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="isEditDialogVisible = false">{{ $t('admin.cancel') }}</el-button>
        <el-button type="primary" :loading="isSaving" @click="handleUpdatePlayer">{{ $t('admin.saveChanges') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.module-shell { display: grid; gap: 24px; padding: 20px; }
.filter-card, .table-card { background: #fff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; }
.filter-card { display: flex; align-items: center; gap: 12px; }
.player-info { display: flex; align-items: center; gap: 12px; }
.player-info .details { display: flex; flex-direction: column; }
.player-info .details span:first-child { font-weight: 700; color: #002855; }
.player-info .details span:last-child { font-size: 0.75rem; color: #64748b; }

.avatar-upload-section { display: flex; flex-direction: column; align-items: center; margin-bottom: 25px; }
.avatar-preview { position: relative; width: 100px; height: 100px; border-radius: 12px; background: #f1f5f9; border: 2px dashed #cbd5e1; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.avatar-preview img { width: 100%; height: 100%; object-fit: cover; }
.avatar-preview .el-icon { font-size: 32px; color: #94a3b8; }
.upload-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; opacity: 0; transition: 0.3s; cursor: pointer; }
.avatar-preview:hover .upload-overlay { opacity: 1; }
.upload-overlay .el-icon { color: #fff; font-size: 24px; }
.upload-tip { font-size: 12px; color: #64748b; margin-top: 8px; }
.custom-table-ava {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid #e2e8f0;
  background: #f1f5f9;
}
</style>