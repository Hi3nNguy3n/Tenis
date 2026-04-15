<script setup>
import { onMounted, computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTournamentStore } from '../../../stores/tournament'
import { useAuthStore } from '../../../stores/auth'
import { apiClient } from '../../../services/apiClient' // Thêm apiClient để gọi API Bracket

const route = useRoute()
const router = useRouter()
const tournamentStore = useTournamentStore()
const authStore = useAuthStore()

const tournamentId = route.params.id

// State cho Tabs và Sơ đồ
const activeTab = ref('info')
const publicMatches = ref([])
const loadingBracket = ref(false)

onMounted(async () => {
  tournamentStore.fetchTournamentById(tournamentId)
  fetchBracket()
})

const fetchBracket = async () => {
  loadingBracket.value = true
  try {
    const data = await apiClient.get(`/api/tournaments/${tournamentId}/public-bracket`)
    publicMatches.value = data
  } catch (err) {
    console.error("Không tải được sơ đồ nhánh đấu:", err)
  } finally {
    loadingBracket.value = false
  }
}

// Logic gom nhóm trận đấu theo Vòng (Round) để vẽ sơ đồ
const groupedMatches = computed(() => {
  const groups = {}
  publicMatches.value.forEach(m => {
    if (!groups[m.round_code]) groups[m.round_code] = []
    groups[m.round_code].push(m)
  })
  const order = ['FINAL', 'SF', 'QF', 'R16', 'R32', 'R64']
  return Object.keys(groups)
    .sort((a, b) => order.indexOf(a) - order.indexOf(b))
    .map(key => ({
      label: key,
      items: groups[key].sort((a, b) => a.match_no - b.match_no)
    }))
})

const t = computed(() => tournamentStore.currentTournament)

const goToRegister = () => {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  router.push({ name: 'tournament-register', params: { id: tournamentId } })
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'TBA'
  return new Date(dateStr).toLocaleDateString('vi-VN', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}
</script>

<template>
  <div v-if="t" class="detail-page">
    <div class="hero-banner">
      <div class="container hero-content">
        <div class="status-badge" :class="t.status">{{ t.status.toUpperCase() }}</div>
        <h1>{{ t.name }}</h1>
        <div class="hero-meta">
          <span class="meta-item">📅 {{ formatDate(t.start_date) }} - {{ formatDate(t.end_date) }}</span>
          <span class="meta-item">📍 {{ t.location || '---' }}</span>
        </div>
      </div>
    </div>

    <div class="container main-content">
      <div class="content-grid">
        <div class="info-section">
          
          <el-tabs v-model="activeTab" class="custom-tabs">
            
            <el-tab-pane label="Thông tin giải đấu" name="info">
              <section class="overview">
                <div class="info-cards">
                  <div class="info-card">
                    <span class="label">Hạng mục</span>
                    <span class="value">{{ t.category_type }}</span>
                  </div>
                  <div class="info-card">
                    <span class="label">Nội dung</span>
                    <span class="value">{{ t.gender_division }}</span>
                  </div>
                  <div class="info-card">
                    <span class="label">Hình thức</span>
                    <span class="value">{{ t.format_type }}</span>
                  </div>
                  <div class="info-card">
                    <span class="label">Quy mô</span>
                    <span class="value">{{ t.draw_size }} người</span>
                  </div>
                </div>
                
                <div class="description">
                  <h3>Thông tin chi tiết</h3>
                  <p>
                    Chào mừng bạn đến với {{ t.name }}. Đây là giải đấu thuộc hệ thống điểm thưởng Saigon Tennis Tour, 
                    nơi bạn có cơ hội giao lưu, học hỏi và cải thiện trình độ Elo của mình.
                  </p>
                  <ul>
                    <li>Thời gian đăng ký: {{ formatDate(t.registration_open_at) }} đến {{ formatDate(t.registration_close_at) }}</li>
                    <li>Mặt sân: {{ t.surface_type || 'Cứng (Hard Court)' }}</li>
                  </ul>
                </div>
              </section>
            </el-tab-pane>

            <el-tab-pane label="Sơ đồ thi đấu (Live)" name="bracket">
              <div v-loading="loadingBracket" class="bracket-wrapper">
                <div v-if="publicMatches.length === 0" class="empty-bracket">
                  <p>Sơ đồ thi đấu chưa được bốc thăm.</p>
                </div>
                
                <div v-else class="bracket-scroll">
                  <div v-for="round in groupedMatches" :key="round.label" class="round-column">
                    <h3 class="round-title">{{ round.label }}</h3>
                    <div class="match-list">
                      <div v-for="m in round.items" :key="m.id" class="public-match-card">
                        
                        <div class="p-item" :class="{ 'is-winner': m.winner_side === 'side_a' }">
                          <span class="p-name">{{ m.p1_name }}</span>
                          <el-icon v-if="m.winner_side === 'side_a'"><Check /></el-icon>
                        </div>
                        
                        <div class="p-item" :class="{ 'is-winner': m.winner_side === 'side_b' }">
                          <span class="p-name">{{ m.p2_name }}</span>
                          <el-icon v-if="m.winner_side === 'side_b'"><Check /></el-icon>
                        </div>

                        <div v-if="m.score" class="match-score">
                          Tỷ số: <strong>{{ m.score }}</strong>
                        </div>
                        <div v-else-if="m.status === 'completed'" class="match-score">
                          Đã kết thúc
                        </div>

                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>

        </div>

        <aside class="sidebar">
          <div class="sticky-card action-card">
            <h3>Đăng ký tham gia</h3>
            <div class="price-wrap">
              <span class="price-label">Lệ phí</span>
              <span class="price-value">{{ t.entry_fee ? new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(t.entry_fee) : 'Miễn phí' }}</span>
            </div>
            
            <div class="registration-meta">
              <div class="slot-info">
                <span class="slot-count">{{ t.current_participants }} / {{ t.max_participants || t.draw_size }}</span>
                <span class="slot-label">Slots đã đăng ký</span>
              </div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: Math.min(100, (t.current_participants / (t.max_participants || t.draw_size)) * 100) + '%' }"></div>
              </div>
            </div>

            <div v-if="t.status === 'open'" class="registration-info">
              <p class="deadline">Hạn đăng ký: {{ formatDate(t.registration_close_at) }}</p>
              <button 
                class="btn-register" 
                @click="goToRegister" 
                :disabled="t.current_participants >= (t.max_participants || t.draw_size)"
              >
                {{ t.current_participants >= (t.max_participants || t.draw_size) ? 'Đã hết chỗ' : 'Đăng ký ngay' }}
              </button>
            </div>
            <div v-else class="status-message">
              <p v-if="t.status === 'draft'">Giải đấu chưa mở đăng ký.</p>
              <p v-else-if="t.status === 'ongoing'">Giải đấu đang diễn ra.</p>
              <p v-else>Giải đấu đã kết thúc.</p>
              <button class="btn-disabled" disabled>Đăng ký đã đóng</button>
            </div>
          </div>
        </aside>
      </div>
    </div>
  </div>
  
  <div v-else-if="tournamentStore.loading" class="loading-full">
    <div class="spinner"></div>
    <p>Đang tải thông tin giải đấu...</p>
  </div>
</template>

<style scoped>
.detail-page { background: #f8f9f9; min-height: 100vh; }
.hero-banner { background: linear-gradient(135deg, #123f34 0%, #006953 100%); color: white; padding: 8rem 0 4rem; }
.status-badge { display: inline-block; padding: 0.5rem 1rem; border-radius: 999px; font-weight: 800; font-size: 0.75rem; letter-spacing: 0.1em; margin-bottom: 1.5rem; background: rgba(255, 255, 255, 0.2); }
.status-badge.open { background: #4caf50; }
.status-badge.ongoing { background: #ff9800; }
.status-badge.finished { background: #757575; }
.hero-content h1 { font-size: clamp(2.5rem, 5vw, 4rem); margin-bottom: 1.5rem; line-height: 1.1; }
.hero-meta { display: flex; gap: 2rem; font-size: 1.1rem; opacity: 0.9; }
.main-content { padding-top: 3rem; padding-bottom: 6rem; }
.content-grid { display: grid; grid-template-columns: 1fr 350px; gap: 3rem; }

/* Custom Tabs */
.custom-tabs { margin-bottom: 2rem; }
:deep(.el-tabs__item) { font-size: 1.1rem; font-weight: 700; height: 50px; line-height: 50px; }
:deep(.el-tabs__item.is-active) { color: #006953; }
:deep(.el-tabs__active-bar) { background-color: #006953; height: 3px; }

.info-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; margin: 2rem 0; }
.info-card { background: white; padding: 1.5rem; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.03); }
.info-card .label { display: block; font-size: 0.8rem; text-transform: uppercase; color: #6e7a74; margin-bottom: 0.5rem; }
.info-card .value { font-size: 1.2rem; font-weight: 700; color: #123f34; }
.description h3 { margin: 2rem 0 1rem; color: #123f34;}
.description p, .description ul { line-height: 1.8; color: #4e6073; }
.description li { margin-bottom: 0.75rem; }

/* Bracket Styles */
.bracket-wrapper { padding: 20px 0; background: white; border-radius: 16px; min-height: 400px;}
.empty-bracket { text-align: center; color: #94a3b8; font-style: italic; padding: 50px 0; }
.bracket-scroll { display: flex; gap: 30px; overflow-x: auto; padding: 10px; }
.round-column { min-width: 260px; display: flex; flex-direction: column; justify-content: center; gap: 20px; }
.round-title { text-align: center; color: #006953; font-weight: 900; margin-bottom: 10px; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;}
.public-match-card { background: white; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
.p-item { padding: 12px 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; font-weight: 600; color: #475569;}
.p-item:last-child { border-bottom: none; }
.p-name { max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.is-winner { background: #f0fdf4; color: #16a34a; }
.match-score { text-align: center; padding: 8px; background: #f8fafc; font-size: 0.85rem; color: #64748b; border-top: 1px dashed #e2e8f0; }

.action-card { background: white; padding: 2rem; border-radius: 28px; box-shadow: 0 30px 60px rgba(0,0,0,0.08); border: 1px solid rgba(0,0,0,0.05); }
.action-card h3 { margin-bottom: 1.5rem; font-size: 1.4rem; color: #123f34; }
.price-wrap { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid #eee; }
.price-label { color: #6e7a74; }
.price-value { font-size: 1.5rem; font-weight: 800; color: #006953; }
.deadline { font-size: 0.9rem; color: #ba1a1a; margin-bottom: 1.5rem; text-align: center; }
.registration-meta { margin-bottom: 2rem; }
.slot-info { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.8rem; }
.slot-count { font-size: 1.4rem; font-weight: 800; color: #123f34; }
.slot-label { font-size: 0.85rem; color: #6e7a74; }
.progress-bar { height: 8px; background: #f0f2f2; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: #006953; border-radius: 4px; transition: width 0.6s ease; }
.btn-register { width: 100%; padding: 1.2rem; border-radius: 18px; border: none; background: linear-gradient(135deg, #006953 0%, #13846a 100%); color: white; font-weight: 700; font-size: 1.1rem; cursor: pointer; transition: transform 0.2s; }
.btn-register:hover { transform: scale(1.02); }
.btn-disabled { width: 100%; padding: 1.2rem; border-radius: 18px; border: none; background: #e0e0e0; color: #9e9e9e; font-weight: 700; cursor: not-allowed; }

.loading-full { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 80vh; }
.spinner { width: 50px; height: 50px; border: 5px solid rgba(0,105,83,0.1); border-top-color: #006953; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 900px) {
  .content-grid { grid-template-columns: 1fr; }
  .sidebar { order: -1; }
  .hero-meta { flex-direction: column; gap: 0.5rem; }
}
</style>