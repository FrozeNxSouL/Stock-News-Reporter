<template>
  <div class="app" :class="{ 'dark-mode': isDark }">
    <!-- Desktop Header -->
    <header class="app-header">
      <div class="header-inner">
        <!-- Logo -->
        <router-link to="/" class="logo" id="logo-link">
          <div class="logo-icon-wrap">
            <span class="logo-icon">☕</span>
          </div>
          <div class="logo-text">
            <span class="logo-title">StockBrew</span>
            <span class="logo-sub">News Analyzer</span>
          </div>
        </router-link>

        <!-- Desktop Nav -->
        <nav class="nav-links" aria-label="Main navigation">
          <router-link to="/" class="nav-link" exact-active-class="active" id="nav-dashboard">
            <span class="nav-icon">📊</span>
            <span>Dashboard</span>
          </router-link>
          <router-link to="/news" class="nav-link" active-class="active" id="nav-news">
            <span class="nav-icon">📰</span>
            <span>News Feed</span>
          </router-link>
          <router-link v-if="authStore.isAuthenticated" to="/profile" class="nav-link" active-class="active" id="nav-profile">
            <span class="nav-icon">👤</span>
            <span>Profile</span>
          </router-link>
          <router-link to="/settings" class="nav-link" active-class="active" id="nav-settings">
            <span class="nav-icon">⚙️</span>
            <span>Settings</span>
          </router-link>
        </nav>

        <!-- Right Controls -->
        <div class="header-right">
          <!-- Connection status -->
          <div class="header-status" :title="backendConnected ? 'Backend connected' : 'Backend disconnected'">
            <span class="status-dot" :class="{ connected: backendConnected }"></span>
            <span class="status-text">{{ backendConnected ? 'Live' : 'Offline' }}</span>
          </div>

          <!-- Dark / Light toggle -->
          <button
            class="theme-toggle"
            @click="toggleTheme"
            :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
            id="theme-toggle-btn"
          >
            <span class="theme-icon">{{ isDark ? '☀️' : '🌙' }}</span>
          </button>

          <!-- Authenticated user menu -->
          <div v-if="authStore.isAuthenticated" class="user-menu" id="user-menu">
            <button class="user-btn" @click.stop="toggleUserMenu" id="user-menu-btn">
              <span class="user-avatar">{{ authStore.user?.username?.[0]?.toUpperCase() }}</span>
              <span class="user-name">{{ authStore.user?.username }}</span>
              <span class="user-arrow" :class="{ open: userMenuOpen }">▾</span>
            </button>
            <Transition name="dropdown">
              <div v-if="userMenuOpen" class="user-dropdown glass-card">
                <router-link to="/profile" class="dropdown-item" @click="userMenuOpen = false" id="dropdown-profile">
                  <span>👤</span> View Profile
                </router-link>
                <div class="dropdown-divider"></div>
                <button class="dropdown-item logout-btn" @click="handleLogout" id="dropdown-logout">
                  <span>🚪</span> Sign Out
                </button>
              </div>
            </Transition>
          </div>

          <!-- Guest buttons -->
          <template v-else>
            <router-link to="/login" class="btn btn-secondary btn-sm" id="nav-signin">Sign In</router-link>
            <router-link to="/signup" class="btn btn-primary btn-sm" id="nav-signup">Sign Up</router-link>
          </template>
        </div>
      </div>
    </header>

    <!-- Page content -->
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </router-view>
    </main>

    <!-- Mobile bottom nav -->
    <nav class="mobile-nav" aria-label="Mobile navigation">
      <router-link to="/" class="mobile-nav-item" exact-active-class="active" id="mobile-nav-dashboard">
        <span class="mobile-nav-icon">📊</span>
        <span class="mobile-nav-label">Market</span>
      </router-link>
      <router-link to="/news" class="mobile-nav-item" active-class="active" id="mobile-nav-news">
        <span class="mobile-nav-icon">📰</span>
        <span class="mobile-nav-label">News</span>
      </router-link>
      <router-link to="/settings" class="mobile-nav-item" active-class="active" id="mobile-nav-settings">
        <span class="mobile-nav-icon">⚙️</span>
        <span class="mobile-nav-label">Settings</span>
      </router-link>
      <router-link
        v-if="authStore.isAuthenticated"
        to="/profile"
        class="mobile-nav-item"
        active-class="active"
        id="mobile-nav-profile"
      >
        <span class="mobile-nav-icon">👤</span>
        <span class="mobile-nav-label">Profile</span>
      </router-link>
      <router-link v-else to="/login" class="mobile-nav-item" active-class="active" id="mobile-nav-login">
        <span class="mobile-nav-icon">🔑</span>
        <span class="mobile-nav-label">Sign In</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from './services/api.js'
import { useAuthStore } from './store/auth.js'

const authStore = useAuthStore()
const router = useRouter()

const backendConnected = ref(false)
const userMenuOpen = ref(false)
const isDark = ref(document.documentElement.classList.contains('dark'))

function toggleTheme() {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

function toggleUserMenu() {
  userMenuOpen.value = !userMenuOpen.value
}

function closeUserMenu() {
  if (userMenuOpen.value) userMenuOpen.value = false
}

function handleLogout() {
  userMenuOpen.value = false
  authStore.logout()
  router.push('/')
}

async function checkConnection() {
  try {
    const response = await api.get('/health')
    backendConnected.value = response.data.status === 'healthy'
  } catch {
    backendConnected.value = false
  }
}

onMounted(() => {
  checkConnection()
  setInterval(checkConnection, 30000)
  authStore.init()
  document.addEventListener('click', closeUserMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeUserMenu)
})
</script>

<style>
/* ---- Layout ---- */
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
  transition: background 0.35s ease;
}

/* ---- Header ---- */
.app-header {
  background: var(--nav-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 200;
  transition: background 0.35s ease, border-color 0.35s ease;
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  gap: 20px;
}

/* ---- Logo ---- */
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  flex-shrink: 0;
}

.logo-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--brand-caramel), var(--brand-espresso));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 2px 8px rgba(107, 63, 31, 0.30);
}

.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.logo-title {
  font-size: 17px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--brand-caramel), var(--brand-espresso));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.3px;
}

.logo-sub {
  font-size: 10px;
  color: var(--text-muted);
  font-weight: 500;
  letter-spacing: 0.4px;
  -webkit-text-fill-color: var(--text-muted);
}

/* ---- Desktop Nav ---- */
.nav-links {
  display: flex;
  gap: 4px;
  flex: 1;
  justify-content: center;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  text-decoration: none;
  color: var(--text-secondary);
  border-radius: var(--r-sm);
  font-size: 14px;
  font-weight: 500;
  transition: var(--trans-fast);
  border: 1px solid transparent;
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--nav-active-bg);
}

.nav-link.active {
  color: var(--nav-active-color);
  background: var(--nav-active-bg);
  border-color: var(--border);
  font-weight: 600;
}

.nav-icon {
  font-size: 15px;
}

/* ---- Right controls ---- */
.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

/* Status dot */
.header-status {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: default;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--down-color);
  transition: all 0.3s;
}

.status-dot.connected {
  background: var(--up-color);
  box-shadow: 0 0 6px rgba(45, 122, 58, 0.5);
}

.status-text {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}

/* Theme toggle */
.theme-toggle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--glass-bg);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: var(--trans-fast);
  backdrop-filter: var(--glass-blur);
}

.theme-toggle:hover {
  border-color: var(--brand-caramel);
  background: var(--nav-active-bg);
  transform: rotate(15deg) scale(1.08);
}

.theme-icon {
  line-height: 1;
  display: flex;
}

/* Btn sizes */
.btn-sm {
  padding: 6px 14px;
  font-size: 12px;
}

/* User menu */
.user-menu {
  position: relative;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 10px 5px 5px;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--border);
  border-radius: 20px;
  color: var(--text-primary);
  cursor: pointer;
  font-size: 13px;
  font-family: 'Outfit', sans-serif;
  transition: var(--trans-fast);
}

.user-btn:hover {
  border-color: var(--brand-caramel);
  background: var(--nav-active-bg);
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--brand-caramel), var(--brand-espresso));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #FAF4EA;
}

.user-name {
  max-width: 90px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.user-arrow {
  font-size: 10px;
  color: var(--text-muted);
  transition: transform 0.2s;
}

.user-arrow.open {
  transform: rotate(180deg);
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 185px;
  padding: 6px;
  z-index: 300;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 13px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  background: none;
  border: none;
  width: 100%;
  text-align: left;
  font-family: 'Outfit', sans-serif;
  transition: background 0.15s;
}

.dropdown-item:hover {
  background: var(--nav-active-bg);
}

.logout-btn {
  color: var(--down-color);
}

.logout-btn:hover {
  background: var(--down-bg);
}

.dropdown-divider {
  height: 1px;
  background: var(--border);
  margin: 4px 0;
}

/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
}

/* ---- Main ---- */
.app-main {
  flex: 1;
  padding: 28px 24px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  padding-bottom: 28px;
}

/* ---- Mobile Bottom Nav ---- */
.mobile-nav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 200;
  background: var(--nav-bg);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-top: 1px solid var(--border);
  padding: 8px 0 max(8px, env(safe-area-inset-bottom));
}

.mobile-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 6px 12px;
  text-decoration: none;
  color: var(--text-muted);
  flex: 1;
  transition: var(--trans-fast);
  border-radius: 10px;
  margin: 0 4px;
}

.mobile-nav-item:hover,
.mobile-nav-item.active {
  color: var(--nav-active-color);
}

.mobile-nav-item.active .mobile-nav-icon {
  transform: scale(1.15);
}

.mobile-nav-icon {
  font-size: 22px;
  transition: transform 0.2s;
}

.mobile-nav-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* ---- Responsive ---- */
@media (max-width: 768px) {
  .nav-links,
  .header-status,
  .status-text {
    display: none;
  }

  .header-inner {
    height: 56px;
  }

  .logo-sub {
    display: none;
  }

  .mobile-nav {
    display: flex;
  }

  .app-main {
    padding: 16px;
    padding-bottom: 88px; /* space for bottom nav */
  }
}
</style>
