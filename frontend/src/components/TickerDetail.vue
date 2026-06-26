<template>
  <div class="ticker-detail">

    <!-- ═══ TOP BAR: Back + Status ═══ -->
    <div class="ticker-top-bar">
      <button class="back-btn" @click="$router.push('/')" id="btn-back" title="Back to Dashboard">
        ←
      </button>
      <span v-if="isInWatchlist" class="added-badge">ADDED</span>
    </div>

    <!-- ═══ LOADING ═══ -->
    <div v-if="loading" class="state-container">
      <div class="spinner"></div>
      <p class="state-text">Loading {{ tickerSymbol }}…</p>
    </div>

    <!-- ═══ ERROR ═══ -->
    <div v-else-if="error" class="state-container">
      <span class="state-icon">⚠️</span>
      <p class="state-text">{{ error }}</p>
      <button class="btn btn-primary" @click="loadData" id="btn-retry">Retry</button>
    </div>

    <!-- ═══ MAIN CONTENT ═══ -->
    <template v-else>

      <!-- Hero Card -->
      <div class="ticker-hero glass-card">
        <div class="hero-bg-orb hero-bg-orb-1"></div>
        <div class="hero-bg-orb hero-bg-orb-2"></div>

        <!-- Tab bar — pill style -->
        <div class="ticker-tabs" role="tablist">
          <button
            class="ticker-tab"
            :class="{ active: activeTab === 'overview' }"
            @click="activeTab = 'overview'"
            role="tab"
            id="tab-overview"
          >Overview</button>
          <button
            class="ticker-tab"
            :class="{ active: activeTab === 'statistics' }"
            @click="activeTab = 'statistics'"
            role="tab"
            id="tab-statistics"
          >Statistics</button>
          <button
            class="ticker-tab"
            :class="{ active: activeTab === 'history' }"
            @click="activeTab = 'history'"
            role="tab"
            id="tab-history"
          >History</button>
        </div>

        <!-- Inline chart in hero -->
        <div class="hero-chart" v-if="price?.historical?.length">
          <svg viewBox="0 0 800 140" preserveAspectRatio="none" class="hero-chart-svg">
            <defs>
              <linearGradient :id="`hero-chart-grad-${tickerSymbol}`" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" :stop-color="chartColor" stop-opacity="0.25" />
                <stop offset="100%" :stop-color="chartColor" stop-opacity="0.02" />
              </linearGradient>
            </defs>
            <path
              :d="heroChartArea"
              :fill="`url(#hero-chart-grad-${tickerSymbol})`"
            />
            <path
              :d="heroChartLine"
              fill="none"
              :stroke="chartColor"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>

        <!-- Ticker name + price display (centered) -->
        <div class="hero-main">
          <h1 class="hero-ticker">{{ tickerSymbol }}</h1>
          <div class="hero-price-display">
            <span class="hero-price" v-if="price">${{ price.current_price?.toFixed(2) }}</span>
            <span class="hero-price" v-else>—</span>
            <div class="hero-change-row" v-if="price">
              <span
                class="hero-change badge"
                :class="price.change_percent >= 0 ? 'badge-up' : 'badge-down'"
              >
                {{ price.change_percent >= 0 ? '+' : '' }}${{ Math.abs(price.change || 0).toFixed(2) }}
                ({{ price.change_percent >= 0 ? '+' : '' }}{{ (price.change_percent || 0).toFixed(2) }}%)
              </span>
            </div>
            <p class="hero-sub">TODAY</p>
          </div>
        </div>

        <!-- Price stats row -->
        <div class="hero-stats" v-if="price">
          <div class="hero-stat">
            <span class="hstat-label">Day High</span>
            <span class="hstat-value">${{ price.day_high?.toFixed(2) }}</span>
          </div>
          <div class="hstat-sep"></div>
          <div class="hero-stat">
            <span class="hstat-label">Day Low</span>
            <span class="hstat-value">${{ price.day_low?.toFixed(2) }}</span>
          </div>
          <div class="hstat-sep"></div>
          <div class="hero-stat">
            <span class="hstat-label">Volume</span>
            <span class="hstat-value">{{ formatVolume(price.volume) }}</span>
          </div>
        </div>

        <!-- Action buttons — dual pill style -->
        <div class="hero-actions">
          <button class="btn btn-primary hero-btn" id="btn-goto-news" @click="$router.push('/news')">
            📰 All News
          </button>
          <button class="hero-btn-outline" id="btn-goto-watchlist" @click="$router.push('/watchlist')">
            📊 Watchlist
          </button>
        </div>
      </div>

      <!-- ═══ TAB PANELS ═══ -->

      <!-- Overview -->
      <template v-if="activeTab === 'overview'">

        <!-- Chart (existing) -->
        <section v-if="price?.historical?.length" class="detail-section glass-card" aria-label="Price chart">
          <h2 class="detail-section-title">Price History (1 Month)</h2>
          <div class="chart-container">
            <apexchart
              type="area"
              :options="chartOptions"
              :series="chartSeries"
              height="320"
            />
          </div>
        </section>

        <!-- Sentiment -->
        <section v-if="sentiment" class="detail-section glass-card" aria-label="Sentiment analysis">
          <h2 class="detail-section-title">📊 Sentiment Analysis</h2>
          <div class="sentiment-grid">
            <div class="sentiment-card">
              <span class="sc-label">Overall Direction</span>
              <span class="sc-value" :class="sentiment.dominant_direction">
                {{ sentiment.dominant_direction === 'up' ? '🟢 Bullish' : sentiment.dominant_direction === 'down' ? '🔴 Bearish' : '⚪ Neutral' }}
              </span>
            </div>
            <div class="sentiment-card">
              <span class="sc-label">Avg Polarity</span>
              <span class="sc-value" :style="{ color: sentiment.avg_polarity > 0 ? 'var(--up-color)' : sentiment.avg_polarity < 0 ? 'var(--down-color)' : 'var(--neutral-color)' }">
                {{ sentiment.avg_polarity.toFixed(3) }}
              </span>
            </div>
            <div class="sentiment-card">
              <span class="sc-label">Confidence</span>
              <span class="sc-value">{{ (sentiment.avg_confidence * 100).toFixed(0) }}%</span>
            </div>
            <div class="sentiment-card">
              <span class="sc-label">Trend</span>
              <span class="sc-value" :class="sentiment.recent_trend">
                {{ sentiment.recent_trend === 'improving' ? '📈 Improving' : sentiment.recent_trend === 'deteriorating' ? '📉 Deteriorating' : '➡️ Stable' }}
              </span>
            </div>
          </div>

          <!-- Distribution bars -->
          <div v-if="sentiment.sentiment_distribution" class="distribution">
            <h3 class="dist-title">Sentiment Distribution</h3>
            <div class="dist-bars">
              <div class="dist-bar positive" :style="{ flex: sentiment.sentiment_distribution.positive || 0.01 }">
                <span>+{{ sentiment.sentiment_distribution.positive }}</span>
              </div>
              <div class="dist-bar neutral" :style="{ flex: sentiment.sentiment_distribution.neutral || 0.01 }">
                <span>{{ sentiment.sentiment_distribution.neutral }}</span>
              </div>
              <div class="dist-bar negative" :style="{ flex: sentiment.sentiment_distribution.negative || 0.01 }">
                <span>-{{ sentiment.sentiment_distribution.negative }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Related News — Article detail style -->
        <section v-if="overview?.recent_news?.length" class="detail-section" aria-label="Related news">
          <div class="section-header-row">
            <h2 class="detail-section-title" style="margin-bottom:0">📰 Related News</h2>
            <span class="article-count">{{ overview.recent_news.length }} articles</span>
          </div>

          <div class="news-article-list">
            <article
              v-for="article in overview.recent_news"
              :key="article.id"
              class="news-article glass-card"
              :id="`article-${article.id}`"
            >
              <!-- Article header -->
              <div class="article-top">
                <div class="article-meta-row">
                  <span class="article-date">{{ formatDate(article.published) }}</span>
                  <div class="article-meta-actions">
                    <button class="meta-action-btn" title="Comment" aria-label="Comment">💬</button>
                    <button class="meta-action-btn" title="Share" aria-label="Share">🔗</button>
                  </div>
                </div>

                <!-- Ticker badge -->
                <div class="article-ticker-row" v-if="article.tickers?.length">
                  <span
                    v-for="t in article.tickers.slice(0, 3)"
                    :key="t"
                    class="badge badge-ticker article-ticker"
                  >
                    <span class="ticker-dot">●</span> {{ t }}
                    <span v-if="article.analysis" class="ticker-pct"
                      :class="article.analysis.impact?.direction === 'up' ? 'up' : article.analysis.impact?.direction === 'down' ? 'down' : ''"
                    >
                      {{ article.analysis.impact?.direction === 'up' ? '+' : '' }}{{ article.analysis.impact?.price_range_high || '' }}%
                    </span>
                  </span>
                </div>

                <!-- Article title -->
                <a :href="article.url" target="_blank" rel="noopener" class="article-title-link" :id="`art-link-${article.id}`">
                  <h3 class="article-title">{{ article.title }}</h3>
                </a>
              </div>

              <!-- Article body -->
              <div class="article-body">
                <p class="article-summary">{{ truncate(article.summary, 400) }}</p>

                <!-- Analysis badges -->
                <div v-if="article.analysis" class="analysis-badges">
                  <span class="badge" :class="`badge-${article.analysis.sentiment?.label === 'positive' ? 'up' : article.analysis.sentiment?.label === 'negative' ? 'down' : 'neutral'}`">
                    {{ article.analysis.sentiment?.label === 'positive' ? '🟢' : article.analysis.sentiment?.label === 'negative' ? '🔴' : '⚪' }}
                    {{ article.analysis.sentiment?.label }}
                  </span>
                  <span class="badge badge-neutral">💥 {{ article.analysis.impact?.strength }} impact</span>
                  <span class="badge badge-neutral">⏱ {{ article.analysis.impact?.effect_duration }}</span>
                </div>

                <!-- Keywords -->
                <div v-if="article.analysis?.keywords?.length" class="keywords">
                  <span v-for="kw in article.analysis.keywords.slice(0, 5)" :key="kw" class="keyword-tag">{{ kw }}</span>
                </div>

                <div class="article-footer">
                  <div class="article-source-row">
                    <div class="source-avatar article-source-avatar">{{ (article.source || '?')[0].toUpperCase() }}</div>
                    <span class="article-source-name">{{ article.source }}</span>
                  </div>
                  <a :href="article.url" target="_blank" rel="noopener" class="read-more-btn btn btn-secondary">
                    Read full article →
                  </a>
                </div>
              </div>
            </article>
          </div>
        </section>

        <!-- No news -->
        <div v-else class="state-container glass-card" style="padding: 40px 24px;">
          <span class="state-icon">📭</span>
          <p class="state-text">No recent news found for {{ tickerSymbol }}</p>
        </div>
      </template>

      <!-- Statistics tab -->
      <div v-if="activeTab === 'statistics'" class="detail-section glass-card">
        <h2 class="detail-section-title">📋 Statistics</h2>
        <div class="stats-table" v-if="price">
          <div class="stats-row">
            <span class="stats-label">Current Price</span>
            <span class="stats-val">${{ price.current_price?.toFixed(2) }}</span>
          </div>
          <div class="stats-row">
            <span class="stats-label">Day Change</span>
            <span class="stats-val" :class="price.change_percent >= 0 ? 'up' : 'down'">
              {{ price.change_percent >= 0 ? '+' : '' }}{{ price.change_percent?.toFixed(2) }}%
            </span>
          </div>
          <div class="stats-row">
            <span class="stats-label">Day High</span>
            <span class="stats-val">${{ price.day_high?.toFixed(2) }}</span>
          </div>
          <div class="stats-row">
            <span class="stats-label">Day Low</span>
            <span class="stats-val">${{ price.day_low?.toFixed(2) }}</span>
          </div>
          <div class="stats-row">
            <span class="stats-label">Volume</span>
            <span class="stats-val">{{ formatVolume(price.volume) }}</span>
          </div>
        </div>
        <div v-else class="state-container">
          <p class="state-text">No price data available</p>
        </div>
      </div>

      <!-- History tab -->
      <div v-if="activeTab === 'history'" class="detail-section glass-card">
        <h2 class="detail-section-title">Price History</h2>
        <div class="chart-container" v-if="price?.historical?.length">
          <apexchart
            type="area"
            :options="chartOptions"
            :series="chartSeries"
            height="400"
          />
        </div>
        <div v-else class="state-container">
          <p class="state-text">No historical data available</p>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useStockStore } from '../store/index.js'
import { useAuthStore } from '../store/auth.js'

const props = defineProps({ symbol: String })
const route = useRoute()
const store = useStockStore()
const authStore = useAuthStore()

const tickerSymbol = computed(() => props.symbol || route.params.symbol)
const loading = ref(true)
const error = ref(null)
const activeTab = ref('overview')

const price = ref(null)
const overview = ref(null)
const sentiment = ref(null)

// Check if ticker is in watchlist
const isInWatchlist = computed(() => {
  return authStore.isAuthenticated && authStore.watchlist.includes(tickerSymbol.value)
})

// Detect dark mode for chart
const isDark = computed(() => document.documentElement.classList.contains('dark'))

// Chart color: bullish green if last close > first close, else bearish red
const chartColor = computed(() => {
  const hist = price.value?.historical
  if (!hist || hist.length < 2) return '#5ee085'
  return hist[hist.length - 1].close >= hist[0].close
    ? '#5ee085'
    : '#ff6b6b'
})

// ─── Inline hero chart SVG paths ───
const heroChartLine = computed(() => buildHeroChartPath(false))
const heroChartArea = computed(() => buildHeroChartPath(true))

function buildHeroChartPath(area) {
  const hist = price.value?.historical
  if (!hist || hist.length < 2) return ''
  const closes = hist.map(p => p.close)
  const min = Math.min(...closes)
  const max = Math.max(...closes)
  const range = (max - min) || 1
  const w = 800
  const h = 140
  const padX = 10
  const padY = 12
  const pts = closes.map((c, i) => {
    const x = padX + (i / (closes.length - 1)) * (w - 2 * padX)
    const y = h - padY - ((c - min) / range) * (h - 2 * padY)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  let d = `M ${pts[0]}`
  for (let i = 1; i < pts.length; i++) {
    d += ` L ${pts[i]}`
  }

  if (area) {
    const lastX = pts[pts.length - 1].split(',')[0]
    d += ` L ${lastX},${h} L ${pts[0].split(',')[0]},${h} Z`
  }

  return d
}

async function loadData() {
  loading.value = true
  error.value = null
  const symbol = tickerSymbol.value
  try {
    const [priceData, overviewData, sentimentData] = await Promise.all([
      store.fetchStockPrice(symbol),
      store.fetchOverview(symbol, 14),
      store.fetchSentiment(symbol, 14),
    ])
    price.value = priceData
    overview.value = overviewData
    sentiment.value = sentimentData
  } catch (err) {
    error.value = err.message || 'Failed to load data'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

const chartOptions = computed(() => ({
  chart: {
    type: 'line',
    height: 320,
    background: 'transparent',
    toolbar: { show: false },
    fontFamily: 'Outfit, sans-serif',
    zoom: { enabled: false },
  },
  theme: {
    mode: isDark.value ? 'dark' : 'light',
  },
  stroke: {
    curve: 'smooth',
    width: 2.5,
    colors: [chartColor.value],
  },
  colors: [chartColor.value],
  dataLabels: { enabled: false },
  markers: {
    size: 0,
    strokeColors: chartColor.value,
    strokeWidth: 2,
    hover: { size: 5 },
  },
  xaxis: {
    type: 'datetime',
    labels: { style: { colors: 'var(--text-muted)', fontFamily: 'DM Mono, monospace', fontSize: '11px' } },
    axisBorder: { color: 'var(--border)' },
    axisTicks: { color: 'var(--border)' },
  },
  yaxis: {
    labels: {
      style: { colors: 'var(--text-muted)', fontFamily: 'DM Mono, monospace', fontSize: '11px' },
      formatter: (val) => `$${val.toFixed(2)}`,
    },
  },
  grid: {
    borderColor: 'var(--border)',
    strokeDashArray: 3,
    padding: { top: 10, bottom: 0 },
  },
  tooltip: {
    theme: isDark.value ? 'dark' : 'light',
    style: { fontFamily: 'Outfit, sans-serif' },
    x: { format: 'dd MMM yyyy' },
    y: {
      formatter: (val) => `$${val.toFixed(2)}`,
    },
  },
}))

const chartSeries = computed(() => {
  if (!price.value?.historical?.length) return []
  return [{
    name: price.value.ticker,
    data: price.value.historical.map(p => ({
      x: new Date(p.timestamp).getTime(),
      y: p.close,
    }))
  }]
})

function formatVolume(vol) {
  if (!vol) return '—'
  if (vol >= 1e9) return (vol / 1e9).toFixed(1) + 'B'
  if (vol >= 1e6) return (vol / 1e6).toFixed(1) + 'M'
  if (vol >= 1e3) return (vol / 1e3).toFixed(1) + 'K'
  return vol.toString()
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('th-TH', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
    timeZoneName: 'short',
  })
}

function truncate(text, maxLen) {
  if (!text || text.length <= maxLen) return text || ''
  return text.substring(0, maxLen) + '…'
}
</script>
