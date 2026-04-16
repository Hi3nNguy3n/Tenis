<script setup>
import { computed, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { courtService } from '../../services/courtService'

const search = ref('')
const statusFilter = ref('')
const courts = ref([])
const isLoading = ref(false)
const isSaving = ref(false)
const isDialogOpen = ref(false)
const isEditMode = ref(false)

const surfaceOptions = ['HARD', 'CLAY', 'GRASS', 'CARPET']
const statusOptions = [
  { label: 'Hoạt động', value: 'AVAILABLE' },
  { label: 'Ngưng hoạt động', value: 'UNAVAILABLE' }
]

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
    const data = await courtService.getAll({ 
      search: search.value, 
      status: statusFilter.value 
    })
    courts.value = Array.isArray(data) ? data : (data.items || [])
  } catch (err) {
    ElMessage.error('Lỗi tải danh sách sân: ' + err.message)
  } finally {
    isLoading.value = false
  }
}

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
  if (!form.value.court_name || !form.value.location_name) {
    return ElMessage.warning('Vui lòng nhập tên và địa điểm sân')
  }
  
  isSaving.value = true
  try {
    if (isEditMode.value) {
      await courtService.update(form.value.id, form.value)
      ElMessage.success('Cập nhật thành công')
    } else {
      await courtService.create(form.value)
      ElMessage.success('Tạo sân thành công')
    }
    isDialogOpen.value = false
    loadCourts()
  } catch (err) {
    ElMessage.error('Lỗi khi lưu: ' + err.message)
  } finally {
    isSaving.value = false
  }
}

const deleteCourt = (id) => {
  ElMessageBox.confirm('Xóa sân này?', 'Cảnh báo', { type: 'warning' }).then(async () => {
    try {
      await courtService.delete(id)
      ElMessage.success('Đã xóa')
      loadCourts()
    } catch (err) {
      ElMessage.error('Lỗi khi xóa: ' + err.message)
    }
  })
}

onMounted(loadCourts)
</script>

<template>
  <div class="module-shell">
    <section class="hero-card">
      <div>
        <span class="section-kicker">Facilities management</span>
        <h2>Quản lý sân đấu</h2>
        <p>Cấu hình danh sách sân tại các cụm sân, theo dõi trạng thái bảo trì và loại mặt sân. Dữ liệu thực tế từ hệ thống.</p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" size="large" @click="openCreateDialog">Thêm sân mới</el-button>
        <el-button plain size="large" @click="loadCourts">Tải lại</el-button>
      </div>
    </section>

    <section class="filter-card">
      <el-input v-model="search" placeholder="Tìm theo tên sân, địa điểm..." clearable @change="loadCourts" style="width: 300px" />
      <el-select v-model="statusFilter" placeholder="Trạng thái" clearable @change="loadCourts" style="width: 180px">
        <el-option v-for="st in statusOptions" :key="st.value" :label="st.label" :value="st.value" />
      </el-select>
    </section>

    <section class="table-card">
      <el-table :data="courts" stripe v-loading="isLoading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="court_name" label="Tên sân" min-width="200" />
        <el-table-column prop="location_name" label="Địa điểm" min-width="220" />
        <el-table-column prop="surface_type" label="Mặt sân" width="120" />
        <el-table-column label="Trạng thái" width="140">
           <template #default="{ row }">
             <el-tag :type="row.is_active ? 'success' : 'danger'">
               {{ row.is_active ? 'ĐANG HOẠT ĐỘNG' : 'NGƯNG HOẠT ĐỘNG' }}
             </el-tag>
           </template>
        </el-table-column>
        <el-table-column label="Actions" width="150" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" type="primary" plain @click="openEditDialog(row)">Sửa</el-button>
              <el-button size="small" type="danger" plain @click="deleteCourt(row.id)">Xóa</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="courts.length === 0" description="Chưa có dữ liệu sân đấu" />
    </section>

    <el-dialog v-model="isDialogOpen" :title="isEditMode ? 'Sửa sân đấu' : 'Thêm sân mới'" width="500px">
      <el-form label-position="top">
        <el-form-item label="Tên sân" required>
          <el-input v-model="form.court_name" placeholder="VD: Sân số 1 - Lan Anh" />
        </el-form-item>
        <el-form-item label="Địa điểm (Cụm sân)" required>
          <el-input v-model="form.location_name" placeholder="VD: CLB Tennis Lan Anh, Q.10" />
        </el-form-item>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
           <el-form-item label="Mặt sân">
             <el-select v-model="form.surface_type" style="width: 100%">
               <el-option v-for="opt in surfaceOptions" :key="opt" :label="opt" :value="opt" />
             </el-select>
           </el-form-item>
           <el-form-item label="Trạng thái">
             <el-switch v-model="form.is_active" active-text="Hoạt động" inactive-text="Đã khóa" />
           </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="isDialogOpen = false">Hủy</el-button>
        <el-button type="primary" :loading="isSaving" @click="saveCourt">Lưu</el-button>
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
</style>
