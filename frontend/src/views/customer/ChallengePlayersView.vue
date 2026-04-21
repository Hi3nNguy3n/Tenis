<script setup>
import { ref, onMounted, computed } from 'vue'
import { Trophy, DataAnalysis, Calendar, Message, Aim } from '@element-plus/icons-vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'

const players = ref([])
const isLoading = ref(false)
const selectedOpponent = ref(null)

// --- Dialog Thách đấu ---
const showChallengeDialog = ref(false)
const challengeForm = ref({ date: '', notes: '' })

// --- Dialog Lịch sử đối đầu (Head-to-Head) ---
const showH2HDialog = ref(false)
const h2hHistory = ref([])

const loadPlayers = async () => {
  isLoading.value = true
  try {
    const data = await apiClient.get('/api/players/rankings')
    players.value = data
  } catch (err) { ElMessage.error('Lỗi tải danh sách VĐV') }
  finally { isLoading.value = false }
}

const openChallenge = (p) => {
  selectedOpponent.value = p
  showChallengeDialog.value = true
}

const sendChallengeRequest = async () => {
  if (!challengeForm.value.date) return ElMessage.warning('Vui lòng chọn ngày dự kiến')
  try {
    await apiClient.post('/api/challenges/', {
      challenged_id: selectedOpponent.value.player_id,
      proposed_date: challengeForm.value.date,
      notes: challengeForm.value.notes
    })
    ElMessage.success('Đã gửi lời mời thách đấu! Vui lòng chờ đối thủ xác nhận.')
    showChallengeDialog.value = false
  } catch (err) { ElMessage.error('Lỗi gửi lời mời') }
}

const viewH2H = async (p) => {
  selectedOpponent.value = p
  showH2HDialog.value = true
  // Giả lập lấy dữ liệu H2H từ API
  // const data = await apiClient.get(`/api/matches/h2h?opponent_id=${p.player_id}`)
  h2hHistory.value = [
    { date: '2026-03-15', score: '6-4, 6-2', winner: 'Bạn' },
    { date: '2026-02-10', score: '3-6, 4-6', winner: p.full_name }
  ]
}

onMounted(loadPlayers)
</script>

<template>
  <div class="challenge-page container">
    <div class="page-header">
      <h1 class="title">Sảnh Thách Đấu 1vs1</h1>
      <p class="subtitle">Tìm kiếm đối thủ xứng tầm và tổ chức trận đấu riêng của bạn.</p>
    </div>

    <div class="players-grid" v-loading="isLoading">
      <div v-for="p in players" :key="p.player_id" class="player-card">
        <div class="card-top">
          <el-avatar :size="80" :src="p.avatar_url" />
          <div class="rank-badge">#{{ p.rank }}</div>
        </div>
        
        <h3 class="name">{{ p.full_name }}</h3>
        <div class="elo-tag">{{ p.elo_points }} ELO</div>

        <div class="stats-mini">
          <div class="stat"><span class="val">{{ p.wins }}</span><span class="lbl">Thắng</span></div>
          <div class="stat"><span class="val">{{ p.losses }}</span><span class="lbl">Bại</span></div>
        </div>

        <div class="card-actions">
          <el-button type="primary" :icon="Aim" class="btn-challenge" @click="openChallenge(p)">Thách đấu</el-button>
          <el-button plain :icon="DataAnalysis" @click="viewH2H(p)">H2H</el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="showChallengeDialog" title="Gửi lời mời thách đấu" width="400px">
      <div class="opponent-preview" v-if="selectedOpponent">
        Thách đấu với: <strong>{{ selectedOpponent.full_name }}</strong>
      </div>
      <el-form label-position="top">
        <el-form-item label="Ngày thi đấu dự kiến" required>
          <el-date-picker v-model="challengeForm.date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="Lời nhắn">
          <el-input v-model="challengeForm.notes" type="textarea" placeholder="Ví dụ: Giao lưu 2 set cafe bác nhé..." />
        </el-form-item>
        <div class="fee-notice">Phí duy trì hệ thống & sân bãi: 200.000 VNĐ</div>
      </el-form>
      <template #footer>
        <el-button @click="showChallengeDialog = false">Hủy</el-button>
        <el-button type="primary" @click="sendChallengeRequest">Xác nhận gửi</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showH2HDialog" title="Lịch sử đối đầu (H2H)" width="500px">
      <div v-if="selectedOpponent" class="h2h-summary">
        Bạn vs {{ selectedOpponent.full_name }}
      </div>
      <el-table :data="h2hHistory" stripe>
        <el-table-column prop="date" label="Ngày" />
        <el-table-column prop="score" label="Tỷ số" />
        <el-table-column prop="winner" label="Người thắng">
          <template #default="{ row }">
            <el-tag :type="row.winner === 'Bạn' ? 'success' : 'danger'">{{ row.winner }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<style scoped>
.challenge-page { padding: 40px 0; }
.page-header { text-align: center; margin-bottom: 40px; }
.title { font-size: 2.2rem; color: #1e293b; font-weight: 800; }
.subtitle { color: #64748b; }

.players-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px; }
.player-card { 
  background: white; border-radius: 20px; padding: 24px; border: 1px solid #e2e8f0;
  text-align: center; transition: 0.3s;
}
.player-card:hover { transform: translateY(-8px); box-shadow: 0 15px 30px rgba(0,0,0,0.08); }

.card-top { position: relative; display: inline-block; margin-bottom: 15px; }
.rank-badge { 
  position: absolute; bottom: 0; right: 0; background: #fbbf24; 
  color: #92400e; font-weight: 800; font-size: 0.75rem;
  padding: 4px 8px; border-radius: 10px; border: 3px solid white;
}

.name { margin: 10px 0 5px; color: #0f172a; }
.elo-tag { background: #f1f5f9; color: #475569; font-weight: 700; font-size: 0.8rem; padding: 4px 12px; border-radius: 20px; display: inline-block; }

.stats-mini { display: flex; justify-content: center; gap: 30px; margin: 20px 0; }
.stat { display: flex; flex-direction: column; }
.stat .val { font-weight: 800; color: #1e293b; }
.stat .lbl { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; }

.card-actions { display: flex; flex-direction: column; gap: 10px; }
.btn-challenge { background: linear-gradient(135deg, #15803d, #166534); border: none; font-weight: 700; }

.fee-notice { background: #fffbeb; color: #b45309; padding: 12px; border-radius: 10px; font-size: 0.85rem; font-weight: 600; margin-top: 15px; text-align: center; }
</style>