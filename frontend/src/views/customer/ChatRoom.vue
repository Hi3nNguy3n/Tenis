<template>
  <div class="chat-app">
    <div class="loading-screen" v-if="isLoading">
      <div class="spinner"></div>
      <p>Đang đồng bộ dữ liệu người dùng...</p>
    </div>

    <div class="error-screen" v-else-if="!isConnected">
      <h2>Bạn chưa đăng nhập!</h2>
      <p>Vui lòng đăng nhập hệ thống để sử dụng tính năng Chat.</p>
    </div>

    <div class="chat-layout" v-else>
      <div class="sidebar">
        <div class="my-profile">
          <div class="avatar">😎</div>
          <div class="info">
            <b>{{ myProfile.full_name }}</b>
            <span class="status">ID: {{ myProfile.id }}</span>
          </div>
          <button @click="disconnectAll" class="btn-logout">Ngắt</button>
        </div>

        <div 
          :class="['chat-item', activeTab === 'global' ? 'active' : '']" 
          @click="selectGlobalChat"
        >
          <div class="avatar bg-global">🌍</div>
          <div class="info">
            <b>Kênh Hệ Thống</b>
            <span>Chat với mọi người</span>
          </div>
        </div>

        <div class="divider"></div>

        <div class="search-section">
          <div class="search-box">
            <input v-model="searchKeyword" @keyup.enter="searchUsers" type="text" placeholder="Tìm tên đối thủ..." />
            <button @click="searchUsers">Tìm</button>
          </div>
        </div>

        <div class="friend-list">
          <div v-if="searchResults.length > 0">
            <div class="section-title">🔍 Kết quả tìm kiếm</div>
            <div 
              v-for="user in searchResults" :key="'search-' + user.id"
              :class="['chat-item', activeTab === user.id ? 'active' : '']"
              @click="openPrivateChat(user)"
            >
              <div class="avatar bg-private">👤</div>
              <div class="info">
                <b>{{ user.full_name }}</b>
                <span>ID: {{ user.id }}</span>
              </div>
            </div>
          </div>

          <div class="section-title">📩 Tin nhắn gần đây</div>
          <div v-if="recentChats.length === 0" class="no-result">Chưa có hội thoại nào.</div>
          
          <div 
            v-for="chat in recentChats" :key="'recent-' + chat.id"
            :class="['chat-item', activeTab === chat.id ? 'active' : '']"
            @click="openPrivateChat(chat)"
          >
            <div class="avatar bg-recent">👤</div>
            <div class="info">
              <b :class="{'unread-text': chat.hasNew}">{{ chat.full_name }}</b>
              <span :class="{'unread-text': chat.hasNew}">{{ chat.lastMsg || 'Nhấn để chat...' }}</span>
            </div>
            <div v-if="chat.hasNew" class="unread-dot"></div>
          </div>
        </div>
      </div>

      <div class="main-chat">
        <div class="chat-header">
          <h3>{{ activeTabName }}</h3>
        </div>

        <div class="messages-container" ref="messagesBox">
          <div v-if="currentMessages.length === 0" class="empty-chat">
            Chưa có tin nhắn nào. Hãy gửi lời chào!
          </div>
          
          <div 
            v-for="(msg, index) in currentMessages" :key="index"
            :class="['message-wrapper', msg.isMine ? 'mine' : 'theirs']"
          >
            <span class="sender-name" v-if="!msg.isMine">{{ msg.senderName }}</span>
            <div class="bubble">{{ msg.text }}</div>
          </div>
        </div>

        <div class="input-area">
          <input 
            v-model="newMessage" 
            @keyup.enter="sendMessage"
            type="text" 
            placeholder="Nhập tin nhắn..." 
          />
          <button @click="sendMessage" class="btn-send">Gửi 🚀</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import apiClient from '../../services/apiClient';

const isLoading = ref(true);
const isConnected = ref(false);
const token = ref('');
const myProfile = ref({ id: null, full_name: '' }); 

const searchKeyword = ref('');
const searchResults = ref([]);
const recentChats = ref([]); // Danh sách Hộp thư đến
const activeTab = ref('global');
const activeTabName = ref('🌍 Kênh Hệ Thống');
const newMessage = ref('');
const messagesBox = ref(null);

const globalMessages = ref([]);
const privateMessages = ref({});

let wsGlobal = null;
let wsPrivate = null;

const currentMessages = computed(() => {
  return activeTab.value === 'global' ? globalMessages.value : (privateMessages.value[activeTab.value] || []);
});

// --- KHỞI CHẠY ---
onMounted(async () => {
  token.value = localStorage.getItem('saigon_tennis_access_token'); 
  const userStr = localStorage.getItem('saigon_tennis_user');
  
  if (!token.value || !userStr) {
    isLoading.value = false;
    return;
  }

  try {
    const userObj = JSON.parse(userStr);
    myProfile.value = {
        id: Number(userObj.user_id), // Lấy đúng user_id từ ảnh LocalStorage của Phú
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

// --- QUẢN LÝ INBOX (RECENT CHATS) ---
const updateInbox = (senderId, senderName, message) => {
    const existing = recentChats.value.find(c => Number(c.id) === Number(senderId));
    if (existing) {
        existing.lastMsg = message;
        if (activeTab.value !== senderId) existing.hasNew = true;
        // Đẩy lên đầu danh sách
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
  const baseWsUrl = `ws://localhost:8001/api/chat/ws`;
  const safeName = encodeURIComponent(myProfile.value.full_name);
  const myId = myProfile.value.id; 

  wsGlobal = new WebSocket(`${baseWsUrl}/global?token=${token.value}&sender_name=${safeName}`);
  wsGlobal.onopen = () => { isConnected.value = true; };
  wsGlobal.onmessage = (event) => {
    const data = JSON.parse(event.data);
    globalMessages.value.push({
      text: data.message,
      senderName: data.sender_name,
      isMine: Number(data.sender_id) === Number(myId)
    });
    scrollToBottom();
  };

  wsPrivate = new WebSocket(`${baseWsUrl}/private?token=${token.value}&sender_name=${safeName}`);
  wsPrivate.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (Number(data.sender_id) === Number(myId)) return;

    const fromId = Number(data.sender_id);
    
    // Lưu tin nhắn vào tab riêng
    if (!privateMessages.value[fromId]) privateMessages.value[fromId] = [];
    privateMessages.value[fromId].push({
      text: data.message,
      senderName: data.sender_name,
      isMine: false
    });

    // Cập nhật vào danh sách "Tin nhắn gần đây"
    updateInbox(fromId, data.sender_name, data.message);
    scrollToBottom();
  };
};

// --- TÌM KIẾM ---
const searchUsers = async () => {
  try {
    const data = await apiClient.get(`/api/players/search?keyword=${searchKeyword.value}`)
    searchResults.value = data
  } catch (error) {
    console.error("Lỗi tìm kiếm:", error.message)
  }
};
// --- CHUYỂN ĐỔI TAB CHAT ---
const selectGlobalChat = () => {
    activeTab.value = 'global';
    activeTabName.value = '🌍 Kênh Hệ Thống';
    scrollToBottom();
};

const openPrivateChat = async (user) => {
  activeTab.value = user.id;
  activeTabName.value = `👤 Chat với: ${user.full_name}`;
  
  // Xóa báo tin nhắn mới nếu có
  const chat = recentChats.value.find(c => Number(c.id) === Number(user.id));
  if (chat) chat.hasNew = false;
  else {
      recentChats.value.unshift({ id: user.id, full_name: user.full_name, lastMsg: '' });
  }

  if (!privateMessages.value[user.id]) privateMessages.value[user.id] = [];
  
  // Tải lịch sử chat riêng
  try {
      const res = await fetch(`http://localhost:8001/api/chat/history/private/${user.id}?token=${token.value}`);
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
    const history = await apiClient.get('/api/chat/history/global', { 
        useChatApi: true 
    })
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
    
    // Cập nhật tin nhắn cuối trong inbox của chính mình
    const chat = recentChats.value.find(c => Number(c.id) === Number(activeTab.value));
    if (chat) chat.lastMsg = newMessage.value;
  }
  newMessage.value = '';
  scrollToBottom();
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesBox.value) messagesBox.value.scrollTop = messagesBox.value.scrollHeight;
  });
};

const disconnectAll = () => {
  if (wsGlobal) wsGlobal.close();
  if (wsPrivate) wsPrivate.close();
  isConnected.value = false;
};
</script>

<style scoped>
* { box-sizing: border-box; }
.chat-app { height: 100vh; display: flex; justify-content: center; align-items: center; background: #e9eaee; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.loading-screen, .error-screen { width: 100%; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; background: #f5f6fa; }
.spinner { width: 40px; height: 40px; border: 4px solid #ccc; border-top-color: #0084ff; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px; }
@keyframes spin { to { transform: rotate(360deg); } }

.chat-layout { display: flex; width: 1000px; height: 80vh; background: white; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); overflow: hidden; }
.sidebar { width: 320px; background: #f5f6fa; border-right: 1px solid #ddd; display: flex; flex-direction: column; }
.my-profile { padding: 20px; display: flex; align-items: center; gap: 10px; background: white; border-bottom: 1px solid #ddd; }
.my-profile .info { flex: 1; display: flex; flex-direction: column; }
.status { font-size: 12px; color: #4CAF50; }
.btn-logout { background: #ffebee; color: #f44336; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; }

.chat-item { display: flex; align-items: center; gap: 12px; padding: 15px 20px; cursor: pointer; transition: background 0.2s; border-bottom: 1px solid #eee; }
.chat-item:hover { background: #e0e4eb; }
.chat-item.active { background: #e3f2fd; border-left: 4px solid #0084ff; }
.avatar { width: 45px; height: 45px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 24px; background: #ddd; }
.bg-global { background: #e8f5e9; }
.bg-private { background: #fff3e0; }
.chat-item .info { display: flex; flex-direction: column; }
.chat-item .info span { font-size: 12px; color: #888; }

.divider { height: 1px; background: #ddd; margin: 10px 0; }
.search-section { padding: 0 20px; margin-bottom: 10px; }
.search-box { display: flex; margin-top: 5px; }
.search-box input { flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 5px 0 0 5px; outline: none; }
.search-box button { padding: 8px 15px; background: #0084ff; color: white; border: none; border-radius: 0 5px 5px 0; cursor: pointer; }

.friend-list { flex: 1; overflow-y: auto; }
.main-chat { flex: 1; display: flex; flex-direction: column; background: white; }
.chat-header { padding: 20px; border-bottom: 1px solid #ddd; background: white; }
.chat-header h3 { margin: 0; color: #333; }

.messages-container { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #f0f2f5; }
.empty-chat { text-align: center; color: #888; margin-top: 50px; font-style: italic; }

.message-wrapper { max-width: 60%; display: flex; flex-direction: column; }
.message-wrapper.mine { align-self: flex-end; align-items: flex-end; }
.message-wrapper.theirs { align-self: flex-start; align-items: flex-start; }
.sender-name { font-size: 11px; color: #888; margin-bottom: 3px; padding: 0 5px; }
.bubble { padding: 12px 16px; border-radius: 18px; font-size: 15px; line-height: 1.4; word-wrap: break-word; }
.mine .bubble { background: #0084ff; color: white; border-bottom-right-radius: 4px; }
.theirs .bubble { background: white; color: black; border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }

.input-area { padding: 20px; background: white; border-top: 1px solid #ddd; display: flex; gap: 10px; }
.input-area input { flex: 1; padding: 15px; border: 1px solid #ddd; border-radius: 25px; font-size: 15px; outline: none; background: #f0f2f5; }
.input-area input:focus { border-color: #0084ff; background: white; }
.btn-send { padding: 0 25px; background: #0084ff; color: white; border: none; border-radius: 25px; font-weight: bold; cursor: pointer; transition: 0.2s; }
.btn-send:hover { background: #0073e6; }
</style>