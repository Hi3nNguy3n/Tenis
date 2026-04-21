import { getActivePinia } from 'pinia'
import { useAuthStore } from '../stores/auth'
import { getStoredAccessToken, getStoredTokenType } from '../utils/authStorage'

// Lấy các Base URL từ biến môi trường
const MAIN_API_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const CHAT_API_URL = import.meta.env.VITE_API_CHAT_URL || 'http://127.0.0.1:8001'

/**
 * Tự động lấy Token để gắn vào Header
 */
const resolveAuthHeader = () => {
  let accessToken = ''
  let tokenType = 'Bearer'

  const pinia = getActivePinia()
  if (pinia) {
    const authStore = useAuthStore(pinia)
    accessToken = authStore.accessToken || ''
    tokenType = authStore.tokenType || 'Bearer'
  }

  if (!accessToken) {
    accessToken = getStoredAccessToken()
    tokenType = getStoredTokenType() || 'Bearer'
  }

  // Tiêu chuẩn JWT thường yêu cầu 'Bearer ' viết hoa chữ B
  const normalizedType = tokenType.charAt(0).toUpperCase() + tokenType.slice(1).toLowerCase()

  if (!accessToken) return {}

  return {
    Authorization: `${normalizedType} ${accessToken}`,
  }
}

/**
 * Chuẩn hóa Header cho mỗi Request
 */
const normalizeHeaders = (headers = {}, includeJson = true) => {
  const authHeaders = resolveAuthHeader()
  const defaultHeaders = includeJson ? { 'Content-Type': 'application/json' } : {}

  return {
    ...defaultHeaders,
    ...authHeaders,
    ...headers,
  }
}

/**
 * Xử lý dữ liệu trả về từ Server
 */
const parseResponse = async (response) => {
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json()
  }
  return response.text()
}

/**
 * API CLIENT - Wrapper cho Fetch API
 */
export const apiClient = {
  async request(endpoint, options = {}) {
    const { method = 'GET', body, headers = {}, includeJson = true, useChatApi = false, ...rest } = options

    const baseUrl = useChatApi ? CHAT_API_URL : MAIN_API_URL
    const url = `${baseUrl}${endpoint}`
    const isFormData = body instanceof FormData
    const finalIncludeJson = isFormData ? false : includeJson

    const response = await fetch(url, {
      method,
      headers: normalizeHeaders(headers, finalIncludeJson),
      body: isFormData
        ? body
        : body && typeof body !== 'string' && finalIncludeJson
          ? JSON.stringify(body)
          : body,
      ...rest,
    })

    const data = await parseResponse(response)

    if (!response.ok) {
      const message =
        typeof data === 'object' && data !== null
          ? data.detail || data.message || 'Yêu cầu API thất bại.'
          : data || 'Yêu cầu API thất bại.'

      const error = new Error(message)
      error.status = response.status
      
      // MÔ PHỎNG CẤU TRÚC LỖI CỦA AXIOS ĐỂ FORM BẮT ĐƯỢC
      error.response = {
        status: response.status,
        data: typeof data === 'object' ? data : { detail: message }
      }
      
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
      body: payload,
    })
  },

  put(endpoint, payload, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: payload,
    })
  },

  patch(endpoint, payload, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH',
      body: payload,
    })
  },

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' })
  },
}

export default apiClient