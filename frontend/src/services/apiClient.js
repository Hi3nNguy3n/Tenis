import { getActivePinia } from 'pinia'
import { useAuthStore } from '../stores/auth'
import { getStoredAccessToken, getStoredTokenType } from '../utils/authStorage'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const resolveAuthHeader = () => {
  let accessToken = ''
  let tokenType = 'bearer'

  const pinia = getActivePinia()

  if (pinia) {
    const authStore = useAuthStore(pinia)
    accessToken = authStore.accessToken || ''
    tokenType = authStore.tokenType || 'bearer'
  }

  if (!accessToken) {
    accessToken = getStoredAccessToken()
    tokenType = getStoredTokenType()
  }

  if (!accessToken) {
    return {}
  }

  const normalizedType = tokenType || 'bearer'

  return {
    Authorization: `${normalizedType} ${accessToken}`,
  }
}

const normalizeHeaders = (headers = {}, includeJson = true) => {
  const authHeaders = resolveAuthHeader()
  const defaultHeaders = includeJson ? { 'Content-Type': 'application/json' } : {}

  return {
    ...defaultHeaders,
    ...authHeaders,
    ...headers,
  }
}

const parseResponse = async (response) => {
  const contentType = response.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    return response.json()
  }

  return response.text()
}

export const apiClient = {
  async request(endpoint, options = {}) {
    const { headers, body, method = 'GET', includeJson = true, ...rest } = options
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method,
      headers: normalizeHeaders(headers, includeJson),
      body,
      ...rest,
    })

    const data = await parseResponse(response)

    if (!response.ok) {
      const message =
        typeof data === 'object' && data !== null
          ? data.detail || data.message || 'API request failed.'
          : data || 'API request failed.'

      const error = new Error(message)
      error.status = response.status
      error.payload = data
      throw error
    }

    return data
  },
  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' })
  },
  post(endpoint, payload, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: typeof payload === 'string' ? payload : JSON.stringify(payload),
    })
  },
  patch(endpoint, payload, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH',
      body: typeof payload === 'string' ? payload : JSON.stringify(payload),
    })
  },
  put(endpoint, payload, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: typeof payload === 'string' ? payload : JSON.stringify(payload),
    })
  },
  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' })
  },
}


export default apiClient

