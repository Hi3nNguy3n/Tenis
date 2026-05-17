<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { t } from '../../utils/locale'
import { ElMessage } from 'element-plus'
import { 
  Trophy, 
  Calendar as CalendarIcon,
  User,
  Iphone,
  Location,
  Right,
  ArrowLeft
} from '@element-plus/icons-vue'
import { apiClient } from '../../services/apiClient'

const route = useRoute()
const router = useRouter()
const playerId = route.params.id

const playerData = ref(null)
const matchHistory = ref([])
const tournaments = ref([])
const isLoading = ref(true)

const stats = computed(() => {
  if (!playerData.value) return null
  const p = playerData.value.player_profile
  const total = (p.wins || 0) + (p.losses || 0)
  const winRate = total > 0 ? Math.round((p.wins / total) * 100) : 0
  return { total, winRate }
})

onMounted(async () => {
  try {
    // 1. Fetch Profile
    const res = await apiClient.get(`/api/players/${playerId}`)
    playerData.value = res
    
    // 2. Fetch History
    const historyRes = await apiClient.get(`/api/players/${playerId}/history`)
    matchHistory.value = historyRes || []
    
    // 3. Fetch Tournaments
    const tourRes = await apiClient.get(`/api/players/${playerId}/tournaments`)
    tournaments.value = tourRes || []
    
  } catch (err) {
    console.error(err)
    ElMessage.error(t('common.errorLoading') || 'Lỗi tải hồ sơ')
    router.push('/players')
  } finally {
    isLoading.value = false
  }
})

const getStatusType = (status) => {
  if (status === 'confirmed' || status === 'checked_in') return 'success'
  if (status === 'pending') return 'warning'
  return 'info'
}

const formatGender = (gender) => {
  if (!gender) return t('profile.notSpecified') || 'N/A'
  const g = gender.toLowerCase()
  if (g === 'male' || g === 'nam') return t('profile.male') || 'Nam'
  if (g === 'female' || g === 'nữ' || g === 'nu') return t('profile.female') || 'Nữ'
  return gender
}
</script>

<template>
  <div class="player-profile-page" v-loading="isLoading">
    <!-- HERO SECTION -->
    <section class="profile-hero" v-if="playerData">
      <div class="hero-overlay"></div>
      <div class="container hero-inner">
        <button class="back-btn" @click="router.back()">
          <el-icon><ArrowLeft /></el-icon> {{ t('common.back') || 'Quay lại' }}
        </button>
        
        <div class="hero-main">
          <div class="profile-avatar">
            <img :src="playerData.user.avatar_url || 'https://ui-avatars.com/api/?name=' + playerData.user.full_name" alt="Avatar" />
            <div class="rank-badge">#{{ playerData.player_profile.rank || '--' }}</div>
          </div>
          
          <div class="profile-info">
            <h1 class="player-name">{{ playerData.user.full_name }}</h1>
            <div class="player-meta">
              <span><el-icon><Location /></el-icon> {{ playerData.user.province || 'Saigon' }}</span>
              <span class="divider">|</span>
              <span><el-icon><Trophy /></el-icon> {{ playerData.player_profile.skill_level || 'N/A' }} Pts</span>
            </div>
            
            <div class="stats-row">
              <div class="stat-box">
                <span class="s-val">{{ playerData.player_profile.elo_points }}</span>
                <span class="s-lbl">ELO</span>
              </div>
              <div class="stat-box">
                <span class="s-val">{{ stats?.winRate }}%</span>
                <span class="s-lbl">{{ t('players.winRate') }}</span>
              </div>
              <div class="stat-box">
                <span class="s-val">{{ stats?.total }}</span>
                <span class="s-lbl">{{ t('players.matchesCount') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div class="container profile-grid" v-if="playerData">
      <!-- LEFT COLUMN -->
      <aside class="info-sidebar">
        <div class="info-card">
          <h3 class="card-title">{{ t('profile.personalInfo') }}</h3>
          <div class="info-list">
            <div class="info-item">
              <label>{{ t('profile.gender') }}</label>
              <span>{{ formatGender(playerData.player_profile.gender) }}</span>
            </div>
            <div class="info-item">
              <label>{{ t('profile.playHand') }}</label>
              <span>{{ playerData.player_profile.play_hand === 'right' ? t('profile.right') : t('profile.left') }}</span>
            </div>
            <div class="info-item" v-if="playerData.user.phone">
              <label>{{ t('profile.phone') }}</label>
              <span>{{ playerData.user.phone }}</span>
            </div>
          </div>
        </div>

        <div class="info-card tournaments-card">
          <h3 class="card-title">{{ t('profile.sections.tournaments') }}</h3>
          <div class="mini-tour-list">
            <div v-for="t in tournaments.slice(0, 5)" :key="t.id" class="mini-tour-item">
              <div class="mt-info">
                <span class="mt-name">{{ t.tournament_name }}</span>
                <span class="mt-date">{{ t.registered_at }}</span>
              </div>
              <el-tag :type="getStatusType(t.status)" size="small" effect="plain">{{ t.status }}</el-tag>
            </div>
            <el-empty v-if="!tournaments.length" :description="t('profile.noTournaments')" />
          </div>
        </div>
      </aside>

      <!-- MAIN CONTENT -->
      <main class="history-main">
        <div class="history-card">
          <div class="card-header">
            <h3 class="card-title">{{ t('profile.matchHistory') }}</h3>
            <div class="header-line"></div>
          </div>

          <div class="match-list">
            <div v-for="match in matchHistory" :key="match.id" class="match-item" :class="match.result_status.toLowerCase()">
              <div class="match-res">
                <span class="res-tag">{{ match.result_status === 'THẮNG' ? 'WIN' : 'LOSS' }}</span>
              </div>
              
              <div class="match-detail">
                <div class="m-tour">{{ match.tournament_name }}</div>
                
                <div class="m-teams">
                  <div class="team-unit">
                    <div class="team-players">
                      <div class="player-unit-tiny">
                        <el-avatar :size="18" :src="match.my_team?.avatar" class="tiny-avatar">
                          <el-icon><User /></el-icon>
                        </el-avatar>
                        <span class="p-name">{{ match.my_team?.name }}</span>
                      </div>
                      <div v-if="match.my_team?.partner_name" class="player-unit-tiny">
                        <el-avatar :size="18" :src="match.my_team?.partner_avatar" class="tiny-avatar">
                          <el-icon><User /></el-icon>
                        </el-avatar>
                        <span class="p-name">{{ match.my_team?.partner_name }}</span>
                      </div>
                    </div>
                  </div>

                  <span class="vs-label">VS</span>

                  <div class="team-unit">
                    <div class="team-players">
                      <div class="player-unit-tiny">
                        <el-avatar :size="18" :src="match.opponent_team?.avatar" class="tiny-avatar">
                          <el-icon><User /></el-icon>
                        </el-avatar>
                        <span class="p-name">{{ match.opponent_team?.name }}</span>
                      </div>
                      <div v-if="match.opponent_team?.partner_name" class="player-unit-tiny">
                        <el-avatar :size="18" :src="match.opponent_team?.partner_avatar" class="tiny-avatar">
                          <el-icon><User /></el-icon>
                        </el-avatar>
                        <span class="p-name">{{ match.opponent_team?.partner_name }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="m-meta">
                  <span>{{ match.round }}</span>
                  <span class="dot"></span>
                  <span>{{ match.time }}</span>
                </div>
              </div>

              <div class="match-score">
                <div class="score-pill">{{ match.score }}</div>
              </div>
            </div>
            
            <el-empty v-if="!matchHistory.length" :description="t('profile.noMatchData')" />
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.player-profile-page {
  --primary: #002855;
  --accent: #c1ff72;
  --bg: #f1f5f9;
  --text: #0f172a;
  --text-muted: #64748b;
  --win: #16a34a;
  --loss: #dc2626;
  
  background: var(--bg);
  min-height: 100vh;
  padding-bottom: 4rem;
  font-family: 'Inter', sans-serif;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* HERO */
.profile-hero {
  background: var(--primary);
  color: white;
  padding: 4rem 0 6rem;
  position: relative;
  overflow: hidden;
  margin-bottom: -4rem;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(0, 40, 85, 0.9) 0%, rgba(0, 40, 85, 0.5) 100%);
}

.hero-inner {
  position: relative;
  z-index: 2;
}

.back-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 99px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  margin-bottom: 2rem;
  transition: 0.2s;
}
.back-btn:hover { background: rgba(255, 255, 255, 0.2); }

.hero-main {
  display: flex;
  align-items: center;
  gap: 3rem;
}

.profile-avatar {
  position: relative;
  width: 160px;
  height: 160px;
  border-radius: 50%;
  padding: 5px;
  background: white;
  box-shadow: 0 15px 30px rgba(0,0,0,0.3);
}

.profile-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.rank-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  background: var(--accent);
  color: var(--primary);
  font-weight: 800;
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 1rem;
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}

.player-name {
  font-size: 3rem;
  font-weight: 800;
  margin: 0 0 0.5rem;
  letter-spacing: -0.02em;
}

.player-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
  margin-bottom: 2rem;
}

.divider { opacity: 0.3; }

.stats-row {
  display: flex;
  gap: 2rem;
}

.stat-box {
  display: flex;
  flex-direction: column;
}

.s-val {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--accent);
}

.s-lbl {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  opacity: 0.7;
}

/* GRID */
.profile-grid {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 2rem;
  position: relative;
  z-index: 3;
}

.info-card {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--primary);
  margin: 0 0 1.5rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted);
}

.info-item span {
  font-weight: 600;
  color: var(--text);
}

.mini-tour-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.mini-tour-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f1f5f9;
}
.mini-tour-item:last-child { border: none; padding: 0; }

.mt-info { display: flex; flex-direction: column; }
.mt-name { font-size: 0.9rem; font-weight: 700; color: var(--text); }
.mt-date { font-size: 0.75rem; color: var(--text-muted); }

/* MATCH HISTORY */
.history-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

.header-line {
  width: 40px;
  height: 3px;
  background: var(--accent);
  margin-top: -1rem;
  margin-bottom: 2rem;
}

.match-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.match-item {
  display: flex;
  align-items: center;
  padding: 1.25rem;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  transition: 0.2s;
}

.match-item:hover {
  transform: translateX(5px);
  border-color: var(--primary);
}

.match-res {
  width: 60px;
  flex-shrink: 0;
}

.res-tag {
  font-size: 0.7rem;
  font-weight: 900;
  padding: 4px 8px;
  border-radius: 4px;
}

.match-item.thắng .res-tag { background: #dcfce7; color: var(--win); }
.match-item.thua .res-tag { background: #fee2e2; color: var(--loss); }

.match-detail {
  flex: 1;
  padding: 0 1.5rem;
}

.m-tour { font-size: 0.85rem; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
.m-teams { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.vs-label { font-size: 0.7rem; font-weight: 900; color: var(--text-muted); opacity: 0.5; }
.team-players { display: flex; flex-direction: column; gap: 4px; }
.player-unit-tiny { display: flex; align-items: center; gap: 6px; }
.player-unit-tiny .p-name { font-size: 0.85rem; font-weight: 600; color: var(--text); }
.tiny-avatar { border: 1px solid rgba(0,0,0,0.05); }

.m-meta { display: flex; align-items: center; gap: 8px; font-size: 0.75rem; color: var(--text-muted); }
.dot { width: 3px; height: 3px; border-radius: 50%; background: #cbd5e1; }

.score-pill {
  background: var(--primary);
  color: white;
  font-weight: 700;
  padding: 6px 16px;
  border-radius: 99px;
  font-size: 0.9rem;
}

@media (max-width: 900px) {
  .hero-main { flex-direction: column; text-align: center; gap: 1.5rem; }
  .profile-grid { grid-template-columns: 1fr; }
  .player-name { font-size: 2.2rem; }
  .player-meta { justify-content: center; }
  .stats-row { justify-content: center; }
  .match-item { flex-direction: column; text-align: center; gap: 1rem; }
  .match-detail { padding: 0; }
}
</style>
