<template>
  <div class="settings">
    <div class="settings-hero glass-card">
      <h1 class="settings-title">⚙️ Settings</h1>
      <p class="settings-sub">Manage tickers, data sources, and application preferences.</p>
    </div>

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

const feeds = ref([
  'https://finance.yahoo.com/news/rssindex',
  'https://feeds.content.dowjones.io/public/rss/mw_topstories',
  'https://www.cnbc.com/id/100003114/device/rss/rss.html',
  'https://feeds.marketwatch.com/marketwatch/marketpulse/',
  'https://www.investing.com/rss/news.rss',
  'https://seekingalpha.com/feed.xml',
])

onMounted(async () => {
  // nothing to load
})
</script>

<style scoped>
</style>
