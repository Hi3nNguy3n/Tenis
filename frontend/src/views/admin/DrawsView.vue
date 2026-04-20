<script setup>
import { onMounted, ref, computed } from 'vue'
import { tournamentService } from '../../services/tournamentService' 
import { useAuthStore } from '../../stores/auth' // Gọi Store để lấy thông tin VĐV đăng nhập
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const tournaments = ref([])
const selectedTournamentId = ref(null)
const matches = ref([])
const isLoading = ref(false)
const generating = ref(false)
const lastDrawSummary = ref(null)

// Tự động nhận diện Tên người dùng đang đăng nhập (hoặc fallback mặc định)
const currentUserName = computed(() => {
  return authStore.profile?.full_name || authStore.user?.full_name || 'Nguyen Cuu Minh Phu'
})

const fetchTournaments = async () => {
  try {
    // Lấy toàn bộ danh sách giải đấu để admin chọn (Limit lớn)
    const data = await tournamentService.getAll({ limit: 100 })
    tournaments.value = data
  } catch (err) {
    ElMessage.error('Lỗi tải danh sách giải: ' + err.message)
  }
}

const fetchMatches = async () => {
  if (!selectedTournamentId.value) return
  isLoading.value = true
  try {
    const data = await tournamentService.getMatches(selectedTournamentId.value)
    matches.value = data
  } catch (err) {
    ElMessage.error('Lỗi tải nhánh đấu: ' + err.message)
    matches.value = []
  } finally {
    isLoading.value = false
  }
}

const generateDraw = async () => {
  if (!selectedTournamentId.value) return
  generating.value = true
  try {
    const response = await tournamentService.generateDraw(selectedTournamentId.value)
    lastDrawSummary.value = response
    ElMessage.success(`${response.message} (Tổng số VĐV: ${response.total_players}, Số vòng đấu: ${response.rounds})`)
    await fetchMatches()
  } catch (err) {
    const errorMsg = err.response?.data?.detail || err.message
    ElMessage.error('Lỗi bốc thăm: ' + errorMsg)
  } finally {
    generating.value = false
  }
}

const roundOrder = (roundCode) => {
  const normalized = String(roundCode || '').toUpperCase()
  const orderMap = {
    R128: 1,
    R64: 2,
    R32: 3,
    R16: 4,
    R8: 5,
    QF: 6,
    SF: 7,
    F: 8,
    FINAL: 8,
  }

  return orderMap[normalized] ?? 99
}

// XỬ LÝ DỮ LIỆU SƠ ĐỒ (BRACKET LOGIC)
// Gom nhóm các trận đấu theo Vòng (Round) và sắp xếp từ vòng ngoài vào Chung kết
const bracketRounds = computed(() => {
  if (!matches.value || matches.value.length === 0) return []

  const roundsMap = {}
  matches.value.forEach(m => {
    if (!roundsMap[m.round_code]) {
      roundsMap[m.round_code] = []
    }
    roundsMap[m.round_code].push(m)
  })

  return Object.entries(roundsMap)
    .map(([roundCode, items]) => ({
      roundCode,
      items: items.slice().sort((a, b) => (a.match_no || 0) - (b.match_no || 0)),
    }))
    .sort((a, b) => roundOrder(a.roundCode) - roundOrder(b.roundCode))
})

onMounted(fetchTournaments)
</script>

<template>
  <div class="module-shell">
    <!-- HEADER PREMIUM -->
    <section class="action-bar-glass shadow-sm">
      <div class="action-info">
        <div class="kicker-wrap">
          <span class="section-kicker">Drawing Matrix</span>
          <div class="live-indicator">
            <span class="dot"></span>
            ACTIVE
          </div>
        </div>
        <p>Phân bổ hạt giống (Seeding) và bốc thăm tự động cho giải đấu.</p>
        <p v-if="lastDrawSummary" class="draw-summary">
          Đã tạo: {{ lastDrawSummary.total_players }} VĐV | {{ lastDrawSummary.seeded }} seed | {{ lastDrawSummary.byes }} bye
        </p>
      </div>
      <div class="hero-actions">
        <div class="control-group-v2">
          <el-select v-model="selectedTournamentId" placeholder="-- Lấy giải đấu --" style="width: 240px" @change="fetchMatches" filterable round>
            <el-option v-for="t in tournaments" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
          <el-button type="primary" :disabled="!selectedTournamentId" :loading="generating" @click="generateDraw" class="btn-generate-premium" round>
            Bắt đầu Bốc thăm & Tạo Nhánh
          </el-button>
        </div>
      </div>
    </section>

    <section class="draw-container" v-loading="isLoading">
      <div v-if="!selectedTournamentId" class="empty-state">
        <p>Vui lòng chọn một giải đấu để xem hoặc tạo sơ đồ nhánh đấu.</p>
      </div>
      <div v-else-if="matches.length === 0" class="empty-state">
        <p>Giải đấu này chưa có nhánh đấu. Nhấn "Tạo nhánh đấu mới" để hệ thống tự động bốc thăm.</p>
      </div>
      
      <div v-else class="bracket-board">
         <div v-for="(round, index) in bracketRounds" :key="round.roundCode" class="bracket-round">
            <div class="round-header">
               <span class="round-tag">{{ round.roundCode }}</span>
            </div>
            
            <div class="matches-column">
               <div v-for="m in round.items" :key="m.id" class="match-wrapper">
                  <div class="match-card-premium">
                     <div class="match-top">
                        <span class="m-no">#{{ m.match_no }}</span>
                        <span class="m-status" :class="m.status">{{ m.status?.toUpperCase() }}</span>
                     </div>
                     
                     <div class="match-players">
                        <div class="p-row" :class="{ 'is-winner': m.winner_side === 'side_a', 'is-me': m.p1_name === currentUserName }">
                           <div class="p-name-wrap">
                             <span class="side-chip">{{ m.p1_label || 'VĐV' }}</span>
                             <span class="p-name">{{ m.p1_name || 'Đang cập nhật...' }}</span>
                             <el-tag v-if="m.seed_a" size="small" effect="plain" class="seed-tag">#{{ m.seed_a }}</el-tag>
                           </div>
                           <el-tag v-if="m.result_note === 'BYE' && m.winner_side === 'side_a'" size="small" effect="dark" type="info" class="bye-tag">BYE</el-tag>
                        </div>
                        
                        <div class="p-row" :class="{ 'is-winner': m.winner_side === 'side_b', 'is-me': m.p2_name === currentUserName }">
                           <div class="p-name-wrap">
                             <span class="side-chip">{{ m.p2_label || 'VĐV' }}</span>
                             <span class="p-name">{{ m.p2_name || 'Đang chờ đối thủ...' }}</span>
                             <el-tag v-if="m.seed_b" size="small" effect="plain" class="seed-tag">#{{ m.seed_b }}</el-tag>
                           </div>
                           <el-tag v-if="m.result_note === 'BYE' && m.winner_side === 'side_b'" size="small" effect="dark" type="info" class="bye-tag">BYE</el-tag>
                        </div>
                     </div>
                  </div>
                  <div class="connector-line" v-if="index < bracketRounds.length - 1"></div>
               </div>
            </div>
         </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.module-shell { display: grid; gap: 20px; padding: 10px; }

.action-bar-glass {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  padding: 20px 24px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 10px 30px rgba(0,0,0,0.03);
}

.kicker-wrap { display: flex; align-items: center; gap: 12px; margin-bottom: 2px; }
.section-kicker { font-size: 0.7rem; font-weight: 800; color: #1e293b; text-transform: uppercase; letter-spacing: 0.05em; }

.live-indicator {
  display: flex; align-items: center; gap: 6px;
  background: #f0fdf4; color: #15803d; font-size: 0.65rem; font-weight: 800;
  padding: 2px 8px; border-radius: 99px;
}
.dot { width: 6px; height: 6px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite; }

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}

.action-info p { color: #64748b; font-size: 0.9rem; margin: 0; }
.draw-summary { margin-top: 6px; font-size: 0.82rem !important; color: #0f172a !important; }

.control-group-v2 { display: flex; gap: 12px; align-items: center; }
.btn-generate-premium {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border: none;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
  transition: all 0.3s ease;
}
.btn-generate-premium:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3);
}

.draw-container {
  background: white; padding: 40px; border-radius: 24px; min-height: 600px;
  border: 1px solid #f1f5f9; box-shadow: 0 10px 40px rgba(0,0,0,0.02);
  overflow-x: auto;
}

.bracket-board { display: flex; gap: 80px; padding: 20px 0; }
.bracket-round { display: flex; flex-direction: column; min-width: 260px; }

.round-header { text-align: center; margin-bottom: 30px; position: relative; }
.round-tag {
  background: #f8fafc; color: #1e293b; padding: 6px 20px; border-radius: 99px;
  font-weight: 800; font-size: 0.75rem; text-transform: uppercase;
  border: 1px solid #e2e8f0;
}

.matches-column { display: flex; flex-direction: column; justify-content: space-around; flex-grow: 1; gap: 40px; }

.match-wrapper { position: relative; display: flex; align-items: center; width: 100%; }

.match-card-premium {
  width: 100%; background: white; border-radius: 16px; border: 1px solid #e2e8f0;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02), 0 2px 4px -1px rgba(0,0,0,0.01);
  overflow: hidden; z-index: 2; transition: all 0.3s ease;
}
.match-card-premium:hover {
  transform: scale(1.02); border-color: #3b82f6;
  box-shadow: 0 20px 25px -5px rgba(0,0,0,0.05);
}

.match-top {
  background: #f8fafc; padding: 8px 12px; display: flex; justify-content: space-between;
  align-items: center; border-bottom: 1px solid #f1f5f9;
}
.m-no { font-size: 0.65rem; font-weight: 800; color: #94a3b8; }
.m-status { font-size: 0.6rem; font-weight: 800; padding: 2px 8px; border-radius: 4px; }
.m-status.pending { background: #fff7ed; color: #c2410c; }
.m-status.completed { background: #f0fdf4; color: #15803d; }

.match-players { padding: 4px; display: grid; gap: 2px; }
.p-row {
  padding: 10px 12px; border-radius: 10px; display: flex; justify-content: space-between;
  align-items: center; transition: all 0.2s ease;
}
.p-name-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.p-name { font-size: 0.9rem; font-weight: 600; color: #334155; }
.seed-tag { font-size: 0.65rem; font-weight: 700; }

.is-winner { background: #f0fdf4; }
.is-winner .p-name { color: #15803d; font-weight: 700; }
.is-me { border: 1px solid #fb923c; background: #fff7ed; }

.bye-tag { font-size: 0.6rem; font-weight: 900; }

.connector-line {
  position: absolute; right: -40px; top: 50%; width: 40px; height: 1.5px;
  background: #e2e8f0; z-index: 1;
}
</style>
