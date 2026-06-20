<template>
  <div class="settings">
    <div class="settings-hero glass-card">
      <h1 class="settings-title">⚙️ Settings</h1>
      <p class="settings-sub">Manage tickers, data sources, and application preferences.</p>
    </div>

    <!-- ═══ TICKER MANAGEMENT ═══ -->
    <section class="settings-section glass-card" aria-labelledby="section-tickers">
      <div class="sec-header">
        <h2 class="sec-title" id="section-tickers">📋 Tracked Tickers</h2>
        <button class="btn btn-secondary" @click="addDefaults" id="btn-load-defaults">Load Defaults</button>
      </div>

      <!-- Add ticker -->
      <div class="add-ticker-form">
        <input
          v-model="newTickerSymbol"
          type="text"
          placeholder="Enter ticker symbol (e.g. AAPL)"
          class="form-input ticker-input"
          id="input-ticker-symbol"
          @keyup.enter="addTicker"
          maxlength="5"
          aria-label="Ticker symbol"
        />
        <button class="btn btn-primary" @click="addTicker" :disabled="!newTickerSymbol.trim()" id="btn-add-ticker">
          + Add
        </button>
      </div>

      <!-- Loading -->
      <div v-if="store.loading" class="loading-inline">
        <div class="spinner-sm"></div>
        <span>Loading tickers…</span>
      </div>

      <!-- Empty -->
      <div v-else-if="store.tickers.length === 0" class="empty-state-inline">
        <p>No tickers configured yet.</p>
        <button class="btn btn-primary" @click="addDefaults" id="btn-load-defaults-inline">📥 Load Default Tickers</button>
      </div>

      <!-- List -->
      <div v-else class="ticker-list" role="list">
        <div
          v-for="ticker in store.tickers"
          :key="ticker.symbol"
          class="ticker-row"
          role="listitem"
          :id="`ticker-row-${ticker.symbol}`"
        >
          <div class="ticker-row-left">
            <div class="source-avatar ticker-avatar">{{ ticker.symbol[0] }}</div>
            <div class="ticker-info">
              <span class="ticker-sym">{{ ticker.symbol }}</span>
              <span v-if="ticker.name" class="ticker-name">{{ ticker.name }}</span>
              <span v-if="ticker.sector" class="ticker-sector badge badge-neutral">{{ ticker.sector }}</span>
            </div>
          </div>
          <div class="ticker-row-right">
            <span class="ticker-status-pill" :class="{ active: ticker.active }">
              {{ ticker.active ? 'Active' : 'Inactive' }}
            </span>
            <button
              class="btn-remove"
              @click="removeTicker(ticker.symbol)"
              :aria-label="`Remove ${ticker.symbol}`"
              :id="`btn-remove-${ticker.symbol}`"
              title="Remove ticker"
            >✕</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══ RSS FEEDS ═══ -->
    <section class="settings-section glass-card" aria-labelledby="section-rss">
      <h2 class="sec-title" id="section-rss">📡 RSS Feed Sources</h2>
      <div class="feed-list" role="list">
        <div v-if="feeds.length === 0" class="empty-state-inline">
          <p>Using default RSS feeds configured in backend.</p>
        </div>
        <div
          v-for="(feed, idx) in feeds"
          :key="idx"
          class="feed-item"
          role="listitem"
          :id="`feed-item-${idx}`"
        >
          <span class="feed-icon">📡</span>
          <span class="feed-url">{{ feed }}</span>
        </div>
      </div>
    </section>

    <!-- ═══ DATA MANAGEMENT ═══ -->
    <section class="settings-section glass-card" aria-labelledby="section-data">
      <h2 class="sec-title" id="section-data">🔄 Data Management</h2>
      <div class="data-actions">
        <button class="btn btn-primary" @click="fetchNews" :disabled="fetching" id="btn-fetch-news">
          {{ fetching ? '⟳ Fetching…' : '⟳ Fetch News Now' }}
        </button>
        <span class="data-hint">Manually trigger news fetching from all sources</span>
      </div>
      <Transition name="fade">
        <div v-if="fetchResult" class="fetch-result" :class="{ success: fetchResult.total_fetched > 0 }">
          <span class="fetch-result-icon">{{ fetchResult.total_fetched > 0 ? '✨' : '📭' }}</span>
          <p>
            Fetched {{ fetchResult.total_fetched }} articles
            ({{ fetchResult.new_saved }} new, {{ fetchResult.analyzed }} analyzed)
          </p>
        </div>
      </Transition>
    </section>

    <!-- ═══ API INFO ═══ -->
    <section class="settings-section glass-card" aria-labelledby="section-api">
      <h2 class="sec-title" id="section-api">🔌 API Information</h2>
      <div class="api-grid">
        <div class="api-row">
          <span class="api-label">Backend URL</span>
          <code class="api-code">http://localhost:8000</code>
        </div>
        <div class="api-row">
          <span class="api-label">API Docs</span>
          <a href="http://localhost:8000/docs" target="_blank" class="api-link" id="link-api-docs">Swagger UI →</a>
        </div>
        <div class="api-row">
          <span class="api-label">Frontend</span>
          <code class="api-code">http://localhost:5173</code>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useStockStore } from '../store/index.js'

const store = useStockStore()
const newTickerSymbol = ref('')
const fetching = ref(false)
const fetchResult = ref(null)

const feeds = ref([
  'https://finance.yahoo.com/news/rssindex',
  'https://feeds.content.dowjones.io/public/rss/mw_topstories',
  'https://www.cnbc.com/id/100003114/device/rss/rss.html',
  'https://feeds.marketwatch.com/marketwatch/marketpulse/',
  'https://www.investing.com/rss/news.rss',
  'https://seekingalpha.com/feed.xml',
])

onMounted(async () => {
  await store.fetchTickers()
})

async function addDefaults() {
  await store.addDefaultTickers()
}

async function addTicker() {
  const symbol = newTickerSymbol.value.trim().toUpperCase()
  if (!symbol) return
  try {
    await store.addTicker(symbol)
    newTickerSymbol.value = ''
  } catch (err) {
    alert(err.response?.data?.detail || 'Failed to add ticker')
  }
}

async function removeTicker(symbol) {
  if (confirm(`Remove ${symbol} from tracking?`)) {
    await store.removeTicker(symbol)
  }
}

async function fetchNews() {
  fetching.value = true
  fetchResult.value = null
  try {
    const result = await store.triggerFetch()
    fetchResult.value = result
  } catch {
    alert('Failed to fetch news')
  } finally {
    fetching.value = false
  }
}
</script>
