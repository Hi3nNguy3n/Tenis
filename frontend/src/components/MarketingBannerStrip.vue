<script setup>
import { computed, onMounted, ref } from 'vue'
import apiClient from '../services/apiClient'

const props = defineProps({
  placement: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    default: '',
  },
  max: {
    type: Number,
    default: 1,
  },
  variant: {
    type: String,
    default: 'wide',
  },
})

const banners = ref([])

const visibleBanners = computed(() => banners.value.filter((banner) => banner?.image_url).slice(0, props.max))

onMounted(async () => {
  try {
    const data = await apiClient.get('/api/marketing/banners', {
      params: {
        placement: props.placement,
        limit: props.max,
      },
    })
    banners.value = Array.isArray(data) ? data : []
  } catch {
    banners.value = []
  }
})
</script>

<template>
  <section v-if="visibleBanners.length" class="marketing-strip" :class="`is-${variant}`">
    <div v-if="title" class="marketing-strip-heading">{{ title }}</div>
    <div class="marketing-strip-grid" :class="{ 'single-card': visibleBanners.length === 1 }">
      <a
        v-for="banner in visibleBanners"
        :key="banner.id"
        class="marketing-strip-card"
        :href="banner.link_url || '#'"
        :target="banner.open_in_new_tab ? '_blank' : '_self'"
        rel="noopener"
        @click="!banner.link_url && $event.preventDefault()"
      >
        <div class="marketing-strip-media">
          <img class="marketing-strip-bg" :src="banner.image_url" alt="" aria-hidden="true" referrerpolicy="no-referrer" />
          <img class="marketing-strip-img" :src="banner.image_url" :alt="banner.title" referrerpolicy="no-referrer" />
        </div>
        <div class="marketing-strip-overlay">
          <strong>{{ banner.title }}</strong>
          <span v-if="banner.subtitle">{{ banner.subtitle }}</span>
        </div>
      </a>
    </div>
  </section>
</template>

<style scoped>
.marketing-strip {
  width: 100%;
  margin-bottom: 24px;
}

.marketing-strip-heading {
  margin-bottom: 10px;
  color: #0f172a;
  font-size: 1rem;
  font-weight: 900;
}

.marketing-strip-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.marketing-strip-grid.single-card {
  grid-template-columns: 1fr;
}

.marketing-strip-card {
  position: relative;
  display: block;
  min-height: 180px;
  overflow: hidden;
  border-radius: 14px;
  background: #0f172a;
  color: #ffffff;
  text-decoration: none;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.12);
  isolation: isolate;
}

.marketing-strip-media {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background:
    radial-gradient(circle at 20% 10%, rgba(37, 99, 235, 0.22), transparent 34%),
    linear-gradient(135deg, #0f172a 0%, #111827 48%, #020617 100%);
  overflow: hidden;
}

.marketing-strip-bg {
  position: absolute;
  inset: -18px;
  width: calc(100% + 36px);
  height: calc(100% + 36px);
  object-fit: cover;
  filter: blur(18px);
  opacity: 0.34;
  transform: scale(1.04);
}

.marketing-strip-img {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: transform 0.35s ease, opacity 0.35s ease;
}

.marketing-strip-card:hover .marketing-strip-img {
  transform: scale(1.02);
  opacity: 0.82;
}

.marketing-strip-card::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.08), rgba(15, 23, 42, 0.82));
}

.marketing-strip-overlay {
  position: absolute;
  inset: auto 0 0 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 20px;
}

.marketing-strip-overlay strong {
  font-size: clamp(1.1rem, 2vw, 1.65rem);
  line-height: 1.15;
  font-weight: 900;
}

.marketing-strip-overlay span {
  color: #dbeafe;
  font-size: 0.9rem;
  line-height: 1.4;
}

.is-compact .marketing-strip-card {
  min-height: clamp(120px, 14vw, 170px);
  max-height: 180px;
}

.is-compact .marketing-strip-media {
  inset: 12px 14px 12px auto;
  width: min(46%, 560px);
  padding: 0;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.28);
  z-index: 2;
}

.is-compact .marketing-strip-bg {
  inset: -30px;
  width: calc(100% + 60px);
  height: calc(100% + 60px);
  opacity: 0.28;
}

.is-compact .marketing-strip-img {
  object-fit: cover;
}

.is-compact .marketing-strip-overlay {
  inset: 0 auto 0 0;
  width: 52%;
  justify-content: center;
  padding: 16px 24px;
}

.is-compact .marketing-strip-overlay strong {
  font-size: clamp(1rem, 1.6vw, 1.35rem);
}

.is-compact .marketing-strip-overlay span {
  font-size: 0.82rem;
}

.is-sidebar .marketing-strip-grid {
  grid-template-columns: 1fr;
}

.is-sidebar .marketing-strip-card {
  min-height: 170px;
  border-radius: 12px;
}

@media (max-width: 768px) {
  .marketing-strip-card {
    min-height: 170px;
  }

  .is-compact .marketing-strip-media {
    inset: 0;
    width: 100%;
    border-radius: 0;
  }

  .is-compact .marketing-strip-img {
    object-fit: cover;
    opacity: 0.76;
  }

  .is-compact .marketing-strip-overlay {
    inset: auto 0 0 0;
    width: auto;
    justify-content: flex-end;
    padding: 18px;
  }
}
</style>
