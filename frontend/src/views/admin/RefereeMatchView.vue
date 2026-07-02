<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiClient from '../../services/apiClient'
import { Location, User, Cellphone, ArrowLeft, VideoPlay, Timer, RefreshRight, Check, Back, Plus } from '@element-plus/icons-vue'
import coinYesUrl from '../../assets/images/coin_yes.png'
import coinNoUrl from '../../assets/images/coin_no.png'

const route = useRoute()
const router = useRouter()
const matchId = route.params.id

// --- STATE MANAGEMENT ---
const isLoading = ref(true)
const saving = ref(false)
const matchData = ref(null)
const courts = ref([])
const activeStep = ref(1) // 1: Setup, 2: Pre-match, 3: Live Scoreboard

// --- STEP 1: SETUP ---
const setupForm = ref({
  court_id: null,
  referee_name: '',
  referee_phone: ''
})

// --- STEP 2: PRE-MATCH ---
const coinFlipped = ref(false)
const coinFlipping = ref(false)
const coinResult = ref(null) // 'heads' (Sấp / A giao) or 'tails' (Ngửa / B giao)
const coinWinner = ref('')   // Tên người thắng bốc thăm
const warmUpMinutes = ref(5)
const warmUpSeconds = ref(0)
const timerInterval = ref(null)
const isTimerRunning = ref(false)
const initialWarmUpTime = ref(300) // 5 minutes in seconds
const serverSide = ref('side_a') // 'side_a' or 'side_b'
const serverPosition = ref('left') // 'left' or 'right' so với ghế trọng tài

// --- STEP 3: LIVE SCOREBOARD ---
// Cấu trúc điểm Tennis: 0 -> 15 -> 30 -> 40 -> Deuce -> AD
const p1Points = ref(0) // 0, 1, 2, 3 (tương đương 0, 15, 30, 40), 4 (AD)
const p2Points = ref(0)
const setsScore = ref([
  { side_a: 0, side_b: 0 }, // Set 1
  { side_a: null, side_b: null }, // Set 2
  { side_a: null, side_b: null }  // Set 3
])
const tieBreaksScore = ref([
  { side_a: null, side_b: null }, // Tiebreak Set 1
  { side_a: null, side_b: null }, // Tiebreak Set 2
  { side_a: null, side_b: null }  // Tiebreak Set 3
])
const currentSetIndex = ref(0)
const scoreHistory = ref([]) // Mảng lưu lịch sử điểm để thực hiện UNDO

// Computed Helpers
const p1DisplayPoints = computed(() => {
  if (isDeuce.value) return '40'
  if (p1Points.value === 4) return 'AD'
  const pointsMap = { 0: '0', 1: '15', 2: '30', 3: '40' }
  return pointsMap[p1Points.value] || '0'
})

const p2DisplayPoints = computed(() => {
  if (isDeuce.value) return '40'
  if (p2Points.value === 4) return 'AD'
  const pointsMap = { 0: '0', 1: '15', 2: '30', 3: '40' }
  return pointsMap[p2Points.value] || '0'
})

const isDeuce = computed(() => {
  return p1Points.value === 3 && p2Points.value === 3
})

const currentServerName = computed(() => {
  if (!matchData.value) return 'Chưa rõ'
  return serverSide.value === 'side_a' 
    ? (matchData.value.p1_name || 'Bên A') 
    : (matchData.value.p2_name || 'Bên B')
})

const isTieBreak = computed(() => {
  const set = setsScore.value[currentSetIndex.value]
  if (!set) return false
  return set.side_a === 6 && set.side_b === 6
})

// --- ACTIONS & METHODS ---

const fetchMatchDetails = async () => {
  isLoading.value = true
  try {
    const res = await apiClient.get(`/api/tournaments/matches/${matchId}`)
    matchData.value = res
    if (res.court_id) setupForm.value.court_id = res.court_id
    setupForm.value.referee_name = res.referee_name || ''
    setupForm.value.referee_phone = res.referee_phone || ''
    
    if (res) {
      // Phục hồi điểm các set từ database
      const parsedSets = []
      const parsedTieBreaks = []
      
      // Set 1
      parsedSets.push({ 
        side_a: res.set1_a !== undefined && res.set1_a !== null ? res.set1_a : null, 
        side_b: res.set1_b !== undefined && res.set1_b !== null ? res.set1_b : null 
      })
      parsedTieBreaks.push({ 
        side_a: res.tie_break_1_a !== undefined && res.tie_break_1_a !== null ? res.tie_break_1_a : null, 
        side_b: res.tie_break_1_b !== undefined && res.tie_break_1_b !== null ? res.tie_break_1_b : null 
      })
      
      // Set 2
      if (res.set2_a !== null || res.set2_b !== null || res.best_of_sets > 1) {
        parsedSets.push({ 
          side_a: res.set2_a !== undefined && res.set2_a !== null ? res.set2_a : null, 
          side_b: res.set2_b !== undefined && res.set2_b !== null ? res.set2_b : null 
        })
        parsedTieBreaks.push({ 
          side_a: res.tie_break_2_a !== undefined && res.tie_break_2_a !== null ? res.tie_break_2_a : null, 
          side_b: res.tie_break_2_b !== undefined && res.tie_break_2_b !== null ? res.tie_break_2_b : null 
        })
      }
      
      // Set 3
      if (res.set3_a !== null || res.set3_b !== null || res.best_of_sets > 2) {
        parsedSets.push({ 
          side_a: res.set3_a !== undefined && res.set3_a !== null ? res.set3_a : null, 
          side_b: res.set3_b !== undefined && res.set3_b !== null ? res.set3_b : null 
        })
        parsedTieBreaks.push({ 
          side_a: res.tie_break_3_a !== undefined && res.tie_break_3_a !== null ? res.tie_break_3_a : null, 
          side_b: res.tie_break_3_b !== undefined && res.tie_break_3_b !== null ? res.tie_break_3_b : null 
        })
      }
      
      // Đảm bảo có ít nhất Set 1 được khởi tạo là 0-0 nếu chưa có điểm nào
      if (parsedSets[0].side_a === null) {
        parsedSets[0].side_a = 0
        parsedSets[0].side_b = 0
      }
      
      setsScore.value = parsedSets
      tieBreaksScore.value = parsedTieBreaks
      
      // Tìm set đang kích hoạt (set cuối cùng có giá trị không null)
      let activeIdx = 0
      for (let i = 0; i < parsedSets.length; i++) {
        if (parsedSets[i].side_a !== null && parsedSets[i].side_b !== null) {
          activeIdx = i
        }
      }
      currentSetIndex.value = activeIdx
    }
  } catch (err) {
    ElMessage.error('Lỗi tải thông tin trận đấu: ' + err.message)
  } finally {
    isLoading.value = false
  }
}

const fetchCourts = async () => {
  try {
    const res = await apiClient.get('/api/courts/')
    courts.value = Array.isArray(res) ? res : []
  } catch (err) {
    courts.value = []
  }
}

// Chuyển sang Bước 2 (Pre-match)
const startPreMatchSetup = async () => {
  if (!setupForm.value.court_id) {
    ElMessage.warning('Vui lòng chọn sân thi đấu!')
    return
  }
  
  saving.value = true
  try {
    // Lưu sân và trọng tài trước lên Server
    await apiClient.put(`/api/tournaments/matches/${matchId}/admin-update`, {
      court_id: setupForm.value.court_id,
      referee_name: setupForm.value.referee_name,
      referee_phone: setupForm.value.referee_phone,
      status: 'scheduled'
    })
    
    // Đồng bộ lại local data
    await fetchMatchDetails()
    
    // Chuyển bước
    activeStep.value = 2
    initialWarmUpTime.value = warmUpMinutes.value * 60 + warmUpSeconds.value
  } catch (err) {
    ElMessage.error('Lỗi thiết lập trận đấu: ' + err.message)
  } finally {
    saving.value = false
  }
}

// Tung đồng xu
const flipCoin = () => {
  if (coinFlipping.value) return
  coinFlipping.value = true
  coinFlipped.value = false
  
  setTimeout(() => {
    const rand = Math.random()
    coinResult.value = rand > 0.5 ? 'heads' : 'tails'
    coinWinner.value = coinResult.value === 'heads' 
      ? (matchData.value?.p1_name || 'Bên A') 
      : (matchData.value?.p2_name || 'Bên B')
    
    // Chọn luôn bên thắng làm bên giao bóng ban đầu làm mặc định
    serverSide.value = coinResult.value === 'heads' ? 'side_a' : 'side_b'
    
    coinFlipping.value = false
    coinFlipped.value = true
    ElMessage.success(`Kết quả: Mặt ${coinResult.value === 'heads' ? 'Sấp (YES)' : 'Ngửa (NO)'}! ${coinWinner.value} thắng bốc thăm.`)
  }, 1200) // Thời gian xoay đồng xu
}

// Timer khởi động
const toggleTimer = () => {
  if (isTimerRunning.value) {
    clearInterval(timerInterval.value)
    isTimerRunning.value = false
  } else {
    isTimerRunning.value = true
    timerInterval.value = setInterval(() => {
      const totalSec = warmUpMinutes.value * 60 + warmUpSeconds.value
      if (totalSec <= 1) {
        clearInterval(timerInterval.value)
        isTimerRunning.value = false
        // Rung thiết bị hoặc phát chuông báo nếu được hỗ trợ
        if ('vibrate' in navigator) navigator.vibrate([200, 100, 200])
        ElMessage.warning('Hết thời gian khởi động! Hãy bắt đầu trận đấu.')
        warmUpMinutes.value = 0
        warmUpSeconds.value = 0
      } else {
        const nextSec = totalSec - 1
        warmUpMinutes.value = Math.floor(nextSec / 60)
        warmUpSeconds.value = nextSec % 60
      }
    }, 1000)
  }
}

const resetTimer = () => {
  clearInterval(timerInterval.value)
  isTimerRunning.value = false
  warmUpMinutes.value = Math.floor(initialWarmUpTime.value / 60)
  warmUpSeconds.value = initialWarmUpTime.value % 60
}

// Chuyển sang Bước 3 (Ghi điểm)
const startLiveMatch = async () => {
  clearInterval(timerInterval.value)
  isTimerRunning.value = false
  
  saving.value = true
  try {
    // Cập nhật trạng thái trận đấu đang diễn ra
    await apiClient.put(`/api/tournaments/matches/${matchId}/admin-update`, {
      status: 'ongoing'
    })
    
    // Chuyển bước
    activeStep.value = 3
    
    // Lưu trạng thái điểm đầu tiên vào history
    saveStateToHistory()
  } catch (err) {
    ElMessage.error('Lỗi bắt đầu trận đấu: ' + err.message)
  } finally {
    saving.value = false
  }
}

const goBackToPreMatch = () => {
  ElMessageBox.confirm(
    'Bạn có chắc chắn muốn quay lại màn hình bốc thăm tung đồng xu không? Điểm số hiện tại của trận đấu vẫn được giữ nguyên.',
    'Xác nhận quay lại',
    {
      confirmButtonText: 'Đồng ý',
      cancelButtonText: 'Hủy',
      type: 'warning'
    }
  ).then(() => {
    activeStep.value = 2
  }).catch(() => {})
}

const handleHeaderBack = () => {
  if (window.history.length > 1 && document.referrer) {
    router.back()
  } else if (matchData.value?.tournament_id) {
    router.push({ name: 'admin-draws', query: { tournamentId: matchData.value.tournament_id } })
  } else {
    router.push('/admin/draws')
  }
}

// --- LOGIC SCOREBOARD ---

const saveStateToHistory = () => {
  scoreHistory.value.push({
    p1Points: p1Points.value,
    p2Points: p2Points.value,
    setsScore: JSON.parse(JSON.stringify(setsScore.value)),
    currentSetIndex: currentSetIndex.value,
    serverSide: serverSide.value
  })
  // Giới hạn lịch sử tối đa 50 bước
  if (scoreHistory.value.length > 50) {
    scoreHistory.value.shift()
  }
}

const undoLastPoint = () => {
  if (scoreHistory.value.length <= 1) {
    ElMessage.warning('Không thể hoàn tác thêm.')
    return
  }
  // Bỏ trạng thái hiện tại
  scoreHistory.value.pop()
  // Lấy trạng thái trước đó
  const prevState = scoreHistory.value[scoreHistory.value.length - 1]
  
  p1Points.value = prevState.p1Points
  p2Points.value = prevState.p2Points
  setsScore.value = JSON.parse(JSON.stringify(prevState.setsScore))
  currentSetIndex.value = prevState.currentSetIndex
  serverSide.value = prevState.serverSide
  
  ElMessage.info('Đã hoàn tác điểm số.')
}

const awardPoint = (winnerSide) => {
  // Lưu trạng thái trước khi thay đổi
  saveStateToHistory()
  
  if (isTieBreak.value) {
    awardTieBreakPoint(winnerSide)
    return
  }
  
  if (winnerSide === 'side_a') {
    if (p1Points.value === 3) {
      if (p2Points.value === 4) {
        // B đang AD -> Quay về Deuce (3-3)
        p2Points.value = 3
      } else if (p2Points.value === 3) {
        // Đang Deuce -> A lên AD (4-3)
        p1Points.value = 4
      } else {
        // A đang 40, B dưới 40 -> A thắng Game
        winGame('side_a')
      }
    } else if (p1Points.value === 4) {
      // A đang AD -> A thắng Game
      winGame('side_a')
    } else {
      // Điểm dưới 40 -> Tăng bình thường (0 -> 15 -> 30 -> 40)
      p1Points.value++
    }
  } else {
    // Winner: Side B
    if (p2Points.value === 3) {
      if (p1Points.value === 4) {
        // A đang AD -> Quay về Deuce (3-3)
        p1Points.value = 3
      } else if (p1Points.value === 3) {
        // Đang Deuce -> B lên AD (3-4)
        p2Points.value = 4
      } else {
        // B đang 40, A dưới 40 -> B thắng Game
        winGame('side_b')
      }
    } else if (p2Points.value === 4) {
      // B đang AD -> B thắng Game
      winGame('side_b')
    } else {
      p2Points.value++
    }
  }
}

// Logic thắng loạt Tie-break (đếm 1, 2, 3...)
const awardTieBreakPoint = (winnerSide) => {
  if (winnerSide === 'side_a') {
    p1Points.value++
  } else {
    p2Points.value++
  }
  
  // Kiểm tra điều kiện thắng Tie-break (ít nhất 7 điểm và cách biệt 2 điểm)
  if (p1Points.value >= 7 && p1Points.value - p2Points.value >= 2) {
    winGame('side_a')
  } else if (p2Points.value >= 7 && p2Points.value - p1Points.value >= 2) {
    winGame('side_b')
  }
}

// Xử lý thắng 1 game đấu
const winGame = (side) => {
  if (isTieBreak.value) {
    // Lưu điểm tie-break trước khi reset điểm game
    tieBreaksScore.value[currentSetIndex.value] = {
      side_a: p1Points.value,
      side_b: p2Points.value
    }
  }

  // Reset điểm game
  p1Points.value = 0
  p2Points.value = 0
  
  const currentSet = setsScore.value[currentSetIndex.value]
  if (side === 'side_a') {
    currentSet.side_a++
    ElMessage.success(`${matchData.value.p1_name || 'Bên A'} thắng game đấu!`)
  } else {
    currentSet.side_b++
    ElMessage.success(`${matchData.value.p2_name || 'Bên B'} thắng game đấu!`)
  }
  
  // Tự động xoay người giao bóng sau mỗi game
  serverSide.value = serverSide.value === 'side_a' ? 'side_b' : 'side_a'
  
  // Kiểm tra thắng Set đấu
  checkSetWinner()
}

// Chuyển set đang ghi điểm thủ công
const changeActiveSet = (idx) => {
  saveStateToHistory()
  currentSetIndex.value = idx
  // Nếu set được chọn chưa có điểm nào (đang null), khởi tạo 0-0
  if (setsScore.value[idx].side_a === null) {
    setsScore.value[idx].side_a = 0
    setsScore.value[idx].side_b = 0
  }
  ElMessage.info(`Đã chuyển sang ghi điểm Set ${idx + 1}`)
}

// Thêm set đấu mới thủ công
const addNewSet = () => {
  const maxSets = matchData.value?.best_of_sets || 3
  if (setsScore.value.length >= maxSets) {
    ElMessage.warning(`Trận đấu tối đa chỉ có ${maxSets} set.`)
    return
  }
  saveStateToHistory()
  setsScore.value.push({ side_a: 0, side_b: 0 })
  tieBreaksScore.value.push({ side_a: null, side_b: null })
  currentSetIndex.value = setsScore.value.length - 1
  ElMessage.success(`Đã thêm Set ${setsScore.value.length}`)
  syncLiveScoreToDB()
}

// Kiểm tra xem Set đấu hiện tại đã có người thắng chưa
const checkSetWinner = () => {
  const currentSet = setsScore.value[currentSetIndex.value]
  const a = currentSet.side_a
  const b = currentSet.side_b
  
  let setWinner = null
  
  // Nếu là loạt tie-break và có bên thắng game thứ 7
  if (a === 7 && b === 6) {
    setWinner = 'side_a'
  } else if (b === 7 && a === 6) {
    setWinner = 'side_b'
  } else if (a >= 6 && a - b >= 2) {
    setWinner = 'side_a'
  } else if (b >= 6 && b - a >= 2) {
    setWinner = 'side_b'
  }
  
  if (setWinner) {
    ElMessageBox.alert(
      `Set ${currentSetIndex.value + 1} kết thúc! Người thắng: ${setWinner === 'side_a' ? (matchData.value.p1_name || 'Bên A') : (matchData.value.p2_name || 'Bên B')}`,
      'Kết quả Set đấu',
      {
        confirmButtonText: 'Đồng ý',
        callback: () => {
          // Chuyển sang Set tiếp theo nếu chưa đạt tối đa số Set
          const maxSets = matchData.value.best_of_sets || 3
          const aSetsWon = setsScore.value.filter((s, idx) => s.side_a > s.side_b && idx <= currentSetIndex.value).length
          const bSetsWon = setsScore.value.filter((s, idx) => s.side_b > s.side_a && idx <= currentSetIndex.value).length
          const setsToWin = Math.ceil(maxSets / 2)
          
          if (aSetsWon === setsToWin || bSetsWon === setsToWin) {
            // Trận đấu kết thúc hoàn toàn
            finishMatch()
          } else {
            // Chuyển qua Set tiếp theo
            currentSetIndex.value++
            setsScore.value[currentSetIndex.value] = { side_a: 0, side_b: 0 }
            saveStateToHistory()
          }
        }
      }
    )
  } else {
    // Tự động đồng bộ điểm Set hiện tại lên server để người xem trực tuyến theo dõi
    syncLiveScoreToDB()
  }
}

// Đồng bộ tỷ số thời gian thực lên backend
const syncLiveScoreToDB = async () => {
  const payload = {
    score: getFormattedScoreSummary(),
    set1_a: setsScore.value[0]?.side_a !== undefined ? setsScore.value[0].side_a : null,
    set1_b: setsScore.value[0]?.side_b !== undefined ? setsScore.value[0].side_b : null,
    set2_a: setsScore.value[1]?.side_a !== undefined ? setsScore.value[1].side_a : null,
    set2_b: setsScore.value[1]?.side_b !== undefined ? setsScore.value[1].side_b : null,
    set3_a: setsScore.value[2]?.side_a !== undefined ? setsScore.value[2].side_a : null,
    set3_b: setsScore.value[2]?.side_b !== undefined ? setsScore.value[2].side_b : null,
    tie_break_1_a: tieBreaksScore.value[0]?.side_a !== undefined ? tieBreaksScore.value[0].side_a : null,
    tie_break_1_b: tieBreaksScore.value[0]?.side_b !== undefined ? tieBreaksScore.value[0].side_b : null,
    tie_break_2_a: tieBreaksScore.value[1]?.side_a !== undefined ? tieBreaksScore.value[1].side_a : null,
    tie_break_2_b: tieBreaksScore.value[1]?.side_b !== undefined ? tieBreaksScore.value[1].side_b : null,
    tie_break_3_a: tieBreaksScore.value[2]?.side_a !== undefined ? tieBreaksScore.value[2].side_a : null,
    tie_break_3_b: tieBreaksScore.value[2]?.side_b !== undefined ? tieBreaksScore.value[2].side_b : null
  }
  try {
    await apiClient.put(`/api/tournaments/matches/${matchId}/admin-update`, payload)
  } catch (err) {
    console.error('Đồng bộ điểm trực tiếp lỗi:', err)
  }
}

// Format tỷ số thành chuỗi để lưu Database
const getFormattedScoreSummary = () => {
  return setsScore.value
    .filter(s => s.side_a !== null && s.side_b !== null)
    .map(s => {
      // Ví dụ: 7-6 (5)
      const idx = setsScore.value.indexOf(s)
      const tb = tieBreaksScore.value[idx]
      if (tb && tb.side_a !== null && tb.side_b !== null) {
        const loserPoints = Math.min(tb.side_a, tb.side_b)
        return `${s.side_a}-${s.side_b}(${loserPoints})`
      }
      return `${s.side_a}-${s.side_b}`
    })
    .join(', ')
}

// Kết thúc trận đấu hoàn toàn và lưu
const finishMatch = async () => {
  // Tính xem ai thắng cuộc dựa trên số Set thắng
  const aSetsWon = setsScore.value.filter(s => s.side_a > s.side_b).length
  const bSetsWon = setsScore.value.filter(s => s.side_b > s.side_a).length
  const winnerSide = aSetsWon > bSetsWon ? 'side_a' : 'side_b'
  
  saving.value = true
  try {
    const payload = {
      score: getFormattedScoreSummary(),
      winner_side: winnerSide,
      referee_name: setupForm.value.referee_name,
      referee_phone: setupForm.value.referee_phone,
      court_id: setupForm.value.court_id,
      set1_a: setsScore.value[0]?.side_a !== undefined ? setsScore.value[0].side_a : null,
      set1_b: setsScore.value[0]?.side_b !== undefined ? setsScore.value[0].side_b : null,
      set2_a: setsScore.value[1]?.side_a !== undefined ? setsScore.value[1].side_a : null,
      set2_b: setsScore.value[1]?.side_b !== undefined ? setsScore.value[1].side_b : null,
      set3_a: setsScore.value[2]?.side_a !== undefined ? setsScore.value[2].side_a : null,
      set3_b: setsScore.value[2]?.side_b !== undefined ? setsScore.value[2].side_b : null,
      tie_break_1_a: tieBreaksScore.value[0]?.side_a !== undefined ? tieBreaksScore.value[0].side_a : null,
      tie_break_1_b: tieBreaksScore.value[0]?.side_b !== undefined ? tieBreaksScore.value[0].side_b : null,
      tie_break_2_a: tieBreaksScore.value[1]?.side_a !== undefined ? tieBreaksScore.value[1].side_a : null,
      tie_break_2_b: tieBreaksScore.value[1]?.side_b !== undefined ? tieBreaksScore.value[1].side_b : null,
      tie_break_3_a: tieBreaksScore.value[2]?.side_a !== undefined ? tieBreaksScore.value[2].side_a : null,
      tie_break_3_b: tieBreaksScore.value[2]?.side_b !== undefined ? tieBreaksScore.value[2].side_b : null
    }
    
    // Gọi API tính toán ELO và cập nhật Match hoàn thành
    await apiClient.post(`/api/tournaments/matches/${matchId}/score`, payload)
    
    ElMessage.success('Đã lưu kết quả trận đấu và cập nhật điểm ELO!')
    // Quay lại màn hình admin bốc thăm
    router.push({ name: 'admin-draws', query: { tournamentId: matchData.value.tournament_id } })
  } catch (err) {
    ElMessage.error('Lỗi kết thúc trận đấu: ' + err.message)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchMatchDetails(), fetchCourts()])
})
</script>

<template>
  <div class="referee-mobile-layout">
    <!-- Header di động -->
    <header class="referee-header">
      <el-button :icon="ArrowLeft" circle plain @click="handleHeaderBack" class="back-btn" />
      <div class="header-match-title">
        <h1>BÀN TRỌNG TÀI</h1>
        <small v-if="matchData">Trận #{{ matchData.match_no }} · {{ matchData.round_code }}</small>
      </div>
      <div class="header-status" v-if="matchData">
        <span class="status-badge" :class="matchData.status">{{ matchData.status.toUpperCase() }}</span>
      </div>
    </header>

    <!-- STEP 1: SETUP SCREEN -->
    <main v-if="activeStep === 1" class="step-container setup-screen" v-loading="isLoading">
      <!-- VS Match Header Card -->
      <div v-if="matchData" class="match-info-setup-card">
        <div class="vs-player side-a">
          <el-avatar :size="54" :src="matchData.p1_avatar" class="avatar-setup" />
          <div class="name-info">
            <span class="player-name-setup">{{ matchData.p1_name || 'Bên A' }}</span>
            <span class="partner-name-setup" v-if="matchData.p1_partner_name">+ {{ matchData.p1_partner_name }}</span>
          </div>
        </div>
        <div class="vs-badge">VS</div>
        <div class="vs-player side-b">
          <el-avatar :size="54" :src="matchData.p2_avatar" class="avatar-setup" />
          <div class="name-info">
            <span class="player-name-setup">{{ matchData.p2_name || 'Bên B' }}</span>
            <span class="partner-name-setup" v-if="matchData.p2_partner_name">+ {{ matchData.p2_partner_name }}</span>
          </div>
        </div>
      </div>

      <!-- Setup Form Card -->
      <div class="referee-setup-card">
        <div class="setup-title-group">
          <h2>Điều phối trận đấu</h2>
          <p>Chọn sân thi đấu chính thức và cập nhật thông tin trọng tài điều khiển để bắt đầu làm thủ tục ra sân.</p>
        </div>

        <el-form label-position="top" class="setup-form">
          <el-form-item label="Sân thi đấu" required>
            <el-select v-model="setupForm.court_id" placeholder="Chọn sân thi đấu tại địa điểm" style="width: 100%" class="mobile-select-premium">
              <template #prefix>
                <el-icon class="select-prefix-icon"><Location /></el-icon>
              </template>
              <el-option v-for="court in courts" :key="court.id" :label="court.court_name" :value="court.id">
                <span>{{ court.court_name }}</span>
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item label="Họ tên trọng tài chính">
            <el-input v-model="setupForm.referee_name" placeholder="Nhập tên trọng tài điều khiển" class="mobile-input-premium">
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="SĐT liên hệ trọng tài">
            <el-input v-model="setupForm.referee_phone" placeholder="Số điện thoại" class="mobile-input-premium">
              <template #prefix>
                <el-icon><Cellphone /></el-icon>
              </template>
            </el-input>
          </el-form-item>
        </el-form>
      </div>

      <div class="mobile-footer-actions">
        <el-button type="primary" size="large" class="mobile-btn-action-premium" @click="startPreMatchSetup" :loading="saving">
          <el-icon class="mr-1"><VideoPlay /></el-icon> BẮT ĐẦU THỦ TỤC
        </el-button>
      </div>
    </main>

    <!-- STEP 2: PRE-MATCH SCREEN (COIN FLIP & TIMER) -->
    <main v-if="activeStep === 2" class="step-container pre-match-screen">
      <!-- 1. Coin Flip Section -->
      <section class="pre-match-card card-premium">
        <h3>BỐC THĂM TUNG ĐỒNG XU</h3>
        <p class="section-desc">Chạm vào đồng xu để thực hiện tung ngẫu nhiên chọn bên giao bóng/chọn sân.</p>
        
        <div class="coin-container" @click="flipCoin">
          <div class="coin" :class="{ 'flipping': coinFlipping, 'heads': coinResult === 'heads', 'tails': coinResult === 'tails' }">
            <div class="coin-face front">
              <img :src="coinYesUrl" alt="YES" class="coin-img" />
            </div>
            <div class="coin-face back">
              <img :src="coinNoUrl" alt="NO" class="coin-img" />
            </div>
          </div>
        </div>

        <div class="coin-result-wrap" v-if="coinFlipped">
          <div class="winner-label">Kết quả tung đồng xu:</div>
          <div class="winner-name">{{ coinResult === 'heads' ? 'Mặt Sấp (YES)' : 'Mặt Ngửa (NO)' }}</div>
        </div>
      </section>

      <!-- 2. Warm-up Timer Section -->
      <section class="pre-match-card card-premium">
        <h3>KHỞI ĐỘNG (WARM-UP)</h3>
        <div class="timer-display">
          <span>{{ String(warmUpMinutes).padStart(2, '0') }}</span>
          <span class="colon">:</span>
          <span>{{ String(warmUpSeconds).padStart(2, '0') }}</span>
        </div>
        <div class="timer-presets" v-if="!isTimerRunning" style="display: flex; justify-content: center; gap: 8px; margin-bottom: 12px;">
          <el-button size="small" round @click="warmUpMinutes = 3; warmUpSeconds = 0; initialWarmUpTime = 180">3 Phút</el-button>
          <el-button size="small" round @click="warmUpMinutes = 5; warmUpSeconds = 0; initialWarmUpTime = 300">5 Phút</el-button>
          <el-button size="small" round @click="warmUpMinutes = 10; warmUpSeconds = 0; initialWarmUpTime = 600">10 Phút</el-button>
        </div>
        <div class="timer-custom-input" v-if="!isTimerRunning" style="margin-bottom: 16px; display: flex; justify-content: center; gap: 10px; align-items: center">
          <span style="font-size: 0.8rem; color: #94a3b8; font-weight: 700">TÙY CHỈNH PHÚT:</span>
          <el-input-number v-model="warmUpMinutes" :min="0" :max="60" size="small" style="width: 100px" @change="initialWarmUpTime = warmUpMinutes * 60 + warmUpSeconds" />
        </div>
        <div class="timer-controls">
          <el-button type="primary" size="large" circle :icon="isTimerRunning ? Timer : VideoPlay" @click="toggleTimer" class="timer-btn" />
          <el-button size="large" circle :icon="RefreshRight" @click="resetTimer" class="timer-btn" />
        </div>
      </section>

      <!-- 3. Pre-match Selections -->
      <section class="pre-match-card card-premium">
        <h3>THIẾT LẬP GIAO BÓNG</h3>
        <div class="server-selection">
          <p class="section-label">Ai giao bóng trước?</p>
          <el-radio-group v-model="serverSide" class="mobile-radio-group">
            <el-radio-button :value="'side_a'">{{ matchData?.p1_name || 'Bên A' }}</el-radio-button>
            <el-radio-button :value="'side_b'">{{ matchData?.p2_name || 'Bên B' }}</el-radio-button>
          </el-radio-group>
        </div>
      </section>

      <div class="mobile-footer-actions">
        <el-button size="large" class="mobile-btn-start-match-white" @click="startLiveMatch">
          BẮT ĐẦU TRẬN ĐẤU <el-icon class="ml-1"><Check /></el-icon>
        </el-button>
      </div>
    </main>

    <!-- STEP 3: LIVE SCOREBOARD SCREEN -->
    <main v-if="activeStep === 3" class="step-container live-scoreboard-screen">
      <!-- 1. Score Display Grid -->
      <div class="scoreboard-card card-premium">
        <div class="scoreboard-header">
          <span>Set ghi điểm: Set {{ currentSetIndex + 1 }}</span>
          <span class="server-indicator">Giao bóng: <strong>{{ currentServerName }}</strong></span>
        </div>
        
        <!-- Bộ chọn Set và Thêm Set Thủ công -->
        <div class="set-selector-wrap" style="display: flex; gap: 8px; align-items: center; margin-bottom: 16px; padding: 10px; background: #f1f5f9; border-radius: 12px; border: 1px solid #e2e8f0; flex-wrap: wrap;">
          <span style="font-size: 0.75rem; font-weight: 900; color: #475569;">CHỌN SET:</span>
          <div style="display: flex; gap: 6px; flex-wrap: wrap; align-items: center;">
            <el-button 
              v-for="(set, idx) in setsScore" 
              :key="idx" 
              size="small" 
              round
              :type="currentSetIndex === idx ? 'primary' : 'default'"
              @click="changeActiveSet(idx)"
              style="font-weight: 800; font-size: 0.75rem;"
            >
              Set {{ idx + 1 }} ({{ set.side_a !== null ? set.side_a : '-' }} - {{ set.side_b !== null ? set.side_b : '-' }})
            </el-button>
            <el-button 
              v-if="setsScore.length < (matchData?.best_of_sets || 3)"
              size="small" 
              type="success" 
              plain
              round
              @click="addNewSet"
              style="font-weight: 800; font-size: 0.75rem; display: inline-flex; align-items: center; gap: 2px;"
            >
              + Thêm Set
            </el-button>
          </div>
        </div>
        
        <div class="score-grid">
          <!-- Side A -->
          <div class="score-row" :class="{ 'is-serving': serverSide === 'side_a' }">
            <div class="player-info">
              <el-avatar :size="24" :src="matchData?.p1_avatar" class="avatar-ref" />
              <div class="name-box">
                <span class="p-name">{{ matchData?.p1_name || 'Bên A' }}</span>
                <span class="p-partner" v-if="matchData?.p1_partner_name">{{ matchData.p1_partner_name }}</span>
              </div>
            </div>
            <div class="set-history" style="display: flex; gap: 8px;">
              <span v-for="(set, idx) in setsScore" :key="idx" style="position: relative; display: inline-flex; align-items: center;">
                <span class="set-score-box" :class="{ 'active': idx === currentSetIndex }">
                  {{ set.side_a !== null ? set.side_a : '-' }}
                </span>
                <span v-if="tieBreaksScore[idx]?.side_a !== null" style="position: absolute; top: -4px; right: -4px; font-size: 0.58rem; font-weight: 900; color: #ef4444; background: #fee2e2; border-radius: 4px; padding: 0 2px; line-height: 1;">
                  {{ tieBreaksScore[idx].side_a }}
                </span>
              </span>
            </div>
            <div class="game-points">{{ p1DisplayPoints }}</div>
          </div>
 
          <!-- Divider -->
          <div class="score-divider"></div>
 
          <!-- Side B -->
          <div class="score-row" :class="{ 'is-serving': serverSide === 'side_b' }">
            <div class="player-info">
              <el-avatar :size="24" :src="matchData?.p2_avatar" class="avatar-ref" />
              <div class="name-box">
                <span class="p-name">{{ matchData?.p2_name || 'Bên B' }}</span>
                <span class="p-partner" v-if="matchData?.p2_partner_name">{{ matchData.p2_partner_name }}</span>
              </div>
            </div>
            <div class="set-history" style="display: flex; gap: 8px;">
              <span v-for="(set, idx) in setsScore" :key="idx" style="position: relative; display: inline-flex; align-items: center;">
                <span class="set-score-box" :class="{ 'active': idx === currentSetIndex }">
                  {{ set.side_b !== null ? set.side_b : '-' }}
                </span>
                <span v-if="tieBreaksScore[idx]?.side_b !== null" style="position: absolute; top: -4px; right: -4px; font-size: 0.58rem; font-weight: 900; color: #ef4444; background: #fee2e2; border-radius: 4px; padding: 0 2px; line-height: 1;">
                  {{ tieBreaksScore[idx].side_b }}
                </span>
              </span>
            </div>
            <div class="game-points">{{ p2DisplayPoints }}</div>
          </div>
        </div>
      </div>

      <!-- 2. Points Buttons (Ngón tay dễ bấm) -->
      <div class="point-trigger-section">
        <button class="point-btn side-a" @click="awardPoint('side_a')">
          <span class="btn-title">+ ĐIỂM</span>
          <span class="player-desc">{{ matchData?.p1_name || 'Bên A' }}</span>
        </button>
        <button class="point-btn side-b" @click="awardPoint('side_b')">
          <span class="btn-title">+ ĐIỂM</span>
          <span class="player-desc">{{ matchData?.p2_name || 'Bên B' }}</span>
        </button>
      </div>

      <!-- 3. Sub-operations (Hoàn tác, Đổi giao bóng, Quay lại bốc thăm, Kết thúc) -->
      <div class="scoreboard-sub-ops-premium">
        <el-button :icon="Back" type="info" plain class="sub-btn-ref" @click="undoLastPoint">
          HOÀN TÁC
        </el-button>
        <el-button :icon="RefreshRight" type="warning" plain class="sub-btn-ref" @click="serverSide = serverSide === 'side_a' ? 'side_b' : 'side_a'">
          ĐỔI GIAO BÓNG
        </el-button>
        <el-button :icon="ArrowLeft" type="primary" plain class="sub-btn-ref" @click="goBackToPreMatch">
          BỐC THĂM LẠI
        </el-button>
        <el-button :icon="Check" type="danger" class="sub-btn-ref end-match-btn" @click="finishMatch" :loading="saving">
          KẾT THÚC
        </el-button>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* MOBILE-FIRST REFEREE STYLING */
.referee-mobile-layout {
  min-height: 100vh;
  background-color: #f8fafc;
  color: #0f172a;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  padding-bottom: 32px;
  padding-top: 12px;
}

.referee-header {
  background-color: #ffffff;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 10;
}

.back-btn {
  background: #ffffff !important;
  border-color: #cbd5e1 !important;
  color: #334155 !important;
}

.header-match-title h1 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 900;
  letter-spacing: 0.05em;
  color: #1e3a8a;
}

.header-match-title small {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 600;
  display: block;
  margin-top: 2px;
}

.header-status {
  margin-left: auto;
}

.status-badge {
  font-size: 0.7rem;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 99px;
  background: #fef3c7;
  color: #d97706;
  border: 1px solid #fde68a;
}

.status-badge.ongoing {
  background: #fee2e2;
  color: #ef4444;
  border: 1px solid #fca5a5;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

.step-container {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.card-premium {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 20px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.06);
}

.match-info-setup-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.05);
}

.vs-player {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
  text-align: center;
}

.avatar-setup {
  border: 2.5px solid #2563eb;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.15);
  background-color: #ffffff;
}

.name-info {
  display: grid;
  gap: 2px;
  margin-top: 4px;
}

.player-name-setup {
  font-weight: 900;
  font-size: 0.95rem;
  color: #0f172a;
  line-height: 1.3;
}

.partner-name-setup {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 700;
}

.vs-badge {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #ffffff;
  font-weight: 900;
  font-size: 0.85rem;
  width: 34px;
  height: 34px;
  border-radius: 99px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);
  margin: 0 16px;
  flex-shrink: 0;
}

.referee-setup-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.06);
}

.setup-title-group {
  margin-bottom: 24px;
}

.setup-title-group h2 {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 900;
  color: #059669;
  letter-spacing: -0.01em;
}

.setup-title-group p {
  margin: 6px 0 0 0;
  font-size: 0.85rem;
  color: #64748b;
  line-height: 1.45;
}

.setup-form :deep(.el-form-item__label) {
  color: #334155;
  font-weight: 800;
  font-size: 0.85rem;
  margin-bottom: 8px;
}

.mobile-select-premium :deep(.el-select__wrapper),
.mobile-input-premium :deep(.el-input__wrapper) {
  background-color: #f1f5f9 !important;
  border: 1px solid #cbd5e1 !important;
  box-shadow: none !important;
  border-radius: 14px !important;
  min-height: 50px !important;
  padding: 0 14px !important;
  transition: all 0.25s ease;
}

.mobile-select-premium :deep(.el-select__wrapper:hover),
.mobile-input-premium :deep(.el-input__wrapper:hover) {
  border-color: #2563eb !important;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}

.mobile-select-premium :deep(.el-select__placeholder),
.mobile-input-premium :deep(.el-input__inner) {
  color: #0f172a !important;
  font-weight: 700;
}

.select-prefix-icon {
  color: #059669 !important;
  font-size: 1.15rem;
  margin-right: 6px;
}

.mobile-footer-actions {
  margin-top: auto;
  padding-top: 20px;
}

.mobile-btn-action-premium {
  width: 100%;
  height: 56px;
  border-radius: 18px !important;
  font-weight: 900 !important;
  font-size: 1.05rem !important;
  letter-spacing: 0.05em;
  background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
  border: none !important;
  box-shadow: 0 6px 20px rgba(4, 120, 87, 0.35) !important;
  color: #ffffff !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.mobile-btn-action-premium:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(4, 120, 87, 0.45) !important;
}

.mobile-btn-action-premium:active {
  transform: translateY(0);
}

.mobile-btn-start-match-white {
  width: 100%;
  height: 56px;
  border-radius: 18px !important;
  font-weight: 900 !important;
  font-size: 1.1rem !important;
  letter-spacing: 0.05em;
  background-color: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05) !important;
  color: #0f172a !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.mobile-btn-start-match-white:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.1) !important;
  background-color: #f8fafc !important;
}

.mobile-btn-start-match-white:active {
  transform: translateY(0);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.05) !important;
}

/* STEP 2: PRE-MATCH SCREEN */
.pre-match-card h3 {
  margin: 0 0 12px 0;
  font-size: 0.95rem;
  font-weight: 900;
  color: #1e3a8a;
  letter-spacing: 0.05em;
  text-align: center;
}

.section-desc {
  text-align: center;
  color: #475569;
  font-size: 0.8rem;
  margin: 0 0 16px 0;
}

/* Coin Toss styles */
.coin-container {
  perspective: 1000px;
  width: 120px;
  height: 120px;
  margin: 20px auto;
  cursor: pointer;
}

.coin {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.1s linear;
}

.coin.flipping {
  animation: flip 1.2s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}

.coin.heads {
  transform: rotateY(0deg);
}

.coin.tails {
  transform: rotateY(180deg);
}

.coin-face {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent !important;
  border: none !important;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25) !important;
}

.coin-face.front {
  background: transparent;
}

.coin-face.back {
  background: transparent;
  transform: rotateY(180deg);
}

.coin-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 50%;
}

@keyframes flip {
  0% { transform: rotateY(0deg) translateY(0); }
  50% { transform: rotateY(900deg) translateY(-80px); }
  100% { transform: rotateY(1800deg) translateY(0); }
}

.coin-result-wrap {
  text-align: center;
  margin-top: 16px;
  background: #f1f5f9;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.winner-label {
  font-size: 0.75rem;
  color: #475569;
  font-weight: 700;
}

.winner-name {
  font-size: 1.1rem;
  font-weight: 900;
  color: #d97706;
  margin-top: 4px;
}

/* Warm-up Timer */
.timer-display {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3.2rem;
  font-weight: 900;
  font-family: 'JetBrains Mono', monospace;
  color: #2563eb;
  margin: 10px 0;
}

.timer-display .colon {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.timer-controls {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.timer-btn {
  width: 50px;
  height: 50px;
  font-size: 1.2rem;
}

.server-selection {
  text-align: center;
}

.section-label {
  font-size: 0.8rem;
  font-weight: 800;
  color: #475569;
  text-transform: uppercase;
  margin-bottom: 10px;
  letter-spacing: 0.05em;
}

.mobile-radio-group :deep(.el-radio-button__inner) {
  background-color: #f1f5f9 !important;
  color: #475569 !important;
  border: 1px solid #cbd5e1 !important;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  padding: 0 24px;
  font-weight: 800;
}

.mobile-radio-group :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: #2563eb !important;
  color: white !important;
  border-color: #2563eb !important;
}

/* STEP 3: LIVE SCOREBOARD */
.scoreboard-card {
  padding: 16px;
}

.scoreboard-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #475569;
  font-weight: 700;
  margin-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 10px;
}

.server-indicator strong {
  color: #d97706;
}

.score-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.score-row {
  display: grid;
  grid-template-columns: 1fr auto 60px;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.score-row.is-serving {
  border-color: #2563eb;
  box-shadow: 0 4px 15px rgba(37, 99, 235, 0.08);
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.player-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.avatar-ref {
  border: 2px solid #cbd5e1;
}

.is-serving .avatar-ref {
  border-color: #2563eb;
}

.name-box {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.p-name {
  font-size: 0.95rem;
  font-weight: 900;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.is-serving .p-name {
  color: #0f172a;
}

.p-partner {
  font-size: 0.75rem;
  color: #64748b;
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.set-history {
  display: flex;
  gap: 6px;
}

.set-score-box {
  width: 24px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  border-radius: 6px;
  font-weight: 900;
  color: #475569;
  font-family: 'JetBrains Mono', monospace;
  font-size: 1rem;
}

.set-score-box.active {
  background: #1e3a8a;
  color: #ffffff;
  border: 1px solid #1e3a8a;
}

.game-points {
  font-family: 'JetBrains Mono', monospace;
  font-size: 2.2rem;
  font-weight: 900;
  color: #059669;
  text-align: right;
  line-height: 1;
}

.is-serving .game-points {
  color: #d97706;
}

.score-divider {
  height: 1px;
  background: #e2e8f0;
  margin: 2px 0;
}

/* Point trigger buttons (Mobile ergonomics) */
.point-trigger-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 10px;
}

.point-btn {
  height: 120px;
  border-radius: 24px;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(0,0,0,0.12);
  transition: transform 0.1s ease, filter 0.18s ease;
}

.point-btn:active {
  transform: scale(0.96);
}

.point-btn.side-a {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
}

.point-btn.side-b {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: white;
}

.point-btn .btn-title {
  font-size: 1.4rem;
  font-weight: 900;
  letter-spacing: 0.05em;
}

.point-btn .player-desc {
  font-size: 0.8rem;
  opacity: 0.9;
  font-weight: 700;
  max-width: 90%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.scoreboard-sub-ops-premium {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 16px;
}

.scoreboard-sub-ops-premium :deep(.sub-btn-ref) {
  height: 50px;
  border-radius: 14px;
  font-weight: 900;
  font-size: 0.85rem;
  margin: 0 !important;
  border: 1.5px solid #cbd5e1 !important;
  color: #334155 !important;
  background-color: #ffffff !important;
  box-shadow: 0 4px 10px rgba(0,0,0,0.03);
}

.scoreboard-sub-ops-premium :deep(.sub-btn-ref.el-button--info) {
  background-color: #f1f5f9 !important;
  border-color: #cbd5e1 !important;
  color: #334155 !important;
}

.scoreboard-sub-ops-premium :deep(.sub-btn-ref.el-button--warning) {
  background-color: #fef3c7 !important;
  border-color: #fde68a !important;
  color: #b45309 !important;
}

.scoreboard-sub-ops-premium :deep(.sub-btn-ref.el-button--primary) {
  background-color: #eff6ff !important;
  border-color: #bfdbfe !important;
  color: #1e40af !important;
}

.scoreboard-sub-ops-premium :deep(.sub-btn-ref.el-button--danger) {
  background-color: #fee2e2 !important;
  border-color: #fca5a5 !important;
  color: #b91c1c !important;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.15);
}
</style>
