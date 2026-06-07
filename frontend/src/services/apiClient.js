import { getActivePinia } from 'pinia'
import { useAuthStore } from '../stores/auth'
import { getStoredAccessToken, getStoredTokenType } from '../utils/authStorage'
import { getApiBaseUrl, getChatApiBaseUrl } from '../utils/apiUrls'
import { ElMessage } from 'element-plus'

export const MAIN_API_URL = getApiBaseUrl()
export const CHAT_API_URL = getChatApiBaseUrl()

const TRAILING_SLASH_ENDPOINTS = new Set([
  '/api/challenges',
  '/api/courts',
  '/api/matches',
  '/api/news',
  '/api/registrations',
  '/api/tournaments',
])

const normalizeEndpoint = (endpoint) => {
  const [path, query = ''] = endpoint.split('?')
  const normalizedPath = TRAILING_SLASH_ENDPOINTS.has(path) ? `${path}/` : path
  return query ? `${normalizedPath}?${query}` : normalizedPath
}

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
    let url = `${baseUrl}${normalizeEndpoint(endpoint)}`
    
    // Support query parameters in GET/DELETE or any request
    if (options.params && Object.keys(options.params).length > 0) {
      const queryParams = new URLSearchParams()
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, value)
        }
      })
      const queryString = queryParams.toString()
      if (queryString) {
        url += (url.includes('?') ? '&' : '?') + queryString
      }
    }

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
      if (response.status === 401) {
        const pinia = getActivePinia()
        if (pinia) {
          const authStore = useAuthStore(pinia)
          authStore.logout()
        }
        
        // Hiển thị thông báo thân thiện hơn
        ElMessage.error('Phiên đăng nhập của bạn đã hết hạn. Vui lòng đăng nhập lại.')
        
        // Điều hướng sau 1.5s
        setTimeout(() => {
          const currentPath = window.location.pathname
          const currentSearch = window.location.search
          const redirectQuery = encodeURIComponent(currentPath + currentSearch)
          
          if (currentPath.startsWith('/admin')) {
            window.location.href = `/admin/login?redirect=${redirectQuery}`
          } else {
            window.location.href = `/login?redirect=${redirectQuery}`
          }
        }, 1500)

        const error = new Error('Phiên đăng nhập của bạn đã hết hạn. Vui lòng đăng nhập lại.')
        error.status = 401
        error.response = {
          status: 401,
          data: { detail: 'Phiên đăng nhập của bạn đã hết hạn. Vui lòng đăng nhập lại.' }
        }
        throw error
      }

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
