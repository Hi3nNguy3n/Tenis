<script setup>
import { onMounted, computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTournamentStore } from '../../../stores/tournament'
import { useAuthStore } from '../../../stores/auth'
import { apiClient } from '../../../services/apiClient'
import { 
  Trophy, 
  Calendar as CalendarIcon, 
  Location, 
  Check,
  User, 
  ArrowRight, 
  InfoFilled, 
  Ticket,
  VideoCamera,
  Picture,
  VideoPlay,
  View
} from '@element-plus/icons-vue'
import { currentLocale, t } from '../../../utils/locale'

const route = useRoute()
const router = useRouter()
const tournamentStore = useTournamentStore()
const authStore = useAuthStore()

const tournamentId = computed(() => route.params.id)
const tournament = computed(() => tournamentStore.currentTournament)

const activeTab = ref('bracket')
const publicMatches = ref([])
const loadingBracket = ref(false)
const standingsData = ref([])
const loadingStandings = ref(false)
const myRegistration = ref(null)
const myRegistrations = ref([])
const registrations = ref([])
const loadingRegistrations = ref(false)
const selectedCategoryId = ref(null)
const isAlreadyRegistered = computed(() => Boolean(myRegistration.value))
const hasHtmlContent = (value) => /<\/?[a-z][\s\S]*>/i.test(value || '')

const renderTournamentDescription = (value) => {
  if (!value) return ''
  if (hasHtmlContent(value)) return value
  return value.replace(/\r\n/g, '\n').replace(/\n/g, '<br>')
}

watch(tournamentId, async (newId) => {
  if (newId) {
    // Reset state
    activeTab.value = 'bracket'
    publicMatches.value = []
    standingsData.value = []
    registrations.value = []
    selectedCategoryId.value = null
    myRegistration.value = null
    myRegistrations.value = []
    
    await tournamentStore.fetchTournamentById(newId)
    
    // Re-check registration
    if (authStore.isAuthenticated) {
      checkRegistration()
    }
  }
}, { immediate: true })

const checkRegistration = async () => {
  try {
    const myRegs = await apiClient.get('/api/registrations/my-registrations')
    myRegistrations.value = myRegs.filter(r => r.tournament_id === parseInt(tournamentId.value) && r.status !== 'cancelled' && r.status !== 'rejected')
    syncCurrentRegistration()
  } catch (err) {
    console.error("Lỗi kiểm tra đăng ký:", err)
  }
}

const syncCurrentRegistration = () => {
  myRegistration.value = myRegistrations.value.find(r => r.category_id === selectedCategoryId.value) || null
}
const fetchRegistrations = async () => {
  loadingRegistrations.value = true
  try {
    const url = `/api/tournaments/${tournamentId.value}/registrations` + 
                (selectedCategoryId.value ? `?category_id=${selectedCategoryId.value}` : '')
    const data = await apiClient.get(url)
    registrations.value = data
  } catch (err) {
    console.error("Lỗi tải danh sách VĐV:", err)
  } finally {
    loadingRegistrations.value = false
  }
}


const fetchStandings = async () => {
  loadingStandings.value = true
  try {
    const url = `/api/tournaments/${tournamentId.value}/standings` + 
                (selectedCategoryId.value ? `?category_id=${selectedCategoryId.value}` : '')
    const data = await apiClient.get(url)
    standingsData.value = data
  } catch (err) {
    console.error("Lỗi tải bảng xếp hạng:", err)
  } finally {
    loadingStandings.value = false
  }
}

const isRegistrationOpen = computed(() => {
  if (!tournament.value) return false;
  if (tournament.value.status !== 'open') return false;
  
  if (tournament.value.registration_close_at) {
    const closeDate = new Date(tournament.value.registration_close_at);
    const now = new Date();
    if (now > closeDate) return false;
  }
  
  return true;
});

const isPastDeadline = computed(() => {
  if (!tournament.value?.registration_close_at) return false;
  return new Date() >= new Date(tournament.value.registration_close_at);
});

const isTournamentFull = computed(() => {
  if (!tournament.value) return false
  return tournament.value.current_participants >= (tournament.value.max_participants || tournament.value.draw_size)
})

const fetchBracket = async () => {
  loadingBracket.value = true
  try {
    const url = `/api/tournaments/${tournamentId.value}/matches` + 
                (selectedCategoryId.value ? `?category_id=${selectedCategoryId.value}` : '')
    const data = await apiClient.get(url)
    publicMatches.value = data
  } catch (err) {
    console.error("Không tải được sơ đồ nhánh đấu:", err)
  } finally {
    loadingBracket.value = false
  }
}

// Watch category change to re-fetch data
watch(selectedCategoryId, (newVal) => {
  if (newVal) {
    syncCurrentRegistration()
    fetchBracket()
    fetchStandings()
    fetchRegistrations()
  }
}, { immediate: true })

// Initialize first category if available from tournament data
watch(() => tournament.value?.categories, (cats) => {
  if (cats && cats.length > 0 && !selectedCategoryId.value) {
    selectedCategoryId.value = cats[0].id
  }
}, { immediate: true })

// RE-FETCH DATA ON TAB SWITCH (Fix blank list bug)
watch(activeTab, (newTab) => {
  if (!selectedCategoryId.value) return
  
  if ((newTab === 'bracket' || newTab === 'schedule' || newTab === 'media') && publicMatches.value.length === 0) {
    fetchBracket()
  } else if (newTab === 'standings' && standingsData.value.length === 0) {
    fetchStandings()
  } else if (newTab === 'participants' && registrations.value.length === 0) {
    fetchRegistrations()
  }
})

const groupedMatches = computed(() => {
  const groups = {}
  bracketTreeMatches.value.forEach(m => {
    if (!groups[m.round_code]) groups[m.round_code] = []
    groups[m.round_code].push(m)
  })
  const order = ['G1', 'G2', 'G3', 'R128', 'R64', 'R32', 'R16', 'QF', 'SF', 'F', 'FINAL']
  return Object.keys(groups)
    .sort((a, b) => {
      const idxA = order.indexOf(a)
      const idxB = order.indexOf(b)
      if (idxA === -1 && idxB === -1) return a.localeCompare(b)
      if (idxA === -1) return 1
      if (idxB === -1) return -1
      return idxA - idxB
    })
    .map(key => ({
      label: key,
      items: [...groups[key]].sort((a, b) => (a.match_no || 0) - (b.match_no || 0))
    }))
})

const isGroupStageMatch = (match) => {
  const roundCode = String(match?.round_code || '').toUpperCase()
  return match?.stage_type === 'group_stage' || /^G\d+/.test(roundCode)
}

const getGroupId = (match) => {
  if (match?.group_id) return Number(match.group_id)
  const roundCode = String(match?.round_code || '')
  const parsed = roundCode.match(/^G(\d+)/i)
  return parsed ? Number(parsed[1]) : 1
}

const groupStageBoards = computed(() => {
  const groupMap = new Map()

  publicMatches.value
    .filter(isGroupStageMatch)
    .forEach(match => {
      const groupId = getGroupId(match)
      if (!groupMap.has(groupId)) {
        groupMap.set(groupId, {
          id: groupId,
          title: `Bảng ${groupId}`,
          matchCount: 0,
          rounds: new Map()
        })
      }

      const group = groupMap.get(groupId)
      const roundCode = match.round_code || 'Vòng bảng'
      if (!group.rounds.has(roundCode)) {
        group.rounds.set(roundCode, {
          code: roundCode,
          label: roundCode,
          items: []
        })
      }

      group.rounds.get(roundCode).items.push(match)
      group.matchCount += 1
    })

  return [...groupMap.values()]
    .sort((a, b) => a.id - b.id)
    .map(group => ({
      ...group,
      rounds: [...group.rounds.values()]
        .map(round => ({
          ...round,
          items: [...round.items].sort((a, b) => (a.match_no || 0) - (b.match_no || 0))
        }))
        .sort((a, b) => getRoundSortIndex(a.code) - getRoundSortIndex(b.code))
    }))
})

const hasGroupStageMatches = computed(() => groupStageBoards.value.length > 0)
const bracketTreeMatches = computed(() => {
  if (!hasGroupStageMatches.value) return publicMatches.value
  return publicMatches.value.filter(match => !isGroupStageMatch(match))
})

const getRoundSortIndex = (roundLabel) => {
  const label = String(roundLabel || '').toUpperCase()
  if (/^G\d+-R\d+$/.test(label)) {
    const match = label.match(/^G(\d+)-R(\d+)$/)
    return Number(match?.[2] || 0)
  }
  if (/^G\d+$/.test(label)) return Number(label.slice(1))
  if (/VONG\s*\d+|VÒNG\s*\d+|ROUND\s*\d+/i.test(label)) {
    const num = Number(label.match(/\d+/)?.[0] || 0)
    return num || 999
  }
  const order = {
    R128: 1,
    R64: 2,
    R32: 3,
    R16: 4,
    QF: 5,
    SF: 6,
    F: 7,
    FINAL: 7
  }
  return order[label] || 999
}

const bracketRounds = computed(() => {
  const layoutMatches = bracketTreeMatches.value
  const hasTreeLinks = layoutMatches.some(m => m.next_match_id)
  if (!hasTreeLinks) return groupedMatches.value

  const matchMap = new Map(layoutMatches.map(m => [m.id, m]))
  const depthMemo = new Map()

  const getDepth = (match, visiting = new Set()) => {
    if (!match) return 0
    if (depthMemo.has(match.id)) return depthMemo.get(match.id)
    if (visiting.has(match.id)) {
      console.warn('Phát hiện vòng lặp next_match_id trong sơ đồ nhánh:', [...visiting, match.id])
      depthMemo.set(match.id, 0)
      return 0
    }
    visiting.add(match.id)
    const next = match.next_match_id ? matchMap.get(match.next_match_id) : null
    const depth = next ? getDepth(next, visiting) + 1 : 0
    visiting.delete(match.id)
    depthMemo.set(match.id, depth)
    return depth
  }

  const groups = new Map()
  layoutMatches.forEach(match => {
    const depth = getDepth(match)
    if (!groups.has(depth)) groups.set(depth, [])
    groups.get(depth).push(match)
  })

  return [...groups.entries()]
    .sort((a, b) => b[0] - a[0])
    .map(([depth, items], index) => {
      const sortedItems = [...items].sort((a, b) => {
        const orderA = getRoundSortIndex(a.round_code)
        const orderB = getRoundSortIndex(b.round_code)
        if (orderA !== orderB) return orderA - orderB
        return (a.match_no || 0) - (b.match_no || 0)
      })

      return {
        id: depth,
        label: sortedItems[0]?.round_code || `${t('tournaments.round') || 'Round'} ${index + 1}`,
        items: sortedItems
      }
    })
})

const bracketLayout = computed(() => {
  const rounds = bracketRounds.value
  if (!rounds.length) {
    return { width: 0, height: 0, nodes: [], lines: [], rounds: [] }
  }

  const cardWidth = 360
  const cardHeight = 282
  const colGap = 104
  const rowGap = 64
  const headerHeight = 54
  const leftPad = 24
  const topPad = 12

  const positionById = new Map()
  const nodes = []

  rounds.forEach((round, roundIdx) => {
    const x = leftPad + roundIdx * (cardWidth + colGap)
    const parentSlots = new Map()

    if (roundIdx > 0) {
      rounds[roundIdx - 1].items.forEach(prevMatch => {
        if (!prevMatch.next_match_id) return
        if (!parentSlots.has(prevMatch.next_match_id)) parentSlots.set(prevMatch.next_match_id, [])
        parentSlots.get(prevMatch.next_match_id).push(positionById.get(prevMatch.id))
      })
    }

    round.items.forEach((match, index) => {
      const childPositions = parentSlots.get(match.id)?.filter(Boolean) || []
      const baseY = topPad + headerHeight + index * (cardHeight + rowGap)
      const linkedY = childPositions.length
        ? (Math.min(...childPositions.map(p => p.y)) + Math.max(...childPositions.map(p => p.y))) / 2
        : baseY
      const y = Math.max(topPad + headerHeight, linkedY)
      const position = { id: match.id, roundIdx, x, y, match }
      positionById.set(match.id, position)
      nodes.push(position)
    })
  })

  const lines = []
  nodes.forEach(node => {
    if (!node.match.next_match_id) return
    const target = positionById.get(node.match.next_match_id)
    if (!target) return
    const startX = node.x + cardWidth
    const startY = node.y + cardHeight / 2
    const endX = target.x
    const endY = target.y + cardHeight / 2
    const midX = startX + Math.max(36, (endX - startX) / 2)
    lines.push({
      id: `${node.id}-${target.id}`,
      points: `${startX},${startY} ${midX},${startY} ${midX},${endY} ${endX},${endY}`
    })
  })

  const width = leftPad * 2 + rounds.length * cardWidth + Math.max(0, rounds.length - 1) * colGap
  const height = Math.max(
    320,
    topPad + headerHeight + Math.max(...nodes.map(node => node.y + cardHeight), 0) + 24
  )
  const roundHeaders = rounds.map((round, index) => ({
    ...round,
    x: leftPad + index * (cardWidth + colGap),
    y: topPad
  }))

  return { width, height, nodes, lines, rounds: roundHeaders, cardWidth, cardHeight }
})

const goToRegister = () => {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  router.push({ name: 'tournament-register', params: { id: tournamentId.value } })
}

const formatDate = (val) => {
  if (!val) return t('tournaments.notUpdated')
  const d = new Date(val)
  if (!isNaN(d.getTime())) {
    return d.toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    })
  }
  // Thử parse thủ công nếu là định dạng dd/mm/yyyy
  if (typeof val === 'string' && val.includes('/')) {
    const p = val.split(/[\/\s:]/)
    if (p.length >= 3) {
      const d2 = new Date(p[2], p[1]-1, p[0])
      if (!isNaN(d2.getTime())) {
        return d2.toLocaleDateString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', {
          day: 'numeric',
          month: 'long',
          year: 'numeric'
        })
      }
    }
  }
  return t('tournaments.notUpdated')
}

const formatDateTime = (val) => {
  if (!val) return '---'
  const d = new Date(val)
  if (isNaN(d.getTime())) return formatDate(val)
  return d.toLocaleString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const selectedCategory = computed(() => {
  if (!selectedCategoryId.value || !tournament.value?.categories) return null
  return tournament.value.categories.find(c => c.id === selectedCategoryId.value)
})

const selectedCategoryName = computed(() => {
  if (selectedCategory.value) return selectedCategory.value.name
  if (tournament.value?.categories?.length > 0) return tournament.value.categories[0].name
  return tournament.value?.category_type || '---'
})

const allMedia = computed(() => {
  const media = []
  publicMatches.value.forEach(m => {
    if (m.video_url || m.image_url || m.live_stream_url) {
      media.push({
        id: m.id,
        match_label: `Trận #${m.match_no}`,
        round_code: m.round_code,
        p1_name: m.p1_name,
        p2_name: m.p2_name,
        live_stream_url: m.live_stream_url,
        video_url: m.video_url,
        image_url: m.image_url,
        match: m
      })
    }
  })
  return media
})

const scheduledMatches = computed(() => {
  return [...publicMatches.value].filter(hasAssignedScheduleSide).sort((a, b) => {
    const timeA = a.start_time ? new Date(a.start_time).getTime() : Number.MAX_SAFE_INTEGER
    const timeB = b.start_time ? new Date(b.start_time).getTime() : Number.MAX_SAFE_INTEGER
    if (timeA !== timeB) return timeA - timeB
    return (a.match_no || 0) - (b.match_no || 0)
  })
})

const selectedScheduleRound = ref('')

const hasAssignedScheduleSide = (match) => {
  return Boolean(
    match?.side_a_registration_id ||
    match?.side_b_registration_id ||
    match?.p1_user_id ||
    match?.p2_user_id ||
    match?.p1_name ||
    match?.p2_name
  )
}

const getScheduleRoundLabel = (roundCode) => roundCode || 'Vòng chưa đặt tên'

const scheduleRounds = computed(() => {
  const roundMap = new Map()

  scheduledMatches.value.forEach(match => {
    const roundCode = match.round_code || ''
    if (!roundMap.has(roundCode)) {
      roundMap.set(roundCode, {
        code: roundCode,
        label: getScheduleRoundLabel(roundCode),
        count: 0
      })
    }
    roundMap.get(roundCode).count += 1
  })

  return [...roundMap.values()].sort((a, b) => {
    const orderA = getRoundSortIndex(a.code)
    const orderB = getRoundSortIndex(b.code)
    if (orderA !== orderB) return orderA - orderB
    return String(a.label).localeCompare(String(b.label), 'vi')
  })
})

watch(scheduleRounds, (rounds) => {
  if (!rounds.length) {
    selectedScheduleRound.value = ''
    return
  }

  const currentExists = rounds.some(round => round.code === selectedScheduleRound.value)
  if (!currentExists) selectedScheduleRound.value = rounds[0].code
}, { immediate: true })

const selectedScheduleRoundLabel = computed(() => {
  return scheduleRounds.value.find(round => round.code === selectedScheduleRound.value)?.label || ''
})

const selectedRoundMatches = computed(() => {
  return scheduledMatches.value.filter(match => (match.round_code || '') === selectedScheduleRound.value)
})

const isAdvanceMatch = (match) => {
  if (match.status !== 'completed') return false
  return Boolean(match.winner_side) && (!match.p1_user_id || !match.p2_user_id)
}

const getMatchStatusLabel = (match) => {
  if (isAdvanceMatch(match)) return 'Vào vòng tiếp'
  if (match.status === 'completed') return t('tournaments.completed') || 'Hoàn thành'
  if (match.status === 'ongoing') return t('tournaments.live') || 'Live'
  if (match.status === 'scheduled') return t('tournaments.upcoming') || 'Sắp đánh'
  return 'Chưa xếp lịch'
}

const getMatchStatusClass = (match) => {
  if (isAdvanceMatch(match)) return 'is-advance'
  if (match.status === 'completed') return 'is-done'
  if (match.status === 'ongoing') return 'is-live'
  if (match.status === 'scheduled') return 'is-upcoming'
  return ''
}

const hasMatchMeta = (match) => {
  return Boolean(match?.start_time || match?.advance_note || match?.referee_name || match?.live_stream_url || match?.video_url || match?.image_url || match?.score_summary)
}

const previewVisible = ref(false)
const previewData = ref({ type: 'image', url: '', title: '', match: null })
const matchDetailVisible = ref(false)
const selectedScheduleMatch = ref(null)

const openPreview = (type, url, title, matchObj = null) => {
  previewData.value = { type, url, title, match: matchObj }
  previewVisible.value = true
}

const openScheduleMatchDetail = (match) => {
  selectedScheduleMatch.value = match
  matchDetailVisible.value = true
}

const getScheduleSidePlayers = (match, side) => {
  if (!match) return ['Chưa xác định']
  const mainName = side === 'a' ? match.p1_name : match.p2_name
  const partnerName = side === 'a' ? match.p1_partner_name : match.p2_partner_name
  return [mainName, partnerName].filter(Boolean).length
    ? [mainName, partnerName].filter(Boolean)
    : ['Chưa xác định']
}

const getVideoEmbedUrl = (url) => {
  if (!url) return ''
  if (url.includes('youtube.com/embed/')) return url
  if (url.includes('youtube.com/watch?v=')) return url.replace('watch?v=', 'embed/')
  if (url.includes('youtube.com/live/')) {
    const id = url.split('/live/')[1]?.split(/[?&]/)[0]
    return id ? `https://www.youtube.com/embed/${id}` : url
  }
  if (url.includes('youtu.be/')) {
    const id = url.split('youtu.be/')[1]?.split(/[?&]/)[0]
    return id ? `https://www.youtube.com/embed/${id}` : url
  }
  return url
}

const parseSets = (scoreSummary) => {
  if (!scoreSummary) return []
  return scoreSummary.split(',').map(s => {
    const parts = s.trim().split('-')
    return {
      a: parts[0] || '0',
      b: parts[1] || '0'
    }
  })
}
</script>

<template>
  <div class="tournament-detail-root">
    <div v-if="tournament" class="neo-tournament-page">
      <div class="neo-hero">
        <div class="hero-glow glow-1"></div>
        <div class="hero-glow glow-2"></div>
        
        <div class="container hero-inner">
          <div class="hero-meta-top">
            <span class="neo-badge" :class="tournament.status">
              <span class="badge-dot"></span>
              {{ tournament.status.toUpperCase() }}
            </span>
            <span class="tour-type">{{ selectedCategoryName }}</span>
          </div>
          
          <h1 class="hero-title">{{ tournament.name }}</h1>
          
          <div class="hero-details">
            <div class="hd-item">
              <el-icon><CalendarIcon /></el-icon>
              <div>
                <span class="hd-lbl">{{ t('tournaments.startDate') }}</span>
                <span class="hd-val">{{ formatDate(tournament.start_date) }} - {{ formatDate(tournament.end_date) }}</span>
              </div>
            </div>
            <div class="hd-divider"></div>
            <div class="hd-item">
              <el-icon><Location /></el-icon>
              <div>
                <span class="hd-lbl">{{ t('tournaments.location') }}</span>
                <span class="hd-val">{{ tournament.location || t('tournaments.notUpdated') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

    <div class="container main-overlap detail-wide-shell">
      <div class="neo-grid">
        
        <div class="neo-col-main">
          
          <div class="neo-tabs-container">
            <el-tabs v-model="activeTab" class="neo-tabs">
              
              <el-tab-pane :label="t('tournaments.overview')" name="info">
                <div class="bento-layout">
                  <div v-if="isAlreadyRegistered" class="bento-box box-sm registered-highlight">
                    <el-icon class="bento-icon"><Check /></el-icon>
                    <span class="bento-lbl">Nội dung bạn tham gia</span>
                    <strong class="bento-val">{{ myRegistration?.category_name || 'Đã đăng ký' }}</strong>
                  </div>
                  <div class="bento-box box-sm" :class="{ 'viewing-highlight': !isAlreadyRegistered }">
                    <el-icon class="bento-icon"><User /></el-icon>
                    <span class="bento-lbl">Đang xem nội dung</span>
                    <strong class="bento-val">{{ selectedCategoryName }}</strong>
                  </div>
                  <div class="bento-box box-sm">
                    <el-icon class="bento-icon"><Trophy /></el-icon>
                    <span class="bento-lbl">Điểm giới hạn</span>
                    <strong class="bento-val">{{ selectedCategory?.max_points || 'Open' }} Pts</strong>
                  </div>
                  
                  <div class="bento-box box-sm">
                    <el-icon class="bento-icon"><Ticket /></el-icon>
                    <span class="bento-lbl">{{ t('tournaments.drawSize') }}</span>
                    <strong class="bento-val">{{ tournament.draw_size }} {{ t('tournaments.playersCount') }}</strong>
                  </div>
                  <div class="bento-box box-sm">
                    <el-icon class="bento-icon"><Location /></el-icon>
                    <span class="bento-lbl">{{ t('tournaments.surface') }}</span>
                    <strong class="bento-val">{{ tournament.surface_type || 'Hard Court' }}</strong>
                  </div>

                  <div class="bento-box box-lg">
                    <h3>{{ t('tournaments.aboutTournament') }}</h3>
                    <div class="tournament-description" v-if="tournament.description" v-html="renderTournamentDescription(tournament.description)"></div>
                    <p v-else>
                      {{ tournament.name }} {{ t('tournaments.tournamentDesc') }}
                    </p>
                    <div class="bento-highlight">
                      <strong>{{ t('tournaments.registrationDeadline') }}</strong> 
                      <span>{{ t('tournaments.from') }} {{ formatDate(tournament.registration_open_at) }} {{ t('tournaments.to') }} {{ formatDate(tournament.registration_close_at) }}</span>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane :label="t('tournaments.bracket')" name="bracket">
                <div v-if="tournament.categories?.length > 1" class="category-filter-wrap">
                  <div class="filter-label">
                    <span class="filter-icon"><el-icon><Trophy /></el-icon></span>
                    <span class="filter-kicker">Nội dung thi đấu</span>
                    <strong>Chọn nội dung</strong>
                  </div>
                  <el-radio-group v-model="selectedCategoryId" size="small">
                    <el-radio-button v-for="cat in tournament.categories" :key="cat.id" :value="cat.id">
                      {{ cat.name }}
                    </el-radio-button>
                  </el-radio-group>
                </div>

                <div v-if="publicMatches.length > 0" class="bracket-scroll-hint">
                  <el-icon><InfoFilled /></el-icon>
                  <span>Vuốt ngang để xem các vòng đấu khác ↔</span>
                </div>

                <div v-loading="loadingBracket" class="bracket-viewport">
                  <div v-if="publicMatches.length === 0" class="empty-state">
                    <div class="es-icon">🎾</div>
                    <p>{{ t('tournaments.bracketNotDrawn') }}</p>
                  </div>

                  <div v-else-if="hasGroupStageMatches" class="group-stage-public-wrap">
                    <section v-for="group in groupStageBoards" :key="group.id" class="public-group-card">
                      <div class="public-group-head">
                        <div>
                          <h3>{{ group.title }}</h3>
                          <p>{{ group.matchCount }} {{ t('tournaments.matches') }}, {{ group.rounds.length }} vòng thi đấu</p>
                        </div>
                      </div>

                      <div class="public-group-rounds">
                        <div v-for="round in group.rounds" :key="`${group.id}-${round.code}`" class="public-round-lane">
                          <div class="public-round-head">
                            <span>{{ round.label }}</span>
                            <small>{{ round.items.length }} {{ t('tournaments.matches') }}</small>
                          </div>

                          <div class="public-round-matches">
                            <div v-for="m in round.items" :key="m.id" class="group-match-card" :class="{ 'has-extra-meta': hasMatchMeta(m) }">
                              <div class="m-v2-header">
                                <div class="m-v2-header-left">
                                  <span class="m-v2-no">#{{ m.match_no }}</span>
                                  <span class="m-v2-court">
                                    <el-icon><Location /></el-icon> {{ m.court || 'Chưa gán sân' }}
                                  </span>
                                </div>
                                <span class="m-v2-status" :class="getMatchStatusClass(m)">{{ getMatchStatusLabel(m) }}</span>
                              </div>

                              <div class="m-v2-meta-strip" v-if="m.start_time || m.score_summary || m.advance_note">
                                <span v-if="m.start_time" class="match-meta-chip">
                                  <el-icon><CalendarIcon /></el-icon>
                                  {{ formatDateTime(m.start_time) }}
                                </span>
                                <span v-if="m.score_summary" class="match-score-chip">{{ m.score_summary }}</span>
                                <span v-if="m.advance_note" class="match-advance-chip">{{ m.advance_note }}</span>
                              </div>

                              <div class="m-v2-body">
                                <div class="m-v2-player" :class="{ 'is-win': m.winner_side === 'side_a' }">
                                  <div class="player-stack-v2">
                                    <div class="p-mini-box">
                                      <el-avatar :size="20" :src="m.p1_avatar" class="p-avatar-mini">
                                        <el-icon><User /></el-icon>
                                      </el-avatar>
                                      <router-link :to="m.p1_user_id ? `/players/${m.p1_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p1_user_id}">
                                        {{ m.p1_name || 'Chưa xác định' }}
                                      </router-link>
                                      <el-icon v-if="m.winner_side === 'side_a'" class="p-win-icon"><Check /></el-icon>
                                    </div>
                                    <div v-if="m.p1_partner_name" class="p-mini-box">
                                      <el-avatar :size="20" :src="m.p1_partner_avatar" class="p-avatar-mini">
                                        <el-icon><User /></el-icon>
                                      </el-avatar>
                                      <router-link :to="m.p1_partner_user_id ? `/players/${m.p1_partner_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p1_partner_user_id}">
                                        {{ m.p1_partner_name }}
                                      </router-link>
                                    </div>
                                  </div>
                                  <div class="score-container-v2" v-if="m.status === 'completed' || m.score_summary">
                                    <div class="set-scores-wrap" v-if="m.score_summary">
                                      <span v-for="(set, sIdx) in parseSets(m.score_summary)" :key="sIdx" class="set-score-pill" :class="{ 'is-set-win': Number(set.a) > Number(set.b) }">
                                        {{ set.a }}
                                      </span>
                                    </div>
                                  </div>
                                </div>

                                <div class="m-v2-divider"></div>

                                <div class="m-v2-player" :class="{ 'is-win': m.winner_side === 'side_b' }">
                                  <div class="player-stack-v2">
                                    <div class="p-mini-box">
                                      <el-avatar :size="20" :src="m.p2_avatar" class="p-avatar-mini">
                                        <el-icon><User /></el-icon>
                                      </el-avatar>
                                      <router-link :to="m.p2_user_id ? `/players/${m.p2_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p2_user_id}">
                                        {{ m.p2_name || 'Chưa xác định' }}
                                      </router-link>
                                      <el-icon v-if="m.winner_side === 'side_b'" class="p-win-icon"><Check /></el-icon>
                                    </div>
                                    <div v-if="m.p2_partner_name" class="p-mini-box">
                                      <el-avatar :size="20" :src="m.p2_partner_avatar" class="p-avatar-mini">
                                        <el-icon><User /></el-icon>
                                      </el-avatar>
                                      <router-link :to="m.p2_partner_user_id ? `/players/${m.p2_partner_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p2_partner_user_id}">
                                        {{ m.p2_partner_name }}
                                      </router-link>
                                    </div>
                                  </div>
                                  <div class="score-container-v2" v-if="m.status === 'completed' || m.score_summary">
                                    <div class="set-scores-wrap" v-if="m.score_summary">
                                      <span v-for="(set, sIdx) in parseSets(m.score_summary)" :key="sIdx" class="set-score-pill" :class="{ 'is-set-win': Number(set.b) > Number(set.a) }">
                                        {{ set.b }}
                                      </span>
                                    </div>
                                  </div>
                                </div>

                                <div v-if="m.referee_name || m.advance_note || m.live_stream_url || m.video_url || m.image_url" class="m-v2-footer">
                                  <div v-if="m.referee_name" class="m-referee-badge" :title="`${m.referee_name}${m.referee_phone ? ' - ' + m.referee_phone : ''}`">
                                    <span class="referee-icon">TT</span>
                                    <span class="referee-name">{{ m.referee_name }}</span>
                                  </div>
                                  <div class="m-media-actions">
                                    <el-tooltip v-if="m.live_stream_url" content="Livestream" placement="top">
                                      <button class="media-icon-btn live-btn" type="button" @click.stop="openPreview('video', m.live_stream_url, `Livestream Trận #${m.match_no}`, m)">
                                        <el-icon><VideoPlay /></el-icon>
                                      </button>
                                    </el-tooltip>
                                    <el-tooltip v-if="m.video_url" content="Video highlight" placement="top">
                                      <button class="media-icon-btn video-btn" type="button" @click.stop="openPreview('video', m.video_url, `Highlight Trận #${m.match_no}`, m)">
                                        <el-icon><VideoCamera /></el-icon>
                                      </button>
                                    </el-tooltip>
                                    <el-tooltip v-if="m.image_url" content="Ảnh trận đấu" placement="top">
                                      <button class="media-icon-btn image-btn" type="button" @click.stop="openPreview('image', m.image_url, `Ảnh Trận #${m.match_no}`, m)">
                                        <el-icon><Picture /></el-icon>
                                      </button>
                                    </el-tooltip>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </section>

                    <div
                      v-if="bracketTreeMatches.length > 0"
                      class="neo-bracket-tree playoff-tree-after-groups"
                      :style="{ width: `${bracketLayout.width}px`, height: `${bracketLayout.height}px` }"
                    >
                      <svg
                        class="bracket-lines"
                        :width="bracketLayout.width"
                        :height="bracketLayout.height"
                        :viewBox="`0 0 ${bracketLayout.width} ${bracketLayout.height}`"
                        aria-hidden="true"
                      >
                        <polyline
                          v-for="line in bracketLayout.lines"
                          :key="line.id"
                          :points="line.points"
                          class="bracket-link"
                        />
                      </svg>

                      <div
                        v-for="(round, roundIdx) in bracketLayout.rounds"
                        :key="round.id"
                        class="round-sticky-header tree-round-header"
                        :style="{ left: `${round.x}px`, top: `${round.y}px`, width: `${bracketLayout.cardWidth}px` }"
                      >
                        <div class="round-title-group">
                          <span class="round-index">{{ roundIdx + 1 }}</span>
                          <h4 class="round-title">{{ round.label }}</h4>
                        </div>
                        <span class="round-count">{{ round.items.length }} {{ t('tournaments.matches') }}</span>
                      </div>

                      <div
                        v-for="node in bracketLayout.nodes"
                        :key="node.id"
                        class="match-node-wrapper tree-node"
                        :style="{
                          left: `${node.x}px`,
                          top: `${node.y}px`,
                          width: `${bracketLayout.cardWidth}px`,
                          height: `${bracketLayout.cardHeight}px`
                        }"
                      >
                        <template v-for="m in [node.match]" :key="m.id">
                          <div class="match-node-v2" :class="{ 'has-extra-meta': hasMatchMeta(m) }">
                            <div class="m-v2-header">
                              <div class="m-v2-header-left">
                                <span class="m-v2-no">#{{ m.match_no }}</span>
                                <span class="m-v2-court">
                                  <el-icon><Location /></el-icon> {{ m.court || 'Chưa gán sân' }}
                                </span>
                              </div>
                              <span class="m-v2-status" :class="getMatchStatusClass(m)">{{ getMatchStatusLabel(m) }}</span>
                            </div>
                            <div class="m-v2-meta-strip" v-if="m.start_time || m.score_summary || m.advance_note">
                              <span v-if="m.start_time" class="match-meta-chip">
                                <el-icon><CalendarIcon /></el-icon>
                                {{ formatDateTime(m.start_time) }}
                              </span>
                              <span v-if="m.score_summary" class="match-score-chip">{{ m.score_summary }}</span>
                              <span v-if="m.advance_note" class="match-advance-chip">{{ m.advance_note }}</span>
                            </div>
                            <div class="m-v2-body">
                              <div class="m-v2-player" :class="{ 'is-win': m.winner_side === 'side_a' }">
                                <div class="player-stack-v2">
                                  <div class="p-mini-box">
                                    <el-avatar :size="20" :src="m.p1_avatar" class="p-avatar-mini"><el-icon><User /></el-icon></el-avatar>
                                    <router-link :to="m.p1_user_id ? `/players/${m.p1_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p1_user_id}">{{ m.p1_name || '???' }}</router-link>
                                    <el-icon v-if="m.winner_side === 'side_a'" class="p-win-icon"><Check /></el-icon>
                                  </div>
                                  <div v-if="m.p1_partner_name" class="p-mini-box">
                                    <el-avatar :size="20" :src="m.p1_partner_avatar" class="p-avatar-mini"><el-icon><User /></el-icon></el-avatar>
                                    <router-link :to="m.p1_partner_user_id ? `/players/${m.p1_partner_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p1_partner_user_id}">{{ m.p1_partner_name }}</router-link>
                                  </div>
                                </div>
                                <div class="score-container-v2" v-if="m.status === 'completed' || m.score_summary">
                                  <div class="set-scores-wrap" v-if="m.score_summary">
                                    <span v-for="(set, sIdx) in parseSets(m.score_summary)" :key="sIdx" class="set-score-pill" :class="{ 'is-set-win': Number(set.a) > Number(set.b) }">{{ set.a }}</span>
                                  </div>
                                </div>
                              </div>
                              <div class="m-v2-divider"></div>
                              <div class="m-v2-player" :class="{ 'is-win': m.winner_side === 'side_b' }">
                                <div class="player-stack-v2">
                                  <div class="p-mini-box">
                                    <el-avatar :size="20" :src="m.p2_avatar" class="p-avatar-mini"><el-icon><User /></el-icon></el-avatar>
                                    <router-link :to="m.p2_user_id ? `/players/${m.p2_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p2_user_id}">{{ m.p2_name || '???' }}</router-link>
                                    <el-icon v-if="m.winner_side === 'side_b'" class="p-win-icon"><Check /></el-icon>
                                  </div>
                                  <div v-if="m.p2_partner_name" class="p-mini-box">
                                    <el-avatar :size="20" :src="m.p2_partner_avatar" class="p-avatar-mini"><el-icon><User /></el-icon></el-avatar>
                                    <router-link :to="m.p2_partner_user_id ? `/players/${m.p2_partner_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p2_partner_user_id}">{{ m.p2_partner_name }}</router-link>
                                  </div>
                                </div>
                                <div class="score-container-v2" v-if="m.status === 'completed' || m.score_summary">
                                  <div class="set-scores-wrap" v-if="m.score_summary">
                                    <span v-for="(set, sIdx) in parseSets(m.score_summary)" :key="sIdx" class="set-score-pill" :class="{ 'is-set-win': Number(set.b) > Number(set.a) }">{{ set.b }}</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </template>
                      </div>
                    </div>
                  </div>
                  
                  <div
                    v-else
                    class="neo-bracket-tree"
                    :style="{ width: `${bracketLayout.width}px`, height: `${bracketLayout.height}px` }"
                  >
                    <svg
                      class="bracket-lines"
                      :width="bracketLayout.width"
                      :height="bracketLayout.height"
                      :viewBox="`0 0 ${bracketLayout.width} ${bracketLayout.height}`"
                      aria-hidden="true"
                    >
                      <polyline
                        v-for="line in bracketLayout.lines"
                        :key="line.id"
                        :points="line.points"
                        class="bracket-link"
                      />
                    </svg>

                    <div
                      v-for="(round, roundIdx) in bracketLayout.rounds"
                      :key="round.id"
                      class="round-sticky-header tree-round-header"
                      :style="{ left: `${round.x}px`, top: `${round.y}px`, width: `${bracketLayout.cardWidth}px` }"
                    >
                      <div class="round-title-group">
                        <span class="round-index">{{ roundIdx + 1 }}</span>
                        <h4 class="round-title">{{ round.label }}</h4>
                      </div>
                      <span class="round-count">{{ round.items.length }} {{ t('tournaments.matches') }}</span>
                    </div>

                    <div
                      v-for="node in bracketLayout.nodes"
                      :key="node.id"
                      class="match-node-wrapper tree-node"
                      :style="{
                        left: `${node.x}px`,
                        top: `${node.y}px`,
                        width: `${bracketLayout.cardWidth}px`,
                        height: `${bracketLayout.cardHeight}px`
                      }"
                    >
                      <template v-for="m in [node.match]" :key="m.id">
                          <div class="match-node-v2" :class="{ 'has-extra-meta': hasMatchMeta(m) }">
                            <div class="m-v2-header">
                              <div class="m-v2-header-left">
                                <span class="m-v2-no">#{{ m.match_no }}</span>
                                <span class="m-v2-court">
                                  <el-icon><Location /></el-icon> {{ m.court || 'Chưa gán sân' }}
                                </span>
                              </div>
                              <span class="m-v2-status" :class="getMatchStatusClass(m)">{{ getMatchStatusLabel(m) }}</span>
                            </div>
                            <div class="m-v2-meta-strip" v-if="m.start_time || m.score_summary || m.advance_note">
                              <span v-if="m.start_time" class="match-meta-chip">
                                <el-icon><CalendarIcon /></el-icon>
                                {{ formatDateTime(m.start_time) }}
                              </span>
                              <span v-if="m.score_summary" class="match-score-chip">{{ m.score_summary }}</span>
                              <span v-if="m.advance_note" class="match-advance-chip">{{ m.advance_note }}</span>
                            </div>
                            
                            <div class="m-v2-body">
                              <div class="m-v2-player" :class="{ 'is-win': m.winner_side === 'side_a' }">
                                <div class="player-stack-v2">
                                  <div class="p-mini-box">
                                    <el-avatar :size="20" :src="m.p1_avatar" class="p-avatar-mini">
                                      <el-icon><User /></el-icon>
                                    </el-avatar>
                                    <router-link :to="m.p1_user_id ? `/players/${m.p1_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p1_user_id}">
                                      {{ m.p1_name || '???' }}
                                    </router-link>
                                    <el-icon v-if="m.winner_side === 'side_a'" class="p-win-icon"><Check /></el-icon>
                                  </div>
                                  <div v-if="m.p1_partner_name" class="p-mini-box">
                                    <el-avatar :size="20" :src="m.p1_partner_avatar" class="p-avatar-mini">
                                      <el-icon><User /></el-icon>
                                    </el-avatar>
                                    <router-link :to="m.p1_partner_user_id ? `/players/${m.p1_partner_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p1_partner_user_id}">
                                      {{ m.p1_partner_name }}
                                    </router-link>
                                  </div>
                                </div>
                                <div class="score-container-v2" v-if="m.status === 'completed'">
                                  <div class="set-scores-wrap" v-if="m.score_summary">
                                    <span v-for="(set, sIdx) in parseSets(m.score_summary)" :key="sIdx" class="set-score-pill" :class="{ 'is-set-win': Number(set.a) > Number(set.b) }">
                                      {{ set.a }}
                                    </span>
                                  </div>
                                  <span class="p-score" v-else-if="m.score_a !== null">{{ m.score_a }}</span>
                                </div>
                              </div>
                              
                              <div class="m-v2-divider"></div>
                              
                              <div class="m-v2-player" :class="{ 'is-win': m.winner_side === 'side_b' }">
                                <div class="player-stack-v2">
                                  <div class="p-mini-box">
                                    <el-avatar :size="20" :src="m.p2_avatar" class="p-avatar-mini">
                                      <el-icon><User /></el-icon>
                                    </el-avatar>
                                    <router-link :to="m.p2_user_id ? `/players/${m.p2_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p2_user_id}">
                                      {{ m.p2_name || '???' }}
                                    </router-link>
                                    <el-icon v-if="m.winner_side === 'side_b'" class="p-win-icon"><Check /></el-icon>
                                  </div>
                                  <div v-if="m.p2_partner_name" class="p-mini-box">
                                    <el-avatar :size="20" :src="m.p2_partner_avatar" class="p-avatar-mini">
                                      <el-icon><User /></el-icon>
                                    </el-avatar>
                                    <router-link :to="m.p2_partner_user_id ? `/players/${m.p2_partner_user_id}` : '#'" class="p-name-link" :class="{'no-link': !m.p2_partner_user_id}">
                                      {{ m.p2_partner_name }}
                                    </router-link>
                                  </div>
                                </div>
                                <div class="score-container-v2" v-if="m.status === 'completed'">
                                  <div class="set-scores-wrap" v-if="m.score_summary">
                                    <span v-for="(set, sIdx) in parseSets(m.score_summary)" :key="sIdx" class="set-score-pill" :class="{ 'is-set-win': Number(set.b) > Number(set.a) }">
                                      {{ set.b }}
                                    </span>
                                  </div>
                                  <span class="p-score" v-else-if="m.score_b !== null">{{ m.score_b }}</span>
                                </div>
                              </div>
                              
                              <div v-if="m.referee_name || m.advance_note || m.live_stream_url || m.video_url || m.image_url" class="m-v2-footer">
                                <div v-if="m.referee_name" class="m-referee-badge" :title="`${m.referee_name}${m.referee_phone ? ' - ' + m.referee_phone : ''}`">
                                  <span class="referee-icon">TT</span>
                                  <span class="referee-name">{{ m.referee_name }}</span>
                                  <span v-if="m.referee_phone" class="referee-phone">{{ m.referee_phone }}</span>
                                </div>
                                <div class="m-media-actions">
                                  <el-tooltip v-if="m.live_stream_url" content="Livestream" placement="top">
                                    <button class="media-icon-btn live-btn" type="button" @click.stop="openPreview('video', m.live_stream_url, `Livestream Trận #${m.match_no}`, m)">
                                      <el-icon><VideoPlay /></el-icon>
                                    </button>
                                  </el-tooltip>
                                  <el-tooltip v-if="m.video_url" content="Video highlight" placement="top">
                                    <button class="media-icon-btn video-btn" type="button" @click.stop="openPreview('video', m.video_url, `Highlight Trận #${m.match_no}`, m)">
                                      <el-icon><VideoCamera /></el-icon>
                                    </button>
                                  </el-tooltip>
                                  <el-tooltip v-if="m.image_url" content="Ảnh trận đấu" placement="top">
                                    <button class="media-icon-btn image-btn" type="button" @click.stop="openPreview('image', m.image_url, `Ảnh Trận #${m.match_no}`, m)">
                                      <el-icon><Picture /></el-icon>
                                    </button>
                                  </el-tooltip>
                                </div>
                              </div>
                            </div>
                          </div>
                      </template>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane label="LỊCH THI ĐẤU" name="schedule">
                <div v-if="tournament.categories?.length > 1" class="category-filter-wrap">
                  <div class="filter-label">
                    <span class="filter-icon"><el-icon><Trophy /></el-icon></span>
                    <span class="filter-kicker">Nội dung thi đấu</span>
                    <strong>Chọn nội dung</strong>
                  </div>
                  <el-radio-group v-model="selectedCategoryId" size="small">
                    <el-radio-button v-for="cat in tournament.categories" :key="cat.id" :value="cat.id">
                      {{ cat.name }}
                    </el-radio-button>
                  </el-radio-group>
                </div>

                <div v-loading="loadingBracket" class="schedule-panel">
                  <div v-if="scheduleRounds.length === 0" class="empty-state">
                    <div class="es-icon">🎾</div>
                    <p>Chưa có lịch thi đấu cho nội dung này.</p>
                  </div>

                  <div v-else class="schedule-round-layout">
                    <div class="schedule-round-list">
                      <button
                        v-for="round in scheduleRounds"
                        :key="round.code || 'unknown-round'"
                        type="button"
                        class="schedule-round-item"
                        :class="{ active: selectedScheduleRound === round.code }"
                        @click="selectedScheduleRound = round.code"
                      >
                        <span class="round-arrow">›</span>
                        <strong>{{ round.label }}</strong>
                        <span class="round-count">{{ round.count }}</span>
                      </button>
                    </div>

                    <div class="schedule-round-content">
                      <div class="schedule-round-heading">
                        <div>
                          <span>Vòng đấu</span>
                          <h3>{{ selectedScheduleRoundLabel }}</h3>
                        </div>
                        <small>{{ selectedRoundMatches.length }} trận</small>
                      </div>

                      <div class="schedule-list">
                        <div
                          v-for="m in selectedRoundMatches"
                          :key="m.id"
                          class="schedule-row"
                          :class="getMatchStatusClass(m)"
                          role="button"
                          tabindex="0"
                          @click="openScheduleMatchDetail(m)"
                          @keydown.enter="openScheduleMatchDetail(m)"
                        >
                          <div class="schedule-time">
                            <strong>{{ m.start_time ? formatDateTime(m.start_time) : 'Chưa xếp giờ' }}</strong>
                            <span>{{ m.court || 'Chưa gán sân' }}</span>
                          </div>

                          <div class="schedule-match">
                            <div class="schedule-title">
                              <span>#{{ m.match_no }}</span>
                              <strong>{{ m.round_code }}</strong>
                              <span class="m-v2-status" :class="getMatchStatusClass(m)">{{ getMatchStatusLabel(m) }}</span>
                            </div>

                            <div class="schedule-sides">
                              <div class="schedule-side" :class="{ 'is-win': m.winner_side === 'side_a' }">
                                <span v-for="name in getScheduleSidePlayers(m, 'a')" :key="`a-${m.id}-${name}`" class="schedule-player-name">
                                  {{ name }}
                                </span>
                              </div>
                              <div class="schedule-score" v-if="m.status === 'completed'">
                                <template v-if="m.score_summary">{{ m.score_summary }}</template>
                                <template v-else>{{ m.score_a ?? '-' }} - {{ m.score_b ?? '-' }}</template>
                              </div>
                              <div class="schedule-score" v-else>VS</div>
                              <div class="schedule-side" :class="{ 'is-win': m.winner_side === 'side_b' }">
                                <span v-for="name in getScheduleSidePlayers(m, 'b')" :key="`b-${m.id}-${name}`" class="schedule-player-name">
                                  {{ name }}
                                </span>
                              </div>
                            </div>

                            <div v-if="m.referee_name" class="schedule-meta">
                              Trọng tài: <strong>{{ m.referee_name }}</strong>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane :label="t('tournaments.standings')" name="standings">
                <div v-if="tournament.categories?.length > 1" class="category-filter-wrap">
                  <div class="filter-label">
                    <span class="filter-icon"><el-icon><Trophy /></el-icon></span>
                    <span class="filter-kicker">Nội dung thi đấu</span>
                    <strong>Chọn nội dung</strong>
                  </div>
                  <el-radio-group v-model="selectedCategoryId" size="small">
                    <el-radio-button v-for="cat in tournament.categories" :key="cat.id" :value="cat.id">
                      {{ cat.name }}
                    </el-radio-button>
                  </el-radio-group>
                </div>
                
                <div v-loading="loadingStandings" class="standings-wrap">
                  <div v-if="standingsData.length === 0" class="empty-state">
                    <div class="es-icon">📊</div>
                    <p>{{ t('tournaments.noGroupData') || 'Giải đấu đang diễn ra hoặc chưa có bảng xếp hạng vòng tròn.' }}</p>
                    <p class="small-hint">Bảng xếp hạng chỉ hiển thị cho các giải đấu có giai đoạn Vòng Bảng.</p>
                  </div>
                  
                  <div v-else class="standings-list">
                    <div v-for="group in standingsData" :key="group.group_name" class="premium-group-card">
                      <div class="pg-header">
                        <div class="pg-accent"></div>
                        <h3 class="pg-title">{{ group.group_name }}</h3>
                      </div>
                      
                      <div class="pg-table-wrap">
                        <table class="pg-table">
                          <thead>
                            <tr>
                              <th class="col-rank">#</th>
                              <th>{{ t('tournaments.athlete') }}</th>
                              <th class="text-center">W-L</th>
                              <th class="text-center">+/-</th>
                              <th class="text-center">PTS</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="(row, idx) in group.rankings" :key="row.player_name" :class="{ 'is-qualified': idx < 2 }">
                              <td class="col-rank">
                                <span class="rank-badge" :class="`rank-${idx + 1}`">{{ idx + 1 }}</span>
                              </td>
                              <td class="col-player">
                                <div class="player-stack-premium">
                                  <div class="player-unit-row">
                                    <el-avatar :size="24" :src="row.player_avatar" class="unit-avatar">
                                      <el-icon><User /></el-icon>
                                    </el-avatar>
                                    <router-link :to="row.player_id ? `/players/${row.player_id}` : '#'" class="main-player">
                                      {{ row.player_name }}
                                    </router-link>
                                  </div>
                                  <div v-if="row.partner_name" class="player-unit-row">
                                    <el-avatar :size="24" :src="row.partner_avatar" class="unit-avatar">
                                      <el-icon><User /></el-icon>
                                    </el-avatar>
                                    <router-link :to="row.partner_player_id ? `/players/${row.partner_player_id}` : '#'" class="partner-name">
                                      {{ row.partner_name }}
                                    </router-link>
                                  </div>
                                </div>
                              </td>
                              <td class="text-center stat-cell">
                                <span class="stat-win">{{ row.won }}</span> - <span class="stat-loss">{{ row.lost }}</span>
                              </td>
                              <td class="text-center diff-cell">
                                <el-tooltip content="Hiệu số Game" placement="top">
                                  <span :class="row.game_diff >= 0 ? 'pos' : 'neg'">{{ row.game_diff >= 0 ? '+' : '' }}{{ row.game_diff }}</span>
                                </el-tooltip>
                              </td>
                              <td class="text-center pts-cell">
                                <strong>{{ row.points }}</strong>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane :label="t('tournaments.participants') || 'Danh sách VĐV'" name="participants">
                <div v-if="tournament.categories?.length > 1" class="category-filter-wrap">
                  <div class="filter-label">
                    <span class="filter-icon"><el-icon><Trophy /></el-icon></span>
                    <span class="filter-kicker">Nội dung thi đấu</span>
                    <strong>Chọn nội dung</strong>
                  </div>
                  <el-radio-group v-model="selectedCategoryId" size="small">
                    <el-radio-button v-for="cat in tournament.categories" :key="cat.id" :value="cat.id">
                      {{ cat.name }}
                    </el-radio-button>
                  </el-radio-group>
                </div>
                
                <div v-loading="loadingRegistrations" class="neo-participants-container">
                  <div v-if="registrations.length === 0" class="empty-state">
                    <div class="es-icon">👥</div>
                    <p>{{ t('tournaments.noParticipants') || 'Chưa có vận động viên nào đăng ký.' }}</p>
                  </div>
                  
                  <div v-else class="participants-grid">
                    <div class="pg-table-wrap shadow-sm">
                      <table class="pg-table">
                        <thead>
                          <tr>
                            <th width="60" class="text-center">#</th>
                            <th>{{ t('tournaments.athlete') }}</th>
                            <th>{{ t('tournaments.category') }}</th>
                            <th class="text-right">{{ t('tournaments.registrationTime') || 'Thời gian đăng ký' }}</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(reg, idx) in registrations" :key="reg.id">
                            <td class="text-center"><span class="idx-badge">{{ idx + 1 }}</span></td>
                            <td class="col-player">
                              <div class="teams-display-premium">
                                <div class="player-item-mini">
                                  <el-avatar :size="32" :src="reg.player_avatar" class="player-avatar">
                                    <el-icon><User /></el-icon>
                                  </el-avatar>
                                  <div class="player-meta">
                                    <router-link :to="`/players/${reg.user_id}`" class="name">{{ reg.player_name }}</router-link>
                                    <span v-if="reg.player_skill" class="skill-tag">{{ reg.player_skill }}</span>
                                  </div>
                                </div>
                                <div v-if="reg.partner_name" class="team-divider">&</div>
                                <div v-if="reg.partner_name" class="player-item-mini">
                                  <el-avatar :size="32" :src="reg.partner_avatar" class="player-avatar">
                                    <el-icon><User /></el-icon>
                                  </el-avatar>
                                  <div class="player-meta">
                                    <router-link v-if="reg.partner_user_id" :to="`/players/${reg.partner_user_id}`" class="name">{{ reg.partner_name }}</router-link>
                                    <span v-else class="name">{{ reg.partner_name }}</span>
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td>
                              <span class="category-text">{{ reg.category_name || (reg.registrant_type === 'team' ? 'Đôi' : 'Đơn') }}</span>
                            </td>
                            <td class="text-right time-cell">
                              {{ formatDateTime(reg.registered_at) }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane label="Media" name="media">
                <div v-if="allMedia.length === 0" class="empty-state">
                  <div class="es-icon">🎞️</div>
                  <p>Giải đấu chưa có hình ảnh hoặc video highlight nào.</p>
                </div>
                <div v-else class="media-gallery-grid">
                  <div v-for="item in allMedia" :key="item.id" class="media-item-card">
                    <div class="media-preview">
                      <img v-if="item.image_url" :src="item.image_url" :alt="item.match_label" />
                      <div v-else class="video-placeholder">
                        <el-icon><VideoCamera /></el-icon>
                        <span>{{ item.live_stream_url ? 'Livestream' : 'Video Highlight' }}</span>
                      </div>
                      <div class="media-overlay">
                        <div class="play-btn" @click="openPreview((item.video_url || item.live_stream_url) ? 'video' : 'image', item.video_url || item.live_stream_url || item.image_url, item.match_label, item.match)">
                          <el-icon v-if="item.video_url || item.live_stream_url"><VideoPlay /></el-icon>
                          <el-icon v-else><View /></el-icon>
                        </div>
                      </div>
                    </div>
                    <div class="media-info">
                      <h4 class="m-match-label">{{ item.match_label }}</h4>
                      <p class="m-round-info">{{ item.round_code }} - {{ item.p1_name }} vs {{ item.p2_name }}</p>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

            </el-tabs>
          </div>
        </div>

        <aside class="neo-col-sidebar">
          <div class="neo-action-card sticky">
            
            <div class="ac-header">
              <h2>{{ t('tournaments.entryTicket') }}</h2>
              <div class="price-tag">
                {{ tournament.entry_fee ? new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(tournament.entry_fee) : t('tournaments.free') }}
              </div>
            </div>

            <div class="ac-progress-section">
              <div class="prog-labels">
                <span class="pl-title">{{ t('tournaments.registeredCount') }}</span>
                <strong class="pl-count">{{ tournament.current_participants }} / {{ tournament.max_participants || tournament.draw_size }}</strong>
              </div>
              <div class="prog-track">
                <div class="prog-fill" :style="{ width: Math.min(100, (tournament.current_participants / (tournament.max_participants || tournament.draw_size)) * 100) + '%' }"></div>
              </div>
              <p class="prog-hint" v-if="tournament.status === 'open'">{{ t('tournaments.registrationCloseAt') }} {{ formatDate(tournament.registration_close_at) }}</p>
            </div>

            <div class="ac-actions">
              <template v-if="isRegistrationOpen">
                <button 
                  class="neo-btn-primary" 
                  @click="goToRegister" 
                  :disabled="isTournamentFull"
                  :class="{ 'is-disabled': isTournamentFull }"
                >
                  <span v-if="isTournamentFull">{{ t('tournaments.fullyBooked') }}</span>
                  <span v-else>{{ t('tournaments.registerNow') }} <el-icon><ArrowRight /></el-icon></span>
                </button>
              </template>
              
              <template v-else>
                <div class="ac-status-msg">
                  <el-icon><InfoFilled /></el-icon>
                  <span v-if="isPastDeadline">{{ t('tournaments.registrationExpired') }}</span>
                  <span v-else-if="tournament.status === 'draft'">{{ t('tournaments.registrationNotOpen') }}</span>
                  <span v-else-if="tournament.status === 'ongoing'">{{ t('tournaments.tournamentOngoing') }}</span>
                  <span v-else>{{ t('tournaments.tournamentClosed') }}</span>
                </div>
              </template>
            </div>

          </div>
        </aside>

      </div>
    </div>

    <!-- Mobile Sticky Registration Bar -->
    <div class="mobile-sticky-action-bar" v-if="tournament">
      <div class="ms-inner">
        <div class="ms-info">
          <span class="ms-label">{{ t('tournaments.entryFee') || 'Lệ phí:' }}</span>
          <strong class="ms-price">
            {{ tournament.entry_fee ? new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(tournament.entry_fee) : t('tournaments.free') }}
          </strong>
        </div>
        <div class="ms-btn-wrap">
          <button 
            v-if="isRegistrationOpen"
            class="neo-btn-primary ms-btn" 
            @click="goToRegister" 
            :disabled="isTournamentFull"
            :class="{ 'is-disabled': isTournamentFull }"
          >
            <span v-if="isTournamentFull">{{ t('tournaments.fullyBooked') || 'Đã hết slot' }}</span>
            <span v-else>{{ t('tournaments.registerNow') || 'Đăng ký ngay' }}</span>
          </button>
          <div v-else class="ms-status-text">
            <span v-if="isPastDeadline">{{ t('tournaments.registrationExpired') || 'Hết hạn' }}</span>
            <span v-else-if="tournament.status === 'draft'">{{ t('tournaments.registrationNotOpen') || 'Chưa mở' }}</span>
            <span v-else>{{ t('tournaments.tournamentClosed') || 'Đã đóng' }}</span>
          </div>
        </div>
      </div>
    </div>

  </div>


    <!-- Media Preview Dialog -->
    <el-dialog
      v-model="previewVisible"
      :title="previewData.title"
      width="85%"
      destroy-on-close
      class="media-preview-dialog-v2"
    >
      <div class="preview-layout">
        <!-- Left: Media Player Column -->
        <div class="preview-media-col">
          <div v-if="previewData.type === 'video'" class="video-container">
            <iframe 
              v-if="previewData.url.includes('youtube.com') || previewData.url.includes('youtu.be')"
              :src="getVideoEmbedUrl(previewData.url)"
              frameborder="0" 
              allowfullscreen
              class="preview-video"
            ></iframe>
            <video v-else :src="previewData.url" controls autoplay class="preview-video"></video>
          </div>
          <div v-else class="image-container">
            <el-image :src="previewData.url" fit="contain" class="preview-image" />
          </div>
        </div>

        <!-- Right: Match Info Metadata Column -->
        <div v-if="previewData.match" class="preview-info-col">
          <div class="info-header">
            <span class="info-badge">Trận #{{ previewData.match.match_no }}</span>
            <span class="info-stage">{{ previewData.match.round_code }}</span>
          </div>

          <h4 class="info-title">Đấu thủ & Kết quả</h4>

          <!-- Match Card -->
          <div class="preview-match-card">
            <!-- Side A -->
            <div class="preview-side" :class="{ 'is-winner': previewData.match.winner_side === 'side_a' }">
              <div class="side-players-list">
                <div class="player-row">
                  <el-avatar :size="24" :src="previewData.match.p1_avatar" class="info-avatar">
                    <el-icon><User /></el-icon>
                  </el-avatar>
                  <span class="info-name">{{ previewData.match.p1_name || '???' }}</span>
                </div>
                <div v-if="previewData.match.p1_partner_name" class="player-row">
                  <el-avatar :size="24" :src="previewData.match.p1_partner_avatar" class="info-avatar">
                    <el-icon><User /></el-icon>
                  </el-avatar>
                  <span class="info-name">{{ previewData.match.p1_partner_name }}</span>
                </div>
              </div>
              <div class="side-score" v-if="previewData.match.status === 'completed'">
                {{ previewData.match.score_a !== null ? previewData.match.score_a : '-' }}
              </div>
              <el-icon v-if="previewData.match.winner_side === 'side_a'" class="side-win-crown"><Check /></el-icon>
            </div>

            <div class="preview-vs-divider">VS</div>

            <!-- Side B -->
            <div class="preview-side" :class="{ 'is-winner': previewData.match.winner_side === 'side_b' }">
              <div class="side-players-list">
                <div class="player-row">
                  <el-avatar :size="24" :src="previewData.match.p2_avatar" class="info-avatar">
                    <el-icon><User /></el-icon>
                  </el-avatar>
                  <span class="info-name">{{ previewData.match.p2_name || '???' }}</span>
                </div>
                <div v-if="previewData.match.p2_partner_name" class="player-row">
                  <el-avatar :size="24" :src="previewData.match.p2_partner_avatar" class="info-avatar">
                    <el-icon><User /></el-icon>
                  </el-avatar>
                  <span class="info-name">{{ previewData.match.p2_partner_name }}</span>
                </div>
              </div>
              <div class="side-score" v-if="previewData.match.status === 'completed'">
                {{ previewData.match.score_b !== null ? previewData.match.score_b : '-' }}
              </div>
              <el-icon v-if="previewData.match.winner_side === 'side_b'" class="side-win-crown"><Check /></el-icon>
            </div>
          </div>

          <!-- Metadata details list -->
          <div class="preview-meta-details">
            <div class="meta-item" v-if="previewData.match.score_summary">
              <span class="meta-label">Tỉ số Set:</span>
              <div class="meta-value score-highlight">{{ previewData.match.score_summary }}</div>
            </div>
            
            <div class="meta-item">
              <span class="meta-label">Sân đấu:</span>
              <div class="meta-value">
                <el-icon><Location /></el-icon>
                <span>{{ previewData.match.court || 'Chưa gán sân' }}</span>
              </div>
            </div>

            <div class="meta-item" v-if="previewData.match.referee_name">
              <span class="meta-label">Trọng tài:</span>
              <div class="meta-value">
                <el-icon><User /></el-icon>
                <span>{{ previewData.match.referee_name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="matchDetailVisible"
      :title="selectedScheduleMatch ? `Chi tiết trận #${selectedScheduleMatch.match_no}` : 'Chi tiết trận đấu'"
      width="720px"
      destroy-on-close
      class="match-detail-dialog"
    >
      <div v-if="selectedScheduleMatch" class="match-detail-body">
        <div class="match-detail-head">
          <div>
            <span class="info-badge">Trận #{{ selectedScheduleMatch.match_no }}</span>
            <span class="info-stage">{{ selectedScheduleMatch.round_code || 'Vòng chưa đặt tên' }}</span>
          </div>
          <span class="m-v2-status" :class="getMatchStatusClass(selectedScheduleMatch)">
            {{ getMatchStatusLabel(selectedScheduleMatch) }}
          </span>
        </div>

        <div class="match-detail-teams">
          <div class="detail-team" :class="{ 'is-winner': selectedScheduleMatch.winner_side === 'side_a' }">
            <span class="team-label">Đội 1</span>
            <div class="detail-player-row" v-for="name in getScheduleSidePlayers(selectedScheduleMatch, 'a')" :key="`detail-a-${name}`">
              <el-avatar :size="28" class="info-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <strong>{{ name }}</strong>
            </div>
          </div>

          <div class="detail-vs">
            <span v-if="selectedScheduleMatch.status === 'completed'">
              {{ selectedScheduleMatch.score_summary || selectedScheduleMatch.score || `${selectedScheduleMatch.score_a ?? '-'} - ${selectedScheduleMatch.score_b ?? '-'}` }}
            </span>
            <span v-else>VS</span>
          </div>

          <div class="detail-team" :class="{ 'is-winner': selectedScheduleMatch.winner_side === 'side_b' }">
            <span class="team-label">Đội 2</span>
            <div class="detail-player-row" v-for="name in getScheduleSidePlayers(selectedScheduleMatch, 'b')" :key="`detail-b-${name}`">
              <el-avatar :size="28" class="info-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <strong>{{ name }}</strong>
            </div>
          </div>
        </div>

        <div class="detail-info-grid">
          <div class="detail-info-item">
            <span>Thời gian</span>
            <strong>{{ selectedScheduleMatch.start_time ? formatDateTime(selectedScheduleMatch.start_time) : 'Chưa xếp giờ' }}</strong>
          </div>
          <div class="detail-info-item">
            <span>Sân đấu</span>
            <strong>{{ selectedScheduleMatch.court || 'Chưa gán sân' }}</strong>
          </div>
          <div class="detail-info-item">
            <span>Trọng tài</span>
            <strong>{{ selectedScheduleMatch.referee_name || 'Chưa gán' }}</strong>
            <small v-if="selectedScheduleMatch.referee_phone">{{ selectedScheduleMatch.referee_phone }}</small>
          </div>
          <div class="detail-info-item">
            <span>Ghi chú</span>
            <strong>{{ selectedScheduleMatch.advance_note || selectedScheduleMatch.score || 'Chưa cập nhật' }}</strong>
          </div>
        </div>

        <div v-if="selectedScheduleMatch.live_stream_url || selectedScheduleMatch.video_url || selectedScheduleMatch.image_url" class="detail-media-actions">
          <button v-if="selectedScheduleMatch.live_stream_url" class="media-btn video" type="button" @click="openPreview('video', selectedScheduleMatch.live_stream_url, `Livestream Trận #${selectedScheduleMatch.match_no}`, selectedScheduleMatch)">
            Livestream
          </button>
          <button v-if="selectedScheduleMatch.video_url" class="media-btn video" type="button" @click="openPreview('video', selectedScheduleMatch.video_url, `Highlight Trận #${selectedScheduleMatch.match_no}`, selectedScheduleMatch)">
            Video
          </button>
          <button v-if="selectedScheduleMatch.image_url" class="media-btn image" type="button" @click="openPreview('image', selectedScheduleMatch.image_url, `Ảnh Trận #${selectedScheduleMatch.match_no}`, selectedScheduleMatch)">
            Ảnh trận đấu
          </button>
        </div>
      </div>
    </el-dialog>

    <div v-if="tournamentStore.loading && !tournament" class="neo-loading">
      <div class="spinner-ring"></div>
      <p>{{ t('tournaments.loadingData') }}</p>
    </div>
  </div>
</template>

<style scoped>
.neo-tournament-page { --bg-body: #f1f5f9; --bg-surface: #ffffff; --hero-bg: #0f172a; --hero-glow-1: #3b82f6; --hero-glow-2: #10b981; --text-primary: #0f172a; --text-secondary: #475569; --text-muted: #94a3b8; --border-light: #e2e8f0; --accent: #2563eb; --accent-hover: #1d4ed8; --radius-xl: 24px; --radius-lg: 16px; --radius-md: 12px; background: var(--bg-body); min-height: 100vh; font-family: 'Inter', -apple-system, sans-serif; color: var(--text-primary); padding-bottom: 5rem; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }
.text-center { text-align: center; }
.text-right { text-align: right; }
.text-green { color: #16a34a !important; font-weight: 700;}
.text-red { color: #dc2626 !important; font-weight: 700;}
.neo-hero { position: relative; background: var(--hero-bg); padding: 6rem 0 7rem; overflow: hidden; color: white; z-index: 1; }
.hero-glow { position: absolute; width: 400px; height: 400px; border-radius: 50%; filter: blur(100px); opacity: 0.3; z-index: -1; pointer-events: none; }
.glow-1 { top: -10%; right: 10%; background: var(--hero-glow-1); }
.glow-2 { bottom: -20%; left: 5%; background: var(--hero-glow-2); }
.hero-inner { position: relative; z-index: 2; }
.hero-meta-top { display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem; }
.neo-badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 99px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); backdrop-filter: blur(4px); }
.badge-dot { width: 6px; height: 6px; border-radius: 50%; background: #94a3b8; }
.neo-badge.open .badge-dot { background: #34d399; box-shadow: 0 0 8px #34d399;}
.neo-badge.ongoing .badge-dot { background: #38bdf8; box-shadow: 0 0 8px #38bdf8;}
.tour-type { font-size: 0.85rem; font-weight: 600; color: #cbd5e1; text-transform: uppercase; letter-spacing: 1px;}
.hero-title { font-size: clamp(2.5rem, 5vw, 4rem); font-weight: 800; line-height: 1.1; margin: 0 0 2rem; letter-spacing: -0.02em; }
.hero-details { display: inline-flex; align-items: center; gap: 2rem; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 1rem 1.5rem; border-radius: var(--radius-lg); backdrop-filter: blur(10px); }
.hd-item { display: flex; align-items: center; gap: 12px; }
.hd-item .el-icon { font-size: 1.5rem; color: #94a3b8; }
.hd-item div { display: flex; flex-direction: column; gap: 2px; }
.hd-lbl { font-size: 0.7rem; text-transform: uppercase; color: #94a3b8; font-weight: 600; letter-spacing: 0.05em;}
.hd-val { font-size: 0.95rem; font-weight: 600; color: white; }
.hd-divider { width: 1px; height: 30px; background: rgba(255,255,255,0.2); }
.main-overlap { position: relative; z-index: 10; margin-top: -4rem; }
.detail-wide-shell { width: min(100% - 48px, 1680px); max-width: none; }
.neo-grid { display: grid; grid-template-columns: minmax(0, 4fr) minmax(280px, 1fr); gap: 2rem; align-items: start; }
.neo-col-main { min-width: 0; width: 100%; }
.neo-tabs-container { background: var(--bg-surface); border-radius: 24px; padding: 2rem; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); min-height: 620px; overflow: hidden; }
:deep(.neo-tabs .el-tabs__nav-wrap::after) { display: none; }
:deep(.neo-tabs .el-tabs__nav) { background: var(--bg-body); padding: 4px; border-radius: 12px; }
:deep(.neo-tabs .el-tabs__item) { font-size: 0.85rem; font-weight: 700; color: var(--text-secondary); height: 40px; line-height: 40px; padding: 0 20px !important; border-radius: 8px; transition: 0.3s; }
:deep(.neo-tabs .el-tabs__item.is-active) { background: white; color: var(--text-primary); box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
:deep(.neo-tabs .el-tabs__active-bar) { display: none; }
:deep(.neo-tabs #tab-bracket) { order: 1; }
:deep(.neo-tabs #tab-schedule) { order: 2; }
:deep(.neo-tabs #tab-info) { order: 3; }
:deep(.neo-tabs #tab-standings) { order: 4; }
:deep(.neo-tabs #tab-participants) { order: 5; }
:deep(.neo-tabs #tab-media) { order: 6; }
.bento-layout { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1.5rem; }
.bento-box { background: var(--bg-body); border-radius: var(--radius-lg); padding: 1.5rem; border: 1px solid var(--border-light); }
.box-sm { display: flex; flex-direction: column; gap: 8px; }
.box-lg { grid-column: span 2; display: flex; flex-direction: column; gap: 1rem;}
.bento-icon { font-size: 1.5rem; color: var(--accent); margin-bottom: 4px;}
.bento-lbl { font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase;}
.bento-val { font-size: 1.25rem; font-weight: 800; color: var(--text-primary); }
.box-lg h3 { margin: 0; font-size: 1.2rem; font-weight: 800; color: var(--text-primary);}
.box-lg p { margin: 0; font-size: 0.95rem; line-height: 1.6; color: var(--text-secondary);}
.bento-highlight { background: white; padding: 1rem; border-radius: var(--radius-md); border: 1px solid var(--border-light); display: flex; flex-direction: column; gap: 4px; }
.bento-highlight strong { font-size: 0.85rem; color: var(--text-primary);}
.bento-highlight span { font-size: 0.9rem; color: var(--accent); font-weight: 600;}
.bracket-scroll-hint {
  display: none;
}
.bracket-viewport {
  margin-top: 10px;
  overflow-x: auto;
  padding: 20px 0;
  -webkit-overflow-scrolling: touch;
}
.bracket-viewport::-webkit-scrollbar {
  height: 6px;
}
.bracket-viewport::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 10px;
}
.bracket-viewport::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
}
.bracket-viewport::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.4);
}

.neo-bracket-tree {
  position: relative;
  min-width: max-content;
  padding: 0;
}

.group-stage-public-wrap {
  display: flex;
  flex-direction: column;
  gap: 28px;
  min-width: 980px;
}

.public-group-card {
  background: #ffffff;
  border: 1px solid #dbe5f0;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
}

.public-group-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
}

.public-group-head h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 900;
  color: #0f172a;
}

.public-group-head p {
  margin: 4px 0 0;
  font-size: 0.78rem;
  font-weight: 700;
  color: #64748b;
}

.public-group-rounds {
  display: flex;
  gap: 24px;
  padding: 20px;
  overflow-x: auto;
  background:
    linear-gradient(#eef4fb 1px, transparent 1px),
    linear-gradient(90deg, #eef4fb 1px, transparent 1px),
    #ffffff;
  background-size: 64px 64px;
}

.public-round-lane {
  min-width: 316px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.public-round-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: rgba(248, 250, 252, 0.92);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
}

.public-round-head span {
  font-size: 0.76rem;
  font-weight: 900;
  color: #0f172a;
  text-transform: uppercase;
}

.public-round-head small {
  font-size: 0.68rem;
  font-weight: 800;
  color: #64748b;
  white-space: nowrap;
}

.public-round-matches {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.group-match-card {
  background: white;
  border: 1px solid #dbe5f0;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.07);
}

.playoff-tree-after-groups {
  margin-top: 4px;
  flex-shrink: 0;
}

.bracket-lines {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: visible;
  z-index: 1;
}

.bracket-link {
  fill: none;
  stroke: #cbd5e1;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.round-sticky-header {
  margin-bottom: 24px;
  background: #f8fafc;
  padding: 12px 20px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tree-round-header {
  position: absolute;
  margin-bottom: 0;
  z-index: 3;
}

.round-title-group { display: flex; align-items: center; gap: 10px; }
.round-index { 
  background: var(--text-primary); 
  color: white; 
  width: 24px; 
  height: 24px; 
  border-radius: 6px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  font-size: 0.75rem; 
  font-weight: 800; 
}
.round-title { margin: 0; font-size: 0.95rem; font-weight: 800; color: var(--text-primary); text-transform: uppercase; letter-spacing: 0.05em; }
.round-count { font-size: 0.75rem; color: #64748b; font-weight: 600; }

.match-node-wrapper {
  position: absolute;
  display: flex;
  align-items: center;
  z-index: 2;
}

.match-node-wrapper.tree-node {
  align-items: stretch;
}

.match-node-v2 {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 2;
  display: flex;
  flex-direction: column;
}

.match-node-v2:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(15, 23, 42, 0.1); border-color: var(--accent-light); }

.m-v2-header { min-height: 42px; padding: 8px 12px; background: #f8fafc; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-shrink: 0; }
.m-v2-header-left { display: flex; align-items: center; gap: 8px; min-width: 0; }
.m-v2-no { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; font-weight: 700; color: #94a3b8; }
.m-v2-court { display: flex; align-items: center; gap: 4px; min-width: 0; max-width: 190px; font-size: 0.68rem; font-weight: 800; color: #64748b; background: #e2e8f0; padding: 3px 8px; border-radius: 7px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.m-v2-status { flex-shrink: 0; font-size: 0.62rem; font-weight: 900; text-transform: uppercase; padding: 4px 8px; border-radius: 8px; background: #f1f5f9; color: #64748b; }
.m-v2-status.is-done { background: #dcfce7; color: #16a34a; }
.m-v2-status.is-live { background: #fee2e2; color: #dc2626; animation: pulse 2s infinite; }
.m-v2-status.is-upcoming { background: #fef3c7; color: #92400e; }
.m-v2-status.is-advance { background: #e0f2fe; color: #0369a1; }
.m-v2-meta-strip { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 8px 12px 0; flex-shrink: 0; }
.match-meta-chip, .match-score-chip, .match-advance-chip { display: inline-flex; align-items: center; gap: 5px; min-width: 0; padding: 5px 8px; border-radius: 9px; background: #eff6ff; color: #2563eb; font-size: 0.68rem; font-weight: 900; }
.match-meta-chip { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.match-score-chip { background: #f0fdf4; color: #16a34a; font-family: 'JetBrains Mono', monospace; }
.match-advance-chip { background: #fff7ed; color: #c2410c; }

.schedule-panel { margin-top: 10px; }
.schedule-round-layout {
  display: grid;
  grid-template-columns: minmax(210px, 280px) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}
.schedule-round-list {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
}
.schedule-round-item {
  width: 100%;
  min-height: 64px;
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 0;
  border-bottom: 1px solid #e2e8f0;
  background: #ffffff;
  color: #0f172a;
  cursor: pointer;
  text-align: left;
  transition: background 0.2s ease, color 0.2s ease;
}
.schedule-round-item:last-child { border-bottom: 0; }
.schedule-round-item:hover { background: #f8fafc; }
.schedule-round-item.active {
  background: #eff6ff;
  color: var(--accent);
}
.schedule-round-item strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.95rem;
}
.round-arrow {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: #f1f5f9;
  color: #16a34a;
  font-size: 1.35rem;
  line-height: 1;
  font-weight: 900;
}
.schedule-round-item.active .round-arrow {
  background: #dbeafe;
  color: var(--accent);
}
.round-count {
  min-width: 34px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #f1f5f9;
  color: #0f172a;
  font-size: 0.82rem;
  font-weight: 900;
}
.schedule-round-content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.schedule-round-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}
.schedule-round-heading span,
.schedule-round-heading small {
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
}
.schedule-round-heading h3 {
  margin: 3px 0 0;
  color: #0f172a;
  font-size: 1.05rem;
  font-weight: 900;
}
.schedule-list { display: flex; flex-direction: column; gap: 12px; }
.schedule-row {
  display: grid;
  grid-template-columns: minmax(150px, 190px) minmax(0, 1fr);
  gap: 16px;
  padding: 16px;
  background: white;
  border: 1px solid #e2e8f0;
  border-left: 4px solid #cbd5e1;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
.schedule-row:hover,
.schedule-row:focus-visible {
  transform: translateY(-2px);
  border-color: #bfdbfe;
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.12);
  outline: none;
}
.schedule-row.is-done { border-left-color: #22c55e; }
.schedule-row.is-live { border-left-color: #ef4444; }
.schedule-row.is-upcoming { border-left-color: #f59e0b; }
.schedule-row.is-advance { border-left-color: #0ea5e9; }
.schedule-time { display: flex; flex-direction: column; gap: 6px; color: #475569; }
.schedule-time strong { color: #0f172a; font-size: 0.9rem; }
.schedule-time span { font-size: 0.8rem; font-weight: 700; }
.schedule-match { min-width: 0; display: flex; flex-direction: column; gap: 12px; }
.schedule-title { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.schedule-title > span:first-child { color: #94a3b8; font-weight: 800; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; }
.schedule-title strong { color: #0f172a; font-size: 0.9rem; }
.schedule-sides { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: center; gap: 12px; }
.schedule-side { display: flex; flex-direction: column; gap: 6px; min-width: 0; padding: 10px 12px; border-radius: 10px; background: #f8fafc; border: 1px solid #eef2f7; }
.schedule-player-name { font-size: 0.92rem; line-height: 1.25; font-weight: 850; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.schedule-side.is-win { background: #f0fdf4; border-color: #bbf7d0; }
.schedule-side.is-win .schedule-player-name { color: #15803d; }
.schedule-score { min-width: 48px; text-align: center; font-weight: 900; color: #2563eb; font-family: 'JetBrains Mono', monospace; }
.schedule-meta { font-size: 0.8rem; color: #64748b; }

.m-v2-body { padding: 8px 0 10px; display: flex; flex-direction: column; min-height: 0; flex: 1; }
.m-v2-player { display: flex; justify-content: space-between; align-items: center; min-height: 50px; padding: 7px 12px; transition: all 0.2s; position: relative; }
.m-v2-player.is-win { background: #f0fdf4; }
.p-info-wrapper { display: flex; align-items: center; gap: 10px; flex: 1; overflow: hidden; }
.p-avatar-mini { border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.p-info { display: flex; align-items: center; gap: 6px; overflow: hidden; }
.p-name-link { font-weight: 700; color: #1e293b; text-decoration: none; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.p-name-link.no-link { pointer-events: none; }
.p-win-icon { color: #22c55e; font-size: 0.9rem; flex-shrink: 0; }
.p-partner { font-size: 0.7rem; color: #64748b; font-style: italic; white-space: nowrap; }
.p-score { font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 800; color: #0f172a; min-width: 24px; text-align: center; }
.m-v2-divider { height: 1px; background: #f1f5f9; margin: 0 12px; flex-shrink: 0; }

.empty-state { text-align: center; padding: 4rem 0; color: var(--text-muted); }
.es-icon { font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;}
.player-stack-v2 { display: flex; flex-direction: column; gap: 5px; flex: 1; min-width: 0; overflow: hidden; padding: 2px 0; }
.p-mini-box { display: flex; align-items: center; gap: 8px; min-width: 0; overflow: hidden; }
.p-name-link { font-size: 0.84rem; font-weight: 800; color: var(--navy); text-decoration: none; transition: 0.2s; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 190px; }
.p-name-link:hover { color: var(--accent); }
.p-name-link.no-link { pointer-events: none; color: #64748b; }

.teams-display-premium { display: flex; align-items: center; gap: 16px; }
.player-item-mini { display: flex; align-items: center; gap: 10px; }
.player-meta { display: flex; flex-direction: column; line-height: 1.2; }
.player-meta .name { font-weight: 700; color: var(--navy); text-decoration: none; font-size: 0.9rem; }
.player-meta .name:hover { color: var(--accent); }
.team-divider { font-weight: 900; color: #cbd5e1; font-size: 1.2rem; margin: 0 4px; }
.m-v2-footer { margin: auto 12px 0; padding-top: 8px; border-top: 1px solid #f1f5f9; display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 8px; flex-shrink: 0; }
.m-referee-badge { display: flex; align-items: center; gap: 6px; min-width: 0; padding: 5px 8px; border-radius: 10px; background: #f8fafc; color: #475569; font-size: 0.7rem; font-weight: 800; }
.referee-icon { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 999px; background: #e0f2fe; color: #0369a1; font-size: 0.65rem; flex-shrink: 0; }
.referee-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.referee-phone { color: #94a3b8; flex-shrink: 0; }
.m-referee { font-size: 0.75rem; color: #64748b; font-weight: 600; display: flex; align-items: center; gap: 4px; }
.m-media-actions { display: flex; gap: 6px; flex-wrap: nowrap; justify-content: flex-end; }
.media-icon-btn { width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center; border-radius: 9px; border: 1px solid transparent; cursor: pointer; transition: all 0.2s ease; }
.media-btn { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; text-decoration: none; transition: all 0.2s; }
.media-btn.video { background: #fef2f2; color: #dc2626; border: 1px solid #fee2e2; }
.media-btn.video:hover { background: #dc2626; color: white; }
.media-btn.image { background: #eff6ff; color: #2563eb; border: 1px solid #dbeafe; }
.media-btn.image:hover { background: #2563eb; color: white; }
.neo-standings-container { margin-top: 1.5rem; }
.standings-list { display: flex; flex-direction: column; gap: 2rem; }
.premium-group-card { background: white; border-radius: 20px; border: 1px solid #f1f5f9; padding: 24px; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.02); }
.pg-header { display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem; }
.pg-accent { width: 4px; height: 20px; background: var(--hero-glow-2); border-radius: 4px; }
.pg-title { font-size: 1.1rem; font-weight: 800; color: var(--text-primary); margin: 0; text-transform: uppercase; letter-spacing: 0.05em; }
.pg-table-wrap { overflow-x: auto; border-radius: 12px; border: 1px solid #f1f5f9; -webkit-overflow-scrolling: touch; }
.pg-table { width: 100%; border-collapse: collapse; min-width: 480px; }
.pg-table th { background: #f8fafc; padding: 12px 16px; font-size: 0.7rem; font-weight: 800; color: #64748b; text-transform: uppercase; border-bottom: 2px solid #f1f5f9; text-align: left; }
.pg-table td { padding: 14px 16px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.pg-table tr:last-child td { border-bottom: none; }
.pg-table tr.is-qualified { background: #f0fdf440; }
.col-rank { width: 50px; text-align: center; }
.rank-badge { width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; font-weight: 800; font-size: 0.75rem; background: #f1f5f9; color: #64748b; }
.rank-1 { background: #fef3c7; color: #92400e; box-shadow: 0 0 0 2px #fde68a; }
.rank-2 { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
.player-stack-premium { display: flex; flex-direction: column; gap: 8px; }
.player-unit-row { display: flex; align-items: center; gap: 10px; }
.unit-avatar { border: 1.5px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }
.main-player, .partner-name { font-weight: 700; color: var(--navy); text-decoration: none; font-size: 0.9rem; }
.main-player:hover, .partner-name:hover { color: var(--accent); }
.stat-cell { font-weight: 600; color: #64748b; font-size: 0.85rem; }
.stat-win { color: #16a34a; }
.stat-loss { color: #dc2626; }
.diff-cell { font-weight: 700; font-size: 0.85rem; }
.diff-cell span.pos { color: #16a34a; }
.diff-cell span.neg { color: #dc2626; }
.pts-cell { color: var(--accent); font-size: 1.05rem; }
.neo-col-sidebar { position: relative; }
.sticky { position: sticky; top: 24px; }
.neo-action-card { background: var(--bg-surface); border-radius: var(--radius-xl); padding: 2rem; box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.1); border: 1px solid var(--border-light); }
.ac-header { margin-bottom: 2rem; }
.ac-header h2 { font-size: 1.4rem; font-weight: 800; margin: 0 0 8px; color: var(--text-primary);}
.price-tag { font-size: 2rem; font-weight: 800; color: var(--accent); letter-spacing: -0.02em;}
.ac-progress-section { margin-bottom: 2rem; }
.prog-labels { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 8px;}
.pl-title { font-size: 0.85rem; font-weight: 600; color: var(--text-muted);}
.pl-count { font-size: 1.1rem; font-weight: 800; color: var(--text-primary);}
.prog-track { height: 10px; background: var(--bg-body); border-radius: 99px; overflow: hidden; }
.prog-fill { height: 100%; background: linear-gradient(90deg, var(--hero-glow-1), var(--hero-glow-2)); border-radius: 99px; transition: width 0.8s ease;}
.prog-hint { font-size: 0.8rem; color: #dc2626; font-weight: 600; margin: 8px 0 0; text-align: center;}
.neo-btn-primary { width: 100%; padding: 1.25rem; border-radius: var(--radius-md); border: none; background: var(--text-primary); color: white; font-size: 1rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.2s; }
.neo-btn-primary:hover:not(.is-disabled) { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(15,23,42,0.2); }
.neo-btn-primary.is-disabled { background: var(--bg-body); color: var(--text-muted); cursor: not-allowed; border: 1px solid var(--border-light);}
.ac-status-msg { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 1rem; background: var(--bg-body); border-radius: var(--radius-md); color: var(--text-muted); font-size: 0.85rem; font-weight: 600; }
.neo-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 60vh; }
.spinner-ring { width: 48px; height: 48px; border: 4px solid var(--border-light); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
  100% { transform: scale(1); opacity: 1; }
}
@media (max-width: 1024px) { 
  .neo-grid { grid-template-columns: 1fr; gap: 1.5rem; } 
  .neo-col-sidebar { order: 2; } 
  .neo-action-card { box-shadow: 0 10px 30px rgba(0,0,0,0.05); } 
  .sticky { position: relative; top: 0; }
  .main-overlap { margin-top: -2rem; }
}
@media (max-width: 768px) { 
  .container { padding: 0 1rem; }
  .neo-hero { padding: 3.5rem 0 4.5rem; }
  .hero-title { font-size: 1.8rem; margin-bottom: 1.25rem; word-break: break-word; } 
  .hero-details { 
    flex-direction: column; 
    align-items: flex-start; 
    gap: 0.75rem; 
    width: 100%;
    padding: 1rem;
    border-radius: var(--radius-md);
  } 
  .hd-divider { display: none; } 
  .bento-layout { grid-template-columns: 1fr; gap: 0.75rem; } 
  .box-lg { grid-column: auto; } 
  .neo-tabs-container { padding: 1rem; border-radius: var(--radius-lg); min-height: auto; max-width: 100vw; overflow: hidden; }
  .main-overlap { margin-top: -1.5rem; }
  .registered-highlight {
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    border: 1px solid #bbf7d0 !important;
  }
  .registered-highlight .bento-icon { color: #22c55e; }
  .registered-highlight .bento-val { color: #15803d; }
  
  .viewing-highlight {
    border: 1px solid var(--accent-light) !important;
  }
  :deep(.neo-tabs .el-tabs__header) { margin-bottom: 1rem; }
  :deep(.neo-tabs .el-tabs__nav-wrap) { overflow-x: auto !important; overflow-y: hidden !important; -webkit-overflow-scrolling: touch; scrollbar-width: none; -ms-overflow-style: none; }
  :deep(.neo-tabs .el-tabs__nav-wrap::-webkit-scrollbar) { display: none !important; }
  :deep(.neo-tabs .el-tabs__nav-wrap.is-scrollable) { padding: 0 !important; }
  :deep(.neo-tabs .el-tabs__nav-prev), :deep(.neo-tabs .el-tabs__nav-next) { display: none !important; }
  :deep(.neo-tabs .el-tabs__nav-scroll) { overflow: visible !important; }
  :deep(.neo-tabs .el-tabs__nav) { display: flex; flex-wrap: nowrap; width: max-content; }
  :deep(.neo-tabs .el-tabs__item) { flex: none !important; text-align: center; padding: 0 16px !important; min-width: max-content; font-size: 0.85rem; }
  .neo-table th, .neo-table td { padding: 8px 6px; font-size: 0.75rem; }
  .sg-title { font-size: 0.95rem; }
  .matches-vertical-grid { grid-template-columns: 1fr; gap: 1rem; }
  .round-sticky-header { padding: 10px 15px; }
  .round-title { font-size: 0.9rem; }
  .m-v2-player { padding: 8px; }
  .p-name { font-size: 0.85rem; }
  .p-score { font-size: 1rem; }
  .schedule-row { grid-template-columns: 1fr; gap: 12px; padding: 12px; }
  .schedule-sides { grid-template-columns: 1fr; }
  .schedule-score { text-align: left; }
  .ac-progress-section { margin-bottom: 1.5rem; }
  
  /* Responsive Bracket draw & filter on mobile */
  .category-filter-wrap {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    padding: 10px;
    overflow: hidden;
  }
  .category-filter-wrap .filter-label {
    text-align: center;
  }
  .category-filter-wrap :deep(.el-radio-group) {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 4px;
    width: 100%;
  }
  .category-filter-wrap :deep(.el-radio-button) {
    flex-shrink: 0;
  }
  .category-filter-wrap :deep(.el-radio-group::-webkit-scrollbar) { display: none; }
  .bracket-scroll-hint {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #eff6ff;
    color: var(--accent);
    padding: 6px 12px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 700;
    margin-bottom: 12px;
    border: 1px solid #dbeafe;
    animation: pulseHint 2s infinite ease-in-out;
  }
  @keyframes pulseHint {
    0%, 100% { opacity: 0.9; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.02); }
  }
  .bracket-viewport {
    scroll-snap-type: x mandatory;
  }
  .neo-bracket-tree {
    transform-origin: top left;
  }
}
@media (max-width: 480px) {
  .hero-title { font-size: 1.5rem; }
  .neo-hero { padding: 2.5rem 0 4rem; }
  .neo-badge { font-size: 0.65rem; padding: 3px 8px; }
  .tour-type { font-size: 0.7rem; }
  .main-overlap { margin-top: 0; }
  .neo-tabs-container { border-radius: 0; margin-left: -1rem; margin-right: -1rem; width: calc(100% + 2rem); max-width: 100vw; overflow: hidden; }
  .bento-box { padding: 0.85rem; }
  .bento-val { font-size: 1rem; }
  .bento-icon { font-size: 1.25rem; }
  .neo-action-card { padding: 1.25rem; border-radius: var(--radius-lg); }
  .price-tag { font-size: 1.25rem; }
  .ac-header h2 { font-size: 1.1rem; }
  .ac-header { margin-bottom: 1.25rem; }
  .ac-progress-section { margin-bottom: 1.5rem; }
}

/* Participants Styles */
.neo-participants-container { margin-top: 1.5rem; }
.idx-badge { width: 24px; height: 24px; background: #f1f5f9; color: #64748b; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; font-weight: 800; font-size: 0.7rem; }
.player-info-cell { display: flex; flex-direction: column; gap: 4px; }
.player-main { display: flex; align-items: center; gap: 8px; }
.player-main .name { font-weight: 700; color: var(--text-primary); text-decoration: none; font-size: 0.95rem; }
.player-main .name:hover { color: var(--accent); text-decoration: underline; }
.skill-tag { font-size: 0.65rem; background: #eff6ff; color: #3b82f6; padding: 2px 6px; border-radius: 4px; font-weight: 700; }
.player-partner { font-size: 0.8rem; color: #64748b; display: flex; gap: 4px; }
.partner-label { font-weight: 500; }
.partner-name { font-weight: 600; color: #334155; }
.type-tag { font-size: 0.7rem; font-weight: 700; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; }
.type-tag.team { background: #fff7ed; color: #f97316; }
.type-tag.player { background: #f1f5f9; color: #475569; }
.time-cell { font-size: 0.8rem; color: #64748b; font-weight: 500; font-family: monospace; }
.shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
.category-filter-wrap {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 16px 18px;
  background:
    linear-gradient(135deg, rgba(37, 99, 235, 0.10), rgba(16, 185, 129, 0.08)),
    #ffffff;
  border-radius: 16px;
  border: 1px solid #bfdbfe;
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.10), inset 0 1px 0 rgba(255,255,255,0.9);
  position: relative;
  overflow: hidden;
}
.category-filter-wrap::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 5px;
  background: linear-gradient(180deg, #2563eb, #10b981);
}
.category-filter-wrap::after {
  content: '';
  position: absolute;
  right: 18px;
  top: -34px;
  width: 120px;
  height: 120px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  pointer-events: none;
}
.filter-label {
  position: relative;
  z-index: 1;
  min-width: 180px;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  column-gap: 12px;
  align-items: center;
  color: var(--text-primary);
}
.filter-icon {
  grid-row: 1 / span 2;
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background:
    linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(16, 185, 129, 0.90));
  box-shadow: 0 10px 18px rgba(37, 99, 235, 0.25);
  color: #ffffff;
  font-size: 1.1rem;
}
.filter-kicker {
  font-size: 0.68rem;
  font-weight: 900;
  color: #64748b;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.filter-label strong {
  font-size: 0.98rem;
  font-weight: 900;
  color: #0f172a;
}

.category-filter-wrap :deep(.el-radio-group) {
  position: relative;
  z-index: 1;
  display: inline-flex;
  gap: 8px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 14px;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(8px);
}

.category-filter-wrap :deep(.el-radio-button__inner) {
  min-width: 92px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0 !important;
  border-radius: 10px !important;
  background: transparent !important;
  color: #475569 !important;
  font-weight: 900;
  box-shadow: none !important;
  transition: transform 0.2s ease, background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.category-filter-wrap :deep(.el-radio-button__inner:hover) {
  color: var(--accent) !important;
  background: #eff6ff !important;
  transform: translateY(-1px);
}

.category-filter-wrap :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
  color: white !important;
  box-shadow: 0 10px 18px rgba(37, 99, 235, 0.28) !important;
}

.category-filter-wrap :deep(.el-radio-button:first-child .el-radio-button__inner),
.category-filter-wrap :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 10px !important;
}

@media (max-width: 768px) {
  .category-filter-wrap {
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
    padding: 14px;
  }
  .filter-label {
    min-width: 0;
  }
  .category-filter-wrap :deep(.el-radio-group) {
    width: 100%;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    -webkit-overflow-scrolling: touch;
  }
  .category-filter-wrap :deep(.el-radio-group::-webkit-scrollbar) {
    display: none;
  }
  .category-filter-wrap :deep(.el-radio-button) {
    flex-shrink: 0;
  }
  .category-filter-wrap :deep(.el-radio-button__inner) {
    min-width: 108px;
  }
}

.standings-wrap, .bracket-viewport {
  margin-top: 10px;
}

/* Match Node Footer */
.m-v2-footer { margin: auto 12px 0; padding-top: 8px; border-top: 1px solid #f1f5f9; display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 8px; flex-shrink: 0; }
.score-container-v2 { display: flex; align-items: center; gap: 4px; margin-left: auto; }
.set-scores-wrap { display: flex; gap: 3px; }
.set-score-pill { display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; font-size: 0.75rem; font-weight: 800; color: #475569; background: #f1f5f9; border-radius: 4px; border: 1px solid #e2e8f0; transition: all 0.2s ease; }
.set-score-pill.is-set-win { background: #22c55e; color: white; border-color: #22c55e; }
.m-referee-badge { display: flex; align-items: center; gap: 6px; min-width: 0; padding: 5px 8px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; font-size: 0.7rem; font-weight: 800; color: #475569; }
.referee-icon { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 999px; background: #e0f2fe; color: #0369a1; font-size: 0.65rem; flex-shrink: 0; }
.referee-name { color: #0f172a; font-weight: 800; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.m-media-actions { display: flex; gap: 6px; margin-top: 0; flex-wrap: nowrap; justify-content: flex-end; }
.media-btn { border-radius: 8px !important; font-weight: 700 !important; font-size: 0.75rem !important; padding: 6px 12px !important; height: 28px !important; transition: all 0.2s ease !important; }
.media-icon-btn { width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center; border-radius: 9px; border: 1px solid transparent; cursor: pointer; transition: all 0.2s ease; }
.live-btn { background: #fef3c7 !important; color: #b45309 !important; border-color: #fde68a !important; }
.live-btn:hover { background: #f59e0b !important; color: white !important; border-color: #f59e0b !important; }
.video-btn { background: #fef2f2 !important; color: #ef4444 !important; border-color: #fee2e2 !important; }
.video-btn:hover { background: #ef4444 !important; color: white !important; border-color: #ef4444 !important; }
.image-btn { background: #eff6ff !important; color: #3b82f6 !important; border-color: #dbeafe !important; }
.image-btn:hover { background: #3b82f6 !important; color: white !important; border-color: #3b82f6 !important; }

/* Media Dialog Split Layout */
.media-preview-dialog-v2 { border-radius: 16px !important; overflow: hidden; }
.media-preview-dialog-v2 :deep(.el-dialog__header) { padding: 20px 24px 10px !important; border-bottom: 1px solid #e2e8f0; }
.media-preview-dialog-v2 :deep(.el-dialog__title) { font-weight: 800; font-size: 1.2rem; color: #0f172a; }
.media-preview-dialog-v2 :deep(.el-dialog__body) { padding: 24px !important; }
.preview-layout { display: grid; grid-template-columns: 2.2fr 1fr; gap: 24px; }
@media (max-width: 992px) { .preview-layout { grid-template-columns: 1fr; } }
.preview-media-col { background: #0f172a; border-radius: 12px; overflow: hidden; display: flex; align-items: center; justify-content: center; min-height: 380px; box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.6); border: 1px solid #1e293b; }
.video-container, .image-container { width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; }
.preview-video { width: 100%; aspect-ratio: 16/9; border: none; max-height: 480px; }
.preview-image { width: 100%; max-height: 480px; object-fit: contain; }
.preview-info-col { display: flex; flex-direction: column; gap: 20px; background: #f8fafc; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; }
.info-header { display: flex; align-items: center; justify-content: space-between; }
.info-badge { background: #eff6ff; color: #2563eb; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; }
.info-stage { background: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }
.info-title { font-size: 1rem; font-weight: 800; color: #0f172a; margin: 5px 0 0; text-transform: uppercase; letter-spacing: 0.05em; }
.preview-match-card { display: flex; flex-direction: column; gap: 12px; background: white; border-radius: 12px; padding: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
.preview-side { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-radius: 8px; background: #f8fafc; transition: all 0.2s ease; border: 1px solid transparent; }
.preview-side.is-winner { background: #f0fdf4; border: 1px solid #bbf7d0; }
.side-players-list { display: flex; flex-direction: column; gap: 6px; }
.player-row { display: flex; align-items: center; gap: 8px; }
.info-avatar { border: 1px solid #e2e8f0; }
.info-name { font-size: 0.85rem; font-weight: 700; color: #334155; }
.preview-side.is-winner .info-name { color: #15803d; }
.side-score { font-size: 1.25rem; font-weight: 800; color: #64748b; margin-left: auto; padding-right: 8px; }
.preview-side.is-winner .side-score { color: #16a34a; }
.side-win-crown { color: #16a34a; font-weight: 900; font-size: 1.1rem; }
.preview-vs-divider { text-align: center; font-weight: 800; font-size: 0.75rem; color: #94a3b8; position: relative; }
.preview-vs-divider::before, .preview-vs-divider::after { content: ''; position: absolute; top: 50%; width: 40%; height: 1px; background: #e2e8f0; }
.preview-vs-divider::before { left: 0; }
.preview-vs-divider::after { right: 0; }
.preview-meta-details { display: flex; flex-direction: column; gap: 12px; border-top: 1px solid #e2e8f0; padding-top: 16px; }
.meta-item { display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; }
.meta-label { font-weight: 600; color: #64748b; }
.meta-value { font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 6px; }
.meta-value.score-highlight { background: #1e293b; color: white; padding: 3px 8px; border-radius: 6px; font-family: monospace; font-size: 0.8rem; }

.match-detail-dialog :deep(.el-dialog) { border-radius: 18px; overflow: hidden; }
.match-detail-dialog :deep(.el-dialog__header) { padding: 22px 24px 12px; border-bottom: 1px solid #e2e8f0; }
.match-detail-dialog :deep(.el-dialog__title) { font-size: 1.15rem; font-weight: 900; color: #0f172a; }
.match-detail-dialog :deep(.el-dialog__body) { padding: 24px; }
.match-detail-body { display: flex; flex-direction: column; gap: 18px; }
.match-detail-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.match-detail-head > div { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.match-detail-teams {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  gap: 14px;
  align-items: stretch;
}
.detail-team {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #f8fafc;
}
.detail-team.is-winner { background: #f0fdf4; border-color: #bbf7d0; }
.team-label { font-size: 0.72rem; font-weight: 900; color: #64748b; text-transform: uppercase; }
.detail-player-row { display: flex; align-items: center; gap: 10px; min-width: 0; }
.detail-player-row strong { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #0f172a; font-size: 0.95rem; }
.detail-team.is-winner .detail-player-row strong { color: #15803d; }
.detail-vs {
  min-width: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2563eb;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 900;
}
.detail-vs span {
  padding: 8px 10px;
  border-radius: 10px;
  background: #eff6ff;
}
.detail-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.detail-info-item {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 13px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #ffffff;
}
.detail-info-item span { font-size: 0.72rem; font-weight: 900; color: #64748b; text-transform: uppercase; }
.detail-info-item strong { min-width: 0; color: #0f172a; font-size: 0.9rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.detail-info-item small { color: #64748b; font-weight: 700; }
.detail-media-actions { display: flex; gap: 10px; flex-wrap: wrap; padding-top: 2px; }
@media (max-width: 768px) {
  .match-detail-teams,
  .detail-info-grid { grid-template-columns: 1fr; }
  .detail-vs { min-height: 40px; }
}

/* Media Gallery */
.media-gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; padding: 10px 0; }
.media-item-card { background: white; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; transition: transform 0.3s; }
.media-item-card:hover { transform: translateY(-5px); }
.media-preview { position: relative; height: 180px; background: #0f172a; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.media-preview img { width: 100%; height: 100%; object-fit: cover; }
.video-placeholder { color: #94a3b8; display: flex; flex-direction: column; align-items: center; gap: 10px; }
.video-placeholder .el-icon { font-size: 2.5rem; }
.media-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s; }
.media-item-card:hover .media-overlay { opacity: 1; }
.play-btn { width: 50px; height: 50px; background: white; color: #dc2626; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; text-decoration: none; }
.media-info { padding: 15px; }
.m-match-label { margin: 0 0 5px; font-size: 1rem; font-weight: 700; color: #1e293b; }
.m-round-info { margin: 0; font-size: 0.8rem; color: #64748b; font-weight: 500; }

/* Premium Sticky Mobile Registration Bar */
.mobile-sticky-action-bar {
  display: none;
}

@media (max-width: 768px) {
  .schedule-round-layout {
    grid-template-columns: 1fr;
  }
  .schedule-round-list {
    display: flex;
    overflow-x: auto;
    border-radius: 12px;
    -webkit-overflow-scrolling: touch;
  }
  .schedule-round-item {
    min-width: 220px;
    border-bottom: 0;
    border-right: 1px solid #e2e8f0;
  }
  .schedule-round-item:last-child { border-right: 0; }
  .mobile-sticky-action-bar {
    display: block;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-top: 1px solid rgba(226, 232, 240, 0.8);
    box-shadow: 0 -10px 30px rgba(15, 23, 42, 0.08);
    padding: 12px 24px;
    z-index: 999;
    padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
  }
  
  .ms-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 600px;
    margin: 0 auto;
    gap: 16px;
  }
  
  .ms-info {
    display: flex;
    flex-direction: column;
  }
  
  .ms-label {
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.05em;
  }
  
  .ms-price {
    font-size: 1.1rem;
    color: var(--accent);
    font-weight: 800;
  }
  
  .ms-btn-wrap {
    flex: 1;
    max-width: 200px;
  }
  
  .ms-btn {
    width: 100%;
    padding: 10px 16px !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    border-radius: var(--radius-md) !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
  }
  
  .ms-status-text {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-align: center;
    padding: 8px 12px;
    background: #f1f5f9;
    border-radius: var(--radius-md);
  }
  
  .neo-tournament-page {
    padding-bottom: calc(7rem + env(safe-area-inset-bottom, 0px)) !important;
  }
}
</style>
