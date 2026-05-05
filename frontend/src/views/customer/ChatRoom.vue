<template>
  <!-- Nếu chưa đăng nhập thì không hiển thị Widget Chat -->
  <div v-if="isLoggedIn" class="floating-chat-widget tech-chat-theme">
    <!-- NÚT TRIGGER (ICON GÓC MÀN HÌNH) -->
    <button class="chat-trigger-btn" @click="toggleChat" :class="{ 'is-active': isOpen }">
      <div class="btn-glow"></div>
      <el-icon v-if="!isOpen" class="trigger-icon"><ChatDotRound /></el-icon>
      <el-icon v-else class="trigger-icon"><Close /></el-icon>
      <span class="unread-badge" v-if="totalUnread > 0 && !isOpen">{{ totalUnread }}</span>
    </button>

    <!-- CỬA SỔ CHAT KÍNH MỜ -->
    <div class="chat-window glass-panel" :class="{ 'is-open': isOpen }">
      
      <!-- SỬA: THÊM TRẠNG THÁI LỖI KẾT NỐI -->
      <div v-if="!isConnected" class="chat-disconnected-state">
         <el-icon class="disconnected-icon"><WarningFilled /></el-icon>
         <h3>Kết nối thất bại</h3>
         <p>Hệ thống trò chuyện hiện đang bảo trì hoặc mất kết nối mạng. Vui lòng thử lại sau.</p>
         <button @click="connectAll" class="btn-retry">Thử kết nối lại</button>
      </div>
      <template v-else>
        <!-- HEADER CHUNG -->
        <div class="chat-header">
          <div class="header-left">
            <button v-if="currentView === 'chat'" @click="goBack" class="btn-back">
              <el-icon><ArrowLeft /></el-icon>
            </button>
            <div class="header-title">
              <h3>{{ currentView === 'list' ? 'MESSAGES' : activeTabName }}</h3>
              <div v-if="currentView === 'chat'" class="online-status">
                <span class="status-dot"></span> Online
              </div>
            </div>
          </div>
        </div>

        <!-- VIEW 1: DANH SÁCH & TÌM KIẾM -->
        <div class="chat-body list-view" v-show="currentView === 'list'">
          
          <!-- Thanh tìm kiếm -->
          <div class="search-wrap">
            <el-input 
              v-model="searchKeyword" 
              placeholder="Tìm kiếm tài năng..." 
              :prefix-icon="Search"
              clearable
              class="tech-search"
            />
          </div>

          <div class="scroll-container">
            <!-- Kênh Hệ Thống -->
            <div class="chat-list-item global-room" @click="selectGlobalChat">
              <div class="avatar-box gradient-bg">🌍</div>
              <div class="item-info">
                <h4>Kênh Cộng Đồng</h4>
                <p>Trò chuyện với mọi người</p>
              </div>
            </div>

            <div class="divider"></div>

            <!-- Kết quả tìm kiếm -->
            <div v-if="searchResults.length > 0" class="section-group">
              <span class="section-label">TÌM KIẾM</span>
              <div 
                v-for="user in searchResults" :key="'search-' + user.id"
                class="chat-list-item"
                @click="openPrivateChat(user)"
              >
                <div class="avatar-box dark-bg"><el-icon><User /></el-icon></div>
                <div class="item-info">
                  <h4>{{ user.full_name }}</h4>
                  <p>ID: {{ user.id }}</p>
                </div>
              </div>
            </div>

            <!-- Tin nhắn gần đây (Inbox) -->
            <div class="section-group">
              <span class="section-label">GẦN ĐÂY</span>
              <div v-if="recentChats.length === 0 && searchResults.length === 0" class="empty-state">
                Chưa có cuộc trò chuyện nào.
              </div>
              
              <div 
                v-for="chat in recentChats" :key="'recent-' + chat.id"
                class="chat-list-item"
                @click="openPrivateChat(chat)"
              >
                <div class="avatar-box dark-bg"><el-icon><User /></el-icon></div>
                <div class="item-info">
                  <h4 :class="{ 'is-unread': chat.hasNew }">{{ chat.full_name }}</h4>
                  <p :class="{ 'is-unread': chat.hasNew }">{{ chat.lastMsg || 'Nhấn để bắt đầu chat...' }}</p>
                </div>
                <div v-if="chat.hasNew" class="unread-dot"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- VIEW 2: KHUNG CHAT -->
        <div class="chat-body chat-room-view" v-show="currentView === 'chat'">
          <div class="messages-area" ref="messagesBox">
            <div v-if="currentMessages.length === 0" class="empty-chat-room">
              <el-icon class="empty-icon"><ChatLineRound /></el-icon>
              <p>Khởi tạo kết nối bảo mật. Gửi lời chào!</p>
            </div>
            
            <div 
              v-for="(msg, index) in currentMessages" :key="index"
              :class="['msg-row', msg.isMine ? 'is-mine' : 'is-theirs']"
            >
              <span class="sender-name" v-if="!msg.isMine">{{ msg.senderName }}</span>
              <div class="msg-bubble">{{ msg.text }}</div>
            </div>
          </div>

          <div class="input-area">
            <input 
              v-model="newMessage" 
              @keyup.enter="sendMessage"
              type="text" 
              placeholder="Nhập tin nhắn..." 
              class="tech-input"
            />
            <button @click="sendMessage" class="btn-send" :disabled="!newMessage.trim()">
              <el-icon><Position /></el-icon>
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch, onBeforeUnmount } from 'vue';
import apiClient from '../../services/apiClient';
import { ChatDotRound, Close, ArrowLeft, Search, User, Position, ChatLineRound , WarningFilled} from '@element-plus/icons-vue';

// --- TRẠNG THÁI GIAO DIỆN MỚI ---
const isOpen = ref(false);
const currentView = ref('list'); // 'list' hoặc 'chat'

const isLoading = ref(true);
const isConnected = ref(false);
const token = ref('');
const myProfile = ref({ id: null, full_name: '' }); 

const searchKeyword = ref('');
const searchResults = ref([]);
const recentChats = ref([]); 
const activeTab = ref('global');
const activeTabName = ref('🌍 Kênh Hệ Thống');
const newMessage = ref('');
const messagesBox = ref(null);
const isLoggedIn = ref(false);
const globalMessages = ref([]);
const privateMessages = ref({});

let wsGlobal = null;
let wsPrivate = null;

const currentMessages = computed(() => {
  return activeTab.value === 'global' ? globalMessages.value : (privateMessages.value[activeTab.value] || []);
});

const totalUnread = computed(() => {
  return recentChats.value.filter(c => c.hasNew).length;
});

// --- TOGGLE GIAO DIỆN ---
const toggleChat = () => {
  isOpen.value = !isOpen.value;
  if (isOpen.value && currentView.value === 'chat') {
    scrollToBottom();
  }
};

const goBack = () => {
  currentView.value = 'list';
};

// --- LOGIC TÌM KIẾM TỰ ĐỘNG (DEBOUNCE) ---
let searchTimer = null;
watch(searchKeyword, (newVal) => {
  clearTimeout(searchTimer);
  if (!newVal.trim()) {
    searchResults.value = [];
    return;
  }
  // Chờ 0.5s sau khi người dùng ngừng gõ mới gọi API
  searchTimer = setTimeout(async () => {
    try {
      const data = await apiClient.get(`/api/players/search?keyword=${encodeURIComponent(newVal.trim())}`);
      searchResults.value = (Array.isArray(data) ? data : []).filter(u => Number(u.id) !== Number(myProfile.value.id));
    } catch (error) {
      console.error("Lỗi tìm kiếm:", error.message);
    }
  }, 500);
});

// --- KHỞI CHẠY ---
onMounted(async () => {
  token.value = localStorage.getItem('saigon_tennis_access_token'); 
  const userStr = localStorage.getItem('saigon_tennis_user');
  
  if (!token.value || !userStr) {
    isLoggedIn.value = false;
    isLoading.value = false;
    return;
  }

  isLoggedIn.value = true;

  try {
    const userObj = JSON.parse(userStr);
    myProfile.value = {
        id: Number(userObj.user_id), 
        full_name: userObj.full_name
    };

    await loadGlobalHistory();
    connectAll(); 
  } catch (error) {
    console.error("Lỗi khởi tạo:", error);
  } finally {
    isLoading.value = false;
  }
});

onBeforeUnmount(() => {
  disconnectAll();
});

// --- QUẢN LÝ INBOX ---
const updateInbox = (senderId, senderName, message) => {
    const existing = recentChats.value.find(c => Number(c.id) === Number(senderId));
    if (existing) {
        existing.lastMsg = message;
        // Chỉ hiện chấm đỏ nếu đang không mở đúng tab đó
        if (activeTab.value !== senderId || currentView.value !== 'chat' || !isOpen.value) {
          existing.hasNew = true;
        }
        recentChats.value = [existing, ...recentChats.value.filter(c => Number(c.id) !== Number(senderId))];
    } else {
        recentChats.value.unshift({
            id: senderId,
            full_name: senderName,
            lastMsg: message,
            hasNew: true
        });
    }
};

// --- KẾT NỐI WEBSOCKET ---
const connectAll = () => {
  const baseWsUrl = `${import.meta.env.VITE_WS_CHAT_URL}/api/chat/ws`;
  const safeName = encodeURIComponent(myProfile.value.full_name);
  const myId = myProfile.value.id; 

  wsGlobal = new WebSocket(`${baseWsUrl}/global?token=${token.value}&sender_name=${safeName}`);
  wsGlobal.onopen = () => { isConnected.value = true; };
  wsGlobal.onerror = (error) => {
    console.error("WebSocket Error:", error);
    isConnected.value = false;
  };
  wsGlobal.onclose = () => {
    isConnected.value = false;
  };
  wsGlobal.onmessage = (event) => {
    const data = JSON.parse(event.data);
    globalMessages.value.push({
      text: data.message,
      senderName: data.sender_name,
      isMine: Number(data.sender_id) === Number(myId)
    });
    if (isOpen.value && currentView.value === 'chat' && activeTab.value === 'global') {
      scrollToBottom();
    }
  };

  wsPrivate = new WebSocket(`${baseWsUrl}/private?token=${token.value}&sender_name=${safeName}`);
  wsPrivate.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (Number(data.sender_id) === Number(myId)) return;

    const fromId = Number(data.sender_id);
    
    if (!privateMessages.value[fromId]) privateMessages.value[fromId] = [];
    privateMessages.value[fromId].push({
      text: data.message,
      senderName: data.sender_name,
      isMine: false
    });

    updateInbox(fromId, data.sender_name, data.message);
    if (isOpen.value && currentView.value === 'chat' && activeTab.value === fromId) {
      scrollToBottom();
    }
  };
};

// --- CHUYỂN ĐỔI TAB CHAT ---
const selectGlobalChat = () => {
    activeTab.value = 'global';
    activeTabName.value = 'Cộng Đồng';
    currentView.value = 'chat';
    scrollToBottom();
};

const openPrivateChat = async (user) => {
  activeTab.value = user.id;
  activeTabName.value = user.full_name;
  currentView.value = 'chat';
  
  const chat = recentChats.value.find(c => Number(c.id) === Number(user.id));
  if (chat) chat.hasNew = false;
  else {
      recentChats.value.unshift({ id: user.id, full_name: user.full_name, lastMsg: '' });
  }

  if (!privateMessages.value[user.id]) privateMessages.value[user.id] = [];
  
  try {
      const res = await fetch(`${import.meta.env.VITE_API_CHAT_URL}/api/chat/history/private/${user.id}?token=${token.value}`);
      if (res.ok) {
          const history = await res.json();
          privateMessages.value[user.id] = history.map(msg => ({
              text: msg.message,
              senderName: msg.sender_name,
              isMine: Number(msg.sender_id) === Number(myProfile.value.id)
          }));
      }
  } catch(e) { console.error(e); }
  scrollToBottom();
};

const loadGlobalHistory = async () => {
  try {
    const history = await apiClient.get('/api/chat/history/global', { useChatApi: true })
    globalMessages.value = history.map(msg => ({
        text: msg.message,
        senderName: msg.sender_name,
        isMine: Number(msg.sender_id) === Number(myProfile.value.id)
    }))
  } catch (error) {
    console.error("Lỗi tải lịch sử:", error.message)
  }
};

const sendMessage = () => {
  if (!newMessage.value.trim()) return;
  const myName = myProfile.value.full_name;

  if (activeTab.value === 'global') {
    wsGlobal.send(newMessage.value);
  } else {
    const payload = JSON.stringify({
      receiver_id: Number(activeTab.value),
      message: newMessage.value
    });
    wsPrivate.send(payload);

    if (!privateMessages.value[activeTab.value]) privateMessages.value[activeTab.value] = [];
    privateMessages.value[activeTab.value].push({
      text: newMessage.value,
      senderName: myName,
      isMine: true
    });
    
    const chat = recentChats.value.find(c => Number(c.id) === Number(activeTab.value));
    if (chat) chat.lastMsg = newMessage.value;
  }
  newMessage.value = '';
  scrollToBottom();
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesBox.value) {
      messagesBox.value.scrollTop = messagesBox.value.scrollHeight;
    }
  });
};

const disconnectAll = () => {
  if (wsGlobal) wsGlobal.close();
  if (wsPrivate) wsPrivate.close();
  isConnected.value = false;
};
</script>

<style scoped>
/* =======================================================
   TECH THEME VARIABLES
   ======================================================= */
.tech-chat-theme {
  --bg-base: #09090b; 
  --glass-bg: rgba(24, 24, 27, 0.85); /* Đen mờ */
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-hover: rgba(255, 255, 255, 0.08);
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --accent-cyan: #06b6d4;
  --accent-purple: #a855f7;
  --gradient-main: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
  
  font-family: 'Inter', -apple-system, sans-serif;
}

/* =======================================================
   FLOATING WIDGET CONTAINER
   ======================================================= */
.floating-chat-widget {
  position: fixed;
  bottom: 30px;
  right: 30px;
  z-index: 9999;
}

/* =======================================================
   TRIGGER BUTTON (NÚT BẤM GÓC)
   ======================================================= */
.chat-trigger-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--bg-base);
  border: 1px solid var(--glass-border);
  color: var(--text-main);
  font-size: 1.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}

.btn-glow {
  position: absolute;
  inset: -2px;
  border-radius: 50%;
  background: var(--gradient-main);
  z-index: -1;
  opacity: 0.8;
  filter: blur(8px);
  transition: opacity 0.3s ease;
}

.chat-trigger-btn:hover {
  transform: translateY(-4px) scale(1.05);
}
.chat-trigger-btn:hover .btn-glow { opacity: 1; filter: blur(12px); }

.trigger-icon { z-index: 2; }

.chat-trigger-btn.is-active {
  transform: rotate(90deg);
  background: var(--glass-bg);
}
.chat-trigger-btn.is-active .btn-glow { opacity: 0; }

.unread-badge {
  position: absolute;
  top: -4px; right: -4px;
  background: var(--accent-cyan);
  color: #000;
  font-size: 0.75rem; font-weight: 800;
  min-width: 22px; height: 22px;
  border-radius: 999px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 12px var(--accent-cyan);
  z-index: 5;
}

/* =======================================================
   CHAT WINDOW (GLASS PANEL)
   ======================================================= */
.chat-window {
  position: absolute;
  bottom: 85px;
  right: 0;
  width: 380px;
  height: 600px;
  max-height: calc(100vh - 140px);
  border-radius: 24px;
  display: flex; flex-direction: column; overflow: hidden;
  
  /* Kính mờ phong cách Tech */
  background: var(--glass-bg);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--glass-border);
  box-shadow: 0 30px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.1);
  
  /* Animation */
  transform-origin: bottom right;
  transform: scale(0.9);
  opacity: 0; pointer-events: none;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.chat-window.is-open {
  transform: scale(1);
  opacity: 1; pointer-events: auto;
}

/* --- HEADER --- */
.chat-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--glass-border);
  display: flex; align-items: center; flex-shrink: 0;
  background: rgba(0,0,0,0.2);
}

.header-left { display: flex; align-items: center; gap: 12px; }

.btn-back {
  background: transparent; border: none;
  color: var(--text-muted); font-size: 1.2rem; cursor: pointer;
  padding: 0; display: flex; align-items: center; transition: 0.2s;
}
.btn-back:hover { color: var(--text-main); transform: translateX(-2px); }

.header-title h3 {
  margin: 0; font-size: 1rem; font-weight: 800; color: var(--text-main);
  letter-spacing: 0.05em;
}

.online-status {
  font-size: 0.75rem; color: var(--text-muted); font-weight: 500;
  display: flex; align-items: center; gap: 6px; margin-top: 4px;
}
.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent-cyan);
  box-shadow: 0 0 8px var(--accent-cyan);
}

/* --- BODY CHUNG --- */
.chat-body {
  flex: 1; display: flex; flex-direction: column; overflow: hidden;
}

/* =======================================================
   VIEW 1: LIST VIEW 
   ======================================================= */
.search-wrap {
  padding: 16px 20px;
  border-bottom: 1px solid var(--glass-border);
}

:deep(.tech-search .el-input__wrapper) {
  border-radius: 12px;
  background: rgba(0,0,0,0.3);
  box-shadow: none; padding: 8px 16px;
  border: 1px solid var(--glass-border);
}
:deep(.tech-search .el-input__wrapper.is-focus) {
  border-color: var(--accent-cyan);
}
:deep(.tech-search .el-input__inner) { color: var(--text-main); font-size: 0.95rem; }
:deep(.tech-search .el-input__inner::placeholder) { color: var(--text-muted); }

.scroll-container { flex: 1; overflow-y: auto; padding-bottom: 20px; }
.scroll-container::-webkit-scrollbar { width: 6px; }
.scroll-container::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }

.section-group { margin-top: 20px; }
.section-label {
  display: block; padding: 0 20px 10px; font-size: 0.7rem;
  font-weight: 800; color: var(--text-muted); letter-spacing: 0.1em;
}

.chat-list-item {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 20px; cursor: pointer; transition: background 0.2s;
}
.chat-list-item:hover { background: var(--glass-hover); }

.avatar-box {
  width: 46px; height: 46px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; color: white; flex-shrink: 0;
}
.gradient-bg { background: var(--gradient-main); }
.dark-bg { background: rgba(255,255,255,0.05); border: 1px solid var(--glass-border); color: var(--text-muted); }

.item-info { flex: 1; min-width: 0; }
.item-info h4 {
  margin: 0 0 6px 0; font-size: 0.95rem; font-weight: 700;
  color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.item-info p {
  margin: 0; font-size: 0.85rem; color: var(--text-muted);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.is-unread { font-weight: 800 !important; color: white !important; }
.unread-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--accent-cyan); flex-shrink: 0;
  box-shadow: 0 0 8px var(--accent-cyan);
}

.divider { height: 1px; background: var(--glass-border); margin: 0 20px; }
.empty-state { padding: 20px; text-align: center; color: var(--text-muted); font-size: 0.85rem; font-style: italic; }

/* =======================================================
   VIEW 2: CHAT ROOM VIEW
   ======================================================= */
.messages-area {
  flex: 1; padding: 24px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 16px;
}
.messages-area::-webkit-scrollbar { width: 6px; }
.messages-area::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }

.empty-chat-room {
  margin: auto; display: flex; flex-direction: column; align-items: center; color: var(--text-muted);
}
.empty-icon { font-size: 3rem; margin-bottom: 16px; opacity: 0.5;}

.msg-row { max-width: 85%; display: flex; flex-direction: column; }
.msg-row.is-mine { align-self: flex-end; align-items: flex-end; }
.msg-row.is-theirs { align-self: flex-start; align-items: flex-start; }

.sender-name { font-size: 0.7rem; color: var(--text-muted); margin-bottom: 6px; font-weight: 600; letter-spacing: 0.05em;}

.msg-bubble {
  padding: 12px 16px; border-radius: 16px;
  font-size: 0.95rem; line-height: 1.5; word-wrap: break-word;
}

.is-mine .msg-bubble {
  background: var(--gradient-main);
  color: white; border-bottom-right-radius: 4px;
}

.is-theirs .msg-bubble {
  background: rgba(255,255,255,0.05);
  color: var(--text-main);
  border-bottom-left-radius: 4px;
  border: 1px solid var(--glass-border);
}

/* INPUT AREA */
.input-area {
  padding: 16px 20px;
  border-top: 1px solid var(--glass-border);
  display: flex; gap: 12px; align-items: center;
  background: rgba(0,0,0,0.3);
}

.tech-input {
  flex: 1; padding: 12px 16px;
  border: 1px solid var(--glass-border); border-radius: 12px;
  font-size: 0.95rem; outline: none;
  background: rgba(255,255,255,0.05); color: var(--text-main);
  transition: 0.2s;
}
.tech-input::placeholder { color: var(--text-muted); }
.tech-input:focus { border-color: var(--accent-cyan); background: rgba(255,255,255,0.08);}

.btn-send {
  width: 44px; height: 44px; border-radius: 12px;
  background: var(--accent-cyan); color: #000; border: none;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; cursor: pointer; transition: 0.2s;
}
.btn-send:hover:not(:disabled) {
  box-shadow: 0 0 15px rgba(6, 182, 212, 0.5);
  transform: scale(1.05);
}
.btn-send:disabled {
  background: rgba(255,255,255,0.1); color: var(--text-muted); cursor: not-allowed;
}

/* =======================================================
   RESPONSIVE MOBILE
   ======================================================= */
@media (max-width: 480px) {
  .chat-window {
    position: fixed; bottom: 0; right: 0; width: 100%; height: 100%; max-height: 100%;
    border-radius: 0; z-index: 10000; border: none;
  }
  
  .chat-trigger-btn { bottom: 20px; right: 20px; z-index: 10001; }
  .chat-trigger-btn.is-active { display: none; }
  .chat-header { justify-content: space-between; padding-top: calc(env(safe-area-inset-top) + 20px);}
  .header-title { flex: 1; }
}
/* THÊM CSS NÀY VÀO CUỐI FILE */
.chat-disconnected-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 2rem;
  text-align: center;
  color: var(--text-main);
}

.disconnected-icon {
  font-size: 4rem;
  color: #ef4444; /* Đỏ cảnh báo */
  margin-bottom: 1rem;
  filter: drop-shadow(0 0 10px rgba(239, 68, 68, 0.5));
}

.chat-disconnected-state h3 {
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0 0 8px;
}

.chat-disconnected-state p {
  font-size: 0.9rem;
  color: var(--text-muted);
  line-height: 1.5;
  margin-bottom: 1.5rem;
}

.btn-retry {
  background: transparent;
  border: 1px solid var(--accent-cyan);
  color: var(--accent-cyan);
  padding: 8px 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.3s;
}

.btn-retry:hover {
  background: var(--accent-cyan);
  color: var(--bg-base);
  box-shadow: 0 0 15px rgba(6, 182, 212, 0.4);
}
</style>