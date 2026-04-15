// src/utils/authStorage.js

const TOKEN_KEY = 'saigon_tennis_access_token'
const TOKEN_TYPE_KEY = 'saigon_tennis_token_type'
const USER_KEY = 'saigon_tennis_user'

export const persistAuthSession = ({ accessToken, tokenType, user }) => {
  if (accessToken) {
    localStorage.setItem(TOKEN_KEY, accessToken)
  }
  if (tokenType) {
    localStorage.setItem(TOKEN_TYPE_KEY, tokenType)
  }
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }
}

export const clearAuthSession = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(TOKEN_TYPE_KEY)
  localStorage.removeItem(USER_KEY)
}

export const getStoredAccessToken = () => {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export const getStoredTokenType = () => {
  return localStorage.getItem(TOKEN_TYPE_KEY) || 'bearer'
}

export const getStoredUser = () => {
  const userStr = localStorage.getItem(USER_KEY)
  if (!userStr) return null
  
  try {
    return JSON.parse(userStr)
  } catch (error) {
    console.error('Lỗi khi parse dữ liệu User từ LocalStorage:', error)
    return null
  }
}