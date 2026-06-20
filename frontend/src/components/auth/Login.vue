<template>
  <div class="auth-page">
    <!-- Decorative background orbs -->
    <div class="auth-orb auth-orb-1" aria-hidden="true"></div>
    <div class="auth-orb auth-orb-2" aria-hidden="true"></div>

    <div class="auth-card glass-card">
      <div class="auth-header">
        <div class="auth-logo">
          <span class="auth-logo-icon">☕</span>
        </div>
        <h1 class="auth-title">Welcome Back</h1>
        <p class="auth-subtitle">Sign in to StockBrew Analyzer</p>
      </div>

      <Transition name="fade">
        <div v-if="authStore.error" class="auth-error" role="alert">
          ⚠️ {{ authStore.error }}
        </div>
      </Transition>

      <form @submit.prevent="handleLogin" class="auth-form" novalidate>
        <div class="form-group">
          <label for="login-email" class="form-label">Email</label>
          <input
            id="login-email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            required
            autocomplete="email"
            class="form-input"
            aria-required="true"
          />
        </div>

        <div class="form-group">
          <label for="login-password" class="form-label">Password</label>
          <input
            id="login-password"
            v-model="password"
            type="password"
            placeholder="Your password"
            required
            autocomplete="current-password"
            class="form-input"
            aria-required="true"
          />
        </div>

        <button
          type="submit"
          class="btn btn-primary btn-full"
          id="btn-login-submit"
          :disabled="authStore.loading || !isFormValid"
        >
          {{ authStore.loading ? '⏳ Signing in…' : 'Sign In' }}
        </button>
      </form>

      <div class="auth-footer">
        Don't have an account?
        <router-link to="/signup" class="auth-link" id="link-signup">Create one →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../store/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')

const isFormValid = computed(() =>
  email.value.trim() && password.value.length > 0
)

async function handleLogin() {
  if (!isFormValid.value) return
  try {
    await authStore.login({
      email: email.value.trim(),
      password: password.value,
    })
    router.push('/')
  } catch {
    // error already set in store
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 64px);
  padding: 32px 16px;
  position: relative;
  overflow: hidden;
}

/* Decorative orbs */
.auth-orb {
  position: fixed;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
}

.auth-orb-1 {
  width: 480px;
  height: 480px;
  background: radial-gradient(circle, rgba(160,98,42,0.22) 0%, transparent 65%);
  top: -120px;
  right: -80px;
}

.auth-orb-2 {
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(10,41,71,0.20) 0%, transparent 65%);
  bottom: -80px;
  left: -60px;
}

/* Card */
.auth-card {
  width: 100%;
  max-width: 440px;
  padding: 44px 40px;
  position: relative;
  z-index: 1;
}

/* Header */
.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-logo {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--brand-caramel), var(--brand-espresso));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin: 0 auto 16px;
  box-shadow: 0 4px 16px rgba(107, 63, 31, 0.30);
}

.auth-title {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 6px;
  letter-spacing: -0.3px;
}

.auth-subtitle {
  font-size: 14px;
  color: var(--text-muted);
}

/* Error */
.auth-error {
  background: var(--down-bg);
  border: 1px solid rgba(181, 50, 48, 0.30);
  border-radius: var(--r-sm);
  padding: 11px 14px;
  font-size: 13px;
  color: var(--down-color);
  margin-bottom: 20px;
}

/* Form */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-bottom: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.form-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.btn-full {
  width: 100%;
  padding: 13px;
  font-size: 15px;
  border-radius: var(--r-md);
}

/* Footer */
.auth-footer {
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}

.auth-link {
  color: var(--brand-caramel);
  text-decoration: none;
  font-weight: 700;
  margin-left: 4px;
  transition: var(--trans-fast);
}

.auth-link:hover {
  color: var(--brand-espresso);
  text-decoration: underline;
}

/* Fade transition */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 480px) {
  .auth-card {
    padding: 32px 20px;
  }
}
</style>
