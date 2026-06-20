import { defineStore } from 'pinia'
import api from '../services/api.js'

const TOKEN_KEY = 'auth_tokens'
const USER_KEY = 'auth_user'

function persistTokens(access, refresh) {
  localStorage.setItem(TOKEN_KEY, JSON.stringify({ access, refresh }))
}

function loadTokens() {
  try {
    const raw = localStorage.getItem(TOKEN_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: null,
    refreshToken: null,
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken && !!state.user,
    watchlist: (state) => state.user?.watchlist || [],
  },

  actions: {
    /** Initialize from persisted tokens (called on app mount) */
    init() {
      const tokens = loadTokens()
      if (tokens?.access) {
        this.accessToken = tokens.access
        this.refreshToken = tokens.refresh
        // Fetch user profile to validate token
        return this.fetchProfile()
      }
    },

    /** Sign up a new user */
    async signup({ email, username, password }) {
      this.loading = true
      this.error = null
      try {
        const res = await api.post('/auth/signup', { email, username, password })
        const { access_token, refresh_token } = res.data
        this.accessToken = access_token
        this.refreshToken = refresh_token
        persistTokens(access_token, refresh_token)
        await this.fetchProfile()
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Signup failed'
        throw err
      } finally {
        this.loading = false
      }
    },

    /** Log in */
    async login({ email, password }) {
      this.loading = true
      this.error = null
      try {
        const res = await api.post('/auth/login', { email, password })
        const { access_token, refresh_token } = res.data
        this.accessToken = access_token
        this.refreshToken = refresh_token
        persistTokens(access_token, refresh_token)
        await this.fetchProfile()
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Login failed'
        throw err
      } finally {
        this.loading = false
      }
    },

    /** Log out */
    logout() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      clearTokens()
    },

    /** Fetch authenticated user profile */
    async fetchProfile() {
      try {
        const res = await api.get('/auth/me')
        this.user = res.data
        localStorage.setItem(USER_KEY, JSON.stringify(res.data))
        return res.data
      } catch {
        // Token expired or invalid — clear auth state
        this.logout()
        return null
      }
    },

    /** Refresh the access token using the refresh token */
    async refreshAccessToken() {
      if (!this.refreshToken) {
        this.logout()
        throw new Error('No refresh token')
      }
      try {
        const res = await api.post('/auth/refresh', {
          refresh_token: this.refreshToken,
        })
        this.accessToken = res.data.access_token
        this.refreshToken = res.data.refresh_token
        persistTokens(this.accessToken, this.refreshToken)
        return this.accessToken
      } catch {
        this.logout()
        throw new Error('Token refresh failed')
      }
    },

    /** Update user profile fields */
    async updateProfile(updates) {
      this.loading = true
      this.error = null
      try {
        const res = await api.patch('/auth/me', updates)
        this.user = res.data
        localStorage.setItem(USER_KEY, JSON.stringify(res.data))
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Profile update failed'
        throw err
      } finally {
        this.loading = false
      }
    },

    /** Sync a ticker in/out of user watchlist */
    async toggleWatchlistTicker(symbol) {
      if (!this.user) return
      const current = [...(this.user.watchlist || [])]
      const idx = current.indexOf(symbol.toUpperCase())
      if (idx >= 0) {
        current.splice(idx, 1)
      } else {
        current.push(symbol.toUpperCase())
      }
      await this.updateProfile({ watchlist: current })
    },

    /** Check if a ticker is in user watchlist */
    isInWatchlist(symbol) {
      return (this.user?.watchlist || []).includes(symbol?.toUpperCase())
    },
  },
})
