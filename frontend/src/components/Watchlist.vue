<template>
  <div class="watchlist-page">
    <div class="wl-hero glass-card">
      <h1 class="wl-title">📋 Watchlist</h1>
      <p class="wl-sub">Manage your tracked tickers. Add verified tickers to monitor on your dashboard.</p>
    </div>

    <!-- ═══ ADD TICKER ═══ -->
    <section class="wl-section glass-card search-section" aria-labelledby="section-add">
      <h2 class="wl-section-title" id="section-add">Add Ticker</h2>

      <div class="wl-add-row">
        <div class="wl-autocomplete" ref="acRef">
          <input
            v-model="query"
            type="text"
            placeholder="Search by symbol or company name (e.g. AAPL, Apple)..."
            class="form-input wl-input"
            id="wl-input"
            @input="onInput"
            @keydown.down.prevent="highlightNext"
            @keydown.up.prevent="highlightPrev"
            @keydown.enter.prevent="selectHighlighted || verifyAndAdd"
            @keydown.esc="hideDropdown"
            @blur="onBlur"
            autocomplete="off"
            aria-label="Search ticker symbol or company name"
            aria-expanded="suggestions.length > 0"
            aria-autocomplete="list"
          />
          <span v-if="searching" class="wl-spinner"></span>
          <span v-else-if="verified" class="wl-verified">✓</span>

          <!-- Autocomplete dropdown -->
          <Transition name="dropdown">
            <ul
              v-if="showDropdown && suggestions.length > 0"
              class="wl-suggestions glass-card"
              role="listbox"
            >
              <li
                v-for="(item, idx) in suggestions"
                :key="item.symbol"
                class="wl-suggestion-item"
                :class="{ highlighted: idx === highlightIdx }"
                role="option"
                :aria-selected="idx === highlightIdx"
                @mousedown.prevent="selectSuggestion(item)"
                @mouseenter="highlightIdx = idx"
              >
                <span class="wl-sym">{{ item.symbol }}</span>
                <span class="wl-name">{{ item.name }}</span>
                <span class="badge badge-neutral wl-exch">{{ item.exchange }}</span>
              </li>
            </ul>
          </Transition>
        </div>

        <button
          class="btn btn-primary"
          @click="verifyAndAdd"
          :disabled="!query.trim() || searching"
          id="btn-add-ticker"
        >+ Add</button>
      </div>

      <!-- Verification message -->
      <Transition name="fade">
        <div v-if="msg" class="wl-msg" :class="msgClass">{{ msg }}</div>
      </Transition>
    </section>

    <!-- ═══ TRACKED TICKERS ═══ -->
    <section class="wl-section glass-card" aria-labelledby="section-tracked">
      <div class="wl-section-header">
        <h2 class="wl-section-title" id="section-tracked">
          Tracked Tickers
          <span class="wl-count" v-if="watchlist.length">({{ watchlist.length }})</span>
        </h2>
      </div>

      <!-- Loading -->
      <div v-if="authStore.loading" class="state-inline">
        <div class="spinner-sm"></div>
        <span>Loading…</span>
      </div>

      <!-- Empty state -->
      <div v-else-if="watchlist.length === 0" class="wl-empty-state">
        <span class="wl-empty-icon">📭</span>
        <p class="wl-empty-text">Your watchlist is empty.</p>
        <p class="wl-empty-hint">Search and add tickers above to start tracking.</p>
      </div>

      <!-- Ticker list -->
      <div v-else class="wl-list" role="list">
        <div
          v-for="ticker in displayTickers"
          :key="ticker.symbol"
          class="wl-row"
          :class="{ 'pinned-row': pinned.includes(ticker.symbol) }"
          role="listitem"
          :id="`wl-row-${ticker.symbol}`"
        >
          <div class="wl-row-left" @click="$router.push(`/ticker/${ticker.symbol}`)" role="button" tabindex="0">
            <div class="wl-avatar source-avatar">{{ ticker.symbol[0] }}</div>
            <div class="wl-row-info">
              <span class="wl-row-symbol">{{ ticker.symbol }}</span>
              <span v-if="ticker.name" class="wl-row-name">{{ ticker.name }}</span>
            </div>
          </div>
          <div class="wl-row-right">
            <button
              class="btn-pin"
              :class="{ pinned: pinned.includes(ticker.symbol), loading: pinning === ticker.symbol }"
              :disabled="pinning === ticker.symbol"
              @click="togglePin(ticker.symbol)"
              :aria-label="pinned.includes(ticker.symbol) ? `Unpin ${ticker.symbol}` : `Pin ${ticker.symbol}`"
              :title="pinned.includes(ticker.symbol) ? 'Unpin' : 'Pin to top'"
            >{{ pinning === ticker.symbol ? '⏳' : '📌' }}</button>
            <span v-if="ticker.exchange" class="badge badge-neutral wl-row-exchange">{{ ticker.exchange }}</span>
            <button
              class="btn-remove"
              @click="removeTicker(ticker.symbol)"
              :aria-label="`Remove ${ticker.symbol}`"
              :title="`Remove ${ticker.symbol}`"
            >✕</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '../store/auth.js'
import { useStockStore } from '../store/index.js'

const authStore = useAuthStore()
const stockStore = useStockStore()

const query = ref('')
const suggestions = ref([])
const highlightIdx = ref(-1)
const showDropdown = ref(false)
const searching = ref(false)
const msg = ref('')
const msgType = ref('')
const selectedTicker = ref(null)
const verified = ref(false)
const pinning = ref(null)   // symbol currently being toggled
let debounce = null

const watchlist = computed(() => authStore.user?.watchlist || [])
const pinned = computed(() => authStore.user?.pinned || [])

// Pinned first, then the rest
const displayTickers = computed(() => {
  const pins = pinned.value
  const all = watchlist.value
  return [
    ...pins.filter(t => all.includes(t)).map(symbol => ({ symbol, name: '', exchange: '' })),
    ...all.filter(t => !pins.includes(t)).map(symbol => ({ symbol, name: '', exchange: '' })),
  ]
})

const msgClass = computed(() => ({
  'wl-msg-success': msgType.value === 'success',
  'wl-msg-error': msgType.value === 'error',
  'wl-msg-warn': msgType.value === 'warn',
}))

// ─── Debounced search ───
function onInput() {
  const val = query.value.trim()
  selectedTicker.value = null
  verified.value = false
  msg.value = ''

  if (val.length < 1) {
    suggestions.value = []
    showDropdown.value = false
    clearTimeout(debounce)
    return
  }

  clearTimeout(debounce)
  searching.value = true
  showDropdown.value = false

  debounce = setTimeout(async () => {
    if (query.value.trim().length < 1) {
      searching.value = false
      return
    }

    const results = await stockStore.searchTickers(query.value)
    suggestions.value = results
    highlightIdx.value = -1
    searching.value = false
    showDropdown.value = results.length > 0
  }, 400)
}

// ─── Keyboard ───
function highlightNext() {
  if (suggestions.value.length === 0) return
  highlightIdx.value = (highlightIdx.value + 1) % suggestions.value.length
  showDropdown.value = true
}

function highlightPrev() {
  if (suggestions.value.length === 0) return
  highlightIdx.value = highlightIdx.value <= 0
    ? suggestions.value.length - 1
    : highlightIdx.value - 1
  showDropdown.value = true
}

function selectSuggestion(item) {
  selectedTicker.value = item
  query.value = item.symbol
  suggestions.value = []
  showDropdown.value = false
  verified.value = true
  msg.value = `${item.name} (${item.exchange})`
  msgType.value = 'success'
}

const selectHighlighted = computed(() => {
  if (highlightIdx.value >= 0 && highlightIdx.value < suggestions.value.length) {
    selectSuggestion(suggestions.value[highlightIdx.value])
    return true
  }
  return false
})

function onBlur() {
  setTimeout(() => { showDropdown.value = false }, 200)
}

function hideDropdown() {
  showDropdown.value = false
}

// ─── Verify & Add ───
async function verifyAndAdd() {
  const raw = query.value.trim()
  if (!raw) return

  const symbol = raw.toUpperCase()

  if (watchlist.value.includes(symbol)) {
    msg.value = `"${symbol}" is already in your watchlist`
    msgType.value = 'warn'
    return
  }

  if (selectedTicker.value) {
    await doAdd(symbol)
    return
  }

  searching.value = true
  const info = await stockStore.lookupTicker(symbol)
  searching.value = false

  if (info) {
    selectedTicker.value = info
    verified.value = true
    query.value = info.symbol
    msg.value = `${info.name} (${info.exchange})`
    msgType.value = 'success'
    await doAdd(info.symbol)
  } else {
    msg.value = `Ticker "${symbol}" not found. Please check the symbol.`
    msgType.value = 'error'
  }
}

async function doAdd(symbol) {
  if (watchlist.value.includes(symbol)) {
    msg.value = `"${symbol}" is already in your watchlist`
    msgType.value = 'warn'
    return
  }

  try {
    const updated = [...watchlist.value, symbol]
    await authStore.updateProfile({ watchlist: updated })

    query.value = ''
    suggestions.value = []
    selectedTicker.value = null
    verified.value = false
    msg.value = `✅ ${symbol} added to watchlist`
    msgType.value = 'success'

    setTimeout(() => {
      if (msgType.value === 'success') msg.value = ''
    }, 3000)
  } catch {
    msg.value = 'Failed to add ticker'
    msgType.value = 'error'
  }
}

async function removeTicker(symbol) {
  try {
    const updated = watchlist.value.filter(t => t !== symbol)
    // Also remove from pinned if present
    const updatedPinned = pinned.value.filter(t => t !== symbol)
    await authStore.updateProfile({ watchlist: updated, pinned: updatedPinned })
  } catch {
    // silent
  }
}

async function togglePin(symbol) {
  pinning.value = symbol
  try {
    await authStore.togglePinned(symbol)
  } finally {
    pinning.value = null
  }
}
</script>

<style scoped>
/* ─── Hero ─── */
.wl-hero {
  margin-bottom: 24px;
  padding: 24px;
}

.wl-title {
  font-size: 1.6rem;
  font-weight: 700;
  margin: 0 0 6px 0;
}

.wl-sub {
  color: var(--text-muted);
  margin: 0;
  font-size: 0.9rem;
}

/* ─── Section ─── */
.wl-section {
  margin-bottom: 24px;
  padding: 20px;
  position: relative;
}

.search-section {
  z-index: 10;
}

.wl-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.wl-section-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 14px 0;
}

.wl-section-header > .wl-section-title {
  margin-bottom: 0;
}

.wl-count {
  font-weight: 400;
  color: var(--text-muted);
  font-size: 0.9rem;
}

/* ─── Add row ─── */
.wl-add-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.wl-autocomplete {
  flex: 1;
  position: relative;
}

.wl-input {
  width: 100%;
  padding-right: 32px;
}

.wl-spinner {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: wl-spin 0.6s linear infinite;
}

@keyframes wl-spin {
  to { transform: translateY(-50%) rotate(360deg); }
}

.wl-verified {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--up-color, #2D7A3A);
  font-weight: bold;
  font-size: 16px;
}

/* ─── Suggestions dropdown ─── */
.wl-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 100;
  margin-top: 4px;
  max-height: 260px;
  overflow-y: auto;
  list-style: none;
  padding: 6px;
  border: 1px solid var(--glass-border);
  background: rgba(30, 30, 30, 0.92);
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
}

html:not(.dark) .wl-suggestions {
  background: rgba(250, 246, 236, 0.92);
}

.wl-suggestion-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.wl-suggestion-item:hover,
.wl-suggestion-item.highlighted {
  background: var(--hover-bg, rgba(255,255,255,0.08));
}

.wl-sym {
  font-weight: 600;
  font-family: 'DM Mono', monospace;
  min-width: 70px;
  font-size: 0.95rem;
  color: var(--text);
}

.wl-name {
  flex: 1;
  font-size: 0.85rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wl-exch {
  font-size: 0.72rem;
  flex-shrink: 0;
}

/* ─── Feedback message ─── */
.wl-msg {
  margin-top: 8px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
}

.wl-msg-success {
  background: rgba(45, 122, 58, 0.12);
  color: var(--up-color, #2D7A3A);
}

.wl-msg-error {
  background: rgba(181, 50, 48, 0.12);
  color: var(--down-color, #B53230);
}

.wl-msg-warn {
  background: rgba(200, 150, 30, 0.12);
  color: #b8860b;
}

/* ─── Empty state ─── */
.state-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  color: var(--text-muted);
}

.wl-empty-state {
  text-align: center;
  padding: 32px 16px;
}

.wl-empty-icon {
  font-size: 2rem;
}

.wl-empty-text {
  margin: 8px 0 4px;
  font-size: 0.95rem;
  color: var(--text-muted);
}

.wl-empty-hint {
  font-size: 0.82rem;
  color: var(--text-muted);
  opacity: 0.7;
}

/* ─── Ticker list ─── */
.wl-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.wl-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  transition: background 0.15s;
}

.wl-row.pinned-row {
  background: rgba(241, 99, 99, 0.06);
  border: 1px solid rgba(241, 99, 99, 0.2);
  box-shadow: inset 3px 0 0 var(--primary, #ff0000);
}

.wl-row:hover {
  background: var(--hover-bg, rgba(255,255,255,0.06));
}

.wl-row.pinned-row:hover {
  background: rgba(241, 99, 99, 0.1);
  border-color: rgba(241, 99, 99, 0.3);
}

.wl-row-left {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex: 1;
}

.wl-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  color: #fff;
  flex-shrink: 0;
}

.wl-row-info {
  display: flex;
  flex-direction: column;
}

.wl-row-symbol {
  font-weight: 600;
  font-family: 'DM Mono', monospace;
  font-size: 0.95rem;
}

.wl-row-name {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.wl-row-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.wl-row-exchange {
  font-size: 0.72rem;
}

.btn-remove {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 4px 8px;
  border-radius: 50%;
  color: var(--text-muted);
  line-height: 1;
  transition: background 0.15s, color 0.15s;
}

.btn-remove:hover {
  background: rgba(181,50,48,0.15);
  color: var(--down-color, #B53230);
}

.btn-pin {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 3px 6px;
  border-radius: 4px;
  color: var(--text-muted);
  opacity: 0.25;
  transition: opacity 0.15s, transform 0.15s, color 0.15s;
}

.btn-pin:hover {
  opacity: 0.55;
  color: var(--text);
}

.btn-pin.pinned {
  opacity: 1;
  color: var(--primary, #ff0000);
  filter: drop-shadow(0 0 3px rgba(99,102,241,0.4));
}

.btn-pin.loading {
  opacity: 1;
  cursor: wait;
  animation: pin-pulse 0.8s ease-in-out infinite;
}

@keyframes pin-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* ─── Transitions ─── */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
