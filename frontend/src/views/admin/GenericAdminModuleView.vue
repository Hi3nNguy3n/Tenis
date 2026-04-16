<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const moduleLabel = computed(() => route.meta.adminModuleLabel || 'Admin Module')
const moduleBadge = computed(() => route.meta.adminModuleBadge || 'UI')
const moduleItems = computed(() => route.meta.adminModuleHighlights || [])
const nextSteps = computed(() => [
  'Hoàn thiện contract dữ liệu FE cho module này.',
  'Dựng table, filter, drawer và form dialog theo design system admin.',
  'Nối API thật sau khi backend mở endpoint và RBAC tương ứng.',
])
</script>

<template>
  <div class="placeholder-shell">
    <section class="hero-card">
      <div class="hero-copy">
        <span class="eyebrow">Roadmap module</span>
        <h2>{{ moduleLabel }}</h2>
        <p>
          Module này đã được thêm vào menu và router để hoàn chỉnh kiến trúc Admin. Hiện tại đây là
          màn định hướng, sẵn sàng để phát triển thành CRUD đầy đủ khi chốt contract dữ liệu.
        </p>
      </div>

      <div class="status-chip">{{ moduleBadge }}</div>
    </section>

    <section class="content-grid">
      <article class="info-card">
        <h3>Phạm vi chính</h3>
        <ul>
          <li v-for="item in moduleItems" :key="item">{{ item }}</li>
        </ul>
      </article>

      <article class="info-card">
        <h3>Bước tiếp theo</h3>
        <ol>
          <li v-for="step in nextSteps" :key="step">{{ step }}</li>
        </ol>
      </article>
    </section>
  </div>
</template>

<style scoped>
.placeholder-shell {
  display: grid;
  gap: 20px;
}

.hero-card,
.info-card {
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 22px 40px rgba(16, 30, 26, 0.08);
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 28px;
  align-items: flex-start;
}

.hero-copy {
  max-width: 760px;
}

.eyebrow {
  display: inline-flex;
  margin-bottom: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(20, 98, 80, 0.08);
  color: #0f5c4d;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.hero-copy h2 {
  margin-bottom: 10px;
  font-size: clamp(1.8rem, 3vw, 2.5rem);
  line-height: 1.05;
  letter-spacing: -0.04em;
  color: #132722;
}

.hero-copy p,
.info-card li {
  color: #5d726c;
  line-height: 1.75;
}

.status-chip {
  min-width: 108px;
  padding: 10px 14px;
  border-radius: 8px;
  text-align: center;
  background: linear-gradient(135deg, #d7f171 0%, #b4db55 100%);
  color: #193126;
  font-weight: 800;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.info-card {
  padding: 24px;
}

.info-card h3 {
  margin-bottom: 14px;
  font-size: 1.05rem;
  color: #132722;
}

.info-card ul,
.info-card ol {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 10px;
}

@media (max-width: 900px) {
  .hero-card,
  .content-grid {
    grid-template-columns: 1fr;
  }

  .hero-card {
    flex-direction: column;
  }
}
</style>
