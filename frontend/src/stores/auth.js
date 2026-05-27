import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  clearAuthSession,
  getStoredAccessToken,
  getStoredTokenType,
  getStoredUser,
  persistAuthSession,
} from '../utils/authStorage'
import { getApiBaseUrl } from '../utils/apiUrls'

const API_BASE_URL = getApiBaseUrl()

const decodeJwtPayload = (token) => {
  if (!token) {
    return null
  }

  try {
    const [, payload] = token.split('.')
    return JSON.parse(window.atob(payload))
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref('')
  const tokenType = ref('bearer')
  const user = ref(null)
  const profile = ref(null)
  const hasHydrated = ref(false)

  const tokenPayload = computed(() => decodeJwtPayload(accessToken.value))
  const isAuthenticated = computed(() => Boolean(accessToken.value))
  const roleId = computed(() => tokenPayload.value?.role_id ?? user.value?.role_id ?? null)
  const isAdmin = computed(() => user.value?.account_type === 'admin')

  const hydrate = () => {
    if (hasHydrated.value) {
      return
    }

    accessToken.value = getStoredAccessToken()
    tokenType.value = getStoredTokenType()
    user.value = getStoredUser()
    hasHydrated.value = true
  }

  const setSession = ({ accessToken: nextAccessToken, tokenType: nextTokenType = 'bearer', user: nextUser = null }) => {
    accessToken.value = nextAccessToken
    tokenType.value = nextTokenType
    user.value = nextUser
    persistAuthSession({
      accessToken: nextAccessToken,
      tokenType: nextTokenType,
      user: nextUser,
    })
  }

  const updateStoredUser = (nextUser) => {
    user.value = nextUser
    persistAuthSession({
      accessToken: accessToken.value,
      tokenType: tokenType.value,
      user: nextUser,
    })
  }

  const logout = () => {
    accessToken.value = ''
    tokenType.value = 'bearer'
    user.value = null
    profile.value = null
    clearAuthSession()
  }

  const fetchCurrentProfile = async () => {
    if (!accessToken.value) {
      return null
    }

    const response = await fetch(`${API_BASE_URL}/api/players/me`, {
      headers: {
        Authorization: `${tokenType.value || 'bearer'} ${accessToken.value}`,
      },
    })

    if (!response.ok) {
      if (response.status === 401) {
        logout()
      }
      return null
    }

    const data = await response.json()
    profile.value = data

    const nextUser = {
      ...(user.value || {}),
      email: data.user?.email || user.value?.email || '',
      full_name: data.user?.full_name || user.value?.full_name || '',
      avatar_url: data.user?.avatar_url || user.value?.avatar_url || '',
      phone: data.user?.phone || user.value?.phone || '',
      province: data.user?.province || user.value?.province || '',
      gender: data.user?.gender || user.value?.gender || '',
      date_of_birth: data.user?.date_of_birth || user.value?.date_of_birth || null,
      user_id: data.user?.id || user.value?.user_id || null,
      role_id: data.user?.role_id || roleId.value,
      account_type: data.user?.account_type || user.value?.account_type || 'user'
    }

    updateStoredUser(nextUser)
    return data
  }

  return {
    accessToken,
    tokenType,
    user,
    profile,
    roleId,
    isAdmin,
    isAuthenticated,
    hydrate,
    setSession,
    updateStoredUser,
    logout,
    fetchCurrentProfile,
  }
})
