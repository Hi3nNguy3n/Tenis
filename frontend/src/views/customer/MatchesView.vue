<script setup>
import { ref } from 'vue'

const matches = ref([])

</script>

<template>
  <div class="matches-page">
    <section class="matches-hero container">
      <div>
        <span class="section-kicker">Live score center</span>
        <h1>Match Intelligence</h1>
        <p>
          Theo dõi diễn biến trận đấu theo phong cách trình bày hiện đại, rõ nhịp độ thi đấu và đồng
          bộ hoàn toàn với hệ thiết kế premium của site.
        </p>
      </div>

      <div class="live-indicator">
        <span class="pulse-dot"></span>
        <strong>{{ matches.length }} trận hiển thị</strong>
      </div>
    </section>

    <section class="matches-section container">
      <div class="matches-grid">
        <article v-for="match in matches" :key="match.id" class="match-card">
          <header class="match-header">
            <span>{{ match.tournament }}</span>
            <span>{{ match.court }}</span>
          </header>

          <div class="match-body">
            <div
              class="player-row"
              :class="{ winner: match.player1.sets > match.player2.sets && match.status === 'Finished' }"
            >
              <span class="player-name">{{ match.player1.name }}</span>
              <div class="score-list">
                <span v-for="(score, index) in match.player1.score" :key="`a-${index}`">{{ score }}</span>
              </div>
            </div>

            <div
              class="player-row"
              :class="{ winner: match.player2.sets > match.player1.sets && match.status === 'Finished' }"
            >
              <span class="player-name">{{ match.player2.name }}</span>
              <div class="score-list">
                <span v-for="(score, index) in match.player2.score" :key="`b-${index}`">{{ score }}</span>
              </div>
            </div>
          </div>

          <footer class="match-footer">
            <span class="status-pill" :class="match.status.toLowerCase().replace(' ', '-')">
              {{ match.status }}
            </span>
          </footer>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.matches-page {
  background: linear-gradient(180deg, #f8f9f9 0%, #eef1f1 100%);
  color: #191c1c;
}

.matches-hero {
  padding-top: 4.5rem;
  padding-bottom: 2.5rem;
  display: flex;
  align-items: end;
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

.matches-hero h1 {
  margin-bottom: 1rem;
  font-size: clamp(2.8rem, 6vw, 4.6rem);
  line-height: 1;
  letter-spacing: -0.05em;
}

.matches-hero p {
  max-width: 700px;
  color: #4e6073;
  line-height: 1.8;
}

.live-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.8rem;
  padding: 1rem 1.25rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 18px 32px rgba(25, 28, 28, 0.06);
}

.pulse-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #006953;
  box-shadow: 0 0 0 0 rgba(0, 105, 83, 0.45);
  animation: pulse 1.8s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(0, 105, 83, 0.45);
  }
  70% {
    box-shadow: 0 0 0 12px rgba(0, 105, 83, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(0, 105, 83, 0);
  }
}

.matches-section {
  padding-top: 1rem;
  padding-bottom: 6rem;
}

.matches-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 1.5rem;
}

.match-card {
  border-radius: 28px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 24px 44px rgba(25, 28, 28, 0.06);
}

.match-header,
.match-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.2rem 1.5rem;
  color: #6e7a74;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.match-header {
  background: rgba(243, 244, 244, 0.9);
}

.match-footer {
  border-top: 1px solid rgba(189, 201, 195, 0.36);
}

.match-body {
  padding: 1.8rem 1.5rem;
  display: grid;
  gap: 1rem;
}

.player-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.player-name {
  font-size: 1.2rem;
  font-weight: 700;
}

.score-list {
  display: flex;
  gap: 0.65rem;
}

.score-list span {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f4;
  font-weight: 800;
  color: #123f34;
}

.player-row.winner .player-name {
  color: #006953;
}

.status-pill {
  display: inline-flex;
  padding: 0.5rem 0.9rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.status-pill.in-progress {
  background: rgba(186, 26, 26, 0.12);
  color: #ba1a1a;
}

.status-pill.finished {
  background: rgba(0, 105, 83, 0.1);
  color: #006953;
}

@media (max-width: 900px) {
  .matches-hero {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 480px) {
  .matches-grid {
    grid-template-columns: 1fr;
  }

  .player-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
