<script setup>
import { RouterLink } from 'vue-router'
import { t } from '../../utils/locale'
import { Location, Phone, Message, Right } from '@element-plus/icons-vue'
</script>

<template>
  <footer class="site-footer">
    <div class="container footer-shell">
      
      <!-- CỘT 1: THƯƠNG HIỆU & LIÊN HỆ -->
      <div class="footer-brand">
        <RouterLink to="/" @click="window.scrollTo(0,0)" class="logo-link">
          <img src="https://res.cloudinary.com/dfs9o3bny/image/upload/v1776309753/z7730353029258_1dbe77285e553a1aa2ae1ab543a985c8-removebg-preview_nj3utv.png" alt="Saigon Tennis" class="footer-logo" />
        </RouterLink>
        <p class="brand-desc">{{ t('auth.brandDesc') }}</p>
        
        <div class="contact-list">
          <div class="contact-item">
            <el-icon class="c-icon"><Location /></el-icon>
            <span>{{ t('footer.address') }}: 173 Cao Thắng, Phường 12, Quận 10, TP.HCM</span>
          </div>
          <div class="contact-item">
            <el-icon class="c-icon"><Phone /></el-icon>
            <span>{{ t('footer.phone') }}: 0904.599.785</span>
          </div>
          <div class="contact-item">
            <el-icon class="c-icon"><Message /></el-icon>
            <span>contact@saigontennis.com</span>
          </div>
        </div>
      </div>

      <!-- CỘT 2: MENU ĐIỀU HƯỚNG -->
      <div class="footer-links">
        <h4>{{ t('footer.menu') }}</h4>
        <ul>
          <li>
            <RouterLink to="/players">
              <el-icon class="arrow"><Right /></el-icon> {{ t('nav.players') }}
            </RouterLink>
          </li>
          <li>
            <RouterLink to="/tournaments">
              <el-icon class="arrow"><Right /></el-icon> {{ t('nav.tournaments') }}
            </RouterLink>
          </li>
          <li>
            <RouterLink to="/matches">
              <el-icon class="arrow"><Right /></el-icon> {{ t('nav.matches') }}
            </RouterLink>
          </li>
          <li>
            <RouterLink to="/rankings">
              <el-icon class="arrow"><Right /></el-icon> {{ t('nav.rankings') }}
            </RouterLink>
          </li>
          <li>
            <RouterLink to="/news">
              <el-icon class="arrow"><Right /></el-icon> {{ t('nav.news') }}
            </RouterLink>
          </li>
        </ul>
      </div>

      <!-- CỘT 3: MẠNG XÃ HỘI -->
      <div class="footer-social">
        <h4>{{ t('footer.social') }}</h4>
        <p>{{ t('footer.socialDesc') || 'Theo dõi Saigontennistours trên các nền tảng mạng xã hội để cập nhật tin tức nhanh nhất.' }}</p>
        
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

    <!-- BOTTOM BAR -->
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
/* =========================================================
   TỔNG QUAN FOOTER
========================================================= */
.site-footer {
  background: #f8fafc; /* Nền Slate cực nhạt */
  color: #1e293b; 
  padding: 5rem 0 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  border-top: 1px solid #e2e8f0; 
  -webkit-font-smoothing: antialiased; 
}

.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.footer-shell {
  display: grid;
  grid-template-columns: 2.5fr 1fr 1.5fr;
  gap: 4rem;
  padding-bottom: 4rem;
}

/* =========================================================
   CỘT 1: THƯƠNG HIỆU & LIÊN HỆ
========================================================= */
.footer-logo { 
  height: 80px; /* Logo to và rõ ràng hơn */
  object-fit: contain; 
  margin-bottom: 1.5rem; 
  transition: transform 0.3s ease;
  /* Đã bỏ filter grayscale để giữ nguyên màu gốc */
}

.logo-link:hover .footer-logo {
  transform: translateY(-2px); 
}

.brand-desc { 
  color: #475569; /* Xám Slate 600 */
  font-size: 0.95rem; 
  line-height: 1.7; 
  margin-bottom: 2rem; 
  max-width: 400px; 
  font-weight: 500; 
}

.contact-list { 
  display: flex; 
  flex-direction: column; 
  gap: 1rem; 
}

.contact-item { 
  display: flex; 
  align-items: center; 
  gap: 12px; 
  color: #0f172a; 
  font-size: 0.95rem; 
  font-weight: 600; 
}

.c-icon { 
  font-size: 1.2rem; 
  color: #002855; /* Điểm nhấn màu xanh Navy ATP */
}

/* =========================================================
   CỘT 2 & 3: TIÊU ĐỀ
========================================================= */
.footer-links h4, .footer-social h4 {
  color: #002855; /* Màu Navy Blue chuẩn thể thao */
  font-size: 1.1rem;
  font-weight: 800; 
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 1.5rem;
}

/* =========================================================
   CỘT 2: LINKS
========================================================= */
.footer-links ul { 
  list-style: none; 
  padding: 0; 
  margin: 0;
  display: flex; 
  flex-direction: column; 
  gap: 1.2rem; 
}

.footer-links a {
  color: #475569; 
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 600; 
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.arrow { 
  color: #94a3b8; 
  font-size: 1.1rem;
  transition: transform 0.2s ease, color 0.2s ease; 
}

.footer-links a:hover { 
  color: #002855; 
}

.footer-links a:hover .arrow { 
  transform: translateX(5px); 
  color: #002855; 
}

/* =========================================================
   CỘT 3: MẠNG XÃ HỘI
========================================================= */
.footer-social p { 
  color: #475569; 
  font-size: 0.95rem; 
  line-height: 1.6; 
  margin-bottom: 1.5rem; 
  font-weight: 500;
}

.social-icons { 
  display: flex; 
  gap: 1rem; 
}

.social-btn {
  width: 44px;
  height: 44px;
  border-radius: 8px; 
  background: #ffffff;
  border: 1px solid #cbd5e1; 
  color: #0f172a; 
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.social-btn svg { 
  width: 20px; 
  height: 20px; 
  fill: currentColor; 
}

.social-btn:hover { 
  background: #002855; 
  color: #ffffff;      
  border-color: #002855; 
  transform: translateY(-3px); 
  box-shadow: 0 4px 12px rgba(0, 40, 85, 0.15); 
}

/* =========================================================
   BOTTOM BAR (BẢN QUYỀN)
========================================================= */
.footer-bottom {
  background: #ffffff;
  border-top: 1px solid #e2e8f0;
  padding: 1.5rem 0;
}

.bottom-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #475569; 
  font-size: 0.85rem;
  font-weight: 600; 
}

.bottom-flex p { margin: 0; }

.legal-links { 
  display: flex; 
  gap: 1rem; 
  align-items: center; 
}

.legal-links a { 
  color: #475569; 
  text-decoration: none; 
  transition: color 0.2s; 
}

.legal-links a:hover { color: #002855; }
.divider { color: #cbd5e1; }

/* =========================================================
   RESPONSIVE
========================================================= */
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
  .footer-logo {
    height: 60px;
  }
  .bottom-flex { 
    flex-direction: column; 
    gap: 1rem; 
    text-align: center; 
  }
}
</style>