<script setup>
import { ref } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'
import jsQR from 'jsqr'
import { 
  Monitor, VideoPlay, Calendar, SuccessFilled,
  WarningFilled, Search, Pointer, Picture,
  Connection, User, Trophy, Location,
  Checked, Camera
} from '@element-plus/icons-vue'
import { t } from '../../utils/locale'

const registrationId = ref('')
const isLoading = ref(false)
const checkInData = ref(null)
const error = ref('')

// Ref để trỏ tới thẻ input file ẩn
const fileInput = ref(null)

const handleCheckIn = async () => {
  let id = registrationId.value.trim()
  if (!id) return
  
  // Hỗ trợ người dùng nhập cả tiền tố STT_REG_
  if (id.toUpperCase().startsWith('STT_REG_')) {
    id = id.substring(8)
  }
  
  isLoading.value = true
  error.value = ''
  checkInData.value = null
  
  try {
    // API scan check-in
    const result = await apiClient.post(`/api/registrations/${id}/check-in`)
    checkInData.value = result
    ElMessage.success(t('admin.checkInSuccess'))
    registrationId.value = '' // Clear for next scan
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('admin.checkInError')
    ElMessage.error(error.value)
  } finally {
    isLoading.value = false
  }
}

// Hàm kích hoạt click vào input file ẩn
const triggerFileInput = () => {
  fileInput.value.click()
}

// Hàm xử lý khi người dùng chọn ảnh
const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    const img = new Image()
    img.onload = () => {
      // 1. Tạo canvas để trích xuất dữ liệu ảnh (ImageData)
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')
      canvas.width = img.width
      canvas.height = img.height
      context.drawImage(img, 0, 0, canvas.width, canvas.height)
      
      const imageData = context.getImageData(0, 0, canvas.width, canvas.height)
      
      // 2. Dùng jsQR để giải mã dữ liệu pixel
      const code = jsQR(imageData.data, imageData.width, imageData.height)
      
      if (code && code.data) {
        registrationId.value = code.data
        ElMessage.success(t('admin.scanSuccess'))
        handleCheckIn() // Tự động gọi hàm check-in sau khi quét xong
      } else {
        ElMessage.error(t('admin.scanError'))
      }
    }
    img.src = e.target.result
  }
  reader.readAsDataURL(file)
  
  // Reset input để người dùng có thể chọn lại cùng 1 file nếu cần
  event.target.value = ''
}
</script>

<template>
  <div class="saas-container" v-loading="isLoading">
    <!-- Action Bar -->
    <section class="saas-header">
      <div class="header-left">
        <div class="operation-badge-premium pink">
          <el-icon class="mr-1"><Checked /></el-icon>
          <span>Access Control</span>
        </div>
        <div class="header-titles">
          <h2 class="saas-title">{{ $t('admin.checkInTitle') || 'Hệ thống Check-in' }}</h2>
          <p class="saas-subtitle">{{ $t('admin.checkInSub') || 'Xác nhận vận động viên có mặt tại giải đấu' }}</p>
        </div>
      </div>
    </section>

    <!-- Main Content Grid -->
    <div class="checkin-grid-premium">
      <!-- Left Column: Scanner -->
      <div class="saas-card-premium scanner-block">
        <div class="scanner-device-mock">
          <div class="device-lens">
            <div class="laser-scanner"></div>
            <div class="lens-glass">
              <el-icon class="camera-icon"><Camera /></el-icon>
              <div class="upload-overlay" @click="triggerFileInput">
                <el-icon><Picture /></el-icon>
                <span>{{ $t('admin.uploadQrTitle') }}</span>
              </div>
            </div>
          </div>
          <input 
            type="file" 
            accept="image/*" 
            ref="fileInput" 
            style="display: none" 
            @change="handleFileUpload"
          />
        </div>

        <div class="manual-input-section">
          <div class="section-divider">
            <span>{{ $t('admin.manualInputLabel') }}</span>
          </div>
          <div class="input-wrapper-saas">
            <el-input 
              v-model="registrationId" 
              :placeholder="$t('admin.manualInputPlaceholder')" 
              @keyup.enter="handleCheckIn"
              class="saas-input-large"
            >
              <template #prefix><el-icon><Pointer /></el-icon></template>
            </el-input>
            <el-button type="primary" @click="handleCheckIn" class="saas-btn-primary">
              {{ $t('admin.confirm') }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- Right Column: Result -->
      <div class="saas-card-premium result-block">
        <div class="result-viewport">
          <!-- Success State -->
          <div v-if="checkInData" class="status-result success-anim">
            <div class="status-icon-wrapper p-green">
              <el-icon><SuccessFilled /></el-icon>
            </div>
            <h3 class="status-title">{{ $t('admin.checkInSuccess') }}</h3>
            
            <div class="result-details-stack">
              <div class="detail-item-saas">
                <div class="di-label"><el-icon><User /></el-icon> {{ $t('admin.playerLabel') }}</div>
                <div class="di-value">{{ checkInData.player_name }}</div>
              </div>
              <div class="detail-item-saas">
                <div class="di-label"><el-icon><Trophy /></el-icon> {{ $t('admin.tournamentLabel') }}</div>
                <div class="di-value">{{ checkInData.tournament_name }}</div>
              </div>
              <div class="detail-item-saas">
                <div class="di-label"><el-icon><Location /></el-icon> {{ $t('admin.locationLabel') }}</div>
                <div class="di-value">{{ checkInData.location }}</div>
              </div>
            </div>

            <div class="success-footer-tip">
              <el-icon class="mr-2"><Checked /></el-icon>
              <span>{{ $t('admin.playerPresentTip') }}</span>
            </div>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="status-result error-anim">
            <div class="status-icon-wrapper p-red">
              <el-icon><WarningFilled /></el-icon>
            </div>
            <h3 class="status-title is-error">{{ $t('admin.authError') }}</h3>
            <p class="error-msg">{{ error }}</p>
            <el-button @click="error = ''" plain round class="mt-4">Thử lại</el-button>
          </div>

          <!-- Idle State -->
          <div v-else class="status-result idle-state">
            <div class="idle-visual">
              <div class="pulse-ring"></div>
              <div class="pulse-ring delay-1"></div>
              <el-icon class="idle-icon"><Connection /></el-icon>
            </div>
            <p>{{ $t('admin.qrScanPrompt') }}</p>
          </div>
        </div>
      </div>
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
.operation-badge-premium.pink { background: #fdf2f8; color: #db2777; }

.header-titles { display: flex; flex-direction: column; gap: 4px; }
.saas-title { font-size: 1.8rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.02em; }
.saas-subtitle { font-size: 0.95rem; color: #64748b; margin: 0; }

/* Grid Layout */
.checkin-grid-premium { display: grid; grid-template-columns: 1.2fr 1fr; gap: 32px; }

.saas-card-premium { background: #fff; border-radius: 32px; border: 1px solid #f1f5f9; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.02); }

/* Scanner Block */
.scanner-block { display: flex; flex-direction: column; align-items: center; justify-content: center; }

.scanner-device-mock {
  width: 100%; max-width: 400px; aspect-ratio: 1; position: relative;
  background: #0f172a; border-radius: 40px; padding: 12px;
  box-shadow: 0 30px 60px rgba(15, 23, 42, 0.2); border: 8px solid #1e293b;
}

.device-lens {
  width: 100%; height: 100%; border-radius: 32px; background: #000;
  position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center;
}

.lens-glass {
  position: relative; z-index: 10; display: flex; flex-direction: column; align-items: center; gap: 16px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer; width: 100%; height: 100%; justify-content: center;
}
.lens-glass:hover { background: rgba(59, 130, 246, 0.1); }

.camera-icon { font-size: 64px; color: rgba(255, 255, 255, 0.2); transition: 0.3s; }
.lens-glass:hover .camera-icon { color: rgba(255, 255, 255, 0.4); transform: scale(1.1); }

.upload-overlay {
  display: flex; flex-direction: column; align-items: center; gap: 10px; color: #fff;
  font-weight: 800; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.1em;
}

.laser-scanner {
  position: absolute; top: 0; left: 0; width: 100%; height: 4px;
  background: linear-gradient(90deg, transparent, #ef4444, transparent);
  box-shadow: 0 0 20px #ef4444; animation: laser-move 3s linear infinite; z-index: 5;
}

@keyframes laser-move { 0% { top: -5%; } 100% { top: 105%; } }

.manual-input-section { width: 100%; max-width: 400px; margin-top: 40px; }
.section-divider { 
  display: flex; align-items: center; gap: 16px; margin-bottom: 24px; color: #94a3b8; font-size: 0.75rem; 
  font-weight: 900; text-transform: uppercase; letter-spacing: 0.15em; 
}
.section-divider::before, .section-divider::after { content: ''; flex: 1; height: 1px; background: #f1f5f9; }

.input-wrapper-saas { display: flex; gap: 12px; }
.saas-input-large :deep(.el-input__wrapper) { 
  background: #f8fafc !important; border: 1px solid #e2e8f0 !important; border-radius: 16px !important;
  height: 52px; box-shadow: none !important;
}

.saas-btn-primary { 
  height: 52px !important; border-radius: 16px !important; font-weight: 900 !important; padding: 0 24px !important;
  background: #2563eb !important; border: none !important;
}

/* Result Block */
.result-block { min-height: 500px; display: flex; align-items: center; justify-content: center; }
.result-viewport { width: 100%; }

.status-result { display: flex; flex-direction: column; align-items: center; text-align: center; }

.status-icon-wrapper {
  width: 100px; height: 100px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 50px; margin-bottom: 24px;
}
.status-icon-wrapper.p-green { background: #f0fdf4; color: #10b981; border: 4px solid #dcfce7; }
.status-icon-wrapper.p-red { background: #fef2f2; color: #ef4444; border: 4px solid #fee2e2; }

.status-title { font-size: 1.5rem; font-weight: 900; color: #0f172a; margin: 0 0 32px; }
.status-title.is-error { color: #ef4444; }

.result-details-stack { width: 100%; background: #f8fafc; border-radius: 24px; padding: 24px; display: flex; flex-direction: column; gap: 16px; margin-bottom: 32px; }
.detail-item-saas { display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; border-bottom: 1px solid #f1f5f9; }
.detail-item-saas:last-child { border: none; padding: 0; }

.di-label { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; }
.di-value { font-weight: 800; color: #1e293b; font-size: 1.1rem; }

.success-footer-tip {
  background: #f0fdf4; color: #166534; padding: 16px 24px; border-radius: 16px;
  font-weight: 800; font-size: 0.9rem; display: flex; align-items: center;
}

.error-msg { color: #64748b; font-weight: 600; line-height: 1.6; }

/* Idle State */
.idle-state p { color: #94a3b8; font-weight: 700; font-style: italic; margin-top: 24px; }
.idle-visual { position: relative; width: 120px; height: 120px; display: flex; align-items: center; justify-content: center; }
.idle-icon { font-size: 48px; color: #cbd5e1; position: relative; z-index: 5; }

.pulse-ring {
  position: absolute; inset: 0; border: 2px solid #e2e8f0; border-radius: 50%;
  animation: pulse-ring 3s infinite cubic-bezier(0.215, 0.61, 0.355, 1);
}
.pulse-ring.delay-1 { animation-delay: 1s; }

@keyframes pulse-ring {
  0% { transform: scale(0.33); opacity: 0; }
  80%, 100% { opacity: 0; }
  50% { opacity: 1; }
}

/* Animations */
.success-anim { animation: slide-up 0.5s ease-out; }
.error-anim { animation: shake 0.5s ease-in-out; }

@keyframes slide-up { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-10px); }
  75% { transform: translateX(10px); }
}

@media (max-width: 1024px) {
  .checkin-grid-premium { grid-template-columns: 1fr; }
}

.mr-1 { margin-right: 4px; }
.mr-2 { margin-right: 8px; }
.mt-4 { margin-top: 16px; }
</style>