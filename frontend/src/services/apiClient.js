import { getActivePinia } from 'pinia'
import { useAuthStore } from '../stores/auth'
import { getStoredAccessToken, getStoredTokenType } from '../utils/authStorage'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

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
    const { headers, body, params, method = 'GET', includeJson = true, ...rest } = options

    let url = `${API_BASE_URL}${endpoint}`
    if (params && Object.keys(params).length > 0) {
      // Clean params: remove null, undefined, or empty strings
      const cleanParams = Object.keys(params).reduce((acc, key) => {
        const value = params[key]
        if (value !== null && value !== undefined && value !== '') {
          acc[key] = value
        }
        return acc
      }, {})

      if (Object.keys(cleanParams).length > 0) {
        const queryString = new URLSearchParams(cleanParams).toString()
        url += `?${queryString}`
      }
    }

    // Nếu body là FormData, trình duyệt sẽ tự đặt Content-Type (multipart/form-data) kèm boundary
    // nên ta cần tránh ép kiểu JSON.
    const isFormData = body instanceof FormData
    const finalIncludeJson = isFormData ? false : includeJson

    const response = await fetch(url, {
      method,
      headers: normalizeHeaders(headers, finalIncludeJson),
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
    const isFormData = payload instanceof FormData
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: isFormData ? payload : (typeof payload === 'string' ? payload : JSON.stringify(payload)),
    })
  },

  patch(endpoint, payload, options = {}) {
    const isFormData = payload instanceof FormData
    return this.request(endpoint, {
      ...options,
      method: 'PATCH',
      body: isFormData ? payload : (typeof payload === 'string' ? payload : JSON.stringify(payload)),
    })
  },
  put(endpoint, payload, options = {}) {
    const isFormData = payload instanceof FormData
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: isFormData ? payload : (typeof payload === 'string' ? payload : JSON.stringify(payload)),
    })
  },
  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' })
  },
}


export default apiClient

