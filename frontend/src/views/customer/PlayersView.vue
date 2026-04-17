<script setup>
import { computed, ref, onMounted } from 'vue'
import { Search, Trophy, ChatDotRound, Microphone, Promotion, CircleCheck } from '@element-plus/icons-vue'
import { playerService } from '../../services/playerService'

// Mock Data for Community Visualization
const onlinePlayers = ref([
  { id: 1, name: 'Lê Văn Tú', elo: 1250, avatar: 'https://i.pravatar.cc/150?u=1', status: 'online' },
  { id: 2, name: 'Nguyễn Minh Anh', elo: 1180, avatar: 'https://i.pravatar.cc/150?u=2', status: 'online' },
  { id: 3, name: 'Trần Hoàng Nam', elo: 1320, avatar: 'https://i.pravatar.cc/150?u=3', status: 'online' },
  { id: 4, name: 'Phạm Bảo Khang', elo: 1100, avatar: 'https://i.pravatar.cc/150?u=4', status: 'away' },
  { id: 5, name: 'Đặng Quốc Huy', elo: 1210, avatar: 'https://i.pravatar.cc/150?u=5', status: 'online' },
])

const chatMessages = ref([
  { id: 1, user: 'Admin', text: 'Chào mừng các VĐV đã quay trở lại với Saigon Tennis Tour 2026!', time: '09:00', isAdmin: true },
  { id: 2, user: 'Lê Văn Tú', text: 'Có ai rảnh sân Celadon tối nay không? Kèo 1200 - 1300 giao lưu nhẹ nhàng.', time: '10:05' },
  { id: 3, user: 'Trần Hoàng Nam', text: 'Tối nay mấy giờ vậy Tú? @Lê Văn Tú', time: '10:12' },
  { id: 4, user: 'Nguyễn Minh Anh', text: 'Sáng mai có giải mini ở Bình Tân, mọi người nhớ đăng ký nhé!', time: '10:15' },
])

const newMessage = ref('')
const searchQuery = ref('')
const players = ref([])
const recentWinners = ref([])
const loading = ref(true)

const sendMessage = () => {
  if (!newMessage.value.trim()) return
  chatMessages.value.push({
    id: Date.now(),
    user: 'Bạn',
    text: newMessage.value,
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  })
  newMessage.value = ''
}

const fetchPlayers = async () => {
  loading.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/players/rankings`)
    const rankings = await response.json()
    players.value = rankings
    recentWinners.value = rankings.slice(0, 4)
  } catch (err) {
    console.error('Lỗi tải dữ liệu:', err)
  } finally {
    loading.value = false
  }
}

onMounted(fetchPlayers)
</script>

<template>
  <div class="community-page">
    
    <!-- TẦNG 1: VINH DANH & TÌM KIẾM -->
    <section class="champions-hero">
      <div class="container hero-inner">
        <div class="hero-header">
          <span class="kicker"><el-icon><Trophy /></el-icon> HALL OF FAME</span>
          <h2>Vinh Danh Nhà Vô Địch</h2>
        </div>
        
        <div class="champions-slider">
          <div v-for="winner in recentWinners" :key="winner.player_id" class="champion-mini-card">
            <div class="champ-avatar">
              <img :src="winner.avatar_url || 'https://res.cloudinary.com/dfs9o3bny/image/upload/v1776311634/default_avatar.png'" alt="Winner" />
              <div class="rank-badge">#{{ winner.rank }}</div>
            </div>
            <div class="champ-info">
              <h3>{{ winner.full_name }}</h3>
              <span class="champ-elo">{{ winner.elo_points }} ELO</span>
            </div>
          </div>
        </div>

        <div class="search-bar-container">
          <el-input
            v-model="searchQuery"
            placeholder="Tìm kiếm bạn chơi hoặc đối thủ..."
            class="global-search"
            size="large"
            :prefix-icon="Search"
            clearable
          />
        </div>
      </div>
    </section>

    <!-- TẦNG 2 & 3: KHÔNG GIAN TƯƠNG TÁC -->
    <section class="interaction-zone">
      <div class="container social-grid">
        
        <!-- SIDEBAR: ONLINE PLAYERS -->
        <aside class="online-sidebar">
          <div class="sidebar-header">
            <h4>ĐANG TRỰC TUYẾN ({{ onlinePlayers.filter(p => p.status === 'online').length }})</h4>
          </div>
          <div class="online-list">
            <div v-for="player in onlinePlayers" :key="player.id" class="online-user">
              <div class="user-avatar-wrap">
                <img :src="player.avatar" />
                <span :class="['status-dot', player.status]"></span>
              </div>
              <div class="user-detail">
                <span class="u-name">{{ player.name }}</span>
                <span class="u-elo">{{ player.elo }} Elo</span>
              </div>
              <button class="chat-trigger" title="Nhắn tin riêng">
                <el-icon><ChatDotRound /></el-icon>
              </button>
            </div>
          </div>
          <div class="sidebar-footer">
            <button class="btn-all-players">Tất cả vận động viên</button>
          </div>
        </aside>

        <!-- MAIN: GLOBAL COMMUNITY CHAT -->
        <main class="community-chat">
          <div class="chat-header">
            <div class="chat-info">
              <div class="chat-avatar-group">
                <img v-for="i in 3" :key="i" :src="`https://i.pravatar.cc/150?u=${i}`" />
                <span class="plus-count">+{{ players.length }}</span>
              </div>
              <div class="chat-title">
                <h4>Phòng Chat Cộng Đồng</h4>
                <p>Nơi kết nối và giao lưu kèo đấu tự do</p>
              </div>
            </div>
            <div class="chat-actions">
              <el-button type="success" plain size="small" :icon="CircleCheck">Hoạt động</el-button>
            </div>
          </div>

          <div class="chat-messages-area">
            <div 
              v-for="msg in chatMessages" 
              :key="msg.id" 
              :class="['message-row', { 'is-admin': msg.isAdmin, 'is-me': msg.user === 'Bạn' }]"
            >
              <div v-if="msg.user !== 'Bạn'" class="msg-avatar">
                <img :src="`https://api.dicebear.com/7.x/avataaars/svg?seed=${msg.user}`" />
              </div>
              <div class="msg-content">
                <div class="msg-meta">
                  <span class="msg-user">{{ msg.user }}</span>
                  <span class="msg-time">{{ msg.time }}</span>
                </div>
                <div class="msg-bubble">
                  {{ msg.text }}
                </div>
              </div>
            </div>
          </div>

          <div class="chat-input-area">
            <div class="input-actions">
              <el-icon class="icon-btn"><Microphone /></el-icon>
            </div>
            <input 
              v-model="newMessage" 
              type="text" 
              placeholder="Nhập tin nhắn để rủ kèo..." 
              @keyup.enter="sendMessage"
            />
            <button class="send-btn" @click="sendMessage">
              <el-icon><Promotion /></el-icon>
            </button>
          </div>
        </main>

      </div>
    </section>

  </div>
</template>

<style scoped>
.community-page {
  background: #f8fafc;
  min-height: 100vh;
  font-family: Arial, sans-serif !important;
}

/* TẦNG 1: CHAMPIONS HERO */
.champions-hero {
  background: #0f172a;
  padding: 4rem 0 6rem;
  color: #fff;
  position: relative;
  overflow: hidden;
}

.champions-hero::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 300px; height: 300px;
  background: radial-gradient(circle, #c1ff72 -100%, transparent 70%);
  opacity: 0.15;
}

.hero-header {
  text-align: center;
  margin-bottom: 3rem;
}

.kicker {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: #c1ff72;
  font-weight: 500;
  letter-spacing: 0.2rem;
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
}

.hero-header h2 {
  font-size: 2.2rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: -0.01em;
}

.champions-slider {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-bottom: 4rem;
  flex-wrap: wrap;
}

.champion-mini-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  min-width: 260px;
  transition: all 0.3s;
}

.champion-mini-card:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-5px);
  border-color: #c1ff72;
}

.champ-avatar {
  position: relative;
  width: 60px; height: 60px;
}

.champ-avatar img {
  width: 100%; height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #c1ff72;
}

.rank-badge {
  position: absolute;
  bottom: -5px; right: -5px;
  background: #c1ff72;
  color: #000;
  font-size: 0.65rem;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 10px;
}

.champ-info h3 { font-size: 1.1rem; font-weight: 500; margin-bottom: 0.2rem; color: #fff; }
.champ-elo { font-size: 0.85rem; color: #c1ff72; font-weight: 500; }

.search-bar-container {
  max-width: 700px;
  margin: 0 auto;
}

:deep(.global-search .el-input__wrapper) {
  background: rgba(255,255,255,0.1);
  box-shadow: none !important;
  border: 1px solid rgba(255,255,255,0.2) !important;
}

:deep(.global-search input) {
  color: #fff;
  height: 54px;
}

/* SOCIAL GRID */
.interaction-zone {
  margin-top: -3rem;
  padding-bottom: 4rem;
}

.social-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 2rem;
  align-items: start;
}

/* ONLINE SIDEBAR */
.online-sidebar {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 10px 25px rgba(0,0,0,0.02);
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.sidebar-header h4 {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.05em;
}

.online-list {
  padding: 1rem;
  max-height: 500px;
  overflow-y: auto;
}

.online-user {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  border-radius: 8px;
  transition: background 0.2s;
  cursor: pointer;
}

.online-user:hover { background: #f1f5f9; }

.user-avatar-wrap { position: relative; width: 42px; height: 42px; }
.user-avatar-wrap img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }

.status-dot {
  position: absolute;
  bottom: 0; right: 0;
  width: 12px; height: 12px;
  border-radius: 50%;
  border: 2px solid #fff;
}
.status-dot.online { background: #10b981; }
.status-dot.away { background: #f59e0b; }

.user-detail { flex: 1; display: flex; flex-direction: column; }
.u-name { font-size: 0.9rem; font-weight: 500; color: #1e293b; }
.u-elo { font-size: 0.75rem; color: #64748b; }

.chat-trigger {
  width: 36px; height: 36px;
  border-radius: 50%;
  border: none;
  background: #f1f5f9;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}
.chat-trigger:hover { background: #c1ff72; color: #000; }

.sidebar-footer { padding: 1rem; }
.btn-all-players {
  width: 100%;
  padding: 0.75rem;
  background: #fff;
  border: 1px dashed #e2e8f0;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  color: #146250;
  cursor: pointer;
}

/* COMMUNITY CHAT */
.community-chat {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  height: 650px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 25px rgba(0,0,0,0.02);
}

.chat-header {
  padding: 1.25rem 2rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-info { display: flex; align-items: center; gap: 1.5rem; }

.chat-avatar-group { display: flex; align-items: center; }
.chat-avatar-group img {
  width: 32px; height: 32px;
  border-radius: 50%;
  border: 2px solid #fff;
  margin-left: -10px;
}
.chat-avatar-group img:first-child { margin-left: 0; }
.chat-avatar-group .plus-count {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: #f1f5f9;
  border: 2px solid #fff;
  margin-left: -10px;
  font-size: 0.7rem;
  display: flex; align-items: center; justify-content: center;
  font-weight: 600; color: #64748b;
}

.chat-title h4 { font-size: 1rem; font-weight: 500; color: #1e293b; margin-bottom: 0.1rem; }
.chat-title p { font-size: 0.75rem; color: #64748b; }

.chat-messages-area {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  background: #fafbfc;
}

.message-row { display: flex; gap: 1rem; max-width: 80%; }
.message-row.is-me { align-self: flex-end; flex-direction: row-reverse; }

.msg-avatar img { width: 36px; height: 36px; border-radius: 50%; background: #e2e8f0; }

.msg-content { display: flex; flex-direction: column; gap: 0.3rem; }
.msg-meta { display: flex; gap: 0.5rem; align-items: baseline; }
.msg-user { font-size: 0.75rem; font-weight: 600; color: #475569; }
.msg-time { font-size: 0.65rem; color: #94a3b8; }

.msg-bubble {
  background: #fff;
  padding: 0.75rem 1rem;
  border-radius: 0 12px 12px 12px;
  font-size: 0.95rem;
  color: #334155;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  line-height: 1.5;
}

.is-me .msg-bubble {
  background: #c1ff72;
  color: #000;
  border-radius: 12px 12px 0 12px;
}
.is-me .msg-meta { flex-direction: row-reverse; }

.is-admin .msg-bubble {
  background: #fef2f2;
  border: 1px solid #fee2e2;
  color: #991b1b;
}

.chat-input-area {
  padding: 1.5rem 2rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.input-actions { color: #94a3b8; cursor: pointer; font-size: 1.2rem; }
.input-actions:hover { color: #c1ff72; }

.chat-input-area input {
  flex: 1;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  padding: 0.8rem 1.2rem;
  border-radius: 25px;
  outline: none;
  font-size: 0.95rem;
  transition: all 0.2s;
}
.chat-input-area input:focus { border-color: #c1ff72; background: #fff; }

.send-btn {
  width: 44px; height: 44px;
  border-radius: 50%;
  background: #c1ff72;
  color: #000;
  border: none;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem;
  transition: transform 0.2s;
}
.send-btn:hover { transform: scale(1.05); }

@media (max-width: 1024px) {
  .social-grid { grid-template-columns: 1fr; }
  .online-sidebar { order: 1; }
}

@media (max-width: 768px) {
  .hero-header h2 { font-size: 1.6rem; }
  .champions-slider { gap: 1rem; }
  .community-chat { height: 500px; }
}
</style>
