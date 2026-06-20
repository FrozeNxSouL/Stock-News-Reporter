import { defineStore } from 'pinia'
import api from '../services/api.js'
import { useAuthStore } from './auth.js'

export const useStockStore = defineStore('stock', {
  state: () => ({
    tickers: [],
    selectedTickers: [],
    news: [],
    analyses: {},
    stockPrices: {},
    sentimentSummary: {},
    overviews: {},
    loading: false,
    newsLoading: false,
    error: null,
    refreshInterval: null,
  }),

  getters: {
    getTickerBySymbol: (state) => (symbol) => {
      return state.tickers.find(t => t.symbol === symbol)
    },
    getStockPrice: (state) => (symbol) => {
      return state.stockPrices[symbol] || null
    },
    getOverview: (state) => (symbol) => {
      return state.overviews[symbol] || null
    },
  },

  actions: {
    // ---- Tickers ----
    async fetchTickers() {
      this.loading = true
      try {
        const response = await api.get('/tickers/')
        this.tickers = response.data
        // Sync selected tickers with user watchlist if authenticated
        const authStore = useAuthStore()
        if (authStore.isAuthenticated && authStore.watchlist.length > 0) {
          this.selectedTickers = authStore.watchlist
        } else {
          this.selectedTickers = this.tickers.filter(t => t.active).map(t => t.symbol)
        }
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to fetch tickers'
        console.error('Fetch tickers error:', err)
      } finally {
        this.loading = false
      }
    },

    async addTicker(symbol) {
      try {
        const response = await api.post('/tickers/', { symbol })
        this.tickers.push(response.data)
        return response.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to add ticker'
        throw err
      }
    },

    async removeTicker(symbol) {
      try {
        await api.delete(`/tickers/${symbol}`)
        this.tickers = this.tickers.filter(t => t.symbol !== symbol)
        delete this.stockPrices[symbol]
        delete this.overviews[symbol]
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to remove ticker'
        throw err
      }
    },

    async addDefaultTickers() {
      try {
        await api.post('/tickers/defaults')
        await this.fetchTickers()
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to add defaults'
      }
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

    async triggerFetch() {
      try {
        const response = await api.get('/news/fetch')
        return response.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to trigger fetch'
        throw err
      }
    },

    // ---- Stock Prices ----
    async fetchStockPrice(ticker) {
      try {
        const response = await api.get(`/stocks/${ticker}`)
        this.stockPrices[ticker] = response.data
        return response.data
      } catch (err) {
        console.error(`Fetch price error for ${ticker}:`, err)
        return null
      }
    },

    async fetchMultiplePrices(tickers) {
      if (!tickers.length) return
      try {
        const response = await api.get('/stocks/', {
          params: { tickers: tickers.join(',') }
        })
        const prices = response.data.prices || []
        prices.forEach(p => {
          this.stockPrices[p.ticker] = p
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

    // ---- Auto refresh ----
    startAutoRefresh(intervalMs = 60000) {
      this.stopAutoRefresh()
      this.refreshInterval = setInterval(async () => {
        const active = this.selectedTickers
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
