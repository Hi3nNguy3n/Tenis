<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Bell, Clock, Promotion } from '@element-plus/icons-vue'
import { tournamentService } from '../../services/tournamentService'
import apiClient from '../../services/apiClient'
import { useAuthStore } from '../../stores/auth'
import { t } from '../../utils/locale'

const authStore = useAuthStore()
const STORAGE_KEY = 'saigon_tennis_mail_campaigns'
const SCHEDULE_KEY = 'saigon_tennis_mail_campaign_queue'

const tournaments = ref([])
const loadingTournaments = ref(false)
const sending = ref(false)
const scheduling = ref(false)
const selectedTournamentId = ref('')
const subject = ref('Thông báo từ Ban tổ chức Saigon Tennis')
const message = ref('')
const sendAt = ref('')
const templateKey = ref('announcement')
const campaignLogs = ref([])
const scheduledQueue = ref([])

import { useRoute } from 'vue-router'
const route = useRoute()

const templates = computed(() => [
  { key: 'announcement', label: t('admin.announcementTemplateLabel', 'Thông báo giải'), subject: t('admin.announcementTemplateSubject', 'Thông báo quan trọng từ Ban tổ chức'), message: t('admin.announcementTemplateMessage', 'Ban tổ chức xin gửi thông báo tới các vận động viên: vui lòng theo dõi lịch thi đấu, cập nhật trạng thái đăng ký và kiểm tra thông tin giải đấu thường xuyên.') },
  { key: 'reminder', label: t('admin.reminderTemplateLabel', 'Nhắc lịch'), subject: t('admin.reminderTemplateSubject', 'Nhắc lịch thi đấu sắp diễn ra'), message: t('admin.reminderTemplateMessage', 'Giải đấu sắp diễn ra. Vui lòng kiểm tra lịch thi đấu, sân thi đấu và có mặt đúng giờ theo lịch đã công bố.') },
  { key: 'result', label: t('admin.resultTemplateLabel', 'Kết quả'), subject: t('admin.resultTemplateSubject', 'Cập nhật kết quả và lịch tiếp theo'), message: t('admin.resultTemplateMessage', 'Kết quả thi đấu đã được cập nhật. Vui lòng xem lại bracket, kết quả trận và lịch thi đấu tiếp theo trên hệ thống.') },
  { key: 'registration', label: t('admin.registrationTemplateLabel', 'Mở đăng ký'), subject: t('admin.registrationTemplateSubject', 'Thông báo mở đăng ký giải đấu'), message: t('admin.registrationTemplateMessage', 'Hệ thống đã mở đăng ký cho giải đấu. Các vận động viên vui lòng hoàn tất đăng ký trước hạn chót để được xếp vào draw.') },
])

const selectedTournament = computed(() => tournaments.value.find((item) => String(item.id) === String(selectedTournamentId.value)) || null)
const upcomingCampaigns = computed(() => [...scheduledQueue.value].sort((a, b) => new Date(a.sendAt).getTime() - new Date(b.sendAt).getTime()).slice(0, 5))

const loadStoredState = () => {
  try { campaignLogs.value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { campaignLogs.value = [] }
  try { scheduledQueue.value = JSON.parse(localStorage.getItem(SCHEDULE_KEY) || '[]') } catch { scheduledQueue.value = [] }
}

const persistStoredState = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(campaignLogs.value))
  localStorage.setItem(SCHEDULE_KEY, JSON.stringify(scheduledQueue.value))
}

const applyTemplate = (key) => {
  templateKey.value = key
  const template = templates.value.find((item) => item.key === key)
  if (template) {
    subject.value = template.subject
    message.value = template.message
  }
}

const loadTournaments = async () => {
  loadingTournaments.value = true
  try {
    const data = await tournamentService.getAll({ limit: 100, skip: 0 })
    tournaments.value = Array.isArray(data) ? data : (data?.items || [])
    if (!selectedTournamentId.value && tournaments.value.length) {
      selectedTournamentId.value = String(tournaments.value[0].id)
    }
  } catch (error) {
    ElMessage.error(t('admin.loadTournamentsError'))
  } finally {
    loadingTournaments.value = false
  }
}

const appendLog = (entry) => {
  campaignLogs.value = [entry, ...campaignLogs.value].slice(0, 30)
  persistStoredState()
}

// 1. CHỈNH SỬA HÀM GỬI NGAY
const sendNow = async () => {
  if (!selectedTournament.value || !subject.value.trim() || !message.value.trim()) {
    return ElMessage.warning(t('admin.fillInfoWarning'))
  }

  const confirmed = await ElMessageBox.confirm(t('admin.confirmSendNow', { tournament: selectedTournament.value.name }), t('admin.confirmTitle'), { type: 'warning' }).catch(() => false)
  if (!confirmed) return

  sending.value = true
  try {
    // Gửi payload với scheduled_at = null để Backend gửi ngay
    const result = await apiClient.post(`/api/tournaments/${selectedTournament.value.id}/send-notifications`, {
      subject: subject.value.trim(),
      message: message.value.trim(),
      scheduled_at: null 
    })

    appendLog({
      id: `campaign-${Date.now()}`, mode: 'sent', status: 'sent',
      tournamentName: selectedTournament.value.name, subject: subject.value.trim(),
      sendAt: new Date().toISOString(), author: authStore.user?.full_name || 'Admin',
      resultMessage: result.message
    })
    ElMessage.success(t('admin.sendSuccess'))
  } catch (error) {
    ElMessage.error(error.message || t('admin.sendError'))
  } finally {
    sending.value = false
  }
}

// 2. CHỈNH SỬA HÀM HẸN GIỜ (GIAO VIỆC CHO BACKEND)
const scheduleCampaign = async () => {
  if (!selectedTournament.value || !subject.value.trim() || !message.value.trim() || !sendAt.value) {
    return ElMessage.warning(t('admin.fillAllAndScheduleWarning'))
  }

  const sendTime = new Date(sendAt.value).getTime()
  if (sendTime <= Date.now()) {
    return ElMessage.warning(t('admin.scheduleTimeInvalidWarning'))
  }

  scheduling.value = true
  try {
    // Ép kiểu Date thành chuẩn ISO (UTC) để Backend không bị lệch múi giờ
    const payload = {
      subject: subject.value.trim(),
      message: message.value.trim(),
      scheduled_at: new Date(sendTime).toISOString() 
    }

    const result = await apiClient.post(`/api/tournaments/${selectedTournament.value.id}/send-notifications`, payload)

    // Thêm vào UI để Admin xem cho vui (Backend đã tự lo việc gửi)
    scheduledQueue.value = [{
      id: `schedule-${Date.now()}`, tournamentName: selectedTournament.value.name,
      subject: payload.subject, sendAt: new Date(sendTime).toISOString(),
      author: authStore.user?.full_name || 'Admin', status: 'scheduled',
    }, ...scheduledQueue.value]
    persistStoredState()

    ElMessage.success(t('admin.scheduleSuccess'))
  } catch (error) {
    ElMessage.error(error.message || t('admin.scheduleError'))
  } finally {
    scheduling.value = false
  }
}

const deleteLog = (id) => {
  campaignLogs.value = campaignLogs.value.filter((item) => item.id !== id)
  persistStoredState()
}

const clearAllLogs = () => {
  campaignLogs.value = []
  persistStoredState()
  ElMessage.success(t('admin.clearLogsSuccess'))
}

onMounted(async () => {
  // 1. Khởi tạo dữ liệu cơ bản
  authStore.hydrate()
  loadStoredState()
  
  // 2. Kiểm tra xem có tournamentId từ trang Giải Đấu truyền sang không
  if (route.query.tournamentId) {
    // Gán vào ID (biến ref), KHÔNG gán vào selectedTournament (biến computed)
    selectedTournamentId.value = String(route.query.tournamentId)
  }
  
  // 3. Gọi hàm load danh sách giải đấu (Nhớ là loadTournaments chứ không phải fetchTournaments)
  await loadTournaments()
  
  // 4. Áp dụng mẫu mail mặc định
  applyTemplate(templateKey.value)
})

</script>

<template>
  <div class="mail-campaign-shell">
    <section class="hero-card">
      <div>
        <span class="eyebrow">Mail campaign</span>
        <h2>{{ $t('admin.mailCampaignTitle') }}</h2>
        <p>
          {{ $t('admin.mailCampaignDesc') }}
        </p>
      </div>
      <div class="hero-stats">
        <div class="hero-stat">
          <span>{{ $t('admin.templateLabel') }}</span>
          <strong>{{ templates.length }}</strong>
        </div>
        <div class="hero-stat">
          <span>{{ $t('admin.queuedLabel') }}</span>
          <strong>{{ scheduledQueue.length }}</strong>
        </div>
        <div class="hero-stat hero-stat-accent">
          <span>{{ $t('admin.latestLogLabel') }}</span>
          <strong>{{ campaignLogs.length }}</strong>
        </div>
      </div>
    </section>

    <section class="content-grid">
      <article class="composer-card">
        <div class="section-head">
          <div>
            <span class="section-kicker">{{ $t('admin.composeMailSection') }}</span>
            <h3>{{ $t('admin.campaignSection') }}</h3>
          </div>
          <span class="section-badge" v-if="selectedTournament">{{ selectedTournament.name }}</span>
        </div>

        <div class="form-grid">
          <label class="field">
            <span>{{ $t('admin.selectTournamentLabel') }}</span>
            <select v-model="selectedTournamentId" :disabled="loadingTournaments">
              <option v-for="item in tournaments" :key="item.id" :value="String(item.id)">
                {{ item.name }}
              </option>
            </select>
          </label>

          <div class="template-row">
            <button
              v-for="item in templates"
              :key="item.key"
              type="button"
              class="template-chip"
              :class="{ active: templateKey === item.key }"
              @click="applyTemplate(item.key)"
            >
              {{ item.label }}
            </button>
          </div>

          <label class="field">
            <span>{{ $t('admin.mailSubjectLabel') }}</span>
            <input v-model="subject" type="text" :placeholder="$t('admin.mailSubjectPlaceholder')" />
          </label>

          <label class="field">
            <span>{{ $t('admin.mailContentLabel') }}</span>
            <textarea v-model="message" rows="10" :placeholder="$t('admin.mailContentPlaceholder')"></textarea>
          </label>

          <div class="schedule-row">
            <label class="field">
              <span>{{ $t('admin.scheduleTimeLabel') }}</span>
              <input v-model="sendAt" type="datetime-local" />
            </label>
            <div class="schedule-hint">
              <Bell />
              <p>{{ $t('admin.scheduleHint') }}</p>
            </div>
          </div>

          <div class="action-row">
            <button type="button" class="btn ghost" @click="scheduleCampaign" :disabled="scheduling">
              <Clock />
              <span>{{ scheduling ? $t('admin.savingScheduleBtn') : $t('admin.saveScheduleBtn') }}</span>
            </button>
            <button type="button" class="btn primary" @click="sendNow" :disabled="sending">
              <Promotion />
              <span>{{ sending ? $t('admin.sendingBtn') : $t('admin.sendNowBtn') }}</span>
            </button>
          </div>
        </div>
      </article>

      <aside class="side-stack">
        <article class="log-card">
          <div class="section-head">
            <div>
              <span class="section-kicker">{{ $t('admin.sendScheduleSection') }}</span>
              <h3>{{ $t('admin.upcomingCampaignsSection') }}</h3>
            </div>
            <span class="count-chip">{{ upcomingCampaigns.length }}</span>
          </div>

          <div v-if="upcomingCampaigns.length" class="queue-list">
            <div v-for="item in upcomingCampaigns" :key="item.id" class="queue-item">
              <div>
                <strong>{{ item.tournamentName }}</strong>
                <p>{{ item.subject }}</p>
              </div>
              <span>{{ new Date(item.sendAt).toLocaleString('vi-VN') }}</span>
            </div>
          </div>
          <p v-else class="muted">{{ $t('admin.noUpcomingCampaigns') }}</p>
        </article>

        <article class="log-card">
          <div class="section-head">
            <div>
              <span class="section-kicker">{{ $t('admin.sendLogsSection') }}</span>
              <h3>{{ $t('admin.recentActivitySection') }}</h3>
            </div>
            <button class="mini-link" type="button" @click="clearAllLogs">{{ $t('admin.clearLogBtn') }}</button>
          </div>

          <div v-if="campaignLogs.length" class="activity-list">
            <div v-for="item in campaignLogs" :key="item.id" class="activity-item">
              <div class="activity-top">
                <strong>{{ item.tournamentName }}</strong>
                <span :class="['status-pill', item.status]">{{ item.status }}</span>
              </div>
              <p>{{ item.subject }}</p>
              <div class="activity-meta">
                <span>{{ item.author }}</span>
                <span>{{ new Date(item.finishedAt || item.sendAt).toLocaleString('vi-VN') }}</span>
              </div>
              <div class="activity-actions">
                <button type="button" class="text-btn" @click="deleteLog(item.id)">{{ $t('admin.deleteBtn') }}</button>
              </div>
            </div>
          </div>
          <p v-else class="muted">{{ $t('admin.noSendLogs') }}</p>
        </article>
      </aside>
    </section>
  </div>
</template>

<style scoped>
.mail-campaign-shell {
  display: grid;
  gap: 20px;
}

.hero-card,
.composer-card,
.log-card {
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(16, 185, 129, 0.14);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.06);
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 24px 26px;
  align-items: flex-start;
}

.eyebrow,
.section-kicker {
  display: inline-flex;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(20, 98, 80, 0.08);
  color: #146250;
  text-transform: uppercase;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.hero-card h2,
.composer-card h3,
.log-card h3 {
  margin: 10px 0 8px;
  color: #0f172a;
}

.hero-card p,
.muted,
.queue-item p,
.activity-item p,
.schedule-hint p {
  color: #5b6b78;
  line-height: 1.6;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  min-width: min(380px, 100%);
}

.hero-stat {
  display: grid;
  gap: 4px;
  padding: 16px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.hero-stat span {
  color: #64748b;
  font-size: 0.76rem;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.hero-stat strong {
  font-size: 1.8rem;
  color: #0f172a;
}

.hero-stat-accent {
  background: linear-gradient(135deg, #0f5c4d, #1b7a61);
}

.hero-stat-accent span,
.hero-stat-accent strong {
  color: #fff;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.7fr);
  gap: 20px;
  align-items: start;
}

.composer-card,
.log-card {
  padding: 22px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.section-badge,
.count-chip {
  padding: 8px 12px;
  border-radius: 999px;
  background: #dcfce7;
  color: #146250;
  font-weight: 800;
  font-size: 0.8rem;
}

.form-grid {
  display: grid;
  gap: 16px;
}

.field {
  display: grid;
  gap: 8px;
}

.field span {
  color: #0f172a;
  font-size: 0.82rem;
  font-weight: 700;
}

.field input,
.field textarea,
.field select {
  width: 100%;
  border-radius: 16px;
  border: 1px solid #cbd5e1;
  background: #fff;
  padding: 14px 16px;
  font: inherit;
  color: #0f172a;
  outline: none;
}

.field input:focus,
.field textarea:focus,
.field select:focus {
  border-color: #146250;
  box-shadow: 0 0 0 4px rgba(20, 98, 80, 0.08);
}

.template-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.template-chip {
  border: 1px solid #dbe4ee;
  background: #f8fafc;
  color: #0f172a;
  border-radius: 999px;
  padding: 10px 14px;
  font-weight: 700;
  cursor: pointer;
}

.template-chip.active {
  background: #146250;
  color: #fff;
  border-color: #146250;
}

.schedule-row {
  display: grid;
  grid-template-columns: 1fr 0.9fr;
  gap: 16px;
}

.schedule-hint {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 16px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.schedule-hint svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: #146250;
  margin-top: 2px;
}

.schedule-hint p {
  margin: 0;
  font-size: 0.92rem;
}

.action-row {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.btn {
  border: none;
  border-radius: 14px;
  padding: 14px 18px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  cursor: pointer;
}

.btn.ghost {
  background: #f1f5f9;
  color: #0f172a;
}

.btn.primary {
  background: linear-gradient(135deg, #146250, #1b7a61);
  color: #fff;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.side-stack {
  display: grid;
  gap: 20px;
}

.queue-list,
.activity-list {
  display: grid;
  gap: 12px;
}

.queue-item,
.activity-item {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
}

.queue-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.queue-item strong,
.activity-top strong {
  color: #0f172a;
}

.queue-item span,
.activity-meta {
  color: #64748b;
  font-size: 0.8rem;
}

.activity-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.status-pill {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
}

.status-pill.sent {
  background: #dcfce7;
  color: #146250;
}

.status-pill.failed {
  background: #fee2e2;
  color: #b91c1c;
}

.status-pill.scheduled {
  background: #dbeafe;
  color: #1d4ed8;
}

.activity-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
}

.activity-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.text-btn,
.mini-link {
  border: none;
  background: transparent;
  color: #146250;
  font-weight: 800;
  cursor: pointer;
  padding: 0;
}

@media (max-width: 1100px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .schedule-row {
    grid-template-columns: 1fr;
  }

  .hero-card {
    flex-direction: column;
  }
}

@media (max-width: 720px) {
  .hero-stats {
    grid-template-columns: 1fr;
    min-width: 0;
    width: 100%;
  }

  .action-row {
    justify-content: stretch;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
