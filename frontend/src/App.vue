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
