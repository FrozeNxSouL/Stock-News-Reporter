<template>
  <div class="auth-page">
    <div class="auth-orb auth-orb-1" aria-hidden="true"></div>
    <div class="auth-orb auth-orb-2" aria-hidden="true"></div>

    <div class="auth-card glass-card">
      <div class="auth-header">
        <div class="auth-logo">
          <span class="auth-logo-icon">☕</span>
        </div>
        <h1 class="auth-title">Create Account</h1>
        <p class="auth-subtitle">Join StockBrew Analyzer to track your portfolio</p>
      </div>

      <Transition name="fade">
        <div v-if="authStore.error" class="auth-error" role="alert">
          ⚠️ {{ authStore.error }}
        </div>
      </Transition>

      <form @submit.prevent="handleSignup" class="auth-form" novalidate>
        <div class="form-group">
          <label for="signup-email" class="form-label">Email</label>
          <input
            id="signup-email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            required
            autocomplete="email"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="signup-username" class="form-label">Username</label>
          <input
            id="signup-username"
            v-model="username"
            type="text"
            placeholder="trading_ninja"
            required
            minlength="3"
            maxlength="30"
            pattern="^[a-zA-Z0-9_]+$"
            autocomplete="username"
            class="form-input"
          />
          <span class="form-hint">Letters, numbers, and underscores only</span>
        </div>

        <div class="form-group">
          <label for="signup-password" class="form-label">Password</label>
          <input
            id="signup-password"
            v-model="password"
            type="password"
            placeholder="Min 8 characters"
            required
            minlength="8"
            autocomplete="new-password"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="signup-confirm" class="form-label">Confirm Password</label>
          <input
            id="signup-confirm"
            v-model="confirmPassword"
            type="password"
            placeholder="Re-enter password"
            required
            autocomplete="new-password"
            class="form-input"
            :class="{ 'input-error': passwordMismatch }"
          />
          <span v-if="passwordMismatch" class="form-error">Passwords do not match</span>
        </div>

        <button
          type="submit"
          class="btn btn-primary btn-full"
          id="btn-signup-submit"
          :disabled="authStore.loading || passwordMismatch || !isFormValid"
        >
          {{ authStore.loading ? '⏳ Creating account…' : 'Create Account' }}
        </button>
      </form>

      <div class="auth-footer">
        Already have an account?
        <router-link to="/login" class="auth-link" id="link-login">Sign in →</router-link>
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
const username = ref('')
const password = ref('')
const confirmPassword = ref('')

const passwordMismatch = computed(() =>
  confirmPassword.value.length > 0 && password.value !== confirmPassword.value
)

const isFormValid = computed(() =>
  email.value.trim() &&
  username.value.trim().length >= 3 &&
  password.value.length >= 8 &&
  !passwordMismatch.value
)

async function handleSignup() {
  if (passwordMismatch.value || !isFormValid.value) return
  try {
    await authStore.signup({
      email: email.value.trim(),
      username: username.value.trim(),
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
  left: -80px;
}

.auth-orb-2 {
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(10,41,71,0.18) 0%, transparent 65%);
  bottom: -80px;
  right: -60px;
}

.auth-card {
  width: 100%;
  max-width: 460px;
  padding: 44px 40px;
  position: relative;
  z-index: 1;
}

.auth-header {
  text-align: center;
  margin-bottom: 28px;
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

.auth-logo-icon { line-height: 1; }

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

.auth-error {
  background: var(--down-bg);
  border: 1px solid rgba(181, 50, 48, 0.30);
  border-radius: var(--r-sm);
  padding: 11px 14px;
  font-size: 13px;
  color: var(--down-color);
  margin-bottom: 20px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
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

.form-input.input-error {
  border-color: var(--down-color);
}

.form-hint {
  font-size: 11px;
  color: var(--text-muted);
}

.form-error {
  font-size: 11px;
  color: var(--down-color);
  font-weight: 500;
}

.btn-full {
  width: 100%;
  padding: 13px;
  font-size: 15px;
  border-radius: var(--r-md);
}

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

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 480px) {
  .auth-card { padding: 28px 18px; }
}
</style>
