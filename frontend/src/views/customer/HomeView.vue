<script setup>
import { RouterLink } from 'vue-router'

const featureCards = [
  {
    id: 'coaching',
    title: 'Performance Coaching',
    description: 'Huấn luyện chuyên sâu cùng đội ngũ coach giàu kinh nghiệm để nâng cấp kỹ thuật và thể lực thi đấu.',
    badge: 'ATP-level training',
  },
  {
    id: 'lounge',
    title: 'Member Lounge',
    description: 'Không gian kết nối thành viên, networking sau trận đấu và trải nghiệm dịch vụ cao cấp tại câu lạc bộ.',
    stat: '68% Full',
  },
  {
    id: 'mixers',
    title: 'Weekly Open Mixers',
    description: 'Các buổi giao lưu định kỳ giúp bạn thi đấu thực chiến, mở rộng cộng đồng và duy trì phong độ.',
    cta: 'Tham gia ngay',
  },
  {
    id: 'shop',
    title: 'The Pro Shop',
    description: 'Trang bị thi đấu, phụ kiện và dịch vụ căng vợt được tuyển chọn cho người chơi bán chuyên và chuyên nghiệp.',
    brands: ['WILSON', 'BABOLAT', 'HEAD'],
  },
]
</script>

<template>
  <div class="home-page">
    <section class="hero-section">
      <div class="hero-media" :style="{ backgroundImage: 'url(/src/assets/hero_bg.png)' }"></div>
      <div class="hero-overlay"></div>
      <div class="hero-grid"></div>

      <div class="container hero-content">
        <div class="hero-copy">
          <span class="hero-pill">Premium Club Experience</span>
          <h1 id="home-page-heading">
            Welcome to
            <span>Saigon Tennis</span>
          </h1>
          <p>
            Trải nghiệm nhịp điệu tennis hiện đại, nơi hiệu suất thi đấu, cộng đồng đẳng cấp và hệ
            thống quản lý chuyên nghiệp hội tụ trong một không gian premium.
          </p>

          <div class="hero-actions">
            <RouterLink id="book-court-home-button" to="/register-otp" class="btn-primary-solid">
              Đăng ký trải nghiệm
            </RouterLink>
            <RouterLink id="view-programs-home-button" to="/players" class="btn-secondary-ghost">
              Khám phá vận động viên
            </RouterLink>
          </div>
        </div>
      </div>

      <div class="hero-accent-card glass-card">
        <div class="accent-status">
          <span class="pulse-dot"></span>
          <strong>Live: 4 sân đang trống</strong>
        </div>
        <button id="hero-live-cta" type="button">+</button>
      </div>
    </section>

    <section class="featured-section container">
      <div class="bento-grid">
        <article class="bento-card bento-feature bento-coaching">
          <div class="feature-image"></div>
          <div class="feature-overlay"></div>
          <div class="feature-content">
            <span class="feature-badge">{{ featureCards[0].badge }}</span>
            <h2>{{ featureCards[0].title }}</h2>
            <p>{{ featureCards[0].description }}</p>
          </div>
        </article>

        <article class="bento-card bento-lounge">
          <div class="icon-wrap">✦</div>
          <div>
            <h3>{{ featureCards[1].title }}</h3>
            <p>{{ featureCards[1].description }}</p>
          </div>
          <div class="capacity-block">
            <div class="capacity-track">
              <div class="capacity-fill"></div>
            </div>
            <span>Capacity: {{ featureCards[1].stat }}</span>
          </div>
        </article>

        <article class="bento-card bento-mixers">
          <div class="icon-wrap calendar">◌</div>
          <h3>{{ featureCards[2].title }}</h3>
          <p>{{ featureCards[2].description }}</p>
          <RouterLink id="weekly-mixers-link" to="/matches" class="inline-link">
            {{ featureCards[2].cta }}
            <span>→</span>
          </RouterLink>
        </article>

        <article class="bento-card bento-shop">
          <div class="shop-copy">
            <h3>{{ featureCards[3].title }}</h3>
            <p>{{ featureCards[3].description }}</p>
            <div class="brand-list">
              <span v-for="brand in featureCards[3].brands" :key="brand">{{ brand }}</span>
            </div>
          </div>
          <div class="shop-visual">
            <div class="racket-card"></div>
          </div>
        </article>
      </div>
    </section>

    <section class="club-footer-section">
      <div class="container footer-shell">
        <div class="footer-branding">
          <h2>Saigon Tennis.</h2>
          <p>
            Nâng tầm tennis tại TP.HCM với hệ sinh thái thi đấu, huấn luyện, cộng đồng và công nghệ
            vận hành dành cho câu lạc bộ hiện đại.
          </p>
        </div>

        <div class="footer-links-grid">
          <div>
            <h4>Club</h4>
            <ul>
              <li><RouterLink to="/">Về chúng tôi</RouterLink></li>
              <li><RouterLink to="/players">Vận động viên</RouterLink></li>
              <li><RouterLink to="/tournaments">Giải đấu</RouterLink></li>
            </ul>
          </div>
          <div>
            <h4>Support</h4>
            <ul>
              <li><RouterLink to="/register-otp">Đăng ký</RouterLink></li>
              <li><RouterLink to="/login">Đăng nhập</RouterLink></li>
              <li><RouterLink to="/matches">Lịch đấu</RouterLink></li>
            </ul>
          </div>
          <div>
            <h4>Follow</h4>
            <div class="social-links">
              <span>Share</span>
              <span>Global</span>
            </div>
          </div>
        </div>
      </div>

      <div class="container footer-bottom-bar">
        © 2026 Saigon Tennis Club. All rights reserved. Professionalism in every swing.
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-page {
  background: #f8f9f9;
  color: #191c1c;
}

.hero-section {
  position: relative;
  min-height: 920px;
  display: flex;
  align-items: center;
  overflow: hidden;
  background: #f3f4f4;
}

.hero-media,
.hero-overlay,
.hero-grid {
  position: absolute;
  inset: 0;
}

.hero-media {
  background-size: cover;
  background-position: center;
  transform: scale(1.04);
}

.hero-overlay {
  background: linear-gradient(90deg, rgba(248, 249, 249, 0.98) 0%, rgba(248, 249, 249, 0.78) 36%, rgba(248, 249, 249, 0.18) 100%);
}

.hero-grid {
  background-image: linear-gradient(45deg, rgba(189, 201, 195, 0.12) 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.5;
}

.hero-content {
  position: relative;
  z-index: 2;
  width: 100%;
}

.hero-copy {
  max-width: 720px;
  padding: 4rem 0;
}

.hero-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.65rem 1rem;
  border-radius: 999px;
  background: #d1e4fb;
  color: #091d2e;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  margin-bottom: 1.5rem;
}

.hero-copy h1 {
  margin-bottom: 1.5rem;
  font-size: clamp(3.6rem, 8vw, 6rem);
  line-height: 1;
  letter-spacing: -0.05em;
  font-weight: 800;
}

.hero-copy h1 span {
  display: inline-block;
  color: #006953;
  font-style: italic;
}

.hero-copy p {
  max-width: 620px;
  margin-bottom: 2.2rem;
  font-size: 1.15rem;
  line-height: 1.8;
  color: #3e4945;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.btn-primary-solid,
.btn-secondary-ghost {
  min-height: 56px;
  padding: 0 2rem;
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  transition: transform 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
}

.btn-primary-solid {
  background: linear-gradient(135deg, #006953 0%, #13846a 100%);
  color: #ffffff;
  box-shadow: 0 18px 34px rgba(0, 105, 83, 0.22);
}

.btn-primary-solid:hover,
.btn-secondary-ghost:hover {
  transform: translateY(-2px) scale(1.01);
}

.btn-secondary-ghost {
  background: rgba(255, 255, 255, 0.9);
  color: #006953;
  border: 1px solid rgba(110, 122, 116, 0.18);
}

.hero-accent-card {
  position: fixed;
  right: 32px;
  bottom: 24px;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.65rem 0.65rem 0.65rem 1.2rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(0, 105, 83, 0.1);
  box-shadow: 0 20px 40px rgba(0, 105, 83, 0.12);
}

.glass-card {
  backdrop-filter: blur(16px);
}

.accent-status {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #191c1c;
  font-size: 0.92rem;
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

.hero-accent-card button {
  width: 48px;
  height: 48px;
  border: none;
  border-radius: 999px;
  background: #006953;
  color: #ffffff;
  font-size: 1.6rem;
  cursor: pointer;
}

.featured-section {
  padding-top: 7rem;
  padding-bottom: 7rem;
}

.bento-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 1.5rem;
}

.bento-card {
  position: relative;
  overflow: hidden;
  border-radius: 28px;
  min-height: 320px;
  box-shadow: 0 24px 50px rgba(25, 28, 28, 0.06);
}

.bento-feature {
  grid-column: span 8;
  min-height: 520px;
}

.feature-image,
.feature-overlay {
  position: absolute;
  inset: 0;
}

.feature-image {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), transparent),
    linear-gradient(135deg, rgba(0, 105, 83, 0.18), rgba(19, 132, 106, 0.04)),
    url('/src/assets/hero_bg.png') center/cover;
  transition: transform 0.7s ease;
}

.bento-feature:hover .feature-image {
  transform: scale(1.07);
}

.feature-overlay {
  background: linear-gradient(180deg, transparent 15%, rgba(25, 28, 28, 0.82) 100%);
}

.feature-content {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2;
  padding: 2.2rem;
  color: #ffffff;
}

.feature-badge {
  display: inline-flex;
  margin-bottom: 0.9rem;
  padding: 0.45rem 0.8rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.feature-content h2 {
  margin-bottom: 0.85rem;
  font-size: 2.2rem;
  line-height: 1.1;
}

.feature-content p {
  max-width: 520px;
  color: rgba(255, 255, 255, 0.86);
  line-height: 1.7;
}

.bento-lounge {
  grid-column: span 4;
  padding: 2.2rem;
  background: linear-gradient(180deg, #13846a 0%, #0f745e 100%);
  color: #f5fff9;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.icon-wrap {
  width: 64px;
  height: 64px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  margin-bottom: 1.5rem;
  background: rgba(255, 255, 255, 0.12);
  font-size: 1.8rem;
  font-weight: 800;
}

.bento-lounge h3,
.bento-mixers h3,
.bento-shop h3 {
  margin-bottom: 0.8rem;
  font-size: 2rem;
  line-height: 1.15;
}

.bento-lounge p,
.bento-mixers p,
.shop-copy p {
  line-height: 1.75;
}

.capacity-block {
  display: grid;
  gap: 0.75rem;
}

.capacity-track {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  overflow: hidden;
}

.capacity-fill {
  width: 68%;
  height: 100%;
  border-radius: inherit;
  background: #f5fff9;
}

.capacity-block span {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.bento-mixers {
  grid-column: span 4;
  padding: 2.2rem;
  background: #e7e8e8;
  color: #191c1c;
}

.calendar {
  color: #006953;
  background: rgba(0, 105, 83, 0.1);
}

.inline-link {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 1rem;
  color: #006953;
  font-weight: 800;
}

.inline-link span {
  transition: transform 0.25s ease;
}

.inline-link:hover span {
  transform: translateX(4px);
}

.bento-shop {
  grid-column: span 8;
  padding: 2.6rem;
  background: #ffffff;
  border: 1px solid rgba(189, 201, 195, 0.4);
  display: flex;
  align-items: center;
  gap: 2rem;
}

.shop-copy {
  flex: 1;
}

.brand-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1.3rem;
}

.brand-list span {
  padding: 0.75rem 1rem;
  border-radius: 999px;
  background: #f8f9f9;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.shop-visual {
  flex: 0 0 32%;
  display: flex;
  justify-content: center;
}

.racket-card {
  width: 220px;
  height: 260px;
  border-radius: 28px;
  transform: rotate(6deg) scale(1.04);
  background:
    radial-gradient(circle at 30% 24%, rgba(255, 255, 255, 0.28), transparent 18%),
    radial-gradient(circle at 58% 70%, rgba(225, 255, 0, 0.26), transparent 18%),
    linear-gradient(135deg, rgba(0, 105, 83, 0.18), rgba(19, 132, 106, 0.04)),
    #eef1f1;
  box-shadow: 0 30px 50px rgba(25, 28, 28, 0.08);
}

.club-footer-section {
  padding: 5rem 0 2.2rem;
  background: #ffffff;
  border-top: 1px solid rgba(189, 201, 195, 0.3);
}

.footer-shell {
  display: flex;
  justify-content: space-between;
  gap: 3rem;
}

.footer-branding {
  max-width: 420px;
}

.footer-branding h2 {
  margin-bottom: 1rem;
  font-size: 3rem;
  line-height: 1;
  letter-spacing: -0.05em;
  color: #123f34;
}

.footer-branding p {
  color: #4e6073;
  line-height: 1.8;
}

.footer-links-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(120px, 1fr));
  gap: 2.5rem;
}

.footer-links-grid h4 {
  margin-bottom: 1rem;
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #006953;
}

.footer-links-grid ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.9rem;
}

.footer-links-grid li,
.social-links span {
  color: #4e6073;
}

.social-links {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.footer-bottom-bar {
  margin-top: 4rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(189, 201, 195, 0.3);
  color: rgba(78, 96, 115, 0.8);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

@media (max-width: 1100px) {
  .bento-feature,
  .bento-lounge,
  .bento-mixers,
  .bento-shop {
    grid-column: span 12;
  }

  .bento-shop {
    flex-direction: column;
    align-items: flex-start;
  }

  .shop-visual {
    width: 100%;
    justify-content: flex-start;
  }

  .footer-shell {
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  .hero-section {
    min-height: 760px;
  }

  .hero-copy {
    padding: 3rem 0 5rem;
  }

  .hero-copy h1 {
    font-size: 3.2rem;
  }

  .hero-copy p {
    font-size: 1rem;
  }

  .hero-accent-card {
    right: 16px;
    left: 16px;
    bottom: 16px;
    justify-content: space-between;
  }

  .featured-section {
    padding-top: 4.5rem;
    padding-bottom: 4.5rem;
  }

  .bento-card,
  .bento-feature {
    min-height: auto;
  }

  .bento-feature {
    min-height: 420px;
  }

  .bento-mixers,
  .bento-lounge,
  .bento-shop {
    padding: 1.6rem;
  }

  .footer-links-grid {
    grid-template-columns: 1fr;
  }
}
</style>
