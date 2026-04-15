<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="payment-failure container">
    <div class="failure-card">
      <div class="icon-section">
        <div class="icon">❌</div>
      </div>

      <h1>Thanh toán thất bại</h1>
      <p class="description">
        Rất tiếc, quá trình thanh toán của bạn không thành công hoặc thời gian giữ chỗ đã hết hạn. Đơn đăng ký này đã bị hủy tự động.
      </p>

      <div class="action-section">
        <button class="btn-primary" @click="router.push('/tournaments')">Tìm giải đấu khác</button>
        <button class="btn-secondary" @click="router.push('/profile/my-tournaments')">Hồ sơ của tôi</button>
      </div>

      <div class="support-check">
        <p>Nếu bạn đã bị trừ tiền nhưng chưa nhận được xác nhận, vui lòng liên hệ hotline: <strong>090x xxx xxx</strong> để được hỗ trợ kiểm tra đối soát.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.payment-failure {
  padding-top: 10rem;
  padding-bottom: 6rem;
  display: flex;
  justify-content: center;
}

.failure-card {
  max-width: 600px;
  width: 100%;
  background: white;
  padding: 4rem;
  border-radius: 40px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0,0,0,0.05);
}

.icon-section {
  width: 100px;
  height: 100px;
  margin: 0 auto 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffebee;
  border-radius: 50%;
}

.icon {
  font-size: 3.5rem;
}

h1 { color: #ba1a1a; font-size: 2.2rem; margin-bottom: 1.5rem; }
.description { color: #6e7a74; font-size: 1.1rem; line-height: 1.6; margin-bottom: 3rem; }

.action-section { display: flex; flex-direction: column; gap: 1rem; }

.btn-primary {
  padding: 1.2rem; border: none; border-radius: 18px;
  background: #123f34; color: white; font-weight: 800; font-size: 1.1rem;
  cursor: pointer; transition: 0.2s;
}
.btn-primary:hover { background: #000; transform: translateY(-3px); }

.btn-secondary {
  padding: 1.2rem; background: transparent; border: 2px solid #eef1f1;
  border-radius: 18px; color: #4e6073; font-weight: 700; cursor: pointer; transition: 0.2s;
}
.btn-secondary:hover { background: #f8f9f9; }

.support-check { margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #f0f0f0; }
.support-check p { font-size: 0.9rem; color: #9e9e9e; }
</style>
