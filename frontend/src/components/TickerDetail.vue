<template>
  <div class="ticker-detail">

    <!-- ═══ BACK BUTTON ═══ -->
    <button class="back-btn" @click="$router.push('/')" id="btn-back">
      ← Back to Dashboard
    </button>

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

      <!-- Hero Header (Picture 2 middle style) -->
      <div class="ticker-hero glass-card">
        <div class="hero-bg-orb hero-bg-orb-1"></div>
        <div class="hero-bg-orb hero-bg-orb-2"></div>

        <!-- Tab bar -->
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

        <!-- Ticker name + price -->
        <div class="hero-main">
          <h1 class="hero-ticker">{{ tickerSymbol }}</h1>
          <div class="hero-price-row">
            <span class="hero-price" v-if="price">${{ price.current_price?.toFixed(2) }}</span>
            <span class="hero-price" v-else>—</span>
            <span
              v-if="price"
              class="hero-change badge"
              :class="price.change_percent >= 0 ? 'badge-up' : 'badge-down'"
            >
              {{ price.change_percent >= 0 ? '▲' : '▼' }}
              ${{ Math.abs(price.change || 0).toFixed(2) }}
              ({{ price.change_percent >= 0 ? '+' : '' }}{{ (price.change_percent || 0).toFixed(2) }}%)
            </span>
          </div>
          <p class="hero-sub">TODAY</p>
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

        <!-- Action buttons (SELL / BUY style) -->
        <div class="hero-actions">
          <button class="btn btn-secondary hero-btn" id="btn-fetch-news" @click="triggerFetch">
            ⟳ Refresh
          </button>
          <button class="btn btn-primary hero-btn" id="btn-goto-news" @click="$router.push('/news')">
            📰 All News
          </button>
        </div>
      </div>

      <!-- ═══ TAB PANELS ═══ -->

      <!-- Overview -->
      <template v-if="activeTab === 'overview'">

        <!-- Chart -->
        <section v-if="price?.historical?.length" class="detail-section glass-card" aria-label="Price chart">
          <h2 class="detail-section-title">📈 Price History (1 Month)</h2>
          <div class="chart-container">
            <apexchart
              type="candlestick"
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

        <!-- Related News — Article detail style (Picture 3) -->
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
              <!-- Article header (Picture 3 style) -->
              <div class="article-top">
                <div class="article-meta-row">
                  <span class="article-date">{{ formatDate(article.published) }}</span>
                  <div class="article-meta-actions">
                    <button class="meta-action-btn" title="Comment" aria-label="Comment">💬</button>
                    <button class="meta-action-btn" title="Share" aria-label="Share">🔗</button>
                  </div>
                </div>

                <!-- Ticker badge (Picture 3 style) -->
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

                <!-- Article title (Picture 3 — large bold) -->
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
          <button class="btn btn-secondary" @click="triggerFetch" id="btn-trigger-fetch">Fetch News Now</button>
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
        <h2 class="detail-section-title">🕐 Price History</h2>
        <div class="chart-container" v-if="price?.historical?.length">
          <apexchart
            type="candlestick"
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

const props = defineProps({ symbol: String })
const route = useRoute()
const store = useStockStore()

const tickerSymbol = computed(() => props.symbol || route.params.symbol)
const loading = ref(true)
const error = ref(null)
const activeTab = ref('overview')

const price = ref(null)
const overview = ref(null)
const sentiment = ref(null)

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

async function triggerFetch() {
  loading.value = true
  try {
    await store.triggerFetch()
    await loadData()
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

// Detect dark mode for chart
const isDark = computed(() => document.documentElement.classList.contains('dark'))

const chartOptions = computed(() => ({
  chart: {
    type: 'candlestick',
    height: 320,
    background: 'transparent',
    toolbar: { show: false },
    fontFamily: 'Outfit, sans-serif',
  },
  theme: {
    mode: isDark.value ? 'dark' : 'light',
  },
  xaxis: {
    type: 'datetime',
    labels: { style: { colors: 'var(--text-muted)', fontFamily: 'DM Mono, monospace', fontSize: '11px' } },
    axisBorder: { color: 'var(--border)' },
    axisTicks: { color: 'var(--border)' },
  },
  yaxis: {
    tooltip: { enabled: true },
    labels: {
      style: { colors: 'var(--text-muted)', fontFamily: 'DM Mono, monospace', fontSize: '11px' },
      formatter: (val) => `$${val.toFixed(2)}`,
    },
  },
  plotOptions: {
    candlestick: {
      colors: {
        upward: '#2D7A3A',
        downward: '#B53230',
      },
      wick: { useFillColor: true },
    },
  },
  grid: {
    borderColor: 'var(--border)',
    strokeDashArray: 3,
  },
  tooltip: {
    theme: isDark.value ? 'dark' : 'light',
    style: { fontFamily: 'Outfit, sans-serif' },
  },
}))

const chartSeries = computed(() => {
  if (!price.value?.historical?.length) return []
  return [{
    data: price.value.historical.map(p => ({
      x: new Date(p.timestamp).getTime(),
      y: [p.open, p.high, p.low, p.close],
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
  return `${Math.floor(diffHours / 24)}d ago`
}

function truncate(text, maxLen) {
  if (!text || text.length <= maxLen) return text || ''
  return text.substring(0, maxLen) + '…'
}
</script>
