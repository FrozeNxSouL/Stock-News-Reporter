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
            <option v-for="t in store.tickers" :key="t.symbol" :value="t.symbol">{{ t.symbol }}</option>
          </select>
          <button class="btn btn-primary" @click="fetchNewNews" :disabled="fetching" id="btn-fetch-latest">
            {{ fetching ? '⟳ Fetching…' : '⟳ Fetch Latest' }}
          </button>
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
      <button class="btn btn-primary" @click="fetchNewNews" id="btn-fetch-empty">Fetch News Now</button>
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
import { ref, onMounted } from 'vue'
import { useStockStore } from '../store/index.js'

const store = useStockStore()

const items = ref([])
const loading = ref(false)
const fetching = ref(false)
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

async function fetchNewNews() {
  fetching.value = true
  try {
    const result = await store.triggerFetch()
    if (result) await loadNews()
  } catch {
    error.value = 'Failed to fetch news'
  } finally {
    fetching.value = false
  }
}

function changePage(page) {
  currentPage.value = page
  loadNews()
}

onMounted(async () => {
  await store.fetchTickers()
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

<style scoped>
.news-feed {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 860px;
  margin: 0 auto;
  width: 100%;
}

/* ---- Feed header ---- */
.feed-header {
  padding: 20px 24px 0;
  overflow: hidden;
}

.feed-header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.feed-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.feed-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
}

.feed-ticker-icon {
  width: 32px;
  height: 32px;
  font-size: 14px;
}

.feed-count {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 400;
}

.feed-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.feed-select {
  width: auto;
  padding: 7px 12px;
  font-size: 13px;
  min-width: 140px;
}

/* ---- Tab bar (Picture 2) ---- */
.tab-bar {
  display: flex;
  gap: 0;
  border-top: 1px solid var(--border);
  margin: 0 -24px;
  padding: 0 24px;
}

.tab-btn {
  padding: 12px 20px;
  border: none;
  background: none;
  font-family: 'Outfit', sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: var(--trans-fast);
  white-space: nowrap;
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  color: var(--brand-caramel);
  border-bottom-color: var(--brand-caramel);
  font-weight: 700;
}

/* ---- News list card ---- */
.news-list {
  padding: 0;
  overflow: hidden;
}

/* ---- News item (Picture 2 style) ---- */
.news-item {
  padding: 0;
}

.ni-row {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 18px 22px;
  transition: background 0.15s;
}

.ni-row:hover {
  background: var(--nav-active-bg);
}

.ni-avatar {
  flex-shrink: 0;
  margin-top: 2px;
  width: 38px;
  height: 38px;
  font-size: 15px;
}

.ni-body {
  flex: 1;
  min-width: 0;
}

.ni-meta {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 5px;
  flex-wrap: wrap;
}

.ni-time {
  font-size: 12px;
  color: var(--text-muted);
}

.ni-dot {
  color: var(--text-muted);
  font-size: 12px;
}

.ni-source {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.ni-type-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: var(--r-pill);
  margin-left: 2px;
}

.ni-type-badge.rss {
  background: rgba(160, 98, 42, 0.14);
  color: var(--brand-caramel);
}

.ni-type-badge.scrape {
  background: rgba(107, 63, 200, 0.12);
  color: #8B5CF6;
}

.ni-title-link {
  text-decoration: none;
  color: inherit;
}

.ni-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.45;
  margin-bottom: 8px;
  transition: color 0.18s;
}

.ni-title-link:hover .ni-title {
  color: var(--brand-caramel);
}

.ni-tickers {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

/* ---- Pagination ---- */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}

.page-btn {
  min-width: 90px;
}

.page-info {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
}

/* ---- Responsive ---- */
@media (max-width: 600px) {
  .news-feed {
    gap: 12px;
  }

  .feed-header {
    padding: 16px 16px 0;
  }

  .tab-bar {
    margin: 0 -16px;
    padding: 0 16px;
  }

  .tab-btn {
    padding: 10px 14px;
    font-size: 13px;
  }

  .ni-row {
    padding: 14px 16px;
  }

  .feed-header-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .feed-actions {
    width: 100%;
  }

  .feed-select {
    flex: 1;
  }
}
</style>
