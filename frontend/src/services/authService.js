import apiClient from './apiClient'

export const authService = {
  sendOtp(email) {
    return apiClient.post('/api/auth/send-otp', { email }, { useChatApi: false })
  },

  register(payload) {
    return apiClient.post('/api/auth/register', payload, { useChatApi: false })
  },

  login(payload) {
    return apiClient.post('/api/auth/login', payload, { useChatApi: false })
  },
}

export default authService
