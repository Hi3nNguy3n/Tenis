<script setup>
import { RouterLink } from 'vue-router'
import { t } from '../../utils/locale'
</script>

<template>
  <footer class="site-footer">
    <div class="footer-pattern"></div>
    <div class="footer-pattern-left"></div>

    <div class="container footer-shell">
      
      <div class="footer-brand">
        <RouterLink to="/" @click="window.scrollTo(0,0)" class="logo-link">
          <img src="https://res.cloudinary.com/dfs9o3bny/image/upload/v1776309753/z7730353029258_1dbe77285e553a1aa2ae1ab543a985c8-removebg-preview_nj3utv.png" alt="Saigon Tennis" class="footer-logo" />
        </RouterLink>
        <p class="brand-desc">{{ t('auth.brandDesc') }}</p>
        
        <div class="contact-list">
          <div class="contact-item">
            <span class="c-icon">📍</span>
            <span>{{ t('footer.address') }}: 173 Cao Thắng, Phường 12, Quận 10, TP.HCM</span>
          </div>
          <div class="contact-item">
            <span class="c-icon">📞</span>
            <span>{{ t('footer.phone') }}: 0904.599.785</span>
          </div>
          <div class="contact-item">
            <span class="c-icon">✉️</span>
            <span>contact@saigontennis.com</span>
          </div>
        </div>
      </div>

      <div class="footer-links">
        <h4>{{ t('footer.menu') }}</h4>
        <ul>
          <li><RouterLink to="/players"><span class="arrow">→</span> {{ t('nav.players') }}</RouterLink></li>
          <li><RouterLink to="/tournaments"><span class="arrow">→</span> {{ t('nav.tournaments') }}</RouterLink></li>
          <li><RouterLink to="/matches"><span class="arrow">→</span> {{ t('nav.matches') }}</RouterLink></li>
          <li><RouterLink to="/rankings"><span class="arrow">→</span> {{ t('nav.rankings') }}</RouterLink></li>
          <li><RouterLink to="/news"><span class="arrow">→</span> {{ t('nav.news') }}</RouterLink></li>
        </ul>
      </div>

      <div class="footer-social">
        <h4>{{ t('footer.social') }}</h4>
        <p>{{ t('footer.socialDesc') || 'Theo dõi Saigon Tennis trên các nền tảng mạng xã hội.' }}</p>
        
        <div class="social-icons">
          <a href="https://www.facebook.com/share/1N74PXKSQq/" target="_blank" class="social-btn fb" title="Facebook">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796V24c5.737-.9 10.125-5.864 10.125-11.927z"/></svg>
          </a>
          <a href="https://www.tiktok.com/@saigontennistours" target="_blank" class="social-btn tt" title="TikTok">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path d="M448 209.91a210.06 210.06 0 0 1-122.77-39.25v178.72c0 90.09-73.04 163.12-163.12 163.12S0 439.46 0 349.38s73.04-163.12 163.12-163.12c10.45 0 20.61.98 30.41 2.87V238c-9.74-2.73-19.98-4.2-30.41-4.2-63.53 0-115.11 51.58-115.11 115.11s51.58 115.11 115.11 115.11 115.11-51.58 115.11-115.11V0h90.91a210.06 210.06 0 0 0 137.91 109.91v99.99z"/></svg>
          </a>
          <a href="#" target="_blank" class="social-btn yt" title="YouTube">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.5 12 3.5 12 3.5s-7.505 0-9.377.55a3.016 3.016 0 0 0-2.122 2.136C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.55 9.376.55 9.376.55s7.505 0 9.377-.55a3.016 3.016 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
          </a>
        </div>
      </div>
    </div>

    <div class="footer-bottom">
      <div class="container bottom-flex">
        <p>{{ t('footer.rights') }}</p>
        <div class="legal-links">
          <a href="#">Điều khoản sử dụng</a>
          <span class="divider">•</span>
          <a href="#">Chính sách bảo mật</a>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  position: relative;
  background: #093f1d; /* Xanh Navy Đậm */
  color: #f8fafc;
  padding: 5rem 0 0;
  overflow: hidden;
  font-family: inherit;
}

/* Hiệu ứng bóng mờ (Glow) */
.footer-pattern {
  position: absolute;
  top: -150px;
  right: -100px;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(204, 255, 0, 0.06) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}
.footer-pattern-left {
  position: absolute;
  bottom: 0;
  left: -150px;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.08) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.footer-shell {
  display: grid;
  grid-template-columns: 2fr 1fr 1.5fr;
  gap: 4rem;
  padding-bottom: 4rem;
  position: relative;
  z-index: 1;
}

/* === CỘT 1: THƯƠNG HIỆU === */
.footer-logo { 
  height: 65px; 
  object-fit: contain; 
  margin-bottom: 1.5rem; 
  filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3)); 
}
.brand-desc { 
  color: #94a3b8; 
  font-size: 0.95rem; 
  line-height: 1.6; 
  margin-bottom: 1.5rem; 
  max-width: 380px; 
}
.contact-list { 
  display: flex; 
  flex-direction: column; 
  gap: 0.8rem; 
}
.contact-item { 
  display: flex; 
  align-items: flex-start; 
  gap: 12px; 
  color: #cbd5e1; 
  font-size: 0.9rem; 
}
.c-icon { 
  font-size: 1.1rem; 
}

/* === CỘT 2 & 3: TIÊU ĐỀ === */
.footer-links h4, .footer-social h4 {
  color: #ccff00; /* Vàng chanh Tennis */
  font-size: 1.1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 1.5rem;
}

/* === CỘT 2: LINKS === */
.footer-links ul { 
  list-style: none; 
  padding: 0; 
  margin: 0;
  display: flex; 
  flex-direction: column; 
  gap: 1rem; 
}
.footer-links a {
  color: #cbd5e1;
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 500;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.arrow { 
  color: #10b981; 
  transition: transform 0.2s ease; 
  font-family: Arial, sans-serif; /* Fix mũi tên */
}
.footer-links a:hover { 
  color: #fff; 
}
.footer-links a:hover .arrow { 
  transform: translateX(4px); 
  color: #ccff00; 
}

/* === CỘT 3: SOCIAL === */
.footer-social p { 
  color: #94a3b8; 
  font-size: 0.95rem; 
  line-height: 1.6; 
  margin-bottom: 1.5rem; 
}
.social-icons { 
  display: flex; 
  gap: 1rem; 
}
.social-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.social-btn svg { 
  width: 20px; 
  height: 20px; 
  fill: currentColor; 
}
.social-btn:hover { 
  background: #ccff00; 
  color: #b1b4bc; 
  border-color: #ccff00; 
  transform: translateY(-4px); 
  box-shadow: 0 10px 20px -5px rgba(204, 255, 0, 0.4); 
}

/* === BOTTOM BAR === */
.footer-bottom {
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding: 1.5rem 0;
}
.bottom-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #64748b;
  font-size: 0.85rem;
  font-weight: 500;
}
.bottom-flex p { margin: 0; }

.legal-links { 
  display: flex; 
  gap: 1rem; 
  align-items: center; 
}
.legal-links a { 
  color: #64748b; 
  text-decoration: none; 
  transition: color 0.2s; 
}
.legal-links a:hover { color: #cbd5e1; }
.divider { color: #334155; }

/* === RESPONSIVE === */
@media (max-width: 960px) {
  .footer-shell { 
    grid-template-columns: 1fr 1fr; 
    gap: 3rem; 
  }
  .footer-brand { 
    grid-column: span 2; 
  }
  .brand-desc { 
    max-width: 100%; 
  }
}

@media (max-width: 640px) {
  .site-footer { padding: 4rem 0 0; }
  .footer-shell { 
    grid-template-columns: 1fr; 
    gap: 2.5rem; 
    padding-bottom: 2.5rem;
  }
  .footer-brand { 
    grid-column: span 1; 
  }
  .bottom-flex { 
    flex-direction: column; 
    gap: 1rem; 
    text-align: center; 
  }
}
</style>