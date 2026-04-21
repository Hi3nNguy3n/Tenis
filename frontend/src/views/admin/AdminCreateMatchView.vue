<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Trophy, Calendar, Location, User, Pointer, Check } from '@element-plus/icons-vue'
import apiClient from '../../services/apiClient'

const router = useRouter()

// Dữ liệu nguồn
const tournamentsList = ref([])
const playersList = ref([])
const courtsList = ref([])
const paidChallenges = ref([]) // Danh sách kèo đã nộp tiền

const loadingData = ref(true)
const submitting = ref(false)
const activeTab = ref('manual') // manual hoặc approve

// Dữ liệu Form
const form = ref({
  tournament_id: null,
  match_name: '',
  side_a_id: null,
  side_b_id: null,
  court_id: null,
  match_date: '',
  start_time: '',
  challenge_id: null // Lưu ID nếu đây là duyệt kèo thách đấu
})

const fetchInitialData = async () => {
  loadingData.value = true
  try {
    const [tourRes, playerResRaw, courtRes, challengeRes] = await Promise.all([
      apiClient.get('/api/tournaments/', { params: { limit: 100 } }),
      apiClient.get('/api/players/rankings'),
      apiClient.get('/api/courts/').catch(() => []),
      apiClient.get('/api/challenges/admin/pending-approvals').catch(() => [])
    ])
    
    tournamentsList.value = Array.isArray(tourRes) ? tourRes : []
    courtsList.value = Array.isArray(courtRes) ? courtRes : []
    paidChallenges.value = challengeRes

    const rawPlayers = Array.isArray(playerResRaw) ? playerResRaw : (playerResRaw?.items || [])
    playersList.value = rawPlayers.map(p => ({
      id: p.id || p.player_id, 
      full_name: p.full_name || p.user?.full_name || 'Vô danh',
      elo_points: p.elo_points || 1200
    }))
  } catch (error) {
    ElMessage.error('Lỗi khi tải dữ liệu khởi tạo.')
  } finally {
    loadingData.value = false
  }
}

// Khi Admin chọn 1 kèo từ danh sách nộp tiền
const selectChallenge = (c) => {
  form.value.side_a_id = c.side_a_id
  form.value.side_b_id = c.side_b_id
  form.value.match_date = c.proposed_date
  form.value.match_name = c.match_name
  form.value.challenge_id = c.id
  form.value.tournament_id = null
  activeTab.value = 'manual' // Nhảy về tab form để gán sân
  ElMessage.success(`Đã lấy thông tin kèo #${c.id}. Vui lòng chọn Sân và Giờ.`)
}

const submitMatch = async () => {
  if (!form.value.side_a_id || !form.value.side_b_id || !form.value.court_id || !form.value.start_time) {
    return ElMessage.warning('Vui lòng điền đủ VĐV, Sân và Giờ thi đấu.')
  }

  submitting.value = true
  try {
    // 1. Tạo trận đấu chính thức
    await apiClient.post('/api/matches/', form.value)
    
    // 2. Nếu đi từ Kèo thách đấu, gọi API cập nhật trạng thái kèo thành 'scheduled'
    if (form.value.challenge_id) {
       await apiClient.patch(`/api/challenges/${form.value.challenge_id}/respond`, { status: 'scheduled' })
    }

    ElMessage.success('Xác nhận & Xếp lịch thành công!')
    router.push({ path: '/admin/matches' })
  } catch (error) {
    ElMessage.error('Lỗi: ' + (error.response?.data?.detail || error.message))
  } finally {
    submitting.value = false
  }
}

const playerA = computed(() => playersList.value.find(p => p.id === form.value.side_a_id))
const playerB = computed(() => playersList.value.find(p => p.id === form.value.side_b_id))

onMounted(fetchInitialData)
</script>

<template>
  <div class="create-match-page" v-loading="loadingData">
    <div class="page-header">
      <div>
        <h1 class="page-title">Vận hành Trận đấu 1vs1</h1>
        <p class="page-subtitle">Quản lý gán lịch cho kèo thách đấu hoặc tạo trận thủ công.</p>
      </div>
      <el-button @click="router.back()" plain>Quay lại</el-button>
    </div>

    <el-tabs v-model="activeTab" type="border-card" class="main-tabs">
      <el-tab-pane name="approve">
        <template #label>
          <span class="tab-label"><el-icon><Pointer /></el-icon> Kèo cần gán lịch (PAID)</span>
          <el-badge v-if="paidChallenges.length" :value="paidChallenges.length" class="tab-badge" />
        </template>

        <div class="challenge-approval-list">
          <div v-for="c in paidChallenges" :key="c.id" class="challenge-item-card">
            <div class="c-info">
              <div class="c-players">
                <strong>{{ c.challenger_name }}</strong> <span>VS</span> <strong>{{ c.challenged_name }}</strong>
              </div>
              <div class="c-meta">
                <span><el-icon><Calendar /></el-icon> Ngày dự kiến: {{ c.proposed_date }}</span>
                <p v-if="c.notes" class="c-note">"{{ c.notes }}"</p>
              </div>
            </div>
            <el-button type="primary" :icon="Check" round @click="selectChallenge(c)">Gán lịch ngay</el-button>
          </div>
          <el-empty v-if="!paidChallenges.length" description="Hiện không có kèo thách đấu nào đang chờ duyệt." />
        </div>
      </el-tab-pane>

      <el-tab-pane name="manual">
        <template #label>
          <span class="tab-label"><el-icon><Trophy /></el-icon> Thiết lập chi tiết trận đấu</span>
        </template>

        <div class="form-container">
          <div class="form-section">
            <h3 class="section-title">1. Thông tin sự kiện</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="Thuộc Giải đấu (Nếu có)">
                  <el-select v-model="form.tournament_id" placeholder="Chọn giải" class="w-full" clearable filterable>
                    <el-option v-for="t in tournamentsList" :key="t.id" :label="t.name" :value="t.id" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="Tên trận đấu / Ghi chú">
                  <el-input v-model="form.match_name" placeholder="VD: Kèo Cafe, Trận giao hữu..." />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <div class="form-section arena-section">
            <h3 class="section-title">2. Cặp đấu</h3>
            <div class="vs-arena-compact">
              <div class="p-select">
                <el-select v-model="form.side_a_id" placeholder="VĐV A" filterable class="w-full">
                  <el-option v-for="p in playersList" :key="p.id" :label="p.full_name" :value="p.id" />
                </el-select>
                <div v-if="playerA" class="p-min-view">Elo: {{ playerA.elo_points }}</div>
              </div>
              <div class="vs-circle">VS</div>
              <div class="p-select">
                <el-select v-model="form.side_b_id" placeholder="VĐV B" filterable class="w-full">
                  <el-option v-for="p in playersList" :key="p.id" :label="p.full_name" :value="p.id" />
                </el-select>
                <div v-if="playerB" class="p-min-view">Elo: {{ playerB.elo_points }}</div>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h3 class="section-title">3. Gán sân & Thời gian</h3>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="Sân thi đấu" required>
                  <el-select v-model="form.court_id" placeholder="Chọn sân" class="w-full">
                    <el-option v-for="c in courtsList" :key="c.id" :label="c.court_name" :value="c.id" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="Ngày thi đấu" required>
                  <el-date-picker v-model="form.match_date" type="date" value-format="YYYY-MM-DD" class="w-full" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="Giờ bắt đầu" required>
                  <el-time-picker v-model="form.start_time" format="HH:mm" value-format="HH:mm:ss" class="w-full" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <div class="form-footer">
            <el-button type="primary" size="large" :loading="submitting" @click="submitMatch" class="btn-confirm">
              XÁC NHẬN & CẬP NHẬT LỊCH THI ĐẤU
            </el-button>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.create-match-page { padding: 24px; background: #f1f5f9; min-height: 100vh; }
.page-title { margin: 0; font-size: 1.6rem; color: #0f172a; }
.page-subtitle { color: #64748b; margin-bottom: 24px; }

.main-tabs { border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
.tab-label { display: flex; align-items: center; gap: 8px; font-weight: 700; }

/* Challenge List Styles */
.challenge-approval-list { display: grid; gap: 12px; padding: 10px; }
.challenge-item-card { 
  background: #fff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;
  display: flex; justify-content: space-between; align-items: center;
  transition: 0.2s;
}
.challenge-item-card:hover { border-color: var(--primary); transform: translateX(5px); }
.c-players strong { font-size: 1.1rem; color: #1e293b; }
.c-players span { margin: 0 15px; color: #ef4444; font-weight: 900; font-style: italic; }
.c-meta { margin-top: 8px; font-size: 0.85rem; color: #64748b; display: flex; gap: 20px; }
.c-note { margin: 4px 0 0; color: #94a3b8; font-style: italic; }

/* Form Section Styles */
.form-container { padding: 10px; }
.form-section { margin-bottom: 30px; }
.section-title { font-size: 0.9rem; color: var(--primary); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px;}

.vs-arena-compact { display: flex; align-items: center; gap: 20px; background: #f8fafc; padding: 25px; border-radius: 16px; border: 1px dashed #cbd5e1; }
.p-select { flex: 1; }
.p-min-view { margin-top: 5px; font-size: 0.75rem; color: #64748b; font-weight: bold; text-align: center;}
.vs-circle { width: 45px; height: 45px; background: #ef4444; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; box-shadow: 0 4px 10px rgba(239, 68, 68, 0.2); }

.form-footer { display: flex; justify-content: center; margin-top: 20px; }
.btn-confirm { padding: 0 50px; font-weight: 800; background: linear-gradient(135deg, #15803d, #166534); border: none; }
.w-full { width: 100%; }
</style>