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
