<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import { Trophy, Check, ArrowRight } from '@element-plus/icons-vue'
import { t } from '../../utils/locale'

const rankings = ref([])
const isLoading = ref(true)

const filters = ref({
  category: '',
  province: ''
})

const provinceOptions = ref([])
const categoryOptions = ref([])

const formatCategoryLabel = (value) => {
  if (!value) return ''
  if (value === 'Singles') return t('common.singles') || 'Đơn'
  if (value === 'Doubles') return t('common.doubles') || 'Đôi'
  return value
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

const fetchRankings = async () => {
  isLoading.value = true
  try {
    let url = '/api/players/rankings'
    const queryParts = []

    if (filters.value.category) {
      queryParts.push(`category=${encodeURIComponent(filters.value.category)}`)
    }

    if (filters.value.province) {
      queryParts.push(`province=${encodeURIComponent(filters.value.province)}`)
    }

    if (queryParts.length > 0) {
      url += `?${queryParts.join('&')}`
    }

    const data = await apiClient.get(url)
    const normalized = data || []
    
    // Lọc admin và đánh lại số thứ tự
    const filteredPlayers = normalized.filter(p => !p.full_name?.toLowerCase().includes('admin'))
    rankings.value = filteredPlayers.map((player, index) => ({
      ...player,
      rank: index + 1
    }))

    if (!filters.value.category && !filters.value.province) {
      buildFilterOptions(rankings.value)
    }
  } catch (error) {
    ElMessage.error(t('common.errorLoading') || 'Lỗi tải dữ liệu')
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchRankings)
</script>

<template>
  <div class="atp-ranking-page">
    
    <div class="top-ad-banner">
      <div class="ad-placeholder">
        <img src="https://tpc.googlesyndication.com/simgad/9470293650305402252" alt="Sponsor Banner" />
      </div>
    </div>

    <div class="container layout-grid">
      
      <main class="main-content">
        
        <div class="ranking-header-section">
          <div class="title-row">
            <h1 class="page-title"><el-icon class="pif-icon"><Trophy /></el-icon> {{ t('rankings.sgt') }} <span>{{ t('rankings.rankingsTitle') }}</span></h1>
          </div>

          <div class="inline-filters">
            <div class="filter-tabs">
              <span class="f-tab active">{{ t('rankings.singlesTab') }}</span>
              <span class="f-tab">{{ t('rankings.doublesTab') }}</span>
              <span class="f-tab">{{ t('rankings.raceToFinals') }}</span>
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
          <div v-if="rankings.length === 0" class="empty-state">
            <el-empty :description="t('common.noData') || t('rankings.noDataDesc')" />
          </div>

          <table v-else class="atp-flat-table">
            <thead>
              <tr>
                <th class="col-rank">{{ t('rankings.rank') }}</th>
                <th class="col-player">{{ t('rankings.player') }}</th>
                <th class="col-level hidden-mobile text-center">{{ t('rankings.level') }}</th>
                <th class="col-pts text-center">{{ t('rankings.points') }}</th>
                <th class="col-matches hidden-mobile text-center">{{ t('rankings.matches') }}</th>
                <th class="col-winrate hidden-mobile text-center">{{ t('rankings.winRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="player in rankings" :key="player.player_id">
                <td class="col-rank">
                  <span class="rank-num">{{ player.rank }}</span>
                </td>
                <td class="col-player">
                  <div class="player-info-cell">
                    <img :src="player.avatar_url || `https://ui-avatars.com/api/?name=${player.full_name}`" class="player-ava" />
                    <span class="flag-mini">🇻🇳</span>
                    <strong class="player-name">{{ player.full_name }}</strong>
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
                <div class="mp-name"><span class="flag-mini">🇻🇳</span> Nguyễn M. Phú <span class="seed">(1)</span> <el-icon class="winner-check"><Check /></el-icon></div>
                <div class="mp-score">
                  <span>6</span><span>6</span>
                </div>
              </div>
              
              <div class="match-player">
                <div class="mp-name"><span class="flag-mini">🇻🇳</span> Nguyễn M. Anh <span class="seed">(2)</span></div>
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
  padding: 1.5rem 0;
  display: flex;
  justify-content: center;
  border-bottom: 1px solid #e2e8f0;
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

.player-ava {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid #e2e8f0;
}

.flag-mini { font-size: 0.9rem; }

.player-name {
  font-size: 1.05rem;
  color: #002855;
  font-weight: 700;
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
    grid-template-columns: 1fr; /* Rớt cột phải xuống dưới */
  }
}

@media (max-width: 768px) {
  .inline-filters {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  .hidden-mobile { display: none; }
  .page-title { font-size: 1.5rem; }
}

@media (max-width: 480px) {
  .filter-dropdowns { flex-direction: column; width: 100%;}
  :deep(.flat-select) { width: 100%; }
}
</style>