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

  if (!accessToken) return {}

  const normalizedType = tokenType || 'bearer'
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
    const { 
      headers, 
      body, 
      method = 'GET', 
      includeJson = true, 
      useChatApi = false, // Option để chọn Server Chat (8001)
      ...rest 
    } = options

    // Lựa chọn Base URL tương ứng
    const baseUrl = useChatApi ? CHAT_API_URL : MAIN_API_URL
    
    // Đảm bảo endpoint bắt đầu bằng /
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
    const url = `${baseUrl}${cleanEndpoint}`

    const response = await fetch(url, {
      method,
      headers: normalizeHeaders(headers, includeJson),
      body: body && typeof body !== 'string' && includeJson ? JSON.stringify(body) : body,
      ...rest,
    })

    const data = await parseResponse(response)

    if (!response.ok) {
      const message = typeof data === 'object' && data !== null
          ? data.detail || data.message || 'Yêu cầu API thất bại.'
          : data || 'Yêu cầu API thất bại.'

      const error = new Error(message)
      error.status = response.status
      error.payload = data
      throw error
    }

    return data
  },

  // --- CÁC HÀM TIỆN ÍCH ---

  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' })
  },

  post(endpoint, payload, options = {}) {
    return this.request(endpoint, { ...options, method: 'POST', body: payload })
  },

  put(endpoint, payload, options = {}) {
    return this.request(endpoint, { ...options, method: 'PUT', body: payload })
  },

  patch(endpoint, payload, options = {}) {
    return this.request(endpoint, { ...options, method: 'PATCH', body: payload })
  },

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' })
  },
}

export default apiClient