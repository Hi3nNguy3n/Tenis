<script setup>
import { onMounted, ref } from 'vue'
import { apiClient } from '../../../services/apiClient'
import { useAuthStore } from '../../../stores/auth'
import { ElMessage } from 'element-plus'
import { 
  User, Trophy, Medal, EditPen, Camera, Phone, Message, Calendar as CalendarIcon, 
  Male, Female, SwitchButton, Document 
} from '@element-plus/icons-vue'

const authStore = useAuthStore()
const loading = ref(true)
const saving = ref(false)
const isEditing = ref(false)
const profile = ref(null)
const error = ref('')

const matchHistory = ref([])
const historyLoading = ref(false)

const editForm = ref({
  full_name: '',
  phone: '',
  gender: '',
  date_of_birth: '',
  play_hand: '',
  skill_level: '',
  preferred_category: ''
})

const fetchProfile = async () => {
  loading.value = true
  try {
    const data = await apiClient.get('/api/players/me')
    profile.value = data
    
    editForm.value = {
      full_name: data.user.full_name || '',
      phone: data.user.phone || '',
      gender: data.player_profile?.gender || '',
      date_of_birth: data.player_profile?.date_of_birth || '',
      play_hand: data.player_profile?.play_hand || '',
      skill_level: data.player_profile?.skill_level || '',
      preferred_category: data.player_profile?.preferred_category || ''
    }
  } catch (err) {
    ElMessage.error('Không thể tải thông tin hồ sơ.')
  } finally {
    loading.value = false
  }
}

const fetchHistory = async () => {
  historyLoading.value = true
  try {
    const data = await apiClient.get('/api/players/me/history')
    matchHistory.value = data
  } catch (err) {
    console.error('Lỗi tải lịch sử:', err)
  } finally {
    historyLoading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await apiClient.put('/api/players/me', editForm.value)
    await fetchProfile()
    await authStore.fetchCurrentProfile()
    isEditing.value = false
    ElMessage.success('Cập nhật hồ sơ thành công!')
  } catch (err) {
    ElMessage.error(err.message || 'Lỗi khi cập nhật hồ sơ.')
  } finally {
    saving.value = false
  }
}

const handleAvatarUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  saving.value = true
  try {
    await apiClient.request('/api/players/me/avatar', {
      method: 'POST',
      body: formData,
      includeJson: false 
    })
    await fetchProfile()
    await authStore.fetchCurrentProfile()
    ElMessage.success('Cập nhật ảnh đại diện thành công!')
  } catch (err) {
    ElMessage.error(err.message || 'Lỗi khi upload ảnh.')
  } finally {
    saving.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'Chưa cập nhật'
  const parts = dateStr.split('-')
  return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : dateStr
}

onMounted(() => {
  fetchProfile()
  fetchHistory()
})
</script>

<template>
  <div class="profile-layout" v-loading.fullscreen.lock="loading">
    <div v-if="profile" class="profile-container">
      
      <section class="profile-hero">
        <div class="hero-backdrop"></div>
        <div class="hero-content">
          <div class="avatar-wrapper">
            <div class="avatar-box">
              <img v-if="profile.user.avatar_url" :src="profile.user.avatar_url" alt="Avatar" />
              <el-icon v-else class="avatar-icon"><User /></el-icon>
            </div>
            <label class="upload-overlay" :class="{ disabled: saving }">
              <input type="file" @change="handleAvatarUpload" accept="image/*" :disabled="saving" hidden />
              <el-icon><Camera /></el-icon>
            </label>
          </div>

          <div class="user-brief">
            <h1>{{ profile.user.full_name }}</h1>
            <div class="user-badges">
              <el-tag effect="dark" round type="success" size="large">
                {{ profile.player_profile?.skill_level || 'Chưa xếp hạng' }}
              </el-tag>
              <div class="stat-pill">
                <el-icon><Trophy /></el-icon>
                <span>ELO: <strong>{{ profile.player_profile?.elo_points || 0 }}</strong></span>
              </div>
              <div class="stat-pill">
                <el-icon><Medal /></el-icon>
                <span>W/L: <strong>{{ profile.player_profile?.wins }} - {{ profile.player_profile?.losses }}</strong></span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div class="profile-grid">
        
        <aside class="profile-sidebar">
          <el-menu default-active="/profile" class="side-menu" :router="true">
            <el-menu-item index="/profile">
              <el-icon><User /></el-icon>
              <span>Thông tin cá nhân</span>
            </el-menu-item>
            <el-menu-item index="/profile/my-tournaments">
              <el-icon><Trophy /></el-icon>
              <span>Giải đấu & Trận đấu</span>
            </el-menu-item>
            <el-divider style="margin: 10px 0;"></el-divider>
            <el-menu-item @click="authStore.logout()" class="logout-item">
              <el-icon><SwitchButton /></el-icon>
              <span>Đăng xuất</span>
            </el-menu-item>
          </el-menu>
        </aside>

        <main class="profile-content">
          
          <el-card class="content-card shadow-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <div class="header-title">
                  <el-icon><Document /></el-icon>
                  <span>Thông tin hồ sơ</span>
                </div>
                <el-button v-if="!isEditing" type="primary" plain :icon="EditPen" @click="isEditing = true">
                  Chỉnh sửa
                </el-button>
              </div>
            </template>

            <el-descriptions v-if="!isEditing" :column="2" border class="profile-descriptions">
              <el-descriptions-item>
                <template #label><div class="desc-label"><el-icon><User /></el-icon> Họ và tên</div></template>
                <strong>{{ profile.user.full_name }}</strong>
              </el-descriptions-item>
              <el-descriptions-item>
                <template #label><div class="desc-label"><el-icon><Message /></el-icon> Email</div></template>
                {{ profile.user.email }}
              </el-descriptions-item>
              <el-descriptions-item>
                <template #label><div class="desc-label"><el-icon><Phone /></el-icon> Số điện thoại</div></template>
                {{ profile.user.phone || 'Chưa cập nhật' }}
              </el-descriptions-item>
              <el-descriptions-item>
                <template #label><div class="desc-label"><el-icon><Male /></el-icon> Giới tính</div></template>
                {{ profile.player_profile?.gender || 'Chưa cập nhật' }}
              </el-descriptions-item>
              <el-descriptions-item>
                <template #label><div class="desc-label"><el-icon><CalendarIcon /></el-icon> Ngày sinh</div></template>
                {{ formatDate(profile.player_profile?.date_of_birth) }}
              </el-descriptions-item>
              <el-descriptions-item>
                <template #label><div class="desc-label"><el-icon><Trophy /></el-icon> Tay thuận</div></template>
                {{ profile.player_profile?.play_hand === 'right' ? 'Tay Phải' : profile.player_profile?.play_hand === 'left' ? 'Tay Trái' : 'N/A' }}
              </el-descriptions-item>
            </el-descriptions>

            <el-form v-else :model="editForm" label-position="top" class="edit-form">
              <el-row :gutter="24">
                <el-col :span="12">
                  <el-form-item label="Họ và tên">
                    <el-input v-model="editForm.full_name" :prefix-icon="User" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Số điện thoại">
                    <el-input v-model="editForm.phone" :prefix-icon="Phone" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Giới tính">
                    <el-select v-model="editForm.gender" placeholder="Chọn giới tính" style="width: 100%">
                      <el-option label="Nam" value="Nam" />
                      <el-option label="Nữ" value="Nữ" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Ngày sinh">
                    <el-date-picker v-model="editForm.date_of_birth" type="date" placeholder="Chọn ngày" format="DD/MM/YYYY" value-format="YYYY-MM-DD" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Tay thuận">
                    <el-select v-model="editForm.play_hand" style="width: 100%">
                      <el-option label="Tay Phải" value="right" />
                      <el-option label="Tay Trái" value="left" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Trình độ (Tự đánh giá)">
                    <el-select v-model="editForm.skill_level" style="width: 100%">
                      <el-option label="Beginner (Mới chơi)" value="Beginner" />
                      <el-option label="Intermediate (Trung cấp)" value="Intermediate" />
                      <el-option label="Advanced (Nâng cao)" value="Advanced" />
                      <el-option label="Professional (Chuyên nghiệp)" value="Professional" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <div class="form-actions">
                <el-button @click="isEditing = false">Hủy bỏ</el-button>
                <el-button type="primary" :loading="saving" @click="handleSave">Lưu thay đổi</el-button>
              </div>
            </el-form>
          </el-card>

          <el-card class="content-card shadow-card mt-4" shadow="hover">
            <template #header>
              <div class="card-header">
                <div class="header-title">
                  <el-icon><CalendarIcon /></el-icon>
                  <span>Lịch sử thi đấu</span>
                </div>
              </div>
            </template>
            
            <el-table :data="matchHistory" v-loading="historyLoading" stripe style="width: 100%">
              <el-table-column prop="time" label="Ngày" width="120" />
              <el-table-column prop="tournament_name" label="Giải đấu" min-width="180" show-overflow-tooltip />
              <el-table-column prop="opponent" label="Đối thủ" min-width="150" />
              <el-table-column prop="score" label="Tỷ số" width="100" align="center" />
              <el-table-column label="Kết quả" width="120" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'THẮNG' ? 'success' : (row.status === 'THUA' ? 'danger' : 'info')" effect="light">
                    {{ row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <template #empty>
                <el-empty description="Bạn chưa tham gia trận đấu nào." />
              </template>
            </el-table>
          </el-card>

        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-layout { padding: 40px 20px; background-color: #f8fafc; min-height: 100vh; }
.profile-container { max-width: 1100px; margin: 0 auto; display: flex; flex-direction: column; gap: 30px; }

/* HERO BANNER */
.profile-hero { position: relative; border-radius: 24px; overflow: hidden; background: white; box-shadow: 0 10px 30px rgba(0,0,0,0.04); }
.hero-backdrop { height: 140px; background: linear-gradient(135deg, #0f5c4d 0%, #123f34 100%); }
.hero-content { display: flex; align-items: flex-end; padding: 0 40px 30px; gap: 30px; margin-top: -60px; }

.avatar-wrapper { position: relative; width: 140px; height: 140px; }
.avatar-box { width: 100%; height: 100%; border-radius: 50%; border: 6px solid white; background: #e2e8f0; overflow: hidden; display: flex; justify-content: center; align-items: center; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
.avatar-box img { width: 100%; height: 100%; object-fit: cover; }
.avatar-icon { font-size: 60px; color: #94a3b8; }

.upload-overlay {
  position: absolute; bottom: 5px; right: 5px; width: 36px; height: 36px;
  background: #006953; color: white; border-radius: 50%; display: flex;
  justify-content: center; align-items: center; cursor: pointer;
  border: 3px solid white; transition: 0.2s;
}
.upload-overlay:hover { transform: scale(1.1); background: #0f5c4d; }

.user-brief { padding-bottom: 5px; }
.user-brief h1 { margin: 0 0 12px 0; font-size: 2rem; color: #0f172a; font-weight: 800; }
.user-badges { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
.stat-pill { display: flex; align-items: center; gap: 6px; background: #f1f5f9; padding: 6px 14px; border-radius: 999px; font-size: 0.85rem; color: #475569; }
.stat-pill strong { color: #0f172a; font-size: 1rem; }
.stat-pill .el-icon { color: #006953; font-size: 1.1rem; }

/* GRID LAYOUT */
.profile-grid { display: grid; grid-template-columns: 260px 1fr; gap: 30px; align-items: start; }

/* SIDEBAR */
.profile-sidebar { position: sticky; top: 20px; }
.side-menu { border-radius: 20px; border: none; box-shadow: 0 10px 30px rgba(0,0,0,0.04); overflow: hidden; padding: 10px 0; }
.side-menu .el-menu-item { border-radius: 10px; margin: 0 10px; height: 50px; }
.side-menu .el-menu-item.is-active { background-color: #f0fdf4; color: #006953; font-weight: bold; }
.logout-item { color: #ef4444 !important; }
.logout-item:hover { background-color: #fef2f2 !important; }

/* CONTENT */
.profile-content { display: flex; flex-direction: column; gap: 24px; }
.shadow-card { border-radius: 20px; border: none; box-shadow: 0 10px 30px rgba(0,0,0,0.04); }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.header-title { display: flex; align-items: center; gap: 10px; font-size: 1.2rem; font-weight: 700; color: #0f172a; }
.header-title .el-icon { color: #006953; font-size: 1.4rem; }

/* DESCRIPTIONS (VIEW MODE) */
.profile-descriptions { --el-descriptions-table-border: 1px solid #e2e8f0; }
.desc-label { display: flex; align-items: center; gap: 8px; color: #64748b; font-weight: 600; }
.desc-label .el-icon { color: #94a3b8; }

/* FORM (EDIT MODE) */
.edit-form { padding-top: 10px; }
.form-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #f1f5f9; }

@media (max-width: 900px) {
  .profile-grid { grid-template-columns: 1fr; }
  .profile-sidebar { position: static; }
  .hero-content { flex-direction: column; align-items: center; text-align: center; margin-top: -70px; }
  .user-badges { justify-content: center; }
}
</style>