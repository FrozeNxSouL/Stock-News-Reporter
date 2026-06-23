import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import TickerDetail from '../components/TickerDetail.vue'
import NewsFeed from '../components/NewsFeed.vue'
import Settings from '../components/Settings.vue'
import Login from '../components/auth/Login.vue'
import Signup from '../components/auth/Signup.vue'
import UserProfile from '../components/auth/UserProfile.vue'
import Watchlist from '../components/Watchlist.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/ticker/:symbol',
    name: 'TickerDetail',
    component: TickerDetail,
    props: true,
  },
  {
    path: '/news',
    name: 'NewsFeed',
    component: NewsFeed,
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { guest: true },
  },
  {
    path: '/signup',
    name: 'Signup',
    component: Signup,
    meta: { guest: true },
  },
  {
    path: '/profile',
    name: 'UserProfile',
    component: UserProfile,
    meta: { requiresAuth: true },
  },
  {
    path: '/watchlist',
    name: 'Watchlist',
    component: Watchlist,
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ---- Navigation guards ----
router.beforeEach((to, from, next) => {
  const TOKEN_KEY = 'auth_tokens'
  let token = null
  try {
    const raw = localStorage.getItem(TOKEN_KEY)
    token = raw ? JSON.parse(raw).access : null
  } catch {
    token = null
  }

  // Protected routes: require auth
  if (to.meta.requiresAuth && !token) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  // Guest routes (login/signup): redirect if already authenticated
  if (to.meta.guest && token) {
    return next({ name: 'Dashboard' })
  }

  next()
})

export default router
