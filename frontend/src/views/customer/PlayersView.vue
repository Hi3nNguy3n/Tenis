<script setup>
import { computed, ref } from 'vue'

const players = ref([])


const totalPoints = computed(() => players.value.reduce((sum, player) => sum + player.points, 0))
</script>

<template>
  <div class="players-page">
    <section class="players-hero container">
      <div class="hero-copy">
        <span class="section-kicker">Player ranking</span>
        <h1>Elite Players</h1>
        <p>
          Danh sách những vận động viên nổi bật trong hệ sinh thái Saigon Tennis, được trình bày theo
          phong cách premium đồng bộ với giao diện Home mới.
        </p>
      </div>

      <div class="hero-stats">
        <div class="stat-card">
          <span>Total Athletes</span>
          <strong>{{ players.length }}</strong>
        </div>
        <div class="stat-card emphasis">
          <span>Total Ranking Points</span>
          <strong>{{ totalPoints }}</strong>
        </div>
      </div>
    </section>

    <section class="players-section container">
      <div class="players-grid">
        <article v-for="player in players" :key="player.id" class="player-card">
          <div class="player-top">
            <span class="player-rank">#{{ player.rank }}</span>
            <div class="avatar-shell">🎾</div>
          </div>

          <div class="player-content">
            <h2>{{ player.name }}</h2>
            <p>{{ player.country }}</p>
          </div>

          <div class="player-divider"></div>

          <div class="player-metrics">
            <span>Points</span>
            <strong>{{ player.points }}</strong>
          </div>

          <button class="profile-button" type="button">View Profile</button>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.players-page {
  background: linear-gradient(180deg, #f8f9f9 0%, #eef1f1 100%);
  color: #191c1c;
}

.players-hero {
  padding-top: 4.5rem;
  padding-bottom: 2.5rem;
  display: flex;
  justify-content: space-between;
  gap: 2rem;
  align-items: end;
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

.hero-copy h1 {
  margin-bottom: 1rem;
  font-size: clamp(2.8rem, 6vw, 4.6rem);
  line-height: 1;
  letter-spacing: -0.05em;
}

.hero-copy p {
  max-width: 700px;
  color: #4e6073;
  line-height: 1.8;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(180px, 1fr));
  gap: 1rem;
}

.stat-card {
  min-width: 180px;
  padding: 1.25rem 1.4rem;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 20px 36px rgba(25, 28, 28, 0.05);
}

.stat-card span {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.78rem;
  color: #6e7a74;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.stat-card strong {
  font-size: 1.9rem;
  color: #123f34;
}

.stat-card.emphasis {
  background: linear-gradient(135deg, #006953 0%, #13846a 100%);
}

.stat-card.emphasis span,
.stat-card.emphasis strong {
  color: #ffffff;
}

.players-section {
  padding-top: 1rem;
  padding-bottom: 6rem;
}

.players-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.player-card {
  padding: 2rem;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 24px 44px rgba(25, 28, 28, 0.06);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.player-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 28px 52px rgba(25, 28, 28, 0.08);
}

.player-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.player-rank {
  color: #006953;
  font-size: 1rem;
  font-weight: 800;
}

.avatar-shell {
  width: 82px;
  height: 82px;
  border-radius: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(0, 105, 83, 0.1), rgba(19, 132, 106, 0.18));
  font-size: 2rem;
}

.player-content h2 {
  margin-bottom: 0.35rem;
  font-size: 1.7rem;
  line-height: 1.2;
}

.player-content p {
  color: #6e7a74;
}

.player-divider {
  height: 1px;
  margin: 1.5rem 0;
  background: rgba(189, 201, 195, 0.5);
}

.player-metrics span {
  display: block;
  margin-bottom: 0.4rem;
  font-size: 0.78rem;
  color: #6e7a74;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.player-metrics strong {
  font-size: 2rem;
  color: #006953;
}

.profile-button {
  width: 100%;
  min-height: 50px;
  margin-top: 1.5rem;
  border: 1px solid rgba(0, 105, 83, 0.12);
  border-radius: 18px;
  background: rgba(0, 105, 83, 0.05);
  color: #006953;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

@media (max-width: 900px) {
  .players-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-stats {
    width: 100%;
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 640px) {
  .hero-stats {
    grid-template-columns: 1fr;
  }
}
</style>
