import { defineStore } from 'pinia'
import { computed, ref, readonly } from 'vue'

const API_BASE_URL = import.meta.env.VITE_API_URL

export interface User{
  id: string;
  full_name: string;
  email: string;
}

export interface LoginCredentials {
  username: string; // This will be the username for FastAPI
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface ActionResult {
  success: boolean;
  error?: string;
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed<boolean>(() => !!user.value && !!token.value)
  const isLoading = computed<boolean>(() => loading.value)
  const currentUser = computed<User | null>(() => user.value)

  // Actions

  async function login(credentials: LoginCredentials): Promise<ActionResult> {
    loading.value = true
    error.value = null

    try {
      // Prepare form data for FastAPI OAuth2PasswordRequestForm
      const formData = new FormData()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)

      // Call FastAPI login endpoint
      const tokenResponse = await fetch(`${API_BASE_URL}/api/auth/login/access-token`, {
        method: 'POST',
        body: formData,
      })

      if (!tokenResponse.ok) {
        const errorData = await tokenResponse.json()
        throw new Error(errorData.detail || 'Login failed')
      }

      const tokenData: TokenResponse = await tokenResponse.json()

      // Store the token
      token.value = tokenData.access_token

      // Fetch user data using access token
      const userResponse = await fetch('/api/users/me', {
        headers: {
          'Authorization': `Bearer ${tokenData.access_token}`,
          'Content-Type' : 'application/json'
        }
      })

      if (!userResponse.ok) {
        throw new Error('Failed to fetch user data')
      }

      const userData: User = await userResponse.json()
      user.value = userData

      // Store in local storage
      try {
        localStorage.setItem('auth_token', tokenData.access_token)
        localStorage.setItem('token_type', tokenData.token_type)
        localStorage.setItem('auth_user', JSON.stringify(userData))
      } catch (storageError) {
        console.warn('Failed to store auth data: ', storageError)
      }

      return { success: true }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed'
      error.value = errorMessage
      return { success: false, error: errorMessage }
    } finally {
      loading.value = false
    }
  }

  async function logout(): Promise<ActionResult> {
    loading.value = true

    try {
      // Optional: Call FastAPI logout endpoint if you have one
      // if (token.value) {
      //   try {
      //     await fetch('/api/auth/logout', {
      //       method: 'POST',
      //       headers: {
      //         'Authorization': `Bearer ${token.value}`,
      //         'Content-Type': 'application/json'
      //       }
      //     });
      //   } catch (logoutError) {
      //     console.warn('Server logout failed:', logoutError);
      //   }
      // }

      // Clear state
      user.value = null
      token.value = null
      error.value = null

      // Clear local storage
      const keysToRemove: string[] = ['auth_token', 'token_type', 'auth_user']
      keysToRemove.forEach(key => {
        localStorage.removeItem(key)
      })

      return { success: true }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Logout failed'
      error.value = errorMessage
      return { success: false, error: errorMessage }
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    user: readonly(user),
    token: readonly(token),
    loading: readonly(loading),
    error: readonly(error),
    // Actions
    login,
    logout,
  };
});
