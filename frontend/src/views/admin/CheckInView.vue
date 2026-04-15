<script setup>
import { ref } from 'vue'
import { apiClient } from '../../services/apiClient'
import { ElMessage } from 'element-plus'

const registrationId = ref('')
const isLoading = ref(false)
const checkInData = ref(null)
const error = ref('')

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
    ElMessage.success('Check-in thành công!')
    registrationId.value = '' // Clear for next scan
  } catch (err) {
    error.value = err.message || 'Lỗi khi check-in.'
    ElMessage.error(error.value)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="checkin-module">
    <section class="hero-card">
      <div>
        <span class="section-kicker">Attendance Control</span>
        <h2>Quét mã Check-in</h2>
        <p>Sử dụng để quét mã QR của vận động viên khi họ đến sân thi đấu.</p>
      </div>
    </section>

    <section class="scanner-container">
      <div class="scanner-mock">
        <div class="scanner-frame">
          <div class="scan-line"></div>
          <div class="scanner-placeholder">
             <span class="icon">📷</span>
             <p> Camera Scanner Mock </p>
          </div>
        </div>
        
        <div class="manual-input">
          <p>Hoặc nhập mã Registration ID thủ công:</p>
          <div class="input-group">
            <el-input v-model="registrationId" placeholder="VD: 123" @keyup.enter="handleCheckIn" />
            <el-button type="primary" :loading="isLoading" @click="handleCheckIn">Xác nhận</el-button>
          </div>
        </div>
      </div>

      <div class="result-panel">
        <div v-if="checkInData" class="success-card">
          <div class="check-icon">✓</div>
          <h3>Check-in thành công!</h3>
          <div class="info-details">
             <div class="info-row">
               <span>Vận động viên:</span>
               <strong>{{ checkInData.player_name }}</strong>
             </div>
             <div class="info-row">
               <span>Giải đấu:</span>
               <strong>{{ checkInData.tournament_name }}</strong>
             </div>
             <div class="info-row">
               <span>Cụm sân:</span>
               <strong>{{ checkInData.location }}</strong>
             </div>
             <p class="success-tip">Vận động viên đã được xác nhận có mặt.</p>
          </div>

        </div>

        <div v-else-if="error" class="error-card">
          <div class="err-icon">!</div>
          <h3>Lỗi xác thực</h3>
          <p>{{ error }}</p>
        </div>

        <div v-else class="empty-result">
          <p>Yêu cầu quét mã QR để hiển thị kết quả xác thực tại đây.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.checkin-module { display: grid; gap: 24px; }

.hero-card {
  border-radius: 28px;
  background: white;
  padding: 28px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.03);
}

.section-kicker {
  display: inline-flex;
  margin-bottom: 12px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(0, 105, 83, 0.08);
  color: #006953;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.hero-card h2 { font-size: 2.2rem; margin-bottom: 10px; color: #123f34; }
.hero-card p { color: #6e7a74; }

.scanner-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.scanner-mock {
  background: white;
  padding: 2rem;
  border-radius: 28px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.03);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.scanner-frame {
  width: 300px;
  height: 300px;
  border: 4px solid #006953;
  border-radius: 24px;
  position: relative;
  overflow: hidden;
  background: #000;
  margin-bottom: 2rem;
}

.scan-line {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 4px;
  background: #d7f171;
  box-shadow: 0 0 15px #d7f171;
  animation: scan 2s linear infinite;
}

@keyframes scan {
  from { top: 0; }
  to { top: 100%; }
}

.scanner-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: white;
  opacity: 0.5;
}

.scanner-placeholder .icon { font-size: 3rem; margin-bottom: 1rem; }

.manual-input { width: 100%; text-align: center; }
.manual-input p { font-size: 0.9rem; color: #6e7a74; margin-bottom: 1rem; }
.input-group { display: flex; gap: 10px; max-width: 300px; margin: 0 auto; }

.result-panel {
  background: #f8f9f9;
  border-radius: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  border: 4px dashed #eef1f1;
}

.success-card {
  text-align: center;
  background: white;
  padding: 3rem;
  border-radius: 24px;
  box-shadow: 0 20px 50px rgba(19, 132, 106, 0.1);
  width: 100%;
}

.check-icon {
  width: 80px; height: 80px; background: #e8f5e9; color: #2e7d32;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 2.5rem; margin: 0 auto 1.5rem;
}

.info-row { display: flex; justify-content: space-between; margin: 1.5rem 0; padding-top: 1rem; border-top: 1px solid #f0f0f0; }

.error-card { text-align: center; color: #ba1a1a; }
.err-icon { font-size: 4rem; margin-bottom: 1rem; }

.success-tip {
  margin-top: 1.5rem;
  font-size: 0.9rem;
  color: #2e7d32;
  font-weight: 600;
  background: #f1f8f1;
  padding: 0.5rem;
  border-radius: 8px;
}

.empty-result { color: #bdc9c3; text-align: center; font-style: italic; }


@media (max-width: 800px) {
  .scanner-container { grid-template-columns: 1fr; }
}
</style>
