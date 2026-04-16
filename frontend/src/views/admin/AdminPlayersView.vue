<script setup>
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { playerService } from '../../services/playerService'

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
  skill_level: '',
  play_hand: '',
  phone: '',
  is_active: true
})

const fetchPlayers = async () => {
  loading.value = true
  try {
    const data = await playerService.getAll({ 
      search: search.value, 
      skill: skillFilter.value,
      status: statusFilter.value 
    })
    players.value = Array.isArray(data) ? data : (data.items || [])
  } catch (err) {
    ElMessage.error('Lỗi tải danh sách VĐV: ' + err.message)
  } finally {
    loading.value = false
  }
}

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

const handleUpdatePlayer = async () => {
  isSaving.value = true
  try {
    await playerService.update(editForm.value.id, editForm.value)
    ElMessage.success('Cập nhật thành công')
    isEditDialogVisible.value = false
    fetchPlayers()
  } catch (err) {
    ElMessage.error('Lỗi cập nhật: ' + err.message)
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
    <section class="hero-card">
      <div>
        <span class="section-kicker">Member Directory</span>
        <h2>Quản lý Vận động viên</h2>
        <p>Xem danh sách người chơi, điều chỉnh trình độ Elo và quản lý trạng thái hoạt động của thành viên.</p>
      </div>
      <div class="hero-actions">
        <el-button plain size="large" @click="fetchPlayers">Làm mới</el-button>
      </div>
    </section>

    <section class="filter-card">
      <el-input v-model="search" placeholder="Tìm tên, email..." clearable @change="fetchPlayers" style="width: 300px" />
      <el-select v-model="skillFilter" placeholder="Trình độ" clearable @change="fetchPlayers" style="width: 150px">
        <el-option label="Beginner" value="Beginner" />
        <el-option label="Intermediate" value="Intermediate" />
        <el-option label="Advanced" value="Advanced" />
        <el-option label="Professional" value="Professional" />
      </el-select>
      <el-select v-model="statusFilter" placeholder="Trạng thái" clearable @change="fetchPlayers" style="width: 150px">
        <el-option label="Hoạt động" value="active" />
        <el-option label="Bị khóa" value="inactive" />
      </el-select>
      <el-button @click="() => { search=''; skillFilter=''; statusFilter=''; fetchPlayers(); }">Reset</el-button>
    </section>

    <section class="table-card">
      <el-table :data="players" v-loading="loading" stripe>
        <el-table-column label="VĐV" min-width="200">
          <template #default="{ row }">
            <div class="player-info">
              <el-avatar :src="row.user.avatar_url" shape="square">{{ row.user.full_name.charAt(0) }}</el-avatar>
              <div class="details">
                <strong>{{ row.user.full_name }}</strong>
                <span>{{ row.user.email }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column property="user.phone" label="SĐT" width="120" />
        <el-table-column label="Trình độ" width="130">
          <template #default="{ row }">
            <el-tag :type="getSkillType(row.player_profile?.skill_level)">
              {{ row.player_profile?.skill_level || 'N/A' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Elo" width="80" align="center">
           <template #default="{ row }">
             <strong>{{ row.player_profile?.elo_points || 0 }}</strong>
           </template>
        </el-table-column>
        <el-table-column label="Trạng thái" width="120">
           <template #default="{ row }">
             <el-tag :type="row.user.is_active ? 'success' : 'danger'">
               {{ row.user.is_active ? 'Hoạt động' : 'Đã khóa' }}
             </el-tag>
           </template>
        </el-table-column>
        <el-table-column label="Hành động" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openEditDialog(row)">Sửa</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="isEditDialogVisible" title="Chỉnh sửa hồ sơ VĐV" width="450px">
      <el-form label-position="top">
        <el-form-item label="Họ và tên">
          <el-input v-model="editForm.full_name" />
        </el-form-item>
        <el-form-item label="Số điện thoại">
          <el-input v-model="editForm.phone" />
        </el-form-item>
        <el-form-item label="Trình độ">
          <el-select v-model="editForm.skill_level" style="width: 100%">
            <el-option label="Beginner" value="Beginner" />
            <el-option label="Intermediate" value="Intermediate" />
            <el-option label="Advanced" value="Advanced" />
            <el-option label="Professional" value="Professional" />
          </el-select>
        </el-form-item>
        <el-form-item label="Trạng thái tài khoản">
           <el-switch v-model="editForm.is_active" active-text="Hoạt động" inactive-text="Đã khóa" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="isEditDialogVisible = false">Hủy</el-button>
        <el-button type="primary" :loading="isSaving" @click="handleUpdatePlayer">Lưu</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.module-shell { display: grid; gap: 24px; }
.hero-card, .filter-card, .table-card {
  background: white; padding: 24px; border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.03);
}
.hero-card { display: flex; justify-content: space-between; align-items: flex-end; }
.section-kicker { font-size: 0.75rem; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 0.1em; display: block; margin-bottom: 8px; }
.hero-card h2 { font-size: 2.22rem; color: var(--text-dark); margin: 0; }
.hero-card p { color: #6e7a74; margin-top: 8px; }
.filter-card { display: flex; gap: 15px; }
.player-info { display: flex; align-items: center; gap: 12px; }
.player-info .details { display: flex; flex-direction: column; }
.player-info .details span { font-size: 0.75rem; color: #9e9e9e; }
</style>
