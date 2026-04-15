<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import { Trophy, Medal, Location, Connection } from '@element-plus/icons-vue'

const rankings = ref([])
const isLoading = ref(true)

// Khai báo state cho bộ lọc
const filters = ref({
  category: '',
  province: ''
})

// Danh sách 34 Tỉnh/Thành phố Việt Nam (Đồng bộ với form Đăng ký)
const provinces = [
  "An Giang", "Bắc Ninh", "Cà Mau", "Cao Bằng", "Đắk Lắk", 
  "Điện Biên", "Đồng Nai", "Đồng Tháp", "Gia Lai", "Hà Tĩnh", 
  "Hưng Yên", "Khánh Hòa", "Lai Châu", "Lâm Đồng", "Lạng Sơn", 
  "Lào Cai", "Nghệ An", "Ninh Bình", "Phú Thọ", "Quảng Ngãi", 
  "Quảng Ninh", "Quảng Trị", "Sơn La", "Tây Ninh", "Thái Nguyên", 
  "Thanh Hóa", "TP Cần Thơ", "TP Đà Nẵng", "TP Hà Nội", "TP Hải Phòng", 
  "TP Hồ Chí Minh", "TP Huế", "Tuyên Quang", "Vĩnh Long"
]

const categories = [
  { label: 'Đơn (Singles)', value: 'Singles' },
  { label: 'Đôi (Doubles)', value: 'Doubles' }
]

const fetchRankings = async () => {
  isLoading.value = true
  try {
    // 1. Bắt đầu với URL gốc
    let url = '/api/players/rankings'
    
    // 2. Tạo mảng chứa các điều kiện lọc
    const queryParts = []
    
    if (filters.value.category) {
      queryParts.push(`category=${encodeURIComponent(filters.value.category)}`)
    }
    
    if (filters.value.province) {
      queryParts.push(`province=${encodeURIComponent(filters.value.province)}`)
    }
    
    // 3. Nếu có điều kiện lọc, nối vào URL với dấu '?'
    if (queryParts.length > 0) {
      url += '?' + queryParts.join('&')
    }

    // 4. Gọi API với URL đã được nối hoàn chỉnh (VD: /api/players/rankings?province=An%20Giang)
    const data = await apiClient.get(url)
    rankings.value = data
  } catch (error) {
    ElMessage.error('Không thể tải Bảng xếp hạng')
  } finally {
    isLoading.value = false
  }
}

const getRankClass = (rank) => {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return 'rank-normal'
}

onMounted(fetchRankings)
</script>

<template>
  <div class="ranking-page">
    <div class="hero-banner">
      <el-icon class="bg-icon"><Trophy /></el-icon>
      <h1>Bảng Xếp Hạng Global</h1>
      <p>Nơi vinh danh những tay vợt xuất sắc nhất hệ thống Saigon Tennis Tour dựa trên điểm số Elo.</p>
    </div>

    <div class="ranking-container">
      <div class="filter-bar">
        <el-select 
          v-model="filters.category" 
          placeholder="Tất cả nội dung" 
          clearable 
          size="large"
          class="filter-item"
          @change="fetchRankings">
          <template #prefix><el-icon><Connection /></el-icon></template>
          <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>

        <el-select 
          v-model="filters.province" 
          placeholder="Tất cả khu vực" 
          clearable 
          filterable
          size="large"
          class="filter-item"
          @change="fetchRankings">
          <template #prefix><el-icon><Location /></el-icon></template>
          <el-option v-for="p in provinces" :key="p" :label="p" :value="p" />
        </el-select>
      </div>

      <div class="leaderboard" v-loading="isLoading">
        <div v-if="rankings.length === 0" class="empty-state">
          <el-empty description="Chưa có vận động viên nào phù hợp với bộ lọc." />
        </div>
        
        <div v-else>
          <div class="lb-header">
            <div class="col-rank">Hạng</div>
            <div class="col-player">Vận động viên</div>
            <div class="col-stats hidden-mobile">Trình độ</div>
            <div class="col-stats">Trận đấu</div>
            <div class="col-stats">Tỷ lệ thắng</div>
            <div class="col-points">Điểm Elo</div>
          </div>

          <div v-for="player in rankings" :key="player.player_id" class="lb-row" :class="getRankClass(player.rank)">
            <div class="col-rank">
              <div class="rank-badge">
                <span v-if="player.rank > 3">{{ player.rank }}</span>
                <el-icon v-else size="24"><Medal /></el-icon>
              </div>
            </div>
            
            <div class="col-player">
              <div class="player-info">
                <div class="avatar">
                  <img v-if="player.avatar_url" :src="player.avatar_url" alt="avatar" />
                  <span v-else>👤</span>
                </div>
                <div class="name-details">
                  <strong>{{ player.full_name }}</strong>
                  <span class="location-tag" v-if="player.province">
                    <el-icon><Location /></el-icon> {{ player.province }}
                  </span>
                </div>
              </div>
            </div>

            <div class="col-stats hidden-mobile">
              <el-tag size="small" effect="plain" type="info">{{ player.skill_level }}</el-tag>
            </div>

            <div class="col-stats">
              <div class="win-loss">
                <span class="wins">{{ player.wins }}W</span> - <span class="losses">{{ player.losses }}L</span>
              </div>
              <div class="matches-total">{{ player.matches_played }} trận</div>
            </div>

            <div class="col-stats">
              <div class="win-rate">
                <div class="rate-bar-bg">
                  <div class="rate-bar-fill" :style="{ width: player.win_rate + '%' }"></div>
                </div>
                <span class="rate-text">{{ player.win_rate }}%</span>
              </div>
            </div>

            <div class="col-points">
              <span class="elo-score">{{ player.elo_points }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ranking-page { background: #f4f7f6; min-height: 100vh; padding-bottom: 50px; }

.hero-banner { 
  background: linear-gradient(135deg, #006953 0%, #123f34 100%);
  color: white; padding: 60px 20px 80px; text-align: center;
  position: relative; overflow: hidden;
}
.hero-banner h1 { font-size: 2.8rem; margin: 0 0 10px 0; position: relative; z-index: 2; }
.hero-banner p { font-size: 1.1rem; opacity: 0.9; max-width: 600px; margin: 0 auto; position: relative; z-index: 2; }
.bg-icon { position: absolute; font-size: 250px; color: rgba(255,255,255,0.05); top: -50px; right: 10%; z-index: 1; transform: rotate(15deg); }

.ranking-container { max-width: 1000px; margin: -50px auto 0; padding: 0 20px; position: relative; z-index: 10; }

/* Filter Bar Styles */
.filter-bar {
  display: flex; gap: 15px; margin-bottom: 20px;
  background: white; padding: 15px; border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}
.filter-item { flex: 1; }

/* Leaderboard Styles */
.leaderboard { background: white; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.08); overflow: hidden; }
.lb-header, .lb-row { 
  display: grid; grid-template-columns: 80px 3fr 1fr 1fr 1.5fr 120px;
  align-items: center; padding: 16px 20px;
}
.lb-header { background: #f8fafc; font-weight: 800; color: #64748b; font-size: 0.85rem; text-transform: uppercase; border-bottom: 2px solid #e2e8f0; }
.lb-row { border-bottom: 1px solid #f1f5f9; transition: background 0.2s; }
.lb-row:hover { background: #f8fafc; }

.col-rank { text-align: center; }
.col-points { text-align: right; }

.rank-badge { 
  width: 40px; height: 40px; border-radius: 50%; display: flex; justify-content: center; align-items: center;
  margin: 0 auto; font-weight: 800; color: #94a3b8; background: #f1f5f9;
}
.rank-gold .rank-badge { background: #fef08a; color: #ca8a04; box-shadow: 0 4px 10px rgba(202,138,4,0.2); }
.rank-silver .rank-badge { background: #e2e8f0; color: #475569; }
.rank-bronze .rank-badge { background: #ffedd5; color: #c2410c; }

.player-info { display: flex; align-items: center; gap: 15px; }
.avatar { width: 45px; height: 45px; border-radius: 50%; background: #e2e8f0; overflow: hidden; display: flex; justify-content: center; align-items: center; font-size: 1.5rem; }
.avatar img { width: 100%; height: 100%; object-fit: cover; }
.name-details { display: flex; flex-direction: column; }
.name-details strong { font-size: 1.05rem; color: #1e293b; }
.location-tag { font-size: 0.75rem; color: #64748b; margin-top: 4px; display: flex; align-items: center; gap: 4px; }

.wins { color: #16a34a; font-weight: 800; }
.losses { color: #dc2626; font-weight: 800; }
.matches-total { font-size: 0.75rem; color: #94a3b8; margin-top: 4px; }

.win-rate { display: flex; align-items: center; gap: 10px; }
.rate-bar-bg { flex-grow: 1; height: 6px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }
.rate-bar-fill { height: 100%; background: linear-gradient(90deg, #10b981, #3b82f6); border-radius: 4px; }
.rate-text { font-size: 0.85rem; font-weight: 700; color: #475569; width: 40px; text-align: right; }

.elo-score { font-size: 1.4rem; font-weight: 900; color: #006953; }
.rank-gold .elo-score { color: #ca8a04; }

@media (max-width: 768px) {
  .hidden-mobile { display: none; }
  .filter-bar { flex-direction: column; }
  .lb-header, .lb-row { grid-template-columns: 60px 2fr 1fr 80px; padding: 12px 10px; }
  .rate-bar-bg { display: none; }
  .win-rate { justify-content: flex-end; }
  .avatar { width: 35px; height: 35px; }
  .name-details strong { font-size: 0.95rem; }
}
</style>