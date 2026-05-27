const isBrowser = typeof window !== 'undefined'

export const normalizeHttpBaseUrl = (value, fallback = '') => {
  if (typeof value === 'undefined' || value === null) return fallback

  const trimmed = String(value).trim().replace(/\/$/, '')
  if (!trimmed) return ''
  if (!isBrowser) return trimmed

  try {
    const url = new URL(trimmed, window.location.origin)
    const isLocalhostTarget = ['localhost', '127.0.0.1'].includes(url.hostname)
    const isLocalhostPage = ['localhost', '127.0.0.1'].includes(window.location.hostname)

    if (isLocalhostTarget && !isLocalhostPage) {
      return ''
    }

    if (window.location.protocol === 'https:' && url.protocol === 'http:') {
      url.protocol = 'https:'
    }

    return url.origin === window.location.origin ? '' : url.origin
  } catch {
    return trimmed
  }
}

export const getApiBaseUrl = () => normalizeHttpBaseUrl(import.meta.env.VITE_API_BASE_URL, '')

export const getChatApiBaseUrl = () => (
  normalizeHttpBaseUrl(import.meta.env.VITE_API_CHAT_URL, getApiBaseUrl())
)

export const getWsChatBaseUrl = () => {
  const envWsUrl = import.meta.env.VITE_WS_CHAT_URL

  if (!isBrowser) {
    return typeof envWsUrl === 'undefined' ? '' : String(envWsUrl).trim().replace(/\/$/, '')
  }

  const fallback = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
  const rawValue = typeof envWsUrl === 'undefined' || envWsUrl === null ? '' : String(envWsUrl).trim()
  if (!rawValue) return fallback

  try {
    const url = new URL(rawValue)
    const isLocalhostTarget = ['localhost', '127.0.0.1'].includes(url.hostname)
    const isLocalhostPage = ['localhost', '127.0.0.1'].includes(window.location.hostname)

    if (isLocalhostTarget && !isLocalhostPage) {
      return fallback
    }

    if (window.location.protocol === 'https:' && url.protocol === 'ws:') {
      url.protocol = 'wss:'
    }

    return url.origin
  } catch {
    return fallback
  }
}
