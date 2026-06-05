<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Bell, Clock, Promotion, Trophy, 
  Monitor, Connection, ArrowLeft,
  CircleCheckFilled, Message, Timer,
  Finished, Delete, Document, Search
} from '@element-plus/icons-vue'
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
const subject = ref('Thông báo từ Ban tổ chức Saigontennistours')
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

const sendNow = async () => {
  if (!selectedTournament.value || !subject.value.trim() || !message.value.trim()) {
    return ElMessage.warning(t('admin.fillInfoWarning'))
  }

  const confirmed = await ElMessageBox.confirm(t('admin.confirmSendNow', { tournament: selectedTournament.value.name }), t('admin.confirmTitle'), { type: 'warning' }).catch(() => false)
  if (!confirmed) return

  sending.value = true
  try {
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
    const payload = {
      subject: subject.value.trim(),
      message: message.value.trim(),
      scheduled_at: new Date(sendTime).toISOString() 
    }

    const result = await apiClient.post(`/api/tournaments/${selectedTournament.value.id}/send-notifications`, payload)

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
  authStore.hydrate()
  loadStoredState()
  if (route.query.tournamentId) {
    selectedTournamentId.value = String(route.query.tournamentId)
  }
  await loadTournaments()
  applyTemplate(templateKey.value)
})

</script>

<template>
  <div class="saas-container" v-loading="loadingTournaments">
    <!-- Action Bar -->
    <section class="saas-header">
      <div class="header-left">
        <div class="operation-badge-premium green">
          <el-icon class="mr-1"><Promotion /></el-icon>
          <span>Email Campaign Manager</span>
        </div>
        <div class="header-titles">
          <h2 class="saas-title">{{ $t('admin.mailCampaignTitle') }}</h2>
          <p class="saas-subtitle">{{ $t('admin.mailCampaignDesc') }}</p>
        </div>
      </div>
    </section>

    <!-- Hero Stats Grid -->
    <div class="saas-stats-grid">
      <div class="saas-stat-card">
        <div class="stat-icon p-blue"><el-icon><Document /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.templateLabel') }}</span>
          <h3 class="stat-value">{{ templates.length }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-orange"><el-icon><Timer /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.queuedLabel') }}</span>
          <h3 class="stat-value">{{ scheduledQueue.length }}</h3>
        </div>
      </div>
      <div class="saas-stat-card">
        <div class="stat-icon p-green"><el-icon><Finished /></el-icon></div>
        <div class="stat-content">
          <span class="stat-label">{{ $t('admin.latestLogLabel') }}</span>
          <h3 class="stat-value">{{ campaignLogs.length }}</h3>
        </div>
      </div>
    </div>

    <!-- Main Content Layout -->
    <div class="campaign-layout-saas">
      <!-- Left: Composer -->
      <main class="saas-card-premium composer-block">
        <div class="section-header-saas">
          <span class="accent-line p-green"></span>
          <div class="sh-text">
            <h3>{{ $t('admin.composeMailSection') }}</h3>
            <p>Thiết kế nội dung và lên lịch gửi email cho vận động viên</p>
          </div>
        </div>

        <el-form label-position="top" class="saas-form-premium">
          <div class="saas-form-grid">
            <el-form-item :label="$t('admin.selectTournamentLabel')" class="span-2">
              <el-select v-model="selectedTournamentId" :disabled="loadingTournaments" filterable class="w-full saas-input-large">
                <template #prefix><el-icon><Trophy /></el-icon></template>
                <el-option v-for="item in tournaments" :key="item.id" :label="item.name" :value="String(item.id)" />
              </el-select>
            </el-form-item>

            <div class="template-selector-wrap span-2">
              <span class="field-label">{{ $t('admin.templateLabel') }}</span>
              <div class="saas-template-row">
                <button
                  v-for="item in templates"
                  :key="item.key"
                  type="button"
                  class="saas-template-chip"
                  :class="{ active: templateKey === item.key }"
                  @click="applyTemplate(item.key)"
                >
                  {{ item.label }}
                </button>
              </div>
            </div>

            <el-form-item :label="$t('admin.mailSubjectLabel')" class="span-2">
              <el-input v-model="subject" :placeholder="$t('admin.mailSubjectPlaceholder')" class="saas-input-large">
                <template #prefix><el-icon><Message /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-form-item :label="$t('admin.mailContentLabel')" class="span-2">
              <el-input 
                v-model="message" 
                type="textarea" 
                :rows="10" 
                :placeholder="$t('admin.mailContentPlaceholder')"
                class="saas-textarea-premium"
              />
            </el-form-item>

            <el-form-item :label="$t('admin.scheduleTimeLabel')" class="span-1">
              <el-date-picker 
                v-model="sendAt" 
                type="datetime" 
                placeholder="Chọn thời gian gửi"
                class="w-full saas-input-large"
              />
            </el-form-item>

            <div class="schedule-info-saas span-1">
              <el-icon><Bell /></el-icon>
              <p>{{ $t('admin.scheduleHint') }}</p>
            </div>
          </div>

          <div class="composer-actions">
            <el-button @click="scheduleCampaign" :loading="scheduling" :icon="Clock" class="saas-btn-action is-secondary">
              {{ scheduling ? $t('admin.savingScheduleBtn') : $t('admin.saveScheduleBtn') }}
            </el-button>
            <el-button type="primary" @click="sendNow" :loading="sending" :icon="Promotion" class="saas-btn-action is-primary">
              {{ sending ? $t('admin.sendingBtn') : $t('admin.sendNowBtn') }}
            </el-button>
          </div>
        </el-form>
      </main>

      <!-- Right: Queue & Logs -->
      <aside class="saas-sidebar-premium">
        <!-- Upcoming Queue -->
        <div class="saas-card-premium mini sidebar-block">
          <div class="sidebar-head">
            <div class="sh-left">
              <el-icon><Timer /></el-icon>
              <h4>{{ $t('admin.upcomingCampaignsSection') }}</h4>
            </div>
            <el-badge :value="upcomingCampaigns.length" type="primary" />
          </div>

          <div v-if="upcomingCampaigns.length" class="queue-stack-saas">
            <div v-for="item in upcomingCampaigns" :key="item.id" class="queue-item-saas">
              <div class="qi-top">
                <strong>{{ item.tournamentName }}</strong>
                <span class="qi-time">{{ new Date(item.sendAt).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' }) }}</span>
              </div>
              <p class="qi-subject">{{ item.subject }}</p>
              <div class="qi-footer">
                <span>By: {{ item.author }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else :image-size="60" :description="$t('admin.noUpcomingCampaigns')" />
        </div>

        <!-- Recent Logs -->
        <div class="saas-card-premium mini sidebar-block mt-6">
          <div class="sidebar-head">
            <div class="sh-left">
              <el-icon><Finished /></el-icon>
              <h4>{{ $t('admin.recentActivitySection') }}</h4>
            </div>
            <el-button link type="danger" @click="clearAllLogs" class="mini-clear-btn">{{ $t('admin.clearLogBtn') }}</el-button>
          </div>

          <div v-if="campaignLogs.length" class="log-stack-saas">
            <div v-for="item in campaignLogs" :key="item.id" class="log-item-saas">
              <div class="li-header">
                <span :class="['status-dot', item.status]"></span>
                <strong class="truncate">{{ item.tournamentName }}</strong>
              </div>
              <p class="li-subject">{{ item.subject }}</p>
              <div class="li-footer">
                <span class="li-time">{{ new Date(item.sendAt).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit' }) }}</span>
                <el-button link type="danger" :icon="Delete" @click="deleteLog(item.id)" />
              </div>
            </div>
          </div>
          <el-empty v-else :image-size="60" :description="$t('admin.noSendLogs')" />
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.saas-container { display: flex; flex-direction: column; gap: 32px; min-height: 100%; }

/* Action Bar */
.saas-header { display: flex; align-items: center; justify-content: space-between; }
.header-left { display: flex; align-items: center; }

.operation-badge-premium {
  background: #eff6ff; color: #2563eb; padding: 10px 20px; border-radius: 14px;
  font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
  display: inline-flex; align-items: center; margin-right: 24px;
}
.operation-badge-premium.green { background: #f0fdf4; color: #16a34a; }

.header-titles { display: flex; flex-direction: column; gap: 4px; }
.saas-title { font-size: 1.8rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.02em; }
.saas-subtitle { font-size: 0.95rem; color: #64748b; margin: 0; }

/* Stats Grid */
.saas-stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.saas-stat-card {
  background: #fff; border-radius: 24px; padding: 24px; display: flex; align-items: center; gap: 20px;
  border: 1px solid #f1f5f9; transition: all 0.3s; box-shadow: 0 4px 20px rgba(0,0,0,0.02);
}
.saas-stat-card:hover { transform: translateY(-5px); box-shadow: 0 12px 30px rgba(0,0,0,0.04); }

.stat-icon { width: 56px; height: 56px; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 24px; }
.stat-icon.p-blue { background: #eff6ff; color: #3b82f6; }
.stat-icon.p-orange { background: #fff7ed; color: #f97316; }
.stat-icon.p-green { background: #f0fdf4; color: #10b981; }

.stat-label { font-size: 0.8rem; color: #64748b; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; }
.stat-value { font-size: 1.75rem; font-weight: 900; color: #0f172a; margin: 2px 0 0; }

/* Main Layout */
.campaign-layout-saas { display: grid; grid-template-columns: 1fr 380px; gap: 32px; }

.saas-card-premium { background: #fff; border-radius: 32px; border: 1px solid #f1f5f9; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.02); }
.saas-card-premium.mini { padding: 24px; }

.section-header-saas { display: flex; gap: 16px; margin-bottom: 32px; }
.accent-line { width: 4px; height: 44px; border-radius: 4px; }
.p-green { background: #10b981; }

.sh-text h3 { font-size: 1.25rem; font-weight: 900; color: #0f172a; margin: 0; }
.sh-text p { font-size: 0.85rem; color: #64748b; margin-top: 4px; font-weight: 600; }

/* Form Styles */
.saas-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.span-2 { grid-column: span 2; }
.span-1 { grid-column: span 1; }

.field-label { display: block; font-weight: 800; color: #475569; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }

.saas-template-row { display: flex; flex-wrap: wrap; gap: 10px; }
.saas-template-chip {
  background: #f8fafc; border: 1px solid #e2e8f0; color: #475569; border-radius: 12px;
  padding: 8px 16px; font-weight: 800; font-size: 0.85rem; cursor: pointer; transition: all 0.2s;
}
.saas-template-chip:hover { border-color: #3b82f6; color: #3b82f6; }
.saas-template-chip.active { background: #2563eb; color: #fff; border-color: #2563eb; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.2); }

.saas-input-large :deep(.el-input__wrapper), .saas-input-large :deep(.el-select__wrapper) { 
  background: #f8fafc !important; border: 1px solid #e2e8f0 !important; border-radius: 16px !important;
  height: 52px; box-shadow: none !important;
}

.saas-textarea-premium :deep(.el-textarea__inner) {
  background: #f8fafc !important; border: 1px solid #e2e8f0 !important; border-radius: 20px !important;
  padding: 16px !important; box-shadow: none !important; font-family: inherit; font-size: 0.95rem; line-height: 1.6;
}

.schedule-info-saas { 
  background: #f1f5f9; border-radius: 16px; padding: 16px 20px; display: flex; gap: 12px; align-items: flex-start;
  color: #475569; font-size: 0.85rem; font-weight: 600; margin-top: 10px;
}
.schedule-info-saas .el-icon { font-size: 18px; color: #2563eb; margin-top: 2px; }
.schedule-info-saas p { margin: 0; line-height: 1.5; }

.composer-actions { display: flex; gap: 16px; margin-top: 32px; justify-content: flex-end; }
.saas-btn-action { height: 52px !important; border-radius: 16px !important; font-weight: 900 !important; padding: 0 32px !important; }
.saas-btn-action.is-primary { background: #2563eb !important; border: none !important; box-shadow: 0 8px 15px rgba(37, 99, 235, 0.2); }
.saas-btn-action.is-secondary { background: #f1f5f9 !important; border: 1px solid #e2e8f0 !important; color: #1e293b !important; }

/* Sidebar Premium */
.saas-sidebar-premium { display: flex; flex-direction: column; gap: 24px; }
.sidebar-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.sh-left { display: flex; align-items: center; gap: 10px; }
.sh-left h4 { font-size: 0.95rem; font-weight: 900; color: #0f172a; margin: 0; text-transform: uppercase; letter-spacing: 0.05em; }
.sh-left .el-icon { color: #2563eb; }

.queue-stack-saas, .log-stack-saas { display: flex; flex-direction: column; gap: 12px; }

.queue-item-saas { 
  background: #f8fafc; border: 1px solid #f1f5f9; border-radius: 20px; padding: 16px;
  display: flex; flex-direction: column; gap: 8px;
}
.qi-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }
.qi-top strong { font-size: 0.9rem; color: #1e293b; font-weight: 800; line-height: 1.4; }
.qi-time { font-size: 0.7rem; color: #2563eb; font-weight: 900; background: #fff; padding: 4px 8px; border-radius: 6px; white-space: nowrap; }
.qi-subject { font-size: 0.8rem; color: #64748b; margin: 0; font-weight: 600; }
.qi-footer { font-size: 0.7rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; }

.log-item-saas {
  background: #fff; border: 1px solid #f1f5f9; border-radius: 16px; padding: 14px;
  transition: all 0.2s;
}
.log-item-saas:hover { border-color: #e2e8f0; background: #fafafa; }
.li-header { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.status-dot.sent { background: #10b981; box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1); }
.status-dot.failed { background: #ef4444; }
.li-header strong { font-size: 0.85rem; color: #1e293b; font-weight: 800; }
.li-subject { font-size: 0.75rem; color: #64748b; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.li-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; }
.li-time { font-size: 0.7rem; color: #94a3b8; font-weight: 700; }

.mini-clear-btn { font-size: 0.75rem; font-weight: 800; }
.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

@media (max-width: 1400px) {
  .campaign-layout-saas { grid-template-columns: 1fr; }
  .saas-sidebar-premium { display: grid; grid-template-columns: 1fr 1fr; }
}

@media (max-width: 900px) {
  .saas-sidebar-premium { grid-template-columns: 1fr; }
  .saas-stats-grid { grid-template-columns: 1fr; }
  .saas-form-grid { grid-template-columns: 1fr; }
}

.mr-1 { margin-right: 4px; }
.mr-2 { margin-right: 8px; }
.mt-6 { margin-top: 24px; }
.w-full { width: 100%; }
</style>
