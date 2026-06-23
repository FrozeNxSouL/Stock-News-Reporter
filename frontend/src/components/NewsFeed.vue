<template>
  <div class="news-feed">

    <!-- ═══ HEADER ═══ -->
    <div class="feed-header glass-card">
      <div class="feed-header-top">
        <div class="feed-title-row">
          <h1 class="feed-title">
            <span v-if="filterTicker" class="feed-ticker-icon source-avatar">{{ filterTicker[0] }}</span>
            <span>{{ filterTicker ? filterTicker + ' ข่าวทั้งหมด' : 'News Feed' }}</span>
          </h1>
          <span class="feed-count" v-if="totalItems">({{ totalItems }} บทความ)</span>
        </div>
        <div class="feed-actions">
          <select v-model="filterTicker" class="form-input feed-select" @change="loadNews" id="filter-ticker-select" aria-label="Filter by ticker">
            <option value="">All Tickers</option>
            <option v-for="t in authStore.watchlist" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>
      </div>

      <!-- Tab bar (Picture 2 style) -->
      <div class="tab-bar" role="tablist" aria-label="News categories">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'news' }"
          @click="activeTab = 'news'"
          role="tab"
          :aria-selected="activeTab === 'news'"
          id="tab-news"
        >ข่าว</button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'rss' }"
          @click="activeTab = 'rss'; filterSource = 'rss'; loadNews()"
          role="tab"
          :aria-selected="activeTab === 'rss'"
          id="tab-rss"
        >📡 RSS</button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'scraped' }"
          @click="activeTab = 'scraped'; filterSource = 'scrape'; loadNews()"
          role="tab"
          :aria-selected="activeTab === 'scraped'"
          id="tab-scraped"
        >🕸 Scraped</button>
      </div>
    </div>

    <!-- ═══ LOADING ═══ -->
    <div v-if="loading" class="state-container">
      <div class="spinner"></div>
      <p class="state-text">กำลังโหลดข่าว…</p>
    </div>

    <!-- ═══ ERROR ═══ -->
    <div v-else-if="error" class="state-container">
      <span class="state-icon">⚠️</span>
      <p class="state-text">{{ error }}</p>
      <button class="btn btn-primary" @click="loadNews" id="btn-retry">Retry</button>
    </div>

    <!-- ═══ NEWS ITEMS ═══ (Picture 2 style — flat list) ═══ -->
    <div v-else-if="items.length > 0" class="news-list glass-card" role="list">
      <article
        v-for="(item, idx) in items"
        :key="item.id"
        class="news-item"
        role="listitem"
        :id="`news-item-${item.id}`"
      >
        <div class="ni-row">
          <!-- Source avatar -->
          <div class="ni-avatar source-avatar" :style="avatarStyle(item.source)">
            {{ (item.source || '?')[0].toUpperCase() }}
          </div>

          <!-- Content -->
          <div class="ni-body">
            <div class="ni-meta">
              <span class="ni-time">{{ timeAgo(item.published) }}</span>
              <span class="ni-dot">·</span>
              <span class="ni-source">{{ item.source }}</span>
              <span v-if="item.source_type" class="ni-type-badge" :class="item.source_type">
                {{ item.source_type === 'rss' ? 'RSS' : 'Scrape' }}
              </span>
            </div>

            <a :href="item.url" target="_blank" rel="noopener" class="ni-title-link" :id="`link-${item.id}`">
              <h2 class="ni-title">{{ item.title }}</h2>
            </a>

            <!-- Ticker tags -->
            <div v-if="item.tickers?.length" class="ni-tickers">
              <span
                v-for="t in item.tickers.slice(0, 4)"
                :key="t"
                class="badge badge-ticker"
                @click.stop="filterTicker = t; loadNews()"
              >{{ t }}</span>
            </div>
          </div>
        </div>

        <!-- Divider (not after last) -->
        <div v-if="idx < items.length - 1" class="section-divider"></div>
      </article>
    </div>

    <!-- ═══ EMPTY ═══ -->
    <div v-else class="state-container">
      <span class="state-icon">📭</span>
      <p class="state-text">ไม่พบบทความข่าว</p>

    </div>

    <!-- ═══ PAGINATION ═══ -->
    <div v-if="totalPages > 1" class="pagination" role="navigation" aria-label="News pagination">
      <button
        class="btn btn-secondary page-btn"
        :disabled="currentPage <= 1"
        @click="changePage(currentPage - 1)"
        id="btn-prev-page"
        aria-label="Previous page"
      >← Prev</button>
      <span class="page-info">หน้า {{ currentPage }} จาก {{ totalPages }}</span>
      <button
        class="btn btn-secondary page-btn"
        :disabled="currentPage >= totalPages"
        @click="changePage(currentPage + 1)"
        id="btn-next-page"
        aria-label="Next page"
      >Next →</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStockStore } from '../store/index.js'
import { useAuthStore } from '../store/auth.js'

const store = useStockStore()
const authStore = useAuthStore()

const items = ref([])
const loading = ref(false)
const error = ref(null)
const currentPage = ref(1)
const totalItems = ref(0)
const totalPages = ref(1)
const pageSize = 20

const filterTicker = ref('')
const filterSource = ref('')
const activeTab = ref('news')

// Deterministic avatar colors based on source initial
const AVATAR_COLORS = [
  ['#A0622A', '#6B3F1F'],
  ['#2D7A3A', '#1A5225'],
  ['#1A5FA8', '#0A2947'],
  ['#7B4A9B', '#4A2D6B'],
  ['#B35A00', '#7A3E00'],
  ['#1E7A7A', '#0E4A4A'],
]

function avatarStyle(source) {
  const idx = ((source || '?').charCodeAt(0)) % AVATAR_COLORS.length
  const [from, to] = AVATAR_COLORS[idx]
  return { background: `linear-gradient(135deg, ${from}, ${to})` }
}

async function loadNews() {
  loading.value = true
  error.value = null
  const params = { page: currentPage.value, page_size: pageSize }
  if (filterTicker.value) params.ticker = filterTicker.value
  if (filterSource.value) params.source_type = filterSource.value
  try {
    const result = await store.fetchNews(params)
    if (result) {
      items.value = result.items || []
      totalItems.value = result.total || 0
      totalPages.value = Math.ceil(totalItems.value / pageSize) || 1
    }
  } catch (err) {
    error.value = 'Failed to load news'
  } finally {
    loading.value = false
  }
}

function changePage(page) {
  currentPage.value = page
  loadNews()
}

onMounted(async () => {
  loadNews()
})

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'เมื่อกี้'
  if (diffMins < 60) return `${diffMins} นาทีที่ผ่านมา`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours} ชั่วโมงที่ผ่านมา`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays} วันที่ผ่านมา`
  return date.toLocaleDateString('th-TH')
}
</script>
