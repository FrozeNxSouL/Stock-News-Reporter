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
          {{ authStore.error }}
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
