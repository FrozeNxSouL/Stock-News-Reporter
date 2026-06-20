import axios from 'axios'

const TOKEN_KEY = 'auth_tokens'

function getStoredAccessToken() {
  try {
    const raw = localStorage.getItem(TOKEN_KEY)
    if (!raw) return null
    return JSON.parse(raw).access || null
  } catch {
    return null
  }
}

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---- Request interceptor: attach JWT ----
api.interceptors.request.use(
  (config) => {
    const token = getStoredAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ---- Response interceptor: handle 401, auto-refresh ----
let isRefreshing = false
let failedQueue = []

function processQueue(error, token = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      resolve(token)
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response) {
      console.error(`API Error ${error.response.status}:`, error.response.data)

      // Attempt token refresh on 401 (exclude auth endpoints to avoid loops)
      if (
        error.response.status === 401 &&
        !originalRequest._retry &&
        !originalRequest.url.includes('/auth/')
      ) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject })
          })
            .then((token) => {
              originalRequest.headers.Authorization = `Bearer ${token}`
              return api(originalRequest)
            })
            .catch((err) => Promise.reject(err))
        }

        originalRequest._retry = true
        isRefreshing = true

        try {
          const tokens = JSON.parse(localStorage.getItem(TOKEN_KEY) || '{}')
          if (tokens.refresh) {
            const { data } = await axios.post('/api/auth/refresh', {
              refresh_token: tokens.refresh,
            })

            localStorage.setItem(
              TOKEN_KEY,
              JSON.stringify({
                access: data.access_token,
                refresh: data.refresh_token,
              }),
            )

            originalRequest.headers.Authorization = `Bearer ${data.access_token}`
            processQueue(null, data.access_token)
            return api(originalRequest)
          }
        } catch (refreshErr) {
          processQueue(refreshErr, null)
          // Clear auth state on refresh failure
          localStorage.removeItem(TOKEN_KEY)
          localStorage.removeItem('auth_user')
          // Redirect to login if we're not already there
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          return Promise.reject(refreshErr)
        } finally {
          isRefreshing = false
        }
      }
    } else if (error.request) {
      console.error('API No response:', error.message)
    } else {
      console.error('API Error:', error.message)
    }
    return Promise.reject(error)
  },
)

export default api
