<script setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import TheHeader from './components/layout/TheHeader.vue'
import TheFooter from './components/layout/TheFooter.vue'

// Import Widget Chat vừa tạo
import ChatWidget from './views/customer/ChatRoom.vue' 

const route = useRoute()

const isAuthLayout = computed(() => Boolean(route.meta.authLayout))
const isAdminLayout = computed(() => Boolean(route.meta.adminLayout))
const shouldShowPublicChrome = computed(() => !isAuthLayout.value && !isAdminLayout.value)
</script>

<template>
  <TheHeader v-if="shouldShowPublicChrome" />

  <main
    :class="{
      'main-default': shouldShowPublicChrome,
      'main-auth': isAuthLayout,
      'main-admin': isAdminLayout,
    }"
  >
    <RouterView v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </RouterView>
  </main>

  <!-- CHÈN WIDGET CHAT VÀO ĐÂY -->
  <!-- Thêm v-if để không hiện khung chat ở trang Login hoặc Admin nếu muốn -->
  <ChatWidget v-if="shouldShowPublicChrome" />

  <TheFooter v-if="shouldShowPublicChrome" />
</template>

<style>
/* Global Layout Styles (Giữ nguyên như cũ) */
.main-default {
  padding-top: 80px;
  min-height: calc(100vh - 220px);
  scrollbar-gutter: stable; /* Prevent horizontal shifting */
}

.main-auth,
.main-admin {
  min-height: 100vh;
}

/* Page Transitions */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 1080px) {
  .main-default {
    padding-top: 70px;
  }
}

@media (max-width: 640px) {
  .main-default {
    padding-top: 56px;
  }
}

@media (max-width: 480px) {
  .main-default {
    padding-top: 50px;
  }
}
</style>