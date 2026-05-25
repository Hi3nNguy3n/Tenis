<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import { Trophy, Check, ArrowRight } from '@element-plus/icons-vue'
import { t } from '../../utils/locale'
import MarketingBannerStrip from '../../components/MarketingBannerStrip.vue'

const rankings = ref([])
const finalMatches = ref([])
const isLoading = ref(true)
const activeRankingTab = ref('Singles')

const filters = ref({
  category: '',
  province: ''
})

const provinceOptions = ref([])
const categoryOptions = ref([
  { value: 'Singles', label: 'Đơn (Singles)' },
  { value: 'Doubles', label: 'Đôi (Doubles)' }
])

const formatCategoryLabel = (value) => {
  if (!value) return ''
  // Nếu value là object (trường hợp khởi tạo), lấy thuộc tính value
  const val = typeof value === 'object' ? value.value : value
  if (val === 'Singles') return t('common.singles') || 'Đơn'
  if (val === 'Doubles') return t('common.doubles') || 'Đôi'
  return val
}

const buildFilterOptions = (items = []) => {
  const provinceSet = new Set()
  const categorySet = new Set()

  items.forEach((item) => {
    if (item?.province) provinceSet.add(item.province)
    if (item?.category) categorySet.add(item.category)
  })

  provinceOptions.value = [...provinceSet].sort((a, b) => a.localeCompare(b, 'vi'))
  categoryOptions.value = [...categorySet].sort((a, b) => a.localeCompare(b))
}

const fetchFinalMatches = async () => {
  try {
    const response = await apiClient.get('/api/matches/')
    const matches = Array.isArray(response) ? response : []
    finalMatches.value = matches.filter((match) => {
      const round = String(match.round_code || '').toUpperCase()
      return round === 'FINAL' || round === 'F' || round.includes('CHUNG KET') || round.includes('CHUNG KẾT')
    })
  } catch (error) {
    finalMatches.value = []
  }
}

const fetchRankings = async () => {
  isLoading.value = true
  try {
    // Sử dụng URLSearchParams để tự động xử lý và nối chuỗi param an toàn
    const params = new URLSearchParams()
    if (filters.value.category) params.append('category', filters.value.category)
    if (filters.value.province) params.append('province', filters.value.province)

    const queryString = params.toString()
    const url = queryString ? `/api/players/rankings?${queryString}` : '/api/players/rankings'

    // Gọi API
    const response = await apiClient.get(url)
    const normalized = Array.isArray(response) ? response : []
    
    // Đánh lại số thứ tự (Rank)
    rankings.value = normalized.map((player, index) => ({
      ...player,
      rank: index + 1
    }))

    // Chỉ tạo danh sách tuỳ chọn Tỉnh/Thành ở lần load đầu tiên (khi chưa có filter)
    if (!filters.value.category && !filters.value.province) {
      buildFilterOptions(rankings.value)
    }
  } catch (error) {
    ElMessage.error(t('common.errorLoading') || 'Lỗi tải dữ liệu bảng xếp hạng')
  } finally {
    isLoading.value = false
  }
}

const doublesRankings = computed(() => {
  const sorted = [...rankings.value].sort((a, b) => (a.rank || 0) - (b.rank || 0))
  const pairs = []
  for (let index = 0; index < sorted.length; index += 2) {
    const first = sorted[index]
    const second = sorted[index + 1]
    if (!first || !second) continue
    const totalMatches = (first.matches_played || 0) + (second.matches_played || 0)
    const totalWins = (first.wins || 0) + (second.wins || 0)
    pairs.push({
      rank: pairs.length + 1,
      player_id: `pair-${first.player_id}-${second.player_id}`,
      full_name: `${first.full_name} / ${second.full_name}`,
      avatar_url: first.avatar_url,
      partner_avatar_url: second.avatar_url,
      partner_name: second.full_name,
      skill_level: `${first.skill_level || 'N/A'} / ${second.skill_level || 'N/A'}`,
      elo_points: (first.elo_points || 0) + (second.elo_points || 0),
      matches_played: totalMatches,
      win_rate: totalMatches ? Math.round((totalWins / totalMatches) * 1000) / 10 : 0,
      isDoublesPair: true
    })
  }
  return pairs
})

const raceToFinalsRankings = computed(() => {
  const playerMap = new Map()
  const ensurePlayer = (name, avatar = null) => {
    if (!name || name.includes('ChÆ°a') || name.includes('Chưa') || name === 'N/A') return null
    if (!playerMap.has(name)) {
      const ranking = rankings.value.find(player => player.full_name === name)
      playerMap.set(name, {
        rank: 0,
        player_id: ranking?.player_id || `finalist-${name}`,
        full_name: name,
        avatar_url: avatar || ranking?.avatar_url,
        skill_level: ranking?.skill_level || 'N/A',
        elo_points: 0,
        matches_played: ranking?.matches_played || 0,
        win_rate: ranking?.win_rate || 0,
        finals_count: 0,
        titles_count: 0,
        isRaceRow: true
      })
    }
    return playerMap.get(name)
  }

  finalMatches.value.forEach((match) => {
    const finalists = [
      [match.p1_name, match.p1_avatar],
      [match.p1_partner_name, null],
      [match.p2_name, match.p2_avatar],
      [match.p2_partner_name, null]
    ]
    finalists.forEach(([name, avatar]) => {
      const row = ensurePlayer(name, avatar)
      if (row) row.finals_count += 1
    })

    const winnerNames = match.winner_side === 'side_a'
      ? [[match.p1_name, match.p1_avatar], [match.p1_partner_name, null]]
      : match.winner_side === 'side_b'
        ? [[match.p2_name, match.p2_avatar], [match.p2_partner_name, null]]
        : []
    winnerNames.forEach(([name, avatar]) => {
      const row = ensurePlayer(name, avatar)
      if (row) row.titles_count += 1
    })
  })

  return [...playerMap.values()]
    .sort((a, b) => {
      if (b.finals_count !== a.finals_count) return b.finals_count - a.finals_count
      if (b.titles_count !== a.titles_count) return b.titles_count - a.titles_count
      return (b.matches_played || 0) - (a.matches_played || 0)
    })
    .map((row, index) => ({
      ...row,
      rank: index + 1,
      elo_points: row.finals_count,
      matches_played: row.titles_count
    }))
})

const displayedRankings = computed(() => {
  if (activeRankingTab.value === 'Doubles') return doublesRankings.value
  if (activeRankingTab.value === 'Race') return raceToFinalsRankings.value
  return rankings.value
})

const rankingTableLabels = computed(() => {
  if (activeRankingTab.value === 'Doubles') {
    return {
      player: 'Cặp vận động viên',
      points: 'Tổng điểm',
      matches: 'Tổng trận',
      winRate: 'Tỉ lệ thắng'
    }
  }
  if (activeRankingTab.value === 'Race') {
    return {
      player: 'Vận động viên',
      points: 'Vào chung kết',
      matches: 'Vô địch',
      winRate: 'Tỉ lệ thắng'
    }
  }
  return {
    player: t('rankings.player'),
    points: t('rankings.points'),
    matches: t('rankings.matches'),
    winRate: t('rankings.winRate')
  }
})

const setRankingTab = (tab) => {
  activeRankingTab.value = tab
  if (tab === 'Singles') filters.value.category = ''
  if (tab === 'Doubles') filters.value.category = ''
}
// TỰ ĐỘNG LỌC LẠI KHI NGƯỜI DÙNG CHỌN MENU THẢ XUỐNG
watch(filters, () => {
  fetchRankings()
}, { deep: true })
onMounted(async () => {
  await Promise.all([fetchRankings(), fetchFinalMatches()])
})
</script>

<template>
  <div class="atp-ranking-page">
    
    <div class="top-ad-banner">
      <MarketingBannerStrip placement="rankings_top" variant="compact" :max="3" />
    </div>

    <div class="container layout-grid">
      
      <main class="main-content">
        
        <div class="ranking-header-section">
          <div class="title-row">
            <h1 class="page-title"><el-icon class="pif-icon"><Trophy /></el-icon> {{ t('rankings.sgt') }} <span>{{ t('rankings.rankingsTitle') }}</span></h1>
          </div>

          <div class="inline-filters">
            <div class="filter-tabs">
              <span class="f-tab" :class="{ active: activeRankingTab === 'Singles' }" @click="setRankingTab('Singles')">{{ t('rankings.singlesTab') }}</span>
              <span class="f-tab" :class="{ active: activeRankingTab === 'Doubles' }" @click="setRankingTab('Doubles')">{{ t('rankings.doublesTab') }}</span>
              <span class="f-tab" :class="{ active: activeRankingTab === 'Race' }" @click="setRankingTab('Race')">{{ t('rankings.raceToFinals') }}</span>
            </div>

            <div class="filter-dropdowns">
              <el-select
                v-model="filters.category"
                :placeholder="t('rankings.searchPlaceholder')"
                clearable
                class="flat-select"
                @change="fetchRankings"
              >
                <el-option
                  v-for="category in categoryOptions"
                  :key="category"
                  :label="formatCategoryLabel(category)"
                  :value="category"
                />
              </el-select>

              <el-select
                v-model="filters.province"
                :placeholder="t('rankings.regionPlaceholder')"
                clearable
                filterable
                class="flat-select"
                @change="fetchRankings"
              >
                <el-option
                  v-for="province in provinceOptions"
                  :key="province"
                  :label="province"
                  :value="province"
                />
              </el-select>
            </div>
          </div>
        </div>

        <div class="ranking-list-container" v-loading="isLoading">
          <div v-if="displayedRankings.length === 0" class="empty-state">
            <el-empty :description="t('common.noData') || t('rankings.noDataDesc')" />
          </div>

          <table v-else class="atp-flat-table">
            <thead>
              <tr>
                <th class="col-rank">{{ t('rankings.rank') }}</th>
                <th class="col-player">{{ rankingTableLabels.player }}</th>
                <th class="col-level hidden-mobile text-center">{{ t('rankings.level') }}</th>
                <th class="col-pts text-center">{{ rankingTableLabels.points }}</th>
                <th class="col-matches hidden-mobile text-center">{{ rankingTableLabels.matches }}</th>
                <th class="col-winrate hidden-mobile text-center">{{ rankingTableLabels.winRate }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="player in displayedRankings" :key="player.player_id">
                <td class="col-rank">
                  <span class="rank-num">{{ player.rank }}</span>
                </td>
                <td class="col-player">
                  <div class="player-info-cell" :class="{ 'is-pair': player.isDoublesPair }">
                    <div class="avatar-stack" v-if="player.isDoublesPair">
                      <img :src="player.avatar_url || `https://ui-avatars.com/api/?name=${player.full_name}`" class="player-ava" referrerpolicy="no-referrer" />
                      <img :src="player.partner_avatar_url || `https://ui-avatars.com/api/?name=${player.partner_name}`" class="player-ava partner-ava" referrerpolicy="no-referrer" />
                    </div>
                    <img v-else :src="player.avatar_url || `https://ui-avatars.com/api/?name=${player.full_name}`" class="player-ava" referrerpolicy="no-referrer" />
                    <div class="player-name-block">
                      <strong class="player-name">{{ player.full_name }}</strong>
                      <span v-if="player.isDoublesPair" class="pair-note">Ghép từ hạng {{ (player.rank - 1) * 2 + 1 }} và {{ (player.rank - 1) * 2 + 2 }}</span>
                      <span v-if="player.isRaceRow" class="pair-note">{{ player.titles_count }} danh hiệu chung kết</span>
                    </div>
                  </div>
                </td>
                <td class="col-level hidden-mobile text-center">
                  {{ player.skill_level || 'N/A' }}
                </td>
                <td class="col-pts text-center">
                  <strong class="points-val">{{ player.elo_points }}</strong>
                </td>
                <td class="col-matches hidden-mobile text-center">
                  {{ player.matches_played || 0 }}
                </td>
                <td class="col-winrate hidden-mobile text-center">
                  {{ player.win_rate || 0 }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>

      <aside class="sidebar">
        <div class="widget-scores">
          <div class="ws-header">
            <h3>{{ t('rankings.scores') }}</h3>
            <a href="#" class="ws-link">{{ t('rankings.seeAll') }} <el-icon><ArrowRight /></el-icon></a>
          </div>
          <div class="ws-tabs">
            <span class="ws-tab active">{{ t('rankings.sgtTour') }}</span>
            <span class="ws-tab">{{ t('rankings.challenger') }}</span>
          </div>
          
          <div class="ws-body">
            <div class="ws-tour-name">
              <h4>{{ t('rankings.saigonMasters') }}</h4>
              <p>{{ t('rankings.hcmc') }}</p>
            </div>
            
            <div class="ws-subtabs">
              <span class="ws-sub active">{{ t('rankings.allScores') }}</span>
              <span class="ws-sub">{{ t('rankings.schedule') }}</span>
              <span class="ws-sub">{{ t('rankings.draw') }}</span>
            </div>

            <div class="ws-match">
              <div class="match-status">{{ t('rankings.finalCenterCourt') }} <span>01:15:20</span></div>
              
              <div class="match-player">
                <div class="mp-name"><span class="flag-mini"></span> Nguyễn M. Phú <span class="seed">(1)</span> <el-icon class="winner-check"><Check /></el-icon></div>
                <div class="mp-score">
                  <span>6</span><span>6</span>
                </div>
              </div>
              
              <div class="match-player">
                <div class="mp-name"><span class="flag-mini"></span> Nguyễn M. Anh <span class="seed">(2)</span></div>
                <div class="mp-score">
                  <span>4</span><span>2</span>
                </div>
              </div>

              <div class="match-footer">
                <span class="umpire">{{ t('rankings.umpire') }}</span>
                <div class="mf-links">
                  <a href="#">{{ t('rankings.h2h') }}</a>
                  <a href="#">{{ t('rankings.stats') }}</a>
                </div>
              </div>
              <p class="match-summary">{{ t('rankings.matchSummary') }}</p>
            </div>
          </div>
        </div>
      </aside>

    </div>
  </div>
</template>

<style scoped>
/* =========================================================
   TỔNG QUAN THEME THEO PHONG CÁCH ATP CHÍNH THỨC
========================================================= */
.atp-ranking-page {
  background: #ffffff; /* Đổi nền thành màu Trắng tinh */
  min-height: 100vh;
  font-family: 'Inter', -apple-system, sans-serif;
  color: #002855; /* Navy Blue text chủ đạo */
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
.ad-placeholder img {
  max-width: 100%;
  height: auto;
  max-height: 90px;
}

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
   HEADER BẢNG XẾP HẠNG & BỘ LỌC
========================================================= */
.ranking-header-section {
  margin-bottom: 1rem;
}

.title-row {
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 800;
  font-style: italic;
  margin: 0;
  color: #002855;
  display: flex;
  align-items: center;
  gap: 10px;
}

.pif-icon {
  background: #002855;
  color: white;
  padding: 4px;
  border-radius: 50%;
  font-size: 1.4rem;
}

.inline-filters {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 10px;
}

.filter-tabs {
  display: flex;
  gap: 1.5rem;
}

.f-tab {
  font-size: 0.9rem;
  font-weight: 700;
  color: #64748b;
  cursor: pointer;
  padding-bottom: 10px;
  position: relative;
}

.f-tab.active {
  color: #00b0f0; /* Màu xanh lơ ATP */
}

.f-tab.active::after {
  content: '';
  position: absolute;
  bottom: -11px;
  left: 0;
  width: 100%;
  height: 3px;
  background: #00b0f0;
}

.filter-dropdowns {
  display: flex;
  gap: 1rem;
}

/* Select Box không viền cứng */
:deep(.flat-select .el-input__wrapper) {
  box-shadow: none !important;
  background: transparent;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 4px 12px;
}
:deep(.flat-select .el-input__wrapper.is-focus) {
  border-color: #002855;
}
:deep(.flat-select .el-input__inner) {
  font-weight: 600;
  color: #0f172a;
  font-size: 0.85rem;
}

/* =========================================================
   TABLE BẢNG XẾP HẠNG (FLAT LIST)
========================================================= */
.ranking-list-container {
  width: 100%;
}

.atp-flat-table {
  width: 100%;
  border-collapse: collapse;
}

.atp-flat-table th {
  text-align: left;
  font-size: 0.75rem;
  text-transform: uppercase;
  color: #64748b;
  font-weight: 600;
  padding: 1rem 0.5rem;
  border-bottom: 1px solid #cbd5e1;
}

.atp-flat-table td {
  padding: 1rem 0.5rem;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.text-center { text-align: center !important; }

/* Các cột */
.col-rank { width: 60px; font-weight: 800; font-size: 1.1rem;}
.rank-num { color: #002855; }

.col-player { min-width: 250px; }
.player-info-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.player-info-cell.is-pair {
  gap: 14px;
}

.avatar-stack {
  position: relative;
  width: 68px;
  height: 44px;
  flex-shrink: 0;
}

.avatar-stack .player-ava {
  position: absolute;
  left: 0;
  top: 0;
  border: 2px solid #fff;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.12);
}

.avatar-stack .partner-ava {
  left: 28px;
}

.player-ava {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid #e2e8f0;
}

.flag-mini { font-size: 0.9rem; }

.player-name-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.player-name {
  font-size: 1.05rem;
  color: #002855;
  font-weight: 700;
}

.pair-note {
  font-size: 0.72rem;
  font-weight: 700;
  color: #64748b;
}

.col-level { font-size: 0.9rem; color: #475569; }
.col-matches, .col-winrate { font-size: 0.9rem; color: #475569; font-weight: 600;}

.col-pts { width: 100px; }
.points-val {
  font-size: 1.15rem;
  font-weight: 800;
  color: #002855;
}

/* =========================================================
   SIDEBAR SCORES WIDGET (NHƯ HÌNH ATP)
========================================================= */
.widget-scores {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: white;
  overflow: hidden;
}

.ws-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
}

.ws-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 800;
  font-style: italic;
  color: #002855;
}

.ws-link {
  font-size: 0.75rem;
  color: #00b0f0;
  text-decoration: none;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 4px;
}

.ws-tabs {
  display: flex;
  border-bottom: 1px solid #e2e8f0;
}

.ws-tab {
  flex: 1;
  text-align: center;
  padding: 0.8rem 0;
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
}

.ws-tab.active {
  color: #00b0f0;
  border-bottom: 2px solid #00b0f0;
}

.ws-body {
  padding: 1.25rem;
}

.ws-tour-name h4 { margin: 0; font-size: 0.9rem; color: #002855; font-weight: 800;}
.ws-tour-name p { margin: 4px 0 1rem; font-size: 0.75rem; color: #64748b; }

.ws-subtabs {
  display: flex;
  gap: 10px;
  margin-bottom: 1.5rem;
}

.ws-sub {
  border: 1px solid #cbd5e1;
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 0.75rem;
  font-weight: 700;
  color: #002855;
  cursor: pointer;
}

.ws-sub.active {
  border-color: #00b0f0;
  color: #00b0f0;
}

.match-status {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: #64748b;
  margin-bottom: 0.8rem;
}

.match-player {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.6rem;
}

.mp-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #002855;
  display: flex;
  align-items: center;
  gap: 8px;
}

.seed { font-weight: 400; color: #94a3b8; font-size: 0.8rem;}
.winner-check { color: #16a34a; font-size: 1rem; font-weight: bold;}

.mp-score {
  display: flex;
  gap: 12px;
  font-weight: 800;
  font-size: 1rem;
}

.match-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f1f5f9;
}

.umpire { font-size: 0.7rem; color: #94a3b8; }
.mf-links { display: flex; gap: 10px; }
.mf-links a {
  border: 1px solid #cbd5e1;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  text-decoration: none;
  color: #64748b;
  font-weight: 600;
}

.match-summary {
  font-size: 0.7rem;
  color: #94a3b8;
  margin-top: 0.8rem;
  line-height: 1.4;
}

/* =========================================================
   RESPONSIVE
========================================================= */
@media (max-width: 1024px) {
  .layout-grid {
    grid-template-columns: 1fr;
    gap: 2.5rem;
  }
  .sidebar {
    order: 2;
    margin-top: 1rem;
  }
}

@media (max-width: 768px) {
  .container { padding: 0 1rem; }
  
  .layout-grid { margin-top: 1rem; gap: 2rem; }

  .ranking-header-section { margin-bottom: 0.5rem; }

  .inline-filters {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
    padding-bottom: 0;
    border-bottom: none;
  }

  .filter-tabs {
    display: flex;
    gap: 1.2rem;
    overflow-x: auto;
    padding-bottom: 8px;
    white-space: nowrap;
    border-bottom: 1px solid #f1f5f9;
  }
  .f-tab { padding-bottom: 8px; font-size: 0.85rem; }
  .f-tab.active::after { bottom: -9px; }

  .filter-dropdowns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    margin-top: 0.5rem;
  }

  .ranking-list-container {
    margin: 0.5rem 0 0;
    overflow-x: visible; /* Bỏ cuộn ngang nếu có thể fit */
  }

  .atp-flat-table {
    min-width: auto; /* Cho phép co giãn tự do */
  }

  .atp-flat-table th { padding: 0.8rem 0.4rem; }
  .atp-flat-table td { padding: 0.8rem 0.4rem; }

  .hidden-mobile { display: none !important; }
  
  .page-title { 
    font-size: 1.4rem; 
    justify-content: flex-start;
  }
  .page-title span { font-size: 1.2rem; }
  .pif-icon { font-size: 1.2rem; padding: 3px; }

  .col-rank { width: 40px; font-size: 0.95rem; }
  .col-pts { width: 80px; }
  .player-ava { width: 34px; height: 34px; }
  .player-name { font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px; }
  .points-val { font-size: 1rem; }
}

@media (max-width: 480px) {
  .filter-dropdowns { 
    grid-template-columns: 1fr; 
    gap: 0.5rem;
  }
  
  .title-row { margin-bottom: 0.8rem; }
  .page-title { font-size: 1.2rem; }
  .page-title span { font-size: 1rem; }
  
  .atp-flat-table th, .atp-flat-table td {
    padding: 0.6rem 0.3rem;
  }
  
  .rank-num { font-size: 0.85rem; }
  .points-val { font-size: 0.9rem; }
  
  .player-ava { width: 30px; height: 30px; }
  .player-name { font-size: 0.8rem; max-width: 110px; }
  
  /* Chống tràn cho sidebar widget */
  .ws-body { padding: 0.75rem; }
  .match-summary { font-size: 0.65rem; }
}
</style>
