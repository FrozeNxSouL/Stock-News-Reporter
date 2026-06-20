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

<style scoped>
.ticker-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

/* ---- Back button ---- */
.back-btn {
  background: none;
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 8px 16px;
  border-radius: var(--r-sm);
  cursor: pointer;
  font-size: 13px;
  font-family: 'Outfit', sans-serif;
  font-weight: 500;
  align-self: flex-start;
  transition: var(--trans-fast);
}

.back-btn:hover {
  color: var(--text-primary);
  border-color: var(--brand-caramel);
  background: var(--nav-active-bg);
}

/* ---- Hero card ---- */
.ticker-hero {
  position: relative;
  overflow: hidden;
  padding: 0;
}

.hero-bg-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  opacity: 0.35;
}

.hero-bg-orb-1 {
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, var(--brand-caramel) 0%, transparent 70%);
  top: -100px;
  right: -60px;
}

.hero-bg-orb-2 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, var(--brand-sage) 0%, transparent 70%);
  bottom: -60px;
  left: 20px;
}

/* Tabs at top */
.ticker-tabs {
  display: flex;
  gap: 0;
  padding: 0 24px;
  border-bottom: 1px solid var(--border);
  position: relative;
}

.ticker-tab {
  padding: 14px 20px;
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
}

.ticker-tab:hover { color: var(--text-primary); }

.ticker-tab.active {
  color: var(--text-primary);
  border-bottom-color: var(--brand-caramel);
  font-weight: 700;
}

/* Hero main area */
.hero-main {
  padding: 24px 28px 16px;
  position: relative;
}

.hero-ticker {
  font-size: 40px;
  font-weight: 900;
  font-family: 'DM Serif Display', serif;
  color: var(--text-primary);
  letter-spacing: -1px;
  margin-bottom: 8px;
}

.hero-price-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.hero-price {
  font-size: 34px;
  font-weight: 800;
  font-family: 'DM Mono', monospace;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.hero-change {
  font-size: 13px;
  padding: 5px 12px;
}

.hero-sub {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 1px;
  font-weight: 600;
  text-transform: uppercase;
}

/* Stats row */
.hero-stats {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 14px 28px;
  border-top: 1px solid var(--border);
  position: relative;
}

.hero-stat {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 0 20px 0 0;
}

.hstat-sep {
  width: 1px;
  height: 28px;
  background: var(--border);
  margin: 0 20px 0 0;
  flex-shrink: 0;
}

.hstat-label {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-weight: 600;
}

.hstat-value {
  font-size: 15px;
  font-weight: 700;
  font-family: 'DM Mono', monospace;
  color: var(--text-primary);
}

/* Action buttons */
.hero-actions {
  display: flex;
  gap: 10px;
  padding: 16px 28px 24px;
  position: relative;
}

.hero-btn {
  flex: 1;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 700;
  border-radius: var(--r-pill);
}

/* ---- Detail sections ---- */
.detail-section {
  padding: 24px;
}

.detail-section-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 18px;
}

.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.article-count {
  font-size: 13px;
  color: var(--text-muted);
}

/* Chart */
.chart-container { width: 100%; }

/* Sentiment grid */
.sentiment-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.sentiment-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 16px;
}

.sc-label {
  display: block;
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 6px;
  font-weight: 600;
}

.sc-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.sc-value.up { color: var(--up-color); }
.sc-value.down { color: var(--down-color); }
.sc-value.improving { color: var(--up-color); }
.sc-value.deteriorating { color: var(--down-color); }

/* Distribution */
.dist-title {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.dist-bars {
  display: flex;
  height: 26px;
  border-radius: var(--r-sm);
  overflow: hidden;
  gap: 2px;
}

.dist-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: white;
  transition: flex 0.3s;
  border-radius: 4px;
}

.dist-bar.positive { background: var(--up-color); }
.dist-bar.neutral { background: var(--brand-sage); }
.dist-bar.negative { background: var(--down-color); }

/* ---- News article list (Picture 3) ---- */
.news-article-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.news-article {
  padding: 0;
  overflow: hidden;
}

.article-top {
  padding: 24px 28px 20px;
  border-bottom: 1px solid var(--border);
}

.article-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.article-date {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.article-meta-actions {
  display: flex;
  gap: 6px;
}

.meta-action-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--glass-bg);
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--trans-fast);
}

.meta-action-btn:hover {
  border-color: var(--brand-caramel);
  background: var(--nav-active-bg);
}

.article-ticker-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.article-ticker {
  font-size: 12px;
  padding: 4px 12px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.ticker-dot {
  font-size: 8px;
  opacity: 0.7;
}

.ticker-pct {
  font-weight: 700;
  margin-left: 2px;
}

.ticker-pct.up { color: var(--up-color); }
.ticker-pct.down { color: var(--down-color); }

.article-title-link {
  text-decoration: none;
  color: inherit;
}

.article-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.35;
  transition: color 0.2s;
}

.article-title-link:hover .article-title {
  color: var(--brand-caramel);
}

/* Article body */
.article-body {
  padding: 20px 28px 24px;
}

.article-summary {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.75;
  margin-bottom: 16px;
}

.analysis-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 16px;
}

.keyword-tag {
  font-size: 11px;
  padding: 3px 10px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  color: var(--text-muted);
  font-weight: 500;
}

.article-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}

.article-source-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.article-source-avatar {
  width: 28px;
  height: 28px;
  font-size: 12px;
  flex-shrink: 0;
}

.article-source-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.read-more-btn {
  font-size: 12px;
  padding: 7px 16px;
}

/* Statistics table */
.stats-table {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stats-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-surface);
  border-radius: var(--r-sm);
  font-size: 14px;
}

.stats-label {
  color: var(--text-muted);
  font-weight: 500;
}

.stats-val {
  font-weight: 700;
  font-family: 'DM Mono', monospace;
  color: var(--text-primary);
}

.stats-val.up { color: var(--up-color); }
.stats-val.down { color: var(--down-color); }

/* ---- Responsive ---- */
@media (max-width: 600px) {
  .ticker-hero, .detail-section {
    border-radius: var(--r-md);
  }

  .hero-ticker { font-size: 32px; }
  .hero-price { font-size: 26px; }

  .hero-stats {
    flex-wrap: wrap;
    gap: 12px;
    padding: 14px 20px;
  }

  .hstat-sep { display: none; }

  .hero-actions {
    padding: 12px 20px 20px;
  }

  .article-top, .article-body {
    padding-left: 18px;
    padding-right: 18px;
  }

  .article-title {
    font-size: 18px;
  }
}
</style>
