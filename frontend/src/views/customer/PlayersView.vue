<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
import { Search, Trophy, ChatDotRound, Microphone, Promotion, CircleCheck, Close, User, Message, Delete, Minus, Expand, ChatLineRound } from '@element-plus/icons-vue'
import apiClient from '../../services/apiClient'
import { newsService } from '../../services/newsService'
import { useAuthStore } from '../../stores/auth'
import { currentLocale, t } from '../../utils/locale'
import { ElMessageBox, ElMessage } from 'element-plus'

const chatApiBase = import.meta.env.VITE_API_CHAT_URL || 'http://127.0.0.1:8001'
const chatWsBase = chatApiBase.replace(/^http/, 'ws')
const isVideo = (url) => {
  if (!url) return false
  return url.match(/\.(mp4|webm|ogg|mov)(\?.*)?$/i) !== null
}
const loading = ref(true)
const players = ref([])
const recentWinners = ref([])
const latestNews = ref([])
const searchQuery = ref('')
const token = ref('')
const myProfile = ref({ id: null, full_name: '' })
const isConnected = ref(false)
const selectedPrivatePlayer = ref(null)
const globalNewMessage = ref('')
const privateNewMessage = ref('')
const isPrivateTyping = ref(false)
const typingTimeout = ref(null)
const typingUsers = ref({})
const globalMessagesBox = ref(null)
const privateMessagesBox = ref(null)
const globalMessages = ref([])
const privateMessages = ref({})
const recentChatsArr = ref([])
const authStore = useAuthStore()
const communityUnreadCount = ref(0)
const privateDrafts = ref({})

// State: toggling between 1v1 chat and community chat in the MAIN area
const isMainCommunityView = ref(false)

const presenceKeyPrefix = 'saigon_tennis_presence_'
let presenceTimer = null
let inboxTimer = null
let wsGlobal = null
let wsPrivate = null

const visiblePlayers = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  const selfId = Number(myProfile.value.id)
  const baseList = players.value.filter(p => Number(p.chat_user_id || p.id) !== selfId)
  if (!keyword) return baseList
  return baseList.filter(p => p.full_name?.toLowerCase().includes(keyword))
})

const unreadCountById = computed(() => {
  return recentChatsArr.value.reduce((acc, chat) => {
    acc[Number(chat.id)] = chat.unreadCount || 0
    return acc
  }, {})
})

const recentChatPlayers = computed(() => {
  return recentChatsArr.value
    .slice()
    .sort((a, b) => {
      const aUnread = Number(a.unreadCount || 0)
      const bUnread = Number(b.unreadCount || 0)
      if (aUnread !== bUnread) return bUnread - aUnread

      const aTime = new Date(a.updatedAt).getTime() || 0
      const bTime = new Date(b.updatedAt).getTime() || 0
      if (aTime !== bTime) return bTime - aTime

      return String(a.full_name || '').localeCompare(String(b.full_name || ''), 'vi')
    })
    .map(chat => players.value.find(p => Number(p.chat_user_id || p.id) === Number(chat.id)))
    .filter(Boolean)
})

const currentPrivateMessages = computed(() => {
  if (!selectedPrivatePlayer.value) return []
  const chatId = Number(selectedPrivatePlayer.value.chat_user_id || selectedPrivatePlayer.value.id)
  return privateMessages.value[chatId] || []
})

const currentDraft = computed({
  get() {
    if (!selectedPrivatePlayer.value) return ''
    const chatId = Number(selectedPrivatePlayer.value.chat_user_id || selectedPrivatePlayer.value.id)
    return privateDrafts.value[chatId] || ''
  },
  set(value) {
    if (!selectedPrivatePlayer.value) return
    const chatId = Number(selectedPrivatePlayer.value.chat_user_id || selectedPrivatePlayer.value.id)
    privateDrafts.value[chatId] = value
    try {
      localStorage.setItem(`saigon_tennis_private_draft_${myProfile.value.id}_${chatId}`, value)
    } catch {
      // ignore
    }
  },
})

const isPlayerActive = (player) => {
  const chatId = Number(player.chat_user_id || player.id)
  const presence = localStorage.getItem(`${presenceKeyPrefix}${chatId}`)
  return presence ? (Date.now() - Number(presence) < 15000) : false
}

const loadPlayers = async () => {
  try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/players/rankings`)
    const rankings = await res.json()
    const normalized = Array.isArray(rankings) ? rankings : []
    const enriched = await Promise.all(normalized.map(async (p) => {
      let chatUserId = Number(p.user_id || p.id)
      try {
        if (p.full_name) {
          const matches = await apiClient.get('/api/players/search', {
            params: { keyword: p.full_name },
          })
          if (Array.isArray(matches) && matches.length) {
            const exact = matches.find((m) => (m.full_name || '').trim().toLowerCase() === (p.full_name || '').trim().toLowerCase())
            chatUserId = Number((exact || matches[0]).id || chatUserId)
          }
        }
      } catch {
        // keep fallback id
      }
      return {
        ...p,
        chat_user_id: chatUserId,
        avatar_url: p.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(p.full_name)}&background=random`
      }
    }))
    players.value = enriched
    recentWinners.value = players.value.slice(0, 8)
  } catch (err) { console.error(err) }
}

const loadLatestNews = async () => {
  try {
    const data = await newsService.getAllPosts({ limit: 3 })
    latestNews.value = Array.isArray(data)
      ? data.map((post) => ({
          id: post.id,
          title: post.title,
          slug: post.slug,
          summary: post.summary || post.excerpt || '',
          thumbnail_url: post.thumbnail_url,
          media_url: post.media_url,
          created_at: post.publish_at || post.created_at,
        }))
      : []
  } catch {
    latestNews.value = []
  }
}

const formatTime = (v) => v ? new Date(v).toLocaleTimeString(currentLocale.value === 'vi' ? 'vi-VN' : 'en-US', { hour: '2-digit', minute: '2-digit', hour12: false }) : ''
const formatRelativeTime = (v) => {
  if (!v) return ''
  const diff = Date.now() - new Date(v).getTime()
  if (diff < 60000) return t('chat.justNow')
  if (diff < 3600000) return `${Math.floor(diff/60000)}p`
  if (diff < 86400000) return `${Math.floor(diff/3600000)}h`
  return `${Math.floor(diff/86400000)}d`
}

const loadGlobalHistory = async () => {
  if (!token.value) return
  try {
    const history = await apiClient.get('/api/chat/history/global', {
      useChatApi: true,
    })
    if (Array.isArray(history)) {
      globalMessages.value = history.map((m) => ({
        text: m.message,
        senderName: m.sender_name,
        isMine: Number(m.sender_id) === Number(myProfile.value.id),
        time: formatTime(m.time),
      }))
      nextTick(() => {
        if (globalMessagesBox.value) globalMessagesBox.value.scrollTop = globalMessagesBox.value.scrollHeight
      })
    }
  } catch (err) {
    console.warn('Không tải được lịch sử cộng đồng:', err)
  }
}

const loadInboxFromServer = async () => {
  if (!token.value) return
  try {
    const data = await apiClient.get('/api/chat/threads/private', { useChatApi: true, params: { token: token.value } })
    if (Array.isArray(data)) {
      const selfId = Number(myProfile.value.id)
      recentChatsArr.value = data
        .map(t => ({
          id: Number(t.id),
          full_name: t.full_name,
          lastMsg: t.lastMsg,
          unreadCount: Number(t.unreadCount || 0),
          updatedAt: t.updatedAt,
          last_sender_id: t.last_sender_id
        }))
        .filter(thread => Number(thread.id) !== selfId)
    }
  } catch (err) { console.warn(err) }
}

const hydrateDrafts = () => {
  try {
    const prefix = `saigon_tennis_private_draft_${myProfile.value.id}_`
    Object.keys(localStorage).forEach((key) => {
      if (!key.startsWith(prefix)) return
      const chatId = Number(key.replace(prefix, ''))
      if (!Number.isFinite(chatId)) return
      privateDrafts.value[chatId] = localStorage.getItem(key) || ''
    })
  } catch {
    privateDrafts.value = {}
  }
}

const updateInbox = (id, name, msg, senderId) => {
  if (Number(id) === Number(myProfile.value.id)) return
  const idx = recentChatsArr.value.findIndex(c => Number(c.id) === Number(id))
  const now = new Date().toISOString()
  if (idx > -1) {
    const item = recentChatsArr.value[idx]
    item.lastMsg = msg; item.updatedAt = now; item.last_sender_id = senderId
    if (!selectedPrivatePlayer.value || Number(selectedPrivatePlayer.value.chat_user_id || selectedPrivatePlayer.value.id) !== Number(id)) item.unreadCount++
    recentChatsArr.value.splice(idx, 1); recentChatsArr.value.unshift(item)
  } else {
    recentChatsArr.value.unshift({ id: Number(id), full_name: name, lastMsg: msg, unreadCount: 1, updatedAt: now, last_sender_id: senderId })
  }
}

const connectSockets = () => {
  if (!token.value || !myProfile.value.id) return
  const name = encodeURIComponent(myProfile.value.full_name)
  
  wsGlobal = new WebSocket(`${chatWsBase}/api/chat/ws/global?token=${token.value}&sender_name=${name}`)
  wsGlobal.onopen = () => { console.log('WS Global connected'); isConnected.value = true }
  wsGlobal.onmessage = (e) => {
    const d = JSON.parse(e.data)
    globalMessages.value.push({ text: d.message, senderName: d.sender_name, isMine: Number(d.sender_id) === Number(myProfile.value.id), time: formatTime(d.time) })
    if (!isMainCommunityView.value) communityUnreadCount.value += 1
    if (isMainCommunityView.value) nextTick(() => { if (globalMessagesBox.value) globalMessagesBox.value.scrollTop = globalMessagesBox.value.scrollHeight })
  }
  wsGlobal.onerror = (err) => console.error('WS Global Error:', err)
  wsGlobal.onclose = () => { isConnected.value = false; setTimeout(connectSockets, 5000) }

  wsPrivate = new WebSocket(`${chatWsBase}/api/chat/ws/private?token=${token.value}&sender_name=${name}`)
  wsPrivate.onopen = () => console.log('WS Private connected for user:', myProfile.value.id)
  wsPrivate.onmessage = (e) => {
    const d = JSON.parse(e.data)
    if (d.type === 'typing') {
      const typingId = Number(d.sender_id)
      if (selectedPrivatePlayer.value && Number(selectedPrivatePlayer.value.chat_user_id || selectedPrivatePlayer.value.id) === typingId) {
        isPrivateTyping.value = Boolean(d.is_typing)
        clearTimeout(typingTimeout.value)
        if (d.is_typing) {
          typingTimeout.value = setTimeout(() => {
            isPrivateTyping.value = false
          }, 2500)
        }
      }
      return
    }

    const fromId = Number(d.sender_id)
    const otherId = Number(d.receiver_id || (fromId === Number(myProfile.value.id) ? selectedPrivatePlayer.value?.chat_user_id || selectedPrivatePlayer.value?.id : fromId))
    console.log('WS Private received message from:', fromId)

    if (!privateMessages.value[otherId]) privateMessages.value[otherId] = []
    privateMessages.value[otherId].push({
      text: d.message,
      senderName: d.sender_name,
      isMine: fromId === Number(myProfile.value.id),
      time: formatTime(d.time),
      is_read: Boolean(d.is_read),
    })

    updateInbox(otherId, d.sender_name, d.message, fromId)
    if (selectedPrivatePlayer.value && Number(selectedPrivatePlayer.value.chat_user_id || selectedPrivatePlayer.value.id) === otherId) {
      apiClient.put(`/api/chat/mark-read/${otherId}`, null, { useChatApi: true, params: { token: token.value } })
      nextTick(() => { if (privateMessagesBox.value) privateMessagesBox.value.scrollTop = privateMessagesBox.value.scrollHeight })
    }
  }
  wsPrivate.onerror = (err) => console.error('WS Private Error:', err)
  wsPrivate.onclose = () => console.warn('WS Private disconnected')
}

const openPrivateChat = async (p) => {
  isMainCommunityView.value = false // Auto switch to private mode
  selectedPrivatePlayer.value = p
  const chatId = Number(p.chat_user_id || p.id)
  const item = recentChatsArr.value.find(c => Number(c.id) === chatId)
  if (item) item.unreadCount = 0
  apiClient.put(`/api/chat/mark-read/${chatId}`, null, { useChatApi: true, params: { token: token.value } })
  try {
    const h = await apiClient.get(`/api/chat/history/private/${chatId}`, { useChatApi: true, params: { token: token.value } })
    privateMessages.value[chatId] = h.map(m => ({
      text: m.message,
      senderName: m.sender_name,
      isMine: Number(m.sender_id) === Number(myProfile.value.id),
      time: formatTime(m.time),
      is_read: Boolean(m.is_read),
    }))
    await loadInboxFromServer()
    hydrateDrafts()
  } catch {
    privateMessages.value[chatId] = privateMessages.value[chatId] || []
  }
  isPrivateTyping.value = false
  nextTick(() => { if (privateMessagesBox.value) privateMessagesBox.value.scrollTop = privateMessagesBox.value.scrollHeight })
}

const toggleCommunityView = () => {
  isMainCommunityView.value = true
  communityUnreadCount.value = 0
  selectedPrivatePlayer.value = null
  nextTick(() => { if (globalMessagesBox.value) globalMessagesBox.value.scrollTop = globalMessagesBox.value.scrollHeight })
}

const sendMessage = (type) => {
  if (type === 'global') {
    if (!globalNewMessage.value.trim()) return
    if (wsGlobal?.readyState === WebSocket.OPEN) {
      wsGlobal.send(globalNewMessage.value); globalNewMessage.value = ''
    }
  } else {
    if (!currentDraft.value.trim() || !selectedPrivatePlayer.value) return
    const id = Number(selectedPrivatePlayer.value.chat_user_id || selectedPrivatePlayer.value.id)
    if (wsPrivate?.readyState === WebSocket.OPEN) {
      wsPrivate.send(JSON.stringify({ receiver_id: id, message: currentDraft.value }))
      wsPrivate.send(JSON.stringify({ type: 'typing', receiver_id: id, is_typing: false }))
      updateInbox(id, selectedPrivatePlayer.value.full_name, currentDraft.value, myProfile.value.id)
      currentDraft.value = ''
      nextTick(() => { if (privateMessagesBox.value) privateMessagesBox.value.scrollTop = privateMessagesBox.value.scrollHeight })
    }
  }
}

const emitTypingState = (isTyping) => {
  if (!selectedPrivatePlayer.value || !wsPrivate || wsPrivate.readyState !== WebSocket.OPEN) return
  const receiverId = Number(selectedPrivatePlayer.value.chat_user_id || selectedPrivatePlayer.value.id)
  wsPrivate.send(JSON.stringify({
    type: 'typing',
    receiver_id: receiverId,
    is_typing: isTyping,
  }))
}

const deleteThread = async () => {
  if (!selectedPrivatePlayer.value) return
  const id = Number(selectedPrivatePlayer.value.chat_user_id || selectedPrivatePlayer.value.id)
  try {
    await ElMessageBox.confirm(t('chat.deleteConfirm'), t('chat.deleteTitle'), { type: 'warning' })
    await apiClient.delete(`/api/chat/thread/${id}`, { useChatApi: true, params: { token: token.value } })
    privateMessages.value[id] = []; recentChatsArr.value = recentChatsArr.value.filter(c => Number(c.id) !== id)
    selectedPrivatePlayer.value = null; ElMessage.success(t('chat.deleted'))
  } catch { /* cancelled */ }
}

watch(
  () => myProfile.value.id,
  () => {
    if (!myProfile.value.id) return
    recentChatsArr.value = recentChatsArr.value.filter(thread => Number(thread.id) !== Number(myProfile.value.id))
  }
)

onMounted(async () => {
  await loadPlayers(); authStore.hydrate(); token.value = authStore.accessToken
  const user = authStore.user || {}
  myProfile.value = { id: Number(user.user_id || user.id), full_name: user.full_name || t('chat.user') }
  await loadInboxFromServer(); connectSockets()
  await loadGlobalHistory()
  await loadLatestNews()
  hydrateDrafts()
  presenceTimer = setInterval(() => { if (myProfile.value.id) localStorage.setItem(`${presenceKeyPrefix}${myProfile.value.id}`, Date.now()) }, 5000)
  inboxTimer = setInterval(loadInboxFromServer, 8000); loading.value = false
})

onBeforeUnmount(() => {
  if (wsGlobal) wsGlobal.close(); if (wsPrivate) wsPrivate.close()
  clearInterval(presenceTimer); clearInterval(inboxTimer)
  clearTimeout(typingTimeout.value)
})
</script>

<template>
  <div class="chat-app">
    <!-- Header: Hall of Fame -->
    <header class="top-honor">
      <div class="honor-label"><el-icon><Trophy /></el-icon> {{ t('players.topPlayers') }}</div>
      <div class="honor-list">
        <div v-for="(p, i) in recentWinners" :key="p.id" class="win-item" @click="openPrivateChat(p)">
          <span class="rank">#{{ i+1 }}</span>
          <img :src="p.avatar_url" />
          <div class="win-meta"><b>{{ p.full_name }}</b><p>{{ p.elo_points }} Elo</p></div>
        </div>
      </div>
      <div class="search-wrap"><el-input v-model="searchQuery" :placeholder="t('common.search')" size="small" :prefix-icon="Search" /></div>
    </header>

    <div class="main-body">
      <!-- Sidebar -->
      <aside class="sidebar-v2">
        <div class="profile-card">
          <img :src="authStore.user?.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(myProfile.full_name)}&background=146250&color=fff`" />
          <div class="p-info"><b>{{ myProfile.full_name }}</b><p>{{ t('players.online') }}</p></div>
        </div>

        <div class="sidebar-tabs">
          <button :class="{ active: !isMainCommunityView }" @click="isMainCommunityView = false">
            {{ t('players.message') }}
            <span v-if="recentChatsArr.some((chat) => Number(chat.unreadCount || 0) > 0)" class="tab-badge">
              {{ recentChatsArr.reduce((sum, chat) => sum + Number(chat.unreadCount || 0), 0) }}
            </span>
          </button>
          <button :class="{ active: isMainCommunityView }" @click="toggleCommunityView">
            {{ t('players.community') }}
            <span v-if="communityUnreadCount > 0" class="tab-badge">{{ communityUnreadCount }}</span>
          </button>
        </div>

        <div class="scroll-area">
          <div v-for="p in recentChatPlayers" :key="p.id" 
               class="user-row" :class="{ active: selectedPrivatePlayer?.id === p.id, unread: unreadCountById[p.chat_user_id || p.id] > 0 }"
               @click="openPrivateChat(p)">
            <div class="ava-box">
              <img :src="p.avatar_url" />
              <span v-if="isPlayerActive(p)" class="dot"></span>
            </div>
            <div class="u-content">
              <div class="u-name-row">
                <span class="u-name">{{ p.full_name }}</span>
                <span class="u-time">{{ formatRelativeTime(recentChatsArr.find(c => Number(c.id) === Number(p.chat_user_id || p.id))?.updatedAt) }}</span>
              </div>
              <div class="u-msg-row">
                <span class="u-msg">
                  <span v-if="recentChatsArr.find(c => Number(c.id) === Number(p.chat_user_id || p.id))?.last_sender_id === myProfile.id" class="msg-prefix">{{ t('chat.me') }}: </span>
                  {{ recentChatsArr.find(c => Number(c.id) === Number(p.chat_user_id || p.id))?.lastMsg }}
                </span>
                <div class="u-badge-dot" v-if="unreadCountById[p.chat_user_id || p.id] > 0">{{ unreadCountById[p.chat_user_id || p.id] }}</div>
              </div>
            </div>
          </div>

          <div v-if="!recentChatPlayers.length" class="sidebar-empty-state">
            <div class="sidebar-empty-title">{{ t('players.noConversations') }}</div>
            <div class="sidebar-empty-text">
              {{ t('players.startMessaging') }}
            </div>
          </div>
        </div>
      </aside>

      <!-- Main Chat Area -->
      <section class="chat-column">
        <!-- Private Mode -->
        <template v-if="selectedPrivatePlayer && !isMainCommunityView">
          <div class="chat-top">
            <div class="top-u"><img :src="selectedPrivatePlayer.avatar_url" /> <div><b>{{ selectedPrivatePlayer.full_name }}</b><p>{{ t('players.online') }}</p></div></div>
            <div class="top-btns">
              <el-button :icon="Delete" circle size="small" type="danger" plain @click="deleteThread" />
              <el-button :icon="Close" circle size="small" @click="selectedPrivatePlayer = null" />
            </div>
          </div>
          <div class="chat-msgs" ref="privateMessagesBox">
            <div v-for="(m, i) in currentPrivateMessages" :key="i" class="row" :class="{ mine: m.isMine }">
              <div class="bubble">{{ m.text }}<div class="time">{{ m.time }}</div></div>
            </div>
          </div>
          <div class="chat-footer">
            <input
              v-model="currentDraft"
              :placeholder="t('chat.inputPlaceholder')"
              @input="emitTypingState(true)"
              @blur="emitTypingState(false)"
              @keyup.enter="sendMessage('private')"
            />
            <button @click="sendMessage('private')"><el-icon><Promotion /></el-icon></button>
          </div>
          <div v-if="isPrivateTyping" class="typing-indicator">{{ t('chat.typing') }}...</div>
        </template>

        <!-- Community Mode -->
        <template v-else-if="isMainCommunityView">
          <div class="chat-top">
            <div class="top-u"><el-icon class="comm-icon"><ChatDotRound /></el-icon> <div><b>{{ t('chat.communityRoom') }}</b><p :class="{ ok: isConnected }">{{ isConnected ? t('chat.connected') : t('chat.connecting') + '...' }}</p></div></div>
            <button class="close-comm" @click="isMainCommunityView = false"><el-icon><Close /></el-icon></button>
          </div>
          <div class="chat-msgs comm-msgs" ref="globalMessagesBox">
            <div v-for="(m, i) in globalMessages" :key="i" class="row" :class="{ mine: m.isMine }">
              <span class="sender-tag" v-if="!m.isMine">{{ m.senderName }}</span>
              <div class="bubble">{{ m.text }}<div class="time">{{ m.time }}</div></div>
            </div>
          </div>
          <div class="chat-footer">
            <input v-model="globalNewMessage" :placeholder="t('chat.globalPlaceholder')" @keyup.enter="sendMessage('global')" />
            <button @click="sendMessage('global')"><el-icon><Promotion /></el-icon></button>
          </div>
        </template>

      </section>

      <aside class="news-column">
        <div class="right-empty-panel">
          <div class="right-empty-card">
            <div class="right-empty-head">
              <div>
                <h3>{{ t('players.newsAndAnnouncements') }}</h3>
                <p>{{ t('players.updateQuickly') }}</p>
              </div>
              <RouterLink to="/news" class="right-empty-link">{{ t('players.viewAll') }}</RouterLink>
            </div>

            <div v-if="latestNews.length" class="news-mini-list">
              <RouterLink
                v-for="news in latestNews"
                :key="news.id"
                :to="news.slug ? `/news/${news.slug}` : '/news'"
                class="news-mini-item"
              >
              <video 
                v-if="isVideo(news.media_url || news.thumbnail_url)" 
                :src="news.media_url || news.thumbnail_url" 
                autoplay muted loop playsinline
              ></video>
              <img 
                v-else 
                :src="news.thumbnail_url || news.media_url || 'https://images.unsplash.com/photo-1575428652377-a2d80e2277fc?auto=format&fit=crop&w=300&q=80'" 
                :alt="news.title" 
              />
                <div class="news-mini-content">
                  <div class="news-mini-title">{{ news.title }}</div>
                  <div class="news-mini-summary">{{ news.summary || t('players.clickToSeeDetails') }}</div>
                </div>
              </RouterLink>
            </div>

            <div v-else class="right-empty-note">
              {{ t('common.noNews') }}
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.chat-app { height: calc(100vh - 100px); display: flex; flex-direction: column; background: #fff; font-family: Arial, sans-serif; overflow: hidden; }
.news-mini-item img,
.news-mini-item video {
  width: 72px;
  height: 72px;
  border-radius: 12px;
  object-fit: cover;
  flex-shrink: 0;
}
/* Top Honor Bar */
.top-honor { background: #1a202c; color: #fff; padding: 10px 20px; display: flex; align-items: center; gap: 20px; border-bottom: 2px solid #2d3748; flex-shrink: 0; }
.honor-label { color: #f6e05e; font-weight: 600; font-size: 0.75rem; display: flex; align-items: center; gap: 5px; }
.honor-list { flex: 1; display: flex; gap: 10px; overflow-x: auto; scrollbar-width: none; }
.win-item { background: rgba(255,255,255,0.05); padding: 5px 10px; border-radius: 8px; display: flex; align-items: center; gap: 8px; cursor: pointer; border: 1px solid rgba(255,255,255,0.1); min-width: 140px; }
.win-item:hover { border-color: #f6e05e; }
.rank { font-weight: 900; color: #f6e05e; font-size: 0.7rem; }
.win-item img { width: 30px!important; height: 30px!important; border-radius: 50%!important; object-fit:cover; border:1px solid #fff; }
.win-meta b { font-size: 0.8rem; display: block; white-space: nowrap; }
.win-meta p { font-size: 0.65rem; color: #a0aec0; margin: 0; }
.search-wrap { width: 180px; }

/* Body Layout */
.main-body { flex: 1; display: flex; overflow: hidden; background: #f0f2f5; }

/* Sidebar v2 */
.sidebar-v2 { width: 340px; background: #fff; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; }
.profile-card { padding: 15px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #f1f5f9; background: #f8fafc; }
.profile-card img { width: 44px!important; height: 44px!important; border-radius: 50%!important; object-fit:cover; }
.p-info b { font-size: 0.95rem; color: #1a202c; display: block; }
.p-info p { margin: 0; font-size: 0.75rem; color: #10b981; font-weight: 500; }

.sidebar-tabs { display: flex; padding: 12px; gap: 8px; background: #fff; }
.sidebar-tabs button { flex: 1; padding: 10px; border: none; background: #f1f5f9; border-radius: 10px; font-size: 0.85rem; font-weight: 500; cursor: pointer; color: #64748b; transition: 0.2s; }
.sidebar-tabs button.active { background: #146250; color: #fff; box-shadow: 0 4px 12px rgba(20, 98, 80, 0.2); }
.tab-badge {
  margin-left: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: #ef4444;
  color: #fff;
  font-size: 0.72rem;
  font-weight: 500;
}

.scroll-area { flex: 1; overflow-y: auto; padding: 8px; }
.user-row { display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 14px; cursor: pointer; margin-bottom: 4px; transition: 0.2s; border: 1px solid transparent; }
.user-row:hover { background: #f7fafc; }
.user-row.active { background: #ecfdf5; border-color: #d1fae5; }
.user-row.unread { background: #fff; border-color: #bee3f8; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }

.ava-box { position: relative; width: 48px; height: 48px; flex-shrink: 0; }
.ava-box img { width: 48px!important; height: 48px!important; border-radius: 50%!important; object-fit:cover; }
.dot { position: absolute; bottom: 2px; right: 2px; width: 12px; height: 12px; background: #10b981; border: 2px solid #fff; border-radius: 50%; }

.u-content { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.u-name-row { display: flex; justify-content: space-between; align-items: center; }
.u-name { font-size: 0.95rem; font-weight: 500; color: #1a202c; }
.u-time { font-size: 0.7rem; color: #a0aec0; }

.u-msg-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.u-msg { font-size: 0.8rem; color: #718096; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
.unread .u-msg { font-weight: 500; color: #2d3748; }
.msg-prefix { color: #146250; font-weight: 500; font-size: 0.75rem; }

.u-badge-dot { background: #3182ce; color: #fff; font-size: 0.65rem; font-weight: 900; min-width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 10px rgba(49, 130, 206, 0.4); }

.sidebar-empty-state {
  margin: 12px 4px 0;
  padding: 14px;
  border: 1px dashed #cbd5e1;
  border-radius: 14px;
  background: #f8fafc;
  color: #64748b;
}
.sidebar-empty-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 6px;
}
.sidebar-empty-text {
  font-size: 0.8rem;
  line-height: 1.45;
}

/* Main Chat Area */
.chat-column { flex: 1 1 auto; background: #fff; min-width: 0; display: flex; flex-direction: column; border-right: 1px solid #e2e8f0; border-left: 1px solid #e2e8f0; position: relative; }
.chat-top { padding: 15px 25px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; background: #fff; }
.top-u { display: flex; align-items: center; gap: 12px; }
.top-u img { width: 40px!important; height: 40px!important; border-radius: 50%!important; object-fit:cover; }
.top-u b { font-size: 1.1rem; color: #1a202c; display: block; font-weight: 500; }
.top-u p { margin: 0; font-size: 0.7rem; color: #10b981; font-weight: 500; }
.top-u .comm-icon { font-size: 1.5rem; color: #146250; }
.close-comm { background: #f1f5f9; border: none; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; }

.chat-msgs { flex: 1; overflow-y: auto; padding: 30px; display: flex; flex-direction: column; gap: 18px; background: #fdfdfd; }
.row { display: flex; flex-direction: column; max-width: 80%; align-self: flex-start; }
.row.mine { align-self: flex-end; align-items: flex-end; }
.bubble { padding: 12px 18px; border-radius: 20px 20px 20px 4px; background: #f1f5f9; font-size: 1rem; color: #1e293b; line-height: 1.5; box-shadow: 0 1px 2px rgba(0,0,0,0.05); font-weight: 400; }
.mine .bubble { background: #146250; color: #fff; border-radius: 20px 20px 4px 20px; box-shadow: 0 4px 12px rgba(20, 98, 80, 0.2); }
.time { font-size: 0.65rem; margin-top: 4px; opacity: 0.6; }
.sender-tag { font-size: 0.7rem; font-weight: 500; color: #64748b; margin-bottom: 4px; }

.chat-footer { padding: 25px; border-top: 1px solid #f1f5f9; display: flex; gap: 15px; background: #fff; }
.chat-footer input { flex: 1; border: 2px solid #f1f5f9; padding: 12px 25px; border-radius: 30px; outline: none; background: #f8fafc; transition: 0.2s; }
.chat-footer input:focus { border-color: #146250; background: #fff; }
.chat-footer button { width: 50px; height: 50px; border: none; background: #146250; color: #fff; border-radius: 50%; cursor: pointer; transition: 0.2s; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }
.chat-footer button:hover { transform: scale(1.05); background: #0e4e3f; }
.typing-indicator {
  padding: 0 25px 14px;
  font-size: 0.78rem;
  color: #64748b;
}

.chat-welcome { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; text-align: center; padding: 40px; }
.chat-welcome .el-icon { font-size: 5rem; margin-bottom: 20px; opacity: 0.2; color: #146250; }
.chat-welcome h3 { color: #1e293b; margin-bottom: 10px; }
.news-column {
  width: 360px;
  flex-shrink: 0;
  background: #f0f2f5;
  border-left: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
}
.right-empty-panel {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
}
.right-empty-card {
  width: min(520px, 100%);
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.05);
  padding: 20px;
}
.right-empty-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}
.right-empty-head h3 {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 600;
  color: #0f172a;
}
.right-empty-head p {
  margin: 4px 0 0;
  font-size: 0.84rem;
  color: #64748b;
}
.right-empty-link {
  flex-shrink: 0;
  color: #146250;
  font-size: 0.82rem;
  font-weight: 600;
  text-decoration: none;
}
.news-mini-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.news-mini-item {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  text-decoration: none;
  color: inherit;
  background: #fafcff;
  transition: 0.2s ease;
}
.news-mini-item:hover {
  border-color: #cbd5e1;
  transform: translateY(-1px);
}
.news-mini-item img {
  width: 72px;
  height: 72px;
  border-radius: 12px;
  object-fit: cover;
  flex-shrink: 0;
}
.news-mini-content {
  min-width: 0;
  flex: 1;
}
.news-mini-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.3;
  margin-bottom: 4px;
}
.news-mini-summary {
  font-size: 0.8rem;
  color: #64748b;
  line-height: 1.4;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}
.right-empty-note {
  padding: 16px;
  border-radius: 14px;
  background: #f8fafc;
  color: #64748b;
  font-size: 0.9rem;
  text-align: center;
}

@media (max-width: 1400px) {
  .top-honor { padding: 10px 14px; gap: 14px; }
  .sidebar-v2 { width: 300px; }
  .chat-column { max-width: none; }
  .news-column { width: 320px; }
  .chat-msgs { padding: 24px; }
  .chat-footer { padding: 20px; }
  .right-empty-panel { padding: 20px; }
}

@media (max-width: 1200px) {
  .top-honor { gap: 12px; }
  .honor-list { gap: 8px; }
  .win-item { min-width: 128px; }
  .sidebar-v2 { width: 270px; }
  .news-column { width: 300px; }
  .chat-top { padding: 14px 18px; }
  .chat-msgs { padding: 18px; gap: 14px; }
  .chat-footer { padding: 18px; gap: 10px; }
  .chat-footer input { padding: 11px 18px; }
  .chat-footer button { width: 46px; height: 46px; }
  .right-empty-card { width: 100%; }
}

@media (max-width: 1000px) {
  .main-body { flex-direction: column; overflow: auto; }
  .sidebar-v2 {
    width: 100%;
    order: 1;
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
  }
  .chat-column {
    width: 100%;
    max-width: none;
    order: 2;
    border-left: none;
    border-right: none;
    min-height: 560px;
  }
  .news-column {
    width: 100%;
    order: 3;
    border-left: none;
    border-top: 1px solid #e2e8f0;
  }
  .sidebar-tabs { padding: 10px; }
  .scroll-area { max-height: 360px; }
  .chat-msgs { padding: 16px; }
  .chat-footer { padding: 14px; }
  .right-empty-panel { padding: 16px; }
  .right-empty-card { padding: 16px; }
}

@media (max-width: 768px) {
  .chat-app { height: auto; min-height: 100vh; }
  .top-honor {
    flex-wrap: wrap;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 12px;
  }
  .honor-label {
    width: 100%;
    margin-bottom: 2px;
  }
  .honor-list {
    width: 100%;
    gap: 8px;
    padding-bottom: 4px;
    flex-wrap: nowrap;
  }
  .win-item {
    flex: 0 0 auto;
    min-width: 132px;
    padding: 6px 8px;
    gap: 6px;
  }
  .win-item img {
    width: 26px !important;
    height: 26px !important;
  }
  .win-meta b {
    font-size: 0.72rem;
    line-height: 1.1;
    max-width: 72px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .win-meta p {
    font-size: 0.62rem;
  }
  .search-wrap {
    width: 100%;
    order: 3;
  }
  .sidebar-v2 {
    padding-bottom: 4px;
  }
  .profile-card {
    padding: 12px;
  }
  .sidebar-tabs {
    padding: 10px;
    gap: 6px;
  }
  .scroll-area {
    padding: 6px;
    max-height: 300px;
  }
  .user-row {
    padding: 10px;
    gap: 10px;
  }
  .ava-box,
  .ava-box img {
    width: 42px !important;
    height: 42px !important;
  }
  .u-name { font-size: 0.9rem; }
  .u-msg { font-size: 0.75rem; }
  .u-badge-dot { min-width: 16px; height: 16px; font-size: 0.6rem; }
  .chat-column {
    min-height: 520px;
  }
  .chat-top {
    padding: 12px 14px;
  }
  .top-u b {
    font-size: 1rem;
  }
  .chat-msgs {
    padding: 14px;
    gap: 12px;
  }
  .row {
    max-width: 92%;
  }
  .bubble {
    font-size: 0.96rem;
    padding: 11px 14px;
  }
  .chat-footer {
    padding: 12px;
    gap: 8px;
  }
  .chat-footer input {
    padding: 10px 16px;
    font-size: 0.95rem;
  }
  .chat-footer button {
    width: 42px;
    height: 42px;
    font-size: 1rem;
  }
  .right-empty-panel {
    padding: 12px;
  }
  .right-empty-card {
    padding: 14px;
    border-radius: 16px;
  }
  .news-mini-item {
    padding: 10px;
  }
  .news-mini-item img {
    width: 60px;
    height: 60px;
  }
}

@media (max-width: 520px) {
  .top-honor {
    padding: 8px 10px;
    gap: 8px;
  }
  .honor-list {
    gap: 6px;
  }
  .win-item {
    flex: 0 0 auto;
    min-width: 128px;
    padding: 5px 7px;
    gap: 5px;
    border-radius: 10px;
  }
  .rank { font-size: 0.62rem; }
  .win-meta b { font-size: 0.68rem; max-width: 68px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .win-meta p { font-size: 0.58rem; }
  .sidebar-v2 {
    min-width: 0;
  }
  .profile-card {
    gap: 10px;
  }
  .profile-card img {
    width: 40px !important;
    height: 40px !important;
  }
  .p-info b {
    font-size: 0.9rem;
  }
  .p-info p {
    font-size: 0.7rem;
  }
  .sidebar-tabs button {
    padding: 9px 8px;
    font-size: 0.8rem;
  }
  .tab-badge {
    min-width: 18px;
    height: 18px;
    font-size: 0.66rem;
  }
  .scroll-area {
    max-height: 260px;
  }
  .u-content {
    gap: 3px;
  }
  .u-time {
    font-size: 0.65rem;
  }
  .u-msg-row {
    gap: 8px;
  }
  .chat-column {
    min-height: 460px;
  }
  .news-column {
    width: 100%;
  }
  .chat-top {
    padding: 10px 12px;
  }
  .chat-msgs {
    padding: 12px;
  }
  .row {
    max-width: 96%;
  }
  .bubble {
    font-size: 0.92rem;
    padding: 10px 12px;
    border-radius: 16px 16px 4px 16px;
  }
  .mine .bubble {
    border-radius: 16px 16px 4px 16px;
  }
  .chat-footer {
    padding: 10px;
  }
  .chat-footer input {
    padding: 9px 14px;
  }
  .right-empty-head {
    flex-direction: column;
  }
  .right-empty-link {
    align-self: flex-start;
  }
  
}
</style>
