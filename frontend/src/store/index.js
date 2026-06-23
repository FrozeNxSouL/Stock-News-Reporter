import { defineStore } from 'pinia'
import api from '../services/api.js'
import { useAuthStore } from './auth.js'

export const useStockStore = defineStore('stock', {
  state: () => ({
    news: [],
    stockPrices: {},
    _priceTimestamps: {},   // ticker → ISO timestamp of last fetch
    sentimentSummary: {},
    overviews: {},
    loading: false,
    newsLoading: false,
    error: null,
    refreshInterval: null,
  }),

  getters: {
    getStockPrice: (state) => (symbol) => {
      return state.stockPrices[symbol] || null
    },

    getOverview: (state) => (symbol) => {
      return state.overviews[symbol] || null
    },
  },

  actions: {
    /** Reset ALL state — called on logout */
    clearAll() {
      this.news = []
      this.stockPrices = {}
      this._priceTimestamps = {}
      this.sentimentSummary = {}
      this.overviews = {}
      this.loading = false
      this.newsLoading = false
      this.error = null
      this.stopAutoRefresh()
    },

    // ---- News ----
    async fetchNews(params = {}) {
      this.newsLoading = true
      try {
        const response = await api.get('/news/', { params })
        this.news = response.data.items || []
        return response.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to fetch news'
        console.error('Fetch news error:', err)
        return null
      } finally {
        this.newsLoading = false
      }
    },

    // ---- Stock Prices ----
    async fetchStockPrice(ticker, forceRefresh = false) {
      // Return cached data if < 5 min old (unless forced)
      const cacheAge = this._priceTimestamps[ticker]
        ? Date.now() - new Date(this._priceTimestamps[ticker]).getTime()
        : Infinity
      if (!forceRefresh && cacheAge < 300_000 && this.stockPrices[ticker]) {
        return this.stockPrices[ticker]
      }

      try {
        const response = await api.get(`/stocks/${ticker}`)
        this.stockPrices[ticker] = response.data
        this._priceTimestamps[ticker] = new Date().toISOString()
        return response.data
      } catch (err) {
        console.error(`Fetch price error for ${ticker}:`, err)
        return this.stockPrices[ticker] || null
      }
    },

    async fetchMultiplePrices(tickers) {
      if (!tickers.length) return
      try {
        const response = await api.get('/stocks/', {
          params: { tickers: tickers.join(',') }
        })
        const prices = response.data.prices || []
        const now = new Date().toISOString()
        prices.forEach(p => {
          this.stockPrices[p.ticker] = p
          this._priceTimestamps[p.ticker] = now
        })
        return prices
      } catch (err) {
        console.error('Fetch multiple prices error:', err)
        return []
      }
    },

    // ---- Analysis ----
    async fetchOverview(ticker, days = 7) {
      try {
        const response = await api.get(`/analysis/overview/${ticker}`, {
          params: { days }
        })
        this.overviews[ticker] = response.data
        return response.data
      } catch (err) {
        console.error(`Fetch overview error for ${ticker}:`, err)
        return null
      }
    },

    async fetchSentiment(ticker, days = 7) {
      try {
        const response = await api.get(`/analysis/sentiment/${ticker}`, {
          params: { days }
        })
        this.sentimentSummary[ticker] = response.data
        return response.data
      } catch (err) {
        console.error(`Fetch sentiment error for ${ticker}:`, err)
        return null
      }
    },

    // ---- Ticker Search / Lookup ----
    async searchTickers(query) {
      if (!query || query.trim().length < 1) return []
      try {
        const response = await api.get('/stocks/search', { params: { q: query } })
        return response.data.results || []
      } catch (err) {
        console.error('Search tickers error:', err)
        return []
      }
    },

    async lookupTicker(ticker) {
      try {
        const response = await api.get(`/stocks/lookup/${ticker}`)
        return response.data
      } catch {
        return null
      }
    },

    // ---- Auto refresh ----
    startAutoRefresh(intervalMs = 60000) {
      this.stopAutoRefresh()
      this.refreshInterval = setInterval(async () => {
        const authStore = useAuthStore()
        const active = authStore.isAuthenticated ? authStore.watchlist : []
        if (active.length > 0) {
          await this.fetchMultiplePrices(active)
        }
      }, intervalMs)
    },

    stopAutoRefresh() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
        this.refreshInterval = null
      }
    },
  },
})
