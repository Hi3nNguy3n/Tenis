<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { newsService } from '../../services/newsService'

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

const newsItems = ref([])

onMounted(async () => {
  try {
    const data = await newsService.getAllPosts({ limit: 3 })
    newsItems.value = data.map(post => ({
      id: post.id,
      slug: post.slug,
      title: post.title,
      date: new Date(post.publish_at || post.created_at).toLocaleDateString('vi-VN'),
      category: 'Tin tức', // Default label
      excerpt: post.summary,
      image: post.thumbnail_url || 'https://images.unsplash.com/photo-1592709823125-a191f07a2a5e?auto=format&fit=crop&q=80&w=800'
    }))
  } catch (error) {
    console.error('Failed to fetch news:', error)
  }
})

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
        <div class="grid-left-col">
          <article class="bento-card bento-feature bento-coaching">
            <div class="feature-image"></div>
            <div class="feature-overlay"></div>
            <div class="feature-content">
              <span class="feature-badge">{{ featureCards[0].badge }}</span>
              <h2>{{ featureCards[0].title }}</h2>
              <p>{{ featureCards[0].description }}</p>
            </div>
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

        <div class="grid-right-col">
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
        </div>
      </div>
    </section>

    <section class="news-section container">
      <div class="section-header">
        <span class="section-kicker">Tin mới nhất</span>
        <h2>Tin tức Tennis</h2>
      </div>
      
      <div class="news-grid">
        <article v-for="news in newsItems" :key="news.id" class="news-card">
          <div class="news-img-wrap">
            <img :src="news.image" :alt="news.title" />
            <span class="news-cat">{{ news.category }}</span>
          </div>
          <div class="news-body">
            <span class="news-date">{{ news.date }}</span>
            <h3>{{ news.title }}</h3>
            <p>{{ news.excerpt }}</p>
            <RouterLink :to="'/news/' + news.slug" class="news-link">Xem chi tiết <span>→</span></RouterLink>
          </div>
        </article>
      </div>
    </section>

  </div>
</template>

<style scoped>
.home-page {
  background: var(--bg-main);
  color: var(--text-dark);
}

.hero-section {
  position: relative;
  min-height: 380px;
  display: flex;
  align-items: center;
  overflow: hidden;
  background: var(--text-dark);
}

.hero-media,
.hero-overlay,
.hero-grid {
  position: absolute;
  inset: 0;
}

.hero-media {
  background-image: url('/src/assets/hero_bg.png');
  background-size: cover;
  background-position: center 20%;
  opacity: 0.4;
  transform: scale(1.02);
}

.hero-overlay {
  background: linear-gradient(90deg, rgba(15, 23, 42, 0.95) 0%, rgba(15, 23, 42, 0.6) 50%, rgba(15, 23, 42, 0) 100%);
}

.hero-grid {
  background-image: linear-gradient(45deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 30px 30px;
  opacity: 0.5;
}

.hero-content {
  position: relative;
  z-index: 2;
  width: 100%;
}

.hero-copy {
  max-width: 680px;
  padding: 3rem 0;
}

.hero-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.65rem 1rem;
  border-radius: 8px;
  background: #d1e4fb;
  color: #091d2e;
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  margin-bottom: 1.5rem;
}

.hero-copy h1 {
  margin-bottom: 1.5rem;
  font-size: clamp(2.4rem, 5vw, 4.2rem);
  line-height: 1;
  letter-spacing: -0.01em;
  font-weight: 500;
  color: #fff;
}

.hero-copy h1 span {
  display: inline-block;
  color: var(--primary);
  font-style: normal;
  margin-left: 0.5rem;
}

.hero-copy p {
  max-width: 580px;
  margin-bottom: 2rem;
  font-size: 1.05rem;
  line-height: 1.7;
  color: #cbd5e1;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.btn-primary-solid,
.btn-secondary-ghost {
  min-height: 52px;
  padding: 0 2rem;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.btn-primary-solid {
  background: var(--primary);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(21, 128, 61, 0.2);
}

.btn-primary-solid:hover {
  background: var(--primary-hover);
  transform: translateY(-2px);
}

.btn-secondary-ghost {
  background: transparent;
  color: var(--primary);
  border: 2px solid var(--primary);
}

.btn-secondary-ghost:hover {
  background: var(--primary);
  color: #ffffff;
  transform: translateY(-2px);
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
  border-radius: 4px;
  background: var(--glass-bg);
  border: 1px solid var(--border-light);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
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
  border-radius: 50%;
  background: var(--secondary);
  box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.45);
  animation: pulse 1.8s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.45);
  }
  70% {
    box-shadow: 0 0 0 12px rgba(34, 197, 94, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0);
  }
}

.hero-accent-card button {
  width: 48px;
  height: 48px;
  border: none;
  border-radius: 4px;
  background: var(--primary);
  color: #ffffff;
  font-size: 1.6rem;
  cursor: pointer;
}

.featured-section {
  padding-top: 3rem;
  padding-bottom: 5rem;
}

.bento-grid {
  display: flex;
  gap: 1.25rem;
}

.grid-left-col {
  flex: 0 0 calc(66.66% - 0.625rem);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.grid-right-col {
  flex: 0 0 calc(33.33% - 0.625rem);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.bento-card {
  position: relative;
  overflow: hidden;
  border-radius: 8px; /* Softer radius */
  background: #ffffff;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
  border: 1px solid var(--border-light);
  width: 100%;
}

.bento-feature {
  min-height: auto;
  display: flex;
  flex-direction: column;
}

.feature-image {
  position: relative;
  height: 360px;
  background: url('/src/assets/hero_bg.png') center/cover;
  border-bottom: 4px solid var(--primary);
}

.feature-overlay {
  display: none; /* Removed gradient */
}

.feature-content {
  position: relative;
  padding: 1.8rem;
  color: var(--text-dark);
  background: #ffffff;
}

.feature-badge {
  display: inline-flex;
  margin-bottom: 0.75rem;
  padding: 0.25rem 0.6rem;
  border-radius: 2px;
  background: var(--bg-soft);
  color: var(--primary);
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.feature-content h2 {
  margin-bottom: 0.6rem;
  font-size: 1.8rem;
  font-weight: 500;
  line-height: 1.2;
  color: var(--text-dark);
}

.feature-content p {
  color: var(--text-muted);
  line-height: 1.6;
  font-size: 0.95rem;
  max-width: 100%;
}

.bento-lounge {
  padding: 1.8rem;
  background: var(--text-dark);
  color: #ffffff;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: none;
}

.icon-wrap {
  width: 64px;
  height: 64px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  background: rgba(255, 255, 255, 0.15);
  font-size: 1.8rem;
  font-weight: 500;
}

.bento-lounge h3,
.bento-mixers h3,
.bento-shop h3 {
  margin-bottom: 0.5rem;
  font-size: 1.4rem;
  font-weight: 500;
  line-height: 1.2;
  text-transform: uppercase;
}

.bento-lounge p,
.bento-mixers p,
.shop-copy p {
  line-height: 1.6;
  font-size: 0.9rem;
}

.bento-lounge p {
  color: #cbd5e1;
}

.capacity-block {
  display: grid;
  gap: 0.6rem;
  margin-top: 1.5rem;
}

.capacity-track {
  width: 100%;
  height: 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.capacity-fill {
  width: 68%;
  height: 100%;
  border-radius: inherit;
  background: var(--primary);
}

.capacity-block span {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #94a3b8;
}

.bento-mixers {
  padding: 1.8rem;
  background: #ffffff;
  color: var(--text-dark);
}

.calendar {
  color: var(--primary);
  background: var(--bg-soft);
}

.inline-link {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 1rem;
  color: var(--primary);
  font-weight: 500;
  text-transform: uppercase;
}

.inline-link span {
  transition: transform 0.25s ease;
}

.inline-link:hover span {
  transform: translateX(4px);
}

.bento-shop {
  padding: 1.8rem;
  background: #ffffff;
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
  border-radius: 8px;
  background: #f8f9f9;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.12em;
}

.shop-visual {
  flex: 0 0 32%;
  display: flex;
  justify-content: center;
}

.racket-card {
  width: 180px;
  height: 220px;
  border-radius: 4px;
  transform: rotate(4deg);
  background:
    radial-gradient(circle at 30% 24%, rgba(255, 255, 255, 0.8), transparent 18%),
    radial-gradient(circle at 58% 70%, rgba(34, 197, 94, 0.4), transparent 18%),
    #e2e8f0;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
}

@media (max-width: 1024px) {
  .bento-grid {
    flex-direction: column;
  }
  
  .grid-left-col, .grid-right-col {
    flex: 1 1 100%;
  }

  .bento-shop {
    flex-direction: column;
    align-items: flex-start;
  }

  .shop-visual {
    width: 100%;
    justify-content: center;
  }
}

.news-section {
  padding-bottom: 5rem;
}

.section-header {
  margin-bottom: 2.5rem;
}

.section-kicker {
  display: block;
  color: var(--primary);
  font-weight: 500;
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 0.1rem;
  margin-bottom: 0.5rem;
}

.section-header h2 {
  font-family: var(--font-main);
  font-size: 2.8rem;
  font-weight: 500;
  text-transform: uppercase;
  color: var(--text-dark);
  letter-spacing: -0.01em;
}

.news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.news-card {
  background: #ffffff;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease;
}

.news-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.news-img-wrap {
  position: relative;
  height: 200px;
}

.news-img-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.news-cat {
  position: absolute;
  top: 1rem;
  left: 1rem;
  background: var(--primary);
  color: white;
  padding: 0.25rem 0.75rem;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  border-radius: 2px;
}

.news-body {
  padding: 1.5rem;
}

.news-date {
  color: var(--text-muted);
  font-size: 0.8rem;
  font-weight: 600;
  display: block;
  margin-bottom: 0.5rem;
}

.news-body h3 {
  font-size: 1.25rem;
  font-weight: 500;
  margin-bottom: 0.8rem;
  line-height: 1.3;
  color: var(--text-dark);
}

.news-body p {
  color: var(--text-muted);
  font-size: 0.95rem;
  margin-bottom: 1.2rem;
  line-height: 1.6;
}

.news-link {
  color: var(--primary);
  font-weight: 500;
  font-size: 0.85rem;
  text-transform: uppercase;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.news-link span {
  transition: transform 0.2s ease;
}

.news-link:hover span {
  transform: translateX(4px);
}


@media (max-width: 768px) {
  .hero-section {
    min-height: auto;
  }

  .hero-copy {
    padding: 3rem 0;
  }

  .hero-copy h1 {
    font-size: 2.2rem;
  }

  .hero-accent-card {
    display: none;
  }

  .featured-section {
    padding-top: 2rem;
    padding-bottom: 2rem;
  }

  .feature-image {
    height: 240px;
  }

  .section-header h2 {
    font-size: 1.8rem;
  }

  .news-img-wrap {
    height: 180px;
  }
}
</style>
