<script setup>
import { onMounted, ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { tournamentService } from '../../services/tournamentService' 
import { useAuthStore } from '../../stores/auth' 
import { getStoredAccessToken, getStoredTokenType } from '../../utils/authStorage'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiClient, { MAIN_API_URL } from '../../services/apiClient'
import { t } from '../../utils/locale'
import { 
  Trophy, Finished, EditPen, Menu,
  CircleCheckFilled, CircleCloseFilled,
  Search, Refresh, Edit, Delete, Location, User, Plus, VideoPlay, Calendar, VideoCamera, Picture
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const tournaments = ref([])
const selectedTournamentId = ref(null)
const matches = ref([])
const isLoading = ref(false)
const generating = ref(false)
const lastDrawSummary = ref(null)

const selectedCategoryId = ref(null)

// --- BIẾN CHO BỐC THĂM BAN ĐẦU ---
const isDrawDialogOpen = ref(false)
const drawForm = ref({
  category_id: null,
  format_type: 'knockout',
  num_groups: 1,
  draw_size: 16,
  round_names: []
})

const knockoutRoundCount = computed(() => {
  const size = Number(drawForm.value.draw_size || 0)
  if (size <= 1) return 1
  let rounds = 0
  let participants = size
  while (participants > 1) {
    const currentMatches = Math.ceil(participants / 2)
    rounds += 1
    participants = currentMatches
  }
  return rounds
})

const roundRobinPreview = computed(() => {
  const participantCount = Math.max(0, Number(drawForm.value.draw_size || 0))
  const groupCount = Math.max(1, Math.min(Number(drawForm.value.num_groups || 1), Math.max(1, participantCount)))
  if (participantCount < 2) {
    return {
      groupCount,
      groupSizes: [],
      matchCount: 0,
      label: 'Cần ít nhất 2 đội/cặp để tạo lịch vòng tròn.'
    }
  }

  const baseSize = Math.floor(participantCount / groupCount)
  const extraSlots = participantCount % groupCount
  const groupSizes = Array.from({ length: groupCount }, (_, index) => baseSize + (index < extraSlots ? 1 : 0))
  const matchCount = groupSizes.reduce((total, size) => total + (size * (size - 1)) / 2, 0)
  return {
    groupCount,
    groupSizes,
    matchCount,
    label: `${participantCount} đội/cặp, ${groupCount} bảng (${groupSizes.join(' - ')} đội/cặp), dự kiến ${matchCount} trận.`
  }
})

watch(knockoutRoundCount, (count) => {
  const defaults = ['Vòng 1', 'Tứ kết', 'Bán kết', 'Chung kết']
  drawForm.value.round_names = Array.from({ length: count }, (_, idx) => drawForm.value.round_names[idx] || defaults[Math.max(0, defaults.length - count + idx)] || `Vòng ${idx + 1}`)
}, { immediate: true })

watch(() => [drawForm.value.draw_size, drawForm.value.num_groups], ([drawSize, numGroups]) => {
  const participantCount = Number(drawSize || 0)
  const groupCount = Number(numGroups || 1)
  if (participantCount > 0 && groupCount > participantCount) {
    drawForm.value.num_groups = participantCount
  }
})

// --- BIẾN GÁN VĐV (GHÉP CẶP THỦ CÔNG) ---
const tournamentRegistrations = ref([])
const assignDialogVisible = ref(false)
const assigning = ref(false)
const currentAssignMatch = ref(null)
const assignForm = ref({
  side_a_registration_id: null,
  side_b_registration_id: null
})

const courts = ref([])
const manualDialogVisible = ref(false)
const controlDialogVisible = ref(false)
const roundNameDialogVisible = ref(false)
const matchDetailDialogVisible = ref(false)
const savingManualMatch = ref(false)
const savingControl = ref(false)
const savingRoundName = ref(false)
const isUploadingVideo = ref(false)
const isUploadingImage = ref(false)
const MAX_VIDEO_DURATION_SECONDS = 60
const MAX_VIDEO_SIZE_MB = 80
const MAX_IMAGE_SIZE_MB = 10
const VIDEO_UPLOAD_HINT = `Video tối đa ${MAX_VIDEO_DURATION_SECONDS} giây, dung lượng tối đa ${MAX_VIDEO_SIZE_MB}MB.`
const currentControlMatch = ref(null)
const currentViewedMatch = ref(null)
const currentRoundName = ref('')
const roundNameForm = ref({
  old_round_code: '',
  new_round_code: ''
})
const manualMatchForm = ref({
  category_id: null,
  stage_type: 'knockout',
  round_code: 'Vòng mới',
  match_no: null,
  side_a_registration_id: null,
  side_b_registration_id: null,
  status: 'pending',
  court_id: null,
  start_time: '',
  referee_name: '',
  referee_phone: '',
  live_stream_url: '',
  next_match_id: null,
  source_match_ids: []
})
const controlForm = ref({
  round_code: '',
  match_no: null,
  stage_type: 'knockout',
  side_a_registration_id: null,
  side_b_registration_id: null,
  status: 'pending',
  score: '',
  winner_side: '',
  court_id: null,
  start_time: '',
  referee_name: '',
  referee_phone: '',
  live_stream_url: '',
  video_url: '',
  image_url: '',
  next_match_id: null,
  advance_note: '',
  sets: [{ side_a: 0, side_b: 0 }]
})

// --- BIẾN CHO VÒNG PLAYOFF ---
const isPlayoffDialogOpen = ref(false)
const generatingPlayoff = ref(false)
const playoffForm = ref({
  category_id: null,
  advancers_per_group: 2
})

const openDrawDialog = () => {
  drawForm.value.category_id = selectedCategoryId.value
  isDrawDialogOpen.value = true
}
const openPlayoffDialog = () => {
  playoffForm.value.category_id = selectedCategoryId.value
  isPlayoffDialogOpen.value = true
}

const currentUserName = computed(() => {
  return authStore.profile?.full_name || authStore.user?.full_name || 'Admin'
})

const uploadHeaders = computed(() => {
  const accessToken = authStore.accessToken || getStoredAccessToken()
  const tokenType = authStore.tokenType || getStoredTokenType() || 'Bearer'
  if (!accessToken) return {}
  const normalizedType = tokenType.charAt(0).toUpperCase() + tokenType.slice(1).toLowerCase()
  return { Authorization: `${normalizedType} ${accessToken}` }
})

const hasGroupStage = computed(() => {
  if (!matches.value) return false
  return matches.value.some(m => m.round_code && m.round_code.includes('G'))
})

const currentTournament = computed(() => {
  return tournaments.value.find(t => t.id === selectedTournamentId.value) || null
})

const selectedCategory = computed(() => {
  if (!selectedCategoryId.value || !currentTournament.value?.categories) return null
  return currentTournament.value.categories.find(c => c.id === selectedCategoryId.value)
})

const canDraw = computed(() => {
  if (!currentTournament.value) return false
  return ['draft', 'open'].includes(currentTournament.value.status)
})

const fetchTournaments = async () => {
  try {
    const data = await tournamentService.getAll({ limit: 100 })
    tournaments.value = data
  } catch (err) {
    ElMessage.error(t('admin.loadTournamentsError') + ': ' + err.message)
  }
}

const fetchCourts = async () => {
  try {
    const data = await apiClient.get('/api/courts/')
    courts.value = Array.isArray(data) ? data : []
  } catch (err) {
    courts.value = []
  }
}

// Các hàm fetchMatches và handleTournamentChange đã được dời xuống dưới để gộp vào luồng khởi tạo chính.

const confirmGenerateDraw = async () => {
  if (!selectedTournamentId.value) return
  isDrawDialogOpen.value = false
  generating.value = true
  
  try {
    const response = await apiClient.post(`/api/tournaments/${selectedTournamentId.value}/generate-draw`, drawForm.value)
    lastDrawSummary.value = { message: response.message } 
    ElMessage.success(response.message || t('admin.drawSuccess'))
    await fetchMatchesAndRegistrations()
  } catch (err) {
    const errorMsg = err.response?.data?.detail || err.message
    ElMessage.error(t('admin.drawError') + ': ' + errorMsg)
  } finally {
    generating.value = false
  }
}

const confirmGeneratePlayoff = async () => {
  if (!selectedTournamentId.value) return
  isPlayoffDialogOpen.value = false
  generatingPlayoff.value = true
  
  try {
    const response = await apiClient.post(`/api/tournaments/${selectedTournamentId.value}/generate-playoffs`, playoffForm.value)
    ElMessage.success(response.message || t('admin.playoffSuccess'))
    await fetchMatchesAndRegistrations() 
  } catch (err) {
    const errorMsg = err.response?.data?.detail || err.message
    ElMessage.error(t('admin.playoffError') + ': ' + errorMsg)
  } finally {
    generatingPlayoff.value = false
  }
}

const roundOrder = (roundCode) => {
  const normalized = String(roundCode || '').toUpperCase()
  if (normalized.includes('G')) return 0
  const orderMap = {
    R128: 1,
    R64: 2,
    R32: 3,
    '1/16': 4,
    R16: 5,
    '1/8': 5,
    R8: 6,
    QF: 6,
    '1/4': 6,
    SF: 7,
    '1/2': 7,
    F: 8,
    FINAL: 8
  }
  return orderMap[normalized] ?? 99
}

const isGroupStageMatch = (match) => {
  const roundCode = String(match?.round_code || '').toUpperCase()
  return match?.stage_type === 'group_stage' || /^G\d+/.test(roundCode)
}

const getGroupIdFromMatch = (match) => {
  if (match?.group_id) return Number(match.group_id)
  const matchRound = String(match?.round_code || '').toUpperCase().match(/^G(\d+)/)
  return matchRound ? Number(matchRound[1]) : 1
}

const groupedMatches = computed(() => {
  const roundsMap = {}
  matches.value.forEach(m => {
    if (!roundsMap[m.round_code]) roundsMap[m.round_code] = []
    roundsMap[m.round_code].push(m)
  })
  return Object.entries(roundsMap)
    .map(([roundCode, items]) => ({
      roundCode,
      items: items.slice().sort((a, b) => (a.match_no || 0) - (b.match_no || 0)),
    }))
    .sort((a, b) => roundOrder(a.roundCode) - roundOrder(b.roundCode))
})

const groupRounds = computed(() => groupedMatches.value.filter(r => Array.isArray(r.items) && r.items.some(isGroupStageMatch)))
const roundRobinGroups = computed(() => {
  const groups = new Map()
  groupRounds.value.forEach(round => {
    round.items.forEach(match => {
      const groupId = getGroupIdFromMatch(match)
      if (!groups.has(groupId)) {
        groups.set(groupId, {
          groupId,
          title: `Bảng ${groupId}`,
          matchCount: 0,
          rounds: new Map()
        })
      }
      const group = groups.get(groupId)
      if (!group.rounds.has(round.roundCode)) {
        group.rounds.set(round.roundCode, {
          roundCode: round.roundCode,
          items: []
        })
      }
      group.rounds.get(round.roundCode).items.push(match)
      group.matchCount += 1
    })
  })

  return [...groups.values()]
    .sort((a, b) => a.groupId - b.groupId)
    .map(group => ({
      ...group,
      rounds: [...group.rounds.values()]
        .map(round => ({
          ...round,
          items: round.items.slice().sort((a, b) => (a.match_no || 0) - (b.match_no || 0))
        }))
        .sort((a, b) => roundOrder(a.roundCode) - roundOrder(b.roundCode) || a.roundCode.localeCompare(b.roundCode))
    }))
})
const knockoutRounds = computed(() => {
  const rounds = groupedMatches.value.filter(r => Array.isArray(r.items) && !r.items.some(isGroupStageMatch))
  const matchMap = new Map(matches.value.map(m => [m.id, m]))
  const memo = new Map()

  const distanceToFinal = (match, visiting = new Set()) => {
    if (!match?.id) return 0
    if (memo.has(match.id)) return memo.get(match.id)
    if (visiting.has(match.id)) {
      memo.set(match.id, 0)
      return 0
    }
    visiting.add(match.id)
    const next = match.next_match_id ? matchMap.get(match.next_match_id) : null
    const distance = next ? distanceToFinal(next, visiting) + 1 : 0
    visiting.delete(match.id)
    memo.set(match.id, distance)
    return distance
  }

  return rounds
    .map(round => ({
      ...round,
      items: Array.isArray(round.items) ? round.items : [],
      treeLevel: Math.max(...(Array.isArray(round.items) ? round.items : []).map(match => distanceToFinal(match)), 0)
    }))
    .sort((a, b) => {
      if (b.treeLevel !== a.treeLevel) return b.treeLevel - a.treeLevel
      if ((b.items || []).length !== (a.items || []).length) return (b.items || []).length - (a.items || []).length
      const orderA = roundOrder(a.roundCode)
      const orderB = roundOrder(b.roundCode)
      if (orderA !== orderB) return orderA - orderB
      return Math.min(...a.items.map(m => m.match_no || 0)) - Math.min(...b.items.map(m => m.match_no || 0))
    })
})

const buildBracketLayout = (roundList) => {
  const cardWidth = 280
  const cardHeight = 224
  const colGap = 86
  const rowGap = 38
  const headerHeight = 54
  const leftPad = 24
  const topPad = 12
  const itemById = new Map()
  const childrenById = new Map()

  roundList.forEach((round, colIndex) => {
    round.items.forEach((match, rowIndex) => {
      itemById.set(match.id, {
        id: match.id,
        match,
        roundCode: round.roundCode,
        colIndex,
        rowIndex,
        x: leftPad + colIndex * (cardWidth + colGap),
        y: topPad + headerHeight + rowIndex * (cardHeight + rowGap)
      })
      if (match.next_match_id) {
        if (!childrenById.has(match.next_match_id)) childrenById.set(match.next_match_id, [])
        childrenById.get(match.next_match_id).push(match.id)
      }
    })
  })

  roundList.forEach((round, colIndex) => {
    if (colIndex === 0) return
    round.items.forEach((match, rowIndex) => {
      const item = itemById.get(match.id)
      const childItems = (childrenById.get(match.id) || [])
        .map(id => itemById.get(id))
        .filter(Boolean)
      if (item && childItems.length) {
        const center = childItems.reduce((sum, child) => sum + child.y + cardHeight / 2, 0) / childItems.length
        item.y = Math.max(topPad + headerHeight, center - cardHeight / 2)
      } else if (item) {
        item.y = topPad + headerHeight + rowIndex * (cardHeight + rowGap)
      }
    })
  })

  const nodes = [...itemById.values()]
  const nodesByColumn = new Map()
  nodes.forEach(node => {
    if (!nodesByColumn.has(node.colIndex)) nodesByColumn.set(node.colIndex, [])
    nodesByColumn.get(node.colIndex).push(node)
  })
  nodesByColumn.forEach(columnNodes => {
    columnNodes.sort((a, b) => a.y - b.y || (a.match.match_no || 0) - (b.match.match_no || 0))
    columnNodes.forEach((node, index) => {
      if (index === 0) return
      const previous = columnNodes[index - 1]
      const minY = previous.y + cardHeight + rowGap
      if (node.y < minY) node.y = minY
    })
  })
  const connectors = []
  nodes.forEach(item => {
    const next = item.match.next_match_id ? itemById.get(item.match.next_match_id) : null
    if (!next) return
    const startX = item.x + cardWidth
    const startY = item.y + cardHeight / 2
    const endX = next.x
    const endY = next.y + cardHeight / 2
    const midX = startX + (endX - startX) / 2
    connectors.push({
      id: `${item.id}-${next.id}`,
      points: `${startX},${startY} ${midX},${startY} ${midX},${endY} ${endX},${endY}`
    })
  })

  const roundHeaders = roundList.map((round, index) => ({
    roundCode: round.roundCode,
    x: leftPad + index * (cardWidth + colGap),
    y: topPad
  }))

  const width = Math.max(900, leftPad * 2 + roundList.length * cardWidth + Math.max(0, roundList.length - 1) * colGap)
  const height = Math.max(
    320,
    topPad + headerHeight + Math.max(...nodes.map(node => node.y + cardHeight), cardHeight) + 36
  )

  return { nodes, connectors, roundHeaders, width, height, cardWidth, cardHeight }
}

const groupBracketLayout = computed(() => buildBracketLayout(groupRounds.value))
const bracketLayout = computed(() => buildBracketLayout(knockoutRounds.value))

const getStageRounds = (stageType) => {
  return stageType === 'group_stage' ? groupRounds.value : knockoutRounds.value
}

const getRoundIndex = (stageType, roundCode) => {
  return getStageRounds(stageType).findIndex(round => round.roundCode === roundCode)
}

const controlNextMatchOptions = computed(() => {
  const index = getRoundIndex(controlForm.value.stage_type, controlForm.value.round_code)
  if (index < 0) return []
  return getStageRounds(controlForm.value.stage_type)
    .slice(index + 1)
    .flatMap(round => round.items
      .filter(match => match.id !== currentControlMatch.value?.id)
      .map(match => ({
        id: match.id,
        label: `${round.roundCode} - #${match.match_no || match.id}`
      })))
})

const parseScoreToSets = (scoreText) => {
  if (!scoreText) return [{ side_a: 0, side_b: 0 }]
  const sets = String(scoreText)
    .split(',')
    .map(part => part.trim())
    .filter(Boolean)
    .map(part => {
      const [left, right] = part.split('-').map(value => Number.parseInt(String(value).trim(), 10))
      return {
        side_a: Number.isFinite(left) ? left : 0,
        side_b: Number.isFinite(right) ? right : 0
      }
    })
    .filter(set => Number.isFinite(set.side_a) && Number.isFinite(set.side_b))
  return sets.length ? sets : [{ side_a: 0, side_b: 0 }]
}

const formatSetsToScore = (sets) => {
  return (sets || [])
    .filter(set => set && (set.side_a !== null || set.side_b !== null))
    .map(set => `${Number(set.side_a || 0)}-${Number(set.side_b || 0)}`)
    .join(', ')
}

// Tải dữ liệu các trận đấu và đăng ký
const fetchMatchesAndRegistrations = async () => {
  if (!selectedTournamentId.value) {
    matches.value = []
    tournamentRegistrations.value = []
    return
  }
  isLoading.value = true
  try {
    const p1 = apiClient.get(`/api/tournaments/${selectedTournamentId.value}/matches` + 
                (selectedCategoryId.value ? `?category_id=${selectedCategoryId.value}` : ''))
    const p2 = apiClient.get(`/api/tournaments/${selectedTournamentId.value}/registrations` + 
                (selectedCategoryId.value ? `?category_id=${selectedCategoryId.value}` : ''))
    
    const [matchData, regData] = await Promise.all([p1, p2])
    matches.value = matchData
    tournamentRegistrations.value = regData || []
  } catch (err) {
    ElMessage.error(t('admin.loadMatchesError') || 'Error loading brackets: ' + err.message)
    matches.value = []
    tournamentRegistrations.value = []
  } finally {
    isLoading.value = false
  }
}

// Mở modal ghép cặp thủ công
const openAssignDialog = (m) => {
  currentAssignMatch.value = m
  // Tìm side_a và side_b registration id (hiện tại Matches list API đang trả về gì? Nó chưa trả về registration_id)
  // API Matches trả về player_a_id, player_b_id nhưng Lịch thi đấu cần registration_id 
  // Vì danh sách này lấy từ get_tournament_matches_detail, API matches có side_a_registration_id
  assignForm.value.side_a_registration_id = m.side_a_registration_id || null
  assignForm.value.side_b_registration_id = m.side_b_registration_id || null
  assignDialogVisible.value = true
}

const getAvailableRegistrations = (excludeMatchId, currentSelectedId, otherSideSelectedId) => {
  return tournamentRegistrations.value.filter(r => {
    if (r.id === currentSelectedId) return true
    if (r.id === otherSideSelectedId) return false
    return true
  })
}

const confirmAssignPlayers = async () => {
  if (!currentAssignMatch.value) return
  
  // Validation phía Client: Không cho phép chọn cùng 1 VĐV cho cả 2 bên
  if (assignForm.value.side_a_registration_id && assignForm.value.side_a_registration_id === assignForm.value.side_b_registration_id) {
    ElMessage.error("Không thể xếp 2 bên thi đấu là cùng một người/cặp đấu!")
    return
  }

  assigning.value = true
  try {
    await apiClient.put(`/api/tournaments/matches/${currentAssignMatch.value.id}/assign-players`, assignForm.value)
    ElMessage.success("Ghép cặp thi đấu thành công!")
    assignDialogVisible.value = false
    await fetchMatchesAndRegistrations()
  } catch (err) {
    ElMessage.error("Lỗi ghép cặp: " + (err.response?.data?.detail || err.message))
  } finally {
    assigning.value = false
  }
}

const openManualMatchDialog = (preset = {}) => {
  const stageType = preset.stage_type || 'knockout'
  const roundCode = preset.round_code || (stageType === 'group_stage' ? groupRounds.value[0]?.roundCode : knockoutRounds.value[0]?.roundCode) || 'Vòng mới'
  const nextLocalNo = (matches.value
    .filter(match => match.stage_type === stageType && match.round_code === roundCode)
    .reduce((max, match) => Math.max(max, Number(match.match_no || 0)), 0) || 0) + 1
  manualMatchForm.value = {
    category_id: selectedCategoryId.value,
    stage_type: stageType,
    round_code: roundCode,
    match_no: nextLocalNo,
    side_a_registration_id: null,
    side_b_registration_id: null,
    status: 'pending',
    court_id: null,
    start_time: '',
    referee_name: '',
    referee_phone: '',
    live_stream_url: '',
    next_match_id: null,
    source_match_ids: []
  }
  manualDialogVisible.value = true
}

const openRoundNameDialog = (roundCode) => {
  currentRoundName.value = roundCode
  roundNameForm.value = {
    old_round_code: roundCode,
    new_round_code: roundCode
  }
  roundNameDialogVisible.value = true
}

const confirmRoundName = async () => {
  const oldName = String(roundNameForm.value.old_round_code || '').trim()
  const newName = String(roundNameForm.value.new_round_code || '').trim()
  if (!oldName || !newName || oldName === newName) {
    roundNameDialogVisible.value = false
    return
  }

  const affectedMatches = matches.value.filter(m => m.round_code === oldName)
  if (!affectedMatches.length) {
    roundNameDialogVisible.value = false
    return
  }

  savingRoundName.value = true
  try {
    await Promise.all(affectedMatches.map(match => apiClient.put(`/api/tournaments/matches/${match.id}/admin-update`, {
      round_code: newName
    })))
    ElMessage.success('Đã cập nhật tên vòng đấu.')
    roundNameDialogVisible.value = false
    await fetchMatchesAndRegistrations()
  } catch (err) {
    ElMessage.error('Lỗi cập nhật tên vòng: ' + (err.response?.data?.detail || err.message))
  } finally {
    savingRoundName.value = false
  }
}

const confirmManualMatch = async () => {
  if (!selectedTournamentId.value) return
  if (manualMatchForm.value.side_a_registration_id && manualMatchForm.value.side_a_registration_id === manualMatchForm.value.side_b_registration_id) {
    ElMessage.error('Không thể chọn cùng một VĐV/cặp đấu cho hai bên.')
    return
  }
  const payload = {
    ...manualMatchForm.value,
    match_no: manualMatchForm.value.match_no || null,
    side_a_registration_id: manualMatchForm.value.side_a_registration_id || null,
    side_b_registration_id: manualMatchForm.value.side_b_registration_id || null,
    court_id: manualMatchForm.value.court_id || null,
    start_time: manualMatchForm.value.start_time || null,
    referee_name: manualMatchForm.value.referee_name?.trim() || null,
    referee_phone: manualMatchForm.value.referee_phone?.trim() || null,
    live_stream_url: manualMatchForm.value.live_stream_url?.trim() || null,
  }
  savingManualMatch.value = true
  try {
    await apiClient.post(`/api/tournaments/${selectedTournamentId.value}/matches/manual`, payload)
    ElMessage.success('Đã thêm trận thủ công vào nhánh.')
    manualDialogVisible.value = false
    await fetchMatchesAndRegistrations()
  } catch (err) {
    const detail = Array.isArray(err.response?.data?.detail)
      ? err.response.data.detail.map(item => item.msg || item.message || JSON.stringify(item)).join(', ')
      : (err.response?.data?.detail || err.message)
    ElMessage.error('Lỗi thêm trận: ' + detail)
  } finally {
    savingManualMatch.value = false
  }
}

const deleteMatchNode = async (match) => {
  if (!match?.id) return
  try {
    await ElMessageBox.confirm(
      `Xóa khung trận #${match.match_no} khỏi vòng ${match.round_code}?`,
      'Xóa khung trận',
      {
        confirmButtonText: 'Xóa',
        cancelButtonText: 'Hủy',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    await apiClient.delete(`/api/tournaments/matches/${match.id}`)
    ElMessage.success('Đã xóa khung trận.')
    matchDetailDialogVisible.value = false
    await fetchMatchesAndRegistrations()
  } catch (err) {
    if (err === 'cancel' || err === 'close') return
    ElMessage.error('Lỗi xóa trận: ' + (err.response?.data?.detail || err.message))
  }
}

const openControlDialog = (m) => {
  currentControlMatch.value = m
  controlForm.value = {
    round_code: m.round_code || '',
    match_no: m.match_no || null,
    stage_type: m.stage_type || (/^G\d+/i.test(String(m.round_code || '')) ? 'group_stage' : 'knockout'),
    side_a_registration_id: m.side_a_registration_id || null,
    side_b_registration_id: m.side_b_registration_id || null,
    status: m.status || 'pending',
    score: m.score_summary || '',
    winner_side: m.winner_side || '',
    court_id: m.court_id || null,
    start_time: m.start_time || '',
    referee_name: m.referee_name || '',
    referee_phone: m.referee_phone || '',
    live_stream_url: m.live_stream_url || '',
    video_url: m.video_url || '',
    image_url: m.image_url || '',
    next_match_id: m.next_match_id || null,
    advance_note: m.advance_note || '',
    show_on_homepage: !!m.show_on_homepage,
    sets: parseScoreToSets(m.score_summary || '')
  }
  controlDialogVisible.value = true
}

const openMatchDetailDialog = (match) => {
  currentViewedMatch.value = match
  matchDetailDialogVisible.value = true
}

const addControlSet = () => {
  controlForm.value.sets.push({ side_a: 0, side_b: 0 })
}

const removeControlSet = (index) => {
  if (controlForm.value.sets.length > 1) {
    controlForm.value.sets.splice(index, 1)
  }
}

const getVideoDuration = (file) => new Promise((resolve, reject) => {
  const video = document.createElement('video')
  const objectUrl = URL.createObjectURL(file)

  video.preload = 'metadata'
  video.onloadedmetadata = () => {
    URL.revokeObjectURL(objectUrl)
    resolve(video.duration || 0)
  }
  video.onerror = () => {
    URL.revokeObjectURL(objectUrl)
    reject(new Error('Không đọc được thời lượng video'))
  }
  video.src = objectUrl
})

const beforeControlVideoUpload = async (file) => {
  const allowedTypes = ['video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('Chỉ hỗ trợ video MP4, WebM, MOV hoặc AVI.')
    return false
  }

  if (file.size / 1024 / 1024 > MAX_VIDEO_SIZE_MB) {
    ElMessage.error(`Video vượt quá ${MAX_VIDEO_SIZE_MB}MB. Vui lòng nén hoặc cắt ngắn video.`)
    return false
  }

  try {
    const duration = await getVideoDuration(file)
    if (duration > MAX_VIDEO_DURATION_SECONDS) {
      ElMessage.error(`Video phải ngắn hơn hoặc bằng ${MAX_VIDEO_DURATION_SECONDS} giây.`)
      return false
    }
  } catch (err) {
    ElMessage.error(err.message || 'Không kiểm tra được thời lượng video.')
    return false
  }

  isUploadingVideo.value = true
  return true
}

const beforeControlImageUpload = (file) => {
  if (file.size / 1024 / 1024 > MAX_IMAGE_SIZE_MB) {
    ElMessage.error(`Ảnh vượt quá ${MAX_IMAGE_SIZE_MB}MB.`)
    return false
  }
  isUploadingImage.value = true
  return true
}

const handleControlVideoSuccess = (res) => {
  isUploadingVideo.value = false
  controlForm.value.video_url = res.url
  ElMessage.success('Tải video lên thành công.')
}

const handleControlImageSuccess = (res) => {
  isUploadingImage.value = false
  controlForm.value.image_url = res.url
  ElMessage.success('Tải ảnh lên thành công.')
}

const handleControlVideoError = () => {
  isUploadingVideo.value = false
  ElMessage.error('Tải video thất bại. Vui lòng thử lại.')
}

const handleControlImageError = () => {
  isUploadingImage.value = false
  ElMessage.error('Tải ảnh thất bại. Vui lòng thử lại.')
}

const confirmControlMatch = async () => {
  if (!currentControlMatch.value) return
  if (controlForm.value.side_a_registration_id && controlForm.value.side_a_registration_id === controlForm.value.side_b_registration_id) {
    ElMessage.error('Không thể chọn cùng một VĐV/cặp đấu cho hai bên.')
    return
  }
  const formattedScore = formatSetsToScore(controlForm.value.sets)
  if (controlForm.value.status === 'completed' && (!formattedScore || !controlForm.value.winner_side)) {
    ElMessage.warning('Trận đã kết thúc cần có tỉ số và bên thắng.')
    return
  }
  const payload = {
    ...controlForm.value,
    status: formattedScore && controlForm.value.winner_side ? 'completed' : controlForm.value.status,
    score: formattedScore,
    court_id: controlForm.value.court_id || null,
    start_time: controlForm.value.start_time || null,
    referee_name: controlForm.value.referee_name?.trim() || null,
    referee_phone: controlForm.value.referee_phone?.trim() || null,
    live_stream_url: controlForm.value.live_stream_url?.trim() || null,
    video_url: controlForm.value.video_url?.trim() || null,
    image_url: controlForm.value.image_url?.trim() || null,
    next_match_id: controlForm.value.next_match_id || null,
    advance_note: controlForm.value.advance_note?.trim() || null,
    show_on_homepage: !!controlForm.value.show_on_homepage,
  }
  savingControl.value = true
  try {
    await apiClient.put(`/api/tournaments/matches/${currentControlMatch.value.id}/admin-update`, payload)
    ElMessage.success('Đã cập nhật điều hành trận đấu.')
    controlDialogVisible.value = false
    matchDetailDialogVisible.value = false
    await fetchMatchesAndRegistrations()
  } catch (err) {
    ElMessage.error('Lỗi cập nhật trận: ' + (err.response?.data?.detail || err.message))
  } finally {
    savingControl.value = false
  }
}


// Xử lý khi chọn giải đấu khác từ dropdown
const handleTournamentChange = (id) => {
  selectedCategoryId.value = null // Reset category when tournament changes
  router.push({ query: { ...route.query, tournamentId: id, categoryId: undefined } })
}

const handleCategoryChange = (catId) => {
  router.push({ query: { ...route.query, categoryId: catId } })
}

// Chỉ theo dõi ID để cập nhật dữ liệu trận đấu
watch(() => [route.query.tournamentId, route.query.categoryId], async ([newId, newCatId]) => {
  if (newId) {
    selectedTournamentId.value = parseInt(newId)
    
    // Auto-select first category if not specified
    if (!newCatId && currentTournament.value?.categories?.length) {
      selectedCategoryId.value = currentTournament.value.categories[0].id
      handleCategoryChange(selectedCategoryId.value)
      return
    }
    
    selectedCategoryId.value = newCatId ? parseInt(newCatId) : null
    await fetchMatchesAndRegistrations()
  } else {
    selectedTournamentId.value = null
    selectedCategoryId.value = null
    matches.value = []
    tournamentRegistrations.value = []
  }
}, { immediate: true })

onMounted(async () => {
  isLoading.value = true
  try {
    await Promise.all([fetchTournaments(), fetchCourts()])
    // Không tự động fill ID từ query để tránh gây bối rối cho người dùng, 
    // buộc người dùng phải chọn giải đấu từ dropdown.
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="saas-container">
    <section class="saas-action-bar">
      <div class="bar-left">
        <div class="page-title-wrap">
          <div class="title-icon"><el-icon><Trophy /></el-icon></div>
          <div>
            <h2 class="page-title">{{ $t('admin.drawingMatrix') }}</h2>
            <p class="page-subtitle">{{ $t('admin.drawingMatrixDesc') || 'Quản lý bốc thăm và sơ đồ nhánh đấu' }}</p>
          </div>
        </div>
      </div>

      <div class="bar-right">
        <div class="control-cluster">
          <el-select v-model="selectedTournamentId" :placeholder="$t('admin.selectTournamentPlaceholder')" class="tournament-selector" @change="handleTournamentChange" filterable>
            <el-option v-for="t in tournaments" :key="t.id" :label="t.name" :value="t.id">
              <div class="t-opt">
                <span class="t-name">{{ t.name }}</span>
                <el-tag size="small" :type="t.status === 'open' ? 'success' : 'info'" effect="plain">{{ t.status.toUpperCase() }}</el-tag>
              </div>
            </el-option>
          </el-select>

          <!-- Category selector removed and moved to tabs below -->

          <el-button v-if="hasGroupStage" type="danger" :disabled="!selectedTournamentId || !selectedCategoryId" :loading="generatingPlayoff" @click="openPlayoffDialog" class="saas-btn-action is-danger">
            <el-icon class="mr-1"><Finished /></el-icon> {{ $t('admin.finalizeGroups') }}
          </el-button>

          <el-button type="primary" :disabled="!canDraw || !selectedCategoryId" :loading="generating" @click="openDrawDialog" class="saas-btn-action is-primary">
            <el-icon class="mr-1"><EditPen /></el-icon> {{ $t('admin.startNewDraw') }}
          </el-button>
        </div>
      </div>
    </section>

    <!-- Tab chọn thể thức thi đấu -->
    <section class="category-tabs-section" v-if="selectedTournamentId && currentTournament?.categories?.length">
      <el-tabs v-model="selectedCategoryId" @tab-change="handleCategoryChange" class="draws-tabs-premium">
        <el-tab-pane 
          v-for="cat in currentTournament.categories" 
          :key="cat.id" 
          :label="cat.name.toUpperCase()" 
          :name="cat.id"
        />
      </el-tabs>
    </section>

    <section class="saas-draw-viewport" v-loading="isLoading">
      <div v-if="!selectedTournamentId" class="saas-empty-state-hero">
        <div class="hero-content">
          <div class="hero-visual">
            <div class="visual-blob"></div>
            <el-icon class="visual-icon"><Trophy /></el-icon>
          </div>
          <h2 class="hero-title">{{ t('admin.selectTournamentToStart') || 'CHỌN GIẢI ĐẤU ĐỂ BẮT ĐẦU' }}</h2>
          <p class="hero-desc">Hệ thống đang sẵn sàng. Vui lòng chọn một giải đấu từ menu phía trên để thực hiện bóc thăm, quản lý sơ đồ nhánh đấu và lịch thi đấu.</p>
          <div class="hero-hint">
            <el-icon><Search /></el-icon>
            <span>Sử dụng bộ chọn giải đấu ở thanh công cụ</span>
          </div>
        </div>
      </div>
      <div v-else-if="matches.length === 0" class="saas-empty-state">
        <el-empty :description="$t('admin.noMatchesState')">
          <el-button type="primary" plain round @click="openDrawDialog" :disabled="!canDraw">
            {{ $t('admin.startNewDraw') }}
          </el-button>
        </el-empty>
      </div>
      
      <div v-else class="saas-stages-grid">
        
        <!-- Vòng Bảng -->
        <div v-if="groupRounds.length > 0" class="saas-stage-block group-stage">
          <div class="stage-header-modern">
            <div class="header-icon"><el-icon><Menu /></el-icon></div>
            <div class="header-text">
              <h3>{{ $t('admin.stage1Title') }}</h3>
              <span>{{ $t('admin.stage1Desc') }}</span>
            </div>
          </div>

          <div class="round-robin-groups">
            <section v-for="group in roundRobinGroups" :key="group.groupId" class="round-robin-group-card">
              <div class="round-robin-group-header">
                <div>
                  <h4>{{ group.title }}</h4>
                  <span>{{ group.matchCount }} trận, {{ group.rounds.length }} vòng thi đấu</span>
                </div>
                <div class="round-robin-group-actions">
                  <el-button size="small" plain type="success" @click="openManualMatchDialog({ stage_type: 'group_stage', round_code: group.rounds[0]?.roundCode || `G${group.groupId}-R1` })">
                    <el-icon><Plus /></el-icon>
                    Thêm trận
                  </el-button>
                </div>
              </div>

              <div class="round-robin-rounds-scroll">
                <div class="round-robin-rounds">
                  <div v-for="round in group.rounds" :key="`${group.groupId}-${round.roundCode}`" class="round-robin-round-column">
                    <div class="round-robin-round-header">
                      <span class="lane-tag">{{ round.roundCode }}</span>
                      <div class="round-header-actions">
                        <el-button size="small" circle plain @click="openRoundNameDialog(round.roundCode)">
                          <el-icon><Edit /></el-icon>
                        </el-button>
                        <el-button size="small" circle plain type="success" @click="openManualMatchDialog({ stage_type: 'group_stage', round_code: round.roundCode })">
                          <el-icon><Plus /></el-icon>
                        </el-button>
                      </div>
                    </div>

                    <div
                      v-for="match in round.items"
                      :key="match.id"
                      class="saas-match-card round-robin-match-card clickable"
                      @click="openMatchDetailDialog(match)"
                    >
                  <div class="m-card-header compact">
                    <div class="m-header-left">
                      <span class="m-id">#{{ match.match_no }}</span>
                      <span class="m-court-tag" v-if="match.court" :title="match.court">
                        <el-icon><Location /></el-icon> {{ match.court }}
                      </span>
                    </div>
                    <div class="m-header-right" style="display: flex; gap: 8px; align-items: center">
                      <el-button type="primary" size="small" circle plain @click.stop="openAssignDialog(match)" v-if="match.status === 'pending' || match.status === 'scheduled'" style="padding: 4px; min-height: unset">
                        <el-icon><Edit /></el-icon>
                      </el-button>
                      <el-button type="success" size="small" circle plain @click.stop="openControlDialog(match)" style="padding: 4px; min-height: unset">
                        <el-icon><Calendar /></el-icon>
                      </el-button>
                      <el-button type="danger" size="small" circle plain @click.stop="deleteMatchNode(match)" style="padding: 4px; min-height: unset">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                      <span class="m-status-dot" :class="match.status"></span>
                    </div>
                  </div>
                  <div class="m-card-body">
                    <div class="team-row compact" :class="{ 'is-winner': match.winner_side === 'side_a' }">
                      <div class="team-meta-container compact">
                        <div class="player-unit compact">
                          <el-avatar :size="18" :src="match.p1_avatar" class="player-avatar-mini">
                            <el-icon><User /></el-icon>
                          </el-avatar>
                          <span class="team-name">{{ match.p1_name || '---' }}</span>
                        </div>
                        <div v-if="match.p1_partner_name" class="player-unit compact">
                          <el-avatar :size="18" :src="match.p1_partner_avatar" class="player-avatar-mini">
                            <el-icon><User /></el-icon>
                          </el-avatar>
                          <span class="team-name">{{ match.p1_partner_name }}</span>
                        </div>
                      </div>
                      <span class="team-score" v-if="match.score_a !== null">{{ match.score_a }}</span>
                    </div>
                    <div class="team-row compact" :class="{ 'is-winner': match.winner_side === 'side_b' }">
                      <div class="team-meta-container compact">
                        <div class="player-unit compact">
                          <el-avatar :size="18" :src="match.p2_avatar" class="player-avatar-mini">
                            <el-icon><User /></el-icon>
                          </el-avatar>
                          <span class="team-name">{{ match.p2_name || '---' }}</span>
                        </div>
                        <div v-if="match.p2_partner_name" class="player-unit compact">
                          <el-avatar :size="18" :src="match.p2_partner_avatar" class="player-avatar-mini">
                            <el-icon><User /></el-icon>
                          </el-avatar>
                          <span class="team-name">{{ match.p2_partner_name }}</span>
                        </div>
                      </div>
                      <span class="team-score" v-if="match.score_b !== null">{{ match.score_b }}</span>
                    </div>
                  </div>
                  <div class="m-card-footer match-ops-footer" v-if="match.score_summary || match.advance_note || match.referee_name || match.live_stream_url">
                    <span class="score-value">{{ match.score_summary || match.advance_note || match.referee_name || 'Thông tin trận' }}</span>
                    <a v-if="match.live_stream_url" :href="match.live_stream_url" target="_blank" rel="noopener" class="stream-link">
                      <el-icon><VideoPlay /></el-icon> Stream
                    </a>
                  </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>

        <!-- Vòng Loại Trực Tiếp -->
        <div v-if="(knockoutRounds || []).length > 0" class="saas-stage-block knockout-stage">
          <div class="stage-header-modern">
            <div class="header-icon knockout"><el-icon><Finished /></el-icon></div>
            <div class="header-text">
              <h3>{{ $t('admin.stage2Title') }}</h3>
              <span>{{ $t('admin.stage2Desc') }}</span>
            </div>
          </div>
          
          <div class="bracket-viewport-wrapper">
            <div
              class="bracket-tree-board"
              :style="{ width: `${bracketLayout.width}px`, height: `${bracketLayout.height}px` }"
            >
              <svg class="bracket-lines" :width="bracketLayout.width" :height="bracketLayout.height">
                <polyline
                  v-for="line in bracketLayout.connectors"
                  :key="line.id"
                  :points="line.points"
                  fill="none"
                  stroke="#94a3b8"
                  stroke-width="3"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>

              <div
                v-for="round in bracketLayout.roundHeaders"
                :key="round.roundCode"
                class="bracket-round-header"
                :style="{ left: `${round.x}px`, top: `${round.y}px`, width: `${bracketLayout.cardWidth}px` }"
              >
                <span class="lane-tag knockout">{{ round.roundCode }}</span>
                <div class="round-header-actions">
                  <el-button size="small" circle plain @click="openRoundNameDialog(round.roundCode)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button size="small" circle plain type="success" @click="openManualMatchDialog({ stage_type: 'knockout', round_code: round.roundCode })">
                    <el-icon><Plus /></el-icon>
                  </el-button>
                </div>
              </div>

              <div
                v-for="node in bracketLayout.nodes"
                :key="node.id"
                class="bracket-match-node"
                :style="{ left: `${node.x}px`, top: `${node.y}px`, width: `${bracketLayout.cardWidth}px` }"
              >
                <div class="saas-match-card bracket-card clickable" @click="openMatchDetailDialog(node.match)">
                  <div class="m-card-header compact">
                    <div class="m-header-left">
                      <span class="m-id">#{{ node.match.match_no }}</span>
                      <span class="m-court-tag" v-if="node.match.court" :title="node.match.court">
                        <el-icon><Location /></el-icon> {{ node.match.court }}
                      </span>
                    </div>
                    <div class="m-header-right" style="display: flex; gap: 8px; align-items: center">
                      <el-button type="primary" size="small" circle plain @click.stop="openAssignDialog(node.match)" v-if="node.match.status === 'pending' || node.match.status === 'scheduled'" style="padding: 4px; min-height: unset">
                        <el-icon><Edit /></el-icon>
                      </el-button>
                      <el-button type="success" size="small" circle plain @click.stop="openControlDialog(node.match)" style="padding: 4px; min-height: unset">
                        <el-icon><Calendar /></el-icon>
                      </el-button>
                      <el-button type="danger" size="small" circle plain @click.stop="deleteMatchNode(node.match)" style="padding: 4px; min-height: unset">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                      <span class="m-status-dot" :class="node.match.status"></span>
                    </div>
                  </div>
                  <div class="m-card-body">
                    <div class="team-row compact" :class="{ 'is-winner': node.match.winner_side === 'side_a' }">
                      <div class="team-meta-container compact">
                        <div class="player-unit compact">
                          <el-avatar :size="18" :src="node.match.p1_avatar" class="player-avatar-mini">
                            <el-icon><User /></el-icon>
                          </el-avatar>
                          <span class="team-name">{{ node.match.p1_name || '---' }}</span>
                        </div>
                        <div v-if="node.match.p1_partner_name" class="player-unit compact">
                          <el-avatar :size="18" :src="node.match.p1_partner_avatar" class="player-avatar-mini">
                            <el-icon><User /></el-icon>
                          </el-avatar>
                          <span class="team-name">{{ node.match.p1_partner_name }}</span>
                        </div>
                      </div>
                      <span class="team-score" v-if="node.match.score_a !== null">{{ node.match.score_a }}</span>
                    </div>
                    <div class="team-row compact" :class="{ 'is-winner': node.match.winner_side === 'side_b' }">
                      <div class="team-meta-container compact">
                        <div class="player-unit compact">
                          <el-avatar :size="18" :src="node.match.p2_avatar" class="player-avatar-mini">
                            <el-icon><User /></el-icon>
                          </el-avatar>
                          <span class="team-name">{{ node.match.p2_name || '---' }}</span>
                        </div>
                        <div v-if="node.match.p2_partner_name" class="player-unit compact">
                          <el-avatar :size="18" :src="node.match.p2_partner_avatar" class="player-avatar-mini">
                            <el-icon><User /></el-icon>
                          </el-avatar>
                          <span class="team-name">{{ node.match.p2_partner_name }}</span>
                        </div>
                      </div>
                      <span class="team-score" v-if="node.match.score_b !== null">{{ node.match.score_b }}</span>
                    </div>
                  </div>
                  <div class="m-card-footer match-ops-footer" v-if="node.match.score_summary || node.match.advance_note || node.match.referee_name || node.match.live_stream_url">
                    <span class="score-value">{{ node.match.score_summary || node.match.advance_note || node.match.referee_name || 'Thông tin trận' }}</span>
                    <a v-if="node.match.live_stream_url" :href="node.match.live_stream_url" target="_blank" rel="noopener" class="stream-link">
                      <el-icon><VideoPlay /></el-icon> Stream
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>

      </div>
    </section>
  <el-dialog v-model="assignDialogVisible" title="Ghép cặp thi đấu" width="450px" destroy-on-close>
    <el-form label-position="top">
      <el-form-item label="Bên A (Side A)">
        <el-select v-model="assignForm.side_a_registration_id" placeholder="Chọn VĐV A" clearable filterable style="width: 100%">
          <el-option v-for="r in getAvailableRegistrations(currentAssignMatch?.id, assignForm.side_a_registration_id, assignForm.side_b_registration_id)" :key="r.id" :label="r.player_name + (r.partner_name ? ' & ' + r.partner_name : '')" :value="r.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="Bên B (Side B)">
        <el-select v-model="assignForm.side_b_registration_id" placeholder="Chọn VĐV B" clearable filterable style="width: 100%">
          <el-option v-for="r in getAvailableRegistrations(currentAssignMatch?.id, assignForm.side_b_registration_id, assignForm.side_a_registration_id)" :key="r.id" :label="r.player_name + (r.partner_name ? ' & ' + r.partner_name : '')" :value="r.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="assignDialogVisible = false">{{ $t('admin.cancel') }}</el-button>
      <el-button type="primary" :loading="assigning" @click="confirmAssignPlayers">Lưu ghép cặp</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="manualDialogVisible" title="Thêm trận thủ công" width="920px" destroy-on-close class="draw-control-dialog manual-premium-dialog">
    <el-form :model="manualMatchForm" label-position="top" class="manual-match-form premium-manual-form">
      <div class="control-dialog-grid">
        <section class="control-panel form-card-accent">
          <div class="control-panel-title">
            <span>Thông tin nhánh</span>
            <small>Xác định vị trí trận trong sơ đồ</small>
          </div>
          <div class="form-grid-2 compact-fields">
            <el-form-item label="Tên vòng đấu">
              <el-input v-model="manualMatchForm.round_code" placeholder="VD: Vòng bảng A, Tứ kết, Chung kết" />
            </el-form-item>
            <el-form-item label="Số thứ tự trận">
              <el-input-number v-model="manualMatchForm.match_no" :min="1" style="width: 100%" />
            </el-form-item>
            <el-form-item label="Giai đoạn">
              <el-select v-model="manualMatchForm.stage_type" style="width: 100%">
                <el-option label="Vòng bảng" value="group_stage" />
                <el-option label="Nhánh loại trực tiếp" value="knockout" />
                <el-option label="Playoff" value="playoff" />
              </el-select>
            </el-form-item>
            <el-form-item label="Trạng thái">
              <el-select v-model="manualMatchForm.status" style="width: 100%">
                <el-option label="Chờ thi đấu" value="pending" />
                <el-option label="Đã xếp lịch" value="scheduled" />
                <el-option label="Đang thi đấu" value="ongoing" />
              </el-select>
            </el-form-item>
          </div>
        </section>

        <section class="control-panel form-card-accent">
          <div class="control-panel-title">
            <span>Vận động viên</span>
            <small>Có thể để trống và nhập sau</small>
          </div>
          <div class="form-grid-2 compact-fields">
            <el-form-item label="Bên A">
              <el-select v-model="manualMatchForm.side_a_registration_id" placeholder="Chọn VĐV/cặp đấu" clearable filterable style="width: 100%">
                <el-option v-for="r in tournamentRegistrations" :key="r.id" :label="r.player_name + (r.partner_name ? ' & ' + r.partner_name : '')" :value="r.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="Bên B">
              <el-select v-model="manualMatchForm.side_b_registration_id" placeholder="Chọn VĐV/cặp đấu" clearable filterable style="width: 100%">
                <el-option v-for="r in tournamentRegistrations" :key="r.id" :label="r.player_name + (r.partner_name ? ' & ' + r.partner_name : '')" :value="r.id" />
              </el-select>
            </el-form-item>
          </div>
        </section>
      </div>

      <section class="control-panel form-card-accent full-span-panel">
        <div class="control-panel-title">
          <span>Điều phối trận</span>
          <small>Sân, lịch thi đấu, trọng tài và livestream</small>
        </div>
        <div class="form-grid-2 compact-fields">
          <el-form-item label="Sân">
            <el-select v-model="manualMatchForm.court_id" placeholder="Chọn sân" clearable filterable style="width: 100%">
              <el-option v-for="court in courts" :key="court.id" :label="court.court_name" :value="court.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="Thời gian">
            <el-date-picker v-model="manualMatchForm.start_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
          </el-form-item>
          <el-form-item label="Trọng tài">
            <el-input v-model="manualMatchForm.referee_name" placeholder="Tên trọng tài" />
          </el-form-item>
          <el-form-item label="Số điện thoại trọng tài">
            <el-input v-model="manualMatchForm.referee_phone" placeholder="Số điện thoại" />
          </el-form-item>
          <el-form-item label="Link stream YouTube" class="wide-form-item">
            <el-input v-model="manualMatchForm.live_stream_url" placeholder="https://youtube.com/..." />
          </el-form-item>
        </div>
      </section>
      <div class="auto-link-hint">
        Hệ thống sẽ tự nối trận mới vào nhánh phù hợp theo vòng đấu và số thứ tự trận. Nếu vị trí chưa đúng, có thể chỉnh hoặc xóa trực tiếp trên khung trận.
      </div>
    </el-form>
    <template #footer>
      <el-button @click="manualDialogVisible = false">{{ $t('admin.cancel') }}</el-button>
      <el-button type="primary" :loading="savingManualMatch" @click="confirmManualMatch">Thêm trận</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="roundNameDialogVisible" title="Chỉnh tên vòng đấu" width="420px" destroy-on-close>
    <el-form :model="roundNameForm" label-position="top">
      <el-form-item label="Tên hiện tại">
        <el-input v-model="roundNameForm.old_round_code" disabled />
      </el-form-item>
      <el-form-item label="Tên mới">
        <el-input v-model="roundNameForm.new_round_code" placeholder="VD: Tứ kết, Bán kết, Chung kết" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="roundNameDialogVisible = false">{{ $t('admin.cancel') }}</el-button>
      <el-button type="primary" :loading="savingRoundName" @click="confirmRoundName">Lưu tên vòng</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="controlDialogVisible" title="Điều hành trận đấu" width="920px" destroy-on-close class="draw-control-dialog">
    <el-form :model="controlForm" label-position="top" class="manual-match-form control-premium-form">
      <div class="control-dialog-grid">
        <section class="control-panel">
          <div class="control-panel-title">
            <span>Thiết lập trận</span>
            <small>Vòng đấu, lịch thi đấu và luồng nhánh</small>
          </div>
          <div class="form-grid-2 compact-fields">
            <el-form-item label="Tên vòng">
              <el-input v-model="controlForm.round_code" />
            </el-form-item>
            <el-form-item label="Số trận">
              <el-input-number v-model="controlForm.match_no" :min="1" style="width: 100%" />
            </el-form-item>
            <el-form-item label="Trạng thái">
              <el-select v-model="controlForm.status" style="width: 100%">
                <el-option label="Chờ thi đấu" value="pending" />
                <el-option label="Đã xếp lịch" value="scheduled" />
                <el-option label="Đang thi đấu" value="ongoing" />
                <el-option label="Đã kết thúc" value="completed" />
              </el-select>
            </el-form-item>
            <el-form-item label="Winner đi tiếp đến">
              <el-select v-model="controlForm.next_match_id" clearable filterable placeholder="Chọn trận vòng sau" style="width: 100%">
                <el-option v-for="item in controlNextMatchOptions" :key="item.id" :label="item.label" :value="item.id" />
              </el-select>
            </el-form-item>
          </div>
          <el-form-item v-if="controlForm.status === 'completed'" label="Thông báo sau trận">
            <el-input
              v-model="controlForm.advance_note"
              maxlength="50"
              show-word-limit
              placeholder="VD: Tiến đến vòng 2, vào bán kết..."
            />
          </el-form-item>
          <el-form-item label="Hiển thị lên trang chủ" style="margin-top: 10px;">
            <el-switch v-model="controlForm.show_on_homepage" />
          </el-form-item>
        </section>

        <section class="control-panel">
          <div class="control-panel-title">
            <span>Kết quả</span>
            <small>Người thắng và tỉ số từng set</small>
          </div>
          <div class="winner-selection-premium">
            <p class="section-label">Ai là người chiến thắng?</p>
            <el-radio-group v-model="controlForm.winner_side" class="winner-grid-selector">
              <el-radio :value="'side_a'" border class="winner-radio-premium">
                <div class="radio-content">
                  <strong>{{ currentControlMatch?.p1_name || 'Bên A' }}</strong>
                  <div v-if="currentControlMatch?.p1_partner_name" class="muted-line">{{ currentControlMatch.p1_partner_name }}</div>
                </div>
              </el-radio>
              <el-radio :value="'side_b'" border class="winner-radio-premium">
                <div class="radio-content">
                  <strong>{{ currentControlMatch?.p2_name || 'Bên B' }}</strong>
                  <div v-if="currentControlMatch?.p2_partner_name" class="muted-line">{{ currentControlMatch.p2_partner_name }}</div>
                </div>
              </el-radio>
            </el-radio-group>
          </div>

          <div class="sets-management">
            <div class="sets-header">
              <span class="section-label">Tỉ số các set</span>
              <el-button type="primary" link @click="addControlSet">
                <el-icon><Plus /></el-icon> Thêm set
              </el-button>
            </div>
            <div class="sets-rows">
              <div v-for="(set, index) in controlForm.sets" :key="index" class="set-row-premium">
                <span class="set-index">Set {{ index + 1 }}</span>
                <div class="set-inputs-wrap">
                  <el-input-number v-model="set.side_a" :min="0" :max="30" controls-position="right" class="saas-number-input" />
                  <span class="vs-dash">-</span>
                  <el-input-number v-model="set.side_b" :min="0" :max="30" controls-position="right" class="saas-number-input" />
                </div>
                <el-button v-if="controlForm.sets.length > 1" type="danger" circle plain link @click="removeControlSet(index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div class="form-grid-2 control-spaced-grid">
        <el-form-item label="Bên A">
          <el-select v-model="controlForm.side_a_registration_id" clearable filterable style="width: 100%">
            <el-option v-for="r in tournamentRegistrations" :key="r.id" :label="r.player_name + (r.partner_name ? ' & ' + r.partner_name : '')" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Bên B">
          <el-select v-model="controlForm.side_b_registration_id" clearable filterable style="width: 100%">
            <el-option v-for="r in tournamentRegistrations" :key="r.id" :label="r.player_name + (r.partner_name ? ' & ' + r.partner_name : '')" :value="r.id" />
          </el-select>
        </el-form-item>
      </div>
      <div class="form-grid-2">
        <el-form-item label="Sân">
          <el-select v-model="controlForm.court_id" clearable filterable style="width: 100%">
            <el-option v-for="court in courts" :key="court.id" :label="court.court_name" :value="court.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Thời gian">
          <el-date-picker v-model="controlForm.start_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
      </div>
      <div class="form-grid-2">
        <el-form-item label="Trọng tài">
          <el-input v-model="controlForm.referee_name" placeholder="Tên trọng tài chính" />
        </el-form-item>
        <el-form-item label="Số điện thoại trọng tài">
          <el-input v-model="controlForm.referee_phone" placeholder="Số điện thoại" />
        </el-form-item>
      </div>
      <div class="form-grid-2">
        <el-form-item label="Link stream YouTube">
          <el-input v-model="controlForm.live_stream_url" placeholder="Dùng khi đang thi đấu" />
        </el-form-item>
        <el-form-item label="Link video kết quả">
          <el-input v-model="controlForm.video_url" placeholder="Highlight hoặc full match" />
        </el-form-item>
      </div>
      <div class="media-management draw-media-management">
        <div class="sets-header">
          <span class="section-label">Media trận đấu</span>
        </div>
        <div class="upload-grid">
          <div class="upload-card">
            <label>Video trận đấu / Highlight</label>
            <el-upload
              class="saas-upload"
              :action="`${MAIN_API_URL}/api/upload/image`"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleControlVideoSuccess"
              :on-error="handleControlVideoError"
              :before-upload="beforeControlVideoUpload"
              accept="video/mp4,video/webm,video/quicktime,video/x-msvideo"
            >
              <el-button v-if="!controlForm.video_url" type="primary" plain :icon="VideoCamera" :loading="isUploadingVideo">
                Tải video lên
              </el-button>
              <div v-else class="upload-result success">
                <el-icon><VideoCamera /></el-icon>
                <span>Đã có video</span>
                <el-button link type="primary" @click.stop="controlForm.video_url = ''">Thay đổi</el-button>
              </div>
            </el-upload>
            <span class="upload-hint">{{ VIDEO_UPLOAD_HINT }}</span>
            <el-input v-model="controlForm.video_url" size="small" placeholder="Hoặc dán URL Youtube/Cloudinary" />
          </div>

          <div class="upload-card">
            <label>Ảnh kết quả / Trao giải</label>
            <el-upload
              class="saas-upload"
              :action="`${MAIN_API_URL}/api/upload/image`"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleControlImageSuccess"
              :on-error="handleControlImageError"
              :before-upload="beforeControlImageUpload"
              accept="image/*"
            >
              <el-button v-if="!controlForm.image_url" type="success" plain :icon="Picture" :loading="isUploadingImage">
                Tải ảnh lên
              </el-button>
              <div v-else class="upload-result success">
                <el-icon><Picture /></el-icon>
                <span>Đã có ảnh</span>
                <el-button link type="primary" @click.stop="controlForm.image_url = ''">Thay đổi</el-button>
              </div>
            </el-upload>
            <el-input v-model="controlForm.image_url" size="small" placeholder="Hoặc dán URL ảnh" />
          </div>
        </div>
      </div>
    </el-form>
    <template #footer>
      <el-button @click="controlDialogVisible = false">{{ $t('admin.cancel') }}</el-button>
      <el-button type="primary" :loading="savingControl" @click="confirmControlMatch">Lưu điều hành</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="matchDetailDialogVisible" title="Thông tin trận đấu" width="640px" destroy-on-close class="draw-control-dialog">
    <div v-if="currentViewedMatch" class="match-detail-sheet">
      <div class="match-detail-top">
        <div>
          <div class="detail-title">{{ currentViewedMatch.round_code }} - Trận #{{ currentViewedMatch.match_no }}</div>
          <div class="detail-subtitle">{{ currentViewedMatch.status?.toUpperCase() }}<span v-if="currentViewedMatch.court"> · {{ currentViewedMatch.court }}</span></div>
        </div>
        <div class="detail-actions">
          <el-button type="primary" @click="openControlDialog(currentViewedMatch)">Chỉnh sửa trận</el-button>
          <el-button type="danger" plain @click="deleteMatchNode(currentViewedMatch)">Xóa khung</el-button>
        </div>
      </div>
      <div class="detail-team-grid">
        <div class="detail-team-card" :class="{ winner: currentViewedMatch.winner_side === 'side_a' }">
          <strong>{{ currentViewedMatch.p1_name || 'Chua xac dinh' }}</strong>
          <span v-if="currentViewedMatch.p1_partner_name">{{ currentViewedMatch.p1_partner_name }}</span>
        </div>
        <div class="detail-team-card" :class="{ winner: currentViewedMatch.winner_side === 'side_b' }">
          <strong>{{ currentViewedMatch.p2_name || 'Chua xac dinh' }}</strong>
          <span v-if="currentViewedMatch.p2_partner_name">{{ currentViewedMatch.p2_partner_name }}</span>
        </div>
      </div>
      <div class="detail-meta-grid">
        <div class="detail-meta-item"><label>Tỉ số</label><span>{{ currentViewedMatch.score_summary || 'Chưa cập nhật' }}</span></div>
        <div class="detail-meta-item"><label>Thông báo</label><span>{{ currentViewedMatch.advance_note || 'Chưa cập nhật' }}</span></div>
        <div class="detail-meta-item"><label>Thời gian</label><span>{{ currentViewedMatch.start_time || 'Chưa xếp lịch' }}</span></div>
        <div class="detail-meta-item"><label>Trọng tài</label><span>{{ currentViewedMatch.referee_name || 'Chưa cập nhật' }}</span></div>
        <div class="detail-meta-item"><label>Điện thoại</label><span>{{ currentViewedMatch.referee_phone || 'Chưa cập nhật' }}</span></div>
      </div>
    </div>
  </el-dialog>

  <el-dialog v-model="isDrawDialogOpen" :title="$t('admin.drawOptionsTitle')" width="450px" destroy-on-close>
    <el-form :model="drawForm" label-position="top">
      <el-form-item :label="$t('admin.category')">
        <el-select v-model="drawForm.category_id" style="width: 100%" placeholder="Chọn nội dung để bốc thăm">
          <el-option 
            v-for="cat in currentTournament?.categories" 
            :key="cat.id" 
            :label="cat.name" 
            :value="cat.id" 
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('admin.formatType')">
        <el-radio-group v-model="drawForm.format_type">
          <el-radio :value="'knockout'">{{ $t('admin.knockout') }}</el-radio>
          <el-radio :value="'round_robin'">{{ $t('admin.roundRobin') }}</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item v-if="['knockout', 'round_robin'].includes(drawForm.format_type)" :label="$t('admin.drawSize', 'Quy mô bốc thăm')">
        <el-input-number v-model="drawForm.draw_size" :min="1" :max="256" style="width: 100%" />
        <div style="font-size: 12px; color: #64748b; margin-top: 5px;">
          Nhập số đội hoặc cặp đấu tham gia. Loại trực tiếp sẽ tự tính nhánh; vòng tròn sẽ tự tạo lịch theo số đội/cặp và số bảng.
        </div>
      </el-form-item>
      <el-form-item v-if="drawForm.format_type === 'knockout'" label="Tên các vòng đấu">
        <div class="round-name-editor">
          <el-input
            v-for="(_, idx) in drawForm.round_names"
            :key="idx"
            v-model="drawForm.round_names[idx]"
            :placeholder="`Tên vòng ${idx + 1}`"
          />
        </div>
      </el-form-item>
      <el-form-item v-if="drawForm.format_type === 'round_robin'" :label="$t('admin.numGroups')">
        <el-input-number v-model="drawForm.num_groups" :min="1" :max="Math.max(1, Number(drawForm.draw_size || 1))" style="width: 100%" />
        <div style="font-size: 12px; color: #64748b; margin-top: 5px;">{{ $t('admin.numGroupsDesc') }}</div>
        <div class="draw-preview-card">
          <div class="draw-preview-title">Số trận dự kiến</div>
          <div class="draw-preview-value">{{ roundRobinPreview.matchCount }}</div>
          <div class="draw-preview-desc">{{ roundRobinPreview.label }}</div>
          <div class="draw-preview-note">
            Vòng tròn nghĩa là các đội/cặp trong cùng bảng sẽ gặp nhau một lần. Ví dụ 16 đội chia 2 bảng sẽ tạo 56 trận; 16 đội trong 1 bảng sẽ tạo 120 trận.
          </div>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="isDrawDialogOpen = false">{{ $t('admin.cancel') }}</el-button>
      <el-button type="primary" @click="confirmGenerateDraw">{{ $t('admin.confirm') }}</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="isPlayoffDialogOpen" :title="$t('admin.finalizePlayoffTitle')" width="450px" destroy-on-close>
    <el-form :model="playoffForm" label-position="top">
      <el-form-item :label="$t('admin.category')">
        <el-select v-model="playoffForm.category_id" style="width: 100%" placeholder="Chọn nội dung chốt bảng">
          <el-option 
            v-for="cat in currentTournament?.categories" 
            :key="cat.id" 
            :label="cat.name" 
            :value="cat.id" 
          />
        </el-select>
      </el-form-item>
      <div style="margin-bottom: 20px; color: #b91c1c; font-size: 0.9rem; background: #fef2f2; padding: 12px; border-radius: 8px;">
        {{ $t('admin.finalizePlayoffNote') }}
      </div>
      <el-form-item :label="$t('admin.advancersPerGroup')">
        <el-input-number v-model="playoffForm.advancers_per_group" :min="1" :max="4" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="isPlayoffDialogOpen = false">{{ $t('admin.cancel') }}</el-button>
      <el-button type="danger" @click="confirmGeneratePlayoff">{{ $t('admin.generatePlayoffBtn') }}</el-button>
    </template>
  </el-dialog>
</div>
</template>

<style scoped>
/* MODER SAAS LAYOUT */
.saas-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 10px;
}

.saas-action-bar {
  background: white;
  padding: 24px 32px;
  border-radius: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.03);
  border: 1px solid #f1f5f9;
}

.page-title-wrap {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-icon {
  width: 48px;
  height: 48px;
  background: #eff6ff;
  color: #2563eb;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.page-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 800;
  color: #1e293b;
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: 4px 0 0;
  font-size: 0.9rem;
  color: #64748b;
}

.control-cluster {
  display: flex;
  gap: 12px;
  align-items: center;
}

.tournament-selector {
  width: 250px;
}

.category-selector {
  width: 200px;
}

.saas-btn-action {
  height: 45px;
  padding: 0 24px;
  font-weight: 800 !important;
  border-radius: 12px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.saas-btn-action.is-primary {
  background: #2563eb !important;
  border: none !important;
}

.saas-btn-action.is-danger {
  background: #dc2626 !important;
  border: none !important;
}

.saas-btn-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 15px rgba(0,0,0,0.1);
}

.saas-empty-state-hero {
  background: white;
  min-height: 500px;
  border-radius: 32px;
  border: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.02);
}

.hero-content { text-align: center; max-width: 500px; padding: 40px; }
.hero-visual { position: relative; width: 140px; height: 140px; margin: 0 auto 32px; display: flex; align-items: center; justify-content: center; }
.visual-blob { position: absolute; inset: 0; background: #eff6ff; border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%; animation: blobMorph 8s infinite alternate; opacity: 0.6; }
.visual-icon { font-size: 80px; color: #3b82f6; position: relative; z-index: 2; }
.hero-title { font-size: 1.8rem; font-weight: 900; color: #0f172a; margin-bottom: 16px; letter-spacing: -0.02em; }
.hero-desc { color: #64748b; font-size: 1.1rem; line-height: 1.6; margin-bottom: 32px; }
.hero-hint { display: inline-flex; align-items: center; gap: 10px; padding: 12px 24px; background: #f8fafc; border-radius: 99px; color: #3b82f6; font-weight: 700; font-size: 0.9rem; border: 1px solid #e2e8f0; }

@keyframes blobMorph {
  0% { border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%; transform: scale(1); }
  100% { border-radius: 70% 30% 30% 70% / 70% 70% 30% 30%; transform: scale(1.1); }
}

/* STAGE BLOCKS */
.saas-stage-block {
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  padding: 32px;
  border-radius: 24px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.06);
  margin-bottom: 32px;
}

.stage-header-modern {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 2px solid #eef2f7;
}

.header-icon {
  width: 40px;
  height: 40px;
  background: #f0fdf4;
  color: #16a34a;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: inset 0 0 0 1px rgba(22, 163, 74, 0.12), 0 8px 18px rgba(22, 163, 74, 0.08);
}

.header-icon.knockout {
  background: #fef2f2;
  color: #dc2626;
  box-shadow: inset 0 0 0 1px rgba(220, 38, 38, 0.12), 0 8px 18px rgba(220, 38, 38, 0.08);
}

.header-text h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 800;
  color: #1e293b;
}

.header-text span {
  font-size: 0.85rem;
  color: #94a3b8;
}

/* MATCH CARDS */
.saas-match-card {
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  border: 1.5px solid #cbd5e1;
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.2s ease;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.07);
}

.saas-match-card:hover {
  border-color: #2563eb;
  box-shadow: 0 16px 34px rgba(37, 99, 235, 0.12);
}

.m-card-header {
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #dbe3ec;
}

.m-id {
  font-size: 0.75rem;
  font-weight: 800;
  color: #334155;
}

.m-card-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.team-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid #eef2f7;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
}

.team-row.is-winner {
  background: linear-gradient(180deg, #ecfdf5 0%, #f7fee7 100%);
  border-color: #86efac;
  box-shadow: inset 3px 0 0 #16a34a, 0 8px 16px rgba(22, 163, 74, 0.08);
}

.team-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1e293b;
}

.is-winner .team-name {
  color: #16a34a;
}

.win-icon {
  color: #16a34a;
  font-size: 18px;
}

.team-score {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.1rem;
  font-weight: 800;
  color: #0f172a;
  min-width: 24px;
  text-align: center;
}

.m-card-footer {
  padding: 10px 16px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.score-label {
  color: #94a3b8;
  font-weight: 600;
}

.score-value {
  color: #1e293b;
  font-weight: 800;
}

.match-ops-footer {
  gap: 10px;
}

.stream-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #b91c1c;
  font-weight: 800;
  text-decoration: none;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 999px;
  padding: 3px 8px;
}

/* HORIZONTAL SCROLL FOR GROUPS */
.group-board-horizontal {
  display: flex;
  gap: 24px;
  overflow-x: auto;
  padding-bottom: 12px;
}

.group-lane {
  min-width: 300px;
  flex: 0 0 300px;
}

.round-robin-groups {
  display: grid;
  gap: 24px;
}

.round-robin-group-card {
  border: 1px solid #dbe3ec;
  border-radius: 24px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.round-robin-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 22px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(90deg, #f8fafc 0%, #ffffff 100%);
}

.round-robin-group-header h4 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 900;
  color: #0f172a;
}

.round-robin-group-header span {
  display: block;
  margin-top: 4px;
  color: #64748b;
  font-size: 0.86rem;
  font-weight: 700;
}

.round-robin-group-actions {
  flex: 0 0 auto;
}

.round-robin-rounds-scroll {
  overflow-x: auto;
  padding: 22px;
  scrollbar-color: #94a3b8 #eef2f7;
  scrollbar-width: thin;
}

.round-robin-rounds-scroll::-webkit-scrollbar {
  height: 10px;
}

.round-robin-rounds-scroll::-webkit-scrollbar-track {
  background: #eef2f7;
  border-radius: 999px;
}

.round-robin-rounds-scroll::-webkit-scrollbar-thumb {
  background: #94a3b8;
  border-radius: 999px;
  border: 2px solid #eef2f7;
}

.round-robin-rounds {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 280px;
  gap: 22px;
  align-items: start;
  min-width: max-content;
}

.round-robin-round-column {
  display: grid;
  gap: 14px;
}

.round-robin-round-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 38px;
}

.round-robin-match-card {
  min-height: 224px;
}

.lane-header {
  margin-bottom: 16px;
  text-align: center;
}
.lane-header.with-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.lane-tag {
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
  color: #334155;
  padding: 6px 20px;
  border-radius: 99px;
  font-weight: 800;
  font-size: 0.75rem;
  text-transform: uppercase;
  border: 1px solid #cbd5e1;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.06);
}

.lane-tag.knockout {
  background: linear-gradient(180deg, #fff7f7 0%, #fef2f2 100%);
  color: #b91c1c;
  border-color: #fca5a5;
}

.lane-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* BRACKET LAYOUT */
.bracket-viewport-wrapper {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 28px 24px 44px;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  background:
    linear-gradient(90deg, rgba(148, 163, 184, 0.12) 1px, transparent 1px),
    linear-gradient(180deg, rgba(148, 163, 184, 0.1) 1px, transparent 1px),
    #ffffff;
  background-size: 96px 96px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
  scrollbar-color: #94a3b8 #eef2f7;
  scrollbar-width: thin;
}

.bracket-viewport-wrapper::-webkit-scrollbar {
  height: 10px;
}

.bracket-viewport-wrapper::-webkit-scrollbar-track {
  background: #eef2f7;
  border-radius: 999px;
}

.bracket-viewport-wrapper::-webkit-scrollbar-thumb {
  background: #94a3b8;
  border-radius: 999px;
  border: 2px solid #eef2f7;
}

.bracket-tree-board {
  position: relative;
  min-width: 100%;
}

.bracket-match-node {
  position: absolute;
  z-index: 2;
}

.bracket-lines {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  filter: drop-shadow(0 1px 0 rgba(15, 23, 42, 0.18));
}

.bracket-round-header {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  z-index: 3;
}

.round-header-actions {
  display: inline-flex;
  gap: 6px;
}

.round-header-actions :deep(.el-button) {
  background: #ffffff;
  border-color: #cbd5e1;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
}

.bracket-card {
  width: 100%;
  margin: 0 !important;
  height: 224px;
  z-index: 2;
  overflow: hidden;
}
.bracket-card.clickable { cursor: pointer; transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease; }
.bracket-card.clickable:hover { transform: translateY(-2px); box-shadow: 0 18px 36px rgba(15, 23, 42, 0.12); }

.m-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1 1 auto;
}
.m-court-tag {
  font-size: 0.65rem; color: #475569; background: #eef2f7;
  padding: 2px 8px; border-radius: 6px; display: inline-flex; align-items: center; gap: 4px;
  font-weight: 800; border: 1px solid #dbe3ec;
  max-width: 96px;
  height: 24px;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
  flex: 0 1 auto;
}

.m-court-tag .el-icon {
  flex: 0 0 auto;
}

.m-card-header.compact {
  gap: 8px;
  min-height: 48px;
}

.m-card-header.compact > div:last-child {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.m-status-dot {
  width: 10px; height: 10px; border-radius: 50%; background: #e2e8f0;
  box-shadow: 0 0 0 4px #f1f5f9;
}
.m-status-dot.completed { background: #16a34a; box-shadow: 0 0 0 4px #dcfce7; }
.m-status-dot.scheduled { background: #2563eb; box-shadow: 0 0 0 4px #dbeafe; }
.m-status-dot.ongoing { background: #ef4444; box-shadow: 0 0 0 4px #fee2e2; }
.m-status-dot.pending { background: #f59e0b; box-shadow: 0 0 0 4px #fef3c7; }

.team-meta-container { display: flex; flex-direction: column; gap: 4px; flex-grow: 1; }
.team-meta-container.compact { gap: 2px; }
.player-unit { display: flex; align-items: center; gap: 8px; min-height: 22px; }
.player-unit.compact { gap: 6px; }
.player-avatar-mini { border: 2px solid white; box-shadow: 0 3px 8px rgba(15, 23, 42, 0.16); flex-shrink: 0; }
.team-name { font-size: 0.9rem; font-weight: 800; color: #0f172a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px; }
.compact .team-name { font-size: 0.82rem; max-width: 120px; }
.is-winner .team-name { color: #16a34a; }
.team-row.compact { min-height: 56px; }
.m-card-body { display: flex; flex-direction: column; gap: 8px; }

.winner-selection-premium { display: grid; gap: 12px; margin-bottom: 12px; }
.control-premium-form { gap: 14px; }
.control-dialog-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}
.control-panel {
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.form-card-accent {
  position: relative;
  overflow: hidden;
}

.form-card-accent::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: linear-gradient(90deg, #2563eb, #14b8a6);
}

.full-span-panel {
  margin-top: 16px;
}
.control-panel-title {
  display: grid;
  gap: 3px;
  margin-bottom: 14px;
}
.control-panel-title span {
  font-size: 1rem;
  font-weight: 900;
  color: #0f172a;
}
.control-panel-title small {
  color: #64748b;
  font-weight: 600;
}
.compact-fields :deep(.el-form-item) { margin-bottom: 4px; }
.control-spaced-grid { margin-top: 2px; }
.auto-link-hint {
  padding: 14px;
  border: 1px dashed #bfdbfe;
  border-radius: 18px;
  background: #eff6ff;
  color: #1e3a8a;
  font-size: 0.86rem;
  font-weight: 600;
  line-height: 1.5;
}
.section-label { font-size: 0.8rem; font-weight: 800; color: #64748b; letter-spacing: 0.03em; text-transform: uppercase; }
.winner-grid-selector { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.winner-radio-premium { margin: 0 !important; height: auto; padding: 12px 14px; border-radius: 18px; }
.radio-content { display: grid; gap: 6px; }
.muted-line { font-size: 0.85rem; color: #64748b; font-weight: 600; }
.sets-management { display: grid; gap: 12px; margin-bottom: 12px; }
.sets-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.sets-rows { display: grid; gap: 10px; }
.set-row-premium { display: grid; grid-template-columns: 70px 1fr 40px; align-items: center; gap: 10px; padding: 12px 14px; border: 1px solid #e2e8f0; border-radius: 18px; background: #f8fafc; }
.set-index { font-weight: 800; color: #475569; }
.set-inputs-wrap { display: flex; align-items: center; gap: 10px; }
.vs-dash { color: #94a3b8; font-weight: 800; }
.saas-number-input { width: 100%; }
.draw-media-management { display: grid; gap: 12px; margin-top: 4px; padding: 16px; border: 1px solid #e2e8f0; border-radius: 18px; background: #f8fafc; }
.upload-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.upload-card { display: grid; gap: 8px; min-width: 0; }
.upload-card label { font-size: 0.85rem; font-weight: 800; color: #334155; }
.saas-upload { display: block; }
.upload-result { display: inline-flex; align-items: center; gap: 8px; font-size: 0.85rem; font-weight: 800; }
.upload-result.success { color: #059669; }
.upload-hint { color: #64748b; font-size: 0.78rem; line-height: 1.4; }

.match-detail-sheet { display: grid; gap: 18px; }
.match-detail-top { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.detail-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.detail-title { font-size: 1.1rem; font-weight: 800; color: #0f172a; }
.detail-subtitle { color: #64748b; font-weight: 600; margin-top: 4px; }
.detail-team-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.detail-team-card { display: grid; gap: 6px; padding: 16px; border: 1px solid #e2e8f0; border-radius: 18px; background: #fff; }
.detail-team-card.winner { border-color: #bbf7d0; background: #f0fdf4; }
.detail-meta-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.detail-meta-item { display: grid; gap: 6px; padding: 14px 16px; border-radius: 16px; background: #f8fafc; border: 1px solid #e2e8f0; }
.detail-meta-item label { font-size: 0.75rem; font-weight: 800; color: #64748b; text-transform: uppercase; }
.detail-meta-item span { color: #0f172a; font-weight: 700; }

.side-score {
  font-family: 'JetBrains Mono', monospace; font-weight: 800;
  color: #0f172a; font-size: 0.9rem; min-width: 20px; text-align: right;
}

@media (max-width: 1024px) {
  .saas-action-bar {
    flex-direction: column;
    gap: 20px;
    align-items: flex-start;
  }
}

.saas-tournament-selector { width: 380px; }

.category-tabs-section {
  background: white; padding: 0 32px; border-radius: 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #f1f5f9;
}

:deep(.draws-tabs-premium .el-tabs__item) {
  font-weight: 800; font-size: 0.85rem; color: #94a3b8; padding: 0 32px;
}
:deep(.draws-tabs-premium .el-tabs__item.is-active) {
  color: #2563eb;
}
:deep(.draws-tabs-premium .el-tabs__active-bar) {
  background-color: #2563eb; height: 4px;
}

.round-name-editor {
  width: 100%;
  display: grid;
  gap: 10px;
}

.draw-preview-card {
  margin-top: 12px;
  padding: 14px 16px;
  border: 1px solid #bfdbfe;
  border-radius: 16px;
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
  display: grid;
  gap: 6px;
}

.draw-preview-title {
  font-size: 0.78rem;
  font-weight: 900;
  color: #1d4ed8;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.draw-preview-value {
  font-size: 2rem;
  line-height: 1;
  font-weight: 900;
  color: #0f172a;
}

.draw-preview-desc {
  color: #334155;
  font-weight: 800;
  line-height: 1.45;
}

.draw-preview-note {
  color: #64748b;
  font-size: 0.82rem;
  line-height: 1.5;
}

.manual-match-form {
  display: grid;
  gap: 14px;
}

.premium-manual-form {
  gap: 16px;
}

.premium-manual-form :deep(.el-form-item__label),
.control-premium-form :deep(.el-form-item__label) {
  margin-bottom: 7px;
  color: #475569;
  font-size: 0.78rem;
  font-weight: 900;
  letter-spacing: 0.02em;
}

.premium-manual-form :deep(.el-input__wrapper),
.premium-manual-form :deep(.el-select__wrapper),
.premium-manual-form :deep(.el-date-editor.el-input__wrapper),
.control-premium-form :deep(.el-input__wrapper),
.control-premium-form :deep(.el-select__wrapper),
.control-premium-form :deep(.el-date-editor.el-input__wrapper) {
  min-height: 42px;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 0 0 1px #dbe3ec inset;
  transition: box-shadow 0.18s ease, background 0.18s ease;
}

.premium-manual-form :deep(.el-input__wrapper:hover),
.premium-manual-form :deep(.el-select__wrapper:hover),
.control-premium-form :deep(.el-input__wrapper:hover),
.control-premium-form :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #93c5fd inset, 0 6px 14px rgba(37, 99, 235, 0.08);
}

.premium-manual-form :deep(.el-input-number),
.control-premium-form :deep(.el-input-number) {
  width: 100%;
}

.wide-form-item {
  grid-column: 1 / -1;
}

.form-grid-2,
.form-grid-3 {
  display: grid;
  gap: 14px;
}

.form-grid-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.form-grid-3 {
  grid-template-columns: 1.2fr 0.8fr 1fr;
}

@media (max-width: 720px) {
  .control-dialog-grid,
  .form-grid-2,
  .form-grid-3 {
    grid-template-columns: 1fr;
  }
}
</style>
