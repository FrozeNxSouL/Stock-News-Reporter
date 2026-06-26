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
            <span>Dashboard</span>
          </router-link>
          <router-link to="/news" class="nav-link" active-class="active" id="nav-news">
            <span>News Feed</span>
          </router-link>
        </nav>

        <!-- Right Controls -->
        <div class="header-right">
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
              <div v-if="userMenuOpen" class="user-dropdown glass-card" @click.stop>
                <router-link to="/profile" class="dropdown-item" @click="userMenuOpen = false" id="dropdown-profile">
                  <span class="dd-icon">◎</span> Profile
                </router-link>
                <router-link to="/watchlist" class="dropdown-item" @click="userMenuOpen = false" id="dropdown-watchlist">
                  <span class="dd-icon">◉</span> Watchlist
                </router-link>
                <router-link to="/settings" class="dropdown-item" @click="userMenuOpen = false" id="dropdown-settings">
                  <span class="dd-icon">◎</span> Settings
                </router-link>
                <div class="dropdown-divider"></div>
                <button class="dropdown-item logout-btn" @click="handleLogout" id="dropdown-logout">
                  <span class="dd-icon">⇤</span> Sign Out
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
      <div v-if="!authStore.initialized" class="state-container" style="padding-top:60px">
        <div class="spinner"></div>
      </div>
      <router-view v-else v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </router-view>
    </main>

    <!-- Mobile bottom nav -->
    <nav class="mobile-nav" aria-label="Mobile navigation">
      <router-link to="/" class="mobile-nav-item" exact-active-class="active" id="mobile-nav-dashboard">
        <span class="mobile-nav-icon">▦</span>
        <span class="mobile-nav-label">MARKET</span>
      </router-link>
      <router-link to="/news" class="mobile-nav-item" active-class="active" id="mobile-nav-news">
        <span class="mobile-nav-icon">☰</span>
        <span class="mobile-nav-label">NEWS</span>
      </router-link>
      <router-link v-if="authStore.isAuthenticated" to="/watchlist" class="mobile-nav-item" active-class="active" id="mobile-nav-watchlist">
        <span class="mobile-nav-icon">◉</span>
        <span class="mobile-nav-label">PORTFOLIO</span>
      </router-link>
      <router-link
        v-if="authStore.isAuthenticated"
        to="/profile"
        class="mobile-nav-item"
        active-class="active"
        id="mobile-nav-profile"
      >
        <span class="mobile-nav-icon">◎</span>
        <span class="mobile-nav-label">PROFILE</span>
      </router-link>
      <router-link v-else to="/login" class="mobile-nav-item" active-class="active" id="mobile-nav-login">
        <span class="mobile-nav-icon">◎</span>
        <span class="mobile-nav-label">SIGN IN</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './store/auth.js'

const authStore = useAuthStore()
const router = useRouter()

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

onMounted(async () => {
  await authStore.init()
  document.addEventListener('click', closeUserMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeUserMenu)
})
</script>
