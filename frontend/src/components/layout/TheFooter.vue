<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <footer class="site-footer">
    <div class="container footer-shell">
      <div class="footer-branding">
        <RouterLink to="/" @click="window.scrollTo(0,0)">
          <img src="https://res.cloudinary.com/dfs9o3bny/image/upload/v1776309753/z7730353029258_1dbe77285e553a1aa2ae1ab543a985c8-removebg-preview_nj3utv.png" alt="Saigon Tennis" class="footer-logo" />
        </RouterLink>
        <div class="contact-info">
          <h3>Saigontennistours Center</h3>
          <p>📍 173 Cao Thắng, P12, Quận 10</p>
          <p>📞 Sđt: 0904599785</p>
        </div>
      </div>

      <div class="footer-links-grid">
        <div class="footer-col">
          <h4>Menu</h4>
          <ul>
            <li><RouterLink to="/players">Vận động viên</RouterLink></li>
            <li><RouterLink to="/tournaments">Giải đấu</RouterLink></li>
            <li><RouterLink to="/matches">Lịch đấu</RouterLink></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>Social</h4>
          <div class="social-actions">
            <a href="https://www.facebook.com/share/1N74PXKSQq/" target="_blank" class="social-link fb" title="Facebook">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796V24c5.737-.9 10.125-5.864 10.125-11.927z"/></svg>
              <span>Facebook</span>
            </a>
            <a href="https://www.tiktok.com/@saigontennistours" target="_blank" class="social-link tt" title="TikTok">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 448 512" fill="currentColor"><path d="M448 209.91a210.06 210.06 0 0 1-122.77-39.25v178.72c0 90.09-73.04 163.12-163.12 163.12S0 439.46 0 349.38s73.04-163.12 163.12-163.12c10.45 0 20.61.98 30.41 2.87V238c-9.74-2.73-19.98-4.2-30.41-4.2-63.53 0-115.11 51.58-115.11 115.11s51.58 115.11 115.11 115.11 115.11-51.58 115.11-115.11V0h90.91a210.06 210.06 0 0 0 137.91 109.91v99.99z"/></svg>
              <span>TikTok</span>
            </a>
          </div>
        </div>
      </div>
    </div>

    <div class="footer-bottom">
      <div class="container">
        <p>© 2026 SAIGONTENNISTOURS CENTER. All rights reserved.</p>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  padding: 4rem 0 0;
  background: #064e3b;
  color: white;
  border-top: 4px solid #c1ff72;
}

.footer-shell {
  display: flex;
  justify-content: space-between;
  gap: 3rem;
  padding-bottom: 4rem;
}

.footer-branding { max-width: 420px; }
.footer-logo { height: 80px; width: auto; object-fit: contain; margin-bottom: 1.5rem; display: block; }
.contact-info h3 { color: white; font-size: 1.1rem; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 1px; }
.contact-info p { color: #94a3b8; font-size: 0.9rem; margin-bottom: 0.3rem; }

.footer-links-grid { display: grid; grid-template-columns: repeat(2, minmax(140px, 1fr)); gap: 4rem; }
.footer-links-grid h4 { margin-bottom: 1.5rem; font-size: 0.9rem; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; color: #c1ff72; }
.footer-links-grid ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.8rem; }
.footer-links-grid li a { color: rgba(255, 255, 255, 0.7); font-weight: 600; text-decoration: none; transition: color 0.2s; }
.footer-links-grid li a:hover { color: #ffffff; }

.social-actions { display: flex; flex-direction: column; gap: 1rem; }
.social-link { display: flex; align-items: center; gap: 0.8rem; color: rgba(255, 255, 255, 0.7); text-decoration: none; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; }
.social-link svg { width: 20px; height: 20px; transition: transform 0.2s ease; }
.social-link:hover { color: #ffffff; }
.social-link:hover svg { transform: scale(1.1); }

.footer-bottom { padding: 1.5rem 0; background: rgba(0, 0, 0, 0.2); color: rgba(255,255,255,0.4); font-size: 0.75rem; font-weight: 700; text-transform: uppercase; text-align: center; border-top: 1px solid rgba(255, 255, 255, 0.05); }

@media (max-width: 768px) {
  .footer-shell { flex-direction: column; gap: 3rem; text-align: center; }
  .footer-branding { max-width: 100%; display: flex; flex-direction: column; align-items: center; }
  .footer-links-grid { grid-template-columns: 1fr; gap: 3rem; justify-items: center; }
  .social-link { justify-content: center; }
}

@media (max-width: 640px) {
  .footer-logo { height: 50px; }
}
</style>
