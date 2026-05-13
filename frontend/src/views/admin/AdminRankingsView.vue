<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import { 
  Trophy, Top, Bottom, DataAnalysis, Filter, Search,
  TrendCharts, Monitor, Refresh, User, StarFilled
} from '@element-plus/icons-vue'
import { t } from '../../utils/locale'

const players = ref([])
const isLoading = ref(false)
const searchQuery = ref('')
const selectedCategory = ref('ALL')

const categories = computed(() => [
  { label: t('admin.allSkillLevels'), value: 'ALL' },
  { label: 'Beginner', value: 'Beginner' },
  { label: 'Intermediate', value: 'Intermediate' },
  { label: 'Advanced', value: 'Advanced' },
  { label: 'Professional', value: 'Professional' }
])

const fetchData = async () => {
  isLoading.value = true
  try {
    const data = await apiClient.get('/api/players/rankings')
    players.value = data
  } catch (err) {
    ElMessage.error(t('admin.loadRankingsError') + ': ' + err.message)
  } finally {
    isLoading.value = false
  }
}

const filteredPlayers = computed(() => {
  return players.value.filter(p => {
    const matchSearch = !searchQuery.value || p.full_name?.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchSkill = selectedCategory.value === 'ALL' || p.skill_level === selectedCategory.value
    return matchSearch && matchSkill
  })
})

const getEloTrendColor = (elo) => {
  if (elo >= 1500) return '#ef4444' // Grandmaster
  if (elo >= 1200) return '#3b82f6' // Pro
  return '#10b981' // Amateur
}

const getEloTrendClass = (elo) => {
  if (elo >= 1500) return 'is-elite'
  if (elo >= 1200) return 'is-pro'
  return 'is-amateur'
}

onMounted(fetchData)
</script>

<template>
  <div class="saas-container">
    <!-- Stats Grid -->
    <div class="saas-stats-grid">
      <div class="saas-stat-card">
        <div class="stat-icon p-red"><el-icon><Top /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.proRank') }}</span>
          <h3 class="stat-value">{{ filteredPlayers.filter(p => p.elo_points >= 1200).length }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-blue"><el-icon><TrendCharts /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.avgElo') }}</span>
          <h3 class="stat-value">{{ Math.round(filteredPlayers.reduce((acc, p) => acc + p.elo_points, 0) / (filteredPlayers.length || 1)) }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-green"><el-icon><User /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.totalPlayers') }}</span>
          <h3 class="stat-value">{{ filteredPlayers.length }}</h3>
        </div>
      </div>
    </div>

    <!-- Header & Action Bar -->
    <div class="saas-header">
      <div class="header-left">
        <div class="operation-badge">
          <el-icon class="mr-1"><Monitor /></el-icon>
          <span>Ranking Engine</span>
        </div>
        <el-input
          v-model="searchQuery"
          :placeholder="$t('admin.searchPlayerPlaceholder')"
          :prefix-icon="Search"
          class="saas-search"
          clearable
        />
        <el-select v-model="selectedCategory" class="saas-filter" @change="fetchData">
          <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
        <el-button :icon="Refresh" circle @click="fetchData" class="saas-icon-btn" />
      </div>
    </div>

    <!-- Main Content: Ranking Table -->
    <div class="saas-content-area" v-loading="isLoading">
      <el-table 
        :data="filteredPlayers" 
        class="saas-table"
        :header-cell-style="{ background: 'transparent', color: '#1e293b', fontWeight: '800', borderBottom: '2px solid #e2e8f0' }"
      >
        <el-table-column :label="$t('admin.rank')" width="100" align="center">
          <template #default="scope">
            <div class="rank-badge-premium">
              <div v-if="scope.$index < 3" class="trophy-hexagon" :class="'rank-' + (scope.$index + 1)">
                <el-icon><Trophy /></el-icon>
                <span class="rank-val">{{ scope.$index + 1 }}</span>
              </div>
              <span v-else class="rank-num-saas">{{ scope.$index + 1 }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.player')" min-width="300">
          <template #default="scope">
            <div class="saas-premium-cell">
              <div class="avatar-wrapper-premium">
                <el-avatar :size="48" :src="scope.row.avatar_url" class="saas-avatar-premium">
                  {{ scope.row.full_name?.charAt(0) }}
                </el-avatar>
                <div v-if="scope.$index < 10" class="star-badge"><el-icon><StarFilled /></el-icon></div>
              </div>
              <div class="cell-meta">
                <span class="cell-title">{{ scope.row.full_name }}</span>
                <span class="cell-subtitle">{{ scope.row.email || 'Saigon Tennis Member' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.eloPoints')" width="160" align="center">
          <template #default="scope">
            <div class="elo-score-saas" :class="getEloTrendClass(scope.row.elo_points)">
              <span class="elo-val">{{ scope.row.elo_points }}</span>
              <span class="elo-lbl">ELO</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.matchesPlayed')" width="140" align="center">
          <template #default="scope">
            <span class="match-count-pill">{{ scope.row.matches_played }} {{ $t('admin.matchCountLabel') }}</span>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.winRate')" min-width="220">
          <template #default="{ row }">
            <div class="saas-winrate-box">
              <div class="wr-header-saas">
                <span class="wr-percent">{{ Math.round((row.wins / (row.matches_played || 1)) * 100) }}%</span>
                <span class="wr-detail">{{ row.wins }}W - {{ row.matches_played - row.wins }}L</span>
              </div>
              <el-progress 
                :percentage="Math.round((row.wins / (row.matches_played || 1)) * 100)" 
                :show-text="false" 
                :stroke-width="8" 
                :color="row.wins / (row.matches_played || 1) > 0.5 ? '#10b981' : '#3b82f6'"
                class="saas-progress-bar"
              />
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.skillLevel')" width="160" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.skill_level === 'Professional' ? 'danger' : 'info'" effect="dark" round class="saas-skill-tag">
              {{ scope.row.skill_level || 'UNRANKED' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.saas-container { display: flex; flex-direction: column; gap: 32px; min-height: 100%; }

/* Stats Grid */
.saas-stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; }
.saas-stat-card {
  background: #fff; border-radius: 24px; padding: 24px; display: flex; align-items: center; gap: 20px;
  border: 1px solid #f1f5f9; transition: all 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.02);
}
.saas-stat-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.05); }

.stat-icon { width: 56px; height: 56px; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 24px; }
.p-red { background: #fef2f2; color: #ef4444; }
.p-blue { background: #eff6ff; color: #3b82f6; }
.p-green { background: #ecfdf5; color: #10b981; }

.stat-label { font-size: 0.75rem; color: #94a3b8; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; }
.stat-value { font-size: 1.8rem; font-weight: 900; color: #0f172a; margin: 4px 0 0; }

/* Header & Action Bar */
.saas-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.header-left { display: flex; align-items: center; gap: 12px; }

.operation-badge {
  background: #fdf2f8; color: #db2777; padding: 8px 16px; border-radius: 12px;
  font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;
  display: flex; align-items: center; border: 1px solid #fce7f3;
}

.saas-search { width: 280px; }
.saas-filter { width: 180px; }

:deep(.el-input__wrapper), :deep(.el-select__wrapper) {
  background-color: #f8fafc !important;
  box-shadow: none !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 12px !important;
  padding: 8px 12px !important;
}

.saas-icon-btn {
  width: 44px; height: 44px; border-radius: 12px !important;
  background: #f8fafc !important; border: 1px solid #e2e8f0 !important;
}

/* Ranking Table */
.saas-content-area { background: #fff; border-radius: 32px; border: 1px solid #f1f5f9; padding: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.02); }

.rank-badge-premium { display: flex; justify-content: center; align-items: center; }
.trophy-hexagon {
  width: 44px; height: 44px; position: relative; display: flex; flex-direction: column;
  align-items: center; justify-content: center; font-size: 1.2rem;
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
}
.rank-val { font-size: 0.65rem; font-weight: 900; position: absolute; bottom: 4px; }

.rank-1 { background: #fffbeb; color: #f59e0b; }
.rank-2 { background: #f8fafc; color: #94a3b8; }
.rank-3 { background: #fff7ed; color: #c2410c; }
.rank-num-saas { font-weight: 900; color: #cbd5e1; font-size: 1.2rem; font-family: monospace; }

.saas-premium-cell { display: flex; align-items: center; gap: 16px; }
.avatar-wrapper-premium { position: relative; }
.saas-avatar-premium { border: 2px solid #fff; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
.star-badge {
  position: absolute; top: -1px; right: -1px; background: #f59e0b; color: #fff;
  width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: 10px; border: 2px solid #fff;
}

.cell-meta { display: flex; flex-direction: column; gap: 2px; }
.cell-title { font-weight: 800; color: #0f172a; font-size: 1rem; }
.cell-subtitle { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }

.elo-score-saas {
  display: flex; flex-direction: column; align-items: center; line-height: 1;
  padding: 8px 16px; border-radius: 16px; min-width: 80px;
}
.elo-val { font-size: 1.3rem; font-weight: 900; }
.elo-lbl { font-size: 0.6rem; font-weight: 800; opacity: 0.8; margin-top: 2px; }

.is-elite { background: #fef2f2; color: #ef4444; }
.is-pro { background: #eff6ff; color: #3b82f6; }
.is-amateur { background: #ecfdf5; color: #10b981; }

.match-count-pill {
  background: #f8fafc; color: #475569; font-weight: 800; font-size: 0.8rem;
  padding: 6px 14px; border-radius: 99px; border: 1px solid #e2e8f0;
}

.saas-winrate-box { display: flex; flex-direction: column; gap: 8px; }
.wr-header-saas { display: flex; justify-content: space-between; align-items: flex-end; }
.wr-percent { font-size: 1.1rem; font-weight: 900; color: #0f172a; }
.wr-detail { font-size: 0.7rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; }
.saas-progress-bar { width: 100%; }

.saas-skill-tag { font-weight: 900; font-size: 0.7rem; letter-spacing: 0.05em; padding: 0 16px; height: 28px; line-height: 26px; border: none !important; }

.mr-1 { margin-right: 4px; }
</style>
