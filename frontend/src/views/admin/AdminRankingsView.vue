<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import { Trophy, Top, Bottom, DataAnalysis, Filter, Search } from '@element-plus/icons-vue'
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

onMounted(fetchData)
</script>

<template>
  <div class="rankings-container">
    <!-- ACTION BAR -->
    <!-- HEADER PREMIUM -->
    <section class="action-bar-glass shadow-sm">
      <div class="action-info">
        <div class="kicker-wrap">
          <span class="section-kicker">Ranking & ELO Stats</span>
          <div class="live-indicator">
            <span class="dot"></span>
            LIVE
          </div>
        </div>
        <p>{{ $t('admin.rankingsDesc') }}</p>
      </div>

      <div class="filter-actions-v2">
        <el-input
          v-model="searchQuery"
          :placeholder="$t('admin.searchPlayerPlaceholder')"
          :prefix-icon="Search"
          style="width: 220px"
          round
          clearable
        />
        <el-select v-model="selectedCategory" style="width: 170px" @change="fetchData" round>
          <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
        <el-button :icon="DataAnalysis" type="primary" round @click="fetchData">{{ $t('admin.refresh') }}</el-button>
      </div>
    </section>

    <div class="stats-grid">
      <div class="stat-card-glass">
        <div class="si pro"><el-icon><Top /></el-icon></div>
        <div class="sd">
          <div class="val">{{ filteredPlayers.filter(p => p.elo_points >= 1200).length }}</div>
          <div class="lab">{{ $t('admin.proRank') }}</div>
        </div>
      </div>
      <div class="stat-card-glass">
        <div class="si avg"><el-icon><DataAnalysis /></el-icon></div>
        <div class="sd">
          <div class="val">{{ Math.round(filteredPlayers.reduce((acc, p) => acc + p.elo_points, 0) / (filteredPlayers.length || 1)) }}</div>
          <div class="lab">{{ $t('admin.avgElo') }}</div>
        </div>
      </div>
      <div class="stat-card-glass">
        <div class="si active"><el-icon><Filter /></el-icon></div>
        <div class="sd">
          <div class="val">{{ filteredPlayers.length }}</div>
          <div class="lab">{{ $t('admin.totalPlayers') }}</div>
        </div>
      </div>
    </div>

    <div class="table-card-premium shadow-sm" v-loading="isLoading">
      <el-table :data="filteredPlayers" style="width: 100%" class="modern-rank-table">
        <el-table-column :label="$t('admin.rank')" min-width="80" align="center">
          <template #default="scope">
            <div class="rank-badge-cell">
              <div v-if="scope.$index < 3" class="trophy-wrap" :class="'rank-' + (scope.$index + 1)">
                <el-icon><Trophy /></el-icon>
                <span>{{ scope.$index + 1 }}</span>
              </div>
              <span v-else class="rank-num">{{ scope.$index + 1 }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.player')" min-width="280">
          <template #default="scope">
            <div class="player-profile-cell">
              <el-avatar :size="40" :src="scope.row.avatar_url">
                {{ scope.row.full_name?.charAt(0) }}
              </el-avatar>
              <div class="p-info">
                <span class="p-name">{{ scope.row.full_name }}</span>
                <span class="p-email">{{ scope.row.email || 'Saigon Tennis Member' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.eloPoints')" min-width="120" sortable prop="elo_points" align="center">
          <template #default="scope">
            <div class="elo-pill" :style="{ background: getEloTrendColor(scope.row.elo_points) }">
              {{ scope.row.elo_points }}
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.matchesPlayed')" min-width="100" align="center">
          <template #default="scope">
            <span class="m-played">{{ scope.row.matches_played }}</span>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.winRate')" min-width="200">
          <template #default="{ row }">
            <div class="win-rate-stack">
              <div class="wr-top">
                <span class="wr-val">{{ Math.round((row.wins / (row.matches_played || 1)) * 100) }}%</span>
                <span class="wr-stat">{{ row.wins }}W - {{ row.matches_played - row.wins }}L</span>
              </div>
              <el-progress 
                :percentage="Math.round((row.wins / (row.matches_played || 1)) * 100)" 
                :show-text="false" 
                :stroke-width="6" 
                stroke-linecap="round"
                :color="row.wins / (row.matches_played || 1) > 0.5 ? '#10b981' : '#3b82f6'"
              />
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('admin.skillLevel')" min-width="150" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.skill_level === 'Professional' ? 'danger' : 'info'" effect="light" class="level-pill">
              {{ scope.row.skill_level || 'UNRANKED' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.rankings-container { display: grid; gap: 16px; padding: 10px; }

.action-bar-glass {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  padding: 16px 24px;
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
.filter-actions-v2 { display: flex; gap: 12px; }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }

.stat-card-glass {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
  padding: 20px 24px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.02);
  transition: all 0.3s ease;
}
.stat-card-glass:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.05); }

.si { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; }
.si.pro { background: #fef2f2; color: #ef4444; }
.si.avg { background: #eff6ff; color: #3b82f6; }
.si.active { background: #f0fdf4; color: #10b981; }

.val { font-size: 1.8rem; font-weight: 900; color: #0f172a; line-height: 1; }
.lab { font-size: 0.75rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-top: 4px; }

.table-card-premium {
  background: white; border-radius: 24px; border: 1px solid #f1f5f9;
  box-shadow: 0 10px 40px rgba(0,0,0,0.02); overflow: hidden;
}

.rank-badge-cell { display: flex; justify-content: center; align-items: center; }
.trophy-wrap {
  width: 36px; height: 36px; border-radius: 50%; display: flex;
  flex-direction: column; align-items: center; justify-content: center; font-size: 1rem; position: relative;
}
.trophy-wrap span { font-size: 0.6rem; font-weight: 900; position: absolute; bottom: 2px; }

.rank-1 { background: #fffbeb; color: #f59e0b; border: 1px solid #fde68a; }
.rank-2 { background: #f8fafc; color: #94a3b8; border: 1px solid #e2e8f0; }
.rank-3 { background: #fff7ed; color: #c2410c; border: 1px solid #ffedd5; }
.rank-num { font-weight: 800; color: #cbd5e1; font-size: 1.1rem; }

.player-profile-cell { display: flex; align-items: center; gap: 16px; }
.p-info { display: flex; flex-direction: column; }
.p-name { font-weight: 700; color: #0f172a; font-size: 1rem; }
.p-email { font-size: 0.75rem; color: #94a3b8; }

.elo-pill {
  padding: 4px 16px; border-radius: 99px; color: white; font-weight: 900;
  font-size: 0.85rem; display: inline-block; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

.m-played { font-weight: 800; color: #475569; font-size: 1rem; }

.win-rate-stack { display: flex; flex-direction: column; gap: 6px; }
.wr-top { display: flex; justify-content: space-between; align-items: flex-end; }
.wr-val { font-size: 1rem; font-weight: 900; color: #0f172a; line-height: 1; }
.wr-stat { font-size: 0.65rem; font-weight: 700; color: #94a3b8; }

.level-pill { font-weight: 800; border-radius: 99px; padding: 0 16px; font-size: 0.65rem; border: none !important; }

:deep(.el-table) { border-radius: 16px; }
:deep(.el-table .cell) { padding: 16px 20px; }
.shadow-sm { box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
</style>
