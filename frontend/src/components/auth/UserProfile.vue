<template>
  <div class="profile-page">
    <h2>👤 User Profile</h2>

    <!-- Profile Card -->
    <div class="profile-card">
      <div class="profile-header">
        <div class="avatar">{{ authStore.user?.username?.[0]?.toUpperCase() || '?' }}</div>
        <div class="profile-info">
          <h3>{{ authStore.user?.username }}</h3>
          <span class="profile-email">{{ authStore.user?.email }}</span>
          <span class="profile-joined">
            Member since {{ formatDate(authStore.user?.created_at) }}
          </span>
        </div>
      </div>

      <div v-if="authStore.error" class="auth-error">
        ⚠️ {{ authStore.error }}
      </div>

      <div v-if="successMsg" class="auth-success">
        ✅ {{ successMsg }}
      </div>

      <!-- Edit Username -->
      <form @submit.prevent="saveProfile" class="profile-form">
        <div class="form-group">
          <label for="edit-username">Username</label>
          <div class="form-row">
            <input
              id="edit-username"
              v-model="editUsername"
              type="text"
              pattern="^[a-zA-Z0-9_]+$"
              minlength="3"
              maxlength="30"
              class="form-input"
            />
            <button
              type="submit"
              class="btn btn-secondary"
              :disabled="!isUsernameChanged || authStore.loading"
            >
              {{ authStore.loading ? '⏳' : 'Save' }}
            </button>
          </div>
        </div>
      </form>
    </div>

    <!-- Watchlist Management -->
    <div class="watchlist-card">
      <h3>📋 My Watchlist</h3>
      <p class="section-hint">Tickers in your watchlist appear on your dashboard. Synced across sessions.</p>

      <!-- Add ticker -->
      <div class="add-ticker-form">
        <input
          v-model="newTicker"
          type="text"
          placeholder="Add ticker (e.g. AAPL)"
          class="form-input ticker-input"
          maxlength="5"
          @keyup.enter="addToWatchlist"
        />
        <button
          class="btn btn-primary"
          @click="addToWatchlist"
          :disabled="!newTicker.trim()"
        >+ Add</button>
      </div>

      <!-- Watchlist pills -->
      <div v-if="watchlist.length > 0" class="watchlist-pills">
        <span
          v-for="ticker in watchlist"
          :key="ticker"
          class="watchlist-pill"
        >
          <router-link :to="`/ticker/${ticker}`" class="pill-link">{{ ticker }}</router-link>
          <button class="pill-remove" @click="removeFromWatchlist(ticker)" title="Remove">✕</button>
        </span>
      </div>

      <div v-else class="empty-watchlist">
        <p>📭 Your watchlist is empty. Add tickers to get started.</p>
        <p class="hint">Click on any ticker pill on the dashboard to add it here!</p>
      </div>
    </div>

    <!-- Danger Zone -->
    <div class="danger-card">
      <h3>🚪 Account</h3>
      <button class="btn btn-danger" @click="handleLogout">
        Sign Out
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../store/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const editUsername = ref(authStore.user?.username || '')
const newTicker = ref('')
const successMsg = ref('')

const watchlist = computed(() => authStore.user?.watchlist || [])

const isUsernameChanged = computed(() =>
  editUsername.value.trim() !== authStore.user?.username
)

async function saveProfile() {
  successMsg.value = ''
  try {
    await authStore.updateProfile({ username: editUsername.value.trim() })
    successMsg.value = 'Username updated!'
    setTimeout(() => { successMsg.value = '' }, 3000)
  } catch {
    // error in store
  }
}

async function addToWatchlist() {
  const symbol = newTicker.value.trim().toUpperCase()
  if (!symbol) return

  if (watchlist.value.includes(symbol)) {
    newTicker.value = ''
    return
  }

  try {
    await authStore.updateProfile({
      watchlist: [...watchlist.value, symbol],
    })
    newTicker.value = ''
    successMsg.value = `${symbol} added to watchlist!`
    setTimeout(() => { successMsg.value = '' }, 2000)
  } catch {
    // error in store
  }
}

async function removeFromWatchlist(ticker) {
  try {
    await authStore.updateProfile({
      watchlist: watchlist.value.filter(t => t !== ticker),
    })
  } catch {
    // error in store
  }
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>
