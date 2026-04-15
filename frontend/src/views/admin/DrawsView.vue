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

// Tự động nhận diện Tên người dùng đang đăng nhập (hoặc fallback mặc định)
const currentUserName = computed(() => {
  return authStore.profile?.full_name || authStore.user?.full_name || 'Nguyen Cuu Minh Phu'
})

const fetchTournaments = async () => {
  try {
    const data = await tournamentService.getAll()
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
    ElMessage.success(`${response.message} (Tổng số VĐV: ${response.total_players}, Số vòng đấu: ${response.rounds})`)
    await fetchMatches()
  } catch (err) {
    const errorMsg = err.response?.data?.detail || err.message
    ElMessage.error('Lỗi bốc thăm: ' + errorMsg)
  } finally {
    generating.value = false
  }
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

  // Sắp xếp các vòng theo số lượng trận đấu giảm dần (VD: 4 trận Tứ kết -> 2 trận Bán kết -> 1 trận Chung kết)
  return Object.values(roundsMap).sort((a, b) => b.length - a.length)
})

onMounted(fetchTournaments)
</script>

<template>
  <div class="module-shell">
    <section class="hero-card">
      <div>
        <span class="section-kicker">Drawing Matrix</span>
        <h2>Quản lý Nhánh đấu</h2>
        <p>Sơ đồ thi đấu tự động cập nhật kết quả và đẩy người thắng vào vòng trong.</p>
      </div>
      <div class="hero-actions">
        <el-select v-model="selectedTournamentId" placeholder="Chọn giải đấu" style="width: 250px" @change="fetchMatches">
          <el-option v-for="t in tournaments" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button type="primary" :disabled="!selectedTournamentId" :loading="generating" @click="generateDraw">Tạo nhánh đấu mới</el-button>
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
         <div v-for="(round, index) in bracketRounds" :key="index" class="bracket-round">
            <div class="round-title">{{ round[0].round_code }}</div>
            
            <div class="matches-column">
               <div v-for="m in round" :key="m.id" class="match-wrapper">
                  <div class="match-card">
                     <div class="match-header">Trận #{{ m.match_no }} <span>• {{ m.status }}</span></div>
                     
                     <div class="match-body">
                        <div class="player-slot" 
                             :class="{ 
                               'winner': m.winner_side === 'side_a',
                               'highlight-me': m.p1_name === currentUserName 
                             }">
                           <span class="player-name">{{ m.p1_name }}</span>
                           <span v-if="m.result_note === 'BYE' && m.winner_side === 'side_a'" class="bye-badge">BYE</span>
                        </div>
                        
                        <div class="divider"></div>
                        
                        <div class="player-slot" 
                             :class="{ 
                               'winner': m.winner_side === 'side_b',
                               'highlight-me': m.p2_name === currentUserName 
                             }">
                           <span class="player-name">{{ m.p2_name }}</span>
                           <span v-if="m.result_note === 'BYE' && m.winner_side === 'side_b'" class="bye-badge">BYE</span>
                        </div>
                     </div>
                  </div>
                  <div class="connector" v-if="index < bracketRounds.length - 1"></div>
               </div>
            </div>
         </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.module-shell { display: grid; gap: 24px; }
.hero-card {
  background: white; padding: 24px; border-radius: 20px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.04);
  display: flex; justify-content: space-between; align-items: flex-end;
}
.section-kicker { font-size: 0.75rem; font-weight: 800; color: #006953; text-transform: uppercase; letter-spacing: 0.1em; display: block; margin-bottom: 8px; }
.hero-card h2 { font-size: 2.22rem; color: #123f34; margin: 0; }
.hero-card p { color: #6e7a74; margin-top: 8px; }
.hero-actions { display: flex; gap: 12px; }

/* BẢNG CHỨA SƠ ĐỒ */
.draw-container {
  background: #fdfdfd; padding: 32px; border-radius: 20px; min-height: 500px;
  overflow-x: auto; /* Cho phép cuộn ngang nếu nhánh đấu quá to */
  box-shadow: inset 0 2px 10px rgba(0,0,0,0.02);
}
.empty-state { text-align: center; color: #9e9e9e; padding-top: 100px; font-size: 1.1rem; }

/* KIẾN TRÚC BRACKET TREE */
.bracket-board {
  display: flex;
  gap: 60px; /* Khoảng cách giữa các Vòng */
  padding: 20px 0;
}

.bracket-round {
  display: flex;
  flex-direction: column;
  min-width: 240px;
}

.round-title {
  text-align: center;
  font-weight: 800;
  color: #006953;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e0e6e4;
  letter-spacing: 1px;
}

.matches-column {
  display: flex;
  flex-direction: column;
  justify-content: space-around; /* Phép màu nằm ở đây: Tự động dãn cách hội tụ */
  flex-grow: 1;
  gap: 20px;
}

/* THẺ TRẬN ĐẤU */
.match-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.match-card {
  width: 100%;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  overflow: hidden;
  position: relative;
  z-index: 2;
  transition: transform 0.2s;
}
.match-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.08);
}

.match-header {
  background: #f4f6f5;
  color: #6e7a74;
  padding: 6px 12px;
  font-size: 0.75rem;
  font-weight: 700;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #e0e0e0;
}

.match-body {
  display: flex;
  flex-direction: column;
}

.divider {
  height: 1px;
  background: #f0f0f0;
}

/* THÔNG TIN VẬN ĐỘNG VIÊN */
.player-slot {
  padding: 10px 12px;
  font-size: 0.9rem;
  font-weight: 500;
  color: #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-left: 4px solid transparent;
}

/* TRẠNG THÁI HIGHLIGHT */
.winner {
  background-color: #f0fdf4;
  color: #166534;
  font-weight: 700;
}

.highlight-me {
  border-left: 4px solid #f97316 !important; /* Màu cam nổi bật cho VĐV hiện tại */
  background-color: #fff7ed;
  font-weight: 700;
}
.highlight-me.winner {
  background-color: #dcfce7; /* Xanh nhẹ nếu vừa là người dùng vừa chiến thắng */
}

/* NHÃN VÉ ĐẶC CÁCH */
.bye-badge {
  background: #e2e8f0;
  color: #64748b;
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 800;
}

/* ĐƯỜNG LINE NỐI (CONNECTOR) */
.connector {
  position: absolute;
  right: -30px;
  top: 50%;
  width: 30px;
  height: 2px;
  background-color: #cbd5e1;
  z-index: 1;
}
</style>