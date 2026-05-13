<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  Monitor, Connection, ArrowLeft, CircleCheckFilled,
  InfoFilled, Search, Filter, VideoPlay, 
  Promotion, Trophy, Calendar, Setting,
  Tools, Histogram, List, Operation
} from '@element-plus/icons-vue'

const route = useRoute()

const moduleLabel = computed(() => route.meta.adminModuleLabel || 'Admin Module')
const moduleBadge = computed(() => route.meta.adminModuleBadge || 'STABLE')
const moduleItems = computed(() => route.meta.adminModuleHighlights || [
  'Quản lý vòng đời dữ liệu',
  'Tích hợp Real-time Dashboard',
  'Báo cáo và phân tích chuyên sâu'
])
const nextSteps = computed(() => [
  'Hoàn thiện contract dữ liệu FE cho module này.',
  'Dựng table, filter, drawer và form dialog theo design system admin.',
  'Nối API thật sau khi backend mở endpoint và RBAC tương ứng.',
])
</script>

<template>
  <div class="saas-container">
    <!-- Action Bar -->
    <section class="saas-header">
      <div class="header-left">
        <div class="operation-badge-premium orange">
          <el-icon class="mr-1"><Tools /></el-icon>
          <span>Module Architecture Roadmap</span>
        </div>
        <div class="header-titles">
          <h2 class="saas-title">{{ moduleLabel }}</h2>
          <p class="saas-subtitle">Hệ thống đang chuẩn bị cấu trúc dữ liệu cho mô-đun này</p>
        </div>
      </div>
      <div class="header-right">
        <div class="saas-status-tag-premium" :class="moduleBadge.toLowerCase()">
          {{ moduleBadge }}
        </div>
      </div>
    </section>

    <!-- Roadmap Content -->
    <div class="roadmap-grid-saas">
      <!-- Main Status Card -->
      <main class="saas-card-premium roadmap-main">
        <div class="roadmap-hero">
          <div class="hero-icon-wrap">
            <el-icon class="hero-icon"><Histogram /></el-icon>
          </div>
          <div class="hero-text">
            <h3>Cấu trúc & Định hướng</h3>
            <p>Module này đã được đăng ký vào hệ thống Router và Navigation. Hiện tại mã nguồn đang ở trạng thái định hướng (Skeleton), sẵn sàng để tích hợp các tính năng CRUD nâng cao ngay khi có Contract API.</p>
          </div>
        </div>

        <div class="progress-bar-saas">
          <div class="pb-track">
            <div class="pb-fill" style="width: 35%;"></div>
          </div>
          <div class="pb-labels">
            <span>Planning</span>
            <span>Design</span>
            <span>Development</span>
            <span>Testing</span>
          </div>
        </div>
      </main>

      <!-- Details Grid -->
      <div class="details-row-saas">
        <section class="saas-card-premium mini">
          <div class="card-header-saas">
            <el-icon class="mr-2"><List /></el-icon>
            <span>Phạm vi chính</span>
          </div>
          <ul class="roadmap-list-saas">
            <li v-for="item in moduleItems" :key="item">
              <el-icon class="mr-2"><CircleCheckFilled /></el-icon>
              {{ item }}
            </li>
          </ul>
        </section>

        <section class="saas-card-premium mini">
          <div class="card-header-saas">
            <el-icon class="mr-2"><Operation /></el-icon>
            <span>Bước tiếp theo</span>
          </div>
          <div class="step-stack-saas">
            <div v-for="(step, idx) in nextSteps" :key="idx" class="step-item-saas">
              <span class="step-num">{{ idx + 1 }}</span>
              <p>{{ step }}</p>
            </div>
          </div>
        </section>
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
.operation-badge-premium.orange { background: #fff7ed; color: #f97316; }

.header-titles { display: flex; flex-direction: column; gap: 4px; }
.saas-title { font-size: 1.8rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.02em; }
.saas-subtitle { font-size: 0.95rem; color: #64748b; margin: 0; }

.saas-status-tag-premium {
  padding: 8px 24px; border-radius: 99px; font-weight: 900; font-size: 0.75rem; letter-spacing: 0.1em;
  background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0;
}
.saas-status-tag-premium.stable { background: #f0fdf4; color: #16a34a; border-color: #dcfce7; }
.saas-status-tag-premium.beta { background: #fff7ed; color: #ea580c; border-color: #ffedd5; }

/* Roadmap Content */
.roadmap-grid-saas { display: flex; flex-direction: column; gap: 32px; }

.saas-card-premium { background: #fff; border-radius: 32px; border: 1px solid #f1f5f9; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.02); }
.saas-card-premium.mini { padding: 32px; }

.roadmap-hero { display: flex; gap: 32px; align-items: center; margin-bottom: 40px; }
.hero-icon-wrap { width: 80px; height: 80px; background: #fff7ed; color: #f97316; border-radius: 24px; display: flex; align-items: center; justify-content: center; font-size: 32px; }
.hero-text h3 { font-size: 1.5rem; font-weight: 900; color: #0f172a; margin: 0 0 12px; }
.hero-text p { font-size: 1.05rem; color: #64748b; margin: 0; line-height: 1.6; }

.progress-bar-saas { display: flex; flex-direction: column; gap: 16px; }
.pb-track { height: 12px; background: #f1f5f9; border-radius: 99px; overflow: hidden; }
.pb-fill { height: 100%; background: linear-gradient(90deg, #f97316, #ea580c); border-radius: 99px; }
.pb-labels { display: flex; justify-content: space-between; }
.pb-labels span { font-size: 0.75rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }

.details-row-saas { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
.card-header-saas { margin-bottom: 24px; display: flex; align-items: center; font-weight: 900; color: #1e293b; font-size: 1rem; text-transform: uppercase; letter-spacing: 0.05em; }

.roadmap-list-saas { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 16px; }
.roadmap-list-saas li { display: flex; align-items: center; font-size: 1rem; color: #475569; font-weight: 600; }
.roadmap-list-saas .el-icon { color: #10b981; font-size: 20px; }

.step-stack-saas { display: flex; flex-direction: column; gap: 16px; }
.step-item-saas { display: flex; gap: 16px; align-items: flex-start; }
.step-num { width: 28px; height: 28px; background: #eff6ff; color: #2563eb; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 0.8rem; flex-shrink: 0; }
.step-item-saas p { margin: 0; font-size: 0.95rem; color: #475569; font-weight: 600; line-height: 1.5; }

@media (max-width: 1100px) {
  .details-row-saas { grid-template-columns: 1fr; }
  .roadmap-hero { flex-direction: column; align-items: flex-start; gap: 24px; }
}

.mr-1 { margin-right: 4px; }
.mr-2 { margin-right: 8px; }
</style>
