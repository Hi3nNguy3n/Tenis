<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTournamentStore } from '../../../stores/tournament'

const router = useRouter()
const tournamentStore = useTournamentStore()

onMounted(() => {
  tournamentStore.fetchTournaments()
})

const getStatusLabel = (status) => {
  const labels = {
    open: 'Đang mở đăng ký',
    ongoing: 'Đang diễn ra',
    finished: 'Đã kết thúc',
    draft: 'Sắp ra mắt'
  }
  return labels[status] || status
}

const viewDetail = (id) => {
  router.push({ name: 'tournament-detail', params: { id } })
}
</script>

<template>
  <div class="tournaments-page">
    <section class="tournaments-hero container">
      <div>
        <span class="section-kicker">Lịch trình giải đấu</span>
        <h1>Các giải đấu lớn</h1>
        <p>
          Khám phá và tham gia các giải đấu chuyên nghiệp trong hệ sinh thái Saigon Tennis. 
          Nơi hội tụ những tay vợt xuất sắc và những trận cầu kịch tính.
        </p>
      </div>

      <div class="hero-highlight">
        <span>Sự kiện mùa giải</span>
        <strong>{{ tournamentStore.tournaments.length }}</strong>
      </div>
    </section>

    <div v-if="tournamentStore.loading" class="loading-state container">
      <div class="spinner"></div>
      <p>Đang tải danh sách giải đấu...</p>
    </div>

    <section v-else class="tournaments-list-section container">
      <article 
        v-for="t in tournamentStore.tournaments" 
        :key="t.id" 
        class="tournament-card"
        @click="viewDetail(t.id)"
      >
        <div class="status-pill" :class="t.status">{{ getStatusLabel(t.status) }}</div>

        <div class="tournament-main">
          <div class="tournament-copy">
            <span class="type-pill">{{ t.category_type }} - {{ t.gender_division }}</span>
            <h2>{{ t.name }}</h2>
            <p>Bắt đầu: {{ new Date(t.start_date).toLocaleDateString('vi-VN') }}</p>
          </div>

          <div class="tournament-meta">
            <div>
              <span>Sân thi đấu</span>
              <strong>{{ t.surface_type || '---' }}</strong>

            </div>
            <div class="location-meta">
              <span>Địa điểm</span>
              <strong>{{ t.location || '---' }}</strong>

            </div>
          </div>
        </div>

        <div class="tournament-actions">
          <button class="action-button action-button-primary">Chi tiết</button>
        </div>
      </article>

      <div v-if="tournamentStore.tournaments.length === 0" class="empty-state">
        <p>Hiện chưa có giải đấu nào được công bố.</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.tournaments-page {
  background: linear-gradient(180deg, #f8f9f9 0%, #eef1f1 100%);
  color: #191c1c;
  min-height: 100vh;
}

.tournaments-hero {
  padding-top: 6rem;
  padding-bottom: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
}

.section-kicker {
  display: inline-flex;
  margin-bottom: 1rem;
  padding: 0.55rem 0.9rem;
  border-radius: 999px;
  background: #d1e4fb;
  color: #091d2e;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.tournaments-hero h1 {
  margin-bottom: 1rem;
  font-size: clamp(2.8rem, 6vw, 4.6rem);
  line-height: 1;
  letter-spacing: -0.05em;
  color: #123f34;
}

.tournaments-hero p {
  max-width: 680px;
  color: #4e6073;
  line-height: 1.8;
}

.hero-highlight {
  min-width: 180px;
  padding: 1.25rem 1.5rem;
  border-radius: 24px;
  background: linear-gradient(135deg, #006953 0%, #13846a 100%);
  color: #ffffff;
  box-shadow: 0 20px 36px rgba(0, 105, 83, 0.16);
}

.hero-highlight span {
  display: block;
  margin-bottom: 0.4rem;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
}

.hero-highlight strong {
  font-size: 2.2rem;
}

.tournaments-list-section {
  padding-top: 1rem;
  padding-bottom: 6rem;
  display: grid;
  gap: 1.25rem;
}

.tournament-card {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.6rem 1.8rem;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 24px 44px rgba(25, 28, 28, 0.06);
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.tournament-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 32px 64px rgba(25, 28, 28, 0.1);
}

.status-pill {
  min-width: 140px;
  padding: 0.65rem 1rem;
  border-radius: 999px;
  text-align: center;
  font-size: 0.78rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.status-pill.open { background: rgba(0, 105, 83, 0.1); color: #006953; }
.status-pill.ongoing { background: rgba(186, 26, 26, 0.1); color: #ba1a1a; }
.status-pill.finished { background: #f3f4f4; color: #6e7a74; }
.status-pill.draft { background: #fff8e1; color: #f57f17; }

.tournament-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.type-pill {
  display: inline-flex;
  margin-bottom: 0.7rem;
  padding: 0.45rem 0.8rem;
  border-radius: 999px;
  background: #f3f4f4;
  color: #006953;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.tournament-copy h2 {
  margin-bottom: 0.55rem;
  font-size: 1.8rem;
  color: #123f34;
}

.tournament-copy p {
  color: #6e7a74;
}

.tournament-meta {
  display: flex;
  gap: 2rem;
}

.tournament-meta span {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: #6e7a74;
}

.tournament-meta strong {
  font-size: 1.1rem;
  color: #123f34;
}

.action-button {
  min-height: 50px;
  padding: 0 1.8rem;
  border-radius: 18px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  border: none;
  background: linear-gradient(135deg, #006953 0%, #13846a 100%);
  color: #ffffff;
  transition: opacity 0.2s;
}

.action-button:hover {
  opacity: 0.9;
}

.loading-state {
  text-align: center;
  padding: 4rem 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 105, 83, 0.1);
  border-top-color: #006953;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 4rem 0;
  color: #6e7a74;
}

@media (max-width: 900px) {
  .tournaments-hero {
    flex-direction: column;
    align-items: flex-start;
    padding-top: 5rem;
  }
  
  .tournament-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .tournament-main {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }

  .tournament-meta {
    flex-direction: column;
    gap: 1rem;
  }

  .tournament-actions {
    width: 100%;
  }

  .action-button {
    width: 100%;
  }
}
</style>
