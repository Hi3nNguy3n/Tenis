<script setup>
import { ref, onMounted, computed } from 'vue'
import { Search, Aim, DataAnalysis, Calendar, CircleCheck, Close, Trophy, InfoFilled, ArrowRight } from '@element-plus/icons-vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import { t } from '../../utils/locale'
import MarketingBannerStrip from '../../components/MarketingBannerStrip.vue'

const authStore = useAuthStore()
const players = ref([])
const isLoading = ref(false)
const selectedOpponent = ref(null)
const searchQuery = ref('')

const showChallengeDialog = ref(false)
const challengeForm = ref({ 
  date: '', 
  notes: '',
  match_type: 'singles',
  challenger_partner_id: null,
  challenged_partner_id: null
})

const showH2HDialog = ref(false)
const h2hHistory = ref([])

const filteredPlayers = computed(() => {
  if (!players.value || !Array.isArray(players.value)) return []
  
  let result = players.value.filter(p => {
    const isMe = p.full_name === authStore.user?.full_name
    const isAdmin = p.full_name?.toLowerCase().includes('admin')
    return !isMe && !isAdmin
  })

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p => p.full_name.toLowerCase().includes(query))
  }

  return result
})

const myPlayer = computed(() => {
  if (!players.value || !Array.isArray(players.value)) return null
  return players.value.find(p => p.full_name === authStore.user?.full_name)
})
const myPlayerId = computed(() => myPlayer.value?.player_id || null)

const myPartnerOptions = computed(() => {
  if (!players.value || !Array.isArray(players.value)) return []
  return players.value.filter(p => {
    const isMe = p.player_id === myPlayerId.value
    const isOpponent = p.player_id === selectedOpponent.value?.player_id
    const isAdmin = p.full_name?.toLowerCase().includes('admin')
    return !isMe && !isOpponent && !isAdmin
  })
})

const opponentPartnerOptions = computed(() => {
  if (!players.value || !Array.isArray(players.value)) return []
  return players.value.filter(p => {
    const isMe = p.player_id === myPlayerId.value
    const isOpponent = p.player_id === selectedOpponent.value?.player_id
    const isMyPartner = p.player_id === challengeForm.value.challenger_partner_id
    const isAdmin = p.full_name?.toLowerCase().includes('admin')
    return !isMe && !isOpponent && !isMyPartner && !isAdmin
  })
})

const loadPlayers = async () => {
  isLoading.value = true
  try {
    const data = await apiClient.get('/api/players/rankings')
    // Đánh lại số thứ tự rank sau khi lấy về (giống trang Rankings)
    const normalized = Array.isArray(data) ? data : (data.data || [])
    players.value = normalized.map((player, index) => ({
      ...player,
      displayRank: index + 1
    }))
  } catch (err) { 
    ElMessage.error(t('challenges.loadError')) 
  } finally { 
    isLoading.value = false 
  }
}

const openChallenge = (p) => {
  selectedOpponent.value = p
  challengeForm.value = { 
    date: '', 
    notes: '', 
    match_type: 'singles',
    challenger_partner_id: null,
    challenged_partner_id: null
  }
  showChallengeDialog.value = true
}

const sendChallengeRequest = async () => {
  if (!challengeForm.value.date) return ElMessage.warning(t('challenges.selectDateWarning'))
  
  if (challengeForm.value.match_type === 'doubles') {
    if (!challengeForm.value.challenger_partner_id || !challengeForm.value.challenged_partner_id) {
      return ElMessage.warning('Vui lòng chọn đầy đủ đồng đội cho cả hai bên khi thách đấu đôi!')
    }
  }

  try {
    await apiClient.post('/api/challenges/', {
      challenged_id: selectedOpponent.value.player_id,
      proposed_date: challengeForm.value.date,
      notes: challengeForm.value.notes,
      match_type: challengeForm.value.match_type,
      challenger_partner_id: challengeForm.value.match_type === 'doubles' ? challengeForm.value.challenger_partner_id : null,
      challenged_partner_id: challengeForm.value.match_type === 'doubles' ? challengeForm.value.challenged_partner_id : null
    })
    ElMessage.success(t('challenges.requestSentSuccess'))
    showChallengeDialog.value = false
    challengeForm.value = { 
      date: '', 
      notes: '',
      match_type: 'singles',
      challenger_partner_id: null,
      challenged_partner_id: null
    }
  } catch (err) { 
    const errorMsg = err.response?.data?.detail || t('challenges.requestSendError')
    ElMessage.error(errorMsg) 
  }
}

const viewH2H = async (p) => {
  selectedOpponent.value = p
  showH2HDialog.value = true
  h2hHistory.value = []
  try {
    const data = await apiClient.get(`/api/players/h2h/${p.player_id}`)
    h2hHistory.value = data
  } catch (err) {
    console.error('H2H Load Error:', err)
  }
}

onMounted(loadPlayers)
</script>

<template>
  <div class="atp-challenge-page">
    
    <div class="top-ad-banner">
      <MarketingBannerStrip placement="challenges_top" variant="compact" :max="3" />
    </div>

    <div class="container layout-grid">
      
      <main class="main-content">
        
        <div class="ranking-header-section">
          <div class="title-row">
            <h1 class="page-title"><el-icon class="pif-icon"><Aim /></el-icon> SGT <span>CHALLENGES</span></h1>
          </div>

          <div class="inline-filters">
            <div class="filter-tabs">
              <span class="f-tab active">{{ t('challenges.allPlayers') }}</span>
              <span class="f-tab">{{ t('challenges.suggested') }}</span>
            </div>

            <div class="filter-dropdowns">
              <div class="flat-search">
                <el-icon><Search /></el-icon>
                <input 
                  v-model="searchQuery" 
                  type="text" 
                  :placeholder="t('challenges.searchOpponent')" 
                />
              </div>
            </div>
          </div>
        </div>

        <div class="ranking-list-container" v-loading="isLoading">
          <div v-if="filteredPlayers.length === 0" class="empty-state">
            <el-empty :description="t('common.noData') || t('challenges.noOpponentFound')" />
          </div>

          <table v-else class="atp-flat-table">
            <thead>
              <tr>
                <th class="col-rank">{{ t('challenges.rank') }}</th>
                <th class="col-player">{{ t('challenges.player') }}</th>
                <th class="col-pts text-center">{{ t('challenges.points') }}</th>
                <th class="col-winrate hidden-mobile text-center">{{ t('challenges.winRate') }}</th>
                <th class="col-actions text-right">{{ t('challenges.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in filteredPlayers" :key="p.player_id">
                <td class="col-rank">
                  <span class="rank-num">{{ p.displayRank || p.rank }}</span>
                </td>
                <td class="col-player" :data-label="t('challenges.player')">
                  <div class="player-info-cell">
                    <img :src="p.avatar_url || `https://ui-avatars.com/api/?name=${p.full_name}`" class="player-ava" referrerpolicy="no-referrer" />
                    <span class="flag-mini"></span>
                    <strong class="player-name">{{ p.full_name }}</strong>
                  </div>
                </td>
                <td class="col-pts text-center" :data-label="t('challenges.points')">
                  <strong class="points-val">{{ p.elo_points || 1000 }}</strong>
                </td>
                <td class="col-winrate hidden-mobile text-center" :data-label="t('challenges.winRate')">
                  {{ p.win_rate || 0 }}%
                </td>
                <td class="col-actions text-right">
                  <div class="action-buttons">
                    <button class="btn-atp-outline" @click="viewH2H(p)">{{ t('challenges.h2h') }}</button>
                    <button class="btn-atp-solid" @click="openChallenge(p)">{{ t('challenges.challengeBtn') }}</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>

      <aside class="sidebar">
        
        <div class="atp-widget">
          <div class="ws-header">
            <h3>{{ t('challenges.yourStatus') }}</h3>
            <a href="/profile" class="ws-link">{{ t('challenges.profile') }} <el-icon><ArrowRight /></el-icon></a>
          </div>
          
          <div class="ws-body profile-widget">
            <div class="my-profile-header">
              <img :src="authStore.user?.avatar_url || 'https://ui-avatars.com/api/?name=Me'" class="my-ava" referrerpolicy="no-referrer" />
              <div class="my-info">
                <h4>{{ authStore.user?.full_name || t('challenges.defaultAthlete') }}</h4>
                <span><span class="flag-mini"></span> {{ t('challenges.vietnam') }}</span>
              </div>
            </div>
            
            <div class="my-stats-grid">
              <div class="my-stat">
                <span class="ms-lbl">{{ t('challenges.rank') }}</span>
                <span class="ms-val">{{ authStore.profile?.player_profile?.rank || '--' }}</span>
              </div>
              <div class="my-stat">
                <span class="ms-lbl">{{ t('challenges.points') }}</span>
                <span class="ms-val text-blue">{{ authStore.profile?.player_profile?.elo_points || 1000 }}</span>
              </div>
              <div class="my-stat">
                <span class="ms-lbl">{{ t('challenges.wl') }}</span>
                <span class="ms-val">{{ authStore.profile?.player_profile?.wins || 0 }} - {{ authStore.profile?.player_profile?.losses || 0 }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="atp-widget">
          <div class="ws-header">
            <h3>{{ t('challenges.howItWorks') }}</h3>
          </div>
          <div class="ws-body rules-widget">
            <ul class="rules-list">
              <li>
                <el-icon class="rule-icon"><Aim /></el-icon>
                <div class="rule-text">
                  <strong>{{ t('challenges.step1Title') }}</strong>
                  <p>{{ t('challenges.step1Desc') }}</p>
                </div>
              </li>
              <li>
                <el-icon class="rule-icon"><Calendar /></el-icon>
                <div class="rule-text">
                  <strong>{{ t('challenges.step2Title') }}</strong>
                  <p>{{ t('challenges.step2Desc') }}</p>
                </div>
              </li>
              <li>
                <el-icon class="rule-icon"><Trophy /></el-icon>
                <div class="rule-text">
                  <strong>{{ t('challenges.step3Title') }}</strong>
                  <p>{{ t('challenges.step3Desc') }}</p>
                </div>
              </li>
            </ul>
          </div>
        </div>

      </aside>
    </div>

    <el-dialog v-model="showChallengeDialog" :show-close="false" width="90%" style="max-width: 450px" class="atp-modal">
      <template #header>
        <div class="modal-custom-header">
          <h3>{{ t('challenges.challengeRequest') }}</h3>
          <button class="close-btn" @click="showChallengeDialog = false"><el-icon><Close /></el-icon></button>
        </div>
      </template>

      <div class="modal-body">
        <div class="challenge-target">
          <img :src="selectedOpponent?.avatar_url" alt="" class="target-avatar" referrerpolicy="no-referrer" />
          <div class="target-info">
            <span>{{ t('challenges.opponent') }}</span>
            <strong>{{ selectedOpponent?.full_name }}</strong>
          </div>
        </div>

        <el-form label-position="top" class="atp-form">
          <el-form-item label="Hình thức thi đấu">
            <el-radio-group v-model="challengeForm.match_type" size="default" style="width: 100%; display: flex; margin-bottom: 10px;">
              <el-radio-button value="singles" style="flex: 1; text-align: center;">Đấu đơn (1vs1)</el-radio-button>
              <el-radio-button value="doubles" style="flex: 1; text-align: center;">Đấu đôi (2vs2)</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <div v-if="challengeForm.match_type === 'doubles'" class="doubles-select-section" style="background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px dashed #cbd5e1; margin-bottom: 15px;">
            <el-form-item label="Đồng đội của bạn" required style="margin-bottom: 10px;">
              <el-select 
                v-model="challengeForm.challenger_partner_id" 
                placeholder="Chọn đồng đội của bạn" 
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="p in myPartnerOptions"
                  :key="p.player_id"
                  :label="p.full_name + ' (ELO: ' + (p.elo_points || 1000) + ')'"
                  :value="p.player_id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="Đồng đội của đối thủ" required style="margin-bottom: 0;">
              <el-select 
                v-model="challengeForm.challenged_partner_id" 
                placeholder="Chọn đồng đội của đối thủ" 
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="p in opponentPartnerOptions"
                  :key="p.player_id"
                  :label="p.full_name + ' (ELO: ' + (p.elo_points || 1000) + ')'"
                  :value="p.player_id"
                />
              </el-select>
            </el-form-item>
          </div>

          <el-form-item :label="t('challenges.proposedDate')">
            <el-date-picker 
              v-model="challengeForm.date" 
              type="date" 
              :placeholder="t('challenges.selectDate')"
              value-format="YYYY-MM-DD" 
              style="width: 100%" 
            />
          </el-form-item>
          <el-form-item :label="t('challenges.messageOptional')">
            <el-input 
              v-model="challengeForm.notes" 
              type="textarea" 
              :rows="3"
              :placeholder="t('challenges.messagePlaceholder')" 
            />
          </el-form-item>
        </el-form>

        <div class="atp-notice-box">
          <el-icon class="notice-icon"><InfoFilled /></el-icon>
          <p>{{ t('challenges.noticeText') }}</p>
        </div>
      </div>

      <template #footer>
        <div class="modal-footer-flex">
          <button class="btn-cancel" @click="showChallengeDialog = false">{{ t('challenges.cancel') }}</button>
          <button class="btn-atp-solid" @click="sendChallengeRequest">{{ t('challenges.sendRequest') }}</button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="showH2HDialog" :show-close="false" width="95%" style="max-width: 550px" class="atp-modal">
      <template #header>
        <div class="modal-custom-header">
          <h3>{{ t('challenges.head2head') }}</h3>
          <button class="close-btn" @click="showH2HDialog = false"><el-icon><Close /></el-icon></button>
        </div>
      </template>

      <div class="h2h-modal-body">
        <div class="h2h-versus-header">
          <div class="v-player">
            <div class="v-avatar"><img :src="authStore.user?.avatar_url || 'https://ui-avatars.com/api/?name=Me'" referrerpolicy="no-referrer" /></div>
            <span>{{ t('challenges.youUpper') }}</span>
          </div>
          <div class="v-divider">{{ t('challenges.vs') }}</div>
          <div class="v-player">
            <div class="v-avatar"><img :src="selectedOpponent?.avatar_url" referrerpolicy="no-referrer" /></div>
            <span>{{ selectedOpponent?.full_name }}</span>
          </div>
        </div>

        <div class="h2h-list">
          <div v-if="h2hHistory.length === 0" class="h2h-empty">
            <el-empty :description="t('challenges.noH2H') || 'Chưa có lịch sử đối đầu'" :image-size="60" />
          </div>
          <div v-for="(item, idx) in h2hHistory" :key="idx" class="h2h-item">
            <div class="h2h-date">{{ item.date }}</div>
            <div class="h2h-score">{{ item.score }}</div>
            <div class="h2h-result">
              <span v-if="item.type === 'win'" class="res-badge win"><el-icon><CircleCheck /></el-icon> {{ t('challenges.win') }}</span>
              <span v-else class="res-badge lose">{{ t('challenges.loss') }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

  </div>
</template>

<style scoped>
/* =========================================================
   TỔNG QUAN THEME (TRẮNG & NAVY)
========================================================= */
.atp-challenge-page {
  background: #ffffff;
  min-height: 100vh;
  font-family: 'Inter', -apple-system, sans-serif;
  color: #002855;
  padding-bottom: 5rem;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* Quảng cáo Top */
.top-ad-banner {
  background: #f8fafc;
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: center;
  border-bottom: 1px solid #e2e8f0;
}
.top-ad-banner :deep(.marketing-strip) {
  max-width: 1200px;
  margin: 0 auto;
}
.top-ad-banner :deep(.marketing-strip-card) {
  min-height: 128px;
  max-height: 160px;
}
.ad-placeholder img { max-width: 100%; height: auto; max-height: 90px; }

/* =========================================================
   BỐ CỤC 2 CỘT
========================================================= */
.layout-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 2rem;
  margin-top: 2rem;
  align-items: start;
}

/* =========================================================
   HEADER BẢNG DANH SÁCH & BỘ LỌC
========================================================= */
.ranking-header-section { margin-bottom: 1rem; }

.title-row { margin-bottom: 1.5rem; }

.page-title {
  font-size: 1.8rem; font-weight: 800; font-style: italic; margin: 0; color: #002855;
  display: flex; align-items: center; gap: 10px;
}
.pif-icon {
  background: #002855; color: white; padding: 6px; border-radius: 50%; font-size: 1.2rem;
}

.inline-filters {
  display: flex; justify-content: space-between; align-items: flex-end;
  border-bottom: 1px solid #e2e8f0; padding-bottom: 10px;
}

.filter-tabs { display: flex; gap: 1.5rem; }
.f-tab {
  font-size: 0.9rem; font-weight: 700; color: #64748b; cursor: pointer;
  padding-bottom: 10px; position: relative;
}
.f-tab.active { color: #00b0f0; }
.f-tab.active::after {
  content: ''; position: absolute; bottom: -11px; left: 0; width: 100%; height: 3px; background: #00b0f0;
}

/* Flat Search Box */
.flat-search {
  display: flex; align-items: center; gap: 8px;
  border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px 12px; width: 250px;
}
.flat-search:focus-within { border-color: #002855; }
.flat-search .el-icon { color: #64748b; }
.flat-search input {
  border: none; outline: none; width: 100%; font-size: 0.85rem; color: #0f172a; font-weight: 600;
}
.flat-search input::placeholder { color: #94a3b8; font-weight: 500;}

/* =========================================================
   TABLE FLAT (DANH SÁCH ĐỐI THỦ)
========================================================= */
.ranking-list-container { width: 100%; }

.atp-flat-table { width: 100%; border-collapse: collapse; }
.atp-flat-table th {
  text-align: left; font-size: 0.75rem; text-transform: uppercase; color: #64748b; font-weight: 600;
  padding: 1rem 0.5rem; border-bottom: 1px solid #cbd5e1;
}

.atp-flat-table td {
  padding: 1rem 0.5rem; border-bottom: 1px solid #f1f5f9; vertical-align: middle;
}

.text-center { text-align: center !important; }
.text-right { text-align: right !important; }

.col-rank { width: 60px; font-weight: 800; font-size: 1.1rem;}
.rank-num { color: #002855; }

.col-player { min-width: 250px; }
.player-info-cell { display: flex; align-items: center; gap: 12px; }
.player-ava { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; border: 1px solid #e2e8f0;}
.flag-mini { font-size: 0.9rem; }
.player-name { font-size: 1.05rem; color: #002855; font-weight: 700; }

.col-pts { width: 100px; }
.points-val { font-size: 1.15rem; font-weight: 800; color: #002855; }

.col-winrate { font-size: 0.9rem; color: #475569; font-weight: 600;}

.col-actions { width: 180px; }
.action-buttons { display: flex; gap: 8px; justify-content: flex-end;}

/* Nút Action ATP Style */
.btn-atp-outline {
  background: transparent; border: 1px solid #cbd5e1; color: #002855;
  padding: 6px 12px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; cursor: pointer; transition: 0.2s;
}
.btn-atp-outline:hover { border-color: #002855; }

.btn-atp-solid {
  background: #0066cc; border: none; color: white;
  padding: 6px 16px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; cursor: pointer; transition: 0.2s;
}
.btn-atp-solid:hover { background: #004080; }

.empty-state { padding: 4rem 0; }

/* =========================================================
   SIDEBAR WIDGETS
========================================================= */
.atp-widget {
  border: 1px solid #cbd5e1; border-radius: 8px; background: white; margin-bottom: 2rem; overflow: hidden;
}
.ws-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1rem 1.25rem; border-bottom: 1px solid #e2e8f0; background: #f8fafc;
}
.ws-header h3 { margin: 0; font-size: 0.95rem; font-weight: 800; color: #002855; }
.ws-link { font-size: 0.75rem; color: #00b0f0; text-decoration: none; font-weight: 700; display: flex; align-items: center; gap: 4px;}

/* Profile Widget */
.profile-widget { padding: 1.25rem; }
.my-profile-header { display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem; }
.my-ava { width: 50px; height: 50px; border-radius: 50%; border: 2px solid #e2e8f0; object-fit: cover;}
.my-info h4 { margin: 0 0 4px; font-size: 1.05rem; font-weight: 800; color: #002855;}
.my-info span { font-size: 0.8rem; color: #64748b; display: flex; align-items: center; gap: 4px;}

.my-stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; background: #f1f5f9; padding: 12px; border-radius: 8px;}
.my-stat { display: flex; flex-direction: column; align-items: center; gap: 4px;}
.ms-lbl { font-size: 0.65rem; font-weight: 700; color: #64748b; text-transform: uppercase;}
.ms-val { font-size: 1rem; font-weight: 800; color: #0f172a;}
.text-blue { color: #00b0f0; }

/* Rules Widget */
.rules-widget { padding: 1.25rem; }
.rules-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 1rem;}
.rules-list li { display: flex; gap: 12px; align-items: flex-start;}
.rule-icon { color: #00b0f0; font-size: 1.2rem; margin-top: 2px;}
.rule-text strong { font-size: 0.85rem; color: #002855; display: block; margin-bottom: 4px;}
.rule-text p { margin: 0; font-size: 0.75rem; color: #64748b; line-height: 1.4;}

/* =======================================================
   MODALS (HỘP THOẠI)
======================================================= */
:deep(.atp-modal .el-dialog) { border-radius: 12px; overflow: hidden; padding: 0; }
:deep(.atp-modal .el-dialog__header) { padding: 0; border: none; }
:deep(.atp-modal .el-dialog__body) { padding: 0; }

.modal-custom-header {
  background: #002855; padding: 1.2rem 1.5rem; display: flex; justify-content: space-between; align-items: center; color: white;
}
.modal-custom-header h3 { margin: 0; font-size: 1rem; font-weight: 800; font-style: italic;}
.close-btn { background: transparent; border: none; color: white; font-size: 1.2rem; cursor: pointer; opacity: 0.8;}
.close-btn:hover { opacity: 1; }

.modal-body { padding: 1.5rem; }
.challenge-target {
  display: flex; align-items: center; gap: 1rem; padding: 1rem;
  background: #f8fafc; border-radius: 8px; margin-bottom: 1.5rem; border: 1px solid #e2e8f0;
}
.target-avatar { width: 50px; height: 50px; border-radius: 50%; object-fit: cover;}
.target-info { display: flex; flex-direction: column; }
.target-info span { font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 600;}
.target-info strong { font-size: 1.05rem; color: #002855; font-weight: 800;}

:deep(.atp-form .el-form-item__label) { font-size: 0.75rem; font-weight: 700; color: #64748b; padding-bottom: 4px; text-transform: uppercase; }
:deep(.atp-form .el-input__wrapper), :deep(.atp-form .el-textarea__inner) { box-shadow: 0 0 0 1px #cbd5e1 inset; border-radius: 4px; }
:deep(.atp-form .el-input__wrapper.is-focus), :deep(.atp-form .el-textarea__inner:focus) { box-shadow: 0 0 0 1px #002855 inset; }

.atp-notice-box {
  display: flex; gap: 10px; background: #f1f5f9; padding: 12px; border-radius: 6px; margin-top: 1.5rem; align-items: flex-start;
}
.notice-icon { color: #64748b; font-size: 1.2rem; margin-top: 2px;}
.atp-notice-box p { margin: 0; font-size: 0.75rem; color: #475569; line-height: 1.4;}

.modal-footer-flex {
  padding: 1rem 1.5rem; border-top: 1px solid #e2e8f0; display: flex; justify-content: flex-end; gap: 12px; background: #f8fafc;
}
.btn-cancel {
  background: white; border: 1px solid #cbd5e1; color: #0f172a;
  padding: 0.6rem 1.2rem; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 0.8rem;
}

/* H2H Modal Specifics */
.h2h-modal-body { padding: 1.5rem; }
.h2h-versus-header {
  display: flex; align-items: center; justify-content: center; gap: 2rem;
  margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid #e2e8f0;
}
.v-player { display: flex; flex-direction: column; align-items: center; gap: 8px; width: 100px; text-align: center;}
.v-avatar { width: 60px; height: 60px; border-radius: 50%; border: 2px solid #002855; overflow: hidden;}
.v-avatar img { width: 100%; height: 100%; object-fit: cover;}
.v-player span { font-size: 0.85rem; font-weight: 800; color: #002855;}
.v-divider { font-size: 1.2rem; font-weight: 800; color: #cbd5e1; }

.h2h-list { display: flex; flex-direction: column; gap: 0.5rem;}
.h2h-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1rem; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
}
.h2h-date { font-size: 0.85rem; color: #64748b; width: 90px; font-weight: 500;}
.h2h-score { font-size: 1.1rem; font-weight: 800; color: #002855; flex: 1; text-align: center;}
.h2h-result { width: 90px; text-align: right;}
.res-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; }
.res-badge.win { background: #dcfce7; color: #16a34a;}
.res-badge.lose { background: #fee2e2; color: #dc2626;}

/* =======================================================
   RESPONSIVE
======================================================= */
@media (max-width: 1024px) {
  .layout-grid { grid-template-columns: 1fr; }
  .sidebar { order: 2; }
  .main-content { order: 1; }
}

@media (max-width: 768px) {
  .container { padding: 0 1rem; }
  .page-title { font-size: 1.5rem; }
  
  .inline-filters { 
    flex-direction: column; 
    align-items: stretch; 
    gap: 1rem; 
    padding-bottom: 15px;
  }
  
  .filter-tabs { justify-content: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 5px; }
  .flat-search { width: 100%; box-sizing: border-box; }

  /* Biến bảng thành Card trên mobile */
  .atp-flat-table thead { display: none; }
  .atp-flat-table tr { 
    display: block; 
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-bottom: 1rem;
    padding: 1rem;
    position: relative;
  }
  .atp-flat-table td { 
    display: flex; 
    justify-content: space-between; 
    align-items: center;
    padding: 0.5rem 0;
    border: none;
    text-align: left;
  }
  
  .atp-flat-table td::before {
    content: attr(data-label);
    font-size: 0.7rem;
    text-transform: uppercase;
    color: #64748b;
    font-weight: 700;
    margin-right: 10px;
  }

  .col-rank { 
    position: absolute; 
    top: -10px; 
    left: 1rem; 
    background: #002855; 
    color: white !important; 
    width: 30px !important;
    height: 30px;
    border-radius: 4px;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    font-size: 0.9rem !important;
    padding: 0 !important;
    z-index: 1;
  }
  .col-rank::before { display: none; }
  .rank-num { color: white; }

  .col-player { padding-top: 1rem !important; }
  .player-info-cell { width: 100%; justify-content: flex-start; }
  
  .col-actions { display: block !important; padding-top: 1rem !important; border-top: 1px solid #f1f5f9 !important; }
  .action-buttons { width: 100%; gap: 10px; }
  .action-buttons button { flex: 1; height: 40px; font-size: 0.8rem; }

  /* H2H Versus Header Mobile */
  .h2h-versus-header { gap: 1rem; }
  .v-avatar { width: 45px; height: 45px; }
  .v-player span { font-size: 0.75rem; }
  .v-divider { font-size: 0.9rem; }
  
  .h2h-item { flex-direction: column; gap: 8px; align-items: center; }
  .h2h-date, .h2h-result { width: 100%; text-align: center; }
  .h2h-score { font-size: 1rem; }
}

@media (max-width: 480px) {
  .page-title { font-size: 1.2rem; }
  .player-name { font-size: 0.95rem; }
  .my-profile-header { flex-direction: column; text-align: center; }
  .my-stats-grid { grid-template-columns: 1fr; }
}
</style>
