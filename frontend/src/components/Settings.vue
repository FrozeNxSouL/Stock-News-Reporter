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

<style scoped>
.settings {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 820px;
  margin: 0 auto;
  width: 100%;
}

/* ---- Hero ---- */
.settings-hero {
  padding: 28px 32px;
}

.settings-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.settings-sub {
  font-size: 14px;
  color: var(--text-muted);
}

/* ---- Sections ---- */
.settings-section {
  padding: 24px 28px;
}

.sec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.sec-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 18px;
}

.sec-header .sec-title {
  margin-bottom: 0;
}

/* ---- Add ticker form ---- */
.add-ticker-form {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
}

.ticker-input {
  flex: 1;
  font-family: 'DM Mono', monospace;
  text-transform: uppercase;
}

/* ---- Ticker list ---- */
.ticker-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ticker-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  transition: var(--trans-fast);
}

.ticker-row:hover {
  border-color: var(--border-strong);
}

.ticker-row-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ticker-avatar {
  width: 36px;
  height: 36px;
  font-size: 14px;
  font-weight: 800;
}

.ticker-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ticker-sym {
  font-size: 14px;
  font-weight: 800;
  font-family: 'DM Mono', monospace;
  color: var(--text-primary);
  min-width: 55px;
}

.ticker-name {
  font-size: 13px;
  color: var(--text-muted);
}

.ticker-sector {
  font-size: 10px;
}

.ticker-row-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ticker-status-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  background: var(--border);
  color: var(--text-muted);
}

.ticker-status-pill.active {
  background: var(--up-bg);
  color: var(--up-color);
}

.btn-remove {
  background: none;
  border: 1px solid var(--border);
  color: var(--down-color);
  width: 30px;
  height: 30px;
  border-radius: var(--r-sm);
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--trans-fast);
}

.btn-remove:hover {
  background: var(--down-bg);
  border-color: var(--down-color);
}

/* ---- Empty / loading inline ---- */
.empty-state-inline {
  text-align: center;
  padding: 28px 16px;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.loading-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  padding: 12px 0;
  font-size: 14px;
}

/* ---- RSS Feeds ---- */
.feed-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.feed-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
}

.feed-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.feed-url {
  font-size: 12px;
  font-family: 'DM Mono', monospace;
  color: var(--text-muted);
  word-break: break-all;
}

/* ---- Data management ---- */
.data-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.data-hint {
  font-size: 13px;
  color: var(--text-muted);
}

.fetch-result {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: var(--r-md);
  font-size: 13px;
  font-weight: 500;
  background: rgba(107, 63, 31, 0.10);
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

.fetch-result.success {
  background: var(--up-bg);
  border-color: rgba(45, 122, 58, 0.25);
  color: var(--up-color);
}

.fetch-result-icon {
  font-size: 18px;
}

/* Fade transition */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* ---- API grid ---- */
.api-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.api-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
}

.api-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
  min-width: 110px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.api-code {
  font-size: 12px;
  font-family: 'DM Mono', monospace;
  color: var(--brand-caramel);
}

.api-link {
  color: var(--brand-caramel);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: var(--trans-fast);
}

.api-link:hover {
  color: var(--brand-espresso);
  text-decoration: underline;
}

/* ---- Responsive ---- */
@media (max-width: 600px) {
  .settings-hero {
    padding: 20px 18px;
  }

  .settings-section {
    padding: 18px 16px;
  }

  .ticker-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 3px;
  }

  .api-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .data-actions {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
