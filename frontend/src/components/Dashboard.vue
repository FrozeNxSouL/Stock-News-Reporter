<template>
  <div class="dashboard">

    <!-- ═══ HERO SECTION ═══ -->
    <div class="hero-section glass-card" :class="{ 'portfolio-mode': viewMode === 'portfolio' }">

      <!-- View toggle button -->
      <button
        class="view-toggle"
        @click.stop="toggleViewMode"
        :title="viewMode === 'market' ? 'Switch to Portfolio view' : 'Switch to Market view'"
      >
        <span v-if="viewMode === 'market'">◎</span>
        <span v-else>▦</span>
      </button>

      <!-- ═══════ MARKET VIEW (Picture 1 style) ═══════ -->
      <template v-if="viewMode === 'market'">
        <div class="hero-content">
          <div class="hero-left">
            <p class="hero-tagline">News Brewing</p>
            <h1 class="hero-title">Market<br><span class="hero-accent">Dashboard</span></h1>
            <p class="hero-sub">Real-time stock news &amp; sentiment analysis</p>
          </div>
        </div>

        <!-- Ticker bubbles + search -->
        <div class="ticker-bubbles" v-if="authStore.isAuthenticated">
          <button
            v-for="ticker in selectedTickers.slice(0, 7)"
            :key="ticker"
            class="ticker-bubble"
            :class="{ active: true }"
            @click="$router.push(`/ticker/${ticker}`)"
            :title="ticker"
          >
            <span v-if="authStore.pinnedTickers.includes(ticker)" class="bubble-pin-dot"></span>
            <span class="bubble-symbol">{{ ticker }}</span>
          </button>
          <button class="search-bubble" @click="$router.push('/watchlist')" title="Search / Add tickers">
            <span>+</span>
          </button>
        </div>

        <div v-else-if="authStore.initialized" class="ticker-bubbles-empty">
          <p class="empty-hint" style="color:rgba(243,228,201,0.45);text-align:center;position:relative;z-index:2;font-size:13px">
            Sign in to start tracking tickers
          </p>
        </div>

        <!-- Featured ticker cards (pinned tickers) -->
        <div v-if="featuredTickers.length > 0" class="featured-cards-row">
          <div
            v-for="ticker in featuredTickers"
            :key="ticker"
            class="featured-card"
            :class="{ 'has-data': getPrice(ticker) }"
            @click="$router.push(`/ticker/${ticker}`)"
          >
            <template v-if="getPrice(ticker)">
              <div class="featured-price-row">
                <span class="featured-ticker">{{ ticker }}</span>
                <span class="featured-price">${{ getPrice(ticker)?.current_price?.toFixed(2) }}</span>
                <span
                  class="featured-change"
                  :class="getPriceClass(ticker)"
                >
                  {{ getPrice(ticker)?.change_percent > 0 ? '▲' : getPrice(ticker)?.change_percent < 0 ? '▼' : '─' }}
                  {{ Math.abs(getPrice(ticker)?.change_percent || 0).toFixed(2) }}%
                </span>
              </div>
              <div class="featured-sparkline" v-if="getPrice(ticker)?.historical?.length">
                <svg viewBox="0 0 100 36" preserveAspectRatio="none">
                  <path
                    :d="sparklinePath(getPrice(ticker))"
                    fill="none"
                    :stroke="sparklineColorForTicker(ticker)"
                    stroke-width="2.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </div>
            </template>
            <template v-else>
              <div class="featured-skeleton">
                <div class="skeleton-line skeleton-price" style="width:60px;height:22px;margin-bottom:6px"></div>
                <div class="skeleton-line" style="width:40px;height:12px"></div>
              </div>
            </template>
          </div>
        </div>
      </template>

      <!-- ═══════ PORTFOLIO VIEW (Packed Bubble Chart) ═══════ -->
      <template v-else>
        <div class="portfolio-header">
          <p class="portfolio-label">PORTFOLIO</p>
          <p class="portfolio-total">
            <span v-if="portfolioBestChange !== null" class="portfolio-best up">Highest {{ portfolioBestChange }}%</span>
            <span>-</span>
            <span v-if="portfolioWorstChange !== null" class="portfolio-best down">Lowest {{ portfolioWorstChange }}%</span>
          </p>
          <p class="portfolio-total-label">{{ selectedTickers.length }} tickers tracked</p>
        </div>

        <div
          v-if="selectedTickers.length > 0"
          class="portfolio-bubbles"
          :style="{ height: portfolioChartHeight + 'px' }"
          ref="portfolioChartRef"
        >

          <div
            v-for="b in portfolioBubbles"
            :key="b.ticker"
            class="portfolio-circle"
            :style="{
              width: b.r * 2 + 'px',
              height: b.r * 2 + 'px',
              left: (b.x - b.r) + 'px',
              top: (b.y - b.r) + 'px',
              background: b.gradient,
            }"
            @click="$router.push(`/ticker/${b.ticker}`)"
          >
            <span class="pc-symbol" :style="{ fontSize: b.symbolFontSize + 'px' }">{{ b.ticker }}</span>
            <span v-if="b.price" class="pc-price" :style="{ fontSize: b.priceFontSize + 'px' }">${{ b.price }}</span>
            <span
              v-if="b.price"
              class="pc-change"
              :class="b.changeClass"
              :style="{ fontSize: b.changeFontSize + 'px' }"
            >{{ b.changePrefix }}{{ b.changePct }}%</span>
          </div>

          <!-- FAB button -->
          <button class="fab-btn" @click="$router.push('/watchlist')" title="Add tickers">+</button>
        </div>

        <div v-else class="state-container" style="position:relative;z-index:2;padding:40px 24px">
          <p class="state-text" style="color:rgba(243,228,201,0.55)">
            No tickers in your watchlist yet.<br>Go to Watchlist to add some.
          </p>
        </div>
      </template>

      <!-- Hero actions (market view) -->
      <div v-if="viewMode === 'market'" class="hero-actions">
        <button class="btn btn-secondary" @click="refreshAll" :disabled="loading" id="btn-refresh">
          {{ loading ? '⟳ Refreshing…' : '⟳ Refresh All' }}
        </button>
      </div>
    </div>

    <!-- ═══ LOADING STATE ═══ -->
    <div v-if="store.loading && selectedTickers.length === 0" class="state-container">
      <div class="spinner"></div>
      <p class="state-text">Brewing market data…</p>
    </div>

    <!-- ═══ ERROR STATE ═══ -->
    <div v-if="store.error" class="state-container">
      <span class="state-icon">⚠️</span>
      <p class="state-text">{{ store.error }}</p>
    </div>

    <!-- ═══ STOCK PRICE CARDS ═══ -->
    <section v-if="selectedTickers.length > 0" class="cards-section" aria-label="Stock prices">
      <h2 class="section-title">Selected Tickers</h2>
      <div class="price-cards">
        <article
          v-for="ticker in selectedTickers"
          :key="ticker"
          class="price-card"
          :class="[getPriceClass(ticker), { 'pinned-card': authStore.pinnedTickers.includes(ticker) }]"
          @click="$router.push(`/ticker/${ticker}`)"
          :id="`price-card-${ticker}`"
          role="button"
          tabindex="0"
          :aria-label="`${ticker} stock card`"
          @keyup.enter="$router.push(`/ticker/${ticker}`)"
        >
          <!-- Gradient background bubble -->
          <div class="card-bg-orb"></div>
          <div v-if="authStore.pinnedTickers.includes(ticker)" class="pinned-badge">PINNED</div>

          <!-- ═══ LOADING SKELETON ═══ -->
          <template v-if="!getPrice(ticker)">
            <div class="card-skeleton-header">
              <span class="card-symbol">{{ ticker }}</span>
            </div>
            <div class="skeleton-line skeleton-price"></div>
            <div class="skeleton-row">
              <div class="skeleton-line skeleton-stat"></div>
              <div class="skeleton-line skeleton-stat"></div>
              <div class="skeleton-line skeleton-stat"></div>
            </div>
            <div class="skeleton-line skeleton-chart"></div>
          </template>

          <!-- ═══ LIVE DATA ═══ -->
          <template v-else>

          <div class="card-header">
            <span class="card-symbol">
              <span v-if="authStore.pinnedTickers.includes(ticker)" class="card-pin-dot"></span>
              {{ ticker }}
            </span>
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
              <path
                :d="sparklinePath(getPrice(ticker))"
                fill="none"
                :stroke="getPriceColor(getPrice(ticker))"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
        </template>
        </article>
      </div>
    </section>

    <!-- ═══ EMPTY STATE ═══ -->
    <div v-if="authStore.isAuthenticated && selectedTickers.length === 0 && !store.loading" class="state-container">
      <p class="state-text">No tickers in your watchlist</p>
      <router-link to="/watchlist" class="btn btn-primary" style="margin-top:12px">Go to Watchlist →</router-link>
    </div>

    <!-- ═══ RECENT NEWS ═══ -->
    <section v-if="recentNews.length > 0" class="news-section" aria-label="Recent news">
      <div class="section-header-row">
        <h2 class="section-title">Recent News</h2>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useStockStore } from '../store/index.js'
import { useAuthStore } from '../store/auth.js'

const store = useStockStore()
const authStore = useAuthStore()
const loading = ref(false)
const viewMode = ref('market') // 'market' | 'portfolio'

function toggleViewMode() {
  viewMode.value = viewMode.value === 'market' ? 'portfolio' : 'market'
}

// ─── selectedTickers: pinned first, then rest; properly reactive ───
const selectedTickers = computed(() => {
  if (!authStore.isAuthenticated) return []
  const wl = authStore.watchlist
  const pinned = authStore.pinnedTickers
  const rest = wl.filter(t => !pinned.includes(t))
  return [...pinned, ...rest]
})

// ─── featured tickers: all pinned tickers, shown as highlight cards ───
const featuredTickers = computed(() => {
  return authStore.pinnedTickers
})

// ─── best (highest positive) and worst (most negative) change % ───
const portfolioBestChange = computed(() => {
  let best = -Infinity
  for (const t of selectedTickers.value) {
    const p = getPrice(t)
    if (p?.change_percent != null && p.change_percent > best) best = p.change_percent
  }
  return isFinite(best) ? best.toFixed(2) : null
})

const portfolioWorstChange = computed(() => {
  let worst = Infinity
  for (const t of selectedTickers.value) {
    const p = getPrice(t)
    if (p?.change_percent != null && p.change_percent < worst) worst = p.change_percent
  }
  return isFinite(worst) ? worst.toFixed(2) : null
})

// ─── Reactive screen width ───
const screenWidth = ref(window.innerWidth)

function onWindowResize() {
  screenWidth.value = window.innerWidth
}

// ─── Packed Bubble Chart ───
const portfolioChartRef = ref(null)

const portfolioBubbles = computed(() => {
  const tickers = selectedTickers.value
  if (!tickers.length) return []

  // Width adapts to screen, clamped for very narrow/wide
  const canvasWidth = Math.max(360, Math.min(800, screenWidth.value - 48))

  // Build data, keyed by absolute change % for sizing
  const tickerData = tickers.map(t => {
    const p = getPrice(t)
    const absChange = p?.change_percent != null ? Math.abs(p.change_percent) : 0
    return {
      ticker: t,
      price: p?.current_price ?? 0,
      priceFmt: p?.current_price?.toFixed(2) ?? '—',
      absChange,
      changePct: p?.change_percent != null ? Math.abs(p.change_percent).toFixed(2) : '0.00',
      changePrefix: p?.change_percent > 0 ? '+' : p?.change_percent < 0 ? '-' : '',
      changeClass: p?.change_percent > 0 ? 'up' : p?.change_percent < 0 ? 'down' : '',
      gradStart: p?.change_percent > 0 ? 'rgba(94,224,133,0.18)' : p?.change_percent < 0 ? 'rgba(255,107,107,0.18)' : 'rgba(243,228,201,0.12)',
      gradEnd: p?.change_percent > 0 ? 'rgba(94,224,133,0.04)' : p?.change_percent < 0 ? 'rgba(255,107,107,0.04)' : 'rgba(243,228,201,0.04)',
    }
  })

  // Sort by absolute change descending (biggest % movers first = largest bubbles)
  tickerData.sort((a, b) => b.absChange - a.absChange)

  // Map change % to radius (min 38, max 70)
  const changes = tickerData.map(i => i.absChange).filter(v => v > 0)
  const cMin = changes.length ? Math.min(...changes) : 0.1
  const cMax = changes.length ? Math.max(...changes) : 5
  const changeRange = (cMax - cMin) || 1
  const maxRadius = tickerData.length > 8 ? 60 : 70
  const minRadius = 38

  const bubbleNodes = tickerData.map((item, i) => {
    let r = minRadius
    if (item.absChange > 0 && changes.length > 0) {
      r = minRadius + ((item.absChange - cMin) / changeRange) * (maxRadius - minRadius)
      r = Math.max(minRadius, Math.min(maxRadius, r))
    }
    if (tickerData.length <= 3) r = Math.max(r, 52)
    return { ...item, r, x: 0, y: 0 }
  })

  // Tight circle packing: each new bubble placed touching existing ones
  const minGap = 0

  // Estimate canvas height from total packed area
  const totalBubbleArea = bubbleNodes.reduce((sum, n) => sum + Math.PI * n.r * n.r, 0)
  const packedHeight = Math.max(320, Math.ceil(totalBubbleArea / (canvasWidth * 0.72) + 60))

  bubbleNodes.forEach((n, i) => {
    if (i === 0) {
      n.x = canvasWidth / 2
      n.y = n.r + 8
      return
    }

    let bestX = canvasWidth / 2
    let bestY = packedHeight - n.r - 8
    let bestDist = Infinity

    // Try placing touching each already-placed bubble
    for (let j = 0; j < i; j++) {
      const existing = bubbleNodes[j]
      const touchDist = n.r + existing.r + minGap
      // Sample angles around the existing bubble (every 15 degrees)
      const angleSteps = 24
      for (let a = 0; a < angleSteps; a++) {
        const angle = (a / angleSteps) * Math.PI * 2
        const cx = existing.x + Math.cos(angle) * touchDist
        const cy = existing.y + Math.sin(angle) * touchDist

        // Bounds check — keep inside canvas
        if (cx - n.r < 0 || cx + n.r > canvasWidth) continue
        if (cy - n.r < 0 || cy + n.r > packedHeight) continue

        // Collision check against all placed bubbles
        let overlaps = false
        for (let k = 0; k < i; k++) {
          const dx = cx - bubbleNodes[k].x
          const dy = cy - bubbleNodes[k].y
          const minDist = n.r + bubbleNodes[k].r + minGap
          if (dx * dx + dy * dy < minDist * minDist - 0.5) { overlaps = true; break }
        }
        if (overlaps) continue

        // Also try spots touching TWO existing bubbles (j and another)
        // by intersecting the two touch circles around j and m
        for (let m = 0; m < i; m++) {
          if (m === j) continue
          const dxJM = existing.x - bubbleNodes[m].x
          const dyJM = existing.y - bubbleNodes[m].y
          const distJM = Math.sqrt(dxJM * dxJM + dyJM * dyJM)
          const rA = n.r + bubbleNodes[j].r + minGap
          const rB = n.r + bubbleNodes[m].r + minGap
          // Check if circles intersect (triangle inequality)
          if (distJM > rA + rB || distJM < Math.abs(rA - rB)) continue
          // Intersection point calculation
          const a_ = (rA * rA - rB * rB + distJM * distJM) / (2 * distJM)
          const h = Math.sqrt(Math.max(0, rA * rA - a_ * a_))
          const midX = existing.x + a_ * (bubbleNodes[m].x - existing.x) / distJM
          const midY = existing.y + a_ * (bubbleNodes[m].y - existing.y) / distJM
          const perpX = -h * (bubbleNodes[m].y - existing.y) / distJM
          const perpY = h * (bubbleNodes[m].x - existing.x) / distJM
          // Two intersection candidates
          for (const sign of [1, -1]) {
            const ix = midX + sign * perpX
            const iy = midY + sign * perpY
            if (ix - n.r < 0 || ix + n.r > canvasWidth) continue
            if (iy - n.r < 0 || iy + n.r > packedHeight) continue
            let ok = true
            for (let k = 0; k < i; k++) {
              const dx = ix - bubbleNodes[k].x
              const dy = iy - bubbleNodes[k].y
              if (dx * dx + dy * dy < (n.r + bubbleNodes[k].r + minGap) ** 2 - 0.3) { ok = false; break }
            }
            if (ok) {
              const d = Math.sqrt((ix - canvasWidth / 2) ** 2 + (iy - packedHeight / 2) ** 2)
              if (d < bestDist) { bestDist = d; bestX = ix; bestY = iy }
            }
          }
        }

        // Accept the single-touch position if no double-touch found yet
        const d = Math.sqrt((cx - canvasWidth / 2) ** 2 + (cy) ** 2)
        if (d < bestDist) { bestDist = d; bestX = cx; bestY = cy }
      }
    }

    n.x = bestX
    n.y = bestY
  })

  // Height from actual bottommost bubble
  const actualMaxY = bubbleNodes.reduce((m, n) => Math.max(m, n.y + n.r), 0)
  _latestChartHeight = Math.max(packedHeight, Math.ceil(actualMaxY + 20), bubbleNodes.length * 40)

  // Add visual props, scale relative to largest bubble
  const maxR = bubbleNodes.reduce((m, n) => Math.max(m, n.r), 65)
  return bubbleNodes.map(n => {
    const scale = n.r / maxR
    return {
      ...n,
      symbolFontSize: Math.round(11 + scale * 6),
      priceFontSize: Math.round(9 + scale * 5),
      changeFontSize: Math.round(8 + scale * 4),
      gradient: `radial-gradient(circle at 45% 40%, ${n.gradStart} 0%, ${n.gradEnd} 100%)`,
    }
  })
})

// Track chart height reactively (mutable module-level, read via computed)
let _latestChartHeight = 700
const portfolioChartHeight = computed(() => {
  portfolioBubbles.value // trigger recompute
  return _latestChartHeight
})

onMounted(async () => {
  if (selectedTickers.value.length > 0) {
    await refreshPrices()
  }
  await store.fetchNews({ page_size: 8 })
  store.startAutoRefresh(60000)
  window.addEventListener('resize', onWindowResize)
})

onUnmounted(() => {
  store.stopAutoRefresh()
  window.removeEventListener('resize', onWindowResize)
})

async function refreshAll() {
  loading.value = true
  await Promise.all([
    refreshPrices(),
    store.fetchNews({ page_size: 8 }),
  ])
  loading.value = false
}

async function refreshPrices() {
  const tickers = selectedTickers.value
  if (tickers.length > 0) {
    await store.fetchMultiplePrices(tickers)
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

function sparklineColorForTicker(ticker) {
  const price = getPrice(ticker)
  if (!price) return 'rgba(94,224,133,0.8)'
  return price.change_percent >= 0 ? 'rgba(94,224,133,0.8)' : 'rgba(255,107,107,0.8)'
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
  return `M ${pts[0]} L ${pts.slice(1).join(' L ')}`
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
  for (const t of selectedTickers) {
    if (article.tickers?.includes(t)) return t
  }
  return selectedTickers[0] || article.tickers?.[0] || 'SPY'
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
