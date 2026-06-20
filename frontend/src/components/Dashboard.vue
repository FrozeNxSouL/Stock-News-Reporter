<template>
  <div class="dashboard">

    <!-- ═══ HERO SECTION ═══ -->
    <div class="hero-section glass-card">
      <div class="hero-content">
        <div class="hero-left">
          <p class="hero-tagline">Good morning ☕</p>
          <h1 class="hero-title">Market<br><span class="hero-accent">Dashboard</span></h1>
          <p class="hero-sub">Real-time stock news &amp; sentiment analysis</p>
        </div>
        <div class="hero-word" aria-hidden="true">STOCKS</div>
      </div>

      <!-- Ticker bubbles row -->
      <div class="ticker-bubbles" v-if="store.tickers.length > 0">
        <button
          v-for="ticker in store.tickers.slice(0, 8)"
          :key="ticker.symbol"
          class="ticker-bubble"
          :class="{ active: selectedTickers.includes(ticker.symbol) }"
          @click="toggleTicker(ticker.symbol)"
          :id="`ticker-bubble-${ticker.symbol}`"
          :title="ticker.name || ticker.symbol"
        >
          <span class="bubble-symbol">{{ ticker.symbol }}</span>
        </button>
        <button
          v-if="store.tickers.length === 0"
          class="btn btn-primary"
          @click="addDefaults"
          id="btn-load-defaults"
        >📥 Load Tickers</button>
      </div>

      <!-- Hero actions -->
      <div class="hero-actions">
        <button v-if="store.tickers.length === 0" class="btn btn-primary" @click="addDefaults" id="btn-load-defaults-main">
          📥 Load Default Tickers
        </button>
        <button class="btn btn-secondary" @click="refreshAll" :disabled="loading" id="btn-refresh">
          {{ loading ? '⟳ Refreshing…' : '⟳ Refresh All' }}
        </button>
      </div>
    </div>

    <!-- ═══ LOADING STATE ═══ -->
    <div v-if="store.loading && store.tickers.length === 0" class="state-container">
      <div class="spinner"></div>
      <p class="state-text">Brewing market data…</p>
    </div>

    <!-- ═══ ERROR STATE ═══ -->
    <div v-if="store.error && store.tickers.length === 0" class="state-container">
      <span class="state-icon">⚠️</span>
      <p class="state-text">{{ store.error }}</p>
      <button class="btn btn-primary" @click="store.fetchTickers()" id="btn-retry">Retry</button>
    </div>

    <!-- ═══ STOCK PRICE CARDS ═══ -->
    <section v-if="selectedTickers.length > 0" class="cards-section" aria-label="Stock prices">
      <h2 class="section-title">Selected Tickers</h2>
      <div class="price-cards">
        <article
          v-for="ticker in selectedTickers"
          :key="ticker"
          class="price-card"
          :class="getPriceClass(ticker)"
          @click="$router.push(`/ticker/${ticker}`)"
          :id="`price-card-${ticker}`"
          role="button"
          tabindex="0"
          :aria-label="`${ticker} stock card`"
          @keyup.enter="$router.push(`/ticker/${ticker}`)"
        >
          <!-- Gradient background bubble -->
          <div class="card-bg-orb"></div>

          <div class="card-header">
            <span class="card-symbol">{{ ticker }}</span>
            <span v-if="getPrice(ticker)?.change_percent !== undefined" class="card-change" :class="getPriceClass(ticker)">
              {{ getPrice(ticker)?.change_percent > 0 ? '▲' : getPrice(ticker)?.change_percent < 0 ? '▼' : '─' }}
              {{ Math.abs(getPrice(ticker)?.change_percent || 0).toFixed(2) }}%
            </span>
          </div>

          <div class="card-price">
            ${{ getPrice(ticker)?.current_price?.toFixed(2) || '—' }}
          </div>

          <div class="card-stats">
            <div class="card-stat">
              <span class="stat-lbl">H</span>
              <span class="stat-val">${{ getPrice(ticker)?.day_high?.toFixed(2) || '—' }}</span>
            </div>
            <div class="card-stat">
              <span class="stat-lbl">L</span>
              <span class="stat-val">${{ getPrice(ticker)?.day_low?.toFixed(2) || '—' }}</span>
            </div>
            <div class="card-stat">
              <span class="stat-lbl">Vol</span>
              <span class="stat-val">{{ formatVolume(getPrice(ticker)?.volume) }}</span>
            </div>
          </div>

          <!-- Mini sparkline -->
          <div class="card-sparkline" v-if="getPrice(ticker)?.historical?.length">
            <svg viewBox="0 0 100 36" preserveAspectRatio="none" class="sparkline-svg">
              <defs>
                <linearGradient :id="`spark-grad-${ticker}`" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" :stop-color="getPriceColor(getPrice(ticker))" stop-opacity="0.35"/>
                  <stop offset="100%" :stop-color="getPriceColor(getPrice(ticker))" stop-opacity="0"/>
                </linearGradient>
              </defs>
              <path
                :d="sparklinePath(getPrice(ticker))"
                :fill="`url(#spark-grad-${ticker})`"
                :stroke="getPriceColor(getPrice(ticker))"
                stroke-width="1.5"
              />
            </svg>
          </div>
        </article>
      </div>
    </section>

    <!-- ═══ EMPTY TICKER STATE ═══ -->
    <div v-if="store.tickers.length > 0 && selectedTickers.length === 0" class="state-container">
      <span class="state-icon">👆</span>
      <p class="state-text">Select tickers above to view their stock data</p>
      <p style="font-size:13px; color: var(--text-muted);">Click on any ticker bubble to add it to your watchlist</p>
    </div>

    <!-- ═══ RECENT NEWS ═══ -->
    <section v-if="recentNews.length > 0" class="news-section" aria-label="Recent news">
      <div class="section-header-row">
        <h2 class="section-title">📰 Recent News</h2>
        <router-link to="/news" class="view-all-link" id="link-view-all-news">View All →</router-link>
      </div>
      <div class="news-grid">
        <article
          v-for="article in recentNews"
          :key="article.id"
          class="news-card glass-card"
          @click="$router.push(`/ticker/${getRelevantTicker(article)}`)"
          role="button"
          tabindex="0"
          :id="`news-card-${article.id}`"
          @keyup.enter="$router.push(`/ticker/${getRelevantTicker(article)}`)"
        >
          <div class="nc-header">
            <div class="nc-source-row">
              <div class="source-avatar">{{ (article.source || '?')[0].toUpperCase() }}</div>
              <div class="nc-meta">
                <span class="nc-source">{{ article.source || 'Unknown' }}</span>
                <span class="nc-time">{{ timeAgo(article.published) }}</span>
              </div>
            </div>
            <div class="nc-tickers">
              <span
                v-for="t in article.tickers?.slice(0, 3)"
                :key="t"
                class="badge badge-ticker"
              >{{ t }}</span>
            </div>
          </div>
          <h3 class="nc-title">{{ article.title }}</h3>
          <p class="nc-summary">{{ truncate(article.summary, 110) }}</p>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useStockStore } from '../store/index.js'
import { useAuthStore } from '../store/auth.js'

const store = useStockStore()
const authStore = useAuthStore()
const selectedTickers = ref([])
const loading = ref(false)

onMounted(async () => {
  await store.fetchTickers()
  if (store.selectedTickers.length > 0) {
    selectedTickers.value = [...store.selectedTickers]
    await refreshPrices()
  } else if (store.tickers.length > 0) {
    selectedTickers.value = store.tickers.slice(0, 6).map(t => t.symbol)
    await refreshPrices()
  }
  await store.fetchNews({ page_size: 8 })
  store.startAutoRefresh(60000)
})

onUnmounted(() => {
  store.stopAutoRefresh()
})

watch(selectedTickers, (newVal) => {
  if (authStore.isAuthenticated) {
    authStore.updateProfile({ watchlist: [...newVal] }).catch(() => {})
  }
}, { deep: true })

async function addDefaults() {
  await store.addDefaultTickers()
  if (store.tickers.length > 0) {
    selectedTickers.value = store.tickers.slice(0, 6).map(t => t.symbol)
    await refreshPrices()
  }
}

async function refreshAll() {
  loading.value = true
  await Promise.all([
    store.fetchTickers(),
    refreshPrices(),
    store.fetchNews({ page_size: 8 }),
  ])
  loading.value = false
}

async function refreshPrices() {
  if (selectedTickers.value.length > 0) {
    await store.fetchMultiplePrices(selectedTickers.value)
  }
}

function toggleTicker(symbol) {
  const idx = selectedTickers.value.indexOf(symbol)
  if (idx >= 0) {
    selectedTickers.value.splice(idx, 1)
  } else {
    selectedTickers.value.push(symbol)
    store.fetchStockPrice(symbol)
  }
}

function getPrice(ticker) {
  return store.stockPrices[ticker]
}

function getPriceClass(ticker) {
  const price = getPrice(ticker)
  if (!price) return ''
  if (price.change_percent > 0) return 'price-up'
  if (price.change_percent < 0) return 'price-down'
  return 'price-neutral'
}

function getPriceColor(price) {
  if (!price) return 'var(--brand-sage)'
  return price.change_percent >= 0 ? 'var(--up-color)' : 'var(--down-color)'
}

function sparklinePath(price) {
  if (!price?.historical?.length) return ''
  const closes = price.historical.map(p => p.close)
  const min = Math.min(...closes)
  const max = Math.max(...closes)
  const range = (max - min) || 1
  const w = 100
  const h = 34
  const pts = closes.map((c, i) => {
    const x = (i / (closes.length - 1)) * w
    const y = h - ((c - min) / range) * (h - 4) - 2
    return `${x},${y}`
  })
  // Build area path
  const linePoints = pts.join(' L ')
  const firstX = 0
  const lastX = w
  return `M ${pts[0]} L ${linePoints} L ${lastX},${h} L ${firstX},${h} Z`
}

function formatVolume(vol) {
  if (!vol) return '—'
  if (vol >= 1e9) return (vol / 1e9).toFixed(1) + 'B'
  if (vol >= 1e6) return (vol / 1e6).toFixed(1) + 'M'
  if (vol >= 1e3) return (vol / 1e3).toFixed(1) + 'K'
  return vol.toString()
}

const recentNews = computed(() => store.news.slice(0, 6))

function getRelevantTicker(article) {
  for (const t of selectedTickers.value) {
    if (article.tickers?.includes(t)) return t
  }
  return article.tickers?.[0] || 'AAPL'
}

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

function truncate(text, maxLen) {
  if (!text || text.length <= maxLen) return text || ''
  return text.substring(0, maxLen) + '…'
}
</script>
