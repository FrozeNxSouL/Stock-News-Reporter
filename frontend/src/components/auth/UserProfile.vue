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

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 680px;
  margin: 0 auto;
  width: 100%;
}

.profile-page > h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.profile-card,
.watchlist-card,
.danger-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--r-lg);
  box-shadow: var(--glass-shadow);
  padding: 26px 28px;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}

.avatar {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--brand-caramel), var(--brand-espresso));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
  color: #FAF4EA;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(107, 63, 31, 0.30);
}

.profile-info h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.profile-email {
  display: block;
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 3px;
}

.profile-joined {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
  opacity: 0.7;
}

.auth-error {
  background: var(--down-bg);
  border: 1px solid rgba(181, 50, 48, 0.30);
  border-radius: var(--r-sm);
  padding: 11px 14px;
  font-size: 13px;
  color: var(--down-color);
  margin-bottom: 16px;
}

.auth-success {
  background: var(--up-bg);
  border: 1px solid rgba(45, 122, 58, 0.30);
  border-radius: var(--r-sm);
  padding: 11px 14px;
  font-size: 13px;
  color: var(--up-color);
  margin-bottom: 16px;
}

.profile-form {
  display: flex;
  flex-direction: column;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.form-group label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.form-row {
  display: flex;
  gap: 8px;
}

.form-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--input-border);
  border-radius: var(--r-sm);
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 14px;
  font-family: 'Outfit', sans-serif;
  transition: var(--trans-fast);
  outline: none;
}

.form-input:focus {
  border-color: var(--input-focus);
  box-shadow: 0 0 0 3px rgba(160, 98, 42, 0.15);
}

.ticker-input {
  text-transform: uppercase;
  font-family: 'DM Mono', monospace;
}

.watchlist-card h3,
.danger-card h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.section-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 16px;
  line-height: 1.5;
}

.add-ticker-form {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.watchlist-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.watchlist-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--r-pill);
  padding: 5px 5px 5px 14px;
  transition: var(--trans-fast);
}

.watchlist-pill:hover {
  border-color: var(--brand-caramel);
}

.pill-link {
  color: var(--brand-caramel);
  text-decoration: none;
  font-size: 13px;
  font-weight: 700;
  font-family: 'DM Mono', monospace;
}

.pill-remove {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 50%;
  transition: var(--trans-fast);
}

.pill-remove:hover {
  color: var(--down-color);
  background: var(--down-bg);
}

.empty-watchlist {
  text-align: center;
  padding: 28px 16px;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.6;
}

.hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
  opacity: 0.7;
}

.btn {
  padding: 8px 18px;
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  font-size: 13px;
  font-weight: 600;
  font-family: 'Outfit', sans-serif;
  cursor: pointer;
  transition: var(--trans-fast);
  background: transparent;
  color: var(--text-primary);
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, var(--brand-caramel), var(--brand-espresso));
  border-color: transparent;
  color: #FAF4EA;
  box-shadow: 0 2px 8px rgba(107, 63, 31, 0.25);
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--brand-latte), var(--brand-caramel));
}

.btn-secondary {
  background: var(--glass-bg);
  border-color: var(--border-strong);
  color: var(--text-secondary);
}

.btn-secondary:hover:not(:disabled) {
  border-color: var(--brand-caramel);
  color: var(--brand-caramel);
}

.btn-danger {
  color: var(--down-color);
  border-color: rgba(181, 50, 48, 0.30);
}

.btn-danger:hover {
  background: var(--down-bg);
  border-color: var(--down-color);
}

@media (max-width: 600px) {
  .profile-card, .watchlist-card, .danger-card {
    padding: 18px 16px;
  }
}
</style>


.profile-page > h2 {
  font-size: 24px;
  font-weight: 700;
}

.profile-card,
.watchlist-card,
.danger-card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 24px;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #30363d;
}

.avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1f6feb, #58a6ff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.profile-info h3 {
  font-size: 18px;
  font-weight: 700;
}

.profile-email {
  display: block;
  font-size: 13px;
  color: #8b949e;
  margin-top: 2px;
}

.profile-joined {
  display: block;
  font-size: 11px;
  color: #484f58;
  margin-top: 2px;
}

.auth-error {
  background: rgba(218, 54, 51, 0.1);
  border: 1px solid rgba(218, 54, 51, 0.3);
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  color: #da3633;
  margin-bottom: 16px;
}

.auth-success {
  background: rgba(63, 185, 80, 0.1);
  border: 1px solid rgba(63, 185, 80, 0.3);
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  color: #3fb950;
  margin-bottom: 16px;
}

.profile-form {
  display: flex;
  flex-direction: column;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-row {
  display: flex;
  gap: 8px;
}

.form-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #30363d;
  border-radius: 8px;
  background: #0d1117;
  color: #e1e4e8;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #58a6ff;
}

.ticker-input {
  text-transform: uppercase;
  font-family: 'SF Mono', 'Fira Code', monospace;
}

.watchlist-card h3,
.danger-card h3 {
  font-size: 16px;
  margin-bottom: 8px;
}

.section-hint {
  font-size: 12px;
  color: #8b949e;
  margin-bottom: 16px;
}

.add-ticker-form {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.watchlist-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.watchlist-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 20px;
  padding: 4px 4px 4px 14px;
  transition: border-color 0.2s;
}

.watchlist-pill:hover {
  border-color: #58a6ff;
}

.pill-link {
  color: #58a6ff;
  text-decoration: none;
  font-size: 13px;
  font-weight: 700;
  font-family: 'SF Mono', monospace;
}

.pill-remove {
  background: none;
  border: none;
  color: #484f58;
  cursor: pointer;
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 50%;
  transition: all 0.2s;
}

.pill-remove:hover {
  color: #da3633;
  background: rgba(218, 54, 51, 0.1);
}

.empty-watchlist {
  text-align: center;
  padding: 24px 16px;
  color: #8b949e;
  font-size: 13px;
}

.hint {
  font-size: 12px;
  color: #484f58;
  margin-top: 6px;
}

.btn {
  padding: 8px 16px;
  border: 1px solid #30363d;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  background: transparent;
  color: #e1e4e8;
  white-space: nowrap;
}

.btn-primary {
  background: linear-gradient(135deg, #238636, #2ea043);
  border-color: #2ea043;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #2ea043, #3fb950);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #21262d;
}

.btn-secondary:hover:not(:disabled) {
  background: #30363d;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-danger {
  color: #da3633;
  border-color: rgba(218, 54, 51, 0.3);
}

.btn-danger:hover {
  background: rgba(218, 54, 51, 0.1);
  border-color: #da3633;
}
</style>
